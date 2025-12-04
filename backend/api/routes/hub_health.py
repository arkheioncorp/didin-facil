"""
Hub Health & Metrics API Routes
================================
Endpoints para monitoramento de saúde e métricas dos Integration Hubs.

Endpoints:
- GET /hub/health - Status de saúde geral
- GET /hub/health/{hub_name} - Status de um hub específico
- GET /hub/metrics - Métricas em formato JSON
- GET /hub/metrics/prometheus - Métricas em formato Prometheus

Autor: TikTrend Finder
Versão: 1.0.0
"""

from fastapi import APIRouter, Response
from typing import Dict, Any

from integrations.metrics import (
    get_metrics_registry,
    get_health_checker,
    export_prometheus_metrics,
    HubHealthChecker
)
from integrations import (
    get_whatsapp_hub,
    get_instagram_hub,
    get_tiktok_hub
)

router = APIRouter(prefix="/hub", tags=["Hub Monitoring"])


# ============================================
# INITIALIZATION
# ============================================

def _register_hubs():
    """Registra hubs no health checker."""
    checker = get_health_checker()
    
    # Registrar hubs disponíveis
    try:
        checker.register_hub("whatsapp", get_whatsapp_hub())
    except Exception:
        pass
    
    try:
        checker.register_hub("instagram", get_instagram_hub())
    except Exception:
        pass
    
    try:
        checker.register_hub("tiktok", get_tiktok_hub())
    except Exception:
        pass


# Registrar hubs na inicialização
_register_hubs()


# ============================================
# HEALTH ENDPOINTS
# ============================================

@router.get("/health")
async def get_overall_health() -> Dict[str, Any]:
    """
    Retorna status de saúde geral de todos os hubs.
    
    Response:
    - status: "healthy" | "degraded" | "unhealthy"
    - timestamp: ISO timestamp
    - hubs: Status individual de cada hub
    """
    checker = get_health_checker()
    return await checker.get_overall_status()


@router.get("/health/{hub_name}")
async def get_hub_health(hub_name: str) -> Dict[str, Any]:
    """
    Retorna status de saúde de um hub específico.
    
    Args:
        hub_name: Nome do hub (whatsapp, instagram, tiktok)
    """
    checker = get_health_checker()
    health = await checker.check_hub_health(hub_name)
    
    return {
        "name": health.name,
        "status": health.status,
        "circuit_breaker_state": health.circuit_breaker_state,
        "success_rate": f"{health.success_rate:.1f}%",
        "avg_latency_ms": f"{health.avg_latency_ms:.1f}",
        "last_success": health.last_success,
        "last_failure": health.last_failure,
        "details": health.details
    }


# ============================================
# METRICS ENDPOINTS
# ============================================

@router.get("/metrics")
async def get_metrics_json() -> Dict[str, Any]:
    """
    Retorna métricas em formato JSON.
    
    Inclui:
    - Contadores de requisições
    - Estatísticas de latência
    - Estado dos circuit breakers
    - Rejeições de rate limiting
    """
    registry = get_metrics_registry()
    return registry.get_metrics()


@router.get("/metrics/prometheus")
async def get_metrics_prometheus() -> Response:
    """
    Retorna métricas em formato Prometheus text.
    
    Compatível com scraping do Prometheus.
    Content-Type: text/plain
    """
    metrics_text = export_prometheus_metrics()
    return Response(
        content=metrics_text,
        media_type="text/plain; charset=utf-8"
    )


# ============================================
# CIRCUIT BREAKER MANAGEMENT
# ============================================

@router.post("/circuit-breaker/{hub_name}/reset")
async def reset_circuit_breaker(hub_name: str) -> Dict[str, Any]:
    """
    Reseta o circuit breaker de um hub.
    
    Use com cuidado - apenas quando souber que o serviço externo
    está funcionando novamente.
    """
    hub = None
    
    if hub_name == "whatsapp":
        hub = get_whatsapp_hub()
    elif hub_name == "instagram":
        hub = get_instagram_hub()
    elif hub_name == "tiktok":
        hub = get_tiktok_hub()
    else:
        return {"error": f"Hub '{hub_name}' não encontrado"}
    
    if hasattr(hub, "_circuit_breaker"):
        # Resetar estado (se o CircuitBreaker tiver método reset)
        cb = hub._circuit_breaker
        if hasattr(cb, "reset"):
            await cb.reset()
        
        return {
            "hub": hub_name,
            "message": "Circuit breaker resetado",
            "new_state": cb.state.value if hasattr(cb, "state") else "unknown"
        }
    
    return {"error": f"Hub '{hub_name}' não tem circuit breaker"}


@router.get("/circuit-breaker/status")
async def get_all_circuit_breaker_status() -> Dict[str, Any]:
    """
    Retorna status de todos os circuit breakers.
    """
    status = {}
    
    for hub_name, hub_getter in [
        ("whatsapp", get_whatsapp_hub),
        ("instagram", get_instagram_hub),
        ("tiktok", get_tiktok_hub)
    ]:
        try:
            hub = hub_getter()
            if hasattr(hub, "_circuit_breaker"):
                cb = hub._circuit_breaker
                status[hub_name] = {
                    "state": cb.state.value if hasattr(cb, "state") else "unknown",
                    "failure_count": cb.stats.failure_count if hasattr(cb, "stats") else 0,
                    "success_count": cb.stats.success_count if hasattr(cb, "stats") else 0,
                }
            else:
                status[hub_name] = {"error": "No circuit breaker"}
        except Exception as e:
            status[hub_name] = {"error": str(e)}
    
    return status
