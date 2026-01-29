"""
Tests for Issue #30: Mentor Booking System
REQ-MENTOR-5: Mentor set availability, learner book session

Run: pytest tests/unit/test_issue_30_booking_system.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.user import User, UserRole
from app.models.mentor import Mentor, AvailabilitySlot, Booking, BookingStatus


@pytest.fixture
def mentor_profile(db: Session, mentor_user: User) -> Mentor:
    """Create mentor profile for testing"""
    mentor = Mentor(
        user_id=mentor_user.user_id,
        full_name="Test Mentor",
        bio="Experienced English teacher",
        skills="Speaking,Grammar,Pronunciation",
        verification_status="VERIFIED"
    )
    db.add(mentor)
    db.commit()
    db.refresh(mentor)
    return mentor


@pytest.fixture
def availability_slot(db: Session, mentor_profile: Mentor) -> AvailabilitySlot:
    """Create an available slot for testing"""
    # Create slot for tomorrow at 10:00-11:00
    tomorrow = datetime.now() + timedelta(days=1)
    start = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    end = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)
    
    slot = AvailabilitySlot(
        mentor_id=mentor_profile.mentor_id,
        start_time=start,
        end_time=end,
        status=BookingStatus.AVAILABLE
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


class TestMentorAvailabilityEndpoints:
    """Test POST/GET /mentors/availability"""
    
    def test_mentor_can_set_availability(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor
    ):
        """
        GIVEN: Authenticated mentor with profile
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
        assert "message" in data
        assert data.get("slots_created", 0) >= 2
    
    def test_mentor_can_get_availability(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor,
        availability_slot: AvailabilitySlot
    ):
        """
        GIVEN: Mentor has set availability
        WHEN: Requests their availability
        THEN: Returns saved slots
        """
        response = client.get(
            "/mentors/availability",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "availability" in data
        assert isinstance(data["availability"], list)
    
    def test_invalid_time_slot_rejected(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor
    ):
        """
        GIVEN: Invalid time slot (end before start)
        WHEN: Mentor tries to set
        THEN: Returns 422 validation error
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
        
        assert response.status_code == 422
    
    def test_learner_cannot_set_availability(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: User is a learner (not mentor)
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


class TestMentorBookingsEndpoint:
    """Test GET /mentors/bookings"""
    
    def test_mentor_can_view_bookings(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor
    ):
        """
        GIVEN: Mentor has profile
        WHEN: Requests bookings list
        THEN: Returns list of bookings
        """
        response = client.get(
            "/mentors/bookings",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        assert isinstance(data["bookings"], list)
    
    def test_booking_has_required_fields(
        self,
        client: TestClient,
        db_session: Session,
        mentor_auth_headers: dict,
        mentor_profile: Mentor,
        availability_slot: AvailabilitySlot,
        learner_user: User
    ):
        """
        GIVEN: Mentor has bookings
        WHEN: Views bookings
        THEN: Each booking has booking_id, learner_id, status
        """
        # Create a booking
        booking = Booking(
            slot_id=availability_slot.slot_id,
            learner_id=learner_user.user_id,
            status="PENDING"
        )
        db_session.add(booking)
        availability_slot.status = BookingStatus.BOOKED
        db_session.commit()
        
        response = client.get(
            "/mentors/bookings",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["bookings"]:
            booking_data = data["bookings"][0]
            assert "booking_id" in booking_data
            assert "learner_id" in booking_data
            assert "status" in booking_data


class TestLearnerBookMentor:
    """Test POST /mentors/{id}/book - learner books mentor"""
    
    def test_learner_can_book_available_slot(
        self,
        client: TestClient,
        learner_auth_headers: dict,
        mentor_profile: Mentor,
        availability_slot: AvailabilitySlot
    ):
        """
        GIVEN: Mentor has available slot
        WHEN: Learner books that slot
        THEN: Booking is created
        """
        # Get slot date/time
        slot_date = availability_slot.start_time.strftime("%Y-%m-%d")
        slot_time = availability_slot.start_time.strftime("%H:%M")
        
        response = client.post(
            f"/mentors/{mentor_profile.mentor_id}/book",
            headers=learner_auth_headers,
            json={
                "date": slot_date,
                "time": slot_time
            }
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "booking_id" in data
    
    def test_cannot_book_unavailable_slot(
        self,
        client: TestClient,
        learner_auth_headers: dict,
        mentor_profile: Mentor
    ):
        """
        GIVEN: No available slot at requested time
        WHEN: Learner tries to book
        THEN: Returns 400 error
        """
        response = client.post(
            f"/mentors/{mentor_profile.mentor_id}/book",
            headers=learner_auth_headers,
            json={
                "date": "2000-01-01",  # Past date with no slots
                "time": "03:00"
            }
        )
        
        assert response.status_code == 400
    
    def test_cannot_book_nonexistent_mentor(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Mentor ID does not exist
        WHEN: Learner tries to book
        THEN: Returns 404
        """
        response = client.post(
            "/mentors/99999/book",
            headers=learner_auth_headers,
            json={
                "date": "2026-01-30",
                "time": "10:00"
            }
        )
        
        assert response.status_code == 404


class TestBookingManagement:
    """Test accept/reject booking endpoints"""
    
    def test_mentor_can_accept_booking(
        self,
        client: TestClient,
        db_session: Session,
        mentor_auth_headers: dict,
        mentor_profile: Mentor,
        availability_slot: AvailabilitySlot,
        learner_user: User
    ):
        """
        GIVEN: Pending booking exists
        WHEN: Mentor accepts it
        THEN: Booking status is CONFIRMED
        """
        booking = Booking(
            slot_id=availability_slot.slot_id,
            learner_id=learner_user.user_id,
            status="PENDING"
        )
        db_session.add(booking)
        db_session.commit()
        db_session.refresh(booking)
        
        response = client.post(
            f"/mentors/bookings/{booking.booking_id}/accept",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify in database
        db_session.refresh(booking)
        assert booking.status == "CONFIRMED"
    
    def test_mentor_can_reject_booking(
        self,
        client: TestClient,
        db_session: Session,
        mentor_auth_headers: dict,
        mentor_profile: Mentor,
        availability_slot: AvailabilitySlot,
        learner_user: User
    ):
        """
        GIVEN: Pending booking exists
        WHEN: Mentor rejects it
        THEN: Booking status is REJECTED, slot is released
        """
        booking = Booking(
            slot_id=availability_slot.slot_id,
            learner_id=learner_user.user_id,
            status="PENDING"
        )
        db_session.add(booking)
        availability_slot.status = BookingStatus.BOOKED
        db_session.commit()
        db_session.refresh(booking)
        
        response = client.post(
            f"/mentors/bookings/{booking.booking_id}/reject",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify booking rejected
        db_session.refresh(booking)
        assert booking.status == "REJECTED"
        
        # Verify slot is available again
        db_session.refresh(availability_slot)
        assert availability_slot.status == BookingStatus.AVAILABLE


class TestLearnerBookingsManagement:
    """Test learner booking viewing and cancellation"""
    
    def test_learner_can_view_their_bookings(
        self,
        client: TestClient,
        db_session: Session,
        learner_auth_headers: dict,
        learner_user: User,
        availability_slot: AvailabilitySlot
    ):
        """
        GIVEN: Learner has booked sessions
        WHEN: Requests their bookings
        THEN: Returns list of their bookings
        """
        booking = Booking(
            slot_id=availability_slot.slot_id,
            learner_id=learner_user.user_id,
            status="CONFIRMED"
        )
        db_session.add(booking)
        db_session.commit()
        
        response = client.get(
            "/learners/bookings",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
    
    def test_learner_can_cancel_booking(
        self,
        client: TestClient,
        db_session: Session,
        learner_auth_headers: dict,
        learner_user: User,
        availability_slot: AvailabilitySlot
    ):
        """
        GIVEN: Learner has booking
        WHEN: Cancels it
        THEN: Booking is cancelled, slot released
        """
        booking = Booking(
            slot_id=availability_slot.slot_id,
            learner_id=learner_user.user_id,
            status="CONFIRMED"
        )
        db_session.add(booking)
        availability_slot.status = BookingStatus.BOOKED
        db_session.commit()
        db_session.refresh(booking)
        
        response = client.post(
            f"/learners/bookings/{booking.booking_id}/cancel",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        
        db_session.refresh(booking)
        assert booking.status == "CANCELLED"
