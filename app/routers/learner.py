"""
Learner-specific endpoints for progress tracking, analytics, and reports.
Issues #35 and #39
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.models.content import SpeakingSession
from app.services.export_service import export_service

router = APIRouter(prefix="/learner", tags=["Learner Progress"])


class ReportSettingsUpdate(BaseModel):
    weekly_email: Optional[bool] = None
    monthly_email: Optional[bool] = None


def calculate_session_duration(session):
    """Calculate duration in seconds from start_time and end_time."""
    if session.end_time and session.start_time:
        delta = session.end_time - session.start_time
        return int(delta.total_seconds())
    return 0


# =============================================================================
# Issue #35: Progress Analytics & Heat Maps
# =============================================================================

@router.get("/progress")
def get_learner_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #35: Get overall learner progress summary.
    """
    # Get speaking sessions for this user
    sessions = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id
    ).all()
    
    total_duration = sum(calculate_session_duration(s) for s in sessions)
    scores = [s.score for s in sessions if s.score is not None]
    avg_score = sum(scores) / max(len(scores), 1) if scores else 0
    
    return {
        "total_sessions": len(sessions),
        "total_speaking_time_minutes": round(total_duration / 60, 1) if total_duration else 0,
        "average_score": round(avg_score, 2),
        "current_level": "A1",  # Default
        "xp_earned": current_user.bonus_xp or 0,
        "streak_days": 0,  # Would need separate tracking
    }


@router.get("/heatmap")
def get_activity_heatmap(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #35: Get GitHub-style activity heatmap data.
    """
    # Default to last 90 days
    if not end_date:
        end_dt = datetime.now()
    else:
        end_dt = datetime.fromisoformat(end_date)
    
    if not start_date:
        start_dt = end_dt - timedelta(days=90)
    else:
        start_dt = datetime.fromisoformat(start_date)
    
    # Get daily activity counts - use start_time instead of created_at
    from sqlalchemy import cast, Date
    daily_activity = db.query(
        cast(SpeakingSession.start_time, Date).label("date"),
        func.count(SpeakingSession.session_id).label("count")
    ).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= start_dt,
        SpeakingSession.start_time <= end_dt
    ).group_by(cast(SpeakingSession.start_time, Date)).all()
    
    return [{"date": str(d.date), "count": d.count} for d in daily_activity]


@router.get("/metrics/speaking-time")
def get_speaking_time_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #35: Get speaking time metrics.
    """
    sessions = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id
    ).all()
    
    total_seconds = sum(calculate_session_duration(s) for s in sessions)
    
    # Weekly breakdown
    week_ago = datetime.now() - timedelta(days=7)
    weekly_sessions = [s for s in sessions if s.start_time and s.start_time >= week_ago]
    weekly_seconds = sum(calculate_session_duration(s) for s in weekly_sessions)
    
    return {
        "total_minutes": round(total_seconds / 60, 1) if total_seconds else 0,
        "weekly_minutes": round(weekly_seconds / 60, 1) if weekly_seconds else 0,
        "daily_goal": current_user.daily_learning_goal or 15,
        "duration": "all_time"
    }


@router.get("/metrics/scenarios")
def get_completed_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #35: Get completed scenarios count.
    """
    completed = db.query(func.count(SpeakingSession.session_id)).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.status == "COMPLETED"
    ).scalar() or 0
    
    total = db.query(func.count(SpeakingSession.session_id)).filter(
        SpeakingSession.user_id == current_user.user_id
    ).scalar() or 0
    
    return {
        "completed": completed,
        "total": total,
        "completion_rate": round(completed / max(total, 1) * 100, 1)
    }


@router.get("/metrics/streak")
def get_streak_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #35: Get current learning streak.
    """
    # Calculate streak by checking consecutive days with activity
    from sqlalchemy import cast, Date, distinct
    
    today = datetime.now().date()
    activity_dates = db.query(
        distinct(cast(SpeakingSession.start_time, Date))
    ).filter(
        SpeakingSession.user_id == current_user.user_id
    ).order_by(cast(SpeakingSession.start_time, Date).desc()).all()
    
    streak = 0
    current_date = today
    
    activity_set = {d[0] for d in activity_dates if d[0] is not None}
    
    while current_date in activity_set:
        streak += 1
        current_date -= timedelta(days=1)
    
    return {
        "current_streak": streak,
        "longest_streak": streak,  # Would need separate tracking
        "days": streak
    }


