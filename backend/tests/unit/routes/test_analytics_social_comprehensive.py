"""
Comprehensive tests for analytics_social.py routes.
Target: Increase coverage from 37% to 90%+
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {"id": "user-123", "email": "test@example.com", "name": "Test User"}


@pytest.fixture
def mock_platform_analytics():
    """Mock platform analytics data."""
    mock = MagicMock()
    mock.platform = MagicMock(value="instagram")
    mock.period = MagicMock(value="last_30_days")
    mock.start_date = datetime(2024, 1, 1)
    mock.end_date = datetime(2024, 1, 31)
    mock.total_posts = 25
    mock.total_stories = 10
    mock.total_reels = 5
    mock.total_likes = 5000
    mock.total_comments = 200
    mock.total_shares = 50
    mock.total_views = 10000
    mock.total_reach = 8000
    mock.total_impressions = 15000
    mock.avg_engagement_rate = 4.5
    mock.avg_likes_per_post = 200
    mock.avg_comments_per_post = 8
    mock.followers_start = 1000
    mock.followers_end = 1200
    mock.followers_gained = 250
    mock.followers_lost = 50
    mock.followers_growth_rate = 20.0
    return mock


@pytest.fixture
def mock_dashboard_overview():
    """Mock dashboard overview data."""
    mock = MagicMock()
    mock.period = MagicMock(value="last_30_days")
    mock.start_date = datetime(2024, 1, 1)
    mock.end_date = datetime(2024, 1, 31)
    mock.total_posts = 50
    mock.total_engagement = 10000
    mock.total_reach = 25000
    mock.total_followers = 5000
    
    # Platform data
    platform_data = MagicMock()
    platform_data.total_posts = 25
    platform_data.total_likes = 2500
    platform_data.total_comments = 100
    platform_data.total_shares = 25
    platform_data.total_reach = 8000
    platform_data.avg_engagement_rate = 4.2
    platform_data.followers_end = 2500
    platform_data.followers_growth_rate = 15.0
    
    mock.by_platform = {"instagram": platform_data, "tiktok": platform_data}
    mock.best_times = [{"hour": 9, "day": "monday", "engagement": 5.5}]
    return mock


@pytest.fixture
def mock_scheduler_stats():
    """Mock scheduler stats data."""
    mock = MagicMock()
    mock.period = MagicMock(value="last_30_days")
    mock.total_scheduled = 100
    mock.total_published = 90
    mock.total_failed = 5
    mock.total_pending = 5
    mock.success_rate = 90.0
    mock.by_platform = {"instagram": 50, "tiktok": 50}
    mock.by_status = {"published": 90, "failed": 5, "pending": 5}
    return mock


# ============================================
# DASHBOARD OVERVIEW TESTS
# ============================================

class TestGetDashboardOverview:
    """Tests for GET /overview endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_overview_success(self, mock_user, mock_dashboard_overview):
        """Test successful dashboard overview retrieval."""
        with patch("api.routes.analytics_social.get_current_user", return_value=mock_user), \
             patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_dashboard_overview = AsyncMock(return_value=mock_dashboard_overview)
            
            from api.routes.analytics_social import get_dashboard_overview
            result = await get_dashboard_overview(period="last_30_days", current_user=mock_user)
            
            assert result["period"] == "last_30_days"
            assert "totals" in result
            assert "by_platform" in result
            assert "best_times" in result
            assert result["totals"]["posts"] == 50
            assert result["totals"]["engagement"] == 10000
    
    @pytest.mark.asyncio
    async def test_get_overview_with_different_periods(self, mock_user, mock_dashboard_overview):
        """Test overview with various period options."""
        periods = ["today", "yesterday", "last_7_days", "last_90_days", "this_month", "this_year"]
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_dashboard_overview = AsyncMock(return_value=mock_dashboard_overview)
            
            from api.routes.analytics_social import get_dashboard_overview
            
            for period in periods:
                mock_dashboard_overview.period = MagicMock(value=period)
                result = await get_dashboard_overview(period=period, current_user=mock_user)
                assert result["period"] == period
    
    @pytest.mark.asyncio
    async def test_get_overview_invalid_period(self, mock_user):
        """Test overview with invalid period raises HTTPException."""
        from api.routes.analytics_social import get_dashboard_overview
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await get_dashboard_overview(period="invalid_period", current_user=mock_user)
        
        assert exc.value.status_code == 400
        assert "Período inválido" in str(exc.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_overview_platform_data_structure(self, mock_user, mock_dashboard_overview):
        """Test that platform data has correct structure."""
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_dashboard_overview = AsyncMock(return_value=mock_dashboard_overview)
            
            from api.routes.analytics_social import get_dashboard_overview
            result = await get_dashboard_overview(period="last_30_days", current_user=mock_user)
            
            for platform, data in result["by_platform"].items():
                assert "posts" in data
                assert "likes" in data
                assert "comments" in data
                assert "shares" in data
                assert "reach" in data
                assert "engagement_rate" in data
                assert "followers" in data
                assert "followers_growth" in data


# ============================================
# PLATFORM ANALYTICS TESTS
# ============================================

class TestGetPlatformAnalytics:
    """Tests for GET /platform/{platform} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_platform_analytics_instagram(self, mock_user, mock_platform_analytics):
        """Test getting Instagram analytics."""
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_platform_analytics = AsyncMock(return_value=mock_platform_analytics)
            
            from api.routes.analytics_social import get_platform_analytics
            result = await get_platform_analytics(
                platform="instagram",
                period="last_30_days",
                current_user=mock_user
            )
            
            assert result["platform"] == "instagram"
            assert result["content"]["posts"] == 25
            assert result["content"]["stories"] == 10
            assert result["content"]["reels"] == 5
    
    @pytest.mark.asyncio
    async def test_get_platform_analytics_tiktok(self, mock_user, mock_platform_analytics):
        """Test getting TikTok analytics."""
        mock_platform_analytics.platform = MagicMock(value="tiktok")
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_platform_analytics = AsyncMock(return_value=mock_platform_analytics)
            
            from api.routes.analytics_social import get_platform_analytics
            result = await get_platform_analytics(
                platform="tiktok",
                period="last_30_days",
                current_user=mock_user
            )
            
            assert result["platform"] == "tiktok"
    
    @pytest.mark.asyncio
    async def test_get_platform_analytics_invalid_platform(self, mock_user):
        """Test with invalid platform raises HTTPException."""
        from api.routes.analytics_social import get_platform_analytics
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await get_platform_analytics(
                platform="invalid_platform",
                period="last_30_days",
                current_user=mock_user
            )
        
        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_platform_analytics_invalid_period(self, mock_user):
        """Test with invalid period raises HTTPException."""
        from api.routes.analytics_social import get_platform_analytics
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await get_platform_analytics(
                platform="instagram",
                period="invalid_period",
                current_user=mock_user
            )
        
        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_platform_analytics_engagement_data(self, mock_user, mock_platform_analytics):
        """Test engagement data structure."""
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_platform_analytics = AsyncMock(return_value=mock_platform_analytics)
            
            from api.routes.analytics_social import get_platform_analytics
            result = await get_platform_analytics(
                platform="instagram",
                period="last_30_days",
                current_user=mock_user
            )
            
            assert result["engagement"]["likes"] == 5000
            assert result["engagement"]["comments"] == 200
            assert result["engagement"]["shares"] == 50
            assert result["engagement"]["views"] == 10000
            assert result["engagement"]["reach"] == 8000
            assert result["engagement"]["engagement_rate"] == 4.5
    
    @pytest.mark.asyncio
    async def test_get_platform_analytics_followers_data(self, mock_user, mock_platform_analytics):
        """Test followers data structure."""
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_platform_analytics = AsyncMock(return_value=mock_platform_analytics)
            
            from api.routes.analytics_social import get_platform_analytics
            result = await get_platform_analytics(
                platform="instagram",
                period="last_30_days",
                current_user=mock_user
            )
            
            assert result["followers"]["start"] == 1000
            assert result["followers"]["end"] == 1200
            assert result["followers"]["gained"] == 250
            assert result["followers"]["lost"] == 50
            assert result["followers"]["growth_rate"] == 20.0


# ============================================
# TRENDS ENDPOINTS TESTS
# ============================================

class TestGetEngagementTrend:
    """Tests for GET /trends/engagement endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_engagement_trend_success(self, mock_user):
        """Test successful engagement trend retrieval."""
        mock_trend = [
            {"date": "2024-01-01", "engagement": 100},
            {"date": "2024-01-02", "engagement": 150}
        ]
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_engagement_trend = AsyncMock(return_value=mock_trend)
            
            from api.routes.analytics_social import get_engagement_trend
            result = await get_engagement_trend(
                period="last_30_days",
                granularity="day",
                current_user=mock_user
            )
            
            assert "trend" in result
            assert result["granularity"] == "day"
            assert len(result["trend"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_engagement_trend_weekly_granularity(self, mock_user):
        """Test engagement trend with weekly granularity."""
        mock_trend = [{"week": "2024-W01", "engagement": 500}]
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_engagement_trend = AsyncMock(return_value=mock_trend)
            
            from api.routes.analytics_social import get_engagement_trend
            result = await get_engagement_trend(
                period="last_90_days",
                granularity="week",
                current_user=mock_user
            )
            
            assert result["granularity"] == "week"
    
    @pytest.mark.asyncio
    async def test_get_engagement_trend_invalid_period(self, mock_user):
        """Test with invalid period raises HTTPException."""
        from api.routes.analytics_social import get_engagement_trend
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await get_engagement_trend(
                period="invalid",
                granularity="day",
                current_user=mock_user
            )
        
        assert exc.value.status_code == 400


class TestGetFollowersTrend:
    """Tests for GET /trends/followers endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_followers_trend_all_platforms(self, mock_user):
        """Test followers trend for all platforms."""
        mock_trend = [
            {"date": "2024-01-01", "followers": 1000},
            {"date": "2024-01-02", "followers": 1050}
        ]
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_followers_trend = AsyncMock(return_value=mock_trend)
            
            from api.routes.analytics_social import get_followers_trend
            result = await get_followers_trend(
                period="last_30_days",
                platform=None,
                current_user=mock_user
            )
            
            assert "trend" in result
    
    @pytest.mark.asyncio
    async def test_get_followers_trend_specific_platform(self, mock_user):
        """Test followers trend for specific platform."""
        mock_trend = [{"date": "2024-01-01", "followers": 500}]
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_followers_trend = AsyncMock(return_value=mock_trend)
            
            from api.routes.analytics_social import get_followers_trend
            result = await get_followers_trend(
                period="last_30_days",
                platform="instagram",
                current_user=mock_user
            )
            
            assert "trend" in result
    
    @pytest.mark.asyncio
    async def test_get_followers_trend_invalid_platform(self, mock_user):
        """Test with invalid platform raises HTTPException."""
        from api.routes.analytics_social import get_followers_trend
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await get_followers_trend(
                period="last_30_days",
                platform="invalid_platform",
                current_user=mock_user
            )
        
        assert exc.value.status_code == 400


# ============================================
# BEST TIMES & TOP CONTENT TESTS
# ============================================

class TestGetBestPostingTimes:
    """Tests for GET /best-times endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_best_times_success(self, mock_user):
        """Test successful best times retrieval."""
        mock_best_times = [
            {"hour": 9, "day": "monday", "engagement_rate": 5.5},
            {"hour": 18, "day": "friday", "engagement_rate": 4.8}
        ]
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_best_posting_times = AsyncMock(return_value=mock_best_times)
            
            from api.routes.analytics_social import get_best_posting_times
            result = await get_best_posting_times(
                period="last_90_days",
                platform=None,
                current_user=mock_user
            )
            
            assert "best_times" in result
            assert len(result["best_times"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_best_times_specific_platform(self, mock_user):
        """Test best times for specific platform."""
        mock_best_times = [{"hour": 12, "day": "wednesday", "engagement_rate": 6.0}]
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_best_posting_times = AsyncMock(return_value=mock_best_times)
            
            from api.routes.analytics_social import get_best_posting_times
            result = await get_best_posting_times(
                period="last_90_days",
                platform="tiktok",
                current_user=mock_user
            )
            
            assert len(result["best_times"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_best_times_invalid_period(self, mock_user):
        """Test with invalid period."""
        from api.routes.analytics_social import get_best_posting_times
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await get_best_posting_times(
                period="invalid",
                platform=None,
                current_user=mock_user
            )
        
        assert exc.value.status_code == 400


class TestGetTopPosts:
    """Tests for GET /top-posts endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_top_posts_success(self, mock_user):
        """Test successful top posts retrieval."""
        mock_posts = [
            {"id": "1", "likes": 500, "comments": 50},
            {"id": "2", "likes": 400, "comments": 40}
        ]
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_top_posts = AsyncMock(return_value=mock_posts)
            
            from api.routes.analytics_social import get_top_posts
            result = await get_top_posts(
                period="last_30_days",
                platform=None,
                sort_by="engagement",
                limit=10,
                current_user=mock_user
            )
            
            assert "posts" in result
            assert len(result["posts"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_top_posts_by_reach(self, mock_user):
        """Test top posts sorted by reach."""
        mock_posts = [{"id": "1", "reach": 10000}]
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_top_posts = AsyncMock(return_value=mock_posts)
            
            from api.routes.analytics_social import get_top_posts
            result = await get_top_posts(
                period="last_30_days",
                platform="instagram",
                sort_by="reach",
                limit=5,
                current_user=mock_user
            )
            
            assert len(result["posts"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_top_posts_invalid_period(self, mock_user):
        """Test with invalid period."""
        from api.routes.analytics_social import get_top_posts
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await get_top_posts(
                period="invalid",
                platform=None,
                sort_by="engagement",
                limit=10,
                current_user=mock_user
            )
        
        assert exc.value.status_code == 400


# ============================================
# COMPARISON & REPORTS TESTS
# ============================================

class TestComparePeriods:
    """Tests for GET /compare endpoint."""
    
    @pytest.mark.asyncio
    async def test_compare_periods_success(self, mock_user):
        """Test successful period comparison."""
        mock_comparison = {
            "period1": {"engagement": 1000, "reach": 5000},
            "period2": {"engagement": 800, "reach": 4000},
            "change": {"engagement": "+25%", "reach": "+25%"}
        }
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.compare_periods = AsyncMock(return_value=mock_comparison)
            
            from api.routes.analytics_social import compare_periods
            result = await compare_periods(
                period1="last_30_days",
                period2="last_month",
                platform=None,
                current_user=mock_user
            )
            
            assert "period1" in result
            assert "period2" in result
    
    @pytest.mark.asyncio
    async def test_compare_periods_with_platform(self, mock_user):
        """Test period comparison for specific platform."""
        mock_comparison = {"period1": {}, "period2": {}}
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.compare_periods = AsyncMock(return_value=mock_comparison)
            
            from api.routes.analytics_social import compare_periods
            result = await compare_periods(
                period1="last_7_days",
                period2="last_30_days",
                platform="instagram",
                current_user=mock_user
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_compare_periods_invalid_period(self, mock_user):
        """Test with invalid period."""
        from api.routes.analytics_social import compare_periods
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await compare_periods(
                period1="invalid",
                period2="last_month",
                platform=None,
                current_user=mock_user
            )
        
        assert exc.value.status_code == 400


class TestGetSchedulerStats:
    """Tests for GET /scheduler-stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_scheduler_stats_success(self, mock_user, mock_scheduler_stats):
        """Test successful scheduler stats retrieval."""
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_scheduler_stats = AsyncMock(return_value=mock_scheduler_stats)
            
            from api.routes.analytics_social import get_scheduler_stats
            result = await get_scheduler_stats(
                period="last_30_days",
                current_user=mock_user
            )
            
            assert result["period"] == "last_30_days"
            assert result["totals"]["scheduled"] == 100
            assert result["totals"]["published"] == 90
            assert result["totals"]["failed"] == 5
            assert result["success_rate"] == 90.0
    
    @pytest.mark.asyncio
    async def test_get_scheduler_stats_invalid_period(self, mock_user):
        """Test with invalid period."""
        from api.routes.analytics_social import get_scheduler_stats
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await get_scheduler_stats(
                period="invalid",
                current_user=mock_user
            )
        
        assert exc.value.status_code == 400


class TestExportReport:
    """Tests for GET /export endpoint."""
    
    @pytest.mark.asyncio
    async def test_export_report_json(self, mock_user):
        """Test exporting report as JSON."""
        mock_data = '{"total_posts": 50}'
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.export_report = AsyncMock(return_value=mock_data)
            
            from api.routes.analytics_social import export_report
            result = await export_report(
                period="last_30_days",
                format="json",
                current_user=mock_user
            )
            
            assert result.body == mock_data.encode()
            assert result.media_type == "application/json"
    
    @pytest.mark.asyncio
    async def test_export_report_csv(self, mock_user):
        """Test exporting report as CSV."""
        mock_data = "date,posts,engagement\n2024-01-01,10,500"
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.export_report = AsyncMock(return_value=mock_data)
            
            from api.routes.analytics_social import export_report
            result = await export_report(
                period="last_30_days",
                format="csv",
                current_user=mock_user
            )
            
            assert result.media_type == "text/csv"
            assert "Content-Disposition" in result.headers
    
    @pytest.mark.asyncio
    async def test_export_report_invalid_format(self, mock_user):
        """Test with invalid format."""
        from api.routes.analytics_social import export_report
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await export_report(
                period="last_30_days",
                format="pdf",
                current_user=mock_user
            )
        
        assert exc.value.status_code == 400
        assert "Formato inválido" in str(exc.value.detail)
    
    @pytest.mark.asyncio
    async def test_export_report_invalid_period(self, mock_user):
        """Test with invalid period."""
        from api.routes.analytics_social import export_report
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await export_report(
                period="invalid",
                format="json",
                current_user=mock_user
            )
        
        assert exc.value.status_code == 400


# ============================================
# EDGE CASES & ERROR HANDLING
# ============================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_empty_analytics_data(self, mock_user):
        """Test handling of empty analytics data."""
        mock_overview = MagicMock()
        mock_overview.period = MagicMock(value="last_30_days")
        mock_overview.start_date = datetime(2024, 1, 1)
        mock_overview.end_date = datetime(2024, 1, 31)
        mock_overview.total_posts = 0
        mock_overview.total_engagement = 0
        mock_overview.total_reach = 0
        mock_overview.total_followers = 0
        mock_overview.by_platform = {}
        mock_overview.best_times = []
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_dashboard_overview = AsyncMock(return_value=mock_overview)
            
            from api.routes.analytics_social import get_dashboard_overview
            result = await get_dashboard_overview(period="last_30_days", current_user=mock_user)
            
            assert result["totals"]["posts"] == 0
            assert result["by_platform"] == {}
            assert result["best_times"] == []
    
    @pytest.mark.asyncio
    async def test_service_exception_handling(self, mock_user):
        """Test handling of service exceptions."""
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_dashboard_overview = AsyncMock(side_effect=Exception("Service error"))
            
            from api.routes.analytics_social import get_dashboard_overview
            
            with pytest.raises(Exception):
                await get_dashboard_overview(period="last_30_days", current_user=mock_user)
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, mock_user):
        """Test handling of large datasets."""
        large_posts = [{"id": str(i), "likes": i * 10} for i in range(1000)]
        
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_top_posts = AsyncMock(return_value=large_posts[:10])
            
            from api.routes.analytics_social import get_top_posts
            result = await get_top_posts(
                period="last_30_days",
                platform=None,
                sort_by="engagement",
                limit=10,
                current_user=mock_user
            )
            
            assert len(result["posts"]) == 10
    
    @pytest.mark.asyncio
    async def test_date_range_in_response(self, mock_user, mock_platform_analytics):
        """Test that date range is properly formatted in response."""
        with patch("api.routes.analytics_social.analytics_service") as mock_service:
            mock_service.get_platform_analytics = AsyncMock(return_value=mock_platform_analytics)
            
            from api.routes.analytics_social import get_platform_analytics
            result = await get_platform_analytics(
                platform="instagram",
                period="last_30_days",
                current_user=mock_user
            )
            
            assert "date_range" in result
            assert "start" in result["date_range"]
            assert "end" in result["date_range"]
