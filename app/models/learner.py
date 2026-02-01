from sqlalchemy import Column, Integer, String, JSON, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class LearnerRankTier(str, enum.Enum):
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"

class LearnerProfile(Base):
    __tablename__ = "learner_profiles"

    profile_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True)
    current_proficiency_level = Column(String, nullable=True)
    target_level = Column(String, nullable=True)
    learning_preferences = Column(JSON, nullable=True)
    streak_count = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)
    current_rank_tier = Column(SqlEnum(LearnerRankTier, name="learner_rank_tier"), default=LearnerRankTier.BRONZE)

    user = relationship("User", backref="learner_profile")
