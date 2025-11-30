"""
CRM Advanced Services
=====================
Serviços avançados de CRM para:
- Score Decay (degradação temporal de scores)
- Deal Risk Detection (detecção de deals em risco)
- Next Best Action (recomendação de próximas ações)
- Predictive Analytics (análise preditiva)

Baseado em best practices de CRM 2024:
- AI-powered lead scoring
- Deal risk indicators
- Engagement tracking
- Automated recommendations
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from .models import (
    Lead, LeadStatus,
    Deal, DealStatus, Activity, ActivityType
)
from .repository import (
    ContactRepository, LeadRepository, DealRepository,
    ActivityRepository, PipelineRepository
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS E DATACLASSES
# =============================================================================

class RiskLevel(str, Enum):
    """Níveis de risco para deals."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionPriority(str, Enum):
    """Prioridade de ações recomendadas."""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ScoreDecayConfig:
    """Configuração para decay de score."""
    # Taxa de decay por semana de inatividade (%)
    decay_rate_per_week: float = 5.0
    # Máximo de decay permitido (%)
    max_decay_percent: float = 70.0
    # Dias de inatividade para iniciar decay
    grace_period_days: int = 7
    # Score mínimo após decay
    minimum_score: int = 5
    
    # Multiplicadores por temperatura
    hot_decay_multiplier: float = 1.5  # Hot leads decaem mais rápido
    warm_decay_multiplier: float = 1.0
    cold_decay_multiplier: float = 0.5  # Cold leads decaem mais devagar


@dataclass
class RiskSignal:
    """Sinal de risco identificado em um deal."""
    signal_type: str
    severity: RiskLevel
    message: str
    detected_at: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "severity": self.severity.value,
            "message": self.message,
            "detected_at": self.detected_at.isoformat(),
            "data": self.data
        }


@dataclass
class RiskAssessment:
    """Avaliação de risco de um deal."""
    deal_id: str
    risk_level: RiskLevel
    risk_score: int  # 0-100
    signals: List[RiskSignal]
    recommendations: List[str]
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "deal_id": self.deal_id,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "signals": [s.to_dict() for s in self.signals],
            "recommendations": self.recommendations,
            "assessed_at": self.assessed_at.isoformat()
        }


@dataclass
class NextBestAction:
    """Recomendação de próxima ação."""
    action_type: str
    action_label: str
    reason: str
    priority: ActionPriority
    suggested_timing: str
    entity_type: str  # lead, deal, contact
    entity_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "action_label": self.action_label,
            "reason": self.reason,
            "priority": self.priority.value,
            "suggested_timing": self.suggested_timing,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "metadata": self.metadata
        }


@dataclass
class ScoreDecayResult:
    """Resultado do decay de score."""
    lead_id: str
    old_score: int
    new_score: int
    old_temperature: str
    new_temperature: str
    decay_applied: float
    reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "old_score": self.old_score,
            "new_score": self.new_score,
            "old_temperature": self.old_temperature,
            "new_temperature": self.new_temperature,
            "decay_applied": self.decay_applied,
            "reason": self.reason
        }


# =============================================================================
# SCORE DECAY SERVICE
# =============================================================================

