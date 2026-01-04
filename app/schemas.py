from pydantic import BaseModel
from typing import List, Optional

class SpeakingSession(BaseModel):
    user_id: str
    scenario_id: str
    duration_seconds: int
    transcript: str
    score: Optional[float] = None

class VocabItem(BaseModel):
    word: str
    definition: str
