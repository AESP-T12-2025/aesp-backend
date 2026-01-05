from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_service import ai_service
from app.services.tts_service import tts_service

router = APIRouter(
    prefix="/ai",
    tags=["AI Core"],
    responses={404: {"description": "Not found"}},
)

class ChatRequest(BaseModel):
    message: str
    context: str = "You are a helpful English tutor."

class AnalyzeRequest(BaseModel):
    text: str

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
async def analyze_speech(request: AnalyzeRequest):
    """
    Analyze user speech text for grammar and pronunciation.
    """
    analysis = await ai_service.analyze_speech(request.text)
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
