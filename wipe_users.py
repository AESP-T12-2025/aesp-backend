import sys
import os

# Add the parent directory to sys.path to resolve app imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import SessionLocal, engine

def wipe_database():
    print("🗑️  Starting database wipe (Users & Related Data)...")
    
    try:
        # Use raw connection for TRUNCATE CASCADE
        with engine.connect() as connection:
            # Disable triggers if needed, but TRUNCATE CASCADE is usually enough
            # We target 'users' because it's the root of the dependency tree
            # CASCADE will wipe everything referencing users
            print("Running: TRUNCATE TABLE users CASCADE;")
            
            # Start transaction
            trans = connection.begin()
            
            # List of tables to truncate specifically if CASCADE doesn't catch them all immediately 
            # or if we want to be thorough. 
            # But TRUNCATE users CASCADE is powerful.
            # Let's try the nuclear option first.
            connection.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE;"))
            
            trans.commit()
            print("✅ Successfully wiped 'users' and all dependent tables.")
            
    except Exception as e:
        print(f"❌ Error wiping database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    confirmation = input("⚠️  WARNING: This will DELETE ALL USERS and related data. Are you sure? (yes/no): ")
    if confirmation.lower() == "yes":
        wipe_database()
    else:
        print("❌ Operation cancelled.")
