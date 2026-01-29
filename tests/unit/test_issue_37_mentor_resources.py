"""
Tests for Issue #37: Mentor Resources/Documents
Mentors upload/share Docs/Videos/Links with learners.

Run: pytest tests/unit/test_issue_37_mentor_resources.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.mentor import Mentor
from app.models.mentor_review import MentorResource


@pytest.fixture
def mentor_profile(db: Session, mentor_user: User) -> Mentor:
    """Create mentor profile for testing"""
    mentor = Mentor(
        user_id=mentor_user.user_id,
        full_name="Resource Mentor",
        bio="I share resources",
        skills="Teaching",
        verification_status="VERIFIED"
    )
    db.add(mentor)
    db.commit()
    db.refresh(mentor)
    return mentor


@pytest.fixture
def sample_resource(db: Session, mentor_profile: Mentor) -> MentorResource:
    """Create sample resource for testing"""
    resource = MentorResource(
        mentor_id=mentor_profile.user_id,  # FK to users.user_id
        title="English Grammar Guide",
        description="Comprehensive grammar reference",
        resource_type="document",
        file_url="https://cloudinary.com/example/grammar.pdf",
        is_public=False
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


class TestCreateMentorResource:
    """Test POST /mentor/resources"""
    
    def test_mentor_can_create_document_resource(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor
    ):
        """
        GIVEN: Authenticated mentor
        WHEN: Creates document resource
        THEN: Resource is created with correct type
        """
        response = client.post(
            "/mentor/resources",
            headers=mentor_auth_headers,
            json={
                "title": "Vocabulary List",
                "description": "Business English vocabulary",
                "resource_type": "document",
                "file_url": "https://storage.example.com/vocab.pdf"
            }
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["title"] == "Vocabulary List"
        assert data["resource_type"] == "document"
    
    def test_mentor_can_create_video_resource(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor
    ):
        """
        GIVEN: Authenticated mentor
        WHEN: Creates video resource
        THEN: Resource is created with video type
        """
        response = client.post(
            "/mentor/resources",
            headers=mentor_auth_headers,
            json={
                "title": "Pronunciation Tips",
                "resource_type": "video",
                "file_url": "https://youtube.com/watch?v=example"
            }
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["resource_type"] == "video"
    
    def test_mentor_can_create_link_resource(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor
    ):
        """
        GIVEN: Authenticated mentor
        WHEN: Creates link resource
        THEN: Resource is created with link type
        """
        response = client.post(
            "/mentor/resources",
            headers=mentor_auth_headers,
            json={
                "title": "Useful Website",
                "resource_type": "link",
                "file_url": "https://example-learning-site.com"
            }
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["resource_type"] == "link"
    
    def test_invalid_resource_type_rejected(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor
    ):
        """
        GIVEN: Invalid resource type
        WHEN: Mentor creates resource
        THEN: Returns 400 error
        """
        response = client.post(
            "/mentor/resources",
            headers=mentor_auth_headers,
            json={
                "title": "Invalid",
                "resource_type": "podcast",  # Not valid
                "file_url": "https://example.com"
            }
        )
        
        assert response.status_code == 400
    
    def test_learner_cannot_create_resource(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: User is learner
        WHEN: Tries to create resource
        THEN: Returns 400 (not a mentor)
        """
        response = client.post(
            "/mentor/resources",
            headers=learner_auth_headers,
            json={
                "title": "Test",
                "resource_type": "document",
                "file_url": "https://example.com"
            }
        )
        
        assert response.status_code == 400


