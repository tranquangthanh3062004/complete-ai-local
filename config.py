"""Configuration management - chỉ dùng Ollama local, không cần API bên ngoài."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    app_name   : str = "CompleteAI"
    app_version: str = "3.0.0"
    debug      : bool = False

    # ── Database (SQLite local - không cần server) ────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./completeai.db"

    # ── LLM - Ollama Local ONLY ───────────────────────────────────────────────
    ollama_base_url  : str = "http://localhost:11434"
    ollama_model     : str = "llama3.2"          # Đổi: mistral, qwen2, phi3, gemma3...
    ollama_embed_model: str = "nomic-embed-text" # Model embedding local (optional)

    # ── Auth ──────────────────────────────────────────────────────────────────
    secret_key                  : str = "super-secret-key-change-in-production-please"
    access_token_expire_minutes : int = 1440     # 24 giờ

    # ── Vector Store (local ChromaDB) ─────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_db"

    # ── Uploads ───────────────────────────────────────────────────────────────
    upload_dir      : str = "./data/uploads"
    max_upload_mb   : int = 50               # giới hạn kích thước file upload
    chunk_size      : int = 1000             # kích thước đoạn văn bản
    chunk_overlap   : int = 200              # overlap giữa các đoạn

    # ── RAG ───────────────────────────────────────────────────────────────────
    rag_top_k    : int   = 4       # số tài liệu lấy từ vector store
    rag_threshold: float = 0.3     # ngưỡng similarity tối thiểu

    # ── Performance ───────────────────────────────────────────────────────────
    llm_timeout_seconds: int = 120   # timeout cho LLM call
    max_history_messages: int = 10   # số tin nhắn lịch sử giữ lại

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"
        extra             = "ignore"   # Bỏ qua các biến env không khai báo


settings = Settings()
