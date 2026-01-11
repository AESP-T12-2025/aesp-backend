import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.content import Topic

def fix_images():
    db = SessionLocal()
    try:
        # Map of keywords to unsplash images
        image_map = {
            "Introduction": "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=500",
            "Restaurant": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500",
            "Airport": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500",
            "Interview": "https://images.unsplash.com/photo-1565688534245-05d6b5be184a?w=500",
            "Shopping": "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=500",
            "Health": "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?w=500",
            "Directions": "https://images.unsplash.com/photo-1455587734955-081b22074882?w=500",
            "Presentation": "https://images.unsplash.com/photo-1544531696-297f0bf0ad31?w=500",
            "Hobbies": "https://images.unsplash.com/photo-1606092195730-5d7b9af1ef4d?w=500",
        }

        topics = db.query(Topic).all()
        for t in topics:
            for key, url in image_map.items():
                if key.lower() in t.name.lower():
                    t.image_url = url
                    print(f"Updated {t.name} -> {url}")
                    break
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    fix_images()
