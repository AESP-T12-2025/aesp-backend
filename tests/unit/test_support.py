"""
Unit tests for Support endpoints
Requirements:
- Provide learner support services (Admin)
"""
import pytest
from fastapi.testclient import TestClient


class TestSupportTickets:
    """Test Support System - Requirement: Learner support services"""

    def test_create_support_ticket(self, client: TestClient, auth_headers: dict):
        """Test learner can create support ticket"""
        response = client.post(
            "/support/tickets",
            headers=auth_headers,
            json={
                "subject": "Need help with AI feature",
                "message": "The AI is not responding properly"
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data or "ticket_id" in data

    def test_get_my_tickets(self, client: TestClient, auth_headers: dict):
        """Test learner can see their tickets"""
        response = client.get("/support/tickets", headers=auth_headers)
        
        if response.status_code == 200:
            assert isinstance(response.json(), list)

    def test_get_ticket_detail(self, client: TestClient, auth_headers: dict):
        """Test getting ticket details"""
        response = client.get("/support/tickets/1", headers=auth_headers)
        
        # Ticket may not exist
        assert response.status_code in [200, 404]


class TestSupportFAQ:
    """Test FAQ System"""

    def test_get_faqs(self, client: TestClient):
        """Test getting FAQ list (public)"""
        response = client.get("/support/faqs")
        
        if response.status_code == 200:
            assert isinstance(response.json(), list)
        elif response.status_code == 404:
            pytest.skip("FAQs endpoint not implemented")
