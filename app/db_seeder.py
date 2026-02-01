from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
import logging
import random

# --- IMPORT MODELS CHUẨN ---
# 1. Content Models (Categories, Topics, Scenarios)
from app.models.content import Category, Topic, Scenario, DifficultyLevel

# 2. User Model
from app.models.user import User, UserRole

# 3. Gamification Models (Challenge & ChallengeType)
from app.models.gamification import Challenge, ChallengeType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    logger.info("Initializing Seeder with NullPool configuration...")
    
    # Get Database URL
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    # Better SQLite detection
    is_sqlite = db_url.startswith("sqlite:///") or db_url.startswith("sqlite://")
    connect_args = {'check_same_thread': False} if is_sqlite else {}
    
    engine = create_engine(
        db_url,
        poolclass=NullPool,
        connect_args=connect_args
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # ==========================================
        # PHẦN 1: SEED CONTENT (Categories, Topics)
        # ==========================================
        if db.query(Category).first():
            logger.info("✅ Categories already exist. Skipping content seeding.")
        else:
            logger.info("🌱 Seeding Categories & Topics...")
            # 1. Categories
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
            logger.info("✅ Content seeding completed.")

        # ==========================================
        # PHẦN 2: SEED GAMIFICATION (Challenges)
        # ==========================================
        if db.query(Challenge).first():
            logger.info("✅ Challenges already exist. Skipping challenge seeding.")
        else:
            logger.info("🌱 Seeding Challenges...")
            
            # CẬP NHẬT CẤU TRÚC CHO KHỚP VỚI MODEL MỚI
            challenges = [
                Challenge(
                    title="Luyện nói 15 phút", 
                    description="Duy trì luyện tập nói mỗi ngày để cải thiện phát âm",
                    target_value=15,             # Đổi tên cột cho đúng model
                    points_reward=50,            # Đổi tên cột cho đúng model
                    challenge_type=ChallengeType.SPEAKING_TIME # Thêm loại challenge
                ),
                Challenge(
                    title="Học 5 từ vựng mới", 
                    description="Mở rộng vốn từ vựng của bạn",
                    target_value=5, 
                    points_reward=30, 
                    challenge_type=ChallengeType.VOCAB_COUNT
                ),
                Challenge(
                    title="Duy trì Streak 3 ngày", 
                    description="Học liên tục không ngắt quãng",
                    target_value=3, 
                    points_reward=150, 
                    challenge_type=ChallengeType.STREAK
                ),
            ]
            db.add_all(challenges)
            db.commit()
            logger.info("✅ Challenges seeding completed.")

        # ==========================================
        # PHẦN 3: SEED FAKE USERS (Leaderboard Bots)
        # ==========================================
        if db.query(User).filter(User.email.contains("bot")).count() > 0:
            logger.info("✅ Bot users already exist. Skipping bot seeding.")
        else:
            logger.info("🌱 Seeding Bot Users for Leaderboard...")
            bots = []
            names = ["Sarah Nguyen", "David Tran", "Emily Le", "Michael Pham", "Anna Vo", "Kevin Do"]
            
            for i, name in enumerate(names):
                bot = User(
                    email=f"bot{i}@example.com",
                    password_hash="fake_hash_password", 
                    full_name=name,
                    role=UserRole.LEARNER,
                    bonus_xp=random.randint(500, 3000), 
                    avatar_url=f"https://i.pravatar.cc/150?u={i+10}"
                )
                bots.append(bot)
            
            db.add_all(bots)
            db.commit()
            logger.info(f"✅ Created {len(bots)} bot users.")

        logger.info("🎉 ALL SEEDING OPERATIONS COMPLETED SUCCESSFULLY!")

    except Exception as e:
        logger.error(f"❌ Error seeding data: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()
        engine.dispose()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    seed_data()