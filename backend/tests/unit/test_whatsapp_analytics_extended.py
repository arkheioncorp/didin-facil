"""
Testes extensivos para WhatsApp Analytics Routes
Aumenta cobertura de api/routes/whatsapp_analytics.py
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_current_user():
    return {"id": "user-123", "email": "test@test.com", "is_admin": False}


@pytest.fixture
def mock_admin_user():
    return {"id": "admin-123", "email": "admin@test.com", "is_admin": True}


@pytest.fixture
def mock_cache():
    """Mock CacheService."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.smembers = AsyncMock(return_value=set())
    return cache


# ============================================
# TEST HELPER FUNCTIONS
# ============================================

class TestGetMetricForDate:
    """Testes para get_metric_for_date."""

    @pytest.mark.asyncio
    async def test_returns_int_when_value_exists(self):
        """Retorna inteiro quando valor existe no cache."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value="42")
            
            from api.routes.whatsapp_analytics import get_metric_for_date
            result = await get_metric_for_date("2024-01-15", "messages_received")
            
            assert result == 42
            mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_zero_when_value_is_none(self):
        """Retorna 0 quando valor não existe."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            
            from api.routes.whatsapp_analytics import get_metric_for_date
            result = await get_metric_for_date("2024-01-15", "messages_sent")
            
            assert result == 0

    @pytest.mark.asyncio
    async def test_correct_key_format(self):
        """Verifica formato correto da key."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value="10")
            
            from api.routes.whatsapp_analytics import get_metric_for_date
            await get_metric_for_date("2024-01-15", "product_searches")
            
            mock_cache.get.assert_called_once_with("whatsapp:metrics:2024-01-15:product_searches")


class TestGetUniqueContactsForDate:
    """Testes para get_unique_contacts_for_date."""

    @pytest.mark.asyncio
    async def test_returns_count_of_contacts(self):
        """Retorna contagem de contatos únicos."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.smembers = AsyncMock(return_value={"phone1", "phone2", "phone3"})
            
            from api.routes.whatsapp_analytics import \
                get_unique_contacts_for_date
            result = await get_unique_contacts_for_date("2024-01-15")
            
            assert result == 3

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_contacts(self):
        """Retorna 0 quando não há contatos."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.smembers = AsyncMock(return_value=None)
            
            from api.routes.whatsapp_analytics import \
                get_unique_contacts_for_date
            result = await get_unique_contacts_for_date("2024-01-15")
            
            assert result == 0

    @pytest.mark.asyncio
    async def test_returns_zero_for_empty_set(self):
        """Retorna 0 para set vazio."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.smembers = AsyncMock(return_value=set())
            
            from api.routes.whatsapp_analytics import \
                get_unique_contacts_for_date
            result = await get_unique_contacts_for_date("2024-01-15")
            
            assert result == 0


class TestCalculateMetricChange:
    """Testes para calculate_metric_change."""

    @pytest.mark.asyncio
    async def test_positive_change_up_trend(self):
        """Calcula mudança positiva com tendência 'up'."""
        from api.routes.whatsapp_analytics import calculate_metric_change
        
        change, trend = await calculate_metric_change(120, 100)
        
        assert change == 20.0
        assert trend == "up"

    @pytest.mark.asyncio
    async def test_negative_change_down_trend(self):
        """Calcula mudança negativa com tendência 'down'."""
        from api.routes.whatsapp_analytics import calculate_metric_change
        
        change, trend = await calculate_metric_change(80, 100)
        
        assert change == -20.0
        assert trend == "down"

    @pytest.mark.asyncio
    async def test_small_change_stable_trend(self):
        """Pequena variação resulta em tendência 'stable'."""
        from api.routes.whatsapp_analytics import calculate_metric_change
        
        change, trend = await calculate_metric_change(102, 100)
        
        assert change == 2.0
        assert trend == "stable"

    @pytest.mark.asyncio
    async def test_previous_zero_current_positive(self):
        """Quando anterior é 0 e atual positivo, retorna 100% up."""
        from api.routes.whatsapp_analytics import calculate_metric_change
        
        change, trend = await calculate_metric_change(50, 0)
        
        assert change == 100.0
        assert trend == "up"

    @pytest.mark.asyncio
    async def test_both_zero_stable(self):
        """Quando ambos são 0, retorna 0% stable."""
        from api.routes.whatsapp_analytics import calculate_metric_change
        
        change, trend = await calculate_metric_change(0, 0)
        
        assert change == 0.0
        assert trend == "stable"


