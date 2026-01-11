"""
Comprehensive Database Seeding Script
Seeds high-quality test data for all AESP models
"""
import sys
import os
sys.path.append(os.getcwd())

from datetime import datetime, timedelta
import random
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.content import Category, Topic, Scenario, DifficultyLevel, SpeakingSession, AIFeedback
from app.models.gamification import Challenge, UserChallenge, UserDailyStats, ChallengeType
from app.models.mentor import Mentor, AvailabilitySlot, Booking, BookingStatus
from app.models.proficiency import ProficiencyTest, LearningPath, UserTestResult
from app.models.social import MentorPost, PostComment, PostLike
from app.models.notification import Notification
from app.models.payment import ServicePackage, Transaction, UserSubscription, TransactionStatus

def seed_all():
    db = SessionLocal()
    try:
        print("🌱 Starting comprehensive database seeding...")
        
        # ========================================
        # 1. USERS (Admin, Mentors, Learners)
        # ========================================
        print("\n📦 Seeding Users...")
        
        # Check if users exist
        existing = db.query(User).count()
        if existing > 0:
            print(f"   Found {existing} existing users, skipping user creation...")
            users = db.query(User).all()
            admin = next((u for u in users if u.role == UserRole.ADMIN), None)
            mentors = [u for u in users if u.role == UserRole.MENTOR]
            learners = [u for u in users if u.role == UserRole.LEARNER]
        else:
            # Create Admin
            admin = User(
                email="admin@aesp.com",
                password_hash=get_password_hash("admin123"),
                full_name="Nguyễn Admin",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            
            # Create Mentors
            mentor_data = [
                ("mentor1@aesp.com", "Trần Mentor Việt", "IELTS Speaking, Business English, Academic Writing"),
                ("mentor2@aesp.com", "Lê Thị Hương", "TOEIC, Conversation, Grammar"),
                ("mentor3@aesp.com", "David Smith", "Native Speaker, Pronunciation, Fluency"),
            ]
            mentors = []
            for email, name, skills in mentor_data:
                m = User(email=email, password_hash=get_password_hash("mentor123"), full_name=name, role=UserRole.MENTOR)
                db.add(m)
                mentors.append(m)
            
            # Create Learners
            learner_data = [
                ("learner@test.com", "Bùi Quang Long"),
                ("student1@aesp.com", "Nguyễn Văn An"),
                ("student2@aesp.com", "Trần Thị Bình"),
                ("student3@aesp.com", "Lê Minh Châu"),
                ("student4@aesp.com", "Phạm Đức Duy"),
            ]
            learners = []
            for email, name in learner_data:
                l = User(email=email, password_hash=get_password_hash("learner123"), full_name=name, role=UserRole.LEARNER)
                db.add(l)
                learners.append(l)
            
            db.commit()
            for u in [admin] + mentors + learners:
                db.refresh(u)
            print(f"   ✅ Created {1 + len(mentors) + len(learners)} users")

        # ========================================
        # 2. CATEGORIES & TOPICS & SCENARIOS
        # ========================================
        print("\n📦 Seeding Content (Categories, Topics, Scenarios)...")
        
        if db.query(Category).count() == 0:
            categories_data = [
                ("Daily Life", "Các tình huống giao tiếp hàng ngày"),
                ("Business", "Tiếng Anh thương mại và công sở"),
                ("Travel", "Du lịch và khám phá"),
                ("Academic", "Tiếng Anh học thuật (IELTS, TOEFL)"),
            ]
            
            categories = []
            for name, desc in categories_data:
                c = Category(name=name, description=desc)
                db.add(c)
                categories.append(c)
            db.commit()
            for c in categories:
                db.refresh(c)
            
            # Topics per category
            topics_data = {
                "Daily Life": [
                    ("Self Introduction", "Giới thiệu bản thân một cách tự nhiên", "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=500"),
                    ("At the Restaurant", "Gọi món, thanh toán, đánh giá", "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500"),
                    ("Shopping", "Mua sắm, trả giá, đổi trả hàng", "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=500"),
                    ("Health & Doctor", "Khám bệnh, mô tả triệu chứng", "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?w=500"),
                ],
                "Business": [
                    ("Job Interview", "Phỏng vấn xin việc chuyên nghiệp", "https://images.unsplash.com/photo-1565688534245-05d6b5be184a?w=500"),
                    ("Business Presentation", "Thuyết trình sản phẩm, dự án", "https://images.unsplash.com/photo-1544531696-297f0bf0ad31?w=500"),
                    ("Meeting & Negotiation", "Họp và đàm phán hiệu quả", "https://images.unsplash.com/photo-1556761175-b413da4baf72?w=500"),
                ],
                "Travel": [
                    ("At the Airport", "Check-in, qua cửa an ninh, thủ tục", "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500"),
                    ("Asking for Directions", "Hỏi đường và chỉ dẫn địa điểm", "https://images.unsplash.com/photo-1455587734955-081b22074882?w=500"),
                    ("Hotel Check-in", "Nhận phòng khách sạn", "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=500"),
                ],
                "Academic": [
                    ("IELTS Speaking Part 1: Hobbies", "Trả lời câu hỏi về sở thích", "https://images.unsplash.com/photo-1606092195730-5d7b9af1ef4d?w=500"),
                    ("IELTS Speaking Part 2: Describe a Person", "Mô tả một người quan trọng", "https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=500"),
                    ("Academic Discussion", "Thảo luận chủ đề học thuật", "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=500"),
                ],
            }
            
            all_topics = []
            for cat in categories:
                for topic_name, topic_desc, topic_img in topics_data.get(cat.name, []):
                    t = Topic(category_id=cat.category_id, name=topic_name, description=topic_desc, image_url=topic_img)
                    db.add(t)
                    all_topics.append(t)
            db.commit()
            for t in all_topics:
                db.refresh(t)
            
            # Scenarios for each topic
            scenarios_data = [
                ("Greeting a stranger", DifficultyLevel.BEGINNER, "You meet someone new at a party. Introduce yourself."),
                ("Formal introduction", DifficultyLevel.INTERMEDIATE, "Introduce yourself in a business networking event."),
                ("Group introduction", DifficultyLevel.ADVANCED, "Lead a group introduction session for a project team."),
            ]
            
            for topic in all_topics:
                for title, diff, script in scenarios_data:
                    s = Scenario(
                        topic_id=topic.topic_id,
                        title=f"{topic.name}: {title}",
                        difficulty_level=diff,
                        script_content=script,
                        key_phrases=["Hello", "Nice to meet you", "I'm from...", "My hobbies include..."]
                    )
                    db.add(s)
            db.commit()
            print(f"   ✅ Created {len(categories)} categories, {len(all_topics)} topics, {len(all_topics) * 3} scenarios")
        else:
            print("   ⏭️ Content already exists, skipping...")
            categories = db.query(Category).all()

        # ========================================
        # 3. MENTOR PROFILES & AVAILABILITY
        # ========================================
        print("\n📦 Seeding Mentor Profiles & Slots...")
        
        if db.query(Mentor).count() == 0:
            mentor_users = db.query(User).filter(User.role == UserRole.MENTOR).all()
            bios = [
                "Hơn 5 năm kinh nghiệm giảng dạy IELTS. Từng là giám khảo IELTS tại British Council.",
                "Giảng viên ĐH Ngoại Thương. Chuyên gia TOEIC 990 và Business English.",
                "Native speaker từ USA, chuyên coaching phát âm và fluency cho người Việt.",
            ]
            skills_list = [
                "IELTS Speaking, IELTS Writing, Academic English",
                "TOEIC, Business Communication, Grammar",
                "Pronunciation, Fluency, Native Expressions"
            ]
            
            for i, mu in enumerate(mentor_users):
                mentor = Mentor(
                    user_id=mu.user_id,
                    full_name=mu.full_name,
                    bio=bios[i % len(bios)],
                    skills=skills_list[i % len(skills_list)],
                    verification_status="VERIFIED"
                )
                db.add(mentor)
            db.commit()
            
            # Create availability slots for each mentor (next 7 days)
            mentor_profiles = db.query(Mentor).all()
            for mentor in mentor_profiles:
                for day_offset in range(1, 8):
                    slot_date = datetime.now() + timedelta(days=day_offset)
                    for hour in [9, 10, 14, 15, 16]:
                        start = slot_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                        end = start + timedelta(hours=1)
                        slot = AvailabilitySlot(mentor_id=mentor.mentor_id, start_time=start, end_time=end, status=BookingStatus.AVAILABLE)
                        db.add(slot)
            db.commit()
            print(f"   ✅ Created {len(mentor_profiles)} mentor profiles with availability slots")
        else:
            print("   ⏭️ Mentors already exist, skipping...")

        # ========================================
        # 4. GAMIFICATION (Challenges, DailyStats)
        # ========================================
        print("\n📦 Seeding Gamification Data...")
        
        if db.query(Challenge).count() == 0:
            challenges = [
                Challenge(title="Tân Thủ", description="Kiếm 100 XP đầu tiên", challenge_type=ChallengeType.VOCAB_COUNT, target_value=10, points_reward=50),
                Challenge(title="Chiến Binh", description="Học 50 từ vựng mới", challenge_type=ChallengeType.VOCAB_COUNT, target_value=50, points_reward=100),
                Challenge(title="Bền Bỉ", description="Duy trì streak 7 ngày", challenge_type=ChallengeType.STREAK, target_value=7, points_reward=150),
                Challenge(title="Thao Thao Bất Tuyệt", description="Luyện nói 60 phút", challenge_type=ChallengeType.SPEAKING_TIME, target_value=3600, points_reward=200),
            ]
            db.add_all(challenges)
            db.commit()
            
            # Assign challenges to learners
            learner_users = db.query(User).filter(User.role == UserRole.LEARNER).all()
            challenge_list = db.query(Challenge).all()
            for learner in learner_users:
                for ch in challenge_list:
                    uc = UserChallenge(
                        user_id=learner.user_id,
                        challenge_id=ch.id,
                        current_progress=random.randint(0, ch.target_value // 2),
                        is_completed=False
                    )
                    db.add(uc)
            db.commit()
            
            # Daily stats for past 14 days
            for learner in learner_users:
                for day_offset in range(14):
                    stat_date = datetime.now() - timedelta(days=day_offset)
                    stats = UserDailyStats(
                        user_id=learner.user_id,
                        date=stat_date,
                        speaking_duration_seconds=random.randint(0, 1800),
                        words_learned=random.randint(0, 20),
                        login_streak_current=random.randint(1, 7)
                    )
                    db.add(stats)
            db.commit()
            print("   ✅ Created challenges, user challenges, and daily stats")
        else:
            print("   ⏭️ Gamification data exists, skipping...")

        # ========================================
        # 5. PROFICIENCY TESTS & LEARNING PATHS
        # ========================================
        print("\n📦 Seeding Proficiency Tests & Learning Paths...")
        
        if db.query(ProficiencyTest).count() == 0:
            test = ProficiencyTest(
                title="AESP Placement Test",
                questions_json=[
                    {"id": 1, "type": "grammar", "text": "I ___ to the gym every day.", "options": ["go", "goes", "going", "went"], "correct": "go"},
                    {"id": 2, "type": "vocabulary", "text": "What is the synonym of 'happy'?", "options": ["sad", "joyful", "angry", "tired"], "correct": "joyful"},
                    {"id": 3, "type": "grammar", "text": "She ___ studying when I called.", "options": ["is", "was", "were", "be"], "correct": "was"},
                    {"id": 4, "type": "vocabulary", "text": "What does 'procrastinate' mean?", "options": ["delay", "hurry", "improve", "forget"], "correct": "delay"},
                    {"id": 5, "type": "pronunciation", "text": "Read aloud: 'The weather in Vietnam is quite pleasant in spring.'", "options": [], "correct": None},
                ],
                level_criteria_json={"0-40": "A1", "41-60": "A2", "61-75": "B1", "76-90": "B2", "91-100": "C1"}
            )
            db.add(test)
            db.commit()
            db.refresh(test)
            
            # Create learning paths for learners
            learner_users = db.query(User).filter(User.role == UserRole.LEARNER).all()
            levels = ["A1", "A2", "B1", "B2"]
            topics = db.query(Topic).limit(5).all()
            
            for i, learner in enumerate(learner_users):
                current = levels[i % len(levels)]
                target = levels[min(i % len(levels) + 1, len(levels) - 1)]
                
                # Create test result
                result = UserTestResult(
                    user_id=learner.user_id,
                    test_id=test.id,
                    score=random.randint(50, 85),
                    assessed_level=current
                )
                db.add(result)
                
                # Create learning path
                roadmap = [f"Topic: {t.name}" for t in topics]
                path = LearningPath(
                    user_id=learner.user_id,
                    current_level=current,
                    target_level=target,
                    generated_roadmap_json=roadmap
                )
                db.add(path)
            db.commit()
            print("   ✅ Created proficiency test and learning paths for all learners")
        else:
            print("   ⏭️ Proficiency data exists, skipping...")

        # ========================================
        # 6. SOCIAL (Posts, Comments, Likes)
        # ========================================
        print("\n📦 Seeding Social Content...")
        
        if db.query(MentorPost).count() == 0:
            mentor_users = db.query(User).filter(User.role == UserRole.MENTOR).all()
            posts_content = [
                ("Tip phát âm: Phân biệt 'Think' vs 'Sink'. Đặt lưỡi giữa hai hàm răng để có âm 'th' chuẩn! 👅", None),
                ("Hôm nay chúng ta học chủ đề 'At the Airport'. Video mới đã up trên kênh! ✈️", "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500"),
                ("IELTS Speaking Band 7+ Tip: Dùng linking words như 'Moreover', 'Furthermore' để nâng band! 📈", None),
                ("Các bạn ơi, ai có câu hỏi về TOEIC Part 5 thì comment nhé! 💬", None),
                ("Mình vừa tổng hợp 100 phrasal verbs thường gặp. Inbox để nhận file PDF nhé! 📚", "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500"),
            ]
            
            all_posts = []
            for i, (content, img) in enumerate(posts_content):
                mentor = mentor_users[i % len(mentor_users)]
                post = MentorPost(mentor_id=mentor.user_id, content=content, image_url=img)
                db.add(post)
                all_posts.append(post)
            db.commit()
            for p in all_posts:
                db.refresh(p)
            
            # Add comments and likes
            learner_users = db.query(User).filter(User.role == UserRole.LEARNER).all()
            comments = [
                "Cảm ơn mentor, bài viết rất hữu ích! 🙏",
                "Mình đã áp dụng và thấy hiệu quả!",
                "Mentor cho em hỏi thêm được không ạ?",
                "Quá tuyệt vời luôn! ❤️",
            ]
            
            for post in all_posts:
                # Random comments
                for j in range(random.randint(1, 3)):
                    learner = random.choice(learner_users)
                    comment = PostComment(post_id=post.id, user_id=learner.user_id, content=random.choice(comments))
                    db.add(comment)
                
                # Random likes
                for learner in random.sample(learner_users, k=random.randint(2, len(learner_users))):
                    like = PostLike(post_id=post.id, user_id=learner.user_id)
                    db.add(like)
            db.commit()
            print(f"   ✅ Created {len(all_posts)} social posts with comments and likes")
        else:
            print("   ⏭️ Social content exists, skipping...")

        # ========================================
        # 7. PAYMENTS (Packages, Subscriptions)
        # ========================================
        print("\n📦 Seeding Payment Data...")
        
        if db.query(ServicePackage).count() == 0:
            packages = [
                ServicePackage(name="Basic", price=0, duration_days=30, description="Gói miễn phí", features=["10 lượt AI/ngày", "Cộng đồng cơ bản"], is_active=True),
                ServicePackage(name="Pro AI", price=199000, duration_days=30, description="AI không giới hạn", features=["AI không giới hạn", "Chấm điểm chi tiết", "Không quảng cáo"], is_active=True),
                ServicePackage(name="Mentor 1-1", price=499000, duration_days=30, description="Học cùng Mentor", features=["Tất cả quyền lợi Pro", "4 buổi Mentor 1-1", "Lộ trình cá nhân hóa"], is_active=True),
            ]
            db.add_all(packages)
            db.commit()
            
            # Give one learner a subscription
            learner = db.query(User).filter(User.role == UserRole.LEARNER).first()
            pro_pkg = db.query(ServicePackage).filter(ServicePackage.name == "Pro AI").first()
            if learner and pro_pkg:
                sub = UserSubscription(
                    user_id=learner.user_id,
                    package_id=pro_pkg.id,
                    start_date=datetime.now() - timedelta(days=10),
                    end_date=datetime.now() + timedelta(days=20),
                    is_active=True
                )
                db.add(sub)
                db.commit()
            print("   ✅ Created service packages and sample subscription")
        else:
            print("   ⏭️ Payment data exists, skipping...")

        # ========================================
        # 8. NOTIFICATIONS
        # ========================================
        print("\n📦 Seeding Notifications...")
        
        if db.query(Notification).count() == 0:
            learner_users = db.query(User).filter(User.role == UserRole.LEARNER).all()
            notif_templates = [
                ("Chào mừng đến với AESP! 🎉", "Bắt đầu hành trình học tiếng Anh của bạn ngay hôm nay.", "SYSTEM"),
                ("Nhắc nhở học tập", "Bạn chưa luyện tập hôm nay. Hãy dành 10 phút nhé!", "SYSTEM"),
                ("Thành tựu mới! 🏆", "Bạn vừa hoàn thành thử thách 'Tân Thủ'. +50 XP!", "SYSTEM"),
                ("Lịch hẹn sắp tới", "Buổi học 1-1 với Mentor Việt sẽ bắt đầu trong 1 giờ.", "BOOKING"),
            ]
            
            for learner in learner_users:
                for title, msg, type_ in notif_templates:
                    n = Notification(user_id=learner.user_id, title=title, message=msg, type=type_, is_read=random.choice([True, False]))
                    db.add(n)
            db.commit()
            print(f"   ✅ Created notifications for all learners")
        else:
            print("   ⏭️ Notifications exist, skipping...")

        print("\n✅ Database seeding completed successfully!")
        print("=" * 50)
        print("Test Accounts:")
        print("  Admin:   admin@aesp.com / admin123")
        print("  Mentor:  mentor1@aesp.com / mentor123")
        print("  Learner: learner@test.com / learner123")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_all()
