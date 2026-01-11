import sys
import os
sys.path.append(os.getcwd())
from app.core.database import engine
from sqlalchemy import text

def reset_all_feature_tables():
    tables_to_drop = [
        "user_challenges", "challenges", "user_daily_stats", # Gamification
        "mentor_reviews", # Review
        # "mentor_assessments", # Existing logic in mentor.py might rely on this, be careful. 
        # But if I redefined logic in mentor_review.py... no, mentor_review.py uses "mentor_reviews".
        # mentor.py uses "mentor_assessments". My code mostly adds NEW tables. 
        # Conflict happens when table names match.
        
        "proficiency_tests", "user_test_results", "learning_paths", # Proficiency
        "user_saved_vocab", # Vocab
        "support_tickets", "notifications", "peer_sessions", "system_policies", # New
        "post_likes", "post_comments", "mentor_posts", # Social (Already dropped)
        "transactions", "user_subscriptions", "service_packages" # Payment
    ]
    
    with engine.connect() as conn:
        print("Dropping feature tables...")
        for t in tables_to_drop:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {t} CASCADE"))
                print(f"Dropped {t}")
            except Exception as e:
                print(f"Error dropping {t}: {e}")
        conn.commit()
    print("Cleanup complete.")

if __name__ == "__main__":
    reset_all_feature_tables()
