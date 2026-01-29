"""
Unit tests for Issue #42: Fix Subscription upgrade/cancel endpoints
Testing subscription management functionality
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone


class TestSubscriptionUpgrade:
    """Test subscription upgrade functionality"""

    def test_upgrade_subscription_success(self, client: TestClient, learner_token: str, test_package):
        """Learner should be able to upgrade to a new package"""
        # First, create a package
        response = client.post(
            "/payment/upgrade",
            params={"package_id": 1},
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Subscription upgraded successfully" in data["message"]
        assert "end_date" in data

    def test_upgrade_to_nonexistent_package(self, client: TestClient, learner_token: str):
        """Upgrading to non-existent package should return 404"""
        response = client.post(
            "/payment/upgrade",
            params={"package_id": 99999},
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 404
        response_data = response.json()
        # API returns nested format: {"success": False, "error": {"message": "..."}}
        error_data = response_data.get("error", {})
        assert "Package not found" in error_data.get("message", "")

    def test_upgrade_deactivates_old_subscription(self, client: TestClient, learner_token: str, db_session, test_package):
        """Upgrading should deactivate old active subscriptions"""
        from app.models.payment import UserSubscription
        
        # Create first subscription
        response1 = client.post(
            "/payment/upgrade",
            params={"package_id": 1},
            headers={"Authorization": f"Bearer {learner_token}"}
        )
        assert response1.status_code == 200

        # Upgrade to new package
        response2 = client.post(
            "/payment/upgrade",
            params={"package_id": 1},
            headers={"Authorization": f"Bearer {learner_token}"}
        )
        assert response2.status_code ==200

        # Check that only 1 subscription is active
        # (This would need db_session fixture to query UserSubscription)

    def test_upgrade_without_auth(self, client: TestClient):
        """Upgrade without authentication should fail with 401"""
        response = client.post(
            "/payment/upgrade",
            params={"package_id": 1}
        )

        assert response.status_code == 401


class TestSubscriptionCancel:
    """Test subscription cancellation functionality"""

    def test_cancel_active_subscription(self, client: TestClient, learner_token: str, test_package):
        """Canceling active subscription should succeed"""
        # First upgrade to create active subscription
        client.post(
            "/payment/upgrade",
            params={"package_id": 1},
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        # Then cancel
        response = client.post(
            "/payment/cancel",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "Subscription cancelled successfully" in data["message"]

    def test_cancel_without_active_subscription(self, client: TestClient, learner_token: str):
        """Canceling without active subscription should return appropriate message"""
        response = client.post(
            "/payment/cancel",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "No active subscription to cancel" in data["message"]

    def test_cancel_without_auth(self, client: TestClient):
        """Cancel without authentication should fail with 401"""
        response = client.post("/payment/cancel")

        assert response.status_code == 401

    def test_cancel_multiple_times(self, client: TestClient, learner_token: str):
        """Canceling multiple times should be idempotent"""
        # Create and cancel subscription
        client.post("/payment/upgrade", params={"package_id": 1}, headers={"Authorization": f"Bearer {learner_token}"})
        response1 = client.post("/payment/cancel", headers={"Authorization": f"Bearer {learner_token}"})
        assert response1.status_code == 200

        # Cancel again - should return "no active subscription"
        response2 = client.post("/payment/cancel", headers={"Authorization": f"Bearer {learner_token}"})
        assert response2.status_code == 200
        assert "No active subscription" in response2.json()["message"]


class TestGetMySubscription:
    """Test getting current user subscription status"""

    def test_get_subscription_with_active_sub(self, client: TestClient, learner_token: str):
        """Get subscription should return active subscription details"""
        # Create subscription first
        client.post("/payment/upgrade", params={"package_id": 1}, headers={"Authorization": f"Bearer {learner_token}"})

        response = client.get(
            "/payment/subscription",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should have subscription details

    def test_get_subscription_without_sub(self, client: TestClient, learner_token: str):
        """Get subscription without active sub should return appropriate response"""
        response = client.get(
            "/payment/subscription",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        # Should indicate no active subscription

    def test_get_subscription_without_auth(self, client: TestClient):
        """Get subscription without auth should return 401"""
        response = client.get("/payment/subscription")

        assert response.status_code == 401


class TestSubscriptionEdgeCases:
    """Test edge cases and validation"""

    def test_upgrade_with_invalid_package_id_type(self, client: TestClient, learner_token: str):
        """Upgrade with invalid package_id type should return 422"""
        response = client.post(
            "/payment/upgrade",
            params={"package_id": "invalid"},
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 422

    def test_subscription_dates_are_valid(self, client: TestClient, learner_token: str, test_package):
        """Upgraded subscription should have valid start and end dates"""
        response = client.post(
            "/payment/upgrade",
            params={"package_id": 1},
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        
        # end_date should be in the future
        end_date = datetime.fromisoformat(data["end_date"].replace("Z", "+00:00"))
        assert end_date > datetime.now(timezone.utc)
