"""
Comprehensive tests for hub_health routes.
Coverage target: 90%+
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Response


@pytest.fixture
def mock_health_checker():
    """Mock health checker."""
    with patch("api.routes.hub_health.get_health_checker") as mock:
        checker = MagicMock()
        mock.return_value = checker
        yield checker


@pytest.fixture
def mock_metrics_registry():
    """Mock metrics registry."""
    with patch("api.routes.hub_health.get_metrics_registry") as mock:
        registry = MagicMock()
        mock.return_value = registry
        yield registry


@pytest.fixture
def mock_hubs():
    """Mock integration hubs."""
    mock_whatsapp = MagicMock()
    mock_instagram = MagicMock()
    mock_tiktok = MagicMock()
    
    # Add circuit breakers
    mock_cb = MagicMock()
    mock_cb.state = MagicMock(value="closed")
    mock_cb.stats = MagicMock()
    mock_cb.stats.failure_count = 0
    mock_cb.stats.success_count = 100
    mock_cb.reset = AsyncMock()
    
    mock_whatsapp._circuit_breaker = mock_cb
    mock_instagram._circuit_breaker = mock_cb
    mock_tiktok._circuit_breaker = mock_cb
    
    with patch("api.routes.hub_health.get_whatsapp_hub", return_value=mock_whatsapp), \
         patch("api.routes.hub_health.get_instagram_hub", return_value=mock_instagram), \
         patch("api.routes.hub_health.get_tiktok_hub", return_value=mock_tiktok):
        yield {
            "whatsapp": mock_whatsapp,
            "instagram": mock_instagram,
            "tiktok": mock_tiktok
        }


@pytest.fixture
def mock_hub_health():
    """Mock hub health response."""
    health = MagicMock()
    health.name = "whatsapp"
    health.status = "healthy"
    health.circuit_breaker_state = "closed"
    health.success_rate = 99.5
    health.avg_latency_ms = 150.0
    health.last_success = datetime.now(timezone.utc).isoformat()
    health.last_failure = None
    health.details = {"connected": True}
    return health


class TestGetOverallHealth:
    """Tests for GET /hub/health endpoint."""
    
    @pytest.mark.asyncio
    async def test_overall_health_success(self, mock_health_checker):
        """Test getting overall health status."""
        from api.routes.hub_health import get_overall_health
        
        mock_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hubs": {
                "whatsapp": {"status": "healthy"},
                "instagram": {"status": "healthy"},
                "tiktok": {"status": "degraded"}
            }
        }
        mock_health_checker.get_overall_status = AsyncMock(return_value=mock_status)
        
        result = await get_overall_health()
        
        assert result["status"] == "healthy"
        assert "hubs" in result
        assert len(result["hubs"]) == 3
    
    @pytest.mark.asyncio
    async def test_overall_health_degraded(self, mock_health_checker):
        """Test degraded overall health."""
        from api.routes.hub_health import get_overall_health
        
        mock_status = {
            "status": "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hubs": {
                "whatsapp": {"status": "unhealthy"},
                "instagram": {"status": "healthy"}
            }
        }
        mock_health_checker.get_overall_status = AsyncMock(return_value=mock_status)
        
        result = await get_overall_health()
        
        assert result["status"] == "degraded"


class TestGetHubHealth:
    """Tests for GET /hub/health/{hub_name} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_hub_health_success(self, mock_health_checker, mock_hub_health):
        """Test getting specific hub health."""
        from api.routes.hub_health import get_hub_health
        
        mock_health_checker.check_hub_health = AsyncMock(return_value=mock_hub_health)
        
        result = await get_hub_health("whatsapp")
        
        assert result["name"] == "whatsapp"
        assert result["status"] == "healthy"
        assert result["circuit_breaker_state"] == "closed"
        assert "99.5%" in result["success_rate"]
    
    @pytest.mark.asyncio
    async def test_get_hub_health_with_failure(self, mock_health_checker):
        """Test hub health with failure info."""
        from api.routes.hub_health import get_hub_health
        
        health = MagicMock()
        health.name = "instagram"
        health.status = "degraded"
        health.circuit_breaker_state = "half_open"
        health.success_rate = 75.0
        health.avg_latency_ms = 500.0
        health.last_success = datetime.now(timezone.utc).isoformat()
        health.last_failure = datetime.now(timezone.utc).isoformat()
        health.details = {"error": "Rate limited"}
        
        mock_health_checker.check_hub_health = AsyncMock(return_value=health)
        
        result = await get_hub_health("instagram")
        
        assert result["status"] == "degraded"
        assert result["last_failure"] is not None


