"""
COMPLETE AI — Shared Enums
Single source of truth for all enum types across the system.
"""
from enum import Enum


class OperationMode(str, Enum):
    """Chế độ vận hành của hệ thống."""
    ONLINE = "online"
    OFFLINE = "offline"
    HYBRID = "hybrid"


class LLMEngine(str, Enum):
    """LLM Engine backend."""
    GROQ = "groq"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class EmbeddingEngine(str, Enum):
    """Embedding model engine."""
    HUGGINGFACE = "huggingface"
    GEMINI = "gemini"
    BGE_M3 = "bge-m3"


class IntentType(str, Enum):
    """Loại intent của câu hỏi người dùng."""
    ROUTE = "route"          # Hỏi đường đi từ A đến B
    INFO = "info"            # Hỏi thông tin (giá vé, lịch trình...)
    GREETING = "greeting"    # Chào hỏi
    AMBIGUOUS = "ambiguous"  # Không rõ ý định → cần LLM phân tích


class TopicType(str, Enum):
    """Phân loại chủ đề GTCC."""
    XE_BUYT = "xe_buyt"
    METRO_TAU_DIEN = "metro_tau_dien"
    BRT_XE_BUYT_NHANH = "brt_xe_buyt_nhanh"
    VE_GIA_CUOC = "ve_gia_cuoc"
    LICH_TRINH_TUYEN = "lich_trinh_tuyen"
    LUAT_QUY_DINH = "luat_quy_dinh"
    GIAO_THONG_DUONG_THUY = "giao_thong_duong_thuy"
    UNG_DUNG_TIEN_ICH = "ung_dung_tien_ich"
    XE_DAP_XE_MAY_CHIA_SE = "xe_dap_xe_may_chia_se"
    SAN_BAY_GA_TAU = "san_bay_ga_tau"
    GTCC_CHUNG = "gtcc_chung"


class VectorStoreType(str, Enum):
    """Loại Vector Store."""
    SUPABASE = "supabase"
    PINECONE = "pinecone"
    CHROMA = "chroma"
    IN_MEMORY = "in_memory"


class NetworkStatus(str, Enum):
    """Trạng thái mạng."""
    ONLINE = "online"
    DEGRADED = "degraded"    # Có mạng nhưng API không ổn định
    OFFLINE = "offline"
