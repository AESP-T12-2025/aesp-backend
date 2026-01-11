import sys
import os
from sqlalchemy import text, inspect

sys.path.append(os.getcwd())
from app.core.database import engine

def fix_feedback_text_column():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('ai_feedbacks')]
    print(f"Current columns in ai_feedbacks: {columns}")

    with engine.connect() as conn:
        if 'user_input_text' not in columns:
            print("Adding 'user_input_text' column...")
            conn.execute(text("ALTER TABLE ai_feedbacks ADD COLUMN user_input_text TEXT"))
        
        conn.commit()
    
    print("Schema update complete.")

if __name__ == "__main__":
    try:
        fix_feedback_text_column()
    except Exception as e:
        print(f"Error: {e}")
