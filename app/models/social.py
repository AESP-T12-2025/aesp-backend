import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum as SqlEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ModerationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class MentorPost(Base):
    __tablename__ = "mentor_posts"

    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    moderation_status = Column(SqlEnum(ModerationStatus), default=ModerationStatus.APPROVED) # Default APPROVED to avoid breaking existing posts, or change to PENDING
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    mentor = relationship("User", backref="posts")
    comments = relationship("PostComment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")

class PostComment(Base):
    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("mentor_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    moderation_status = Column(SqlEnum(ModerationStatus), default=ModerationStatus.APPROVED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("MentorPost", back_populates="comments")
    user = relationship("User")

class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("mentor_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("MentorPost", back_populates="likes")
    user = relationship("User")
