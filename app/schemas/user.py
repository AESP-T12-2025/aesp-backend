from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    role: Optional[UserRole] = UserRole.LEARNER

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to return via API
class UserResponse(UserBase):
    user_id: int
    avatar_url: Optional[str] = None
    daily_learning_goal: Optional[int] = 15
    # is_admin is removed, frontend check role == UserRole.ADMIN

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class Login(BaseModel):
    email: EmailStr
    password: str
