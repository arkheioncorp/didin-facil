"""
CRM Advanced API Router
=======================
Endpoints para serviços avançados do CRM:
- Risk Detection (detecção de deals em risco)
- Next Best Action (recomendação de ações)
- Workflows (automações)
- Score Decay (manutenção)
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import logging

from shared.postgres import get_db
from modules.crm import (
    # Advanced Services
    DealRiskDetectionService,
    NextBestActionEngine,
    WorkflowEngine,
    WorkflowTemplates,
    ScoreDecayService,
    ScoreDecayConfig,
    # Enums
    RiskLevel,
    WorkflowEventType,
    WorkflowActionType,
    # Dataclasses
    Workflow,
    WorkflowCondition,
    WorkflowAction,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crm/advanced", tags=["CRM Advanced"])


# ==================== Schemas ====================

class RiskAssessmentResponse(BaseModel):
    deal_id: str
    risk_level: str
    risk_score: int
    signals: List[dict]
    recommendations: List[str]
    assessed_at: str


class NextActionResponse(BaseModel):
    action_type: str
    action_label: str
    reason: str
    priority: str
    suggested_timing: str
    entity_type: str
    entity_id: str
    metadata: dict = {}


class WorkflowConditionSchema(BaseModel):
    field: str
    operator: str
    value: str | int | float | bool | list


class WorkflowActionSchema(BaseModel):
    action_type: str
    config: dict = {}


class WorkflowCreateRequest(BaseModel):
    name: str
    description: str = ""
    event_type: str
    conditions: List[WorkflowConditionSchema] = []
    actions: List[WorkflowActionSchema]
    is_active: bool = True
    run_once_per_entity: bool = False


class ScoreDecayConfigRequest(BaseModel):
    decay_rate_per_week: float = Field(default=5.0, ge=0, le=50)
    max_decay_percent: float = Field(default=70.0, ge=0, le=100)
    grace_period_days: int = Field(default=7, ge=0, le=30)
    minimum_score: int = Field(default=5, ge=0, le=100)


# ==================== Risk Detection ====================

@router.get("/deals/{deal_id}/risk")
async def assess_deal_risk(deal_id: str, user_id: str = Query(...)):
    """
    Avalia risco de um deal específico.
    
    Retorna sinais de risco identificados e recomendações de ação.
    """
    try:
        pool = await get_db()
        service = DealRiskDetectionService(pool)
        
        assessment = await service.assess_deal_risk(deal_id, user_id)
        
        return assessment.to_dict()
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error assessing deal risk: {e}")
        raise HTTPException(status_code=500, detail="Erro ao avaliar risco")


@router.get("/deals/at-risk")
async def get_deals_at_risk(
    user_id: str = Query(...),
    pipeline_id: Optional[str] = None,
    min_risk_level: str = Query(default="medium")
):
    """
    Lista todos os deals em risco.
    
    Filtra por nível mínimo de risco: low, medium, high, critical
    """
    try:
        pool = await get_db()
        service = DealRiskDetectionService(pool)
        
        result = await service.assess_all_deals(user_id, pipeline_id)
        
        # Filtra por nível mínimo
        risk_order = ["low", "medium", "high", "critical"]
        min_idx = risk_order.index(min_risk_level) if min_risk_level in risk_order else 1
        
        filtered_results = {
            "critical": result.get("critical", []),
            "high": result.get("high", []) if min_idx <= 2 else [],
            "medium": result.get("medium", []) if min_idx <= 1 else [],
            "low": result.get("low", []) if min_idx == 0 else [],
            "summary": result.get("summary", {})
        }
        
        return filtered_results
        
    except Exception as e:
        logger.error(f"Error getting deals at risk: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar deals em risco")


# ==================== Next Best Action ====================

@router.get("/leads/{lead_id}/next-action")
async def get_next_action_for_lead(lead_id: str, user_id: str = Query(...)):
    """
    Recomenda próxima melhor ação para um lead.
    
    Considera estado atual, temperatura, histórico de atividades.
    """
    try:
        pool = await get_db()
        engine = NextBestActionEngine(pool)
        
        action = await engine.get_next_action_for_lead(lead_id, user_id)
        
        return action.to_dict()
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting next action for lead: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter recomendação")


@router.get("/deals/{deal_id}/next-action")
async def get_next_action_for_deal(deal_id: str, user_id: str = Query(...)):
    """
    Recomenda próxima melhor ação para um deal.
    
    Considera stage atual, tempo no stage, probabilidade, atividades.
    """
    try:
        pool = await get_db()
        engine = NextBestActionEngine(pool)
        
        action = await engine.get_next_action_for_deal(deal_id, user_id)
        
        return action.to_dict()
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting next action for deal: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter recomendação")


@router.get("/actions/prioritized")
async def get_prioritized_actions(
    user_id: str = Query(...),
    limit: int = Query(default=10, le=50)
):
    """
    Lista ações priorizadas para todos os leads e deals.
    
    Retorna as ações mais urgentes que o vendedor deve tomar.
    """
    try:
        pool = await get_db()
        engine = NextBestActionEngine(pool)
        
        actions = await engine.get_prioritized_actions(user_id, limit)
        
        return {
            "actions": [a.to_dict() for a in actions],
            "total": len(actions)
        }
        
    except Exception as e:
        logger.error(f"Error getting prioritized actions: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter ações")


# ==================== Workflows ====================

@router.post("/workflows")
async def create_workflow(request: WorkflowCreateRequest, user_id: str = Query(...)):
    """
    Cria um novo workflow de automação.
    
    Workflows são disparados quando eventos específicos ocorrem.
    """
    try:
        # Valida event_type
        try:
            event_type = WorkflowEventType(request.event_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Event type inválido. Valores: {[e.value for e in WorkflowEventType]}"
            )
        
        # Converte conditions
        conditions = [
            WorkflowCondition(
                field=c.field,
                operator=c.operator,
                value=c.value
            )
            for c in request.conditions
        ]
        
        # Converte actions
        actions = []
        for a in request.actions:
            try:
                action_type = WorkflowActionType(a.action_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Action type inválido: {a.action_type}"
                )
            actions.append(WorkflowAction(
                action_type=action_type,
                config=a.config
            ))
        
        # Cria workflow
        workflow = Workflow(
            user_id=user_id,
            name=request.name,
            description=request.description,
            event_type=event_type,
            conditions=conditions,
            actions=actions,
            is_active=request.is_active,
            run_once_per_entity=request.run_once_per_entity
        )
        
        # Registra no engine (em produção, persistir no banco)
        pool = await get_db()
        engine = WorkflowEngine(pool)
        engine.register_workflow(workflow)
        
        return workflow.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar workflow")


@router.get("/workflows/templates")
async def list_workflow_templates():
    """
    Lista templates de workflows disponíveis.
    
    Templates são configurações prontas para casos comuns.
    """
    templates = [
        {
            "id": "hot_lead_notification",
            "name": "Notificação Lead Hot",
            "description": "Notifica quando um lead fica hot",
            "event_type": "lead_temperature_changed",
            "preview_conditions": [{"field": "temperature", "operator": "equals", "value": "hot"}],
            "preview_actions": ["notify_user", "add_tag"]
        },
        {
            "id": "deal_won_celebration",
            "name": "Deal Ganho",
            "description": "Ações quando deal é ganho",
            "event_type": "deal_won",
            "preview_conditions": [],
            "preview_actions": ["notify_user", "add_tag", "log_activity"]
        },
        {
            "id": "stalled_deal_alert",
            "name": "Alerta Deal Parado",
            "description": "Alerta quando deal está parado muito tempo",
            "event_type": "deal_stalled",
            "preview_conditions": [{"field": "days_in_stage", "operator": "greater_than", "value": 14}],
            "preview_actions": ["notify_user", "add_tag"]
        },
        {
            "id": "high_value_lead",
            "name": "Lead Alto Valor",
            "description": "Alerta para leads de alto valor",
            "event_type": "lead_created",
            "preview_conditions": [{"field": "estimated_value", "operator": "greater_than", "value": 10000}],
            "preview_actions": ["notify_user", "add_tag"]
        }
    ]
    
    return {"templates": templates}


@router.post("/workflows/templates/{template_id}/apply")
async def apply_workflow_template(
    template_id: str,
    user_id: str = Query(...),
    threshold: Optional[float] = Query(default=10000)
):
    """
    Aplica um template de workflow para o usuário.
    """
    try:
        pool = await get_db()
        engine = WorkflowEngine(pool)
        
        # Cria workflow baseado no template
        if template_id == "hot_lead_notification":
            workflow = WorkflowTemplates.hot_lead_notification(user_id)
        elif template_id == "deal_won_celebration":
            workflow = WorkflowTemplates.deal_won_celebration(user_id)
        elif template_id == "stalled_deal_alert":
            workflow = WorkflowTemplates.stalled_deal_alert(user_id)
        elif template_id == "high_value_lead":
            workflow = WorkflowTemplates.high_value_lead(user_id, threshold)
        else:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        engine.register_workflow(workflow)
        
        return workflow.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying template: {e}")
        raise HTTPException(status_code=500, detail="Erro ao aplicar template")


@router.get("/workflows/event-types")
async def list_event_types():
    """Lista todos os tipos de eventos disponíveis para workflows."""
    return {
        "event_types": [
            {"value": e.value, "name": e.name.replace("_", " ").title()}
            for e in WorkflowEventType
        ]
    }


@router.get("/workflows/action-types")
async def list_action_types():
    """Lista todos os tipos de ações disponíveis para workflows."""
    return {
        "action_types": [
            {"value": a.value, "name": a.name.replace("_", " ").title()}
            for a in WorkflowActionType
        ]
    }


# ==================== Score Decay (Admin/Maintenance) ====================

@router.post("/maintenance/score-decay")
async def run_score_decay(
    user_id: str = Query(...),
    config: Optional[ScoreDecayConfigRequest] = None
):
    """
    Executa decay de scores para leads inativos.
    
    Este endpoint é para uso administrativo/manutenção.
    Em produção, deve ser executado via job scheduler.
    """
    try:
        pool = await get_db()
        
        # Configura decay
        decay_config = None
        if config:
            decay_config = ScoreDecayConfig(
                decay_rate_per_week=config.decay_rate_per_week,
                max_decay_percent=config.max_decay_percent,
                grace_period_days=config.grace_period_days,
                minimum_score=config.minimum_score
            )
        
        service = ScoreDecayService(pool, decay_config)
        result = await service.run_decay_batch(user_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error running score decay: {e}")
        raise HTTPException(status_code=500, detail="Erro ao executar decay")


# ==================== Dashboard Summary ====================

@router.get("/dashboard")
async def get_advanced_dashboard(user_id: str = Query(...)):
    """
    Dashboard unificado com todas as métricas avançadas do CRM.
    
    Inclui:
    - Deals em risco
    - Ações prioritárias
    - Métricas de workflows
    """
    try:
        pool = await get_db()
        
        # Risk Detection
        risk_service = DealRiskDetectionService(pool)
        risk_result = await risk_service.assess_all_deals(user_id)
        
        # Next Best Actions
        nba_engine = NextBestActionEngine(pool)
        actions = await nba_engine.get_prioritized_actions(user_id, limit=5)
        
        return {
            "risk_summary": {
                "total_assessed": risk_result["summary"]["total_assessed"],
                "at_risk": risk_result["summary"]["at_risk"],
                "value_at_risk": risk_result["summary"]["total_value_at_risk"],
                "critical_count": len(risk_result.get("critical", [])),
                "high_count": len(risk_result.get("high", []))
            },
            "top_risks": [
                {
                    "deal_id": item["deal"]["id"],
                    "title": item["deal"]["title"],
                    "value": item["deal"]["value"],
                    "risk_level": item["assessment"]["risk_level"],
                    "risk_score": item["assessment"]["risk_score"]
                }
                for item in (
                    risk_result.get("critical", [])[:3] + 
                    risk_result.get("high", [])[:2]
                )
            ],
            "priority_actions": [a.to_dict() for a in actions],
            "action_breakdown": {
                "urgent": len([a for a in actions if a.priority.value == "urgent"]),
                "high": len([a for a in actions if a.priority.value == "high"]),
                "medium": len([a for a in actions if a.priority.value == "medium"]),
                "low": len([a for a in actions if a.priority.value == "low"])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting advanced dashboard: {e}")
        raise HTTPException(status_code=500, detail="Erro ao carregar dashboard")
