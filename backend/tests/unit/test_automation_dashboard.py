"""
Tests for automation dashboard routes
Tests dashboard overview, metrics, queue management, and scheduling.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
# Import models and router
from api.routes.automation_dashboard import (AUTOMATION_AVAILABLE,
                                             AutomationMetrics,
                                             DashboardOverview,
                                             QueueDepthResponse,
                                             ScheduledEventResponse,
                                             ScheduleEventRequest, TimeRange,
                                             router)
from fastapi import HTTPException
from fastapi.testclient import TestClient


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

class TestTimeRangeEnum:
    """Tests for TimeRange enum."""
    
    def test_hour_value(self):
        """Hour should be 1h."""
        assert TimeRange.HOUR.value == "1h"
    
    def test_day_value(self):
        """Day should be 24h."""
        assert TimeRange.DAY.value == "24h"
    
    def test_week_value(self):
        """Week should be 7d."""
        assert TimeRange.WEEK.value == "7d"
    
    def test_month_value(self):
        """Month should be 30d."""
        assert TimeRange.MONTH.value == "30d"
    
    def test_all_values_exist(self):
        """All time range values should exist."""
        assert len(TimeRange) == 4


class TestDashboardOverviewModel:
    """Tests for DashboardOverview model."""
    
    def test_create_overview(self):
        """Should create overview with all fields."""
        overview = DashboardOverview(
            total_automations=10,
            active_automations=7,
            pending_events=50,
            processing_events=3,
            completed_today=100,
            failed_today=5,
            success_rate=95.24,
            avg_processing_time_ms=150.5,
        )
        
        assert overview.total_automations == 10
        assert overview.active_automations == 7
        assert overview.pending_events == 50
        assert overview.processing_events == 3
        assert overview.completed_today == 100
        assert overview.failed_today == 5
        assert overview.success_rate == 95.24
        assert overview.avg_processing_time_ms == 150.5
    
    def test_overview_with_zero_success_rate(self):
        """Should handle zero success rate."""
        overview = DashboardOverview(
            total_automations=0,
            active_automations=0,
            pending_events=0,
            processing_events=0,
            completed_today=0,
            failed_today=0,
            success_rate=0.0,
            avg_processing_time_ms=0.0,
        )
        
        assert overview.success_rate == 0.0
    
    def test_overview_with_100_success_rate(self):
        """Should handle 100% success rate."""
        overview = DashboardOverview(
            total_automations=5,
            active_automations=5,
            pending_events=0,
            processing_events=0,
            completed_today=50,
            failed_today=0,
            success_rate=100.0,
            avg_processing_time_ms=75.0,
        )
        
        assert overview.success_rate == 100.0


class TestQueueDepthResponseModel:
    """Tests for QueueDepthResponse model."""
    
    def test_create_queue_depth(self):
        """Should create queue depth with all priorities."""
        depth = QueueDepthResponse(
            high=10,
            normal=50,
            low=25,
            total=85,
        )
        
        assert depth.high == 10
        assert depth.normal == 50
        assert depth.low == 25
        assert depth.total == 85
    
    def test_queue_depth_empty(self):
        """Should handle empty queue."""
        depth = QueueDepthResponse(
            high=0,
            normal=0,
            low=0,
            total=0,
        )
        
        assert depth.total == 0


class TestScheduleEventRequestModel:
    """Tests for ScheduleEventRequest model."""
    
    def test_minimal_request(self):
        """Should create request with minimal fields."""
        request = ScheduleEventRequest(
            automation_type="welcome_message",
            user_id="user-123",
        )
        
        assert request.automation_type == "welcome_message"
        assert request.user_id == "user-123"
        assert request.data == {}
        assert request.priority == "normal"
    
    def test_full_request(self):
        """Should create request with all fields."""
        scheduled = datetime.now(timezone.utc) + timedelta(hours=1)
        
        request = ScheduleEventRequest(
            automation_type="abandoned_cart",
            user_id="user-456",
            data={"cart_id": "cart-789", "items": ["product-1"]},
            delay_minutes=30,
            scheduled_for=scheduled,
            priority="high",
        )
        
        assert request.automation_type == "abandoned_cart"
        assert request.user_id == "user-456"
        assert request.data["cart_id"] == "cart-789"
        assert request.delay_minutes == 30
        assert request.scheduled_for == scheduled
        assert request.priority == "high"


class TestScheduledEventResponseModel:
    """Tests for ScheduledEventResponse model."""
    
    def test_create_response(self):
        """Should create response with all fields."""
        now = datetime.now(timezone.utc)
        scheduled = now + timedelta(minutes=30)
        
        response = ScheduledEventResponse(
            id="event-123",
            automation_type="welcome_message",
            schedule_type="delayed",
            user_id="user-456",
            status="pending",
            scheduled_for=scheduled,
            priority="normal",
            retry_count=0,
            created_at=now,
            processed_at=None,
            error_message=None,
        )
        
        assert response.id == "event-123"
        assert response.automation_type == "welcome_message"
        assert response.status == "pending"
        assert response.retry_count == 0
        assert response.processed_at is None
    
    def test_response_with_error(self):
        """Should include error message when present."""
        now = datetime.now(timezone.utc)
        
        response = ScheduledEventResponse(
            id="event-fail-1",
            automation_type="abandoned_cart",
            schedule_type="immediate",
            user_id="user-789",
            status="failed",
            scheduled_for=now,
            priority="high",
            retry_count=3,
            created_at=now - timedelta(minutes=10),
            processed_at=now,
            error_message="Connection timeout to n8n webhook",
        )
        
        assert response.status == "failed"
        assert response.retry_count == 3
        assert "timeout" in response.error_message


class TestAutomationMetricsModel:
    """Tests for AutomationMetrics model."""
    
    def test_create_metrics(self):
        """Should create metrics with all fields."""
        now = datetime.now(timezone.utc)
        
        metrics = AutomationMetrics(
            automation_type="welcome_message",
            display_name="Welcome Message",
            enabled=True,
            total_triggers=1000,
            successful=950,
            failed=50,
            pending=10,
            success_rate=95.0,
            avg_delay_ms=120.5,
            last_triggered=now,
            channels=["whatsapp", "email"],
        )
        
        assert metrics.automation_type == "welcome_message"
        assert metrics.display_name == "Welcome Message"
        assert metrics.enabled is True
        assert metrics.success_rate == 95.0
        assert len(metrics.channels) == 2
    
    def test_metrics_disabled_automation(self):
        """Should handle disabled automation."""
        metrics = AutomationMetrics(
            automation_type="upsell",
            display_name="Upsell Campaign",
            enabled=False,
            total_triggers=0,
            successful=0,
            failed=0,
            pending=0,
            success_rate=0.0,
            avg_delay_ms=0.0,
            last_triggered=None,
            channels=[],
        )
        
        assert metrics.enabled is False
        assert metrics.last_triggered is None
        assert len(metrics.channels) == 0


# ============================================
# TEST HEALTH ENDPOINT
# ============================================

class TestDashboardHealth:
    """Tests for dashboard health endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_automation_unavailable(self):
        """Should return unavailable when module not loaded."""
        from api.routes.automation_dashboard import dashboard_health
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", False):
            result = await dashboard_health()
            
            assert result["status"] == "unavailable"
            assert result["automation_available"] is False
    
    @pytest.mark.asyncio
    async def test_health_with_orchestrator(self):
        """Should check orchestrator when available."""
        from api.routes.automation_dashboard import dashboard_health
        
        mock_orchestrator = MagicMock()
        mock_orchestrator.is_configured = True
        
        mock_scheduler = MagicMock()
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                with patch("api.routes.automation_dashboard.get_scheduler") as mock_get_sched:
                    mock_get_orch.return_value = mock_orchestrator
                    mock_get_sched.return_value = mock_scheduler
                    
                    result = await dashboard_health()
                    
                    assert result["status"] == "healthy"
                    assert result["components"]["orchestrator"] is True
                    assert result["components"]["scheduler"] is True


