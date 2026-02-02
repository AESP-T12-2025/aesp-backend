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
# Settings optimized for Render/Neon free tier with limited connections
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Check connection vitality before usage (critical!)
    pool_recycle=60,         # Recycle connections every 60 seconds (shorter for free tier)
    pool_size=3,             # Smaller pool for free tier limits
    max_overflow=5,          # Allow temporary overflow
    pool_timeout=30,         # Wait max 30 seconds for connection
    connect_args={
        "connect_timeout": 10,     # Connection timeout
        "keepalives": 1,           # Enable TCP keepalives
        "keepalives_idle": 30,     # Start keepalive after 30 seconds idle
        "keepalives_interval": 10, # Keepalive interval
        "keepalives_count": 5,     # Number of keepalive probes
    },
    echo=False,              # Set to True for SQL query logging in dev
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Don't expire objects after commit (helps with detached objects)
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
