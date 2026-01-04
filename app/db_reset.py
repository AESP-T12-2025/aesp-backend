from app.core.database import engine, Base
from sqlalchemy import text
from app.models import user, content
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_db_force():
    logger.info("Dropping schema public CASCADE...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        conn.commit()
    
    logger.info("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database reset complete.")

if __name__ == "__main__":
    reset_db_force()
