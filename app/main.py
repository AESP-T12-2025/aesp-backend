from dotenv import load_dotenv
# QUAN TRỌNG: Phải load biến môi trường NGAY ĐẦU TIÊN
# Trước khi import các file khác (như upload) để nó kịp nhận Key
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles # Added import for StaticFiles
from app.routers import upload, auth, content, users, payment, ai, mentor
from app.core.database import engine, Base
from app.models import user, content as content_model, mentor as mentor_model # Import models to register them with Base
import uvicorn
import os

# Tạo bảng trong DB (tạm thời dùng cách này thay vì alembic cho nhanh giai đoạn đầu)
Base.metadata.create_all(bind=engine)

# Khởi tạo ứng dụng
app = FastAPI(title="AESP Backend API")
from app.api.social import router as social_router
app.include_router(social_router)

# Mount static directory for audio files
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Cấu hình CORS
from fastapi.middleware.cors import CORSMiddleware
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kết nối router
app.include_router(upload.router, tags=["Upload"])
app.include_router(auth.router, tags=["Auth"])
app.include_router(content.router, tags=["Content"])
app.include_router(users.router, tags=["Users"])
app.include_router(payment.router, tags=["Payment"])
app.include_router(ai.router, tags=["AI Core"]) # Added AI router
app.include_router(mentor.router, tags=["Mentor & Booking"]) # Added Mentor router

@app.get("/")
def read_root():
    return {"message": "Backend AESP chạy ngon lành!"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)