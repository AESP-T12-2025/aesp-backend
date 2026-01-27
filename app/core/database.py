"""
Database configuration for AESP Backend
Handles SQLAlchemy engine, session, and base model setup
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Get database URL from settings
DATABASE_URL = settings.DATABASE_URL

# Fix for Neon/Postgres if URL starts with postgres://
# SQLAlchemy 2.0+ requires postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Validate database URL
if not DATABASE_URL:
    logger.error("❌ DATABASE_URL is not configured!")
    raise ValueError("DATABASE_URL must be set in environment variables")

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Check connection vitality before usage
    pool_recycle=300,        # Recycle connections every 5 minutes
    pool_size=5,             # Maintain a pool of connections
    max_overflow=10,         # Allow temporary overflow
    echo=False,              # Set to True for SQL query logging in dev
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    
    Yields:
        Session: A SQLAlchemy database session
        
    Example:
        @router.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables() -> None:
    """
    Create all database tables.
    Should be called once at application startup.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created/verified")
