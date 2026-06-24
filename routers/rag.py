"""
RAG Router v4.0 — Chatbot Giao Thông Công Cộng (GTCC)
Chủ đề: Hỏi đáp về xe buýt, metro, BRT, luật giao thông, lịch trình...
Tính năng:
  - Hỗ trợ .pdf, .docx, .txt
  - Highlight đoạn trích nguồn
  - Xóa tài liệu khỏi ChromaDB
  - LearningEvent tracking
  - Topic detection chuyên về GTCC
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import os, shutil, time

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from rate_limiter import limiter
from config import settings
from database import get_db
from routers.auth import get_current_user
from models import User, Document, LearningEvent, TopicMastery
from llm_factory import get_llm
from logger import get_logger

router = APIRouter(prefix="/documents", tags=["rag"])
logger = get_logger("rag")

# ── Supported file types ──────────────────────────────────────────────────────
SUPPORTED_TYPES = {".pdf", ".txt", ".docx"}

# ── Embeddings (lazy load + cache) ────────────────────────────────────────────
_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        if settings.embedding_engine == "gemini" and settings.gemini_api_key:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            logger.info("Loading Google Gemini Embeddings...")
            _embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.embedding_model, 
                google_api_key=settings.gemini_api_key
            )
        else:
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
                logger.info(f"Loading local embeddings...")
                _embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={"device": "cpu"}
                )
            except ImportError:
                raise Exception("Missing HuggingFaceEmbeddings. Set gemini_api_key or install sentence-transformers.")
    return _embeddings

# ── Vector Store (Supabase pgvector hoặc ChromaDB) ────────────────────────────
_vector_store_instance = None

def get_vector_store():
    global _vector_store_instance
    if _vector_store_instance is None:
        embeddings = get_embeddings()
        
        # 1. Pinecone
        if settings.pinecone_api_key:
            try:
                from langchain_pinecone import PineconeVectorStore
                logger.info("Initializing Pinecone Vector Store...")
                _vector_store_instance = PineconeVectorStore(
                    index_name=settings.pinecone_index_name,
                    embedding=embeddings,
                    pinecone_api_key=settings.pinecone_api_key
                )
                return _vector_store_instance
            except ImportError:
                logger.error("Missing pinecone packages.")

        # 2. Supabase pgvector
        if settings.supabase_url and settings.supabase_key:
            try:
                from supabase.client import create_client
                from langchain_community.vectorstores import SupabaseVectorStore
                logger.info("Initializing Supabase Vector Store...")
                supabase_client = create_client(settings.supabase_url, settings.supabase_key)
                _vector_store_instance = SupabaseVectorStore(
                    embedding=embeddings,
                    client=supabase_client,
                    table_name="documents",
                    query_name="match_documents"
                )
                return _vector_store_instance
            except ImportError:
                logger.error("Missing supabase package.")
                
        # 3. Fallback (không dùng Chroma trên serverless)
        raise Exception("Không tìm thấy cấu hình Vector Database (Pinecone/Supabase)!")
            
    return _vector_store_instance


# ── Topic Detection - Chuyên về GTCC ─────────────────────────────────────────
TOPIC_KEYWORDS = {
    "xe_buyt": [
        "xe buýt", "xe buyt", "bus", "tuyến buýt", "tuyen buyt", "bến xe",
        "trạm xe buýt", "tram xe buyt", "vé xe buýt", "ve xe buyt",
        "giờ xe buýt", "lịch xe buýt", "lich xe buyt", "số tuyến", "so tuyen",
        "xe bus", "minibus", "transerco", "ttqlgtcc",
    ],
    "metro_tau_dien": [
        "metro", "tàu điện", "tau dien", "đường sắt đô thị", "duong sat do thi",
        "mrt", "lrt", "tàu ngầm", "tau ngam", "ga metro", "cát linh",
        "cat linh", "hà đông", "ha dong", "nhổn", "nhon", "bến thành",
        "ben thanh", "suối tiên", "suoi tien", "tuyến metro", "tuyen metro",
        "tàu điện ngầm", "mrb", "vml",
    ],
    "brt_xe_buyt_nhanh": [
        "brt", "xe buýt nhanh", "xe buyt nhanh", "bus rapid transit",
        "kim mã", "kim ma", "yên nghĩa", "yen nghia", "làn đường riêng",
        "lan duong rieng",
    ],
    "ve_gia_cuoc": [
        "giá vé", "gia ve", "vé tháng", "ve thang", "vé ngày", "ve ngay",
        "học sinh sinh viên", "hoc sinh sinh vien", "miễn phí", "mien phi",
        "ưu đãi", "uu dai", "giảm giá", "giam gia", "thanh toán", "thanh toan",
        "mua vé", "mua ve", "thẻ xe buýt", "the xe buyt",
    ],
    "lich_trinh_tuyen": [
        "lịch trình", "lich trinh", "giờ chạy", "gio chay", "giờ mở cửa",
        "gio mo cua", "tần suất", "tan suat", "chuyến đầu", "chuyen dau",
        "chuyến cuối", "chuyen cuoi", "lộ trình", "lo trinh", "tuyến đường",
        "tuyen duong", "đón trả khách", "don tra khach",
    ],
    "luat_quy_dinh": [
        "luật", "luat", "quy định", "quy dinh", "nghị định", "nghi dinh",
        "vi phạm", "vi pham", "xử phạt", "xu phat", "phạt tiền", "phat tien",
        "đèn đỏ", "den do", "tốc độ", "toc do", "mũ bảo hiểm", "mu bao hiem",
        "nồng độ cồn", "nong do con", "bằng lái", "bang lai", "giấy phép",
        "giay phep", "luật giao thông", "luat giao thong",
    ],
    "giao_thong_duong_thuy": [
        "buýt sông", "buyt song", "phà", "pha", "tàu thủy", "tau thuy",
        "đường thủy", "duong thuy", "bến phà", "ben pha", "sông sài gòn",
        "song sai gon", "cần giờ", "can gio",
    ],
    "ung_dung_tien_ich": [
        "busmap", "imaas", "ứng dụng", "ung dung", "app", "google maps",
        "tra cứu", "tra cuu", "thông tin tuyến", "thong tin tuyen",
        "thẻ thông minh", "the thong minh", "thanh toán điện tử",
        "thanh toan dien tu", "qr code", "mã qr",
    ],
    "xe_dap_xe_may_chia_se": [
        "xe đạp chia sẻ", "xe dap chia se", "xe máy điện chia sẻ",
        "xe may dien chia se", "tnego", "ecobike", "mobike", "grab bike",
        "xe điện", "xe dien",
    ],
    "san_bay_ga_tau": [
        "sân bay", "san bay", "tân sơn nhất", "tan son nhat", "nội bài",
        "noi bai", "ga tàu", "ga tau", "từ sân bay", "tu san bay",
        "đến trung tâm", "den trung tam",
    ],
}

def detect_topic(text: str) -> str:
    text_lower = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return topic
    return "gtcc_chung"

# Tên hiển thị topic đẹp hơn
TOPIC_DISPLAY = {
    "xe_buyt": "🚌 Xe Buýt",
    "metro_tau_dien": "🚇 Metro / Tàu Điện",
    "brt_xe_buyt_nhanh": "🚍 BRT - Xe Buýt Nhanh",
    "ve_gia_cuoc": "🎫 Vé & Giá Cước",
    "lich_trinh_tuyen": "🗓️ Lịch Trình / Tuyến",
    "luat_quy_dinh": "📋 Luật & Quy Định",
    "giao_thong_duong_thuy": "⛵ Giao Thông Đường Thủy",
    "ung_dung_tien_ich": "📱 Ứng Dụng & Tiện Ích",
    "xe_dap_xe_may_chia_se": "🛵 Xe Đạp / Xe Máy Chia Sẻ",
    "san_bay_ga_tau": "✈️ Sân Bay & Nhà Ga",
    "gtcc_chung": "🚦 GTCC Chung",
}


# ── Schemas ───────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query     : str
    model_name: Optional[str] = None
    session_id: Optional[str] = "default"
    suggest   : Optional[bool] = False


class ChatResponse(BaseModel):
    response   : str
    event_id   : int
    topic      : str
    sources    : list[str] = []
    excerpts   : list[str] = []    # đoạn trích trực tiếp từ tài liệu
    suggestions: list[str] = []    # gợi ý câu hỏi tiếp theo


# ── RAG Prompt - Chuyên về GTCC (v3.0 - Tối ưu độ chính xác) ─────────────────
RAG_PROMPT = ChatPromptTemplate.from_template("""Bạn là Trợ lý GTCC (Giao Thông Công Cộng) chuyên nghiệp Việt Nam.

