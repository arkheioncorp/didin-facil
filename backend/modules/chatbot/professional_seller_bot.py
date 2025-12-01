"""
Professional Seller Bot - Didin Fácil
======================================
Bot de vendas profissional com IA avançada, CRM integrado e multi-canal.

Features:
- Análise de intenção com IA
- Busca inteligente de produtos
- Qualificação automática de leads
- Integração com CRM
- Analytics em tempo real
- Multi-canal (WhatsApp, Instagram, TikTok)
- Escalonamento para humano
- Memória de contexto
- Automações n8n integradas
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

# Import do orchestrator de automações
try:
    from modules.automation.n8n_orchestrator import AutomationType
    from modules.automation.n8n_orchestrator import \
        ChannelType as AutomationChannel
    from modules.automation.n8n_orchestrator import get_orchestrator
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False
    get_orchestrator = None

logger = logging.getLogger(__name__)


# ============================================
# ENUMS E MODELOS
# ============================================

class MessageChannel(str, Enum):
    """Canais de comunicação suportados."""
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    WEBCHAT = "webchat"
    TELEGRAM = "telegram"


class ConversationStage(str, Enum):
    """Estágios do funil de conversa."""
    NEW = "new"                           # Primeiro contato
    GREETING = "greeting"                 # Saudação inicial
    DISCOVERY = "discovery"               # Descoberta de necessidades
    QUALIFICATION = "qualification"       # Qualificação do lead
    PRODUCT_SEARCH = "product_search"     # Busca de produtos
    PRODUCT_DETAIL = "product_detail"     # Detalhes do produto
    COMPARISON = "comparison"             # Comparação de preços
    OBJECTION = "objection"               # Tratando objeções
    CLOSING = "closing"                   # Fechamento
    SUPPORT = "support"                   # Suporte/pós-venda
    HUMAN_HANDOFF = "human_handoff"       # Escalonado para humano


class Intent(str, Enum):
    """Intenções detectadas nas mensagens."""
    # Saudações
    GREETING = "greeting"
    FAREWELL = "farewell"
    
    # Navegação
    MENU = "menu"
    HELP = "help"
    
    # Produtos
    PRODUCT_SEARCH = "product_search"
    PRODUCT_INFO = "product_info"
    PRICE_CHECK = "price_check"
    COMPARE_PRICES = "compare_prices"
    AVAILABILITY = "availability"
    
    # Compra
    HOW_TO_BUY = "how_to_buy"
    PAYMENT_INFO = "payment_info"
    SHIPPING_INFO = "shipping_info"
    PURCHASE_INTEREST = "purchase_interest"
    ALERT_CREATE = "alert_create"
    CART_ABANDONED_CHECK = "cart_abandoned_check"
    
    # Suporte
    ORDER_STATUS = "order_status"
    COMPLAINT = "complaint"
    REFUND = "refund"
    QUESTION = "question"
    
    # Ações
    TALK_TO_HUMAN = "talk_to_human"
    SCHEDULE = "schedule"
    SUBSCRIBE = "subscribe"
    
    # Contextuais
    AFFIRMATIVE = "affirmative"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


class SentimentType(str, Enum):
    """Tipos de sentimento."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"
    EXCITED = "excited"


class LeadTemperature(str, Enum):
    """Temperatura do lead (quão pronto para comprar)."""
    COLD = "cold"         # Apenas curiosidade
    WARM = "warm"         # Interesse real
    HOT = "hot"           # Pronto para comprar
    QUALIFIED = "qualified"  # Lead qualificado


# ============================================
# MODELOS PYDANTIC
# ============================================

class IncomingMessage(BaseModel):
    """Mensagem recebida do usuário."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    channel: MessageChannel
    sender_id: str
    sender_name: Optional[str] = None
    sender_phone: Optional[str] = None
    content: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None  # image, video, audio, document
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Contexto adicional
    reply_to: Optional[str] = None
    is_group: bool = False
    group_id: Optional[str] = None


class BotResponse(BaseModel):
    """Resposta do bot."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    quick_replies: List[str] = Field(default_factory=list)
    buttons: List[Dict[str, str]] = Field(default_factory=list)
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    delay_ms: int = 0  # Delay antes de enviar (simula digitação)
    
    # Ações
    should_handoff: bool = False
    handoff_reason: Optional[str] = None
    follow_up_action: Optional[str] = None
    
    # Metadados
    intent_detected: Optional[Intent] = None
    confidence: float = 1.0
    generated_by: str = "bot"  # bot, ai, template, human
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationContext(BaseModel):
    """Contexto persistente da conversa."""
    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    channel: MessageChannel
    stage: ConversationStage = ConversationStage.NEW
    
    # Estado
    is_active: bool = True
    last_interaction: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    
    # Informações coletadas
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    user_email: Optional[str] = None
    
    # Lead tracking
    lead_id: Optional[str] = None
    lead_temperature: LeadTemperature = LeadTemperature.COLD
    lead_score: int = 0
    
    # Produtos de interesse
    interested_products: List[str] = Field(default_factory=list)
    search_history: List[str] = Field(default_factory=list)
    last_product_viewed: Optional[Dict[str, Any]] = None
    
    # Histórico resumido
    intents_detected: List[str] = Field(default_factory=list)
    sentiment_history: List[str] = Field(default_factory=list)
    
    # CRM
    crm_contact_id: Optional[str] = None
    crm_deal_id: Optional[str] = None
    
    # Variáveis customizadas
    variables: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IntentAnalysis(BaseModel):
    """Resultado da análise de intenção."""
    intent: Intent
    confidence: float
    entities: Dict[str, Any] = Field(default_factory=dict)  # produto, preço, etc.
    sentiment: SentimentType = SentimentType.NEUTRAL
    sentiment_score: float = 0.5
    keywords: List[str] = Field(default_factory=list)
    suggested_stage: Optional[ConversationStage] = None
    requires_ai: bool = False


# ============================================
# INTENT DETECTOR (RULE-BASED + KEYWORDS)
# ============================================

