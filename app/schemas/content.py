from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.models.content import DifficultyLevel

# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    category_id: int

    class Config:
        from_attributes = True

# --- Topic Schemas ---
class TopicBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    industry: Optional[str] = "GENERAL" # NEW
    category_id: int

class TopicCreate(TopicBase):
    pass

class TopicResponse(TopicBase):
    topic_id: int

    class Config:
        from_attributes = True

# --- Scenario Schemas ---
class ScenarioBase(BaseModel):
    title: str
    difficulty_level: DifficultyLevel
    script_content: Optional[str] = None
    key_phrases: Optional[Dict[str, Any]] = None # Or List, depending on exact JSON structure
    topic_id: int

class ScenarioCreate(ScenarioBase):
    pass

class ScenarioResponse(ScenarioBase):
    scenario_id: int

    class Config:
        from_attributes = True
