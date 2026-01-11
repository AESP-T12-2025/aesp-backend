from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UserSavedVocab(Base):
    __tablename__ = "user_saved_vocab"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    word = Column(String, nullable=False, index=True)
    meaning = Column(Text, nullable=True)
    example_sentence = Column(Text, nullable=True)
    saved_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="saved_vocab")
