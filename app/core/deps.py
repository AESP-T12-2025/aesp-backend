"""
FastAPI Dependencies for AESP Backend
Provides reusable dependencies for authentication and authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: The HTTP Bearer credentials
        db: Database session
        
    Returns:
        The authenticated User object
        
    Raises:
        AuthenticationException: If token is missing, invalid, or user not found
    """
    if not credentials:
        raise AuthenticationException(message="Missing authentication token")
    
    token_str = credentials.credentials
    
    # Decode and validate token
    payload = decode_access_token(token_str)
    if not payload:
        raise AuthenticationException(message="Invalid or expired token")
    
    # Extract email from token payload
    email: Optional[str] = payload.get("sub")
    if not email:
        raise AuthenticationException(message="Invalid token payload")
    
    # Get user from database
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise AuthenticationException(message="User not found")
    
    if not user.is_active:
        raise AuthenticationException(message="User account is disabled")
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        The active User object
        
    Raises:
        AuthenticationException: If user is inactive
    """
    if not current_user.is_active:
        raise AuthenticationException(message="Inactive user")
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.
    Useful for endpoints that work both with and without authentication.
    
    Args:
        credentials: The HTTP Bearer credentials (optional)
        db: Database session
        
    Returns:
        The User object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials, db)
    except AuthenticationException:
        return None


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that requires admin role.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        The admin User object
        
    Raises:
        AuthorizationException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        # Handle enum/string comparison
        role_value = (
            current_user.role.value 
            if hasattr(current_user.role, 'value') 
            else str(current_user.role)
        )
        if role_value != "ADMIN":
            logger.warning(
                f"Non-admin user {current_user.email} attempted admin action"
            )
            raise AuthorizationException(message="Admin privileges required")
    return current_user


def require_mentor(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that requires mentor role.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        The mentor User object
        
    Raises:
        AuthorizationException: If user is not a mentor
    """
    if current_user.role != UserRole.MENTOR:
        role_value = (
            current_user.role.value 
            if hasattr(current_user.role, 'value') 
            else str(current_user.role)
        )
        if role_value != "MENTOR":
            raise AuthorizationException(message="Mentor privileges required")
    return current_user


def require_learner(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that requires learner role.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        The learner User object
        
    Raises:
        AuthorizationException: If user is not a learner
    """
    if current_user.role != UserRole.LEARNER:
        role_value = (
            current_user.role.value 
            if hasattr(current_user.role, 'value') 
            else str(current_user.role)
        )
        if role_value != "LEARNER":
            raise AuthorizationException(message="Learner privileges required")
    return current_user


def get_current_mentor(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's Mentor profile, auto-creating if needed.
    
    This dependency:
    1. Checks if user has MENTOR role
    2. Returns existing Mentor profile if found
    3. Auto-creates Mentor profile with PENDING status if missing
    
    Args:
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The Mentor object (existing or newly created)
        
    Raises:
        AuthorizationException: If user doesn't have MENTOR role
    """
    from app.models.mentor import Mentor
    
    # Check role
    role_value = (
        current_user.role.value 
        if hasattr(current_user.role, 'value') 
        else str(current_user.role)
    )
    if role_value != "MENTOR":
        raise AuthorizationException(message="Mentor role required")
    
    # Find existing mentor profile
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.user_id).first()
    
    if not mentor:
        # Auto-create with PENDING status (requires Admin approval)
        mentor = Mentor(
            user_id=current_user.user_id,
            full_name=current_user.full_name or "Mentor",
            verification_status="PENDING",
            bio="",
            skills=""
        )
        db.add(mentor)
        db.commit()
        db.refresh(mentor)
        logger.info(f"Auto-created Mentor profile for user {current_user.email}")
    
    return mentor
