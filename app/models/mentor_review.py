from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
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
