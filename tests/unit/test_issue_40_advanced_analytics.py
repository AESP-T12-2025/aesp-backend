"""
Tests for Issue #40: Advanced Analytics & Daily Stats
Deeper insights (time of day, retention rate), daily stats aggregation.

Run: pytest tests/unit/test_issue_40_advanced_analytics.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.user import User, UserRole
from app.models.content import SpeakingSession
from app.models.gamification import UserDailyStats
from app.models.content import Category, Topic, Scenario


@pytest.fixture
def test_scenario(db: Session) -> Scenario:
    """Create a test scenario for analytics fixtures"""
    category = Category(name="Test Category", description="For testing")
    db.add(category)
    db.commit()
    db.refresh(category)
    
    topic = Topic(
        category_id=category.category_id,
        name="Test Topic",
        description="For testing"
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    
    scenario = Scenario(
        topic_id=topic.topic_id,
        title="Test Scenario",
        difficulty_level="BEGINNER"
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@pytest.fixture
def user_sessions(db: Session, learner_user: User, test_scenario: Scenario) -> list:
    """Create sample speaking sessions for analytics"""
    sessions = []
    base_time = datetime.now() - timedelta(days=3)
    
    # Sessions at different times of day
    for i in range(5):
        session_time = base_time + timedelta(hours=i * 4)
        session = SpeakingSession(
            user_id=learner_user.user_id,
            scenario_id=test_scenario.scenario_id,
            start_time=session_time
        )
        db.add(session)
        sessions.append(session)
    
    db.commit()
    return sessions


@pytest.fixture
def user_daily_stats(db: Session, learner_user: User) -> UserDailyStats:
    """Create daily stats for analytics"""
    today = datetime.now().date()
    stats = UserDailyStats(
        user_id=learner_user.user_id,
        date=today,
        speaking_duration_seconds=1800,  # 30 minutes
        words_learned=25,
        login_streak_current=7
    )
    db.add(stats)
    db.commit()
    db.refresh(stats)
    return stats


class TestAdvancedAnalyticsEndpoint:
    """Test GET /analytics/advanced"""
    
    def test_advanced_analytics_returns_time_of_day(
        self,
        client: TestClient,
        learner_auth_headers: dict,
        user_sessions: list
    ):
        """
        GIVEN: User has speaking sessions
        WHEN: Requests advanced analytics
        THEN: Returns time of day analysis
        """
        response = client.get(
            "/analytics/advanced",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timeOfDay" in data
        assert "distribution" in data["timeOfDay"]
        assert "peakHours" in data["timeOfDay"]
        assert "preference" in data["timeOfDay"]
    
    def test_time_distribution_has_24_hours(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: User requests analytics
        WHEN: Time distribution returned
        THEN: Contains 24 hour slots
        """
        response = client.get(
            "/analytics/advanced",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        distribution = data["timeOfDay"]["distribution"]
        assert len(distribution) == 24
    
    def test_advanced_analytics_returns_retention_rate(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: User has sessions
        WHEN: Requests advanced analytics
        THEN: Returns retention rate data
        """
        response = client.get(
            "/analytics/advanced",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "retention" in data
        retention = data["retention"]
        assert "thisWeek" in retention
        assert "lastWeek" in retention
        assert "ratePercent" in retention
        assert "trend" in retention
    
    def test_retention_trend_is_valid(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Retention data calculated
        WHEN: Trend returned
        THEN: Is one of: improving, declining, stable
        """
        response = client.get(
            "/analytics/advanced",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        valid_trends = ["improving", "declining", "stable"]
        assert data["retention"]["trend"] in valid_trends
    
    def test_advanced_analytics_returns_weekly_trend(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: User has sessions over weeks
        WHEN: Requests analytics
        THEN: Returns weekly trend data
        """
        response = client.get(
            "/analytics/advanced",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "weeklyTrend" in data
        assert isinstance(data["weeklyTrend"], list)
        # Should have 4 weeks data
        assert len(data["weeklyTrend"]) == 4
    
    def test_preference_is_valid_time_category(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Time of day analysis
        WHEN: Preference returned
        THEN: Is one of: morning, afternoon, evening, night
        """
        response = client.get(
            "/analytics/advanced",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        valid_preferences = ["morning", "afternoon", "evening", "night"]
        assert data["timeOfDay"]["preference"] in valid_preferences


class TestDailyStatsEndpoint:
    """Test GET /analytics/daily-stats"""
    
    def test_daily_stats_for_today(
        self,
        client: TestClient,
        learner_auth_headers: dict,
        user_daily_stats: UserDailyStats
    ):
        """
        GIVEN: User has stats for today
        WHEN: Requests daily stats (no date param)
        THEN: Returns today's stats
        """
        response = client.get(
            "/analytics/daily-stats",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "date" in data
        assert "speakingMinutes" in data
        assert "wordsLearned" in data
        assert "sessionsCount" in data
    
    def test_daily_stats_for_specific_date(
        self,
        client: TestClient,
        db_session: Session,
        learner_auth_headers: dict,
        learner_user: User
    ):
        """
        GIVEN: Stats for specific date
        WHEN: Requests that date
        THEN: Returns stats for that date
        """
        # Create stats for yesterday
        yesterday = (datetime.now() - timedelta(days=1)).date()
        stats = UserDailyStats(
            user_id=learner_user.user_id,
            date=yesterday,
            speaking_duration_seconds=600,
            words_learned=10
        )
        db_session.add(stats)
        db_session.commit()
        
        response = client.get(
            f"/analytics/daily-stats?date={yesterday.isoformat()}",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == yesterday.isoformat()
    
    def test_daily_stats_returns_zero_for_no_data(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: No stats for date
        WHEN: Requests that date
        THEN: Returns zeroed stats
        """
        old_date = "2020-01-01"
        
        response = client.get(
            f"/analytics/daily-stats?date={old_date}",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["speakingMinutes"] == 0
        assert data["wordsLearned"] == 0
    
    def test_daily_stats_includes_scores(
        self,
        client: TestClient,
        learner_auth_headers: dict,
        user_daily_stats: UserDailyStats
    ):
        """
        GIVEN: User has daily stats
        WHEN: Requests stats
        THEN: Includes grammar, pronunciation, fluency scores
        """
        response = client.get(
            "/analytics/daily-stats",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "scores" in data
        scores = data["scores"]
        assert "grammar" in scores
        assert "pronunciation" in scores
        assert "fluency" in scores


class TestSystemStatsEndpoint:
    """Test GET /analytics/system-stats (Admin only)"""
    
    def test_admin_can_view_system_stats(
        self,
        client: TestClient,
        admin_auth_headers: dict
    ):
        """
        GIVEN: User is admin
        WHEN: Requests system stats
        THEN: Returns system-wide analytics
        """
        response = client.get(
            "/analytics/system-stats",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "users" in data
        assert "sessions" in data
    
    def test_system_stats_users_section(
        self,
        client: TestClient,
        admin_auth_headers: dict
    ):
        """
        GIVEN: Admin requests system stats
        WHEN: Data returned
        THEN: Users section has total and active count
        """
        response = client.get(
            "/analytics/system-stats",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        users = data["users"]
        assert "total" in users
        assert "active7d" in users
    
    def test_system_stats_sessions_section(
        self,
        client: TestClient,
        admin_auth_headers: dict
    ):
        """
        GIVEN: Admin requests system stats
        WHEN: Data returned
        THEN: Sessions section has counts and avg duration
        """
        response = client.get(
            "/analytics/system-stats",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        sessions = data["sessions"]
        assert "last7d" in sessions
        assert "last30d" in sessions
        assert "avgDurationMinutes" in sessions
    
    def test_learner_cannot_access_system_stats(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: User is learner
        WHEN: Tries to access system stats
        THEN: Returns 403
        """
        response = client.get(
            "/analytics/system-stats",
            headers=learner_auth_headers
        )
        
        assert response.status_code == 403
    
    def test_mentor_cannot_access_system_stats(
        self,
        client: TestClient,
        mentor_auth_headers: dict
    ):
        """
        GIVEN: User is mentor
        WHEN: Tries to access system stats
        THEN: Returns 403
        """
        response = client.get(
            "/analytics/system-stats",
            headers=mentor_auth_headers
        )
        
        assert response.status_code == 403


class TestAnalyticsEdgeCases:
    """Test edge cases for analytics"""
    
    def test_new_user_analytics(
        self,
        client: TestClient,
        create_test_user,
        get_auth_headers
    ):
        """
        GIVEN: New user with no activity
        WHEN: Requests advanced analytics
        THEN: Returns empty/zero data structure
        """
        new_user = create_test_user(email="newanalytics@test.com")
        headers = get_auth_headers(new_user)
        
        response = client.get(
            "/analytics/advanced",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still have structure, just empty
        assert data["retention"]["thisWeek"] == 0
        assert data["retention"]["lastWeek"] == 0
    
    def test_invalid_date_format_handled(
        self,
        client: TestClient,
        learner_auth_headers: dict
    ):
        """
        GIVEN: Invalid date format
        WHEN: Requests daily stats
        THEN: Falls back to today's date
        """
        response = client.get(
            "/analytics/daily-stats?date=not-a-date",
            headers=learner_auth_headers
        )
        
        # Should handle gracefully
        assert response.status_code == 200
    
    def test_unauthenticated_access_denied(
        self,
        client: TestClient
    ):
        """
        GIVEN: No authentication
        WHEN: Tries to access analytics
        THEN: Returns 401
        """
        response = client.get("/analytics/advanced")
        assert response.status_code == 401
        
        response = client.get("/analytics/daily-stats")
        assert response.status_code == 401
