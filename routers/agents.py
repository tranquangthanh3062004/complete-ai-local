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

from llm_factory import get_llm
from routers.auth import get_current_user
from models import User, LearningEvent
from database import get_db
from config import settings
from services.ai_rag import get_vector_store, format_docs
from services.ai_topic import detect_topic, TOPIC_DISPLAY, _get_gtcc_suggestions
from logger import get_logger
from services.cache_service import get_semantic_cache, get_agent_cache
from services.sanitizer import sanitize_query, is_gtcc_related
from services.lang_detect import build_multilingual_query

router = APIRouter(prefix="/agents", tags=["agents"])
logger = get_logger("agents")

# ── System Prompt cực ngắn, tập trung ─────────────────────────────────────────
GTCC_SYSTEM_PROMPT = (
    "Bạn là Trợ lý AI Giao Thông Công Cộng (GTCC) Việt Nam.\n"
    "NGUYÊN TẮC TRẢ LỜI:\n"
    "1. ĐỊNH DẠNG: Bắt buộc dùng Markdown (in đậm, danh sách, bảng biểu nếu cần) để câu trả lời rõ ràng.\n"
    "2. TRỌNG TÂM: Chỉ trả lời các vấn đề về xe buýt, metro, lộ trình, giá vé, luật giao thông. Từ chối khéo léo các chủ đề khác.\n"
    "3. KẾT HỢP PTTCC: Nếu hỏi lộ trình, ưu tiên gợi ý kết hợp đa phương thức (ví dụ: Xe buýt + Metro).\n"
    "4. TÍCH CỰC: Thêm emoji 🚌 🚇 🎫 📍 🚲 để giao diện thân thiện.\n"
    "5. NGẮN GỌN: Không xin lỗi dài dòng, trả lời ngay vào vấn đề, tối đa 250 từ.\n"
)

