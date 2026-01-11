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
        orm_mode = True

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

@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    # Simple logic: Top users by daily stats 'words_learned' for demo
    # Real logic might be aggregations of all time
    stats = db.query(UserDailyStats).order_by(UserDailyStats.words_learned.desc()).limit(10).all()
    results = []
    for s in stats:
        results.append({
            "user_name": s.user.full_name if s.user else "Unknown",
            "words_learned_today": s.words_learned
        })
    return results
