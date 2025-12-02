"""
Tests for WhatsApp Analytics routes
Tests analytics overview, daily metrics, alerts, and health checks.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.whatsapp_analytics import (Alert, AnalyticsOverview,
                                           BotPerformance, DailyMetrics,
                                           HourlyActivity, MetricValue,
                                           TopContact, calculate_metric_change,
                                           get_metric_for_date,
                                           get_top_contacts,
                                           get_unique_contacts_for_date)
from fastapi import HTTPException


class MockUser:
    """Mock user for auth dependency."""
    def __init__(self, **kwargs):
        self.data = {
            "id": kwargs.get("id", "user-123"),
            "email": kwargs.get("email", "test@example.com"),
            "name": kwargs.get("name", "Test User"),
            "plan": kwargs.get("plan", "premium"),
            "is_admin": kwargs.get("is_admin", False),
        }
    
    def __getitem__(self, key):
        return self.data.get(key)
    
    def get(self, key, default=None):
        return self.data.get(key, default)


# ============================================
# TEST MODELS
# ============================================

class TestMetricValueModel:
    """Tests for MetricValue model."""
    
    def test_default_values(self):
        """Should have sensible defaults."""
        metric = MetricValue()
        
        assert metric.current == 0
        assert metric.previous == 0
        assert metric.change_percent == 0.0
        assert metric.trend == "stable"
    
    def test_custom_values(self):
        """Should accept custom values."""
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
    
    def test_negative_change(self):
        """Should handle negative change."""
        metric = MetricValue(
            current=50,
            previous=100,
            change_percent=-50.0,
            trend="down"
        )
        
        assert metric.change_percent == -50.0
        assert metric.trend == "down"


class TestDailyMetricsModel:
    """Tests for DailyMetrics model."""
    
    def test_create_with_date(self):
        """Should create metrics for a date."""
        metrics = DailyMetrics(
            date="2024-01-15",
            messages_received=100,
            messages_sent=95,
            unique_contacts=50,
            product_searches=25,
            products_found=20,
            human_transfers=5,
            total_interactions=150,
        )
        
        assert metrics.date == "2024-01-15"
        assert metrics.messages_received == 100
        assert metrics.messages_sent == 95
        assert metrics.unique_contacts == 50
    
    def test_default_zeros(self):
        """Should default to zeros."""
        metrics = DailyMetrics(date="2024-01-15")
        
        assert metrics.messages_received == 0
        assert metrics.messages_sent == 0
        assert metrics.product_searches == 0


class TestHourlyActivityModel:
    """Tests for HourlyActivity model."""
    
    def test_create_activity(self):
        """Should create hourly activity."""
        activity = HourlyActivity(hour=14, count=50)
        
        assert activity.hour == 14
        assert activity.count == 50
    
    def test_default_count(self):
        """Should default count to zero."""
        activity = HourlyActivity(hour=0)
        
        assert activity.count == 0


class TestTopContactModel:
    """Tests for TopContact model."""
    
    def test_minimal_contact(self):
        """Should create contact with minimal data."""
        contact = TopContact(
            phone="***1234",
            message_count=10,
        )
        
        assert contact.phone == "***1234"
        assert contact.name is None
        assert contact.message_count == 10
        assert contact.last_interaction is None
    
    def test_full_contact(self):
        """Should create contact with all data."""
        contact = TopContact(
            phone="***5678",
            name="John Doe",
            message_count=50,
            last_interaction="2024-01-15T10:30:00Z",
        )
        
        assert contact.name == "John Doe"
        assert contact.message_count == 50
        assert contact.last_interaction is not None


class TestBotPerformanceModel:
    """Tests for BotPerformance model."""
    
    def test_default_values(self):
        """Should have sensible defaults."""
        perf = BotPerformance()
        
        assert perf.total_responses == 0
        assert perf.avg_response_time_ms == 0
        assert perf.automation_rate == 0.0
        assert perf.escalation_rate == 0.0
        assert perf.satisfaction_score == 0.0
    
    def test_high_performance(self):
        """Should represent high performance bot."""
        perf = BotPerformance(
            total_responses=1000,
            avg_response_time_ms=500,
            automation_rate=95.5,
            escalation_rate=4.5,
            satisfaction_score=4.8,
        )
        
        assert perf.automation_rate == 95.5
        assert perf.escalation_rate == 4.5
        assert perf.satisfaction_score == 4.8


class TestAlertModel:
    """Tests for Alert model."""
    
    def test_warning_alert(self):
        """Should create warning alert."""
        alert = Alert(
            id="alert-1",
            type="warning",
            title="Low Response Rate",
            message="Response rate is below 80%",
            timestamp="2024-01-15T10:00:00Z",
        )
        
        assert alert.type == "warning"
        assert alert.title == "Low Response Rate"
    
    def test_error_alert(self):
        """Should create error alert."""
        alert = Alert(
            id="alert-2",
            type="error",
            title="Connection Lost",
            message="WhatsApp disconnected",
            timestamp="2024-01-15T10:00:00Z",
        )
        
        assert alert.type == "error"


# ============================================
# TEST HELPER FUNCTIONS
# ============================================

class TestGetMetricForDate:
    """Tests for get_metric_for_date function."""
    
    @pytest.mark.asyncio
    async def test_metric_found(self):
        """Should return metric value when found."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value="100")
            
            result = await get_metric_for_date("2024-01-15", "messages_received")
            
            assert result == 100
            mock_cache.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_metric_not_found(self):
        """Should return 0 when metric not found."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            
            result = await get_metric_for_date("2024-01-15", "messages_received")
            
            assert result == 0
    
    @pytest.mark.asyncio
    async def test_metric_empty_string(self):
        """Should handle empty string value."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value="")
            
            result = await get_metric_for_date("2024-01-15", "messages_received")
            
            assert result == 0


