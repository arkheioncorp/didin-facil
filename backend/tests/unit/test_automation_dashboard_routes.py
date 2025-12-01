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
