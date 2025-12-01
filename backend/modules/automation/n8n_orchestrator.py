"""
N8N Automation Orchestrator
============================
Orquestrador central para automações do Seller Bot com n8n.

Funcionalidades:
- Disparar workflows automaticamente baseado em eventos
- Lead nurturing sequences
- Recuperação de carrinho abandonado
- Follow-ups pós-venda
- Alertas de preço e estoque
- Integração multi-canal (WhatsApp, Instagram, Email)

Uso:
    orchestrator = N8nOrchestrator()
    
    # Disparar automação de boas-vindas
    await orchestrator.trigger_onboarding(user_id="123", channel="whatsapp")
    
    # Agendar follow-up
    await orchestrator.schedule_followup(
        lead_id="lead_123",
        delay_hours=24,
        template="interest_check"
    )
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4

from pydantic import BaseModel, Field

from integrations.n8n import N8nClient, get_n8n_client, TriggerType
from shared.config import settings

logger = logging.getLogger(__name__)


# ============================================
# ENUMS E CONFIGURAÇÕES
# ============================================

class AutomationType(str, Enum):
    """Tipos de automação disponíveis."""
    # Onboarding
    NEW_USER_WELCOME = "new_user_welcome"
    NEW_LEAD_NURTURING = "new_lead_nurturing"
    
    # Sales
    CART_ABANDONED = "cart_abandoned"
    PRICE_DROP_ALERT = "price_drop_alert"
    STOCK_LOW_ALERT = "stock_low_alert"
    PRODUCT_AVAILABLE = "product_available"
    
    # Follow-up
    POST_PURCHASE_THANKS = "post_purchase_thanks"
    REVIEW_REQUEST = "review_request"
    CROSS_SELL = "cross_sell"
    UPSELL = "upsell"
    
    # Re-engagement
    INACTIVE_USER = "inactive_user"
    BIRTHDAY_GREETING = "birthday_greeting"
    ANNIVERSARY_DISCOUNT = "anniversary_discount"
    
    # Support
    TICKET_CREATED = "ticket_created"
    TICKET_RESOLVED = "ticket_resolved"
    NPS_SURVEY = "nps_survey"
    COMPLAINT_ALERT = "complaint_alert"
    HUMAN_HANDOFF = "human_handoff"
    
    # Social
    NEW_POST_SCHEDULED = "new_post_scheduled"
    POST_PUBLISHED = "post_published"
    ENGAGEMENT_SPIKE = "engagement_spike"
    
    # CRM
    LEAD_QUALIFIED = "lead_qualified"
    DEAL_WON = "deal_won"
    DEAL_LOST = "deal_lost"


class ChannelType(str, Enum):
    """Canais de comunicação."""
    WHATSAPP = "whatsapp"
    INSTAGRAM_DM = "instagram_dm"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class AutomationPriority(str, Enum):
    """Prioridade de execução."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ============================================
# MODELOS
# ============================================

class AutomationConfig(BaseModel):
    """Configuração de uma automação."""
    automation_type: AutomationType
    enabled: bool = True
    channels: List[ChannelType] = Field(default_factory=lambda: [ChannelType.WHATSAPP])
    delay_minutes: int = 0
    priority: AutomationPriority = AutomationPriority.NORMAL
    
    # Webhook n8n
    webhook_path: str
    
    # Condições
    min_delay_between_triggers_hours: int = 24
    max_triggers_per_user_per_day: int = 3
    
    # Horários permitidos (evitar enviar de madrugada)
    allowed_hours_start: int = 8
    allowed_hours_end: int = 22
    
    # Templates
    templates: Dict[str, str] = Field(default_factory=dict)


