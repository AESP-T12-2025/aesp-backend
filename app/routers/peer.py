from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.peer import PeerSession
from app.models.user import User

router = APIRouter(prefix="/peer", tags=["Peer Practice"])

@router.post("/join-queue")
def join_queue(
    topic_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if already in waiting session
    existing = db.query(PeerSession).filter(
        PeerSession.user1_id != current_user.user_id,
        PeerSession.status == "WAITING",
        PeerSession.topic_id == topic_id # Optional topic matching
    ).first()
    
    if existing:
        # Match found!
        existing.user2_id = current_user.user_id
        existing.status = "MATCHED"
        db.commit()
        return {"status": "MATCHED", "session_id": existing.id, "partner_id": existing.user1_id}
    else:
        # Create new waiting session
        new_session = PeerSession(
            user1_id=current_user.user_id,
            status="WAITING",
            topic_id=topic_id
        )
        db.add(new_session)
        db.commit()
        return {"status": "WAITING", "session_id": new_session.id}

@router.get("/status/{session_id}")
def check_status(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(PeerSession).filter(PeerSession.id == session_id).first()
    if not session: 
        raise HTTPException(404, "Session not found")
    return {"status": session.status, "user2": session.user2_id}
