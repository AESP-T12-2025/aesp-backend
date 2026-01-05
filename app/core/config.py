import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv, find_dotenv
import pathlib

# Force load .env from current directory
env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
print(f"DEBUG: Loading .env from {env_path}")
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    PROJECT_NAME: str = "AESP Backend"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    print(f"DEBUG: DATABASE_URL loaded: {DATABASE_URL}")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changethis")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()