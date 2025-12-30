from fastapi import FastAPI
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(
    title="AESP - AI English Speaking Platform",
    description="API hệ thống luyện nói tiếng Anh hỗ trợ bởi AI",
    version="1.0.0",
    docs_url="/docs" # Đường dẫn Swagger UI
)

# Mock Data (Dữ liệu mẫu)
CATEGORIES = [
    {"id": 1, "name": "IELTS Speaking", "description": "Luyện thi IELTS"},
    {"id": 2, "name": "Daily Conversation", "description": "Giao tiếp hàng ngày"}
]

TOPICS = [
    {"id": 101, "category_id": 1, "title": "Environment", "level": "Intermediate"},
    {"id": 102, "category_id": 1, "title": "Education", "level": "Advanced"},
    {"id": 201, "category_id": 2, "title": "Introduction", "level": "Beginner"}
]
