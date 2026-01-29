from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.gamification import UserDailyStats
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/weekly")
def get_weekly_stats(
    date: str = None, # YYYY-MM-DD
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.content import SpeakingSession, AIFeedback

    # Calculate start of week (Monday)
    if date:
        try:
            today = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
             today = datetime.now().date()
    else:
        today = datetime.now().date()

    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Query daily stats for this week
    stats = db.query(UserDailyStats).filter(
        UserDailyStats.user_id == current_user.user_id,
        UserDailyStats.date >= start_of_week,
        UserDailyStats.date <= end_of_week
    ).all()
    
    # Map stats to days (0=Mon, 6=Sun)
    daily_activity = [0] * 7
    total_seconds = 0
    total_words = 0
    
    # Get latest stat for streak
    latest_stat = db.query(UserDailyStats).filter(
        UserDailyStats.user_id == current_user.user_id
    ).order_by(UserDailyStats.date.desc()).first()
    
    streak = latest_stat.login_streak_current if latest_stat else 0

    for s in stats:
        day_idx = s.date.weekday()
        hours = round(s.speaking_duration_seconds / 3600, 1)
        daily_activity[day_idx] = hours
        total_seconds += s.speaking_duration_seconds
        total_words += s.words_learned
        
    # Calculate aggregates
    total_hours = round(total_seconds / 3600, 1)
    xp_earned = total_words * 10
    
    # Real Avg Score
    avg_score_query = db.query(func.avg(AIFeedback.grammar_score)).join(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id
    ).scalar()
    
    # Normalize score (0-100 -> 0-10 or keep 0-100 depending on UI)
    # UI shows "8.5", assuming 0-10 scale. AI returns 0-100 usually? 
    # Let's assume AI returns 0-100.
    avg_score = round(avg_score_query / 10, 1) if avg_score_query else 0.0

    # Real Completed Scenarios
    scenarios_completed = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        # SpeakingSession.status == "COMPLETED" # Uncomment if status is reliable
    ).count()
    
    # Dynamic Feedback
    feedback_list = []
    if avg_score >= 8.0:
        feedback_list.append({ "type": 'strength', "text": 'Kỹ năng ngữ pháp của bạn rất xuất sắc!' })
    elif avg_score > 0:
        feedback_list.append({ "type": 'weakness', "text": 'Cần cải thiện độ chính xác ngữ pháp hơn.' })
    else:
        feedback_list.append({ "type": 'strength', "text": 'Hãy bắt đầu bài luyện tập đầu tiên để nhận đánh giá.' })

    if streak > 3:
        feedback_list.append({ "type": 'strength', "text": 'Bạn đang duy trì chuỗi học tập rất tốt!' })

    # Heat Map Data (last 30 days)
    heat_map_data = []
    for i in range(30):
        check_date = today - timedelta(days=29-i)
        stat = db.query(UserDailyStats).filter(
            UserDailyStats.user_id == current_user.user_id,
            func.date(UserDailyStats.date) == check_date
        ).first()
        
        activity_level = 0
        if stat:
            total_mins = (stat.speaking_duration_seconds or 0) / 60
            if total_mins > 30:
                activity_level = 4
            elif total_mins > 15:
                activity_level = 3
            elif total_mins > 5:
                activity_level = 2
            elif total_mins > 0:
                activity_level = 1
        
        heat_map_data.append({
            "date": check_date.isoformat(),
            "level": activity_level
        })

    return {
        "totalHours": total_hours,
        "scenariosCompleted": scenarios_completed,
        "avgScore": avg_score,
        "streak": streak,
        "xpEarned": xp_earned,
        "dailyActivity": daily_activity,
        "feedback": feedback_list,
        "heatMap": heat_map_data
    }

