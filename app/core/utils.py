"""
Shared utility functions for AESP Backend
"""
import logging
from fastapi import HTTPException, status
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

def is_admin(user: User) -> bool:
    """Check if user has admin role - handles both Enum and string comparison"""
    if user.role == UserRole.ADMIN:
        return True
    # Fallback for string comparison
    if hasattr(user.role, 'value') and user.role.value == "ADMIN":
        return True
    if str(user.role) == "ADMIN":
        return True
    return False

def require_admin(user: User) -> None:
    """Raise 403 if user is not admin"""
    if not is_admin(user):
        logger.warning(f"Non-admin user {user.email} attempted admin action")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

def is_mentor(user: User) -> bool:
    """Check if user has mentor role"""
    if user.role == UserRole.MENTOR:
        return True
    if hasattr(user.role, 'value') and user.role.value == "MENTOR":
        return True
    if str(user.role) == "MENTOR":
        return True
    return False

def require_mentor(user: User) -> None:
    """Raise 403 if user is not mentor"""
    if not is_mentor(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mentor privileges required"
        )
