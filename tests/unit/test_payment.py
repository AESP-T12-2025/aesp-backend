"""
Unit tests for Payment & Subscription endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestServicePackages:
    """Test service package listing"""

    def test_get_packages(self, client: TestClient):
        """Test getting list of service packages"""
        response = client.get("/payment/packages")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestSubscription:
    """Test subscription management"""

    def test_get_current_subscription_unauthorized(self, client: TestClient):
        """Test getting subscription without auth fails"""
        response = client.get("/payment/my-subscription")
        
        assert response.status_code == 401

    def test_get_current_subscription_no_subscription(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting subscription when user has none"""
        response = client.get("/payment/my-subscription", headers=auth_headers)
        
        # Should return 200 with has_subscription: False
        assert response.status_code == 200
        assert response.json()["has_subscription"] is False


class TestTransaction:
    """Test transaction creation"""

    def test_create_transaction_unauthorized(self, client: TestClient):
        """Test creating transaction without auth fails"""
        response = client.post("/payment/create-transaction", json={
            "package_id": 1,
            "amount": 100
        })
        
        assert response.status_code == 401
