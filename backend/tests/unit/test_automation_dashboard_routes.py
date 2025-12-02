"""
Unit Tests for Automation Dashboard Routes
==========================================
Tests for automation_dashboard.py endpoints.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ============================================
# SCHEMA TESTS
# ============================================

class TestDashboardSchemas:
    """Tests for dashboard schemas"""

    def test_time_range_enum(self):
        """Test TimeRange enum values"""
        from api.routes.automation_dashboard import TimeRange

        assert TimeRange.HOUR == "1h"
        assert TimeRange.DAY == "24h"
        assert TimeRange.WEEK == "7d"
        assert TimeRange.MONTH == "30d"

    def test_dashboard_overview_model(self):
        """Test DashboardOverview model"""
        from api.routes.automation_dashboard import DashboardOverview

        overview = DashboardOverview(
            total_automations=10,
            active_automations=8,
            pending_events=5,
            processing_events=2,
            completed_today=100,
            failed_today=3,
            success_rate=97.0,
            avg_processing_time_ms=250.5
        )

        assert overview.total_automations == 10
        assert overview.active_automations == 8
        assert overview.success_rate == 97.0

    def test_automation_metrics_model(self):
        """Test AutomationMetrics model"""
        from api.routes.automation_dashboard import AutomationMetrics

        metrics = AutomationMetrics(
            automation_type="new_user_welcome",
            display_name="New User Welcome",
            enabled=True,
            total_triggers=500,
            successful=480,
            failed=20,
            pending=5,
            success_rate=96.0,
            avg_delay_ms=150.0,
            last_triggered=datetime.now(),
            channels=["whatsapp", "email"]
        )

        assert metrics.automation_type == "new_user_welcome"
        assert metrics.enabled is True
        assert metrics.success_rate == 96.0

    def test_scheduled_event_response_model(self):
        """Test ScheduledEventResponse model"""
        from api.routes.automation_dashboard import ScheduledEventResponse

        event = ScheduledEventResponse(
            id="evt-123",
            automation_type="cart_abandoned",
            schedule_type="delayed",
            user_id="user-456",
            status="pending",
            scheduled_for=datetime.now() + timedelta(hours=1),
            priority="normal",
            retry_count=0,
            created_at=datetime.now(),
            processed_at=None,
            error_message=None
        )

        assert event.id == "evt-123"
        assert event.status == "pending"

    def test_queue_depth_response_model(self):
        """Test QueueDepthResponse model"""
        from api.routes.automation_dashboard import QueueDepthResponse

        queue = QueueDepthResponse(
            high=10,
            normal=50,
            low=20,
            total=80
        )

        assert queue.high == 10
        assert queue.total == 80

    def test_time_series_data_point_model(self):
        """Test TimeSeriesDataPoint model"""
        from api.routes.automation_dashboard import TimeSeriesDataPoint

        point = TimeSeriesDataPoint(
            timestamp=datetime.now(),
            value=42.5
        )

        assert point.value == 42.5

    def test_schedule_event_request_model(self):
        """Test ScheduleEventRequest model"""
        from api.routes.automation_dashboard import ScheduleEventRequest

        request = ScheduleEventRequest(
            automation_type="price_drop",
            user_id="user-123",
            data={"product_id": "prod-456"},
            delay_minutes=30,
            priority="high"
        )

        assert request.automation_type == "price_drop"
        assert request.delay_minutes == 30


# ============================================
# ENDPOINT TESTS
# ============================================

class TestHealthEndpoint:
    """Tests for dashboard health endpoint"""

    @pytest.mark.asyncio
    async def test_dashboard_health_available(self):
        """Test health when automation is available"""
        from api.routes.automation_dashboard import dashboard_health

        mock_orchestrator = MagicMock()
        mock_orchestrator.is_configured = True

        mock_scheduler = MagicMock()

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            result = await dashboard_health()

            assert result["status"] == "healthy"
            assert result["automation_available"] is True
            assert result["components"]["orchestrator"] is True

    @pytest.mark.asyncio
    async def test_dashboard_health_unavailable(self):
        """Test health when automation is unavailable"""
        from api.routes.automation_dashboard import dashboard_health

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            result = await dashboard_health()

            assert result["status"] == "unavailable"
            assert result["automation_available"] is False

    @pytest.mark.asyncio
    async def test_dashboard_health_degraded(self):
        """Test health when orchestrator raises exception"""
        from api.routes.automation_dashboard import dashboard_health

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            side_effect=Exception("Connection failed")
        ):
            result = await dashboard_health()

            assert result["status"] == "degraded"
            assert "error" in result


class TestOverviewEndpoint:
    """Tests for dashboard overview endpoint"""

    @pytest.mark.asyncio
    async def test_get_dashboard_overview_unavailable(self):
        """Test overview when automation unavailable"""
        from api.routes.automation_dashboard import get_dashboard_overview
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_overview()

            assert exc_info.value.status_code == 503


class TestQueueDepthEndpoint:
    """Tests for queue depth endpoint"""

    @pytest.mark.asyncio
    async def test_get_queue_depth_unavailable(self):
        """Test queue depth when automation unavailable"""
        from api.routes.automation_dashboard import get_queue_depth
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_queue_depth()

            assert exc_info.value.status_code == 503


class TestAllMetricsEndpoint:
    """Tests for all metrics endpoint"""

    @pytest.mark.asyncio
    async def test_get_all_metrics_unavailable(self):
        """Test all metrics when unavailable"""
        from api.routes.automation_dashboard import get_all_metrics
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_all_metrics()

            assert exc_info.value.status_code == 503


class TestAutomationMetricsEndpoint:
    """Tests for single automation metrics endpoint"""

    @pytest.mark.asyncio
    async def test_get_automation_metrics_unavailable(self):
        """Test automation metrics when unavailable"""
        from api.routes.automation_dashboard import get_automation_metrics
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_automation_metrics("new_user_welcome")

            assert exc_info.value.status_code == 503


class TestListQueuedEventsEndpoint:
    """Tests for list queued events endpoint"""

    @pytest.mark.asyncio
    async def test_list_queued_events_unavailable(self):
        """Test list queued events when unavailable"""
        from api.routes.automation_dashboard import list_queued_events
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await list_queued_events()

            assert exc_info.value.status_code == 503


class TestEventDetailsEndpoint:
    """Tests for event details endpoint"""

    @pytest.mark.asyncio
    async def test_get_event_details_unavailable(self):
        """Test event details when unavailable"""
        from api.routes.automation_dashboard import get_event_details
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_event_details("evt-123")

            assert exc_info.value.status_code == 503


class TestCancelEventEndpoint:
    """Tests for cancel event endpoint"""

    @pytest.mark.asyncio
    async def test_cancel_scheduled_event_unavailable(self):
        """Test cancel event when unavailable"""
        from api.routes.automation_dashboard import cancel_scheduled_event
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await cancel_scheduled_event("evt-123")

            assert exc_info.value.status_code == 503


class TestProcessEventNowEndpoint:
    """Tests for process event now endpoint"""

    @pytest.mark.asyncio
    async def test_process_event_now_unavailable(self):
        """Test process event now when unavailable"""
        from api.routes.automation_dashboard import process_event_now
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await process_event_now("evt-123")

            assert exc_info.value.status_code == 503


class TestScheduleEventEndpoint:
    """Tests for schedule event endpoint"""

    @pytest.mark.asyncio
    async def test_schedule_event_unavailable(self):
        """Test schedule event when unavailable"""
        from api.routes.automation_dashboard import (ScheduleEventRequest,
                                                     schedule_event)
        from fastapi import HTTPException

        request = ScheduleEventRequest(
            automation_type="cart_abandoned",
            user_id="user-123",
            delay_minutes=30
        )

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await schedule_event(request)

            assert exc_info.value.status_code == 503


class TestListAutomationsEndpoint:
    """Tests for list automations endpoint"""

    @pytest.mark.asyncio
    async def test_list_automations_unavailable(self):
        """Test list automations when unavailable"""
        from api.routes.automation_dashboard import list_automations
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await list_automations()

            assert exc_info.value.status_code == 503


class TestToggleAutomationEndpoint:
    """Tests for toggle automation endpoint"""

    @pytest.mark.asyncio
    async def test_toggle_automation_unavailable(self):
        """Test toggle automation when unavailable"""
        from api.routes.automation_dashboard import toggle_automation
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await toggle_automation("new_user_welcome", enabled=True)

            assert exc_info.value.status_code == 503


class TestStatsSummaryEndpoint:
    """Tests for stats summary endpoint"""

    @pytest.mark.asyncio
    async def test_get_stats_summary_unavailable(self):
        """Test stats summary when unavailable"""
        from api.routes.automation_dashboard import get_stats_summary
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_stats_summary()

            assert exc_info.value.status_code == 503


class TestStatsByTypeEndpoint:
    """Tests for stats by type endpoint"""

    @pytest.mark.asyncio
    async def test_get_stats_by_type_unavailable(self):
        """Test stats by type when unavailable"""
        from api.routes.automation_dashboard import get_stats_by_type
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE',
            False
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_stats_by_type()

            assert exc_info.value.status_code == 503


# ============================================
# ADDITIONAL COMPREHENSIVE TESTS
# ============================================

class TestDashboardOverviewWithMocks:
    """Tests for dashboard overview with proper mocking"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        orch = MagicMock()
        orch.automations = {}
        return orch

    @pytest.fixture
    def mock_scheduler(self):
        """Create mock scheduler"""
        sched = MagicMock()
        sched.get_stats.return_value = MagicMock(
            total_completed=100,
            total_failed=5,
            total_pending=10,
            total_processing=2,
            avg_processing_time_ms=150.5
        )
        return sched

    @pytest.mark.asyncio
    async def test_get_dashboard_overview_success(
        self, mock_orchestrator, mock_scheduler
    ):
        """Test overview success with mocked components"""
        from api.routes.automation_dashboard import get_dashboard_overview

        # Add some automations
        mock_auto = MagicMock()
        mock_auto.enabled = True
        mock_orchestrator.automations = {"type1": mock_auto}

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            result = await get_dashboard_overview()

            assert result.total_automations == 1
            assert result.active_automations == 1
            assert result.pending_events == 10

    @pytest.mark.asyncio
    async def test_get_dashboard_overview_error(self):
        """Test overview when exception occurs"""
        from api.routes.automation_dashboard import get_dashboard_overview
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            side_effect=Exception("Failed to get orchestrator")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_overview()

            assert exc_info.value.status_code == 500


