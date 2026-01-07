from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core import database, deps
from app.models.mentor import Mentor, AvailabilitySlot, Booking, BookingStatus, MentorAssessment
from app.models.user import User
from app.schemas.mentor import MentorSchema, MentorResponse, SlotCreate, BookingCreate, MentorCreate, AssessmentCreate, AssessmentResponse

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
    # 1. Kiểm tra slot có tồn tại và còn trống không
    slot = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.slot_id == booking_in.slot_id, 
        AvailabilitySlot.status == BookingStatus.AVAILABLE
    ).first()
    
    if not slot:
        raise HTTPException(status_code=400, detail="Slot này không còn trống hoặc không tồn tại")

    # 2. Cập nhật trạng thái slot thành BOOKED
    slot.status = BookingStatus.BOOKED
    
    # 3. Tạo record Booking mới
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
        db.rollback()
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
def get_slots_by_mentor(
    mentor_id: int,
    db: Session = Depends(database.get_db)
):
    slots = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_id == mentor_id,
        AvailabilitySlot.status == BookingStatus.AVAILABLE
    ).all()
    return slots

@router.get("/mentors/my-bookings")
def get_my_bookings(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Get mentor profile
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor profile not found")
    
    # Get all bookings for this mentor's slots
    bookings = db.query(Booking).join(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_id == mentor.mentor_id
    ).all()
    
    return bookings

@router.put("/mentors/{id}/verify")
def verify_mentor(
    id: int,
    db: Session = Depends(database.get_db),
    # current_user: User = Depends(deps.get_current_user) # Add Auth check if needed
):
    mentor = db.query(Mentor).filter(Mentor.mentor_id == id).first()
    if not mentor:
         raise HTTPException(status_code=404, detail="Mentor not found")
    
    mentor.verification_status = "VERIFIED"
    db.commit()
    db.refresh(mentor)
    return {"message": "Mentor verified successfully", "status": mentor.verification_status}

@router.post("/mentors/reviews", response_model=AssessmentResponse)
def create_review(
    assessment: AssessmentCreate,
    db: Session = Depends(database.get_db),
    # current_user: User = Depends(deps.get_current_user)
):
    # Verify booking exists
    booking = db.query(Booking).filter(Booking.booking_id == assessment.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    # Check if already reviewed (optional but good)
    if booking.assessment:
         raise HTTPException(status_code=400, detail="Booking already reviewed")

    new_assessment = MentorAssessment(
        booking_id=assessment.booking_id,
        score=assessment.score,
        feedback=assessment.feedback
    )
    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)
    return new_assessment
