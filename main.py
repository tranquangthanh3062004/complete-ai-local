"""
Main FastAPI application entry point — CompleteAI v3.0
Dùng lifespan context manager (cách mới, không dùng @app.on_event deprecated).
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time
import uuid

from database import create_tables, seed_superuser
from routers import auth, rag, agents, learning


# ─── Lifespan (startup / shutdown) ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Chạy khi khởi động app: tạo bảng DB, seed admin, kiểm tra Ollama."""
    print("🚀 Đang khởi động CompleteAI v3.0...")
    await create_tables()
    await seed_superuser()

    # Kiểm tra Ollama khi startup
    from llm_factory import check_ollama_health
    health = check_ollama_health()
    if health["online"]:
        print(f"✅ Ollama online — models: {', '.join(health['models']) or 'none'}")
    else:
        print(f"⚠️  Ollama offline: {health['error']}")

    print("✅ CompleteAI sẵn sàng!")
    yield
    print("👋 Đang tắt CompleteAI...")


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "CompleteAI - Trợ Lý AI Cục Bộ",
    description = "Hệ thống AI hoàn toàn cục bộ, không cần API bên ngoài",
    version     = "3.0.0",
    lifespan    = lifespan,
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ─── Middleware: Request ID + Timing ──────────────────────────────────────────
@app.middleware("http")
async def add_request_metadata(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    response = await call_next(request)
    process_time = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"]    = request_id
    response.headers["X-Process-Time"]  = f"{process_time}ms"
    return response


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(rag.router)
app.include_router(agents.router)
app.include_router(learning.router)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health():
    """Kiểm tra backend có chạy không."""
    from llm_factory import check_ollama_health
    from config import settings

    h = check_ollama_health()
    return {
        "status"        : "healthy",
        "version"       : "3.0.0",
        "ollama_online" : h["online"],
        "ollama_models" : h["models"],
        "ollama_latency": f"{h['latency_ms']}ms",
        "active_model"  : settings.ollama_model,
        "error"         : h.get("error"),
    }


# ─── Models endpoint (cho UI dropdown) ────────────────────────────────────────
@app.get("/models", tags=["system"])
async def list_models():
    """Lấy danh sách model đang có trong Ollama."""
    from llm_factory import get_available_models
    from config import settings
    models = get_available_models()
    return {
        "models"       : models,
        "active_model" : settings.ollama_model,
        "total"        : len(models),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
