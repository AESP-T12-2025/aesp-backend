from pydantic import BaseModel
from typing import Optional

class ChallengeBase(BaseModel):
    title: str
    description: Optional[str] = None
    points: int

class ChallengeCreate(ChallengeBase):
    pass

class ChallengeResponse(ChallengeBase):
    id: int
    class Config:
        from_attributes = True # Cho phép làm việc với SQLAlchemy model
