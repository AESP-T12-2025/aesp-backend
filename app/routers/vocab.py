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


# =============================================================================
# Issue #36: Vocabulary System (Learner/Mentor)
# =============================================================================

@router.delete("/{vocab_id}")
def delete_vocab(
    vocab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Issue #36: Delete saved vocabulary word."""
    vocab = db.query(UserSavedVocab).filter(
        UserSavedVocab.id == vocab_id,
        UserSavedVocab.user_id == current_user.user_id
    ).first()
    
    if not vocab:
        raise HTTPException(404, "Vocabulary not found")
    
    db.delete(vocab)
    db.commit()
    return {"message": "Vocabulary deleted"}

@router.get("/review")
def get_review_words(
    count: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #36: Get random words for flashcard review.
    Returns random vocabulary items for review mode.
    """
    from sqlalchemy.sql.expression import func
    
    words = db.query(UserSavedVocab).filter(
        UserSavedVocab.user_id == current_user.user_id
    ).order_by(func.random()).limit(count).all()
    
    result = []
    for w in words:
        result.append({
            "id": w.id,
            "word": w.word,
            "meaning": w.meaning,
            "example": w.example_sentence
        })
    
    return {"items": result, "total": len(result)}

class MentorVocabSuggestion(BaseModel):
    learner_id: int
    word: str
    meaning: str
    example: str = None
    tips: str = None

@router.post("/mentor-suggest")
def mentor_suggest_vocab(
    data: MentorVocabSuggestion,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #36: Mentor suggests vocabulary to learner.
    Creates a vocab entry for the specified learner.
    """
    from app.models.mentor import Mentor
    
    # Verify current user is a mentor
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    if not mentor:
        raise HTTPException(403, "Only mentors can suggest vocabulary")
    
    # Create vocab for learner
    new_vocab = UserSavedVocab(
        user_id=data.learner_id,
        word=data.word,
        meaning=data.meaning,
        example_sentence=data.example
    )
    db.add(new_vocab)
    db.commit()
    
    return {"message": f"Vocabulary suggested to learner {data.learner_id}"}