class TestGetMetricsJson:
    """Tests for GET /hub/metrics endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_metrics_json(self, mock_metrics_registry):
        """Test getting metrics in JSON format."""
        from api.routes.hub_health import get_metrics_json
        
        mock_metrics = {
            "requests_total": 1000,
            "requests_success": 950,
            "requests_failure": 50,
            "latency_avg_ms": 200,
            "circuit_breakers": {
                "whatsapp": "closed",
                "instagram": "closed"
            }
        }
        mock_metrics_registry.get_metrics.return_value = mock_metrics
        
        result = await get_metrics_json()
        
        assert result["requests_total"] == 1000
        assert result["requests_success"] == 950
    
    @pytest.mark.asyncio
    async def test_get_metrics_empty(self, mock_metrics_registry):
        """Test getting empty metrics."""
        from api.routes.hub_health import get_metrics_json
        
        mock_metrics_registry.get_metrics.return_value = {}
        
        result = await get_metrics_json()
        
        assert result == {}


class TestGetMetricsPrometheus:
    """Tests for GET /hub/metrics/prometheus endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_prometheus_metrics(self):
        """Test getting Prometheus format metrics."""
        from api.routes.hub_health import get_metrics_prometheus
        
        prometheus_text = """# HELP requests_total Total requests
# TYPE requests_total counter
requests_total{hub="whatsapp"} 1000
requests_total{hub="instagram"} 500
"""
        
        with patch("api.routes.hub_health.export_prometheus_metrics", return_value=prometheus_text):
            result = await get_metrics_prometheus()
        
        assert isinstance(result, Response)
        assert result.media_type == "text/plain; charset=utf-8"
        assert b"requests_total" in result.body
    
    @pytest.mark.asyncio
    async def test_get_prometheus_metrics_empty(self):
        """Test empty Prometheus metrics."""
        from api.routes.hub_health import get_metrics_prometheus
        
        with patch("api.routes.hub_health.export_prometheus_metrics", return_value=""):
            result = await get_metrics_prometheus()
        
        assert result.body == b""


class TestResetCircuitBreaker:
    """Tests for POST /hub/circuit-breaker/{hub_name}/reset endpoint."""
    
    @pytest.mark.asyncio
    async def test_reset_whatsapp_circuit_breaker(self, mock_hubs):
        """Test resetting WhatsApp circuit breaker."""
        from api.routes.hub_health import reset_circuit_breaker
        
        result = await reset_circuit_breaker("whatsapp")
        
        assert result["hub"] == "whatsapp"
        assert "resetado" in result["message"]
        mock_hubs["whatsapp"]._circuit_breaker.reset.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reset_instagram_circuit_breaker(self, mock_hubs):
        """Test resetting Instagram circuit breaker."""
        from api.routes.hub_health import reset_circuit_breaker
        
        result = await reset_circuit_breaker("instagram")
        
        assert result["hub"] == "instagram"
    
    @pytest.mark.asyncio
    async def test_reset_tiktok_circuit_breaker(self, mock_hubs):
        """Test resetting TikTok circuit breaker."""
        from api.routes.hub_health import reset_circuit_breaker
        
        result = await reset_circuit_breaker("tiktok")
        
        assert result["hub"] == "tiktok"
    
    @pytest.mark.asyncio
    async def test_reset_unknown_hub(self):
        """Test resetting unknown hub."""
        from api.routes.hub_health import reset_circuit_breaker
        
        with patch("api.routes.hub_health.get_whatsapp_hub"), \
             patch("api.routes.hub_health.get_instagram_hub"), \
             patch("api.routes.hub_health.get_tiktok_hub"):
            result = await reset_circuit_breaker("unknown")
        
        assert "error" in result
        assert "não encontrado" in result["error"]
    
    @pytest.mark.asyncio
    async def test_reset_hub_without_circuit_breaker(self):
        """Test resetting hub without circuit breaker."""
        from api.routes.hub_health import reset_circuit_breaker
        
        mock_hub = MagicMock(spec=[])  # No _circuit_breaker attribute
        
        with patch("api.routes.hub_health.get_whatsapp_hub", return_value=mock_hub):
            result = await reset_circuit_breaker("whatsapp")
        
        assert "error" in result
        assert "circuit breaker" in result["error"]
    
    @pytest.mark.asyncio
    async def test_reset_circuit_breaker_without_reset_method(self):
        """Test resetting when circuit breaker has no reset method."""
        from api.routes.hub_health import reset_circuit_breaker
        
        mock_hub = MagicMock()
        mock_cb = MagicMock(spec=["state"])  # No reset method
        mock_cb.state = MagicMock(value="open")
        mock_hub._circuit_breaker = mock_cb
        
        with patch("api.routes.hub_health.get_whatsapp_hub", return_value=mock_hub):
            result = await reset_circuit_breaker("whatsapp")
        
        # Should still work, just not call reset
        assert result["hub"] == "whatsapp"


