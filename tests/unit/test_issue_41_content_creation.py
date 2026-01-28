"""
Unit tests for Issue #41: Content Creation Routes (Topics/Scenarios)
Testing admin ability to create, update, and delete topics and scenarios
"""
import pytest
from fastapi.testclient import TestClient
from app.models.content import DifficultyLevel


class TestTopicCreation:
    """Test Topic CRUD operations as Admin"""

    def test_create_topic_as_admin(self, client: TestClient, admin_token: str, test_category):
        """Admin should be able to create topics"""
        response = client.post(
            "/topics",
            json={
                "name": "Business Communication",
                "description": "Professional English for business contexts",
                "category_id": test_category.category_id,
                "industry": "BUSINESS",
                "image_url": "https://example.com/business.jpg"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Business Communication"
        assert data["industry"] == "BUSINESS"
        assert "topic_id" in data

    def test_create_topic_minimal_fields(self, client: TestClient, admin_token: str, test_category):
        """Test creating topic with only required fields"""
        response = client.post(
            "/topics",
            json={
                "name": "Minimal Topic",
                "category_id": test_category.category_id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal Topic"
        assert data["industry"] == "GENERAL"  # Default value

    def test_create_topic_as_learner_forbidden(self, client: TestClient, learner_token: str, test_category):
        """Learner should NOT be able to create topics"""
        response = client.post(
            "/topics",
            json={
                "name": "Unauthorized Topic",
                "category_id": test_category.category_id
            },
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        # Should be 403 Forbidden due to admin check
        assert response.status_code == 403

    def test_update_topic_as_admin(self, client: TestClient, admin_token: str, test_category):
        """Admin should be able to update existing topics"""
        # First create a topic
        create_response = client.post(
            "/topics",
            json={"name": "Original Topic", "category_id": test_category.category_id},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        topic_id = create_response.json()["topic_id"]

        # Update it
        update_response = client.put(
            f"/topics/{topic_id}",
            json={
                "name": "Updated Topic",
                "description": "New description",
                "category_id": test_category.category_id,
                "industry": "TECHNOLOGY"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Updated Topic"
        assert data["description"] == "New description"

    def test_delete_topic_as_admin(self, client: TestClient, admin_token: str, test_category):
        """Admin should be able to delete topics"""
        # Create topic first
        create_response = client.post(
            "/topics",
            json={"name": "Deletable Topic", "category_id": test_category.category_id},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        topic_id = create_response.json()["topic_id"]

        # Delete it
        delete_response = client.delete(
            f"/topics/{topic_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert delete_response.status_code == 200
        assert "deleted successfully" in delete_response.json()["message"]

        # Verify it's gone
        get_response = client.get(f"/topics/{topic_id}")
        assert get_response.status_code == 404


class TestScenarioCreation:
    """Test Scenario CRUD operations as Admin"""

    def test_create_scenario_as_admin(self, client: TestClient, admin_token: str, test_topic):
        """Admin should be able to create scenarios"""
        response = client.post(
            "/scenarios",
            json={
                "title": "Job Interview Role Play",
                "difficulty_level": "INTERMEDIATE",
                "topic_id": test_topic.topic_id,
                "script_content": "You are applying for a marketing position...",
                "key_phrases": {
                    "greeting": "Good morning, thank you for coming in",
                    "question": "Tell me about your previous experience"
                }
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Job Interview Role Play"
        assert data["difficulty_level"] == "INTERMEDIATE"
        assert "scenario_id" in data

    def test_create_scenario_all_difficulty_levels(self, client: TestClient, admin_token: str, test_topic):
        """Test creating scenarios with all difficulty levels"""
        for level in ["BEGINNER", "INTERMEDIATE", "ADVANCED"]:
            response = client.post(
                "/scenarios",
                json={
                    "title": f"Test {level} Scenario",
                    "difficulty_level": level,
                    "topic_id": test_topic.topic_id
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            assert response.json()["difficulty_level"] == level

    def test_create_scenario_as_learner_forbidden(self, client: TestClient, learner_token: str, test_topic):
        """Learner should NOT be able to create scenarios"""
        response = client.post(
            "/scenarios",
            json={
                "title": "Unauthorized Scenario",
                "difficulty_level": "BEGINNER",
                "topic_id": test_topic.topic_id
            },
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 403

    def test_update_scenario_as_admin(self, client: TestClient, admin_token: str, test_topic):
        """Admin should be able to update scenarios"""
        # Create scenario first
        create_response = client.post(
            "/scenarios",
            json={
                "title": "Original Scenario",
                "difficulty_level": "BEGINNER",
                "topic_id": test_topic.topic_id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        scenario_id = create_response.json()["scenario_id"]

        # Update it
        update_response = client.put(
            f"/scenarios/{scenario_id}",
            json={
                "title": "Updated Scenario",
                "difficulty_level": "ADVANCED",
                "topic_id": test_topic.topic_id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["title"] == "Updated Scenario"
        assert data["difficulty_level"] == "ADVANCED"

    def test_delete_scenario_as_admin(self, client: TestClient, admin_token: str, test_topic):
        """Admin should be able to delete scenarios"""
        # Create scenario first
        create_response = client.post(
            "/scenarios",
            json={
                "title": "Deletable Scenario",
                "difficulty_level": "BEGINNER",
                "topic_id": test_topic.topic_id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        scenario_id = create_response.json()["scenario_id"]

        # Delete it
        delete_response = client.delete(
            f"/scenarios/{scenario_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert delete_response.status_code == 200
        assert "deleted successfully" in delete_response.json()["message"]

        # Verify it's gone  
        get_response = client.get(f"/scenarios/{scenario_id}")
        assert get_response.status_code == 404


class TestContentValidation:
    """Test validation and error handling"""

    def test_create_topic_invalid_category(self, client: TestClient, admin_token: str):
        """Test creating topic with non-existent category"""
        response = client.post(
            "/topics",
            json={
                "name": "Invalid Topic",
                "category_id": 99999  # Non-existent
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Should fail with foreign key constraint
        assert response.status_code in [400, 422, 500]

    def test_create_scenario_invalid_topic(self, client: TestClient, admin_token: str):
        """Test creating scenario with non-existent topic"""
        response = client.post(
            "/scenarios",
            json={
                "title": "Invalid Scenario",
                "difficulty_level": "BEGINNER",
                "topic_id": 99999  # Non-existent
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Should fail with foreign key constraint
        assert response.status_code in [400, 422, 500]

    def test_create_scenario_invalid_difficulty(self, client: TestClient, admin_token: str, test_topic):
        """Test creating scenario with invalid difficulty level"""
        response = client.post(
            "/scenarios",
            json={
                "title": "Invalid Difficulty",
                "difficulty_level": "SUPER_EXPERT",  # Invalid
                "topic_id": test_topic.topic_id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Should fail validation
        assert response.status_code == 422
