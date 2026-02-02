"""
AI Router
=========
AI-powered endpoints for speech analysis, chat, and TTS.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.exceptions import ValidationException
from app.services.ai_service import ai_service
from app.services.tts_service import tts_service
from app.services.stt_service import stt_service
from app.models.content import AIFeedback, SpeakingSession, Scenario
from app.models.gamification import UserDailyStats
from app.models.user import User
from app.core import deps


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai",
    tags=["AI Core"],
    responses={404: {"description": "Not found"}},
)


# =============================================================================
# SCHEMAS
# =============================================================================

class ChatRequest(BaseModel):
    """Request schema for AI chat."""
    message: str = Field(..., min_length=1, max_length=1000)
    context: str = Field(
        default="You are a helpful English tutor.",
        max_length=500
    )


class SuggestionRequest(BaseModel):
    """Request schema for AI suggestion."""
    context: str = Field(..., max_length=1000)


class AnalyzeRequest(BaseModel):
    """Request schema for speech analysis."""
    text: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[int] = None
    duration_seconds: float = Field(default=0.0, ge=0)


class TTSRequest(BaseModel):
    """Request schema for text-to-speech."""
    text: str = Field(..., min_length=1, max_length=500)
    voice: str = Field(default="en-US-AriaNeural")


class STTRequest(BaseModel):
    """Request schema for speech-to-text."""
    audio_data: str = Field(..., description="Base64-encoded audio data")
    format: str = Field(default="wav", description="Audio format: wav, mp3, webm, ogg")
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    language: str = Field(default="en-US")
    session_id: Optional[int] = Field(default=None, description="Speaking session ID for feedback integration")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with Gemini AI using a specific context (Scenario).
    
    The AI will respond as a friendly English tutor or
    as the persona defined in the context.
    """
    response = await ai_service.chat_with_context(
        request.message, 
        request.context
    )
    return {"reply": response}


class ConversationMessage(BaseModel):
    """Single message in conversation history."""
    role: str = Field(..., description="'user' or 'ai'")
    content: str


class ConversationRequest(BaseModel):
    """Request schema for scenario-based conversation."""
    message: str = Field(..., min_length=1, max_length=2000)
    scenario_id: int
    context: list[ConversationMessage] = Field(default=[])


@router.post("/conversation")
async def conversation(
    request: ConversationRequest,
    db: Session = Depends(get_db),
):
    """
    Have a conversation within a specific scenario context.
    """
    try:
        # Load scenario for context
        scenario = db.query(Scenario).filter(Scenario.scenario_id == request.scenario_id).first()
        
        scenario_title = scenario.title if scenario else "English Practice"
        scenario_desc = scenario.topic.description if (scenario and scenario.topic) else "General English conversation practice"
        difficulty = scenario.difficulty_level if scenario else "Any"

        # Build conversation context from history
        history_text = ""
        if request.context:
            for msg in request.context[-6:]:  # Last 6 messages for context
                role = "User" if msg.role == "user" else "AI"
                history_text += f"{role}: {msg.content}\n"
        
        # Build system prompt
        system_context = f"""You are an English conversation practice partner. 
Roleplay Scenario: "{scenario_title}"
Description: {scenario_desc}
Learner Level: {difficulty}

Your role:
- Speak naturally and keep the conversation flowing.
- Be encouraging and helpful.
- Gently correct small grammar errors if they appear.
- Ask one short follow-up question.
- Match the learner's level ({difficulty}).

Recent history:
{history_text}
"""
        # Call AI service
        response = await ai_service.chat_with_context(
            request.message,
            system_context
        )
        
        return {
            "response": response, 
            "scenario_title": scenario_title,
            "success": True
        }

    except Exception as e:
        logger.error(f"Critical conversation error: {e}", exc_info=True)
        # Always return a valid response object to the frontend
        return {
            "response": "That's a great point! I'm listening. Could you tell me more about that? (Hệ thống đang bận, hãy thử lại sau giây lát)",
            "scenario_title": scenario_title if 'scenario_title' in locals() else "English Practice",
            "fallback": True,
            "success": False
        }


@router.post("/suggest-reply")
async def suggest_reply(request: SuggestionRequest):
    """
    Generate a suggested response for the learner to say.
    
    Based on the scenario description (context), the AI suggests 
    a natural sentence or phrase to start speaking.
    """
    response = await ai_service.generate_response_suggestion(request.context)
    return {"suggestion": response}


