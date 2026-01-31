import os
import logging
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import pathlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Force load .env from current directory
env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Security constants
WEAK_SECRET_KEYS = ["changethis", "supersecretkey", "secret", "password", "123456"]

class Settings(BaseSettings):
    PROJECT_NAME: str = "AESP Backend"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changethis")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    
    # AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    class Config:
        env_file = ".env"
        extra = "ignore"

    def validate_security(self):
        """Validate security settings on startup"""
        if self.SECRET_KEY in WEAK_SECRET_KEYS:
            logger.warning(
                "⚠️  SECURITY WARNING: Using weak SECRET_KEY! "
                "Please set a strong SECRET_KEY in .env for production."
            )
        if not self.DATABASE_URL:
            logger.error("❌ DATABASE_URL not configured!")
        return self

settings = Settings()
settings.validate_security()
