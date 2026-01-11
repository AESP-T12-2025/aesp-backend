from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
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
    features: Optional[dict]
    
    class Config:
        orm_mode = True

class PaymentRequest(BaseModel):
    package_id: int
    payment_method: str = "MOCK_BANKING"

# --- APIs ---

@router.get("/packages", response_model=List[PackageResponse])
def list_packages(db: Session = Depends(get_db)):
    return db.query(ServicePackage).filter(ServicePackage.is_active == True).all()

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
