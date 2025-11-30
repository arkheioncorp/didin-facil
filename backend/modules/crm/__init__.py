"""
CRM Module - Customer Relationship Management
==============================================
Sistema de gestão de relacionamento com clientes.

Features:
- Contatos e Leads
- Pipeline de vendas
- Deals (Negócios)
- Automações e triggers
- Segmentação
- Histórico de interações
- Score Decay (degradação temporal)
- Deal Risk Detection
- Next Best Action recommendations
"""

from .models import (
    Contact,
    ContactStatus,
    Lead,
    LeadSource,
    LeadStatus,
    Deal,
    DealStage,
    DealStatus,
    Pipeline,
    PipelineStage,
    Activity,
    ActivityType,
    Tag,
    Segment,
    SegmentCondition,
)
from .services import (
    CRMService,
    ContactService,
    LeadService,
    DealService,
    PipelineService,
    SegmentationService,
)
from .repository import (
    ContactRepository,
    LeadRepository,
    DealRepository,
    PipelineRepository,
)
from .advanced_services import (
    # Enums
    RiskLevel,
    ActionPriority,
    WorkflowEventType,
    WorkflowActionType,
    # Configs
    ScoreDecayConfig,
    # Dataclasses
    RiskSignal,
    RiskAssessment,
    NextBestAction,
    ScoreDecayResult,
    WorkflowCondition,
    WorkflowAction,
    Workflow,
    WorkflowExecutionLog,
    # Services
    ScoreDecayService,
    DealRiskDetectionService,
    NextBestActionEngine,
    WorkflowEngine,
    WorkflowTemplates,
)
from .events import (
    CRMEventType,
    EventDispatcher,
    get_event_dispatcher,
    crm_dispatcher,
)

__all__ = [
    # Models
    "Contact",
    "ContactStatus",
    "Lead",
    "LeadSource",
    "LeadStatus",
    "Deal",
    "DealStage",
    "DealStatus",
    "Pipeline",
    "PipelineStage",
    "Activity",
    "ActivityType",
    "Tag",
    "Segment",
    "SegmentCondition",
    # Services
    "CRMService",
    "ContactService",
    "LeadService",
    "DealService",
    "PipelineService",
    "SegmentationService",
    # Advanced Services - Enums
    "RiskLevel",
    "ActionPriority",
    "WorkflowEventType",
    "WorkflowActionType",
    # Advanced Services - Configs/Dataclasses
    "ScoreDecayConfig",
    "RiskSignal",
    "RiskAssessment",
    "NextBestAction",
    "ScoreDecayResult",
    "WorkflowCondition",
    "WorkflowAction",
    "Workflow",
    "WorkflowExecutionLog",
    # Advanced Services - Services
    "ScoreDecayService",
    "DealRiskDetectionService",
    "NextBestActionEngine",
    "WorkflowEngine",
    "WorkflowTemplates",
    # Events
    "CRMEventType",
    "EventDispatcher",
    "get_event_dispatcher",
    "crm_dispatcher",
    # Repositories
    "ContactRepository",
    "LeadRepository",
    "DealRepository",
    "PipelineRepository",
]
