"""
Tests for Analytics Routes
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from modules.analytics.social_analytics import (
    DashboardOverview,
    PlatformAnalytics,
    PostAnalytics,
    EngagementMetrics,
    Platform,
    MetricPeriod,
)


class MockUser:
    id = "user_123"
    email = "test@example.com"


@pytest.fixture
def mock_current_user():
    return MockUser()


@pytest.fixture
def mock_analytics_service():
    """Mock SocialAnalyticsService"""
    service = AsyncMock()

    # Setup default return for get_dashboard_overview
    overview = DashboardOverview(
        period=MetricPeriod.LAST_30_DAYS,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow(),
        total_posts=100,
        total_engagement=5000,
        total_reach=20000,
        total_followers=10000,
        by_platform={
            "instagram": PlatformAnalytics(
                platform=Platform.INSTAGRAM,
                period=MetricPeriod.LAST_30_DAYS,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow(),
                total_posts=50,
                total_likes=2000,
                total_comments=500,
                total_shares=100,
                total_views=10000,
                total_reach=8000,
                total_impressions=12000,
                avg_engagement_rate=5.0,
                followers_end=5000,
                followers_start=4900,
                followers_gained=150,
                followers_lost=50,
                total_stories=10,
                total_reels=5,
                avg_likes_per_post=40,
                avg_comments_per_post=10,
            )
        },
        top_posts=[
            PostAnalytics(
                post_id="post_1",
                platform=Platform.INSTAGRAM,
                published_at=datetime.utcnow(),
                content_type="image",
                caption="Test Post",
                metrics=EngagementMetrics(
                    likes=100,
                    comments=10,
                    shares=5,
                    views=1000,
                    saves=2,
                    reach=800,
                    impressions=1200,
                    clicks=50,
                ),
            )
        ],
        best_times={"Wednesday": [18]},
        engagement_trend=[],
        followers_trend=[],
    )
    service.get_dashboard_overview.return_value = overview
    return service


class TestAnalyticsOverview:
    """Tests for analytics overview endpoint"""

    @pytest.mark.asyncio
    async def test_get_overview_structure(
        self, mock_current_user, mock_analytics_service
    ):
        from api.routes.analytics import get_analytics_overview

        with patch("api.routes.analytics.analytics_service", mock_analytics_service):
            result = await get_analytics_overview(
                period="30d", platform="all", current_user=mock_current_user
            )

            # Verify structure matches frontend expectations
            assert result.period.days == 30
            assert len(result.platforms) == 1
            assert result.platforms[0].platform == "instagram"
            assert result.engagement.total_likes == 2000
            assert result.engagement.best_performing_day == "Wednesday"
            assert len(result.top_content) == 1
            assert result.top_content[0].id == "post_1"
            assert result.audience.total_audience == 10000

    @pytest.mark.asyncio
    async def test_get_overview_period_mapping(
        self, mock_current_user, mock_analytics_service
    ):
        from api.routes.analytics import get_analytics_overview

        with patch("api.routes.analytics.analytics_service", mock_analytics_service):
            await get_analytics_overview(
                period="7d", platform="all", current_user=mock_current_user
            )

            # Verify service was called with correct period
            mock_analytics_service.get_dashboard_overview.assert_called_with(
                "user_123", MetricPeriod.LAST_7_DAYS
            )

    @pytest.mark.asyncio
    async def test_get_overview_platform_filtering(
        self, mock_current_user, mock_analytics_service
    ):
        from api.routes.analytics import get_analytics_overview

        with patch("api.routes.analytics.analytics_service", mock_analytics_service):
            result = await get_analytics_overview(
                period="30d", platform="instagram", current_user=mock_current_user
            )

            assert len(result.platforms) == 1
            assert result.platforms[0].platform == "instagram"

            # Test filtering out
            result_tiktok = await get_analytics_overview(
                period="30d", platform="tiktok", current_user=mock_current_user
            )
            assert len(result_tiktok.platforms) == 0
