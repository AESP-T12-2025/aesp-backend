from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class TicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class TicketPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    ticket_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SqlEnum(TicketStatus), default=TicketStatus.OPEN)
    priority = Column(SqlEnum(TicketPriority), default=TicketPriority.MEDIUM)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="tickets")
