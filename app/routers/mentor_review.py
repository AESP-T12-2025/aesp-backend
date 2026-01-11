from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.core.database import get_db
from app.models.mentor_review import MentorReview
from app.models.mentor import Booking, BookingStatus
from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter(prefix="/reviews", tags=["Mentor Reviews"])

# --- Schemas ---
class ReviewCreate(BaseModel):
    booking_id: int
    pronunciation_score: int # 1-5
    fluency_score: int
    grammar_score: int
    lexical_score: int
    general_feedback: str
    actionable_next_steps: str

class ReviewResponse(BaseModel):
    id: int
    mentor_name: str
    scores: dict
    feedback: str
    next_steps: str

# --- APIs ---

@router.post("/submit")
def submit_mentor_review(
    review_data: ReviewCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "MENTOR":
        raise HTTPException(403, "Only mentors can review")

    # 1. Verify Booking (Strict Check)
    # Join Booking -> Slot -> Mentor to ensure ownership
    # We need to query: Is there a booking with this ID, linked to a slot, linked to THIS mentor?
    
    booking = (
        db.query(Booking)
        .join(Booking.slot)
        .filter(
            Booking.booking_id == review_data.booking_id,
            Booking.slot.has(mentor_id=current_user.mentor_profile.mentor_id)
        )
        .first()
    )

    if not booking:
        raise HTTPException(404, "Booking not found or does not belong to you")

    # 2. Save Review
    new_review = MentorReview(
        booking_id=review_data.booking_id,
        mentor_id=current_user.user_id,
        learner_id=booking.learner_id,
        pronunciation_score=review_data.pronunciation_score,
        fluency_score=review_data.fluency_score,
        grammar_score=review_data.grammar_score,
        lexical_score=review_data.lexical_score,
        general_feedback=review_data.general_feedback,
        actionable_next_steps=review_data.actionable_next_steps
    )
    db.add(new_review)
    
    # 3. Update Booking Status
    booking.status = BookingStatus.COMPLETED
    
    db.commit()
    return {"message": "Review submitted successfully", "review_id": new_review.id}

@router.get("/me", response_model=List[ReviewResponse])
def get_my_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reviews = db.query(MentorReview).filter(MentorReview.learner_id == current_user.user_id).all()
    results = []
    for r in reviews:
        results.append({
            "id": r.id,
            "mentor_name": r.mentor.full_name if r.mentor else "Unknown",
            "scores": {
                "pronunciation": r.pronunciation_score,
                "fluency": r.fluency_score,
                "grammar": r.grammar_score,
                "lexical": r.lexical_score
            },
            "feedback": r.general_feedback,
            "next_steps": r.actionable_next_steps
        })
    return results
