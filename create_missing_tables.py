import sys
import os
sys.path.append(os.getcwd())

from app.core.database import engine, Base
from app.models.content import SpeakingSession, AIFeedback
from sqlalchemy import inspect

def fix():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Existing tables: {tables}")
    
    if "speaking_sessions" not in tables:
        print("Creating speaking_sessions table...")
        SpeakingSession.__table__.create(engine)
    else:
        print("speaking_sessions table already exists.")

    if "ai_feedbacks" not in tables:
        print("Creating ai_feedbacks table...")
        AIFeedback.__table__.create(engine)
    else:
        print("ai_feedbacks table already exists.")

if __name__ == "__main__":
    try:
        fix()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
