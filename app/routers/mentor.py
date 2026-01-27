from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime

from app.core import database, deps
from app.models.mentor import Mentor, AvailabilitySlot, Booking, BookingStatus
from app.models.user import User
from app.schemas.mentor import MentorSchema, MentorResponse, SlotCreate, BookingCreate, MentorCreate

router = APIRouter()

# --- Mentor Profile ---

@router.post("/mentors/profile", response_model=MentorResponse)
def create_or_update_profile(
    data: MentorCreate, 
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # No need to check ID match, we use current_user.user_id as source of truth
    user_id_to_use = current_user.user_id

    mentor = db.query(Mentor).filter(Mentor.user_id == user_id_to_use).first()
    if not mentor:
        mentor = Mentor(
            user_id=user_id_to_use, 
            full_name=data.full_name, 
            bio=data.bio, 
            skills=data.skills,
            verification_status="PENDING"
        )
        db.add(mentor)
    else:
        mentor.full_name = data.full_name
        mentor.bio = data.bio
        mentor.skills = data.skills
    
    db.commit()
    db.refresh(mentor)
    return mentor

@router.get("/mentors", response_model=List[MentorResponse])
def get_mentors(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    mentors = db.query(Mentor).offset(skip).limit(limit).all()
    return mentors

# --- Booking System ---

@router.post("/bookings/create")
def create_booking(
    booking_in: BookingCreate, 
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # 1. ATOMIC UPDATE: Try to mark slot as BOOKED only if it is currently AVAILABLE
    # This prevents race conditions where two users read "AVAILABLE" at the same time.
    result = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.slot_id == booking_in.slot_id, 
        AvailabilitySlot.status == BookingStatus.AVAILABLE
    ).update({"status": BookingStatus.BOOKED}, synchronize_session=False)
    
    db.commit()

    if result == 0:
        # If no rows were updated, it means the slot was NOT available (or doesn't exist)
        raise HTTPException(status_code=400, detail="Slot này không còn trống hoặc không tồn tại (Race Condition Protected)")

    # 2. Tạo record Booking mới (Safe to proceed)
    new_booking = Booking(
        slot_id=booking_in.slot_id,
        learner_id=current_user.user_id,
        created_at=datetime.now()
    )
    
    db.add(new_booking)
    try:
        db.commit()
        db.refresh(new_booking)
    except Exception as e:
        # Rollback slot status if booking creation fails (rare)
        db.query(AvailabilitySlot).filter(AvailabilitySlot.slot_id == booking_in.slot_id).update({"status": BookingStatus.AVAILABLE})
        db.commit()
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi đặt lịch: {str(e)}")

    return {"message": "Đặt lịch thành công", "booking_id": new_booking.booking_id}

@router.post("/mentors/slots")
def create_slot(
    slot: SlotCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Check if user is a mentor
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
         raise HTTPException(status_code=400, detail="User is not a registered mentor")

    new_slot = AvailabilitySlot(
        mentor_id=mentor.mentor_id,
        start_time=slot.start_time,
        end_time=slot.end_time,
        status=BookingStatus.AVAILABLE
    )
    db.add(new_slot)
    db.commit()
    return {"message": "Slot created successfully"}

@router.get("/mentors/{mentor_id}/slots")
def get_mentor_slots(
    mentor_id: int,
    db: Session = Depends(database.get_db)
):
    slots = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_id == mentor_id,
        AvailabilitySlot.status == BookingStatus.AVAILABLE
    ).all()
    return slots

@router.get("/mentors/me/bookings")
def get_my_bookings(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # 1. Get Mentor ID
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
         raise HTTPException(400, "User is not a mentor")
         
    # 2. Get Bookings via Slots
    # Join Booking -> Slot -> Mentor
    bookings = db.query(Booking).join(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_id == mentor.mentor_id
    ).all()
    
    return bookings

@router.post("/sessions/{booking_id}/feedback")
def submit_session_feedback(
    booking_id: int,
    feedback: str,
    rating: int, # 1-5
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Verify mentor owns this booking
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
        
    # TODO: Verify ownership (complex join needed or trust ID for now)
    
    booking.feedback_notes = feedback
    booking.status = "COMPLETED" # Assume enum string or object
    db.commit()
    return {"message": "Feedback submitted"}

# --- Mentor Assessments for Learners ---
from pydantic import BaseModel as PydanticBase
from typing import Optional

class AssessmentCreate(PydanticBase):
    booking_id: int
    score: int  # 1-10
    feedback: str
    level_assigned: Optional[str] = None  # A1, A2, B1, B2, C1, C2

@router.post("/mentor/assessments")
def create_assessment(
    data: AssessmentCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    from app.models.mentor import MentorAssessment, Booking
    
    # Verify booking exists
    booking = db.query(Booking).filter(Booking.booking_id == data.booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    # Create or update assessment
    assessment = db.query(MentorAssessment).filter(MentorAssessment.booking_id == data.booking_id).first()
    if assessment:
        assessment.score = data.score
        assessment.feedback = data.feedback
    else:
        assessment = MentorAssessment(
            booking_id=data.booking_id,
            score=data.score,
            feedback=data.feedback
        )
        db.add(assessment)
    
    # Update booking status
    booking.status = "COMPLETED"
    
    # Optionally update learner's level
    if data.level_assigned:
        from app.models.proficiency import LearningPath
        path = db.query(LearningPath).filter(LearningPath.user_id == booking.learner_id).first()
        if path:
            path.current_level = data.level_assigned
        else:
            path = LearningPath(user_id=booking.learner_id, current_level=data.level_assigned)
            db.add(path)
    
    db.commit()
    return {"message": "Assessment created", "assessment_id": assessment.assessment_id}

@router.get("/mentor/assessments")
def get_my_assessments(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    from app.models.mentor import MentorAssessment, Booking, AvailabilitySlot, Mentor
    
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(400, "User is not a mentor")
    
    # Get assessments through booking -> slot -> mentor chain
    # Optimization: Use joinedload to prevent N+1 queries when accessing learner details
    assessments = db.query(MentorAssessment).join(Booking).join(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_id == mentor.mentor_id
    ).options(
        joinedload(MentorAssessment.booking).joinedload(Booking.learner)
    ).all()
    
    result = []
    for a in assessments:
        result.append({
            "assessment_id": a.assessment_id,
            "booking_id": a.booking_id,
            "learner_name": a.booking.learner.full_name if a.booking.learner else "Unknown",
            "score": a.score,
            "feedback": a.feedback,
            "created_at": a.created_at.isoformat() if a.created_at else None
        })
    
    return result


# --- Mentor Vocab Suggestions ---

from app.models.mentor_resource import MentorVocabSuggestion

class VocabSuggestionCreate(PydanticBase):
    topic_id: Optional[int] = None
    vocabulary: str
    collocations: Optional[str] = None
    idioms: Optional[str] = None
    tips: Optional[str] = None

class VocabSuggestionResponse(VocabSuggestionCreate):
    id: int
    mentor_id: int
    created_at: datetime

    class Config:
        orm_mode = True

@router.post("/mentor/vocab-suggestions", response_model=VocabSuggestionResponse)
def create_vocab_suggestion(
    data: VocabSuggestionCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(400, "User is not a mentor")
    
    suggestion = MentorVocabSuggestion(
        mentor_id=mentor.mentor_id,
        topic_id=data.topic_id,
        vocabulary=data.vocabulary,
        collocations=data.collocations,
        idioms=data.idioms,
        tips=data.tips
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return suggestion

@router.get("/mentor/vocab-suggestions", response_model=List[VocabSuggestionResponse])
def get_my_vocab_suggestions(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(400, "User is not a mentor")
    
    return db.query(MentorVocabSuggestion).filter(MentorVocabSuggestion.mentor_id == mentor.mentor_id).all()

@router.get("/topics/{topic_id}/vocab-suggestions", response_model=List[VocabSuggestionResponse])
def get_topic_vocab_suggestions(
    topic_id: int,
    db: Session = Depends(database.get_db)
):
    # This endpoint is public for learners/mentors to see suggestions for a topic
    return db.query(MentorVocabSuggestion).filter(MentorVocabSuggestion.topic_id == topic_id).all()
