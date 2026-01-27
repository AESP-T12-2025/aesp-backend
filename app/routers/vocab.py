from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.core.database import get_db
from app.models.vocab import UserSavedVocab
from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter(prefix="/vocab", tags=["Vocabulary"])

class VocabSave(BaseModel):
    word: str
    meaning: str
    example: str = None

@router.post("/save")
def save_vocab(
    data: VocabSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_vocab = UserSavedVocab(
        user_id=current_user.user_id,
        word=data.word,
        meaning=data.meaning,
        example_sentence=data.example
    )
    db.add(new_vocab)
    db.commit()
    return {"message": "Saved"}

@router.get("/list")
def list_vocab(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = db.query(UserSavedVocab).filter(UserSavedVocab.user_id == current_user.user_id).all()
    return items
