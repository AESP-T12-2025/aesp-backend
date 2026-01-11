from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.payment import Transaction, UserSubscription
from app.models.policy import SystemPolicy

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(403, "Admin only")
        
    total_users = db.query(User).count()
    total_revenue = db.query(func.sum(Transaction.amount)).scalar() or 0
    active_subs = db.query(UserSubscription).filter(UserSubscription.is_active == True).count()
    
    return {
        "total_users": total_users,
        "total_revenue": total_revenue,
        "active_subscriptions": active_subs
    }

@router.post("/policies")
def create_policy(
    title: str, content: str, type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(403, "Admin only")
    
    policy = SystemPolicy(title=title, content=content, type=type)
    db.add(policy)
    db.commit()
    return {"message": "Policy created"}

@router.get("/policies")
def list_policies(db: Session = Depends(get_db)):
    return db.query(SystemPolicy).all()
