from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Notification).filter(Notification.user_id == current_user.user_id).order_by(Notification.created_at.desc()).all()

@router.put("/{noti_id}/read")
def mark_read(
    noti_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    noti = db.query(Notification).filter(Notification.id == noti_id, Notification.user_id == current_user.user_id).first()
    if noti:
        noti.is_read = True
        db.commit()
    return {"status": "ok"}
