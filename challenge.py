from fastapi import FastAPI
from .routers import challenge # Import router bạn vừa viết

app = FastAPI()

# Đăng ký router
app.include_router(challenge.router)

@app.get("/")
def root():
    return {"message": "AESP Backend is running"}
