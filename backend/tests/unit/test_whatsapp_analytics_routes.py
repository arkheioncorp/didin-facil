"""
Tests for WhatsApp Analytics Routes
====================================
Comprehensive tests for analytics, metrics, alerts and health endpoints.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from api.routes.whatsapp_analytics import (Alert, AnalyticsOverview,
                                           BotPerformance, DailyMetrics,
                                           HourlyActivity, MetricValue,
                                           TopContact, calculate_metric_change,
                                           get_metric_for_date,
                                           get_top_contacts,
                                           get_unique_contacts_for_date,
                                           router)
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """User mock as dict for route authentication."""
    return {
        "id": str(uuid4()),
        "email": "analytics@test.com",
        "is_admin": False
    }


@pytest.fixture
def mock_admin_user():
    """Admin user mock as dict."""
    return {
        "id": str(uuid4()),
        "email": "admin@test.com",
        "is_admin": True
    }


@pytest.fixture
def app(mock_user):
    """Create test FastAPI app with mocked auth."""
    app = FastAPI()
    app.include_router(router)
    
    from api.middleware.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    return app


@pytest.fixture
def admin_app(mock_admin_user):
    """Create test FastAPI app with admin auth."""
    app = FastAPI()
    app.include_router(router)
    
    from api.middleware.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    
    return app


@pytest.fixture
async def client(app):
    """Async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def admin_client(admin_app):
    """Async admin test client."""
    async with AsyncClient(
        transport=ASGITransport(app=admin_app),
        base_url="http://test"
    ) as ac:
        yield ac


# ============================================
# UNIT TESTS - Models
# ============================================

class TestModels:
    """Tests for Pydantic models."""

    def test_metric_value_defaults(self):
        """Test MetricValue default values."""
        metric = MetricValue()
        assert metric.current == 0
        assert metric.previous == 0
        assert metric.change_percent == 0.0
        assert metric.trend == "stable"

    def test_metric_value_with_values(self):
        """Test MetricValue with custom values."""
        metric = MetricValue(
            current=100,
            previous=80,
            change_percent=25.0,
            trend="up"
        )
        assert metric.current == 100
        assert metric.previous == 80
        assert metric.change_percent == 25.0
        assert metric.trend == "up"

    def test_daily_metrics_defaults(self):
        """Test DailyMetrics default values."""
        metrics = DailyMetrics(date="2024-01-01")
        assert metrics.date == "2024-01-01"
        assert metrics.messages_received == 0
        assert metrics.messages_sent == 0
        assert metrics.unique_contacts == 0

    def test_daily_metrics_with_values(self):
        """Test DailyMetrics with custom values."""
        metrics = DailyMetrics(
            date="2024-01-01",
            messages_received=50,
            messages_sent=45,
            unique_contacts=10,
            product_searches=15,
            products_found=12,
            human_transfers=3,
            total_interactions=100
        )
        assert metrics.messages_received == 50
        assert metrics.product_searches == 15

    def test_hourly_activity(self):
        """Test HourlyActivity model."""
        activity = HourlyActivity(hour=14, count=25)
        assert activity.hour == 14
        assert activity.count == 25

    def test_top_contact(self):
        """Test TopContact model."""
        contact = TopContact(
            phone="5511999999999",
            name="John Doe",
            message_count=50,
            last_interaction="2024-01-01T12:00:00Z"
        )
        assert contact.phone == "5511999999999"
        assert contact.name == "John Doe"
        assert contact.message_count == 50

    def test_bot_performance(self):
        """Test BotPerformance model."""
        perf = BotPerformance(
            total_responses=100,
            avg_response_time_ms=500,
            automation_rate=95.5,
            escalation_rate=4.5,
            satisfaction_score=4.8
        )
        assert perf.total_responses == 100
        assert perf.automation_rate == 95.5

    def test_alert_model(self):
        """Test Alert model."""
        alert = Alert(
            id="alert-1",
            type="warning",
            title="Test Alert",
            message="This is a test alert",
            timestamp="2024-01-01T12:00:00Z"
        )
        assert alert.id == "alert-1"
        assert alert.type == "warning"

    def test_analytics_overview(self):
        """Test AnalyticsOverview model."""
        overview = AnalyticsOverview(
            period="7d",
            messages=MetricValue(current=100),
            contacts=MetricValue(current=50),
            bot_performance=BotPerformance()
        )
        assert overview.period == "7d"
        assert overview.messages.current == 100


