import sys
import os
sys.path.append(os.getcwd())
from app.main import app
from app.core.database import SessionLocal
from app.models.gamification import UserDailyStats
from app.models.user import User
from datetime import datetime

# Creates a fake stats entry for ALL users
def seed_stats():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            print("No users found!")
            return

        today = datetime.now().date()
        
        for user in users:
            print(f"Seeding stats for user: {user.email} (ID: {user.user_id}) for date: {today}")

            stat = db.query(UserDailyStats).filter_by(user_id=user.user_id, date=today).first()
            if not stat:
                stat = UserDailyStats(
                    user_id=user.user_id,
                    date=today,
                    speaking_duration_seconds=3600, # 1 hour
                    words_learned=150,
                    login_streak_current=7
                )
                db.add(stat)
                print("  Created new stats record.")
            else:
                stat.speaking_duration_seconds += 1800 # Add 30 mins
                stat.words_learned += 50
                print("  Updated existing stats record.")
        
        db.commit()
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_stats()