# ============================================
# TEST OVERVIEW ENDPOINT
# ============================================

class TestDashboardOverviewEndpoint:
    """Tests for overview endpoint."""
    
    @pytest.mark.asyncio
    async def test_overview_automation_unavailable(self):
        """Should raise 503 when automation unavailable."""
        from api.routes.automation_dashboard import get_dashboard_overview
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc:
                await get_dashboard_overview(current_user=MockUser())
            
            assert exc.value.status_code == 503
            assert "não disponível" in exc.value.detail
    
    @pytest.mark.asyncio
    async def test_overview_success(self):
        """Should return overview data."""
        from api.routes.automation_dashboard import get_dashboard_overview
        
        mock_stats = MagicMock()
        mock_stats.total_pending = 10
        mock_stats.total_processing = 2
        mock_stats.total_completed = 100
        mock_stats.total_failed = 5
        mock_stats.avg_processing_time_ms = 150.0
        
        mock_automation = MagicMock()
        mock_automation.enabled = True
        
        mock_orchestrator = MagicMock()
        mock_orchestrator.automations = {"type1": mock_automation}
        
        mock_scheduler = MagicMock()
        mock_scheduler.get_stats.return_value = mock_stats
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                with patch("api.routes.automation_dashboard.get_scheduler") as mock_get_sched:
                    mock_get_orch.return_value = mock_orchestrator
                    mock_get_sched.return_value = mock_scheduler
                    
                    result = await get_dashboard_overview(current_user=MockUser())
                    
                    assert result.total_automations == 1
                    assert result.active_automations == 1
                    assert result.pending_events == 10
                    assert result.completed_today == 100


