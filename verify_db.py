
import sys
import os
from sqlalchemy import text

# Add current dir to path to import app modules
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine

def test_connection():
    try:
        # Try to connect and execute a simple query
        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        print("✅ KẾT NỐI THÀNH CÔNG! (Connection Successful)")
        print(f"Database response: {result.fetchone()[0]}")
        db.close()
    except Exception as e:
        print("❌ KẾT NỐI THẤT BẠI! (Connection Failed)")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
