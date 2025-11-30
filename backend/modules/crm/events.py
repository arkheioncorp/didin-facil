"""
CRM Event Dispatcher
====================
Sistema de eventos para integração com WorkflowEngine.

Dispara eventos quando ações ocorrem no CRM, permitindo
que workflows sejam acionados automaticamente.

Uso:
    dispatcher = EventDispatcher(db_pool)
    await dispatcher.emit_lead_created(lead, user_id)
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

from .advanced_services import WorkflowEngine, WorkflowEventType
from .models import Lead, Deal, Contact

logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Dispatcher de eventos do CRM.
    
    Centraliza a emissão de eventos para o WorkflowEngine.
    """
    
    def __init__(self, db_pool):
        self.pool = db_pool
        self._engine: Optional[WorkflowEngine] = None
    
    @property
    def engine(self) -> WorkflowEngine:
        """Lazy load do WorkflowEngine."""
        if self._engine is None:
            self._engine = WorkflowEngine(self.pool)
        return self._engine
    
    # ==================== Contact Events ====================
    
    async def emit_contact_created(
        self,
        contact: Contact,
        user_id: str
    ):
        """Emite evento de contato criado."""
        await self._emit(
            event_type=WorkflowEventType.CONTACT_CREATED,
            user_id=user_id,
            entity_type="contact",
            entity_id=contact.id,
            context={
                "user_id": user_id,
                "contact_id": contact.id,
                "email": contact.email,
                "name": contact.full_name,
                "source": contact.source.value if contact.source else "manual",
                "subscribed": contact.subscribed,
            }
        )
    
    async def emit_contact_subscribed(
        self,
        contact: Contact,
        user_id: str
    ):
        """Emite evento de contato inscrito."""
        await self._emit(
            event_type=WorkflowEventType.CONTACT_SUBSCRIBED,
            user_id=user_id,
            entity_type="contact",
            entity_id=contact.id,
            context={
                "user_id": user_id,
                "contact_id": contact.id,
                "email": contact.email,
            }
        )
    
    async def emit_contact_unsubscribed(
        self,
        contact: Contact,
        user_id: str
    ):
        """Emite evento de contato desinscrito."""
        await self._emit(
            event_type=WorkflowEventType.CONTACT_UNSUBSCRIBED,
            user_id=user_id,
            entity_type="contact",
            entity_id=contact.id,
            context={
                "user_id": user_id,
                "contact_id": contact.id,
                "email": contact.email,
            }
        )
    
    # ==================== Lead Events ====================
    
    async def emit_lead_created(
        self,
        lead: Lead,
        user_id: str
    ):
        """Emite evento de lead criado."""
        await self._emit(
            event_type=WorkflowEventType.LEAD_CREATED,
            user_id=user_id,
            entity_type="lead",
            entity_id=lead.id,
            context={
                "user_id": user_id,
                "lead_id": lead.id,
                "contact_id": lead.contact_id,
                "title": lead.title,
                "source": lead.source.value if lead.source else "organic",
                "estimated_value": lead.estimated_value,
                "score": lead.score,
                "temperature": lead.temperature,
            }
        )
    
    async def emit_lead_qualified(
        self,
        lead: Lead,
        user_id: str
    ):
        """Emite evento de lead qualificado."""
        await self._emit(
            event_type=WorkflowEventType.LEAD_QUALIFIED,
            user_id=user_id,
            entity_type="lead",
            entity_id=lead.id,
            context={
                "user_id": user_id,
                "lead_id": lead.id,
                "contact_id": lead.contact_id,
                "score": lead.score,
                "temperature": lead.temperature,
                "estimated_value": lead.estimated_value,
            }
        )
    
    async def emit_lead_temperature_changed(
        self,
        lead: Lead,
        old_temperature: str,
        new_temperature: str,
        user_id: str
    ):
        """Emite evento de mudança de temperatura do lead."""
        await self._emit(
            event_type=WorkflowEventType.LEAD_TEMPERATURE_CHANGED,
            user_id=user_id,
            entity_type="lead",
            entity_id=lead.id,
            context={
                "user_id": user_id,
                "lead_id": lead.id,
                "contact_id": lead.contact_id,
                "old_temperature": old_temperature,
                "temperature": new_temperature,
                "score": lead.score,
            }
        )
    
    async def emit_lead_score_threshold(
        self,
        lead: Lead,
        threshold: int,
        user_id: str
    ):
        """Emite evento quando lead atinge threshold de score."""
        await self._emit(
            event_type=WorkflowEventType.LEAD_SCORE_THRESHOLD,
            user_id=user_id,
            entity_type="lead",
            entity_id=lead.id,
            context={
                "user_id": user_id,
                "lead_id": lead.id,
                "contact_id": lead.contact_id,
                "score": lead.score,
                "threshold": threshold,
                "temperature": lead.temperature,
            }
        )
    
    async def emit_lead_converted(
        self,
        lead: Lead,
        deal: Deal,
        user_id: str
    ):
        """Emite evento de lead convertido em deal."""
        await self._emit(
            event_type=WorkflowEventType.LEAD_CONVERTED,
            user_id=user_id,
            entity_type="lead",
            entity_id=lead.id,
            context={
                "user_id": user_id,
                "lead_id": lead.id,
                "deal_id": deal.id,
                "contact_id": lead.contact_id,
                "deal_value": deal.value,
            }
        )
    
    async def emit_lead_lost(
        self,
        lead: Lead,
        reason: Optional[str],
        user_id: str
    ):
        """Emite evento de lead perdido."""
        await self._emit(
            event_type=WorkflowEventType.LEAD_LOST,
            user_id=user_id,
            entity_type="lead",
            entity_id=lead.id,
            context={
                "user_id": user_id,
                "lead_id": lead.id,
                "contact_id": lead.contact_id,
                "reason": reason,
                "estimated_value": lead.estimated_value,
            }
        )
    
    # ==================== Deal Events ====================
    
    async def emit_deal_created(
        self,
        deal: Deal,
        user_id: str
    ):
        """Emite evento de deal criado."""
        await self._emit(
            event_type=WorkflowEventType.DEAL_CREATED,
            user_id=user_id,
            entity_type="deal",
            entity_id=deal.id,
            context={
                "user_id": user_id,
                "deal_id": deal.id,
                "contact_id": deal.contact_id,
                "lead_id": deal.lead_id,
                "title": deal.title,
                "value": deal.value,
                "pipeline_id": deal.pipeline_id,
                "stage_id": deal.stage_id,
            }
        )
    
    async def emit_deal_stage_changed(
        self,
        deal: Deal,
        old_stage_id: str,
        new_stage_id: str,
        stage_name: str,
        user_id: str
    ):
        """Emite evento de deal movido de stage."""
        await self._emit(
            event_type=WorkflowEventType.DEAL_STAGE_CHANGED,
            user_id=user_id,
            entity_type="deal",
            entity_id=deal.id,
            context={
                "user_id": user_id,
                "deal_id": deal.id,
                "contact_id": deal.contact_id,
                "old_stage_id": old_stage_id,
                "stage_id": new_stage_id,
                "stage_name": stage_name,
                "value": deal.value,
                "probability": deal.probability,
            }
        )
    
    async def emit_deal_won(
        self,
        deal: Deal,
        user_id: str
    ):
        """Emite evento de deal ganho."""
        await self._emit(
            event_type=WorkflowEventType.DEAL_WON,
            user_id=user_id,
            entity_type="deal",
            entity_id=deal.id,
            context={
                "user_id": user_id,
                "deal_id": deal.id,
                "contact_id": deal.contact_id,
                "title": deal.title,
                "value": deal.value,
            }
        )
    
    async def emit_deal_lost(
        self,
        deal: Deal,
        reason: Optional[str],
        user_id: str
    ):
        """Emite evento de deal perdido."""
        await self._emit(
            event_type=WorkflowEventType.DEAL_LOST,
            user_id=user_id,
            entity_type="deal",
            entity_id=deal.id,
            context={
                "user_id": user_id,
                "deal_id": deal.id,
                "contact_id": deal.contact_id,
                "title": deal.title,
                "value": deal.value,
                "reason": reason,
            }
        )
    
    async def emit_deal_stalled(
        self,
        deal: Deal,
        days_in_stage: int,
        user_id: str
    ):
        """Emite evento de deal parado (stalled)."""
        await self._emit(
            event_type=WorkflowEventType.DEAL_STALLED,
            user_id=user_id,
            entity_type="deal",
            entity_id=deal.id,
            context={
                "user_id": user_id,
                "deal_id": deal.id,
                "contact_id": deal.contact_id,
                "title": deal.title,
                "value": deal.value,
                "days_in_stage": days_in_stage,
                "stage_id": deal.stage_id,
            }
        )
    
    async def emit_deal_value_changed(
        self,
        deal: Deal,
        old_value: float,
        new_value: float,
        user_id: str
    ):
        """Emite evento de mudança de valor do deal."""
        await self._emit(
            event_type=WorkflowEventType.DEAL_VALUE_CHANGED,
            user_id=user_id,
            entity_type="deal",
            entity_id=deal.id,
            context={
                "user_id": user_id,
                "deal_id": deal.id,
                "contact_id": deal.contact_id,
                "old_value": old_value,
                "value": new_value,
                "change_percent": (
                    ((new_value - old_value) / old_value * 100)
                    if old_value > 0 else 0
                ),
            }
        )
    
    # ==================== Activity Events ====================
    
    async def emit_activity_logged(
        self,
        entity_type: str,
        entity_id: str,
        activity_type: str,
        user_id: str,
        contact_id: Optional[str] = None
    ):
        """Emite evento de atividade registrada."""
        await self._emit(
            event_type=WorkflowEventType.ACTIVITY_LOGGED,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            context={
                "user_id": user_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "contact_id": contact_id,
                "activity_type": activity_type,
            }
        )
    
    async def emit_inactivity_threshold(
        self,
        entity_type: str,
        entity_id: str,
        days_inactive: int,
        user_id: str
    ):
        """Emite evento de threshold de inatividade atingido."""
        await self._emit(
            event_type=WorkflowEventType.INACTIVITY_THRESHOLD,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            context={
                "user_id": user_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "days_inactive": days_inactive,
            }
        )
    
    # ==================== Internal ====================
    
    async def _emit(
        self,
        event_type: WorkflowEventType,
        user_id: str,
        entity_type: str,
        entity_id: str,
        context: Dict[str, Any]
    ):
        """
        Emite evento para o WorkflowEngine.
        
        Captura exceções para não impactar o fluxo principal.
        """
        try:
            await self.engine.trigger_event(
                event_type=event_type,
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                context=context
            )
        except Exception as e:
            # Log mas não interrompe o fluxo principal
            logger.warning(
                f"Failed to emit workflow event {event_type.value}: {e}"
            )


