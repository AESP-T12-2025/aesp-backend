import sys
import os
sys.path.append(os.getcwd())

from app.core.database import engine
from sqlalchemy import inspect

def check_columns():
    inspector = inspect(engine)
    if inspector.has_table("mentor_posts"):
        print("Table 'mentor_posts' exists. Columns:")
        for col in inspector.get_columns("mentor_posts"):
            print(f"- {col['name']} ({col['type']})")
    else:
        print("Table 'mentor_posts' does not exist.")

if __name__ == "__main__":
    check_columns()
