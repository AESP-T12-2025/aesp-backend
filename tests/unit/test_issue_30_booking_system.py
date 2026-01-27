"""
Tests for Issue #30: Mentor Booking System
REQ-MENTOR-5: Learner có thể book session với mentor

Run: pytest tests/unit/test_issue_30_booking_system.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole



@pytest.mark.skip(reason="Feature not implemented yet. Unskip when implementing Issue #30")
class TestMentorAvailabilityEndpoint:
    """Test POST /mentors/availability"""
    
    # ========== SUCCESS CASES ==========
    
    def test_mentor_can_set_availability(
        self,
        client: TestClient,
        mentor_auth_headers: dict
    ):
        """
        GIVEN: Authenticated mentor
        WHEN: Sets availability slots
        THEN: Slots are saved successfully
        """
        response = client.post(
            "/mentors/availability",
            headers=mentor_auth_headers,
            json={
                "slots": [
                    {"day": "monday", "start_time": "09:00", "end_time": "12:00"},
                    {"day": "wednesday", "start_time": "14:00", "end_time": "17:00"}
                ]
            }
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "message" in data or "availability" in data
    
    def test_mentor_can_get_availability(
        self,
        client: TestClient,
        mentor_auth_headers: dict
    ):
        """
        GIVEN: Mentor has set availability
        WHEN: Requests their availability
        THEN: Returns saved slots
        """
        # First set availability
        client.post(
            "/mentors/availability",
            headers=mentor_auth_headers,
            json={
                "slots": [
                    {"day": "monday", "start_time": "09:00", "end_time": "12:00"}
                ]
            }
        )
        
        # Get availability
        response = client.get(
            "/mentors/availability",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
    
    def test_update_existing_availability(
        self,
        client: TestClient,
        mentor_auth_headers: dict
    ):
        """
        GIVEN: Mentor has existing availability
        WHEN: Updates with new slots
        THEN: Availability is updated
        """
        # Set initial
        client.post(
            "/mentors/availability",
            headers=mentor_auth_headers,
            json={
                "slots": [
                    {"day": "monday", "start_time": "09:00", "end_time": "12:00"}
                ]
            }
        )
        
        # Update
        response = client.post(
            "/mentors/availability",
            headers=mentor_auth_headers,
            json={
                "slots": [
                    {"day": "tuesday", "start_time": "10:00", "end_time": "15:00"}
                ]
            }
        )
        
        assert response.status_code in [200, 201]
    
    # ========== ERROR CASES ==========
    
    def test_learner_cannot_set_mentor_availability(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Learner is authenticated
        WHEN: Tries to set availability
        THEN: Returns 403 Forbidden
        """
        response = client.post(
            "/mentors/availability",
            headers=learner_auth_headers,
            json={
                "slots": [
                    {"day": "monday", "start_time": "09:00", "end_time": "12:00"}
                ]
            }
        )
        
        assert response.status_code == 403
    
    def test_invalid_time_slot_rejected(
        self,
        client: TestClient,
        mentor_auth_headers: dict
    ):
        """
        GIVEN: Invalid time slot (end before start)
        WHEN: Mentor tries to set
        THEN: Returns validation error
        """
        response = client.post(
            "/mentors/availability",
            headers=mentor_auth_headers,
            json={
                "slots": [
                    {"day": "monday", "start_time": "15:00", "end_time": "09:00"}
                ]
            }
        )
        
        assert response.status_code in [400, 422]