class TestGetUniqueContactsForDate:
    """Tests for get_unique_contacts_for_date function."""
    
    @pytest.mark.asyncio
    async def test_contacts_found(self):
        """Should return count of unique contacts."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.smembers = AsyncMock(return_value={
                "5511999990001",
                "5511999990002",
                "5511999990003",
            })
            
            result = await get_unique_contacts_for_date("2024-01-15")
            
            assert result == 3
    
    @pytest.mark.asyncio
    async def test_no_contacts(self):
        """Should return 0 when no contacts."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.smembers = AsyncMock(return_value=None)
            
            result = await get_unique_contacts_for_date("2024-01-15")
            
            assert result == 0
    
    @pytest.mark.asyncio
    async def test_empty_set(self):
        """Should return 0 for empty set."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.smembers = AsyncMock(return_value=set())
            
            result = await get_unique_contacts_for_date("2024-01-15")
            
            assert result == 0


class TestCalculateMetricChange:
    """Tests for calculate_metric_change function."""
    
    @pytest.mark.asyncio
    async def test_increase(self):
        """Should calculate increase correctly."""
        change, trend = await calculate_metric_change(150, 100)
        
        assert change == 50.0
        assert trend == "up"
    
    @pytest.mark.asyncio
    async def test_decrease(self):
        """Should calculate decrease correctly."""
        change, trend = await calculate_metric_change(50, 100)
        
        assert change == -50.0
        assert trend == "down"
    
    @pytest.mark.asyncio
    async def test_stable(self):
        """Should identify stable metric."""
        change, trend = await calculate_metric_change(102, 100)
        
        assert change == 2.0
        assert trend == "stable"
    
    @pytest.mark.asyncio
    async def test_zero_previous(self):
        """Should handle zero previous value."""
        change, trend = await calculate_metric_change(100, 0)
        
        assert change == 100.0
        assert trend == "up"
    
    @pytest.mark.asyncio
    async def test_both_zero(self):
        """Should handle both values zero."""
        change, trend = await calculate_metric_change(0, 0)
        
        assert change == 0.0
        assert trend == "stable"
    
    @pytest.mark.asyncio
    async def test_threshold_exactly_5_percent(self):
        """Should be stable at exactly 5%."""
        change, trend = await calculate_metric_change(105, 100)
        
        assert change == 5.0
        assert trend == "stable"
    
    @pytest.mark.asyncio
    async def test_above_threshold(self):
        """Should be up above 5%."""
        change, trend = await calculate_metric_change(106, 100)
        
        assert change == 6.0
        assert trend == "up"


class TestGetTopContacts:
    """Tests for get_top_contacts function."""
    
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_contacts(self):
        """Should return empty list when no contacts."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.smembers = AsyncMock(return_value=None)
            
            result = await get_top_contacts(5)
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_returns_limited_contacts(self):
        """Should limit number of contacts."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.smembers = AsyncMock(return_value={
                "5511999990001",
                "5511999990002",
            })
            mock_cache.get = AsyncMock(return_value=[
                {"content": "msg1", "timestamp": "2024-01-15T10:00:00Z"},
                {"content": "msg2", "timestamp": "2024-01-15T10:05:00Z"},
            ])
            
            result = await get_top_contacts(2)
            
            assert len(result) <= 2
    
    @pytest.mark.asyncio
    async def test_handles_exception(self):
        """Should return empty list on exception."""
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.smembers = AsyncMock(side_effect=Exception("Redis error"))
            
            result = await get_top_contacts(5)
            
            assert result == []


# ============================================
# TEST ROUTES
# ============================================

class TestAnalyticsOverviewRoute:
    """Tests for analytics overview route."""
    
    @pytest.mark.asyncio
    async def test_overview_7d(self):
        """Should return 7-day overview."""
        from api.routes.whatsapp_analytics import get_analytics_overview
        
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            mock_cache.smembers = AsyncMock(return_value={"phone1", "phone2"})
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date") as mock_metric:
                mock_metric.return_value = 10
                
                with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date") as mock_contacts:
                    mock_contacts.return_value = 5
                    
                    with patch("api.routes.whatsapp_analytics.get_top_contacts") as mock_top:
                        mock_top.return_value = []
                        
                        result = await get_analytics_overview(
                            period="7d",
                            current_user=MockUser()
                        )
                        
                        assert result.period == "7d"
                        assert len(result.trends) == 7
    
    @pytest.mark.asyncio
    async def test_overview_handles_exception(self):
        """Should raise 500 on exception."""
        from api.routes.whatsapp_analytics import get_analytics_overview
        
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(side_effect=Exception("Database error"))
            
            with pytest.raises(HTTPException) as exc:
                await get_analytics_overview(
                    period="7d",
                    current_user=MockUser()
                )
            
            assert exc.value.status_code == 500


class TestDailyMetricsRoute:
    """Tests for daily metrics route."""
    
    @pytest.mark.asyncio
    async def test_get_daily_metrics(self):
        """Should return metrics for specific date."""
        from api.routes.whatsapp_analytics import get_daily_metrics
        
        with patch("api.routes.whatsapp_analytics.get_metric_for_date") as mock_metric:
            with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date") as mock_contacts:
                mock_metric.return_value = 50
                mock_contacts.return_value = 25
                
                result = await get_daily_metrics(
                    date="2024-01-15",
                    current_user=MockUser()
                )
                
                assert result.date == "2024-01-15"
                assert result.messages_received == 50
    
    @pytest.mark.asyncio
    async def test_daily_metrics_handles_exception(self):
        """Should raise 500 on exception."""
        from api.routes.whatsapp_analytics import get_daily_metrics
        
        with patch("api.routes.whatsapp_analytics.get_metric_for_date") as mock_metric:
            mock_metric.side_effect = Exception("Cache error")
            
            with pytest.raises(HTTPException) as exc:
                await get_daily_metrics(
                    date="2024-01-15",
                    current_user=MockUser()
                )
            
            assert exc.value.status_code == 500


class TestAlertsRoute:
    """Tests for alerts route."""
    
    @pytest.mark.asyncio
    async def test_get_alerts_empty(self):
        """Should return empty alerts when all healthy."""
        from api.routes.whatsapp_analytics import get_alerts
        
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date") as mock_metric:
                mock_metric.return_value = 100
                
                result = await get_alerts(current_user=MockUser())
                
                assert "alerts" in result
    
    @pytest.mark.asyncio
    async def test_get_alerts_disconnected(self):
        """Should return alert when WhatsApp disconnected."""
        from api.routes.whatsapp_analytics import get_alerts
        
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date") as mock_metric:
                mock_metric.return_value = 0
                
                result = await get_alerts(current_user=MockUser())
                
                assert len(result["alerts"]) >= 1
                assert any(a.type == "warning" for a in result["alerts"])
    
    @pytest.mark.asyncio
    async def test_get_alerts_high_transfer_rate(self):
        """Should alert on high transfer rate."""
        from api.routes.whatsapp_analytics import get_alerts
        
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            
            with patch("api.routes.whatsapp_analytics.get_metric_for_date") as mock_metric:
                # 40 transfers out of 100 messages = 40% rate
                def metric_side_effect(date, metric_name):
                    if metric_name == "messages_received":
                        return 100
                    elif metric_name == "human_transfers":
                        return 40
                    return 0
                
                mock_metric.side_effect = metric_side_effect
                
                result = await get_alerts(current_user=MockUser())
                
                assert any("Transferência" in a.title for a in result["alerts"])


class TestConversationHistoryRoute:
    """Tests for conversation history route."""
    
    @pytest.mark.asyncio
    async def test_get_conversation(self):
        """Should return conversation history."""
        from api.routes.whatsapp_analytics import get_conversation_history
        
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=[
                {"content": "Hello", "timestamp": "2024-01-15T10:00:00Z"},
                {"content": "Hi there", "timestamp": "2024-01-15T10:01:00Z"},
            ])
            
            result = await get_conversation_history(
                phone="5511999990001",
                current_user=MockUser()
            )
            
            assert result["phone"] == "5511999990001"
            assert result["message_count"] == 2
            assert len(result["messages"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_conversation_empty(self):
        """Should handle empty conversation."""
        from api.routes.whatsapp_analytics import get_conversation_history
        
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            
            result = await get_conversation_history(
                phone="5511999990001",
                current_user=MockUser()
            )
            
            assert result["message_count"] == 0
            assert result["messages"] == []
    
    @pytest.mark.asyncio
    async def test_get_conversation_handles_exception(self):
        """Should raise 500 on exception."""
        from api.routes.whatsapp_analytics import get_conversation_history
        
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.get = AsyncMock(side_effect=Exception("Redis error"))
            
            with pytest.raises(HTTPException) as exc:
                await get_conversation_history(
                    phone="5511999990001",
                    current_user=MockUser()
                )
            
            assert exc.value.status_code == 500


class TestResetMetricsRoute:
    """Tests for reset metrics route."""
    
    @pytest.mark.asyncio
    async def test_reset_requires_admin(self):
        """Should require admin access."""
        from api.routes.whatsapp_analytics import reset_metrics
        
        with pytest.raises(HTTPException) as exc:
            await reset_metrics(current_user=MockUser(is_admin=False))
        
        assert exc.value.status_code == 403
        assert "Admin only" in exc.value.detail
    
    @pytest.mark.asyncio
    async def test_reset_as_admin(self):
        """Should reset metrics as admin."""
        from api.routes.whatsapp_analytics import reset_metrics
        
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.delete = AsyncMock()
            
            result = await reset_metrics(
                date="2024-01-15",
                current_user=MockUser(is_admin=True)
            )
            
            assert result["success"] is True
            assert result["date"] == "2024-01-15"
    
    @pytest.mark.asyncio
    async def test_reset_uses_today_if_no_date(self):
        """Should use today's date if not specified."""
        from api.routes.whatsapp_analytics import reset_metrics
        
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.delete = AsyncMock()
            
            result = await reset_metrics(
                current_user=MockUser(is_admin=True)
            )
            
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            assert result["date"] == today
    
    @pytest.mark.asyncio
    async def test_reset_handles_exception(self):
        """Should raise 500 on exception."""
        from api.routes.whatsapp_analytics import reset_metrics
        
        with patch("api.routes.whatsapp_analytics.cache") as mock_cache:
            mock_cache.delete = AsyncMock(side_effect=Exception("Redis error"))
            
            with pytest.raises(HTTPException) as exc:
                await reset_metrics(
                    current_user=MockUser(is_admin=True)
                )
            
            assert exc.value.status_code == 500


