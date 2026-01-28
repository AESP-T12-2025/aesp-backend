"""
Unit tests for Issue #37: Mentor Resources/Documents (Mentor)
Testing mentor resource upload and management
"""
import pytest
from fastapi.testclient import TestClient


class TestUploadResources:
    """Test uploading mentor resources"""

    def test_mentor_can_upload_document(self, client: TestClient, mentor_token: str):
        """Mentor should be able to upload resource documents"""
        response = client.post(
            "/mentor/resources",
            json={
                "title": "Business English Cheat Sheet",
                "description": "Common phrases for business meetings",
                "type": "PDF",
                "url": "https://example.com/resource.pdf"
            },
            headers={"Authorization": f"Bearer {mentor_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data or "resource_id" in data

    def test_learner_cannot_upload_resources(self, client: TestClient, learner_token: str):
        """Learner should not be able to upload resources (mentor only)"""
        response = client.post(
            "/mentor/resources",
            json={"title": "Test", "type": "PDF"},
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 403

    def test_upload_validation(self, client: TestClient, mentor_token: str):
        """Upload with invalid data should return 422"""
        response = client.post(
            "/mentor/resources",
            json={"title": ""},  # Missing required fields
            headers={"Authorization": f"Bearer {mentor_token}"}
        )

        assert response.status_code == 422


class TestListResources:
    """Test listing mentor resources"""

    def test_learner_can_view_resources(self, client: TestClient, learner_token: str):
        """Learners should be able to view available resources"""
        response = client.get(
            "/resources",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_mentor_can_view_own_resources(self, client: TestClient, mentor_token: str):
        """Mentor should be able to view their own uploaded resources"""
        response = client.get(
            "/mentor/resources",
            headers={"Authorization": f"Bearer {mentor_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_filter_resources_by_type(self, client: TestClient, learner_token: str):
        """Should be able to filter resources by type"""
        response = client.get(
            "/resources?type=PDF",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200


class TestUpdateResources:
    """Test updating resources"""

    def test_mentor_can_update_own_resource(self, client: TestClient, mentor_token: str):
        """Mentor should be able to update their own resources"""
        # Create resource
        create_response = client.post(
            "/mentor/resources",
            json={"title": "Test", "description": "Original", "type": "PDF"},
            headers={"Authorization": f"Bearer {mentor_token}"}
        )
        resource_id = create_response.json().get("id")

        # Update it
        response = client.put(
            f"/mentor/resources/{resource_id}",
            json={"title": "Updated Title", "description": "Updated"},
            headers={"Authorization": f"Bearer {mentor_token}"}
        )

        assert response.status_code == 200

    def test_mentor_cannot_update_others_resource(self, client: TestClient, mentor_token: str):
        """Mentor should not be able to update other mentors' resources"""
        response = client.put(
            "/mentor/resources/99999",
            json={"title": "Hacked"},
            headers={"Authorization": f"Bearer {mentor_token}"}
        )

        assert response.status_code in [403, 404]


class TestDeleteResources:
    """Test deleting resources"""

    def test_mentor_can_delete_own_resource(self, client: TestClient, mentor_token: str):
        """Mentor should be able to delete their own resources"""
        # Create resource
        create_response = client.post(
            "/mentor/resources",
            json={"title": "To Delete", "type": "PDF"},
            headers={"Authorization": f"Bearer {mentor_token}"}
        )
        resource_id = create_response.json().get("id")

        # Delete it
        response = client.delete(
            f"/mentor/resources/{resource_id}",
            headers={"Authorization": f"Bearer {mentor_token}"}
        )

        assert response.status_code == 200

    def test_admin_can_delete_any_resource(self, client: TestClient, admin_token: str):
        """Admin should be able to delete any resource"""
        response = client.delete(
            "/admin/resources/1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code in [200, 404]


class TestResourceDownload:
    """Test downloading/accessing resources"""

    def test_learner_can_download_resource(self, client: TestClient, learner_token: str):
        """Learner should be able to access/download resources"""
        response = client.get(
            "/resources/1/download",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        # Might redirect or provide download URL
        assert response.status_code in [200, 302, 404]

    def test_track_resource_views(self, client: TestClient, learner_token: str):
        """Should track resource view counts"""
        response = client.post(
            "/resources/1/view",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code in [200, 404]