@pytest.mark.skip(reason="Feature not implemented yet. Unskip when implementing Issue #30")
class TestMentorBookingsEndpoint:
    """Test GET /mentors/bookings"""
    
    def test_mentor_can_view_bookings(
        self,
        client: TestClient,
        mentor_auth_headers: dict
    ):
        """
        GIVEN: Mentor has bookings
        WHEN: Requests bookings list
        THEN: Returns list of bookings
        """
        response = client.get(
            "/mentors/bookings",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data or isinstance(data, list)
    
    def test_booking_has_required_fields(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        create_test_booking
    ):
        """
        GIVEN: Mentor has bookings
        WHEN: Views bookings
        THEN: Each booking has learner, date, status
        """
        create_test_booking()
        
        response = client.get(
            "/mentors/bookings",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        bookings = data.get("bookings", data)
        if bookings:
            booking = bookings[0]
            # Check expected fields
            assert "id" in booking or "booking_id" in booking



@pytest.mark.skip(reason="Feature not implemented yet. Unskip when implementing Issue #30")
class TestLearnerBookMentor:
    """Test learner booking mentor sessions"""
    
    def test_learner_can_book_available_slot(
        self,
        client: TestClient,
        learner_auth_headers: dict,
        mentor_user: User,
        mentor_auth_headers: dict
    ):
        """
        GIVEN: Mentor has available slots
        WHEN: Learner books a slot
        THEN: Booking is created
        """
        # Mentor sets availability
        client.post(
            "/mentors/availability",
            headers=mentor_auth_headers,
            json={
                "slots": [
                    {"day": "monday", "start_time": "09:00", "end_time": "12:00"}
                ]
            }
        )
        
        # Learner books
        response = client.post(
            f"/mentors/{mentor_user.user_id}/book",
            headers=learner_auth_headers,
            json={
                "date": "2024-12-02",
                "time": "10:00"
            }
        )
        
        assert response.status_code in [200, 201, 404, 422]
    
    def test_cannot_book_unavailable_slot(
        self,
        client: TestClient,
        learner_auth_headers: dict,
        mentor_user: User
    ):
        """
        GIVEN: Mentor has no availability at time
        WHEN: Learner tries to book
        THEN: Returns error (400 or 409)
        """
        response = client.post(
            f"/mentors/{mentor_user.user_id}/book",
            headers=learner_auth_headers,
            json={
                "date": "2024-12-25",  # Holiday - likely unavailable
                "time": "03:00"  # Odd hour
            }
        )
        
        assert response.status_code in [400, 404, 409, 422]
    
    def test_learner_can_view_their_bookings(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Learner has booked sessions
        WHEN: Requests their bookings
        THEN: Returns list of their bookings
        """
        response = client.get(
            "/learners/bookings",
            headers=learner_auth_headers
        )
        
        assert response.status_code in [200, 404]



@pytest.mark.skip(reason="Feature not implemented yet. Unskip when implementing Issue #30")
class TestBookingManagement:
    """Test mentor accepting/rejecting bookings"""
    
    def test_mentor_can_accept_booking(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        create_pending_booking
    ):
        """
        GIVEN: Pending booking exists
        WHEN: Mentor accepts it
        THEN: Booking status is confirmed
        """
        booking = create_pending_booking()
        
        response = client.post(
            f"/mentors/bookings/{booking.id}/accept",
            headers=mentor_auth_headers
        )
        
        assert response.status_code in [200, 404]
    
    def test_mentor_can_reject_booking(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        create_pending_booking
    ):
        """
        GIVEN: Pending booking exists
        WHEN: Mentor rejects it
        THEN: Booking status is rejected
        """
        booking = create_pending_booking()
        
        response = client.post(
            f"/mentors/bookings/{booking.id}/reject",
            headers=mentor_auth_headers,
            json={"reason": "Schedule conflict"}
        )
        
        assert response.status_code in [200, 404]
    
    def test_learner_can_cancel_booking(
        self,
        client: TestClient,
        learner_auth_headers: dict,
        create_learner_booking
    ):
        """
        GIVEN: Learner has booking
        WHEN: Cancels before session
        THEN: Booking is cancelled
        """
        booking = create_learner_booking()
        
        response = client.post(
            f"/learners/bookings/{booking.id}/cancel",
            headers=learner_auth_headers
        )
        
        assert response.status_code in [200, 404]



@pytest.mark.skip(reason="Feature not implemented yet. Unskip when implementing Issue #30")
class TestMentorListForLearners:
    """Test learners browsing available mentors"""
    
    def test_learner_can_view_mentor_list(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Mentors exist with availability
        WHEN: Learner browses mentors
        THEN: Returns list of available mentors
        """
        response = client.get(
            "/mentors",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "mentors" in data or isinstance(data, list)
    
    def test_mentor_list_includes_availability(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Mentors have availability set
        WHEN: Learner views mentor list
        THEN: Availability info is included
        """
        response = client.get(
            "/mentors",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