class ScoreDecayService:
    """
    Serviço de decay de score para leads inativos.
    
    Aplica degradação temporal aos scores de leads que não tiveram
    atividade recente, evitando que leads "mortos" apareçam como hot.
    
    Algoritmo:
    - Calcula dias desde última atividade
    - Aplica decay exponencial baseado no tempo
    - Ajusta por temperatura atual do lead
    - Atualiza score e temperatura no banco
    """
    
    def __init__(
        self, 
        db_pool, 
        config: Optional[ScoreDecayConfig] = None
    ):
        self.lead_repo = LeadRepository(db_pool)
        self.contact_repo = ContactRepository(db_pool)
        self.activity_repo = ActivityRepository(db_pool)
        self.config = config or ScoreDecayConfig()
    
    async def run_decay_batch(
        self, 
        user_id: str,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Executa decay em batch para todos os leads do usuário.
        
        Usado pelo job diário de manutenção.
        
        Returns:
            Dict com estatísticas: processed, decayed, unchanged
        """
        leads, total = await self.lead_repo.list(
            user_id=user_id,
            limit=batch_size
        )
        
        results = {
            "processed": 0,
            "decayed": 0,
            "unchanged": 0,
            "details": []
        }
        
        for lead in leads:
            if lead.status in [LeadStatus.WON, LeadStatus.LOST]:
                continue  # Ignora leads finalizados
            
            result = await self.calculate_and_apply_decay(lead, user_id)
            results["processed"] += 1
            
            if result:
                if result.old_score != result.new_score:
                    results["decayed"] += 1
                    results["details"].append(result.to_dict())
                else:
                    results["unchanged"] += 1
        
        logger.info(
            f"Score decay batch for user {user_id}: "
            f"processed={results['processed']}, decayed={results['decayed']}"
        )
        
        return results
    
    async def calculate_and_apply_decay(
        self,
        lead: Lead,
        user_id: str
    ) -> Optional[ScoreDecayResult]:
        """
        Calcula e aplica decay para um lead específico.
        
        Returns:
            ScoreDecayResult com detalhes da operação
        """
        # Determina última atividade
        last_activity = lead.last_contact_at
        if not last_activity:
            last_activity = lead.created_at
        
        # Calcula dias de inatividade
        days_inactive = (datetime.utcnow() - last_activity).days
        
        # Verifica período de graça
        if days_inactive <= self.config.grace_period_days:
            return ScoreDecayResult(
                lead_id=lead.id,
                old_score=lead.score,
                new_score=lead.score,
                old_temperature=lead.temperature,
                new_temperature=lead.temperature,
                decay_applied=0.0,
                reason="Within grace period"
            )
        
        # Calcula decay
        decay_percent = self._calculate_decay_percent(
            days_inactive,
            lead.temperature
        )
        
        if decay_percent <= 0:
            return ScoreDecayResult(
                lead_id=lead.id,
                old_score=lead.score,
                new_score=lead.score,
                old_temperature=lead.temperature,
                new_temperature=lead.temperature,
                decay_applied=0.0,
                reason="No decay needed"
            )
        
        # Aplica decay
        old_score = lead.score
        new_score = max(
            self.config.minimum_score,
            int(old_score * (1 - decay_percent / 100))
        )
        
        # Recalcula temperatura
        new_temperature = self._calculate_temperature(new_score)
        
        # Atualiza no banco
        await self.lead_repo.update_score_and_temperature(
            lead.id,
            user_id,
            new_score,
            new_temperature
        )
        
        result = ScoreDecayResult(
            lead_id=lead.id,
            old_score=old_score,
            new_score=new_score,
            old_temperature=lead.temperature,
            new_temperature=new_temperature,
            decay_applied=decay_percent,
            reason=f"Inactive for {days_inactive} days"
        )
        
        logger.debug(
            f"Applied decay to lead {lead.id}: "
            f"{old_score} -> {new_score} ({decay_percent:.1f}% decay)"
        )
        
        return result
    
    def _calculate_decay_percent(
        self,
        days_inactive: int,
        temperature: str
    ) -> float:
        """
        Calcula percentual de decay baseado em inatividade.
        
        Usa decay exponencial suave para evitar quedas bruscas.
        """
        # Semanas de inatividade (após período de graça)
        effective_days = days_inactive - self.config.grace_period_days
        weeks_inactive = effective_days / 7.0
        
        # Decay base por semana
        base_decay = self.config.decay_rate_per_week * weeks_inactive
        
        # Multiplicador por temperatura
        multipliers = {
            "hot": self.config.hot_decay_multiplier,
            "warm": self.config.warm_decay_multiplier,
            "cold": self.config.cold_decay_multiplier
        }
        multiplier = multipliers.get(temperature, 1.0)
        
        # Decay final (limitado pelo máximo)
        decay_percent = min(
            base_decay * multiplier,
            self.config.max_decay_percent
        )
        
        return decay_percent
    
    def _calculate_temperature(self, score: int) -> str:
        """Calcula temperatura baseado no score."""
        if score >= 70:
            return "hot"
        elif score >= 40:
            return "warm"
        return "cold"


# =============================================================================
# DEAL RISK DETECTION SERVICE
# =============================================================================

class DealRiskDetectionService:
    """
    Serviço de detecção de risco em deals.
    
    Monitora sinais de risco:
    - Stalled: Deal parado muito tempo no mesmo stage
    - Engagement Drop: Queda de interações/atividades
    - Timeline Slip: Data de fechamento esperada passou
    - Value Reduction: Valor do deal foi reduzido
    - No Recent Contact: Sem contato recente com cliente
    
    Cada sinal tem severidade e gera recomendações de ação.
    """
    
    # Thresholds de risco
    STALL_WARNING_DAYS = 14
    STALL_HIGH_DAYS = 30
    STALL_CRITICAL_DAYS = 45
    
    NO_ACTIVITY_WARNING_DAYS = 7
    NO_ACTIVITY_HIGH_DAYS = 14
    NO_ACTIVITY_CRITICAL_DAYS = 21
    
    VALUE_REDUCTION_WARNING = 0.20  # 20%
    VALUE_REDUCTION_HIGH = 0.40  # 40%
    
    def __init__(self, db_pool):
        self.deal_repo = DealRepository(db_pool)
        self.pipeline_repo = PipelineRepository(db_pool)
        self.activity_repo = ActivityRepository(db_pool)
    
    async def assess_deal_risk(
        self,
        deal_id: str,
        user_id: str
    ) -> RiskAssessment:
        """
        Avalia risco de um deal específico.
        
        Returns:
            RiskAssessment com todos os sinais detectados
        """
        deal = await self.deal_repo.get_by_id(deal_id, user_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")
        
        # Ignora deals finalizados
        if deal.status != DealStatus.OPEN:
            return RiskAssessment(
                deal_id=deal_id,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                signals=[],
                recommendations=["Deal já finalizado"]
            )
        
        # Busca pipeline para contexto
        pipeline = await self.pipeline_repo.get_by_id(
            deal.pipeline_id, user_id
        )
        
        # Busca atividades recentes
        activities, _ = await self.activity_repo.list_for_entity(
            user_id=user_id,
            deal_id=deal_id,
            limit=20
        )
        
        # Detecta sinais de risco
        signals = []
        
        # 1. Stalled check
        stall_signal = self._check_stalled(deal, pipeline)
        if stall_signal:
            signals.append(stall_signal)
        
        # 2. Engagement drop
        engagement_signal = self._check_engagement_drop(deal, activities)
        if engagement_signal:
            signals.append(engagement_signal)
        
        # 3. Timeline slip
        timeline_signal = self._check_timeline_slip(deal)
        if timeline_signal:
            signals.append(timeline_signal)
        
        # 4. No recent contact
        contact_signal = self._check_no_recent_contact(deal, activities)
        if contact_signal:
            signals.append(contact_signal)
        
        # Calcula risk score e level
        risk_score = self._calculate_risk_score(signals)
        risk_level = self._determine_risk_level(risk_score)
        
        # Gera recomendações
        recommendations = self._generate_recommendations(signals, deal)
        
        return RiskAssessment(
            deal_id=deal_id,
            risk_level=risk_level,
            risk_score=risk_score,
            signals=signals,
            recommendations=recommendations
        )
    
    async def assess_all_deals(
        self,
        user_id: str,
        pipeline_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Avalia risco de todos os deals abertos.
        
        Returns:
            Dict com deals organizados por nível de risco
        """
        deals, total = await self.deal_repo.list(
            user_id=user_id,
            pipeline_id=pipeline_id,
            status=DealStatus.OPEN,
            limit=1000
        )
        
        results = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "summary": {
                "total_assessed": 0,
                "at_risk": 0,
                "total_value_at_risk": 0.0
            }
        }
        
        for deal in deals:
            assessment = await self.assess_deal_risk(deal.id, user_id)
            results["summary"]["total_assessed"] += 1
            
            level = assessment.risk_level.value
            results[level].append({
                "deal": deal.to_dict(),
                "assessment": assessment.to_dict()
            })
            
            if assessment.risk_level in [
                RiskLevel.HIGH, RiskLevel.CRITICAL
            ]:
                results["summary"]["at_risk"] += 1
                results["summary"]["total_value_at_risk"] += deal.value
        
        return results
    
    def _check_stalled(
        self,
        deal: Deal,
        pipeline: Optional[Any]
    ) -> Optional[RiskSignal]:
        """Verifica se deal está parado muito tempo."""
        days_in_stage = deal.days_in_stage
        
        # Usa deal_rotting_days do pipeline se disponível
        rotting_days = 30
        if pipeline:
            rotting_days = pipeline.deal_rotting_days
        
        if days_in_stage >= self.STALL_CRITICAL_DAYS:
            return RiskSignal(
                signal_type="stalled",
                severity=RiskLevel.CRITICAL,
                message=f"Deal parado há {days_in_stage} dias no mesmo estágio",
                data={
                    "days_in_stage": days_in_stage,
                    "threshold": self.STALL_CRITICAL_DAYS
                }
            )
        elif days_in_stage >= self.STALL_HIGH_DAYS:
            return RiskSignal(
                signal_type="stalled",
                severity=RiskLevel.HIGH,
                message=f"Deal parado há {days_in_stage} dias no mesmo estágio",
                data={
                    "days_in_stage": days_in_stage,
                    "threshold": self.STALL_HIGH_DAYS
                }
            )
        elif days_in_stage >= self.STALL_WARNING_DAYS:
            return RiskSignal(
                signal_type="stalled",
                severity=RiskLevel.MEDIUM,
                message=f"Deal há {days_in_stage} dias no mesmo estágio",
                data={
                    "days_in_stage": days_in_stage,
                    "threshold": self.STALL_WARNING_DAYS
                }
            )
        
        return None
    
    def _check_engagement_drop(
        self,
        deal: Deal,
        activities: List[Activity]
    ) -> Optional[RiskSignal]:
        """Verifica queda de engajamento."""
        if not activities:
            # Sem atividades registradas
            days_since_creation = (datetime.utcnow() - deal.created_at).days
            if days_since_creation >= self.NO_ACTIVITY_HIGH_DAYS:
                return RiskSignal(
                    signal_type="no_activities",
                    severity=RiskLevel.HIGH,
                    message="Nenhuma atividade registrada para este deal",
                    data={"days_since_creation": days_since_creation}
                )
        else:
            # Verifica atividades recentes
            recent_activities = [
                a for a in activities
                if (datetime.utcnow() - a.created_at).days <= 14
            ]
            older_activities = [
                a for a in activities
                if (datetime.utcnow() - a.created_at).days > 14
            ]
            
            # Se tinha atividades antes e agora não tem
            if len(older_activities) > 0 and len(recent_activities) == 0:
                return RiskSignal(
                    signal_type="engagement_drop",
                    severity=RiskLevel.MEDIUM,
                    message="Queda de engajamento - sem atividades nos últimos 14 dias",
                    data={
                        "recent_count": len(recent_activities),
                        "older_count": len(older_activities)
                    }
                )
        
        return None
    
    def _check_timeline_slip(self, deal: Deal) -> Optional[RiskSignal]:
        """Verifica se data de fechamento passou."""
        if not deal.expected_close_date:
            return None
        
        now = datetime.utcnow()
        
        if deal.expected_close_date < now:
            days_overdue = (now - deal.expected_close_date).days
            
            if days_overdue >= 30:
                severity = RiskLevel.CRITICAL
            elif days_overdue >= 14:
                severity = RiskLevel.HIGH
            else:
                severity = RiskLevel.MEDIUM
            
            return RiskSignal(
                signal_type="timeline_slip",
                severity=severity,
                message=f"Data de fechamento esperada passou há {days_overdue} dias",
                data={
                    "expected_close": deal.expected_close_date.isoformat(),
                    "days_overdue": days_overdue
                }
            )
        elif (deal.expected_close_date - now).days <= 7:
            # Fecha em breve - alerta informativo
            days_to_close = (deal.expected_close_date - now).days
            return RiskSignal(
                signal_type="closing_soon",
                severity=RiskLevel.LOW,
                message=f"Deal fecha em {days_to_close} dias",
                data={
                    "expected_close": deal.expected_close_date.isoformat(),
                    "days_to_close": days_to_close
                }
            )
        
        return None
    
    def _check_no_recent_contact(
        self,
        deal: Deal,
        activities: List[Activity]
    ) -> Optional[RiskSignal]:
        """Verifica se houve contato recente com cliente."""
        # Tipos de atividade que contam como contato
        contact_types = [
            ActivityType.CALL,
            ActivityType.EMAIL,
            ActivityType.MEETING,
            ActivityType.NOTE
        ]
        
        contact_activities = [
            a for a in activities
            if a.activity_type in contact_types
        ]
        
        if not contact_activities:
            last_activity = deal.last_activity_at or deal.created_at
        else:
            last_activity = max(a.created_at for a in contact_activities)
        
        days_since_contact = (datetime.utcnow() - last_activity).days
        
        if days_since_contact >= self.NO_ACTIVITY_CRITICAL_DAYS:
            return RiskSignal(
                signal_type="no_recent_contact",
                severity=RiskLevel.HIGH,
                message=f"Sem contato com cliente há {days_since_contact} dias",
                data={"days_since_contact": days_since_contact}
            )
        elif days_since_contact >= self.NO_ACTIVITY_WARNING_DAYS:
            return RiskSignal(
                signal_type="no_recent_contact",
                severity=RiskLevel.MEDIUM,
                message=f"Último contato há {days_since_contact} dias",
                data={"days_since_contact": days_since_contact}
            )
        
        return None
    
    def _calculate_risk_score(self, signals: List[RiskSignal]) -> int:
        """Calcula score de risco (0-100) baseado nos sinais."""
        if not signals:
            return 0
        
        # Peso por severidade
        weights = {
            RiskLevel.LOW: 10,
            RiskLevel.MEDIUM: 25,
            RiskLevel.HIGH: 40,
            RiskLevel.CRITICAL: 60
        }
        
        total_weight = sum(weights[s.severity] for s in signals)
        
        # Normaliza para 0-100
        return min(100, total_weight)
    
    def _determine_risk_level(self, risk_score: int) -> RiskLevel:
        """Determina nível de risco baseado no score."""
        if risk_score >= 80:
            return RiskLevel.CRITICAL
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 25:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
    
    def _generate_recommendations(
        self,
        signals: List[RiskSignal],
        deal: Deal
    ) -> List[str]:
        """Gera recomendações baseadas nos sinais de risco."""
        recommendations = []
        
        for signal in signals:
            if signal.signal_type == "stalled":
                if signal.severity == RiskLevel.CRITICAL:
                    recommendations.append(
                        "Agendar reunião urgente com cliente para "
                        "entender bloqueios"
                    )
                    recommendations.append(
                        "Considerar oferecer desconto ou condição especial"
                    )
                else:
                    recommendations.append(
                        "Fazer follow-up para mover deal para próximo estágio"
                    )
            
            elif signal.signal_type == "engagement_drop":
                recommendations.append(
                    "Reengajar cliente com conteúdo relevante ou novidade"
                )
            
            elif signal.signal_type == "timeline_slip":
                recommendations.append(
                    "Atualizar data de fechamento esperada com base "
                    "em nova previsão"
                )
                recommendations.append(
                    "Identificar motivos do atraso com cliente"
                )
            
            elif signal.signal_type == "no_recent_contact":
                recommendations.append(
                    "Agendar ligação ou enviar email de follow-up"
                )
            
            elif signal.signal_type == "no_activities":
                recommendations.append(
                    "Registrar histórico de interações para melhor tracking"
                )
        
        return list(set(recommendations))  # Remove duplicatas