class TestGetMentorResources:
    """Test GET /mentor/resources"""
    
    def test_mentor_can_view_own_resources(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor,
        sample_resource: MentorResource
    ):
        """
        GIVEN: Mentor has resources
        WHEN: Requests resource list
        THEN: Returns their resources
        """
        response = client.get(
            "/mentor/resources",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(r["title"] == "English Grammar Guide" for r in data)
    
    def test_resource_has_required_fields(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor,
        sample_resource: MentorResource
    ):
        """
        GIVEN: Resources exist
        WHEN: Fetched
        THEN: Each has id, title, resource_type, url
        """
        response = client.get(
            "/mentor/resources",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        resource = data[0]
        assert "resource_id" in resource
        assert "title" in resource
        assert "resource_type" in resource
        assert "file_url" in resource
        assert "created_at" in resource


class TestUpdateMentorResource:
    """Test PUT /mentor/resources/{id}"""
    
    def test_mentor_can_update_resource_title(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor,
        sample_resource: MentorResource
    ):
        """
        GIVEN: Resource exists
        WHEN: Mentor updates title
        THEN: Title is changed
        """
        response = client.put(
            f"/mentor/resources/{sample_resource.resource_id}",
            headers=mentor_auth_headers,
            json={"title": "Updated Grammar Guide"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Grammar Guide"
    
    def test_mentor_can_make_resource_public(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor,
        sample_resource: MentorResource
    ):
        """
        GIVEN: Private resource
        WHEN: Mentor sets is_public=True
        THEN: Resource becomes public
        """
        response = client.put(
            f"/mentor/resources/{sample_resource.resource_id}",
            headers=mentor_auth_headers,
            json={"is_public": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_public"] == True
    
    def test_cannot_update_other_mentor_resource(
        self,
        client: TestClient,
        db_session: Session,
        create_test_user,
        get_auth_headers,
        sample_resource: MentorResource
    ):
        """
        GIVEN: Resource belongs to another mentor
        WHEN: Different mentor tries to update
        THEN: Returns 400 or 404
        """
        # Create another mentor
        other_mentor_user = create_test_user(
            email="othermentor@test.com",
            role=UserRole.MENTOR
        )
        other_mentor = Mentor(
            user_id=other_mentor_user.user_id,
            full_name="Other Mentor",
            bio="Different mentor",
            verification_status="VERIFIED"
        )
        db_session.add(other_mentor)
        db_session.commit()
        
        headers = get_auth_headers(other_mentor_user)
        
        response = client.put(
            f"/mentor/resources/{sample_resource.resource_id}",
            headers=headers,
            json={"title": "Stolen resource"}
        )
        
        assert response.status_code in [400, 404]


class TestDeleteMentorResource:
    """Test DELETE /mentor/resources/{id}"""
    
    def test_mentor_can_delete_own_resource(
        self,
        client: TestClient,
        db_session: Session,
        mentor_auth_headers: dict,
        mentor_profile: Mentor,
        sample_resource: MentorResource
    ):
        """
        GIVEN: Resource exists
        WHEN: Mentor deletes it
        THEN: Resource is removed
        """
        response = client.delete(
            f"/mentor/resources/{sample_resource.resource_id}",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify deleted
        deleted = db_session.query(MentorResource).filter(
            MentorResource.resource_id == sample_resource.resource_id
        ).first()
        assert deleted is None
    
    def test_delete_nonexistent_returns_404(
        self,
        client: TestClient,
        mentor_auth_headers: dict,
        mentor_profile: Mentor
    ):
        """
        GIVEN: Resource ID does not exist
        WHEN: Tries to delete
        THEN: Returns 404
        """
        response = client.delete(
            "/mentor/resources/99999",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 404


class TestPublicResourcesAccess:
    """Test GET /resources/public - learners access public resources"""
    
    def test_learner_can_view_public_resources(
        self,
        client: TestClient,
        db_session: Session,
        learner_auth_headers: dict,
        mentor_profile: Mentor
    ):
        """
        GIVEN: Public resources exist
        WHEN: Learner requests public resources
        THEN: Returns only public ones
        """
        # Create public resource
        public_resource = MentorResource(
            mentor_id=mentor_profile.user_id,
            title="Free Learning Material",
            resource_type="document",
            file_url="https://example.com/free.pdf",
            is_public=True
        )
        db_session.add(public_resource)
        db_session.commit()
        
        response = client.get(
            "/resources/public",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned should be public
        for resource in data:
            assert resource["is_public"] == True
    
    def test_can_filter_public_by_type(
        self,
        client: TestClient,
        db_session: Session,
        learner_auth_headers: dict,
        mentor_profile: Mentor
    ):
        """
        GIVEN: Public resources of different types
        WHEN: Filter by type=video
        THEN: Returns only videos
        """
        # Create public video
        video = MentorResource(
            mentor_id=mentor_profile.user_id,
            title="Tutorial Video",
            resource_type="video",
            file_url="https://youtube.com/example",
            is_public=True
        )
        db_session.add(video)
        db_session.commit()
        
        response = client.get(
            "/resources/public?resource_type=video",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        for resource in data:
            assert resource["resource_type"] == "video"
