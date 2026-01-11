import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.user import User

def check_users():
    db = SessionLocal()
    users = db.query(User).all()
    for u in users:
        print(f"ID: {u.user_id}, Email: {u.email}, Name: {u.full_name}")
    db.close()

if __name__ == "__main__":
    check_users()