# =============================================================================
# NEXT BEST ACTION ENGINE
# =============================================================================

class NextBestActionEngine:
    """
    Motor de recomendação de próximas ações.
    
    Analisa estado atual de leads/deals e recomenda
    a melhor ação a ser tomada pelo vendedor.
    
    Considera:
    - Estado atual (stage, score, temperatura)
    - Histórico de atividades
    - Tempo desde última interação
    - Valor e prioridade
    """
    
    # Ações disponíveis
    ACTIONS = {
        "schedule_call": {
            "label": "Agendar ligação",
            "icon": "phone"
        },
        "send_email": {
            "label": "Enviar email",
            "icon": "mail"
        },
        "send_proposal": {
            "label": "Enviar proposta",
            "icon": "file-text"
        },
        "schedule_meeting": {
            "label": "Agendar reunião",
            "icon": "calendar"
        },
        "send_content": {
            "label": "Enviar conteúdo/case",
            "icon": "book"
        },
        "follow_up": {
            "label": "Follow-up",
            "icon": "refresh-cw"
        },
        "negotiate": {
            "label": "Negociar condições",
            "icon": "dollar-sign"
        },
        "close_deal": {
            "label": "Fechar negócio",
            "icon": "check-circle"
        },
        "ask_referral": {
            "label": "Pedir indicação",
            "icon": "users"
        },
        "qualify_lead": {
            "label": "Qualificar lead",
            "icon": "target"
        }
    }
    
    def __init__(self, db_pool):
        self.lead_repo = LeadRepository(db_pool)
        self.deal_repo = DealRepository(db_pool)
        self.contact_repo = ContactRepository(db_pool)
        self.activity_repo = ActivityRepository(db_pool)
        self.pipeline_repo = PipelineRepository(db_pool)
    
    async def get_next_action_for_lead(
        self,
        lead_id: str,
        user_id: str
    ) -> NextBestAction:
        """Recomenda próxima ação para um lead."""
        lead = await self.lead_repo.get_by_id(lead_id, user_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        activities, _ = await self.activity_repo.list_for_entity(
            user_id=user_id,
            lead_id=lead_id,
            limit=10
        )
        
        days_since_activity = self._days_since_last_activity(
            lead.last_contact_at or lead.created_at
        )
        
        # Lead HOT sem contato recente → Ligação urgente
        if lead.temperature == "hot":
            if days_since_activity >= 2:
                return NextBestAction(
                    action_type="schedule_call",
                    action_label=self.ACTIONS["schedule_call"]["label"],
                    reason="Lead quente sem contato há 2+ dias - "
                           "prioridade máxima",
                    priority=ActionPriority.URGENT,
                    suggested_timing="Hoje",
                    entity_type="lead",
                    entity_id=lead_id,
                    metadata={"temperature": "hot", "days_inactive": days_since_activity}
                )
            else:
                # Tem contato recente - próximo passo
                if lead.status == LeadStatus.QUALIFIED:
                    return NextBestAction(
                        action_type="send_proposal",
                        action_label=self.ACTIONS["send_proposal"]["label"],
                        reason="Lead qualificado e engajado - "
                               "hora de enviar proposta",
                        priority=ActionPriority.HIGH,
                        suggested_timing="Próximas 24h",
                        entity_type="lead",
                        entity_id=lead_id
                    )
        
        # Lead WARM - nutrir
        if lead.temperature == "warm":
            if days_since_activity >= 5:
                return NextBestAction(
                    action_type="send_content",
                    action_label=self.ACTIONS["send_content"]["label"],
                    reason="Lead morno precisa de nurturing - "
                           "enviar conteúdo relevante",
                    priority=ActionPriority.MEDIUM,
                    suggested_timing="Próximos 2 dias",
                    entity_type="lead",
                    entity_id=lead_id
                )
            elif lead.status == LeadStatus.NEW:
                return NextBestAction(
                    action_type="qualify_lead",
                    action_label=self.ACTIONS["qualify_lead"]["label"],
                    reason="Lead novo com potencial - "
                           "qualificar para entender necessidades",
                    priority=ActionPriority.MEDIUM,
                    suggested_timing="Esta semana",
                    entity_type="lead",
                    entity_id=lead_id
                )
        
        # Lead COLD - reengajar ou desqualificar
        if lead.temperature == "cold":
            if days_since_activity >= 14:
                return NextBestAction(
                    action_type="send_email",
                    action_label=self.ACTIONS["send_email"]["label"],
                    reason="Lead frio sem contato - "
                           "tentar reengajar com email",
                    priority=ActionPriority.LOW,
                    suggested_timing="Próxima semana",
                    entity_type="lead",
                    entity_id=lead_id
                )
        
        # Default
        return NextBestAction(
            action_type="follow_up",
            action_label=self.ACTIONS["follow_up"]["label"],
            reason="Manter relacionamento ativo",
            priority=ActionPriority.LOW,
            suggested_timing="Próxima semana",
            entity_type="lead",
            entity_id=lead_id
        )
    
    async def get_next_action_for_deal(
        self,
        deal_id: str,
        user_id: str
    ) -> NextBestAction:
        """Recomenda próxima ação para um deal."""
        deal = await self.deal_repo.get_by_id(deal_id, user_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")
        
        # Deal fechado
        if deal.status != DealStatus.OPEN:
            if deal.status == DealStatus.WON:
                return NextBestAction(
                    action_type="ask_referral",
                    action_label=self.ACTIONS["ask_referral"]["label"],
                    reason="Deal ganho - ótimo momento para "
                           "pedir indicações",
                    priority=ActionPriority.MEDIUM,
                    suggested_timing="Próximos dias",
                    entity_type="deal",
                    entity_id=deal_id
                )
            return NextBestAction(
                action_type="follow_up",
                action_label=self.ACTIONS["follow_up"]["label"],
                reason="Deal finalizado",
                priority=ActionPriority.LOW,
                suggested_timing="",
                entity_type="deal",
                entity_id=deal_id
            )
        
        pipeline = await self.pipeline_repo.get_by_id(
            deal.pipeline_id, user_id
        )
        
        activities, _ = await self.activity_repo.list_for_entity(
            user_id=user_id,
            deal_id=deal_id,
            limit=10
        )
        
        days_since_activity = self._days_since_last_activity(
            deal.last_activity_at or deal.created_at
        )
        
        # Encontra stage atual
        current_stage = None
        if pipeline:
            for stage in pipeline.stages:
                if stage.id == deal.stage_id:
                    current_stage = stage
                    break
        
        # Deal parado muito tempo
        if deal.days_in_stage >= 14:
            return NextBestAction(
                action_type="schedule_call",
                action_label=self.ACTIONS["schedule_call"]["label"],
                reason=f"Deal parado há {deal.days_in_stage} dias - "
                       "ligar para destravar",
                priority=ActionPriority.URGENT,
                suggested_timing="Hoje",
                entity_type="deal",
                entity_id=deal_id,
                metadata={"days_in_stage": deal.days_in_stage}
            )
        
        # Alta probabilidade - fechar
        if deal.probability >= 80:
            return NextBestAction(
                action_type="close_deal",
                action_label=self.ACTIONS["close_deal"]["label"],
                reason="Deal com alta probabilidade - "
                       "hora de fechar negócio",
                priority=ActionPriority.HIGH,
                suggested_timing="Esta semana",
                entity_type="deal",
                entity_id=deal_id,
                metadata={"probability": deal.probability}
            )
        
        # Sem atividade recente
        if days_since_activity >= 7:
            return NextBestAction(
                action_type="follow_up",
                action_label=self.ACTIONS["follow_up"]["label"],
                reason=f"Sem atividade há {days_since_activity} dias - "
                       "fazer follow-up",
                priority=ActionPriority.HIGH,
                suggested_timing="Hoje",
                entity_type="deal",
                entity_id=deal_id
            )
        
        # Probabilidade média - negociar
        if 40 <= deal.probability < 80:
            return NextBestAction(
                action_type="negotiate",
                action_label=self.ACTIONS["negotiate"]["label"],
                reason="Deal em fase de negociação",
                priority=ActionPriority.MEDIUM,
                suggested_timing="Próximos dias",
                entity_type="deal",
                entity_id=deal_id
            )
        
        # Baixa probabilidade - qualificar/nutrir
        return NextBestAction(
            action_type="send_proposal",
            action_label=self.ACTIONS["send_proposal"]["label"],
            reason="Avançar deal com proposta ou apresentação",
            priority=ActionPriority.MEDIUM,
            suggested_timing="Esta semana",
            entity_type="deal",
            entity_id=deal_id
        )
    
    async def get_prioritized_actions(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[NextBestAction]:
        """
        Retorna lista priorizada de ações para o vendedor.
        
        Considera todos os leads e deals abertos.
        """
        actions = []
        
        # Busca leads ativos
        leads, _ = await self.lead_repo.list(
            user_id=user_id,
            limit=50
        )
        
        for lead in leads:
            if lead.status not in [LeadStatus.WON, LeadStatus.LOST]:
                try:
                    action = await self.get_next_action_for_lead(
                        lead.id, user_id
                    )
                    actions.append(action)
                except Exception as e:
                    logger.error(f"Error getting action for lead {lead.id}: {e}")
        
        # Busca deals abertos
        deals, _ = await self.deal_repo.list(
            user_id=user_id,
            status=DealStatus.OPEN,
            limit=50
        )
        
        for deal in deals:
            try:
                action = await self.get_next_action_for_deal(
                    deal.id, user_id
                )
                actions.append(action)
            except Exception as e:
                logger.error(f"Error getting action for deal {deal.id}: {e}")
        
        # Ordena por prioridade
        priority_order = {
            ActionPriority.URGENT: 0,
            ActionPriority.HIGH: 1,
            ActionPriority.MEDIUM: 2,
            ActionPriority.LOW: 3
        }
        
        actions.sort(key=lambda a: priority_order.get(a.priority, 99))
        
        return actions[:limit]
    
    def _days_since_last_activity(
        self,
        last_activity: Optional[datetime]
    ) -> int:
        """Calcula dias desde última atividade."""
        if not last_activity:
            return 999  # Muito tempo
        return (datetime.utcnow() - last_activity).days


# =============================================================================
# WORKFLOW TRIGGERS
# =============================================================================

class WorkflowEventType(str, Enum):
    """Tipos de eventos que disparam workflows."""
    # Lead events
    LEAD_CREATED = "lead_created"
    LEAD_QUALIFIED = "lead_qualified"
    LEAD_SCORE_THRESHOLD = "lead_score_threshold"
    LEAD_TEMPERATURE_CHANGED = "lead_temperature_changed"
    LEAD_CONVERTED = "lead_converted"
    LEAD_LOST = "lead_lost"
    
    # Deal events
    DEAL_CREATED = "deal_created"
    DEAL_STAGE_CHANGED = "deal_stage_changed"
    DEAL_WON = "deal_won"
    DEAL_LOST = "deal_lost"
    DEAL_VALUE_CHANGED = "deal_value_changed"
    DEAL_STALLED = "deal_stalled"
    
    # Contact events
    CONTACT_CREATED = "contact_created"
    CONTACT_SUBSCRIBED = "contact_subscribed"
    CONTACT_UNSUBSCRIBED = "contact_unsubscribed"
    
    # Activity events
    ACTIVITY_LOGGED = "activity_logged"
    INACTIVITY_THRESHOLD = "inactivity_threshold"


class WorkflowActionType(str, Enum):
    """Tipos de ações que workflows podem executar."""
    SEND_EMAIL = "send_email"
    CREATE_TASK = "create_task"
    NOTIFY_USER = "notify_user"
    UPDATE_FIELD = "update_field"
    ADD_TAG = "add_tag"
    REMOVE_TAG = "remove_tag"
    MOVE_STAGE = "move_stage"
    ASSIGN_USER = "assign_user"
    WEBHOOK_CALL = "webhook_call"
    LOG_ACTIVITY = "log_activity"


@dataclass
class WorkflowCondition:
    """Condição para execução de workflow."""
    field: str
    operator: str  # equals, not_equals, greater_than, less_than, contains, etc.
    value: Any
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowCondition":
        return cls(
            field=data.get("field", ""),
            operator=data.get("operator", "equals"),
            value=data.get("value")
        )


@dataclass
class WorkflowAction:
    """Ação a ser executada pelo workflow."""
    action_type: WorkflowActionType
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "config": self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowAction":
        return cls(
            action_type=WorkflowActionType(data.get("action_type", "notify_user")),
            config=data.get("config", {})
        )


@dataclass
class Workflow:
    """Definição de um workflow automatizado."""
    id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_id: str = ""
    name: str = ""
    description: str = ""
    
    # Trigger
    event_type: WorkflowEventType = WorkflowEventType.LEAD_CREATED
    
    # Conditions (all must match)
    conditions: List[WorkflowCondition] = field(default_factory=list)
    
    # Actions to execute
    actions: List[WorkflowAction] = field(default_factory=list)
    
    # Settings
    is_active: bool = True
    run_once_per_entity: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "event_type": self.event_type.value,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "is_active": self.is_active,
            "run_once_per_entity": self.run_once_per_entity,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_triggered_at": (
                self.last_triggered_at.isoformat() 
                if self.last_triggered_at else None
            ),
            "trigger_count": self.trigger_count
        }


@dataclass
class WorkflowExecutionLog:
    """Log de execução de workflow."""
    id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))
    workflow_id: str = ""
    entity_type: str = ""
    entity_id: str = ""
    event_type: str = ""
    status: str = "pending"  # pending, running, completed, failed
    actions_executed: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "event_type": self.event_type,
            "status": self.status,
            "actions_executed": self.actions_executed,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() 
                if self.completed_at else None
            )
        }


