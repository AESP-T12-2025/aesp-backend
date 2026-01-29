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


# --- Issue #30: Mentor Booking System (REQ-MENTOR-5) ---

from pydantic import BaseModel as PydanticBase, validator
from typing import Optional

class AvailabilitySlotInput(PydanticBase):
    day: str  # "monday", "tuesday", etc.
    start_time: str  # "HH:MM"
    end_time: str    # "HH:MM"
    
    @validator('end_time')
    def end_after_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class AvailabilityCreate(PydanticBase):
    slots: List[AvailabilitySlotInput]

class BookingRequest(PydanticBase):
    date: str  # "YYYY-MM-DD"
    time: str  # "HH:MM"

@router.post("/mentors/availability")
def set_mentor_availability(
    data: AvailabilityCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    REQ-MENTOR-5: Mentor sets availability schedule
    Replaces existing availability with new slots.
    """
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(403, "Only mentors can set availability")
    
    # Parse day to datetime for each slot
    from datetime import timedelta
    day_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, 
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
    }
    
    # Get next occurrence of each day
    today = datetime.now()
    current_weekday = today.weekday()
    
    created_slots = []
    for slot in data.slots:
        day_lower = slot.day.lower()
        if day_lower not in day_map:
            raise HTTPException(400, f"Invalid day: {slot.day}")
        
        target_weekday = day_map[day_lower]
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:
            days_ahead += 7
        
        slot_date = today + timedelta(days=days_ahead)
        
        # Parse times
        start_parts = slot.start_time.split(":")
        end_parts = slot.end_time.split(":")
        
        start_dt = slot_date.replace(
            hour=int(start_parts[0]), 
            minute=int(start_parts[1]), 
            second=0, microsecond=0
        )
        end_dt = slot_date.replace(
            hour=int(end_parts[0]), 
            minute=int(end_parts[1]), 
            second=0, microsecond=0
        )
        
        new_slot = AvailabilitySlot(
            mentor_id=mentor.mentor_id,
            start_time=start_dt,
            end_time=end_dt,
            status=BookingStatus.AVAILABLE
        )
        db.add(new_slot)
        created_slots.append(new_slot)
    
    db.commit()
    return {"message": "Availability updated successfully", "slots_created": len(created_slots)}

@router.get("/mentors/availability")
def get_my_availability(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get mentor's own availability slots"""
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(400, "User is not a mentor")
    
    slots = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_id == mentor.mentor_id,
        AvailabilitySlot.status == BookingStatus.AVAILABLE
    ).all()
    
    return {
        "availability": [
            {
                "slot_id": s.slot_id,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "status": s.status.value if s.status else None
            }
            for s in slots
        ]
    }

@router.get("/mentors/bookings")
def get_mentor_bookings(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get all bookings for mentor"""
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(400, "User is not a mentor")
    
    bookings = db.query(Booking).join(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_id == mentor.mentor_id
    ).options(joinedload(Booking.learner)).all()
    
    return {
        "bookings": [
            {
                "booking_id": b.booking_id,
                "slot_id": b.slot_id,
                "learner_id": b.learner_id,
                "learner_name": b.learner.full_name if b.learner else None,
                "status": b.status,
                "created_at": b.created_at.isoformat() if b.created_at else None
            }
            for b in bookings
        ]
    }

@router.post("/mentors/{mentor_id}/book")
def book_mentor_session(
    mentor_id: int,
    booking_data: BookingRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """REQ-MENTOR-5: Learner books mentor session"""
    mentor = db.query(Mentor).filter(Mentor.mentor_id == mentor_id).first()
    if not mentor:
        raise HTTPException(404, "Mentor not found")
    
    # Parse requested date/time
    from datetime import timedelta
    try:
        requested_date = datetime.strptime(booking_data.date, "%Y-%m-%d")
        time_parts = booking_data.time.split(":")
        requested_dt = requested_date.replace(
            hour=int(time_parts[0]),
            minute=int(time_parts[1])
        )
    except ValueError:
        raise HTTPException(422, "Invalid date/time format")
    
    # Find available slot for this mentor at this time
    slot = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_id == mentor_id,
        AvailabilitySlot.status == BookingStatus.AVAILABLE,
        AvailabilitySlot.start_time <= requested_dt,
        AvailabilitySlot.end_time >= requested_dt
    ).first()
    
    if not slot:
        raise HTTPException(400, "No available slot at requested time")
    
    # Atomic update to prevent race condition
    result = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.slot_id == slot.slot_id,
        AvailabilitySlot.status == BookingStatus.AVAILABLE
    ).update({"status": BookingStatus.BOOKED})
    
    if result == 0:
        raise HTTPException(400, "Slot no longer available")
    
    new_booking = Booking(
        slot_id=slot.slot_id,
        learner_id=current_user.user_id,
        status="PENDING"
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    return {"message": "Booking created successfully", "booking_id": new_booking.booking_id}

@router.post("/mentors/bookings/{booking_id}/accept")
def accept_booking(
    booking_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Mentor accepts pending booking"""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    # Verify mentor ownership
    slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.slot_id == booking.slot_id).first()
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor or slot.mentor_id != mentor.mentor_id:
        raise HTTPException(403, "Not authorized to manage this booking")
    
    booking.status = "CONFIRMED"
    db.commit()
    return {"message": "Booking accepted", "booking_id": booking_id}

