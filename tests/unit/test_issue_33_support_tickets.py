"""
Unit tests for Issue #33: Support Services/Tickets (Admin/Learner)
Testing support ticket system functionality
"""
import pytest
from fastapi.testclient import TestClient


class TestCreateSupportTicket:
    """Test creating support tickets"""

    def test_learner_can_create_ticket(self, client: TestClient, learner_token: str):
        """Learner should be able to create a support ticket"""
        response = client.post(
            "/support/tickets",
            json={
                "title": "Need help with pronunciation",
                "description": "I'm having trouble with the 'th' sound",
                "category": "TECHNICAL"
            },
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "ticket_id" in data or "id" in data

    def test_create_ticket_validation(self, client: TestClient, learner_token: str):
        """Creating ticket with missing fields should return 422"""
        response = client.post(
            "/support/tickets",
            json={"title": ""},  # Missing description
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 422

    def test_create_ticket_without_auth(self, client: TestClient):
        """Creating ticket without auth should return 401"""
        response = client.post(
            "/support/tickets",
            json={"title": "Test", "description": "Test"}
        )

        assert response.status_code == 401


class TestViewTickets:
    """Test viewing support tickets"""

    def test_learner_can_view_own_tickets(self, client: TestClient, learner_token: str):
        """Learner should be able to view their own tickets"""
        response = client.get(
            "/support/tickets",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_admin_can_view_all_tickets(self, client: TestClient, admin_token: str):
        """Admin should be able to view all support tickets"""
        response = client.get(
            "/admin/support/tickets",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_learner_cannot_view_others_tickets(self, client: TestClient, learner_token: str):
        """Learner should not be able to view other users' tickets"""
        # Attempt to access admin endpoint
        response = client.get(
            "/admin/support/tickets",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 403


class TestUpdateTicketStatus:
    """Test updating ticket status"""

    def test_admin_can_resolve_ticket(self, client: TestClient, admin_token: str, learner_token: str):
        """Admin should be able to resolve a ticket"""
        # Create ticket as learner
        create_response = client.post(
            "/support/tickets",
            json={"title": "Test", "description": "Test issue"},
            headers={"Authorization": f"Bearer {learner_token}"}
        )
        ticket_id = create_response.json().get("id") or create_response.json().get("ticket_id")

        # Resolve as admin
        response = client.put(
            f"/admin/support/tickets/{ticket_id}/resolve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_admin_can_add_response(self, client: TestClient, admin_token: str, learner_token: str):
        """Admin should be able to add a response to a ticket"""
        # Create ticket
        create_response = client.post(
            "/support/tickets",
            json={"title": "Test", "description": "Test"},
            headers={"Authorization": f"Bearer {learner_token}"}
        )
        ticket_id = create_response.json().get("id") or create_response.json().get("ticket_id")

        # Add response
        response = client.post(
            f"/admin/support/tickets/{ticket_id}/respond",
            json={"message": "We're looking into this issue"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_learner_cannot_resolve_ticket(self, client: TestClient, learner_token: str):
        """Learner should not be able to resolve tickets (admin only)"""
        response = client.put(
            "/admin/support/tickets/1/resolve",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 403


class TestTicketFiltering:
    """Test filtering and searching tickets"""

    def test_filter_by_status(self, client: TestClient, admin_token: str):
        """Should be able to filter tickets by status"""
        response = client.get(
            "/admin/support/tickets?status=OPEN",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_filter_by_category(self, client: TestClient, admin_token: str):
        """Should be able to filter tickets by category"""
        response = client.get(
            "/admin/support/tickets?category=TECHNICAL",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_search_tickets(self, client: TestClient, admin_token: str):
        """Should be able to search tickets by keywords"""
        response = client.get(
            "/admin/support/tickets?search=pronunciation",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
