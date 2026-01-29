from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.peer import PeerSession
from app.models.user import User
from app.models.proficiency import LearningPath
from typing import Optional

router = APIRouter(prefix="/peer", tags=["Peer Practice"])

@router.post("/find-partner")
@router.post("/join-queue")
def find_partner(
    topic_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Match learners by proficiency level and optionally topic.
    If a partner is found, returns status MATCHED and partner info.
    Otherwise, returns status WAITING and session_id.
    """
    # Fetch user's current level from LearningPath
    lp = db.query(LearningPath).filter(LearningPath.user_id == current_user.user_id).first()
    user_level = lp.current_level if lp else "A1" # Default to A1

    # Look for an existing waiting session with the same level (and topic if specified)
    query = db.query(PeerSession).filter(
        PeerSession.user1_id != current_user.user_id,
        PeerSession.status == "WAITING",
        PeerSession.level == user_level
    )
    
    if topic_id:
        query = query.filter(PeerSession.topic_id == topic_id)

    existing = query.first()

    if existing:
        # Match found! Update practice session
        existing.user2_id = current_user.user_id
        existing.status = "MATCHED"
        db.commit()
        db.refresh(existing)
        
        # Partner info (user1 is the one who was waiting)
        partner = db.query(User).filter(User.user_id == existing.user1_id).first()
        return {
            "session_id": existing.id,
            "status": "MATCHED",
            "partner": {
                "id": partner.user_id,
                "full_name": partner.full_name,
                "avatar_url": partner.avatar_url,
                "proficiency_level": user_level
            }
        }
    else:
        # Check if user already has an active waiting/matched session
        active_session = db.query(PeerSession).filter(
            (PeerSession.user1_id == current_user.user_id) | (PeerSession.user2_id == current_user.user_id),
            PeerSession.status.in_(["WAITING", "MATCHED"])
        ).first()
        
        if active_session:
            # If already matched, return the match info
            if active_session.status == "MATCHED":
                partner_id = active_session.user2_id if active_session.user1_id == current_user.user_id else active_session.user1_id
                partner = db.query(User).filter(User.user_id == partner_id).first()
                return {
                    "session_id": active_session.id,
                    "status": "MATCHED",
                    "partner": {
                        "id": partner.user_id,
                        "full_name": partner.full_name,
                        "avatar_url": partner.avatar_url,
                        "proficiency_level": user_level
                    }
                }
            return {"status": "WAITING", "session_id": active_session.id}

        # Create new practice session (waiting for partner)
        new_session = PeerSession(
            user1_id=current_user.user_id,
            status="WAITING",
            level=user_level,
            topic_id=topic_id
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return {"status": "WAITING", "session_id": new_session.id}

@router.get("/sessions/{id}")
@router.get("/status/{id}")
def get_session(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get session info and partner info.
    """
    session = db.query(PeerSession).filter(PeerSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if user is part of the session
    if session.user1_id != current_user.user_id and session.user2_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this session")
    
    partner_id = session.user2_id if session.user1_id == current_user.user_id else session.user1_id
    partner = None
    if partner_id:
        partner_obj = db.query(User).filter(User.user_id == partner_id).first()
        if partner_obj:
            partner = {
                "id": partner_obj.user_id,
                "full_name": partner_obj.full_name,
                "avatar_url": partner_obj.avatar_url,
                "role": partner_obj.role
            }
            
    return {
        "session_id": session.id,
        "status": session.status,
        "level": session.level,
        "topic_id": session.topic_id,
        "partner": partner,
        "is_audio_only": True
    }

@router.post("/sessions/{id}/end")
def end_session(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    End a practice session by setting status to COMPLETED.
    """
    session = db.query(PeerSession).filter(PeerSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if user is part of the session
    if session.user1_id != current_user.user_id and session.user2_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to end this session")
    
    if session.status == "COMPLETED":
        return {"message": "Session already ended"}

    session.status = "COMPLETED"
    db.commit()
    return {"message": "Session ended successfully"}

@router.post("/cancel-search")
def cancel_search(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a waiting session.
    """
    waiting = db.query(PeerSession).filter(
        PeerSession.user1_id == current_user.user_id,
        PeerSession.status == "WAITING"
    ).first()
    
    if waiting:
        db.delete(waiting)
        db.commit()
        return {"message": "Search cancelled successfully"}
    
    return {"message": "No active search found"}
