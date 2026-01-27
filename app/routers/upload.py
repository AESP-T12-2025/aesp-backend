import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, UploadFile, File, HTTPException
import os

router = APIRouter()

# Cấu hình lấy từ file .env
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Upload lên Cloudinary vào thư mục aesp_uploads
        result = cloudinary.uploader.upload(file.file, folder="aesp_uploads")
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")