from sqlalchemy import Boolean, Column, Integer, String, Enum as SqlEnum, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MENTOR = "MENTOR"
    LEARNER = "LEARNER"

class AuthProvider(str, enum.Enum):
    LOCAL = "LOCAL"
    GOOGLE = "GOOGLE"

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True) # Renamed from id to user_id to match ERD
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True) # Nullable for Google Auth
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    role = Column(SqlEnum(UserRole), default=UserRole.LEARNER)
    auth_provider = Column(SqlEnum(AuthProvider), default=AuthProvider.LOCAL)
    is_active = Column(Boolean, default=True)
    daily_learning_goal = Column(Integer, default=15) # Minutes/day
    bonus_xp = Column(Integer, default=0) # XP earned from challenges/events
    created_at = Column(DateTime, default=func.now())

    # Backwards compatibility properties if needed, or update codebase to use user_id
    @property
    def id(self):
        return self.user_id
