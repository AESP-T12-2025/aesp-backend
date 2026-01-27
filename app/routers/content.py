from fastapi import APIRouter, Depends, HTTPException, status
import logging
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core import database, deps
from app.models.content import Category, Topic, Scenario
from app.schemas.content import CategoryResponse, TopicResponse, ScenarioResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    # current_user = Depends(deps.get_current_user) # Optional if public
):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories

@router.get("/topics", response_model=List[TopicResponse])
def get_topics(
    category_id: Optional[int] = None,
    industry: Optional[str] = None, # NEW
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    # current_user = Depends(deps.get_current_user)
):
    query = db.query(Topic)
    if category_id:
        query = query.filter(Topic.category_id == category_id)
    if industry and industry != "ALL":
        query = query.filter(Topic.industry == industry)
        
    topics = query.offset(skip).limit(limit).all()
    return topics

@router.get("/topics/{id}", response_model=TopicResponse)
def get_topic(
    id: int,
    db: Session = Depends(database.get_db),
):
    topic = db.query(Topic).filter(Topic.topic_id == id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic

@router.get("/scenarios", response_model=List[ScenarioResponse])
def get_scenarios(
    topic_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
):
    query = db.query(Scenario)
    if topic_id:
        query = query.filter(Scenario.topic_id == topic_id)
    scenarios = query.offset(skip).limit(limit).all()
    return scenarios

@router.get("/scenarios/{id}", response_model=ScenarioResponse)
def get_scenario(
    id: int,
    db: Session = Depends(database.get_db),
    # current_user = Depends(deps.get_current_user)
):
    scenario = db.query(Scenario).filter(Scenario.scenario_id == id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario

@router.get("/scenarios/{id}/vocab")
def get_scenario_vocab(
    id: int,
    db: Session = Depends(database.get_db)
):
    scenario = db.query(Scenario).filter(Scenario.scenario_id == id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Trả về key_phrases (dạng JSON) của kịch bản
    return {
        "scenario_id": id,
        "vocabulary": scenario.key_phrases or {}
    }

# --- Admin Routes (Protected) ---

from app.schemas.content import TopicCreate, ScenarioCreate
from app.models.user import UserRole
from app.models.user import User

# Helper to check Admin (Simple version)
def check_admin(user: User):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")

@router.post("/topics", response_model=TopicResponse)
def create_topic(
    topic: TopicCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    check_admin(current_user)  # SECURITY: Enforce Admin
    new_topic = Topic(**topic.dict())
    db.add(new_topic)
    db.commit()
    db.refresh(new_topic)
    return new_topic

    db.refresh(new_topic)
    return new_topic

@router.put("/topics/{id}", response_model=TopicResponse)
def update_topic(
    id: int,
    topic_in: TopicCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    check_admin(current_user)  # SECURITY: Enforce Admin
    topic = db.query(Topic).filter(Topic.topic_id == id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    topic.name = topic_in.name
    topic.description = topic_in.description
    # Note: image_url needs handling if TopicCreate has it (it should)
    if hasattr(topic_in, 'image_url') and topic_in.image_url:
        topic.image_url = topic_in.image_url
    
    db.commit()
    db.refresh(topic)
    return topic

@router.delete("/topics/{id}")
def delete_topic(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    check_admin(current_user)  # SECURITY: Enforce Admin
    topic = db.query(Topic).filter(Topic.topic_id == id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    db.delete(topic)
    db.commit()
    return {"message": "Topic deleted successfully"}

@router.post("/scenarios", response_model=ScenarioResponse)
def create_scenario(
    scenario: ScenarioCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    check_admin(current_user)  # SECURITY: Enforce Admin
    new_scenario = Scenario(**scenario.dict())
    db.add(new_scenario)
    db.commit()
    db.refresh(new_scenario)
    return new_scenario

@router.put("/scenarios/{id}", response_model=ScenarioResponse)
def update_scenario(
    id: int,
    scenario_in: ScenarioCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    check_admin(current_user)  # SECURITY: Enforce Admin
    scenario = db.query(Scenario).filter(Scenario.scenario_id == id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    scenario.title = scenario_in.title
    scenario.difficulty_level = scenario_in.difficulty_level
    scenario.topic_id = scenario_in.topic_id
    
    db.commit()
    db.refresh(scenario)
    return scenario

@router.delete("/scenarios/{id}")

def delete_scenario(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    scenario = db.query(Scenario).filter(Scenario.scenario_id == id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    db.delete(scenario)
    db.commit()
    return {"message": "Scenario deleted successfully"}

# --- Speaking Session API (Practice) ---
from pydantic import BaseModel
from datetime import datetime

class SpeakingSessionCreate(BaseModel):
    scenario_id: int
    start_time: datetime = None # Optional, default to now in DB if None

@router.post("/speaking-sessions")
def create_speaking_session(
    session_in: SpeakingSessionCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    from app.models.content import SpeakingSession
    
    # Verify scenario exists
    try:
        scenario = db.query(Scenario).filter(Scenario.scenario_id == session_in.scenario_id).first()
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")

        new_session = SpeakingSession(
            user_id=current_user.user_id,
            scenario_id=session_in.scenario_id,
            start_time=session_in.start_time or datetime.now(),
            status="IN_PROGRESS"
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return {
            "session_id": new_session.session_id,
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Server Error creating session")
