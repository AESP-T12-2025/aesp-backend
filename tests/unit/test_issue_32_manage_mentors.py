"""
Unit tests for Issue #32: Manage Mentor List (Admin)
Testing admin functionality for managing mentor accounts
"""
import pytest
from fastapi.testclient import TestClient


class TestListMentors:
    """Test listing mentors"""

    def test_admin_can_list_all_mentors(self, client: TestClient, admin_token: str, mentor_user):
        """Admin should be able to list all mentors"""
        response = client.get(
            "/admin/mentors",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_learner_cannot_list_mentors(self, client: TestClient, learner_token: str):
        """Learner should not be able to list mentors (admin only)"""
        response = client.get(
            "/admin/mentors",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 403

    def test_list_mentors_without_auth(self, client: TestClient):
        """Listing mentors without auth should return 401"""
        response = client.get("/admin/mentors")

        assert response.status_code == 401


class TestVerifyMentor:
    """Test mentor verification functionality"""

    def test_admin_can_verify_mentor(self, client: TestClient, admin_token: str, mentor_user):
        """Admin should be able to verify a mentor"""
        response = client.put(
            f"/admin/mentors/{mentor_user.user_id}/verify",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("is_verified") == True or "verified" in data.get("message", "").lower()

    def test_admin_can_unverify_mentor(self, client: TestClient, admin_token: str, mentor_user):
        """Admin should be able to unverify a mentor"""
        # First verify
        client.put(
            f"/admin/mentors/{mentor_user.user_id}/verify",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Then unverify
        response = client.put(
            f"/admin/mentors/{mentor_user.user_id}/unverify",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_verify_nonexistent_mentor(self, client: TestClient, admin_token: str):
        """Verifying non-existent mentor should return 404"""
        response = client.put(
            "/admin/mentors/99999/verify",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404

    def test_learner_cannot_verify_mentor(self, client: TestClient, learner_token: str, mentor_user):
        """Learner should not be able to verify mentors"""
        response = client.put(
            f"/admin/mentors/{mentor_user.user_id}/verify",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 403


class TestMentorDetails:
    """Test viewing mentor details"""

    def test_admin_can_view_mentor_details(self, client: TestClient, admin_token: str, mentor_user):
        """Admin should be able to view detailed mentor info"""
        response = client.get(
            f"/admin/mentors/{mentor_user.user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "email" in data or "full_name" in data

    def test_view_nonexistent_mentor(self, client: TestClient, admin_token: str):
        """Viewing non-existent mentor should return 404"""
        response = client.get(
            "/admin/mentors/99999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404


class TestFilterMentors:
    """Test filtering mentors by various criteria"""

    def test_filter_by_verification_status(self, client: TestClient, admin_token: str):
        """Should be able to filter mentors by verification status"""
        response = client.get(
            "/admin/mentors?is_verified=true",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_pagination_mentors_list(self, client: TestClient, admin_token: str):
        """Should support pagination for mentor list"""
        response = client.get(
            "/admin/mentors?skip=0&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
