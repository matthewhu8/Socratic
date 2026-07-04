from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..database.models import UserFeedback

router = APIRouter()


class FeedbackCreate(BaseModel):
    type: str  # suggestion, feature, bug, other
    description: str
    email: Optional[str] = None
    timestamp: Optional[str] = None

@router.post("/api/feedback")
async def submit_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """Submit user feedback."""
    try:
        print("storing user feedback into production database")
        # Create feedback entry
        feedback = UserFeedback(
            type=feedback_data.type,
            description=feedback_data.description,
            email=feedback_data.email,
            user_id=None,  # Not requiring authentication for feedback
            timestamp=datetime.utcnow()
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        return {
            "status": "success",
            "message": "Thank you for your feedback!",
            "feedback_id": feedback.id
        }

    except Exception as e:
        db.rollback()
        print(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.post("/developer-jeeter")
async def get_user_feedback_dashboard():
    pass
    # ideally a route where devs can go in and check user feedback
