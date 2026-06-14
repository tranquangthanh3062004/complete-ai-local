"""
TTS Service v1.0 — Text-to-Speech cho GTCC Bot
Dùng gTTS (Google TTS) để đọc câu trả lời tiếng Việt.
Fallback: pyttsx3 nếu không có internet.
"""
import os
import hashlib
import tempfile
from pathlib import Path
from logger import get_logger

logger = get_logger("tts_service")

# Thư mục cache audio
TTS_CACHE_DIR = Path("./data/tts_cache")
TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Giới hạn text (gTTS có thể handle ~5000 ký tự)
MAX_TTS_LENGTH = 800


def _clean_text_for_tts(text: str) -> str:
    """Làm sạch text: bỏ markdown, emoji, link để đọc mượt hơn."""
    import re
    # Bỏ markdown bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # Bỏ link markdown
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    # Bỏ emoji (Unicode ranges)
    text = re.sub(
        r'[\U00010000-\U0010ffff'
        r'\U0001F600-\U0001F64F'
        r'\U0001F300-\U0001F5FF'
        r'\U0001F680-\U0001F6FF'
        r'\U0001F1E0-\U0001F1FF'
        r'\u2600-\u26FF\u2700-\u27BF]+',
        '', text, flags=re.UNICODE
    )
    # Bỏ dòng trống liên tiếp
    text = re.sub(r'\n{2,}', '\n', text)
    # Chỉ giữ 800 ký tự đầu
    return text[:MAX_TTS_LENGTH].strip()


def generate_tts_edge(text: str, lang: str = "vi") -> str | None:
    """
    Dùng edge-tts (Microsoft) để tạo file audio MP3.
    Giọng chuẩn, tự nhiên hơn gTTS rất nhiều.
    """
    try:
        import asyncio
        import edge_tts  # type: ignore

        clean = _clean_text_for_tts(text)
        if not clean:
            return None

        # Dùng hash để cache — cùng câu → cùng file
        cache_key = hashlib.md5(f"edge:{lang}:{clean}".encode()).hexdigest()
        cache_path = TTS_CACHE_DIR / f"{cache_key}.mp3"

        if cache_path.exists():
            logger.info(f"[TTS] Cache hit: {cache_key}")
            return str(cache_path)

        logger.info(f"[TTS] Generating audio for: {clean[:50]}...")
        
        # Chọn giọng tiếng Việt: Hoài My (nữ) hoặc Nam Minh (nam)
        voice = "vi-VN-HoaiMyNeural" if lang == "vi" else "en-US-AriaNeural"

        async def _generate():
            communicate = edge_tts.Communicate(clean, voice)
            await communicate.save(str(cache_path))

        # Chạy async trong môi trường sync
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Nếu event loop đang chạy (ví dụ trong FastAPI endpoint), cần tạo task hoặc luồng khác
                # Tuy nhiên, endpoints FastAPI trong app thường được chạy dạng async/await hoặc threadpool
                # Cách an toàn nhất cho sync code:
                import nest_asyncio
                nest_asyncio.apply()
                loop.run_until_complete(_generate())
            else:
                asyncio.run(_generate())
        except RuntimeError:
            asyncio.run(_generate())

        logger.info(f"[TTS] Saved to: {cache_path}")
        return str(cache_path)

    except ImportError:
        logger.warning("[TTS] edge-tts not installed. Run: pip install edge-tts nest_asyncio")
        return None
    except Exception as e:
        logger.error(f"[TTS] edge-tts error: {e}")
        return None


def generate_tts_pyttsx3(text: str) -> str | None:
    """
    Fallback offline TTS dùng pyttsx3.
    Trả về đường dẫn file WAV nếu thành công.
    """
    try:
        import pyttsx3  # type: ignore
        clean = _clean_text_for_tts(text)
        if not clean:
            return None

        cache_key = hashlib.md5(f"offline:{clean}".encode()).hexdigest()
        cache_path = TTS_CACHE_DIR / f"{cache_key}_offline.wav"

        if cache_path.exists():
            return str(cache_path)

        engine = pyttsx3.init()
        # Chọn giọng tiếng Việt nếu có
        voices = engine.getProperty("voices")
        for v in voices:
            if "vi" in v.id.lower() or "viet" in v.name.lower():
                engine.setProperty("voice", v.id)
                break
        engine.setProperty("rate", 160)
        engine.save_to_file(clean, str(cache_path))
        engine.runAndWait()
        return str(cache_path)
    except Exception as e:
        logger.error(f"[TTS] pyttsx3 error: {e}")
        return None


def text_to_speech(text: str, lang: str = "vi", prefer_online: bool = True) -> str | None:
    """
    Entry point thống nhất:
    - Thử edge-tts trước (online, chất lượng cao)
    - Fallback pyttsx3 nếu không có internet
    """
    if prefer_online:
        result = generate_tts_edge(text, lang)
        if result:
            return result
    return generate_tts_pyttsx3(text)


def cleanup_tts_cache(max_files: int = 100):
    """Dọn cache khi quá nhiều file (xóa file cũ nhất)."""
    files = sorted(TTS_CACHE_DIR.glob("*.mp3"), key=lambda f: f.stat().st_mtime)
    if len(files) > max_files:
        for f in files[:len(files) - max_files]:
            f.unlink()
            logger.info(f"[TTS] Cleaned cache: {f.name}")
