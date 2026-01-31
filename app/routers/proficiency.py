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
        logger.info(f"DEBUG: Processing answers: {data.answers}")
        
        for q in test.questions_json:
            # Handle both string and int possibilities for ID matching
            qid_str = str(q.get("id"))
            qid_int = q.get("id")
            
            # Try getting answer with string key first, then int key
            user_ans = data.answers.get(qid_str)
            if user_ans is None and isinstance(qid_int, int):
                 user_ans = data.answers.get(qid_int) # Try generic lookup if keys are ints
            
            # Simple normalization of string keys in answers dict if it helps
            # But safer to just look up flexible.
            
            correct_opt = q.get("correct_option")
            logger.info(f"DEBUG: Q{qid_str} - User: {user_ans} vs Correct: {correct_opt}") 
            
            if user_ans and user_ans == correct_opt:
                correct_count += 1
        
        score = (correct_count / total_questions) * 100
        logger.info(f"DEBUG: Total Score: {score} ({correct_count}/{total_questions})")

    # 2b. (Removed Speaking Score - Grammar/Vocab only)
    ai_feedback = None
    # if data.speaking_text: ... (REMOVED)
    
    score = min(100, score) # Cap at 100

    # 3. Determine Level
    level = "A1" # Default
    if test.level_criteria_json:
        # Sort criteria by score ascending to ensure we find the highest matching level
        # items() -> [("A1", 0), ("A2", 30)...]
        sorted_criteria = sorted(test.level_criteria_json.items(), key=lambda item: item[1])
        
        for lvl, min_score in sorted_criteria:
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

    # Query existing path to update or create new
    existing_path = db.query(LearningPath).filter(LearningPath.user_id == current_user.user_id).first()

    try:
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
    except Exception as e:
        logger.error(f"Database commit error in submit_test: {e}")
        db.rollback()
        return {"level": level, "score": score, "message": "Assessment complete (Data save failed)", "feedback": "Great job completing the test!"}
    
    return {"level": level, "score": score, "message": "Assessment complete", "feedback": "Great job! Based on your grammar and vocabulary, we have assigned your level."}

@router.get("/test", response_model=TestResponse)
def get_placement_test(db: Session = Depends(get_db)):
    # Return the first active test (Placement Test)
    test = db.query(ProficiencyTest).first()
    if not test:
        # Create a comprehensive placement test with 20 questions (Grammar & Vocabulary Only)
        default_questions = [
            # ============================================
            # GRAMMAR SECTION (10 questions - A1 to C1)
            # ============================================
            # A1 Level
            {"id": 1, "type": "grammar", "text": "She _____ to school every day.", 
             "options": ["go", "goes", "going", "gone"], "correct_option": "goes"},
            {"id": 2, "type": "grammar", "text": "I _____ a student.", 
             "options": ["am", "is", "are", "be"], "correct_option": "am"},
            {"id": 3, "type": "grammar", "text": "They _____ playing football now.", 
             "options": ["is", "are", "am", "be"], "correct_option": "are"},
            
            # A2 Level
            {"id": 4, "type": "grammar", "text": "He _____ to London last week.", 
             "options": ["go", "goes", "went", "gone"], "correct_option": "went"},
            {"id": 5, "type": "grammar", "text": "I have _____ my homework.", 
             "options": ["do", "did", "done", "doing"], "correct_option": "done"},
            
            # B1 Level
            {"id": 6, "type": "grammar", "text": "If I _____ rich, I would travel the world.", 
             "options": ["am", "was", "were", "be"], "correct_option": "were"},
            {"id": 7, "type": "grammar", "text": "The book _____ by millions of people.", 
             "options": ["has read", "was read", "is reading", "read"], "correct_option": "was read"},
            
            # B2 Level
            {"id": 8, "type": "grammar", "text": "By this time next year, I _____ graduated.", 
             "options": ["will have", "would have", "have", "had"], "correct_option": "will have"},
            {"id": 9, "type": "grammar", "text": "He asked me where I _____.", 
             "options": ["live", "lived", "living", "am living"], "correct_option": "lived"},
            
            # C1 Level
            {"id": 10, "type": "grammar", "text": "_____ the circumstances, we decided to postpone the meeting.", 
             "options": ["Given", "Giving", "To give", "Having given"], "correct_option": "Given"},
            
            # ============================================
            # VOCABULARY SECTION (10 questions - A1 to C1)
            # ============================================
            # A1-A2 Level
            {"id": 11, "type": "vocabulary", "text": "What is the opposite of 'big'?", 
             "options": ["Large", "Small", "Huge", "Giant"], "correct_option": "Small"},
            {"id": 12, "type": "vocabulary", "text": "Choose the synonym of 'happy':", 
             "options": ["Sad", "Angry", "Joyful", "Tired"], "correct_option": "Joyful"},
            {"id": 13, "type": "vocabulary", "text": "A person who teaches in a school is called a _____.", 
             "options": ["Doctor", "Teacher", "Engineer", "Lawyer"], "correct_option": "Teacher"},
            
            # B1 Level
            {"id": 14, "type": "vocabulary", "text": "To 'postpone' means to _____.", 
             "options": ["Cancel", "Delay", "Start", "Finish"], "correct_option": "Delay"},
            {"id": 15, "type": "vocabulary", "text": "Something that is 'inevitable' is _____.", 
             "options": ["Impossible", "Avoidable", "Certain to happen", "Optional"], "correct_option": "Certain to happen"},
            
            # B2 Level
            {"id": 16, "type": "vocabulary", "text": "The word 'ubiquitous' means _____.", 
             "options": ["Rare", "Present everywhere", "Invisible", "Expensive"], "correct_option": "Present everywhere"},
            {"id": 17, "type": "vocabulary", "text": "To 'exacerbate' a problem means to _____.", 
             "options": ["Solve it", "Ignore it", "Make it worse", "Prevent it"], "correct_option": "Make it worse"},
            {"id": 18, "type": "vocabulary", "text": "'Paradigm' most closely means _____.", 
             "options": ["Problem", "Model or pattern", "Mistake", "Paradox"], "correct_option": "Model or pattern"},
             
            # C1 Level (New additions)
            {"id": 19, "type": "vocabulary", "text": "Which word is a synonym for 'ephemeral'?", 
             "options": ["Lasting", "Short-lived", "Heavy", "Important"], "correct_option": "Short-lived"},
            {"id": 20, "type": "vocabulary", "text": "To 'scrutinize' means to _____.", 
             "options": ["Ignore", "Examine closely", "Write quickly", "Understand fully"], "correct_option": "Examine closely"},
        ]
        
        # Level criteria (adjusted for 20 questions)
        # A1: 0-29% (0-5 correct)
        # A2: 30-49% (6-9 correct)
        # B1: 50-69% (10-13 correct)
        # B2: 70-84% (14-16 correct)
        # C1: 85-94% (17-18 correct)
        # C2: 95-100% (19-20 correct)
        level_criteria = {"A1": 0, "A2": 30, "B1": 50, "B2": 70, "C1": 85, "C2": 95}
        
        test = ProficiencyTest(
            title="Grammar & Vocabulary Placement Test",
            questions_json=default_questions,
            level_criteria_json=level_criteria
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
