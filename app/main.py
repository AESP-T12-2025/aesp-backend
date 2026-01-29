"""
AESP Backend - Main Application Entry Point
===========================================
FastAPI application configuration with:
- Security middleware (CORS, Rate Limiting)
- Standardized exception handling
- All API routers
"""
from dotenv import load_dotenv
# IMPORTANT: Load environment variables FIRST before any other imports
load_dotenv()

import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.database import engine, Base, create_all_tables
from app.core.limiter import limiter
from app.core.exceptions import register_exception_handlers

# Import all routers
from app.routers import (
    upload, auth, content, users, payment, ai, mentor,
    social, gamification, mentor_review, proficiency, vocab,
    support, notification, peer, admin, analytics, policies,
    images
)

# Import all models to register them with SQLAlchemy
from app.models import (
    user,
    content as content_model,
    mentor as mentor_model,
    social as social_model,
    payment as payment_model,
    gamification as game_model,
    mentor_review as review_model,
    proficiency as prof_model,
    vocab as vocab_model,
    support as support_model,
    notification as noti_model,
    peer as peer_model,
    policy as policy_model
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# LIFESPAN CONTEXT MANAGER
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # STARTUP
    logger.info("🚀 Starting AESP Backend...")
    
    # Create database tables
    create_all_tables()
    
    # Create static directory for audio files
    os.makedirs("app/static", exist_ok=True)
    
    logger.info("✅ AESP Backend started successfully!")
    
    yield
    
    # SHUTDOWN
    logger.info("👋 Shutting down AESP Backend...")


# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="AESP Backend API",
    description="AI-assisted English Speaking Practice Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Standardized Exception Handling
register_exception_handlers(app)

# Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# =============================================================================
# CORS CONFIGURATION
# =============================================================================

# SECURITY: Restrict CORS to specific origins only
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://aesp-frontend.vercel.app",
]

# Add optional additional origin from environment
if os.getenv("FRONTEND_URL"):
    ALLOWED_ORIGINS.append(os.getenv("FRONTEND_URL"))

# Filter out empty strings
origins = [origin for origin in ALLOWED_ORIGINS if origin]
logger.info(f"CORS allowed origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
)


# =============================================================================
# ROUTER REGISTRATION
# =============================================================================

# Core routers
app.include_router(auth.router, tags=["Auth"])
app.include_router(users.router, tags=["Users"])

# Content routers
app.include_router(content.router, tags=["Content"])
app.include_router(vocab.router, tags=["Vocabulary"])

# AI routers
app.include_router(ai.router, tags=["AI Core"])

# Mentor routers
app.include_router(mentor.router, tags=["Mentor & Booking"])
app.include_router(mentor_review.router, tags=["Mentor Review"])
app.include_router(mentor_review.session_router, tags=["Mentor Sessions"])

# Social routers
app.include_router(social.router, tags=["Social"])
app.include_router(peer.router, tags=["Peer Practice"])

# Gamification routers
app.include_router(gamification.router, tags=["Gamification"])
app.include_router(proficiency.router, tags=["Proficiency"])

# Payment routers
app.include_router(payment.router, tags=["Payment"])

# Admin routers
app.include_router(admin.router, tags=["Admin"])
app.include_router(policies.router, tags=["Policies"])

# Support routers
app.include_router(support.router, tags=["Support"])
app.include_router(support.admin_support_router, tags=["Admin Support"])  # Issue #33
app.include_router(notification.router, tags=["Notifications"])

# Analytics routers
app.include_router(analytics.router, tags=["Analytics"])

# Utility routers
app.include_router(upload.router, tags=["Upload"])
app.include_router(images.router, tags=["Images"])


# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@app.get("/", tags=["Health"])
def health_check():
    """
    Health check endpoint.
    Returns a simple message to verify the API is running.
    """
    return {
        "status": "healthy",
        "message": "AESP Backend is running!",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def detailed_health_check():
    """
    Detailed health check endpoint.
    Returns application status and configuration info.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "cors_origins": len(origins),
        "rate_limiting": True
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )