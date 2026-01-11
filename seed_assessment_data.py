
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.proficiency import ProficiencyTest

def seed_assessment():
    db = SessionLocal()
    try:
        print("🌱 Seeding Quality Assessment Test Data...")

        # Clear existing tests to avoid confusion (optional, or just update)
        db.query(ProficiencyTest).delete()
        
        real_questions = [
            # --- GRAMMAR (A1-A2) ---
            {
                "id": 1,
                "type": "grammar",
                "text": "My brother _____ tennis every weekend.",
                "options": ["play", "plays", "playing", "played"],
                "correct_option": "plays"
            },
            {
                "id": 2, 
                "type": "grammar",
                "text": "I _____ to the doctor yesterday.",
                "options": ["go", "went", "gone", "going"],
                "correct_option": "went"
            },
            # --- GRAMMAR (B1-B2) ---
            {
                "id": 3,
                "type": "grammar", 
                "text": "If I _____ you, I would take that job offer.",
                "options": ["am", "was", "were", "been"],
                "correct_option": "were"
            },
            {
                "id": 4,
                "type": "grammar",
                "text": "By the time we arrived, the movie _____.",
                "options": ["had started", "has started", "starts", "started"],
                "correct_option": "had started"
            },
            # --- VOCABULARY ---
            {
                "id": 5,
                "type": "vocabulary",
                "text": "Choose the synonym for 'Beautiful'.",
                "options": ["Ugly", "Gorgeous", "Plain", "Messy"],
                "correct_option": "Gorgeous"
            },
            {
                "id": 6,
                "type": "vocabulary",
                "text": "The company is looking to _____ its operations into new markets.",
                "options": ["expand", "expend", "expect", "exile"],
                "correct_option": "expand"
            },
             {
                "id": 7,
                "type": "vocabulary",
                "text": "A person who is 'ambitious' is...",
                "options": ["Lazy", "Determined to succeed", "Shy", "Friendly"],
                "correct_option": "Determined to succeed"
            },
            # --- PRONUNCIATION / SPEAKING ---
            {
                "id": 8,
                "type": "pronunciation",
                "text": "Please read aloud: 'The rain in Spain stays mainly in the plain.'",
                "correct_option": "audio_check" 
            },
            {
                "id": 9,
                "type": "pronunciation",
                "text": "Describe your favorite hobby in one sentence.",
                "correct_option": "audio_check"
            }
        ]

        test = ProficiencyTest(
            title="Comprehensive Placement Test",
            questions_json=real_questions,
            level_criteria_json={
                "A1": 0,    # 0-19
                "A2": 20,   # 20-39
                "B1": 40,   # 40-59
                "B2": 60,   # 60-79
                "C1": 80,   # 80-89
                "C2": 90    # 90-100
            }
        )
        
        db.add(test)
        db.commit()
        print("✅ Created new 'Comprehensive Placement Test' with 9 questions.")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_assessment()