@router.get("/monthly")
def get_monthly_stats(
    date: str = None, # YYYY-MM
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.content import SpeakingSession, AIFeedback

    # 1. Determine Date Range (Start/End of Month)
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m").date()
        except ValueError:
            target_date = datetime.now().date()
    else:
        target_date = datetime.now().date()

    # Start of month: 1st day of target_date month
    start_of_month = target_date.replace(day=1)
    
    # End of month: (1st day of next month) - 1 day
    if start_of_month.month == 12:
        next_month = start_of_month.replace(year=start_of_month.year + 1, month=1)
    else:
        next_month = start_of_month.replace(month=start_of_month.month + 1)
    end_of_month = next_month - timedelta(days=1)

    # 2. Query Daily Stats for this Month
    stats = db.query(UserDailyStats).filter(
        UserDailyStats.user_id == current_user.user_id,
        UserDailyStats.date >= start_of_month,
        UserDailyStats.date <= end_of_month
    ).all()

    # 3. Aggregate Data
    days_in_month = (end_of_month - start_of_month).days + 1
    daily_activity = [0] * days_in_month
    total_seconds = 0
    total_words = 0

    for s in stats:
        day_idx = (s.date - start_of_month).days # 0 to 30
        if 0 <= day_idx < days_in_month:
            hours = round(s.speaking_duration_seconds / 3600, 1)
            daily_activity[day_idx] = hours
            total_seconds += s.speaking_duration_seconds
            total_words += s.words_learned

    total_hours = round(total_seconds / 3600, 1)
    xp_earned = total_words * 10

    # 4. Count Completed Scenarios in this Month
    scenarios_completed = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= start_of_month,
        SpeakingSession.start_time <= end_of_month
        # SpeakingSession.status == "COMPLETED" 
    ).count()

    # 5. Average Score (All time or this month? Let's do this month)
    avg_score_query = db.query(func.avg(AIFeedback.grammar_score)).join(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= start_of_month,
        SpeakingSession.start_time <= end_of_month
    ).scalar()
    
    avg_score = round(avg_score_query / 10, 1) if avg_score_query else 0.0

    # 6. Streak (Current streak is global, not monthly specific, but we can return it)
    streak_stat = db.query(UserDailyStats).filter(
        UserDailyStats.user_id == current_user.user_id
    ).order_by(UserDailyStats.date.desc()).first()
    streak = streak_stat.login_streak_current if streak_stat else 0

    # 7. Comparison (vs Previous Month)
    # Start/End of Prev Month
    start_of_prev_month = (start_of_month - timedelta(days=1)).replace(day=1)
    end_of_prev_month = start_of_month - timedelta(days=1)

    prev_month_seconds = db.query(func.sum(UserDailyStats.speaking_duration_seconds)).filter(
        UserDailyStats.user_id == current_user.user_id,
        UserDailyStats.date >= start_of_prev_month,
        UserDailyStats.date <= end_of_prev_month
    ).scalar() or 0
    
    prev_month_hours = round(prev_month_seconds / 3600, 1)
    hours_diff = round(total_hours - prev_month_hours, 1)

    return {
        "totalHours": total_hours,
        "scenariosCompleted": scenarios_completed,
        "avgScore": avg_score,
        "streak": streak,
        "xpEarned": xp_earned,
        "dailyActivity": daily_activity, # Array of hours for each day of month
        "comparison": {
            "prevMonthHours": prev_month_hours,
            "diff": hours_diff
        }
    }


# =============================================================================
# Issue #35: Progress Analytics & Heat Maps (Learner)
# =============================================================================

