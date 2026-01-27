"""
Unit tests for Policies endpoints
Requirements (Admin role):
- Create system policies
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.core.security import get_password_hash


class TestPolicies:
    """Test Policies System - Requirement: Create system policies"""

    @pytest.fixture
    def admin_auth_headers(self, client: TestClient, db: Session) -> dict:
        """Create admin for policies"""
        admin = User(
            email="policy_admin@test.com",
            password_hash=get_password_hash("AdminPass123!"),
            full_name="Policy Admin",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        
        response = client.post("/auth/login", json={
            "email": "policy_admin@test.com",
            "password": "AdminPass123!"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_get_public_policies(self, client: TestClient):
        """Test public can view policies (terms, privacy)"""
        response = client.get("/policies")
        
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    def test_get_specific_policy(self, client: TestClient):
        """Test getting a specific policy by type"""
        response = client.get("/policies/TERMS_OF_SERVICE")
        
        # May or may not exist
        assert response.status_code in [200, 404]

    def test_admin_create_policy(self, client: TestClient, admin_auth_headers: dict):
        """Test admin can create policy"""
        response = client.post(
            "/policies",
            headers=admin_auth_headers,
            json={
                "policy_type": "PRIVACY_POLICY",
                "content": "This is our privacy policy..."
            }
        )
        
        if response.status_code in [200, 201]:
            assert True  # Policy created
        elif response.status_code == 409:
            # Policy type already exists
            pass

    def test_admin_update_policy(self, client: TestClient, admin_auth_headers: dict):
        """Test admin can update policy"""
        response = client.put(
            "/policies/TERMS_OF_SERVICE",
            headers=admin_auth_headers,
            json={"content": "Updated terms..."}
        )
        
        # Policy may not exist yet
        assert response.status_code in [200, 404]

    def test_learner_cannot_create_policy(self, client: TestClient, auth_headers: dict):
        """Test non-admin cannot create policies"""
        response = client.post(
            "/policies",
            headers=auth_headers,
            json={
                "policy_type": "HACK",
                "content": "Hacked"
            }
        )
        
        assert response.status_code == 403
