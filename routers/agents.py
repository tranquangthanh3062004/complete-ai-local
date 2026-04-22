"""
Agents Router - LCEL chain thuần với Ollama local v3.1
System prompt tiếng Việt được nhúng trực tiếp vào prompt (tương thích mọi phiên bản).
"""
from fastapi import APIRouter, Depends, HTTPException
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

router = APIRouter(prefix="/agents", tags=["agents"])


# ── Math Tool ─────────────────────────────────────────────────────────────────
def try_calculate(text: str) -> Optional[str]:
    """Thử phát hiện và tính toán biểu thức toán học."""
    import re
    match = re.search(r'[\d\s\+\-\*\/\(\)\.]{3,}', text)
    if match:
        expr = match.group().strip()
        try:
            allowed = set("0123456789+-*/.() ")
            if all(c in allowed for c in expr) and any(c.isdigit() for c in expr):
                result = eval(expr, {"__builtins__": {}})
                return f"Ket qua tinh toan: {expr} = {result}"
        except Exception:
            pass
    return None


# ── Prompt — System prompt tiếng Việt nhúng trực tiếp ────────────────────────
CHAT_PROMPT = PromptTemplate.from_template(
    "Bạn là trợ lý AI thông minh, chuyên nghiệp, thân thiện.\n"
    "BẮT BUỘC: Luôn luôn trả lời bằng Tiếng Việt chuẩn xác, tự nhiên.\n"
    "CHỈ THỊ QUAN TRỌNG: Hãy trả lời trực tiếp, ngắn gọn và đi thẳng vào trọng tâm câu hỏi của người dùng. Không giải thích lan man, dài dòng.\n"
    "Trình bày rõ ràng, dùng markdown để dễ đọc.\n"
    "Nếu bạn hoàn toàn không biết hoặc chưa học kiến thức này, hãy chỉ trả lời một câu duy nhất: '[SEARCH_REQUIRED]'. Không bịa đặt.\n\n"
    "{history}"
    "{context}"
    "Người dùng: {question}\n\n"
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
async def _save_chat_event(db: AsyncSession, current_user, request: AgentRequest,
                            answer: str, elapsed_ms: float) -> LearningEvent:
    from routers.rag import detect_topic
    topic = detect_topic(request.query)
    event = LearningEvent(
        user_id          = current_user.id if current_user else None,
        session_id       = request.session_id,
        question         = request.query,
        answer           = answer,
        topic            = topic,
        response_time_ms = elapsed_ms,
        model_used       = request.model_name or settings.ollama_model,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


# ── Wikipedia Fallback Search ──────────────────────────────────────────────────
def search_wikipedia(query: str) -> Optional[str]:
    import requests, re
    try:
        url = "https://vi.wikipedia.org/w/api.php"
        params = {
            "action": "query", "format": "json", "list": "search",
            "srsearch": query, "utf8": 1, "srlimit": 3
        }
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        snippets = []
        for item in data.get('query', {}).get('search', []):
            clean = re.sub('<[^<]+>', '', item['snippet'])
            snippets.append(clean)
        if snippets:
            return " ".join(snippets)
    except Exception:
        pass
    return None


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/direct")
async def direct_chat(
    request     : AgentRequest,
    db          : AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Chat trực tiếp với Ollama — có memory + feedback tracking."""
    try:
        llm   = get_llm(request.model_name, request.temperature or 0.1)
        start = time.time()

        # Xây dựng lịch sử hội thoại (tối đa 6 tin nhắn gần nhất)
        history_text = ""
        if request.messages:
            for msg in request.messages[-6:]:
                role = "Người dùng" if msg.get("role") == "user" else "Trợ lý"
                content = str(msg.get("content", ""))[:500]  # giới hạn độ dài
                history_text += f"{role}: {content}\n\n"

        history_block  = f"Lịch sử hội thoại:\n{history_text}" if history_text else ""
        calc_result    = try_calculate(request.query)
        context_block  = f"[Thông tin thêm: {calc_result}]\n\n" if calc_result else ""

        chain  = CHAT_PROMPT | llm | StrOutputParser()
        answer = chain.invoke({
            "history" : history_block,
            "context" : context_block,
            "question": request.query,
        })
        
        # Nếu AI không biết, gọi fallback Wikipedia
        if "[SEARCH_REQUIRED]" in answer:
            wiki_context = search_wikipedia(request.query)
            if wiki_context:
                context_block += f"[Thông tin từ Wikipedia (Google fallback): {wiki_context}]\n\n"
                # Xóa luật SEARCH_REQUIRED cho lần gọi thứ 2 để bắt buộc trả lời
                chain2 = PromptTemplate.from_template(
                    "Bạn là trợ lý AI thông minh.\n"
                    "CHỈ THỊ: Trả lời trực tiếp, ngắn gọn, đi thẳng vào trọng tâm bằng Tiếng Việt dựa trên thông tin được cung cấp.\n"
                    "BẮT BUỘC thêm dòng '*Nguồn: Tìm kiếm Internet (Wikipedia)*' ở cuối câu trả lời.\n\n"
                    "{history}{context}Người dùng: {question}\n\nTrả lời:"
                ) | llm | StrOutputParser()
                answer = chain2.invoke({
                    "history" : history_block,
                    "context" : context_block,
                    "question": request.query,
                })
            else:
                answer = "Xin lỗi, tôi chưa học kiến thức này và cũng không tìm thấy thông tin phù hợp trên internet (Google/Wikipedia)."

        elapsed_ms = round((time.time() - start) * 1000, 1)
        event      = await _save_chat_event(db, current_user, request, answer, elapsed_ms)

        return {
            "result"     : answer,
            "event_id"   : event.id,
            "response_ms": elapsed_ms,
            "model"      : request.model_name or settings.ollama_model,
            "suggestions": [],
        }

    except Exception as e:
        err = str(e)
        if "connection" in err.lower() or "refused" in err.lower() or "10061" in err:
            raise HTTPException(status_code=503,
                                detail="Ollama chua chay. Go lenh: ollama serve")
        raise HTTPException(status_code=500, detail=err)


@router.post("/research")
async def research_agent(
    request     : AgentRequest,
    db          : AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    return await direct_chat(request, db, current_user)