# ============================================
# UNIT TESTS - Helper Functions
# ============================================

class TestHelperFunctions:
    """Tests for helper functions."""

    @pytest.mark.asyncio
    async def test_get_metric_for_date_with_value(self):
        """Test getting metric when value exists."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value="42")
            result = await get_metric_for_date("2024-01-01", "messages_received")
            assert result == 42
            mock_cache.get.assert_called_once_with("whatsapp:metrics:2024-01-01:messages_received")

    @pytest.mark.asyncio
    async def test_get_metric_for_date_no_value(self):
        """Test getting metric when no value exists."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            result = await get_metric_for_date("2024-01-01", "messages_received")
            assert result == 0

    @pytest.mark.asyncio
    async def test_get_unique_contacts_for_date_with_contacts(self):
        """Test getting unique contacts when contacts exist."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.smembers = AsyncMock(return_value={"5511111111", "5522222222", "5533333333"})
            result = await get_unique_contacts_for_date("2024-01-01")
            assert result == 3

    @pytest.mark.asyncio
    async def test_get_unique_contacts_for_date_no_contacts(self):
        """Test getting unique contacts when no contacts exist."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.smembers = AsyncMock(return_value=None)
            result = await get_unique_contacts_for_date("2024-01-01")
            assert result == 0

    @pytest.mark.asyncio
    async def test_calculate_metric_change_increase(self):
        """Test calculating metric change for increase."""
        change, trend = await calculate_metric_change(120, 100)
        assert change == 20.0
        assert trend == "up"

    @pytest.mark.asyncio
    async def test_calculate_metric_change_decrease(self):
        """Test calculating metric change for decrease."""
        change, trend = await calculate_metric_change(80, 100)
        assert change == -20.0
        assert trend == "down"

    @pytest.mark.asyncio
    async def test_calculate_metric_change_stable(self):
        """Test calculating metric change for stable."""
        change, trend = await calculate_metric_change(102, 100)
        assert change == 2.0
        assert trend == "stable"

    @pytest.mark.asyncio
    async def test_calculate_metric_change_from_zero(self):
        """Test calculating metric change from zero."""
        change, trend = await calculate_metric_change(100, 0)
        assert change == 100.0
        assert trend == "up"

    @pytest.mark.asyncio
    async def test_calculate_metric_change_zero_to_zero(self):
        """Test calculating metric change from zero to zero."""
        change, trend = await calculate_metric_change(0, 0)
        assert change == 0.0
        assert trend == "stable"

    @pytest.mark.asyncio
    async def test_get_top_contacts_with_contacts(self):
        """Test getting top contacts when contacts exist."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.smembers = AsyncMock(return_value={"5511999999999", "5522888888888"})
            mock_cache.get = AsyncMock(side_effect=[
                [{"timestamp": "2024-01-01T12:00:00Z"}, {"timestamp": "2024-01-01T13:00:00Z"}],
                [{"timestamp": "2024-01-01T14:00:00Z"}]
            ])
            
            result = await get_top_contacts(5)
            assert len(result) == 2
            assert result[0].message_count >= result[1].message_count

    @pytest.mark.asyncio
    async def test_get_top_contacts_no_contacts(self):
        """Test getting top contacts when no contacts exist."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.smembers = AsyncMock(return_value=None)
            result = await get_top_contacts(5)
            assert result == []

    @pytest.mark.asyncio
    async def test_get_top_contacts_error(self):
        """Test getting top contacts handles errors."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.smembers = AsyncMock(side_effect=Exception("Redis error"))
            result = await get_top_contacts(5)
            assert result == []


# ============================================
# INTEGRATION TESTS - Analytics Overview
# ============================================

class TestAnalyticsOverviewEndpoint:
    """Tests for /overview endpoint."""

    @pytest.mark.asyncio
    async def test_get_analytics_overview_7d(self, client):
        """Test getting analytics overview for 7 days."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            mock_cache.smembers = AsyncMock(return_value=set())
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
                mock_metric.return_value = 10
                
                with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                    mock_contacts.return_value = 5
                    
                    with patch("api.routes.whatsapp_analytics.get_top_contacts", new_callable=AsyncMock) as mock_top:
                        mock_top.return_value = []
                        
                        response = await client.get("/whatsapp-analytics/overview?period=7d")
                        assert response.status_code == 200
                        data = response.json()
                        assert data["period"] == "7d"
                        assert "messages" in data
                        assert "contacts" in data
                        assert "bot_performance" in data

    @pytest.mark.asyncio
    async def test_get_analytics_overview_14d(self, client):
        """Test getting analytics overview for 14 days."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            mock_cache.smembers = AsyncMock(return_value=set())
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
                mock_metric.return_value = 10
                
                with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                    mock_contacts.return_value = 5
                    
                    with patch("api.routes.whatsapp_analytics.get_top_contacts", new_callable=AsyncMock) as mock_top:
                        mock_top.return_value = []
                        
                        response = await client.get("/whatsapp-analytics/overview?period=14d")
                        assert response.status_code == 200
                        data = response.json()
                        assert data["period"] == "14d"

    @pytest.mark.asyncio
    async def test_get_analytics_overview_30d(self, client):
        """Test getting analytics overview for 30 days."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            mock_cache.smembers = AsyncMock(return_value=set())
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
                mock_metric.return_value = 10
                
                with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                    mock_contacts.return_value = 5
                    
                    with patch("api.routes.whatsapp_analytics.get_top_contacts", new_callable=AsyncMock) as mock_top:
                        mock_top.return_value = []
                        
                        response = await client.get("/whatsapp-analytics/overview?period=30d")
                        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_analytics_overview_with_metrics(self, client):
        """Test analytics overview with real metrics."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            mock_cache.smembers = AsyncMock(return_value=set())
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
                # Return different values for different calls
                mock_metric.return_value = 100
                
                with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                    mock_contacts.return_value = 50
                    
                    with patch("api.routes.whatsapp_analytics.get_top_contacts", new_callable=AsyncMock) as mock_top:
                        mock_top.return_value = [
                            TopContact(phone="****9999", message_count=10)
                        ]
                        
                        response = await client.get("/whatsapp-analytics/overview")
                        assert response.status_code == 200
                        data = response.json()
                        assert data["messages"]["current"] > 0
                        assert len(data["top_contacts"]) == 1

    @pytest.mark.asyncio
    async def test_get_analytics_overview_disconnected(self, client):
        """Test analytics when WhatsApp is disconnected."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)  # No connection
            mock_cache.smembers = AsyncMock(return_value=set())
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
                mock_metric.return_value = 0
                
                with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                    mock_contacts.return_value = 0
                    
                    with patch("api.routes.whatsapp_analytics.get_top_contacts", new_callable=AsyncMock) as mock_top:
                        mock_top.return_value = []
                        
                        response = await client.get("/whatsapp-analytics/overview")
                        assert response.status_code == 200
                        data = response.json()
                        assert data["connection_status"] == "unknown"

    @pytest.mark.asyncio
    async def test_get_analytics_overview_error(self, client):
        """Test analytics overview handles errors."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(side_effect=Exception("Redis error"))
            
            response = await client.get("/whatsapp-analytics/overview")
            assert response.status_code == 500


# ============================================
# INTEGRATION TESTS - Daily Metrics
# ============================================

class TestDailyMetricsEndpoint:
    """Tests for /daily/{date} endpoint."""

    @pytest.mark.asyncio
    async def test_get_daily_metrics_success(self, client):
        """Test getting daily metrics for a date."""
        with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
            mock_metric.return_value = 25
            
            with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                mock_contacts.return_value = 10
                
                response = await client.get("/whatsapp-analytics/daily/2024-01-15")
                assert response.status_code == 200
                data = response.json()
                assert data["date"] == "2024-01-15"
                assert data["messages_received"] == 25
                assert data["unique_contacts"] == 10

    @pytest.mark.asyncio
    async def test_get_daily_metrics_today(self, client):
        """Test getting daily metrics for today."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
            mock_metric.return_value = 50
            
            with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                mock_contacts.return_value = 20
                
                response = await client.get(f"/whatsapp-analytics/daily/{today}")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_daily_metrics_no_data(self, client):
        """Test getting daily metrics when no data exists."""
        with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
            mock_metric.return_value = 0
            
            with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                mock_contacts.return_value = 0
                
                response = await client.get("/whatsapp-analytics/daily/2020-01-01")
                assert response.status_code == 200
                data = response.json()
                assert data["messages_received"] == 0
                assert data["unique_contacts"] == 0

    @pytest.mark.asyncio
    async def test_get_daily_metrics_error(self, client):
        """Test getting daily metrics handles errors."""
        with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
            mock_metric.side_effect = Exception("Redis error")
            
            response = await client.get("/whatsapp-analytics/daily/2024-01-15")
            assert response.status_code == 500


