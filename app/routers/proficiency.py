from fastapi import APIRouter, Depends, HTTPException
import logging
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.proficiency import ProficiencyTest, UserTestResult, LearningPath
from app.models.user import User
from app.core.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proficiency", tags=["Proficiency & Adaptive Learning"])

# --- Schemas ---
class TestSubmission(BaseModel):
    test_id: int
    answers: dict # {question_id: selected_option}
    speaking_text: Optional[str] = None

class LearningPathResponse(BaseModel):
    current_level: str
    target_level: str
    roadmap: List[str]

class QuestionResponse(BaseModel):
    id: int
    type: str
    text: str
    options: Optional[List[str]] = None

class TestResponse(BaseModel):
    id: int
    title: str
    questions: List[QuestionResponse]

# --- APIs ---

@router.post("/submit")
async def submit_test(
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

    # 2b. Add Speaking Score (if any)
    ai_feedback = None
    if data.speaking_text:
        try:
            from app.services.ai_service import ai_service
            # Analyze speaking
            ai_res = await ai_service.analyze_speech(data.speaking_text)
            
            # Simple average: 70% Questions + 30% Speaking
            speaking_score = (ai_res.get("grammar_score", 0) + ai_res.get("pronunciation_score", 0)) / 2
            
            # Weighted Score
            score = (score * 0.7) + (speaking_score * 0.3)
            ai_feedback = ai_res.get("detailed_feedback") or "Good effort!"
        except Exception as e:
            logger.error(f"AI speech analysis error: {e}") 
    
    score = min(100, score) # Cap at 100

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
    # Map CEFR level to DifficultyLevel
    level_map = {
        "A1": "BEGINNER", "A2": "BEGINNER",
        "B1": "INTERMEDIATE", "B2": "INTERMEDIATE",
        "C1": "ADVANCED", "C2": "ADVANCED"
    }
    target_difficulty = level_map.get(level, "BEGINNER")
    
    # Query REAL scenarios from DB
    from app.models.content import Scenario
    suggested_scenarios = db.query(Scenario).filter(
        Scenario.difficulty_level == target_difficulty
    ).limit(5).all()
    
    if suggested_scenarios:
        roadmap = [f"Scenario: {s.title}" for s in suggested_scenarios]
    else:
        roadmap = [f"No {target_difficulty} scenarios found. Please contact admin."]

    existing_path = db.query(LearningPath).filter(LearningPath.user_id == current_user.user_id).first()
    if existing_path:
        existing_path.current_level = level
        existing_path.generated_roadmap_json = roadmap
    else:
        new_path = LearningPath(
            user_id=current_user.user_id,
            current_level=level,
            target_level="C1", 
            generated_roadmap_json=roadmap
        )
        db.add(new_path)
    
    db.commit()
    db.commit()
    return {"level": level, "score": score, "message": "Assessment complete", "feedback": ai_feedback}

@router.get("/test", response_model=TestResponse)
def get_placement_test(db: Session = Depends(get_db)):
    # Return the first active test (Placement Test)
    test = db.query(ProficiencyTest).first()
    if not test:
        # Create a default seed test if none exists
        default_questions = [
             {"id": 1, "type": "grammar", "text": "I _____ (be) a student.", "options": ["am", "is", "are", "be"], "correct_option": "am"},
             {"id": 2, "type": "vocabulary", "text": "Opposite of 'Big'?", "options": ["Large", "Small", "Huge", "Giant"], "correct_option": "Small"},
             {"id": 3, "type": "pronunciation", "text": "Please read this sentence: 'The quick brown fox jumps over the lazy dog.'", "correct_option": "audio_check"},
        ]
        test = ProficiencyTest(
            title="General Placement Test",
            questions_json=default_questions,
            level_criteria_json={"A1": 0, "A2": 30, "B1": 50, "B2": 70, "C1": 85, "C2": 95}
        )
        db.add(test)
        db.commit()
        db.refresh(test)
    
    # Transform for response (hide correct_option)
    q_response = []
    for q in test.questions_json:
        q_response.append({
            "id": q["id"],
            "type": q["type"],
            "text": q["text"],
            "options": q.get("options")
        })
        
    return {
        "id": test.id,
        "title": test.title,
        "questions": q_response
    }

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


# --- Issue #27: Personalized Learning Path (REQ-LEARNER-7) ---

class PersonalizedPathResponse(BaseModel):
    current_level: str
    recommended_topics: List[dict]
    next_milestone: str

@router.get("/path", response_model=PersonalizedPathResponse)
def get_personalized_learning_path(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    REQ-LEARNER-7: Personalized Learning Path
    Returns current level, recommended topics based on proficiency,
    and next milestone (always higher than current level).
    """
    from app.models.content import Topic, Scenario
    
    # 1. Get user's learning path or default to A1
    path = db.query(LearningPath).filter(
        LearningPath.user_id == current_user.user_id
    ).first()
    
    current_level = path.current_level if path else "A1"
    
    # 2. Calculate next milestone (must be higher than current)
    level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
    try:
        current_idx = level_order.index(current_level)
    except ValueError:
        current_idx = 0
        current_level = "A1"
    
    next_milestone = level_order[min(current_idx + 1, len(level_order) - 1)]
    
    # 3. Map CEFR to difficulty for topic recommendations
    difficulty_map = {
        "A1": "BEGINNER", "A2": "BEGINNER",
        "B1": "INTERMEDIATE", "B2": "INTERMEDIATE",
        "C1": "ADVANCED", "C2": "ADVANCED"
    }
    target_difficulty = difficulty_map.get(current_level, "BEGINNER")
    
    # 4. Get recommended topics based on user's level
    topics = db.query(Topic).join(
        Scenario, Topic.topic_id == Scenario.topic_id
    ).filter(
        Scenario.difficulty_level == target_difficulty
    ).distinct().limit(5).all()
    
    recommended_topics = [
        {
            "id": t.topic_id,
            "name": t.name,
            "difficulty": target_difficulty
        }
        for t in topics
    ]
    
    # 5. If no topics found, provide default recommendations
    if not recommended_topics:
        recommended_topics = [
            {"id": 0, "name": f"Start with {target_difficulty} level content", "difficulty": target_difficulty}
        ]
    
    return {
        "current_level": current_level,
        "recommended_topics": recommended_topics,
        "next_milestone": next_milestone
    }
