from app.core.database import SessionLocal, engine
from app.models.payment import ServicePackage
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_packages():
    db = SessionLocal()
    try:
        # Check if column exists
        logger.info("Checking if mentor_included column exists...")
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='service_packages' AND column_name='mentor_included';"))
        exists = result.fetchone()
        
        if not exists:
            logger.info("Column mentor_included does not exist. Adding it...")
            db.execute(text("ALTER TABLE service_packages ADD COLUMN mentor_included BOOLEAN DEFAULT FALSE;"))
            db.commit()
            logger.info("Successfully added mentor_included column.")
        else:
            logger.info("Column mentor_included already exists.")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_packages()
