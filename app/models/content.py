from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SqlEnum, JSON
from sqlalchemy.orm import relationship
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
