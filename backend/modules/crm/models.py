"""
CRM Models
==========
Modelos de dados para o sistema CRM.

Entidades:
- Contact: Contato de cliente
- Lead: Lead qualificado
- Deal: Negócio/Oportunidade
- Pipeline: Funil de vendas
- Activity: Histórico de atividades
- Tag: Marcadores
- Segment: Segmentação dinâmica
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


# ==================== ENUMS ====================

class ContactStatus(str, Enum):
    """Status do contato."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    BLOCKED = "blocked"


class LeadSource(str, Enum):
    """Origem do lead."""
    ORGANIC = "organic"
    PAID_ADS = "paid_ads"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    WEBSITE = "website"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    CHATBOT = "chatbot"
    MANUAL = "manual"
    IMPORT = "import"
    API = "api"


class LeadStatus(str, Enum):
    """Status do lead."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    NURTURING = "nurturing"


class DealStage(str, Enum):
    """Estágio padrão do deal."""
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    WON = "won"
    LOST = "lost"


class DealStatus(str, Enum):
    """Status do deal."""
    OPEN = "open"
    WON = "won"
    LOST = "lost"
    STALE = "stale"
    ON_HOLD = "on_hold"


class ActivityType(str, Enum):
    """Tipo de atividade."""
    NOTE = "note"
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    TASK = "task"
    WHATSAPP = "whatsapp"
    INSTAGRAM_DM = "instagram_dm"
    PROPOSAL_SENT = "proposal_sent"
    DEAL_CREATED = "deal_created"
    DEAL_UPDATED = "deal_updated"
    DEAL_WON = "deal_won"
    DEAL_LOST = "deal_lost"
    STAGE_CHANGED = "stage_changed"
    TAG_ADDED = "tag_added"
    TAG_REMOVED = "tag_removed"
    AUTOMATION = "automation"
    SYSTEM = "system"


class SegmentOperator(str, Enum):
    """Operadores para condições de segmento."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    IN = "in"
    NOT_IN = "not_in"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    BEFORE = "before"
    AFTER = "after"
    BETWEEN = "between"


# ==================== DATACLASSES ====================

@dataclass
class Tag:
    """Tag para categorização."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    color: str = "#3B82F6"  # Blue default
    description: Optional[str] = None
    user_id: str = ""
    created_at: datetime = field(default_factory=_utc_now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "description": self.description,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tag":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            color=data.get("color", "#3B82F6"),
            description=data.get("description"),
            user_id=data.get("user_id", ""),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data else datetime.now(timezone.utc),
        )


@dataclass
class CustomField:
    """Campo customizado."""
    key: str
    value: Any
    field_type: str = "text"  # text, number, date, boolean, select


@dataclass
class Contact:
    """
    Contato de cliente.
    
    Representa uma pessoa ou empresa no CRM.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""  # Owner
    
    # Informações básicas
    email: str = ""
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    
    # Status
    status: ContactStatus = ContactStatus.ACTIVE
    
    # Social
    instagram: Optional[str] = None
    tiktok: Optional[str] = None
    whatsapp: Optional[str] = None
    website: Optional[str] = None
    
    # Endereço
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Metadata
    source: LeadSource = LeadSource.MANUAL
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    # Email marketing
    subscribed: bool = True
    subscription_date: Optional[datetime] = None
    unsubscribe_date: Optional[datetime] = None
    
    # Scores
    lead_score: int = 0
    engagement_score: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    last_activity_at: Optional[datetime] = None
    
    @property
    def full_name(self) -> str:
        """Nome completo do contato."""
        if self.name:
            return self.name
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else self.email
    
    @property
    def display_name(self) -> str:
        """Nome para exibição."""
        return self.full_name or self.email or "Sem nome"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "company": self.company,
            "job_title": self.job_title,
            "status": self.status.value,
            "instagram": self.instagram,
            "tiktok": self.tiktok,
            "whatsapp": self.whatsapp,
            "website": self.website,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "postal_code": self.postal_code,
            "source": self.source.value,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
            "subscribed": self.subscribed,
            "subscription_date": self.subscription_date.isoformat()
            if self.subscription_date else None,
            "unsubscribe_date": self.unsubscribe_date.isoformat()
            if self.unsubscribe_date else None,
            "lead_score": self.lead_score,
            "engagement_score": self.engagement_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat()
            if self.last_activity_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contact":
        """Cria instância a partir de dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            email=data.get("email", ""),
            name=data.get("name"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            phone=data.get("phone"),
            company=data.get("company"),
            job_title=data.get("job_title"),
            status=ContactStatus(data.get("status", "active")),
            instagram=data.get("instagram"),
            tiktok=data.get("tiktok"),
            whatsapp=data.get("whatsapp"),
            website=data.get("website"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            country=data.get("country"),
            postal_code=data.get("postal_code"),
            source=LeadSource(data.get("source", "manual")),
            tags=data.get("tags", []),
            custom_fields=data.get("custom_fields", {}),
            subscribed=data.get("subscribed", True),
            subscription_date=datetime.fromisoformat(data["subscription_date"])
            if data.get("subscription_date") else None,
            unsubscribe_date=datetime.fromisoformat(data["unsubscribe_date"])
            if data.get("unsubscribe_date") else None,
            lead_score=data.get("lead_score", 0),
            engagement_score=data.get("engagement_score", 0),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data else datetime.now(timezone.utc),
            last_activity_at=datetime.fromisoformat(data["last_activity_at"])
            if data.get("last_activity_at") else None,
        )


@dataclass
class Lead:
    """
    Lead qualificado.
    
    Um lead é um contato que demonstrou interesse
    e está no funil de vendas.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    contact_id: str = ""  # Referência ao contato
    
    # Informações do lead
    title: str = ""
    description: Optional[str] = None
    source: LeadSource = LeadSource.ORGANIC
    status: LeadStatus = LeadStatus.NEW
    
    # Valor estimado
    estimated_value: float = 0.0
    currency: str = "BRL"
    
    # Score
    score: int = 0
    temperature: str = "cold"  # cold, warm, hot
    
    # Interesse
    interested_products: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    
    # Atribuição
    assigned_to: Optional[str] = None
    
    # Datas
    qualified_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None
    lost_at: Optional[datetime] = None
    lost_reason: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    last_contact_at: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None
    
    @property
    def is_active(self) -> bool:
        """Verifica se o lead está ativo."""
        return self.status not in [LeadStatus.WON, LeadStatus.LOST]
    
    @property
    def days_in_pipeline(self) -> int:
        """Dias no pipeline."""
        end_date = self.converted_at or self.lost_at or datetime.now(timezone.utc)
        return (end_date - self.created_at).days
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "contact_id": self.contact_id,
            "title": self.title,
            "description": self.description,
            "source": self.source.value,
            "status": self.status.value,
            "estimated_value": self.estimated_value,
            "currency": self.currency,
            "score": self.score,
            "temperature": self.temperature,
            "interested_products": self.interested_products,
            "interests": self.interests,
            "assigned_to": self.assigned_to,
            "qualified_at": self.qualified_at.isoformat()
            if self.qualified_at else None,
            "converted_at": self.converted_at.isoformat()
            if self.converted_at else None,
            "lost_at": self.lost_at.isoformat() if self.lost_at else None,
            "lost_reason": self.lost_reason,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
            "is_active": self.is_active,
            "days_in_pipeline": self.days_in_pipeline,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_contact_at": self.last_contact_at.isoformat()
            if self.last_contact_at else None,
            "next_follow_up": self.next_follow_up.isoformat()
            if self.next_follow_up else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Lead":
        """Cria instância a partir de dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            contact_id=data.get("contact_id", ""),
            title=data.get("title", ""),
            description=data.get("description"),
            source=LeadSource(data.get("source", "organic")),
            status=LeadStatus(data.get("status", "new")),
            estimated_value=data.get("estimated_value", 0.0),
            currency=data.get("currency", "BRL"),
            score=data.get("score", 0),
            temperature=data.get("temperature", "cold"),
            interested_products=data.get("interested_products", []),
            interests=data.get("interests", []),
            assigned_to=data.get("assigned_to"),
            qualified_at=datetime.fromisoformat(data["qualified_at"])
            if data.get("qualified_at") else None,
            converted_at=datetime.fromisoformat(data["converted_at"])
            if data.get("converted_at") else None,
            lost_at=datetime.fromisoformat(data["lost_at"])
            if data.get("lost_at") else None,
            lost_reason=data.get("lost_reason"),
            tags=data.get("tags", []),
            custom_fields=data.get("custom_fields", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data else datetime.now(timezone.utc),
            last_contact_at=datetime.fromisoformat(data["last_contact_at"])
            if data.get("last_contact_at") else None,
            next_follow_up=datetime.fromisoformat(data["next_follow_up"])
            if data.get("next_follow_up") else None,
        )


@dataclass
class PipelineStage:
    """Estágio de um pipeline."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    order: int = 0
    color: str = "#3B82F6"
    probability: int = 0  # 0-100%
    is_won: bool = False
    is_lost: bool = False
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "order": self.order,
            "color": self.color,
            "probability": self.probability,
            "is_won": self.is_won,
            "is_lost": self.is_lost,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineStage":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            order=data.get("order", 0),
            color=data.get("color", "#3B82F6"),
            probability=data.get("probability", 0),
            is_won=data.get("is_won", False),
            is_lost=data.get("is_lost", False),
            description=data.get("description"),
        )


@dataclass
class Pipeline:
    """
    Pipeline de vendas.
    
    Define os estágios pelos quais um deal passa.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    name: str = "Pipeline Principal"
    description: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    
    stages: List[PipelineStage] = field(default_factory=list)
    
    # Configurações
    currency: str = "BRL"
    deal_rotting_days: int = 30  # Dias para deal ficar "stale"
    
    # Stats cache
    total_deals: int = 0
    total_value: float = 0.0
    
    # Timestamps
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    
    @classmethod
    def default_pipeline(cls, user_id: str) -> "Pipeline":
        """Cria pipeline padrão com estágios típicos."""
        return cls(
            user_id=user_id,
            name="Pipeline Principal",
            is_default=True,
            stages=[
                PipelineStage(
                    name="Lead",
                    order=0,
                    color="#94A3B8",
                    probability=10,
                ),
                PipelineStage(
                    name="Qualificado",
                    order=1,
                    color="#3B82F6",
                    probability=25,
                ),
                PipelineStage(
                    name="Proposta",
                    order=2,
                    color="#8B5CF6",
                    probability=50,
                ),
                PipelineStage(
                    name="Negociação",
                    order=3,
                    color="#F59E0B",
                    probability=75,
                ),
                PipelineStage(
                    name="Fechamento",
                    order=4,
                    color="#10B981",
                    probability=90,
                ),
                PipelineStage(
                    name="Ganho",
                    order=5,
                    color="#22C55E",
                    probability=100,
                    is_won=True,
                ),
                PipelineStage(
                    name="Perdido",
                    order=6,
                    color="#EF4444",
                    probability=0,
                    is_lost=True,
                ),
            ],
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "stages": [s.to_dict() for s in self.stages],
            "currency": self.currency,
            "deal_rotting_days": self.deal_rotting_days,
            "total_deals": self.total_deals,
            "total_value": self.total_value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pipeline":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            name=data.get("name", "Pipeline Principal"),
            description=data.get("description"),
            is_default=data.get("is_default", False),
            is_active=data.get("is_active", True),
            stages=[PipelineStage.from_dict(s) for s in data.get("stages", [])],
            currency=data.get("currency", "BRL"),
            deal_rotting_days=data.get("deal_rotting_days", 30),
            total_deals=data.get("total_deals", 0),
            total_value=data.get("total_value", 0.0),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data else datetime.now(timezone.utc),
        )


@dataclass
class Deal:
    """
    Deal (Negócio/Oportunidade).
    
    Representa uma oportunidade de venda no pipeline.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Relacionamentos
    contact_id: str = ""
    lead_id: Optional[str] = None
    pipeline_id: str = ""
    stage_id: str = ""
    
    # Informações do deal
    title: str = ""
    description: Optional[str] = None
    
    # Valor
    value: float = 0.0
    currency: str = "BRL"
    
    # Status
    status: DealStatus = DealStatus.OPEN
    probability: int = 0  # Herdado do stage
    
    # Datas
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    won_at: Optional[datetime] = None
    lost_at: Optional[datetime] = None
    lost_reason: Optional[str] = None
    
    # Atribuição
    assigned_to: Optional[str] = None
    
    # Produtos
    products: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    last_activity_at: Optional[datetime] = None
    stage_entered_at: datetime = field(default_factory=_utc_now)
    
    @property
    def is_open(self) -> bool:
        """Verifica se o deal está aberto."""
        return self.status == DealStatus.OPEN
    
    @property
    def is_won(self) -> bool:
        """Verifica se o deal foi ganho."""
        return self.status == DealStatus.WON
    
    @property
    def is_lost(self) -> bool:
        """Verifica se o deal foi perdido."""
        return self.status == DealStatus.LOST
    
    @property
    def days_in_stage(self) -> int:
        """Dias no estágio atual."""
        return (datetime.now(timezone.utc) - self.stage_entered_at).days
    
    @property
    def weighted_value(self) -> float:
        """Valor ponderado pela probabilidade."""
        return self.value * (self.probability / 100)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "contact_id": self.contact_id,
            "lead_id": self.lead_id,
            "pipeline_id": self.pipeline_id,
            "stage_id": self.stage_id,
            "title": self.title,
            "description": self.description,
            "value": self.value,
            "currency": self.currency,
            "status": self.status.value,
            "probability": self.probability,
            "expected_close_date": self.expected_close_date.isoformat()
            if self.expected_close_date else None,
            "actual_close_date": self.actual_close_date.isoformat()
            if self.actual_close_date else None,
            "won_at": self.won_at.isoformat() if self.won_at else None,
            "lost_at": self.lost_at.isoformat() if self.lost_at else None,
            "lost_reason": self.lost_reason,
            "assigned_to": self.assigned_to,
            "products": self.products,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
            "is_open": self.is_open,
            "is_won": self.is_won,
            "is_lost": self.is_lost,
            "days_in_stage": self.days_in_stage,
            "weighted_value": self.weighted_value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat()
            if self.last_activity_at else None,
            "stage_entered_at": self.stage_entered_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Deal":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            contact_id=data.get("contact_id", ""),
            lead_id=data.get("lead_id"),
            pipeline_id=data.get("pipeline_id", ""),
            stage_id=data.get("stage_id", ""),
            title=data.get("title", ""),
            description=data.get("description"),
            value=data.get("value", 0.0),
            currency=data.get("currency", "BRL"),
            status=DealStatus(data.get("status", "open")),
            probability=data.get("probability", 0),
            expected_close_date=datetime.fromisoformat(data["expected_close_date"])
            if data.get("expected_close_date") else None,
            actual_close_date=datetime.fromisoformat(data["actual_close_date"])
            if data.get("actual_close_date") else None,
            won_at=datetime.fromisoformat(data["won_at"])
            if data.get("won_at") else None,
            lost_at=datetime.fromisoformat(data["lost_at"])
            if data.get("lost_at") else None,
            lost_reason=data.get("lost_reason"),
            assigned_to=data.get("assigned_to"),
            products=data.get("products", []),
            tags=data.get("tags", []),
            custom_fields=data.get("custom_fields", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data else datetime.now(timezone.utc),
            last_activity_at=datetime.fromisoformat(data["last_activity_at"])
            if data.get("last_activity_at") else None,
            stage_entered_at=datetime.fromisoformat(data["stage_entered_at"])
            if data.get("stage_entered_at") else datetime.now(timezone.utc),
        )


