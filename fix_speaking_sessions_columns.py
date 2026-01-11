import sys
import os
from sqlalchemy import text, inspect

sys.path.append(os.getcwd())
from app.core.database import engine

def fix_columns():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('speaking_sessions')]
    print(f"Current columns in speaking_sessions: {columns}")

    with engine.connect() as conn:
        if 'score' not in columns:
            print("Adding 'score' column...")
            conn.execute(text("ALTER TABLE speaking_sessions ADD COLUMN score INTEGER"))
        
        if 'audio_url' not in columns:
            print("Adding 'audio_url' column...")
            conn.execute(text("ALTER TABLE speaking_sessions ADD COLUMN audio_url VARCHAR"))

        if 'status' not in columns:
            print("Adding 'status' column...")
            conn.execute(text("ALTER TABLE speaking_sessions ADD COLUMN status VARCHAR DEFAULT 'IN_PROGRESS'"))
        
        conn.commit()
    
    print("Schema update complete.")

if __name__ == "__main__":
    try:
        fix_columns()
    except Exception as e:
        print(f"Error: {e}")
