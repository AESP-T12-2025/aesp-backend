from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Enum as SqlEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class ServicePackage(Base):
    __tablename__ = "service_packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    duration_days = Column(Integer, nullable=False) # e.g., 30 for 1 month
    features = Column(JSON, nullable=True) # e.g., {"with_mentor": true, "ai_limit": 100}
    is_active = Column(Boolean, default=True)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    package_id = Column(Integer, ForeignKey("service_packages.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(SqlEnum(TransactionStatus), default=TransactionStatus.PENDING)
    payment_method = Column(String, nullable=True) # e.g., "MOMO", "VNPAY", "MOCK"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="transactions")
    package = relationship("ServicePackage")

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    package_id = Column(Integer, ForeignKey("service_packages.id"), nullable=False)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User", backref="subscription")
    package = relationship("ServicePackage")
