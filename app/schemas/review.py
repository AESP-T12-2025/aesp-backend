from pydantic import BaseModel, Field

class MentorReviewCreate(BaseModel):
    booking_id: str
    score: int = Field(..., ge=1, le=5)
    note: str = None
