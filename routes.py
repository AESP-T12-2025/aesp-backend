from fastapi import FastAPI, HTTPException
from typing import List
from app.schemas.speaking import SpeakingSession, VocabItem

app = FastAPI(title="AESP - AI English Speaking Practice Platform")

# Mock database
sessions_db = []

# API POST /speaking-sessions: Lưu session vào DB
@app.post("/speaking-sessions", status_code=201)
async def create_speaking_session(session: SpeakingSession):
    sessions_db.append(session.dict())
    return {"message": "Session saved successfully", "data": session}

# API GET /scenarios/{id}/vocab: Trả về từ vựng gợi ý
@app.get("/scenarios/{scenario_id}/vocab", response_model=List[VocabItem])
async def get_scenario_vocab(scenario_id: str):
    # Dữ liệu mẫu dựa trên ID kịch bản
    mock_vocab = [
        {"word": "Fluency", "definition": "Speaking easily and smoothly."},
        {"word": "Pronunciation", "definition": "The way in which a word is pronounced."}
    ]
    
    if not scenario_id:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    return mock_vocab
