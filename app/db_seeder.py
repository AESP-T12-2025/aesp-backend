from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.models.content import Category, Topic, Scenario, DifficultyLevel
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    logger.info("Initializing Seeder with NullPool configuration...")
    
    # Get Database URL
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    # Create engine with NullPool to avoid keeping connections open excessively
    # preventing "server closed the connection unexpectedly" errors
    engine = create_engine(
        db_url,
        poolclass=NullPool,
        connect_args={'sslmode': 'require'}
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        logger.info("Checking existing data...")
        if db.query(Category).first():
             logger.info("Categories already exist. Skipping basic seeding.")
             return

        # 1. Categories
        logger.info("Seeding Categories...")
        categories = [
            Category(name="Business English", description="For workplace and professional settings"),
            Category(name="Travel & Tourism", description="Essential phrases for travelers"),
            Category(name="Daily Conversation", description="Casual chats and everyday scenarios"),
            Category(name="Technology", description="IT, AI, and modern tech terms"),
            Category(name="Culture & Arts", description="Discussing movies, books, and traditions"),
        ]
        db.add_all(categories)
        db.commit()
        
        # Refresh to get IDs
        for cat in categories:
            db.refresh(cat)

        # 2. Topics
        logger.info("Seeding Topics...")
        cat_map = {c.name: c.category_id for c in categories}
        
        topics = [
            Topic(category_id=cat_map["Business English"], name="Job Interview", description="Common interview questions"),
            Topic(category_id=cat_map["Business English"], name="Meeting Etiquette", description="How to speak in meetings"),
            Topic(category_id=cat_map["Travel & Tourism"], name="At the Airport", description="Check-in and customs"),
            Topic(category_id=cat_map["Travel & Tourism"], name="Booking Hotel", description="Reservations and inquiries"),
            Topic(category_id=cat_map["Daily Conversation"], name="Ordering Coffee", description="Cafes and restaurants"),
            Topic(category_id=cat_map["Daily Conversation"], name="Making Friends", description="Introductions and small talk"),
        ]
        db.add_all(topics)
        db.commit()

        # Refresh topics
        for t in topics:
            db.refresh(t)

        # 3. Scenarios
        logger.info("Seeding Scenarios...")
        scenarios = []
        for topic in topics:
            scenarios.append(Scenario(
                topic_id=topic.topic_id, 
                title=f"Scenario for {topic.name}", 
                difficulty_level=DifficultyLevel.BEGINNER,
                script_content="A: Hello!\nB: Hi there! How can I help you?",
                key_phrases={"hello": "Xin chao", "help": "Giup do"}
            ))
        
        db.add_all(scenarios)
        db.commit()

        logger.info("Seeding COMPLETED successfully!")

    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()
        # Explicitly dispose the engine
        engine.dispose()

if __name__ == "__main__":
    seed_data()
