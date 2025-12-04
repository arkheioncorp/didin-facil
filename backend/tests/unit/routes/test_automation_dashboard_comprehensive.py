"""
Testes abrangentes para api/routes/automation_dashboard.py
Cobertura: Dashboard de automações, filas, métricas, agendamento
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from pydantic import ValidationError

# ============================================
# TEST MODELS
# ============================================

class TestTimeRange:
    """Testes para TimeRange enum."""
    
    def test_time_range_values(self):
        """Testa valores do enum."""
        from api.routes.automation_dashboard import TimeRange
        
        assert TimeRange.HOUR.value == "1h"
        assert TimeRange.DAY.value == "24h"
        assert TimeRange.WEEK.value == "7d"
        assert TimeRange.MONTH.value == "30d"


class TestDashboardOverview:
    """Testes para DashboardOverview model."""
    
    def test_overview_creation(self):
        """Testa criação de overview."""
        from api.routes.automation_dashboard import DashboardOverview
        
        overview = DashboardOverview(
            total_automations=10,
            active_automations=8,
            pending_events=15,
            processing_events=2,
            completed_today=100,
            failed_today=5,
            success_rate=95.24,
            avg_processing_time_ms=250.5
        )
        
        assert overview.total_automations == 10
        assert overview.active_automations == 8
        assert overview.pending_events == 15
        assert overview.success_rate == 95.24


class TestAutomationMetrics:
    """Testes para AutomationMetrics model."""
    
    def test_metrics_creation(self):
        """Testa criação de métricas."""
        from api.routes.automation_dashboard import AutomationMetrics
        
        metrics = AutomationMetrics(
            automation_type="post_published",
            display_name="Post Published",
            enabled=True,
            total_triggers=500,
            successful=490,
            failed=10,
            pending=5,
            success_rate=98.0,
            avg_delay_ms=150.0,
            last_triggered=datetime.now(timezone.utc),
            channels=["whatsapp", "email"]
        )
        
        assert metrics.automation_type == "post_published"
        assert metrics.enabled is True
        assert metrics.success_rate == 98.0


class TestScheduledEventResponse:
    """Testes para ScheduledEventResponse model."""
    
    def test_event_response(self):
        """Testa resposta de evento."""
        from api.routes.automation_dashboard import ScheduledEventResponse
        
        now = datetime.now(timezone.utc)
        
        event = ScheduledEventResponse(
            id="event-123",
            automation_type="welcome_message",
            schedule_type="immediate",
            user_id="user-456",
            status="pending",
            scheduled_for=now,
            priority="normal",
            retry_count=0,
            created_at=now,
            processed_at=None,
            error_message=None
        )
        
        assert event.id == "event-123"
        assert event.status == "pending"
        assert event.retry_count == 0
        assert event.processed_at is None
        assert event.error_message is None


class TestQueueDepthResponse:
    """Testes para QueueDepthResponse model."""
    
    def test_queue_depth(self):
        """Testa profundidade da fila."""
        from api.routes.automation_dashboard import QueueDepthResponse
        
        depth = QueueDepthResponse(
            high=10,
            normal=50,
            low=20,
            total=80
        )
        
        assert depth.high == 10
        assert depth.normal == 50
        assert depth.total == 80


class TestTimeSeriesDataPoint:
    """Testes para TimeSeriesDataPoint model."""
    
    def test_data_point(self):
        """Testa ponto de dados."""
        from api.routes.automation_dashboard import TimeSeriesDataPoint
        
        point = TimeSeriesDataPoint(
            timestamp=datetime.now(timezone.utc),
            value=42.5
        )
        
        assert point.value == 42.5


class TestScheduleEventRequest:
    """Testes para ScheduleEventRequest model."""
    
    def test_request_minimal(self):
        """Testa request minimal."""
        from api.routes.automation_dashboard import ScheduleEventRequest
        
        request = ScheduleEventRequest(
            automation_type="welcome_message",
            user_id="user-123"
        )
        
        assert request.automation_type == "welcome_message"
        assert request.user_id == "user-123"
        assert request.data == {}
        assert request.priority == "normal"
    
    def test_request_full(self):
        """Testa request completa."""
        from api.routes.automation_dashboard import ScheduleEventRequest
        
        now = datetime.now(timezone.utc) + timedelta(hours=1)
        
        request = ScheduleEventRequest(
            automation_type="reminder",
            user_id="user-123",
            data={"message": "Hello"},
            delay_minutes=30,
            scheduled_for=now,
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
    async def test_health_automation_unavailable(self):
        """Testa health quando módulo não disponível."""
        from api.routes.automation_dashboard import dashboard_health
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            result = await dashboard_health()
            
            assert result["status"] == "unavailable"
            assert result["automation_available"] is False
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.get_orchestrator')
    @patch('api.routes.automation_dashboard.get_scheduler')
    async def test_health_healthy(self, mock_scheduler, mock_orchestrator):
        """Testa health quando saudável."""
        from api.routes.automation_dashboard import dashboard_health
        
        mock_orch = MagicMock()
        mock_orch.is_configured = True
        mock_orchestrator.return_value = mock_orch
        
        mock_sched = MagicMock()
        mock_scheduler.return_value = mock_sched
        
        result = await dashboard_health()
        
        assert result["status"] == "healthy"
        assert result["components"]["orchestrator"] is True
        assert result["components"]["n8n_connection"] is True
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.get_orchestrator')
    async def test_health_degraded(self, mock_orchestrator):
        """Testa health degradado."""
        from api.routes.automation_dashboard import dashboard_health
        
        mock_orchestrator.side_effect = Exception("Connection error")
        
        result = await dashboard_health()
        
        assert result["status"] == "degraded"
        assert "error" in result


# ============================================
# TEST OVERVIEW ENDPOINT
# ============================================

class TestGetDashboardOverview:
    """Testes para GET /overview."""
    
    @pytest.mark.asyncio
    async def test_overview_automation_unavailable(self):
        """Testa overview quando módulo não disponível."""
        from api.routes.automation_dashboard import get_dashboard_overview
        from fastapi import HTTPException
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            mock_user = {"id": "user-123"}
            
            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_overview(current_user=mock_user)
            
            assert exc_info.value.status_code == 503
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.get_orchestrator')
    @patch('api.routes.automation_dashboard.get_scheduler')
    async def test_overview_success(self, mock_scheduler, mock_orchestrator):
        """Testa overview com sucesso."""
        from api.routes.automation_dashboard import get_dashboard_overview

        # Mock orchestrator
        mock_orch = MagicMock()
        mock_orch.automations = {"type1": MagicMock(enabled=True), "type2": MagicMock(enabled=False)}
        mock_orchestrator.return_value = mock_orch
        
        # Mock scheduler stats
        mock_stats = MagicMock()
        mock_stats.total_pending = 10
        mock_stats.total_processing = 2
        mock_stats.total_completed = 100
        mock_stats.total_failed = 5
        mock_stats.avg_processing_time_ms = 250.0
        
        mock_sched = MagicMock()
        mock_sched.get_stats.return_value = mock_stats
        mock_scheduler.return_value = mock_sched
        
        mock_user = {"id": "user-123"}
        
        result = await get_dashboard_overview(current_user=mock_user)
        
        assert result.total_automations == 2
        assert result.active_automations == 1
        assert result.pending_events == 10
        assert result.completed_today == 100
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.get_orchestrator')
    async def test_overview_error(self, mock_orchestrator):
        """Testa overview com erro."""
        from api.routes.automation_dashboard import get_dashboard_overview
        from fastapi import HTTPException
        
        mock_orchestrator.side_effect = Exception("Error")
        
        mock_user = {"id": "user-123"}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_dashboard_overview(current_user=mock_user)
        
        assert exc_info.value.status_code == 500


# ============================================
# TEST METRICS ENDPOINTS
# ============================================

class TestGetAllMetrics:
    """Testes para GET /metrics."""
    
    @pytest.mark.asyncio
    async def test_metrics_automation_unavailable(self):
        """Testa métricas quando módulo não disponível."""
        from api.routes.automation_dashboard import TimeRange, get_all_metrics
        from fastapi import HTTPException
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            mock_user = {"id": "user-123"}
            
            with pytest.raises(HTTPException) as exc_info:
                await get_all_metrics(time_range=TimeRange.DAY, current_user=mock_user)
            
            assert exc_info.value.status_code == 503
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.get_orchestrator')
    @patch('api.routes.automation_dashboard.get_scheduler')
    async def test_metrics_success(self, mock_scheduler, mock_orchestrator):
        """Testa métricas com sucesso."""
        from api.routes.automation_dashboard import TimeRange, get_all_metrics

        # Mock automation type
        mock_auto_type = MagicMock()
        mock_auto_type.value = "welcome_message"
        
        # Mock config
        mock_config = MagicMock()
        mock_config.name = "Welcome Message"
        mock_config.enabled = True
        mock_config.channels = [MagicMock(value="whatsapp")]
        
        # Mock orchestrator
        mock_orch = MagicMock()
        mock_orch.automations = {mock_auto_type: mock_config}
        mock_orchestrator.return_value = mock_orch
        
        # Mock scheduler
        mock_stats = MagicMock()
        mock_stats.events_per_type = {"welcome_message": 5}
        
        mock_sched = MagicMock()
        mock_sched.get_stats.return_value = mock_stats
        mock_scheduler.return_value = mock_sched
        
        mock_user = {"id": "user-123"}
        
        result = await get_all_metrics(time_range=TimeRange.DAY, current_user=mock_user)
        
        assert "metrics" in result
        assert result["time_range"] == "24h"


class TestGetAutomationMetrics:
    """Testes para GET /metrics/{automation_type}."""
    
    @pytest.mark.asyncio
    async def test_specific_metrics_unavailable(self):
        """Testa métricas específicas quando módulo não disponível."""
        from api.routes.automation_dashboard import (TimeRange,
                                                     get_automation_metrics)
        from fastapi import HTTPException
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            mock_user = {"id": "user-123"}
            
            with pytest.raises(HTTPException) as exc_info:
                await get_automation_metrics(
                    automation_type="welcome",
                    time_range=TimeRange.DAY,
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 503
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.AutomationType')
    async def test_specific_metrics_invalid_type(self, mock_auto_type):
        """Testa métricas com tipo inválido."""
        from api.routes.automation_dashboard import (TimeRange,
                                                     get_automation_metrics)
        from fastapi import HTTPException
        
        mock_auto_type.side_effect = ValueError("Invalid type")
        
        mock_user = {"id": "user-123"}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_automation_metrics(
                automation_type="invalid",
                time_range=TimeRange.DAY,
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 404


# ============================================
# TEST QUEUE ENDPOINTS
# ============================================

class TestGetQueueDepth:
    """Testes para GET /queue/depth."""
    
    @pytest.mark.asyncio
    async def test_queue_depth_unavailable(self):
        """Testa profundidade quando módulo não disponível."""
        from api.routes.automation_dashboard import get_queue_depth
        from fastapi import HTTPException
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            mock_user = {"id": "user-123"}
            
            with pytest.raises(HTTPException) as exc_info:
                await get_queue_depth(current_user=mock_user)
            
            assert exc_info.value.status_code == 503
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.get_orchestrator')
    @patch('api.routes.automation_dashboard.get_scheduler')
    async def test_queue_depth_success(self, mock_scheduler, mock_orchestrator):
        """Testa profundidade com sucesso."""
        from api.routes.automation_dashboard import get_queue_depth
        
        mock_orch = MagicMock()
        mock_orchestrator.return_value = mock_orch
        
        mock_sched = MagicMock()
        mock_sched.get_queue_depth.return_value = {"high": 5, "normal": 20, "low": 10}
        mock_scheduler.return_value = mock_sched
        
        mock_user = {"id": "user-123"}
        
        result = await get_queue_depth(current_user=mock_user)
        
        assert result.high == 5
        assert result.normal == 20
        assert result.low == 10
        assert result.total == 35


class TestListQueuedEvents:
    """Testes para GET /queue/events."""
    
    @pytest.mark.asyncio
    async def test_list_events_unavailable(self):
        """Testa listagem quando módulo não disponível."""
        from api.routes.automation_dashboard import list_queued_events
        from fastapi import HTTPException
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            mock_user = {"id": "user-123"}
            
            with pytest.raises(HTTPException) as exc_info:
                await list_queued_events(current_user=mock_user)
            
            assert exc_info.value.status_code == 503
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.get_orchestrator')
    @patch('api.routes.automation_dashboard.get_scheduler')
    @patch('api.routes.automation_dashboard.AutomationType')
    async def test_list_events_invalid_type(self, mock_auto_type, mock_scheduler, mock_orchestrator):
        """Testa listagem com tipo inválido."""
        from api.routes.automation_dashboard import list_queued_events
        from fastapi import HTTPException
        
        mock_orch = MagicMock()
        mock_orchestrator.return_value = mock_orch
        
        mock_sched = MagicMock()
        mock_scheduler.return_value = mock_sched
        
        mock_auto_type.side_effect = ValueError("Invalid")
        
        mock_user = {"id": "user-123"}
        
        with pytest.raises(HTTPException) as exc_info:
            await list_queued_events(
                automation_type="invalid",
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 400


class TestGetEventDetails:
    """Testes para GET /queue/events/{event_id}."""
    
    @pytest.mark.asyncio
    async def test_event_details_unavailable(self):
        """Testa detalhes quando módulo não disponível."""
        from api.routes.automation_dashboard import get_event_details
        from fastapi import HTTPException
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            mock_user = {"id": "user-123"}
            
            with pytest.raises(HTTPException) as exc_info:
                await get_event_details(event_id="evt-123", current_user=mock_user)
            
            assert exc_info.value.status_code == 503
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.get_orchestrator')
    @patch('api.routes.automation_dashboard.get_scheduler')
    async def test_event_details_not_found(self, mock_scheduler, mock_orchestrator):
        """Testa evento não encontrado."""
        from api.routes.automation_dashboard import get_event_details
        from fastapi import HTTPException
        
        mock_orch = MagicMock()
        mock_orchestrator.return_value = mock_orch
        
        mock_sched = MagicMock()
        mock_sched.get_event.return_value = None
        mock_scheduler.return_value = mock_sched
        
        mock_user = {"id": "user-123"}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_event_details(event_id="not-found", current_user=mock_user)
        
        assert exc_info.value.status_code == 404


# ============================================
# TEST SCHEDULING ENDPOINTS
# ============================================

class TestScheduleEvent:
    """Testes para POST /schedule."""
    
    @pytest.mark.asyncio
    async def test_schedule_unavailable(self):
        """Testa agendamento quando módulo não disponível."""
        from api.routes.automation_dashboard import (ScheduleEventRequest,
                                                     schedule_event)
        from fastapi import HTTPException
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            request = ScheduleEventRequest(
                automation_type="welcome",
                user_id="user-123"
            )
            mock_user = {"id": "user-123"}
            
            with pytest.raises(HTTPException) as exc_info:
                await schedule_event(request=request, current_user=mock_user)
            
            assert exc_info.value.status_code == 503
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.AutomationType')
    async def test_schedule_invalid_type(self, mock_auto_type):
        """Testa agendamento com tipo inválido."""
        from api.routes.automation_dashboard import (ScheduleEventRequest,
                                                     schedule_event)
        from fastapi import HTTPException
        
        mock_auto_type.side_effect = ValueError("Invalid")
        
        request = ScheduleEventRequest(
            automation_type="invalid",
            user_id="user-123"
        )
        mock_user = {"id": "user-123"}
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_event(request=request, current_user=mock_user)
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.AutomationType')
    @patch('api.routes.automation_dashboard.AutomationPriority')
    @patch('api.routes.automation_dashboard.get_orchestrator')
    @patch('api.routes.automation_dashboard.get_scheduler')
    async def test_schedule_success(
        self, mock_scheduler, mock_orchestrator, mock_priority, mock_auto_type
    ):
        """Testa agendamento com sucesso."""
        from api.routes.automation_dashboard import (ScheduleEventRequest,
                                                     schedule_event)
        
        mock_auto_type.return_value = MagicMock()
        mock_priority.return_value = MagicMock()
        
        mock_orch = MagicMock()
        mock_orchestrator.return_value = mock_orch
        
        mock_event = MagicMock()
        mock_event.id = "evt-new-123"
        mock_event.scheduled_for = datetime.now(timezone.utc)
        
        mock_sched = MagicMock()
        mock_sched.schedule = AsyncMock(return_value=mock_event)
        mock_scheduler.return_value = mock_sched
        
        request = ScheduleEventRequest(
            automation_type="welcome_message",
            user_id="user-123",
            data={"key": "value"}
        )
        mock_user = {"id": "user-123"}
        
        result = await schedule_event(request=request, current_user=mock_user)
        
        assert result["success"] is True
        assert result["event_id"] == "evt-new-123"


class TestCancelScheduledEvent:
    """Testes para DELETE /schedule/{event_id}."""
    
    @pytest.mark.asyncio
    async def test_cancel_unavailable(self):
        """Testa cancelamento quando módulo não disponível."""
        from api.routes.automation_dashboard import cancel_scheduled_event
        from fastapi import HTTPException
        
        with patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', False):
            mock_user = {"id": "user-123"}
            
            with pytest.raises(HTTPException) as exc_info:
                await cancel_scheduled_event(event_id="evt-123", current_user=mock_user)
            
            assert exc_info.value.status_code == 503
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.get_orchestrator')
    @patch('api.routes.automation_dashboard.get_scheduler')
    async def test_cancel_not_found(self, mock_scheduler, mock_orchestrator):
        """Testa cancelar evento não encontrado."""
        from api.routes.automation_dashboard import cancel_scheduled_event
        from fastapi import HTTPException
        
        mock_orch = MagicMock()
        mock_orchestrator.return_value = mock_orch
        
        mock_sched = MagicMock()
        mock_sched.cancel = AsyncMock(return_value=False)
        mock_scheduler.return_value = mock_sched
        
        mock_user = {"id": "user-123"}
        
        with pytest.raises(HTTPException) as exc_info:
            await cancel_scheduled_event(event_id="not-found", current_user=mock_user)
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    @patch('api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True)
    @patch('api.routes.automation_dashboard.get_orchestrator')
    @patch('api.routes.automation_dashboard.get_scheduler')
    async def test_cancel_success(self, mock_scheduler, mock_orchestrator):
        """Testa cancelamento com sucesso."""
        from api.routes.automation_dashboard import cancel_scheduled_event
        
        mock_orch = MagicMock()
        mock_orchestrator.return_value = mock_orch
        
        mock_sched = MagicMock()
        mock_sched.cancel = AsyncMock(return_value=True)
        mock_scheduler.return_value = mock_sched
        
        mock_user = {"id": "user-123"}
        
        result = await cancel_scheduled_event(event_id="evt-123", current_user=mock_user)
        
        assert result["success"] is True


# ============================================
# TEST ROUTER CONFIG
# ============================================

class TestRouter:
    """Testes para configuração do router."""
    
    def test_router_exists(self):
        """Testa que router existe."""
        from api.routes.automation_dashboard import router
        
        assert router is not None
    
    def test_router_tags(self):
        """Testa tags do router."""
        from api.routes.automation_dashboard import router
        
        assert "Automation Dashboard" in router.tags


class TestAutomationAvailable:
    """Testes para AUTOMATION_AVAILABLE flag."""
    
    def test_flag_defined(self):
        """Testa que flag está definida."""
        from api.routes.automation_dashboard import AUTOMATION_AVAILABLE
        
        assert isinstance(AUTOMATION_AVAILABLE, bool)
