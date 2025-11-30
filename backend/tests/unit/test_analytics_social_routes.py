"""
Testes para Analytics Social Routes - api/routes/analytics_social.py
Cobertura: dashboard_overview, platform_analytics, engagement_trend, followers_trend,
           best_times, top_posts, compare_periods, scheduler_stats, export_report
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from fastapi import HTTPException, Response


# ============================================
# MOCKS & FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """Mock de usuário autenticado"""
    user = MagicMock()
    user.id = "user-123"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_overview():
    """Mock de overview do dashboard"""
    overview = MagicMock()
    overview.period.value = "last_30_days"
    overview.start_date = datetime(2024, 1, 1)
    overview.end_date = datetime(2024, 1, 31)
    overview.total_posts = 50
    overview.total_engagement = 5000
    overview.total_reach = 100000
    overview.total_followers = 10000
    overview.best_times = {"Monday": "10:00", "Tuesday": "14:00"}
    
    # Mock platform data
    platform_data = MagicMock()
    platform_data.total_posts = 20
    platform_data.total_likes = 1000
    platform_data.total_comments = 200
    platform_data.total_shares = 50
    platform_data.total_reach = 30000
    platform_data.avg_engagement_rate = 5.5
    platform_data.followers_end = 5000
    platform_data.followers_growth_rate = 2.5
    
    overview.by_platform = {"instagram": platform_data}
    
    return overview


@pytest.fixture
def mock_platform_analytics():
    """Mock de analytics de plataforma"""
    analytics = MagicMock()
    analytics.platform.value = "instagram"
    analytics.period.value = "last_30_days"
    analytics.start_date = datetime(2024, 1, 1)
    analytics.end_date = datetime(2024, 1, 31)
    analytics.total_posts = 20
    analytics.total_stories = 10
    analytics.total_reels = 5
    analytics.total_likes = 1000
    analytics.total_comments = 200
    analytics.total_shares = 50
    analytics.total_views = 5000
    analytics.total_reach = 30000
    analytics.total_impressions = 50000
    analytics.avg_engagement_rate = 5.5
    analytics.avg_likes_per_post = 50
    analytics.avg_comments_per_post = 10
    analytics.followers_start = 4500
    analytics.followers_end = 5000
    analytics.followers_gained = 600
    analytics.followers_lost = 100
    analytics.followers_growth_rate = 11.1
    return analytics


@pytest.fixture
def mock_scheduler_stats():
    """Mock de estatísticas do agendador"""
    stats = MagicMock()
    stats.period.value = "last_30_days"
    stats.total_scheduled = 100
    stats.total_published = 90
    stats.total_failed = 5
    stats.total_pending = 5
    stats.success_rate = 90.0
    stats.by_platform = {"instagram": 50, "tiktok": 50}
    stats.by_status = {"published": 90, "failed": 5, "pending": 5}
    return stats


@pytest.fixture
def mock_analytics_service(mock_overview, mock_platform_analytics, mock_scheduler_stats):
    """Mock do SocialAnalyticsService"""
    service = AsyncMock()
    service.get_dashboard_overview.return_value = mock_overview
    service.get_platform_analytics.return_value = mock_platform_analytics
    service.get_engagement_trend.return_value = [
        {"date": "2024-01-01", "engagement": 100},
        {"date": "2024-01-02", "engagement": 120}
    ]
    service.get_followers_trend.return_value = [
        {"date": "2024-01-01", "followers": 4500},
        {"date": "2024-01-31", "followers": 5000}
    ]
    service.get_best_posting_times.return_value = {
        "Monday": ["10:00", "14:00"],
        "Tuesday": ["11:00", "15:00"]
    }
    service.get_top_posts.return_value = [
        {"id": "post1", "engagement": 500},
        {"id": "post2", "engagement": 400}
    ]
    service.compare_periods.return_value = {
        "period1": {"engagement": 5000},
        "period2": {"engagement": 4000},
        "growth": 25.0
    }
    service.get_scheduler_stats.return_value = mock_scheduler_stats
    service.export_report.return_value = '{"data": "test"}'
    return service


# ============================================
# TESTS: Dashboard Overview
# ============================================

class TestDashboardOverview:
    """Testes do endpoint get_dashboard_overview"""
    
    @pytest.mark.asyncio
    async def test_get_overview_success(self, mock_user, mock_analytics_service):
        """Deve retornar overview do dashboard"""
        with patch("api.routes.analytics_social.analytics_service", mock_analytics_service):
            with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
                MockPeriod.return_value = MagicMock()
                
                from api.routes.analytics_social import get_dashboard_overview
                
                response = await get_dashboard_overview(
                    period="last_30_days",
                    current_user=mock_user
                )
                
                assert "period" in response
                assert "totals" in response
                assert "by_platform" in response
                assert "best_times" in response
    
    @pytest.mark.asyncio
    async def test_get_overview_invalid_period(self, mock_user):
        """Deve retornar 400 para período inválido"""
        with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
            MockPeriod.side_effect = ValueError("Invalid period")
            
            from api.routes.analytics_social import get_dashboard_overview
            
            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_overview(
                    period="invalid_period",
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 400


# ============================================
# TESTS: Platform Analytics
# ============================================

class TestPlatformAnalytics:
    """Testes do endpoint get_platform_analytics"""
    
    @pytest.mark.asyncio
    async def test_get_platform_success(self, mock_user, mock_analytics_service):
        """Deve retornar analytics de plataforma"""
        with patch("api.routes.analytics_social.analytics_service", mock_analytics_service):
            with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
                with patch("api.routes.analytics_social.Platform") as MockPlatform:
                    MockPeriod.return_value = MagicMock()
                    MockPlatform.return_value = MagicMock()
                    
                    from api.routes.analytics_social import get_platform_analytics
                    
                    response = await get_platform_analytics(
                        platform="instagram",
                        period="last_30_days",
                        current_user=mock_user
                    )
                    
                    assert response["platform"] == "instagram"
                    assert "engagement" in response
                    assert "followers" in response
    
    @pytest.mark.asyncio
    async def test_get_platform_invalid(self, mock_user):
        """Deve retornar 400 para plataforma inválida"""
        with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
            with patch("api.routes.analytics_social.Platform") as MockPlatform:
                MockPeriod.side_effect = ValueError("Invalid")
                
                from api.routes.analytics_social import get_platform_analytics
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_platform_analytics(
                        platform="invalid",
                        current_user=mock_user
                    )
                
                assert exc_info.value.status_code == 400


# ============================================
# TESTS: Trends
# ============================================

class TestTrends:
    """Testes dos endpoints de tendências"""
    
    @pytest.mark.asyncio
    async def test_get_engagement_trend_success(self, mock_user, mock_analytics_service):
        """Deve retornar tendência de engajamento"""
        with patch("api.routes.analytics_social.analytics_service", mock_analytics_service):
            with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
                MockPeriod.return_value = MagicMock()
                
                from api.routes.analytics_social import get_engagement_trend
                
                response = await get_engagement_trend(
                    period="last_30_days",
                    granularity="day",
                    current_user=mock_user
                )
                
                assert "trend" in response
                assert response["granularity"] == "day"
    
    @pytest.mark.asyncio
    async def test_get_engagement_trend_invalid_period(self, mock_user):
        """Deve retornar 400 para período inválido"""
        with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
            MockPeriod.side_effect = ValueError("Invalid period")
            
            from api.routes.analytics_social import get_engagement_trend
            
            with pytest.raises(HTTPException) as exc_info:
                await get_engagement_trend(
                    period="invalid",
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_followers_trend_success(self, mock_user, mock_analytics_service):
        """Deve retornar tendência de seguidores"""
        with patch("api.routes.analytics_social.analytics_service", mock_analytics_service):
            with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
                with patch("api.routes.analytics_social.Platform") as MockPlatform:
                    MockPeriod.return_value = MagicMock()
                    MockPlatform.return_value = None
                    
                    from api.routes.analytics_social import get_followers_trend
                    
                    response = await get_followers_trend(
                        period="last_30_days",
                        current_user=mock_user
                    )
                    
                    assert "trend" in response
    
    @pytest.mark.asyncio
    async def test_get_followers_trend_with_platform(self, mock_user, mock_analytics_service):
        """Deve filtrar por plataforma"""
        with patch("api.routes.analytics_social.analytics_service", mock_analytics_service):
            with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
                with patch("api.routes.analytics_social.Platform") as MockPlatform:
                    MockPeriod.return_value = MagicMock()
                    MockPlatform.return_value = MagicMock()
                    
                    from api.routes.analytics_social import get_followers_trend
                    
                    await get_followers_trend(
                        period="last_30_days",
                        platform="instagram",
                        current_user=mock_user
                    )
                    
                    mock_analytics_service.get_followers_trend.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_followers_trend_invalid(self, mock_user):
        """Deve retornar 400 para dados inválidos"""
        with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
            MockPeriod.side_effect = ValueError("Invalid")
            
            from api.routes.analytics_social import get_followers_trend
            
            with pytest.raises(HTTPException) as exc_info:
                await get_followers_trend(period="invalid", current_user=mock_user)
            
            assert exc_info.value.status_code == 400


# ============================================
# TESTS: Best Times & Top Posts
# ============================================

class TestBestTimesAndTopPosts:
    """Testes dos endpoints de melhores horários e posts"""
    
    @pytest.mark.asyncio
    async def test_get_best_times_success(self, mock_user, mock_analytics_service):
        """Deve retornar melhores horários"""
        with patch("api.routes.analytics_social.analytics_service", mock_analytics_service):
            with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
                with patch("api.routes.analytics_social.Platform") as MockPlatform:
                    MockPeriod.return_value = MagicMock()
                    MockPlatform.return_value = None
                    
                    from api.routes.analytics_social import get_best_posting_times
                    
                    response = await get_best_posting_times(
                        period="last_90_days",
                        current_user=mock_user
                    )
                    
                    assert "best_times" in response
    
    @pytest.mark.asyncio
    async def test_get_best_times_invalid(self, mock_user):
        """Deve retornar 400 para dados inválidos"""
        with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
            MockPeriod.side_effect = ValueError("Invalid")
            
            from api.routes.analytics_social import get_best_posting_times
            
            with pytest.raises(HTTPException) as exc_info:
                await get_best_posting_times(period="invalid", current_user=mock_user)
            
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_top_posts_success(self, mock_user, mock_analytics_service):
        """Deve retornar top posts"""
        with patch("api.routes.analytics_social.analytics_service", mock_analytics_service):
            with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
                with patch("api.routes.analytics_social.Platform") as MockPlatform:
                    MockPeriod.return_value = MagicMock()
                    MockPlatform.return_value = None
                    
                    from api.routes.analytics_social import get_top_posts
                    
                    response = await get_top_posts(
                        period="last_30_days",
                        limit=10,
                        current_user=mock_user
                    )
                    
                    assert "posts" in response
    
    @pytest.mark.asyncio
    async def test_get_top_posts_invalid(self, mock_user):
        """Deve retornar 400 para dados inválidos"""
        with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
            MockPeriod.side_effect = ValueError("Invalid")
            
            from api.routes.analytics_social import get_top_posts
            
            with pytest.raises(HTTPException) as exc_info:
                await get_top_posts(period="invalid", current_user=mock_user)
            
            assert exc_info.value.status_code == 400


# ============================================
# TESTS: Compare Periods
# ============================================

class TestComparePeriods:
    """Testes do endpoint compare_periods"""
    
    @pytest.mark.asyncio
    async def test_compare_periods_success(self, mock_user, mock_analytics_service):
        """Deve comparar dois períodos"""
        with patch("api.routes.analytics_social.analytics_service", mock_analytics_service):
            with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
                with patch("api.routes.analytics_social.Platform") as MockPlatform:
                    MockPeriod.return_value = MagicMock()
                    MockPlatform.return_value = None
                    
                    from api.routes.analytics_social import compare_periods
                    
                    response = await compare_periods(
                        period1="last_30_days",
                        period2="last_month",
                        current_user=mock_user
                    )
                    
                    assert "growth" in response
    
    @pytest.mark.asyncio
    async def test_compare_periods_invalid(self, mock_user):
        """Deve retornar 400 para dados inválidos"""
        with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
            MockPeriod.side_effect = ValueError("Invalid")
            
            from api.routes.analytics_social import compare_periods
            
            with pytest.raises(HTTPException) as exc_info:
                await compare_periods(
                    period1="invalid",
                    period2="also_invalid",
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 400


# ============================================
# TESTS: Scheduler Stats
# ============================================

class TestSchedulerStats:
    """Testes do endpoint get_scheduler_stats"""
    
    @pytest.mark.asyncio
    async def test_get_scheduler_stats_success(self, mock_user, mock_analytics_service):
        """Deve retornar estatísticas do agendador"""
        with patch("api.routes.analytics_social.analytics_service", mock_analytics_service):
            with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
                MockPeriod.return_value = MagicMock()
                
                from api.routes.analytics_social import get_scheduler_stats
                
                response = await get_scheduler_stats(
                    period="last_30_days",
                    current_user=mock_user
                )
                
                assert "period" in response
                assert "totals" in response
                assert "success_rate" in response
    
    @pytest.mark.asyncio
    async def test_get_scheduler_stats_invalid_period(self, mock_user):
        """Deve retornar 400 para período inválido"""
        with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
            MockPeriod.side_effect = ValueError("Invalid")
            
            from api.routes.analytics_social import get_scheduler_stats
            
            with pytest.raises(HTTPException) as exc_info:
                await get_scheduler_stats(period="invalid", current_user=mock_user)
            
            assert exc_info.value.status_code == 400


# ============================================
# TESTS: Export Report
# ============================================

class TestExportReport:
    """Testes do endpoint export_report"""
    
    @pytest.mark.asyncio
    async def test_export_json_success(self, mock_user, mock_analytics_service):
        """Deve exportar relatório em JSON"""
        with patch("api.routes.analytics_social.analytics_service", mock_analytics_service):
            with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
                MockPeriod.return_value = MagicMock()
                
                from api.routes.analytics_social import export_report
                
                response = await export_report(
                    period="last_30_days",
                    format="json",
                    current_user=mock_user
                )
                
                assert isinstance(response, Response)
                assert response.media_type == "application/json"
    
    @pytest.mark.asyncio
    async def test_export_csv_success(self, mock_user, mock_analytics_service):
        """Deve exportar relatório em CSV"""
        mock_analytics_service.export_report.return_value = "col1,col2\nval1,val2"
        
        with patch("api.routes.analytics_social.analytics_service", mock_analytics_service):
            with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
                MockPeriod.return_value = MagicMock()
                
                from api.routes.analytics_social import export_report
                
                response = await export_report(
                    period="last_30_days",
                    format="csv",
                    current_user=mock_user
                )
                
                assert response.media_type == "text/csv"
    
    @pytest.mark.asyncio
    async def test_export_invalid_format(self, mock_user):
        """Deve retornar 400 para formato inválido"""
        from api.routes.analytics_social import export_report
        
        with pytest.raises(HTTPException) as exc_info:
            await export_report(
                period="last_30_days",
                format="pdf",
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_export_invalid_period(self, mock_user):
        """Deve retornar 400 para período inválido"""
        with patch("api.routes.analytics_social.MetricPeriod") as MockPeriod:
            MockPeriod.side_effect = ValueError("Invalid")
            
            from api.routes.analytics_social import export_report
            
            with pytest.raises(HTTPException) as exc_info:
                await export_report(
                    period="invalid",
                    format="json",
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 400


# ============================================
# TESTS: Models
# ============================================

class TestAnalyticsSocialModels:
    """Testes dos modelos Pydantic"""
    
    def test_date_range_request(self):
        """Deve criar DateRangeRequest corretamente"""
        from api.routes.analytics_social import DateRangeRequest
        
        req = DateRangeRequest()
        
        assert req.start_date is None
        assert req.end_date is None
    
    def test_date_range_request_with_dates(self):
        """Deve criar DateRangeRequest com datas"""
        from api.routes.analytics_social import DateRangeRequest
        
        req = DateRangeRequest(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        assert req.start_date == datetime(2024, 1, 1)
        assert req.end_date == datetime(2024, 1, 31)
    
    def test_overview_response(self):
        """Deve criar OverviewResponse corretamente"""
        from api.routes.analytics_social import OverviewResponse
        
        resp = OverviewResponse(
            period="last_30_days",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            total_posts=50,
            total_engagement=5000,
            total_reach=100000,
            total_followers=10000
        )
        
        assert resp.period == "last_30_days"
        assert resp.total_posts == 50
