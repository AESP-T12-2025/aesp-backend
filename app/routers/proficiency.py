from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.proficiency import ProficiencyTest, UserTestResult, LearningPath
from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter(prefix="/proficiency", tags=["Proficiency & Adaptive Learning"])

# --- Schemas ---
class TestSubmission(BaseModel):
    test_id: int
    answers: dict # {question_id: selected_option}

class LearningPathResponse(BaseModel):
    current_level: str
    target_level: str
    roadmap: List[str]

# --- APIs ---

@router.post("/submit")
def submit_test(
    data: TestSubmission, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch Test
    test = db.query(ProficiencyTest).filter(ProficiencyTest.id == data.test_id).first()
    if not test:
        raise HTTPException(404, "Test not found")
        
    # 2. Calculate Score
    # Assuming questions_json is List[dict] with "id", "correct_option" keys
    total_questions = len(test.questions_json)
    if total_questions == 0:
        score = 0
    else:
        correct_count = 0
        for q in test.questions_json:
            qid = str(q.get("id"))
            user_ans = data.answers.get(qid)
            if user_ans and user_ans == q.get("correct_option"):
                correct_count += 1
        
        score = (correct_count / total_questions) * 100

    # 3. Determine Level
    level = "A1" # Default
    if test.level_criteria_json:
        # e.g. {"A1": 0, "A2": 30, "B1": 50, ...}
        # Find highest key where score >= val
        # Simplified logic:
        for lvl, min_score in test.level_criteria_json.items():
            if score >= min_score:
                level = lvl
    else:
        # Fallback simple logic
        if score >= 90: level = "C2"
        elif score >= 75: level = "C1"
        elif score >= 60: level = "B2"
        elif score >= 45: level = "B1"
        elif score >= 30: level = "A2"
    
    # 2. Save Result
    result = UserTestResult(
        user_id=current_user.user_id,
        test_id=data.test_id,
        score=score,
        assessed_level=level
    )
    db.add(result)
    
    # 3. Generate/Update Learning Path
    # "Evaluates... then creates a tailored learning path"
    roadmap = ["Unit 1: Business Basics", "Unit 2: Negotiation", "Challenge: Daily Vlog"]
    
    existing_path = db.query(LearningPath).filter(LearningPath.user_id == current_user.user_id).first()
    if existing_path:
        existing_path.current_level = level
        existing_path.generated_roadmap_json = roadmap
    else:
        new_path = LearningPath(
            user_id=current_user.user_id,
            current_level=level,
            target_level="C1", # Default target
            generated_roadmap_json=roadmap
        )
        db.add(new_path)
    
    db.commit()
    return {"level": level, "score": score, "message": "Assessment complete"}

@router.get("/my-path", response_model=LearningPathResponse)
def get_learning_path(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    path = db.query(LearningPath).filter(LearningPath.user_id == current_user.user_id).first()
    if not path:
        raise HTTPException(404, "No learning path found. Take the test first.")
        
    return {
        "current_level": path.current_level,
        "target_level": path.target_level,
        "roadmap": path.generated_roadmap_json or []
    }
