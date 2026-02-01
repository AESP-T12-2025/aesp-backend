"""
Users Router
============
User profile management and statistics.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.user import UserResponse
from app.models.user import User


router = APIRouter(tags=["Users"])


# =============================================================================
# SCHEMAS
# =============================================================================

class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    daily_learning_goal: Optional[int] = Field(default=None, ge=5, le=120)
    learning_target: Optional[str] = Field(default=None, max_length=100)
    preferred_practice_time: Optional[str] = Field(default=None, max_length=100)
    target_level: Optional[str] = Field(default=None, max_length=10)


class UserStatsResponse(BaseModel):
    """Response schema for user statistics."""
    full_name: str
    email: str
    level: str
    xp: int
    practice_hours: float
    lessons_completed: int
    streak: int


# =============================================================================
# APIS
# =============================================================================

@router.get("/users", response_model=list[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)  # Uncomment for auth
):
    """
    List all users with pagination.
    
    Note: This endpoint should be admin-only in production.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/users/me", response_model=UserResponse)
def read_users_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user's profile."""
    # Fetch target level from LearningPath
    from app.models.proficiency import LearningPath
    path = db.query(LearningPath).filter(LearningPath.user_id == current_user.user_id).first()
    
    # We can attach arbitrary attributes to the SQLAlchmey model instance
    # if we are careful, or better, convert to dict. Pydantic from_attributes handles objects.
    if path:
        current_user.target_level = path.target_level
    else:
        current_user.target_level = None
        
    return current_user


@router.put("/users/me", response_model=UserResponse)
def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's profile."""
    # Only update fields that are provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    if user_update.daily_learning_goal is not None:
        current_user.daily_learning_goal = user_update.daily_learning_goal
    if user_update.learning_target is not None:
        current_user.learning_target = user_update.learning_target
    if user_update.preferred_practice_time is not None:
        current_user.preferred_practice_time = user_update.preferred_practice_time
    
    target_level_response = None
    if user_update.target_level is not None:
        from app.models.proficiency import LearningPath
        path = db.query(LearningPath).filter(LearningPath.user_id == current_user.user_id).first()
        if path:
            path.target_level = user_update.target_level
            db.add(path)
            target_level_response = user_update.target_level
        else:
            # Create a path if it doesn't exist (assuming default A1 curr level)
            new_path = LearningPath(
                user_id=current_user.user_id,
                current_level="A1",
                target_level=user_update.target_level
            )
            db.add(new_path)
            target_level_response = user_update.target_level
    else:
        # Fetch existing if not updating
        from app.models.proficiency import LearningPath
        path = db.query(LearningPath).filter(LearningPath.user_id == current_user.user_id).first()
        if path:
            target_level_response = path.target_level
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    current_user.target_level = target_level_response
    return current_user


@router.get("/users/me/stats", response_model=UserStatsResponse)
def read_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's learning statistics.
    
    Returns:
        - Level: Current proficiency level
        - XP: Total experience points
        - Practice hours: Total speaking practice time
        - Lessons completed: Total words learned
        - Streak: Consecutive learning days
    """
    from app.models.proficiency import LearningPath
    from app.models.gamification import UserDailyStats

    # 1. Get current level
    path = db.query(LearningPath).filter(
        LearningPath.user_id == current_user.user_id
    ).first()
    level = path.current_level if path else "Unassessed"

    # 2. Get aggregated stats
    stats_query = db.query(
        func.sum(UserDailyStats.words_learned).label("total_words"),
        func.sum(UserDailyStats.speaking_duration_seconds).label("total_seconds")
    ).filter(
        UserDailyStats.user_id == current_user.user_id
    ).first()

    total_words = stats_query.total_words or 0
    total_seconds = stats_query.total_seconds or 0
    
    # XP = Words * 10 + Bonus from Challenges
    total_xp = (total_words * 10) + (current_user.bonus_xp or 0)
    practice_hours = round(total_seconds / 3600, 1)

    # 3. Calculate current streak
    streak = _calculate_streak(db, current_user.user_id)

    return UserStatsResponse(
        full_name=current_user.full_name or "",
        email=current_user.email,
        level=level,
        xp=total_xp,
        practice_hours=practice_hours,
        lessons_completed=total_words,
        streak=streak
    )


def _calculate_streak(db: Session, user_id: int) -> int:
    """
    Calculate consecutive learning days for a user.
    
    A day counts if user has any speaking duration or words learned.
    """
    from app.models.gamification import UserDailyStats
    
    today = datetime.now(timezone.utc).date()
    streak = 0
    check_date = today
    max_streak = 365  # Safety limit
    
    while streak < max_streak:
        day_stat = db.query(UserDailyStats).filter(
            UserDailyStats.user_id == user_id,
            func.date(UserDailyStats.date) == check_date
        ).first()
        
        if day_stat and (day_stat.speaking_duration_seconds > 0 or day_stat.words_learned > 0):
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    return streak
