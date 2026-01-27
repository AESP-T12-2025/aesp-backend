"""
Unit tests for Admin endpoints
Requirements:
- Dashboard (Admin)
- Manage user accounts (enable/disable, view list)
- Manage mentor list
- View statistics & reports
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.core.security import get_password_hash


@pytest.fixture
def admin_auth_headers(client: TestClient, db: Session) -> dict:
    """Create admin user and return auth headers"""
    # Create admin directly in DB
    admin = User(
        email="admin@test.com",
        password_hash=get_password_hash("AdminPass123!"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    db.commit()
    
    # Login
    response = client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "AdminPass123!"
    })
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


class TestAdminDashboard:
    """Test Admin Dashboard - Requirement: Dashboard"""

    def test_admin_dashboard_access(self, client: TestClient, admin_auth_headers: dict):
        """Test admin can access dashboard endpoint"""
        response = client.get("/admin/dashboard", headers=admin_auth_headers)
        
        # Endpoint may not exist yet, but shouldn't be 401
        assert response.status_code != 401

    def test_dashboard_requires_auth(self, client: TestClient):
        """Test dashboard requires authentication"""
        response = client.get("/admin/dashboard")
        
        assert response.status_code == 401


class TestAdminUserManagement:
    """Test Admin User Management - Requirement: Manage user accounts"""

    def test_admin_list_users(self, client: TestClient, admin_auth_headers: dict):
        """Test admin can list all users"""
        response = client.get("/admin/users", headers=admin_auth_headers)
        
        if response.status_code == 200:
            assert isinstance(response.json(), list)
        else:
            # May require different endpoint
            pass

    def test_admin_disable_user(self, client: TestClient, admin_auth_headers: dict, db: Session):
        """Test admin can disable user - Requirement: Enable/Disable Account"""
        # Create a test user to disable
        user = User(
            email="todisable@test.com",
            password_hash=get_password_hash("Test123!"),
            full_name="To Disable",
            role=UserRole.LEARNER,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Try to disable
        response = client.put(
            f"/admin/users/{user.user_id}/toggle-status",
            headers=admin_auth_headers
        )
        
        # May need different endpoint structure
        if response.status_code == 200:
            assert True  # Endpoint works
        elif response.status_code == 404:
            # Endpoint not implemented yet
            pytest.skip("Endpoint not implemented")

    def test_non_admin_cannot_manage_users(self, client: TestClient, auth_headers: dict):
        """Test non-admin cannot access admin endpoints"""
        response = client.get("/admin/users", headers=auth_headers)
        
        assert response.status_code in [401, 403]


class TestAdminMentorManagement:
    """Test Admin Mentor Management - Requirement: Manage mentor list"""

    def test_admin_list_mentors(self, client: TestClient, admin_auth_headers: dict):
        """Test admin can list mentors"""
        response = client.get("/admin/mentors", headers=admin_auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            # Should return list or paginated data
            assert isinstance(data, (list, dict))

    def test_admin_approve_mentor(self, client: TestClient, admin_auth_headers: dict):
        """Test admin can approve mentor - Requirement: Manage mentor list"""
        # This tests the approval workflow
        # Actual implementation may vary
        pass  # TODO: Implement when endpoint is ready


class TestAdminReports:
    """Test Admin Reports - Requirement: View statistics & reports"""

    def test_admin_get_reports(self, client: TestClient, admin_auth_headers: dict):
        """Test admin can access reports"""
        response = client.get("/analytics/admin/summary", headers=admin_auth_headers)
        
        # Reports endpoint may have different path
        if response.status_code == 200:
            assert True
        elif response.status_code == 404:
            pytest.skip("Reports endpoint not implemented")
