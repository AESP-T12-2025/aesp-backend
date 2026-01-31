from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
import uuid
import json
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.peer import PeerSession
from app.models.user import User
from app.models.proficiency import LearningPath
from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class ConnectionManager:
    def __init__(self):
        # session_id -> list of websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: int):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: int):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast_to_session(self, message: str, session_id: int, exclude: WebSocket = None):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                if connection != exclude:
                    await connection.send_text(message)

manager = ConnectionManager()


class JoinQueueRequest(BaseModel):
    topic_id: Optional[str] = Field(None, alias="topicId")
    topic_preference: Optional[str] = None
    session_type: str = "voice"

    class Config:
        populate_by_name = True

router = APIRouter(prefix="/peer", tags=["Peer Practice"])

@router.post("/join-queue")
def join_queue(
    request: JoinQueueRequest = None,
    topic_id: Optional[str] = None, # Support query param too
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Join the queue to match with a partner.
    """
    # Extraction logic for topic_id from various sources
    final_topic_id = topic_id
    session_type = "voice"
    
    if request:
        final_topic_id = request.topic_id or request.topic_preference or final_topic_id
        session_type = request.session_type

    # Fetch user's current level from LearningPath
    lp = db.query(LearningPath).filter(LearningPath.user_id == current_user.user_id).first()
    user_level = lp.current_level if lp else "A1" 

    level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
    
    try:
        user_level_index = level_order.index(user_level)
    except ValueError:
        user_level_index = 0 # Default to A1 if level is unknown

    # Step 1: Look for exact match
    existing = db.query(PeerSession).filter(
        PeerSession.user1_id != current_user.user_id,
        PeerSession.status == "WAITING",
        PeerSession.level == user_level,
        PeerSession.session_type == session_type
    ).first()

    # Step 2: Relaxed matching (adjacent levels)
    if not existing:
        adjacent_levels = []
        if user_level_index > 0:
            adjacent_levels.append(level_order[user_level_index - 1])
        if user_level_index < len(level_order) - 1:
            adjacent_levels.append(level_order[user_level_index + 1])
        
        if adjacent_levels:
            existing = db.query(PeerSession).filter(
                PeerSession.user1_id != current_user.user_id,
                PeerSession.status == "WAITING",
                PeerSession.level.in_(adjacent_levels),
                PeerSession.session_type == session_type
            ).first()

    if existing:
        # Match found!
        existing.user2_id = current_user.user_id
        existing.status = "MATCHED"
        existing.call_id = str(uuid.uuid4()) # Generate a call ID for signaling
        db.commit()
        db.refresh(existing)
        
        partner = db.query(User).filter(User.user_id == existing.user1_id).first()
        return {
            "session_id": existing.id,
            "status": "MATCHED",
            "call_id": existing.call_id,
            "session_type": existing.session_type,
            "partner": {
                "id": partner.user_id,
                "full_name": partner.full_name,
                "avatar_url": partner.avatar_url
            }
        }
    else:
        # Check for existing waiting session for this user
        waiting = db.query(PeerSession).filter(
            PeerSession.user1_id == current_user.user_id,
            PeerSession.status == "WAITING"
        ).first()
        
        if waiting:
            # Update session_type if user requested a different one
            waiting.session_type = session_type
            db.commit()
            return {"status": "WAITING", "session_id": waiting.id}

        # Create new practice session
        new_session = PeerSession(
            user1_id=current_user.user_id,
            status="WAITING",
            level=user_level,
            session_type=session_type,
            topic_id=final_topic_id
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return {"status": "WAITING", "session_id": new_session.id}

@router.get("/status/{id}")
def get_session_status(
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
        "session_type": session.session_type,
        "call_id": session.call_id,
        "user_id": current_user.user_id,
        "user1_id": session.user1_id,
        "user2_id": session.user2_id,
        "partner": partner
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
    
    session.status = "COMPLETED"
    db.commit()
    return {"message": "Session ended successfully"}

@router.post("/cancel-search")
def cancel_search(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel current search and remove user from waiting queue.
    """
    waiting = db.query(PeerSession).filter(
        PeerSession.user1_id == current_user.user_id,
        PeerSession.status == "WAITING"
    ).all()
    
    for session in waiting:
        db.delete(session)
    
    db.commit()
    return {"message": "Search cancelled successfully"}

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int):
    await manager.connect(websocket, session_id)
    print(f"DEBUG: WebSocket connected to session {session_id}")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"DEBUG: Received signaling message for session {session_id}: {data[:50]}...")
            # Relay the message to the other peer in the same session
            await manager.broadcast_to_session(data, session_id, exclude=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        print(f"DEBUG: WebSocket disconnected from session {session_id}")



