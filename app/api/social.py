from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/social",
    tags=["Social"]
)

class PostCreate(BaseModel):
    mentor_id: int
    content: str

class CommentCreate(BaseModel):
    content: str

@router.post("/posts")
def create_post(post: PostCreate):
    if not post.content:
        raise HTTPException(status_code=400, detail="Content is required")

    return {
        "message": "Post created successfully",
        "data": {
            "id": 1,
            "mentor_id": post.mentor_id,
            "content": post.content,
            "likes": 0
        }
    }

@router.get("/posts")
def list_posts():
    return {"data": []}

@router.post("/posts/{post_id}/comments")
def add_comment(post_id: int, comment: CommentCreate):
    return {
        "message": "Comment added",
        "post_id": post_id,
        "content": comment.content
    }

@router.post("/posts/{post_id}/like")
def like_post(post_id: int):
    return {
        "message": "Post liked",
        "post_id": post_id
    }
