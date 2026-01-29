"""
Tests for Issue #33: Support Services/Tickets
Learners create support tickets, Admins view and resolve.

Run: pytest tests/unit/test_issue_33_support_tickets.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.support import SupportTicket


@pytest.fixture
def sample_ticket(db: Session, learner_user: User) -> SupportTicket:
    """Create a sample support ticket for testing"""
    ticket = SupportTicket(
        user_id=learner_user.user_id,
        title="Test Issue",
        description="I need help with my account",
        status="OPEN",
        priority="MEDIUM"
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


class TestLearnerCreateTicket:
    """Test POST /support/tickets - Learner creates ticket"""
    
    def test_learner_can_create_support_ticket(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Authenticated learner
        WHEN: Creates support ticket
        THEN: Ticket is created successfully
        """
        response = client.post(
            "/support/tickets",
            headers=learner_auth_headers,
            json={
                "title": "Cannot access lesson",
                "description": "Getting error when trying to start lesson 5"
            }
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "ticket_id" in data or "id" in data
    
    def test_ticket_has_open_status_by_default(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: New ticket created
        WHEN: Ticket is returned
        THEN: Status is OPEN
        """
        response = client.post(
            "/support/tickets",
            headers=learner_auth_headers,
            json={
                "title": "Payment issue",
                "description": "My payment did not go through"
            }
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("status") == "OPEN"
    
    def test_unauthenticated_cannot_create_ticket(
        self,
        client: TestClient
    ):
        """
        GIVEN: No authentication
        WHEN: Tries to create ticket
        THEN: Returns 401
        """
        response = client.post(
            "/support/tickets",
            json={
                "title": "Test",
                "description": "Test description"
            }
        )
        
        assert response.status_code == 401
    
    def test_empty_title_handled(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Empty title
        WHEN: Tries to create ticket
        THEN: Either rejected (422/400) or handled gracefully
        """
        response = client.post(
            "/support/tickets",
            headers=learner_auth_headers,
            json={
                "title": "",
                "description": "Test description"
            }
        )
        
        # API may accept empty titles or reject - either is valid behavior
        assert response.status_code in [200, 201, 400, 422]


class TestAdminViewTickets:
    """Test GET /admin/support/tickets - Admin views all tickets"""
    
    def test_admin_can_view_all_tickets(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        sample_ticket: SupportTicket
    ):
        """
        GIVEN: Tickets exist in system
        WHEN: Admin requests all tickets
        THEN: Returns list of all tickets
        """
        response = client.get(
            "/admin/support/tickets",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_admin_can_filter_by_status(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        sample_ticket: SupportTicket
    ):
        """
        GIVEN: Tickets with various statuses
        WHEN: Admin filters by status=OPEN
        THEN: Returns only OPEN tickets
        """
        response = client.get(
            "/admin/support/tickets?status=OPEN",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        for ticket in data:
            assert ticket["status"] == "OPEN"
    
    def test_learner_cannot_access_admin_tickets(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: User is learner (not admin)
        WHEN: Tries to access admin endpoint
        THEN: Returns 403 Forbidden
        """
        response = client.get(
            "/admin/support/tickets",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 403
    
    def test_mentor_cannot_access_admin_tickets(
        self,
        client: TestClient,
        mentor_auth_headers: dict
    ):
        """
        GIVEN: User is mentor (not admin)
        WHEN: Tries to access admin endpoint  
        THEN: Returns 403 Forbidden
        """
        response = client.get(
            "/admin/support/tickets",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 403


class TestAdminUpdateTicket:
    """Test PATCH /admin/support/tickets/{id} - Admin updates ticket"""
    
    def test_admin_can_update_status(
        self,
        client: TestClient,
        db_session: Session,
        admin_auth_headers: dict,
        sample_ticket: SupportTicket
    ):
        """
        GIVEN: OPEN ticket exists
        WHEN: Admin updates to IN_PROGRESS
        THEN: Status is updated
        """
        response = client.patch(
            f"/admin/support/tickets/{sample_ticket.ticket_id}",
            headers=admin_auth_headers,
            json={"status": "IN_PROGRESS"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"
    
    def test_admin_can_update_priority(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        sample_ticket: SupportTicket
    ):
        """
        GIVEN: Ticket with MEDIUM priority
        WHEN: Admin updates to HIGH
        THEN: Priority is updated
        """
        response = client.patch(
            f"/admin/support/tickets/{sample_ticket.ticket_id}",
            headers=admin_auth_headers,
            json={"priority": "HIGH"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "HIGH"
    
    def test_admin_can_resolve_ticket(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        sample_ticket: SupportTicket
    ):
        """
        GIVEN: OPEN ticket
        WHEN: Admin resolves it
        THEN: Status is RESOLVED
        """
        response = client.patch(
            f"/admin/support/tickets/{sample_ticket.ticket_id}",
            headers=admin_auth_headers,
            json={"status": "RESOLVED"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RESOLVED"
    
    def test_invalid_status_rejected(
        self,
        client: TestClient,
        admin_auth_headers: dict,
        sample_ticket: SupportTicket
    ):
        """
        GIVEN: Invalid status value
        WHEN: Admin tries to update
        THEN: Returns 400 error
        """
        response = client.patch(
            f"/admin/support/tickets/{sample_ticket.ticket_id}",
            headers=admin_auth_headers,
            json={"status": "INVALID_STATUS"}
        )
        
        assert response.status_code == 400
    
    def test_update_nonexistent_ticket_returns_404(
        self,
        client: TestClient,
        admin_auth_headers: dict
    ):
        """
        GIVEN: Ticket ID does not exist
        WHEN: Admin tries to update
        THEN: Returns 404
        """
        response = client.patch(
            "/admin/support/tickets/99999",
            headers=admin_auth_headers,
            json={"status": "RESOLVED"}
        )
        
        assert response.status_code == 404


class TestTicketStatusFlow:
    """Test valid status transitions"""
    
    def test_complete_ticket_lifecycle(
        self,
        client: TestClient,
        db_session: Session,
        learner_auth_headers: dict,
        admin_auth_headers: dict
    ):
        """
        GIVEN: New ticket
        WHEN: Ticket goes through OPEN → IN_PROGRESS → RESOLVED → CLOSED
        THEN: All transitions are valid
        """
        # 1. Learner creates ticket
        create_response = client.post(
            "/support/tickets",
            headers=learner_auth_headers,
            json={
                "title": "Complete lifecycle test",
                "description": "Testing full ticket flow"
            }
        )
        assert create_response.status_code in [200, 201]
        ticket_id = create_response.json().get("ticket_id") or create_response.json().get("id")
        
        # 2. Admin moves to IN_PROGRESS
        progress_response = client.patch(
            f"/admin/support/tickets/{ticket_id}",
            headers=admin_auth_headers,
            json={"status": "IN_PROGRESS"}
        )
        assert progress_response.status_code == 200
        
        # 3. Admin resolves
        resolve_response = client.patch(
            f"/admin/support/tickets/{ticket_id}",
            headers=admin_auth_headers,
            json={"status": "RESOLVED"}
        )
        assert resolve_response.status_code == 200
        
        # 4. Admin closes
        close_response = client.patch(
            f"/admin/support/tickets/{ticket_id}",
            headers=admin_auth_headers,
            json={"status": "CLOSED"}
        )
        assert close_response.status_code == 200
        assert close_response.json()["status"] == "CLOSED"
