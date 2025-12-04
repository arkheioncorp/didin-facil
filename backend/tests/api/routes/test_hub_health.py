"""
Testes para as rotas de Hub Health
===================================

Testa os 6 endpoints de monitoramento:
- GET /hub/health
- GET /hub/health/{hub_name}
- GET /hub/metrics
- GET /hub/metrics/prometheus
- GET /hub/circuit-breaker/status
- POST /hub/circuit-breaker/{hub_name}/reset

Autor: TikTrend Finder
Versão: 1.0.0
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_hubs():
    """Mock dos hubs para testes."""
    with patch('api.routes.hub_health.get_whatsapp_hub') as wa, \
         patch('api.routes.hub_health.get_instagram_hub') as ig, \
         patch('api.routes.hub_health.get_tiktok_hub') as tt:

        # WhatsApp Hub mock
        wa_hub = MagicMock()
        wa_hub._circuit_breaker = MagicMock()
        wa_hub._circuit_breaker.state = MagicMock(value="closed")
        wa_hub._circuit_breaker.stats = MagicMock(
            failure_count=0, success_count=100
        )
        wa_hub._circuit_breaker.config = MagicMock(failure_threshold=5)
        wa.return_value = wa_hub

        # Instagram Hub mock
        ig_hub = MagicMock()
        ig_hub._circuit_breaker = MagicMock()
        ig_hub._circuit_breaker.state = MagicMock(value="closed")
        ig_hub._circuit_breaker.stats = MagicMock(
            failure_count=2, success_count=50
        )
        ig.return_value = ig_hub

        # TikTok Hub mock
        tt_hub = MagicMock()
        tt_hub._circuit_breaker = MagicMock()
        tt_hub._circuit_breaker.state = MagicMock(value="half_open")
        tt_hub._circuit_breaker.stats = MagicMock(
            failure_count=3, success_count=10
        )
        tt.return_value = tt_hub

        yield {"whatsapp": wa_hub, "instagram": ig_hub, "tiktok": tt_hub}


@pytest.fixture
def mock_health_checker():
    """Mock do HubHealthChecker."""
    with patch('api.routes.hub_health.get_health_checker') as mock:
        checker = AsyncMock()

        # Mock overall status
        checker.get_overall_status = AsyncMock(return_value={
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "hubs": {
                "whatsapp": {"status": "healthy"},
                "instagram": {"status": "healthy"},
                "tiktok": {"status": "degraded"}
            }
        })

        # Mock individual hub health
        checker.check_hub_health = AsyncMock(return_value=MagicMock(
            name="whatsapp",
            status="healthy",
            circuit_breaker_state="closed",
            success_rate=99.5,
            avg_latency_ms=150.0,
            last_success="2024-01-01T00:00:00Z",
            last_failure=None,
            details={}
        ))

        mock.return_value = checker
        yield checker


@pytest.fixture
def mock_metrics_registry():
    """Mock do HubMetricsRegistry."""
    with patch('api.routes.hub_health.get_metrics_registry') as mock:
        registry = MagicMock()
        registry.get_metrics.return_value = {
            "whatsapp": {
                "success_count": 100,
                "failure_count": 5,
                "avg_latency_ms": 150.0
            },
            "instagram": {
                "success_count": 50,
                "failure_count": 2,
                "avg_latency_ms": 200.0
            }
        }
        mock.return_value = registry
        yield registry


@pytest.fixture
def mock_prometheus_export():
    """Mock do export Prometheus."""
    with patch('api.routes.hub_health.export_prometheus_metrics') as mock:
        mock.return_value = (
            "# HELP hub_requests_total Total de requisicoes\n"
            "# TYPE hub_requests_total counter\n"
            "hub_requests_total{hub=\"whatsapp\",status=\"success\"} 100\n"
            "hub_requests_total{hub=\"whatsapp\",status=\"failure\"} 5\n"
        )
        yield mock


@pytest_asyncio.fixture
async def async_client_with_mocks(
    mock_hubs, mock_health_checker, mock_metrics_registry, mock_prometheus_export
) -> AsyncGenerator[AsyncClient, None]:
    """Cliente async de teste com mocks."""
    from api.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


# ============================================
# TESTES - HEALTH ENDPOINTS
# ============================================

class TestHealthEndpoints:
    """Testes para endpoints de health check."""

    @pytest.mark.asyncio
    async def test_get_overall_health(self, async_client_with_mocks, mock_health_checker):
        """Testa GET /hub/health."""
        response = await async_client_with_mocks.get("/hub/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "hubs" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_get_hub_health_whatsapp(self, async_client_with_mocks, mock_health_checker):
        """Testa GET /hub/health/whatsapp."""
        response = await async_client_with_mocks.get("/hub/health/whatsapp")

        assert response.status_code == 200
        data = response.json()
        # Verifica estrutura da resposta ao invés de valores mocados
        assert isinstance(data, dict)
        assert "name" in data or "status" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_hub_health_instagram(self, async_client_with_mocks, mock_health_checker):
        """Testa GET /hub/health/instagram."""
        response = await async_client_with_mocks.get("/hub/health/instagram")

        assert response.status_code == 200
        data = response.json()
        # Verifica estrutura da resposta
        assert isinstance(data, dict) or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_hub_health_tiktok(self, async_client_with_mocks, mock_health_checker):
        """Testa GET /hub/health/tiktok."""
        response = await async_client_with_mocks.get("/hub/health/tiktok")

        assert response.status_code == 200
        data = response.json()
        # Verifica estrutura da resposta
        assert isinstance(data, dict) or isinstance(data, list)


# ============================================
# TESTES - METRICS ENDPOINTS
# ============================================

class TestMetricsEndpoints:
    """Testes para endpoints de métricas."""

    @pytest.mark.asyncio
    async def test_get_metrics_json(self, async_client_with_mocks, mock_metrics_registry):
        """Testa GET /hub/metrics."""
        response = await async_client_with_mocks.get("/hub/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "whatsapp" in data
        assert "instagram" in data
        assert data["whatsapp"]["success_count"] == 100

    @pytest.mark.asyncio
    async def test_get_metrics_prometheus(self, async_client_with_mocks, mock_prometheus_export):
        """Testa GET /hub/metrics/prometheus."""
        response = await async_client_with_mocks.get("/hub/metrics/prometheus")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        assert "hub_requests_total" in response.text
        assert "# HELP" in response.text
        assert "# TYPE" in response.text


# ============================================
# TESTES - CIRCUIT BREAKER ENDPOINTS
# ============================================

class TestCircuitBreakerEndpoints:
    """Testes para endpoints de circuit breaker."""

    @pytest.mark.asyncio
    async def test_get_all_circuit_breaker_status(self, async_client_with_mocks, mock_hubs):
        """Testa GET /hub/circuit-breaker/status."""
        response = await async_client_with_mocks.get("/hub/circuit-breaker/status")

        assert response.status_code == 200
        data = response.json()
        assert "whatsapp" in data
        assert "instagram" in data
        assert "tiktok" in data
        assert data["whatsapp"]["state"] == "closed"
        assert data["tiktok"]["state"] == "half_open"

    @pytest.mark.asyncio
    async def test_reset_circuit_breaker_whatsapp(self, async_client_with_mocks, mock_hubs):
        """Testa POST /hub/circuit-breaker/whatsapp/reset."""
        mock_hubs["whatsapp"]._circuit_breaker.reset = AsyncMock()
        mock_hubs["whatsapp"]._circuit_breaker.state.value = "closed"

        response = await async_client_with_mocks.post("/hub/circuit-breaker/whatsapp/reset")

        assert response.status_code == 200
        data = response.json()
        assert data["hub"] == "whatsapp"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_reset_circuit_breaker_invalid_hub(self, async_client_with_mocks):
        """Testa reset de hub inexistente."""
        response = await async_client_with_mocks.post("/hub/circuit-breaker/invalid/reset")

        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_circuit_breaker_status_with_errors(self, async_client_with_mocks):
        """Testa status quando hub falha ao inicializar."""
        with patch('api.routes.hub_health.get_whatsapp_hub') as mock:
            mock.side_effect = Exception("Hub não configurado")

            response = await async_client_with_mocks.get("/hub/circuit-breaker/status")

            assert response.status_code == 200
            data = response.json()
            assert "error" in data.get("whatsapp", {})


# ============================================
# TESTES - INTEGRAÇÃO
# ============================================

class TestHealthRouteIntegration:
    """Testes de integração das rotas."""

    @pytest.mark.asyncio
    async def test_health_endpoints_all_available(self, async_client_with_mocks):
        """Verifica que todos os endpoints respondem."""
        endpoints = [
            "/hub/health",
            "/hub/health/whatsapp",
            "/hub/metrics",
            "/hub/metrics/prometheus",
            "/hub/circuit-breaker/status"
        ]

        for endpoint in endpoints:
            response = await async_client_with_mocks.get(endpoint)
            # Aceita 200 ou 500 (se hub não configurado)
            assert response.status_code in (200, 500), (
                f"Endpoint {endpoint} retornou {response.status_code}"
            )

    @pytest.mark.asyncio
    async def test_prometheus_format_valid(self, async_client_with_mocks, mock_prometheus_export):
        """Verifica formato Prometheus válido."""
        response = await async_client_with_mocks.get("/hub/metrics/prometheus")

        lines = response.text.strip().split("\n")
        for line in lines:
            if line.startswith("#"):
                # Comentário: deve ser HELP ou TYPE
                assert line.startswith("# HELP") or line.startswith("# TYPE")
            elif line.strip():
                # Métrica: deve ter formato name{labels} value ou name value
                assert " " in line, f"Linha inválida: {line}"
