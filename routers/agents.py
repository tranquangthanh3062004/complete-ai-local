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

from llm_factory import get_llm
from routers.auth import get_current_user
from models import User, LearningEvent
from database import get_db
from config import settings
from routers.rag import get_vector_store, format_docs, detect_topic, TOPIC_DISPLAY
from logger import get_logger
from services.cache_service import get_agent_cache
from services.sanitizer import sanitize_query, is_gtcc_related
from services.lang_detect import build_multilingual_query

router = APIRouter(prefix="/agents", tags=["agents"])
logger = get_logger("agents")

# ── System Prompt cực ngắn, tập trung ─────────────────────────────────────────
GTCC_SYSTEM_PROMPT = (
    "Bạn là Trợ lý GTCC Việt Nam. Trả lời NGẮN GỌN, TRỌNG TÂM bằng tiếng Việt.\n"
    "NGUYÊN TẮC:\n"
    "1. Nếu có tài liệu GTCC → dùng ngay, không nói thêm.\n"
    "2. Nếu không có dữ liệu → trả lời dựa trên kiến thức chung, đừng xin lỗi dài dòng.\n"
    "3. Câu khó/không biết → trả lời ngắn: thông tin gợi ý + hướng dẫn dùng app BusMap/Google Maps.\n"
    "4. Dùng emoji 🚌🚇🎫📍 cho dễ đọc. Không viết dài quá 200 từ.\n"
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
        "🚌 **Xe Buýt:** TP.HCM ~100 tuyến (5.000-8.000đ), Hà Nội ~120 tuyến (7.000-9.000đ).\n"
        "📱 Tra tuyến: App **BusMap** hoặc **Google Maps**.\n"
        "🎫 HSSV giảm 50% | Người cao tuổi, khuyết tật: miễn phí."
    ),
    "metro_tau_dien": (
        "🚇 **Metro TP.HCM số 1** (Bến Thành - Suối Tiên): 14 ga, 5:30-22:00, 6.000-20.000đ/lượt.\n"
        "🚇 **Metro Hà Nội 2A** (Cát Linh - Hà Đông): 12 ga, 5:30-22:30, 8.000-15.000đ/lượt.\n"
        "📱 Mua vé: App HCMC Metro (HCM) | iMaaS (HN)."
    ),
    "ve_gia_cuoc": (
        "🎫 **Giá vé:** Xe buýt HCM 5.000-8.000đ | Metro HCM 6.000-20.000đ | Metro HN 8.000-15.000đ.\n"
        "💳 Vé tháng: Metro HCM 300.000đ (sv: 150.000đ) | Metro HN 200.000đ (sv: 100.000đ).\n"
        "✅ HSSV giảm 50% | Người cao tuổi, khuyết tật, thương binh: miễn phí."
    ),
    "san_bay_ga_tau": (
        "✈️ **Sân bay TSN → Trung tâm HCM:** Xe buýt 152 (5.000đ, 30-45ph) hoặc Metro số 1.\n"
        "✈️ **Sân bay Nội Bài → HN:** Xe buýt 7 → Mỹ Đình (9.000đ, 45ph) hoặc tuyến 86 → Gia Lâm."
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
        from routers.rag import _get_gtcc_suggestions
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

        from routers.rag import _get_gtcc_suggestions
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
        # Ollama offline → trả fallback ngay, không raise lỗi
        fallback = QUICK_FALLBACK.get(topic, DEFAULT_FALLBACK)
        fallback += "\n\n⚠️ *AI đang offline — đang hiển thị thông tin cơ bản.*"

        try:
            event = await _save_chat_event(db, current_user, payload, fallback, 0)
            from routers.rag import _get_gtcc_suggestions
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


@router.post("/research")
@limiter.limit("20/minute")
async def research_agent(
    request     : Request,
    payload     : AgentRequest,
    db          : AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    return await direct_chat(request, payload, db, current_user)
