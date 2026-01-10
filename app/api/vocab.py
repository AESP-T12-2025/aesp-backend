from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import List

router = APIRouter(prefix="/vocab", tags=["Saved Vocabulary"])


# --------- SCHEMA ----------
class SaveVocabRequest(BaseModel):
    user_id: int
    word: str
    meaning: str


class SavedVocabResponse(BaseModel):
    user_id: int
    word: str
    meaning: str
    saved_at: datetime


# --------- MOCK STORAGE ----------
SAVED_VOCABS: List[SavedVocabResponse] = []


# --------- APIs ----------
@router.post("/save")
def save_vocab(payload: SaveVocabRequest):
    vocab = SavedVocabResponse(
        user_id=payload.user_id,
        word=payload.word,
        meaning=payload.meaning,
        saved_at=datetime.utcnow()
    )
    SAVED_VOCABS.append(vocab)
    return {
        "message": "Saved vocabulary successfully",
        "data": vocab
    }


@router.get("/saved/{user_id}")
def get_saved_vocab(user_id: int):
    data = [v for v in SAVED_VOCABS if v.user_id == user_id]
    return {
        "user_id": user_id,
        "total": len(data),
        "data": data
    }