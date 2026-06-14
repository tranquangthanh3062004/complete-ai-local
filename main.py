"""
Main FastAPI application entry point — GTCC Bot v5.1
Chatbot hoi dap ve Giao Thong Cong Cong Viet Nam.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
import time
import uuid

from database import create_tables, seed_superuser
from routers import auth, rag, agents, learning
from logger import get_logger

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khoi dong app: tao bang DB, seed admin, kiem tra Ollama."""
    logger.info("🚌 Dang khoi dong GTCC Bot v4.0...")
    await create_tables()
    await seed_superuser()

    from llm_factory import check_health
    health = check_health()
    engine = health.get("engine", "Ollama")
    if health["online"]:
        logger.info(f"✅ {engine} Engine online")
    else:
        logger.warning(f"⚠️  {engine} offline / Lỗi API: {health['error']}")
        logger.warning("   Bot van hoat dong voi fallback GTCC co ban.")

    logger.info("✅ GTCC Bot san sang phuc vu!")
    yield
    logger.info("👋 Dang tat GTCC Bot...")


app = FastAPI(
    title       = "GTCC Bot - Chatbot Giao Thong Cong Cong Viet Nam",
    description = "He thong AI hoi dap ve Giao Thong Cong Cong: Xe Buyt, Metro, BRT, Luat GT...",
    version     = "5.1.0",
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


@app.middleware("http")
async def add_request_metadata(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"Incoming request: {request.method} {request.url.path} (ID: {request_id})")
    
    response = await call_next(request)
    
    process_time = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"]   = request_id
    response.headers["X-Process-Time"] = f"{process_time}ms"
    
    # Log completed request
    logger.info(f"Completed request: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time}ms (ID: {request_id})")
    return response


app.include_router(auth.router)
app.include_router(rag.router)
app.include_router(agents.router)
app.include_router(learning.router)


@app.get("/health", tags=["system"])
async def health():
    """Kiem tra backend co chay khong."""
    from llm_factory import check_health
    from config import settings
    h = check_health()
    return {
        "status"        : "healthy",
        "version"       : "5.1.0",
        "app_name"      : "GTCC Bot v5.1 — Giao Thong Cong Cong",
        "engine"        : h.get("engine", "Ollama"),
        "llm_online"    : h["online"],
        "ollama_online" : h["online"],   # backward compat
        "ollama_models" : h.get("models", []),
        "ollama_latency": f"{h.get('latency_ms', 0)}ms",
        "active_model"  : settings.llm_model_name,
        "fallback_mode" : not h["online"],
        "error"         : h.get("error"),
    }


@app.get("/models", tags=["system"])
async def list_models():
    """Lay danh sach model dang co trong LLM engine."""
    from llm_factory import get_available_models, check_health
    from config import settings
    models = get_available_models()
    h = check_health()
    return {
        "models"      : models,
        "engine"      : h.get("engine", "Ollama"),
        "active_model": settings.llm_model_name,
        "total"       : len(models),
    }


@app.post("/tts", tags=["utility"])
async def text_to_speech_endpoint(request: Request):
    """
    Chuyen van ban thanh file audio MP3 (gTTS).
    Body: {"text": "...", "lang": "vi"}
    """
    try:
        body = await request.json()
        text = body.get("text", "").strip()
        lang = body.get("lang", "vi")
        if not text:
            return JSONResponse(status_code=400, content={"error": "text is required"})
        if len(text) > 1500:
            text = text[:1500]

        from services.tts_service import text_to_speech
        audio_path = text_to_speech(text, lang=lang)
        if audio_path:
            return FileResponse(
                path=audio_path,
                media_type="audio/mpeg",
                filename="gtcc_tts.mp3",
            )
        return JSONResponse(status_code=503, content={"error": "TTS unavailable. Install gtts: pip install gtts"})
    except Exception as e:
        logger.error(f"TTS endpoint error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/cache-stats", tags=["system"])
async def cache_stats():
    """Thong ke cache hien tai."""
    from services.cache_service import get_agent_cache, get_rag_cache
    return {
        "agent_cache" : get_agent_cache().stats,
        "rag_cache"   : get_rag_cache().stats,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
