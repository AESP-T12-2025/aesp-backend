from fastapi import APIRouter, HTTPException
import logging
from pydantic import BaseModel
from app.services.ai_service import ai_service
from app.services.tts_service import tts_service
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core import database
from app.models.content import AIFeedback

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai",
    tags=["AI Core"],
    responses={404: {"description": "Not found"}},
)


from typing import Optional

class ChatRequest(BaseModel):
    message: str
    context: str = "You are a helpful English tutor."

class AnalyzeRequest(BaseModel):
    text: str
    session_id: Optional[int] = None
    duration_seconds: float = 0.0

class TTSRequest(BaseModel):
    text: str
    voice: str = "en-US-AriaNeural"

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with Gemini AI with a specific context (Scenario).
    """
    response = await ai_service.chat_with_context(request.message, request.context)
    return {"reply": response}

@router.post("/analyze")
async def analyze_speech(
    request: AnalyzeRequest,
    db: Session = Depends(database.get_db),
    # Optional implicit user from session if available, or force dependency if needed. 
    # For now, rely on session_id to find user OR simpler: current_user (but practice page needs auth)
    # Let's add current_user to be safe for gamification updates
    # Note: frontend must send token. practiceService does use api which sets token.
):
    from app.models.gamification import UserDailyStats
    from datetime import datetime
    
    """
    Analyze user speech text for grammar and pronunciation.
    """
    analysis = await ai_service.analyze_speech(request.text)
    
    # Save to DB if session_id provided and Update Stats
    if request.session_id:
        try:
            # 1. Save Feedback
            feedback = AIFeedback(
                session_id=request.session_id,
                user_input_text=request.text,
                grammar_score=analysis.get("grammar_score", 0),
                pronunciation_score=analysis.get("pronunciation_score", 0),
                fluency_score=analysis.get("fluency_score", 0),
                better_version=analysis.get("better_version", ""),
                feedback_details=analysis # Store full JSON
            )
            db.add(feedback)
            
            # 2. Update Daily Stats (Gamification)
            # Find user_id from session (or inject current_user)
            # Query session to get user_id
            from app.models.content import SpeakingSession
            session_rec = db.query(SpeakingSession).filter(SpeakingSession.session_id == request.session_id).first()
            
            if session_rec:
                user_id = session_rec.user_id
                today = datetime.now().date()
                
                daily_stat = db.query(UserDailyStats).filter(
                    UserDailyStats.user_id == user_id, 
                    UserDailyStats.date == today
                ).first()
                
                if not daily_stat:
                    daily_stat = UserDailyStats(user_id=user_id, date=today)
                    db.add(daily_stat)
                
                # Update metrics
                word_count = len(request.text.split())
                daily_stat.words_learned += word_count
                daily_stat.speaking_duration_seconds += int(request.duration_seconds)
                # Note: login_streak is handled in login
                
                # --- UPDATE CHALLENGES ---
                from app.routers.gamification import update_user_challenge_progress
                # 1. Update Vocab Count
                update_user_challenge_progress(db, user_id, "VOCAB_COUNT", word_count)
                # 2. Update Speaking Time
                update_user_challenge_progress(db, user_id, "SPEAKING_TIME", int(request.duration_seconds))
                
            db.commit()
            db.refresh(feedback)
        except Exception as e:
            logger.error(f"Error saving AI Feedback & Stats: {e}", exc_info=True)
            # Do not raise 500 here, just log it and return analysis so user still sees result
            # Or raise if critical. Let's return analysis but log error.


    return analysis

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Generate audio from text using EdgeTTS.
    """
    audio_url = await tts_service.generate_audio(request.text, request.voice)
    if not audio_url:
        raise HTTPException(status_code=500, detail="Failed to generate audio")
    
    return {"audio_url": audio_url}
