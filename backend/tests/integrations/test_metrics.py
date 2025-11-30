"""
Testes para o módulo de métricas dos Integration Hubs.
"""

import pytest
import time
from integrations.metrics import (
    HubMetricsRegistry,
    HubHealthChecker,
    HubHealth,
    MetricType,
    with_metrics,
    get_metrics_registry,
    export_prometheus_metrics,
)


class TestHubMetricsRegistry:
    """Testes para o registry de métricas."""
    
    @pytest.fixture
    def registry(self):
        """Registry limpo para cada teste."""
        reg = HubMetricsRegistry()
        reg.reset()
        return reg
    
    def test_record_request(self, registry):
        """Testa registro de requisições."""
        registry.record_request("whatsapp", "send_text")
        registry.record_request("whatsapp", "send_text")
        registry.record_request("instagram", "send_message")
        
        metrics = registry.get_metrics()
        assert metrics["requests"]["total"]["whatsapp:send_text"] == 2
        assert metrics["requests"]["total"]["instagram:send_message"] == 1
    
    def test_record_success(self, registry):
        """Testa registro de sucesso."""
        registry.record_success("whatsapp", "send_text", latency_ms=150.5)
        
        metrics = registry.get_metrics()
        assert metrics["requests"]["success"]["whatsapp:send_text"] == 1
        assert "whatsapp:send_text" in metrics["latencies"]
    
    def test_record_failure(self, registry):
        """Testa registro de falha."""
        registry.record_failure("whatsapp", "send_text", "TimeoutError")
        
        metrics = registry.get_metrics()
        assert metrics["requests"]["failure"]["whatsapp:send_text"] == 1
    
    def test_record_circuit_breaker_state(self, registry):
        """Testa registro de estado do circuit breaker."""
        registry.record_circuit_breaker_state("whatsapp", "open", 5)
        
        metrics = registry.get_metrics()
        assert metrics["circuit_breakers"]["whatsapp"]["state"] == "open"
        assert metrics["circuit_breakers"]["whatsapp"]["failures"] == 5
    
    def test_record_rate_limit_rejection(self, registry):
        """Testa registro de rejeição por rate limit."""
        registry.record_rate_limit_rejection("instagram")
        registry.record_rate_limit_rejection("instagram")
        
        metrics = registry.get_metrics()
        assert metrics["rate_limiting"]["rejections"]["instagram"] == 2
    
    def test_latency_stats_calculation(self, registry):
        """Testa cálculo de estatísticas de latência."""
        # Adicionar várias latências
        for latency in [100, 150, 200, 250, 300, 350, 400, 450, 500, 550]:
            registry.record_success("whatsapp", "send_text", latency_ms=latency)
        
        metrics = registry.get_metrics()
        stats = metrics["latencies"]["whatsapp:send_text"]
        
        assert stats["count"] == 10
        assert stats["avg"] == 325.0  # Média
        assert stats["p50"] >= 250  # Mediana aproximada (index 5 = 350)
    
    def test_get_instance_singleton(self):
        """Testa que get_instance retorna singleton."""
        reg1 = HubMetricsRegistry.get_instance()
        reg2 = HubMetricsRegistry.get_instance()
        assert reg1 is reg2
    
    def test_reset(self, registry):
        """Testa reset de métricas."""
        registry.record_request("whatsapp", "send_text")
        registry.record_success("whatsapp", "send_text", 100)
        
        registry.reset()
        
        metrics = registry.get_metrics()
        assert len(metrics["requests"]["total"]) == 0


class TestPrometheusExport:
    """Testes para exportação Prometheus."""
    
    @pytest.fixture
    def registry(self):
        """Registry com dados para exportação."""
        reg = HubMetricsRegistry()
        reg.reset()
        
        # Popular com dados
        reg.record_request("whatsapp", "send_text")
        reg.record_success("whatsapp", "send_text", 150)
        reg.record_circuit_breaker_state("whatsapp", "closed", 0)
        
        return reg
    
    def test_prometheus_format_contains_metrics(self, registry):
        """Testa que formato Prometheus contém métricas esperadas."""
        output = registry.to_prometheus_format()
        
        # Verificar headers
        assert "# HELP hub_requests_total" in output
        assert "# TYPE hub_requests_total counter" in output
        
        # Verificar métricas
        assert 'hub_requests_total{hub="whatsapp",method="send_text"}' in output
        assert 'hub_circuit_breaker_state{hub="whatsapp"' in output
    
    def test_prometheus_format_valid_structure(self, registry):
        """Testa estrutura válida do formato Prometheus."""
        output = registry.to_prometheus_format()
        lines = output.strip().split("\n")
        
        for line in lines:
            if line.startswith("#"):
                # Comentário - deve ter HELP ou TYPE
                assert "HELP" in line or "TYPE" in line
            elif line:
                # Métrica - deve ter nome{labels} value
                assert "{" in line or line.split()[-1].replace(".", "").isdigit()


