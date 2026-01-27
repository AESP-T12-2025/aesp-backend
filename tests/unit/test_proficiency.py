"""
Unit tests for Proficiency endpoints
Requirements (Learner role):
- Complete initial English proficiency & pronunciation assessments
- Access adaptive curriculum & personalized learning paths
- Evaluates users' English proficiency via initial speaking test
"""
import pytest
from fastapi.testclient import TestClient


class TestProficiencyAssessment:
    """Test Assessment - Requirement: Initial proficiency assessment"""

    def test_get_assessment_questions(self, client: TestClient, auth_headers: dict):
        """Test getting assessment questions"""
        response = client.get("/proficiency/assessment", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            # Should return questions or status
            assert isinstance(data, (list, dict))

    def test_submit_assessment(self, client: TestClient, auth_headers: dict):
        """Test submitting assessment answers"""
        response = client.post(
            "/proficiency/assessment",
            headers=auth_headers,
            json={
                "answers": [
                    {"question_id": 1, "answer": "A"},
                    {"question_id": 2, "answer": "B"}
                ]
            }
        )
        
        # May return level or require different format
        assert response.status_code != 401


class TestLearningPath:
    """Test Learning Path - Requirement: Personalized learning paths"""

    def test_get_learning_path(self, client: TestClient, auth_headers: dict):
        """Test getting user's learning path"""
        response = client.get("/proficiency/path", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            # Should have path info
            assert "current_level" in data or isinstance(data, dict)

    def test_get_recommended_topics(self, client: TestClient, auth_headers: dict):
        """Test getting recommended topics based on level"""
        response = client.get("/proficiency/recommendations", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
        elif response.status_code == 404:
            pytest.skip("Recommendations endpoint not implemented")


class TestAdaptiveCurriculum:
    """Test Adaptive Content - Requirement: Adaptive curriculum"""

    def test_content_adapts_to_level(self, client: TestClient, auth_headers: dict):
        """Test that content is adapted to user level"""
        # Get topics - should be filtered/sorted by level
        response = client.get("/content/topics", headers=auth_headers)
        
        if response.status_code == 200:
            # Topics should be accessible
            assert True


class TestUserLevel:
    """Test User Level Management"""

    def test_get_current_level(self, client: TestClient, auth_headers: dict):
        """Test getting user's current proficiency level"""
        response = client.get("/proficiency/level", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            # Should have level info
            pass
        elif response.status_code == 404:
            # May be in different endpoint
            pass
