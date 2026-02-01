from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core import database, deps
from app.models.mentor import Mentor, AvailabilitySlot, Booking, BookingStatus
from app.models.user import User
from app.schemas.mentor import MentorSchema, MentorResponse, SlotCreate, BookingCreate, MentorCreate

router = APIRouter()

class BookingRequest(BaseModel):
    date: str
    time: str

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
    # Check role
    user_role = str(current_user.role).upper() if current_user.role else ""
    if "MENTOR" not in user_role:
        raise HTTPException(status_code=403, detail="Only mentors can create slots")
    
    # Get or create mentor profile
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        mentor = Mentor(
            user_id=current_user.user_id,
            full_name=current_user.full_name or "Mentor",
            verification_status="PENDING"
        )
        db.add(mentor)
        db.commit()
        db.refresh(mentor)

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


# =============================================================================
# Issue #29: Mentor Sessions (for assessment organization)
# =============================================================================

class ScheduleAssessmentRequest(BaseModel):
    learner_id: int
    date: str
    type: str = "speaking_assessment"


@router.get("/mentor-sessions")
def get_mentor_sessions(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user),
    status: str = None
):
    """
    Issue #29: Get mentor's sessions for assessment organization.
    Returns list of bookings/sessions for the authenticated mentor.
    """
    from app.models.user import UserRole
    
    # Check if user is a mentor
    user_role = str(current_user.role).upper() if current_user.role else ""
    if "MENTOR" not in user_role:
        raise HTTPException(403, "Only mentors can access this endpoint")
    
    # Get mentor profile
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    
    if not mentor:
        # Return empty list if no mentor profile
        return {"sessions": []}
    
    # Get all bookings for this mentor via slots (Booking has no mentor_id directly)
    query = db.query(Booking).join(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_id == mentor.mentor_id
    ).options(
        joinedload(Booking.learner),
        joinedload(Booking.slot)
    )
    
    # Filter by status if provided
    if status:
        query = query.filter(Booking.status == status)
    
    bookings = query.all()
    
    sessions = []
    for b in bookings:
        sessions.append({
            "id": b.booking_id,
            "session_id": b.booking_id,
            "booking_id": b.booking_id,
            "learner": {
                "id": b.learner.user_id if b.learner else None,
                "name": b.learner.full_name if b.learner else None,
                "email": b.learner.email if b.learner else None
            } if b.learner else None,
            "date": b.slot.start_time.isoformat() if b.slot and b.slot.start_time else None,
            "status": b.status.value if hasattr(b.status, 'value') else str(b.status),
            "created_at": b.created_at.isoformat() if hasattr(b, 'created_at') and b.created_at else None
        })
    
    return {"sessions": sessions}


