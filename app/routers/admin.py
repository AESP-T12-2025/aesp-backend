from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.models.payment import Transaction, UserSubscription, ServicePackage
from app.models.policy import SystemPolicy
from app.models.content import SpeakingSession, Topic, Scenario
from app.models.mentor import Mentor, Booking
from app.models.social import MentorPost, PostComment

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value != "ADMIN":
        raise HTTPException(403, "Admin only")
    
    # User Stats
    total_users = db.query(User).count()
    learners = db.query(User).filter(User.role == UserRole.LEARNER).count()
    mentors = db.query(User).filter(User.role == UserRole.MENTOR).count()
    new_users_7d = db.query(User).filter(User.created_at >= datetime.now() - timedelta(days=7)).count()
    
    # Revenue Stats
    total_revenue = db.query(func.sum(Transaction.amount)).scalar() or 0
    revenue_7d = db.query(func.sum(Transaction.amount)).filter(
        Transaction.created_at >= datetime.now() - timedelta(days=7)
    ).scalar() or 0
    
    # Subscription Stats
    active_subs = db.query(UserSubscription).filter(UserSubscription.is_active == True).count()
    
    # Content Stats
    total_topics = db.query(Topic).count()
    total_scenarios = db.query(Scenario).count()
    total_sessions = db.query(SpeakingSession).count()
    sessions_7d = db.query(SpeakingSession).filter(
        SpeakingSession.start_time >= datetime.now() - timedelta(days=7)
    ).count()
    
    # Mentor Stats
    verified_mentors = db.query(Mentor).filter(Mentor.verification_status == "VERIFIED").count()
    total_bookings = db.query(Booking).count()
    
    # Social Stats
    total_posts = db.query(MentorPost).count()
    total_comments = db.query(PostComment).count()
    
    return {
        "users": {
            "total": total_users,
            "learners": learners,
            "mentors": mentors,
            "new_7d": new_users_7d
        },
        "revenue": {
            "total": total_revenue,
            "last_7d": revenue_7d
        },
        "subscriptions": {
            "active": active_subs
        },
        "content": {
            "topics": total_topics,
            "scenarios": total_scenarios,
            "sessions_total": total_sessions,
            "sessions_7d": sessions_7d
        },
        "mentors": {
            "verified": verified_mentors,
            "total_bookings": total_bookings
        },
        "social": {
            "posts": total_posts,
            "comments": total_comments
        }
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

@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(403, "Admin only")
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
        
    user.is_active = is_active
    db.commit()
    return {"message": "User status updated", "user_id": user_id, "is_active": user.is_active}

@router.put("/mentors/{mentor_id}/verify")
def verify_mentor(
    mentor_id: int,
    status: str, # APPROVED, REJECTED
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.mentor import Mentor
    if current_user.role != "ADMIN":
        raise HTTPException(403, "Admin only")
        
    mentor = db.query(Mentor).filter(Mentor.mentor_id == mentor_id).first()
    if not mentor:
         raise HTTPException(404, "Mentor not found")
         
    mentor.verification_status = status
    db.commit()
    return {"message": "Mentor verification updated", "status": status}

@router.post("/packages")
def create_package(
    name: str, price: float, duration_days: int, features: list[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.payment import ServicePackage
    if current_user.role != "ADMIN":
        raise HTTPException(403, "Admin only")
        
    pkg = ServicePackage(name=name, price=price, duration_days=duration_days, features=features, is_active=True)
    db.add(pkg)
    db.commit()
    return {"message": "Package created"}

@router.put("/packages/{pkg_id}")
def update_package(
    pkg_id: int, price: float = None, is_active: bool = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    from app.models.payment import ServicePackage
    if current_user.role != "ADMIN":
        raise HTTPException(403, "Admin only")
    
    pkg = db.query(ServicePackage).filter(ServicePackage.id == pkg_id).first()
    if not pkg: 
        raise HTTPException(404, "Package not found")
        
    if price is not None: pkg.price = price
    if is_active is not None: pkg.is_active = is_active
    
    db.commit()
    return {"message": "Package updated"}

@router.get("/transactions")
def get_all_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value != "ADMIN":
        raise HTTPException(403, "Admin only")
    
    transactions = db.query(Transaction).order_by(Transaction.created_at.desc()).all()
    result = []
    for t in transactions:
        user = db.query(User).filter(User.user_id == t.user_id).first()
        package = db.query(ServicePackage).filter(ServicePackage.id == t.package_id).first()
        result.append({
            "transaction_id": t.id,
            "user_id": t.user_id,
            "user": {"full_name": user.full_name if user else None, "email": user.email if user else None},
            "package_id": t.package_id,
            "package": {"name": package.name if package else None},
            "amount": t.amount,
            "status": t.status.value if hasattr(t.status, 'value') else t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
    return result