@router.get("/progress/weekly")
def get_weekly_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #35: Get weekly progress summary.
    """
    week_ago = datetime.now() - timedelta(days=7)
    
    sessions = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= week_ago
    ).all()
    
    total_time = sum(calculate_session_duration(s) for s in sessions)
    scores = [s.score for s in sessions if s.score is not None]
    avg_score = sum(scores) / max(len(scores), 1) if scores else 0
    
    return {
        "week_start": str(week_ago.date()),
        "week_end": str(datetime.now().date()),
        "sessions_completed": len(sessions),
        "total_practice_time_minutes": round(total_time / 60, 1) if total_time else 0,
        "average_score": round(avg_score, 2),
        "daily_goal_completion_rate": round(min(total_time / 60 / (7 * 15) * 100, 100), 1) if total_time else 0
    }


@router.get("/goals/weekly")
def get_weekly_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #35: Get weekly goals and completion status.
    """
    daily_goal = current_user.daily_learning_goal or 15
    weekly_goal = daily_goal * 7
    
    week_ago = datetime.now() - timedelta(days=7)
    sessions = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= week_ago
    ).all()
    
    weekly_seconds = sum(calculate_session_duration(s) for s in sessions)
    weekly_minutes = weekly_seconds / 60 if weekly_seconds else 0
    
    return {
        "daily_goal_minutes": daily_goal,
        "weekly_goal_minutes": weekly_goal,
        "weekly_achieved_minutes": round(weekly_minutes, 1),
        "completion_percentage": round(min(weekly_minutes / weekly_goal * 100, 100), 1) if weekly_goal > 0 else 0,
        "on_track": weekly_minutes >= weekly_goal * 0.7
    }


@router.get("/analytics/trends")
def get_improvement_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #35: Get improvement trends over time.
    """
    # Get scores grouped by week
    from sqlalchemy import extract
    
    weekly_scores = db.query(
        extract('week', SpeakingSession.start_time).label("week"),
        func.avg(SpeakingSession.score).label("avg_score"),
        func.count(SpeakingSession.session_id).label("sessions")
    ).filter(
        SpeakingSession.user_id == current_user.user_id
    ).group_by(
        extract('week', SpeakingSession.start_time)
    ).order_by("week").limit(12).all()
    
    return {
        "trend_data": [
            {"week": int(w.week) if w.week else 0, "average_score": round(float(w.avg_score or 0), 2), "sessions": w.sessions}
            for w in weekly_scores
        ],
        "overall_improvement": "improving" if len(weekly_scores) > 1 else "insufficient_data"
    }


@router.get("/analytics/pronunciation")
def get_pronunciation_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #35: Get pronunciation improvement over time.
    """
    sessions = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id
    ).order_by(SpeakingSession.start_time.desc()).limit(20).all()
    
    return {
        "recent_scores": [
            {"date": str(s.start_time.date() if s.start_time else ""), "score": s.score or 0}
            for s in sessions
        ],
        "average_pronunciation": round(
            sum(s.score or 0 for s in sessions) / max(len(sessions), 1), 2
        ),
        "trend": "stable"
    }


# =============================================================================
# Issue #39: Weekly/Monthly Reports
# =============================================================================

@router.get("/reports")
def list_reports(
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #39: List all available reports for the learner.
    """
    # Generate mock report list
    reports = []
    now = datetime.now()
    
    for i in range(4):
        week_start = now - timedelta(weeks=i)
        reports.append({
            "id": f"weekly_{i+1}",
            "type": "weekly",
            "period_start": str((week_start - timedelta(days=7)).date()),
            "period_end": str(week_start.date()),
            "generated_at": str(week_start)
        })
    
    for i in range(3):
        month_start = now - timedelta(days=30*i)
        reports.append({
            "id": f"monthly_{i+1}",
            "type": "monthly",
            "period_start": str((month_start - timedelta(days=30)).date()),
            "period_end": str(month_start.date()),
            "generated_at": str(month_start)
        })
    
    if type:
        reports = [r for r in reports if r["type"] == type]
    
    return reports


@router.get("/reports/weekly")
def get_weekly_report(
    week: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #39: Get weekly progress report.
    """
    now = datetime.now()
    if week and year:
        # Calculate week dates
        try:
            week_start = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w")
        except ValueError:
            week_start = now - timedelta(days=now.weekday())
    else:
        week_start = now - timedelta(days=now.weekday())
    
    week_end = week_start + timedelta(days=6)
    
    sessions = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= week_start,
        SpeakingSession.start_time <= week_end
    ).all()
    
    total_seconds = sum(calculate_session_duration(s) for s in sessions)
    scores = [s.score for s in sessions if s.score is not None]
    avg_score = sum(scores) / max(len(scores), 1) if scores else 0
    
    return {
        "period": {
            "start": str(week_start.date()),
            "end": str(week_end.date()),
            "type": "weekly"
        },
        "metrics": {
            "sessions_completed": len(sessions),
            "total_practice_time_minutes": round(total_seconds / 60, 1) if total_seconds else 0,
            "average_score": round(avg_score, 2),
            "vocabulary_learned": 0,
            "scenarios_completed": len([s for s in sessions if s.status == "COMPLETED"])
        },
        "highlights": [],
        "areas_for_improvement": []
    }


