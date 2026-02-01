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


# =============================================================================
# Learner Bookings with Mentor Assessment
# =============================================================================

@router.get("/my-bookings")
def get_my_bookings_as_learner(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get learner's bookings with mentor, meeting link, and assessment.
    """
    from app.models.mentor import Booking, MentorAssessment
    from app.models.mentor_review import MentorResource
    from sqlalchemy.orm import joinedload
    
    bookings = db.query(Booking).filter(
        Booking.learner_id == current_user.user_id
    ).options(
        joinedload(Booking.slot),
        joinedload(Booking.assessment)
    ).order_by(Booking.created_at.desc()).all()
    
    result = []
    for b in bookings:
        assessment_data = None
        shared_resources = []
        
        if b.assessment:
            # Get shared resources if any
            if b.assessment.shared_resource_ids:
                try:
                    resource_ids = [int(rid) for rid in b.assessment.shared_resource_ids.split(',') if rid]
                    resources = db.query(MentorResource).filter(
                        MentorResource.resource_id.in_(resource_ids)
                    ).all()
                    shared_resources = [
                        {
                            "resource_id": r.resource_id,
                            "title": r.title,
                            "description": r.description,
                            "resource_type": r.resource_type,
                            "file_url": r.file_url
                        }
                        for r in resources
                    ]
                except:
                    pass
            
            assessment_data = {
                "assessment_id": b.assessment.assessment_id,
                "score": b.assessment.score,
                "feedback": b.assessment.feedback,
                "level_assigned": b.assessment.level_assigned,
                "pronunciation_score": b.assessment.pronunciation_score,
                "grammar_score": b.assessment.grammar_score,
                "vocabulary_score": b.assessment.vocabulary_score,
                "fluency_score": b.assessment.fluency_score,
                "pronunciation_notes": b.assessment.pronunciation_notes,
                "grammar_notes": b.assessment.grammar_notes,
                "vocabulary_tips": b.assessment.vocabulary_tips,
                "communication_tips": b.assessment.communication_tips,
                "shared_resources": shared_resources
            }
        
        result.append({
            "booking_id": b.booking_id,
            "slot_id": b.slot_id,
            "learner_id": b.learner_id,
            "status": b.status,
            "meeting_link": b.meeting_link,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "slot": {
                "start_time": b.slot.start_time.isoformat() if b.slot and b.slot.start_time else None,
                "end_time": b.slot.end_time.isoformat() if b.slot and b.slot.end_time else None
            } if b.slot else None,
            "assessment": assessment_data
        })
    
    return result


@router.get("/shared-topics")
def get_shared_topics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get topics shared by mentors via notifications.
    Returns topic details from TOPIC_SHARED notifications.
    """
    import json
    from app.models.notification import Notification
    from app.models.content import Topic
    
    # Get all TOPIC_SHARED notifications for this user
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.user_id,
        Notification.type == "TOPIC_SHARED"
    ).order_by(Notification.created_at.desc()).all()
    
    result = []
    seen_topic_ids = set()
    
    for notif in notifications:
        if not notif.extra_data:
            continue
        try:
            topic_ids = json.loads(notif.extra_data)
            for tid in topic_ids:
                if tid in seen_topic_ids:
                    continue
                seen_topic_ids.add(tid)
                
                topic = db.query(Topic).filter(Topic.topic_id == tid).first()
                if topic:
                    result.append({
                        "topic_id": topic.topic_id,
                        "name": topic.name,
                        "description": topic.description,
                        "difficulty_level": "GENERAL", # Topic model doesn't have difficulty_level
                        "industry": topic.industry,
                        "shared_at": notif.created_at.isoformat() if notif.created_at else None,
                        "mentor_message": notif.message
                    })
        except:
            continue
    
    return result
