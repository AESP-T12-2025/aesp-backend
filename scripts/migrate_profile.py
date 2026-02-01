import logging
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    logger.error("DATABASE_URL not found!")
    exit(1)

engine = create_engine(DATABASE_URL)

def run_migration():
    with engine.connect() as conn:
        logger.info("Connecting to database...")
        
        # Add columns to users table
        try:
            logger.info("Adding 'learning_target' to users...")
            conn.execute(text("ALTER TABLE users ADD COLUMN learning_target VARCHAR DEFAULT 'General English';"))
            conn.commit()
            logger.info("Added 'learning_target'")
        except Exception as e:
            logger.warning(f"Could not add 'learning_target' (maybe already exists?): {e}")
            conn.rollback()

        try:
            logger.info("Adding 'preferred_practice_time' to users...")
            conn.execute(text("ALTER TABLE users ADD COLUMN preferred_practice_time VARCHAR DEFAULT 'Anytime';"))
            conn.commit()
            logger.info("Added 'preferred_practice_time'")
        except Exception as e:
            logger.warning(f"Could not add 'preferred_practice_time' (maybe already exists?): {e}")
            conn.rollback()

        logger.info("Migration finished!")

if __name__ == "__main__":
    run_migration()
