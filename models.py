"""
Database models - SQLAlchemy ORM
Bao gồm hệ thống theo dõi học tập để cá nhân hóa câu trả lời.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    Float, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


# ─────────────────────────────────────────────
#  Core Models
# ─────────────────────────────────────────────

class User(Base):
    """Người dùng hệ thống."""
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    display_name    = Column(String, default="")
    is_active       = Column(Boolean, default=True)
    is_superuser    = Column(Boolean, default=False)
    role            = Column(String, default="user")   # admin | user | guest
    created_at      = Column(DateTime, default=datetime.utcnow)

    documents       = relationship("Document",     back_populates="owner",    cascade="all, delete-orphan")
    chats           = relationship("Chat",         back_populates="user",     cascade="all, delete-orphan")
    learning_events = relationship("LearningEvent",back_populates="user",     cascade="all, delete-orphan")
    topic_mastery   = relationship("TopicMastery", back_populates="user",     cascade="all, delete-orphan")


class Document(Base):
    """Tài liệu PDF đã upload."""
    __tablename__ = "documents"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    filename   = Column(String, nullable=False)
    content    = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="documents")


class Chat(Base):
    """Lịch sử hội thoại."""
    __tablename__ = "chats"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String, index=True)
    message    = Column(Text, nullable=False)
    role       = Column(String, nullable=False)   # user | assistant
    model_used = Column(String, default="ollama")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chats")


# ─────────────────────────────────────────────
#  Learning / Personalization Models
# ─────────────────────────────────────────────

class LearningEvent(Base):
    """
    Mỗi lần người dùng hỏi → ghi lại để phân tích.
    Dùng để biết: câu nào hay hỏi, chủ đề nào yếu, câu trả lời có hữu ích không.
    """
    __tablename__ = "learning_events"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id    = Column(String, index=True)

    # Nội dung câu hỏi
    question      = Column(Text, nullable=False)
    answer        = Column(Text, nullable=False)

    # Phân loại chủ đề (tự động detect)
    topic         = Column(String, default="general")     # vd: "luật", "kỹ thuật", "toán"
    subtopic      = Column(String, default="")

    # Đánh giá của người dùng (sau khi bấm 👍/👎)
    feedback      = Column(Integer, default=0)            # 1=tốt, -1=kém, 0=chưa đánh giá
    feedback_note = Column(Text, default="")

    # Metadata
    response_time_ms = Column(Float, default=0)
    model_used    = Column(String, default="ollama")
    created_at    = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="learning_events")


class TopicMastery(Base):
    """
    Điểm thành thạo của mỗi user theo từng chủ đề.
    Được cập nhật mỗi khi có feedback.
    Score: 0.0 (rất yếu) → 1.0 (rất giỏi)
    """
    __tablename__ = "topic_mastery"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=True)

    topic          = Column(String, nullable=False, index=True)
    total_questions = Column(Integer, default=0)
    positive_feedback = Column(Integer, default=0)   # số lần 👍
    negative_feedback = Column(Integer, default=0)   # số lần 👎
    mastery_score  = Column(Float, default=0.5)      # 0.0–1.0

    last_updated   = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="topic_mastery")

    @property
    def total_feedback(self):
        return self.positive_feedback + self.negative_feedback
