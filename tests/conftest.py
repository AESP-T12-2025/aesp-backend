"""
Pytest fixtures and configuration for AESP Backend tests
"""
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override"""
    app.dependency_overrides[get_db] = lambda: db
    
    # Disable rate limiter for testing
    from app.core.limiter import limiter
    limiter.enabled = False
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Re-enable limiter after tests
    limiter.enabled = True
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data() -> dict:
    """Sample user data for registration tests"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }


@pytest.fixture
def test_admin_data() -> dict:
    """Sample admin user data"""
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "full_name": "Admin User",
        "role": "ADMIN"
    }


@pytest.fixture
def test_mentor_data() -> dict:
    """Sample mentor user data"""
    return {
        "email": "mentor@example.com",
        "password": "MentorPassword123!",
        "full_name": "Mentor User",
        "role": "MENTOR"
    }


@pytest.fixture
def auth_headers(client: TestClient, test_user_data: dict) -> dict:
    """Get authentication headers for a test user"""
    # Register user
    client.post("/auth/register", json=test_user_data)
    
    # Login
    response = client.post("/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}