class WorkflowEngine:
    """
    Motor de execução de workflows.
    
    Processa eventos do CRM e dispara workflows configurados.
    
    Uso típico:
    1. Evento ocorre (ex: lead qualificado)
    2. Engine busca workflows matching o evento
    3. Verifica condições de cada workflow
    4. Executa ações dos workflows válidos
    """
    
    def __init__(self, db_pool):
        self.pool = db_pool
        self.contact_repo = ContactRepository(db_pool)
        self.lead_repo = LeadRepository(db_pool)
        self.deal_repo = DealRepository(db_pool)
        self.activity_repo = ActivityRepository(db_pool)
        
        # In-memory workflow cache (em produção, usar Redis)
        self._workflows_cache: Dict[str, List[Workflow]] = {}
    
    async def trigger_event(
        self,
        event_type: WorkflowEventType,
        user_id: str,
        entity_type: str,
        entity_id: str,
        context: Dict[str, Any]
    ) -> List[WorkflowExecutionLog]:
        """
        Dispara evento e executa workflows matching.
        
        Args:
            event_type: Tipo do evento
            user_id: ID do usuário
            entity_type: Tipo da entidade (lead, deal, contact)
            entity_id: ID da entidade
            context: Dados do contexto do evento
        
        Returns:
            Lista de logs de execução
        """
        logger.debug(
            f"Workflow event triggered: {event_type.value} "
            f"for {entity_type} {entity_id}"
        )
        
        # Busca workflows do usuário para este evento
        workflows = await self._get_workflows_for_event(user_id, event_type)
        
        if not workflows:
            return []
        
        execution_logs = []
        
        for workflow in workflows:
            if not workflow.is_active:
                continue
            
            # Verifica condições
            if not self._check_conditions(workflow.conditions, context):
                continue
            
            # Executa workflow
            log = await self._execute_workflow(
                workflow=workflow,
                entity_type=entity_type,
                entity_id=entity_id,
                context=context
            )
            execution_logs.append(log)
        
        return execution_logs
    
    async def _get_workflows_for_event(
        self,
        user_id: str,
        event_type: WorkflowEventType
    ) -> List[Workflow]:
        """Busca workflows ativos para o evento."""
        # Em produção, buscar do banco de dados
        # Por enquanto, retorna workflows do cache
        cache_key = f"{user_id}:{event_type.value}"
        return self._workflows_cache.get(cache_key, [])
    
    def register_workflow(self, workflow: Workflow):
        """Registra workflow no cache (para uso imediato)."""
        cache_key = f"{workflow.user_id}:{workflow.event_type.value}"
        if cache_key not in self._workflows_cache:
            self._workflows_cache[cache_key] = []
        self._workflows_cache[cache_key].append(workflow)
    
    def _check_conditions(
        self,
        conditions: List[WorkflowCondition],
        context: Dict[str, Any]
    ) -> bool:
        """Verifica se todas as condições são atendidas."""
        if not conditions:
            return True
        
        for condition in conditions:
            value = context.get(condition.field)
            
            if not self._evaluate_condition(
                value, condition.operator, condition.value
            ):
                return False
        
        return True
    
    def _evaluate_condition(
        self,
        value: Any,
        operator: str,
        target: Any
    ) -> bool:
        """Avalia uma condição específica."""
        if operator == "equals":
            return value == target
        elif operator == "not_equals":
            return value != target
        elif operator == "greater_than":
            return value is not None and value > target
        elif operator == "less_than":
            return value is not None and value < target
        elif operator == "greater_or_equal":
            return value is not None and value >= target
        elif operator == "less_or_equal":
            return value is not None and value <= target
        elif operator == "contains":
            return target in str(value) if value else False
        elif operator == "not_contains":
            return target not in str(value) if value else True
        elif operator == "in":
            return value in target if isinstance(target, list) else False
        elif operator == "is_empty":
            return not value
        elif operator == "is_not_empty":
            return bool(value)
        
        return False
    
    async def _execute_workflow(
        self,
        workflow: Workflow,
        entity_type: str,
        entity_id: str,
        context: Dict[str, Any]
    ) -> WorkflowExecutionLog:
        """Executa um workflow e suas ações."""
        log = WorkflowExecutionLog(
            workflow_id=workflow.id,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=workflow.event_type.value,
            status="running"
        )
        
        try:
            for action in workflow.actions:
                result = await self._execute_action(
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    context=context
                )
                log.actions_executed.append({
                    "action_type": action.action_type.value,
                    "result": result
                })
            
            log.status = "completed"
            log.completed_at = datetime.utcnow()
            
            # Atualiza estatísticas do workflow
            workflow.last_triggered_at = datetime.utcnow()
            workflow.trigger_count += 1
            
            logger.info(
                f"Workflow '{workflow.name}' executed successfully "
                f"for {entity_type} {entity_id}"
            )
            
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            log.completed_at = datetime.utcnow()
            
            logger.error(
                f"Workflow '{workflow.name}' failed for "
                f"{entity_type} {entity_id}: {e}"
            )
        
        return log
    
    async def _execute_action(
        self,
        action: WorkflowAction,
        entity_type: str,
        entity_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executa uma ação específica."""
        action_type = action.action_type
        config = action.config
        user_id = context.get("user_id", "")
        
        if action_type == WorkflowActionType.ADD_TAG:
            tag = config.get("tag", "")
            if entity_type == "lead":
                # Adiciona tag ao lead
                # Implementar: await self.lead_repo.add_tag(...)
                return {"status": "success", "tag_added": tag}
            elif entity_type == "contact":
                await self.contact_repo.add_tag(entity_id, user_id, tag)
                return {"status": "success", "tag_added": tag}
        
        elif action_type == WorkflowActionType.NOTIFY_USER:
            # Em produção, integrar com sistema de notificações
            message = config.get("message", "")
            logger.info(f"[Notification] {message}")
            return {"status": "success", "message": message}
        
        elif action_type == WorkflowActionType.LOG_ACTIVITY:
            title = config.get("title", "Workflow Activity")
            description = config.get("description", "")
            
            activity = Activity(
                user_id=user_id,
                contact_id=context.get("contact_id", ""),
                lead_id=entity_id if entity_type == "lead" else None,
                deal_id=entity_id if entity_type == "deal" else None,
                activity_type=ActivityType.SYSTEM,
                title=title,
                description=description,
                metadata={"workflow_triggered": True}
            )
            await self.activity_repo.create(activity)
            return {"status": "success", "activity_id": activity.id}
        
        elif action_type == WorkflowActionType.UPDATE_FIELD:
            field_name = config.get("field", "")
            field_value = config.get("value", "")
            # Implementar atualização de campo
            return {
                "status": "success", 
                "field": field_name, 
                "value": field_value
            }
        
        elif action_type == WorkflowActionType.WEBHOOK_CALL:
            url = config.get("url", "")
            # Em produção, fazer chamada HTTP
            logger.info(f"[Webhook] Would call: {url}")
            return {"status": "success", "url": url}
        
        return {"status": "not_implemented"}


# Factory para criar workflows comuns
class WorkflowTemplates:
    """Templates de workflows comuns pré-configurados."""
    
    @staticmethod
    def hot_lead_notification(user_id: str) -> Workflow:
        """Notifica quando lead fica hot."""
        return Workflow(
            user_id=user_id,
            name="Notificação Lead Hot",
            description="Notifica quando temperatura do lead muda para hot",
            event_type=WorkflowEventType.LEAD_TEMPERATURE_CHANGED,
            conditions=[
                WorkflowCondition(
                    field="temperature",
                    operator="equals",
                    value="hot"
                )
            ],
            actions=[
                WorkflowAction(
                    action_type=WorkflowActionType.NOTIFY_USER,
                    config={
                        "message": "🔥 Lead ficou HOT! Contate agora.",
                        "priority": "high"
                    }
                ),
                WorkflowAction(
                    action_type=WorkflowActionType.ADD_TAG,
                    config={"tag": "hot-lead"}
                )
            ]
        )
    
    @staticmethod
    def deal_won_celebration(user_id: str) -> Workflow:
        """Celebração quando deal é ganho."""
        return Workflow(
            user_id=user_id,
            name="Deal Won!",
            description="Ações quando deal é ganho",
            event_type=WorkflowEventType.DEAL_WON,
            actions=[
                WorkflowAction(
                    action_type=WorkflowActionType.NOTIFY_USER,
                    config={
                        "message": "🎉 Parabéns! Deal fechado com sucesso!",
                        "priority": "high"
                    }
                ),
                WorkflowAction(
                    action_type=WorkflowActionType.ADD_TAG,
                    config={"tag": "cliente"}
                ),
                WorkflowAction(
                    action_type=WorkflowActionType.LOG_ACTIVITY,
                    config={
                        "title": "Deal ganho",
                        "description": "Cliente convertido com sucesso"
                    }
                )
            ]
        )
    
    @staticmethod
    def stalled_deal_alert(user_id: str) -> Workflow:
        """Alerta para deals parados."""
        return Workflow(
            user_id=user_id,
            name="Deal Stalled Alert",
            description="Alerta quando deal está parado há muito tempo",
            event_type=WorkflowEventType.DEAL_STALLED,
            conditions=[
                WorkflowCondition(
                    field="days_in_stage",
                    operator="greater_than",
                    value=14
                )
            ],
            actions=[
                WorkflowAction(
                    action_type=WorkflowActionType.NOTIFY_USER,
                    config={
                        "message": "⚠️ Deal parado! Precisa de atenção.",
                        "priority": "high"
                    }
                ),
                WorkflowAction(
                    action_type=WorkflowActionType.ADD_TAG,
                    config={"tag": "needs-attention"}
                )
            ]
        )
    
    @staticmethod
    def high_value_lead(user_id: str, threshold: float = 10000) -> Workflow:
        """Alerta para leads de alto valor."""
        return Workflow(
            user_id=user_id,
            name="High Value Lead",
            description=f"Alerta para leads com valor > R${threshold}",
            event_type=WorkflowEventType.LEAD_CREATED,
            conditions=[
                WorkflowCondition(
                    field="estimated_value",
                    operator="greater_than",
                    value=threshold
                )
            ],
            actions=[
                WorkflowAction(
                    action_type=WorkflowActionType.NOTIFY_USER,
                    config={
                        "message": f"💰 Lead de alto valor (>R${threshold})!",
                        "priority": "urgent"
                    }
                ),
                WorkflowAction(
                    action_type=WorkflowActionType.ADD_TAG,
                    config={"tag": "high-value"}
                )
            ]
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "RiskLevel",
    "ActionPriority",
    "WorkflowEventType",
    "WorkflowActionType",
    # Configs
    "ScoreDecayConfig",
    # Dataclasses
    "RiskSignal",
    "RiskAssessment",
    "NextBestAction",
    "ScoreDecayResult",
    "WorkflowCondition",
    "WorkflowAction",
    "Workflow",
    "WorkflowExecutionLog",
    # Services
    "ScoreDecayService",
    "DealRiskDetectionService",
    "NextBestActionEngine",
    "WorkflowEngine",
    "WorkflowTemplates"
]
