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

# ============== SESSION MANAGEMENT ==============
from app.models.content import SpeakingSession
from datetime import datetime

# Using a secondary router for /mentor-review prefix
session_router = APIRouter(prefix="/mentor-review", tags=["Mentor Sessions & Resources"])

@session_router.get("/sessions")
def get_mentor_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all sessions for current mentor (via bookings)"""
    from app.models.mentor import Mentor, AvailabilitySlot
    
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        return []
    
    # Get bookings then construct session-like data
    bookings = (
        db.query(Booking)
        .join(AvailabilitySlot)
        .filter(AvailabilitySlot.mentor_id == mentor.mentor_id)
        .all()
    )
    
    result = []
    for b in bookings:
        result.append({
            "session_id": b.booking_id,  # Use booking_id as session reference
            "booking_id": b.booking_id,
            "learner_id": b.learner_id,
            "start_time": b.slot.start_time.isoformat() if b.slot else None,
            "end_time": b.slot.end_time.isoformat() if b.slot else None,
            "status": b.slot.status.value if b.slot else "UNKNOWN",
            "notes": getattr(b, 'feedback_notes', None)
        })
    return result

@session_router.post("/sessions/start")
def start_session(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    booking.slot.status = BookingStatus.BOOKED  # Mark as in progress
    db.commit()
    return {"message": "Session started", "booking_id": booking_id}

@session_router.post("/sessions/{session_id}/end")
def end_session(
    session_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    booking = db.query(Booking).filter(Booking.booking_id == session_id).first()
    if not booking:
        raise HTTPException(404, "Session not found")
    
    booking.slot.status = BookingStatus.COMPLETED
    if notes:
        booking.feedback_notes = notes
    db.commit()
    return {"message": "Session ended"}

@session_router.put("/sessions/{session_id}/notes")
def update_notes(
    session_id: int,
    notes: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    booking = db.query(Booking).filter(Booking.booking_id == session_id).first()
    if not booking:
        raise HTTPException(404, "Session not found")
    
    booking.feedback_notes = notes
    db.commit()
    return {"message": "Notes updated"}

# ============== RESOURCES ==============
from app.models.mentor_review import MentorResource

class ResourceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    file_url: str
    resource_type: str = "DOCUMENT"

@session_router.get("/resources")
def get_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resources = db.query(MentorResource).filter(MentorResource.mentor_id == current_user.user_id).all()
    return resources

@session_router.post("/resources")
def create_resource(
    data: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resource = MentorResource(
        mentor_id=current_user.user_id,
        title=data.title,
        description=data.description,
        file_url=data.file_url,
        resource_type=data.resource_type
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource

@session_router.delete("/resources/{resource_id}")
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resource = db.query(MentorResource).filter(
        MentorResource.resource_id == resource_id,
        MentorResource.mentor_id == current_user.user_id
    ).first()
    if not resource:
        raise HTTPException(404, "Resource not found")
    
    db.delete(resource)
    db.commit()
    return {"message": "Resource deleted"}

