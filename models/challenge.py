from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from .base import Base  # Giả sử bạn có file base định nghĩa declarative_base

class Challenge(Base):
    __tablename__ = "challenges"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    points = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class UserChallenge(Base):
    __tablename__ = "user_challenges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True) # ID của người dùng
    challenge_id = Column(Integer, ForeignKey("challenges.id"))
    status = Column(String, default="joined") # joined, completed
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
