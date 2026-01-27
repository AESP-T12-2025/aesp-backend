"""
Unit tests for Content endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestCategories:
    """Test category endpoints"""

    def test_get_categories(self, client: TestClient):
        """Test getting list of categories"""
        response = client.get("/categories")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestTopics:
    """Test topic endpoints"""

    def test_get_topics(self, client: TestClient):
        """Test getting list of topics"""
        response = client.get("/topics")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_topic_not_found(self, client: TestClient):
        """Test getting non-existent topic"""
        response = client.get("/topics/99999")
        
        assert response.status_code == 404


class TestScenarios:
    """Test scenario endpoints"""

    def test_get_scenarios(self, client: TestClient):
        """Test getting list of scenarios"""
        response = client.get("/scenarios")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_scenarios_by_topic(self, client: TestClient):
        """Test getting scenarios filtered by topic"""
        response = client.get("/scenarios?topic_id=1")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAdminContentManagement:
    """Test admin-only content management - should require auth"""

    def test_create_topic_unauthorized(self, client: TestClient):
        """Test creating topic without auth fails"""
        response = client.post("/topics", json={
            "name": "Test Topic",
            "description": "Test Description",
            "category_id": 1
        })
        
        assert response.status_code == 401

    def test_delete_topic_unauthorized(self, client: TestClient):
        """Test deleting topic without auth fails"""
        response = client.delete("/topics/1")
        
        assert response.status_code == 401
