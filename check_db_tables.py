import sys
import os

# Ensure app is in path
sys.path.append(os.getcwd())

from app.main import app
from app.core.database import engine
from sqlalchemy import inspect

def check_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = [
        "users", "mentors", "availability_slots", "bookings", "mentor_assessments",
        "mentor_posts", "post_comments", "post_likes",
        "service_packages", "transactions", "user_subscriptions",
        "challenges", "user_challenges", "user_daily_stats",
        "mentor_reviews",
        "proficiency_tests", "user_test_results", "learning_paths",
        "user_saved_vocab",
        "support_tickets", "notifications", "peer_sessions", "system_policies"
    ]
    
    print("--- Database Verification Report ---")
    print(f"Total Tables Found: {len(tables)}")
    
    missing = []
    for t in expected_tables:
        if t in tables:
            print(f"[OK] Found table: {t}")
        else:
            print(f"[ERROR] Missing table: {t}")
            missing.append(t)
            
    if not missing:
        print("\nSUCCESS: All core tables are present.")
        sys.exit(0)
    else:
        print(f"\nFAILURE: Missing {len(missing)} tables.")
        sys.exit(1)

if __name__ == "__main__":
    check_tables()