TÀI LIỆU THAM KHẢO:
{context}

CÂU HỎI: {question}

HƯỚNG DẪN TRẢ LỜI:
- Trả lời HOÀN TOÀN bằng Tiếng Việt, rõ ràng, có cấu trúc
- Dùng thông tin từ tài liệu ở trên (ưu tiên cao nhất)
- Với lộ trình/tuyến: ghi rõ số tuyến, điểm đầu-cuối, giờ chạy, giá vé
- Với giá vé: ghi rõ đơn vị đồng/VNĐ, phân loại (lượt/ngày/tháng/SV)
- Dùng emoji phù hợp: 🚌 xe buýt, 🚇 metro, 🎫 vé, 📍 địa điểm, ⏰ giờ
- Nếu không tìm thấy thông tin: nói rõ và gợi ý dùng BusMap/Go!Bus/Tìm Buýt

TRẢ LỜI:""")

def format_docs(docs):
    return "\n\n---\n\n".join(
        f"[Nguồn: {os.path.basename(d.metadata.get('source', d.metadata.get('file_path', 'GTCC Data')))}]\n{d.page_content}"
        for d in docs
    )


# ── Upload PDF / DOCX / TXT ───────────────────────────────────────────────────
@router.post("/upload/")
async def upload_document(
    file        : UploadFile = File(...),
    db          : AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Chỉ hỗ trợ: {', '.join(SUPPORTED_TYPES)}. File của bạn: {ext}"
        )

    # Kiểm tra kích thước
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File quá lớn ({size_mb:.1f}MB). Giới hạn: {settings.max_upload_mb}MB"
        )

    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, file.filename)

    with open(file_path, "wb") as buf:
        buf.write(content)

    try:
        # ── Load theo loại file ──
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
            docs   = loader.load()
        elif ext == ".txt":
            loader = TextLoader(file_path, encoding="utf-8")
            docs   = loader.load()
        elif ext == ".docx":
            try:
                from langchain_community.document_loaders import Docx2txtLoader
                loader = Docx2txtLoader(file_path)
                docs   = loader.load()
            except ImportError:
                raise HTTPException(
                    status_code=400,
                    detail="Cần cài thêm: pip install docx2txt"
                )
        else:
            raise HTTPException(status_code=400, detail="Loại file không hỗ trợ")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size    = settings.chunk_size,
            chunk_overlap = settings.chunk_overlap,
        )
        chunks = splitter.split_documents(docs)

        vectordb = get_vector_store()
        vectordb.add_documents(chunks)

        doc = Document(
            user_id  = current_user.id if current_user else None,
            filename = file.filename,
            content  = f"{len(chunks)} chunks indexed",
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        return {
            "message" : f"✅ Đã xử lý tài liệu GTCC '{file.filename}' — {len(chunks)} đoạn văn bản",
            "doc_id"  : doc.id,
            "chunks"  : len(chunks),
            "pages"   : len(docs),
            "size_mb" : round(size_mb, 2),
        }
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ── Chat với tài liệu GTCC ────────────────────────────────────────────────────
@router.post("/chat/", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(
    request     : Request,
    payload     : ChatRequest,
    db          : AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    # ── 1. Sanitize input ──────────────────────────────────────────────────────
    from services.sanitizer import sanitize_query
    clean_query, is_safe, reason = sanitize_query(payload.query)
    if not is_safe:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=reason)

    # ── 2. Cache check ─────────────────────────────────────────────────────────
    from services.cache_service import get_rag_cache
    from services.lang_detect import build_multilingual_query
    cache = get_rag_cache()
    cached = cache.get(clean_query)
    if cached:
        logger.info(f"[RAG Cache HIT] Q: '{clean_query[:60]}'")
        elapsed = 0
        event = await _save_event(db, current_user, payload, cached,
                                  detect_topic(clean_query), elapsed)
        return ChatResponse(
            response    = cached,
            event_id    = event.id,
            topic       = TOPIC_DISPLAY.get(detect_topic(clean_query), "🚦 GTCC Chung"),
            sources     = [],
            excerpts    = [],
            suggestions = _get_gtcc_suggestions(detect_topic(clean_query)),
        )

    topic = detect_topic(clean_query)
    lang, lang_instruction = build_multilingual_query(clean_query)
    llm   = get_llm(payload.model_name)
    start = time.time()

    # ── 3. Kiểm tra Vector Store có data chưa ─────────────────────────────────
    vectordb = get_vector_store()
    try:
        probe_docs = vectordb.similarity_search(clean_query, k=1)
        has_data   = bool(probe_docs)
    except Exception:
        has_data = False

    # ── 4. Fallback khi chưa có dữ liệu RAG ───────────────────────────────────
    if not has_data:
        fallback_answer = (
            "📋 **Chưa có tài liệu GTCC trong hệ thống.**\n\n"
            "Bạn có thể upload file PDF/TXT/DOCX tại tab **📁 Tài Liệu** để bot học thêm.\n"
            "Hoặc hỏi trực tiếp tại tab **💬 Hỏi AI Trực Tiếp** để tôi trả lời từ kiến thức chung."
        )
        try:
            system = lang_instruction + "\nBạn là trợ lý GTCC Việt Nam. Trả lời ngắn gọn." if lang_instruction else "Bạn là trợ lý GTCC Việt Nam. Trả lời ngắn gọn bằng tiếng Việt."
            answer = llm.invoke(f"{system}\nCâu hỏi: {clean_query}")
            if isinstance(answer, str):
                answer = answer.strip()
            # langchain trả về AIMessage
            if hasattr(answer, "content"):
                answer = answer.content.strip()
            if not answer:
                answer = fallback_answer
        except Exception:
            answer = fallback_answer

        elapsed = (time.time() - start) * 1000
        event   = await _save_event(db, current_user, payload, answer, topic, elapsed)
        return ChatResponse(response=answer, event_id=event.id, topic=TOPIC_DISPLAY.get(topic, topic))

    # ── 5. Thực hiện RAG ───────────────────────────────────────────────────────
    try:
        retriever = vectordb.as_retriever(search_kwargs={"k": settings.rag_top_k})

        # Lấy source docs trước (1 lần duy nhất, tái dùng cho cả chain và excerpt)
        source_docs = retriever.invoke(clean_query)
        context_text = format_docs(source_docs)

        # Thêm language instruction nếu cần
        if lang_instruction:
            context_text = lang_instruction + "\n\n" + context_text

        # Build chain dùng context đã có (không gọi retriever thêm lần nữa)
        from langchain_core.prompts import ChatPromptTemplate
        prompt_with_context = ChatPromptTemplate.from_template(
            RAG_PROMPT.messages[0].prompt.template if hasattr(RAG_PROMPT, 'messages') else str(RAG_PROMPT)
        )
        answer = (RAG_PROMPT | llm | StrOutputParser()).invoke({
            "context" : context_text,
            "question": clean_query,
        })
        elapsed = (time.time() - start) * 1000

        if not answer or not answer.strip():
            answer = "⚠️ Chưa tìm thấy thông tin phù hợp trong tài liệu. Hãy thử hỏi tab 💬 Hỏi AI."

        sources  = list({
            os.path.basename(d.metadata.get("source", d.metadata.get("file_path", "")))
            for d in source_docs
            if d.metadata.get("source") or d.metadata.get("file_path")
        })
        excerpts = [d.page_content[:250] + "..." for d in source_docs[:3]]
        suggestions = _get_gtcc_suggestions(topic)

        # Lưu vào cache
        cache.set(clean_query, answer)

        event = await _save_event(db, current_user, payload, answer, topic, elapsed)
        await _update_topic_count(db, current_user.id if current_user else None, topic)

        logger.info(f"[RAG Chat] lang={lang} | Q: '{clean_query[:60]}' | Topic: {topic} | Sources: {len(sources)} | Time: {elapsed:.0f}ms")

        return ChatResponse(
            response    = answer,
            event_id    = event.id,
            topic       = TOPIC_DISPLAY.get(topic, topic),
            sources     = sources,
            excerpts    = excerpts,
            suggestions = suggestions,
        )

    except Exception as e:
        err = str(e)
        logger.error(f"Error in RAG chat: {err}", exc_info=True)
        if "connection" in err.lower() or "refused" in err.lower() or "10061" in err:
            raise HTTPException(status_code=503, detail="Ollama/LLM chưa chạy hoặc mất kết nối.")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý RAG: {err}")



def _get_gtcc_suggestions(topic: str) -> list:
    """Gợi ý câu hỏi tiếp theo theo chủ đề GTCC."""
    suggestions_map = {
        "xe_buyt": [
            "Giá vé xe buýt TP.HCM là bao nhiêu?",
            "Học sinh có được giảm giá vé không?",
            "Làm sao mua vé tháng xe buýt?",
        ],
        "metro_tau_dien": [
            "Metro số 1 TP.HCM có những ga nào?",
            "Giờ chạy của metro Cát Linh - Hà Đông?",
            "Giá vé metro là bao nhiêu?",
        ],
        "ve_gia_cuoc": [
            "Ai được miễn phí vé xe buýt?",
            "Mua vé tháng ở đâu?",
            "Thanh toán vé điện tử được không?",
        ],
        "luat_quy_dinh": [
            "Vi phạm vượt đèn đỏ bị phạt bao nhiêu?",
            "Quy định về nồng độ cồn khi lái xe?",
            "Quy định đi xe buýt có gì?",
        ],
        "san_bay_ga_tau": [
            "Đi từ sân bay Nội Bài vào trung tâm Hà Nội bằng gì?",
            "Có xe buýt từ sân bay Tân Sơn Nhất không?",
            "Giá taxi sân bay so với xe buýt?",
        ],
    }
    default = [
        "Xe buýt tuyến nào đi qua trung tâm?",
        "Làm thế nào để tra cứu lộ trình GTCC?",
        "App nào hỗ trợ đi xe buýt tốt nhất?",
    ]
    return suggestions_map.get(topic, default)


# ── Danh sách tài liệu ────────────────────────────────────────────────────────
@router.get("/list/")
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc()).limit(50)
    )
    docs = result.scalars().all()
    return [
        {
            "id"        : d.id,
            "filename"  : d.filename,
            "content"   : d.content,
            "created_at": str(d.created_at),
        }
        for d in docs
    ]


# ── Xóa tài liệu ─────────────────────────────────────────────────────────────
@router.delete("/delete/{doc_id}")
async def delete_document(
    doc_id      : int,
    db          : AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Xóa tài liệu khỏi DB."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

    await db.delete(doc)
    await db.commit()
    return {"message": f"✅ Đã xóa '{doc.filename}' khỏi danh sách"}


# ── Helpers ───────────────────────────────────────────────────────────────────
async def _save_event(db, current_user, payload, answer, topic, elapsed):
    event = LearningEvent(
        user_id          = current_user.id if current_user else None,
        session_id       = payload.session_id,
        question         = payload.query,
        answer           = answer,
        topic            = topic,
        response_time_ms = elapsed,
        model_used       = payload.model_name or settings.llm_model_name,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def _update_topic_count(db, user_id, topic):
    result = await db.execute(
        select(TopicMastery).where(
            TopicMastery.user_id == user_id,
            TopicMastery.topic   == topic,
        )
    )
    mastery = result.scalar_one_or_none()
    if mastery is None:
        mastery = TopicMastery(
            user_id=user_id, topic=topic,
            total_questions=0, positive_feedback=0,
            negative_feedback=0, mastery_score=0.5,
        )
        db.add(mastery)
    mastery.total_questions += 1
    from datetime import datetime
    mastery.last_updated = datetime.utcnow()
    await db.commit()
