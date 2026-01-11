import sys
import os
sys.path.append(os.getcwd())
from app.main import app
from app.core.database import engine
from sqlalchemy import inspect, text

def check_columns():
    inspector = inspect(engine)
    tables = ['user_daily_stats', 'speaking_sessions', 'ai_feedbacks']
    for table in tables:
        if inspector.has_table(table):
            print(f"\nTable '{table}' exists. Columns:")
            for col in inspector.get_columns(table):
                print(f"- {col['name']} ({col['type']})")
        else:
            print(f"\nTable '{table}' DOES NOT EXIST.")

if __name__ == "__main__":
    check_columns()
