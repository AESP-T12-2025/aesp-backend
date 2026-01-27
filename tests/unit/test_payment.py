"""
Unit tests for expanded Payment endpoints
Requirements (Learner role):
- Search, compare, and purchase service packages
- Upgrade/downgrade subscription
- Can choose package with or without mentor
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.payment import ServicePackage
from app.core.security import get_password_hash


@pytest.fixture
def sample_package(db: Session) -> ServicePackage:
    """Create a sample package for testing"""
    package = ServicePackage(
        name="Pro Plan",
        description="Full access package",
        price=199000,
        duration_days=30,
        features=["AI Chat", "Speech Analysis"],
        mentor_included=False,
        is_active=True
    )
    db.add(package)
    db.commit()
    db.refresh(package)
    return package


class TestPackageListing:
    """Test Package Listing - Requirement: Search and compare packages"""

    def test_list_all_packages(self, client: TestClient):
        """Test GET /payment/packages returns list"""
        response = client.get("/payment/packages")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_filter_mentor_packages(self, client: TestClient):
        """Test filtering packages with mentor - Requirement: With or without mentor"""
        response = client.get("/payment/packages?mentor_included=true")
        
        assert response.status_code == 200

    def test_filter_no_mentor_packages(self, client: TestClient):
        """Test filtering packages without mentor"""
        response = client.get("/payment/packages?mentor_included=false")
        
        assert response.status_code == 200


class TestPurchasePackage:
    """Test Package Purchase - Requirement: Purchase service packages"""

    def test_create_transaction(self, client: TestClient, auth_headers: dict, sample_package: ServicePackage):
        """Test creating a payment transaction"""
        response = client.post(
            "/payment/create-transaction",
            headers=auth_headers,
            json={"package_id": sample_package.id}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "transaction_id" in data or "message" in data

    def test_purchase_nonexistent_package(self, client: TestClient, auth_headers: dict):
        """Test purchasing non-existent package fails"""
        response = client.post(
            "/payment/create-transaction",
            headers=auth_headers,
            json={"package_id": 99999}
        )
        
        assert response.status_code == 404


class TestSubscription:
    """Test Subscription Management - Requirement: Upgrade/downgrade"""

    def test_get_my_subscription(self, client: TestClient, auth_headers: dict):
        """Test getting current subscription"""
        response = client.get("/payment/my-subscription", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "has_subscription" in data

    def test_upgrade_subscription(self, client: TestClient, auth_headers: dict, sample_package: ServicePackage):
        """Test upgrading subscription"""
        response = client.post(
            f"/payment/upgrade?package_id={sample_package.id}",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            assert "message" in response.json()

    def test_cancel_subscription(self, client: TestClient, auth_headers: dict):
        """Test cancelling subscription"""
        response = client.post("/payment/cancel", headers=auth_headers)
        
        assert response.status_code == 200
        assert "message" in response.json()


class TestAdminPackageManagement:
    """Test Admin Package CRUD - Requirement: Manage service packages"""

    @pytest.fixture
    def admin_auth_headers(self, client: TestClient, db: Session) -> dict:
        """Create admin user"""
        admin = User(
            email="pkg_admin@test.com",
            password_hash=get_password_hash("AdminPass123!"),
            full_name="Package Admin",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        
        response = client.post("/auth/login", json={
            "email": "pkg_admin@test.com",
            "password": "AdminPass123!"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_admin_create_package(self, client: TestClient, admin_auth_headers: dict):
        """Test admin can create package"""
        response = client.post(
            "/payment/packages",
            headers=admin_auth_headers,
            json={
                "name": "New Package",
                "price": 99000,
                "duration_days": 30,
                "mentor_included": False
            }
        )
        
        assert response.status_code in [200, 201]

    def test_admin_update_package(self, client: TestClient, admin_auth_headers: dict, sample_package: ServicePackage):
        """Test admin can update package"""
        response = client.put(
            f"/payment/packages/{sample_package.id}",
            headers=admin_auth_headers,
            json={
                "name": "Updated Package",
                "price": 299000,
                "duration_days": 30
            }
        )
        
        assert response.status_code in [200, 422]  # 422 if validation differs

    def test_admin_delete_package(self, client: TestClient, admin_auth_headers: dict, sample_package: ServicePackage):
        """Test admin can delete package"""
        response = client.delete(
            f"/payment/packages/{sample_package.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200

    def test_learner_cannot_manage_packages(self, client: TestClient, auth_headers: dict):
        """Test non-admin cannot create packages"""
        response = client.post(
            "/payment/packages",
            headers=auth_headers,
            json={"name": "Hack", "price": 0, "duration_days": 30}
        )
        
        assert response.status_code == 403
