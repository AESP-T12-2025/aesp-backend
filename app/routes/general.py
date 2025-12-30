from fastapi import APIRouter
from app.models import Category, Topic
from typing import List

router = APIRouter()

# Dữ liệu mẫu (sau này sẽ thay bằng gọi Database)
categories_db = [
    {"id": 1, "name": "Daily Life", "description": "Giao tiếp hàng ngày"},
    {"id": 2, "name": "Business", "description": "Tiếng Anh công sở"}
]

topics_db = [
    {"id": 101, "category_id": 1, "title": "Hobbies", "level": "Easy"},
    {"id": 201, "category_id": 2, "title": "Job Interview", "level": "Hard"}
]

@router.get("/categories", response_model=List[Category])
async def get_categories():
    return categories_db

@router.get("/topics", response_model=List[Topic])
async def get_topics(category_id: int = None):
    if category_id:
        return [t for t in topics_db if t["category_id"] == category_id]
    return topics_db
