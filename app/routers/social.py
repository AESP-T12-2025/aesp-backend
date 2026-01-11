from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.social import MentorPost, PostComment, PostLike
from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter(prefix="/social", tags=["Social (Community)"])

# --- Schemas ---
class PostCreate(BaseModel):
    content: str
    image_url: Optional[str] = None

class CommentCreate(BaseModel):
    content: str

class PostResponse(BaseModel):
    id: int
    mentor_id: int
    mentor_name: str
    content: str
    image_url: Optional[str]
    like_count: int
    comment_count: int
    # created_at: datetime... (omitted for brevity)

    class Config:
        orm_mode = True

# --- APIs ---

@router.post("/posts", response_model=PostResponse)
def create_mentor_post(
    post_data: PostCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "MENTOR" and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only Mentors can post")

    new_post = MentorPost(
        mentor_id=current_user.user_id,
        content=post_data.content,
        image_url=post_data.image_url
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return {
        "id": new_post.id,
        "mentor_id": new_post.mentor_id,
        "mentor_name": current_user.full_name,
        "content": new_post.content,
        "image_url": new_post.image_url,
        "like_count": 0,
        "comment_count": 0
    }

@router.get("/posts", response_model=List[PostResponse])
def get_community_feed(db: Session = Depends(get_db)):
    posts = db.query(MentorPost).order_by(MentorPost.created_at.desc()).all()
    results = []
    for p in posts:
        mentor_name = p.mentor.full_name if p.mentor else "Unknown"
        results.append({
            "id": p.id,
            "mentor_id": p.mentor_id,
            "mentor_name": mentor_name,
            "content": p.content,
            "image_url": p.image_url,
            "like_count": len(p.likes),
            "comment_count": len(p.comments)
        })
    return results

@router.post("/posts/{post_id}/comments")
def add_comment(
    post_id: int, 
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(MentorPost).filter(MentorPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
        
    new_comment = PostComment(
        post_id=post_id,
        user_id=current_user.user_id,
        content=comment_data.content
    )
    db.add(new_comment)
    db.commit()
    return {"message": "Comment added successfully"}

@router.post("/posts/{post_id}/like")
def toggle_like(
    post_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(MentorPost).filter(MentorPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
        
    existing_like = db.query(PostLike).filter_by(post_id=post_id, user_id=current_user.user_id).first()
    if existing_like:
        db.delete(existing_like)
        db.commit()
        return {"message": "Unliked"}
    else:
        new_like = PostLike(post_id=post_id, user_id=current_user.user_id)
        db.add(new_like)
        db.commit()
        return {"message": "Liked"}
