"""
Tests for Hub Health Routes
Health monitoring and metrics endpoints.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestHubHealthRouter:
    """Tests for hub health router"""

    def test_router_exists(self):
        """Test router is properly configured"""
        from api.routes.hub_health import router

        assert router is not None
        assert router.prefix == "/hub"
        assert "Hub Monitoring" in router.tags


class TestHealthEndpoints:
    """Tests for health check endpoints"""

    @pytest.mark.asyncio
    async def test_get_overall_health(self):
        """Test overall health endpoint"""
        from api.routes.hub_health import get_overall_health

        with patch('api.routes.hub_health.get_health_checker') as mock_get:
            mock_checker = MagicMock()
            mock_checker.get_overall_status = AsyncMock(return_value={
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hubs": {}
            })
            mock_get.return_value = mock_checker

            result = await get_overall_health()

            assert "status" in result
            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_hub_health(self):
        """Test individual hub health endpoint"""
        from api.routes.hub_health import get_hub_health

        with patch('api.routes.hub_health.get_health_checker') as mock_get:
            mock_health = MagicMock()
            mock_health.name = "whatsapp"
            mock_health.status = "healthy"
            mock_health.circuit_breaker_state = "closed"
            mock_health.success_rate = 99.5
            mock_health.avg_latency_ms = 150.0
            mock_health.last_success = datetime.now(timezone.utc)
            mock_health.last_failure = None
            mock_health.details = {}

            mock_checker = MagicMock()
            mock_checker.check_hub_health = AsyncMock(return_value=mock_health)
            mock_get.return_value = mock_checker

            result = await get_hub_health("whatsapp")

            assert result["name"] == "whatsapp"
            assert result["status"] == "healthy"
            assert "99.5%" in result["success_rate"]

    @pytest.mark.asyncio
    async def test_get_hub_health_with_failure(self):
        """Test hub health with failure info"""
        from api.routes.hub_health import get_hub_health

        with patch('api.routes.hub_health.get_health_checker') as mock_get:
            mock_health = MagicMock()
            mock_health.name = "instagram"
            mock_health.status = "degraded"
            mock_health.circuit_breaker_state = "half-open"
            mock_health.success_rate = 85.0
            mock_health.avg_latency_ms = 500.0
            mock_health.last_success = datetime.now(timezone.utc)
            mock_health.last_failure = datetime.now(timezone.utc)
            mock_health.details = {"error": "Rate limited"}

            mock_checker = MagicMock()
            mock_checker.check_hub_health = AsyncMock(return_value=mock_health)
            mock_get.return_value = mock_checker

            result = await get_hub_health("instagram")

            assert result["status"] == "degraded"
            assert result["circuit_breaker_state"] == "half-open"


class TestMetricsEndpoints:
    """Tests for metrics endpoints"""

    @pytest.mark.asyncio
    async def test_get_metrics_json(self):
        """Test JSON metrics endpoint"""
        from api.routes.hub_health import get_metrics_json

        with patch('api.routes.hub_health.get_metrics_registry') as mock_get:
            mock_registry = MagicMock()
            mock_registry.get_metrics.return_value = {
                "requests_total": 1000,
                "latency_avg_ms": 200,
                "errors_total": 5
            }
            mock_get.return_value = mock_registry

            result = await get_metrics_json()

            assert "requests_total" in result
            assert result["requests_total"] == 1000

    @pytest.mark.asyncio
    async def test_get_metrics_prometheus(self):
        """Test Prometheus metrics endpoint"""
        from api.routes.hub_health import get_metrics_prometheus

        with patch('api.routes.hub_health.export_prometheus_metrics') as mock_export:
            mock_export.return_value = (
                "# HELP requests_total Total requests\n"
                "requests_total 1000\n"
            )

            response = await get_metrics_prometheus()

            assert response.media_type == "text/plain; charset=utf-8"
            assert "requests_total" in response.body.decode()


class TestCircuitBreakerEndpoints:
    """Tests for circuit breaker management"""

    @pytest.mark.asyncio
    async def test_reset_circuit_breaker_whatsapp(self):
        """Test resetting WhatsApp circuit breaker"""
        from api.routes.hub_health import reset_circuit_breaker

        with patch('api.routes.hub_health.get_whatsapp_hub') as mock_get:
            mock_hub = MagicMock()
            mock_cb = MagicMock()
            mock_cb.reset = AsyncMock()
            mock_cb.state = MagicMock()
            mock_cb.state.value = "closed"
            mock_hub._circuit_breaker = mock_cb
            mock_get.return_value = mock_hub

            result = await reset_circuit_breaker("whatsapp")

            assert result["hub"] == "whatsapp"
            assert "resetado" in result["message"]

    @pytest.mark.asyncio
    async def test_reset_circuit_breaker_instagram(self):
        """Test resetting Instagram circuit breaker"""
        from api.routes.hub_health import reset_circuit_breaker

        with patch('api.routes.hub_health.get_instagram_hub') as mock_get:
            mock_hub = MagicMock()
            mock_cb = MagicMock()
            mock_cb.reset = AsyncMock()
            mock_cb.state = MagicMock()
            mock_cb.state.value = "closed"
            mock_hub._circuit_breaker = mock_cb
            mock_get.return_value = mock_hub

            result = await reset_circuit_breaker("instagram")

            assert result["hub"] == "instagram"

    @pytest.mark.asyncio
    async def test_reset_circuit_breaker_tiktok(self):
        """Test resetting TikTok circuit breaker"""
        from api.routes.hub_health import reset_circuit_breaker

        with patch('api.routes.hub_health.get_tiktok_hub') as mock_get:
            mock_hub = MagicMock()
            mock_cb = MagicMock()
            mock_cb.reset = AsyncMock()
            mock_cb.state = MagicMock()
            mock_cb.state.value = "closed"
            mock_hub._circuit_breaker = mock_cb
            mock_get.return_value = mock_hub

            result = await reset_circuit_breaker("tiktok")

            assert result["hub"] == "tiktok"

    @pytest.mark.asyncio
    async def test_reset_circuit_breaker_unknown_hub(self):
        """Test resetting unknown hub returns error"""
        from api.routes.hub_health import reset_circuit_breaker

        result = await reset_circuit_breaker("unknown")

        assert "error" in result
        assert "não encontrado" in result["error"]

    @pytest.mark.asyncio
    async def test_reset_circuit_breaker_no_cb(self):
        """Test resetting hub without circuit breaker"""
        from api.routes.hub_health import reset_circuit_breaker

        with patch('api.routes.hub_health.get_whatsapp_hub') as mock_get:
            mock_hub = MagicMock(spec=[])
            mock_get.return_value = mock_hub

            result = await reset_circuit_breaker("whatsapp")

            assert "error" in result

    @pytest.mark.asyncio
    async def test_get_all_circuit_breaker_status(self):
        """Test getting all circuit breaker statuses"""
        from api.routes.hub_health import get_all_circuit_breaker_status

        with patch('api.routes.hub_health.get_whatsapp_hub') as mock_wa, \
             patch('api.routes.hub_health.get_instagram_hub') as mock_ig, \
             patch('api.routes.hub_health.get_tiktok_hub') as mock_tt:

            for mock_get in [mock_wa, mock_ig, mock_tt]:
                mock_hub = MagicMock()
                mock_cb = MagicMock()
                mock_cb.state = MagicMock()
                mock_cb.state.value = "closed"
                mock_cb.stats = MagicMock()
                mock_cb.stats.failure_count = 0
                mock_cb.stats.success_count = 100
                mock_hub._circuit_breaker = mock_cb
                mock_get.return_value = mock_hub

            result = await get_all_circuit_breaker_status()

            assert "whatsapp" in result
            assert "instagram" in result
            assert "tiktok" in result

    @pytest.mark.asyncio
    async def test_get_all_circuit_breaker_status_with_error(self):
        """Test circuit breaker status when hub throws exception"""
        from api.routes.hub_health import get_all_circuit_breaker_status

        with patch('api.routes.hub_health.get_whatsapp_hub') as mock_wa, \
             patch('api.routes.hub_health.get_instagram_hub') as mock_ig, \
             patch('api.routes.hub_health.get_tiktok_hub') as mock_tt:

            mock_wa.side_effect = Exception("Connection failed")
            mock_ig.return_value = MagicMock(spec=[])
            mock_tt.side_effect = Exception("Hub not available")

            result = await get_all_circuit_breaker_status()

            assert "error" in result["whatsapp"]
            assert "error" in result["tiktok"]


class TestRegisterHubs:
    """Tests for hub registration"""

    def test_register_hubs_function_exists(self):
        """Test _register_hubs function exists"""
        from api.routes.hub_health import _register_hubs

        assert callable(_register_hubs)


class TestImports:
    """Tests for module imports"""

    def test_metrics_imports(self):
        """Test metrics functions are imported"""
        from api.routes.hub_health import (HubHealthChecker,
                                           export_prometheus_metrics,
                                           get_health_checker,
                                           get_metrics_registry)

        assert get_metrics_registry is not None
        assert get_health_checker is not None
        assert export_prometheus_metrics is not None

    def test_hub_imports(self):
        """Test hub getters are imported"""
        from api.routes.hub_health import (get_instagram_hub, get_tiktok_hub,
                                           get_whatsapp_hub)

        assert get_whatsapp_hub is not None
        assert get_instagram_hub is not None
        assert get_tiktok_hub is not None
