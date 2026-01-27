from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class SystemPolicy(Base):
    __tablename__ = "system_policies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String, default="TERMS") # TERMS, PRIVACY, REFUND
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
