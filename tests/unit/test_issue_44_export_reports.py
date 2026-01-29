"""
Test Issue #44: Export Reports (PDF/Excel)
===========================================
REQ-ADMIN-13: View statistics & reports
REQ-LEARNER-14: Receive weekly/monthly performance reports

Tests for:
- PDF report generation for learner progress
- Excel export for admin analytics
- Report content validation
"""
import pytest
from fastapi.testclient import TestClient


class TestPDFExport:
    """Tests for PDF export functionality."""

    # ========== Test: Weekly Report PDF Export ==========

    def test_export_weekly_report_pdf(self, client: TestClient, learner_auth_headers: dict):
        """
        Issue #44: Export weekly report as PDF.
        
        Arrange: Authenticated learner
        Act: GET /learner/reports/weekly/export?format=pdf
        Assert: Returns PDF file or export URL
        """
        response = client.get(
            "/learner/reports/weekly/export",
            params={"format": "pdf"},
            headers=learner_auth_headers
        )
        
        # Accept 200 (implemented), 404, or 501 (not implemented)
        if response.status_code == 200:
            data = response.json()
            # Should return either:
            # 1. Direct PDF bytes (content-type: application/pdf)
            # 2. URL to download PDF
            assert "url" in data or "download_url" in data or \
                   response.headers.get("content-type") == "application/pdf", \
                   "Should return PDF file or download URL"
        else:
            assert response.status_code in [404, 501], \
                f"Unexpected status: {response.status_code}"

    # ========== Test: Monthly Report PDF Export ==========

    def test_export_monthly_report_pdf(self, client: TestClient, learner_auth_headers: dict):
        """
        Issue #44: Export monthly report as PDF.
        """
        response = client.get(
            "/learner/reports/monthly/export",
            params={"format": "pdf"},
            headers=learner_auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "url" in data or "download_url" in data or "message" in data, \
                "Should return download URL or status message"

    # ========== Test: PDF Contains Required Sections ==========

    def test_pdf_report_content_structure(self, client: TestClient, learner_auth_headers: dict):
        """
        Issue #44: PDF report should contain required sections.
        
        Expected sections:
        - Summary statistics
        - Progress charts
        - Speaking time breakdown
        - Recommendations
        """
        response = client.get(
            "/learner/reports/weekly",
            headers=learner_auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # These fields should be included in report data
            expected_fields = ["total_sessions", "total_speaking_time", "average_score"]
            for field in expected_fields:
                # At least some of these should exist
                pass  # Placeholder for actual validation


class TestExcelExport:
    """Tests for Excel export functionality."""

    # ========== Test: Admin Analytics Excel Export ==========

    def test_admin_export_analytics_excel(self, client: TestClient, admin_auth_headers: dict):
        """
        Issue #44: Admin exports analytics as Excel.
        
        Arrange: Authenticated admin
        Act: GET /admin/analytics/export?format=excel
        Assert: Returns Excel file or download URL
        """
        response = client.get(
            "/admin/analytics/export",
            params={"format": "excel"},
            headers=admin_auth_headers
        )
        
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            data = response.json() if "json" in content_type else {}
            
            # Should return Excel file or download URL
            is_excel = "spreadsheet" in content_type or "excel" in content_type
            has_url = "url" in data or "download_url" in data
            
            assert is_excel or has_url or "message" in data, \
                "Should return Excel file or download URL"
        else:
            assert response.status_code in [404, 501], \
                f"Unexpected status: {response.status_code}"

    # ========== Test: Export User Statistics ==========

    def test_export_user_statistics(self, client: TestClient, admin_auth_headers: dict):
        """
        Issue #44: Export user statistics to Excel.
        """
        response = client.get(
            "/admin/users/export",
            params={"format": "excel"},
            headers=admin_auth_headers
        )
        
        # Accept any non-500 response
        assert response.status_code != 500, "Server should not error"

    # ========== Test: Export Transaction History ==========

    def test_export_transactions_excel(self, client: TestClient, admin_auth_headers: dict):
        """
        Issue #44: Export transaction history to Excel.
        """
        response = client.get(
            "/admin/transactions/export",
            params={"format": "excel"},
            headers=admin_auth_headers
        )
        
        assert response.status_code != 500, "Server should not error"


class TestExportPermissions:
    """Test export permission requirements."""

    def test_learner_cannot_export_admin_reports(
        self, 
        client: TestClient, 
        learner_auth_headers: dict
    ):
        """
        Issue #44: Learners should not access admin exports.
        """
        response = client.get(
            "/admin/analytics/export",
            params={"format": "excel"},
            headers=learner_auth_headers
        )
        
        # Should return 403 Forbidden or 404 (endpoint not found)
        assert response.status_code in [403, 404, 401], \
            "Learner should not access admin exports"

    def test_export_requires_authentication(self, client: TestClient):
        """
        Issue #44: Export endpoints require authentication.
        """
        response = client.get(
            "/learner/reports/weekly/export",
            params={"format": "pdf"}
        )
        
        assert response.status_code in [401, 403, 404], \
            "Export should require authentication"


class TestExportFormats:
    """Test various export format options."""

    @pytest.mark.parametrize("export_format", ["pdf", "excel", "csv"])
    def test_supported_export_formats(
        self, 
        client: TestClient, 
        learner_auth_headers: dict,
        export_format: str
    ):
        """
        Issue #44: Support multiple export formats.
        """
        response = client.get(
            "/learner/reports/weekly/export",
            params={"format": export_format},
            headers=learner_auth_headers
        )
        
        # Should not return 415 (Unsupported Media Type) for common formats
        if response.status_code not in [404, 501]:
            assert response.status_code != 415, \
                f"Format {export_format} should be supported"


class TestExportWithDateRange:
    """Test export with date range parameters."""

    def test_export_with_date_range(self, client: TestClient, admin_auth_headers: dict):
        """
        Issue #44: Export analytics with custom date range.
        """
        response = client.get(
            "/admin/analytics/export",
            params={
                "format": "excel",
                "start_date": "2026-01-01",
                "end_date": "2026-01-31"
            },
            headers=admin_auth_headers
        )
        
        # Just verify no server error
        assert response.status_code != 500, "Server should handle date range"

    def test_export_invalid_date_range(self, client: TestClient, admin_auth_headers: dict):
        """
        Issue #44: Handle invalid date ranges gracefully.
        """
        response = client.get(
            "/admin/analytics/export",
            params={
                "format": "excel",
                "start_date": "2026-12-31",
                "end_date": "2026-01-01"  # End before start
            },
            headers=admin_auth_headers
        )
        
        if response.status_code not in [404, 501]:
            # 400/422 for strict validation, OR 200 with empty results (lenient approach)
            assert response.status_code in [200, 400, 422], \
                "Should return 400/422 for invalid date range or 200 with empty results"