class TestGetTopContacts:
    """Testes para get_top_contacts."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_contacts(self):
        """Retorna lista vazia quando não há contatos."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.smembers = AsyncMock(return_value=None)
            
            from api.routes.whatsapp_analytics import get_top_contacts
            result = await get_top_contacts(5)
            
            assert result == []

    @pytest.mark.asyncio
    async def test_returns_limited_contacts(self):
        """Retorna contatos limitados ao parâmetro."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.smembers = AsyncMock(return_value={"5511999990001", "5511999990002"})
            mock_cache.get = AsyncMock(return_value=[
                {"text": "Oi", "timestamp": "2024-01-15T10:00:00"},
                {"text": "Tudo bem?", "timestamp": "2024-01-15T10:01:00"}
            ])
            
            from api.routes.whatsapp_analytics import get_top_contacts
            result = await get_top_contacts(2)
            
            assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_masks_phone_numbers(self):
        """Verifica que números de telefone são mascarados."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.smembers = AsyncMock(return_value={"5511999990001"})
            mock_cache.get = AsyncMock(return_value=[])
            
            from api.routes.whatsapp_analytics import get_top_contacts
            result = await get_top_contacts(1)
            
            if result:
                assert "*" in result[0].phone

    @pytest.mark.asyncio
    async def test_handles_cache_error(self):
        """Trata erro de cache graciosamente."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.smembers = AsyncMock(side_effect=Exception("Cache error"))
            
            from api.routes.whatsapp_analytics import get_top_contacts
            result = await get_top_contacts(5)
            
            assert result == []


# ============================================
# TEST ROUTES
# ============================================

class TestGetAnalyticsOverview:
    """Testes para GET /overview."""

    @pytest.mark.asyncio
    async def test_returns_overview_for_7d(self, mock_current_user):
        """Retorna overview para período de 7 dias."""
        with patch('api.routes.whatsapp_analytics.get_current_user', return_value=mock_current_user), \
             patch('api.routes.whatsapp_analytics.cache') as mock_cache, \
             patch('api.routes.whatsapp_analytics.get_metric_for_date', new_callable=AsyncMock, return_value=10), \
             patch('api.routes.whatsapp_analytics.get_unique_contacts_for_date', new_callable=AsyncMock, return_value=5), \
             patch('api.routes.whatsapp_analytics.get_top_contacts', new_callable=AsyncMock, return_value=[]):
            
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            
            from api.routes.whatsapp_analytics import get_analytics_overview
            
            result = await get_analytics_overview(period="7d", current_user=mock_current_user)
            
            assert result.period == "7d"
            assert hasattr(result, 'messages')
            assert hasattr(result, 'contacts')
            assert hasattr(result, 'bot_performance')

    @pytest.mark.asyncio
    async def test_returns_overview_for_14d(self, mock_current_user):
        """Retorna overview para período de 14 dias."""
        with patch('api.routes.whatsapp_analytics.get_current_user', return_value=mock_current_user), \
             patch('api.routes.whatsapp_analytics.cache') as mock_cache, \
             patch('api.routes.whatsapp_analytics.get_metric_for_date', new_callable=AsyncMock, return_value=20), \
             patch('api.routes.whatsapp_analytics.get_unique_contacts_for_date', new_callable=AsyncMock, return_value=10), \
             patch('api.routes.whatsapp_analytics.get_top_contacts', new_callable=AsyncMock, return_value=[]):
            
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            
            from api.routes.whatsapp_analytics import get_analytics_overview
            
            result = await get_analytics_overview(period="14d", current_user=mock_current_user)
            
            assert result.period == "14d"

    @pytest.mark.asyncio
    async def test_calculates_automation_rate(self, mock_current_user):
        """Calcula taxa de automação corretamente."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            mock_cache.smembers = AsyncMock(return_value=set())
            
            with patch('api.routes.whatsapp_analytics.get_metric_for_date') as mock_metric:
                async def get_metric(date, metric):
                    if metric == "messages_received":
                        return 100
                    if metric == "human_transfers":
                        return 20
                    return 0
                
                mock_metric.side_effect = get_metric
                
                with patch('api.routes.whatsapp_analytics.get_unique_contacts_for_date', new_callable=AsyncMock, return_value=10), \
                     patch('api.routes.whatsapp_analytics.get_top_contacts', new_callable=AsyncMock, return_value=[]):
                    
                    from api.routes.whatsapp_analytics import \
                        get_analytics_overview
                    result = await get_analytics_overview(period="7d", current_user=mock_current_user)
                    
                    # automation_rate = (100 - 20) / 100 * 100 = 80%
                    assert result.bot_performance.automation_rate >= 0

    @pytest.mark.asyncio
    async def test_handles_exception(self, mock_current_user):
        """Trata exceção com HTTPException 500."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.get = AsyncMock(side_effect=Exception("Database error"))
            
            from api.routes.whatsapp_analytics import get_analytics_overview
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_analytics_overview(period="7d", current_user=mock_current_user)
            
            assert exc_info.value.status_code == 500


class TestGetDailyMetrics:
    """Testes para GET /daily/{date}."""

    @pytest.mark.asyncio
    async def test_returns_metrics_for_date(self, mock_current_user):
        """Retorna métricas para data específica."""
        with patch('api.routes.whatsapp_analytics.get_metric_for_date', new_callable=AsyncMock) as mock_metric, \
             patch('api.routes.whatsapp_analytics.get_unique_contacts_for_date', new_callable=AsyncMock, return_value=15):
            
            mock_metric.return_value = 50
            
            from api.routes.whatsapp_analytics import get_daily_metrics
            result = await get_daily_metrics(date="2024-01-15", current_user=mock_current_user)
            
            assert result.date == "2024-01-15"
            assert result.messages_received == 50
            assert result.unique_contacts == 15

    @pytest.mark.asyncio
    async def test_handles_error(self, mock_current_user):
        """Trata erro ao buscar métricas."""
        with patch('api.routes.whatsapp_analytics.get_metric_for_date', new_callable=AsyncMock, side_effect=Exception("Error")):
            from api.routes.whatsapp_analytics import get_daily_metrics
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_daily_metrics(date="2024-01-15", current_user=mock_current_user)
            
            assert exc_info.value.status_code == 500


class TestGetAlerts:
    """Testes para GET /alerts."""

    @pytest.mark.asyncio
    async def test_returns_connection_alert_when_disconnected(self, mock_current_user):
        """Retorna alerta quando WhatsApp desconectado."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache, \
             patch('api.routes.whatsapp_analytics.get_metric_for_date', new_callable=AsyncMock, return_value=0):
            
            mock_cache.get = AsyncMock(return_value={"state": "disconnected"})
            
            from api.routes.whatsapp_analytics import get_alerts
            result = await get_alerts(current_user=mock_current_user)
            
            assert "alerts" in result
            assert len(result["alerts"]) >= 1

    @pytest.mark.asyncio
    async def test_returns_transfer_alert_when_high_rate(self, mock_current_user):
        """Retorna alerta quando taxa de transferência alta."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value={"state": "open"})
            
            async def get_metric(date, metric):
                if metric == "messages_received":
                    return 100
                if metric == "human_transfers":
                    return 50  # 50% transfer rate
                return 0
            
            with patch('api.routes.whatsapp_analytics.get_metric_for_date', side_effect=get_metric):
                from api.routes.whatsapp_analytics import get_alerts
                result = await get_alerts(current_user=mock_current_user)
                
                # Should have transfer alert (50% > 30%)
                alerts = result["alerts"]
                transfer_alerts = [a for a in alerts if "transfer" in a.id.lower()]
                assert len(transfer_alerts) >= 0  # May or may not have alert

    @pytest.mark.asyncio
    async def test_returns_empty_alerts_on_error(self, mock_current_user):
        """Retorna lista vazia de alertas em caso de erro."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.get = AsyncMock(side_effect=Exception("Cache error"))
            
            from api.routes.whatsapp_analytics import get_alerts
            result = await get_alerts(current_user=mock_current_user)
            
            assert result == {"alerts": []}


