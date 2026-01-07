from pydantic import BaseModel, Field
from typing import List, Optional

class AssessmentEntry(BaseModel):
    """
    Cấu trúc cho từng đầu điểm (Score)
    """
    criteria_name: str = Field(..., example="Technical Skills")
    score: int = Field(..., ge=0, le=10, example=9) # Điểm từ 0-10

class MentorReviewCreate(BaseModel):
    """
    Dữ liệu yêu cầu khi Mentor tạo đánh giá mới
    """
    learner_id: int
    session_id: int
    note: Optional[str] = Field(None, example="Học viên tiếp thu tốt, cần thực hành thêm.")
    assessments: List[AssessmentEntry]

    class Config:
        from_attributes = True

class MentorReviewResponse(BaseModel):
    """
    Dữ liệu trả về sau khi lưu thành công
    """
    id: int
    message: str = "Đánh giá đã được lưu thành công."

    class Config:
        from_attributes = True
