from app.core.database import SessionLocal, engine
from app.models.user import User
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_user_bonus_xp():
    db = SessionLocal()
    try:
        # Check if column exists
        logger.info("Checking if bonus_xp column exists...")
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='bonus_xp';"))
        exists = result.fetchone()
        
        if not exists:
            logger.info("Column bonus_xp does not exist. Adding it...")
            db.execute(text("ALTER TABLE users ADD COLUMN bonus_xp INTEGER DEFAULT 0;"))
            db.commit()
            logger.info("Successfully added bonus_xp column.")
        else:
            logger.info("Column bonus_xp already exists.")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_user_bonus_xp()