# ============================================
# INTEGRATION TESTS - Alerts
# ============================================

class TestAlertsEndpoint:
    """Tests for /alerts endpoint."""

    @pytest.mark.asyncio
    async def test_get_alerts_all_ok(self, client):
        """Test getting alerts when everything is OK."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
                # 100 messages, 5 transfers = 5% transfer rate (OK)
                def metric_side_effect(date, name):
                    if name == "messages_received":
                        return 100
                    elif name == "human_transfers":
                        return 5  # Low transfer rate
                    return 0
                
                mock_metric.side_effect = metric_side_effect
                
                response = await client.get("/whatsapp-analytics/alerts")
                assert response.status_code == 200
                data = response.json()
                assert "alerts" in data
                # No high transfer rate alert because rate is low
                assert not any("Taxa de Transferência" in a["title"] for a in data["alerts"])

    @pytest.mark.asyncio
    async def test_get_alerts_disconnected(self, client):
        """Test getting alerts when WhatsApp is disconnected."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
                mock_metric.return_value = 0
                
                response = await client.get("/whatsapp-analytics/alerts")
                assert response.status_code == 200
                data = response.json()
                assert len(data["alerts"]) >= 1
                assert any(a["title"] == "Conexão WhatsApp" for a in data["alerts"])

    @pytest.mark.asyncio
    async def test_get_alerts_high_transfer_rate(self, client):
        """Test getting alerts when transfer rate is high."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
                # 50% transfer rate (50 transfers out of 100 messages)
                def metric_side_effect(date, name):
                    if name == "messages_received":
                        return 100
                    elif name == "human_transfers":
                        return 50
                    return 0
                
                mock_metric.side_effect = metric_side_effect
                
                response = await client.get("/whatsapp-analytics/alerts")
                assert response.status_code == 200
                data = response.json()
                assert any("Taxa de Transferência" in a["title"] for a in data["alerts"])

    @pytest.mark.asyncio
    async def test_get_alerts_error_handling(self, client):
        """Test alerts endpoint handles errors gracefully."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(side_effect=Exception("Redis error"))
            
            response = await client.get("/whatsapp-analytics/alerts")
            assert response.status_code == 200
            data = response.json()
            assert data["alerts"] == []