class IntentDetector:
    """
    Detector de intenções baseado em regras e keywords.
    Funciona offline como primeira camada antes da IA.
    """
    
    # Padrões de intenção
    INTENT_PATTERNS = {
        Intent.GREETING: [
            r"\b(oi|olá|ola|hey|eai|e ai|bom dia|boa tarde|boa noite|salve|opa|oie|oiii)\b",
            r"^(oi|olá|hey)[\?!\.]*$"
        ],
        Intent.FAREWELL: [
            r"\b(tchau|adeus|até mais|ate mais|bye|flw|falou|vlw|valeu|obrigad[oa])\b",
        ],
        Intent.MENU: [
            r"\b(menu|opções|opcoes|o que (você|vc) (faz|pode)|cardápio|ajuda)\b",
        ],
        Intent.HELP: [
            r"\b(ajuda|help|socorro|preciso de ajuda|não (sei|entendi))\b",
        ],
        Intent.PRODUCT_SEARCH: [
            r"\b(procur[oa]|busca|quero|preciso|tem|vende[rm]?|achei|encontr)\b.*(produto|celular|iphone|samsung|tv|notebook|eletrônico)",
            r"\b(quero|preciso|busco|procuro)\b.*\b(comprar|ver|olhar)\b",
            r"\b(tem|vende|achei)\b.*\b(barato|promoção|oferta|desconto)\b",
        ],
        Intent.PRODUCT_INFO: [
            r"\b(informaç[ãõo]|detalhe|especificaç|sobre o produto|me fala|característica)\b",
            r"\b(como funciona|é bom|vale a pena|recomenda)\b",
        ],
        Intent.PRICE_CHECK: [
            r"\b(quanto (custa|é)|preço|valor|$|R\$|reais)\b",
            r"\b(tá|está|fica) (quanto|por quanto)\b",
        ],
        Intent.COMPARE_PRICES: [
            r"\b(compar[ae]|diferença|melhor|vs|versus|ou)\b.*(preço|produto)",
            r"\b(qual|onde).*(mais barato|menor preço|melhor oferta)\b",
        ],
        Intent.HOW_TO_BUY: [
            r"\b(como (compro|faço|posso)|quero comprar|onde compro)\b",
            r"\b(forma de pagamento|aceita|pago|parcela)\b",
        ],
        Intent.PAYMENT_INFO: [
            r"\b(pagamento|pagar|parcela|pix|cartão|boleto|crédito|débito)\b",
        ],
        Intent.SHIPPING_INFO: [
            r"\b(entrega|frete|envio|prazo|chega|demora|dias)\b",
            r"\b(qual o prazo|quando chega|tem frete grátis)\b",
        ],
        Intent.ORDER_STATUS: [
            r"\b(meu pedido|status|rastreio|rastreamento|código|cadê|onde está)\b",
            r"\b(acompanhar|verificar).*(pedido|compra)\b",
        ],
        Intent.COMPLAINT: [
            r"\b(reclama|problema|errado|defeito|quebrou|não (funciona|chegou))\b",
            r"\b(insatisfeit|péssim|horrível|absurdo)\b",
        ],
        Intent.REFUND: [
            r"\b(devolv|estorn|reembols|cancelar|troc)\b",
            r"\b(quero meu dinheiro|pedir reembolso)\b",
        ],
        Intent.TALK_TO_HUMAN: [
            r"\b(falar com (humano|pessoa|atendente|alguém)|atendimento)\b",
            r"\b(quero (um|uma) (pessoa|atendente)|não (é|és) (robô|bot))\b",
        ],
        Intent.SCHEDULE: [
            r"\b(agend[ao]|marcar|horário|disponibilidade|quando)\b",
        ],
        Intent.SUBSCRIBE: [
            r"\b(cadastr|inscrever|newsletter|notificaç)\b",
        ],
        Intent.ALERT_CREATE: [
            r"\b(alerta|avisa|notifica).*(preço|baixar|promoção)\b",
            r"\b(cria|criar|quero).*(alerta|aviso)\b",
            r"\b(quando (baixar|cair|ter promoção))\b",
        ],
        Intent.PURCHASE_INTEREST: [
            r"\b(quero comprar|vou comprar|vou levar|pode mandar|como compro)\b",
            r"\b(fecha[r]?|fechar|finalizar|comprar agora)\b",
            r"\b(add|adicionar).*(carrinho|sacola)\b",
        ],
        Intent.AFFIRMATIVE: [
            r"^(sim|s|yes|ok|pode|isso|exato|certo|claro|bora|vamos|beleza|show|top|perfeito)[\?!\.]*$",
        ],
        Intent.NEGATIVE: [
            r"^(não|nao|n|no|nunca|negativo|nope)[\?!\.]*$",
        ],
    }
    
    # Entidades para extrair
    ENTITY_PATTERNS = {
        "product": r"(iphone|samsung|xiaomi|motorola|tv|notebook|playstation|xbox|airpods?)",
        "price_range": r"(até|menos de|no máximo)[\s]*(R?\$?\s*)?(\d+[.,]?\d*)",
        "phone": r"(\+?55\s?)?\(?\d{2}\)?[\s.-]?\d{4,5}[\s.-]?\d{4}",
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "order_id": r"(pedido|ordem)[\s#]*(\d+)",
    }
    
    def __init__(self):
        # Compilar regex
        self._compiled_patterns = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in self.INTENT_PATTERNS.items()
        }
        self._entity_patterns = {
            name: re.compile(p, re.IGNORECASE)
            for name, p in self.ENTITY_PATTERNS.items()
        }
    
    def detect(self, message: str, context: Optional[ConversationContext] = None) -> IntentAnalysis:
        """
        Detecta intenção e extrai entidades.
        
        Args:
            message: Texto da mensagem
            context: Contexto opcional para decisões contextuais
        
        Returns:
            IntentAnalysis com intenção, entidades e sentimento
        """
        message_lower = message.lower().strip()
        
        # Detectar intenção
        detected_intent = Intent.UNKNOWN
        max_confidence = 0.0
        
        for intent, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(message_lower):
                    # Calcular confiança baseado no match
                    match = pattern.search(message_lower)
                    match_ratio = len(match.group()) / len(message_lower) if match else 0
                    confidence = 0.6 + (match_ratio * 0.4)
                    
                    if confidence > max_confidence:
                        max_confidence = confidence
                        detected_intent = intent
        
        # Extrair entidades
        entities = self._extract_entities(message)
        
        # Detectar sentimento básico
        sentiment, sentiment_score = self._detect_sentiment(message_lower)
        
        # Extrair keywords relevantes
        keywords = self._extract_keywords(message_lower)
        
        # Sugerir estágio baseado na intenção
        suggested_stage = self._suggest_stage(detected_intent, context)
        
        # Determinar se precisa de IA (baixa confiança ou contexto complexo)
        requires_ai = max_confidence < 0.5 or len(message.split()) > 15
        
        return IntentAnalysis(
            intent=detected_intent,
            confidence=max_confidence if detected_intent != Intent.UNKNOWN else 0.3,
            entities=entities,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            keywords=keywords,
            suggested_stage=suggested_stage,
            requires_ai=requires_ai
        )
    
    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extrai entidades nomeadas da mensagem."""
        entities = {}
        
        for entity_name, pattern in self._entity_patterns.items():
            match = pattern.search(message)
            if match:
                entities[entity_name] = match.group()
        
        return entities
    
    def _detect_sentiment(self, message: str) -> Tuple[SentimentType, float]:
        """Detecta sentimento básico."""
        positive_words = ["ótimo", "excelente", "bom", "maravilhoso", "perfeito", "amei", "adorei", "obrigado"]
        negative_words = ["ruim", "péssimo", "horrível", "terrível", "raiva", "absurdo", "decepcionado", "frustrado"]
        frustrated_words = ["não funciona", "problema", "erro", "defeito", "demora", "nunca chega"]
        excited_words = ["uau", "incrível", "show", "demais", "top", "!"]
        
        positive_count = sum(1 for w in positive_words if w in message)
        negative_count = sum(1 for w in negative_words if w in message)
        frustrated_count = sum(1 for w in frustrated_words if w in message)
        excited_count = sum(1 for w in excited_words if w in message)
        
        if frustrated_count > 0 or negative_count > 1:
            return SentimentType.FRUSTRATED, 0.2
        elif negative_count > 0:
            return SentimentType.NEGATIVE, 0.3
        elif excited_count > 0 and positive_count > 0:
            return SentimentType.EXCITED, 0.9
        elif positive_count > 0:
            return SentimentType.POSITIVE, 0.7
        
        return SentimentType.NEUTRAL, 0.5
    
    def _extract_keywords(self, message: str) -> List[str]:
        """Extrai palavras-chave relevantes."""
        # Remove stopwords e extrai substantivos/adjetivos importantes
        stopwords = {"o", "a", "os", "as", "um", "uma", "de", "da", "do", "para", "que", "e", "é", "em", "com"}
        words = message.split()
        return [w for w in words if len(w) > 3 and w.lower() not in stopwords][:5]
    
    def _suggest_stage(
        self,
        intent: Intent,
        context: Optional[ConversationContext]
    ) -> Optional[ConversationStage]:
        """Sugere próximo estágio baseado na intenção."""
        stage_mapping = {
            Intent.GREETING: ConversationStage.GREETING,
            Intent.PRODUCT_SEARCH: ConversationStage.PRODUCT_SEARCH,
            Intent.PRODUCT_INFO: ConversationStage.PRODUCT_DETAIL,
            Intent.PRICE_CHECK: ConversationStage.PRODUCT_DETAIL,
            Intent.COMPARE_PRICES: ConversationStage.COMPARISON,
            Intent.HOW_TO_BUY: ConversationStage.CLOSING,
            Intent.ORDER_STATUS: ConversationStage.SUPPORT,
            Intent.COMPLAINT: ConversationStage.SUPPORT,
            Intent.TALK_TO_HUMAN: ConversationStage.HUMAN_HANDOFF,
        }
        return stage_mapping.get(intent)


# ============================================
# RESPONSE TEMPLATES
# ============================================

class ResponseTemplates:
    """Templates de resposta organizados por estágio e intenção."""
    
    # Saudações dinâmicas
    GREETINGS = {
        "morning": [
            "Bom dia! ☀️ Sou o assistente da Didin Fácil. Como posso ajudar você hoje?",
            "Bom dia! Bem-vindo à Didin Fácil! O que você procura hoje?",
        ],
        "afternoon": [
            "Boa tarde! 👋 Sou o assistente virtual da Didin Fácil. Em que posso ajudar?",
            "Boa tarde! Como posso te ajudar a encontrar a melhor oferta hoje?",
        ],
        "evening": [
            "Boa noite! 🌙 Estou aqui para ajudar. O que você está procurando?",
            "Boa noite! Mesmo nesse horário, posso te ajudar a encontrar as melhores ofertas!",
        ],
        "returning": [
            "Que bom te ver de novo, {name}! 😊 Como posso ajudar?",
            "Olá {name}! Pronto para encontrar mais ofertas?",
        ],
    }
    
    # Menu principal
    MAIN_MENU = """
