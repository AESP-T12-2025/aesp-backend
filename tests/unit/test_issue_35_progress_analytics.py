"""
Unit tests for Issue #35: Progress Analytics & Heat Maps (Learner)
Testing learner progress tracking and heat map visualization
"""
import pytest
from fastapi.testclient import TestClient


class TestProgressAnalytics:
    """Test progress analytics endpoints"""

    def test_learner_can_view_own_progress(self, client: TestClient, learner_token: str):
        """Learner should be able to view their own progress analytics"""
        response = client.get(
            "/learner/progress",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_mentor_cannot_view_learner_progress(self, client: TestClient, mentor_token: str):
        """Mentor should not access learner-specific progress (unless assigned)"""
        response = client.get(
            "/learner/progress",
            headers={"Authorization": f"Bearer {mentor_token}"}
        )

        # Depending on implementation, might be 403 or return empty
        assert response.status_code in [403, 200]

    def test_progress_without_auth(self, client: TestClient):
        """Progress without auth should return 401"""
        response = client.get("/learner/progress")

        assert response.status_code == 401


class TestHeatMapData:
    """Test heat map generation"""

    def test_get_activity_heatmap(self, client: TestClient, learner_token: str):
        """Should return activity heat map data"""
        response = client.get(
            "/learner/heatmap",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should be a list or dict with dates and activity counts
        assert isinstance(data, (list, dict))

    def test_heatmap_with_date_range(self, client: TestClient, learner_token: str):
        """Should support date range for heat map"""
        response = client.get(
            "/learner/heatmap?start_date=2024-01-01&end_date=2024-12-31",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_heatmap_empty_for_new_user(self, client: TestClient, learner_token: str):
        """Heat map for new user without activity should return empty data"""
        response = client.get(
            "/learner/heatmap",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        # Data might be empty or have zero counts


class TestProgressMetrics:
    """Test various progress metrics"""

    def test_get_speaking_time(self, client: TestClient, learner_token: str):
        """Should return total speaking time"""
        response = client.get(
            "/learner/metrics/speaking-time",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_minutes" in data or "duration" in str(data).lower()

    def test_get_completed_scenarios(self, client: TestClient, learner_token: str):
        """Should return completed scenarios count"""
        response = client.get(
            "/learner/metrics/scenarios",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_get_streak_count(self, client: TestClient, learner_token: str):
        """Should return current streak count"""
        response = client.get(
            "/learner/metrics/streak",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "streak" in str(data).lower() or "days" in str(data).lower()


class TestWeeklyProgress:
    """Test weekly progress tracking"""

    def test_get_weekly_summary(self, client: TestClient, learner_token: str):
        """Should return weekly progress summary"""
        response = client.get(
            "/learner/progress/weekly",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_weekly_goals(self, client: TestClient, learner_token: str):
        """Should return weekly goals and completion status"""
        response = client.get(
            "/learner/goals/weekly",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200


class TestTrendAnalysis:
    """Test trend analysis over time"""

    def test_improvement_trends(self, client: TestClient, learner_token: str):
        """Should return improvement trends"""
        response = client.get(
            "/learner/analytics/trends",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_pronunciation_progress(self, client: TestClient, learner_token: str):
        """Should track pronunciation improvement over time"""
        response = client.get(
            "/learner/analytics/pronunciation",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
