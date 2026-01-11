import sys
import os
from sqlalchemy import text, inspect

sys.path.append(os.getcwd())
from app.core.database import engine

def fix_feedback_columns():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('ai_feedbacks')]
    print(f"Current columns in ai_feedbacks: {columns}")

    with engine.connect() as conn:
        if 'grammar_score' not in columns:
            print("Adding 'grammar_score' column...")
            conn.execute(text("ALTER TABLE ai_feedbacks ADD COLUMN grammar_score INTEGER DEFAULT 0"))
        
        if 'pronunciation_score' not in columns:
            print("Adding 'pronunciation_score' column...")
            conn.execute(text("ALTER TABLE ai_feedbacks ADD COLUMN pronunciation_score INTEGER DEFAULT 0"))

        if 'fluency_score' not in columns:
            print("Adding 'fluency_score' column...")
            conn.execute(text("ALTER TABLE ai_feedbacks ADD COLUMN fluency_score INTEGER DEFAULT 0"))

        if 'better_version' not in columns:
            print("Adding 'better_version' column...")
            conn.execute(text("ALTER TABLE ai_feedbacks ADD COLUMN better_version TEXT"))

        if 'feedback_details' not in columns:
            print("Adding 'feedback_details' column...")
            # JSON/JSONB handling depends on DB support, using JSON for simplicity in script
            conn.execute(text("ALTER TABLE ai_feedbacks ADD COLUMN feedback_details JSON"))
        
        conn.commit()
    
    print("Schema update complete.")

if __name__ == "__main__":
    try:
        fix_feedback_columns()
    except Exception as e:
        print(f"Error: {e}")
