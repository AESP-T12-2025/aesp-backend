"""
Unit tests for Issue #34: Statistics & Reports Dashboard (Admin)
Testing admin dashboard statistics and reports
"""
import pytest
from fastapi.testclient import TestClient


class TestDashboardStats:
    """Test dashboard statistics endpoints"""

    def test_admin_can_view_dashboard_stats(self, client: TestClient, admin_token: str):
        """Admin should be able to view dashboard statistics"""
        response = client.get(
            "/admin/dashboard/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should contain various metrics
        assert isinstance(data, dict)

    def test_learner_cannot_view_dashboard(self, client: TestClient, learner_token: str):
        """Learner should not be able to access admin dashboard"""
        response = client.get(
            "/admin/dashboard/stats",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 403

    def test_dashboard_without_auth(self, client: TestClient):
        """Dashboard without auth should return 401"""
        response = client.get("/admin/dashboard/stats")

        assert response.status_code == 401


class TestUserStatistics:
    """Test user statistics"""

    def test_total_users_count(self, client: TestClient, admin_token: str):
        """Should return total user count"""
        response = client.get(
            "/admin/stats/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data or "count" in data

    def test_users_by_role(self, client: TestClient, admin_token: str):
        """Should return user breakdown by role"""
        response = client.get(
            "/admin/stats/users/by-role",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict) or isinstance(data, list)

    def test_active_users_count(self, client: TestClient, admin_token: str):
        """Should return active users count"""
        response = client.get(
            "/admin/stats/users/active",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200


class TestSubscriptionStatistics:
    """Test subscription/revenue statistics"""

    def test_subscription_breakdown(self, client: TestClient, admin_token: str):
        """Should return subscription breakdown by package"""
        response = client.get(
            "/admin/stats/subscriptions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_revenue_stats(self, client: TestClient, admin_token: str):
        """Should return revenue statistics"""
        response = client.get(
            "/admin/stats/revenue",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data or "revenue" in str(data).lower()


class TestContentStatistics:
    """Test content usage statistics"""

    def test_popular_topics(self, client: TestClient, admin_token: str):
        """Should return most popular topics"""
        response = client.get(
            "/admin/stats/content/popular",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_scenario_completion_rates(self, client: TestClient, admin_token: str):
        """Should return scenario completion rates"""
        response = client.get(
            "/admin/stats/scenarios/completion",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200


class TestDateRangeFiltering:
    """Test filtering stats by date range"""

    def test_stats_with_date_range(self, client: TestClient, admin_token: str):
        """Should support date range filtering"""
        response = client.get(
            "/admin/stats/users?start_date=2024-01-01&end_date=2024-12-31",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_monthly_stats(self, client: TestClient, admin_token: str):
        """Should return monthly statistics"""
        response = client.get(
            "/admin/stats/monthly",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
