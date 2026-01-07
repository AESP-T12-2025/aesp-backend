from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_service import ai_service
from app.services.tts_service import tts_service
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core import database
from app.models.content import AIFeedback

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
    db: Session = Depends(database.get_db)
):
    """
    Analyze user speech text for grammar and pronunciation.
    """
    analysis = await ai_service.analyze_speech(request.text)
    
    # Save to DB if session_id provided
    if request.session_id:
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
        db.commit()
        db.refresh(feedback)

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
