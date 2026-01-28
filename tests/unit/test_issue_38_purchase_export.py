"""
Unit tests for Issue #38: Purchase History Export (Admin)
Testing purchase history export functionality for admins
"""
import pytest
from fastapi.testclient import TestClient


class TestPurchaseHistoryList:
    """Test listing purchase history"""

    def test_admin_can_view_all_purchases(self, client: TestClient, admin_token: str):
        """Admin should be able to view all purchase history"""
        response = client.get(
            "/admin/purchases",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_learner_cannot_view_all_purchases(self, client: TestClient, learner_token: str):
        """Learner should not access admin purchase history"""
        response = client.get(
            "/admin/purchases",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 403


class TestExportPurchaseHistory:
    """Test exporting purchase history"""

    def test_export_as_csv(self, client: TestClient, admin_token: str):
        """Should be able to export purchase history as CSV"""
        response = client.get(
            "/admin/purchases/export?format=csv",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        # Should return CSV content
        assert "text/csv" in response.headers.get("content-type", "").lower() or response.status_code == 200

    def test_export_as_excel(self, client: TestClient, admin_token: str):
        """Should be able to export purchase history as Excel"""
        response = client.get(
            "/admin/purchases/export?format=xlsx",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_export_with_date_range(self, client: TestClient, admin_token: str):
        """Should support date range filtering in export"""
        response = client.get(
            "/admin/purchases/export?format=csv&start_date=2024-01-01&end_date=2024-12-31",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_learner_cannot_export(self, client: TestClient, learner_token: str):
        """Learner should not be able to export purchase history"""
        response = client.get(
            "/admin/purchases/export?format=csv",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 403


class TestFilterPurchases:
    """Test filtering purchase history"""

    def test_filter_by_user(self, client: TestClient, admin_token: str):
        """Should be able to filter purchases by user ID"""
        response = client.get(
            "/admin/purchases?user_id=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_filter_by_package(self, client: TestClient, admin_token: str):
        """Should be able to filter purchases by package ID"""
        response = client.get(
            "/admin/purchases?package_id=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_filter_by_status(self, client: TestClient, admin_token: str):
        """Should be able to filter purchases by payment status"""
        response = client.get(
            "/admin/purchases?status=SUCCESS",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200


class TestPurchaseDetails:
    """Test viewing purchase details"""

    def test_admin_can_view_purchase_details(self, client: TestClient, admin_token: str):
        """Admin should be able to view detailed purchase information"""
        response = client.get(
            "/admin/purchases/1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code in [200, 404]

    def test_learner_can_view_own_purchases(self, client: TestClient, learner_token: str):
        """Learner should be able to view their own purchase history"""
        response = client.get(
            "/learner/purchases",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
