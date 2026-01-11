from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Enum as SqlEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class ChallengeType(str, enum.Enum):
    STREAK = "STREAK"
    SPEAKING_TIME = "SPEAKING_TIME"
    VOCAB_COUNT = "VOCAB_COUNT"

class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    challenge_type = Column(SqlEnum(ChallengeType), nullable=False)
    target_value = Column(Integer, nullable=False) # e.g., 7 days, 100 minutes
    points_reward = Column(Integer, default=10)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

class UserChallenge(Base):
    __tablename__ = "user_challenges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    current_progress = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="challenges")
    challenge = relationship("Challenge")

class UserDailyStats(Base):
    __tablename__ = "user_daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.current_date()) # Stores only date part usually logic handled
    speaking_duration_seconds = Column(Integer, default=0)
    words_learned = Column(Integer, default=0)
    login_streak_current = Column(Integer, default=0)

    user = relationship("User", backref="daily_stats")
