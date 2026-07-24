"""Configuration management - Hỗ trợ cả Local Ollama và Free Cloud APIs (Groq/Gemini)."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional

from core.constants import APP_NAME, APP_VERSION
from core.enums import OperationMode

class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    app_name   : str = Field(default=APP_NAME)
    app_version: str = Field(default=APP_VERSION)
    debug      : bool = False
    operation_mode: OperationMode = Field(default=OperationMode.ONLINE)
    edge_gateway_port: int = 8080

    # ── Database (SQLite local hoặc PostgreSQL Cloud) ────────────────────────────
    database_url: str = "sqlite+aiosqlite:////tmp/completeai.db"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        # Nếu nhập nhầm biến môi trường Railway (dạng chữ chưa giải mã)
        if v and "${{" in v:
            return "sqlite+aiosqlite:///./completeai.db"
            
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v
    
    # ── Supabase / pgvector ───────────────────────────────────────────────────
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # ── AI Engine Configurations ──────────────────────────────────────────────
    llm_engine      : str = "gemini"  # 'groq', 'gemini', 'ollama'
    llm_model_name  : str = "gemini-2.5-flash" 
    
    # API Keys
    groq_api_key    : Optional[str] = None
    gemini_api_key  : Optional[str] = None
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: str = "gtcc-index"
    google_maps_api_key: Optional[str] = None
    
    # Ollama (Nếu dùng local)
    ollama_base_url : str = "http://localhost:11434"
    offline_model_name: str = "qwen2.5:3b"
    offline_fallback_model: str = "gemma2:2b"

    # Embeddings
    embedding_engine: str = "bge-m3" # Primary is bge-m3
    embedding_model : str = "BAAI/bge-m3"
    embedding_engine_offline: str = "huggingface"
    embedding_model_offline: str = "intfloat/multilingual-e5-small"

    # ── Auth ──────────────────────────────────────────────────────────────────
    secret_key                  : str
    access_token_expire_minutes : int = 1440     # 24 giờ

    # ── Vector Store & Logging ───────────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_db"
    log_dir           : str = "./logs"

    # ── Uploads ───────────────────────────────────────────────────────────────
    upload_dir      : str = "./uploads"
    max_upload_mb   : int = 50               # giới hạn kích thước file upload
    chunk_size      : int = 800             # chunk nhỏ hơn = chính xác hơn
    chunk_overlap   : int = 150              # overlap vừa phải

    # ── RAG ───────────────────────────────────────────────────────────────────
    rag_top_k    : int   = 8       # Tăng lên 8 để lấy nhiều ngữ cảnh hơn
    rag_threshold: float = 0.25    # Hạ ngưỡng để bắt được câu hỏi biến thể

    # ── Performance ───────────────────────────────────────────────────────────
    llm_timeout_seconds: int = 120   # timeout cho LLM call
    max_history_messages: int = 10   # số tin nhắn lịch sử giữ lại

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
