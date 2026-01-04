from dotenv import load_dotenv
# QUAN TRỌNG: Phải load biến môi trường NGAY ĐẦU TIÊN
# Trước khi import các file khác (như upload) để nó kịp nhận Key
load_dotenv()

from fastapi import FastAPI
from app.routers import upload, auth, content, users, payment
from app.core.database import engine, Base
from app.models import user, content as content_model # Import models to register them with Base
import uvicorn

# Tạo bảng trong DB (tạm thời dùng cách này thay vì alembic cho nhanh giai đoạn đầu)
Base.metadata.create_all(bind=engine)

# Khởi tạo ứng dụng
app = FastAPI()

# Kết nối router
app.include_router(upload.router)
app.include_router(auth.router)
app.include_router(content.router)
app.include_router(users.router)
app.include_router(payment.router)

@app.get("/")
def read_root():
    return {"message": "Backend AESP chạy ngon lành!"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)