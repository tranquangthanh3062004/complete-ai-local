"""
Input Sanitizer v1.0 — Bảo vệ GTCC Bot khỏi Prompt Injection
Phát hiện và chặn các pattern nguy hiểm trước khi gửi vào LLM.
"""
import re
from logger import get_logger

logger = get_logger("sanitizer")

# ── Danh sách pattern injection phổ biến (Đa ngôn ngữ & Tiếng Việt) ────────────
INJECTION_PATTERNS = [
    # Classic prompt injection & English Jailbreak
    r"ignore\s+(?:all\s+)?(?:previous|above)\s+instructions?",
    r"forget\s+(?:everything|all)\s+(?:above|previous|you)",
    r"disregard\s+(?:all\s+)?(?:previous|above|your)\s+instructions?",
    r"do\s+not\s+follow\s+(?:the\s+)?(?:previous|above)\s+instructions?",
    r"override\s+(?:all\s+)?(?:previous\s+)?(?:instructions?|rules?|guidelines?)",
    r"you\s+are\s+now\s+(?:a\s+)?(?:different|new|evil|jailbroken|DAN)",
    r"\bDAN\b",
    r"jailbreak",
    r"pretend\s+you\s+(?:are|have\s+no)\s+(?:restrictions?|rules?|guidelines?)",
    r"as\s+an?\s+(?:ai|llm)\s+without\s+(?:any\s+)?restrictions?",
    r"act\s+as\s+if\s+you\s+(?:have\s+no|were\s+not)\s+(?:trained|restricted)",

    # Prompt Injection Tiếng Việt
    r"bỏ\s+qua\s+(?:tất\s+cả\s+)?(?:các\s+)?(?:hướng\s+dẫn|quy\s+tắc|chỉ\s+dẫn)\s+(?:trước|trên)",
    r"quên\s+(?:đi\s+)?(?:tất\s+cả|mọi)\s+(?:quy\s+tắc|chỉ\s+dẫn|hướng\s+dẫn)",
    r"không\s+tuân\s+theo\s+(?:quy\s+tắc|hướng\s+dẫn)\s+trước",
    r"từ\s+bây\s+giờ\s+hãy\s+(?:đóng\s+vai|làm|trở\s+thành)",
    r"hãy\s+đóng\s+vai",
    r"bắt\s+đầu\s+chế\s+độ\s+(?:god|admin|developer|thần\s+thánh)",

    # System prompt leak (Anh & Việt)
    r"reveal\s+your\s+(?:system\s+)?(?:prompt|instructions?)",
    r"print\s+your\s+(?:initial|system)\s+(?:prompt|instructions?)",
    r"what\s+(?:are|is)\s+your\s+(?:system\s+)?prompt",
    r"show\s+me\s+your\s+(?:system\s+)?(?:prompt|instructions?)",
    r"repeat\s+the\s+words\s+above",
    r"hiển\s+thị\s+(?:system\s+)?prompt",
    r"cho\s+tôi\s+xem\s+(?:prompt|hướng\s+dẫn\s+hệ\s+thống|chỉ\s+dẫn\s+ban\s+đầu)",
    r"cho\s+biết\s+câu\s+lệnh\s+hệ\s+thống",
    r"lặp\s+lại\s+(?:toàn\s+bộ\s+)?(?:lời\s+nhắc|prompt)",

    # Context boundary hijacking & XML tag injection
    r"</?(?:system_context|rag_docs|system_prompt|instructions|maps_data|smart_routes)>",
    r"\[SYSTEM_PROMPT\]",
    r"\[INSTRUCTION\]",

    # Role manipulation
    r"from\s+now\s+on(?:\s+you\s+(?:are|will\s+be))?",
    r"you\s+will\s+(?:no\s+longer|not)\s+(?:act\s+as|be)",
    r"switch\s+(?:to\s+)?(?:evil|developer|admin|god)\s+mode",

    # SQL/code injection (đề phòng)
    r"(?:DROP|DELETE|INSERT|UPDATE|SELECT\s+\*)\s+(?:TABLE|FROM|INTO)",
    r"<script[^>]*>",
    r"javascript:",
]

# Biên dịch trước để nhanh
_compiled = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

# Giới hạn độ dài
MAX_QUERY_LENGTH = 2000
MIN_QUERY_LENGTH = 2

# Từ khóa ngoài phạm vi GTCC (tùy chỉnh)
OUT_OF_SCOPE_KEYWORDS = [
    "chế tạo bom", "vũ khí", "hướng dẫn hack",
    "make bomb", "how to hack", "bypass security",
]


def sanitize_query(query: str) -> tuple[str, bool, str]:
    """
    Kiểm tra và làm sạch câu hỏi.
    
    Returns:
        (cleaned_query, is_safe, reason)
        - cleaned_query: câu hỏi đã trim/truncate
        - is_safe: True nếu an toàn
        - reason: lý do bị từ chối (rỗng nếu an toàn)
    """
    if not query or not isinstance(query, str):
        return "", False, "Query rỗng hoặc không hợp lệ."

    # Trim và kiểm tra độ dài
    cleaned = query.strip()
    if len(cleaned) < MIN_QUERY_LENGTH:
        return "", False, "Câu hỏi quá ngắn."
    if len(cleaned) > MAX_QUERY_LENGTH:
        logger.warning(f"[Sanitizer] Query truncated from {len(cleaned)} to {MAX_QUERY_LENGTH}")
        cleaned = cleaned[:MAX_QUERY_LENGTH]

    # Kiểm tra injection pattern
    for pattern in _compiled:
        if pattern.search(cleaned):
            logger.warning(f"[Sanitizer] Prompt injection detected: '{cleaned[:100]}...'")
            return "", False, "Yêu cầu không hợp lệ. Vui lòng hỏi về Giao Thông Công Cộng."

    # Kiểm tra ngoài phạm vi
    query_lower = cleaned.lower()
    for kw in OUT_OF_SCOPE_KEYWORDS:
        if kw in query_lower:
            logger.warning(f"[Sanitizer] Out-of-scope keyword: '{kw}'")
            return "", False, "Chủ đề không phù hợp với GTCC Bot."

    # Chuẩn hóa khoảng trắng
    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned, True, ""


def is_gtcc_related(query: str) -> bool:
    """
    Kiểm tra nhanh xem câu hỏi có liên quan đến GTCC không.
    Không block — chỉ dùng để log cảnh báo.
    """
    gtcc_signals = [
        "xe", "bus", "metro", "buýt", "buyt", "tàu", "tau",
        "ga", "trạm", "tram", "vé", "ve", "lộ trình", "lo trinh",
        "giao thông", "giao thong", "sân bay", "san bay",
        "bến xe", "ben xe", "tuyến", "tuyen", "lịch", "lich",
        "giá", "gia", "cước", "cuoc", "luật", "luat", "phạt", "phat",
        "brt", "xe đạp", "xe dap", "phà", "pha", "cáp treo", "đường thủy",
    ]
    query_lower = query.lower()
    return any(sig in query_lower for sig in gtcc_signals)
