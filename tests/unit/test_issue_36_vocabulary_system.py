"""
Unit tests for Issue #36: Vocabulary System (Learner/Mentor)
Testing vocabulary management and learning features
"""
import pytest
from fastapi.testclient import TestClient


class TestVocabularyRetrieval:
    """Test retrieving vocabulary"""

    def test_get_scenario_vocabulary(self, client: TestClient, learner_token: str):
        """Should return vocabulary for a specific scenario"""
        response = client.get(
            "/vocabulary/scenario/1",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code in [200, 404]  # 404 if scenario doesn't exist

    def test_get_all_vocabulary(self, client: TestClient, learner_token: str):
        """Should return all vocabulary items"""
        response = client.get(
            "/vocabulary",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_vocabulary_without_auth(self, client: TestClient):
        """Accessing vocabulary without auth should return 401"""
        response = client.get("/vocabulary")

        assert response.status_code == 401


class TestPersonalCollection:
    """Test personal vocabulary collection"""

    def test_add_to_personal_collection(self, client: TestClient, learner_token: str):
        """Learner should be able to add vocab to personal collection"""
        response = client.post(
            "/vocabulary/personal",
            json={
                "word": "ubiquitous",
                "definition": "present everywhere",
                "example": "Smartphones are ubiquitous in modern society"
            },
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_get_personal_collection(self, client: TestClient, learner_token: str):
        """Should return learner's personal vocabulary collection"""
        response = client.get(
            "/vocabulary/personal",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_remove_from_collection(self, client: TestClient, learner_token: str):
        """Should be able to remove vocab from personal collection"""
        # First add
        add_response = client.post(
            "/vocabulary/personal",
            json={"word": "test", "definition": "test"},
            headers={"Authorization": f"Bearer {learner_token}"}
        )
        vocab_id = add_response.json().get("id")

        # Then remove
        response = client.delete(
            f"/vocabulary/personal/{vocab_id}",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200


class TestVocabularyQuiz:
    """Test vocabulary quiz/practice"""

    def test_get_quiz_questions(self, client: TestClient, learner_token: str):
        """Should generate vocabulary quiz questions"""
        response = client.get(
            "/vocabulary/quiz",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_submit_quiz_answers(self, client: TestClient, learner_token: str):
        """Should be able to submit quiz answers and get results"""
        response = client.post(
            "/vocabulary/quiz/submit",
            json={
                "answers": [
                    {"question_id": 1, "selected_answer": "A"}
                ]
            },
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "score" in data or "correct" in str(data).lower()


class TestMentorVocabularySuggestions:
    """Test mentor vocabulary suggestions"""

    def test_mentor_can_suggest_vocabulary(self, client: TestClient, mentor_token: str):
        """Mentor should be able to suggest vocabulary items"""
        response = client.post(
            "/mentor/vocabulary/suggest",
            json={
                "topic_id": 1,
                "word": "collaborate",
                "definition": "work jointly with others",
                "example": "Let's collaborate on this project"
            },
            headers={"Authorization": f"Bearer {mentor_token}"}
        )

        assert response.status_code == 200

    def test_learner_cannot_suggest_vocabulary(self, client: TestClient, learner_token: str):
        """Learner should not be able to suggest vocab (mentor only)"""
        response = client.post(
            "/mentor/vocabulary/suggest",
            json={"word": "test", "definition": "test"},
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 403


class TestVocabularySearch:
    """Test vocabulary search functionality"""

    def test_search_vocabulary(self, client: TestClient, learner_token: str):
        """Should be able to search vocabulary by keyword"""
        response = client.get(
            "/vocabulary/search?q=collaborate",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_filter_by_difficulty(self, client: TestClient, learner_token: str):
        """Should be able to filter vocabulary by difficulty"""
        response = client.get(
            "/vocabulary?difficulty=INTERMEDIATE",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
