import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.payment import ServicePackage
from app.models.social import MentorPost

def verify_data():
    db = SessionLocal()
    try:
        # Packages
        packages = db.query(ServicePackage).all()
        print(f"Packages Count: {len(packages)}")
        for p in packages:
            print(f" - {p.name}: {p.price} ({p.id})")
            
        # Posts
        posts = db.query(MentorPost).all()
        print(f"Posts Count: {len(posts)}")
        for p in posts:
            print(f" - Post ID {p.id}: {p.content[:30]}...")
            
    finally:
        db.close()

if __name__ == "__main__":
    verify_data()
