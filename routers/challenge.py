from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/challenges", tags=["Challenges"])

# --- CRUD ---
@router.post("/", response_model=schemas.ChallengeResponse)
def create_challenge(challenge: schemas.ChallengeCreate, db: Session = Depends(get_db)):
    db_challenge = models.Challenge(**challenge.dict())
    db.add(db_challenge)
    db.commit()
    db.refresh(db_challenge)
    return db_challenge

@router.get("/", response_model=List[schemas.ChallengeResponse])
def read_challenges(db: Session = Depends(get_db)):
    return db.query(models.Challenge).all()

# --- LOGIC USER JOIN ---
@router.post("/{challenge_id}/join")
def join_challenge(challenge_id: int, user_id: int, db: Session = Depends(get_db)):
    # 1. Check tồn tại
    challenge = db.query(models.Challenge).filter(models.Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Thử thách không tồn tại")
    
    # 2. Check đã join chưa
    is_joined = db.query(models.UserChallenge).filter_by(user_id=user_id, challenge_id=challenge_id).first()
    if is_joined:
        raise HTTPException(status_code=400, detail="Bạn đã tham gia rồi")
    
    # 3. Lưu vào DB
    new_participation = models.UserChallenge(user_id=user_id, challenge_id=challenge_id)
    db.add(new_participation)
    db.commit()
    return {"message": "Tham gia thử thách thành công"}
