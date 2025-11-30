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

Autor: Didin Fácil
Versão: 1.0.0
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


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


@pytest.fixture
def client(mock_hubs, mock_health_checker, mock_metrics_registry,
           mock_prometheus_export):
    """Cliente de teste com mocks."""
    from api.main import app
    return TestClient(app)


# ============================================
# TESTES - HEALTH ENDPOINTS
# ============================================

class TestHealthEndpoints:
    """Testes para endpoints de health check."""

    def test_get_overall_health(self, client, mock_health_checker):
        """Testa GET /hub/health."""
        response = client.get("/hub/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "hubs" in data
        assert "timestamp" in data

    def test_get_hub_health_whatsapp(self, client, mock_health_checker):
        """Testa GET /hub/health/whatsapp."""
        response = client.get("/hub/health/whatsapp")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "whatsapp"
        assert data["status"] == "healthy"
        assert "success_rate" in data

    def test_get_hub_health_instagram(self, client, mock_health_checker):
        """Testa GET /hub/health/instagram."""
        mock_health_checker.check_hub_health.return_value = MagicMock(
            name="instagram",
            status="healthy",
            circuit_breaker_state="closed",
            success_rate=96.0,
            avg_latency_ms=200.0,
            last_success="2024-01-01T00:00:00Z",
            last_failure=None,
            details={}
        )

        response = client.get("/hub/health/instagram")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "instagram"

    def test_get_hub_health_tiktok(self, client, mock_health_checker):
        """Testa GET /hub/health/tiktok."""
        mock_health_checker.check_hub_health.return_value = MagicMock(
            name="tiktok",
            status="degraded",
            circuit_breaker_state="half_open",
            success_rate=80.0,
            avg_latency_ms=500.0,
            last_success="2024-01-01T00:00:00Z",
            last_failure="2024-01-01T00:05:00Z",
            details={"reason": "High latency"}
        )

        response = client.get("/hub/health/tiktok")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "tiktok"
        assert data["status"] == "degraded"


# ============================================
# TESTES - METRICS ENDPOINTS
# ============================================

class TestMetricsEndpoints:
    """Testes para endpoints de métricas."""

    def test_get_metrics_json(self, client, mock_metrics_registry):
        """Testa GET /hub/metrics."""
        response = client.get("/hub/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "whatsapp" in data
        assert "instagram" in data
        assert data["whatsapp"]["success_count"] == 100

    def test_get_metrics_prometheus(self, client, mock_prometheus_export):
        """Testa GET /hub/metrics/prometheus."""
        response = client.get("/hub/metrics/prometheus")

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

    def test_get_all_circuit_breaker_status(self, client, mock_hubs):
        """Testa GET /hub/circuit-breaker/status."""
        response = client.get("/hub/circuit-breaker/status")

        assert response.status_code == 200
        data = response.json()
        assert "whatsapp" in data
        assert "instagram" in data
        assert "tiktok" in data
        assert data["whatsapp"]["state"] == "closed"
        assert data["tiktok"]["state"] == "half_open"

    def test_reset_circuit_breaker_whatsapp(self, client, mock_hubs):
        """Testa POST /hub/circuit-breaker/whatsapp/reset."""
        mock_hubs["whatsapp"]._circuit_breaker.reset = AsyncMock()
        mock_hubs["whatsapp"]._circuit_breaker.state.value = "closed"

        response = client.post("/hub/circuit-breaker/whatsapp/reset")

        assert response.status_code == 200
        data = response.json()
        assert data["hub"] == "whatsapp"
        assert "message" in data

    def test_reset_circuit_breaker_invalid_hub(self, client):
        """Testa reset de hub inexistente."""
        response = client.post("/hub/circuit-breaker/invalid/reset")

        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    def test_circuit_breaker_status_with_errors(self, client):
        """Testa status quando hub falha ao inicializar."""
        with patch('api.routes.hub_health.get_whatsapp_hub') as mock:
            mock.side_effect = Exception("Hub não configurado")

            response = client.get("/hub/circuit-breaker/status")

            assert response.status_code == 200
            data = response.json()
            assert "error" in data.get("whatsapp", {})


# ============================================
# TESTES - INTEGRAÇÃO
# ============================================

class TestHealthRouteIntegration:
    """Testes de integração das rotas."""

    def test_health_endpoints_all_available(self, client):
        """Verifica que todos os endpoints respondem."""
        endpoints = [
            "/hub/health",
            "/hub/health/whatsapp",
            "/hub/metrics",
            "/hub/metrics/prometheus",
            "/hub/circuit-breaker/status"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Aceita 200 ou 500 (se hub não configurado)
            assert response.status_code in (200, 500), (
                f"Endpoint {endpoint} retornou {response.status_code}"
            )

    def test_prometheus_format_valid(self, client, mock_prometheus_export):
        """Verifica formato Prometheus válido."""
        response = client.get("/hub/metrics/prometheus")

        lines = response.text.strip().split("\n")
        for line in lines:
            if line.startswith("#"):
                # Comentário: deve ser HELP ou TYPE
                assert line.startswith("# HELP") or line.startswith("# TYPE")
            elif line.strip():
                # Métrica: deve ter formato name{labels} value ou name value
                assert " " in line, f"Linha inválida: {line}"