class AutomationEvent(BaseModel):
    """Evento que dispara uma automação."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    automation_type: AutomationType
    user_id: str
    channel: ChannelType = ChannelType.WHATSAPP
    
    # Dados do evento
    data: Dict[str, Any] = Field(default_factory=dict)
    
    # Controle
    scheduled_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    status: str = "pending"  # pending, executed, failed, cancelled
    
    # Resultado
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AutomationResult(BaseModel):
    """Resultado de uma automação executada."""
    event_id: str
    success: bool
    n8n_response: Optional[Dict[str, Any]] = None
    message_sent: bool = False
    error: Optional[str] = None
    executed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# CONFIGURAÇÕES PRÉ-DEFINIDAS
# ============================================

DEFAULT_AUTOMATIONS: Dict[AutomationType, AutomationConfig] = {
    AutomationType.NEW_USER_WELCOME: AutomationConfig(
        automation_type=AutomationType.NEW_USER_WELCOME,
        webhook_path="/didin/new-user",
        channels=[ChannelType.WHATSAPP, ChannelType.EMAIL],
        delay_minutes=0,
        priority=AutomationPriority.HIGH,
        templates={
            "whatsapp": "Olá {name}! 🎉 Bem-vindo ao Didin Fácil! Sou seu assistente virtual e vou te ajudar a encontrar os melhores produtos com os melhores preços. O que você está procurando hoje?",
            "email": "Bem-vindo ao Didin Fácil, {name}!",
        }
    ),
    
    AutomationType.NEW_LEAD_NURTURING: AutomationConfig(
        automation_type=AutomationType.NEW_LEAD_NURTURING,
        webhook_path="/didin/lead-nurture",
        channels=[ChannelType.WHATSAPP],
        delay_minutes=60,  # 1 hora após primeiro contato
        priority=AutomationPriority.NORMAL,
        templates={
            "whatsapp": "Oi {name}! Vi que você estava interessado em {product}. Encontrei algumas ofertas especiais pra você! 🔥 Quer que eu te mostre?",
        }
    ),
    
    AutomationType.CART_ABANDONED: AutomationConfig(
        automation_type=AutomationType.CART_ABANDONED,
        webhook_path="/didin/cart-abandoned",
        channels=[ChannelType.WHATSAPP, ChannelType.EMAIL],
        delay_minutes=120,  # 2 horas
        priority=AutomationPriority.HIGH,
        min_delay_between_triggers_hours=8,
        templates={
            "whatsapp": "Ei {name}! 🛒 Vi que você esqueceu alguns produtos no carrinho. {product_name} ainda está disponível com desconto especial! Quer finalizar a compra?",
        }
    ),
    
    AutomationType.PRICE_DROP_ALERT: AutomationConfig(
        automation_type=AutomationType.PRICE_DROP_ALERT,
        webhook_path="/didin/price-drop",
        channels=[ChannelType.WHATSAPP, ChannelType.EMAIL, ChannelType.PUSH],
        delay_minutes=0,
        priority=AutomationPriority.URGENT,
        templates={
            "whatsapp": "🔥 ALERTA DE PREÇO! O {product_name} que você estava de olho baixou de R${old_price} para R${new_price}! É {discount}% OFF! 👉 {product_url}",
        }
    ),
    
    AutomationType.POST_PURCHASE_THANKS: AutomationConfig(
        automation_type=AutomationType.POST_PURCHASE_THANKS,
        webhook_path="/didin/post-purchase",
        channels=[ChannelType.WHATSAPP],
        delay_minutes=30,
        priority=AutomationPriority.NORMAL,
        templates={
            "whatsapp": "Obrigado pela compra, {name}! 🙏 Seu pedido #{order_id} foi confirmado. Vou te avisar quando sair pra entrega. Qualquer dúvida, é só me chamar!",
        }
    ),
    
    AutomationType.REVIEW_REQUEST: AutomationConfig(
        automation_type=AutomationType.REVIEW_REQUEST,
        webhook_path="/didin/review-request",
        channels=[ChannelType.WHATSAPP, ChannelType.EMAIL],
        delay_minutes=10080,  # 7 dias
        priority=AutomationPriority.LOW,
        min_delay_between_triggers_hours=168,  # 1 semana
        templates={
            "whatsapp": "Oi {name}! Tudo bem? Como foi sua experiência com o {product_name}? Adoraríamos saber sua opinião! ⭐ Pode deixar uma avaliação?",
        }
    ),
    
    AutomationType.CROSS_SELL: AutomationConfig(
        automation_type=AutomationType.CROSS_SELL,
        webhook_path="/didin/cross-sell",
        channels=[ChannelType.WHATSAPP],
        delay_minutes=4320,  # 3 dias
        priority=AutomationPriority.LOW,
        templates={
            "whatsapp": "Oi {name}! Como você comprou {product_name}, separei algumas sugestões que combinam perfeitamente: {suggestions}. Quer dar uma olhada?",
        }
    ),
    
    AutomationType.INACTIVE_USER: AutomationConfig(
        automation_type=AutomationType.INACTIVE_USER,
        webhook_path="/didin/reengagement",
        channels=[ChannelType.WHATSAPP, ChannelType.EMAIL],
        delay_minutes=0,
        priority=AutomationPriority.LOW,
        min_delay_between_triggers_hours=168,  # 1 semana
        templates={
            "whatsapp": "Oi {name}! Senti sua falta! 😊 Temos novidades incríveis e ofertas exclusivas esperando por você. Quer ver o que tem de novo?",
        }
    ),
    
    AutomationType.LEAD_QUALIFIED: AutomationConfig(
        automation_type=AutomationType.LEAD_QUALIFIED,
        webhook_path="/didin/lead-qualified",
        channels=[ChannelType.WHATSAPP],
        delay_minutes=0,
        priority=AutomationPriority.HIGH,
        templates={
            "whatsapp": "Oi {name}! Vi que você está super interessado. Tenho uma oferta especial exclusiva pra você! Quer que eu te mostre os detalhes?",
        }
    ),
    
    AutomationType.DEAL_WON: AutomationConfig(
        automation_type=AutomationType.DEAL_WON,
        webhook_path="/didin/deal-won",
        channels=[ChannelType.WHATSAPP, ChannelType.EMAIL],
        delay_minutes=0,
        priority=AutomationPriority.HIGH,
        templates={
            "whatsapp": "🎉 PARABÉNS! Seu pedido foi confirmado!",
        }
    ),

    AutomationType.COMPLAINT_ALERT: AutomationConfig(
        automation_type=AutomationType.COMPLAINT_ALERT,
        webhook_path="/didin/complaint-alert",
        channels=[ChannelType.EMAIL],  # Notifica equipe interna
        delay_minutes=0,
        priority=AutomationPriority.URGENT,
        templates={
            "email": "⚠️ Nova reclamação de {name}: {complaint}",
        }
    ),

    AutomationType.HUMAN_HANDOFF: AutomationConfig(
        automation_type=AutomationType.HUMAN_HANDOFF,
        webhook_path="/didin/handoff",
        channels=[ChannelType.EMAIL],  # Notifica atendente
        delay_minutes=0,
        priority=AutomationPriority.HIGH,
        templates={
            "email": "🔔 Handoff solicitado: {name} - {reason}",
        }
    ),
}


# ============================================
# ORCHESTRATOR PRINCIPAL
# ============================================

class N8nOrchestrator:
    """
    Orquestrador de automações com n8n.
    
    Gerencia o ciclo de vida de automações:
    1. Recebe eventos (novo lead, carrinho abandonado, etc.)
    2. Determina qual automação disparar
    3. Verifica regras de rate limiting
    4. Dispara webhook n8n
    5. Monitora resultados
    """
    
    def __init__(
        self,
        n8n_client: Optional[N8nClient] = None,
        automations: Optional[Dict[AutomationType, AutomationConfig]] = None
    ):
        self.n8n = n8n_client or get_n8n_client()
        self.automations = automations or DEFAULT_AUTOMATIONS.copy()
        
        # Cache de eventos recentes (para rate limiting)
        self._event_cache: Dict[str, List[datetime]] = {}
        
        # Fila de eventos pendentes
        self._pending_events: List[AutomationEvent] = []
        
        logger.info("N8nOrchestrator inicializado com %d automações", len(self.automations))
    
    # ========================================
    # TRIGGERS PRINCIPAIS
    # ========================================
    
    async def trigger_automation(
        self,
        automation_type: AutomationType,
        user_id: str,
        data: Dict[str, Any],
        channel: ChannelType = ChannelType.WHATSAPP,
        force: bool = False
    ) -> AutomationResult:
        """
        Dispara uma automação.
        
        Args:
            automation_type: Tipo de automação
            user_id: ID do usuário
            data: Dados do evento
            channel: Canal de comunicação
            force: Ignorar rate limiting
        
        Returns:
            AutomationResult com status da execução
        """
        config = self.automations.get(automation_type)
        
        if not config:
            return AutomationResult(
                event_id="",
                success=False,
                error=f"Automação {automation_type} não configurada"
            )
        
        if not config.enabled:
            return AutomationResult(
                event_id="",
                success=False,
                error=f"Automação {automation_type} desabilitada"
            )
        
        # Verificar rate limiting
        if not force and not self._check_rate_limit(user_id, automation_type, config):
            return AutomationResult(
                event_id="",
                success=False,
                error="Rate limit atingido"
            )
        
        # Verificar horário permitido
        if not self._check_allowed_hours(config):
            # Agendar para próximo horário permitido
            event = AutomationEvent(
                automation_type=automation_type,
                user_id=user_id,
                channel=channel,
                data=data,
                scheduled_at=self._get_next_allowed_time(config)
            )
            self._pending_events.append(event)
            return AutomationResult(
                event_id=event.id,
                success=True,
                message_sent=False,
                error="Agendado para horário permitido"
            )
        
        # Criar evento
        event = AutomationEvent(
            automation_type=automation_type,
            user_id=user_id,
            channel=channel,
            data=data
        )
        
        # Aplicar delay se configurado
        if config.delay_minutes > 0:
            event.scheduled_at = datetime.utcnow() + timedelta(minutes=config.delay_minutes)
            self._pending_events.append(event)
            return AutomationResult(
                event_id=event.id,
                success=True,
                message_sent=False,
                error=f"Agendado para {config.delay_minutes} minutos"
            )
        
        # Executar imediatamente
        return await self._execute_automation(event, config)
    
    async def _execute_automation(
        self,
        event: AutomationEvent,
        config: AutomationConfig
    ) -> AutomationResult:
        """Executa a automação disparando webhook n8n."""
        try:
            # Preparar payload
            payload = {
                "event_id": event.id,
                "automation_type": event.automation_type.value,
                "user_id": event.user_id,
                "channel": event.channel.value,
                "data": event.data,
                "template": config.templates.get(event.channel.value, ""),
                "priority": config.priority.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Disparar webhook n8n
            response = await self.n8n.trigger_webhook(
                webhook_path=config.webhook_path,
                data=payload
            )
            
            # Atualizar cache de rate limiting
            self._update_rate_limit_cache(event.user_id, event.automation_type)
            
            # Marcar evento como executado
            event.executed_at = datetime.utcnow()
            event.status = "executed"
            event.result = response
            
            logger.info(
                "Automação %s executada para user %s via %s",
                event.automation_type.value, event.user_id, event.channel.value
            )
            
            return AutomationResult(
                event_id=event.id,
                success=True,
                n8n_response=response,
                message_sent=True
            )
            
        except Exception as e:
            logger.error("Erro ao executar automação: %s", e)
            event.status = "failed"
            event.error = str(e)
            
            return AutomationResult(
                event_id=event.id,
                success=False,
                error=str(e)
            )
    
    # ========================================
    # MÉTODOS DE CONVENIÊNCIA
    # ========================================
    
    async def trigger_onboarding(
        self,
        user_id: str,
        name: str,
        channel: ChannelType = ChannelType.WHATSAPP,
        phone: Optional[str] = None,
        email: Optional[str] = None
    ) -> AutomationResult:
        """Dispara sequência de onboarding para novo usuário."""
        return await self.trigger_automation(
            AutomationType.NEW_USER_WELCOME,
            user_id=user_id,
            data={
                "name": name,
                "phone": phone,
                "email": email,
                "source": "seller_bot"
            },
            channel=channel
        )
    
    async def trigger_cart_abandoned(
        self,
        user_id: str,
        name: str,
        product_name: str,
        product_url: str,
        price: float,
        channel: ChannelType = ChannelType.WHATSAPP
    ) -> AutomationResult:
        """Dispara recuperação de carrinho abandonado."""
        return await self.trigger_automation(
            AutomationType.CART_ABANDONED,
            user_id=user_id,
            data={
                "name": name,
                "product_name": product_name,
                "product_url": product_url,
                "price": price
            },
            channel=channel
        )
    
    async def trigger_price_drop(
        self,
        user_id: str,
        name: str,
        product_name: str,
        product_url: str,
        old_price: float,
        new_price: float,
        channel: ChannelType = ChannelType.WHATSAPP
    ) -> AutomationResult:
        """Dispara alerta de queda de preço."""
        discount = round((1 - new_price / old_price) * 100)
        
        return await self.trigger_automation(
            AutomationType.PRICE_DROP_ALERT,
            user_id=user_id,
            data={
                "name": name,
                "product_name": product_name,
                "product_url": product_url,
                "old_price": old_price,
                "new_price": new_price,
                "discount": discount
            },
            channel=channel,
            force=True  # Alertas de preço são importantes
        )
    
    async def trigger_post_purchase(
        self,
        user_id: str,
        name: str,
        order_id: str,
        product_name: str,
        total: float,
        channel: ChannelType = ChannelType.WHATSAPP
    ) -> AutomationResult:
        """Dispara agradecimento pós-compra."""
        return await self.trigger_automation(
            AutomationType.POST_PURCHASE_THANKS,
            user_id=user_id,
            data={
                "name": name,
                "order_id": order_id,
                "product_name": product_name,
                "total": total
            },
            channel=channel
        )
    
    async def trigger_lead_qualified(
        self,
        user_id: str,
        name: str,
        lead_score: int,
        interested_products: List[str],
        channel: ChannelType = ChannelType.WHATSAPP
    ) -> AutomationResult:
        """Dispara automação para lead qualificado."""
        return await self.trigger_automation(
            AutomationType.LEAD_QUALIFIED,
            user_id=user_id,
            data={
                "name": name,
                "lead_score": lead_score,
                "interested_products": interested_products
            },
            channel=channel
        )
    
    async def trigger_review_request(
        self,
        user_id: str,
        name: str,
        order_id: str,
        product_name: str,
        days_since_delivery: int = 7,
        channel: ChannelType = ChannelType.WHATSAPP
    ) -> AutomationResult:
        """Solicita avaliação do produto."""
        return await self.trigger_automation(
            AutomationType.REVIEW_REQUEST,
            user_id=user_id,
            data={
                "name": name,
                "order_id": order_id,
                "product_name": product_name,
                "days_since_delivery": days_since_delivery
            },
            channel=channel
        )
    
    async def trigger_reengagement(
        self,
        user_id: str,
        name: str,
        days_inactive: int,
        last_product_viewed: Optional[str] = None,
        channel: ChannelType = ChannelType.WHATSAPP
    ) -> AutomationResult:
        """Dispara campanha de reengajamento."""
        return await self.trigger_automation(
            AutomationType.INACTIVE_USER,
            user_id=user_id,
            data={
                "name": name,
                "days_inactive": days_inactive,
                "last_product_viewed": last_product_viewed
            },
            channel=channel
        )

    async def trigger_complaint_alert(
        self,
        user_id: str,
        name: str,
        complaint: str,
        channel: ChannelType = ChannelType.WHATSAPP,
        sentiment: str = "unknown",
        priority: str = "medium"
    ) -> AutomationResult:
        """
        Dispara alerta de reclamação para equipe de suporte.

        Notifica via n8n para ação imediata.
        """
        return await self.trigger_automation(
            AutomationType.COMPLAINT_ALERT,
            user_id=user_id,
            data={
                "name": name,
                "complaint": complaint,
                "original_channel": channel.value,
                "sentiment": sentiment,
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat()
            },
            channel=ChannelType.EMAIL,  # Alerta interno
            force=True  # Sempre notificar reclamações
        )

    async def trigger_human_handoff(
        self,
        user_id: str,
        name: str,
        reason: str,
        context_summary: str,
        channel: ChannelType = ChannelType.WHATSAPP,
        lead_score: int = 0
    ) -> AutomationResult:
        """
        Dispara handoff para atendimento humano.

        Envia contexto completo para o atendente.
        """
        return await self.trigger_automation(
            AutomationType.HUMAN_HANDOFF,
            user_id=user_id,
            data={
                "name": name,
                "reason": reason,
                "context_summary": context_summary,
                "original_channel": channel.value,
                "lead_score": lead_score,
                "timestamp": datetime.utcnow().isoformat()
            },
            channel=ChannelType.EMAIL,  # Notifica atendente
            force=True
        )
    
    # ========================================
    # RATE LIMITING & SCHEDULING
    # ========================================
    
    def _check_rate_limit(
        self,
        user_id: str,
        automation_type: AutomationType,
        config: AutomationConfig
    ) -> bool:
        """Verifica se pode enviar baseado no rate limit."""
        cache_key = f"{user_id}:{automation_type.value}"
        
        if cache_key not in self._event_cache:
            return True
        
        recent_events = self._event_cache[cache_key]
        now = datetime.utcnow()
        
        # Limpar eventos antigos
        min_time = now - timedelta(hours=config.min_delay_between_triggers_hours)
        recent_events = [e for e in recent_events if e > min_time]
        self._event_cache[cache_key] = recent_events
        
        # Verificar máximo por dia
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_events = [e for e in recent_events if e > today_start]
        
        if len(today_events) >= config.max_triggers_per_user_per_day:
            return False
        
        return len(recent_events) == 0
    
    def _update_rate_limit_cache(self, user_id: str, automation_type: AutomationType):
        """Atualiza cache de rate limiting."""
        cache_key = f"{user_id}:{automation_type.value}"
        
        if cache_key not in self._event_cache:
            self._event_cache[cache_key] = []
        
        self._event_cache[cache_key].append(datetime.utcnow())
    
    def _check_allowed_hours(self, config: AutomationConfig) -> bool:
        """Verifica se está em horário permitido."""
        now = datetime.utcnow()
        # Ajustar para horário de Brasília (UTC-3)
        br_hour = (now.hour - 3) % 24
        
        return config.allowed_hours_start <= br_hour <= config.allowed_hours_end
    
    def _get_next_allowed_time(self, config: AutomationConfig) -> datetime:
        """Calcula próximo horário permitido."""
        now = datetime.utcnow()
        br_hour = (now.hour - 3) % 24
        
        if br_hour < config.allowed_hours_start:
            # Agendar para hoje no horário de início
            delta_hours = config.allowed_hours_start - br_hour
        else:
            # Agendar para amanhã no horário de início
            delta_hours = 24 - br_hour + config.allowed_hours_start
        
        return now + timedelta(hours=delta_hours)
    
    # ========================================
    # GESTÃO DE AUTOMAÇÕES
    # ========================================
    
    def enable_automation(self, automation_type: AutomationType):
        """Habilita uma automação."""
        if automation_type in self.automations:
            self.automations[automation_type].enabled = True
            logger.info("Automação %s habilitada", automation_type.value)
    
    def disable_automation(self, automation_type: AutomationType):
        """Desabilita uma automação."""
        if automation_type in self.automations:
            self.automations[automation_type].enabled = False
            logger.info("Automação %s desabilitada", automation_type.value)
    
    def update_automation_config(
        self,
        automation_type: AutomationType,
        **kwargs
    ):
        """Atualiza configuração de uma automação."""
        if automation_type in self.automations:
            config = self.automations[automation_type]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            logger.info("Automação %s atualizada: %s", automation_type.value, kwargs)
    
    def get_pending_events(self) -> List[AutomationEvent]:
        """Retorna eventos pendentes."""
        now = datetime.utcnow()
        return [
            e for e in self._pending_events
            if e.status == "pending" and e.scheduled_at <= now
        ]
    
    async def process_pending_events(self) -> List[AutomationResult]:
        """Processa eventos pendentes que já podem ser executados."""
        results = []
        pending = self.get_pending_events()
        
        for event in pending:
            config = self.automations.get(event.automation_type)
            if config:
                result = await self._execute_automation(event, config)
                results.append(result)
                self._pending_events.remove(event)
        
        return results
    
    def get_automation_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das automações."""
        stats = {
            "total_automations": len(self.automations),
            "enabled_automations": sum(1 for a in self.automations.values() if a.enabled),
            "pending_events": len(self._pending_events),
            "by_type": {}
        }
        
        for automation_type, config in self.automations.items():
            stats["by_type"][automation_type.value] = {
                "enabled": config.enabled,
                "priority": config.priority.value,
                "channels": [c.value for c in config.channels],
                "delay_minutes": config.delay_minutes
            }
        
        return stats


# ============================================
# SINGLETON
# ============================================

_orchestrator: Optional[N8nOrchestrator] = None


def get_orchestrator() -> N8nOrchestrator:
    """Obtém instância singleton do orchestrator."""
    global _orchestrator
    
    if _orchestrator is None:
        _orchestrator = N8nOrchestrator()
    
    return _orchestrator
