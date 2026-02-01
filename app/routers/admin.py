from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.utils import require_admin, paginate
from app.core.constants import DAYS_IN_WEEK, DEFAULT_PAGE_SIZE
from app.models.user import User, UserRole
from app.models.payment import Transaction, UserSubscription, ServicePackage
from app.models.policy import SystemPolicy
from app.models.content import SpeakingSession, Topic, Scenario
from app.models.mentor import Mentor, Booking, AvailabilitySlot
from app.models.social import MentorPost, PostComment
from app.services.export_service import export_service

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

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
        raise HTTPException(404, "Mentor not found")
    
    mentor.verification_status = "VERIFIED"
    db.commit()
    return {"message": "Mentor verified", "is_verified": True, "verification_status": "VERIFIED"}

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
        result.append({
            "transaction_id": t.id,
            "user_id": t.user_id,
            "user": {"full_name": t.user.full_name if t.user else None, "email": t.user.email if t.user else None},
            "package_id": t.package_id,
            "package": {"name": t.package.name if t.package else None},
            "amount": t.amount,
            "status": t.status.value if hasattr(t.status, 'value') else t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
    
    return {
        "items": result,
        "total": paginated["total"],
        "page": paginated["page"],
        "per_page": paginated["per_page"],
        "pages": paginated["pages"],
        "has_next": paginated["has_next"],
        "has_prev": paginated["has_prev"]
    }


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
    """Issue #34: Get revenue statistics with daily breakdown."""
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
    
    # Daily breakdown for last 7 days
    daily_breakdown = []
    for i in range(6, -1, -1):  # 6 days ago to today
        day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        day_revenue = db.query(func.sum(Transaction.amount)).filter(
            Transaction.created_at >= day_start,
            Transaction.created_at < day_end
        ).scalar() or 0
        daily_breakdown.append({
            "date": day_start.strftime("%d/%m"),
            "day_name": ["CN", "T2", "T3", "T4", "T5", "T6", "T7"][day_start.weekday() + 1 if day_start.weekday() < 6 else 0],
            "revenue": float(day_revenue)
        })
    
    return {
        "total": float(total),
        "revenue": float(total),
        "monthly_revenue": float(monthly),
        "weekly_revenue": float(weekly),
        "daily_breakdown": daily_breakdown
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


@router.put("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    new_role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change a user's role (e.g., LEARNER -> MENTOR)."""
    require_admin(current_user)
    
    # Validate new_role
    valid_roles = ["ADMIN", "MENTOR", "LEARNER"]
    if new_role.upper() not in valid_roles:
        raise HTTPException(400, f"Invalid role. Must be one of: {valid_roles}")
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    old_role = str(user.role.value) if hasattr(user.role, 'value') else str(user.role)
    user.role = UserRole[new_role.upper()]
    
    # Auto-create Mentor profile if promoting to MENTOR
    if new_role.upper() == "MENTOR":
        existing_mentor = db.query(Mentor).filter(Mentor.user_id == user_id).first()
        if not existing_mentor:
            mentor = Mentor(
                user_id=user_id,
                full_name=user.full_name or "Mentor",
                verification_status="PENDING",
                bio="",
                skills=""
            )
            db.add(mentor)
    
    db.commit()
    
    return {
        "user_id": user_id,
        "old_role": old_role,
        "new_role": new_role.upper(),
        "message": f"User role changed from {old_role} to {new_role.upper()}"
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
    
    return [
        {
            "id": t.id,
            "user_id": t.user_id,
            "user_email": t.user.email if t.user else None,
            "user_name": t.user.full_name if t.user else None,
            "package_id": t.package_id,
            "package_name": t.package.name if t.package else None,
            "amount": float(t.amount),
            "status": t.status.value if hasattr(t.status, 'value') else t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in items
    ]


@router.get("/purchases/export")
async def export_purchases(
    format: str = "csv",
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #38 + #44: Export purchase history as Excel/CSV."""
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
    
    # Format data for export
    transactions_data = [
        {
            "ID": t.id,
            "User": t.user.email if t.user else None,
            "Package": t.package.name if t.package else None,
            "Amount": float(t.amount),
            "Status": t.status.value if hasattr(t.status, 'value') else str(t.status),
            "Date": t.created_at.isoformat() if t.created_at else None
        }
        for t in items
    ]
    
    # Use export service for Excel format
    if format in ["xlsx", "excel"]:
        from datetime import datetime as dt
        start_dt = dt.fromisoformat(start_date) if start_date else None
        end_dt = dt.fromisoformat(end_date) if end_date else None
        
        result = await export_service.export_transactions_excel(
            transactions=transactions_data,
            start_date=start_dt,
            end_date=end_dt
        )
        return result.to_dict()
    
    # Return JSON for other formats
    return {"format": format, "count": len(transactions_data), "data": transactions_data}


@router.get("/analytics/export")
async def export_analytics(
    format: str = "excel",
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #44: Export analytics data as Excel."""
    require_admin(current_user)
    
    # Get analytics data
    from datetime import datetime as dt
    
    start_dt = dt.fromisoformat(start_date) if start_date else None
    end_dt = dt.fromisoformat(end_date) if end_date else None
    
    # User stats
    total_users = db.query(User).count()
    learners = db.query(User).filter(User.role == UserRole.LEARNER).count()
    mentors = db.query(User).filter(User.role == UserRole.MENTOR).count()
    
    # Revenue
    total_revenue = db.query(func.sum(Transaction.amount)).scalar() or 0
    
    # Sessions
    total_sessions = db.query(SpeakingSession).count()
    
    analytics_data = {
        "headers": ["Metric", "Value"],
        "rows": [
            {"Metric": "Total Users", "Value": total_users},
            {"Metric": "Learners", "Value": learners},
            {"Metric": "Mentors", "Value": mentors},
            {"Metric": "Total Revenue", "Value": float(total_revenue)},
            {"Metric": "Total Sessions", "Value": total_sessions},
        ]
    }
    
    result = await export_service.export_analytics_excel(
        data=analytics_data,
        export_type="analytics",
        start_date=start_dt,
        end_date=end_dt
    )
    
    return result.to_dict()


