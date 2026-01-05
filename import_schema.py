
import sys
import os
from sqlalchemy import text

# Add current dir to path to import app modules
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine

def import_schema():
    sql_file = "full_schema.sql"
    
    print(f"Reading {sql_file}...")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    print("Executing SQL script...")
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            # We execute the whole script. 
            # Note: SQLAlchemy might have trouble with passing the whole block at once if it contains specific delimiters, 
            # but usually it works nicely with standard Postgres DDL blocks.
            connection.execute(text(sql_content))
            trans.commit()
            print("✅ SUCCESS: Full schema imported successfully!")
        except Exception as e:
            trans.rollback()
            print(f"❌ ERROR: Failed to import schema. {e}")

if __name__ == "__main__":
    import_schema()
