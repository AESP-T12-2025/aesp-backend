import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.social import MentorPost
from app.models.user import User, UserRole

def fix_posts():
    db = SessionLocal()
    try:
        mentor = db.query(User).filter(User.role == UserRole.MENTOR).first()
        if not mentor:
            print("No mentor found.")
            return

        # Clear existing posts to avoid duplicates
        db.query(MentorPost).delete()
        db.commit()

        posts = [
            MentorPost(
                mentor_id=mentor.user_id,
                content="Hôm nay chúng ta học chủ đề Greetings nha! 😊",
                image_url="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500"
            ),
            MentorPost(
                mentor_id=mentor.user_id,
                content="Tip phát âm: 'Think' vs 'Sink'. Đặt lưỡi giữa hai hàm răng! 👅",
                image_url=None
            )
        ]
        db.add_all(posts)
        db.commit()
        print("Re-seeded posts.")
    finally:
        db.close()

if __name__ == "__main__":
    fix_posts()