class TestMetricsWithMocks:
    """Tests for metrics endpoints with mocks"""

    @pytest.fixture
    def mock_auto_type(self):
        """Create mock automation type"""
        from enum import Enum
        class MockAutoType(str, Enum):
            TEST = "test_auto"
        return MockAutoType

    @pytest.mark.asyncio
    async def test_get_all_metrics_success(self):
        """Test getting all metrics successfully"""
        from api.routes.automation_dashboard import TimeRange, get_all_metrics

        mock_orchestrator = MagicMock()
        mock_config = MagicMock()
        mock_config.name = "Test Auto"
        mock_config.enabled = True
        mock_config.channels = []

        # Create proper enum mock
        mock_type = MagicMock()
        mock_type.value = "test"
        mock_orchestrator.automations = {mock_type: mock_config}

        mock_scheduler = MagicMock()
        mock_stats = MagicMock()
        mock_stats.events_per_type = {"test": 5}
        mock_scheduler.get_stats.return_value = mock_stats

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            result = await get_all_metrics(TimeRange.DAY)

            assert "metrics" in result
            assert result["time_range"] == "24h"

    @pytest.mark.asyncio
    async def test_get_all_metrics_error(self):
        """Test all metrics when error occurs"""
        from api.routes.automation_dashboard import TimeRange, get_all_metrics
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            side_effect=Exception("Error")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_all_metrics(TimeRange.DAY)

            assert exc_info.value.status_code == 500


