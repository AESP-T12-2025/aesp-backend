
import sys
import os
import json

# Add parent dir to path to find app package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.content import Category, Topic, Scenario, DifficultyLevel

def seed_data():
    db = SessionLocal()
    try:
        print("🌱 Seeding Quality Data...")

        # --- 1. Categories ---
        categories_data = [
            {"name": "Giao tiếp hàng ngày", "description": "Conversations for daily life situations."},
            {"name": "Tiếng Anh công sở", "description": "Professional communication for work."},
            {"name": "Du lịch", "description": "Essential English for traveling abroad."},
            {"name": "Luyện thi IELTS", "description": "Speaking practice for IELTS exam."},
        ]

        categories = {}
        for cat_data in categories_data:
            cat = db.query(Category).filter(Category.name == cat_data["name"]).first()
            if not cat:
                cat = Category(name=cat_data["name"], description=cat_data["description"])
                db.add(cat)
                db.commit()
                db.refresh(cat)
                print(f"   + Created Category: {cat.name}")
            categories[cat.name] = cat

        # --- 2. Topics ---
        topics_data = [
            # Daily
            {"cat": "Giao tiếp hàng ngày", "name": "Giới thiệu bản thân", "image": "/images/topics/intro.jpg"},
            {"cat": "Giao tiếp hàng ngày", "name": "Gọi món tại nhà hàng", "image": "/images/topics/restaurant.jpg"},
            # Business
            {"cat": "Tiếng Anh công sở", "name": "Phỏng vấn xin việc", "image": "/images/topics/interview.jpg"},
            {"cat": "Tiếng Anh công sở", "name": "Thuyết trình dự án", "image": "/images/topics/presentation.jpg"},
            # Travel
            {"cat": "Du lịch", "name": "Làm thủ tục sân bay", "image": "/images/topics/airport.jpg"},
            {"cat": "Du lịch", "name": "Hỏi đường", "image": "/images/topics/directions.jpg"},
             # IELTS
            {"cat": "Luyện thi IELTS", "name": "Speaking Part 1: Hobbies", "image": "/images/topics/ielts_hobbies.jpg"},
        ]

        topics = {}
        for t_data in topics_data:
            cat = categories.get(t_data["cat"])
            if not cat: continue
            
            topic = db.query(Topic).filter(Topic.name == t_data["name"]).first()
            if not topic:
                topic = Topic(
                    name=t_data["name"], 
                    category_id=cat.category_id,
                    description=f"Learn to talk about {t_data['name']}",
                    image_url=t_data["image"]
                )
                db.add(topic)
                db.commit()
                db.refresh(topic)
                print(f"   + Created Topic: {topic.name}")
            topics[topic.name] = topic

        # --- 3. Scenarios (Crucial for Learning Path & Practice) ---
        scenarios_data = [
            # --- BEGINNER (Daily) ---
            {
                "topic": "Giới thiệu bản thân",
                "title": "Lần đầu gặp gỡ",
                "level": DifficultyLevel.BEGINNER,
                "script": "A: Hello, my name is John. Nice to meet you.\nB: Hi John, I'm Sarah. Nice to meet you too.\nA: Where are you from?\nB: I'm from Vietnam. And you?",
                "vocab": {
                    "Nice to meet you": "Rất vui được gặp bạn",
                    "Where are you from": "Bạn đến từ đâu",
                    "I'm from": "Tôi đến từ..."
                }
            },
            {
                "topic": "Gọi món tại nhà hàng",
                "title": "Đặt cà phê",
                "level": DifficultyLevel.BEGINNER,
                "script": "A: Hi, what would you like to order?\nB: I'd like a black coffee, please.\nA: Hot or iced?\nB: Iced, please.",
                "vocab": {
                    "What would you like": "Bạn muốn dùng gì",
                    "I'd like": "Tôi muốn...",
                    "Black coffee": "Cà phê đen"
                }
            },
             # --- INTERMEDIATE (Travel/Business) ---
            {
                "topic": "Làm thủ tục sân bay",
                "title": "Check-in tại quầy",
                "level": DifficultyLevel.INTERMEDIATE,
                "script": "A: Can I see your passport and ticket, please?\nB: Here they are.\nA: Do you have any bags to check in?\nB: Yes, just one suitcase.",
                "vocab": {
                    "Passport": "Hộ chiếu",
                    "Check in": "Làm thủ tục gửi hành lý",
                    "Suitcase": "Vali"
                }
            },
            {
                "topic": "Phỏng vấn xin việc",
                "title": "Giới thiệu kinh nghiệm",
                "level": DifficultyLevel.INTERMEDIATE,
                "script": "A: Tell me a little about your experience.\nB: I have been working as a software engineer for 3 years.\nA: What are your key strengths?\nB: I am good at problem-solving and teamwork.",
                "vocab": {
                    "Experience": "Kinh nghiệm",
                    "Strengths": "Điểm mạnh",
                    "Problem-solving": "Giải quyết vấn đề"
                }
            },
             # --- ADVANCED (Business/IELTS) ---
            {
                "topic": "Thuyết trình dự án",
                "title": "Trình bày chiến lược Q1",
                "level": DifficultyLevel.ADVANCED,
                "script": "A: Let's analyze our performance in Q4.\nB: Despite market volatility, we achieved a 15% growth.\nA: That's impressive. What's the strategy for Q1?\nB: We should focus on diversifying our portfolio.",
                "vocab": {
                    "Volatility": "Sự biến động",
                    "Diversify": "Đa dạng hóa",
                    "Portfolio": "Danh mục đầu tư"
                }
            },
            {
                "topic": "Speaking Part 1: Hobbies",
                "title": "Discussing Leisure Time",
                "level": DifficultyLevel.ADVANCED,
                "script": "A: What do you do in your spare time?\nB: I'm quite keen on photography. It helps me unwind.\nA: Do you prefer indoor or outdoor activities?\nB: Definitely outdoor. I find nature very therapeutic.",
                "vocab": {
                    "Spare time": "Thời gian rảnh",
                    "Keen on": "Thích thú với",
                    "Therapeutic": "Có tính chữa lành/thư giãn"
                }
            },
        ]

        for s_data in scenarios_data:
            topic = topics.get(s_data["topic"])
            if not topic: continue

            scenario = db.query(Scenario).filter(Scenario.title == s_data["title"]).first()
            if not scenario:
                scenario = Scenario(
                    title=s_data["title"],
                    topic_id=topic.topic_id,
                    difficulty_level=s_data["level"],
                    script_content=s_data["script"],
                    key_phrases=s_data["vocab"]
                )
                db.add(scenario)
                db.commit()
                print(f"   + Created Scenario: {scenario.title} ({s_data['level']})")
        
        print("✅ Seeding Complete! Real data is ready.")

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
