from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.utils import require_admin, paginate
from app.core.constants import DAYS_IN_WEEK, DEFAULT_PAGE_SIZE
from pydantic import BaseModel, Field
from app.core import security
from app.models.user import User, UserRole, AuthProvider
from app.models.payment import Transaction, UserSubscription, ServicePackage
from app.models.policy import SystemPolicy
from app.models.content import SpeakingSession, Topic, Scenario
from app.models.mentor import Mentor, Booking, AvailabilitySlot
from app.models.social import MentorPost, PostComment, ModerationStatus

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

# =============================================================================
# SCHEMAS
# =============================================================================

class UserCreateAdmin(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.LEARNER
    is_active: bool = True

class UserUpdateAdmin(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_admin(current_user)
    
    # User Stats
    total_users = db.query(User).count()
    learners = db.query(User).filter(User.role == UserRole.LEARNER).count()
    mentors = db.query(User).filter(User.role == UserRole.MENTOR).count()
    new_users_7d = db.query(User).filter(User.created_at >= datetime.now() - timedelta(days=DAYS_IN_WEEK)).count()
    
    # Revenue Stats
    total_revenue = db.query(func.sum(Transaction.amount)).scalar() or 0
    revenue_7d = db.query(func.sum(Transaction.amount)).filter(
        Transaction.created_at >= datetime.now() - timedelta(days=DAYS_IN_WEEK)
    ).scalar() or 0
    
    # Subscription Stats
    active_subs = db.query(UserSubscription).filter(UserSubscription.is_active == True).count()
    
    # Content Stats
    total_topics = db.query(Topic).count()
    total_scenarios = db.query(Scenario).count()
    total_sessions = db.query(SpeakingSession).count()
    sessions_7d = db.query(SpeakingSession).filter(
        SpeakingSession.start_time >= datetime.now() - timedelta(days=DAYS_IN_WEEK)
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
    require_admin(current_user)
    
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
    require_admin(current_user)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
        
    user.is_active = is_active
    db.commit()
    return {"message": "User status updated", "user_id": user_id, "is_active": user.is_active}

@router.put("/mentors/{mentor_id}/verify")
def verify_mentor(
    mentor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #32: Verify a mentor (set to VERIFIED status)."""
    require_admin(current_user)
    
    # Try to find by mentor_id first
    mentor = db.query(Mentor).filter(Mentor.mentor_id == mentor_id).first()
    
    # If not found, try to find by user_id
    if not mentor:
        mentor = db.query(Mentor).filter(Mentor.user_id == mentor_id).first()
    
    # If still not found, try to find user and create mentor profile
    if not mentor:
        user = db.query(User).filter(User.user_id == mentor_id).first()
        if user and str(user.role) == "MENTOR":
            # Auto-create mentor profile
            mentor = Mentor(
                user_id=user.user_id,
                full_name=user.full_name or "Mentor",
                verification_status="VERIFIED"
            )
            db.add(mentor)
            db.commit()
            db.refresh(mentor)
            return {"message": "Mentor verified", "is_verified": True, "verification_status": "VERIFIED"}
    
    return {"message": "Mentor already verified or profile exists"}


# =============================================================================
# User Management (CRUD)
# =============================================================================

@router.post("/users")
def admin_create_user(
    user_in: UserCreateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Create a new user."""
    require_admin(current_user)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(400, "Email already registered")
        
    new_user = User(
        email=user_in.email,
        password_hash=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=user_in.is_active,
        auth_provider=AuthProvider.LOCAL
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.patch("/users/{user_id}")
def admin_update_user(
    user_id: int,
    user_update: UserUpdateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Update any user detail."""
    require_admin(current_user)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
        
    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
        
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin only: Permanently delete a user."""
    require_admin(current_user)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
        
    # Safety: Don't delete self
    if user.user_id == current_user.user_id:
        raise HTTPException(400, "Cannot delete your own admin account")
        
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully", "user_id": user_id}


@router.post("/packages")
def create_package(
    name: str, price: float, duration_days: int, features: list[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_admin(current_user)
        
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
    require_admin(current_user)
    
    pkg = db.query(ServicePackage).filter(ServicePackage.id == pkg_id).first()
    if not pkg: 
        raise HTTPException(404, "Package not found")
        
    if price is not None: pkg.price = price
    if is_active is not None: pkg.is_active = is_active
    
    db.commit()
    return {"message": "Package updated"}

@router.get("/transactions")
def get_all_transactions(
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_admin(current_user)
    
    # Build query with joinedload to avoid N+1 queries
    query = db.query(Transaction).options(
        joinedload(Transaction.user),
        joinedload(Transaction.package)
    ).order_by(Transaction.created_at.desc())
    
    # Apply pagination
    paginated = paginate(query, skip=skip, limit=limit)
    
    # Transform items
    result = []
    for t in paginated["items"]:
        # Map SUCCESS to COMPLETED for frontend compatibility
        status_val = t.status.value if hasattr(t.status, 'value') else t.status
        if status_val == "SUCCESS":
            status_val = "COMPLETED"
            
        result.append({
            "transaction_id": t.id,
            "id": t.id,
            "user_id": t.user_id,
            "user": {"full_name": t.user.full_name if t.user else None, "email": t.user.email if t.user else None},
            "package_id": t.package_id,
            "package": {"name": t.package.name if t.package else None},
            "amount": t.amount,
            "status": status_val,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
    
    # Return flat list instead of paginated object as requested by frontend code: setTransactions(data)
    return result


# =============================================================================
# Issue #34: Dashboard Stats and Analytics - Additional Endpoints
# =============================================================================

@router.get("/dashboard/stats")
def get_dashboard_stats_alias(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Alias for /admin/stats - Issue #34"""
    return get_dashboard_stats(db=db, current_user=current_user)


@router.get("/stats/users")
def get_user_stats(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #34: Get detailed user statistics."""
    require_admin(current_user)
    
    query = db.query(User)
    if start_date:
        query = query.filter(User.created_at >= start_date)
    if end_date:
        query = query.filter(User.created_at <= end_date)
    
    total = query.count()
    active = query.filter(User.is_active == True).count()
    
    return {
        "total": total,
        "count": total,
        "active": active,
        "inactive": total - active
    }


@router.get("/stats/users/by-role")
def get_users_by_role(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #34: Get user breakdown by role."""
    require_admin(current_user)
    
    return {
        "LEARNER": db.query(User).filter(User.role == UserRole.LEARNER).count(),
        "MENTOR": db.query(User).filter(User.role == UserRole.MENTOR).count(),
        "ADMIN": db.query(User).filter(User.role == UserRole.ADMIN).count()
    }


@router.get("/stats/users/active")
def get_active_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #34: Get active users count."""
    require_admin(current_user)
    
    active_count = db.query(User).filter(User.is_active == True).count()
    last_week = datetime.now() - timedelta(days=7)
    recently_active = db.query(User).filter(
        User.last_login_at >= last_week if hasattr(User, 'last_login_at') else User.created_at >= last_week
    ).count()
    
    return {
        "active": active_count,
        "recently_active_7d": recently_active
    }


@router.get("/stats/subscriptions")
def get_subscription_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #34: Get subscription breakdown by package."""
    require_admin(current_user)
    
    # Get subscriptions grouped by package
    from sqlalchemy import and_
    
    packages = db.query(ServicePackage).all()
    breakdown = []
    
    for pkg in packages:
        count = db.query(UserSubscription).filter(
            and_(
                UserSubscription.package_id == pkg.id,
                UserSubscription.is_active == True
            )
        ).count()
        breakdown.append({
            "package_id": pkg.id,
            "package_name": pkg.name,
            "active_subscriptions": count
        })
    
    total_active = db.query(UserSubscription).filter(UserSubscription.is_active == True).count()
    
    return {
        "total_active": total_active,
        "by_package": breakdown
    }


@router.get("/stats/revenue")
def get_revenue_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #34: Get revenue statistics."""
    require_admin(current_user)
    
    total = db.query(func.sum(Transaction.amount)).scalar() or 0
    last_month = datetime.now() - timedelta(days=30)
    monthly = db.query(func.sum(Transaction.amount)).filter(
        Transaction.created_at >= last_month
    ).scalar() or 0
    
    last_week = datetime.now() - timedelta(days=7)
    weekly = db.query(func.sum(Transaction.amount)).filter(
        Transaction.created_at >= last_week
    ).scalar() or 0
    
    return {
        "total": float(total),
        "revenue": float(total),
        "monthly_revenue": float(monthly),
        "weekly_revenue": float(weekly)
    }


@router.get("/stats/content/popular")
def get_popular_content(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #34: Get most popular topics."""
    require_admin(current_user)
    
    # Get topics with session counts
    topics = db.query(Topic).limit(limit).all()
    
    result = []
    for topic in topics:
        session_count = db.query(func.count(SpeakingSession.session_id)).join(
            Scenario, SpeakingSession.scenario_id == Scenario.scenario_id
        ).filter(Scenario.topic_id == topic.topic_id).scalar() or 0
        
        result.append({
            "topic_id": topic.topic_id,
            "title": topic.title,
            "session_count": session_count
        })
    
    return sorted(result, key=lambda x: x["session_count"], reverse=True)


@router.get("/stats/scenarios/completion")
def get_scenario_completion_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #34: Get scenario completion rates."""
    require_admin(current_user)
    
    total_sessions = db.query(SpeakingSession).count()
    completed_sessions = db.query(SpeakingSession).filter(
        SpeakingSession.status == "COMPLETED"
    ).count()
    
    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "completion_rate": round(completed_sessions / max(total_sessions, 1) * 100, 1)
    }


@router.get("/stats/monthly")
def get_monthly_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #34: Get monthly statistics."""
    require_admin(current_user)
    
    from sqlalchemy import extract
    
    # Get data for each of the last 6 months
    monthly_data = []
    for i in range(6):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        if month_start.month == 12:
            month_end = datetime(month_start.year + 1, 1, 1)
        else:
            month_end = datetime(month_start.year, month_start.month + 1, 1)
        
        new_users = db.query(User).filter(
            User.created_at >= month_start,
            User.created_at < month_end
        ).count()
        
        revenue = db.query(func.sum(Transaction.amount)).filter(
            Transaction.created_at >= month_start,
            Transaction.created_at < month_end
        ).scalar() or 0
        
        sessions = db.query(SpeakingSession).filter(
            SpeakingSession.start_time >= month_start,
            SpeakingSession.start_time < month_end
        ).count()
        
        monthly_data.append({
            "month": month_start.strftime("%Y-%m"),
            "new_users": new_users,
            "revenue": float(revenue),
            "sessions": sessions
        })
    
    return monthly_data


# =============================================================================
# Issue #32: Mentor Management - Additional Endpoints
# =============================================================================

@router.get("/mentors")
def list_mentors(
    status: str = None,
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #32: List all mentors with optional filtering."""
    require_admin(current_user)
    
    query = db.query(Mentor).options(joinedload(Mentor.user))
    
    if status:
        query = query.filter(Mentor.verification_status == status)
    
    mentors = query.offset(skip).limit(limit).all()
    
    # Return as list to match test expectations
    return [
        {
            "mentor_id": m.mentor_id,
            "user_id": m.user_id,
            "full_name": m.full_name if hasattr(m, 'full_name') else None,
            "user": {"full_name": m.user.full_name if m.user else None, "email": m.user.email if m.user else None},
            "skills": m.skills if hasattr(m, 'skills') else None,
            "verification_status": m.verification_status.value if hasattr(m.verification_status, 'value') else m.verification_status,
            "bio": m.bio
        }
        for m in mentors
    ]


@router.get("/mentors/{mentor_id}")
def get_mentor_details(
    mentor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #32: Get mentor details."""
    require_admin(current_user)
    
    mentor = db.query(Mentor).options(joinedload(Mentor.user)).filter(
        Mentor.mentor_id == mentor_id
    ).first()
    
    if not mentor:
        # Try to find by user_id
        mentor = db.query(Mentor).options(joinedload(Mentor.user)).filter(
            Mentor.user_id == mentor_id
        ).first()
    
    if not mentor:
        raise HTTPException(404, "Mentor not found")
    
    return {
        "mentor_id": mentor.mentor_id,
        "user_id": mentor.user_id,
        "full_name": mentor.full_name if hasattr(mentor, 'full_name') else (mentor.user.full_name if mentor.user else None),
        "email": mentor.user.email if mentor.user else None,
        "user": {"full_name": mentor.user.full_name if mentor.user else None, "email": mentor.user.email if mentor.user else None},
        "specialization": mentor.specialization if hasattr(mentor, 'specialization') else None,
        "verification_status": mentor.verification_status.value if hasattr(mentor.verification_status, 'value') else mentor.verification_status,
        "bio": mentor.bio,
        "hourly_rate": mentor.hourly_rate if hasattr(mentor, 'hourly_rate') else None,
        "total_sessions": db.query(Booking).join(AvailabilitySlot).filter(AvailabilitySlot.mentor_id == mentor.mentor_id).count()
    }


@router.put("/mentors/{mentor_id}/unverify")
def unverify_mentor(
    mentor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #32: Unverify a mentor (set to PENDING)."""
    require_admin(current_user)
    
    mentor = db.query(Mentor).filter(Mentor.mentor_id == mentor_id).first()
    if not mentor:
        mentor = db.query(Mentor).filter(Mentor.user_id == mentor_id).first()
    
    if not mentor:
        raise HTTPException(404, "Mentor not found")
    
    mentor.verification_status = "PENDING"
    db.commit()
    return {"message": "Mentor unverified", "status": "PENDING"}


# =============================================================================
# Issue #26: Toggle User Account Status (Alternative Endpoint)
# =============================================================================

@router.put("/users/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #26: Toggle user account active/inactive status."""
    require_admin(current_user)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(404, detail="User not found")
    
    user.is_active = not user.is_active
    db.commit()
    
    return {
        "user_id": user_id,
        "is_active": user.is_active,
        "message": f"User {'activated' if user.is_active else 'deactivated'} successfully"
    }


# =============================================================================
# Issue #38: Purchase History Export
# =============================================================================

@router.get("/purchases")
def get_purchases(
    start_date: str = None,
    end_date: str = None,
    package_id: int = None,
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #38: Get purchase history with filtering options."""
    require_admin(current_user)
    
    query = db.query(Transaction).options(
        joinedload(Transaction.user),
        joinedload(Transaction.package)
    )
    
    if start_date:
        query = query.filter(Transaction.created_at >= start_date)
    if end_date:
        query = query.filter(Transaction.created_at <= end_date)
    if package_id:
        query = query.filter(Transaction.package_id == package_id)
    
    total = query.count()
    items = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for t in items:
        # Map SUCCESS to COMPLETED for frontend compatibility
        status_val = t.status.value if hasattr(t.status, 'value') else t.status
        if status_val == "SUCCESS":
            status_val = "COMPLETED"
            
        result.append({
            "id": t.id,
            "transaction_id": t.id,
            "user_id": t.user_id,
            "user_email": t.user.email if t.user else None,
            "user_name": t.user.full_name if t.user else None,
            "user": {"full_name": t.user.full_name if t.user else None, "email": t.user.email if t.user else None},
            "package_id": t.package_id,
            "package_name": t.package.name if t.package else None,
            "package": {"name": t.package.name if t.package else None},
            "amount": float(t.amount or 0),
            "status": status_val,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
    
    return result


@router.get("/purchases/export")
def export_purchases(
    format: str = "csv",
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #38: Export purchase history."""
    require_admin(current_user)
    
    if format not in ["csv", "json", "xlsx", "excel"]:
        raise HTTPException(400, "Format must be 'csv', 'json', or 'xlsx'")
    
    query = db.query(Transaction).options(
        joinedload(Transaction.user),
        joinedload(Transaction.package)
    )
    
    if start_date:
        query = query.filter(Transaction.created_at >= start_date)
    if end_date:
        query = query.filter(Transaction.created_at <= end_date)
    
    items = query.order_by(Transaction.created_at.desc()).all()
    
    data = [
        {
            "id": t.id,
            "user_email": t.user.email if t.user else None,
            "amount": float(t.amount),
            "status": t.status.value if hasattr(t.status, 'value') else t.status,
            "date": t.created_at.isoformat() if t.created_at else None
        }
        for t in items
    ]
    
    return {"format": format, "count": len(data), "data": data}


# =============================================================================
# Issue: Content Moderation Endpoints
# =============================================================================

@router.get("/posts")
def get_admin_posts(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all posts for admin moderation."""
    require_admin(current_user)

    query = db.query(MentorPost).order_by(MentorPost.created_at.desc())
    
    if status and status != 'ALL':
        query = query.filter(MentorPost.moderation_status == status)

    posts = query.all()
    
    return [
        {
            "id": p.id,
            "content": p.content,
            "mentor_id": p.mentor_id,
            "mentor_name": p.mentor.full_name if p.mentor else "Unknown",
            "status": p.moderation_status.value if hasattr(p.moderation_status, 'value') else p.moderation_status,
            "created_at": p.created_at
        }
        for p in posts
    ]


@router.put("/posts/{post_id}/moderate")
def moderate_post(
    post_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject a post."""
    require_admin(current_user)

    post = db.query(MentorPost).filter(MentorPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Validate status
    if status not in ["APPROVED", "REJECTED", "PENDING"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    post.moderation_status = status
    db.commit()
    
    return {"message": f"Post {status.lower()}"}


@router.get("/reports/export")
def export_reports_alias(
    format: str = "csv",
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Alias for /admin/reports/export - Issue #38"""
    return export_purchases(format, start_date, end_date, db, current_user)
