from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.payment import ServicePackage, Transaction, UserSubscription, TransactionStatus
from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter(prefix="/payment", tags=["Payment & Packages"])

# --- Schemas ---
class PackageResponse(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str]
    features: Optional[Any]  # Changed from dict to Any to support list or dict
    mentor_included: bool = False
    
    class Config:
        orm_mode = True

class PaymentRequest(BaseModel):
    package_id: int
    payment_method: str = "MOCK_BANKING"

# --- APIs ---

@router.get("/packages", response_model=List[PackageResponse])
def list_packages(
    mentor_included: Optional[bool] = None,
    db: Session = Depends(get_db)
):
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
    # 1. Validate Package
    package = db.query(ServicePackage).filter(ServicePackage.id == req.package_id).first()
    if not package:
        raise HTTPException(404, "Package not found")
        
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
    
    # 3. MOCK: Auto-success for testing (In production, this would be a webhook callback)
    # Automatically grant subscription
    new_txn.status = TransactionStatus.SUCCESS
    
    # Calculate end date
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=package.duration_days)
    
    new_sub = UserSubscription(
        user_id=current_user.user_id,
        package_id=package.id,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
    
    # Deactivate old active subscriptions? (Optional business logic)
    # db.query(UserSubscription).filter(user_id=...).update({is_active: False})
    
    db.add(new_sub)
    db.commit()
    
    return {
        "message": "Payment successful (Mocked)",
        "transaction_id": new_txn.id,
        "subscription_end_date": end_date
    }

@router.get("/my-subscription")
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's active subscription"""
    sub = db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.user_id,
        UserSubscription.is_active == True
    ).order_by(UserSubscription.end_date.desc()).first()
    
    if not sub:
        return {"has_subscription": False, "plan": None}
    
    package = db.query(ServicePackage).filter(ServicePackage.id == sub.package_id).first()
    
    return {
        "has_subscription": True,
        "plan": package.name if package else "Unknown",
        "status": "active" if sub.end_date > datetime.utcnow() else "expired",
        "start_date": sub.start_date.isoformat(),
        "end_date": sub.end_date.isoformat(),
        "package_id": sub.package_id
    }

# --- Package CRUD (Admin) ---
class PackageCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    duration_days: int = 30
    features: Optional[List[str]] = None
    mentor_included: bool = False
    is_active: bool = True

@router.post("/packages")
def create_package(data: PackageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(403, "Admin only")
    pkg = ServicePackage(**data.dict())
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg

@router.put("/packages/{package_id}")
def update_package(package_id: int, data: PackageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(403, "Admin only")
    pkg = db.query(ServicePackage).filter(ServicePackage.id == package_id).first()
    if not pkg:
        raise HTTPException(404, "Package not found")
    for k, v in data.dict().items():
        setattr(pkg, k, v)
    db.commit()
    return pkg

@router.delete("/packages/{package_id}")
def delete_package(package_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(403, "Admin only")
    pkg = db.query(ServicePackage).filter(ServicePackage.id == package_id).first()
    if not pkg:
        raise HTTPException(404, "Package not found")
    db.delete(pkg)
    db.commit()
    return {"message": "Package deleted"}

# --- Upgrade/Cancel Subscription ---
@router.post("/upgrade")
def upgrade_subscription(package_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    package = db.query(ServicePackage).filter(ServicePackage.id == package_id).first()
    if not package:
        raise HTTPException(404, "Package not found")
    
    # Deactivate old subscriptions
    db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.user_id,
        UserSubscription.is_active == True
    ).update({"is_active": False})
    
    # Create new subscription
    start_date = datetime.utcnow()
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
    return {"message": "Subscription upgraded", "end_date": end_date.isoformat()}

@router.post("/cancel")
def cancel_subscription(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.user_id,
        UserSubscription.is_active == True
    ).update({"is_active": False})
    db.commit()
    return {"message": "Subscription cancelled"}

