"""
Testes extensivos para Automation Dashboard Routes
Aumenta cobertura de api/routes/automation_dashboard.py
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
import pytest_asyncio

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_current_user():
    return {"id": "user-123", "email": "test@test.com"}


@pytest.fixture
def mock_orchestrator():
    """Mock AutomationOrchestrator."""
    orchestrator = MagicMock()
    orchestrator.automations = {}
    orchestrator.is_configured = True
    return orchestrator


@pytest.fixture
def mock_scheduler():
    """Mock AutomationScheduler."""
    scheduler = MagicMock()
    scheduler.get_stats = MagicMock()
    scheduler.get_queue_depth = MagicMock(return_value={"high": 0, "normal": 0, "low": 0})
    scheduler.get_pending_events = MagicMock(return_value=[])
    scheduler.get_scheduled_events = MagicMock(return_value=[])
    scheduler.schedule_event = AsyncMock()
    scheduler.cancel_event = AsyncMock(return_value=True)
    scheduler.retry_event = AsyncMock(return_value=True)
    return scheduler


@pytest.fixture
def mock_stats():
    """Mock scheduler stats."""
    stats = MagicMock()
    stats.total_pending = 5
    stats.total_processing = 2
    stats.total_completed = 100
    stats.total_failed = 10
    stats.avg_processing_time_ms = 150.5
    stats.events_per_type = {}
    return stats


# ============================================
# TEST MODELS
# ============================================

class TestTimeRange:
    """Testes para TimeRange enum."""

    def test_time_range_values(self):
        """Testa valores do TimeRange."""
        from api.routes.automation_dashboard import TimeRange
        
        assert TimeRange.HOUR.value == "1h"
        assert TimeRange.DAY.value == "24h"
        assert TimeRange.WEEK.value == "7d"
        assert TimeRange.MONTH.value == "30d"


class TestDashboardOverview:
    """Testes para DashboardOverview schema."""

    def test_creates_overview(self):
        """Testa criação de overview."""
        from api.routes.automation_dashboard import DashboardOverview
        
        overview = DashboardOverview(
            total_automations=10,
            active_automations=5,
            pending_events=20,
            processing_events=3,
            completed_today=100,
            failed_today=5,
            success_rate=95.23,
            avg_processing_time_ms=150.5
        )
        
        assert overview.total_automations == 10
        assert overview.active_automations == 5
        assert overview.success_rate == 95.23


class TestAutomationMetrics:
    """Testes para AutomationMetrics schema."""

    def test_creates_metrics(self):
        """Testa criação de métricas."""
        from api.routes.automation_dashboard import AutomationMetrics
        
        metrics = AutomationMetrics(
            automation_type="welcome_message",
            display_name="Welcome Message",
            enabled=True,
            total_triggers=1000,
            successful=950,
            failed=50,
            pending=10,
            success_rate=95.0,
            avg_delay_ms=100.0,
            last_triggered=datetime.now(timezone.utc),
            channels=["whatsapp", "telegram"]
        )
        
        assert metrics.automation_type == "welcome_message"
        assert metrics.enabled == True
        assert len(metrics.channels) == 2


class TestScheduledEventResponse:
    """Testes para ScheduledEventResponse schema."""

    def test_creates_response(self):
        """Testa criação de resposta."""
        from api.routes.automation_dashboard import ScheduledEventResponse
        
        response = ScheduledEventResponse(
            id="event-123",
            automation_type="follow_up",
            schedule_type="delayed",
            user_id="user-123",
            status="pending",
            scheduled_for=datetime.now(timezone.utc),
            priority="high",
            retry_count=0,
            created_at=datetime.now(timezone.utc),
            processed_at=None,
            error_message=None
        )
        
        assert response.id == "event-123"
        assert response.priority == "high"


class TestQueueDepthResponse:
    """Testes para QueueDepthResponse schema."""

    def test_creates_response(self):
        """Testa criação de resposta."""
        from api.routes.automation_dashboard import QueueDepthResponse
        
        response = QueueDepthResponse(
            high=5,
            normal=10,
            low=3,
            total=18
        )
        
        assert response.total == 18


class TestScheduleEventRequest:
    """Testes para ScheduleEventRequest schema."""

    def test_creates_request(self):
        """Testa criação de request."""
        from api.routes.automation_dashboard import ScheduleEventRequest
        
        request = ScheduleEventRequest(
            automation_type="welcome_message",
            user_id="user-123",
            data={"name": "John"},
            delay_minutes=30,
            priority="high"
        )
        
        assert request.delay_minutes == 30
        assert request.priority == "high"


# ============================================
# TEST HEALTH ENDPOINT
# ============================================

class TestDashboardHealth:
    """Testes para GET /health."""

    @pytest.mark.asyncio
    async def test_returns_healthy_when_available(self, mock_orchestrator, mock_scheduler):
        """Retorna healthy quando módulo disponível."""
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True), \
             patch('api.routes.automation_dashboard.get_orchestrator', return_value=mock_orchestrator), \
             patch('api.routes.automation_dashboard.get_scheduler', return_value=mock_scheduler):
            
            from api.routes.automation_dashboard import dashboard_health
            result = await dashboard_health()
            
            assert result["status"] == "healthy"
            assert result["automation_available"] == True
            assert result["components"]["orchestrator"] == True

    @pytest.mark.asyncio
    async def test_returns_unavailable_when_module_not_available(self):
        """Retorna unavailable quando módulo não disponível."""
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            from api.routes.automation_dashboard import dashboard_health
            result = await dashboard_health()
            
            assert result["status"] == "unavailable"
            assert result["automation_available"] == False

    @pytest.mark.asyncio
    async def test_returns_degraded_on_error(self):
        """Retorna degraded em caso de erro."""
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True), \
             patch('api.routes.automation_dashboard.get_orchestrator', side_effect=Exception("Error")):
            
            from api.routes.automation_dashboard import dashboard_health
            result = await dashboard_health()
            
            assert result["status"] == "degraded"
            assert "error" in result


# ============================================
# TEST OVERVIEW ENDPOINT
# ============================================

class TestGetDashboardOverview:
    """Testes para GET /overview."""

    @pytest.mark.asyncio
    async def test_returns_overview(self, mock_current_user, mock_orchestrator, mock_scheduler, mock_stats):
        """Retorna overview com sucesso."""
        mock_scheduler.get_stats.return_value = mock_stats
        
        # Add some automations
        mock_automation = MagicMock()
        mock_automation.enabled = True
        mock_orchestrator.automations = {"type1": mock_automation}
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True), \
             patch('api.routes.automation_dashboard.get_orchestrator', return_value=mock_orchestrator), \
             patch('api.routes.automation_dashboard.get_scheduler', return_value=mock_scheduler):
            
            from api.routes.automation_dashboard import get_dashboard_overview
            result = await get_dashboard_overview(current_user=mock_current_user)
            
            assert result.total_automations == 1
            assert result.active_automations == 1
            assert result.pending_events == 5

    @pytest.mark.asyncio
    async def test_returns_503_when_not_available(self, mock_current_user):
        """Retorna 503 quando módulo não disponível."""
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            from api.routes.automation_dashboard import get_dashboard_overview
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_overview(current_user=mock_current_user)
            
            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_calculates_success_rate(self, mock_current_user, mock_orchestrator, mock_scheduler, mock_stats):
        """Calcula taxa de sucesso corretamente."""
        mock_stats.total_completed = 90
        mock_stats.total_failed = 10
        mock_scheduler.get_stats.return_value = mock_stats
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True), \
             patch('api.routes.automation_dashboard.get_orchestrator', return_value=mock_orchestrator), \
             patch('api.routes.automation_dashboard.get_scheduler', return_value=mock_scheduler):
            
            from api.routes.automation_dashboard import get_dashboard_overview
            result = await get_dashboard_overview(current_user=mock_current_user)
            
            # 90 / (90 + 10) * 100 = 90%
            assert result.success_rate == 90.0

    @pytest.mark.asyncio
    async def test_handles_zero_processed(self, mock_current_user, mock_orchestrator, mock_scheduler, mock_stats):
        """Trata zero processados."""
        mock_stats.total_completed = 0
        mock_stats.total_failed = 0
        mock_scheduler.get_stats.return_value = mock_stats
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True), \
             patch('api.routes.automation_dashboard.get_orchestrator', return_value=mock_orchestrator), \
             patch('api.routes.automation_dashboard.get_scheduler', return_value=mock_scheduler):
            
            from api.routes.automation_dashboard import get_dashboard_overview
            result = await get_dashboard_overview(current_user=mock_current_user)
            
            assert result.success_rate == 100.0


# ============================================
# TEST ALL METRICS ENDPOINT
# ============================================

class TestGetAllMetrics:
    """Testes para GET /metrics."""

    @pytest.mark.asyncio
    async def test_returns_metrics(self, mock_current_user, mock_orchestrator, mock_scheduler, mock_stats):
        """Retorna métricas com sucesso."""
        mock_scheduler.get_stats.return_value = mock_stats
        
        # Mock automation type enum
        MockAutoType = MagicMock()
        MockAutoType.value = "welcome"
        
        mock_config = MagicMock()
        mock_config.name = "Welcome Message"
        mock_config.enabled = True
        mock_config.channels = []
        
        mock_orchestrator.automations = {MockAutoType: mock_config}
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True), \
             patch('api.routes.automation_dashboard.get_orchestrator', return_value=mock_orchestrator), \
             patch('api.routes.automation_dashboard.get_scheduler', return_value=mock_scheduler):
            
            from api.routes.automation_dashboard import (TimeRange,
                                                         get_all_metrics)
            result = await get_all_metrics(
                time_range=TimeRange.DAY,
                current_user=mock_current_user
            )
            
            assert "metrics" in result
            assert result["time_range"] == "24h"

    @pytest.mark.asyncio
    async def test_returns_503_when_not_available(self, mock_current_user):
        """Retorna 503 quando módulo não disponível."""
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            from api.routes.automation_dashboard import (TimeRange,
                                                         get_all_metrics)
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_all_metrics(
                    time_range=TimeRange.DAY,
                    current_user=mock_current_user
                )
            
            assert exc_info.value.status_code == 503


# ============================================
# TEST AUTOMATION METRICS ENDPOINT
# ============================================

class TestGetAutomationMetrics:
    """Testes para GET /metrics/{automation_type}."""

    @pytest.mark.asyncio
    async def test_returns_503_when_not_available(self, mock_current_user):
        """Retorna 503 quando módulo não disponível."""
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            from api.routes.automation_dashboard import (
                TimeRange, get_automation_metrics)
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_automation_metrics(
                    automation_type="welcome",
                    time_range=TimeRange.DAY,
                    current_user=mock_current_user
                )
            
            assert exc_info.value.status_code == 503


# ============================================
# TEST QUEUE DEPTH ENDPOINT
# ============================================

class TestGetQueueDepth:
    """Testes para GET /queue/depth."""

    @pytest.mark.asyncio
    async def test_returns_queue_depth(self, mock_current_user, mock_orchestrator, mock_scheduler):
        """Retorna profundidade da fila."""
        mock_scheduler.get_queue_depth.return_value = {
            "high": 5,
            "normal": 10,
            "low": 3
        }
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True), \
             patch('api.routes.automation_dashboard.get_orchestrator', return_value=mock_orchestrator), \
             patch('api.routes.automation_dashboard.get_scheduler', return_value=mock_scheduler):
            
            from api.routes.automation_dashboard import get_queue_depth
            result = await get_queue_depth(current_user=mock_current_user)
            
            assert result.high == 5
            assert result.normal == 10
            assert result.low == 3
            assert result.total == 18

    @pytest.mark.asyncio
    async def test_returns_503_when_not_available(self, mock_current_user):
        """Retorna 503 quando módulo não disponível."""
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            from api.routes.automation_dashboard import get_queue_depth
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_queue_depth(current_user=mock_current_user)
            
            assert exc_info.value.status_code == 503


# ============================================
# TEST LIST QUEUED EVENTS
# ============================================

class TestListQueuedEvents:
    """Testes para GET /queue/events."""

    @pytest.mark.asyncio
    async def test_returns_503_when_not_available(self, mock_current_user):
        """Retorna 503 quando módulo não disponível."""
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            from api.routes.automation_dashboard import list_queued_events
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await list_queued_events(current_user=mock_current_user)
            
            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_returns_events(self, mock_current_user, mock_orchestrator, mock_scheduler):
        """Retorna eventos da fila."""
        mock_event = MagicMock()
        mock_event.id = "event-1"
        mock_event.automation_type = MagicMock()
        mock_event.automation_type.value = "welcome"
        mock_event.schedule_type = MagicMock()
        mock_event.schedule_type.value = "delayed"
        mock_event.user_id = "user-1"
        mock_event.status = MagicMock()
        mock_event.status.value = "pending"
        mock_event.scheduled_for = datetime.now(timezone.utc)
        mock_event.priority = MagicMock()
        mock_event.priority.value = "normal"
        mock_event.retry_count = 0
        mock_event.created_at = datetime.now(timezone.utc)
        mock_event.processed_at = None
        mock_event.error_message = None
        
        mock_scheduler.get_pending_events.return_value = [mock_event]
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True), \
             patch('api.routes.automation_dashboard.get_orchestrator', return_value=mock_orchestrator), \
             patch('api.routes.automation_dashboard.get_scheduler', return_value=mock_scheduler):
            
            from api.routes.automation_dashboard import list_queued_events
            result = await list_queued_events(
                status=None,
                automation_type=None,
                user_id=None,
                limit=50,
                current_user=mock_current_user
            )
            
            assert "events" in result
            assert result["total"] == 1


# ============================================
# TEST TIME SERIES DATA
# ============================================

class TestTimeSeriesDataPoint:
    """Testes para TimeSeriesDataPoint schema."""

    def test_creates_data_point(self):
        """Testa criação de data point."""
        from api.routes.automation_dashboard import TimeSeriesDataPoint
        
        point = TimeSeriesDataPoint(
            timestamp=datetime.now(timezone.utc),
            value=42.5
        )
        
        assert point.value == 42.5


# ============================================
# TEST ERROR HANDLING
# ============================================

class TestErrorHandling:
    """Testes para tratamento de erros."""

    @pytest.mark.asyncio
    async def test_overview_handles_exception(self, mock_current_user, mock_orchestrator):
        """Overview trata exceção."""
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True), \
             patch('api.routes.automation_dashboard.get_orchestrator', return_value=mock_orchestrator), \
             patch('api.routes.automation_dashboard.get_scheduler', side_effect=Exception("Error")):
            
            from api.routes.automation_dashboard import get_dashboard_overview
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_overview(current_user=mock_current_user)
            
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_metrics_handles_exception(self, mock_current_user, mock_orchestrator):
        """Metrics trata exceção."""
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True), \
             patch('api.routes.automation_dashboard.get_orchestrator', return_value=mock_orchestrator), \
             patch('api.routes.automation_dashboard.get_scheduler', side_effect=Exception("Error")):
            
            from api.routes.automation_dashboard import (TimeRange,
                                                         get_all_metrics)
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_all_metrics(
                    time_range=TimeRange.DAY,
                    current_user=mock_current_user
                )
            
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_queue_depth_handles_exception(self, mock_current_user, mock_orchestrator):
        """Queue depth trata exceção."""
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True), \
             patch('api.routes.automation_dashboard.get_orchestrator', return_value=mock_orchestrator), \
             patch('api.routes.automation_dashboard.get_scheduler', side_effect=Exception("Error")):
            
            from api.routes.automation_dashboard import get_queue_depth
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_queue_depth(current_user=mock_current_user)
            
            assert exc_info.value.status_code == 500