@router.get("/learner/heatmap")
def get_learning_heatmap(
    days: int = 365,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #35: Learning activity heatmap (GitHub-style).
    Returns daily activity levels for the specified number of days.
    """
    from app.models.content import SpeakingSession
    from sqlalchemy import cast, Date
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Get daily session counts
    stats = db.query(
        cast(SpeakingSession.start_time, Date).label("date"),
        func.count(SpeakingSession.session_id).label("count")
    ).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= start_date
    ).group_by(
        cast(SpeakingSession.start_time, Date)
    ).all()
    
    # Convert to heatmap format (0-4 intensity levels)
    result = []
    for s in stats:
        # Calculate intensity level based on session count
        if s.count >= 5:
            level = 4
        elif s.count >= 3:
            level = 3
        elif s.count >= 2:
            level = 2
        elif s.count >= 1:
            level = 1
        else:
            level = 0
            
        result.append({
            "date": str(s.date),
            "count": s.count,
            "level": level
        })
    
    return {
        "days": days,
        "data": result,
        "total_sessions": sum(s.count for s in stats)
    }

@router.get("/learner/skills-radar")
def get_skills_radar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #35: Skills radar chart data.
    Returns average scores for grammar, fluency, pronunciation.
    """
    from app.models.content import SpeakingSession, AIFeedback
    
    # Get average AI feedback scores
    feedback = db.query(
        func.avg(AIFeedback.grammar_score).label("grammar"),
        func.avg(AIFeedback.fluency_score).label("fluency"),
        func.avg(AIFeedback.pronunciation_score).label("pronunciation")
    ).join(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id
    ).first()
    
    return {
        "grammar": round(float(feedback.grammar or 0), 1),
        "fluency": round(float(feedback.fluency or 0), 1),
        "pronunciation": round(float(feedback.pronunciation or 0), 1),
        "overall": round(
            (float(feedback.grammar or 0) + 
             float(feedback.fluency or 0) + 
             float(feedback.pronunciation or 0)) / 3, 1
        )
    }


# --- Issue #40: Advanced Analytics & Daily Stats ---

@router.get("/advanced")
def get_advanced_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #40: Advanced Analytics
    - Time of day analysis (when user practices most)
    - Retention rate (this week vs last week)
    - Learning patterns
    """
    from app.models.content import SpeakingSession
    
    today = datetime.now().date()
    
    # 1. Time of Day Analysis
    sessions = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id
    ).all()
    
    hour_distribution = [0] * 24
    for s in sessions:
        if s.start_time:
            hour_distribution[s.start_time.hour] += 1
    
    # Find peak hours (top 3)
    peak_hours = []
    if any(hour_distribution):
        sorted_hours = sorted(range(24), key=lambda h: hour_distribution[h], reverse=True)
        peak_hours = [{"hour": h, "sessions": hour_distribution[h]} for h in sorted_hours[:3] if hour_distribution[h] > 0]
    
    # Determine practice time category
    morning = sum(hour_distribution[6:12])
    afternoon = sum(hour_distribution[12:18])
    evening = sum(hour_distribution[18:24])
    night = sum(hour_distribution[0:6])
    
    time_preference = "morning" if morning >= max(afternoon, evening, night) else \
                     "afternoon" if afternoon >= max(evening, night) else \
                     "evening" if evening >= night else "night"
    
    # 2. Retention Rate (this week vs last week)
    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(days=7)
    
    this_week_count = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= this_week_start
    ).count()
    
    last_week_count = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= last_week_start,
        SpeakingSession.start_time < this_week_start
    ).count()
    
    if last_week_count > 0:
        retention_rate = round((this_week_count / last_week_count) * 100, 1)
    else:
        retention_rate = 100.0 if this_week_count > 0 else 0.0
    
    # 3. Weekly learning trend
    weekly_trend = []
    for i in range(4):  # Last 4 weeks
        week_start = this_week_start - timedelta(days=7 * i)
        week_end = week_start + timedelta(days=6)
        count = db.query(SpeakingSession).filter(
            SpeakingSession.user_id == current_user.user_id,
            SpeakingSession.start_time >= week_start,
            SpeakingSession.start_time <= week_end
        ).count()
        weekly_trend.append({
            "week_start": week_start.isoformat(),
            "sessions": count
        })
    
    weekly_trend.reverse()  # Chronological order
    
    return {
        "timeOfDay": {
            "distribution": hour_distribution,
            "peakHours": peak_hours,
            "preference": time_preference
        },
        "retention": {
            "thisWeek": this_week_count,
            "lastWeek": last_week_count,
            "ratePercent": retention_rate,
            "trend": "improving" if retention_rate > 100 else "declining" if retention_rate < 100 else "stable"
        },
        "weeklyTrend": weekly_trend
    }

@router.get("/daily-stats")
def get_daily_aggregated_stats(
    date: str = None,  # YYYY-MM-DD
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #40: Daily stats aggregation
    Returns detailed stats for a specific day for chart visualization.
    """
    # Parse date or use today
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            target_date = datetime.now().date()
    else:
        target_date = datetime.now().date()
    
    # Get stats for specific day
    stat = db.query(UserDailyStats).filter(
        UserDailyStats.user_id == current_user.user_id,
        func.date(UserDailyStats.date) == target_date
    ).first()
    
    # Get sessions for this day
    from app.models.content import SpeakingSession, AIFeedback
    
    sessions = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        func.date(SpeakingSession.start_time) == target_date
    ).all()
    
    # Calculate average scores
    feedback_scores = db.query(
        func.avg(AIFeedback.grammar_score).label("grammar"),
        func.avg(AIFeedback.pronunciation_score).label("pronunciation"),
        func.avg(AIFeedback.fluency_score).label("fluency")
    ).join(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        func.date(SpeakingSession.start_time) == target_date
    ).first()
    
    if not stat:
        return {
            "date": target_date.isoformat(),
            "speakingMinutes": 0,
            "wordsLearned": 0,
            "sessionsCount": len(sessions),
            "scores": {
                "grammar": 0,
                "pronunciation": 0,
                "fluency": 0
            }
        }
    
    return {
        "date": target_date.isoformat(),
        "speakingMinutes": round((stat.speaking_duration_seconds or 0) / 60, 1),
        "wordsLearned": stat.words_learned or 0,
        "sessionsCount": len(sessions),
        "scores": {
            "grammar": round(feedback_scores.grammar or 0, 1) if feedback_scores else 0,
            "pronunciation": round(feedback_scores.pronunciation or 0, 1) if feedback_scores else 0,
            "fluency": round(feedback_scores.fluency or 0, 1) if feedback_scores else 0
        },
        "streak": stat.login_streak_current if stat else 0
    }

