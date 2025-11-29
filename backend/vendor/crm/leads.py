"""
Lead Management Module
======================
Sistema de gerenciamento de leads para vendas e marketing.

Funcionalidades:
- Captura de leads de múltiplas fontes
- Scoring automático
- Pipeline de vendas
- Integração com WhatsApp/Email
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr
import logging

logger = logging.getLogger(__name__)


class LeadSource(str, Enum):
    """Origem do lead."""
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    WEBSITE = "website"
    REFERRAL = "referral"
    ADS_GOOGLE = "google_ads"
    ADS_META = "meta_ads"
    ORGANIC = "organic"
    OTHER = "other"


class LeadStatus(str, Enum):
    """Status do lead no pipeline."""
    NEW = "new"                    # Recém capturado
    CONTACTED = "contacted"        # Primeiro contato feito
    QUALIFIED = "qualified"        # Qualificado (tem interesse real)
    NEGOTIATING = "negotiating"    # Em negociação
    WON = "won"                    # Convertido em cliente
    LOST = "lost"                  # Perdido
    NURTURING = "nurturing"        # Em nutrição (ainda não está pronto)


class LeadPriority(str, Enum):
    """Prioridade do lead."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class LeadTag(str, Enum):
    """Tags comuns para leads."""
    INTERESTED_PRICING = "interested_in_pricing"
    ASKED_DEMO = "asked_demo"
    RETURNING_VISITOR = "returning_visitor"
    HIGH_VALUE = "high_value"
    NEEDS_FOLLOWUP = "needs_followup"
    HOT_LEAD = "hot_lead"
    COLD_LEAD = "cold_lead"


# ==================== Pydantic Models ====================

class LeadCreate(BaseModel):
    """Schema para criação de lead."""
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: LeadSource = LeadSource.WEBSITE
    source_details: Optional[str] = None  # Ex: campanha específica
    notes: Optional[str] = None
    custom_fields: Dict[str, Any] = {}