# ============================================
# TEST METRICS ENDPOINTS
# ============================================

class TestMetricsEndpoints:
    """Tests for metrics endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_all_metrics_unavailable(self):
        """Should raise 503 when automation unavailable."""
        from api.routes.automation_dashboard import get_all_metrics
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc:
                await get_all_metrics(
                    time_range=TimeRange.DAY,
                    current_user=MockUser()
                )
            
            assert exc.value.status_code == 503
    
    @pytest.mark.asyncio
    async def test_get_automation_metrics_invalid_type(self):
        """Should raise 404 for invalid automation type."""
        from api.routes.automation_dashboard import get_automation_metrics
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.AutomationType") as mock_type:
                mock_type.side_effect = ValueError("Invalid type")
                
                with pytest.raises(HTTPException) as exc:
                    await get_automation_metrics(
                        automation_type="invalid_type",
                        current_user=MockUser()
                    )
                
                assert exc.value.status_code == 404


# ============================================
# TEST QUEUE ENDPOINTS
# ============================================

class TestQueueEndpoints:
    """Tests for queue management endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_queue_depth_unavailable(self):
        """Should raise 503 when automation unavailable."""
        from api.routes.automation_dashboard import get_queue_depth
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc:
                await get_queue_depth(current_user=MockUser())
            
            assert exc.value.status_code == 503
    
    @pytest.mark.asyncio
    async def test_get_queue_depth_success(self):
        """Should return queue depths."""
        from api.routes.automation_dashboard import get_queue_depth
        
        mock_scheduler = MagicMock()
        mock_scheduler.get_queue_depth.return_value = {
            "high": 5,
            "normal": 20,
            "low": 10,
        }
        
        mock_orchestrator = MagicMock()
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                with patch("api.routes.automation_dashboard.get_scheduler") as mock_get_sched:
                    mock_get_orch.return_value = mock_orchestrator
                    mock_get_sched.return_value = mock_scheduler
                    
                    result = await get_queue_depth(current_user=MockUser())
                    
                    assert result.high == 5
                    assert result.normal == 20
                    assert result.low == 10
                    assert result.total == 35
    
    @pytest.mark.asyncio
    async def test_list_queued_events_unavailable(self):
        """Should raise 503 when automation unavailable."""
        from api.routes.automation_dashboard import list_queued_events
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc:
                await list_queued_events(current_user=MockUser())
            
            assert exc.value.status_code == 503
    
    @pytest.mark.asyncio
    async def test_list_queued_events_invalid_type(self):
        """Should raise 400 for invalid automation type."""
        from api.routes.automation_dashboard import list_queued_events
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator"):
                with patch("api.routes.automation_dashboard.get_scheduler"):
                    with patch("api.routes.automation_dashboard.AutomationType") as mock_type:
                        mock_type.side_effect = ValueError("Invalid")
                        
                        with pytest.raises(HTTPException) as exc:
                            await list_queued_events(
                                automation_type="bad_type",
                                current_user=MockUser()
                            )
                        
                        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_event_details_not_found(self):
        """Should raise 404 when event not found."""
        from api.routes.automation_dashboard import get_event_details
        
        mock_scheduler = MagicMock()
        mock_scheduler.get_event.return_value = None
        
        mock_orchestrator = MagicMock()
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                with patch("api.routes.automation_dashboard.get_scheduler") as mock_get_sched:
                    mock_get_orch.return_value = mock_orchestrator
                    mock_get_sched.return_value = mock_scheduler
                    
                    with pytest.raises(HTTPException) as exc:
                        await get_event_details(
                            event_id="nonexistent-event",
                            current_user=MockUser()
                        )
                    
                    assert exc.value.status_code == 404