class TestAutomationMetricsWithMocks:
    """Tests for single automation metrics with mocks"""

    @pytest.mark.asyncio
    async def test_get_automation_metrics_invalid_type(self):
        """Test metrics with invalid automation type"""
        from api.routes.automation_dashboard import get_automation_metrics
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.AutomationType',
            side_effect=ValueError("Invalid type")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_automation_metrics("invalid_type")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_automation_metrics_not_configured(self):
        """Test metrics when automation not configured"""
        from api.routes.automation_dashboard import get_automation_metrics
        from fastapi import HTTPException

        mock_orchestrator = MagicMock()
        mock_orchestrator.automations = {}

        # Need to mock AutomationType to return valid value
        mock_auto_type = MagicMock()
        
        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.AutomationType',
            return_value=mock_auto_type
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_automation_metrics("test_type")

            assert exc_info.value.status_code == 404


class TestQueueDepthWithMocks:
    """Tests for queue depth with mocks"""

    @pytest.mark.asyncio
    async def test_get_queue_depth_success(self):
        """Test queue depth successfully"""
        from api.routes.automation_dashboard import get_queue_depth

        mock_orchestrator = MagicMock()
        mock_scheduler = MagicMock()
        mock_scheduler.get_queue_depth.return_value = {
            "high": 5,
            "normal": 20,
            "low": 10
        }

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            result = await get_queue_depth()

            assert result.high == 5
            assert result.normal == 20
            assert result.total == 35

    @pytest.mark.asyncio
    async def test_get_queue_depth_error(self):
        """Test queue depth when error occurs"""
        from api.routes.automation_dashboard import get_queue_depth
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            side_effect=Exception("Error")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_queue_depth()

            assert exc_info.value.status_code == 500