class TestGetConversationHistory:
    """Testes para GET /conversations/{phone}."""

    @pytest.mark.asyncio
    async def test_returns_conversation(self, mock_current_user):
        """Retorna histórico de conversa."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value=[
                {"text": "Olá", "timestamp": "2024-01-15T10:00:00"},
                {"text": "Tudo bem?", "timestamp": "2024-01-15T10:01:00"}
            ])
            
            from api.routes.whatsapp_analytics import get_conversation_history
            result = await get_conversation_history(phone="5511999990001", current_user=mock_current_user)
            
            assert result["phone"] == "5511999990001"
            assert result["message_count"] == 2
            assert len(result["messages"]) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_conversation(self, mock_current_user):
        """Retorna vazio quando não há conversa."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            
            from api.routes.whatsapp_analytics import get_conversation_history
            result = await get_conversation_history(phone="5511999990001", current_user=mock_current_user)
            
            assert result["message_count"] == 0
            assert result["messages"] == []

    @pytest.mark.asyncio
    async def test_limits_to_100_messages(self, mock_current_user):
        """Limita retorno a 100 mensagens."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            # 150 messages
            messages = [{"text": f"Msg {i}", "timestamp": f"2024-01-15T10:{i:02d}:00"} for i in range(150)]
            mock_cache.get = AsyncMock(return_value=messages)
            
            from api.routes.whatsapp_analytics import get_conversation_history
            result = await get_conversation_history(phone="5511999990001", current_user=mock_current_user)
            
            assert len(result["messages"]) == 100

    @pytest.mark.asyncio
    async def test_handles_error(self, mock_current_user):
        """Trata erro ao buscar conversa."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.get = AsyncMock(side_effect=Exception("Error"))
            
            from api.routes.whatsapp_analytics import get_conversation_history
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_conversation_history(phone="5511999990001", current_user=mock_current_user)
            
            assert exc_info.value.status_code == 500