@router.get("/system-stats")
def get_system_performance_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #40: System-wide stats for admin dashboard
    Aggregated stats for system performance monitoring.
    """
    from app.models.content import SpeakingSession
    from app.models.user import User as UserModel, UserRole
    
    # Only admins can view system stats
    if current_user.role != UserRole.ADMIN:
        from fastapi import HTTPException
        raise HTTPException(403, "Admin access required")
    
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # User stats
    total_users = db.query(UserModel).count()
    active_users_7d = db.query(UserDailyStats.user_id).filter(
        UserDailyStats.date >= week_ago
    ).distinct().count()
    
    # Session stats
    sessions_7d = db.query(SpeakingSession).filter(
        SpeakingSession.start_time >= week_ago
    ).count()
    sessions_30d = db.query(SpeakingSession).filter(
        SpeakingSession.start_time >= month_ago
    ).count()
    
    # Average session duration
    avg_duration = db.query(func.avg(UserDailyStats.speaking_duration_seconds)).filter(
        UserDailyStats.date >= week_ago
    ).scalar() or 0
    
    return {
        "users": {
            "total": total_users,
            "active7d": active_users_7d
        },
        "sessions": {
            "last7d": sessions_7d,
            "last30d": sessions_30d,
            "avgDurationMinutes": round(avg_duration / 60, 1) if avg_duration else 0
        },
        "generatedAt": datetime.now().isoformat()
    }


# =============================================================================
# Issue #39: Weekly/Monthly Reports (Learner)
# =============================================================================

@router.get("/reports/generate")
def generate_learner_report(
    period: str = "weekly",  # weekly or monthly
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #39: Generate weekly/monthly performance report for learner.
    Returns comprehensive summary of progress, errors, and XP.
    """
    from app.models.content import SpeakingSession, AIFeedback
    from app.models.gamification import UserDailyStats
    
    # Calculate date range
    if period == "weekly":
        days = 7
    else:
        days = 30
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Sessions count
    sessions = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= start_date
    ).all()
    
    total_sessions = len(sessions)
    total_minutes = sum(
        (s.end_time - s.start_time).total_seconds() / 60 
        for s in sessions if s.end_time and s.start_time
    )
    
    # Average scores from AI feedback
    feedback = db.query(
        func.avg(AIFeedback.grammar_score).label("grammar"),
        func.avg(AIFeedback.fluency_score).label("fluency"),
        func.avg(AIFeedback.pronunciation_score).label("pronunciation"),
        func.count(AIFeedback.feedback_id).label("feedback_count")
    ).join(SpeakingSession).filter(
        SpeakingSession.user_id == current_user.user_id,
        SpeakingSession.start_time >= start_date
    ).first()
    
    # Words learned from daily stats
    words_learned = db.query(func.sum(UserDailyStats.words_learned)).filter(
        UserDailyStats.user_id == current_user.user_id,
        UserDailyStats.date >= start_date.date()
    ).scalar() or 0
    
    # XP earned
    xp_earned = db.query(func.sum(UserDailyStats.xp_earned)).filter(
        UserDailyStats.user_id == current_user.user_id,
        UserDailyStats.date >= start_date.date()
    ).scalar() or 0
    
    # Calculate streak
    from app.models.user import User
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    streak = user.streak_count if user else 0
    
    return {
        "period": period,
        "dateRange": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": datetime.now().strftime("%Y-%m-%d")
        },
        "summary": {
            "totalSessions": total_sessions,
            "totalMinutes": round(total_minutes, 1),
            "wordsLearned": words_learned,
            "xpEarned": xp_earned,
            "currentStreak": streak
        },
        "scores": {
            "grammar": round(float(feedback.grammar or 0), 1),
            "fluency": round(float(feedback.fluency or 0), 1),
            "pronunciation": round(float(feedback.pronunciation or 0), 1),
            "sessionsScored": feedback.feedback_count or 0
        },
        "generatedAt": datetime.now().isoformat()
    }

@router.post("/reports/send-email")
def request_report_email(
    period: str = "weekly",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #39: Request report to be sent via email.
    Note: Email service integration is a placeholder for school project.
    """
    # Generate report data
    report = generate_learner_report(period, db, current_user)
    
    # Placeholder for email sending
    # In production: integrate with SendGrid/SES/etc.
    
    return {
        "message": f"Report request submitted for {current_user.email}",
        "period": period,
        "note": "Email service integration pending (school project placeholder)"
    }