# ============================================
# INTEGRATION TESTS - Conversation History
# ============================================

class TestConversationHistoryEndpoint:
    """Tests for /conversations/{phone} endpoint."""

    @pytest.mark.asyncio
    async def test_get_conversation_history_success(self, client):
        """Test getting conversation history."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=[
                {"from": "user", "text": "Hello", "timestamp": "2024-01-01T12:00:00Z"},
                {"from": "bot", "text": "Hi!", "timestamp": "2024-01-01T12:00:01Z"}
            ])
            
            response = await client.get("/whatsapp-analytics/conversations/5511999999999")
            assert response.status_code == 200
            data = response.json()
            assert data["phone"] == "5511999999999"
            assert data["message_count"] == 2
            assert len(data["messages"]) == 2

    @pytest.mark.asyncio
    async def test_get_conversation_history_empty(self, client):
        """Test getting conversation history when empty."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            
            response = await client.get("/whatsapp-analytics/conversations/5511999999999")
            assert response.status_code == 200
            data = response.json()
            assert data["message_count"] == 0
            assert data["messages"] == []

    @pytest.mark.asyncio
    async def test_get_conversation_history_long(self, client):
        """Test getting long conversation history (truncated to 100)."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            messages = [
                {"from": "user", "text": f"Message {i}", "timestamp": f"2024-01-01T{i:02d}:00:00Z"}
                for i in range(150)
            ]
            mock_cache.get = AsyncMock(return_value=messages)
            
            response = await client.get("/whatsapp-analytics/conversations/5511999999999")
            assert response.status_code == 200
            data = response.json()
            assert data["message_count"] == 150
            assert len(data["messages"]) == 100  # Truncated

    @pytest.mark.asyncio
    async def test_get_conversation_history_error(self, client):
        """Test conversation history handles errors."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(side_effect=Exception("Redis error"))
            
            response = await client.get("/whatsapp-analytics/conversations/5511999999999")
            assert response.status_code == 500


