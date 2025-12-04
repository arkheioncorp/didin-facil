"""
Hub Metrics Module
==================
Métricas Prometheus para monitoramento dos Integration Hubs.

Este módulo fornece:
- Contadores de requisições por hub
- Histogramas de latência
- Gauges para estado dos circuit breakers
- Endpoint /metrics compatível com Prometheus

Autor: Didin Fácil
Versão: 1.0.0
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger(__name__)


# ============================================
# METRIC TYPES
# ============================================

class MetricType(Enum):
    """Tipos de métricas suportadas."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """Valor de uma métrica com labels."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE
    help_text: str = ""
    timestamp: float = field(default_factory=time.time)


# ============================================
# PROMETHEUS REGISTRY
# ============================================

class HubMetricsRegistry:
    """
    Registry centralizado de métricas dos hubs.
    
    Coleta e expõe métricas em formato Prometheus.
    """
    
    _instance: Optional["HubMetricsRegistry"] = None
    
    def __init__(self):
        # Contadores
        self._request_total: Dict[str, int] = {}
        self._request_success: Dict[str, int] = {}
        self._request_failure: Dict[str, int] = {}
        
        # Latências (histograma simplificado)
        self._latencies: Dict[str, list] = {}
        
        # Circuit breaker states
        self._circuit_breaker_state: Dict[str, str] = {}
        self._circuit_breaker_failures: Dict[str, int] = {}
        
        # Rate limiter
        self._rate_limit_rejections: Dict[str, int] = {}
        
        # Timestamps
        self._last_success: Dict[str, float] = {}
        self._last_failure: Dict[str, float] = {}
    
    @classmethod
    def get_instance(cls) -> "HubMetricsRegistry":
        """Retorna singleton do registry."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _make_key(self, hub: str, method: str = "") -> str:
        """Cria chave para métricas."""
        if method:
            return f"{hub}:{method}"
        return hub
    
    # ============================================
    # RECORDING METHODS
    # ============================================
    
    def record_request(self, hub: str, method: str = ""):
        """Registra uma requisição."""
        key = self._make_key(hub, method)
        self._request_total[key] = self._request_total.get(key, 0) + 1
    
    def record_success(self, hub: str, method: str = "", latency_ms: float = 0):
        """Registra sucesso de requisição."""
        key = self._make_key(hub, method)
        self._request_success[key] = self._request_success.get(key, 0) + 1
        self._last_success[key] = time.time()
        
        if latency_ms > 0:
            if key not in self._latencies:
                self._latencies[key] = []
            # Mantém últimas 1000 latências
            self._latencies[key].append(latency_ms)
            if len(self._latencies[key]) > 1000:
                self._latencies[key] = self._latencies[key][-1000:]
    
    def record_failure(self, hub: str, method: str = "", error_type: str = ""):
        """Registra falha de requisição."""
        key = self._make_key(hub, method)
        self._request_failure[key] = self._request_failure.get(key, 0) + 1
        self._last_failure[key] = time.time()
    
    def record_circuit_breaker_state(self, hub: str, state: str, failures: int):
        """Registra estado do circuit breaker."""
        self._circuit_breaker_state[hub] = state
        self._circuit_breaker_failures[hub] = failures
    
    def record_rate_limit_rejection(self, hub: str):
        """Registra rejeição por rate limit."""
        self._rate_limit_rejections[hub] = (
            self._rate_limit_rejections.get(hub, 0) + 1
        )
    
    # ============================================
    # QUERY METHODS
    # ============================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna todas as métricas em formato dict."""
        return {
            "requests": {
                "total": self._request_total.copy(),
                "success": self._request_success.copy(),
                "failure": self._request_failure.copy(),
            },
            "latencies": {
                key: self._calculate_latency_stats(values)
                for key, values in self._latencies.items()
            },
            "circuit_breakers": {
                hub: {
                    "state": self._circuit_breaker_state.get(hub, "unknown"),
                    "failures": self._circuit_breaker_failures.get(hub, 0)
                }
                for hub in set(
                    list(self._circuit_breaker_state.keys()) +
                    list(self._circuit_breaker_failures.keys())
                )
            },
            "rate_limiting": {
                "rejections": self._rate_limit_rejections.copy()
            },
            "last_activity": {
                "success": self._last_success.copy(),
                "failure": self._last_failure.copy(),
            }
        }
    
    def _calculate_latency_stats(self, values: list) -> Dict[str, float]:
        """Calcula estatísticas de latência."""
        if not values:
            return {"count": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_vals = sorted(values)
        count = len(sorted_vals)
        
        return {
            "count": count,
            "avg": sum(sorted_vals) / count,
            "p50": sorted_vals[int(count * 0.5)],
            "p95": sorted_vals[int(count * 0.95)] if count >= 20 else sorted_vals[-1],
            "p99": sorted_vals[int(count * 0.99)] if count >= 100 else sorted_vals[-1],
        }
    
    def to_prometheus_format(self) -> str:
        """Exporta métricas em formato Prometheus text."""
        lines = []
        
        # Request counters
        lines.append("# HELP hub_requests_total Total de requisições por hub")
        lines.append("# TYPE hub_requests_total counter")
        for key, value in self._request_total.items():
            hub, method = (key.split(":") + [""])[:2]
            lines.append(
                f'hub_requests_total{{hub="{hub}",method="{method}"}} {value}'
            )
        
        lines.append("")
        lines.append("# HELP hub_requests_success_total Requisições bem-sucedidas")
        lines.append("# TYPE hub_requests_success_total counter")
        for key, value in self._request_success.items():
            hub, method = (key.split(":") + [""])[:2]
            lines.append(
                f'hub_requests_success_total{{hub="{hub}",method="{method}"}} {value}'
            )
        
        lines.append("")
        lines.append("# HELP hub_requests_failure_total Requisições com falha")
        lines.append("# TYPE hub_requests_failure_total counter")
        for key, value in self._request_failure.items():
            hub, method = (key.split(":") + [""])[:2]
            lines.append(
                f'hub_requests_failure_total{{hub="{hub}",method="{method}"}} {value}'
            )
        
        # Latency histograms
        lines.append("")
        lines.append("# HELP hub_request_latency_ms Latência de requisições em ms")
        lines.append("# TYPE hub_request_latency_ms summary")
        for key, values in self._latencies.items():
            hub, method = (key.split(":") + [""])[:2]
            stats = self._calculate_latency_stats(values)
            lines.append(
                f'hub_request_latency_ms{{hub="{hub}",method="{method}",'
                f'quantile="0.5"}} {stats["p50"]}'
            )
            lines.append(
                f'hub_request_latency_ms{{hub="{hub}",method="{method}",'
                f'quantile="0.95"}} {stats["p95"]}'
            )
            lines.append(
                f'hub_request_latency_ms{{hub="{hub}",method="{method}",'
                f'quantile="0.99"}} {stats["p99"]}'
            )
            lines.append(
                f'hub_request_latency_ms_count{{hub="{hub}",'
                f'method="{method}"}} {stats["count"]}'
            )
        
        # Circuit breaker
        lines.append("")
        lines.append("# HELP hub_circuit_breaker_state Estado do circuit breaker")
        lines.append("# TYPE hub_circuit_breaker_state gauge")
        state_map = {"closed": 0, "half_open": 1, "open": 2}
        for hub, state in self._circuit_breaker_state.items():
            state_value = state_map.get(state.lower(), -1)
            lines.append(
                f'hub_circuit_breaker_state{{hub="{hub}",state="{state}"}} '
                f'{state_value}'
            )
        
        lines.append("")
        lines.append("# HELP hub_circuit_breaker_failures Falhas do circuit breaker")
        lines.append("# TYPE hub_circuit_breaker_failures gauge")
        for hub, failures in self._circuit_breaker_failures.items():
            lines.append(
                f'hub_circuit_breaker_failures{{hub="{hub}"}} {failures}'
            )
        
        # Rate limiting
        lines.append("")
        lines.append("# HELP hub_rate_limit_rejections Rejeições por rate limit")
        lines.append("# TYPE hub_rate_limit_rejections counter")
        for hub, rejections in self._rate_limit_rejections.items():
            lines.append(
                f'hub_rate_limit_rejections{{hub="{hub}"}} {rejections}'
            )
        
        return "\n".join(lines)
    
    def reset(self):
        """Reseta todas as métricas (para testes)."""
        self._request_total.clear()
        self._request_success.clear()
        self._request_failure.clear()
        self._latencies.clear()
        self._circuit_breaker_state.clear()
        self._circuit_breaker_failures.clear()
        self._rate_limit_rejections.clear()
        self._last_success.clear()
        self._last_failure.clear()


# ============================================
# DECORATOR FOR AUTOMATIC METRICS
# ============================================

def with_metrics(hub_name: str, method_name: str = ""):
    """
    Decorator para coletar métricas automaticamente.
    
    Uso:
        @with_metrics("whatsapp", "send_text")
        async def send_text(self, ...):
            ...
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            registry = HubMetricsRegistry.get_instance()
            registry.record_request(hub_name, method_name)
            
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                latency_ms = (time.time() - start) * 1000
                registry.record_success(hub_name, method_name, latency_ms)
                return result
            except Exception as e:
                registry.record_failure(hub_name, method_name, type(e).__name__)
                raise
        
        return wrapper
    return decorator


# ============================================
# HEALTH CHECK
# ============================================

@dataclass
class HubHealth:
    """Status de saúde de um hub."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    circuit_breaker_state: str
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    success_rate: float = 0.0
    avg_latency_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class HubHealthChecker:
    """
    Verifica saúde de todos os hubs.
    """
    
    def __init__(self):
        self._hubs: Dict[str, Any] = {}
    
    def register_hub(self, name: str, hub: Any):
        """Registra um hub para monitoramento."""
        self._hubs[name] = hub
    
    async def check_hub_health(self, name: str) -> HubHealth:
        """Verifica saúde de um hub específico."""
        registry = HubMetricsRegistry.get_instance()
        metrics = registry.get_metrics()
        
        # Calcular taxa de sucesso
        total = metrics["requests"]["total"].get(name, 0)
        success = metrics["requests"]["success"].get(name, 0)
        success_rate = (success / total * 100) if total > 0 else 100.0
        
        # Estado do circuit breaker
        cb_info = metrics["circuit_breakers"].get(name, {})
        cb_state = cb_info.get("state", "unknown")
        
        # Latência média
        latency_stats = metrics["latencies"].get(name, {})
        avg_latency = latency_stats.get("avg", 0)
        
        # Determinar status
        if cb_state == "open":
            status = "unhealthy"
        elif cb_state == "half_open" or success_rate < 90:
            status = "degraded"
        else:
            status = "healthy"
        
        return HubHealth(
            name=name,
            status=status,
            circuit_breaker_state=cb_state,
            last_success=metrics["last_activity"]["success"].get(name),
            last_failure=metrics["last_activity"]["failure"].get(name),
            success_rate=success_rate,
            avg_latency_ms=avg_latency,
            details={
                "total_requests": total,
                "successful_requests": success,
                "failed_requests": metrics["requests"]["failure"].get(name, 0),
                "circuit_breaker_failures": cb_info.get("failures", 0)
            }
        )
    
    async def check_all_hubs(self) -> Dict[str, HubHealth]:
        """Verifica saúde de todos os hubs registrados."""
        results = {}
        for name in self._hubs:
            results[name] = await self.check_hub_health(name)
        return results
    
    async def get_overall_status(self) -> Dict[str, Any]:
        """Retorna status geral de todos os hubs."""
        hub_health = await self.check_all_hubs()
        
        statuses = [h.status for h in hub_health.values()]
        
        if all(s == "healthy" for s in statuses):
            overall = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall = "unhealthy"
        else:
            overall = "degraded"
        
        return {
            "status": overall,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hubs": {
                name: {
                    "status": health.status,
                    "circuit_breaker": health.circuit_breaker_state,
                    "success_rate": f"{health.success_rate:.1f}%",
                    "avg_latency_ms": f"{health.avg_latency_ms:.1f}"
                }
                for name, health in hub_health.items()
            }
        }


# Singleton
_health_checker: Optional[HubHealthChecker] = None


def get_health_checker() -> HubHealthChecker:
    """Retorna singleton do health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HubHealthChecker()
    return _health_checker


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def get_metrics_registry() -> HubMetricsRegistry:
    """Retorna o registry de métricas."""
    return HubMetricsRegistry.get_instance()


def export_prometheus_metrics() -> str:
    """Exporta métricas em formato Prometheus."""
    return HubMetricsRegistry.get_instance().to_prometheus_format()
