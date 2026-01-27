from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core import database, deps
from app.schemas.user import UserResponse, UserCreate
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()

from typing import List

@router.get("/users", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    # current_user: User = Depends(deps.get_current_user) # Uncomment for auth
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(deps.get_current_user)):
    return current_user

class UserUpdate(BaseModel):
    full_name: str = None
    avatar_url: str = None
    daily_learning_goal: int = None

@router.put("/users/me", response_model=UserResponse)
def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(database.get_db),
):
    if user_update.full_name:
        current_user.full_name = user_update.full_name
    if user_update.avatar_url:
        current_user.avatar_url = user_update.avatar_url
    if user_update.daily_learning_goal:
        current_user.daily_learning_goal = user_update.daily_learning_goal
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/users/me/stats")
def read_user_stats(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(database.get_db)
):
    from app.models.proficiency import LearningPath
    from app.models.gamification import UserDailyStats
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # 1. Level
    path = db.query(LearningPath).filter(LearningPath.user_id == current_user.user_id).first()
    level = path.current_level if path else "Unassessed"

    # 2. Aggregated Stats
    stats_query = db.query(
        func.sum(UserDailyStats.words_learned).label("total_words"),
        func.sum(UserDailyStats.speaking_duration_seconds).label("total_seconds")
    ).filter(UserDailyStats.user_id == current_user.user_id).first()

    total_words = stats_query.total_words or 0
    total_seconds = stats_query.total_seconds or 0
    
    # XP = Words * 10 + Bonus from Challenges
    total_xp = (total_words * 10) + (current_user.bonus_xp or 0)
    practice_hours = round(total_seconds / 3600, 1)

    # 3. Calculate Current Streak
    today = datetime.now().date()
    streak = 0
    check_date = today
    
    while True:
        day_stat = db.query(UserDailyStats).filter(
            UserDailyStats.user_id == current_user.user_id,
            func.date(UserDailyStats.date) == check_date
        ).first()
        
        if day_stat and (day_stat.speaking_duration_seconds > 0 or day_stat.words_learned > 0):
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
        
        if streak > 365:  # Safety limit
            break

    return {
        "full_name": current_user.full_name,
        "email": current_user.email,
        "level": level,
        "xp": total_xp,
        "practice_hours": practice_hours,
        "lessons_completed": total_words,
        "streak": streak  # NEW: Current streak in days
    }
