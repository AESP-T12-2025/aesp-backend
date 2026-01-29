from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core import security, database
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, Login
from app.core.config import settings
from app.core.limiter import limiter
from app.core.exceptions import DuplicateResourceException, AuthenticationException

router = APIRouter()

@router.post("/auth/register", response_model=UserResponse)
@limiter.limit("5/minute")
def register(request: Request, user_in: UserCreate, db: Session = Depends(database.get_db)):
    # Check if limiter is disabled for testing
    if hasattr(request.app.state, 'limiter') and not request.app.state.limiter.enabled:
        pass  # Skip rate limiting in tests
    
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise DuplicateResourceException(
            resource="Email",
            details={"email": user_in.email}
        )
    user = User(
        email=user_in.email,
        password_hash=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=user_in.is_active,
        role=user_in.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, login_data: Login, db: Session = Depends(database.get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not security.verify_password(login_data.password, user.password_hash):
        raise AuthenticationException(
            message="Email hoặc mật khẩu không chính xác"
        )
    
    # Issue #26: Check if user account is disabled
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa. Vui lòng liên hệ admin."
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
