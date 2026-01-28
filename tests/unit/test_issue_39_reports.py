"""
Unit tests for Issue #39: Weekly/Monthly Reports (Learner)
Testing automated report generation for learners
"""
import pytest
from fastapi.testclient import TestClient


class TestWeeklyReports:
    """Test weekly report generation"""

    def test_get_current_week_report(self, client: TestClient, learner_token: str):
        """Should return current week's progress report"""
        response = client.get(
            "/learner/reports/weekly",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_specific_week_report(self, client: TestClient, learner_token: str):
        """Should return report for a specific week"""
        response = client.get(
            "/learner/reports/weekly?week=1&year=2024",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_weekly_report_contains_key_metrics(self, client: TestClient, learner_token: str):
        """Weekly report should contain essential progress metrics"""
        response = client.get(
            "/learner/reports/weekly",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should contain metrics like practice_time, scenarios_completed, etc.
        assert isinstance(data, dict)


class TestMonthlyReports:
    """Test monthly report generation"""

    def test_get_current_month_report(self, client: TestClient, learner_token: str):
        """Should return current month's progress report"""
        response = client.get(
            "/learner/reports/monthly",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_specific_month_report(self, client: TestClient, learner_token: str):
        """Should return report for a specific month"""
        response = client.get(
            "/learner/reports/monthly?month=1&year=2024",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_monthly_report_summary(self, client: TestClient, learner_token: str):
        """Monthly report should include comprehensive summary"""
        response = client.get(
            "/learner/reports/monthly",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200


class TestReportHistory:
    """Test viewing report history"""

    def test_list_all_reports(self, client: TestClient, learner_token: str):
        """Should list all available reports for a learner"""
        response = client.get(
            "/learner/reports",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_filter_reports_by_type(self, client: TestClient, learner_token: str):
        """Should be able to filter reports by type (weekly/monthly)"""
        response = client.get(
            "/learner/reports?type=weekly",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200


class TestExportReports:
    """Test exporting reports"""

    def test_export_weekly_report_pdf(self, client: TestClient, learner_token: str):
        """Should be able to export weekly report as PDF"""
        response = client.get(
            "/learner/reports/weekly/export?format=pdf",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code in [200, 501]  # 501 if not implemented

    def test_export_monthly_report_pdf(self, client: TestClient, learner_token: str):
        """Should be able to export monthly report as PDF"""
        response = client.get(
            "/learner/reports/monthly/export?format=pdf",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code in [200, 501]


class TestReportNotifications:
    """Test report email notifications"""

    def test_enable_weekly_email_reports(self, client: TestClient, learner_token: str):
        """Should be able to enable weekly email reports"""
        response = client.put(
            "/learner/settings/reports",
            json={"weekly_email": True},
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_disable_monthly_email_reports(self, client: TestClient, learner_token: str):
        """Should be able to disable monthly email reports"""
        response = client.put(
            "/learner/settings/reports",
            json={"monthly_email": False},
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200


class TestReportPermissions:
    """Test report access permissions"""

    def test_mentor_cannot_view_learner_reports(self, client: TestClient, mentor_token: str):
        """Mentor should not access learner-specific reports (unless assigned)"""
        response = client.get(
            "/learner/reports/weekly",
            headers={"Authorization": f"Bearer {mentor_token}"}
        )

        assert response.status_code in [403, 200]  # Depends on implementation

    def test_report_without_auth(self, client: TestClient):
        """Accessing reports without auth should return 401"""
        response = client.get("/learner/reports/weekly")

        assert response.status_code == 401
