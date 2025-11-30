"""
Tests for Analytics Routes
"""

import pytest
from unittest.mock import AsyncMock, patch


class MockUser:
    id = "user_123"
    email = "test@example.com"


@pytest.fixture
def mock_current_user():
    return MockUser()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.get.return_value = None
    redis.set.return_value = True
    redis.hgetall.return_value = {}
    redis.hset.return_value = True
    redis.expire.return_value = True
    redis.hincrby.return_value = 1
    return redis


class TestAnalyticsOverview:
    """Tests for analytics overview endpoint"""

    @pytest.mark.asyncio
    async def test_get_overview_empty_data(self, mock_current_user, mock_redis):
        from api.routes.analytics import get_analytics_overview, Platform, TimeRange

        with patch("api.routes.analytics.redis_client", mock_redis):
            result = await get_analytics_overview(
                platform=Platform.ALL,
                time_range=TimeRange.WEEK,
                current_user=mock_current_user
            )

            assert result.total_posts == 0
            assert result.total_views == 0
            assert result.period == "7d"

    @pytest.mark.asyncio
    async def test_get_overview_with_data(self, mock_current_user, mock_redis):
        from api.routes.analytics import get_analytics_overview, Platform, TimeRange

        # Mock some daily data
        mock_redis.hgetall.return_value = {
            "posts": "5",
            "views": "1000",
            "engagement": "100"
        }

        with patch("api.routes.analytics.redis_client", mock_redis):
            result = await get_analytics_overview(
                platform=Platform.ALL,
                time_range=TimeRange.WEEK,
                current_user=mock_current_user
            )

            # Should have data from 7 days
            assert result.total_posts == 35  # 5 * 7 days
            assert result.total_views == 7000
            assert len(result.daily_stats) == 7


class TestPlatformAnalytics:
    """Tests for platform-specific analytics"""

    @pytest.mark.asyncio
    async def test_get_platform_instagram(self, mock_current_user, mock_redis):
        from api.routes.analytics import get_platform_analytics, Platform, TimeRange

        mock_redis.hgetall.return_value = {
            "posts": "10",
            "views": "5000",
            "likes": "500",
            "comments": "50",
            "shares": "25"
        }

        with patch("api.routes.analytics.redis_client", mock_redis):
            result = await get_platform_analytics(
                platform=Platform.INSTAGRAM,
                time_range=TimeRange.WEEK,
                current_user=mock_current_user
            )

            assert result["platform"] == "instagram"
            assert result["period"] == "7d"
            assert "metrics" in result

    @pytest.mark.asyncio
    async def test_get_platform_all_raises_error(self, mock_current_user, mock_redis):
        from api.routes.analytics import get_platform_analytics, Platform, TimeRange
        from fastapi import HTTPException

        with patch("api.routes.analytics.redis_client", mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await get_platform_analytics(
                    platform=Platform.ALL,
                    time_range=TimeRange.WEEK,
                    current_user=mock_current_user
                )

            assert exc_info.value.status_code == 400


class TestDailyStats:
    """Tests for daily statistics endpoint"""

    @pytest.mark.asyncio
    async def test_get_daily_empty(self, mock_current_user, mock_redis):
        from api.routes.analytics import get_daily_stats, TimeRange

        with patch("api.routes.analytics.redis_client", mock_redis):
            result = await get_daily_stats(
                time_range=TimeRange.WEEK,
                current_user=mock_current_user
            )

            assert "daily" in result
            assert len(result["daily"]) == 7

    @pytest.mark.asyncio
    async def test_get_daily_with_data(self, mock_current_user, mock_redis):
        from api.routes.analytics import get_daily_stats, TimeRange

        mock_redis.hgetall.return_value = {
            "posts": "3",
            "views": "500",
            "engagement": "50"
        }

        with patch("api.routes.analytics.redis_client", mock_redis):
            result = await get_daily_stats(
                time_range=TimeRange.WEEK,
                current_user=mock_current_user
            )

            assert result["daily"][0]["posts"] == 3
            assert result["daily"][0]["views"] == 500


class TestRecordMetrics:
    """Tests for recording metrics"""

    @pytest.mark.asyncio
    async def test_record_metrics_success(self, mock_current_user, mock_redis):
        from api.routes.analytics import record_metrics

        with patch("api.routes.analytics.redis_client", mock_redis):
            result = await record_metrics(
                platform="instagram",
                post_id="post_123",
                views=1000,
                likes=100,
                comments=10,
                shares=5,
                current_user=mock_current_user
            )

            assert result["status"] == "recorded"
            # Verify hset was called
            assert mock_redis.hset.called


class TestGrowthStats:
    """Tests for growth statistics"""

    @pytest.mark.asyncio
    async def test_get_growth_no_data(self, mock_current_user, mock_redis):
        from api.routes.analytics import get_growth_stats, TimeRange

        with patch("api.routes.analytics.redis_client", mock_redis):
            result = await get_growth_stats(
                time_range=TimeRange.WEEK,
                current_user=mock_current_user
            )

            assert result["period"] == "7d"
            assert "growth" in result

    @pytest.mark.asyncio
    async def test_get_growth_with_data(self, mock_current_user, mock_redis):
        from api.routes.analytics import get_growth_stats, TimeRange

        mock_redis.hgetall.return_value = {
            "posts": "5",
            "views": "1000",
            "engagement": "100"
        }

        with patch("api.routes.analytics.redis_client", mock_redis):
            result = await get_growth_stats(
                time_range=TimeRange.WEEK,
                current_user=mock_current_user
            )

            assert "posts" in result["growth"]
            assert "views" in result["growth"]
            assert "engagement" in result["growth"]


class TestTopPosts:
    """Tests for top posts endpoint"""

    @pytest.mark.asyncio
    async def test_get_top_posts(self, mock_current_user, mock_redis):
        from api.routes.analytics import get_top_posts, Platform

        with patch("api.routes.analytics.redis_client", mock_redis):
            result = await get_top_posts(
                platform=Platform.ALL,
                limit=10,
                current_user=mock_current_user
            )

            assert result["platform"] == "all"
            assert "posts" in result


class TestAnalyticsService:
    """Tests for AnalyticsService class"""

    @pytest.mark.asyncio
    async def test_record_post(self, mock_redis):
        from api.routes.analytics import analytics_service

        with patch("api.routes.analytics.redis_client", mock_redis):
            await analytics_service.record_post(
                user_id="user_123",
                platform="instagram",
                post_id="post_456",
                metrics={
                    "views": 1000,
                    "likes": 100,
                    "comments": 10
                }
            )

            assert mock_redis.hset.called
            assert mock_redis.expire.called
            assert mock_redis.hincrby.called

    @pytest.mark.asyncio
    async def test_get_platform_metrics(self, mock_redis):
        from api.routes.analytics import analytics_service, Platform

        mock_redis.hgetall.return_value = {
            "posts": "5",
            "views": "1000",
            "likes": "100",
            "comments": "20",
            "shares": "10"
        }

        with patch("api.routes.analytics.redis_client", mock_redis):
            result = await analytics_service._get_platform_metrics(
                "user_123",
                Platform.INSTAGRAM,
                7
            )

            assert result.platform == "instagram"
            assert result.views == 7000  # 1000 * 7 days