# ============================================
# TEST SCHEDULING ENDPOINTS
# ============================================

class TestSchedulingEndpoints:
    """Tests for scheduling endpoints."""
    
    @pytest.mark.asyncio
    async def test_schedule_event_unavailable(self):
        """Should raise 503 when automation unavailable."""
        from api.routes.automation_dashboard import schedule_event
        
        request = ScheduleEventRequest(
            automation_type="welcome_message",
            user_id="user-123",
        )
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc:
                await schedule_event(request=request, current_user=MockUser())
            
            assert exc.value.status_code == 503
    
    @pytest.mark.asyncio
    async def test_schedule_event_invalid_type(self):
        """Should raise 400 for invalid automation type."""
        from api.routes.automation_dashboard import schedule_event
        
        request = ScheduleEventRequest(
            automation_type="invalid_automation",
            user_id="user-123",
        )
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.AutomationType") as mock_type:
                mock_type.side_effect = ValueError("Invalid")
                
                with pytest.raises(HTTPException) as exc:
                    await schedule_event(request=request, current_user=MockUser())
                
                assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_cancel_event_unavailable(self):
        """Should raise 503 when automation unavailable."""
        from api.routes.automation_dashboard import cancel_scheduled_event
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc:
                await cancel_scheduled_event(
                    event_id="event-123",
                    current_user=MockUser()
                )
            
            assert exc.value.status_code == 503
    
    @pytest.mark.asyncio
    async def test_cancel_event_not_found(self):
        """Should raise 404 when event not found."""
        from api.routes.automation_dashboard import cancel_scheduled_event
        
        mock_scheduler = MagicMock()
        mock_scheduler.cancel = AsyncMock(return_value=False)
        
        mock_orchestrator = MagicMock()
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                with patch("api.routes.automation_dashboard.get_scheduler") as mock_get_sched:
                    mock_get_orch.return_value = mock_orchestrator
                    mock_get_sched.return_value = mock_scheduler
                    
                    with pytest.raises(HTTPException) as exc:
                        await cancel_scheduled_event(
                            event_id="nonexistent-event",
                            current_user=MockUser()
                        )
                    
                    assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_cancel_event_success(self):
        """Should cancel event successfully."""
        from api.routes.automation_dashboard import cancel_scheduled_event
        
        mock_scheduler = MagicMock()
        mock_scheduler.cancel = AsyncMock(return_value=True)
        
        mock_orchestrator = MagicMock()
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                with patch("api.routes.automation_dashboard.get_scheduler") as mock_get_sched:
                    mock_get_orch.return_value = mock_orchestrator
                    mock_get_sched.return_value = mock_scheduler
                    
                    result = await cancel_scheduled_event(
                        event_id="event-123",
                        current_user=MockUser()
                    )
                    
                    assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_process_event_now_unavailable(self):
        """Should raise 503 when automation unavailable."""
        from api.routes.automation_dashboard import process_event_now
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc:
                await process_event_now(
                    event_id="event-123",
                    current_user=MockUser()
                )
            
            assert exc.value.status_code == 503
    
    @pytest.mark.asyncio
    async def test_process_event_now_failure(self):
        """Should raise 400 when processing fails."""
        from api.routes.automation_dashboard import process_event_now
        
        mock_scheduler = MagicMock()
        mock_scheduler.process_now = AsyncMock(return_value={
            "success": False,
            "error": "Event already processed",
        })
        
        mock_orchestrator = MagicMock()
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                with patch("api.routes.automation_dashboard.get_scheduler") as mock_get_sched:
                    mock_get_orch.return_value = mock_orchestrator
                    mock_get_sched.return_value = mock_scheduler
                    
                    with pytest.raises(HTTPException) as exc:
                        await process_event_now(
                            event_id="event-123",
                            current_user=MockUser()
                        )
                    
                    assert exc.value.status_code == 400


