"""
Language Detection Service v1.0 — GTCC Bot
Phát hiện ngôn ngữ câu hỏi để bot trả lời đúng tiếng (VI/EN).
"""
from logger import get_logger

logger = get_logger("lang_detect")


def detect_language(text: str) -> str:
    """
    Phát hiện ngôn ngữ của text.
    Returns: "vi", "en", hoặc "unknown"
    """
    # Bước 1: Heuristic nhanh — nếu có ký tự tiếng Việt đặc trưng → "vi"
    vi_chars = set("àáảãạăắặẳẵâấậẩẫđèéẻẽẹêếệểễìíỉĩịòóỏõọôốộổỗơớợởỡùúủũụưứựửữỳýỷỹỵ"
                   "ÀÁẢÃẠĂẮẶẲẴÂẤẬẨẪĐÈÉẺẼẸÊẾỆỂỄÌÍỈĨỊÒÓỎÕỌÔỐỘỔỖƠỚỢỞỠÙÚỦŨỤƯỨỰỬỮỲÝỶỸỴ")
    if any(c in vi_chars for c in text):
        return "vi"

    # Bước 2: Dùng langdetect nếu có
    try:
        from langdetect import detect, DetectorFactory  # type: ignore
        DetectorFactory.seed = 0  # Đảm bảo kết quả ổn định
        lang = detect(text)
        logger.debug(f"[LangDetect] Detected '{lang}' for: '{text[:50]}'")
        return lang
    except ImportError:
        logger.debug("[LangDetect] langdetect not installed — using heuristic only")
    except Exception as e:
        logger.debug(f"[LangDetect] Detection error: {e}")

    # Bước 3: Nếu toàn ASCII → khả năng cao là tiếng Anh
    if text.isascii():
        return "en"

    return "vi"  # Default tiếng Việt


def get_response_language_instruction(lang: str) -> str:
    """
    Trả về câu lệnh system để LLM phản hồi đúng ngôn ngữ.
    """
    if lang == "en":
        return "IMPORTANT: The user is asking in English. Please respond entirely in English."
    return ""  # Mặc định tiếng Việt đã có trong system prompt gốc


def build_multilingual_query(query: str) -> tuple[str, str]:
    """
    Phân tích ngôn ngữ và trả về (lang, lang_instruction).
    """
    lang = detect_language(query)
    instruction = get_response_language_instruction(lang)
    return lang, instruction