class TestListQueuedEventsWithMocks:
    """Tests for listing queued events with mocks"""

    @pytest.mark.asyncio
    async def test_list_queued_events_success(self):
        """Test listing queued events successfully"""
        from api.routes.automation_dashboard import list_queued_events

        mock_orchestrator = MagicMock()
        mock_scheduler = MagicMock()
        
        # Create mock events
        mock_event = MagicMock()
        mock_event.id = "evt-123"
        mock_event.automation_type = MagicMock()
        mock_event.automation_type.value = "test"
        mock_event.schedule_type = MagicMock()
        mock_event.schedule_type.value = "delayed"
        mock_event.user_id = "user-123"
        mock_event.status = MagicMock()
        mock_event.status.value = "pending"
        mock_event.scheduled_for = datetime.now()
        mock_event.priority = MagicMock()
        mock_event.priority.value = "normal"
        mock_event.retry_count = 0
        mock_event.created_at = datetime.now()
        mock_event.processed_at = None
        mock_event.error_message = None

        mock_scheduler.get_pending_events.return_value = [mock_event]

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            # Pass None explicitly for optional parameters
            result = await list_queued_events(
                status=None,
                automation_type=None,
                user_id=None,
                limit=50
            )

            assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_list_queued_events_invalid_type(self):
        """Test listing events with invalid automation type"""
        from api.routes.automation_dashboard import list_queued_events
        from fastapi import HTTPException

        mock_orchestrator = MagicMock()
        mock_scheduler = MagicMock()

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ), patch(
            'api.routes.automation_dashboard.AutomationType',
            side_effect=ValueError("Invalid")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await list_queued_events(automation_type="invalid")

            assert exc_info.value.status_code == 400


class TestEventDetailsWithMocks:
    """Tests for event details with mocks"""

    @pytest.mark.asyncio
    async def test_get_event_details_success(self):
        """Test getting event details successfully"""
        from api.routes.automation_dashboard import get_event_details

        mock_orchestrator = MagicMock()
        mock_scheduler = MagicMock()

        mock_event = MagicMock()
        mock_event.id = "evt-123"
        mock_event.automation_type = MagicMock()
        mock_event.automation_type.value = "test"
        mock_event.schedule_type = MagicMock()
        mock_event.schedule_type.value = "delayed"
        mock_event.user_id = "user-123"
        mock_event.status = MagicMock()
        mock_event.status.value = "pending"
        mock_event.scheduled_for = datetime.now()
        mock_event.priority = MagicMock()
        mock_event.priority.value = "normal"
        mock_event.retry_count = 0
        mock_event.created_at = datetime.now()
        mock_event.processed_at = None
        mock_event.error_message = None
        mock_event.data = {}
        mock_event.metadata = {}

        mock_scheduler.get_event.return_value = mock_event

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            result = await get_event_details("evt-123")

            assert result["event"].id == "evt-123"

    @pytest.mark.asyncio
    async def test_get_event_details_not_found(self):
        """Test getting non-existent event"""
        from api.routes.automation_dashboard import get_event_details
        from fastapi import HTTPException

        mock_orchestrator = MagicMock()
        mock_scheduler = MagicMock()
        mock_scheduler.get_event.return_value = None

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_event_details("non-existent")

            assert exc_info.value.status_code == 404


class TestScheduleEventWithMocks:
    """Tests for scheduling events with mocks"""

    @pytest.mark.asyncio
    async def test_schedule_event_invalid_type(self):
        """Test scheduling with invalid automation type"""
        from api.routes.automation_dashboard import (ScheduleEventRequest,
                                                     schedule_event)
        from fastapi import HTTPException

        request = ScheduleEventRequest(
            automation_type="invalid",
            user_id="user-123"
        )

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.AutomationType',
            side_effect=ValueError("Invalid")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await schedule_event(request)

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_schedule_event_success(self):
        """Test scheduling event successfully"""
        from api.routes.automation_dashboard import (ScheduleEventRequest,
                                                     schedule_event)

        request = ScheduleEventRequest(
            automation_type="test",
            user_id="user-123",
            delay_minutes=30
        )

        mock_orchestrator = MagicMock()
        mock_scheduler = MagicMock()
        
        mock_event = MagicMock()
        mock_event.id = "evt-new"
        mock_event.scheduled_for = datetime.now()
        mock_scheduler.schedule = AsyncMock(return_value=mock_event)

        mock_auto_type = MagicMock()
        mock_priority = MagicMock()

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.AutomationType',
            return_value=mock_auto_type
        ), patch(
            'api.routes.automation_dashboard.AutomationPriority',
            return_value=mock_priority
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            result = await schedule_event(request)

            assert result["success"] is True


class TestCancelEventWithMocks:
    """Tests for canceling events with mocks"""

    @pytest.mark.asyncio
    async def test_cancel_event_success(self):
        """Test canceling event successfully"""
        from api.routes.automation_dashboard import cancel_scheduled_event

        mock_orchestrator = MagicMock()
        mock_scheduler = MagicMock()
        mock_scheduler.cancel = AsyncMock(return_value=True)

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            result = await cancel_scheduled_event("evt-123")

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_cancel_event_not_found(self):
        """Test canceling non-existent event"""
        from api.routes.automation_dashboard import cancel_scheduled_event
        from fastapi import HTTPException

        mock_orchestrator = MagicMock()
        mock_scheduler = MagicMock()
        mock_scheduler.cancel = AsyncMock(return_value=False)

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            with pytest.raises(HTTPException) as exc_info:
                await cancel_scheduled_event("non-existent")

            assert exc_info.value.status_code == 404


class TestProcessEventNowWithMocks:
    """Tests for processing events immediately with mocks"""

    @pytest.mark.asyncio
    async def test_process_event_success(self):
        """Test processing event successfully"""
        from api.routes.automation_dashboard import process_event_now

        mock_orchestrator = MagicMock()
        mock_scheduler = MagicMock()
        mock_scheduler.process_now = AsyncMock(return_value={
            "success": True,
            "status": "completed"
        })

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            result = await process_event_now("evt-123")

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_process_event_failure(self):
        """Test processing event failure"""
        from api.routes.automation_dashboard import process_event_now
        from fastapi import HTTPException

        mock_orchestrator = MagicMock()
        mock_scheduler = MagicMock()
        mock_scheduler.process_now = AsyncMock(return_value={
            "success": False,
            "error": "Processing failed"
        })

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            with pytest.raises(HTTPException) as exc_info:
                await process_event_now("evt-123")

            assert exc_info.value.status_code == 400


class TestListAutomationsWithMocks:
    """Tests for listing automations with mocks"""

    @pytest.mark.asyncio
    async def test_list_automations_success(self):
        """Test listing automations successfully"""
        from api.routes.automation_dashboard import list_automations

        mock_orchestrator = MagicMock()
        
        mock_auto_type = MagicMock()
        mock_auto_type.value = "test"
        
        mock_config = MagicMock()
        mock_config.name = "Test Automation"
        mock_config.enabled = True
        mock_config.channels = []
        mock_config.webhook_url = "https://example.com"
        mock_config.max_triggers_per_day = 100
        mock_config.time_window_minutes = 60
        mock_config.retry_on_failure = True
        mock_config.max_retries = 3

        mock_orchestrator.automations = {mock_auto_type: mock_config}

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ):
            result = await list_automations()

            assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_list_automations_enabled_only(self):
        """Test listing only enabled automations"""
        from api.routes.automation_dashboard import list_automations

        mock_orchestrator = MagicMock()
        
        mock_auto_type = MagicMock()
        mock_auto_type.value = "test"
        
        mock_config = MagicMock()
        mock_config.name = "Test"
        mock_config.enabled = False
        mock_config.channels = []
        mock_config.webhook_url = None
        mock_config.max_triggers_per_day = 10
        mock_config.time_window_minutes = 30
        mock_config.retry_on_failure = False
        mock_config.max_retries = 0

        mock_orchestrator.automations = {mock_auto_type: mock_config}

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ):
            result = await list_automations(enabled_only=True)

            assert result["total"] == 0


