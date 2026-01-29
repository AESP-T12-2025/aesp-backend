"""
Payment Router
==============
Handles payment, packages, and subscription management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.utils import require_admin
from app.models.payment import ServicePackage, Transaction, UserSubscription, TransactionStatus
from app.models.user import User, UserRole


router = APIRouter(prefix="/payment", tags=["Payment & Packages"])


# =============================================================================
# SCHEMAS
# =============================================================================

class PackageResponse(BaseModel):
    """Response schema for service packages."""
    id: int
    name: str
    price: float
    description: Optional[str] = None
    features: Optional[Any] = None  # Supports list or dict
    mentor_included: bool = False
    
    class Config:
        from_attributes = True


class PaymentRequest(BaseModel):
    """Request schema for creating a payment transaction."""
    package_id: int
    payment_method: str = Field(default="MOCK_BANKING", description="Payment method")


class PackageCreate(BaseModel):
    """Schema for creating/updating a service package."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    price: float = Field(..., ge=0)
    duration_days: int = Field(default=30, ge=1, le=365)
    features: Optional[List[str]] = None
    mentor_included: bool = False
    is_active: bool = True


# =============================================================================
# PUBLIC APIs
# =============================================================================

@router.get("/packages", response_model=List[PackageResponse])
def list_packages(
    mentor_included: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List all active service packages.
    
    Args:
        mentor_included: Optional filter for mentor packages
    """
    query = db.query(ServicePackage).filter(ServicePackage.is_active == True)
    if mentor_included is not None:
        query = query.filter(ServicePackage.mentor_included == mentor_included)
    return query.all()


@router.post("/create-transaction")
def create_mock_payment(
    req: PaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a mock payment transaction (for development/testing).
    
    In production, this would integrate with a real payment gateway.
    """
    # 1. Validate Package
    package = db.query(ServicePackage).filter(ServicePackage.id == req.package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
        
    # 2. Create Pending Transaction
    new_txn = Transaction(
        user_id=current_user.user_id,
        package_id=package.id,
        amount=package.price,
        status=TransactionStatus.PENDING,
        payment_method=req.payment_method
    )
    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)
    
    # 3. MOCK: Auto-success for testing
    # In production, this would be handled by a webhook callback
    new_txn.status = TransactionStatus.SUCCESS
    
    # Calculate subscription dates (timezone-aware)
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=package.duration_days)
    
    # Deactivate existing active subscriptions
    db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.user_id,
        UserSubscription.is_active == True
    ).update({"is_active": False})
    
    # Create new subscription
    new_sub = UserSubscription(
        user_id=current_user.user_id,
        package_id=package.id,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
    
    db.add(new_sub)
    db.commit()
    
    return {
        "message": "Payment successful (Mocked)",
        "transaction_id": new_txn.id,
        "subscription_end_date": end_date.isoformat()
    }


@router.get("/my-subscription")
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's active subscription status."""
    sub = db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.user_id,
        UserSubscription.is_active == True
    ).order_by(UserSubscription.end_date.desc()).first()
    
    if not sub:
        return {"has_subscription": False, "plan": None}
    
    package = db.query(ServicePackage).filter(ServicePackage.id == sub.package_id).first()
    now = datetime.now(timezone.utc)
    
    # Handle naive datetime comparison
    end_date = sub.end_date
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    
    return {
        "has_subscription": True,
        "plan": package.name if package else "Unknown",
        "status": "active" if end_date > now else "expired",
        "start_date": sub.start_date.isoformat(),
        "end_date": sub.end_date.isoformat(),
        "package_id": sub.package_id
    }


# Alias for /my-subscription (Issue #42 tests use this path)
@router.get("/subscription")
def get_subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's subscription - alias for /my-subscription"""
    return get_my_subscription(db, current_user)


# =============================================================================
# ADMIN APIs - Package CRUD
# =============================================================================

@router.post("/packages", response_model=PackageResponse)
def create_package(
    data: PackageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new service package. Admin only."""
    require_admin(current_user)
    
    pkg = ServicePackage(**data.model_dump())
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


@router.put("/packages/{package_id}", response_model=PackageResponse)
def update_package(
    package_id: int,
    data: PackageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing service package. Admin only."""
    require_admin(current_user)
    
    pkg = db.query(ServicePackage).filter(ServicePackage.id == package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    
    for key, value in data.model_dump().items():
        setattr(pkg, key, value)
    
    db.commit()
    db.refresh(pkg)
    return pkg


@router.delete("/packages/{package_id}")
def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a service package. Admin only."""
    require_admin(current_user)
    
    pkg = db.query(ServicePackage).filter(ServicePackage.id == package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    
    db.delete(pkg)
    db.commit()
    return {"message": "Package deleted successfully"}


# =============================================================================
# SUBSCRIPTION MANAGEMENT
# =============================================================================

@router.post("/upgrade")
def upgrade_subscription(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upgrade to a new subscription package."""
    package = db.query(ServicePackage).filter(ServicePackage.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    # Deactivate old subscriptions
    db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.user_id,
        UserSubscription.is_active == True
    ).update({"is_active": False})
    
    # Create new subscription (timezone-aware)
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=package.duration_days)
    
    new_sub = UserSubscription(
        user_id=current_user.user_id,
        package_id=package.id,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
    db.add(new_sub)
    db.commit()
    
    return {
        "message": "Subscription upgraded successfully",
        "end_date": end_date.isoformat()
    }


@router.post("/cancel")
def cancel_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel user's active subscription."""
    result = db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.user_id,
        UserSubscription.is_active == True
    ).update({"is_active": False})
    
    db.commit()
    
    if result == 0:
        return {"message": "No active subscription to cancel"}
    
    return {"message": "Subscription cancelled successfully"}
