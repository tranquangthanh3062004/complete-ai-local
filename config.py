"""Configuration management - Hỗ trợ cả Local Ollama và Free Cloud APIs (Groq/Gemini)."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    app_name   : str = "CompleteAI"
    app_version: str = "3.0.0"
    debug      : bool = False

    # ── Database (SQLite local hoặc PostgreSQL Cloud) ────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:YourPassword@db.yourproject.supabase.co:5432/postgres"
    
    # ── Supabase / pgvector ───────────────────────────────────────────────────
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # ── AI Engine Configurations ──────────────────────────────────────────────
    llm_engine      : str = "gemini" # 'groq', 'gemini', 'ollama'
    llm_model_name  : str = "gemini-1.5-flash" 
    
    # API Keys
    groq_api_key    : Optional[str] = None
    gemini_api_key  : Optional[str] = None
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: str = "gtcc-index"
    
    # Ollama (Nếu dùng local)
    ollama_base_url : str = "http://localhost:11434"

    # Embeddings
    embedding_engine: str = "gemini" # 'huggingface' or 'gemini'
    embedding_model : str = "models/text-embedding-004"

    # ── Auth ──────────────────────────────────────────────────────────────────
    secret_key                  : str = "super-secret-key-change-in-production-please"
    access_token_expire_minutes : int = 1440     # 24 giờ

    # ── Vector Store & Logging ───────────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_db"
    log_dir           : str = "./logs"

    # ── Uploads ───────────────────────────────────────────────────────────────
    upload_dir      : str = "./data/uploads"
    max_upload_mb   : int = 50               # giới hạn kích thước file upload
    chunk_size      : int = 800             # chunk nhỏ hơn = chính xác hơn
    chunk_overlap   : int = 150              # overlap vừa phải

    # ── RAG ───────────────────────────────────────────────────────────────────
    rag_top_k    : int   = 8       # Tăng lên 8 để lấy nhiều ngữ cảnh hơn
    rag_threshold: float = 0.25    # Hạ ngưỡng để bắt được câu hỏi biến thể

    # ── Performance ───────────────────────────────────────────────────────────
    llm_timeout_seconds: int = 120   # timeout cho LLM call
    max_history_messages: int = 10   # số tin nhắn lịch sử giữ lại

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"
        extra             = "ignore"   # Bỏ qua các biến env không khai báo


settings = Settings()
