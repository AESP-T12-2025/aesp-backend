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


# =============================================================================
# Issue #51: Google OAuth Endpoints
# =============================================================================

from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.oauth_service import oauth_service, AuthProvider, GoogleUserInfo
from app.core.deps import get_current_user


class GoogleTokenRequest(BaseModel):
    access_token: Optional[str] = None
    id_token: Optional[str] = None


class GoogleLinkRequest(BaseModel):
    google_token: str
    email: Optional[str] = None


@router.get("/auth/google/login")
def google_login():
    """
    Issue #51: Get Google OAuth authorization URL.
    
    Returns URL to redirect user to Google for authentication.
    """
    result = oauth_service.get_google_auth_url()
    return result


@router.get("/auth/google/callback")
async def google_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(database.get_db)
):
    """
    Issue #51: Handle Google OAuth callback.
    
    Google redirects here after user authentication.
    """
    if error:
        raise HTTPException(400, f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(400, "Authorization code is required")
    
    # Validate state (if provided)
    if state:
        state_data = oauth_service.validate_state(state)
        if not state_data:
            raise HTTPException(400, "Invalid or expired state parameter")
    
    # Exchange code for tokens
    tokens = await oauth_service.exchange_google_code(code)
    if not tokens:
        raise HTTPException(401, "Failed to exchange authorization code")
    
    # Get user info
    user_info = await oauth_service.get_google_user_info(tokens.access_token)
    if not user_info:
        raise HTTPException(401, "Failed to get user info from Google")
    
    # Find or create user
    user = db.query(User).filter(User.email == user_info.email).first()
    
    if not user:
        # Create new user from Google info
        user = User(
            email=user_info.email,
            full_name=user_info.name,
            password_hash="",  # No password for OAuth users
            is_active=True,
            role="LEARNER"  # Default role for new OAuth users
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Check if account is disabled
    if not user.is_active:
        raise HTTPException(403, "Account is disabled")
    
    # Link Google account
    oauth_service.link_oauth_account(
        user_id=user.user_id,
        provider=AuthProvider.GOOGLE,
        provider_user_id=user_info.email
    )
    
    # Create JWT token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.user_id,
            "email": user.email,
            "full_name": user.full_name
        }
    }


@router.post("/auth/google/token")
async def google_token_login(
    token_request: GoogleTokenRequest,
    db: Session = Depends(database.get_db)
):
    """
    Issue #51: Login with Google tokens directly.
    
    For mobile apps that handle OAuth flow client-side.
    """
    user_info = None
    
    # Prefer ID token validation
    if token_request.id_token:
        user_info = await oauth_service.validate_google_id_token(token_request.id_token)
    elif token_request.access_token:
        user_info = await oauth_service.get_google_user_info(token_request.access_token)
    else:
        raise HTTPException(400, "access_token or id_token is required")
    
    if not user_info:
        raise HTTPException(401, "Invalid Google token")
    
    # Find or create user
    user = db.query(User).filter(User.email == user_info.email).first()
    
    if not user:
        user = User(
            email=user_info.email,
            full_name=user_info.name,
            password_hash="",
            is_active=True,
            role="LEARNER"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    if not user.is_active:
        raise HTTPException(403, "Account is disabled")
    
    # Link Google account
    oauth_service.link_oauth_account(
        user_id=user.user_id,
        provider=AuthProvider.GOOGLE,
        provider_user_id=user_info.email
    )
    
    # Create JWT token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.user_id,
            "email": user.email,
            "full_name": user.full_name
        }
    }


@router.post("/auth/google/link")
async def link_google_account(
    link_request: GoogleLinkRequest,
    db: Session = Depends(database.get_db)
):
    """
    Issue #51: Link Google account to existing user.
    """
    # Validate Google token
    user_info = await oauth_service.validate_google_id_token(link_request.google_token)
    if not user_info:
        user_info = await oauth_service.get_google_user_info(link_request.google_token)
    
    if not user_info:
        raise HTTPException(401, "Invalid Google token")
    
    # Find existing user by email
    email_to_find = link_request.email or user_info.email
    user = db.query(User).filter(User.email == email_to_find).first()
    
    if not user:
        raise HTTPException(404, "User not found")
    
    # Link the account
    result = oauth_service.link_oauth_account(
        user_id=user.user_id,
        provider=AuthProvider.GOOGLE,
        provider_user_id=user_info.email
    )
    
    return result


@router.delete("/auth/google/unlink")
def unlink_google_account(
    current_user: User = Depends(get_current_user)
):
    """
    Issue #51: Unlink Google account from user.
    """
    result = oauth_service.unlink_oauth_account(
        user_id=current_user.user_id,
        provider=AuthProvider.GOOGLE
    )
    
    if not result["success"]:
        raise HTTPException(400, result["message"])
    
    return result


# Placeholder endpoints for other OAuth providers

@router.get("/auth/facebook/login")
def facebook_login():
    """Facebook OAuth (not implemented)."""
    raise HTTPException(501, "Facebook OAuth not implemented")


@router.get("/auth/github/login")
def github_login():
    """GitHub OAuth (not implemented)."""
    raise HTTPException(501, "GitHub OAuth not implemented")

