import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.gamification import Challenge, ChallengeType, UserChallenge
from app.models.user import User

def seed_challenges():
    db = SessionLocal()
    try:
        # Check if challenges exist
        if db.query(Challenge).count() > 0:
            print("Challenges already exist. Skipping creation.")
        else:
            print("Seeding base challenges...")
            challenges = [
                Challenge(title="Tân Thủ", description="Đạt 100 XP đầu tiên", challenge_type=ChallengeType.VOCAB_COUNT, target_value=10, points_reward=50),
                Challenge(title="Chiến Binh", description="Học 50 từ vựng", challenge_type=ChallengeType.VOCAB_COUNT, target_value=50, points_reward=100),
                Challenge(title="Bền Bỉ", description="Duy trì chuỗi 3 ngày", challenge_type=ChallengeType.STREAK, target_value=3, points_reward=200),
                Challenge(title="Thao Thao Bất Tuyệt", description="Luyện nói 60 phút", challenge_type=ChallengeType.SPEAKING_TIME, target_value=3600, points_reward=300),
            ]
            db.add_all(challenges)
            db.commit()
            print("Challenges seeded.")

        # Assign to all users
        users = db.query(User).all()
        challenges = db.query(Challenge).all()
        
        for user in users:
            for ch in challenges:
                exists = db.query(UserChallenge).filter_by(user_id=user.user_id, challenge_id=ch.id).first()
                if not exists:
                    uc = UserChallenge(
                        user_id=user.user_id,
                        challenge_id=ch.id,
                        current_progress=0
                    )
                    db.add(uc)
                    print(f"Assigned challenge '{ch.title}' to {user.email}")
        db.commit()
        print("Done!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_challenges()
