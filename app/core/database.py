from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

SQL_ALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Fix for Neon/Postgres if URL starts with postgres:// (SQLAlchemy requires postgresql://)
if SQL_ALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQL_ALCHEMY_DATABASE_URL = SQL_ALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    SQL_ALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Check connection vitality before usage
    pool_recycle=300,    # Recycle connections every 5 minutes
    pool_size=5,         # Maintain a pool of connections
    max_overflow=10      # Allow temporary overflow
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
