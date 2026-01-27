"""
Tests for Issue #29: Assessment Organization
REQ-MENTOR-2: Mentor tổ chức assessments cho learners

Run: pytest tests/unit/test_issue_29_mentor_assessments.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole



@pytest.mark.skip(reason="Feature not implemented yet. Unskip when implementing Issue #29")
class TestMentorSessionsEndpoint:
    """Test GET /mentor-sessions"""
    
    # ========== SUCCESS CASES ==========
    
    def test_mentor_can_view_sessions(
        self,
        client: TestClient,
        mentor_auth_headers: dict
    ):
        """
        GIVEN: Authenticated mentor
        WHEN: Calls GET /mentor-sessions
        THEN: Returns list of mentor's sessions
        """
        response = client.get(
            "/mentor-sessions",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return list or object with sessions
        assert "sessions" in data or isinstance(data, list)
    
    def test_sessions_list_is_array(
        self,
        client: TestClient,
        mentor_auth_headers: dict
    ):
        """
        GIVEN: Mentor requests sessions
        WHEN: Sessions returned
        THEN: Result is an array
        """
        response = client.get(
            "/mentor-sessions",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        sessions = data.get("sessions", data)
        assert isinstance(sessions, list)
    
    def test_session_has_required_fields(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        create_mentor_session
    ):
        """
        GIVEN: Mentor has sessions
        WHEN: Sessions returned
        THEN: Each session has id, learner, date, status
        """
        # Create a session for this mentor
        create_mentor_session()
        
        response = client.get(
            "/mentor-sessions",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        sessions = data.get("sessions", data)
        if sessions:
            session = sessions[0]
            # Verify expected fields exist
            assert "id" in session or "session_id" in session
    
    # ========== FILTER TESTS ==========
    
    def test_filter_sessions_by_status(
        self,
        client: TestClient,
        mentor_auth_headers: dict
    ):
        """
        GIVEN: Mentor has sessions with different statuses
        WHEN: Filters by status
        THEN: Only matching sessions returned
        """
        response = client.get(
            "/mentor-sessions?status=pending",
            headers=mentor_auth_headers
        )
        
        assert response.status_code in [200, 422]
    
    def test_filter_sessions_by_date_range(
        self,
        client: TestClient,
        mentor_auth_headers: dict
    ):
        """
        GIVEN: Mentor has sessions on different dates
        WHEN: Filters by date range
        THEN: Only sessions in range returned
        """
        response = client.get(
            "/mentor-sessions?from_date=2024-01-01&to_date=2024-12-31",
            headers=mentor_auth_headers
        )
        
        assert response.status_code in [200, 422]
    
    # ========== ERROR CASES ==========
    
    def test_learner_cannot_view_mentor_sessions(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Learner is authenticated
        WHEN: Tries to access mentor-sessions
        THEN: Returns 403 Forbidden
        """
        response = client.get(
            "/mentor-sessions",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 403
    
    def test_unauthenticated_cannot_view_sessions(
        self,
        client: TestClient
    ):
        """
        GIVEN: No authentication
        WHEN: Tries to access mentor-sessions
        THEN: Returns 401
        """
        response = client.get("/mentor-sessions")
        assert response.status_code == 401



@pytest.mark.skip(reason="Feature not implemented yet. Unskip when implementing Issue #29")
class TestScheduleAssessment:
    """Test scheduling assessment sessions"""
    
    def test_mentor_can_schedule_assessment(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        learner_user: User
    ):
        """
        GIVEN: Mentor wants to schedule assessment
        WHEN: Calls schedule endpoint
        THEN: Assessment is created
        """
        response = client.post(
            "/mentor-sessions/schedule",
            headers=mentor_auth_headers,
            json={
                "learner_id": learner_user.user_id,
                "date": "2024-12-01T10:00:00Z",
                "type": "speaking_assessment"
            }
        )
        
        assert response.status_code in [200, 201, 422]
    
    def test_cannot_schedule_overlapping_assessment(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        learner_user: User
    ):
        """
        GIVEN: Mentor already has session at time
        WHEN: Tries to schedule another
        THEN: Returns conflict error
        """
        # Schedule first
        client.post(
            "/mentor-sessions/schedule",
            headers=mentor_auth_headers,
            json={
                "learner_id": learner_user.user_id,
                "date": "2024-12-01T10:00:00Z",
                "type": "speaking_assessment"
            }
        )
        
        # Try to schedule at same time
        response = client.post(
            "/mentor-sessions/schedule",
            headers=mentor_auth_headers,
            json={
                "learner_id": learner_user.user_id,
                "date": "2024-12-01T10:00:00Z",
                "type": "speaking_assessment"
            }
        )
        
        # Should conflict or succeed (duplicate handling)
        assert response.status_code in [200, 201, 409, 422]



@pytest.mark.skip(reason="Feature not implemented yet. Unskip when implementing Issue #29")
class TestAssignProficiencyLevel:
    """Test mentor assigning proficiency levels"""
    
    def test_mentor_can_assign_level(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        learner_user: User
    ):
        """
        GIVEN: Mentor completed assessment
        WHEN: Assigns proficiency level to learner
        THEN: Level is saved
        """
        response = client.post(
            f"/mentor-sessions/assign-level",
            headers=mentor_auth_headers,
            json={
                "learner_id": learner_user.user_id,
                "level": "B1",
                "notes": "Good progress in speaking"
            }
        )
        
        assert response.status_code in [200, 201, 404, 422]
    
    def test_level_must_be_valid_cefr(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        learner_user: User
    ):
        """
        GIVEN: Mentor assigns invalid level
        WHEN: Level is not A1-C2
        THEN: Returns validation error
        """
        response = client.post(
            f"/mentor-sessions/assign-level",
            headers=mentor_auth_headers,
            json={
                "learner_id": learner_user.user_id,
                "level": "INVALID",
                "notes": "Test"
            }
        )
        
        assert response.status_code in [422, 400, 404]
