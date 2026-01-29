"""
Pytest fixtures and configuration for AESP Backend tests
"""
import pytest
from unittest.mock import patch
from typing import Generator, Callable
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash

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


# Alias for db
@pytest.fixture(scope="function")
def db_session(db: Session) -> Session:
    """Alias for db fixture"""
    return db


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override"""
    app.dependency_overrides[get_db] = lambda: db
    
    # Disable rate limiter for testing
    try:
        from app.core.limiter import limiter
        limiter.enabled = False
    except ImportError:
        pass
    
    # Mock create_all_tables to avoid connecting to the main database
    with patch("app.main.create_all_tables"), TestClient(app) as test_client:
        yield test_client
    
    # Re-enable limiter after tests
    try:
        from app.core.limiter import limiter
        limiter.enabled = True
    except ImportError:
        pass
    app.dependency_overrides.clear()


# ========== User Fixtures ==========

@pytest.fixture
def create_test_user(db: Session) -> Callable:
    """Factory fixture to create test users"""
    def _create_user(
        email: str = "test@example.com",
        password: str = "TestPassword123!",
        full_name: str = "Test User",
        role: UserRole = UserRole.LEARNER,
        is_active: bool = True
    ) -> User:
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role=role,
            is_active=is_active
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    return _create_user


@pytest.fixture
def admin_user(create_test_user) -> User:
    """Create admin user"""
    return create_test_user(
        email="admin@test.com",
        role=UserRole.ADMIN
    )


@pytest.fixture
def mentor_user(create_test_user, db: Session) -> User:
    """Create mentor user with Mentor profile"""
    from app.models.mentor import Mentor
    
    user = create_test_user(
        email="mentor@test.com",
        role=UserRole.MENTOR
    )
    
    # Check if Mentor profile already exists for this user
    existing_mentor = db.query(Mentor).filter(Mentor.user_id == user.user_id).first()
    if not existing_mentor:
        # Create Mentor profile for this user
        mentor = Mentor(
            user_id=user.user_id,
            full_name=user.full_name or "Test Mentor",
            bio="Test mentor bio",
            verification_status="PENDING"
        )
        db.add(mentor)
        db.commit()
        db.refresh(mentor)
    
    return user


@pytest.fixture
def learner_user(create_test_user) -> User:
    """Create learner user"""
    return create_test_user(
        email="learner@test.com",
        role=UserRole.LEARNER
    )


# ========== Auth Header Fixtures ==========

@pytest.fixture
def get_auth_headers(client: TestClient) -> Callable:
    """Factory to get auth headers for any user"""
    def _get_headers(user: User, password: str = "TestPassword123!") -> dict:
        response = client.post("/auth/login", json={
            "email": user.email,
            "password": password
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        return {}
    return _get_headers


@pytest.fixture
def admin_auth_headers(client: TestClient, admin_user: User) -> dict:
    """Get admin auth headers"""
    response = client.post("/auth/login", json={
        "email": admin_user.email,
        "password": "TestPassword123!"
    })
    token = response.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mentor_auth_headers(client: TestClient, mentor_user: User) -> dict:
    """Get mentor auth headers"""
    response = client.post("/auth/login", json={
        "email": mentor_user.email,
        "password": "TestPassword123!"
    })
    token = response.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def learner_auth_headers(client: TestClient, learner_user: User) -> dict:
    """Get learner auth headers"""
    response = client.post("/auth/login", json={
        "email": learner_user.email,
        "password": "TestPassword123!"
    })
    token = response.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


# ========== Sample Data Fixtures ==========

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


# ========== Booking & Session Fixtures (Stubs) ==========

@pytest.fixture
def create_mentor_session(db: Session, mentor_user: User) -> Callable:
    """Factory to create mentor sessions"""
    def _create():
        # Stub - will be implemented when session model exists
        return None
    return _create


@pytest.fixture
def create_test_booking(db: Session, mentor_user: User, learner_user: User) -> Callable:
    """Factory to create bookings"""
    def _create():
        # Stub - will be implemented when booking model exists
        return None
    return _create


@pytest.fixture
def create_pending_booking(db: Session, mentor_user: User, learner_user: User) -> Callable:
    """Factory to create pending bookings"""
    def _create():
        # Stub - will be implemented when booking model exists
        class FakeBooking:
            id = 1
        return FakeBooking()
    return _create


@pytest.fixture
def create_learner_booking(db: Session, learner_user: User) -> Callable:
    """Factory to create learner bookings"""
    def _create():
        class FakeBooking:
            id = 1
        return FakeBooking()
    return _create


# ========== Token Fixtures (for simpler auth) ==========

@pytest.fixture
def admin_token(client: TestClient, admin_user: User) -> str:
    """Get admin JWT token"""
    response = client.post("/auth/login", json={
        "email": admin_user.email,
        "password": "TestPassword123!"
    })
    return response.json().get("access_token", "")


@pytest.fixture
def learner_token(client: TestClient, learner_user: User) -> str:
    """Get learner JWT token"""
    response = client.post("/auth/login", json={
        "email": learner_user.email,
        "password": "TestPassword123!"
    })
    return response.json().get("access_token", "")


@pytest.fixture
def mentor_token(client: TestClient, mentor_user: User) -> str:
    """Get mentor JWT token"""
    response = client.post("/auth/login", json={
        "email": mentor_user.email,
        "password": "TestPassword123!"
    })
    return response.json().get("access_token", "")


# ========== Content Fixtures ==========

@pytest.fixture
def test_package(db: Session):
    """Create a test service package for subscription tests"""
    from app.models.payment import ServicePackage
    
    # Check if already exists
    existing = db.query(ServicePackage).filter(ServicePackage.id == 1).first()
    if existing:
        return existing
    
    package = ServicePackage(
        id=1,
        name="Basic Plan",
        description="Basic subscription plan",
        price=9.99,
        duration_days=30,
        is_active=True
    )
    db.add(package)
    db.commit()
    db.refresh(package)
    return package


@pytest.fixture
def test_category(db: Session):
    """Create a test category for content tests"""
    from app.models.content import Category
    category = Category(
        name="Business English",
        description="Professional communication scenarios"
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def test_topic(db: Session, test_category):
    """Create a test topic for scenario tests"""
    from app.models.content import Topic
    topic = Topic(
        category_id=test_category.category_id,
        name="Job Interviews",
        description="Prepare for professional interviews"
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic
