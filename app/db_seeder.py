from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.content import Category, Topic, Scenario, DifficultyLevel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    db = SessionLocal()
    try:
        # Check if we have categories
        if db.query(Category).first():
            logger.info("Data already exists. Skipping seeding.")
            return

        logger.info("Seeding data...")

        # 1. Categories
        cat_business = Category(name="Business English", description="For workplace and professional settings")
        cat_travel = Category(name="Travel & Tourism", description="Essential phrases for travelers")
        cat_daily = Category(name="Daily Conversation", description="Casual chats and everyday scenarios")
        cat_tech = Category(name="Technology", description="IT, AI, and modern tech terms")
        cat_culture = Category(name="Culture & Arts", description="Discussing movies, books, and traditions")
        
        db.add_all([cat_business, cat_travel, cat_daily, cat_tech, cat_culture])
        db.commit()

        # Refresh to get IDs
        db.refresh(cat_business)
        db.refresh(cat_travel)
        db.refresh(cat_daily)
        db.refresh(cat_tech)
        db.refresh(cat_culture)

        # 2. Topics
        topics = [
            Topic(category_id=cat_business.category_id, name="Job Interview", description="Common interview questions"),
            Topic(category_id=cat_business.category_id, name="Meeting Etiquette", description="How to speak in meetings"),
            Topic(category_id=cat_travel.category_id, name="At the Airport", description="Check-in and customs"),
            Topic(category_id=cat_travel.category_id, name="Booking Hotel", description="Reservations and inquiries"),
            Topic(category_id=cat_daily.category_id, name="Ordering Coffee", description="Cafes and restaurants"),
            Topic(category_id=cat_daily.category_id, name="Making Friends", description="Introductions and small talk"),
            Topic(category_id=cat_tech.category_id, name="AI Trends", description="Discussion about AI"),
            Topic(category_id=cat_tech.category_id, name="Programming Basics", description="Coding terminology"),
            Topic(category_id=cat_culture.category_id, name="Movies", description="Talking about recent films"),
            Topic(category_id=cat_culture.category_id, name="Holidays", description="Describing festival experiences"),
        ]
        
        db.add_all(topics)
        db.commit()
        
        # 3. Scenarios (One sample per topic)
        # Fetch topics back to get IDs
        all_topics = db.query(Topic).all()
        scenarios = []
        for topic in all_topics:
            scenarios.append(Scenario(
                topic_id=topic.topic_id, 
                title=f"Scenario for {topic.name}", 
                difficulty_level=DifficultyLevel.BEGINNER,
                script_content="A: Hello!\nB: Hi there!",
                key_phrases={"phrase1": "Hello", "phrase2": "Hi"}
            ))

        db.add_all(scenarios)
        db.commit()

        logger.info("Seeding completed successfully!")

    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Ensure tables exist
    # Base.metadata.create_all(bind=engine) # App main already does this, but good for standalone
    seed_data()
