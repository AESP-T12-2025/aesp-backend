"""
Peer Practice Router
====================
WebSocket-based peer-to-peer practice matching and chat.
"""
import logging
import asyncio
from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.core import deps

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/peer",
    tags=["Peer Practice"],
)


# =============================================================================
# IN-MEMORY STATE (For demo - use Redis in production)
# =============================================================================

class PeerSession:
    """Represents a peer practice session between two users."""
    def __init__(self, user1_id: int, user2_id: int, topic: str = "General English"):
        self.session_id = f"{user1_id}_{user2_id}_{datetime.now().timestamp()}"
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.topic = topic
        self.created_at = datetime.now()
        self.messages: list = []


# Waiting queue: user_id -> WebSocket
waiting_queue: Dict[int, WebSocket] = {}

# Active sessions: session_id -> PeerSession
active_sessions: Dict[str, PeerSession] = {}

# User to session mapping: user_id -> session_id
user_sessions: Dict[int, str] = {}

# User WebSocket connections: user_id -> WebSocket
user_connections: Dict[int, WebSocket] = {}


# =============================================================================
# REST ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_peer_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get current peer practice status for user."""
    user_id = current_user.user_id
    
    # Check if in active session
    if user_id in user_sessions:
        session_id = user_sessions[user_id]
        session = active_sessions.get(session_id)
        if session:
            partner_id = session.user2_id if session.user1_id == user_id else session.user1_id
            partner = db.query(User).filter(User.user_id == partner_id).first()
            return {
                "status": "connected",
                "session_id": session_id,
                "partner": {
                    "user_id": partner_id,
                    "full_name": partner.full_name if partner else "Unknown"
                },
                "topic": session.topic
            }
    
    # Check if in queue
    if user_id in waiting_queue:
        return {
            "status": "searching",
            "queue_position": list(waiting_queue.keys()).index(user_id) + 1,
            "queue_size": len(waiting_queue)
        }
    
    return {
        "status": "idle",
        "queue_size": len(waiting_queue)
    }


@router.post("/leave")
async def leave_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Leave current peer session."""
    user_id = current_user.user_id
    
    # Remove from queue if waiting
    if user_id in waiting_queue:
        del waiting_queue[user_id]
        return {"message": "Left waiting queue"}
    
    # Leave active session
    if user_id in user_sessions:
        session_id = user_sessions[user_id]
        session = active_sessions.get(session_id)
        
        if session:
            # Notify partner
            partner_id = session.user2_id if session.user1_id == user_id else session.user1_id
            if partner_id in user_connections:
                try:
                    await user_connections[partner_id].send_json({
                        "type": "partner_left",
                        "message": "Đối tác đã rời phiên học"
                    })
                except:
                    pass
            
            # Cleanup
            if partner_id in user_sessions:
                del user_sessions[partner_id]
            del user_sessions[user_id]
            del active_sessions[session_id]
        
        return {"message": "Left session"}
    
    return {"message": "Not in any session"}


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@router.websocket("/ws/{token}")
async def peer_websocket(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for peer practice.
    
    Flow:
    1. Connect with auth token
    2. Join waiting queue
    3. Get matched with another user
    4. Exchange messages in real-time
    """
    await websocket.accept()
    
    # Authenticate user from token
    try:
        from app.core.security import decode_access_token
        payload = decode_access_token(token)
        email = payload.get("sub")  # Token contains email, not user_id
        user = db.query(User).filter(User.email == email).first()
        if not user:
            await websocket.send_json({"type": "error", "message": "User not found"})
            await websocket.close()
            return
        user_id = user.user_id
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        await websocket.send_json({"type": "error", "message": "Invalid token"})
        await websocket.close()
        return
    
    logger.info(f"Peer WS connected: user {user_id}")
    user_connections[user_id] = websocket
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "message": "Đã kết nối. Đang tìm bạn học..."
        })
        
        # Add to waiting queue
        waiting_queue[user_id] = websocket
        
        # Try to match with someone
        matched = await try_match_users(user_id, db)
        
        if not matched:
            await websocket.send_json({
                "type": "searching",
                "queue_position": list(waiting_queue.keys()).index(user_id) + 1 if user_id in waiting_queue else 0,
                "message": "Đang chờ người học khác..."
            })
        
        # Listen for messages
        while True:
            data = await websocket.receive_json()
            await handle_message(user_id, data, db)
            
    except WebSocketDisconnect:
        logger.info(f"Peer WS disconnected: user {user_id}")
    except Exception as e:
        logger.error(f"Peer WS error: {e}")
    finally:
        await cleanup_user(user_id)


async def try_match_users(user_id: int, db: Session) -> bool:
    """Try to match user with someone in queue."""
    if len(waiting_queue) < 2:
        return False
    
    # Find another user in queue (not self)
    for other_id, other_ws in list(waiting_queue.items()):
        if other_id != user_id:
            # Match found!
            user_ws = waiting_queue.get(user_id)
            if not user_ws:
                return False
            
            # Remove both from queue
            del waiting_queue[user_id]
            del waiting_queue[other_id]
            
            # Create session
            session = PeerSession(user_id, other_id)
            active_sessions[session.session_id] = session
            user_sessions[user_id] = session.session_id
            user_sessions[other_id] = session.session_id
            
            # Get user info
            user1 = db.query(User).filter(User.user_id == user_id).first()
            user2 = db.query(User).filter(User.user_id == other_id).first()
            
            # Notify both users
            match_msg_1 = {
                "type": "matched",
                "session_id": session.session_id,
                "partner": {
                    "user_id": other_id,
                    "full_name": user2.full_name if user2 else "Unknown"
                },
                "topic": session.topic,
                "message": f"Đã ghép đôi với {user2.full_name if user2 else 'Unknown'}!"
            }
            
            match_msg_2 = {
                "type": "matched",
                "session_id": session.session_id,
                "partner": {
                    "user_id": user_id,
                    "full_name": user1.full_name if user1 else "Unknown"
                },
                "topic": session.topic,
                "message": f"Đã ghép đôi với {user1.full_name if user1 else 'Unknown'}!"
            }
            
            try:
                await user_ws.send_json(match_msg_1)
                await other_ws.send_json(match_msg_2)
            except:
                pass
            
            logger.info(f"Matched users {user_id} and {other_id}")
            return True
    
    return False


