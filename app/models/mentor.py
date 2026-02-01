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
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True, index=True)
    full_name = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    skills = Column(String, nullable=True) # Comma separated skills for simplicity per PR
    verification_status = Column(String, default="PENDING") # PENDING, VERIFIED, REJECTED

    user = relationship("app.models.user.User", backref="mentor_profile")
    slots = relationship("AvailabilitySlot", back_populates="mentor")

class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    slot_id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("mentors.mentor_id"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(SqlEnum(BookingStatus), default=BookingStatus.AVAILABLE)

    mentor = relationship("Mentor", back_populates="slots")
    booking = relationship("Booking", back_populates="slot", uselist=False)

class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("availability_slots.slot_id"), nullable=False, unique=True, index=True)
    learner_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="PENDING")  # PENDING -> CONFIRMED -> COMPLETED
    meeting_link = Column(String, nullable=True)  # Google Meet/Zoom link from mentor

    slot = relationship("AvailabilitySlot", back_populates="booking")
    learner = relationship("app.models.user.User", foreign_keys=[learner_id])
    assessment = relationship("MentorAssessment", back_populates="booking", uselist=False)

class MentorAssessment(Base):
    """
    Consolidated post-session assessment from Mentor.
    Covers: pronunciation, grammar, vocabulary, fluency, and overall feedback.
    """
    __tablename__ = "mentor_assessments"

    assessment_id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False, index=True)
    
    # Overall Score (1-10)
    score = Column(Integer, nullable=True)
    
    # Detailed Scores (1-10 each)
    pronunciation_score = Column(Integer, nullable=True)
    grammar_score = Column(Integer, nullable=True)
    vocabulary_score = Column(Integer, nullable=True)
    fluency_score = Column(Integer, nullable=True)
    
    # Level Assignment (A1, A2, B1, B2, C1, C2)
    level_assigned = Column(String(10), nullable=True)
    
    # Detailed Feedback / Notes
    feedback = Column(Text, nullable=True)  # General feedback
    pronunciation_notes = Column(Text, nullable=True)  # Pronunciation errors & tips
    grammar_notes = Column(Text, nullable=True)  # Grammar corrections
    vocabulary_tips = Column(Text, nullable=True)  # Vocabulary, collocations, idioms
    communication_tips = Column(Text, nullable=True)  # How to express more clearly
    
    # Shared Resources (JSON or comma-separated resource IDs)
    shared_resource_ids = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    booking = relationship("Booking", back_populates="assessment")
