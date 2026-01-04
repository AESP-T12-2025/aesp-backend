from dotenv import load_dotenv
# QUAN TRỌNG: Phải load biến môi trường NGAY ĐẦU TIÊN
# Trước khi import các file khác (như upload) để nó kịp nhận Key
load_dotenv()

from fastapi import FastAPI
from routers import upload
import uvicorn

# Khởi tạo ứng dụng
app = FastAPI()

# Kết nối router
app.include_router(upload.router)

@app.get("/")
def read_root():
    return {"message": "Backend AESP chạy ngon lành!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)