"""
LLM Factory v5.1 — Hỗ trợ Cloud APIs (Groq, Gemini) và Local Ollama.
V5.1: Chuẩn hóa output (str), health check mạnh, available_models thực tế.
"""
from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import StrOutputParser
from config import settings

# System prompt chuyên biệt cho GTCC
GTCC_SYSTEM_PROMPT = """Bạn là trợ lý AI chuyên về Giao Thông Công Cộng (GTCC) tại Việt Nam.

NGUYÊN TẮC BẮT BUỘC (TUÂN THỦ 100%):
1. NGÔN NGỮ: Chỉ trả lời bằng Tiếng Việt chuẩn mực, tự nhiên, và lịch sự.
2. TRÌNH BÀY: Định dạng bằng Markdown sạch sẽ. Sử dụng danh sách (bullet points), in đậm các ý chính.
3. CHÍNH XÁC: Ưu tiên dữ liệu từ tài liệu được cung cấp (nếu có). Không bịa đặt thông tin.
4. NỘI DUNG: Nêu rõ tên/số hiệu tuyến, điểm đầu cuối, thời gian, giá vé.
5. KẾT THÚC: Có thể cung cấp thêm 1 gợi ý ứng dụng tra cứu uy tín (VD: BusMap, Google Maps) nếu phù hợp.
6. CẢM XÚC: Thêm một vài emoji cơ bản (🚌, 🚇, 🎫, 📍, ⏰) để câu trả lời thêm sinh động.
"""

# ── Singleton LLM instances ────────────────────────────────────────────────────
_llm_cache: dict = {}


def get_llm(model_name: str = None, temperature: float = 0.05) -> BaseLanguageModel:
    """
    Trả về LLM được cấu hình dựa trên file .env (Groq, Gemini hoặc Ollama).
    Cache instance để không khởi tạo lại mỗi request.
    """
    engine = settings.llm_engine.lower()
    name = model_name or settings.llm_model_name
    cache_key = f"{engine}:{name}:{temperature}"

    if cache_key in _llm_cache:
        return _llm_cache[cache_key]

    if engine == "groq":
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=name,
            temperature=temperature,
        )
    elif engine == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            google_api_key=settings.gemini_api_key,
            model=name,
            temperature=temperature,
        )
    else:
        # Local Ollama
        from langchain_ollama import OllamaLLM
        llm = OllamaLLM(
            base_url    = settings.ollama_base_url,
            model       = settings.ollama_model if not model_name else model_name,
            temperature = temperature,
            system      = GTCC_SYSTEM_PROMPT,
        )

    _llm_cache[cache_key] = llm
    return llm


def get_llm_creative(model_name: str = None) -> BaseLanguageModel:
    """LLM với temperature cao hơn cho các câu hỏi mở."""
    return get_llm(model_name, temperature=0.3)


def safe_invoke(llm, prompt: str) -> str:
    """
    Gọi LLM và chuẩn hóa output thành str dù là OllamaLLM hay ChatModel (AIMessage).
    """
    try:
        result = llm.invoke(prompt)
        # OllamaLLM trả về str trực tiếp
        if isinstance(result, str):
            return result.strip()
        # ChatGroq / ChatGemini trả về AIMessage
        if hasattr(result, "content"):
            return str(result.content).strip()
        return str(result).strip()
    except Exception as e:
        return ""


def check_health() -> dict:
    """Kiểm tra health của LLM Engine đang dùng."""
    engine = settings.llm_engine.lower()
    if engine == "groq":
        ok = bool(settings.groq_api_key and settings.groq_api_key != "your_groq_api_key_here")
        return {
            "online" : ok,
            "engine" : "Groq",
            "models" : [settings.llm_model_name],
            "latency_ms": 0,
            "error"  : None if ok else "Missing or invalid GROQ_API_KEY in .env",
        }
    elif engine == "gemini":
        ok = bool(settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here")
        return {
            "online" : ok,
            "engine" : "Gemini",
            "models" : [settings.llm_model_name],
            "latency_ms": 0,
            "error"  : None if ok else "Missing or invalid GEMINI_API_KEY in .env",
        }
    else:
        # Ollama: ping /api/tags
        import httpx, time
        try:
            t0 = time.time()
            resp = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
            latency = round((time.time() - t0) * 1000)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                return {
                    "online"    : True,
                    "engine"    : "Ollama",
                    "models"    : models or [settings.ollama_model],
                    "latency_ms": latency,
                    "error"     : None,
                }
            return {"online": False, "engine": "Ollama", "models": [], "latency_ms": latency, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"online": False, "engine": "Ollama", "models": [], "latency_ms": 0, "error": str(e)}


def get_available_models() -> list:
    """Trả về danh sách model có sẵn."""
    h = check_health()
    return h.get("models", [settings.llm_model_name])


# Backward compatibility aliases
check_ollama_health  = check_health
check_ollama_online  = lambda: check_health().get("online", False)
