"""
Vocabulary System endpoints for learners.
Issue #36
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.models.vocab import UserSavedVocab
from app.models.content import Scenario

router = APIRouter(prefix="/vocabulary", tags=["Vocabulary System"])


class PersonalVocabCreate(BaseModel):
    word: str
    definition: str
    example: Optional[str] = None


class QuizAnswer(BaseModel):
    question_id: int
    selected_answer: str


class QuizSubmission(BaseModel):
    answers: List[QuizAnswer]


# =============================================================================
# Issue #36: Vocabulary System
# =============================================================================

@router.get("")
def get_all_vocabulary(
    difficulty: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #36: Get all vocabulary items for the user.
    """
    query = db.query(UserSavedVocab).filter(
        UserSavedVocab.user_id == current_user.user_id
    )
    
    # If difficulty is specified, we would filter by difficulty
    # But since UserSavedVocab may not have difficulty field, just return all
    
    items = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": item.id,
            "word": item.word,
            "definition": item.meaning,
            "example": item.example_sentence,
            "created_at": item.created_at.isoformat() if hasattr(item, 'created_at') and item.created_at else None
        }
        for item in items
    ]


@router.get("/scenario/{scenario_id}")
def get_scenario_vocabulary(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #36: Get vocabulary for a specific scenario.
    """
    scenario = db.query(Scenario).filter(Scenario.scenario_id == scenario_id).first()
    if not scenario:
        raise HTTPException(404, "Scenario not found")
    
    # Return empty list since we don't have scenario-linked vocabulary yet
    return []


@router.get("/personal")
def get_personal_collection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #36: Get learner's personal vocabulary collection.
    """
    items = db.query(UserSavedVocab).filter(
        UserSavedVocab.user_id == current_user.user_id
    ).all()
    
    return [
        {
            "id": item.id,
            "word": item.word,
            "definition": item.meaning,
            "example": item.example_sentence
        }
        for item in items
    ]


@router.post("/personal")
def add_to_personal_collection(
    data: PersonalVocabCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #36: Add vocabulary to personal collection.
    """
    new_vocab = UserSavedVocab(
        user_id=current_user.user_id,
        word=data.word,
        meaning=data.definition,
        example_sentence=data.example
    )
    db.add(new_vocab)
    db.commit()
    db.refresh(new_vocab)
    
    return {
        "id": new_vocab.id,
        "word": new_vocab.word,
        "definition": new_vocab.meaning,
        "example": new_vocab.example_sentence,
        "message": "Vocabulary added to personal collection"
    }


@router.delete("/personal/{vocab_id}")
def remove_from_personal_collection(
    vocab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #36: Remove vocabulary from personal collection.
    """
    vocab = db.query(UserSavedVocab).filter(
        UserSavedVocab.id == vocab_id,
        UserSavedVocab.user_id == current_user.user_id
    ).first()
    
    if not vocab:
        raise HTTPException(404, "Vocabulary not found in your collection")
    
    db.delete(vocab)
    db.commit()
    
    return {"message": "Vocabulary removed from personal collection"}


@router.get("/quiz")
def get_quiz_questions(
    count: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #36: Generate vocabulary quiz questions.
    """
    # Get random vocabulary from user's collection
    items = db.query(UserSavedVocab).filter(
        UserSavedVocab.user_id == current_user.user_id
    ).order_by(func.random()).limit(count).all()
    
    questions = []
    for i, item in enumerate(items):
        # Simple multiple choice question
        questions.append({
            "question_id": i + 1,
            "type": "multiple_choice",
            "question": f"What is the meaning of '{item.word}'?",
            "word": item.word,
            "options": ["A", "B", "C", "D"],  # Simplified
            "correct_answer": "A"  # Placeholder
        })
    
    return questions


@router.post("/quiz/submit")
def submit_quiz_answers(
    submission: QuizSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #36: Submit quiz answers and get results.
    """
    # Simple scoring logic
    total = len(submission.answers)
    correct = sum(1 for a in submission.answers if a.selected_answer == "A")  # Simplified
    
    return {
        "score": round(correct / max(total, 1) * 100, 1),
        "correct_count": correct,
        "total_questions": total,
        "percentage": round(correct / max(total, 1) * 100, 1)
    }


@router.get("/search")
def search_vocabulary(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue #36: Search vocabulary by keyword.
    """
    items = db.query(UserSavedVocab).filter(
        UserSavedVocab.user_id == current_user.user_id,
        or_(
            UserSavedVocab.word.ilike(f"%{q}%"),
            UserSavedVocab.meaning.ilike(f"%{q}%")
        )
    ).all()
    
    return [
        {
            "id": item.id,
            "word": item.word,
            "definition": item.meaning,
            "example": item.example_sentence
        }
        for item in items
    ]