# ============================================
# TEST AUTOMATION MANAGEMENT ENDPOINTS
# ============================================

class TestAutomationManagementEndpoints:
    """Tests for automation management endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_automations_unavailable(self):
        """Should raise 503 when automation unavailable."""
        from api.routes.automation_dashboard import list_automations
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc:
                await list_automations(current_user=MockUser())
            
            assert exc.value.status_code == 503
    
    @pytest.mark.asyncio
    async def test_list_automations_all(self):
        """Should list all automations."""
        from api.routes.automation_dashboard import list_automations
        
        mock_config1 = MagicMock()
        mock_config1.name = "Welcome"
        mock_config1.enabled = True
        mock_config1.channels = []
        mock_config1.webhook_url = "http://n8n/welcome"
        mock_config1.max_triggers_per_day = 100
        mock_config1.time_window_minutes = 60
        mock_config1.retry_on_failure = True
        mock_config1.max_retries = 3
        
        mock_config2 = MagicMock()
        mock_config2.name = "Abandoned Cart"
        mock_config2.enabled = False
        mock_config2.channels = []
        mock_config2.webhook_url = "http://n8n/cart"
        mock_config2.max_triggers_per_day = 50
        mock_config2.time_window_minutes = 120
        mock_config2.retry_on_failure = False
        mock_config2.max_retries = 0
        
        mock_type1 = MagicMock()
        mock_type1.value = "welcome_message"
        
        mock_type2 = MagicMock()
        mock_type2.value = "abandoned_cart"
        
        mock_orchestrator = MagicMock()
        mock_orchestrator.automations = {
            mock_type1: mock_config1,
            mock_type2: mock_config2,
        }
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                mock_get_orch.return_value = mock_orchestrator
                
                result = await list_automations(
                    enabled_only=False,
                    current_user=MockUser()
                )
                
                assert result["total"] == 2
                assert len(result["automations"]) == 2
    
    @pytest.mark.asyncio
    async def test_list_automations_enabled_only(self):
        """Should filter to enabled automations only."""
        from api.routes.automation_dashboard import list_automations
        
        mock_config1 = MagicMock()
        mock_config1.name = "Welcome"
        mock_config1.enabled = True
        mock_config1.channels = []
        mock_config1.webhook_url = "http://n8n/welcome"
        mock_config1.max_triggers_per_day = 100
        mock_config1.time_window_minutes = 60
        mock_config1.retry_on_failure = True
        mock_config1.max_retries = 3
        
        mock_config2 = MagicMock()
        mock_config2.name = "Disabled"
        mock_config2.enabled = False
        
        mock_type1 = MagicMock()
        mock_type1.value = "welcome"
        
        mock_type2 = MagicMock()
        mock_type2.value = "disabled"
        
        mock_orchestrator = MagicMock()
        mock_orchestrator.automations = {
            mock_type1: mock_config1,
            mock_type2: mock_config2,
        }
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                mock_get_orch.return_value = mock_orchestrator
                
                result = await list_automations(
                    enabled_only=True,
                    current_user=MockUser()
                )
                
                assert result["total"] == 1


# ============================================
# TEST ERROR HANDLING
# ============================================

class TestErrorHandling:
    """Tests for error handling in endpoints."""
    
    @pytest.mark.asyncio
    async def test_overview_catches_exception(self):
        """Should convert exceptions to 500."""
        from api.routes.automation_dashboard import get_dashboard_overview
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                mock_get_orch.side_effect = RuntimeError("Orchestrator crashed")
                
                with pytest.raises(HTTPException) as exc:
                    await get_dashboard_overview(current_user=MockUser())
                
                assert exc.value.status_code == 500
                assert "Orchestrator crashed" in exc.value.detail
    
    @pytest.mark.asyncio
    async def test_metrics_catches_exception(self):
        """Should convert exceptions to 500."""
        from api.routes.automation_dashboard import get_all_metrics
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                mock_get_orch.side_effect = Exception("Unknown error")
                
                with pytest.raises(HTTPException) as exc:
                    await get_all_metrics(
                        time_range=TimeRange.DAY,
                        current_user=MockUser()
                    )
                
                assert exc.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_queue_depth_catches_exception(self):
        """Should convert exceptions to 500."""
        from api.routes.automation_dashboard import get_queue_depth
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                mock_get_orch.side_effect = ValueError("Bad value")
                
                with pytest.raises(HTTPException) as exc:
                    await get_queue_depth(current_user=MockUser())
                
                assert exc.value.status_code == 500


# ============================================
# TEST EDGE CASES
# ============================================

class TestEdgeCases:
    """Edge case tests."""
    
    @pytest.mark.asyncio
    async def test_health_with_degraded_scheduler(self):
        """Should handle scheduler failure gracefully."""
        from api.routes.automation_dashboard import dashboard_health
        
        mock_orchestrator = MagicMock()
        mock_orchestrator.is_configured = True
        
        with patch("api.routes.automation_dashboard.AUTOMATION_AVAILABLE", True):
            with patch("api.routes.automation_dashboard.get_orchestrator") as mock_get_orch:
                with patch("api.routes.automation_dashboard.get_scheduler") as mock_get_sched:
                    mock_get_orch.return_value = mock_orchestrator
                    mock_get_sched.side_effect = ValueError("Scheduler not ready")
                    
                    result = await dashboard_health()
                    
                    assert result["components"]["orchestrator"] is True
                    assert result["components"]["scheduler"] is False
    
    def test_time_range_is_string_enum(self):
        """TimeRange should be string enum."""
        assert TimeRange.HOUR == "1h"
        assert str(TimeRange.DAY) == "TimeRange.DAY"
    
    def test_schedule_request_default_priority(self):
        """Default priority should be normal."""
        request = ScheduleEventRequest(
            automation_type="test",
            user_id="user-1",
        )
        
        assert request.priority == "normal"
    
    def test_schedule_request_empty_data(self):
        """Default data should be empty dict."""
        request = ScheduleEventRequest(
            automation_type="test",
            user_id="user-1",
        )
        
        assert request.data == {}
        assert isinstance(request.data, dict)
