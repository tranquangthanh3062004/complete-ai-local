"""
RAG Router v3.0 — Upload nhiều loại file, Chat với tài liệu qua Ollama local.
Tính năng mới:
  - Hỗ trợ .pdf, .docx, .txt (Feature 3.1)
  - Highlight đoạn trích nguồn (Feature 3.4)
  - Xóa tài liệu khỏi ChromaDB (Feature 3.3)
  - LearningEvent tracking
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import os, shutil, time

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from config import settings
from database import get_db
from routers.auth import get_current_user
from models import User, Document, LearningEvent, TopicMastery
from llm_factory import get_llm

router = APIRouter(prefix="/documents", tags=["rag"])

# ── Supported file types ──────────────────────────────────────────────────────
SUPPORTED_TYPES = {".pdf", ".txt", ".docx"}

# ── Embeddings (lazy load + cache) ────────────────────────────────────────────
_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="keepitreal/vietnamese-sbert",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


# ── Topic Detection ───────────────────────────────────────────────────────────
TOPIC_KEYWORDS = {
    "luat": [
        "luat", "dieu", "khoan", "quy dinh", "nghi dinh", "thong tu", "phap ly",
        "luật", "điều", "khoản", "quy định", "nghị định", "thông tư", "pháp lý",
    ],
    "ky thuat": [
        "lap trinh", "code", "python", "api", "server", "database", "ham", "thuat toan",
        "lập trình", "hàm", "thuật toán", "javascript", "react", "docker",
    ],
    "toan": [
        "tinh", "phuong trinh", "so hoc", "xac suat", "dao ham", "tich phan",
        "tính", "phương trình", "số học", "xác suất", "đạo hàm", "tích phân",
        "thống kê", "ma trận",
    ],
    "y te": [
        "benh", "thuoc", "trieu chung", "chan doan", "suc khoe",
        "bệnh", "thuốc", "triệu chứng", "chẩn đoán", "sức khỏe", "y tế", "bác sĩ",
    ],
    "kinh te": [
        "kinh doanh", "tai chinh", "dau tu", "thi truong", "loi nhuan",
        "tài chính", "đầu tư", "thị trường", "lợi nhuận", "kinh tế", "ngân hàng",
    ],
    "lich su": [
        "lich su", "chien tranh", "trieu dai", "su kien",
        "lịch sử", "chiến tranh", "triều đại", "sự kiện", "lịch sử",
    ],
    "khoa hoc": [
        "vật lý", "hóa học", "sinh học", "thiên văn", "khoa học", "nghiên cứu",
        "physics", "chemistry", "biology", "science",
    ],
}

def detect_topic(text: str) -> str:
    text_lower = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return topic
    return "general"


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


# ── RAG Prompt ────────────────────────────────────────────────────────────────
RAG_PROMPT = ChatPromptTemplate.from_template("""Bạn là trợ lý AI thông minh. Hãy trả lời câu hỏi DỰA TRÊN nội dung tài liệu dưới đây.
Nếu tài liệu không có thông tin liên quan, hãy nói rõ là không tìm thấy trong tài liệu.
CHỈ THỊ QUAN TRỌNG: Chỉ trích xuất những thông tin phục vụ trực tiếp cho việc trả lời câu hỏi. Trả lời ngắn gọn, đi thẳng vào trọng tâm và tuyệt đối KHÔNG phân tích lan man hay thêm các thông tin thừa.
Trả lời bằng Tiếng Việt, rõ ràng và chính xác. Dùng markdown để trình bày.
BẮT BUỘC phải thêm dòng '*Nguồn: Dữ liệu từ tài liệu upload*' ở cuối câu trả lời nếu tìm thấy thông tin.

Tài liệu tham khảo:
{context}

Câu hỏi: {question}

Trả lời:""")

def format_docs(docs):
    return "\n\n---\n\n".join(
        f"[Nguồn: {os.path.basename(d.metadata.get('source', d.metadata.get('file_path', 'unknown')))}]\n{d.page_content}"
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

        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        vectordb = Chroma(
            persist_directory  = settings.chroma_persist_dir,
            embedding_function = get_embeddings(),
        )
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
            "message" : f"✅ Đã xử lý '{file.filename}' — {len(chunks)} đoạn văn bản",
            "doc_id"  : doc.id,
            "chunks"  : len(chunks),
            "pages"   : len(docs),
            "size_mb" : round(size_mb, 2),
        }
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ── Chat với tài liệu ─────────────────────────────────────────────────────────
@router.post("/chat/", response_model=ChatResponse)
async def chat(
    request     : ChatRequest,
    db          : AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    llm   = get_llm(request.model_name)
    topic = detect_topic(request.query)
    start = time.time()

    chroma_dir = settings.chroma_persist_dir

    if not os.path.exists(chroma_dir):
        answer  = llm.invoke(request.query)
        elapsed = (time.time() - start) * 1000
        event   = await _save_event(db, current_user, request, answer, topic, elapsed)
        return ChatResponse(response=answer, event_id=event.id, topic=topic)

    try:
        vectordb  = Chroma(
            persist_directory  = chroma_dir,
            embedding_function = get_embeddings(),
        )
        retriever = vectordb.as_retriever(
            search_kwargs={"k": settings.rag_top_k}
        )

        # LCEL chain
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | RAG_PROMPT
            | llm
            | StrOutputParser()
        )

        answer  = rag_chain.invoke(request.query)
        elapsed = (time.time() - start) * 1000

        # Lấy nguồn và đoạn trích
        source_docs = retriever.invoke(request.query)
        sources = list({
            os.path.basename(d.metadata.get("source", d.metadata.get("file_path", "")))
            for d in source_docs
            if d.metadata.get("source") or d.metadata.get("file_path")
        })
        excerpts = [d.page_content[:200] + "..." for d in source_docs[:2]]

        event = await _save_event(db, current_user, request, answer, topic, elapsed)
        await _update_topic_count(db, current_user.id if current_user else None, topic)

        return ChatResponse(
            response    = answer,
            event_id    = event.id,
            topic       = topic,
            sources     = sources,
            excerpts    = excerpts,
            suggestions = [],
        )

    except Exception as e:
        err = str(e)
        if "connection" in err.lower() or "refused" in err.lower() or "10061" in err:
            raise HTTPException(status_code=503, detail="Ollama chưa chạy hoặc mất kết nối. Hãy kiểm tra lại.")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý RAG: {err}")


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
    """Xóa tài liệu khỏi DB (ChromaDB không xóa được dễ, chỉ xóa record)."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

    await db.delete(doc)
    await db.commit()
    return {"message": f"✅ Đã xóa '{doc.filename}' khỏi danh sách"}


# ── Helpers ───────────────────────────────────────────────────────────────────
async def _save_event(db, current_user, request, answer, topic, elapsed):
    event = LearningEvent(
        user_id          = current_user.id if current_user else None,
        session_id       = request.session_id,
        question         = request.query,
        answer           = answer,
        topic            = topic,
        response_time_ms = elapsed,
        model_used       = request.model_name or settings.ollama_model,
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
