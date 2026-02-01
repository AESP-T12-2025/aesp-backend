"""
Social Router
=============
Community features: mentor posts, comments, likes, and moderation.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.utils import require_admin
from app.models.social import MentorPost, PostComment, PostLike, ModerationStatus
from app.models.user import User, UserRole


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/social", tags=["Social (Community)"])


# =============================================================================
# SCHEMAS
# =============================================================================

class PostCreate(BaseModel):
    """Schema for creating a mentor post."""
    content: str = Field(..., min_length=1, max_length=5000)
    image_url: Optional[str] = Field(default=None, max_length=500)


class CommentCreate(BaseModel):
    """Schema for creating a comment."""
    content: str = Field(..., min_length=1, max_length=1000)


class PostResponse(BaseModel):
    """Response schema for posts."""
    id: int
    mentor_id: int
    mentor_name: str
    content: str
    image_url: Optional[str] = None
    like_count: int
    comment_count: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminPostResponse(BaseModel):
    """Response schema for admin post management."""
    id: int
    content: str
    mentor_name: str
    status: str
    created_at: datetime


# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

@router.post("/posts", response_model=PostResponse)
def create_mentor_post(
    post_data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new community post.
    
    Only Mentors and Admins can create posts.
    Posts are auto-approved for Mentors to reduce friction.
    """
    if current_user.role not in (UserRole.MENTOR, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Mentors can post"
        )

    new_post = MentorPost(
        mentor_id=current_user.user_id,
        content=post_data.content,
        image_url=post_data.image_url,
        moderation_status=ModerationStatus.APPROVED
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return PostResponse(
        id=new_post.id,
        mentor_id=new_post.mentor_id,
        mentor_name=current_user.full_name or "Unknown",
        content=new_post.content,
        image_url=new_post.image_url,
        like_count=0,
        comment_count=0,
        created_at=new_post.created_at
    )


@router.get("/posts")
def get_community_feed(db: Session = Depends(get_db)):
    """
    Get community feed with approved posts.
    
    Returns posts ordered by most recent first.
    """
    posts = db.query(MentorPost).filter(
        MentorPost.moderation_status == ModerationStatus.APPROVED
    ).order_by(MentorPost.created_at.desc()).all()

    return [
        {
            "id": p.id,
            "mentor_id": p.mentor_id,
            "mentor_name": p.mentor.full_name if p.mentor else "Unknown",
            "content": p.content,
            "image_url": p.image_url,
            "like_count": len(p.likes) if p.likes else 0,
            "comment_count": len(p.comments) if p.comments else 0,
            "created_at": p.created_at,
            "is_liked": False  # Will be updated via separate check if needed
        }
        for p in posts
    ]


@router.get("/posts/{post_id}/comments")
def get_comments(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Get all comments for a post."""
    post = db.query(MentorPost).filter(MentorPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comments = db.query(PostComment).filter(PostComment.post_id == post_id).order_by(PostComment.created_at.asc()).all()
    
    return [
        {
            "id": c.id,
            "comment_id": c.id,
            "post_id": c.post_id,
            "user_id": c.user_id,
            "user_name": c.user.full_name if c.user else "Ẩn danh",
            "content": c.content,
            "created_at": c.created_at
        }
        for c in comments
    ]


@router.post("/posts/{post_id}/comments")
def add_comment(
    post_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a post."""
    post = db.query(MentorPost).filter(MentorPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = PostComment(
        post_id=post_id,
        user_id=current_user.user_id,
        content=comment_data.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return {
        "id": new_comment.id,
        "comment_id": new_comment.id,
        "user_id": new_comment.user_id,
        "user_name": current_user.full_name or "Ẩn danh",
        "content": new_comment.content,
        "created_at": new_comment.created_at,
        "message": "Comment added successfully"
    }


@router.post("/posts/{post_id}/like")
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle like on a post."""
    post = db.query(MentorPost).filter(MentorPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing_like = db.query(PostLike).filter_by(
        post_id=post_id,
        user_id=current_user.user_id
    ).first()

    if existing_like:
        db.delete(existing_like)
        db.commit()
        return {"message": "Unliked", "liked": False}
    else:
        new_like = PostLike(post_id=post_id, user_id=current_user.user_id)
        db.add(new_like)
        db.commit()
        return {"message": "Liked", "liked": True}


@router.post("/posts/{post_id}/report")
def report_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Report a post for moderation.
    
    When a learner reports a post, it changes status to REPORTED
    so Admin can review it in the moderation panel.
    """
    post = db.query(MentorPost).filter(MentorPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Only change to REPORTED if currently APPROVED
    if post.moderation_status == ModerationStatus.APPROVED:
        post.moderation_status = ModerationStatus.REPORTED
        db.commit()
        logger.info(f"Post {post_id} reported by user {current_user.user_id}")
        return {"message": "Báo cáo thành công. Admin sẽ xem xét bài viết này."}
    
    return {"message": "Bài viết đã được báo cáo trước đó."}


# =============================================================================
# ADMIN MODERATION ENDPOINTS
# =============================================================================

@router.get("/admin/posts")
def get_admin_posts(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all posts for admin moderation.
    
    Admin only.
    """
    require_admin(current_user)

    query = db.query(MentorPost).order_by(MentorPost.created_at.desc())
    
    if status:
        query = query.filter(MentorPost.moderation_status == status)

    posts = query.all()
    
    return [
        {
            "id": p.id,
            "content": p.content,
            "mentor_name": p.mentor.full_name if p.mentor else "Unknown",
            "status": p.moderation_status.value if hasattr(p.moderation_status, 'value') else p.moderation_status,
            "created_at": p.created_at
        }
        for p in posts
    ]


@router.put("/admin/posts/{post_id}/moderate")
def moderate_post(
    post_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve or reject a post.
    
    Admin only.
    
    Args:
        new_status: APPROVED or REJECTED
    """
    require_admin(current_user)

    post = db.query(MentorPost).filter(MentorPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Validate status
    valid_statuses = ["APPROVED", "REJECTED", "PENDING"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    post.moderation_status = new_status
    db.commit()
    
    logger.info(f"Post {post_id} moderated to {new_status} by admin {current_user.email}")
    
    return {"message": f"Post {new_status.lower()}"}


@router.delete("/admin/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a comment.
    
    Admin only.
    """
    require_admin(current_user)

    comment = db.query(PostComment).filter(PostComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    db.delete(comment)
    db.commit()
    
    return {"message": "Comment deleted successfully"}
