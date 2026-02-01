from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.core.database import get_db
from app.models.gamification import Challenge, UserChallenge, UserDailyStats
from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter(prefix="/gamification", tags=["Gamification"])

# --- Schemas ---
class ChallengeResponse(BaseModel):
    id: int
    title: str
    description: str
    points_reward: int
    
    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    user_name: str
    total_xp: int # Using simple metric for now

# --- APIs ---

@router.get("/challenges", response_model=List[ChallengeResponse])
def get_challenges(db: Session = Depends(get_db)):
    return db.query(Challenge).all()

@router.post("/challenges/{challenge_id}/join")
def join_challenge(
    challenge_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(404, "Challenge not found")
        
    exists = db.query(UserChallenge).filter_by(
        user_id=current_user.user_id, 
        challenge_id=challenge_id
    ).first()
    
    if exists:
        return {"message": "Already joined"}
        
    new_entry = UserChallenge(
        user_id=current_user.user_id,
        challenge_id=challenge_id,
        current_progress=0
    )
    db.add(new_entry)
    db.commit()
    return {"message": "Joined challenge successfully"}

@router.post("/challenges/{challenge_id}/claim")
def claim_reward(
    challenge_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    uc = db.query(UserChallenge).filter_by(
        user_id=current_user.user_id, 
        challenge_id=challenge_id
    ).first()
    
    if not uc:
        raise HTTPException(404, "You have not joined this challenge")
        
    if not uc.is_completed:
        raise HTTPException(400, "Challenge not completed yet")
        
    if uc.is_claimed:
        raise HTTPException(400, "Reward already claimed")
        
    # Claim reward
    uc.is_claimed = True
    
    # Calculate points to award
    points = uc.challenge.points_reward
    
    # Update stats
    current_user.bonus_xp = (current_user.bonus_xp or 0) + points
    
    db.commit()
    return {"message": f"Claimed {points} XP successfully", "points": points}



@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    # Simple logic: Top users by daily stats 'words_learned' for demo
    # Real logic might be aggregations of all time
    stats = db.query(UserDailyStats).join(User).filter(User.role == "LEARNER").order_by(UserDailyStats.words_learned.desc()).limit(10).all()
    results = []
    for s in stats:
        results.append({
            "user_name": s.user.full_name if s.user else "Unknown",
            "total_xp": s.words_learned * 10 # consistent with users.py logic
        })
    return results

@router.get("/my-progress")
def get_my_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get all challenges
    all_challenges = db.query(Challenge).all()
    
    # Get user progress
    user_challenges = db.query(UserChallenge).filter(UserChallenge.user_id == current_user.user_id).all()
    progress_map = {uc.challenge_id: uc for uc in user_challenges}
    
    response = []
    for ch in all_challenges:
        uc = progress_map.get(ch.id)
        prog = uc.current_progress if uc else 0
        is_unlocked = uc.is_completed if uc else False
        is_claimed = uc.is_claimed if uc else False
        is_joined = True if uc else False 
        
        # Calculate percentage
        percent = min(100, int((prog / ch.target_value) * 100)) if ch.target_value > 0 else 0
        
        response.append({
            "id": ch.id,
            "title": ch.title,
            "description": ch.description,
            "progress": percent,
            "unlocked": is_unlocked,
            "claimed": is_claimed, # NEW
            "joined": is_joined, # NEW
            "points": ch.points_reward,
            "icon": "🏆" # Placeholder, could be in DB
        })
    return response

# --- Internal Helper ---
# Called by other services (like AI or Auth) to update challenge progress
def update_user_challenge_progress(db: Session, user_id: int, metric_type: str, increment_value: int):
    """
    metric_type matches ChallengeType enum values: 
    'VOCAB_COUNT', 'STREAK', 'SPEAKING_TIME', 'LESSON_COMPLETED'
    """
    from app.models.gamification import ChallengeType # ensure import
    
    # Find all active challenges for this user of this type
    user_challenges = db.query(UserChallenge).join(Challenge).filter(
        UserChallenge.user_id == user_id,
        UserChallenge.is_completed == False,
        Challenge.challenge_type == metric_type
    ).all()
    
    for uc in user_challenges:
        uc.current_progress += increment_value
        
        # Check completion
        if uc.current_progress >= uc.challenge.target_value:
            uc.current_progress = uc.challenge.target_value # Cap it
            uc.is_completed = True
            # Award points? (Logic can be added here or strictly visual)
            # e.g., user.xp += uc.challenge.points_reward
            
    db.commit()
