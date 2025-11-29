"""
Typebot Integration
===================
Integração com Typebot para chatbots visuais.

Typebot: https://github.com/baptisteArno/typebot.io
License: AGPL-3.0

Este módulo permite:
- Iniciar conversas com bots
- Enviar/receber mensagens
- Gerenciar sessões
- Sincronizar com WhatsApp
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import httpx
import logging

logger = logging.getLogger(__name__)


class InputType(Enum):
    TEXT = "text input"
    NUMBER = "number input"
    EMAIL = "email input"
    URL = "url input"
    DATE = "date input"
    PHONE = "phone number input"
    CHOICE = "choice input"
    PAYMENT = "payment input"
    FILE = "file input"


@dataclass
class TypebotConfig:
    """Configuração para Typebot."""
    api_url: str  # Ex: https://typebot.io ou self-hosted
    api_token: Optional[str] = None  # Para endpoints autenticados
    public_id: Optional[str] = None  # ID público do bot


@dataclass
class ChatSession:
    """Sessão de chat com o Typebot."""
    session_id: str
    typebot_id: str
    messages: List[Dict[str, Any]]
    current_input: Optional[Dict[str, Any]] = None
    is_completed: bool = False


@dataclass
class BotMessage:
    """Mensagem do bot."""
    content: str
    type: str  # text, image, video, etc.
    rich_content: Optional[Dict[str, Any]] = None


@dataclass
class InputRequest:
    """Solicitação de input do bot."""
    input_type: InputType
    options: Optional[List[str]] = None  # Para choice input
    placeholder: Optional[str] = None


class TypebotClient:
    """
    Cliente para API do Typebot.
    
    Uso:
        config = TypebotConfig(
            api_url="https://typebot.io",
            public_id="my-bot-id"
        )
        
        client = TypebotClient(config)
        
        # Iniciar conversa
        session = await client.start_chat()
        
        # Responder
        response = await client.send_message(session.session_id, "Olá!")
        
        # Processar resposta
        for msg in response.messages:
            print(f"Bot: {msg['content']}")
    """
    
    def __init__(self, config: TypebotConfig):
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.api_url.rstrip('/'),
            timeout=30.0
        )
        
        if config.api_token:
            self._client.headers["Authorization"] = f"Bearer {config.api_token}"
    
    async def close(self):
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    # ==================== Chat API ====================
    
    async def start_chat(
        self,
        typebot_id: Optional[str] = None,
        prefilted_variables: Optional[Dict[str, Any]] = None
    ) -> ChatSession:
        """
        Inicia uma nova conversa.
        
        Args:
            typebot_id: ID do bot (usa config.public_id se não fornecido)
            prefilted_variables: Variáveis pré-definidas
            
        Returns:
            Sessão de chat com mensagens iniciais
        """
        bot_id = typebot_id or self.config.public_id
        if not bot_id:
            raise ValueError("typebot_id é obrigatório")
        
        payload = {}
        if prefilted_variables:
            payload["prefilledVariables"] = prefilted_variables
        
        response = await self._client.post(
            f"/api/v1/typebots/{bot_id}/startChat",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        return ChatSession(
            session_id=data.get("sessionId", ""),
            typebot_id=bot_id,
            messages=data.get("messages", []),
            current_input=data.get("input"),
            is_completed=data.get("isCompleted", False)
        )
    
    async def send_message(
        self,
        session_id: str,
        message: str
    ) -> ChatSession:
        """
        Envia mensagem para a conversa.
        
        Args:
            session_id: ID da sessão
            message: Mensagem do usuário
            
        Returns:
            Sessão atualizada com novas mensagens
        """
        response = await self._client.post(
            f"/api/v1/sessions/{session_id}/continueChat",
            json={"message": message}
        )
        response.raise_for_status()
        data = response.json()
        
        return ChatSession(
            session_id=session_id,
            typebot_id="",  # Não retornado na resposta
            messages=data.get("messages", []),
            current_input=data.get("input"),
            is_completed=data.get("isCompleted", False)
        )
    
    async def set_variable(
        self,
        session_id: str,
        variable_name: str,
        value: Any
    ) -> bool:
        """Define variável na sessão."""
        try:
            response = await self._client.post(
                f"/api/v1/sessions/{session_id}/setVariable",
                json={"name": variable_name, "value": value}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Erro ao definir variável: {e}")
            return False
    
    # ==================== Bot Management ====================
    
    async def list_bots(self) -> List[Dict[str, Any]]:
        """Lista bots disponíveis (requer autenticação)."""
        response = await self._client.get("/api/v1/typebots")
        response.raise_for_status()
        data = response.json()
        
        return [
            {
                "id": bot["id"],
                "name": bot["name"],
                "public_id": bot.get("publicId")
            }
            for bot in data.get("typebots", [])
        ]
    
    async def get_bot(self, typebot_id: str) -> Dict[str, Any]:
        """Obtém detalhes de um bot."""
        response = await self._client.get(f"/api/v1/typebots/{typebot_id}")
        response.raise_for_status()
        return response.json()
    
    # ==================== Results ====================
    
    async def get_results(
        self,
        typebot_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtém resultados/respostas coletadas.
        
        Útil para ver dados de leads capturados.
        """
        response = await self._client.get(
            f"/api/v1/typebots/{typebot_id}/results",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json().get("results", [])


# ==================== WhatsApp Integration ====================

class TypebotWhatsAppBridge:
    """
    Ponte entre WhatsApp e Typebot.
    
    Permite usar Typebot como backend de chatbot para WhatsApp.
    
    Uso:
        typebot = TypebotClient(typebot_config)
        whatsapp = WhatsAppClient(whatsapp_config)
        
        bridge = TypebotWhatsAppBridge(typebot, whatsapp, "bot-id")
        
        # No webhook do WhatsApp:
        await bridge.handle_message(incoming_message)
    """
    
    def __init__(
        self,
        typebot_client: TypebotClient,
        whatsapp_client: Any,  # WhatsAppClient
        typebot_id: str
    ):
        self.typebot = typebot_client
        self.whatsapp = whatsapp_client
        self.typebot_id = typebot_id
        
        # Cache de sessões: phone -> session_id
        self._sessions: Dict[str, str] = {}
    
    async def handle_message(
        self,
        from_number: str,
        message: str,
        prefilted_variables: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Processa mensagem do WhatsApp via Typebot.
        
        Args:
            from_number: Número do remetente
            message: Mensagem recebida
            prefilted_variables: Variáveis iniciais (ex: nome do contato)
            
        Returns:
            Lista de mensagens de resposta
        """
        responses = []
        
        # Verificar sessão existente ou criar nova
        if from_number not in self._sessions:
            session = await self.typebot.start_chat(
                self.typebot_id,
                prefilted_variables
            )
            self._sessions[from_number] = session.session_id
            
            # Processar mensagens iniciais
            for msg in session.messages:
                if msg.get("type") == "text":
                    content = msg.get("content", {}).get("richText", [])
                    text = self._extract_text(content)
                    if text:
                        responses.append(text)
                        await self.whatsapp.send_text(from_number, text)
        
        # Enviar mensagem do usuário
        session_id = self._sessions[from_number]
        
        try:
            session = await self.typebot.send_message(session_id, message)
            
            # Processar respostas
            for msg in session.messages:
                if msg.get("type") == "text":
                    content = msg.get("content", {}).get("richText", [])
                    text = self._extract_text(content)
                    if text:
                        responses.append(text)
                        await self.whatsapp.send_text(from_number, text)
                
                elif msg.get("type") == "image":
                    url = msg.get("content", {}).get("url")
                    if url:
                        await self.whatsapp.send_image(from_number, url)
            
            # Verificar se conversa terminou
            if session.is_completed:
                del self._sessions[from_number]
                
        except Exception as e:
            logger.error(f"Erro no Typebot: {e}")
            # Reiniciar sessão em caso de erro
            if from_number in self._sessions:
                del self._sessions[from_number]
        
        return responses
    
    def _extract_text(self, rich_text: List[Dict]) -> str:
        """Extrai texto do formato rich text do Typebot."""
        texts = []
        for item in rich_text:
            if item.get("type") == "p":
                children = item.get("children", [])
                for child in children:
                    if isinstance(child, dict):
                        texts.append(child.get("text", ""))
                    elif isinstance(child, str):
                        texts.append(child)
        return " ".join(texts).strip()
    
    def clear_session(self, from_number: str):
        """Limpa sessão de um número."""
        if from_number in self._sessions:
            del self._sessions[from_number]
    
    def clear_all_sessions(self):
        """Limpa todas as sessões."""
        self._sessions.clear()
