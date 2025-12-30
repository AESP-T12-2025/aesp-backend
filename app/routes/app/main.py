from fastapi import FastAPI
from app.routes import general

app = FastAPI(
    title="AESP - AI English Speaking Practice Platform",
    description="API documentation for AESP project",
    version="1.0.0"
)

# Kết nối các route từ file general.py vào hệ thống
app.include_router(general.router, tags=["General Endpoints"])

@app.get("/")
async def root():
    return {"message": "Welcome to AESP Backend API. Go to /docs for Swagger UI."}
