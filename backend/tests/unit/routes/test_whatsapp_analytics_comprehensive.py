"""
Testes abrangentes para api/routes/whatsapp_analytics.py
Cobertura: Métricas WhatsApp, analytics, alertas, conversas
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

# ============================================
# TEST MODELS
# ============================================

class TestMetricValue:
    """Testes para MetricValue model."""
    
    def test_default_values(self):
        """Testa valores default."""
        from api.routes.whatsapp_analytics import MetricValue
        
        metric = MetricValue()
        
        assert metric.current == 0
        assert metric.previous == 0
        assert metric.change_percent == 0.0
        assert metric.trend == "stable"
    
    def test_with_values(self):
        """Testa com valores customizados."""
        from api.routes.whatsapp_analytics import MetricValue
        
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
    
    def test_trend_down(self):
        """Testa tendência de queda."""
        from api.routes.whatsapp_analytics import MetricValue
        
        metric = MetricValue(
            current=50,
            previous=100,
            change_percent=-50.0,
            trend="down"
        )
        
        assert metric.trend == "down"
        assert metric.change_percent < 0


class TestDailyMetrics:
    """Testes para DailyMetrics model."""
    
    def test_default_values(self):
        """Testa valores default."""
        from api.routes.whatsapp_analytics import DailyMetrics
        
        metrics = DailyMetrics(date="2025-01-15")
        
        assert metrics.date == "2025-01-15"
        assert metrics.messages_received == 0
        assert metrics.messages_sent == 0
        assert metrics.unique_contacts == 0
        assert metrics.product_searches == 0
        assert metrics.products_found == 0
        assert metrics.human_transfers == 0
        assert metrics.total_interactions == 0
    
    def test_with_values(self):
        """Testa com valores."""
        from api.routes.whatsapp_analytics import DailyMetrics
        
        metrics = DailyMetrics(
            date="2025-01-15",
            messages_received=100,
            messages_sent=95,
            unique_contacts=20,
            product_searches=15,
            products_found=12,
            human_transfers=5,
            total_interactions=200
        )
        
        assert metrics.messages_received == 100
        assert metrics.messages_sent == 95
        assert metrics.unique_contacts == 20


class TestHourlyActivity:
    """Testes para HourlyActivity model."""
    
    def test_hourly_activity(self):
        """Testa atividade por hora."""
        from api.routes.whatsapp_analytics import HourlyActivity
        
        activity = HourlyActivity(hour=14, count=50)
        
        assert activity.hour == 14
        assert activity.count == 50
    
    def test_default_count(self):
        """Testa count default."""
        from api.routes.whatsapp_analytics import HourlyActivity
        
        activity = HourlyActivity(hour=0)
        
        assert activity.count == 0


class TestTopContact:
    """Testes para TopContact model."""
    
    def test_top_contact(self):
        """Testa contato top."""
        from api.routes.whatsapp_analytics import TopContact
        
        contact = TopContact(
            phone="****1234",
            name="John Doe",
            message_count=50,
            last_interaction="2025-01-15T10:30:00Z"
        )
        
        assert contact.phone == "****1234"
        assert contact.name == "John Doe"
        assert contact.message_count == 50
    
    def test_minimal_contact(self):
        """Testa contato minimal."""
        from api.routes.whatsapp_analytics import TopContact
        
        contact = TopContact(phone="****5678")
        
        assert contact.phone == "****5678"
        assert contact.name is None
        assert contact.message_count == 0
        assert contact.last_interaction is None


class TestBotPerformance:
    """Testes para BotPerformance model."""
    
    def test_default_values(self):
        """Testa valores default."""
        from api.routes.whatsapp_analytics import BotPerformance
        
        perf = BotPerformance()
        
        assert perf.total_responses == 0
        assert perf.avg_response_time_ms == 0
        assert perf.automation_rate == 0.0
        assert perf.escalation_rate == 0.0
        assert perf.satisfaction_score == 0.0
    
    def test_with_values(self):
        """Testa com valores."""
        from api.routes.whatsapp_analytics import BotPerformance
        
        perf = BotPerformance(
            total_responses=500,
            avg_response_time_ms=850,
            automation_rate=92.5,
            escalation_rate=7.5,
            satisfaction_score=4.5
        )
        
        assert perf.total_responses == 500
        assert perf.automation_rate == 92.5


class TestAnalyticsOverview:
    """Testes para AnalyticsOverview model."""
    
    def test_overview_creation(self):
        """Testa criação de overview."""
        from api.routes.whatsapp_analytics import (AnalyticsOverview,
                                                   BotPerformance, MetricValue)
        
        overview = AnalyticsOverview(
            period="7d",
            messages=MetricValue(current=100, previous=80),
            contacts=MetricValue(current=20, previous=15),
            response_time_avg=850,
            satisfaction=4.2,
            trends=[],
            hourly_activity=[],
            top_contacts=[],
            bot_performance=BotPerformance(),
            connection_status="open"
        )
        
        assert overview.period == "7d"
        assert overview.messages.current == 100
        assert overview.connection_status == "open"


class TestAlert:
    """Testes para Alert model."""
    
    def test_alert_creation(self):
        """Testa criação de alerta."""
        from api.routes.whatsapp_analytics import Alert
        
        alert = Alert(
            id="conn-1",
            type="warning",
            title="Conexão WhatsApp",
            message="WhatsApp desconectado",
            timestamp="2025-01-15T10:30:00Z"
        )
        
        assert alert.id == "conn-1"
        assert alert.type == "warning"
        assert alert.title == "Conexão WhatsApp"
    
    def test_alert_types(self):
        """Testa diferentes tipos de alerta."""
        from api.routes.whatsapp_analytics import Alert
        
        for alert_type in ["warning", "error", "info"]:
            alert = Alert(
                id=f"test-{alert_type}",
                type=alert_type,
                title="Test",
                message="Test message",
                timestamp="2025-01-15T10:30:00Z"
            )
            assert alert.type == alert_type


# ============================================
# TEST HELPER FUNCTIONS
# ============================================

class TestCalculateMetricChange:
    """Testes para calculate_metric_change."""
    
    @pytest.mark.asyncio
    async def test_increase(self):
        """Testa aumento de métrica."""
        from api.routes.whatsapp_analytics import calculate_metric_change
        
        change, trend = await calculate_metric_change(120, 100)
        
        assert change == 20.0
        assert trend == "up"
    
    @pytest.mark.asyncio
    async def test_decrease(self):
        """Testa diminuição de métrica."""
        from api.routes.whatsapp_analytics import calculate_metric_change
        
        change, trend = await calculate_metric_change(80, 100)
        
        assert change == -20.0
        assert trend == "down"
    
    @pytest.mark.asyncio
    async def test_stable(self):
        """Testa métrica estável (pequena variação)."""
        from api.routes.whatsapp_analytics import calculate_metric_change
        
        change, trend = await calculate_metric_change(102, 100)
        
        assert change == 2.0
        assert trend == "stable"
    
    @pytest.mark.asyncio
    async def test_previous_zero_with_current(self):
        """Testa com previous zero e current > 0."""
        from api.routes.whatsapp_analytics import calculate_metric_change
        
        change, trend = await calculate_metric_change(50, 0)
        
        assert change == 100.0
        assert trend == "up"
    
    @pytest.mark.asyncio
    async def test_both_zero(self):
        """Testa ambos zero."""
        from api.routes.whatsapp_analytics import calculate_metric_change
        
        change, trend = await calculate_metric_change(0, 0)
        
        assert change == 0.0
        assert trend == "stable"


class TestGetMetricForDate:
    """Testes para get_metric_for_date."""
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_get_existing_metric(self, mock_cache):
        """Testa buscar métrica existente."""
        from api.routes.whatsapp_analytics import get_metric_for_date
        
        mock_cache.get = AsyncMock(return_value="150")
        
        result = await get_metric_for_date("2025-01-15", "messages_received")
        
        assert result == 150
        mock_cache.get.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_get_missing_metric(self, mock_cache):
        """Testa métrica inexistente retorna 0."""
        from api.routes.whatsapp_analytics import get_metric_for_date
        
        mock_cache.get = AsyncMock(return_value=None)
        
        result = await get_metric_for_date("2025-01-15", "unknown_metric")
        
        assert result == 0


class TestGetUniqueContactsForDate:
    """Testes para get_unique_contacts_for_date."""
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_get_contacts_existing(self, mock_cache):
        """Testa buscar contatos existentes."""
        from api.routes.whatsapp_analytics import get_unique_contacts_for_date
        
        mock_cache.smembers = AsyncMock(return_value={"5511999999999", "5511888888888", "5511777777777"})
        
        result = await get_unique_contacts_for_date("2025-01-15")
        
        assert result == 3
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_get_contacts_none(self, mock_cache):
        """Testa sem contatos."""
        from api.routes.whatsapp_analytics import get_unique_contacts_for_date
        
        mock_cache.smembers = AsyncMock(return_value=None)
        
        result = await get_unique_contacts_for_date("2025-01-15")
        
        assert result == 0


# ============================================
# TEST ROUTES
# ============================================

class TestGetAnalyticsOverview:
    """Testes para GET /overview."""
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    @patch('api.routes.whatsapp_analytics.get_top_contacts')
    async def test_overview_success(self, mock_top_contacts, mock_cache):
        """Testa overview com sucesso."""
        from api.routes.whatsapp_analytics import get_analytics_overview
        
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.smembers = AsyncMock(return_value=set())
        mock_top_contacts.return_value = []
        
        mock_user = {"id": "user-123", "email": "test@example.com"}
        
        result = await get_analytics_overview(period="7d", current_user=mock_user)
        
        assert result.period == "7d"
        assert result.messages is not None
        assert result.contacts is not None
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    @patch('api.routes.whatsapp_analytics.get_top_contacts')
    async def test_overview_14d_period(self, mock_top_contacts, mock_cache):
        """Testa overview com período de 14 dias."""
        from api.routes.whatsapp_analytics import get_analytics_overview

        # Mock get to return appropriate values based on key
        async def mock_get(key):
            if "connection" in key:
                return {"state": "open"}
            return "10"
        
        mock_cache.get = mock_get
        mock_cache.smembers = AsyncMock(return_value={"phone1", "phone2"})
        mock_top_contacts.return_value = []
        
        mock_user = {"id": "user-123"}
        
        result = await get_analytics_overview(period="14d", current_user=mock_user)
        
        assert result.period == "14d"
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_overview_error_handling(self, mock_cache):
        """Testa tratamento de erro."""
        from api.routes.whatsapp_analytics import get_analytics_overview
        from fastapi import HTTPException
        
        mock_cache.get = AsyncMock(side_effect=Exception("Redis error"))
        
        mock_user = {"id": "user-123"}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_analytics_overview(period="7d", current_user=mock_user)
        
        assert exc_info.value.status_code == 500


class TestGetDailyMetrics:
    """Testes para GET /daily/{date}."""
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.get_metric_for_date')
    @patch('api.routes.whatsapp_analytics.get_unique_contacts_for_date')
    async def test_daily_metrics_success(self, mock_contacts, mock_metric):
        """Testa métricas diárias com sucesso."""
        from api.routes.whatsapp_analytics import get_daily_metrics
        
        mock_metric.return_value = 50
        mock_contacts.return_value = 10
        
        mock_user = {"id": "user-123"}
        
        result = await get_daily_metrics(date="2025-01-15", current_user=mock_user)
        
        assert result.date == "2025-01-15"
        assert result.messages_received == 50
        assert result.unique_contacts == 10
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.get_metric_for_date')
    @patch('api.routes.whatsapp_analytics.get_unique_contacts_for_date')
    async def test_daily_metrics_error(self, mock_contacts, mock_metric):
        """Testa erro nas métricas diárias."""
        from api.routes.whatsapp_analytics import get_daily_metrics
        from fastapi import HTTPException
        
        mock_metric.side_effect = Exception("Error")
        
        mock_user = {"id": "user-123"}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_daily_metrics(date="2025-01-15", current_user=mock_user)
        
        assert exc_info.value.status_code == 500


class TestGetAlerts:
    """Testes para GET /alerts."""
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    @patch('api.routes.whatsapp_analytics.get_metric_for_date')
    async def test_alerts_connected(self, mock_metric, mock_cache):
        """Testa alertas com conexão ativa."""
        from api.routes.whatsapp_analytics import get_alerts
        
        mock_cache.get = AsyncMock(return_value={"state": "open"})
        mock_metric.return_value = 100
        
        mock_user = {"id": "user-123"}
        
        result = await get_alerts(current_user=mock_user)
        
        assert "alerts" in result
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    @patch('api.routes.whatsapp_analytics.get_metric_for_date')
    async def test_alerts_disconnected(self, mock_metric, mock_cache):
        """Testa alerta de desconexão."""
        from api.routes.whatsapp_analytics import get_alerts
        
        mock_cache.get = AsyncMock(return_value=None)
        mock_metric.return_value = 0
        
        mock_user = {"id": "user-123"}
        
        result = await get_alerts(current_user=mock_user)
        
        assert "alerts" in result
        # Deve haver alerta de conexão
        connection_alerts = [a for a in result["alerts"] if "conn" in a.id]
        assert len(connection_alerts) > 0
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    @patch('api.routes.whatsapp_analytics.get_metric_for_date')
    async def test_alerts_high_transfer_rate(self, mock_metric, mock_cache):
        """Testa alerta de alta taxa de transferência."""
        from api.routes.whatsapp_analytics import get_alerts
        
        mock_cache.get = AsyncMock(return_value={"state": "open"})
        
        # 40% de transfers
        def metric_side_effect(date, metric_name):
            if metric_name == "messages_received":
                return 100
            elif metric_name == "human_transfers":
                return 40
            return 0
        
        mock_metric.side_effect = metric_side_effect
        
        mock_user = {"id": "user-123"}
        
        result = await get_alerts(current_user=mock_user)
        
        assert "alerts" in result
        # Deve haver alerta de transfer
        transfer_alerts = [a for a in result["alerts"] if "transfer" in a.id]
        assert len(transfer_alerts) > 0
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_alerts_error_returns_empty(self, mock_cache):
        """Testa que erro retorna lista vazia."""
        from api.routes.whatsapp_analytics import get_alerts
        
        mock_cache.get = AsyncMock(side_effect=Exception("Redis error"))
        
        mock_user = {"id": "user-123"}
        
        result = await get_alerts(current_user=mock_user)
        
        assert result == {"alerts": []}


class TestGetConversationHistory:
    """Testes para GET /conversations/{phone}."""
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_conversation_success(self, mock_cache):
        """Testa buscar conversa com sucesso."""
        from api.routes.whatsapp_analytics import get_conversation_history
        
        mock_conversation = [
            {"role": "user", "content": "Olá", "timestamp": "2025-01-15T10:00:00Z"},
            {"role": "bot", "content": "Olá! Como posso ajudar?", "timestamp": "2025-01-15T10:00:01Z"}
        ]
        mock_cache.get = AsyncMock(return_value=mock_conversation)
        
        mock_user = {"id": "user-123"}
        
        result = await get_conversation_history(phone="5511999999999", current_user=mock_user)
        
        assert result["phone"] == "5511999999999"
        assert result["message_count"] == 2
        assert len(result["messages"]) == 2
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_conversation_empty(self, mock_cache):
        """Testa conversa vazia."""
        from api.routes.whatsapp_analytics import get_conversation_history
        
        mock_cache.get = AsyncMock(return_value=None)
        
        mock_user = {"id": "user-123"}
        
        result = await get_conversation_history(phone="5511999999999", current_user=mock_user)
        
        assert result["phone"] == "5511999999999"
        assert result["message_count"] == 0
        assert result["messages"] == []
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_conversation_error(self, mock_cache):
        """Testa erro ao buscar conversa."""
        from api.routes.whatsapp_analytics import get_conversation_history
        from fastapi import HTTPException
        
        mock_cache.get = AsyncMock(side_effect=Exception("Redis error"))
        
        mock_user = {"id": "user-123"}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_conversation_history(phone="5511999999999", current_user=mock_user)
        
        assert exc_info.value.status_code == 500


class TestResetMetrics:
    """Testes para POST /reset-metrics."""
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_reset_metrics_admin(self, mock_cache):
        """Testa reset por admin."""
        from api.routes.whatsapp_analytics import reset_metrics
        
        mock_cache.delete = AsyncMock()
        
        mock_admin = {"id": "admin-123", "is_admin": True}
        
        result = await reset_metrics(date="2025-01-15", current_user=mock_admin)
        
        assert result["success"] is True
        assert result["date"] == "2025-01-15"
    
    @pytest.mark.asyncio
    async def test_reset_metrics_non_admin(self):
        """Testa reset por não-admin é bloqueado."""
        from api.routes.whatsapp_analytics import reset_metrics
        from fastapi import HTTPException
        
        mock_user = {"id": "user-123", "is_admin": False}
        
        with pytest.raises(HTTPException) as exc_info:
            await reset_metrics(current_user=mock_user)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_reset_metrics_today(self, mock_cache):
        """Testa reset de hoje."""
        from api.routes.whatsapp_analytics import reset_metrics
        
        mock_cache.delete = AsyncMock()
        
        mock_admin = {"id": "admin-123", "is_admin": True}
        
        result = await reset_metrics(date=None, current_user=mock_admin)
        
        assert result["success"] is True
        # Date should be today
        assert result["date"] is not None
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_reset_metrics_error(self, mock_cache):
        """Testa erro no reset."""
        from api.routes.whatsapp_analytics import reset_metrics
        from fastapi import HTTPException
        
        mock_cache.delete = AsyncMock(side_effect=Exception("Redis error"))
        
        mock_admin = {"id": "admin-123", "is_admin": True}
        
        with pytest.raises(HTTPException) as exc_info:
            await reset_metrics(date="2025-01-15", current_user=mock_admin)
        
        assert exc_info.value.status_code == 500


class TestAnalyticsHealth:
    """Testes para GET /health."""
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.get_metric_for_date')
    @patch('api.routes.whatsapp_analytics.get_unique_contacts_for_date')
    async def test_health_healthy(self, mock_contacts, mock_metric):
        """Testa health check saudável."""
        from api.routes.whatsapp_analytics import analytics_health
        
        mock_metric.return_value = 50
        mock_contacts.return_value = 10
        
        result = await analytics_health()
        
        assert result["status"] == "healthy"
        assert "date" in result
        assert "today_stats" in result
        assert result["today_stats"]["messages_received"] == 50
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.get_metric_for_date')
    async def test_health_degraded(self, mock_metric):
        """Testa health check degradado."""
        from api.routes.whatsapp_analytics import analytics_health
        
        mock_metric.side_effect = Exception("Redis error")
        
        result = await analytics_health()
        
        assert result["status"] == "degraded"
        assert "error" in result


class TestGetTopContacts:
    """Testes para get_top_contacts helper."""
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_top_contacts_success(self, mock_cache):
        """Testa buscar top contatos."""
        from api.routes.whatsapp_analytics import get_top_contacts
        
        mock_cache.smembers = AsyncMock(return_value={"5511999999999", "5511888888888"})
        mock_cache.get = AsyncMock(return_value=[
            {"role": "user", "content": "msg1", "timestamp": "2025-01-15T10:00:00Z"},
            {"role": "bot", "content": "msg2", "timestamp": "2025-01-15T10:00:01Z"}
        ])
        
        result = await get_top_contacts(limit=5)
        
        assert isinstance(result, list)
        assert len(result) <= 5
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_top_contacts_empty(self, mock_cache):
        """Testa sem contatos."""
        from api.routes.whatsapp_analytics import get_top_contacts
        
        mock_cache.smembers = AsyncMock(return_value=None)
        
        result = await get_top_contacts(limit=5)
        
        assert result == []
    
    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_analytics.cache')
    async def test_top_contacts_error(self, mock_cache):
        """Testa erro retorna lista vazia."""
        from api.routes.whatsapp_analytics import get_top_contacts
        
        mock_cache.smembers = AsyncMock(side_effect=Exception("Error"))
        
        result = await get_top_contacts(limit=5)
        
        assert result == []


class TestRouter:
    """Testes para configuração do router."""
    
    def test_router_exists(self):
        """Testa que router existe."""
        from api.routes.whatsapp_analytics import router
        
        assert router is not None
    
    def test_router_prefix(self):
        """Testa prefixo do router."""
        from api.routes.whatsapp_analytics import router
        
        assert router.prefix == "/whatsapp-analytics"
    
    def test_router_tags(self):
        """Testa tags do router."""
        from api.routes.whatsapp_analytics import router
        
        assert "WhatsApp Analytics" in router.tags
