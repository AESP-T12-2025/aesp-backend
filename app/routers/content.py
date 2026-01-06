from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core import database, deps
from app.models.content import Category, Topic, Scenario
from app.schemas.content import CategoryResponse, TopicResponse, ScenarioResponse

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
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    # current_user = Depends(deps.get_current_user)
):
    query = db.query(Topic)
    if category_id:
        query = query.filter(Topic.category_id == category_id)
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
    # check_admin(current_user) # Uncomment to enforce Admin
    new_topic = Topic(**topic.dict())
    db.add(new_topic)
    db.commit()
    db.refresh(new_topic)
    return new_topic

@router.delete("/topics/{id}")
def delete_topic(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # check_admin(current_user)
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
    # check_admin(current_user)
    new_scenario = Scenario(**scenario.dict())
    db.add(new_scenario)
    db.commit()
    db.refresh(new_scenario)
    return new_scenario

@router.delete("/scenarios/{id}")
def delete_scenario(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(deps.get_current_user)
):
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
    scenario = db.query(Scenario).filter(Scenario.scenario_id == session_in.scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    new_session = SpeakingSession(
        user_id=current_user.user_id,
        scenario_id=session_in.scenario_id,
        start_time=session_in.start_time or datetime.now(),
        status="IN_PROGRESS" # Optional field if needed later, for now just create
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {
        "session_id": new_session.session_id,
        "message": "Session started successfully",
        "scenario_title": scenario.title
    }