CHAT_PROMPT = PromptTemplate.from_template(
    GTCC_SYSTEM_PROMPT +
    "{context}"
    "Câu hỏi: {question}\n"
    "{history}"
    "Trả lời:"
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
    "🚦 Tôi có thể giúp bạn về GTCC Việt Nam:\n"
    "🚌 Xe buýt | 🚇 Metro | 🎫 Vé & giá cước | 📋 Luật GT | ✈️ Sân bay\n"
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
        llm = get_llm(payload.model_name, payload.temperature or 0.1)

        # ── 3. Phát hiện ngôn ngữ ───────────────────────────────────────────
        lang, lang_instruction = build_multilingual_query(clean_query)
        if not is_gtcc_related(clean_query):
            logger.info(f"[Direct Chat] Off-topic detected (lang={lang}): '{clean_query[:60]}'")

        # ── 4. Lịch sử hội thoại (giới hạn 3 tin nhắn để tăng tốc) ──────────
        history_text = ""
        if payload.messages:
            for msg in payload.messages[-3:]:
                role = "User" if msg.get("role") == "user" else "Bot"
                content = str(msg.get("content", ""))[:200]
                history_text += f"{role}: {content}\n"

        # ── 5. RAG context ───────────────────────────────────────────────────
        rag_context = ""
        try:
            vectordb = get_vector_store()
            docs = vectordb.similarity_search(clean_query, k=4)
            if docs:
                rag_context = "Tài liệu GTCC:\n" + format_docs(docs) + "\n\n"
        except Exception:
            pass

        # Thêm language instruction vào context nếu không phải tiếng Việt
        if lang_instruction:
            rag_context = lang_instruction + "\n" + rag_context

        # ── 6. Gọi LLM với Retry (tenacity) ─────────────────────────────────
        try:
            from tenacity import retry, stop_after_attempt, wait_exponential, RetryError  # type: ignore

            @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
            def call_llm():
                chain = CHAT_PROMPT | llm | StrOutputParser()
                return chain.invoke({
                    "history" : history_text,
                    "context" : rag_context,
                    "question": clean_query,
                })

            answer = call_llm()
        except Exception:
            # Nếu tenacity chưa cài hoặc lỗi → gọi trực tiếp
            chain = CHAT_PROMPT | llm | StrOutputParser()
            answer = chain.invoke({
                "history" : history_text,
                "context" : rag_context,
                "question": clean_query,
            })

        # Normalize answer: StrOutputParser tra ve str, nhung de an toan
        if not isinstance(answer, str):
            answer = getattr(answer, 'content', str(answer))
        answer = answer.strip()

        if len(answer) < 5:
            answer = QUICK_FALLBACK.get(topic, DEFAULT_FALLBACK)

        # ── 7. Lưu vào Cache ─────────────────────────────────────────────────
        cache.set(clean_query, answer)

        elapsed_ms = round((time.time() - start) * 1000, 1)
        event = await _save_chat_event(db, current_user, payload, answer, elapsed_ms, clean_query)

        suggestions = _get_gtcc_suggestions(topic) if payload.suggest else []

        logger.info(f"[Direct Chat] Session: {payload.session_id} | lang={lang} | Q: '{clean_query[:60]}' | Topic: {topic} | Time: {elapsed_ms}ms")

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
        # Ollama/Cloud API offline → trả fallback ngay, không raise lỗi
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
    cache = get_semantic_cache()
    cached_answer = cache.get(clean_query)

    async def event_generator():
        if cached_answer:
            # Fake streaming for cached responses to keep the UX consistent
            chunk_size = max(1, len(cached_answer) // 20)
            for i in range(0, len(cached_answer), chunk_size):
                chunk = cached_answer[i:i+chunk_size]
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.02)
            return

        llm = get_llm(payload.model_name, payload.temperature or 0.1)
        lang, lang_instruction = build_multilingual_query(clean_query)
        
        # History
        history_text = ""
        if payload.messages:
            for msg in payload.messages[-3:]:
                role = "User" if msg.get("role") == "user" else "Bot"
                content = str(msg.get("content", ""))[:200]
                history_text += f"{role}: {content}\n"
                
        # Smart Transport Injection logic
        # If user is asking for a route, try to provide transit context
        route_context = ""
        query_lower = clean_query.lower()
        if "đi từ" in query_lower or "đến" in query_lower or "lộ trình" in query_lower or "tuyến" in query_lower:
            try:
                from services.route_planner import find_route
                import re

                def extract_route_query(text: str):
                    patterns = [
                        r"từ\s+(.+?)\s+đến\s+(.+?)(?:\s*\?|$)",
                        r"đi từ\s+(.+?)\s+tới\s+(.+?)(?:\s*\?|$)",
                        r"(.+?)\s+đến\s+(.+?)(?:\s*\?|$)",
                    ]
                    for p in patterns:
                        m = re.search(p, text.lower())
                        if m:
                            return m.group(1).strip(), m.group(2).strip()
                    return text, text

                origin, destination = extract_route_query(clean_query)
                route_data = find_route(origin, destination)
                if "error" not in route_data:
                    route_context = f"\nLỘ TRÌNH KẾT HỢP GỢI Ý:\nTừ {route_data['origin']} đến {route_data['destination']}: Tổng {route_data['total_time']}phút, {route_data['total_cost']}VNĐ.\n"
                    for s in route_data["steps"]:
                        route_context += f"- Bước {s['step']}: {s['type']} {s['line']} từ {s['from']} đến {s['to']} ({s['duration']}phút, {s['cost']}VNĐ)\n"
            except Exception as e:
                pass

        # RAG context
        rag_context = ""
        try:
            vectordb = get_vector_store()
            docs = vectordb.similarity_search(clean_query, k=4)
            if docs:
                rag_context = "Tài liệu GTCC:\n" + format_docs(docs) + "\n\n"
        except Exception:
            pass

        if lang_instruction:
            rag_context = lang_instruction + "\n" + rag_context
            
        full_context = rag_context + route_context

        chain = CHAT_PROMPT | llm | StrOutputParser()
        full_answer = ""
        
        try:
            # Langchain's astream
            async for chunk in chain.astream({
                "history" : history_text,
                "context" : full_context,
                "question": clean_query,
            }):
                full_answer += chunk
                # Safely format SSE chunk with newlines
                chunk_sse = chunk.replace('\n', '\ndata: ')
                yield f"data: {chunk_sse}\n\n"
                
            if len(full_answer) >= 5:
                cache.set(clean_query, full_answer)
                elapsed_ms = round((time.time() - start) * 1000, 1)
                # Background task to save event could be used here
                await _save_chat_event(db, current_user, payload, full_answer, elapsed_ms, clean_query)
        except Exception as e:
            err = str(e)
            logger.error(f"Streaming error: {err}")
            fallback = QUICK_FALLBACK.get(topic, DEFAULT_FALLBACK)
            
            if "api_key" in err.lower() or "401" in err.lower() or "authentication" in err.lower() or "none" in err.lower():
                fallback += "\n\n⚠️ *Bot đang offline vì thiếu thiết lập GEMINI_API_KEY trên Vercel.*"
            else:
                fallback += "\n\n⚠️ *Bot đang gặp lỗi cấu hình trên Vercel.*"
                
            yield f"data: {fallback}\n\n"
            
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
