from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SqlEnum, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class DifficultyLevel(str, enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"

class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    topics = relationship("Topic", back_populates="category")

class Topic(Base):
    __tablename__ = "topics"

    topic_id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)

    category = relationship("Category", back_populates="topics")
    scenarios = relationship("Scenario", back_populates="topic")

class Scenario(Base):
    __tablename__ = "scenarios"

    scenario_id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.topic_id"), nullable=False)
    title = Column(String, nullable=False)
    difficulty_level = Column(SqlEnum(DifficultyLevel), nullable=False)
    script_content = Column(Text, nullable=True) # Kịch bản mẫu cho AI đóng vai
    key_phrases = Column(JSON, nullable=True) # Gợi ý cho Advanced learners (JSONB in ERD, JSON in SQLAlchemy general)

    topic = relationship("Topic", back_populates="scenarios")

class SpeakingSession(Base):
    __tablename__ = "speaking_sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.scenario_id"), nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    score = Column(Integer, nullable=True) # Điểm số đánh giá (0-100)
    audio_url = Column(String, nullable=True) # Link file ghi âm (nếu có)
    status = Column(String, default="IN_PROGRESS") # Trạng thái session

    feedbacks = relationship("AIFeedback", back_populates="session")

class AIFeedback(Base):
    __tablename__ = "ai_feedbacks"

    feedback_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("speaking_sessions.session_id"), nullable=True)
    user_input_text = Column(Text, nullable=False)
    grammar_score = Column(Integer, default=0)
    pronunciation_score = Column(Integer, default=0)
    fluency_score = Column(Integer, default=0)
    better_version = Column(Text, nullable=True)
    feedback_details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("SpeakingSession", back_populates="feedbacks")