class TestToggleAutomationWithMocks:
    """Tests for toggling automations with mocks"""

    @pytest.mark.asyncio
    async def test_toggle_automation_invalid_type(self):
        """Test toggle with invalid automation type"""
        from api.routes.automation_dashboard import toggle_automation
        from fastapi import HTTPException

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.AutomationType',
            side_effect=ValueError("Invalid")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await toggle_automation("invalid", enabled=True)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_toggle_automation_not_configured(self):
        """Test toggle when automation not configured"""
        from api.routes.automation_dashboard import toggle_automation
        from fastapi import HTTPException

        mock_orchestrator = MagicMock()
        mock_orchestrator.automations = {}
        mock_auto_type = MagicMock()

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.AutomationType',
            return_value=mock_auto_type
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ):
            with pytest.raises(HTTPException) as exc_info:
                await toggle_automation("test", enabled=True)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_toggle_automation_success(self):
        """Test toggle automation successfully"""
        from api.routes.automation_dashboard import toggle_automation

        mock_orchestrator = MagicMock()
        mock_auto_type = MagicMock()
        mock_config = MagicMock()
        mock_config.enabled = False
        mock_orchestrator.automations = {mock_auto_type: mock_config}

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.AutomationType',
            return_value=mock_auto_type
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ):
            result = await toggle_automation("test", enabled=True)

            assert result["success"] is True
            assert result["enabled"] is True


