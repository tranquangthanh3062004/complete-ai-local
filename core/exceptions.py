"""
COMPLETE AI — Custom Exception Hierarchy
Cung cấp exception cụ thể cho từng loại lỗi, thay vì dùng generic Exception.

Hierarchy:
    CompleteAIException (base)
    ├── LLMError
    │   ├── LLMUnavailableError
    │   ├── LLMTimeoutError
    │   └── LLMRateLimitError
    ├── RAGError
    │   ├── RAGRetrievalError
    │   └── EmbeddingError
    ├── InputError
    │   ├── InvalidQueryError
    │   └── UnsafeQueryError
    ├── NetworkError
    │   └── NetworkModeError
    ├── MapsAPIError
    └── RouteNotFoundError
"""


class CompleteAIException(Exception):
    """Base exception cho toàn bộ hệ thống COMPLETE AI."""

    def __init__(self, message: str = "", code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# ── LLM Errors ────────────────────────────────────────────────────────────────

class LLMError(CompleteAIException):
    """Base exception cho tất cả lỗi liên quan đến LLM."""

    def __init__(self, message: str = "LLM error", code: str = "LLM_ERROR"):
        super().__init__(message, code)


class LLMUnavailableError(LLMError):
    """Không thể kết nối tới LLM engine (Groq/Gemini/Ollama)."""

    def __init__(self, engine: str = "", message: str = ""):
        msg = message or f"LLM engine '{engine}' không available."
        super().__init__(msg, code="LLM_UNAVAILABLE")
        self.engine = engine


class LLMTimeoutError(LLMError):
    """LLM không phản hồi trong thời gian cho phép."""

    def __init__(self, timeout_seconds: float = 0, message: str = ""):
        msg = message or f"LLM timeout sau {timeout_seconds}s."
        super().__init__(msg, code="LLM_TIMEOUT")
        self.timeout_seconds = timeout_seconds


class LLMRateLimitError(LLMError):
    """Vượt quá rate limit của LLM provider."""

    def __init__(self, engine: str = "", message: str = ""):
        msg = message or f"Rate limit exceeded cho engine '{engine}'."
        super().__init__(msg, code="LLM_RATE_LIMIT")
        self.engine = engine


# ── RAG Errors ────────────────────────────────────────────────────────────────

class RAGError(CompleteAIException):
    """Base exception cho tất cả lỗi liên quan đến RAG."""

    def __init__(self, message: str = "RAG error", code: str = "RAG_ERROR"):
        super().__init__(message, code)


class RAGRetrievalError(RAGError):
    """Lỗi khi truy xuất dữ liệu từ Vector Store."""

    def __init__(self, store_type: str = "", message: str = ""):
        msg = message or f"Không thể truy xuất dữ liệu từ {store_type}."
        super().__init__(msg, code="RAG_RETRIEVAL_ERROR")
        self.store_type = store_type


class EmbeddingError(RAGError):
    """Lỗi khi tạo embedding cho query hoặc documents."""

    def __init__(self, model: str = "", message: str = ""):
        msg = message or f"Embedding model '{model}' lỗi."
        super().__init__(msg, code="EMBEDDING_ERROR")
        self.model = model


# ── Input Errors ──────────────────────────────────────────────────────────────

class InputError(CompleteAIException):
    """Base exception cho lỗi đầu vào."""

    def __init__(self, message: str = "Input error", code: str = "INPUT_ERROR"):
        super().__init__(message, code)


class InvalidQueryError(InputError):
    """Query không hợp lệ (quá ngắn, quá dài, rỗng)."""

    def __init__(self, reason: str = "", message: str = ""):
        msg = message or f"Query không hợp lệ: {reason}"
        super().__init__(msg, code="INVALID_QUERY")
        self.reason = reason


class UnsafeQueryError(InputError):
    """Query bị phát hiện là prompt injection hoặc unsafe content."""

    def __init__(self, reason: str = "", message: str = ""):
        msg = message or f"Query không an toàn: {reason}"
        super().__init__(msg, code="UNSAFE_QUERY")
        self.reason = reason


# ── Network Errors ────────────────────────────────────────────────────────────

class NetworkError(CompleteAIException):
    """Base exception cho lỗi mạng."""

    def __init__(self, message: str = "Network error", code: str = "NETWORK_ERROR"):
        super().__init__(message, code)


class NetworkModeError(NetworkError):
    """Lỗi khi chuyển đổi chế độ mạng (online ↔ offline)."""

    def __init__(self, from_mode: str = "", to_mode: str = "", message: str = ""):
        msg = message or f"Không thể chuyển từ {from_mode} sang {to_mode}."
        super().__init__(msg, code="NETWORK_MODE_ERROR")
        self.from_mode = from_mode
        self.to_mode = to_mode


# ── Maps & Routing Errors ────────────────────────────────────────────────────

class MapsAPIError(CompleteAIException):
    """Lỗi khi gọi Google Maps / OpenStreetMap API."""

    def __init__(self, provider: str = "", message: str = ""):
        msg = message or f"Maps API '{provider}' lỗi."
        super().__init__(msg, code="MAPS_API_ERROR")
        self.provider = provider


class RouteNotFoundError(CompleteAIException):
    """Không tìm được lộ trình giữa origin và destination."""

    def __init__(self, origin: str = "", destination: str = "", message: str = ""):
        msg = message or f"Không tìm thấy lộ trình từ '{origin}' đến '{destination}'."
        super().__init__(msg, code="ROUTE_NOT_FOUND")
        self.origin = origin
        self.destination = destination
