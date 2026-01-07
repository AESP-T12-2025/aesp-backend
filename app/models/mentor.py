from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SqlEnum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class BookingStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Mentor(Base):
    __tablename__ = "mentors"

    mentor_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)
    full_name = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    skills = Column(String, nullable=True) # Comma separated skills for simplicity per PR
    verification_status = Column(String, default="PENDING") # PENDING, VERIFIED, REJECTED

    user = relationship("app.models.user.User", backref="mentor_profile")
    slots = relationship("AvailabilitySlot", back_populates="mentor")

class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    slot_id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("mentors.mentor_id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(SqlEnum(BookingStatus), default=BookingStatus.AVAILABLE)

    mentor = relationship("Mentor", back_populates="slots")
    booking = relationship("Booking", back_populates="slot", uselist=False)

class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("availability_slots.slot_id"), nullable=False, unique=True)
    learner_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="CONFIRMED")

    slot = relationship("AvailabilitySlot", back_populates="booking")
    learner = relationship("app.models.user.User", foreign_keys=[learner_id])
    assessment = relationship("MentorAssessment", back_populates="booking", uselist=False)

class MentorAssessment(Base):
    __tablename__ = "mentor_assessments"

    assessment_id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False)
    score = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    booking = relationship("Booking", back_populates="assessment")
