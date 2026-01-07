from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class MentorReview(Base):
    __tablename__ = "mentor_reviews"

    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, nullable=False) # ID của người đánh giá
    learner_id = Column(Integer, nullable=False) # ID của người được đánh giá
    session_id = Column(Integer, nullable=True)  # ID buổi học liên quan
    note = Column(Text, nullable=True)           # Nội dung nhận xét (Note)
    created_at = Column(DateTime, server_default=func.now())

    # Quan hệ 1-nhiều với bảng Assessments
    assessments = relationship("MentorAssessment", back_populates="review", cascade="all, delete-orphan")

class MentorAssessment(Base):
    __tablename__ = "mentor_assessments"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("mentor_reviews.id"))
    criteria_name = Column(String(255), nullable=False) 
    score = Column(Integer, nullable=False)            
    
    review = relationship("MentorReview", back_populates="assessments")