class TestHealthRoute:
    """Tests for analytics health route."""
    
    @pytest.mark.asyncio
    async def test_health_healthy(self):
        """Should return healthy status."""
        from api.routes.whatsapp_analytics import analytics_health
        
        with patch("api.routes.whatsapp_analytics.get_metric_for_date") as mock_metric:
            with patch("api.routes.whatsapp_analytics.get_unique_contacts_for_date") as mock_contacts:
                mock_metric.return_value = 50
                mock_contacts.return_value = 10
                
                result = await analytics_health()
                
                assert result["status"] == "healthy"
                assert "today_stats" in result
                assert result["today_stats"]["messages_received"] == 50
    
    @pytest.mark.asyncio
    async def test_health_degraded(self):
        """Should return degraded on exception."""
        from api.routes.whatsapp_analytics import analytics_health
        
        with patch("api.routes.whatsapp_analytics.get_metric_for_date") as mock_metric:
            mock_metric.side_effect = Exception("Cache unavailable")
            
            result = await analytics_health()
            
            assert result["status"] == "degraded"
            assert "error" in result


# ============================================
# TEST EDGE CASES
# ============================================

class TestEdgeCases:
    """Edge case tests."""
    
    def test_analytics_overview_model_complete(self):
        """Should create complete analytics overview."""
        overview = AnalyticsOverview(
            period="30d",
            messages=MetricValue(current=1000, previous=800, change_percent=25.0, trend="up"),
            contacts=MetricValue(current=500, previous=400, change_percent=25.0, trend="up"),
            response_time_avg=500,
            satisfaction=4.5,
            trends=[
                DailyMetrics(date="2024-01-15", messages_received=100)
            ],
            hourly_activity=[
                HourlyActivity(hour=10, count=50)
            ],
            top_contacts=[
                TopContact(phone="***1234", message_count=20)
            ],
            bot_performance=BotPerformance(
                total_responses=900,
                automation_rate=90.0
            ),
            connection_status="open"
        )
        
        assert overview.period == "30d"
        assert overview.connection_status == "open"
        assert len(overview.trends) == 1
        assert len(overview.hourly_activity) == 1
        assert len(overview.top_contacts) == 1
    
    @pytest.mark.asyncio
    async def test_metric_change_with_large_numbers(self):
        """Should handle large numbers correctly."""
        change, trend = await calculate_metric_change(1000000, 500000)
        
        assert change == 100.0
        assert trend == "up"
    
    @pytest.mark.asyncio
    async def test_metric_change_with_small_decrease(self):
        """Should correctly identify small decreases."""
        change, trend = await calculate_metric_change(94, 100)
        
        assert change == -6.0
        assert trend == "down"
    
    def test_alert_with_long_message(self):
        """Should handle long alert messages."""
        long_message = "A" * 500
        
        alert = Alert(
            id="long-1",
            type="warning",
            title="Long Alert",
            message=long_message,
            timestamp="2024-01-15T10:00:00Z"
        )
        
        assert len(alert.message) == 500
    
    def test_phone_masking_in_top_contact(self):
        """Should handle phone masking properly."""
        contact = TopContact(
            phone="5511999991234"[-4:].rjust(14, '*'),
            message_count=10
        )
        
        assert contact.phone.endswith("1234")
        assert "*" in contact.phone
