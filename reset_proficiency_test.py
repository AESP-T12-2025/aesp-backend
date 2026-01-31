"""
Reset the old proficiency test so the new 25-question test will be created.
Run this script once to apply the update.
"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.proficiency import ProficiencyTest

db = SessionLocal()

# Delete old test(s)
deleted = db.query(ProficiencyTest).delete()
print(f"Deleted {deleted} old proficiency test(s)")

db.commit()
db.close()

print("Done! New 25-question test will be created on next API call to /proficiency/test")
