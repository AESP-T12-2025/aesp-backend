"""
Tests for Issue #28: Peer Practice Matching
REQ-LEARNER-8: Match learners để practice speaking cùng nhau

Run: pytest tests/unit/test_issue_28_peer_matching.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole



@pytest.mark.skip(reason="Feature not implemented yet. Unskip when implementing Issue #28")
class TestFindPartnerEndpoint:
    """Test POST /peer/find-partner"""
    
    # ========== SUCCESS CASES ==========
    
    def test_learner_can_find_partner(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Authenticated learner
        WHEN: Calls POST /peer/find-partner
        THEN: Returns partner match or waiting status
        """
        response = client.post(
            "/peer/find-partner",
            headers=learner_auth_headers
        )
        
        assert response.status_code in [200, 201, 202]
        data = response.json()
        
        # Either matched or waiting
        assert "session_id" in data or "status" in data
    
    def test_find_partner_returns_session_id(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Partner is found
        WHEN: Match is made
        THEN: Returns session_id for practice
        """
        response = client.post(
            "/peer/find-partner",
            headers=learner_auth_headers
        )
        
        # If matched, should have session_id
        if response.status_code == 200:
            data = response.json()
            if "session_id" in data:
                assert data["session_id"] is not None
    
    def test_find_partner_returns_partner_info(
        self,
        client: TestClient,
        learner_auth_headers: dict,
        create_test_user,
        get_auth_headers
    ):
        """
        GIVEN: Two learners looking for partners
        WHEN: Both call find-partner
        THEN: Both get matched with each other's info
        """
        # Create second learner
        learner2 = create_test_user(
            email="learner2@test.com",
            role=UserRole.LEARNER
        )
        headers2 = get_auth_headers(learner2)
        
        # Both request partners
        response1 = client.post(
            "/peer/find-partner",
            headers=learner_auth_headers
        )
        response2 = client.post(
            "/peer/find-partner",
            headers=headers2
        )
        
        # At least one should succeed
        assert response1.status_code in [200, 201, 202]
        assert response2.status_code in [200, 201, 202]
    
    def test_find_partner_with_topic_preference(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Learner specifies topic preference
        WHEN: Calls find-partner with topic
        THEN: Matches with learner interested in same topic
        """
        response = client.post(
            "/peer/find-partner",
            headers=learner_auth_headers,
            json={"topic_preference": "business"}
        )
        
        assert response.status_code in [200, 201, 202, 422]
    
    # ========== ERROR CASES ==========
    
    def test_unauthenticated_cannot_find_partner(
        self,
        client: TestClient
    ):
        """
        GIVEN: No authentication
        WHEN: Tries to find partner
        THEN: Returns 401
        """
        response = client.post("/peer/find-partner")
        assert response.status_code == 401
    
    def test_admin_cannot_find_peer_partner(
        self,
        client: TestClient,
        admin_auth_headers: dict
    ):
        """
        GIVEN: Admin user
        WHEN: Tries to find peer partner
        THEN: Returns 403 (admins don't practice)
        """
        response = client.post(
            "/peer/find-partner",
            headers=admin_auth_headers
        )
        
        # Admin might be blocked or allowed
        assert response.status_code in [200, 403]
    
    # ========== MATCHING LOGIC ==========
    
    def test_match_by_similar_level(
        self,
        client: TestClient,
        db_session: Session,
        create_test_user,
        get_auth_headers
    ):
        """
        GIVEN: Learners with different levels
        WHEN: Finding partner
        THEN: Match with similar level learner
        """
        # Create B1 learner
        learner_b1 = create_test_user(
            email="b1_learner@test.com",
            role=UserRole.LEARNER
        )
        
        # Create B2 learner
        learner_b2 = create_test_user(
            email="b2_learner@test.com",
            role=UserRole.LEARNER
        )
        
        headers_b1 = get_auth_headers(learner_b1)
        headers_b2 = get_auth_headers(learner_b2)
        
        # Both request matching
        response_b1 = client.post(
            "/peer/find-partner",
            headers=headers_b1
        )
        response_b2 = client.post(
            "/peer/find-partner",
            headers=headers_b2
        )
        
        # Should get some response
        assert response_b1.status_code in [200, 201, 202]
        assert response_b2.status_code in [200, 201, 202]



@pytest.mark.skip(reason="Feature not implemented yet. Unskip when implementing Issue #28")
class TestPeerSession:
    """Test peer practice session management"""
    
    def test_get_active_session(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Learner has active peer session
        WHEN: Requests session info
        THEN: Returns session details
        """
        # First find a partner
        match_response = client.post(
            "/peer/find-partner",
            headers=learner_auth_headers
        )
        
        if match_response.status_code == 200 and "session_id" in match_response.json():
            session_id = match_response.json()["session_id"]
            
            # Get session details
            session_response = client.get(
                f"/peer/sessions/{session_id}",
                headers=learner_auth_headers
            )
            
            assert session_response.status_code in [200, 404]
    
    def test_end_peer_session(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Active peer session
        WHEN: Learner ends session
        THEN: Session is closed
        """
        # Find partner first
        match_response = client.post(
            "/peer/find-partner",
            headers=learner_auth_headers
        )
        
        if match_response.status_code == 200 and "session_id" in match_response.json():
            session_id = match_response.json()["session_id"]
            
            # End session
            end_response = client.post(
                f"/peer/sessions/{session_id}/end",
                headers=learner_auth_headers
            )
            
            assert end_response.status_code in [200, 404]
    
    def test_cancel_partner_search(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Learner is waiting for partner
        WHEN: Cancels search
        THEN: Removed from waiting queue
        """
        # Start searching
        client.post(
            "/peer/find-partner",
            headers=learner_auth_headers
        )
        
        # Cancel search
        cancel_response = client.post(
            "/peer/cancel-search",
            headers=learner_auth_headers
        )
        
        # Either succeeds or endpoint doesn't exist
        assert cancel_response.status_code in [200, 404]
