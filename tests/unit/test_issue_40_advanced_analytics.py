"""
Unit tests for Issue #40: Advanced Analytics & Daily Stats (Learner)
Testing advanced analytics features and daily statistics
"""
import pytest
from fastapi.testclient import TestClient


class TestDailyStatistics:
    """Test daily statistics tracking"""

    def test_get_today_stats(self, client: TestClient, learner_token: str):
        """Should return today's statistics"""
        response = client.get(
            "/learner/stats/daily",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_specific_date_stats(self, client: TestClient, learner_token: str):
        """Should return statistics for a specific date"""
        response = client.get(
            "/learner/stats/daily?date=2024-01-15",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_daily_stats_history(self, client: TestClient, learner_token: str):
        """Should return daily stats for a date range"""
        response = client.get(
            "/learner/stats/daily/history?start_date=2024-01-01&end_date=2024-01-31",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAdvancedAnalytics:
    """Test advanced analytics features"""

    def test_pronunciation_breakdown(self, client: TestClient, learner_token: str):
        """Should provide detailed pronunciation analytics"""
        response = client.get(
            "/learner/analytics/pronunciation",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_vocabulary_retention_analysis(self, client: TestClient, learner_token: str):
        """Should analyze vocabulary retention rates"""
        response = client.get(
            "/learner/analytics/vocabulary/retention",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_fluency_trends(self, client: TestClient, learner_token: str):
        """Should track fluency improvement trends"""
        response = client.get(
            "/learner/analytics/fluency",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_error_pattern_analysis(self, client: TestClient, learner_token: str):
        """Should identify common error patterns"""
        response = client.get(
            "/learner/analytics/errors",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200


class TestComparisonAnalytics:
    """Test comparison and benchmarking"""

    def test_compare_with_average(self, client: TestClient, learner_token: str):
        """Should compare learner's progress with platform average"""
        response = client.get(
            "/learner/analytics/compare/average",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_compare_with_similar_learners(self, client: TestClient, learner_token: str):
        """Should compare with learners at similar proficiency level"""
        response = client.get(
            "/learner/analytics/compare/peers",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200


class TestGoalTracking:
    """Test goal tracking and recommendations"""

    def test_get_personalized_recommendations(self, client: TestClient, learner_token: str):
        """Should provide personalized improvement recommendations"""
        response = client.get(
            "/learner/analytics/recommendations",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_set_weekly_goal(self, client: TestClient, learner_token: str):
        """Should be able to set weekly practice goals"""
        response = client.post(
            "/learner/goals",
            json={
                "type": "WEEKLY",
                "target_minutes": 300,
                "target_scenarios": 10
            },
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_goal_progress_tracking(self, client: TestClient, learner_token: str):
        """Should track progress towards set goals"""
        response = client.get(
            "/learner/goals/progress",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200


class TestPerformanceMetrics:
    """Test advanced performance metrics"""

    def test_speaking_speed_analysis(self, client: TestClient, learner_token: str):
        """Should analyze speaking speed trends"""
        response = client.get(
            "/learner/analytics/speaking-speed",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_confidence_score_trends(self, client: TestClient, learner_token: str):
        """Should track confidence score over time"""
        response = client.get(
            "/learner/analytics/confidence",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_topic_difficulty_match(self, client: TestClient, learner_token: str):
        """Should analyze performance vs topic difficulty"""
        response = client.get(
            "/learner/analytics/difficulty-match",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200


class TestExportAnalytics:
    """Test exporting analytics data"""

    def test_export_full_analytics(self, client: TestClient, learner_token: str):
        """Should be able to export complete analytics data"""
        response = client.get(
            "/learner/analytics/export?format=json",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code == 200

    def test_export_specific_metric(self, client: TestClient, learner_token: str):
        """Should be able to export specific metric data"""
        response = client.get(
            "/learner/analytics/export/pronunciation?format=csv",
            headers={"Authorization": f"Bearer {learner_token}"}
        )

        assert response.status_code in [200, 501]