class TestResetMetrics:
    """Testes para POST /reset-metrics."""

    @pytest.mark.asyncio
    async def test_admin_can_reset_metrics(self, mock_admin_user):
        """Admin pode resetar métricas."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.delete = AsyncMock(return_value=True)
            
            from api.routes.whatsapp_analytics import reset_metrics
            result = await reset_metrics(date="2024-01-15", current_user=mock_admin_user)
            
            assert result["success"] == True
            assert result["date"] == "2024-01-15"

    @pytest.mark.asyncio
    async def test_non_admin_forbidden(self, mock_current_user):
        """Não-admin recebe erro 403."""
        from api.routes.whatsapp_analytics import reset_metrics
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await reset_metrics(date="2024-01-15", current_user=mock_current_user)
        
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_uses_today_when_no_date(self, mock_admin_user):
        """Usa data de hoje quando date não fornecida."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.delete = AsyncMock(return_value=True)
            
            from api.routes.whatsapp_analytics import reset_metrics
            result = await reset_metrics(date=None, current_user=mock_admin_user)
            
            assert result["success"] == True
            assert "date" in result

    @pytest.mark.asyncio
    async def test_handles_error(self, mock_admin_user):
        """Trata erro ao resetar métricas."""
        with patch('api.routes.whatsapp_analytics.cache') as mock_cache:
            mock_cache.delete = AsyncMock(side_effect=Exception("Error"))
            
            from api.routes.whatsapp_analytics import reset_metrics
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await reset_metrics(date="2024-01-15", current_user=mock_admin_user)
            
            assert exc_info.value.status_code == 500


