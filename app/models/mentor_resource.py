from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class MentorVocabSuggestion(Base):
    __tablename__ = "mentor_vocab_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("mentors.mentor_id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.topic_id"), nullable=True) # Optional, can be general
    vocabulary = Column(String, nullable=False)
    collocations = Column(Text, nullable=True)
    idioms = Column(Text, nullable=True)
    tips = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    mentor = relationship("app.models.mentor.Mentor")
    topic = relationship("app.models.content.Topic")


# Note: MentorResource model is defined in mentor_review.py to avoid duplication
# Import from there: from app.models.mentor_review import MentorResource
