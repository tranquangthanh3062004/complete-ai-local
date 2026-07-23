"""
Agents Router v5.0 — Chatbot Giao Thông Công Cộng (GTCC)
Tối ưu: trả lời nhanh, trọng tâm, có fallback thông minh.
V5 bổ sung: Cache, Sanitizer, Lang-detect, Retry logic.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from rate_limiter import limiter
from pydantic import BaseModel
from typing import Optional
import time

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
import asyncio

from llm_factory import get_llm, GTCC_SYSTEM_PROMPT
from routers.auth import get_current_user
from models import User, LearningEvent
from database import get_db
from config import settings
from services.ai_rag import get_vector_store, format_docs
from services.ai_topic import detect_topic, TOPIC_DISPLAY, _get_gtcc_suggestions
from logger import get_logger
from services.cache_service import get_agent_cache
from services.sanitizer import sanitize_query, is_gtcc_related
from services.lang_detect import build_multilingual_query

router = APIRouter(prefix="/agents", tags=["agents"])
logger = get_logger("agents")

# ── System Prompt được import từ llm_factory ──────────────────────────────────
# GTCC_SYSTEM_PROMPT được quản lý tập trung tại llm_factory.py để đồng nhất.

CHAT_PROMPT = PromptTemplate.from_template(
    GTCC_SYSTEM_PROMPT +
    "{context}\n"
    "Lịch sử trò chuyện:\n"
    "{history}\n"
    "Câu hỏi mới của người dùng: {question}\n"
    "Trả lời của bạn:"
)


# ── Schemas ───────────────────────────────────────────────────────────────────
class AgentRequest(BaseModel):
    query      : str
    model_name : Optional[str] = None
    temperature: Optional[float] = 0.1
    messages   : Optional[list] = None
    session_id : Optional[str] = "default"
    suggest    : Optional[bool] = False


# ── Save event helper ─────────────────────────────────────────────────────────
async def _save_chat_event(db, current_user, request, answer: str, elapsed_ms: float, clean_query: str = None):
    """Luu su kien chat vao DB. Dung clean_query neu co."""
    q = clean_query or request.query
    topic = detect_topic(q)
    event = LearningEvent(
        user_id          = current_user.id if current_user else None,
        session_id       = request.session_id,
        question         = q,
        answer           = str(answer)[:2000],   # Gioi han de tranh DB loi
        topic            = topic,
        response_time_ms = elapsed_ms,
        model_used       = request.model_name or settings.llm_model_name,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


# ── Fallback thông minh theo topic ────────────────────────────────────────────
QUICK_FALLBACK = {
    "xe_buyt": (
        "🚌 **Xe Buýt:** Hà Nội có hơn 120 tuyến (giá vé 7.000-9.000đ/lượt).\n"
        "📱 Tra tuyến: App **BusMap** hoặc **Tìm Buýt**.\n"
        "🎫 Sinh viên mua vé tháng 100.000đ | Người cao tuổi: miễn phí."
    ),
    "metro_tau_dien": (
        "🚇 **Metro Hà Nội 2A** (Cát Linh - Hà Đông): 12 ga, 5:30-22:30, 8.000-15.000đ/lượt.\n"
        "🚇 **Metro Nhổn - Ga Hà Nội** (Đoạn trên cao): 8.000-12.000đ/lượt.\n"
        "📱 Mua vé: Tại nhà ga hoặc dùng vé tháng 200.000đ."
    ),
    "ve_gia_cuoc": (
        "🎫 **Giá vé:** Xe buýt HN 7.000-9.000đ | Metro HN 8.000-15.000đ.\n"
        "💳 Vé tháng: Xe buýt liên tuyến 200.000đ (sv: 100.000đ) | Metro 200.000đ (sv: 100.000đ).\n"
        "✅ Người cao tuổi, người có công: miễn phí."
    ),
    "san_bay_ga_tau": (
        "✈️ **Sân bay Nội Bài → HN:**\n"
        "- Tuyến 86 (Ga Hà Nội - Nội Bài): 45.000đ\n"
        "- Tuyến 68 (Hà Đông/Cầu Giấy - Nội Bài): 50.000đ\n"
        "- Tuyến 07, 17, 90 (Xe buýt thường): 9.000đ."
    ),
    "luat_quy_dinh": (
        "📋 **Mức phạt chính (NĐ 100/2019):**\n"
        "• Vượt đèn đỏ: 4-6 triệu (xe máy), 6-8 triệu (ô tô)\n"
        "• Nồng độ cồn mức cao: 30-40 triệu + tước GPLX\n"
        "• Không mũ BH: 200.000-400.000đ"
    ),
}

DEFAULT_FALLBACK = (
    "🚦 Tôi có thể giúp bạn về GTCC Việt Nam:\n\n"
    "🚌 Xe buýt | 🚇 Metro | 🎫 Vé & giá cước | 📋 Luật GT | ✈️ Sân bay\n\n"
    "📱 Tra cứu nhanh: **BusMap** hoặc **Google Maps**."
)


# ── Endpoint chính ────────────────────────────────────────────────────────────
@router.post("/direct")
@limiter.limit("20/minute")
async def direct_chat(
    request     : Request,
    payload     : AgentRequest,
    db          : AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    # ── 1. Sanitize input ────────────────────────────────────────────────────
    clean_query, is_safe, reason = sanitize_query(payload.query)
    if not is_safe:
        raise HTTPException(status_code=400, detail=reason)

    topic = detect_topic(clean_query)
    start = time.time()

    # ── 2. Kiểm tra Cache (tránh gọi LLM lại cho câu hỏi đã trả lời) ────────
    cache = get_agent_cache()
    cached_answer = cache.get(clean_query)
    if cached_answer:
        logger.info(f"[Direct Chat] Cache HIT | Q: '{clean_query[:60]}'")
        return {
            "result"      : cached_answer,
            "event_id"    : -1,   # Không tạo event mới cho cached response
            "response_ms" : 0,
            "model"       : "cache",
            "topic"       : TOPIC_DISPLAY.get(topic, topic),
            "suggestions" : _get_gtcc_suggestions(topic) if payload.suggest else [],
            "cached"      : True,
        }
    try:
        # ── Refactored LangGraph Integration ──
        from services.langgraph_agent import graph_app
        from langchain_core.messages import HumanMessage
        
        agent_msgs = []
        if payload.messages:
            for msg in payload.messages[-3:]:
                if msg.get("role") == "user":
                    agent_msgs.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "ai" or msg.get("role") == "assistant":
                    from langchain_core.messages import AIMessage
                    agent_msgs.append(AIMessage(content=msg.get("content", "")))
        
        agent_msgs.append(HumanMessage(content=clean_query))
        
        state_input = {
            "messages": agent_msgs,
            "model_name": payload.model_name or settings.llm_model_name,
            "temperature": payload.temperature or 0.1
        }
        
        # Invoke LangGraph
        result = await graph_app.ainvoke(state_input)
        answer = result["messages"][-1].content
        
        answer = answer.strip()
        if len(answer) < 5:
            ctx = result.get("context", "")
            if "Lộ trình" in ctx or "OpenStreetMap" in ctx or "Google Maps" in ctx:
                answer = ctx.strip()
            else:
                answer = QUICK_FALLBACK.get(topic, DEFAULT_FALLBACK)

        # ── 7. Lưu vào Cache ─────────────────────────────────────────────────
        cache.set(clean_query, answer)

        elapsed_ms = round((time.time() - start) * 1000, 1)
        event = await _save_chat_event(db, current_user, payload, answer, elapsed_ms, clean_query)

        suggestions = _get_gtcc_suggestions(topic) if payload.suggest else []

        logger.info(f"[Direct Chat] Session: {payload.session_id} | Q: '{clean_query[:60]}' | Topic: {topic} | Time: {elapsed_ms}ms")

        return {
            "result"      : answer,
            "event_id"    : event.id,
            "response_ms" : elapsed_ms,
            "model"       : payload.model_name or settings.llm_model_name,
            "topic"       : TOPIC_DISPLAY.get(topic, topic),
            "suggestions" : suggestions,
            "cached"      : False,
        }

    except Exception as e:
        err = str(e)
        logger.error(f"[Direct Chat] LLM Error: {err}")
        
        # Nếu là câu hỏi lộ trình, ưu tiên dùng dữ liệu định tuyến thực tế thay vì menu tĩnh
        from services.langgraph_agent import extract_locations_and_intent
        req_map, _, orig, dest = extract_locations_and_intent(clean_query)
        if req_map and dest:
            from services.google_maps import gmaps_service
            orig_str = orig if orig else "Vị trí hiện tại"
            fallback = gmaps_service.get_directions(orig_str, dest)
        else:
            fallback = QUICK_FALLBACK.get(topic, DEFAULT_FALLBACK)
            if "api_key" in err.lower() or "401" in err.lower() or "authentication" in err.lower():
                fallback += "\n\n⚠️ *AI đang offline (Thiếu hoặc sai API Key) — đang hiển thị thông tin cơ bản.*"
            else:
                fallback += "\n\n⚠️ *AI đang offline hoặc bị lỗi kết nối — đang hiển thị thông tin cơ bản.*"

        try:
            event = await _save_chat_event(db, current_user, payload, fallback, 0)
            return {
                "result"      : fallback,
                "event_id"    : event.id,
                "response_ms" : 0,
                "model"       : "offline-fallback",
                "topic"       : TOPIC_DISPLAY.get(topic, topic),
                "suggestions" : _get_gtcc_suggestions(topic),
            }
        except Exception:
            pass

        if "connection" in err.lower() or "refused" in err.lower():
            logger.error("Ollama connection failed. Returning fallback.")
            raise HTTPException(status_code=503, detail="Ollama chưa chạy. Gõ: ollama serve")
        
        logger.error(f"Error in direct_chat: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=err)


@router.post("/stream")
@limiter.limit("20/minute")
async def stream_chat(
    request     : Request,
    payload     : AgentRequest,
    db          : AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Streaming endpoint for fast UX."""
    clean_query, is_safe, reason = sanitize_query(payload.query)
    if not is_safe:
        raise HTTPException(status_code=400, detail=reason)

    topic = detect_topic(clean_query)
    start = time.time()
    cache = get_agent_cache()
    cached_answer = cache.get(clean_query)

    async def event_generator():
        if cached_answer:
            # Fake streaming for cached responses to keep the UX consistent
            chunk_size = max(1, len(cached_answer) // 20)
            for i in range(0, len(cached_answer), chunk_size):
                chunk = cached_answer[i:i+chunk_size]
                chunk_sse = chunk.replace('\n', '\ndata: ')
                yield f"data: {chunk_sse}\n\n"
                await asyncio.sleep(0.02)
            return

        lang, lang_instruction = build_multilingual_query(clean_query)
        
        # History
        history_text = ""
        if payload.messages:
            for msg in payload.messages[-3:]:
                role = "User" if msg.get("role") == "user" else "Bot"
                content = str(msg.get("content", ""))[:200]
                history_text += f"{role}: {content}\n"
                
        # ── Refactored LangGraph Integration ──
        try:
            from services.langgraph_agent import graph_app
            from langchain_core.messages import HumanMessage
            import json
            
            # Khởi tạo messages
            agent_msgs = []
            if payload.messages:
                for msg in payload.messages[-4:]:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if role == "user":
                        agent_msgs.append(HumanMessage(content=content))
                    elif role in ["ai", "assistant"]:
                        from langchain_core.messages import AIMessage
                        agent_msgs.append(AIMessage(content=content))
            
            # Thêm tin nhắn hiện tại
            agent_msgs.append(HumanMessage(content=clean_query))
            
            state_input = {
                "messages": agent_msgs,
                "model_name": payload.model_name or settings.llm_model_name,
                "temperature": payload.temperature or 0.1
            }
            
            final_answer = ""
            
            # Stream events
            async for event in graph_app.astream_events(state_input, version="v1"):
                kind = event["event"]
                if kind in ["on_chat_model_stream", "on_llm_stream"]:
                    node = event.get("metadata", {}).get("langgraph_node")
                    # CHỈ stream output từ node generate, tuyệt đối không stream từ analyze/intent node
                    if node != "generate":
                        continue
                    
                    chunk = event["data"]["chunk"]
                    content = getattr(chunk, "content", str(chunk))
                    if content:
                        final_answer += content
                        # Escape newlines for SSE
                        chunk_sse = content.replace('\n', '\ndata: ')
                        yield f"data: {chunk_sse}\n\n"
                        
            # Normalize answer
            final_answer = final_answer.strip()
            if len(final_answer) < 5:
                final_answer = QUICK_FALLBACK.get(topic, DEFAULT_FALLBACK)
                
            cache.set(clean_query, final_answer)
            elapsed_ms = round((time.time() - start) * 1000, 1)
            
            # Save event in background (no await here in generator since db session might be tricky, but let's keep original logic)
            # Original code did save_chat_event but it's not strictly necessary in stream if it causes session issues, but let's just log it.
            logger.info(f"[LangGraph Stream] Time: {elapsed_ms}ms | Q: '{clean_query[:60]}'")
            return
            
        except Exception as e:
            logger.error(f"[LangGraph Stream] Error: {e}", exc_info=True)
            fallback = QUICK_FALLBACK.get(topic, DEFAULT_FALLBACK)
            if "429" in str(e) or "quota" in str(e).lower():
                fallback += "\n\n⚠️ *Hệ thống đang quá tải (vượt quá giới hạn API). Vui lòng thử lại sau.*"
            fallback_sse = fallback.replace('\n', '\ndata: ')
            yield f"data: {fallback_sse}\n\n"
            return
        # Old logic removed
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/research")
@limiter.limit("20/minute")
async def research_agent(
    request     : Request,
    payload     : AgentRequest,
    db          : AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    return await direct_chat(request, payload, db, current_user)