📱 *Menu Principal*

Posso te ajudar com:

1️⃣ 🔍 *Buscar produtos* - Encontre o melhor preço
2️⃣ 💰 *Comparar preços* - Compare entre lojas
3️⃣ 🔔 *Alertas de preço* - Avise quando baixar
4️⃣ 📦 *Status de pedido* - Rastrear compra
5️⃣ 🆘 *Suporte* - Falar com atendente

Digite o número ou descreva o que precisa!
"""
    
    # Busca de produtos
    PRODUCT_SEARCH = {
        "ask": "🔍 O que você está procurando? Me conta o produto, marca ou categoria!",
        "searching": "🔎 Buscando as melhores ofertas para *{query}*... Um momento!",
        "found": """
🎯 Encontrei {count} ofertas para *{query}*!

{products}

Quer ver mais detalhes de algum? Digite o número!
""",
        "not_found": """
😕 Não encontrei resultados para *{query}*.

Tente:
• Verificar a ortografia
• Usar termos mais gerais
• Me perguntar de outra forma

Ou me diga outro produto que procura!
""",
    }
    
    # Detalhes do produto
    PRODUCT_DETAIL = """
📦 *{name}*

💰 *Menor preço:* R$ {min_price}
🏪 *Loja:* {store}
📊 *Variação 30d:* {price_change}

{description}

🔗 *Link:* {url}

O que deseja fazer?
• "Comparar" - Ver preços em outras lojas
• "Alerta" - Avisar quando baixar
• "Comprar" - Ir para a loja
"""
    
    # Comparação de preços
    PRICE_COMPARISON = """
📊 *Comparação de Preços*
*{product_name}*

{comparison_table}

💡 *Dica:* O menor preço está na *{best_store}*!
Economia de R$ {savings} vs média.

Quer que eu te avise se o preço baixar ainda mais?
"""
    
    # Qualificação
    QUALIFICATION = {
        "ask_budget": "💰 Qual seu orçamento para essa compra?",
        "ask_urgency": "⏰ Você precisa do produto com urgência ou pode esperar uma promoção?",
        "ask_preferences": "🤔 Prefere comprar online ou em loja física?",
    }
    
    # Suporte
    SUPPORT = {
        "order_ask": "📦 Por favor, me informe o número do seu pedido ou e-mail de cadastro.",
        "complaint_ack": """
😔 Lamento muito pelo inconveniente, {name}.
Sua satisfação é muito importante para nós.

Vou encaminhar seu caso para nossa equipe priorizar o atendimento.
Um especialista entrará em contato em até 2 horas úteis.

Enquanto isso, posso ajudar com algo mais?
""",
        "handoff": """
🧑‍💼 Entendo! Vou te conectar com um de nossos especialistas.

Tempo estimado de espera: {wait_time}
Você é o {position}º na fila.

Enquanto aguarda, posso ajudar com mais alguma coisa?
""",
    }
    
    # Fechamento
    CLOSING = {
        "how_to_buy": """
🛒 *Como Comprar*

1. Clique no link do produto
2. Você será direcionado para a loja
3. Complete a compra direto no site da loja
4. Use cupons de desconto se disponíveis!

💡 Dica: Cadastre seu e-mail para receber alertas de ofertas!
""",
        "payment_info": """
💳 *Formas de Pagamento*

Cada loja tem suas próprias opções:
• Cartão de crédito (até 12x)
• PIX (desconto extra!)
• Boleto bancário