class LeadUpdate(BaseModel):
    """Schema para atualização de lead."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[LeadStatus] = None
    priority: Optional[LeadPriority] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class LeadResponse(BaseModel):
    """Schema de resposta de lead."""
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    source: LeadSource
    status: LeadStatus
    priority: LeadPriority
    score: int
    tags: List[str]
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_contact_at: Optional[datetime]
    notes: Optional[str]
    custom_fields: Dict[str, Any]


# ==================== Lead Entity ====================

@dataclass
class Lead:
    """Entidade Lead."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    source: LeadSource = LeadSource.WEBSITE
    source_details: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW
    priority: LeadPriority = LeadPriority.MEDIUM
    score: int = 0
    tags: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_contact_at: Optional[datetime] = None
    notes: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    activities: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_tag(self, tag: str):
        """Adiciona tag ao lead."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str):
        """Remove tag do lead."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def log_activity(self, activity_type: str, description: str, data: Dict[str, Any] = None):
        """Registra atividade no histórico."""
        self.activities.append({
            "type": activity_type,
            "description": description,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def mark_contacted(self):
        """Marca como contatado."""
        self.status = LeadStatus.CONTACTED
        self.last_contact_at = datetime.now()
        self.log_activity("contact", "Lead contatado")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "source": self.source.value,
            "source_details": self.source_details,
            "status": self.status.value,
            "priority": self.priority.value,
            "score": self.score,
            "tags": self.tags,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_contact_at": self.last_contact_at.isoformat() if self.last_contact_at else None,
            "notes": self.notes,
            "custom_fields": self.custom_fields,
            "activities": self.activities
        }


# ==================== Lead Scoring ====================

class LeadScorer:
    """
    Sistema de scoring de leads.
    
    Pontuação baseada em:
    - Completude do perfil
    - Origem
    - Interações
    - Tempo desde criação
    """
    
    # Pesos por origem
    SOURCE_SCORES = {
        LeadSource.REFERRAL: 30,
        LeadSource.WHATSAPP: 25,
        LeadSource.ADS_GOOGLE: 20,
        LeadSource.ADS_META: 20,
        LeadSource.INSTAGRAM: 15,
        LeadSource.TIKTOK: 15,
        LeadSource.WEBSITE: 10,
        LeadSource.ORGANIC: 10,
        LeadSource.OTHER: 5,
    }
    
    # Pesos por completude
    PROFILE_SCORES = {
        "has_email": 10,
        "has_phone": 15,
        "has_name": 5,
    }
    
    # Pesos por atividade
    ACTIVITY_SCORES = {
        "contact": 10,
        "message_sent": 5,
        "message_received": 15,
        "page_visit": 3,
        "product_view": 5,
        "cart_add": 20,
        "demo_request": 30,
    }
    
    def score_by_source(self, lead: Lead) -> int:
        """Calcula score baseado na origem do lead."""
        return self.SOURCE_SCORES.get(lead.source, 0)
    
    def score_by_completeness(self, lead: Lead) -> int:
        """Calcula score baseado na completude do perfil."""
        score = 0
        if lead.email:
            score += self.PROFILE_SCORES["has_email"]
        if lead.phone:
            score += self.PROFILE_SCORES["has_phone"]
        if lead.name and len(lead.name) > 2:
            score += self.PROFILE_SCORES["has_name"]
        return score
    
    def score_by_engagement(self, lead: Lead) -> int:
        """Calcula score baseado em tags de engajamento."""
        score = 0
        if "hot_lead" in lead.tags:
            score += 25
        if "high_value" in lead.tags:
            score += 20
        if "asked_demo" in lead.tags:
            score += 15
        return score
    
    def score_by_recency(self, lead: Lead) -> int:
        """Calcula score baseado na recência de contato."""
        if not lead.last_contact_at:
            return 0
        
        days_since_contact = (datetime.now() - lead.last_contact_at).days
        if days_since_contact <= 3:
            return 20
        elif days_since_contact <= 7:
            return 15
        elif days_since_contact <= 14:
            return 10
        elif days_since_contact <= 30:
            return 5
        else:
            return 0
    
    def calculate_score(self, lead: Lead) -> int:
        """Calcula score do lead."""
        score = 0
        
        # Score por origem
        score += self.SOURCE_SCORES.get(lead.source, 0)
        
        # Score por completude
        if lead.email:
            score += self.PROFILE_SCORES["has_email"]
        if lead.phone:
            score += self.PROFILE_SCORES["has_phone"]
        if lead.name and len(lead.name) > 2:
            score += self.PROFILE_SCORES["has_name"]
        
        # Score por atividades
        for activity in lead.activities:
            activity_type = activity.get("type", "")
            score += self.ACTIVITY_SCORES.get(activity_type, 0)
        
        # Bonus por tags especiais
        if "hot_lead" in lead.tags:
            score += 25
        if "high_value" in lead.tags:
            score += 20
        if "asked_demo" in lead.tags:
            score += 15
        
        # Penalidade por inatividade
        if lead.last_contact_at:
            days_since_contact = (datetime.now() - lead.last_contact_at).days
            if days_since_contact > 30:
                score -= 10
            elif days_since_contact > 14:
                score -= 5
        
        return max(0, min(100, score))  # Clamp 0-100
    
    def get_priority(self, score: int) -> LeadPriority:
        """Determina prioridade baseada no score."""
        if score >= 75:
            return LeadPriority.URGENT
        elif score >= 50:
            return LeadPriority.HIGH
        elif score >= 25:
            return LeadPriority.MEDIUM
        else:
            return LeadPriority.LOW


# ==================== Lead Manager (In-Memory) ====================

class LeadManager:
    """
    Gerenciador de leads (in-memory para MVP).
    
    Em produção, substituir por repository com banco de dados.
    
    Uso:
        manager = LeadManager()
        
        # Criar lead
        lead = manager.create_lead(LeadCreate(
            name="João Silva",
            email="joao@email.com",
            phone="5511999999999",
            source=LeadSource.WHATSAPP
        ))
        
        # Buscar leads
        hot_leads = manager.get_leads(status=LeadStatus.QUALIFIED, min_score=50)
        
        # Atualizar
        manager.update_lead(lead.id, LeadUpdate(status=LeadStatus.NEGOTIATING))
    """
    
    def __init__(self):
        self._leads: Dict[str, Lead] = {}
        self._scorer = LeadScorer()
        self._id_counter = 0
    
    def _generate_id(self) -> str:
        """Gera ID único."""
        self._id_counter += 1
        return f"lead_{self._id_counter}"
    
    def create_lead(self, data: LeadCreate) -> Lead:
        """Cria novo lead."""
        lead_id = self._generate_id()
        
        lead = Lead(
            id=lead_id,
            name=data.name,
            email=data.email,
            phone=data.phone,
            source=data.source,
            source_details=data.source_details,
            notes=data.notes,
            custom_fields=data.custom_fields
        )
        
        # Calcular score inicial
        lead.score = self._scorer.calculate_score(lead)
        lead.priority = self._scorer.get_priority(lead.score)
        
        # Registrar atividade
        lead.log_activity("created", f"Lead criado via {data.source.value}")
        
        self._leads[lead_id] = lead
        logger.info(f"Lead criado: {lead_id} - {lead.name}")
        
        return lead
    
    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Obtém lead por ID."""
        return self._leads.get(lead_id)
    
    def get_leads(
        self,
        status: Optional[LeadStatus] = None,
        source: Optional[LeadSource] = None,
        priority: Optional[LeadPriority] = None,
        min_score: Optional[int] = None,
        assigned_to: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 100
    ) -> List[Lead]:
        """Lista leads com filtros."""
        results = []
        
        for lead in self._leads.values():
            if status and lead.status != status:
                continue
            if source and lead.source != source:
                continue
            if priority and lead.priority != priority:
                continue
            if min_score and lead.score < min_score:
                continue
            if assigned_to and lead.assigned_to != assigned_to:
                continue
            if tag and tag not in lead.tags:
                continue
            
            results.append(lead)
            
            if len(results) >= limit:
                break
        
        # Ordenar por score (maior primeiro)
        results.sort(key=lambda lead: lead.score, reverse=True)
        
        return results
    
    def update_lead(self, lead_id: str, data: LeadUpdate) -> Optional[Lead]:
        """Atualiza lead."""
        lead = self._leads.get(lead_id)
        if not lead:
            return None
        
        if data.name is not None:
            lead.name = data.name
        if data.email is not None:
            lead.email = data.email
        if data.phone is not None:
            lead.phone = data.phone
        if data.status is not None:
            old_status = lead.status
            lead.status = data.status
            lead.log_activity("status_change", f"Status: {old_status.value} → {data.status.value}")
        if data.priority is not None:
            lead.priority = data.priority
        if data.assigned_to is not None:
            lead.assigned_to = data.assigned_to
            lead.log_activity("assigned", f"Atribuído para: {data.assigned_to}")
        if data.notes is not None:
            lead.notes = data.notes
        if data.custom_fields is not None:
            lead.custom_fields.update(data.custom_fields)
        
        lead.updated_at = datetime.now()
        
        # Recalcular score
        lead.score = self._scorer.calculate_score(lead)
        
        return lead
    
    def delete_lead(self, lead_id: str) -> bool:
        """Remove lead."""
        if lead_id in self._leads:
            del self._leads[lead_id]
            return True
        return False
    
    def add_activity(
        self,
        lead_id: str,
        activity_type: str,
        description: str,
        data: Dict[str, Any] = None
    ) -> Optional[Lead]:
        """Adiciona atividade ao lead."""
        lead = self._leads.get(lead_id)
        if not lead:
            return None
        
        lead.log_activity(activity_type, description, data)
        lead.score = self._scorer.calculate_score(lead)
        
        return lead
    
    def add_tag(self, lead_id: str, tag: str) -> Optional[Lead]:
        """Adiciona tag ao lead."""
        lead = self._leads.get(lead_id)
        if not lead:
            return None
        
        lead.add_tag(tag)
        lead.score = self._scorer.calculate_score(lead)
        
        return lead
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas dos leads."""
        stats = {
            "total": len(self._leads),
            "by_status": {},
            "by_source": {},
            "by_priority": {},
            "average_score": 0
        }
        
        total_score = 0
        
        for lead in self._leads.values():
            # Por status
            status = lead.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Por origem
            source = lead.source.value
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            
            # Por prioridade
            priority = lead.priority.value
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            
            total_score += lead.score
        
        if self._leads:
            stats["average_score"] = total_score / len(self._leads)
        
        return stats


# ==================== WhatsApp Lead Capture ====================

def create_lead_from_whatsapp(
    manager: LeadManager,
    from_number: str,
    from_name: str,
    first_message: str
) -> Lead:
    """
    Cria lead a partir de mensagem WhatsApp.
    
    Uso no webhook:
        message = parse_webhook_message(payload)
        lead = create_lead_from_whatsapp(
            manager,
            message.from_number,
            message.from_name,
            message.content
        )
    """
    # Verificar se já existe lead com esse telefone
    existing = manager.get_leads(limit=1000)
    for lead in existing:
        if lead.phone == from_number:
            # Atualizar com nova atividade
            manager.add_activity(
                lead.id,
                "message_received",
                f"Nova mensagem: {first_message[:100]}"
            )
            return lead
    
    # Criar novo lead
    return manager.create_lead(LeadCreate(
        name=from_name or f"WhatsApp {from_number[-4:]}",
        phone=from_number,
        source=LeadSource.WHATSAPP,
        notes=f"Primeira mensagem: {first_message[:500]}"
    ))