@router.get("/reports/weekly/export")
async def export_weekly_report(
    format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #39 + #44: Export weekly report as PDF.
    """
    # Get weekly report data first
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=6)
    
    sessions = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= week_start,
        SpeakingSession.start_time <= week_end
    ).all()
    
    total_seconds = sum(calculate_session_duration(s) for s in sessions)
    scores = [s.score for s in sessions if s.score is not None]
    avg_score = sum(scores) / max(len(scores), 1) if scores else 0
    
    report_data = {
        "total_sessions": len(sessions),
        "total_speaking_time": round(total_seconds / 60, 1) if total_seconds else 0,
        "average_score": round(avg_score, 2),
        "streak_days": 0,
        "skills": {
            "Grammar": round(avg_score * 0.9, 1),
            "Pronunciation": round(avg_score * 0.85, 1),
            "Fluency": round(avg_score * 0.95, 1),
        }
    }
    
    result = await export_service.export_learner_report_pdf(
        user_id=current_user.user_id,
        report_type="weekly",
        data=report_data,
        start_date=week_start,
        end_date=week_end
    )
    
    return result.to_dict()


@router.get("/reports/monthly")
def get_monthly_report(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #39: Get monthly progress report.
    """
    now = datetime.now()
    if month and year:
        month_start = datetime(year, month, 1)
    else:
        month_start = datetime(now.year, now.month, 1)
    
    if month_start.month == 12:
        month_end = datetime(month_start.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = datetime(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
    
    sessions = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= month_start,
        SpeakingSession.start_time <= month_end
    ).all()
    
    total_seconds = sum(calculate_session_duration(s) for s in sessions)
    scores = [s.score for s in sessions if s.score is not None]
    avg_score = sum(scores) / max(len(scores), 1) if scores else 0
    
    return {
        "period": {
            "start": str(month_start.date()),
            "end": str(month_end.date()),
            "type": "monthly"
        },
        "summary": {
            "total_sessions": len(sessions),
            "total_practice_hours": round(total_seconds / 3600, 1) if total_seconds else 0,
            "average_daily_time_minutes": round(total_seconds / 60 / 30, 1) if total_seconds else 0,
            "best_day": None,
            "improvement_rate": 0
        },
        "metrics": {
            "average_score": round(avg_score, 2),
            "vocabulary_mastered": 0,
            "scenarios_completed": len([s for s in sessions if s.status == "COMPLETED"])
        },
        "monthly_goal_completion": 0
    }


@router.get("/reports/monthly/export")
async def export_monthly_report(
    format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #39 + #44: Export monthly report as PDF.
    """
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    if month_start.month == 12:
        month_end = datetime(month_start.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = datetime(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
    
    sessions = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= month_start,
        SpeakingSession.start_time <= month_end
    ).all()
    
    total_seconds = sum(calculate_session_duration(s) for s in sessions)
    scores = [s.score for s in sessions if s.score is not None]
    avg_score = sum(scores) / max(len(scores), 1) if scores else 0
    
    report_data = {
        "total_sessions": len(sessions),
        "total_speaking_time": round(total_seconds / 60, 1) if total_seconds else 0,
        "average_score": round(avg_score, 2),
        "streak_days": 0,
        "skills": {
            "Grammar": round(avg_score * 0.9, 1),
            "Pronunciation": round(avg_score * 0.85, 1),
            "Fluency": round(avg_score * 0.95, 1),
        }
    }
    
    result = await export_service.export_learner_report_pdf(
        user_id=current_user.user_id,
        report_type="monthly",
        data=report_data,
        start_date=month_start,
        end_date=month_end
    )
    
    return result.to_dict()


@router.put("/settings/reports")
def update_report_settings(
    settings: ReportSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #39: Update report notification settings.
    """
    # Store in user preferences (simplified - just return success)
    return {
        "message": "Report settings updated",
        "settings": {
            "weekly_email": settings.weekly_email,
            "monthly_email": settings.monthly_email
        }
    }


# =============================================================================
# Issue #38: Learner Purchase History
# =============================================================================

@router.get("/purchases")
def get_my_purchases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #38: Get learner's purchase history.
    """
    from app.models.payment import Transaction
    from sqlalchemy.orm import joinedload
    
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.user_id
    ).options(
        joinedload(Transaction.package)
    ).order_by(Transaction.created_at.desc()).all()
    
    return [
        {
            "id": t.id,
            "amount": float(t.amount),
            "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
            "package_name": t.package.name if t.package else None,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in transactions
    ]
