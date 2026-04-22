"""
LLM Factory — CHỈ dùng Ollama local.
Không cần API key, không bao giờ hết hạn, chạy mãi.
Tối ưu: lazy-load, caching instance.
"""
import time
from typing import Optional

from langchain_ollama import OllamaLLM
from langchain_core.language_models import BaseLanguageModel
from config import settings

# ── Cache LLM instances (tránh tạo lại mỗi request) ─────────────────────────
_llm_cache: dict = {}


def get_llm(model_name: str = None, temperature: float = 0.1) -> BaseLanguageModel:
    """
    Trả về Ollama LLM với caching theo model_name.
    Chỉ dùng các tham số cơ bản, tương thích mọi phiên bản langchain_ollama.
    """
    name = model_name or settings.ollama_model
    cache_key = f"{name}_{temperature}"

    if cache_key not in _llm_cache:
        _llm_cache[cache_key] = OllamaLLM(
            base_url    = settings.ollama_base_url,
            model       = name,
            temperature = temperature,
        )
    return _llm_cache[cache_key]


def clear_llm_cache():
    """Xóa cache LLM (dùng khi cần reload model)."""
    _llm_cache.clear()


def get_available_models() -> list:
    """Lấy danh sách model đang có trong Ollama."""
    import httpx
    try:
        resp = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        if resp.status_code == 200:
            return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass
    return [settings.ollama_model]


def check_ollama_health() -> dict:
    """Kiểm tra Ollama có đang chạy không."""
    import httpx
    try:
        t0 = time.time()
        resp = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        latency_ms = round((time.time() - t0) * 1000)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            return {"online": True, "models": models, "latency_ms": latency_ms, "error": None}
    except httpx.ConnectError:
        return {"online": False, "models": [], "latency_ms": -1,
                "error": "Ollama chua chay. Mo terminal va chay: ollama serve"}
    except Exception as e:
        return {"online": False, "models": [], "latency_ms": -1, "error": str(e)}
    return {"online": False, "models": [], "latency_ms": -1, "error": "Unknown error"}
