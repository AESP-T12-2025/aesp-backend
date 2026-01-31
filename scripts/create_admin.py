"""
Script tạo Admin account cho AESP
Sử dụng khi cần tạo admin account mới
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def create_admin_user(email: str, password: str, full_name: str):
    """Tạo admin user mới"""
    db = SessionLocal()
    try:
        # Check if email exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ FAILED: Email '{email}' đã tồn tại!")
            print(f"   User ID: {existing_user.user_id}")
            print(f"   Role: {existing_user.role}")
            print(f"   Active: {existing_user.is_active}")
            print("\n💡 Suggestion:")
            print("   1. Sử dụng email khác")
            print("   2. Hoặc login với email này nếu đây là admin account của bạn")
            print(f"   3. Hoặc reset password cho email: {email}")
            return False
        
        # Create admin user
        admin = User(
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("✅ SUCCESS: Admin account created!")
        print(f"   Email: {admin.email}")
        print(f"   Name: {admin.full_name}")
        print(f"   Role: {admin.role}")
        print(f"   User ID: {admin.user_id}")
        print("\n🔐 Login credentials:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print("\n🌐 Login tại: http://localhost:3000/login")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def list_admin_users():
    """List tất cả admin users"""
    db = SessionLocal()
    try:
        admins = db.query(User).filter(User.role == UserRole.ADMIN).all()
        
        print("\n📋 Danh sách Admin users:")
        print("-" * 80)
        
        if not admins:
            print("Không có admin user nào trong database.")
            return
        
        for admin in admins:
            status = "✅ Active" if admin.is_active else "❌ Disabled"
            print(f"ID: {admin.user_id:3d} | {admin.email:30s} | {admin.full_name:20s} | {status}")
        
        print("-" * 80)
        print(f"Total: {len(admins)} admin(s)")
        
    finally:
        db.close()

def reset_password(email: str, new_password: str):
    """Reset password cho existing user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User '{email}' không tồn tại!")
            return False
        
        user.password_hash = get_password_hash(new_password)
        db.commit()
        
        print(f"✅ Password đã được reset cho: {email}")
        print(f"   New password: {new_password}")
        print(f"   Role: {user.role}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 80)
    print("🔧 AESP Admin Account Management")
    print("=" * 80)
    
    # Menu
    print("\nChọn thao tác:")
    print("1. Tạo admin user mới")
    print("2. Xem danh sách admin users")
    print("3. Reset password cho user")
    print("0. Thoát")
    
    choice = input("\nNhập lựa chọn (0-3): ").strip()
    
    if choice == "1":
        print("\n--- TẠO ADMIN USER MỚI ---")
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        full_name = input("Họ tên: ").strip()
        
        if email and password and full_name:
            create_admin_user(email, password, full_name)
        else:
            print("❌ Vui lòng nhập đầy đủ thông tin!")
    
    elif choice == "2":
        list_admin_users()
    
    elif choice == "3":
        print("\n--- RESET PASSWORD ---")
        email = input("Email: ").strip()
        new_password = input("New password: ").strip()
        
        if email and new_password:
            reset_password(email, new_password)
        else:
            print("❌ Vui lòng nhập đầy đủ thông tin!")
    
    elif choice == "0":
        print("Bye!")
    
    else:
        print("❌ Lựa chọn không hợp lệ!")
    
    print("\n" + "=" * 80)
