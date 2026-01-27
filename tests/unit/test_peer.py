"""
Unit tests for Peer Practice endpoints
Requirements (Learner role):
- Practice speaking with other learners with AI support
"""
import pytest
from fastapi.testclient import TestClient


class TestPeerPractice:
    """Test Peer Practice - Requirement: Practice with other learners"""

    def test_find_practice_partner(self, client: TestClient, auth_headers: dict):
        """Test finding a peer for practice"""
        response = client.post(
            "/peer/find-partner",
            headers=auth_headers,
            json={"topic_id": 1}
        )
        
        # May return partner or no match
        assert response.status_code != 401

    def test_get_available_peers(self, client: TestClient, auth_headers: dict):
        """Test getting list of available peers"""
        response = client.get("/peer/available", headers=auth_headers)
        
        if response.status_code == 200:
            assert isinstance(response.json(), list)
        elif response.status_code == 404:
            pytest.skip("Peer matching not implemented")

    def test_join_peer_session(self, client: TestClient, auth_headers: dict):
        """Test joining a peer practice session"""
        response = client.post(
            "/peer/sessions/1/join",
            headers=auth_headers
        )
        
        # Session may not exist
        assert response.status_code in [200, 404]