@router.post("/analyze")
async def analyze_speech(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Analyze user speech text for grammar and pronunciation.
    
    If session_id is provided:
    - Saves feedback to database
    - Updates daily learning statistics
    - Tracks challenge progress
    """
    # Get AI analysis
    analysis = await ai_service.analyze_speech(request.text)
    
    # Save to DB and update stats if session_id provided
    if request.session_id:
        try:
            _save_feedback_and_update_stats(
                db=db,
                session_id=request.session_id,
                text=request.text,
                duration_seconds=request.duration_seconds,
                analysis=analysis
            )
        except Exception as e:
            # Log but don't fail - user still gets their analysis
            logger.error(f"Error saving AI Feedback & Stats: {e}", exc_info=True)

    return analysis


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Generate audio from text using EdgeTTS.
    
    Returns a URL to the generated MP3 file.
    """
    audio_url = await tts_service.generate_audio(request.text, request.voice)
    
    if not audio_url:
        raise ValidationException(
            message="Failed to generate audio",
            details={"voice": request.voice}
        )
    
    return {"audio_url": audio_url}


@router.post("/stt")
async def speech_to_text(
    request: STTRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Transcribe audio to text using Speech-to-Text.
    
    Accepts base64-encoded audio and returns transcription with word timings.
    
    Supported formats: wav, mp3, webm, ogg, flac, m4a
    
    If session_id is provided, the transcription can be used for 
    pronunciation feedback integration.
    """
    try:
        result = await stt_service.transcribe(
            audio_data=request.audio_data,
            audio_format=request.format,
            sample_rate=request.sample_rate,
            language=request.language
        )
        
        response = result.to_dict()
        
        # If session_id provided, store for feedback integration
        if request.session_id:
            response["session_id"] = request.session_id
            logger.info(f"STT linked to session {request.session_id}")
        
        return response
        
    except ValueError as e:
        raise ValidationException(
            message=str(e),
            details={"format": request.format}
        )
    except Exception as e:
        logger.error(f"STT error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to process audio"
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _save_feedback_and_update_stats(
    db: Session,
    session_id: int,
    text: str,
    duration_seconds: float,
    analysis: dict
) -> None:
    """
    Save AI feedback and update user's daily statistics.
    
    Args:
        db: Database session
        session_id: Speaking session ID
        text: User's spoken text
        duration_seconds: Duration of speech
        analysis: AI analysis results
    """
    # 1. Save Feedback
    feedback = AIFeedback(
        session_id=session_id,
        user_input_text=text,
        grammar_score=analysis.get("grammar_score", 0),
        pronunciation_score=analysis.get("pronunciation_score", 0),
        fluency_score=analysis.get("fluency_score", 0),
        better_version=analysis.get("better_version", ""),
        feedback_details=analysis
    )
    db.add(feedback)
    
    # 2. Find user_id from session
    session_rec = db.query(SpeakingSession).filter(
        SpeakingSession.session_id == session_id
    ).first()
    
    if not session_rec:
        logger.warning(f"Session {session_id} not found")
        db.commit()
        return
    
    user_id = session_rec.user_id
    today = datetime.now(timezone.utc).date()
    
    # 3. Update or create daily stats
    daily_stat = db.query(UserDailyStats).filter(
        UserDailyStats.user_id == user_id,
        UserDailyStats.date == today
    ).first()
    
    if not daily_stat:
        daily_stat = UserDailyStats(user_id=user_id, date=today)
        db.add(daily_stat)
    
    # Update metrics
    word_count = len(text.split())
    daily_stat.words_learned += word_count
    daily_stat.speaking_duration_seconds += int(duration_seconds)
    
    # 4. Update challenge progress
    _update_challenge_progress(db, user_id, word_count, int(duration_seconds))
    
    db.commit()
    db.refresh(feedback)


def _update_challenge_progress(
    db: Session,
    user_id: int,
    word_count: int,
    duration_seconds: int
) -> None:
    """Update user's challenge progress based on activity."""
    try:
        from app.routers.gamification import update_user_challenge_progress
        
        # Update vocab count challenge
        update_user_challenge_progress(db, user_id, "VOCAB_COUNT", word_count)
        
        # Update speaking time challenge
        update_user_challenge_progress(db, user_id, "SPEAKING_TIME", duration_seconds)
        
    except ImportError:
        logger.debug("Gamification module not available")
    except Exception as e:
        logger.error(f"Error updating challenge progress: {e}")