@dataclass
class Activity:
    """
    Atividade/Histórico.
    
    Registra todas as interações e eventos.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Relacionamentos (um dos três)
    contact_id: Optional[str] = None
    lead_id: Optional[str] = None
    deal_id: Optional[str] = None
    
    # Tipo e conteúdo
    activity_type: ActivityType = ActivityType.NOTE
    title: str = ""
    description: Optional[str] = None
    content: Optional[str] = None
    
    # Metadados específicos por tipo
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Para tasks
    is_done: bool = False
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Participantes
    performed_by: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "contact_id": self.contact_id,
            "lead_id": self.lead_id,
            "deal_id": self.deal_id,
            "activity_type": self.activity_type.value,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "metadata": self.metadata,
            "is_done": self.is_done,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at else None,
            "performed_by": self.performed_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Activity":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            contact_id=data.get("contact_id"),
            lead_id=data.get("lead_id"),
            deal_id=data.get("deal_id"),
            activity_type=ActivityType(data.get("activity_type", "note")),
            title=data.get("title", ""),
            description=data.get("description"),
            content=data.get("content"),
            metadata=data.get("metadata", {}),
            is_done=data.get("is_done", False),
            due_date=datetime.fromisoformat(data["due_date"])
            if data.get("due_date") else None,
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at") else None,
            performed_by=data.get("performed_by"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data else datetime.now(timezone.utc),
        )


@dataclass
class SegmentCondition:
    """Condição de um segmento."""
    field: str  # contact.email, lead.score, deal.value, etc.
    operator: SegmentOperator
    value: Any
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SegmentCondition":
        return cls(
            field=data.get("field", ""),
            operator=SegmentOperator(data.get("operator", "equals")),
            value=data.get("value"),
        )


@dataclass
class Segment:
    """
    Segmento dinâmico.
    
    Agrupa contatos/leads baseado em condições.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    name: str = ""
    description: Optional[str] = None
    
    # Condições
    conditions: List[SegmentCondition] = field(default_factory=list)
    match_type: str = "all"  # all = AND, any = OR
    
    # Tipo
    segment_type: str = "contacts"  # contacts, leads, deals
    
    # Cache
    count: int = 0
    last_computed_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "conditions": [c.to_dict() for c in self.conditions],
            "match_type": self.match_type,
            "segment_type": self.segment_type,
            "count": self.count,
            "last_computed_at": self.last_computed_at.isoformat()
            if self.last_computed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Segment":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            conditions=[
                SegmentCondition.from_dict(c)
                for c in data.get("conditions", [])
            ],
            match_type=data.get("match_type", "all"),
            segment_type=data.get("segment_type", "contacts"),
            count=data.get("count", 0),
            last_computed_at=datetime.fromisoformat(data["last_computed_at"])
            if data.get("last_computed_at") else None,
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data else datetime.now(timezone.utc),
        )
