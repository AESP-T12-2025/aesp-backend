from app.core.database import SessionLocal, engine
from app.models.user import User
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_user_goals():
    db = SessionLocal()
    try:
        # Check if column exists
        logger.info("Checking if daily_learning_goal column exists...")
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='daily_learning_goal';"))
        exists = result.fetchone()
        
        if not exists:
            logger.info("Column daily_learning_goal does not exist. Adding it...")
            db.execute(text("ALTER TABLE users ADD COLUMN daily_learning_goal INTEGER DEFAULT 15;"))
            db.commit()
            logger.info("Successfully added daily_learning_goal column.")
        else:
            logger.info("Column daily_learning_goal already exists.")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_user_goals()
