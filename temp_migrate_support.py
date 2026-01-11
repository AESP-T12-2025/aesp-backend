from app.core.database import SessionLocal, engine, Base
from app.models.support import SupportTicket
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_support_tickets():
    db = SessionLocal()
    try:
        # Check if table exists
        logger.info("Checking if support_tickets table exists...")
        result = db.execute(text("SELECT to_regclass('public.support_tickets');"))
        exists = result.scalar()
        
        if not exists:
            logger.info("Table support_tickets does not exist. Creating it...")
            SupportTicket.__table__.create(bind=engine)
            logger.info("Successfully created support_tickets table.")
        else:
            logger.info("Table support_tickets already exists.")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_support_tickets()
