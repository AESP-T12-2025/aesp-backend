from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class MentorReview(Base):
    __tablename__ = "mentor_reviews"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False, unique=True)
    mentor_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    learner_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    # Detailed Scoring (1-5 or 1-10)
    pronunciation_score = Column(Integer, nullable=True)
    fluency_score = Column(Integer, nullable=True)
    grammar_score = Column(Integer, nullable=True)
    lexical_score = Column(Integer, nullable=True)

    # Qualitative Feedback
    general_feedback = Column(Text, nullable=True)
    actionable_next_steps = Column(Text, nullable=True) # "Guide how to express..."

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # booking relationship might need to be imported or lazy loaded if circular import
    booking = relationship("Booking", backref="detailed_review")
    mentor = relationship("User", foreign_keys=[mentor_id])
    learner = relationship("User", foreign_keys=[learner_id])

class MentorResource(Base):
    """
    Issue #37: Mentor Resources/Documents
    Enhanced with is_public for sharing with learners.
    """
    __tablename__ = "mentor_resources"

    resource_id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=False)
    resource_type = Column(String(50), default="DOCUMENT")  # DOCUMENT, VIDEO, AUDIO, LINK
    is_public = Column(Boolean, default=False)  # Share with all learners?
    file_size = Column(Integer, nullable=True)  # bytes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    mentor = relationship("User", backref="resources")