class TestStatsSummaryWithMocks:
    """Tests for stats summary with mocks"""

    @pytest.mark.asyncio
    async def test_get_stats_summary_success(self):
        """Test getting stats summary successfully"""
        from api.routes.automation_dashboard import get_stats_summary

        mock_orchestrator = MagicMock()
        mock_scheduler = MagicMock()
        
        mock_stats = MagicMock()
        mock_stats.total_pending = 10
        mock_stats.total_processing = 5
        mock_stats.total_completed = 100
        mock_stats.total_failed = 3
        mock_stats.avg_processing_time_ms = 150.5
        mock_stats.events_per_type = {"test": 50}
        mock_stats.last_run = datetime.now()
        
        mock_scheduler.get_stats.return_value = mock_stats

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.get_scheduler',
            return_value=mock_scheduler
        ):
            result = await get_stats_summary()

            assert result["queue"]["pending"] == 10


class TestStatsByTypeWithMocks:
    """Tests for stats by type with mocks"""

    @pytest.mark.asyncio
    async def test_get_stats_by_type_success(self):
        """Test getting stats by type successfully"""
        from api.routes.automation_dashboard import get_stats_by_type

        mock_orchestrator = MagicMock()
        
        # Create mock AutomationType enum
        mock_auto_type = MagicMock()
        mock_auto_type.value = "test"
        
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_orchestrator.automations = {mock_auto_type: mock_config}

        with patch(
            'api.routes.automation_dashboard.AUTOMATION_AVAILABLE', True
        ), patch(
            'api.routes.automation_dashboard.get_orchestrator',
            return_value=mock_orchestrator
        ), patch(
            'api.routes.automation_dashboard.AutomationType',
            [mock_auto_type]
        ):
            result = await get_stats_by_type()

            assert "by_type" in result
