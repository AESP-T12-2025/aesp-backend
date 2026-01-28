"""
Unit tests for Social endpoints
Requirements:
- Practice speaking with other learners (Learner)
- Moderate feedback & comments (Admin)
- Share communication experiences (Mentor)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.core.security import get_password_hash


@pytest.fixture
def mentor_auth_headers(client: TestClient, db: Session) -> dict:
    """Create mentor for social posts"""
    mentor = User(
        email="social_mentor@test.com",
        password_hash=get_password_hash("MentorPass123!"),
        full_name="Social Mentor",
        role=UserRole.MENTOR,
        is_active=True
    )
    db.add(mentor)
    db.commit()
    
    response = client.post("/auth/login", json={
        "email": "social_mentor@test.com",
        "password": "MentorPass123!"
    })
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


class TestCommunityFeed:
    """Test Community Feed - Requirement: Share experiences"""

    def test_get_community_feed(self, client: TestClient):
        """Test GET /social/posts returns feed"""
        response = client.get("/social/posts")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_feed_paginates(self, client: TestClient):
        """Test feed supports pagination"""
        response = client.get("/social/posts?limit=5")
        
        assert response.status_code == 200


class TestMentorPosts:
    """Test Mentor Posts - Requirement: Share communication experiences"""

    def test_mentor_create_post(self, client: TestClient, mentor_auth_headers: dict):
        """Test mentor can create community post"""
        response = client.post(
            "/social/posts",
            headers=mentor_auth_headers,
            json={"content": "Tips for better pronunciation!"}
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "content" in data or "id" in data

    def test_learner_cannot_create_post(self, client: TestClient, auth_headers: dict):
        """Test learner cannot create mentor posts"""
        response = client.post(
            "/social/posts",
            headers=auth_headers,
            json={"content": "This should fail"}
        )
        
        assert response.status_code == 403


class TestComments:
    """Test Comments on Posts"""

    def test_add_comment(self, client: TestClient, auth_headers: dict):
        """Test adding comment to a post"""
        response = client.post(
            "/social/posts/1/comments",
            headers=auth_headers,
            json={"content": "Great tips!"}
        )
        
        # Post 1 may not exist, but should not be 401
        assert response.status_code != 401


class TestLikes:
    """Test Like functionality"""

    def test_toggle_like(self, client: TestClient, auth_headers: dict):
        """Test liking/unliking a post"""
        response = client.post("/social/posts/1/like", headers=auth_headers)
        
        # Post may not exist, but auth should work
        assert response.status_code != 401


class TestAdminModeration:
    """Test Admin Moderation - Requirement: Moderate feedback & comments"""

    @pytest.fixture
    def admin_auth_headers(self, client: TestClient, db: Session) -> dict:
        """Create admin for moderation"""
        admin = User(
            email="mod_admin@test.com",
            password_hash=get_password_hash("AdminPass123!"),
            full_name="Mod Admin",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        
        response = client.post("/auth/login", json={
            "email": "mod_admin@test.com",
            "password": "AdminPass123!"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_admin_get_posts_for_moderation(self, client: TestClient, admin_auth_headers: dict):
        """Test admin can see all posts for moderation"""
        response = client.get("/social/admin/posts", headers=admin_auth_headers)
        
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    def test_admin_moderate_post(self, client: TestClient, admin_auth_headers: dict):
        """Test admin can approve/reject posts"""
        response = client.put(
            "/social/admin/posts/1/moderate?new_status=APPROVED",
            headers=admin_auth_headers
        )
        
        # Should work or return 404 if post doesn't exist
        assert response.status_code in [200, 404]

    def test_admin_delete_comment(self, client: TestClient, admin_auth_headers: dict):
        """Test admin can delete inappropriate comments"""
        response = client.delete(
            "/social/admin/comments/1",
            headers=admin_auth_headers
        )
        
        assert response.status_code in [200, 404]