async def handle_message(user_id: int, data: dict, db: Session):
    """Handle incoming message from user."""
    msg_type = data.get("type", "chat")
    
    if msg_type == "chat":
        # Forward chat message to partner
        if user_id not in user_sessions:
            return
        
        session_id = user_sessions[user_id]
        session = active_sessions.get(session_id)
        if not session:
            return
        
        partner_id = session.user2_id if session.user1_id == user_id else session.user1_id
        partner_ws = user_connections.get(partner_id)
        
        message = {
            "type": "chat",
            "from_user_id": user_id,
            "content": data.get("content", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        # Store message
        session.messages.append(message)
        
        # Forward to partner
        if partner_ws:
            try:
                await partner_ws.send_json(message)
            except:
                pass
    
    elif msg_type == "typing":
        # Forward typing indicator
        if user_id in user_sessions:
            session_id = user_sessions[user_id]
            session = active_sessions.get(session_id)
            if session:
                partner_id = session.user2_id if session.user1_id == user_id else session.user1_id
                partner_ws = user_connections.get(partner_id)
                if partner_ws:
                    try:
                        await partner_ws.send_json({"type": "typing", "user_id": user_id})
                    except:
                        pass
    
    # =========================================================================
    # WEBRTC SIGNALING FOR VOICE CHAT
    # =========================================================================
    
    elif msg_type == "voice_request":
        # User requests to start voice chat
        if user_id in user_sessions:
            session_id = user_sessions[user_id]
            session = active_sessions.get(session_id)
            if session:
                partner_id = session.user2_id if session.user1_id == user_id else session.user1_id
                partner_ws = user_connections.get(partner_id)
                if partner_ws:
                    try:
                        await partner_ws.send_json({
                            "type": "voice_request",
                            "from_user_id": user_id,
                            "message": "Đối tác muốn bắt đầu voice chat"
                        })
                    except:
                        pass
    
    elif msg_type == "voice_accept":
        # Partner accepts voice chat
        if user_id in user_sessions:
            session_id = user_sessions[user_id]
            session = active_sessions.get(session_id)
            if session:
                partner_id = session.user2_id if session.user1_id == user_id else session.user1_id
                partner_ws = user_connections.get(partner_id)
                if partner_ws:
                    try:
                        await partner_ws.send_json({
                            "type": "voice_accept",
                            "from_user_id": user_id
                        })
                    except:
                        pass
    
    elif msg_type == "voice_reject":
        # Partner rejects voice chat
        if user_id in user_sessions:
            session_id = user_sessions[user_id]
            session = active_sessions.get(session_id)
            if session:
                partner_id = session.user2_id if session.user1_id == user_id else session.user1_id
                partner_ws = user_connections.get(partner_id)
                if partner_ws:
                    try:
                        await partner_ws.send_json({
                            "type": "voice_reject",
                            "from_user_id": user_id
                        })
                    except:
                        pass
    
    elif msg_type == "voice_end":
        # End voice chat
        if user_id in user_sessions:
            session_id = user_sessions[user_id]
            session = active_sessions.get(session_id)
            if session:
                partner_id = session.user2_id if session.user1_id == user_id else session.user1_id
                partner_ws = user_connections.get(partner_id)
                if partner_ws:
                    try:
                        await partner_ws.send_json({
                            "type": "voice_end",
                            "from_user_id": user_id
                        })
                    except:
                        pass
    
    elif msg_type in ["offer", "answer", "ice-candidate"]:
        # WebRTC signaling - forward to partner
        if user_id in user_sessions:
            session_id = user_sessions[user_id]
            session = active_sessions.get(session_id)
            if session:
                partner_id = session.user2_id if session.user1_id == user_id else session.user1_id
                partner_ws = user_connections.get(partner_id)
                if partner_ws:
                    try:
                        # Forward the entire message including SDP/candidate data
                        forward_msg = {
                            "type": msg_type,
                            "from_user_id": user_id,
                            "data": data.get("data")
                        }
                        await partner_ws.send_json(forward_msg)
                        logger.info(f"Forwarded {msg_type} from {user_id} to {partner_id}")
                    except Exception as e:
                        logger.error(f"Error forwarding {msg_type}: {e}")


async def cleanup_user(user_id: int):
    """Clean up user from all data structures."""
    # Remove from queue
    if user_id in waiting_queue:
        del waiting_queue[user_id]
    
    # Remove from connections
    if user_id in user_connections:
        del user_connections[user_id]
    
    # Handle active session
    if user_id in user_sessions:
        session_id = user_sessions[user_id]
        session = active_sessions.get(session_id)
        
        if session:
            partner_id = session.user2_id if session.user1_id == user_id else session.user1_id
            
            # Notify partner
            if partner_id in user_connections:
                try:
                    await user_connections[partner_id].send_json({
                        "type": "partner_left",
                        "message": "Đối tác đã ngắt kết nối"
                    })
                except:
                    pass
            
            # Remove session
            if partner_id in user_sessions:
                del user_sessions[partner_id]
            del active_sessions[session_id]
        
        del user_sessions[user_id]
