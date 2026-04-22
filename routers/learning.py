"""
Learning Router — Thu thập feedback và trả về hồ sơ học tập cá nhân.
Đây là lõi của hệ thống cá nhân hóa.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database import get_db
from routers.auth import get_current_user
from models import User, LearningEvent, TopicMastery

router = APIRouter(prefix="/learning", tags=["learning"])


# ─── Schemas ──────────────────────────────────────────────────────────────────
class FeedbackRequest(BaseModel):
    event_id: int
    feedback: int     # 1 = 👍 hữu ích,  -1 = 👎 không hữu ích
    note    : str = ""


class TopicMasteryOut(BaseModel):
    topic             : str
    total_questions   : int
    positive_feedback : int
    negative_feedback : int
    mastery_score     : float   # 0.0–1.0

    class Config:
        from_attributes = True


class LearningProfileOut(BaseModel):
    user_id          : Optional[int]
    total_questions  : int
    total_feedback   : int
    strong_topics    : List[TopicMasteryOut]   # điểm mạnh (score >= 0.6)
    weak_topics      : List[TopicMasteryOut]   # điểm yếu (score < 0.4)
    all_topics       : List[TopicMasteryOut]
    recent_questions : list


# ─── Gửi feedback sau khi đọc câu trả lời ────────────────────────────────────
@router.post("/feedback")
async def submit_feedback(
    req         : FeedbackRequest,
    db          : AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Người dùng bấm 👍/👎 → lưu feedback vào LearningEvent
    → cập nhật TopicMastery.
    """
    if req.feedback not in (1, -1):
        raise HTTPException(status_code=400, detail="feedback phải là 1 (tốt) hoặc -1 (kém)")

    # Tìm event
    result = await db.execute(
        select(LearningEvent).where(LearningEvent.id == req.event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    # Cập nhật feedback
    event.feedback      = req.feedback
    event.feedback_note = req.note
    await db.commit()

    # Cập nhật TopicMastery
    uid   = current_user.id if current_user else event.user_id
    topic = event.topic

    mastery_result = await db.execute(
        select(TopicMastery).where(
            TopicMastery.user_id == uid,
            TopicMastery.topic   == topic,
        )
    )
    mastery = mastery_result.scalar_one_or_none()

    if mastery is None:
        mastery = TopicMastery(
            user_id           = uid,
            topic             = topic,
            total_questions   = 1,
            positive_feedback = 0,
            negative_feedback = 0,
            mastery_score     = 0.5,
        )
        db.add(mastery)

    if req.feedback == 1:
        mastery.positive_feedback += 1
    else:
        mastery.negative_feedback += 1

    total = mastery.positive_feedback + mastery.negative_feedback
    if total > 0:
        mastery.mastery_score = mastery.positive_feedback / total

    mastery.last_updated = datetime.utcnow()
    await db.commit()

    label = "👍 Tốt" if req.feedback == 1 else "👎 Cần cải thiện"
    return {
        "message"      : f"Đã ghi nhận feedback: {label}",
        "topic"        : topic,
        "mastery_score": round(mastery.mastery_score, 2),
    }


# ─── Lấy hồ sơ học tập ───────────────────────────────────────────────────────
@router.get("/profile", response_model=LearningProfileOut)
async def get_learning_profile(
    db          : AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Trả về hồ sơ học tập: chủ đề giỏi, chủ đề yếu, lịch sử câu hỏi.
    """
    uid = current_user.id if current_user else None

    # Lấy tất cả TopicMastery của user
    mastery_result = await db.execute(
        select(TopicMastery).where(TopicMastery.user_id == uid)
        .order_by(TopicMastery.mastery_score.desc())
    )
    all_mastery = mastery_result.scalars().all()

    # Tổng câu hỏi
    count_result = await db.execute(
        select(func.count(LearningEvent.id)).where(LearningEvent.user_id == uid)
    )
    total_q = count_result.scalar() or 0

    # Tổng feedback
    fb_result = await db.execute(
        select(func.count(LearningEvent.id)).where(
            LearningEvent.user_id == uid,
            LearningEvent.feedback != 0,
        )
    )
    total_fb = fb_result.scalar() or 0

    # 5 câu gần nhất
    recent_result = await db.execute(
        select(LearningEvent)
        .where(LearningEvent.user_id == uid)
        .order_by(LearningEvent.created_at.desc())
        .limit(5)
    )
    recent = [
        {
            "id"      : e.id,
            "question": e.question[:100] + ("..." if len(e.question) > 100 else ""),
            "topic"   : e.topic,
            "feedback": e.feedback,
            "created_at": str(e.created_at),
        }
        for e in recent_result.scalars().all()
    ]

    strong = [m for m in all_mastery if m.mastery_score >= 0.6]
    weak   = [m for m in all_mastery if m.mastery_score < 0.4]

    return LearningProfileOut(
        user_id         = uid,
        total_questions = total_q,
        total_feedback  = total_fb,
        strong_topics   = strong,
        weak_topics     = weak,
        all_topics      = all_mastery,
        recent_questions= recent,
    )


# ─── Stats tổng quan (cho admin) ─────────────────────────────────────────────
@router.get("/stats")
async def global_stats(db: AsyncSession = Depends(get_db)):
    """Thống kê toàn hệ thống."""
    total_q = (await db.execute(select(func.count(LearningEvent.id)))).scalar() or 0
    total_pos = (await db.execute(
        select(func.count(LearningEvent.id)).where(LearningEvent.feedback == 1)
    )).scalar() or 0
    total_neg = (await db.execute(
        select(func.count(LearningEvent.id)).where(LearningEvent.feedback == -1)
    )).scalar() or 0

    # Top 5 chủ đề được hỏi nhiều nhất
    topic_counts = await db.execute(
        select(LearningEvent.topic, func.count(LearningEvent.id).label("count"))
        .group_by(LearningEvent.topic)
        .order_by(func.count(LearningEvent.id).desc())
        .limit(5)
    )
    top_topics = [{"topic": r[0], "count": r[1]} for r in topic_counts.all()]

    satisfaction = round(total_pos / max(total_pos + total_neg, 1) * 100, 1)

    return {
        "total_questions" : total_q,
        "positive_feedback": total_pos,
        "negative_feedback": total_neg,
        "satisfaction_rate": f"{satisfaction}%",
        "top_topics"       : top_topics,
    }