@router.post("/mentor-sessions/schedule")
def schedule_assessment(
    data: ScheduleAssessmentRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Issue #29: Schedule assessment session for a learner.
    """
    from app.models.user import UserRole
    
    # Check if user is a mentor
    user_role = str(current_user.role).upper() if current_user.role else ""
    if "MENTOR" not in user_role:
        raise HTTPException(403, "Only mentors can schedule assessments")
    
    # Get or create mentor profile
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        mentor = Mentor(
            user_id=current_user.user_id,
            full_name=current_user.full_name or "Mentor",
            verification_status="PENDING"
        )
        db.add(mentor)
        db.commit()
        db.refresh(mentor)
    
    # Parse date
    from datetime import datetime
    try:
        session_date = datetime.fromisoformat(data.date.replace("Z", "+00:00"))
    except:
        raise HTTPException(422, "Invalid date format")
    
    # Create availability slot
    slot = AvailabilitySlot(
        mentor_id=mentor.mentor_id,
        start_time=session_date,
        end_time=session_date + timedelta(hours=1),
        status=BookingStatus.BOOKED
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    
    # Create booking
    booking = Booking(
        slot_id=slot.slot_id,
        learner_id=data.learner_id,
        status="SCHEDULED"
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    return {
        "message": "Assessment scheduled successfully",
        "session_id": booking.booking_id,
        "date": session_date.isoformat(),
        "type": data.type
    }



# =============================================================================
# Issue #37: Mentor Resources (Documents/Videos/Links)
# =============================================================================

from app.models.mentor_review import MentorResource

class MentorResourceCreate(PydanticBase):
    title: str
    description: Optional[str] = None
    resource_type: str = "document"  # document, video, link
    file_url: str
    is_public: bool = False


class MentorResourceUpdate(PydanticBase):
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


@router.get("/mentor/resources")
def list_mentor_resources(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #37: List mentor's resources."""
    resources = db.query(MentorResource).filter(
        MentorResource.mentor_id == current_user.user_id
    ).all()
    
    return [
        {
            "id": r.resource_id,
            "resource_id": r.resource_id,
            "title": r.title,
            "description": r.description,
            "resource_type": r.resource_type,
            "file_url": r.file_url,
            "is_public": r.is_public if hasattr(r, 'is_public') else False,
            "created_at": r.created_at.isoformat() if hasattr(r, 'created_at') and r.created_at else None
        }
        for r in resources
    ]


@router.post("/mentor/resources")
def create_mentor_resource(
    data: MentorResourceCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #37: Create a new mentor resource."""
    # Verify user has mentor role
    user_role = str(current_user.role).upper() if current_user.role else ""
    if "MENTOR" not in user_role:
        raise HTTPException(403, "Only mentors can create resources")
    
    # Validate resource type (normalize to lowercase)
    allowed_types = ["document", "video", "link", "audio"]
    resource_type_normalized = data.resource_type.lower()
    if resource_type_normalized not in allowed_types:
        raise HTTPException(400, f"Invalid resource type. Allowed types: {', '.join(allowed_types)}")
    
    resource = MentorResource(
        mentor_id=current_user.user_id,
        title=data.title,
        description=data.description,
        resource_type=resource_type_normalized,
        file_url=data.file_url,
        is_public=data.is_public
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    
    return {
        "id": resource.resource_id,
        "resource_id": resource.resource_id,
        "title": resource.title,
        "description": resource.description,
        "resource_type": resource.resource_type,
        "file_url": resource.file_url,
        "is_public": resource.is_public if hasattr(resource, 'is_public') else False,
        "message": "Resource created successfully"
    }


@router.get("/mentor/resources/{resource_id}")
def get_mentor_resource(
    resource_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #37: Get a specific mentor resource."""
    resource = db.query(MentorResource).filter(
        MentorResource.resource_id == resource_id
    ).first()
    
    if not resource:
        raise HTTPException(404, "Resource not found")
    
    # Check ownership or public status
    is_owner = resource.mentor_id == current_user.user_id
    is_public = getattr(resource, 'is_public', False)
    
    if not is_owner and not is_public:
        raise HTTPException(403, "Access denied")
    
    return {
        "id": resource.resource_id,
        "resource_id": resource.resource_id,
        "title": resource.title,
        "description": resource.description,
        "resource_type": resource.resource_type,
        "file_url": resource.file_url,
        "is_public": is_public,
        "mentor_id": resource.mentor_id
    }


@router.put("/mentor/resources/{resource_id}")
def update_mentor_resource(
    resource_id: int,
    data: MentorResourceUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #37: Update a mentor resource."""
    resource = db.query(MentorResource).filter(
        MentorResource.resource_id == resource_id,
        MentorResource.mentor_id == current_user.user_id
    ).first()
    
    if not resource:
        raise HTTPException(404, "Resource not found or access denied")
    
    if data.title is not None:
        resource.title = data.title
    if data.description is not None:
        resource.description = data.description
    if data.is_public is not None:
        resource.is_public = data.is_public
    
    db.commit()
    db.refresh(resource)
    
    return {
        "id": resource.resource_id,
        "title": resource.title,
        "description": resource.description,
        "resource_type": resource.resource_type,
        "is_public": resource.is_public if hasattr(resource, 'is_public') else False,
        "message": "Resource updated successfully"
    }


@router.delete("/mentor/resources/{resource_id}")
def delete_mentor_resource(
    resource_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #37: Delete a mentor resource."""
    resource = db.query(MentorResource).filter(
        MentorResource.resource_id == resource_id,
        MentorResource.mentor_id == current_user.user_id
    ).first()
    
    if not resource:
        raise HTTPException(404, "Resource not found or access denied")
    
    db.delete(resource)
    db.commit()
    
    return {"message": "Resource deleted successfully"}


@router.get("/resources")
def get_public_resources(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #37: Get all public resources (for learners)."""
    resources = db.query(MentorResource).filter(
        MentorResource.is_public == True
    ).all()
    
    return [
        {
            "id": r.resource_id,
            "title": r.title,
            "description": r.description,
            "resource_type": r.resource_type,
            "file_url": r.file_url,
            "mentor_id": r.mentor_id
        }
        for r in resources
    ]


# =============================================================================
# Issue #36: Mentor Vocabulary Suggestions (alternate path)
# =============================================================================

class VocabSuggestRequest(PydanticBase):
    word: Optional[str] = None
    vocabulary: Optional[str] = None
    topic_id: Optional[int] = None
    collocations: Optional[str] = None
    idioms: Optional[str] = None
    tips: Optional[str] = None


@router.post("/mentor/vocabulary/suggest")
def suggest_vocabulary(
    data: VocabSuggestRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #36: Mentor suggests vocabulary to learner."""
    # Check if user is a mentor
    user_role = str(current_user.role).upper() if current_user.role else ""
    if "MENTOR" not in user_role:
        raise HTTPException(403, "Only mentors can suggest vocabulary")
    
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        # Auto-create mentor profile
        mentor = Mentor(
            user_id=current_user.user_id,
            full_name=current_user.full_name or "Mentor",
            verification_status="PENDING"
        )
        db.add(mentor)
        db.commit()
        db.refresh(mentor)
    
    vocab_word = data.word or data.vocabulary or "Unknown"
    suggestion = MentorVocabSuggestion(
        mentor_id=mentor.mentor_id,
        topic_id=data.topic_id,
        vocabulary=vocab_word,
        collocations=data.collocations,
        idioms=data.idioms,
        tips=data.tips
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    
    return {
        "id": suggestion.id,
        "vocabulary": suggestion.vocabulary,
        "message": "Vocabulary suggested successfully"
    }


# =============================================================================
# Issue #37: Public Resources Endpoint  
# =============================================================================

@router.get("/resources/public")
def get_all_public_resources(
    resource_type: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #37: Get all public resources available to learners."""
    query = db.query(MentorResource).filter(MentorResource.is_public == True)
    
    if resource_type:
        query = query.filter(MentorResource.resource_type == resource_type)
    
    resources = query.all()
    
    return [
        {
            "id": r.resource_id,
            "resource_id": r.resource_id,
            "title": r.title,
            "description": r.description,
            "resource_type": r.resource_type,
            "file_url": r.file_url,
            "mentor_id": r.mentor_id,
            "is_public": r.is_public
        }
        for r in resources
    ]


# =============================================================================
# Issue #30: Booking System Endpoints
# =============================================================================

class SlotInput(PydanticBase):
    day: Optional[str] = None
    start_time: str
    end_time: str
    date: Optional[str] = None


class AvailabilityInput(PydanticBase):
    slots: List[SlotInput]


@router.post("/mentors/availability")
def set_mentor_availability(
    data: AvailabilityInput,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #30: Mentor sets availability slots."""
    user_role = str(current_user.role).upper() if current_user.role else ""
    if "MENTOR" not in user_role:
        raise HTTPException(403, "Only mentors can set availability")
    
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        mentor = Mentor(
            user_id=current_user.user_id,
            full_name=current_user.full_name or "Mentor",
            verification_status="PENDING"
        )
        db.add(mentor)
        db.commit()
        db.refresh(mentor)
    
    slots_created = 0
    for slot_data in data.slots:
        # Parse times
        from datetime import datetime
        base_date = datetime.now() + timedelta(days=1)
        start_str = slot_data.start_time
        end_str = slot_data.end_time
        
        try:
            start_time = datetime.strptime(f"{base_date.date()} {start_str}", "%Y-%m-%d %H:%M")
            end_time = datetime.strptime(f"{base_date.date()} {end_str}", "%Y-%m-%d %H:%M")
            
            # Validate time order
            if end_time <= start_time:
                raise HTTPException(422, "End time must be after start time")
        except HTTPException:
            raise
        except:
            continue
        
        slot = AvailabilitySlot(
            mentor_id=mentor.mentor_id,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.AVAILABLE
        )
        db.add(slot)
        slots_created += 1
    
    db.commit()
    return {"message": "Availability set successfully", "slots_created": slots_created}


@router.get("/mentors/availability")
def get_mentor_availability(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #30: Get mentor's availability slots."""
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        return {"availability": []}
    
    slots = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_id == mentor.mentor_id
    ).all()
    
    return {
        "availability": [
            {
                "id": s.slot_id,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "status": s.status.value if hasattr(s.status, 'value') else str(s.status)
            }
            for s in slots
        ]
    }


@router.get("/mentors/bookings")
def get_mentor_bookings(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #30: Get mentor's bookings."""
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        return {"bookings": []}
    
    # Get bookings via slots (Booking doesn't have mentor_id directly)
    bookings = db.query(Booking).join(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_id == mentor.mentor_id
    ).options(
        joinedload(Booking.learner),
        joinedload(Booking.slot)
    ).all()
    
    return {
        "bookings": [
            {
                "booking_id": b.booking_id,
                "learner_id": b.learner_id,
                "learner_name": b.learner.full_name if b.learner else None,
                "start_time": b.slot.start_time.isoformat() if b.slot and b.slot.start_time else None,
                "end_time": b.slot.end_time.isoformat() if b.slot and b.slot.end_time else None,
                "status": b.status.value if hasattr(b.status, 'value') else str(b.status)
            }
            for b in bookings
        ]
    }


@router.post("/mentors/{mentor_id}/book")
def book_mentor(
    mentor_id: int,
    booking: BookingRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #30: Learner books a mentor's slot."""
    from datetime import datetime
    
    # Check if mentor exists
    mentor = db.query(Mentor).filter(Mentor.mentor_id == mentor_id).first()
    if not mentor:
        raise HTTPException(404, "Mentor not found")
    
    # Find slot by mentor_id and time
    try:
        requested_datetime = datetime.strptime(f"{booking.date} {booking.time}", "%Y-%m-%d %H:%M")
    except:
        raise HTTPException(422, "Invalid date or time format")
    
    slot = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_id == mentor_id,
        AvailabilitySlot.start_time == requested_datetime
    ).first()
    
    if not slot or slot.status != BookingStatus.AVAILABLE:
        raise HTTPException(400, "Slot is not available")
    
    booking_obj = Booking(
        slot_id=slot.slot_id,
        learner_id=current_user.user_id,
        status="CONFIRMED"
    )
    slot.status = BookingStatus.BOOKED
    
    db.add(booking_obj)
    db.commit()
    db.refresh(booking_obj)
    
    return {"message": "Booking created", "booking_id": booking_obj.booking_id}


@router.post("/bookings")
def create_booking(
    slot_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #30: Learner books an available slot."""
    slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.slot_id == slot_id).first()
    if not slot:
        raise HTTPException(404, "Slot not found")
    
    if slot.status != BookingStatus.AVAILABLE:
        raise HTTPException(400, "Slot is not available")
    
    booking = Booking(
        slot_id=slot.slot_id,
        learner_id=current_user.user_id,
        status="CONFIRMED"
    )
    slot.status = BookingStatus.BOOKED
    
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    return {"message": "Booking created", "booking_id": booking.booking_id}


@router.post("/mentors/bookings/{booking_id}/accept")
def accept_booking(
    booking_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #30: Mentor accepts a booking."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    booking.status = "CONFIRMED"
    db.commit()
    return {"message": "Booking accepted", "status": "CONFIRMED"}


@router.post("/mentors/bookings/{booking_id}/reject")
def reject_booking(
    booking_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #30: Mentor rejects a booking."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    booking.status = "REJECTED"
    if booking.slot:
        booking.slot.status = BookingStatus.AVAILABLE
    db.commit()
    return {"message": "Booking rejected", "status": "REJECTED"}


@router.get("/learners/bookings")
def get_learner_bookings(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #30: Get learner's bookings."""
    bookings = db.query(Booking).filter(
        Booking.learner_id == current_user.user_id
    ).options(
        joinedload(Booking.slot).joinedload(AvailabilitySlot.mentor)
    ).all()
    
    return {
        "bookings": [
            {
                "id": b.booking_id,
                "mentor_id": b.slot.mentor.mentor_id if b.slot and b.slot.mentor else None,
                "start_time": b.slot.start_time.isoformat() if b.slot and b.slot.start_time else None,
                "status": b.status.value if hasattr(b.status, 'value') else str(b.status)
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
    """Issue #30: Learner cancels their booking."""
    booking = db.query(Booking).filter(
        Booking.booking_id == booking_id,
        Booking.learner_id == current_user.user_id
    ).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    booking.status = "CANCELLED"
    if booking.slot:
        booking.slot.status = BookingStatus.AVAILABLE
    db.commit()
    
    return {"message": "Booking cancelled"}


# =============================================================================
# Issue #29: Schedule Assessment Endpoints
# =============================================================================

class ScheduleAssessmentRequest(PydanticBase):
    learner_id: int
    scheduled_time: str
    assessment_type: Optional[str] = "speaking"
    notes: Optional[str] = None


@router.post("/mentor/assessments/schedule")
def schedule_assessment(
    data: ScheduleAssessmentRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Issue #29: Mentor schedules assessment for learner."""
    user_role = str(current_user.role).upper() if current_user.role else ""
    if "MENTOR" not in user_role:
        raise HTTPException(403, "Only mentors can schedule assessments")
    
    # Create a booking/session for assessment
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        mentor = Mentor(
            user_id=current_user.user_id,
            full_name=current_user.full_name or "Mentor",
            verification_status="PENDING"
        )
        db.add(mentor)
        db.commit()
        db.refresh(mentor)
    
    # Create availability slot for assessment
    try:
        from datetime import datetime
        scheduled = datetime.fromisoformat(data.scheduled_time.replace("Z", "+00:00"))
    except:
        scheduled = datetime.now() + timedelta(days=1)
    
    slot = AvailabilitySlot(
        mentor_id=mentor.mentor_id,
        start_time=scheduled,
        end_time=scheduled + timedelta(hours=1),
        status=BookingStatus.BOOKED
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    
    booking = Booking(
        slot_id=slot.slot_id,
        mentor_id=mentor.mentor_id,
        learner_id=data.learner_id,
        status=BookingStatus.CONFIRMED,
        notes=data.notes
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    return {
        "message": "Assessment scheduled",
        "assessment_id": booking.booking_id,
        "scheduled_time": scheduled.isoformat()
    }
