from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

# 1. Định nghĩa dữ liệu mẫu (Thực tế sẽ lấy từ Database)
LEVEL_MAP = [
    {"min_score": 0, "max_score": 30, "rank": "Beginner (A1)"},
    {"min_score": 31, "max_score": 60, "rank": "Intermediate (B1)"},
    {"min_score": 61, "max_score": 85, "rank": "Advanced (C1)"},
    {"min_score": 86, "max_score": 100, "rank": "Expert (C2)"},
]

# 2. Schema dữ liệu đầu vào
class AnswerSchema(BaseModel):
    question_id: int
    selected_option: str

class TestSubmission(BaseModel):
    user_id: str
    answers: List[AnswerSchema]

# 3. Logic xử lý chính
def calculate_proficiency(user_answers: List[AnswerSchema]):
    # Giả lập đáp án đúng từ DB
    # Trong thực tế: db.query(Question).all()
    correct_answers = {
        1: {"ans": "A", "points": 5},
        2: {"ans": "C", "points": 5},
        3: {"ans": "B", "points": 10}, # Câu khó hơn điểm cao hơn
    }
    
    total_score = 0
    for item in user_answers:
        correct_info = correct_answers.get(item.question_id)
        if correct_info and item.selected_option == correct_info["ans"]:
            total_score += correct_info["points"]
            
    # Xếp hạng dựa trên bảng điểm
    user_rank = "Unranked"
    for level in LEVEL_MAP:
        if level["min_score"] <= total_score <= level["max_score"]:
            user_rank = level["rank"]
            break
            
    return total_score, user_rank

# 4. API Endpoint
@app.post("/api/v1/test/submit")
async def submit_test(submission: TestSubmission):
    try:
        score, rank = calculate_proficiency(submission.answers)
        
        return {
            "status": "success",
            "user_id": submission.user_id,
            "total_score": score,
            "proficiency_level": rank,
            "message": f"Chúc mừng! Trình độ của bạn là {rank}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
