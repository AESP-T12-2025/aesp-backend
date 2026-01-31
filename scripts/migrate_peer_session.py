import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    print("DATABASE_URL not found in .env")
    exit(1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Adding level, session_type and call_id columns to peer_sessions...")
    try:
        conn.execute(text("ALTER TABLE peer_sessions ADD COLUMN IF NOT EXISTS level VARCHAR;"))
        conn.execute(text("ALTER TABLE peer_sessions ADD COLUMN IF NOT EXISTS session_type VARCHAR DEFAULT 'voice';"))
        conn.execute(text("ALTER TABLE peer_sessions ADD COLUMN IF NOT EXISTS call_id VARCHAR;"))
        conn.commit()
        print("✅ Columns added successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
