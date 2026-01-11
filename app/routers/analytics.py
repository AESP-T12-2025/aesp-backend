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