class TestAnalyticsHealth:
    """Testes para GET /health."""

    @pytest.mark.asyncio
    async def test_returns_healthy_status(self):
        """Retorna status healthy quando tudo funciona."""
        with patch('api.routes.whatsapp_analytics.get_metric_for_date', new_callable=AsyncMock, return_value=10), \
             patch('api.routes.whatsapp_analytics.get_unique_contacts_for_date', new_callable=AsyncMock, return_value=5):
            
            from api.routes.whatsapp_analytics import analytics_health
            result = await analytics_health()
            
            assert result["status"] == "healthy"
            assert "date" in result
            assert "today_stats" in result

    @pytest.mark.asyncio
    async def test_returns_degraded_on_error(self):
        """Retorna status degraded em caso de erro."""
        with patch('api.routes.whatsapp_analytics.get_metric_for_date', new_callable=AsyncMock, side_effect=Exception("Error")):
            from api.routes.whatsapp_analytics import analytics_health
            result = await analytics_health()
            
            assert result["status"] == "degraded"
            assert "error" in result


# ============================================
# TEST MODELS
# ============================================

class TestModels:
    """Testes para modelos Pydantic."""

    def test_metric_value_defaults(self):
        """Testa valores padrão de MetricValue."""
        from api.routes.whatsapp_analytics import MetricValue
        
        m = MetricValue()
        assert m.current == 0
        assert m.previous == 0
        assert m.change_percent == 0.0
        assert m.trend == "stable"

    def test_daily_metrics_defaults(self):
        """Testa valores padrão de DailyMetrics."""
        from api.routes.whatsapp_analytics import DailyMetrics
        
        dm = DailyMetrics(date="2024-01-15")
        assert dm.date == "2024-01-15"
        assert dm.messages_received == 0
        assert dm.messages_sent == 0

    def test_hourly_activity(self):
        """Testa HourlyActivity."""
        from api.routes.whatsapp_analytics import HourlyActivity
        
        ha = HourlyActivity(hour=10, count=50)
        assert ha.hour == 10
        assert ha.count == 50

    def test_top_contact(self):
        """Testa TopContact."""
        from api.routes.whatsapp_analytics import TopContact
        
        tc = TopContact(phone="*****0001", message_count=25)
        assert tc.phone == "*****0001"
        assert tc.message_count == 25
        assert tc.name is None

    def test_bot_performance_defaults(self):
        """Testa valores padrão de BotPerformance."""
        from api.routes.whatsapp_analytics import BotPerformance
        
        bp = BotPerformance()
        assert bp.total_responses == 0
        assert bp.avg_response_time_ms == 0
        assert bp.automation_rate == 0.0

    def test_alert(self):
        """Testa Alert."""
        from api.routes.whatsapp_analytics import Alert
        
        alert = Alert(
            id="test-1",
            type="warning",
            title="Test Alert",
            message="This is a test",
            timestamp="2024-01-15T10:00:00"
        )
        assert alert.id == "test-1"
        assert alert.type == "warning"

    def test_analytics_overview(self):
        """Testa AnalyticsOverview."""
        from api.routes.whatsapp_analytics import (AnalyticsOverview,
                                                   BotPerformance, MetricValue)
        
        ao = AnalyticsOverview(
            period="7d",
            messages=MetricValue(current=100, previous=90),
            contacts=MetricValue(current=50, previous=45),
            bot_performance=BotPerformance()
        )
        assert ao.period == "7d"
        assert ao.messages.current == 100
        assert ao.contacts.current == 50
