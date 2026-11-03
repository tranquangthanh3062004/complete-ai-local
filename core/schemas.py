"""
COMPLETE AI — Shared Schemas / Data Transfer Objects (DTO)
Định nghĩa tất cả cấu trúc dữ liệu giao tiếp giữa các module và API.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from core.enums import OperationMode, NetworkStatus, IntentType, TopicType


# ── Chat API Schemas ──────────────────────────────────────────────────────────

class MessageHistory(BaseModel):
    """Một tin nhắn trong lịch sử chat."""
    role: str = Field(..., description="Role of the sender: 'user' or 'assistant'")
    content: str = Field(..., description="Content of the message")


class ChatRequest(BaseModel):
    """Payload đầu vào cho chat endpoint."""
    query: str = Field(..., min_length=1, max_length=2000, description="Nội dung câu hỏi của người dùng")
    messages: List[MessageHistory] = Field(default_factory=list, description="Lịch sử chat gần nhất")
    session_id: Optional[str] = Field(None, description="ID của phiên chat để tracking")
    suggest: bool = Field(False, description="Có sinh câu hỏi gợi ý hay không")
    mode_override: Optional[OperationMode] = Field(None, description="Ép buộc chạy ở mode cụ thể (test/debug)")


class ChatResponse(BaseModel):
    """Payload trả về từ chat endpoint (dùng cho non-streaming)."""
    reply: str = Field(..., description="Câu trả lời cuối cùng từ AI")
    mode: OperationMode = Field(..., description="Chế độ đã xử lý (online/offline/hybrid)")
    model: str = Field(..., description="Tên model đã sử dụng")
    intent: Optional[str] = Field(None, description="Ý định được detect (vd: route, info)")
    latency_ms: float = Field(..., description="Tổng thời gian xử lý (ms)")
    sources: List[str] = Field(default_factory=list, description="Danh sách các nguồn dữ liệu đã dùng")
    suggestions: List[str] = Field(default_factory=list, description="Danh sách câu hỏi gợi ý tiếp theo")


# ── Internal Pipeline DTOs ────────────────────────────────────────────────────

class RouteStep(BaseModel):
    """Một chặng trong lộ trình đi lại."""
    step_number: int = Field(alias="step")
    type: str = Field(..., description="Loại phương tiện: walk, bus, metro, bike")
    line: str = Field(default="", description="Số hiệu tuyến (vd: 01, 2A)")
    from_loc: str = Field(..., alias="from", description="Điểm đi của chặng này")
    to_loc: str = Field(..., alias="to", description="Điểm đến của chặng này")
    duration_mins: int = Field(..., alias="duration", description="Thời gian đi chặng này (phút)")
    cost_vnd: int = Field(..., alias="cost", description="Chi phí cho chặng này (VNĐ)")
    
    model_config = ConfigDict(populate_by_name=True)


class RouteOption(BaseModel):
    """Một phương án lộ trình tổng thể."""
    option_name: str = Field(..., description="Tên phương án (vd: Nhanh nhất, Rẻ nhất)")
    origin: str
    destination: str
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    total_time_mins: int = Field(..., alias="total_time")
    total_cost_vnd: int = Field(..., alias="total_cost")
    transfers: int
    walk_km: float
    co2_kg: float
    steps: List[RouteStep]
    
    model_config = ConfigDict(populate_by_name=True)


class IntentResult(BaseModel):
    """Kết quả phân tích ý định người dùng."""
    type: IntentType
    topic: TopicType = Field(default=TopicType.GTCC_CHUNG)
    origin: Optional[str] = None
    destination: Optional[str] = None
    rewritten_query: str = Field(..., description="Câu hỏi đã được chuẩn hóa để RAG search tốt hơn")
    confidence: float = Field(default=1.0, description="Độ tự tin của detector (0.0 - 1.0)")


class DocumentChunk(BaseModel):
    """Một đoạn text được lấy từ Vector Store."""
    content: str
    source_file: str
    similarity_score: float = Field(default=0.0)
    chunk_id: str


# ── Health & Telemetry ────────────────────────────────────────────────────────

class HealthStatus(BaseModel):
    """Trạng thái hệ thống (trả về từ /api/health)."""
    status: str = "ok"
    version: str
    network_mode: NetworkStatus
    llm_status: Dict[str, str] = Field(default_factory=dict)
    vector_db_status: str
    uptime_seconds: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
