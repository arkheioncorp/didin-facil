"""
Typebot Integration
===================
Integração com Typebot para chatbots visuais.

Repository: https://github.com/baptisteArno/typebot.io
License: AGPL-3.0 (Self-hosted OK)

Funcionalidades:
- Iniciar conversas em fluxos específicos
- Continuar conversas existentes
- Webhook para respostas
- Gerenciar fluxos via API
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from shared.config import settings

logger = logging.getLogger(__name__)


class TypebotStatus(str, Enum):
    """Status da sessão de chat."""
    ACTIVE = "active"
    COMPLETED = "completed"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class TypebotMessage:
    """Mensagem do Typebot."""
    id: str
    type: str  # text, image, video, audio, file, choice
    content: Any
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class TypebotSession:
    """Sessão de conversa com Typebot."""
    session_id: str
    typebot_id: str
    user_id: Optional[str] = None
    status: TypebotStatus = TypebotStatus.ACTIVE
    current_block: Optional[str] = None
    variables: Dict[str, Any] = None
    messages: List[TypebotMessage] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.messages is None:
            self.messages = []
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)


class TypebotClient:
    """
    Cliente para integração com Typebot.
    
    Uso:
        client = TypebotClient()
        
        # Iniciar conversa
        session = await client.start_chat(
            typebot_id="ofertas-bot",
            user_id="user123",
            variables={"nome": "João"}
        )
        
        # Continuar conversa
        response = await client.send_message(
            session_id=session.session_id,
            message="Quero ver ofertas de celular"
        )
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.api_url = api_url or settings.TYPEBOT_API_URL or "http://localhost:3000"
        self.api_key = api_key or settings.TYPEBOT_API_KEY
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtém cliente HTTP com configuração."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=headers,
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        """Fecha cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # ========================================
    # CHAT OPERATIONS
    # ========================================
    
    async def start_chat(
        self,
        typebot_id: str,
        user_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        prefilledVariables: Optional[Dict[str, Any]] = None
    ) -> TypebotSession:
        """
        Inicia uma nova sessão de chat.
        
        Args:
            typebot_id: ID do fluxo no Typebot
            user_id: ID do usuário (opcional)
            variables: Variáveis iniciais
            prefilledVariables: Variáveis pré-preenchidas
        
        Returns:
            TypebotSession com session_id e mensagens iniciais
        """
        client = await self._get_client()
        
        payload = {
            "startParams": {
                "isPreview": False
            }
        }
        
        if variables:
            payload["startParams"]["typebot"] = {"variables": variables}
        
        if prefilledVariables:
            payload["prefilledVariables"] = prefilledVariables
        
        try:
            response = await client.post(
                f"/api/v1/typebots/{typebot_id}/startChat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            # Extrair mensagens da resposta
            messages = []
            for msg in data.get("messages", []):
                messages.append(TypebotMessage(
                    id=msg.get("id", ""),
                    type=msg.get("type", "text"),
                    content=msg.get("content", {})
                ))
            
            session = TypebotSession(
                session_id=data.get("sessionId", ""),
                typebot_id=typebot_id,
                user_id=user_id,
                status=TypebotStatus.ACTIVE,
                variables=variables or {},
                messages=messages
            )
            
            logger.info(f"Started Typebot session: {session.session_id}")
            return session
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to start Typebot chat: {e}")
            raise
    
    async def send_message(
        self,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Envia mensagem para sessão existente.
        
        Args:
            session_id: ID da sessão
            message: Texto da mensagem
        
        Returns:
            Dict com mensagens de resposta do bot
        """
        client = await self._get_client()
        
        payload = {
            "message": message
        }
        
        try:
            response = await client.post(
                f"/api/v1/sessions/{session_id}/continueChat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            # Processar resposta
            messages = []
            for msg in data.get("messages", []):
                messages.append(TypebotMessage(
                    id=msg.get("id", ""),
                    type=msg.get("type", "text"),
                    content=msg.get("content", {})
                ))
            
            return {
                "messages": messages,
                "input": data.get("input"),
                "clientSideActions": data.get("clientSideActions", [])
            }
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to send message to Typebot: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtém informações da sessão."""
        client = await self._get_client()
        
        try:
            response = await client.get(f"/api/v1/sessions/{session_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    # ========================================
    # TYPEBOT MANAGEMENT
    # ========================================
    
    async def list_typebots(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista todos os typebots disponíveis."""
        client = await self._get_client()
        
        params = {}
        if workspace_id:
            params["workspaceId"] = workspace_id
        
        try:
            response = await client.get("/api/v1/typebots", params=params)
            response.raise_for_status()
            return response.json().get("typebots", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to list typebots: {e}")
            raise
    
    async def get_typebot(self, typebot_id: str) -> Optional[Dict[str, Any]]:
        """Obtém detalhes de um typebot específico."""
        client = await self._get_client()
        
        try:
            response = await client.get(f"/api/v1/typebots/{typebot_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def get_results(
        self,
        typebot_id: str,
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtém resultados/respostas de um typebot.
        
        Args:
            typebot_id: ID do typebot
            limit: Número máximo de resultados
            cursor: Cursor para paginação
        
        Returns:
            Dict com results e nextCursor
        """
        client = await self._get_client()
        
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        try:
            response = await client.get(
                f"/api/v1/typebots/{typebot_id}/results",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get typebot results: {e}")
            raise


class TypebotWebhookHandler:
    """
    Handler para webhooks do Typebot.
    
    Processa eventos como:
    - Conversa iniciada
    - Mensagem recebida
    - Conversa finalizada
    - Variáveis atualizadas
    """
    
    def __init__(self):
        self._handlers: Dict[str, callable] = {}
    
    def on(self, event_type: str):
        """Decorator para registrar handlers."""
        def decorator(func):
            self._handlers[event_type] = func
            return func
        return decorator
    
    async def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa payload de webhook do Typebot.
        
        Args:
            payload: Dados do webhook
        
        Returns:
            Resposta para o Typebot (se necessário)
        """
        event_type = payload.get("type", "unknown")
        
        handler = self._handlers.get(event_type)
        if handler:
            try:
                return await handler(payload)
            except Exception as e:
                logger.error(f"Error processing Typebot webhook: {e}")
                return {"error": str(e)}
        
        logger.warning(f"No handler for Typebot event: {event_type}")
        return {"status": "ignored"}


# ============================================
# TEMPLATES DE FLUXOS PARA DIDIN FÁCIL
# ============================================

DIDIN_TYPEBOT_TEMPLATES = {
    "welcome_flow": {
        "name": "Boas-vindas TikTrend Finder",
        "description": "Fluxo de onboarding para novos usuários",
        "category": "engagement",
        "preview_url": "",
        "tags": ["onboarding", "bem-vindo", "introdução"],
        "blocks": [
            {"type": "text", "content": "👋 Olá! Bem-vindo ao TikTrend Finder!"},
            {"type": "text", "content": "Sou o assistente virtual e vou te ajudar a economizar."},
            {"type": "choice", "content": "O que você procura hoje?", "options": [
                "🔍 Comparar preços",
                "📱 Ofertas de celulares",
                "💻 Ofertas de notebooks",
                "🎧 Ofertas de eletrônicos"
            ]}
        ]
    },
    "price_alert_flow": {
        "name": "Alerta de Preços",
        "description": "Fluxo para configurar alertas de preço",
        "category": "sales",
        "preview_url": "",
        "tags": ["alertas", "preço", "monitoramento"],
        "blocks": [
            {"type": "text", "content": "🔔 Vamos configurar seu alerta de preço!"},
            {"type": "input", "content": "Qual produto você quer monitorar?", "variable": "product_name"},
            {"type": "input", "content": "Qual o preço máximo que você quer pagar?", "variable": "max_price"},
            {"type": "text", "content": "Pronto! Vou te avisar quando {{product_name}} estiver por R$ {{max_price}} ou menos."}
        ]
    },
    "support_flow": {
        "name": "Suporte ao Cliente",
        "description": "Fluxo de atendimento e FAQ",
        "category": "support",
        "preview_url": "",
        "tags": ["suporte", "ajuda", "FAQ"],
        "blocks": [
            {"type": "text", "content": "💬 Como posso te ajudar?"},
            {"type": "choice", "content": "Escolha uma opção:", "options": [
                "❓ Perguntas frequentes",
                "🔧 Problema técnico",
                "💳 Dúvidas sobre pagamento",
                "👤 Falar com atendente"
            ]}
        ]
    },
    "lead_capture_flow": {
        "name": "Captura de Leads",
        "description": "Coletar informações de potenciais clientes",
        "category": "sales",
        "preview_url": "",
        "tags": ["leads", "cadastro", "conversão"],
        "blocks": [
            {"type": "text", "content": "📋 Vamos cadastrar você para receber ofertas exclusivas!"},
            {"type": "input", "content": "Qual é o seu nome?", "variable": "name"},
            {"type": "input", "content": "Qual é o seu email?", "variable": "email"},
            {"type": "input", "content": "Qual é o seu telefone?", "variable": "phone"},
            {"type": "choice", "content": "Qual categoria de produtos te interessa mais?", "options": [
                "📱 Eletrônicos",
                "👗 Moda e Vestuário",
                "🏠 Casa e Decoração",
                "🎮 Games e Entretenimento",
                "📚 Livros e Educação"
            ], "variable": "interest"},
            {"type": "text", "content": "Perfeito, {{name}}! Você vai receber nossas melhores ofertas de {{interest}} no email {{email}}. 🎉"}
        ]
    },
    "product_recommendation_flow": {
        "name": "Recomendação de Produtos",
        "description": "Ajudar clientes a encontrar o produto ideal",
        "category": "sales",
        "preview_url": "",
        "tags": ["recomendação", "vendas", "produto"],
        "blocks": [
            {"type": "text", "content": "🛍️ Vou te ajudar a encontrar o produto perfeito!"},
            {"type": "choice", "content": "Qual tipo de produto você procura?", "options": [
                "📱 Smartphone",
                "💻 Notebook",
                "🎧 Fones de Ouvido",
                "⌚ Smart Watch",
                "📷 Câmera"
            ], "variable": "product_type"},
            {"type": "choice", "content": "Qual é o seu orçamento?", "options": [
                "💰 Até R$ 500",
                "💵 R$ 500 - R$ 1.500",
                "💸 R$ 1.500 - R$ 3.000",
                "💎 Acima de R$ 3.000"
            ], "variable": "budget"},
            {"type": "text", "content": "Ótimo! Estou buscando os melhores {{product_type}} dentro do seu orçamento..."},
            {"type": "text", "content": "Encontrei 3 opções perfeitas para você! Clique abaixo para ver:"}
        ]
    }
}


# Factory function para obter cliente configurado
_typebot_client: Optional[TypebotClient] = None


def get_typebot_client() -> TypebotClient:
    """
    Obtém instância singleton do cliente Typebot.
    
    Returns:
        TypebotClient configurado
    """
    global _typebot_client
    
    if _typebot_client is None:
        _typebot_client = TypebotClient(
            base_url=getattr(settings, 'TYPEBOT_URL', 'http://localhost:3000'),
            api_key=getattr(settings, 'TYPEBOT_API_KEY', None),
        )
    
    return _typebot_client
