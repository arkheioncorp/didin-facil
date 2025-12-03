"""
Automation Dashboard API Routes
===============================
Endpoints para dashboard de métricas das automações.

Fornece:
- Métricas em tempo real
- Histórico de execuções
- Estatísticas por tipo de automação
- Health checks
- Gerenciamento de agendamentos
"""

from datetime import datetime, timezone, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from api.middleware.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

# Imports do módulo de automação
try:
    from modules.automation import (AutomationPriority, AutomationType,
                                    ScheduleStatus, ScheduleType,
                                    get_orchestrator, get_scheduler)
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False


router = APIRouter(tags=["Automation Dashboard"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class TimeRange(str, Enum):
    """Intervalo de tempo para métricas."""
    HOUR = "1h"
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"


class DashboardOverview(BaseModel):
    """Visão geral do dashboard."""
    total_automations: int = Field(..., description="Total de automações configuradas")
    active_automations: int = Field(..., description="Automações ativas")
    pending_events: int = Field(..., description="Eventos pendentes na fila")
    processing_events: int = Field(..., description="Eventos em processamento")
    completed_today: int = Field(..., description="Eventos completados hoje")
    failed_today: int = Field(..., description="Eventos falhados hoje")
    success_rate: float = Field(..., description="Taxa de sucesso (%)")
    avg_processing_time_ms: float = Field(..., description="Tempo médio de processamento")


class AutomationMetrics(BaseModel):
    """Métricas de uma automação específica."""
    automation_type: str
    display_name: str
    enabled: bool
    total_triggers: int
    successful: int
    failed: int
    pending: int
    success_rate: float
    avg_delay_ms: float
    last_triggered: Optional[datetime]
    channels: List[str]


class ScheduledEventResponse(BaseModel):
    """Resposta de evento agendado."""
    id: str
    automation_type: str
    schedule_type: str
    user_id: str
    status: str
    scheduled_for: datetime
    priority: str
    retry_count: int
    created_at: datetime
    processed_at: Optional[datetime]
    error_message: Optional[str]


class QueueDepthResponse(BaseModel):
    """Profundidade da fila por prioridade."""
    high: int
    normal: int
    low: int
    total: int


class TimeSeriesDataPoint(BaseModel):
    """Ponto de dados em série temporal."""
    timestamp: datetime
    value: float


class ScheduleEventRequest(BaseModel):
    """Request para agendar evento."""
    automation_type: str
    user_id: str
    data: Dict[str, Any] = {}
    delay_minutes: Optional[int] = None
    scheduled_for: Optional[datetime] = None
    priority: str = "normal"


# ============================================
# HEALTH & STATUS
# ============================================

@router.get("/health")
async def dashboard_health():
    """
    Health check do sistema de automações.
    """
    health = {
        "status": "healthy",
        "automation_available": AUTOMATION_AVAILABLE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "orchestrator": False,
            "scheduler": False,
            "n8n_connection": False,
        }
    }
    
    if AUTOMATION_AVAILABLE:
        try:
            orchestrator = get_orchestrator()
            health["components"]["orchestrator"] = True
            health["components"]["n8n_connection"] = orchestrator.is_configured
            
            # Verificar scheduler
            try:
                scheduler = get_scheduler(orchestrator)
                health["components"]["scheduler"] = True
            except ValueError:
                pass
                
        except Exception as e:
            health["status"] = "degraded"
            health["error"] = str(e)
    else:
        health["status"] = "unavailable"
    
    return health


# ============================================
# OVERVIEW & STATS
# ============================================

@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    current_user=Depends(get_current_user)
):
    """
    Retorna visão geral do dashboard de automações.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)
        stats = scheduler.get_stats()
        
        # Calcular métricas
        total_processed = stats.total_completed + stats.total_failed
        success_rate = (
            (stats.total_completed / total_processed * 100)
            if total_processed > 0 else 100.0
        )
        
        return DashboardOverview(
            total_automations=len(orchestrator.automations),
            active_automations=sum(
                1 for a in orchestrator.automations.values()
                if a.enabled
            ),
            pending_events=stats.total_pending,
            processing_events=stats.total_processing,
            completed_today=stats.total_completed,
            failed_today=stats.total_failed,
            success_rate=round(success_rate, 2),
            avg_processing_time_ms=round(stats.avg_processing_time_ms, 2),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_all_metrics(
    time_range: TimeRange = Query(
        TimeRange.DAY,
        description="Intervalo de tempo"
    ),
    current_user=Depends(get_current_user)
):
    """
    Retorna métricas de todas as automações.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)
        stats = scheduler.get_stats()
        
        metrics = []
        
        for auto_type, config in orchestrator.automations.items():
            pending_count = stats.events_per_type.get(auto_type.value, 0)
            
            metrics.append(AutomationMetrics(
                automation_type=auto_type.value,
                display_name=config.name,
                enabled=config.enabled,
                total_triggers=0,  # TODO: Implementar contagem real
                successful=0,
                failed=0,
                pending=pending_count,
                success_rate=100.0,
                avg_delay_ms=0.0,
                last_triggered=None,
                channels=[c.value for c in config.channels],
            ))
        
        return {
            "metrics": metrics,
            "time_range": time_range.value,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{automation_type}")
async def get_automation_metrics(
    automation_type: str,
    time_range: TimeRange = Query(TimeRange.DAY),
    current_user=Depends(get_current_user)
):
    """
    Retorna métricas detalhadas de uma automação específica.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        auto_type = AutomationType(automation_type)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Tipo de automação não encontrado: {automation_type}"
        )
    
    try:
        orchestrator = get_orchestrator()
        config = orchestrator.automations.get(auto_type)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuração não encontrada: {automation_type}"
            )
        
        scheduler = get_scheduler(orchestrator)
        pending = scheduler.get_pending_events(automation_type=auto_type)
        
        return {
            "automation_type": auto_type.value,
            "display_name": config.name,
            "enabled": config.enabled,
            "channels": [c.value for c in config.channels],
            "webhook_url": config.webhook_url,
            "rate_limit": {
                "max_per_day": config.max_triggers_per_day,
                "time_window_minutes": config.time_window_minutes,
            },
            "retry": {
                "enabled": config.retry_on_failure,
                "max_attempts": config.max_retries,
            },
            "pending_events": len(pending),
            "time_range": time_range.value,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# QUEUE MANAGEMENT
# ============================================

@router.get("/queue/depth", response_model=QueueDepthResponse)
async def get_queue_depth(
    current_user=Depends(get_current_user)
):
    """
    Retorna profundidade da fila por prioridade.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)
        depths = scheduler.get_queue_depth()
        
        return QueueDepthResponse(
            high=depths["high"],
            normal=depths["normal"],
            low=depths["low"],
            total=sum(depths.values()),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/events")
async def list_queued_events(
    status: Optional[str] = Query(None, description="Filtrar por status"),
    automation_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    user_id: Optional[str] = Query(None, description="Filtrar por usuário"),
    limit: int = Query(50, ge=1, le=200),
    current_user=Depends(get_current_user)
):
    """
    Lista eventos na fila de automação.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)
        
        # Converter tipo de automação se fornecido
        auto_type = None
        if automation_type:
            try:
                auto_type = AutomationType(automation_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tipo inválido: {automation_type}"
                )
        
        events = scheduler.get_pending_events(
            user_id=user_id,
            automation_type=auto_type,
        )
        
        # Limitar resultados
        events = events[:limit]
        
        return {
            "events": [
                ScheduledEventResponse(
                    id=e.id,
                    automation_type=e.automation_type.value,
                    schedule_type=e.schedule_type.value,
                    user_id=e.user_id,
                    status=e.status.value,
                    scheduled_for=e.scheduled_for,
                    priority=e.priority.value,
                    retry_count=e.retry_count,
                    created_at=e.created_at,
                    processed_at=e.processed_at,
                    error_message=e.error_message,
                )
                for e in events
            ],
            "total": len(events),
            "limit": limit,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/events/{event_id}")
async def get_event_details(
    event_id: str,
    current_user=Depends(get_current_user)
):
    """
    Retorna detalhes de um evento específico.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)
        event = scheduler.get_event(event_id)
        
        if not event:
            raise HTTPException(
                status_code=404,
                detail=f"Evento não encontrado: {event_id}"
            )
        
        return {
            "event": ScheduledEventResponse(
                id=event.id,
                automation_type=event.automation_type.value,
                schedule_type=event.schedule_type.value,
                user_id=event.user_id,
                status=event.status.value,
                scheduled_for=event.scheduled_for,
                priority=event.priority.value,
                retry_count=event.retry_count,
                created_at=event.created_at,
                processed_at=event.processed_at,
                error_message=event.error_message,
            ),
            "data": event.data,
            "metadata": event.metadata,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SCHEDULING
# ============================================

@router.post("/schedule")
async def schedule_event(
    request: ScheduleEventRequest,
    current_user=Depends(get_current_user)
):
    """
    Agenda um novo evento de automação.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        auto_type = AutomationType(request.automation_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo inválido: {request.automation_type}"
        )
    
    try:
        priority = AutomationPriority(request.priority)
    except ValueError:
        priority = AutomationPriority.NORMAL
    
    try:
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)
        
        event = await scheduler.schedule(
            automation_type=auto_type,
            user_id=request.user_id,
            data=request.data,
            delay_minutes=request.delay_minutes,
            scheduled_for=request.scheduled_for,
            priority=priority,
        )
        
        return {
            "success": True,
            "event_id": event.id,
            "scheduled_for": event.scheduled_for.isoformat(),
            "message": "Evento agendado com sucesso",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/schedule/{event_id}")
async def cancel_scheduled_event(
    event_id: str,
    current_user=Depends(get_current_user)
):
    """
    Cancela um evento agendado.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)
        
        success = await scheduler.cancel(event_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Evento não encontrado ou já processado: {event_id}"
            )
        
        return {
            "success": True,
            "message": "Evento cancelado com sucesso",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/{event_id}/process")
async def process_event_now(
    event_id: str,
    current_user=Depends(get_current_user)
):
    """
    Processa um evento imediatamente (ignora agendamento).
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)
        
        result = await scheduler.process_now(event_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Falha ao processar evento")
            )
        
        return {
            "success": True,
            "status": result.get("status"),
            "message": "Evento processado",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# AUTOMATION MANAGEMENT
# ============================================

@router.get("/automations")
async def list_automations(
    enabled_only: bool = Query(False),
    current_user=Depends(get_current_user)
):
    """
    Lista todas as automações configuradas.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        orchestrator = get_orchestrator()
        
        automations = []
        for auto_type, config in orchestrator.automations.items():
            if enabled_only and not config.enabled:
                continue
            
            automations.append({
                "type": auto_type.value,
                "name": config.name,
                "enabled": config.enabled,
                "channels": [c.value for c in config.channels],
                "webhook_url": config.webhook_url,
                "rate_limit": {
                    "max_per_day": config.max_triggers_per_day,
                    "time_window_minutes": config.time_window_minutes,
                },
                "retry": {
                    "enabled": config.retry_on_failure,
                    "max_attempts": config.max_retries,
                },
            })
        
        return {
            "automations": automations,
            "total": len(automations),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/automations/{automation_type}/toggle")
async def toggle_automation(
    automation_type: str,
    enabled: bool = Query(..., description="Habilitar ou desabilitar"),
    current_user=Depends(get_current_user)
):
    """
    Habilita ou desabilita uma automação.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        auto_type = AutomationType(automation_type)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Tipo não encontrado: {automation_type}"
        )
    
    try:
        orchestrator = get_orchestrator()
        
        if auto_type not in orchestrator.automations:
            raise HTTPException(
                status_code=404,
                detail=f"Automação não configurada: {automation_type}"
            )
        
        orchestrator.automations[auto_type].enabled = enabled
        
        return {
            "success": True,
            "automation_type": automation_type,
            "enabled": enabled,
            "message": f"Automação {'habilitada' if enabled else 'desabilitada'}",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# STATISTICS & REPORTS
# ============================================

@router.get("/stats/summary")
async def get_stats_summary(
    current_user=Depends(get_current_user)
):
    """
    Retorna resumo estatístico das automações.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        orchestrator = get_orchestrator()
        scheduler = get_scheduler(orchestrator)
        stats = scheduler.get_stats()
        
        return {
            "queue": {
                "pending": stats.total_pending,
                "processing": stats.total_processing,
                "completed": stats.total_completed,
                "failed": stats.total_failed,
            },
            "performance": {
                "avg_processing_time_ms": round(
                    stats.avg_processing_time_ms, 2
                ),
                "success_rate": round(
                    (stats.total_completed / 
                     (stats.total_completed + stats.total_failed) * 100)
                    if (stats.total_completed + stats.total_failed) > 0
                    else 100.0,
                    2
                ),
            },
            "by_type": stats.events_per_type,
            "last_run": (
                stats.last_run.isoformat()
                if stats.last_run else None
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/types")
async def get_stats_by_type(
    current_user=Depends(get_current_user)
):
    """
    Retorna estatísticas agrupadas por tipo de automação.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo de automação não disponível"
        )
    
    try:
        orchestrator = get_orchestrator()
        
        # Coletar estatísticas por tipo
        by_type = {}
        for auto_type in AutomationType:
            by_type[auto_type.value] = {
                "configured": auto_type in orchestrator.automations,
                "enabled": (
                    orchestrator.automations[auto_type].enabled
                    if auto_type in orchestrator.automations
                    else False
                ),
                "triggers_today": 0,  # TODO: Implementar contagem real
                "success_rate": 100.0,
            }
        
        return {
            "by_type": by_type,
            "total_types": len(AutomationType),
            "configured_types": len(orchestrator.automations),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