# ============================================
# INTEGRATION TESTS - Reset Metrics
# ============================================

class TestResetMetricsEndpoint:
    """Tests for /reset-metrics endpoint."""

    @pytest.mark.asyncio
    async def test_reset_metrics_admin_success(self, admin_client):
        """Test resetting metrics as admin."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.delete = AsyncMock(return_value=True)
            
            response = await admin_client.post("/whatsapp-analytics/reset-metrics")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "date" in data

    @pytest.mark.asyncio
    async def test_reset_metrics_admin_specific_date(self, admin_client):
        """Test resetting metrics for specific date as admin."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.delete = AsyncMock(return_value=True)
            
            response = await admin_client.post("/whatsapp-analytics/reset-metrics?date=2024-01-15")
            assert response.status_code == 200
            data = response.json()
            assert data["date"] == "2024-01-15"

    @pytest.mark.asyncio
    async def test_reset_metrics_non_admin_forbidden(self, client):
        """Test resetting metrics as non-admin is forbidden."""
        response = await client.post("/whatsapp-analytics/reset-metrics")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_reset_metrics_error(self, admin_client):
        """Test reset metrics handles errors."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.delete = AsyncMock(side_effect=Exception("Redis error"))
            
            response = await admin_client.post("/whatsapp-analytics/reset-metrics")
            assert response.status_code == 500


# ============================================
# INTEGRATION TESTS - Health
# ============================================

class TestHealthEndpoint:
    """Tests for /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, client):
        """Test health check when healthy."""
        with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
            mock_metric.return_value = 100
            
            with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                mock_contacts.return_value = 50
                
                response = await client.get("/whatsapp-analytics/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert "date" in data
                assert "today_stats" in data
                assert data["today_stats"]["messages_received"] == 100

    @pytest.mark.asyncio
    async def test_health_check_degraded(self, client):
        """Test health check when degraded."""
        with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
            mock_metric.side_effect = Exception("Redis error")
            
            response = await client.get("/whatsapp-analytics/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert "error" in data

    @pytest.mark.asyncio
    async def test_health_check_no_metrics(self, client):
        """Test health check with no metrics."""
        with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
            mock_metric.return_value = 0
            
            with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                mock_contacts.return_value = 0
                
                response = await client.get("/whatsapp-analytics/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert data["today_stats"]["messages_received"] == 0


# ============================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================

class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_analytics_overview_default_period(self, client):
        """Test analytics uses default 7d period."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            mock_cache.smembers = AsyncMock(return_value=set())
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
                mock_metric.return_value = 0
                
                with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                    mock_contacts.return_value = 0
                    
                    with patch("api.routes.whatsapp_analytics.get_top_contacts", new_callable=AsyncMock) as mock_top:
                        mock_top.return_value = []
                        
                        response = await client.get("/whatsapp-analytics/overview")
                        assert response.status_code == 200
                        data = response.json()
                        assert data["period"] == "7d"

    @pytest.mark.asyncio
    async def test_bot_performance_calculation_zero_messages(self, client):
        """Test bot performance when no messages."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            mock_cache.smembers = AsyncMock(return_value=set())
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
                mock_metric.return_value = 0
                
                with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                    mock_contacts.return_value = 0
                    
                    with patch("api.routes.whatsapp_analytics.get_top_contacts", new_callable=AsyncMock) as mock_top:
                        mock_top.return_value = []
                        
                        response = await client.get("/whatsapp-analytics/overview")
                        assert response.status_code == 200
                        data = response.json()
                        assert data["bot_performance"]["automation_rate"] == 0.0
                        assert data["bot_performance"]["escalation_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_hourly_activity_generated(self, client):
        """Test hourly activity is generated for 24 hours."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            mock_cache.smembers = AsyncMock(return_value=set())
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
                mock_metric.return_value = 10
                
                with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                    mock_contacts.return_value = 5
                    
                    with patch("api.routes.whatsapp_analytics.get_top_contacts", new_callable=AsyncMock) as mock_top:
                        mock_top.return_value = []
                        
                        response = await client.get("/whatsapp-analytics/overview")
                        assert response.status_code == 200
                        data = response.json()
                        assert len(data["hourly_activity"]) == 24
                        hours = [h["hour"] for h in data["hourly_activity"]]
                        assert hours == list(range(24))

    @pytest.mark.asyncio
    async def test_trends_reversed_chronologically(self, client):
        """Test daily trends are in chronological order (oldest first)."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            mock_cache.smembers = AsyncMock(return_value=set())
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date", new_callable=AsyncMock) as mock_metric:
                mock_metric.return_value = 10
                
                with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date", new_callable=AsyncMock) as mock_contacts:
                    mock_contacts.return_value = 5
                    
                    with patch("api.routes.whatsapp_analytics.get_top_contacts", new_callable=AsyncMock) as mock_top:
                        mock_top.return_value = []
                        
                        response = await client.get("/whatsapp-analytics/overview?period=7d")
                        assert response.status_code == 200
                        data = response.json()
                        assert len(data["trends"]) == 7
                        # First date should be older than last date
                        first_date = data["trends"][0]["date"]
                        last_date = data["trends"][-1]["date"]
                        assert first_date < last_date

    @pytest.mark.asyncio
    async def test_masked_phone_in_top_contacts(self):
        """Test phone numbers are masked in top contacts."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.smembers = AsyncMock(return_value={"5511999998888"})
            mock_cache.get = AsyncMock(return_value=[{"timestamp": "2024-01-01T12:00:00Z"}])
            
            result = await get_top_contacts(1)
            assert len(result) == 1
            # Phone should be masked
            assert "****" in result[0].phone or "*" in result[0].phone