@router.post("/mentors/bookings/{booking_id}/reject")
def reject_booking(
    booking_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Mentor rejects pending booking"""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    # Verify mentor ownership
    slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.slot_id == booking.slot_id).first()
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor or slot.mentor_id != mentor.mentor_id:
        raise HTTPException(403, "Not authorized to manage this booking")
    
    # Release the slot back to available
    slot.status = BookingStatus.AVAILABLE
    booking.status = "REJECTED"
    db.commit()
    
    return {"message": "Booking rejected", "booking_id": booking_id}

# --- Learner Bookings ---

@router.get("/learners/bookings")
def get_learner_bookings(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get learner's own bookings"""
    bookings = db.query(Booking).filter(
        Booking.learner_id == current_user.user_id
    ).options(joinedload(Booking.slot)).all()
    
    return {
        "bookings": [
            {
                "booking_id": b.booking_id,
                "status": b.status,
                "created_at": b.created_at.isoformat() if b.created_at else None
            }
            for b in bookings
        ]
    }

@router.post("/learners/bookings/{booking_id}/cancel")
def cancel_learner_booking(
    booking_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Learner cancels their own booking"""
    booking = db.query(Booking).filter(
        Booking.booking_id == booking_id,
        Booking.learner_id == current_user.user_id
    ).first()
    
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    # Release the slot
    slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.slot_id == booking.slot_id).first()
    if slot:
        slot.status = BookingStatus.AVAILABLE
    
    booking.status = "CANCELLED"
    db.commit()
    
    return {"message": "Booking cancelled"}



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


# --- Issue #37: Mentor Resources/Documents ---

from app.models.mentor_review import MentorResource

class ResourceCreate(PydanticBase):
    title: str
    description: Optional[str] = None
    resource_type: str  # "document", "video", "link"
    file_url: str  # Pre-uploaded to Cloudinary or external URL
    is_public: bool = False

class ResourceUpdate(PydanticBase):
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

class ResourceResponse(PydanticBase):
    resource_id: int
    mentor_id: int
    title: str
    description: Optional[str]
    resource_type: str
    file_url: str
    is_public: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/mentor/resources", response_model=ResourceResponse)
def create_mentor_resource(
    data: ResourceCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Issue #37: Create mentor resource (document/video/link)
    Resource types: 'document', 'video', 'link'
    """
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(400, "User is not a mentor")
    
    # Validate resource type
    valid_types = ["document", "video", "link"]
    if data.resource_type.lower() not in valid_types:
        raise HTTPException(400, f"Invalid resource_type. Must be one of: {valid_types}")
    
    resource = MentorResource(
        mentor_id=current_user.user_id,  # FK to users.user_id
        title=data.title,
        description=data.description,
        resource_type=data.resource_type.lower(),
        file_url=data.file_url,
        is_public=data.is_public
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource

@router.get("/mentor/resources", response_model=List[ResourceResponse])
def get_mentor_resources(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Issue #37: Get mentor's resource library
    Returns all resources created by the mentor.
    """
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(400, "User is not a mentor")
    
    return db.query(MentorResource).filter(
        MentorResource.mentor_id == current_user.user_id
    ).order_by(MentorResource.created_at.desc()).all()

@router.get("/mentor/resources/{resource_id}", response_model=ResourceResponse)
def get_mentor_resource_detail(
    resource_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get single resource detail"""
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(400, "User is not a mentor")
    
    resource = db.query(MentorResource).filter(
        MentorResource.resource_id == resource_id,
        MentorResource.mentor_id == current_user.user_id
    ).first()
    
    if not resource:
        raise HTTPException(404, "Resource not found")
    
    return resource

@router.put("/mentor/resources/{resource_id}", response_model=ResourceResponse)
def update_mentor_resource(
    resource_id: int,
    data: ResourceUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Update mentor resource"""
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(400, "User is not a mentor")
    
    resource = db.query(MentorResource).filter(
        MentorResource.resource_id == resource_id,
        MentorResource.mentor_id == current_user.user_id
    ).first()
    
    if not resource:
        raise HTTPException(404, "Resource not found")
    
    if data.title:
        resource.title = data.title
    if data.description is not None:
        resource.description = data.description
    if data.is_public is not None:
        resource.is_public = data.is_public
    
    db.commit()
    db.refresh(resource)
    return resource

@router.delete("/mentor/resources/{resource_id}")
def delete_mentor_resource(
    resource_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Delete mentor resource"""
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(400, "User is not a mentor")
    
    resource = db.query(MentorResource).filter(
        MentorResource.resource_id == resource_id,
        MentorResource.mentor_id == current_user.user_id
    ).first()
    
    if not resource:
        raise HTTPException(404, "Resource not found")
    
    db.delete(resource)
    db.commit()
    return {"message": "Resource deleted successfully"}

@router.get("/resources/public", response_model=List[ResourceResponse])
def get_public_resources(
    resource_type: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get all public resources shared by mentors.
    Learners can access this to find learning materials.
    """
    query = db.query(MentorResource).filter(MentorResource.is_public == True)
    
    if resource_type:
        query = query.filter(MentorResource.resource_type == resource_type.lower())
    
    return query.order_by(MentorResource.created_at.desc()).all()

