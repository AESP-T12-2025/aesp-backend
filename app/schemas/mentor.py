from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MentorSchema(BaseModel):
    user_id: int # Linked to existing user
    full_name: str
    bio: Optional[str] = None
    skills: Optional[str] = None

class MentorCreate(BaseModel):
    full_name: str
    bio: Optional[str] = None
    skills: Optional[str] = None

class SlotCreate(BaseModel):
    start_time: datetime
    end_time: datetime

class BookingCreate(BaseModel):
    slot_id: int

class MentorResponse(MentorSchema):
    mentor_id: int
    verification_status: str
    
    class Config:
        from_attributes = True