# Singleton para uso global (opcional)
_dispatcher: Optional[EventDispatcher] = None


def get_event_dispatcher(db_pool) -> EventDispatcher:
    """Retorna instância do EventDispatcher."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = EventDispatcher(db_pool)
    return _dispatcher


# Alias para compatibilidade
crm_dispatcher = get_event_dispatcher


class CRMEventType:
    """Tipos de eventos do CRM."""
    CONTACT_CREATED = "contact.created"
    CONTACT_UPDATED = "contact.updated"
    LEAD_CREATED = "lead.created"
    LEAD_UPDATED = "lead.updated"
    LEAD_CONVERTED = "lead.converted"
    DEAL_CREATED = "deal.created"
    DEAL_UPDATED = "deal.updated"
    DEAL_WON = "deal.won"
    DEAL_LOST = "deal.lost"
    DEAL_STAGE_CHANGED = "deal.stage_changed"
    ACTIVITY_CREATED = "activity.created"
    ACTIVITY_COMPLETED = "activity.completed"


class CRMEvent:
    """Representação de um evento do CRM."""

    def __init__(
        self,
        event_type: str,
        entity_id: str,
        entity_type: str,
        user_id: str,
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.event_type = event_type
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.user_id = user_id
        self.data = data or {}
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "user_id": self.user_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


# Alias para compatibilidade
CRMEventDispatcher = EventDispatcher
