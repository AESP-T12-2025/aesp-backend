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
from app.models.mentor import Mentor, Booking
from app.models.social import MentorPost, PostComment

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

# Issue #34: User Growth Statistics
@router.get("/stats/users")
def get_user_growth_stats(
    period: str = "daily",  # daily, weekly, monthly
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #34: User growth statistics for charts.
    Returns new users per period for the specified number of days.
    """
    require_admin(current_user)
    
    start_date = datetime.now() - timedelta(days=days)
    
    if period == "daily":
        # Group by date
        from sqlalchemy import cast, Date
        stats = db.query(
            cast(User.created_at, Date).label("date"),
            func.count(User.user_id).label("count")
        ).filter(
            User.created_at >= start_date
        ).group_by(
            cast(User.created_at, Date)
        ).order_by("date").all()
        
        result = [{"date": str(s.date), "count": s.count} for s in stats]
    else:
        # Simple weekly/monthly aggregation
        result = []
        
    return {
        "period": period,
        "data": result,
        "total_new": sum(r["count"] for r in result)
    }

# Issue #34: Revenue Statistics
@router.get("/stats/revenue")
def get_revenue_stats(
    period: str = "daily",  # daily, weekly, monthly
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #34: Revenue statistics for charts.
    Returns revenue per period for the specified number of days.
    """
    require_admin(current_user)
    
    start_date = datetime.now() - timedelta(days=days)
    
    from sqlalchemy import cast, Date
    stats = db.query(
        cast(Transaction.created_at, Date).label("date"),
        func.sum(Transaction.amount).label("revenue"),
        func.count(Transaction.id).label("transactions")
    ).filter(
        Transaction.created_at >= start_date,
        Transaction.status == "COMPLETED"
    ).group_by(
        cast(Transaction.created_at, Date)
    ).order_by("date").all()
    
    result = [{
        "date": str(s.date),
        "revenue": float(s.revenue or 0),
        "transactions": s.transactions
    } for s in stats]
    
    return {
        "period": period,
        "data": result,
        "total_revenue": sum(r["revenue"] for r in result),
        "total_transactions": sum(r["transactions"] for r in result)
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

# Issue #26: Toggle account status (enable/disable)
@router.put("/users/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #26: Toggle user account status (enable <-> disable).
    Admin can quickly toggle without specifying target state.
    """
    require_admin(current_user)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # Prevent admin from disabling themselves
    if user.user_id == current_user.user_id:
        raise HTTPException(400, "Cannot toggle your own account")
    
    # Toggle the status
    user.is_active = not user.is_active
    db.commit()
    
    action = "enabled" if user.is_active else "disabled"
    return {
        "message": f"User {action} successfully",
        "user_id": user_id,
        "is_active": user.is_active
    }

# Issue #32: Manage Mentor List
@router.get("/mentors")
def list_mentors(
    status: str = None,  # PENDING, VERIFIED, REJECTED
    skills: str = None,  # Search by skills
    rating_min: float = None,  # Filter by minimum rating
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #32: Admin list all mentors with filters.
    Supports filtering by verification status, skills, and rating.
    """
    require_admin(current_user)
    
    query = db.query(Mentor).options(joinedload(Mentor.user))
    
    # Apply filters
    if status:
        query = query.filter(Mentor.verification_status == status)
    if skills:
        query = query.filter(Mentor.skills.ilike(f"%{skills}%"))
    if rating_min is not None:
        query = query.filter(Mentor.avg_rating >= rating_min)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    mentors = query.offset(skip).limit(limit).all()
    
    result = []
    for m in mentors:
        result.append({
            "mentor_id": m.mentor_id,
            "user_id": m.user_id,
            "full_name": m.user.full_name if m.user else "Unknown",
            "email": m.user.email if m.user else None,
            "skills": m.skills,
            "bio": m.bio,
            "verification_status": m.verification_status,
            "avg_rating": m.avg_rating,
            "total_sessions": m.total_sessions or 0,
            "is_active": m.user.is_active if m.user else False
        })
    
    return {
        "items": result,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
        "pages": (total + limit - 1) // limit
    }

@router.put("/mentors/{mentor_id}/verify")
def verify_mentor(
    mentor_id: int,
    status: str, # APPROVED, REJECTED
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_admin(current_user)
        
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
# Issue #38: Purchase History Export (Admin)
# =============================================================================

@router.get("/purchases/export")
def export_purchase_history(
    start_date: str = None,  # YYYY-MM-DD
    end_date: str = None,    # YYYY-MM-DD
    format: str = "csv",     # csv or json
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #38: Export purchase history to CSV or JSON.
    Admin can filter by date range and export for accounting.
    """
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    require_admin(current_user)
    
    query = db.query(Transaction).options(
        joinedload(Transaction.user),
        joinedload(Transaction.package)
    )
    
    # Apply date filters
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Transaction.created_at >= start)
        except ValueError:
            raise HTTPException(400, "Invalid start_date format. Use YYYY-MM-DD")
    
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Transaction.created_at <= end)
        except ValueError:
            raise HTTPException(400, "Invalid end_date format. Use YYYY-MM-DD")
    
    transactions = query.order_by(Transaction.created_at.desc()).all()
    
    if format == "json":
        result = []
        for t in transactions:
            result.append({
                "transaction_id": t.id,
                "user_email": t.user.email if t.user else None,
                "user_name": t.user.full_name if t.user else None,
                "package_name": t.package.name if t.package else None,
                "amount": t.amount,
                "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
                "created_at": t.created_at.isoformat() if t.created_at else None
            })
        return {"data": result, "total": len(result)}
    
    # CSV Export
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["Transaction ID", "User Email", "User Name", "Package", "Amount", "Status", "Date"])
    
    # Data rows
    for t in transactions:
        writer.writerow([
            t.id,
            t.user.email if t.user else "",
            t.user.full_name if t.user else "",
            t.package.name if t.package else "",
            t.amount,
            t.status.value if hasattr(t.status, 'value') else str(t.status),
            t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=purchases_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