class TestWithMetricsDecorator:
    """Testes para o decorator with_metrics."""
    
    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reseta registry antes de cada teste."""
        HubMetricsRegistry.get_instance().reset()
    
    @pytest.mark.asyncio
    async def test_decorator_records_success(self):
        """Testa que decorator registra sucesso."""
        @with_metrics("test_hub", "test_method")
        async def successful_operation():
            return "success"
        
        result = await successful_operation()
        
        assert result == "success"
        
        registry = HubMetricsRegistry.get_instance()
        metrics = registry.get_metrics()
        
        assert metrics["requests"]["total"]["test_hub:test_method"] == 1
        assert metrics["requests"]["success"]["test_hub:test_method"] == 1
    
    @pytest.mark.asyncio
    async def test_decorator_records_failure(self):
        """Testa que decorator registra falha."""
        @with_metrics("test_hub", "test_method")
        async def failing_operation():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            await failing_operation()
        
        registry = HubMetricsRegistry.get_instance()
        metrics = registry.get_metrics()
        
        assert metrics["requests"]["total"]["test_hub:test_method"] == 1
        assert metrics["requests"]["failure"]["test_hub:test_method"] == 1
    
    @pytest.mark.asyncio
    async def test_decorator_records_latency(self):
        """Testa que decorator registra latência."""
        import asyncio
        
        @with_metrics("test_hub", "slow_method")
        async def slow_operation():
            await asyncio.sleep(0.05)  # 50ms
            return "done"
        
        await slow_operation()
        
        registry = HubMetricsRegistry.get_instance()
        metrics = registry.get_metrics()
        
        latency = metrics["latencies"].get("test_hub:slow_method", {})
        assert latency.get("count", 0) == 1
        assert latency.get("avg", 0) >= 50  # Pelo menos 50ms


class TestHubHealthChecker:
    """Testes para o health checker."""
    
    @pytest.fixture
    def checker(self):
        """Health checker limpo."""
        checker = HubHealthChecker()
        HubMetricsRegistry.get_instance().reset()
        return checker
    
    @pytest.mark.asyncio
    async def test_check_hub_health_healthy(self, checker):
        """Testa verificação de hub saudável."""
        registry = HubMetricsRegistry.get_instance()
        
        # Simular tráfego saudável
        for _ in range(10):
            registry.record_request("whatsapp")
            registry.record_success("whatsapp", latency_ms=100)
        
        registry.record_circuit_breaker_state("whatsapp", "closed", 0)
        
        health = await checker.check_hub_health("whatsapp")
        
        assert health.status == "healthy"
        assert health.circuit_breaker_state == "closed"
        assert health.success_rate == 100.0
    
    @pytest.mark.asyncio
    async def test_check_hub_health_degraded(self, checker):
        """Testa verificação de hub degradado."""
        registry = HubMetricsRegistry.get_instance()
        
        # Simular tráfego com falhas
        for _ in range(8):
            registry.record_request("instagram")
            registry.record_success("instagram")
        for _ in range(2):
            registry.record_request("instagram")
            registry.record_failure("instagram")
        
        registry.record_circuit_breaker_state("instagram", "half_open", 2)
        
        health = await checker.check_hub_health("instagram")
        
        # 80% success rate ou half_open = degraded
        assert health.status in ["degraded", "unhealthy"]
    
    @pytest.mark.asyncio
    async def test_check_hub_health_unhealthy(self, checker):
        """Testa verificação de hub não saudável."""
        registry = HubMetricsRegistry.get_instance()
        
        registry.record_circuit_breaker_state("tiktok", "open", 5)
        
        health = await checker.check_hub_health("tiktok")
        
        assert health.status == "unhealthy"
        assert health.circuit_breaker_state == "open"
    
    @pytest.mark.asyncio
    async def test_get_overall_status(self, checker):
        """Testa status geral."""
        registry = HubMetricsRegistry.get_instance()
        
        # Registrar hubs
        class FakeHub:
            pass
        
        checker.register_hub("hub1", FakeHub())
        checker.register_hub("hub2", FakeHub())
        
        registry.record_circuit_breaker_state("hub1", "closed", 0)
        registry.record_circuit_breaker_state("hub2", "closed", 0)
        
        status = await checker.get_overall_status()
        
        assert "status" in status
        assert "timestamp" in status
        assert "hubs" in status


class TestHubHealth:
    """Testes para dataclass HubHealth."""
    
    def test_hub_health_creation(self):
        """Testa criação de HubHealth."""
        health = HubHealth(
            name="whatsapp",
            status="healthy",
            circuit_breaker_state="closed",
            success_rate=99.5,
            avg_latency_ms=150.2
        )
        
        assert health.name == "whatsapp"
        assert health.status == "healthy"
        assert health.success_rate == 99.5
    
    def test_hub_health_defaults(self):
        """Testa valores padrão de HubHealth."""
        health = HubHealth(
            name="test",
            status="unknown",
            circuit_breaker_state="unknown"
        )
        
        assert health.last_success is None
        assert health.last_failure is None
        assert health.details == {}


class TestMetricType:
    """Testes para enum MetricType."""
    
    def test_metric_types(self):
        """Testa valores do enum."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.SUMMARY.value == "summary"