class TestGetAllCircuitBreakerStatus:
    """Tests for GET /hub/circuit-breaker/status endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_all_status_success(self, mock_hubs):
        """Test getting all circuit breaker status."""
        from api.routes.hub_health import get_all_circuit_breaker_status
        
        result = await get_all_circuit_breaker_status()
        
        assert "whatsapp" in result
        assert "instagram" in result
        assert "tiktok" in result
        assert result["whatsapp"]["state"] == "closed"
    
    @pytest.mark.asyncio
    async def test_get_status_hub_without_cb(self):
        """Test status when hub has no circuit breaker."""
        from api.routes.hub_health import get_all_circuit_breaker_status
        
        mock_hub = MagicMock(spec=[])  # No _circuit_breaker
        
        with patch("api.routes.hub_health.get_whatsapp_hub", return_value=mock_hub), \
             patch("api.routes.hub_health.get_instagram_hub", return_value=mock_hub), \
             patch("api.routes.hub_health.get_tiktok_hub", return_value=mock_hub):
            result = await get_all_circuit_breaker_status()
        
        assert result["whatsapp"]["error"] == "No circuit breaker"
    
    @pytest.mark.asyncio
    async def test_get_status_hub_error(self):
        """Test status when hub getter raises error."""
        from api.routes.hub_health import get_all_circuit_breaker_status
        
        with patch("api.routes.hub_health.get_whatsapp_hub", 
                   side_effect=Exception("Connection failed")), \
             patch("api.routes.hub_health.get_instagram_hub",
                   side_effect=Exception("Not initialized")), \
             patch("api.routes.hub_health.get_tiktok_hub",
                   side_effect=Exception("Service unavailable")):
            result = await get_all_circuit_breaker_status()
        
        assert "error" in result["whatsapp"]
        assert "Connection failed" in result["whatsapp"]["error"]
    
    @pytest.mark.asyncio
    async def test_get_status_cb_without_state(self):
        """Test status when circuit breaker has no state attribute."""
        from api.routes.hub_health import get_all_circuit_breaker_status
        
        mock_hub = MagicMock()
        mock_cb = MagicMock(spec=["stats"])  # No state attribute
        mock_cb.stats = MagicMock()
        mock_cb.stats.failure_count = 5
        mock_cb.stats.success_count = 95
        mock_hub._circuit_breaker = mock_cb
        
        with patch("api.routes.hub_health.get_whatsapp_hub", return_value=mock_hub), \
             patch("api.routes.hub_health.get_instagram_hub", return_value=mock_hub), \
             patch("api.routes.hub_health.get_tiktok_hub", return_value=mock_hub):
            result = await get_all_circuit_breaker_status()
        
        assert result["whatsapp"]["state"] == "unknown"
    
    @pytest.mark.asyncio
    async def test_get_status_cb_without_stats(self):
        """Test status when circuit breaker has no stats attribute."""
        from api.routes.hub_health import get_all_circuit_breaker_status
        
        mock_hub = MagicMock()
        mock_cb = MagicMock(spec=["state"])  # No stats attribute
        mock_cb.state = MagicMock(value="closed")
        mock_hub._circuit_breaker = mock_cb
        
        with patch("api.routes.hub_health.get_whatsapp_hub", return_value=mock_hub), \
             patch("api.routes.hub_health.get_instagram_hub", return_value=mock_hub), \
             patch("api.routes.hub_health.get_tiktok_hub", return_value=mock_hub):
            result = await get_all_circuit_breaker_status()
        
        assert result["whatsapp"]["failure_count"] == 0
        assert result["whatsapp"]["success_count"] == 0


class TestRegisterHubs:
    """Tests for hub registration."""
    
    def test_register_hubs_success(self):
        """Test successful hub registration."""
        from api.routes.hub_health import _register_hubs
        
        mock_checker = MagicMock()
        mock_whatsapp = MagicMock()
        mock_instagram = MagicMock()
        mock_tiktok = MagicMock()
        
        with patch("api.routes.hub_health.get_health_checker", return_value=mock_checker), \
             patch("api.routes.hub_health.get_whatsapp_hub", return_value=mock_whatsapp), \
             patch("api.routes.hub_health.get_instagram_hub", return_value=mock_instagram), \
             patch("api.routes.hub_health.get_tiktok_hub", return_value=mock_tiktok):
            _register_hubs()
        
        assert mock_checker.register_hub.call_count == 3
    
    def test_register_hubs_with_errors(self):
        """Test hub registration with some hubs failing."""
        from api.routes.hub_health import _register_hubs
        
        mock_checker = MagicMock()
        
        with patch("api.routes.hub_health.get_health_checker", return_value=mock_checker), \
             patch("api.routes.hub_health.get_whatsapp_hub", 
                   side_effect=Exception("Not available")), \
             patch("api.routes.hub_health.get_instagram_hub", return_value=MagicMock()), \
             patch("api.routes.hub_health.get_tiktok_hub",
                   side_effect=Exception("Not initialized")):
            _register_hubs()
        
        # Only instagram should be registered
        assert mock_checker.register_hub.call_count == 1


class TestHealthResponse:
    """Tests for health response formatting."""
    
    @pytest.mark.asyncio
    async def test_health_response_format(self, mock_health_checker, mock_hub_health):
        """Test health response has correct format."""
        from api.routes.hub_health import get_hub_health
        
        mock_health_checker.check_hub_health = AsyncMock(return_value=mock_hub_health)
        
        result = await get_hub_health("whatsapp")
        
        # Check all required fields
        assert "name" in result
        assert "status" in result
        assert "circuit_breaker_state" in result
        assert "success_rate" in result
        assert "avg_latency_ms" in result
        assert "last_success" in result
        assert "last_failure" in result
        assert "details" in result
    
    @pytest.mark.asyncio
    async def test_latency_formatting(self, mock_health_checker):
        """Test latency is formatted correctly."""
        from api.routes.hub_health import get_hub_health
        
        health = MagicMock()
        health.name = "test"
        health.status = "healthy"
        health.circuit_breaker_state = "closed"
        health.success_rate = 100.0
        health.avg_latency_ms = 123.456789
        health.last_success = None
        health.last_failure = None
        health.details = {}
        
        mock_health_checker.check_hub_health = AsyncMock(return_value=health)
        
        result = await get_hub_health("test")
        
        # Should be formatted with 1 decimal place
        assert result["avg_latency_ms"] == "123.5"


class TestRouterConfiguration:
    """Tests for router configuration."""
    
    def test_router_prefix(self):
        """Test router has correct prefix."""
        from api.routes.hub_health import router
        
        assert router.prefix == "/hub"
    
    def test_router_tags(self):
        """Test router has correct tags."""
        from api.routes.hub_health import router
        
        assert "Hub Monitoring" in router.tags
