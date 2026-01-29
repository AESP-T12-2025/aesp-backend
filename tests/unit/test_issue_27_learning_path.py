"""
Tests for Issue #27: Personalized Learning Path
REQ-LEARNER-7: Learner xem learning path cá nhân hóa dựa trên proficiency level

Run: pytest tests/unit/test_issue_27_learning_path.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.proficiency import LearningPath


class TestPersonalizedLearningPathEndpoint:
    """Test GET /proficiency/path - REQ-LEARNER-7"""
    
    # ========== SUCCESS CASES ==========
    
    def test_learner_gets_personalized_path_with_all_required_fields(
        self,
        client: TestClient,
        learner_auth_headers: dict,
        learner_user: User
    ):
        """
        GIVEN: Authenticated learner
        WHEN: Calls GET /proficiency/path
        THEN: Returns current_level, recommended_topics, and next_milestone
        """
        response = client.get(
            "/proficiency/path",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields exist (per Issue #27 acceptance criteria)
        assert "current_level" in data, "Missing current_level field"
        assert "recommended_topics" in data, "Missing recommended_topics field"
        assert "next_milestone" in data, "Missing next_milestone field"
    
    def test_current_level_is_valid_cefr_level(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Learner requests learning path
        WHEN: Path is returned
        THEN: current_level is valid CEFR level (A1, A2, B1, B2, C1, C2)
        """
        response = client.get(
            "/proficiency/path",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        valid_cefr_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        assert data["current_level"] in valid_cefr_levels, \
            f"Invalid CEFR level: {data['current_level']}"
    
    def test_recommended_topics_is_list(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Learner requests learning path
        WHEN: Path is returned
        THEN: recommended_topics is a list
        """
        response = client.get(
            "/proficiency/path",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["recommended_topics"], list), \
            "recommended_topics should be a list"
    
    def test_next_milestone_higher_than_current_level(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Learner has a current level
        WHEN: Path is returned
        THEN: next_milestone > current_level (unless C2)
        """
        response = client.get(
            "/proficiency/path",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
        current_idx = level_order.index(data["current_level"])
        next_idx = level_order.index(data["next_milestone"])
        
        if data["current_level"] != "C2":
            assert next_idx > current_idx, \
                f"next_milestone ({data['next_milestone']}) should be higher than current_level ({data['current_level']})"
        else:
            # C2 is max level, next_milestone should also be C2
            assert data["next_milestone"] == "C2"
    
    def test_new_user_without_assessment_gets_default_a1_path(
        self,
        client: TestClient,
        create_test_user,
        get_auth_headers
    ):
        """
        GIVEN: New user without proficiency assessment
        WHEN: Requests learning path
        THEN: Gets default A1 path (beginner level)
        """
        # Create brand new user
        new_user = create_test_user(email="newlearner@test.com")
        headers = get_auth_headers(new_user)
        
        response = client.get(
            "/proficiency/path",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # New user should start at A1
        assert data["current_level"] == "A1", \
            "New users should default to A1 level"
        assert data["next_milestone"] == "A2", \
            "Next milestone for A1 should be A2"
    
    def test_user_with_existing_path_gets_personalized_recommendations(
        self,
        client: TestClient,
        db_session: Session,
        learner_auth_headers: dict,
        learner_user: User
    ):
        """
        GIVEN: User has completed proficiency assessment (B1 level)
        WHEN: Requests learning path
        THEN: Gets B1-appropriate recommendations
        """
        # Set user's level to B1
        existing_path = LearningPath(
            user_id=learner_user.user_id,
            current_level="B1",
            target_level="C1"
        )
        db_session.add(existing_path)
        db_session.commit()
        
        response = client.get(
            "/proficiency/path",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["current_level"] == "B1"
        assert data["next_milestone"] == "B2"
    
    # ========== ERROR CASES ==========
    
    def test_unauthenticated_request_returns_401(
        self,
        client: TestClient
    ):
        """
        GIVEN: No authentication
        WHEN: Tries to get learning path
        THEN: Returns 401 Unauthorized
        """
        response = client.get("/proficiency/path")
        assert response.status_code == 401
    
    def test_admin_can_access_learning_path(
        self,
        client: TestClient,
        admin_auth_headers: dict
    ):
        """
        GIVEN: Admin is authenticated
        WHEN: Requests learning path
        THEN: Returns 200 (admin also has learning path)
        """
        response = client.get(
            "/proficiency/path",
            headers=admin_auth_headers
        )
        
        # Admin should also be able to access their own path
        assert response.status_code == 200


class TestLearningPathTopicsContent:
    """Test recommended_topics structure and content"""
    
    def test_topic_has_id_name_difficulty(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Learner requests path
        WHEN: Topics are returned
        THEN: Each topic has id, name, difficulty fields
        """
        response = client.get(
            "/proficiency/path",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["recommended_topics"]:
            topic = data["recommended_topics"][0]
            assert "id" in topic, "Topic missing 'id' field"
            assert "name" in topic, "Topic missing 'name' field"
            assert "difficulty" in topic, "Topic missing 'difficulty' field"
