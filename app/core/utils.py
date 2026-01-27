"""
Shared utility functions for AESP Backend
Contains pagination helpers and other common utilities
"""
from typing import TypeVar, List, Any, Dict, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Query
import logging
import re

from app.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# PAGINATION UTILITIES
# =============================================================================

class PaginationParams(BaseModel):
    """
    Standard pagination parameters for API requests.
    
    Attributes:
        skip: Number of items to skip (offset)
        limit: Maximum number of items to return
    """
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Maximum number of items to return"
    )
    
    def get_validated_limit(self) -> int:
        """Ensure limit doesn't exceed max."""
        return min(self.limit, MAX_PAGE_SIZE)


class PaginatedResponse(BaseModel):
    """
    Standard paginated response format.
    
    Attributes:
        items: List of items for current page
        total: Total number of items
        page: Current page number (1-indexed)
        per_page: Items per page
        pages: Total number of pages
        has_next: Whether there is a next page
        has_prev: Whether there is a previous page
    """
    items: List[Any]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    per_page: int = Field(ge=1)
    pages: int = Field(ge=0)
    has_next: bool
    has_prev: bool


def paginate(
    query: Query,
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE
) -> Dict[str, Any]:
    """
    Apply pagination to a SQLAlchemy query.
    
    Args:
        query: The SQLAlchemy query to paginate
        skip: Number of items to skip (offset)
        limit: Maximum number of items per page
        
    Returns:
        Dictionary with items and pagination metadata
        
    Example:
        >>> query = db.query(User).filter(User.is_active == True)
        >>> result = paginate(query, skip=0, limit=20)
        >>> return result
    """
    # Ensure limit is within bounds
    limit = min(max(limit, 1), MAX_PAGE_SIZE)
    skip = max(skip, 0)
    
    # Get total count (optimized for large datasets)
    total = query.count()
    
    # Calculate pagination metadata
    page = (skip // limit) + 1 if limit > 0 else 1
    pages = (total + limit - 1) // limit if limit > 0 and total > 0 else 1
    
    # Get paginated items
    items = query.offset(skip).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": limit,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }


# =============================================================================
# STRING UTILITIES
# =============================================================================

def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: The text to slugify
        
    Returns:
        URL-friendly slug string
    """
    # Lower case
    slug = text.lower()
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: The text to truncate
        max_length: Maximum length (including suffix)
        suffix: String to append when truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


# =============================================================================
# ROLE CHECKING UTILITIES (Deprecated - use deps.py)
# =============================================================================

def is_admin(user: Any) -> bool:
    """
    Check if user has admin role.
    
    DEPRECATED: Use `require_admin` dependency from `app.core.deps` instead.
    """
    from app.models.user import UserRole
    
    if user.role == UserRole.ADMIN:
        return True
    if hasattr(user.role, 'value') and user.role.value == "ADMIN":
        return True
    if str(user.role) == "ADMIN":
        return True
    return False


def is_mentor(user: Any) -> bool:
    """
    Check if user has mentor role.
    
    DEPRECATED: Use `require_mentor` dependency from `app.core.deps` instead.
    """
    from app.models.user import UserRole
    
    if user.role == UserRole.MENTOR:
        return True
    if hasattr(user.role, 'value') and user.role.value == "MENTOR":
        return True
    if str(user.role) == "MENTOR":
        return True
    return False


def require_admin(user: Any) -> None:
    """
    Raise 403 if user is not admin.
    
    This is a utility function for inline permission checks.
    For dependency injection, use `require_admin` from `app.core.deps`.
    
    Args:
        user: The user object to check
        
    Raises:
        HTTPException: If user is not an admin
    """
    from fastapi import HTTPException, status
    
    if not is_admin(user):
        logger.warning(f"Non-admin user {user.email} attempted admin action")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )


def require_mentor(user: Any) -> None:
    """
    Raise 403 if user is not mentor.
    
    This is a utility function for inline permission checks.
    For dependency injection, use `require_mentor` from `app.core.deps`.
    
    Args:
        user: The user object to check
        
    Raises:
        HTTPException: If user is not a mentor
    """
    from fastapi import HTTPException, status
    
    if not is_mentor(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mentor privileges required"
        )

