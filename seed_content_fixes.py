import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.payment import ServicePackage
from app.models.social import MentorPost
from app.models.user import User, UserRole

def seed_content_fixes():
    db = SessionLocal()
    try:
        # 1. Seed Packages
        print("Seeding Packages...")
        if db.query(ServicePackage).count() == 0:
            packages = [
                ServicePackage(
                    name="Basic",
                    price=0.0,
                    duration_days=30,
                    description="Gói cơ bản miễn phí",
                    features=["10 lượt AI/ngày", "Cộng đồng cơ bản"],
                    is_active=True
                ),
                ServicePackage(
                    name="Pro AI",
                    price=199000.0,
                    duration_days=30,
                    description="Mở khóa AI không giới hạn",
                    features=["AI không giới hạn", "Chấm điểm chi tiết", "Không quảng cáo"],
                    is_active=True
                ),
                ServicePackage(
                    name="Mentor 1-1",
                    price=499000.0,
                    duration_days=30,
                    description="Học trực tiếp cùng Mentor",
                    features=["Tất cả quyền lợi Pro", "4 buổi Mentor 1-1", "Lộ trình cá nhân hóa"],
                    is_active=True
                )
            ]
            db.add_all(packages)
            db.commit()
            print("  Created 3 packages.")
        else:
            print("  Packages already exist.")

        # 2. Seed Social Posts
        print("\nSeeding Social Posts...")
        mentor = db.query(User).filter(User.role == UserRole.MENTOR).first()
        if not mentor:
            print("  No mentor found to create posts! Creating one...")
            # Create a dummy mentor if needed, strictly for seeding correctness
            mentor = User(email="mentor_seed@test.com", full_name="Ms. Jenny", role=UserRole.MENTOR)
            db.add(mentor)
            db.commit()
        
        if db.query(MentorPost).count() == 0:
            posts = [
                MentorPost(
                    mentor_id=mentor.user_id,
                    content="Chào các bạn! Hôm nay chúng ta sẽ học về chủ đề 'Greetings' nhé. Một tips nhỏ là hãy cười khi nói Hello! 😄",
                    like_count=15,
                    comment_count=2
                ),
                 MentorPost(
                    mentor_id=mentor.user_id,
                    content="🔥 Thử thách tuần này: Quay video 30s giới thiệu bản thân bằng tiếng Anh. Ai tham gia comment bên dưới nhé!",
                    like_count=24,
                    comment_count=10
                )
            ]
            db.add_all(posts)
            db.commit()
            print("  Created 2 mentor posts.")
        else:
            print("  Social posts already exist.")
            
        print("Done!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_content_fixes()
