from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserRole, AuthProvider
from app.core.security import get_password_hash

def create_test_users():
    db = SessionLocal()
    try:
        # 1. Create ADMIN
        admin_email = "admin@aesp.com"
        if not db.query(User).filter(User.email == admin_email).first():
            print(f"Creating Admin: {admin_email}")
            admin = User(
                email=admin_email,
                password_hash=get_password_hash("admin123"),
                full_name="Super Admin",
                role=UserRole.ADMIN,
                auth_provider=AuthProvider.LOCAL,
                is_active=True
            )
            db.add(admin)

        # 2. Create MENTOR
        mentor_email = "mentor@aesp.com"
        if not db.query(User).filter(User.email == mentor_email).first():
            print(f"Creating Mentor: {mentor_email}")
            mentor = User(
                email=mentor_email,
                password_hash=get_password_hash("mentor123"),
                full_name="Expert Mentor",
                role=UserRole.MENTOR,
                auth_provider=AuthProvider.LOCAL,
                is_active=True
            )
            db.add(mentor)
        
        db.commit()
        print("Test users created successfully.")
    except Exception as e:
        print(f"Error creating users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()
