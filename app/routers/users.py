from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core import database, deps
from app.schemas.user import UserResponse, UserCreate
from app.models.user import User

router = APIRouter()

@router.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(deps.get_current_user)):
    return current_user

@router.put("/users/me", response_model=UserResponse)
def update_user_me(
    full_name: str = None,
    avatar_url: str = None,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(database.get_db),
):
    if full_name:
        current_user.full_name = full_name
    if avatar_url:
        current_user.avatar_url = avatar_url
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
