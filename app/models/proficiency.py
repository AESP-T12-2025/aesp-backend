from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ProficiencyTest(Base):
    __tablename__ = "proficiency_tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False) # e.g. "Entrance Test A1-B2"
    questions_json = Column(JSON, nullable=False) # Stores list of questions/answers
    level_criteria_json = Column(JSON, nullable=True) # Logic for mapping score -> level
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserTestResult(Base):
    __tablename__ = "user_test_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    test_id = Column(Integer, ForeignKey("proficiency_tests.id"), nullable=False)
    score = Column(Float, nullable=False)
    assessed_level = Column(String, nullable=False) # A1, A2, B1, ...
    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="test_results")
    test = relationship("ProficiencyTest")

class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    current_level = Column(String, nullable=False)
    target_level = Column(String, nullable=False)
    generated_roadmap_json = Column(JSON, nullable=True) # List of recommended topics/challenges
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="learning_path")
