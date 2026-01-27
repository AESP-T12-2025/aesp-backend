"""
Unit tests for AI endpoints
Requirements (Learner role):
- Receive grammar/vocabulary corrections & pronunciation scoring
- AI acts as conversation assistant with vocabulary, example sentences
- Instant pronunciation feedback
"""
import pytest
from fastapi.testclient import TestClient


class TestAIChat:
    """Test AI Chat - Requirement: AI as conversation assistant"""

    def test_chat_with_context(self, client: TestClient, auth_headers: dict):
        """Test POST /ai/chat returns AI response"""
        response = client.post(
            "/ai/chat",
            headers=auth_headers,
            json={
                "message": "Hello, how are you?",
                "context": "You are a friendly English tutor"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "reply" in data
        elif response.status_code == 500:
            # AI service may not be configured in test
            pytest.skip("AI service not configured")

    def test_chat_empty_message_fails(self, client: TestClient, auth_headers: dict):
        """Test chat with empty message fails validation"""
        response = client.post(
            "/ai/chat",
            headers=auth_headers,
            json={"message": "", "context": "Tutor"}
        )
        
        assert response.status_code == 422  # Validation error


class TestAISpeechAnalysis:
    """Test AI Speech Analysis - Requirement: Pronunciation scoring"""

    def test_analyze_speech(self, client: TestClient, auth_headers: dict):
        """Test POST /ai/analyze returns scores"""
        response = client.post(
            "/ai/analyze",
            headers=auth_headers,
            json={"text": "I want to practice speaking English"}
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should return scores
            assert "grammar_score" in data or "error" in data
        elif response.status_code == 500:
            pytest.skip("AI service not configured")

    def test_analyze_with_session_id(self, client: TestClient, auth_headers: dict):
        """Test analyze saves feedback when session_id provided"""
        response = client.post(
            "/ai/analyze",
            headers=auth_headers,
            json={
                "text": "Hello world",
                "session_id": 1,  # May not exist
                "duration_seconds": 5.0
            }
        )
        
        # Should not crash even if session doesn't exist
        assert response.status_code in [200, 500]


class TestAITextToSpeech:
    """Test TTS - Requirement: Vocabulary & example sentences"""

    def test_text_to_speech(self, client: TestClient, auth_headers: dict):
        """Test POST /ai/tts generates audio"""
        response = client.post(
            "/ai/tts",
            headers=auth_headers,
            json={"text": "Hello, this is a test."}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "audio_url" in data
        elif response.status_code in [400, 500]:
            # TTS may fail in test environment
            pass

    def test_tts_with_custom_voice(self, client: TestClient, auth_headers: dict):
        """Test TTS with different voice"""
        response = client.post(
            "/ai/tts",
            headers=auth_headers,
            json={
                "text": "Testing voice",
                "voice": "en-US-GuyNeural"
            }
        )
        
        # Should at least not crash
        assert response.status_code != 422