A Didin Fácil é um comparador - a compra é feita direto na loja escolhida.
""",
    }
    
    # Fallback
    FALLBACK = [
        "🤔 Não entendi bem. Pode reformular?",
        "Hmm, pode explicar de outra forma?",
        "Desculpa, não consegui entender. Que tal escolher uma opção do menu?",
    ]
    
    # Despedida
    FAREWELL = [
        "Até mais! 👋 Volte sempre que precisar!",
        "Obrigado pelo contato! Estou aqui se precisar! 😊",
        "Tchau! Boas compras! 🛍️",
    ]


# ============================================
# PROFESSIONAL SELLER BOT
# ============================================

class ProfessionalSellerBot:
    """
    Bot de vendas profissional da Didin Fácil.
    
    Features:
    - Intent detection (rule-based + AI)
    - Context management
    - Product search integration
    - CRM integration
    - Analytics tracking
    - Multi-channel support
    """
    
    def __init__(
        self,
        product_service=None,
        crm_service=None,
        analytics_service=None,
        ai_client=None,
        n8n_client=None,
    ):
        """
        Args:
            product_service: Serviço de busca de produtos
            crm_service: Serviço de CRM
            analytics_service: Serviço de analytics
            ai_client: Cliente OpenAI para respostas avançadas
            n8n_client: Cliente n8n para automações
        """
        self.intent_detector = IntentDetector()
        self.templates = ResponseTemplates()
        
        # Serviços opcionais
        self.product_service = product_service
        self.crm_service = crm_service
        self.analytics_service = analytics_service
        self.ai_client = ai_client
        self.n8n_client = n8n_client
        
        # Cache de contextos (em produção usar Redis)
        self._contexts: Dict[str, ConversationContext] = {}
        
        # Handlers por intenção
        self._intent_handlers = {
            Intent.GREETING: self._handle_greeting,
            Intent.FAREWELL: self._handle_farewell,
            Intent.MENU: self._handle_menu,
            Intent.HELP: self._handle_help,
            Intent.PRODUCT_SEARCH: self._handle_product_search,
            Intent.PRODUCT_INFO: self._handle_product_info,
            Intent.PRICE_CHECK: self._handle_price_check,
            Intent.COMPARE_PRICES: self._handle_compare_prices,
            Intent.HOW_TO_BUY: self._handle_how_to_buy,
            Intent.PAYMENT_INFO: self._handle_payment_info,
            Intent.SHIPPING_INFO: self._handle_shipping_info,
            Intent.ORDER_STATUS: self._handle_order_status,
            Intent.COMPLAINT: self._handle_complaint,
            Intent.REFUND: self._handle_refund,
            Intent.TALK_TO_HUMAN: self._handle_human_handoff,
            Intent.SCHEDULE: self._handle_schedule,
            Intent.SUBSCRIBE: self._handle_subscribe,
            Intent.ALERT_CREATE: self._handle_alert_create,
            Intent.PURCHASE_INTEREST: self._handle_purchase_interest,
            Intent.AFFIRMATIVE: self._handle_affirmative,
            Intent.NEGATIVE: self._handle_negative,
            Intent.UNKNOWN: self._handle_unknown,
        }
    
    # ========================================
    # MAIN ENTRY POINT
    # ========================================
    
    async def process_message(
        self,
        message: IncomingMessage
    ) -> List[BotResponse]:
        """
        Processa mensagem e retorna respostas.
        
        Args:
            message: Mensagem recebida
        
        Returns:
            Lista de respostas (pode ser múltiplas)
        """
        # Obter ou criar contexto
        context = await self._get_or_create_context(message)
        
        # Atualizar contexto
        context.message_count += 1
        context.last_interaction = datetime.utcnow()
        
        # Detectar intenção
        analysis = self.intent_detector.detect(message.content, context)
        
        # Atualizar histórico de intenções
        context.intents_detected.append(analysis.intent.value)
        context.sentiment_history.append(analysis.sentiment.value)
        
        # Atualizar temperatura do lead
        self._update_lead_temperature(context, analysis)
        
        # Trackear analytics
        await self._track_message(message, context, analysis)
        
        # Processar com handler apropriado
        handler = self._intent_handlers.get(analysis.intent, self._handle_unknown)
        responses = await handler(message, context, analysis)
        
        # Se confiança baixa e temos IA, enriquecer resposta
        if analysis.requires_ai and self.ai_client:
            responses = await self._enrich_with_ai(message, context, responses)
        
        # Salvar contexto
        await self._save_context(context)
        
        # Sync com CRM se necessário
        if context.lead_temperature in [LeadTemperature.WARM, LeadTemperature.HOT]:
            await self._sync_to_crm(context)
        
        # Disparar automações n8n baseado no contexto
        await self._trigger_automations(message, context, analysis)
        
        return responses
    
    # ========================================
    # N8N AUTOMATION INTEGRATION
    # ========================================
    
    async def _trigger_automations(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ):
        """Dispara automações n8n baseado no comportamento."""
        if not AUTOMATION_AVAILABLE:
            return

        try:
            orchestrator = get_orchestrator()

            # Mapear canal do bot para canal de automação
            channel_map = {
                MessageChannel.WHATSAPP: AutomationChannel.WHATSAPP,
                MessageChannel.INSTAGRAM: AutomationChannel.INSTAGRAM_DM,
                MessageChannel.WEBCHAT: AutomationChannel.EMAIL,
            }
            automation_channel = channel_map.get(
                message.channel, AutomationChannel.WHATSAPP
            )

            # 1. Novo usuário - disparar onboarding
            if context.message_count == 1:
                await orchestrator.trigger_onboarding(
                    user_id=context.user_id,
                    name=context.user_name or "Cliente",
                    channel=automation_channel,
                    phone=context.user_phone
                )

            # 2. Lead qualificado - disparar nurturing
            is_hot = context.lead_temperature == LeadTemperature.HOT
            high_score = context.lead_score >= 80
            not_triggered = "lead_qualified_triggered" not in context.variables

            if is_hot and high_score and not_triggered:
                await orchestrator.trigger_lead_qualified(
                    user_id=context.user_id,
                    name=context.user_name or "Cliente",
                    lead_score=context.lead_score,
                    interested_products=context.interested_products,
                    channel=automation_channel
                )
                context.variables["lead_qualified_triggered"] = True

            # 3. Busca de produto - nurturing
            is_search = analysis.intent == Intent.PRODUCT_SEARCH
            engaged = context.message_count > 2
            nurture_pending = "nurturing_triggered" not in context.variables

            if is_search and engaged and nurture_pending:
                product = analysis.entities.get("product", "produtos")
                await orchestrator.trigger_automation(
                    AutomationType.NEW_LEAD_NURTURING,
                    user_id=context.user_id,
                    data={
                        "name": context.user_name or "Cliente",
                        "product": product,
                        "search_query": message.content
                    },
                    channel=automation_channel
                )
                context.variables["nurturing_triggered"] = True

        except Exception as e:
            logger.warning("Erro ao disparar automações: %s", e)
    
    # ========================================
    # CONTEXT MANAGEMENT
    # ========================================
    
    async def _get_or_create_context(
        self,
        message: IncomingMessage
    ) -> ConversationContext:
        """Obtém contexto existente ou cria novo."""
        context_key = f"{message.channel.value}:{message.sender_id}"
        
        if context_key in self._contexts:
            context = self._contexts[context_key]
            
            # Verificar se expirou (30 min de inatividade)
            if datetime.utcnow() - context.last_interaction > timedelta(minutes=30):
                # Criar novo contexto mas manter info do usuário
                old_context = context
                context = ConversationContext(
                    user_id=message.sender_id,
                    channel=message.channel,
                    user_name=old_context.user_name,
                    user_phone=old_context.user_phone,
                    crm_contact_id=old_context.crm_contact_id,
                )
        else:
            context = ConversationContext(
                user_id=message.sender_id,
                channel=message.channel,
                user_name=message.sender_name,
                user_phone=message.sender_phone,
            )
        
        self._contexts[context_key] = context
        return context
    
    async def _save_context(self, context: ConversationContext):
        """Salva contexto (em produção, persistir em Redis/DB)."""
        context.updated_at = datetime.utcnow()
        context_key = f"{context.channel.value}:{context.user_id}"
        self._contexts[context_key] = context
    
    def _update_lead_temperature(
        self,
        context: ConversationContext,
        analysis: IntentAnalysis
    ):
        """Atualiza temperatura do lead baseado em comportamento."""
        # Pontuação por intenção
        intent_scores = {
            Intent.PRODUCT_SEARCH: 5,
            Intent.PRODUCT_INFO: 10,
            Intent.PRICE_CHECK: 15,
            Intent.COMPARE_PRICES: 20,
            Intent.HOW_TO_BUY: 50,
            Intent.PAYMENT_INFO: 40,
            Intent.SHIPPING_INFO: 30,
        }
        
        score_delta = intent_scores.get(analysis.intent, 0)
        context.lead_score += score_delta
        
        # Determinar temperatura
        if context.lead_score >= 80:
            context.lead_temperature = LeadTemperature.HOT
        elif context.lead_score >= 40:
            context.lead_temperature = LeadTemperature.WARM
        else:
            context.lead_temperature = LeadTemperature.COLD
    
    # ========================================
    # INTENT HANDLERS
    # ========================================
    
    async def _handle_greeting(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Trata saudação inicial."""
        context.stage = ConversationStage.GREETING
        
        # Determinar período do dia
        hour = datetime.now().hour
        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 18:
            period = "afternoon"
        else:
            period = "evening"
        
        # Se é usuário retornando
        if context.user_name and context.message_count > 1:
            greeting = self.templates.GREETINGS["returning"][0].format(name=context.user_name)
        else:
            greeting = self.templates.GREETINGS[period][0]
        
        responses = [
            BotResponse(
                content=greeting,
                intent_detected=Intent.GREETING,
            ),
            BotResponse(
                content=self.templates.MAIN_MENU,
                delay_ms=1000,
                quick_replies=["Buscar produto", "Comparar preços", "Falar com atendente"]
            )
        ]
        
        return responses
    
    async def _handle_farewell(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Trata despedida."""
        context.is_active = False
        
        farewell = self.templates.FAREWELL[0]
        
        return [
            BotResponse(
                content=farewell,
                intent_detected=Intent.FAREWELL,
            )
        ]
    
    async def _handle_menu(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Mostra menu principal."""
        return [
            BotResponse(
                content=self.templates.MAIN_MENU,
                intent_detected=Intent.MENU,
                quick_replies=["Buscar", "Comparar", "Alertas", "Suporte"]
            )
        ]
    
    async def _handle_help(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Mostra ajuda."""
        help_text = """
🆘 *Central de Ajuda*

Sou o assistente virtual da Didin Fácil!

Eu posso te ajudar a:
• 🔍 Encontrar produtos com os melhores preços
• 📊 Comparar preços entre lojas
• 🔔 Criar alertas de preço
• 📦 Rastrear pedidos

*Dica:* Basta me dizer o que você procura!
Exemplo: "Quero um iPhone barato"

Precisa falar com uma pessoa?
Digite "atendente" ou "falar com humano".
"""
        return [
            BotResponse(
                content=help_text,
                intent_detected=Intent.HELP,
            )
        ]
    
    async def _handle_product_search(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Busca produtos."""
        context.stage = ConversationStage.PRODUCT_SEARCH
        
        # Extrair query de busca
        query = message.content
        
        # Se temos entidade de produto, usar ela
        if "product" in analysis.entities:
            query = analysis.entities["product"]
        
        # Adicionar ao histórico
        context.search_history.append(query)
        
        # Buscar produtos (simulado se não tiver serviço)
        if self.product_service:
            products = await self.product_service.search(query, limit=5)
        else:
            # Mock para demonstração
            products = self._mock_product_search(query)
        
        if not products:
            return [
                BotResponse(
                    content=self.templates.PRODUCT_SEARCH["not_found"].format(query=query),
                    intent_detected=Intent.PRODUCT_SEARCH,
                    quick_replies=["Tentar novamente", "Ver menu"]
                )
            ]
        
        # Formatar lista de produtos
        products_text = self._format_product_list(products)
        
        return [
            BotResponse(
                content=self.templates.PRODUCT_SEARCH["found"].format(
                    count=len(products),
                    query=query,
                    products=products_text
                ),
                intent_detected=Intent.PRODUCT_SEARCH,
                quick_replies=["1", "2", "3", "Ver mais"]
            )
        ]
    
    async def _handle_product_info(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Mostra informações do produto."""
        context.stage = ConversationStage.PRODUCT_DETAIL
        
        # Usar último produto visto ou buscar novo
        product = context.last_product_viewed or {"name": "Produto", "price": 0}
        
        detail_text = self.templates.PRODUCT_DETAIL.format(
            name=product.get("name", "Produto"),
            min_price=product.get("min_price", 0),
            store=product.get("store", "Loja"),
            price_change=product.get("price_change", "-5%"),
            description=product.get("description", "")[:200],
            url=product.get("url", "#")
        )
        
        return [
            BotResponse(
                content=detail_text,
                intent_detected=Intent.PRODUCT_INFO,
                quick_replies=["Comparar", "Alerta de preço", "Voltar"]
            )
        ]
    
    async def _handle_price_check(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Verifica preço de produto."""
        # Similar ao product_info mas focado em preço
        return await self._handle_product_info(message, context, analysis)
    
    async def _handle_compare_prices(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Compara preços entre lojas."""
        context.stage = ConversationStage.COMPARISON
        
        product = context.last_product_viewed
        
        if not product:
            return [
                BotResponse(
                    content="🤔 Qual produto você quer comparar? Me diz o nome!",
                    intent_detected=Intent.COMPARE_PRICES,
                )
            ]
        
        # Mock de comparação
        comparison = """
| Loja | Preço | Frete |
|------|-------|-------|
| Amazon | R$ 4.199 | Grátis |
| Magalu | R$ 4.299 | R$ 25 |
| Casas Bahia | R$ 4.399 | Grátis |
| Americanas | R$ 4.249 | R$ 30 |
"""
        
        response = self.templates.PRICE_COMPARISON.format(
            product_name=product.get("name", "Produto"),
            comparison_table=comparison,
            best_store="Amazon",
            savings="200"
        )
        
        return [
            BotResponse(
                content=response,
                intent_detected=Intent.COMPARE_PRICES,
                quick_replies=["Criar alerta", "Ir para Amazon", "Voltar"]
            )
        ]
    
    async def _handle_how_to_buy(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Explica como comprar."""
        context.stage = ConversationStage.CLOSING
        
        return [
            BotResponse(
                content=self.templates.CLOSING["how_to_buy"],
                intent_detected=Intent.HOW_TO_BUY,
            )
        ]
    
    async def _handle_payment_info(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Informa sobre pagamento."""
        return [
            BotResponse(
                content=self.templates.CLOSING["payment_info"],
                intent_detected=Intent.PAYMENT_INFO,
            )
        ]
    
    async def _handle_shipping_info(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Informa sobre entrega."""
        shipping_info = """
📦 *Informações de Entrega*

A entrega depende de cada loja e da sua região.
A Didin Fácil mostra o frete de cada loja na comparação.

Geralmente:
• Capitais: 2-5 dias úteis
• Interior: 5-10 dias úteis
• Frete grátis: Geralmente em compras acima de R$ 200

Dica: Use o CEP no site da loja para calcular o frete exato!
"""
        return [
            BotResponse(
                content=shipping_info,
                intent_detected=Intent.SHIPPING_INFO,
            )
        ]
    
    async def _handle_order_status(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Verifica status de pedido."""
        context.stage = ConversationStage.SUPPORT
        
        # Extrair ID do pedido se houver
        order_id = analysis.entities.get("order_id")
        
        if order_id:
            # Buscar status (mock)
            status_text = f"""
📦 *Pedido #{order_id}*

Status: Em trânsito 🚚
Previsão: 3 dias úteis
Código de rastreio: BR123456789

Acompanhe pelo site dos Correios ou da transportadora.
"""
            return [BotResponse(content=status_text, intent_detected=Intent.ORDER_STATUS)]
        
        return [
            BotResponse(
                content=self.templates.SUPPORT["order_ask"],
                intent_detected=Intent.ORDER_STATUS,
            )
        ]
    
    async def _handle_complaint(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Trata reclamação."""
        context.stage = ConversationStage.SUPPORT

        # Priorizar atendimento humano para reclamações
        response = self.templates.SUPPORT["complaint_ack"].format(
            name=context.user_name or "cliente"
        )

        # Disparar n8n para notificar equipe via orquestrador
        if AUTOMATION_AVAILABLE:
            try:
                orchestrator = get_orchestrator()
                await orchestrator.trigger_complaint_alert(
                    user_id=context.user_id,
                    name=context.user_name or "Cliente",
                    complaint=message.content,
                    channel=self._map_channel(message.channel),
                    sentiment=analysis.sentiment.value if analysis.sentiment else "unknown",
                    priority="high" if analysis.sentiment == SentimentType.FRUSTRATED else "medium"
                )
            except Exception as e:
                logger.warning("Erro ao disparar alerta de reclamação: %s", e)
        elif self.n8n_client:
            await self._trigger_support_alert(context, message.content)

        is_frustrated = analysis.sentiment == SentimentType.FRUSTRATED
        return [
            BotResponse(
                content=response,
                intent_detected=Intent.COMPLAINT,
                should_handoff=is_frustrated,
            )
        ]

    def _map_channel(self, channel: MessageChannel) -> "AutomationChannel":
        """Mapeia canal de mensagem para canal de automação."""
        if not AUTOMATION_AVAILABLE:
            return None
        channel_map = {
            MessageChannel.WHATSAPP: AutomationChannel.WHATSAPP,
            MessageChannel.INSTAGRAM: AutomationChannel.INSTAGRAM_DM,
            MessageChannel.WEBCHAT: AutomationChannel.EMAIL,
        }
        return channel_map.get(channel, AutomationChannel.WHATSAPP)
    
    async def _handle_refund(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Trata pedido de reembolso."""
        refund_info = """
💸 *Política de Reembolso*

A Didin Fácil é um comparador de preços.
As compras são realizadas diretamente nas lojas.

Para solicitar reembolso, você deve:
1. Acessar o site da loja onde comprou
2. Ir em "Meus Pedidos"
3. Solicitar devolução/reembolso

Cada loja tem sua própria política, mas geralmente:
• 7 dias para arrependimento (CDC)
• 30 dias para defeito

Precisa de ajuda com alguma loja específica?
"""
        return [
            BotResponse(
                content=refund_info,
                intent_detected=Intent.REFUND,
                quick_replies=["Falar com atendente", "Voltar ao menu"]
            )
        ]
    
    async def _handle_human_handoff(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Escala para atendente humano."""
        context.stage = ConversationStage.HUMAN_HANDOFF

        # Disparar automação de handoff
        if AUTOMATION_AVAILABLE:
            try:
                orchestrator = get_orchestrator()
                await orchestrator.trigger_human_handoff(
                    user_id=context.user_id,
                    name=context.user_name or "Cliente",
                    reason="user_request",
                    context_summary=self._summarize_context(context),
                    channel=self._map_channel(message.channel),
                    lead_score=context.lead_score
                )
            except Exception as e:
                logger.warning("Erro ao disparar handoff: %s", e)

        response = self.templates.SUPPORT["handoff"].format(
            wait_time="5 minutos",
            position=1
        )

        return [
            BotResponse(
                content=response,
                intent_detected=Intent.TALK_TO_HUMAN,
                should_handoff=True,
                handoff_reason="user_request"
            )
        ]

    def _summarize_context(self, context: ConversationContext) -> str:
        """Resume o contexto para o atendente."""
        summary_parts = []
        if context.user_name:
            summary_parts.append(f"Cliente: {context.user_name}")
        if context.interested_products:
            products = ", ".join(context.interested_products[:3])
            summary_parts.append(f"Interesse: {products}")
        if context.lead_temperature:
            summary_parts.append(f"Temperatura: {context.lead_temperature.value}")
        summary_parts.append(f"Mensagens: {context.message_count}")
        return " | ".join(summary_parts) if summary_parts else "Novo contato"
    
    async def _handle_schedule(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Agenda contato."""
        schedule_text = """
📅 *Agendamento*

Posso agendar um contato com nossa equipe!

Quando prefere ser contatado?
• Manhã (8h-12h)
• Tarde (13h-18h)
• Noite (18h-20h)

Digite sua preferência!
"""
        return [
            BotResponse(
                content=schedule_text,
                intent_detected=Intent.SCHEDULE,
                quick_replies=["Manhã", "Tarde", "Noite"]
            )
        ]
    
    async def _handle_subscribe(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Cadastra para alertas."""
        subscribe_text = """
🔔 *Alertas de Ofertas*

Ótimo! Posso te avisar quando:
• Preço de um produto cair
• Aparecer cupom de desconto
• Ter promoção relâmpago

Para isso, preciso do seu e-mail.
Digite seu e-mail para se cadastrar!
"""
        return [
            BotResponse(
                content=subscribe_text,
                intent_detected=Intent.SUBSCRIBE,
            )
        ]
    
    async def _handle_affirmative(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Trata resposta afirmativa baseado no contexto."""
        # Depende do estágio atual
        if context.stage == ConversationStage.PRODUCT_SEARCH:
            return await self._handle_product_info(message, context, analysis)
        elif context.stage == ConversationStage.COMPARISON:
            return [BotResponse(content="Ótimo! Vou criar o alerta de preço para você. 🔔")]
        
        return [BotResponse(content="Perfeito! O que mais posso fazer por você?")]
    
    async def _handle_negative(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Trata resposta negativa."""
        return [
            BotResponse(
                content="Sem problemas! O que mais posso fazer por você?",
                intent_detected=Intent.NEGATIVE,
            )
        ]
    
    async def _handle_unknown(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Trata intenção desconhecida."""
        import random
        fallback = random.choice(self.templates.FALLBACK)
        
        return [
            BotResponse(
                content=fallback,
                intent_detected=Intent.UNKNOWN,
                quick_replies=["Ver menu", "Buscar produto", "Falar com atendente"]
            )
        ]

    async def _handle_alert_create(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Cria alerta de preço para produto."""
        # Verificar se há produto específico na mensagem
        product_mentioned = analysis.entities.get("product")
        target_price = analysis.entities.get("price")

        if product_mentioned:
            # Disparar automação n8n para criar alerta
            if AUTOMATION_AVAILABLE:
                try:
                    orchestrator = get_orchestrator()
                    await orchestrator.trigger_automation(
                        AutomationType.PRICE_DROP_ALERT,
                        user_id=context.user_id,
                        data={
                            "user_name": context.user_name,
                            "user_email": context.user_email,
                            "product_query": product_mentioned,
                            "target_price": target_price,
                            "channel": context.channel.value,
                        }
                    )
                except Exception as e:
                    logger.warning("Erro ao disparar alerta: %s", e)

            price_text = ""
            if target_price:
                price_text = f"Preço alvo: R$ {target_price:,.2f}"

            response = f"""
🔔 *Alerta de Preço Criado!*

Produto: *{product_mentioned}*
{price_text}

Vou te avisar assim que encontrar uma oferta boa!

📱 Você receberá notificações por:
• WhatsApp
• E-mail (se cadastrado)
• Push notification

Quer criar mais algum alerta?
"""
            return [
                BotResponse(
                    content=response,
                    intent_detected=Intent.ALERT_CREATE,
                    quick_replies=[
                        "Criar outro alerta",
                        "Ver meus alertas",
                        "Menu principal"
                    ]
                )
            ]

        # Sem produto específico, pedir informações
        return [
            BotResponse(
                content="""
🔔 *Criar Alerta de Preço*

Para criar um alerta, me diga:
1️⃣ Qual produto você quer monitorar?
2️⃣ Qual preço máximo deseja pagar? (opcional)

Exemplo: "Avise quando iPhone 15 baixar para R$ 5000"
""",
                intent_detected=Intent.ALERT_CREATE,
                quick_replies=["iPhone", "Samsung Galaxy", "Notebook"]
            )
        ]

    async def _handle_purchase_interest(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Trata intenção de compra - lead quente!"""
        # Atualizar temperatura do lead para HOT
        context.lead_temperature = LeadTemperature.HOT
        context.lead_score = min(100, context.lead_score + 30)

        # Capturar produto de interesse
        product = analysis.entities.get("product")
        if product and product not in context.interested_products:
            context.interested_products.append(product)

        # Disparar automação para lead qualificado
        if AUTOMATION_AVAILABLE:
            try:
                orchestrator = get_orchestrator()
                await orchestrator.trigger_lead_qualified(
                    user_id=context.user_id,
                    name=context.user_name or "Cliente",
                    lead_score=context.lead_score,
                    interested_products=context.interested_products,
                    channel=self._map_channel(message.channel)
                )
            except Exception as e:
                logger.warning("Erro ao disparar lead qualificado: %s", e)

        # Sincronizar com CRM (criar deal)
        await self._sync_to_crm(context)

        response = """
🎯 *Excelente escolha!*

Você está perto de fazer um ótimo negócio! 💪

Posso te ajudar a:
• 💰 Encontrar o melhor preço disponível
• 🏪 Comparar lojas confiáveis
• 📊 Ver histórico de preços
• 🔔 Criar alerta para queda de preço

O que prefere?
"""
        return [
            BotResponse(
                content=response,
                intent_detected=Intent.PURCHASE_INTEREST,
                quick_replies=[
                    "Ver melhor preço",
                    "Comparar lojas",
                    "Criar alerta"
                ],
                metadata={"lead_hot": True}
            )
        ]

    async def _handle_cart_abandoned_check(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ) -> List[BotResponse]:
        """Trata verificação de carrinho abandonado."""
        # Buscar carrinhos abandonados do usuário (mock)
        abandoned_carts = await self._get_abandoned_carts(context.user_id)

        if abandoned_carts:
            # Disparar automação de recuperação
            if AUTOMATION_AVAILABLE:
                try:
                    orchestrator = get_orchestrator()
                    await orchestrator.trigger_automation(
                        AutomationType.CART_ABANDONED,
                        user_id=context.user_id,
                        data={
                            "user_name": context.user_name,
                            "channel": context.channel.value,
                            "abandoned_items": abandoned_carts,
                        }
                    )
                except Exception as e:
                    logger.warning("Erro ao disparar cart abandoned: %s", e)

            # Formatar lista de itens abandonados
            items_text = "\n".join([
                f"• {item['name']} - R$ {item['price']:,.2f}"
                for item in abandoned_carts[:5]
            ])

            response = f"""
🛒 *Seus Itens Salvos*

Encontrei alguns produtos que você mostrou interesse:

{items_text}

Quer que eu verifique se algum deles baixou de preço? 📉
"""
            return [
                BotResponse(
                    content=response,
                    intent_detected=Intent.CART_ABANDONED_CHECK,
                    quick_replies=[
                        "Verificar preços",
                        "Criar alertas",
                        "Limpar lista"
                    ]
                )
            ]

        return [
            BotResponse(
                content="""
🛒 *Nenhum item salvo*

Você não tem produtos salvos no momento.

Quer buscar algo? Me diga o que procura!
""",
                intent_detected=Intent.CART_ABANDONED_CHECK,
                quick_replies=["Buscar produto", "Ver ofertas", "Menu"]
            )
        ]

    async def _get_abandoned_carts(self, user_id: str) -> List[Dict]:
        """Busca carrinhos abandonados do usuário."""
        # TODO: Implementar busca real no banco de dados
        # Por enquanto retorna mock para demonstração
        return [
            {"name": "iPhone 15 Pro 256GB", "price": 7499.00},
            {"name": "AirPods Pro 2", "price": 1799.00},
        ]

    # ========================================
    # AI ENRICHMENT
    # ========================================
    
    async def _enrich_with_ai(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        responses: List[BotResponse]
    ) -> List[BotResponse]:
        """Enriquece respostas usando IA quando necessário."""
        if not self.ai_client:
            return responses
        
        try:
            # Construir prompt para IA
            system_prompt = """Você é o assistente virtual da Didin Fácil, 
            um comparador de preços brasileiro. Seja prestativo, 
            educado e objetivo. Use emojis com moderação."""
            
            user_context = f"""
            Usuário: {context.user_name or 'Cliente'}
            Mensagem: {message.content}
            Histórico de buscas: {context.search_history[-3:]}
            Estágio: {context.stage.value}
            """
            
            # Chamar API (mock - implementar com OpenAI real)
            ai_response = await self._call_ai(system_prompt, user_context)
            
            if ai_response:
                responses.append(
                    BotResponse(
                        content=ai_response,
                        generated_by="ai",
                        delay_ms=500
                    )
                )
        except Exception as e:
            logger.error(f"Erro ao enriquecer com IA: {e}")
        
        return responses
    
    async def _call_ai(self, system: str, user: str) -> Optional[str]:
        """Chama API de IA."""
        # Implementar chamada real ao OpenAI
        return None
    
    # ========================================
    # CRM INTEGRATION
    # ========================================
    
    async def _sync_to_crm(self, context: ConversationContext):
        """Sincroniza lead com CRM."""
        if not self.crm_service:
            return
        
        try:
            # Criar ou atualizar contato
            if not context.crm_contact_id:
                contact = await self.crm_service.contacts.create(
                    user_id="system",
                    email=context.user_email or f"{context.user_id}@unknown.com",
                    name=context.user_name,
                    phone=context.user_phone,
                    source="chatbot",
                    tags=["chatbot", context.channel.value],
                    custom_fields={
                        "lead_score": context.lead_score,
                        "lead_temperature": context.lead_temperature.value,
                        "interested_products": context.interested_products,
                    }
                )
                context.crm_contact_id = contact.id
            
            # Criar deal se lead qualificado
            if context.lead_temperature == LeadTemperature.HOT and not context.crm_deal_id:
                deal = await self.crm_service.deals.create(
                    user_id="system",
                    contact_id=context.crm_contact_id,
                    title=f"Lead {context.user_name or context.user_id}",
                    value=0,
                    stage="new",
                )
                context.crm_deal_id = deal.id
                
        except Exception as e:
            logger.error(f"Erro ao sincronizar com CRM: {e}")
    
    # ========================================
    # ANALYTICS
    # ========================================
    
    async def _track_message(
        self,
        message: IncomingMessage,
        context: ConversationContext,
        analysis: IntentAnalysis
    ):
        """Registra analytics da mensagem."""
        if not self.analytics_service:
            return
        
        try:
            await self.analytics_service.track_event(
                event_type="chatbot_message",
                user_id=context.user_id,
                properties={
                    "channel": message.channel.value,
                    "intent": analysis.intent.value,
                    "confidence": analysis.confidence,
                    "sentiment": analysis.sentiment.value,
                    "stage": context.stage.value,
                    "lead_score": context.lead_score,
                    "message_count": context.message_count,
                }
            )
        except Exception as e:
            logger.error(f"Erro ao rastrear analytics: {e}")
    
    # ========================================
    # N8N INTEGRATION
    # ========================================
    
    async def _trigger_support_alert(
        self,
        context: ConversationContext,
        complaint: str
    ):
        """Dispara alerta de suporte no n8n."""
        if not self.n8n_client:
            return
        
        try:
            await self.n8n_client.trigger_webhook(
                webhook_path="/didin/support-alert",
                data={
                    "user_id": context.user_id,
                    "user_name": context.user_name,
                    "channel": context.channel.value,
                    "complaint": complaint,
                    "sentiment": context.sentiment_history[-1] if context.sentiment_history else "unknown",
                    "lead_score": context.lead_score,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Erro ao disparar alerta n8n: {e}")
    
    # ========================================
    # HELPERS
    # ========================================
    
    def _mock_product_search(self, query: str) -> List[Dict]:
        """Mock de busca de produtos para demonstração."""
        return [
            {
                "id": "1",
                "name": f"iPhone 15 Pro Max 256GB",
                "min_price": 7999.00,
                "store": "Amazon",
                "price_change": "-5%",
                "description": "Apple iPhone 15 Pro Max com chip A17 Pro",
                "url": "https://amazon.com.br/...",
            },
            {
                "id": "2",
                "name": f"iPhone 15 Pro 128GB",
                "min_price": 6799.00,
                "store": "Magalu",
                "price_change": "-3%",
                "description": "Apple iPhone 15 Pro com chip A17 Pro",
                "url": "https://magalu.com.br/...",
            },
            {
                "id": "3",
                "name": f"iPhone 14 128GB",
                "min_price": 4199.00,
                "store": "Casas Bahia",
                "price_change": "-10%",
                "description": "Apple iPhone 14 com chip A15 Bionic",
                "url": "https://casasbahia.com.br/...",
            },
        ]
    
    def _format_product_list(self, products: List[Dict]) -> str:
        """Formata lista de produtos para exibição."""
        lines = []
        for i, p in enumerate(products, 1):
            lines.append(f"{i}️⃣ *{p['name']}*")
            lines.append(f"   💰 R$ {p['min_price']:,.2f} - {p['store']}")
            lines.append("")
        return "\n".join(lines)


# ============================================
# FACTORY FUNCTION
# ============================================

def create_seller_bot(
    product_service=None,
    crm_service=None,
    analytics_service=None,
    ai_client=None,
    n8n_client=None,
) -> ProfessionalSellerBot:
    """
    Factory function para criar o Seller Bot.
    
    Uso:
        from modules.chatbot import create_seller_bot
        
        bot = create_seller_bot(
            product_service=product_service,
            crm_service=crm_service
        )
        
        responses = await bot.process_message(message)
    """
    return ProfessionalSellerBot(
        product_service=product_service,
        crm_service=crm_service,
        analytics_service=analytics_service,
        ai_client=ai_client,
        n8n_client=n8n_client,
    )
