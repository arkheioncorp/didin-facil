"""
Channel Integrations - Integrações de Canal
============================================
Adaptadores para diferentes canais de comunicação.

Suporta:
- WhatsApp (Evolution API)
- Instagram (API de Mensagens)
- TikTok (Mensagens)
- Chatwoot (Unified inbox)
"""

import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .professional_seller_bot import (
    IncomingMessage,
    BotResponse,
    MessageChannel,
)
from integrations.whatsapp_hub import WhatsAppHub
from integrations.instagram_hub import InstagramHub, get_instagram_hub, InstagramHubConfig
from integrations.tiktok_hub import TikTokHub, get_tiktok_hub, TikTokHubConfig

logger = logging.getLogger(__name__)


# ============================================
# BASE ADAPTER
# ============================================

class ChannelAdapter(ABC):
    """Interface base para adaptadores de canal."""
    
    @abstractmethod
    async def parse_incoming(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Converte payload do canal para IncomingMessage."""
        pass
    
    @abstractmethod
    async def send_response(self, response: BotResponse, recipient_id: str) -> bool:
        """Envia resposta para o canal."""
        pass
    
    @abstractmethod
    async def send_typing(self, recipient_id: str, duration_ms: int = 3000) -> bool:
        """Envia indicador de digitação."""
        pass


# ============================================
# EVOLUTION API ADAPTER (WHATSAPP)
# ============================================

@dataclass
class EvolutionConfig:
    """Configuração da Evolution API."""
    api_url: str = "http://localhost:8080"
    api_key: str = ""
    instance_name: str = "tiktrend-bot"


class EvolutionAdapter(ChannelAdapter):
    """
    Adaptador para Evolution API (WhatsApp).
    
    DEPRECATED: Esta classe agora é um wrapper para o WhatsAppHubAdapter.
    Prefira usar WhatsAppHubAdapter diretamente.
    """
    
    def __init__(self, config: EvolutionConfig):
        from .whatsapp_adapter import WhatsAppHubAdapter
        self.config = config
        # Inicializa o Hub com as configurações fornecidas
        # Nota: Para integração completa com Chatwoot, o Hub deve ser configurado via variáveis de ambiente
        # ou passado externamente. Aqui usamos o que temos no config.
        self.hub = WhatsAppHub(
            evolution_url=config.api_url,
            evolution_key=config.api_key
        )
        self.adapter = WhatsAppHubAdapter(self.hub, config.instance_name)
    
    async def close(self):
        # Hub não precisa de fechamento explícito de cliente HTTP persistente por enquanto,
        # mas se precisar, implementamos no Hub.
        pass
    
    async def parse_incoming(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Converte webhook da Evolution API para IncomingMessage usando o Hub."""
        return await self.adapter.parse_incoming(payload)
    
    async def send_response(self, response: BotResponse, recipient_id: str) -> bool:
        """Envia resposta via Evolution API usando o Hub."""
        return await self.adapter.send_response(response, recipient_id)
    
    async def send_typing(self, recipient_id: str, duration_ms: int = 3000) -> bool:
        """Envia indicador de digitação."""
        return await self.adapter.send_typing(recipient_id, duration_ms)


# ============================================
# CHATWOOT ADAPTER
# ============================================

@dataclass
class ChatwootConfig:
    """Configuração do Chatwoot."""
    api_url: str = "http://localhost:3000"
    api_token: str = ""
    account_id: int = 1
    inbox_id: Optional[int] = None


class ChatwootAdapter(ChannelAdapter):
    """
    Adaptador para Chatwoot (unified inbox).
    
    Uso:
        adapter = ChatwootAdapter(config)
        message = await adapter.parse_incoming(webhook_payload)
        await adapter.send_response(response, conversation_id)
    """
    
    def __init__(self, config: ChatwootConfig):
        self.config = config
        self.base_url = f"{config.api_url}/api/v1/accounts/{config.account_id}"
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "api_access_token": self.config.api_token,
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def parse_incoming(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Converte webhook do Chatwoot para IncomingMessage."""
        try:
            event = payload.get("event")
            
            # Só processar mensagens recebidas
            if event != "message_created":
                return None
            
            message_data = payload.get("message", {})
            conversation = payload.get("conversation", {})
            sender = payload.get("sender", {})
            
            # Ignorar mensagens do bot
            if message_data.get("message_type") != "incoming":
                return None
            
            # Determinar canal baseado no inbox
            inbox = conversation.get("inbox", {})
            channel_type = inbox.get("channel_type", "").lower()
            
            if "whatsapp" in channel_type:
                channel = MessageChannel.WHATSAPP
            elif "instagram" in channel_type:
                channel = MessageChannel.INSTAGRAM
            elif "telegram" in channel_type:
                channel = MessageChannel.TELEGRAM
            else:
                channel = MessageChannel.WEBCHAT
            
            # Extrair mídia
            media_url = None
            media_type = None
            attachments = message_data.get("attachments", [])
            if attachments:
                first_attachment = attachments[0]
                media_url = first_attachment.get("data_url")
                media_type = first_attachment.get("file_type")
            
            return IncomingMessage(
                channel=channel,
                sender_id=str(sender.get("id", "")),
                sender_name=sender.get("name", ""),
                sender_phone=sender.get("phone_number"),
                content=message_data.get("content", ""),
                media_url=media_url,
                media_type=media_type,
                metadata={
                    "conversation_id": conversation.get("id"),
                    "message_id": message_data.get("id"),
                    "inbox_id": inbox.get("id"),
                    "contact_id": sender.get("id"),
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao parsear webhook Chatwoot: {e}")
            return None
    
    async def send_response(self, response: BotResponse, recipient_id: str) -> bool:
        """Envia resposta via Chatwoot."""
        try:
            client = await self._get_client()
            
            # recipient_id é o conversation_id no Chatwoot
            conversation_id = recipient_id
            
            # Payload base
            payload = {
                "content": response.content,
                "message_type": "outgoing",
                "private": False,
            }
            
            # Se tem quick replies, adicionar como botões
            if response.quick_replies:
                payload["content_attributes"] = {
                    "items": [
                        {"title": qr, "value": qr}
                        for qr in response.quick_replies
                    ]
                }
            
            # Enviar
            resp = await client.post(
                f"/conversations/{conversation_id}/messages",
                json=payload
            )
            resp.raise_for_status()
            
            logger.info(f"Mensagem enviada para conversa {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem Chatwoot: {e}")
            return False
    
    async def send_typing(self, recipient_id: str, duration_ms: int = 3000) -> bool:
        """Envia indicador de digitação."""
        try:
            client = await self._get_client()
            
            await client.post(
                f"/conversations/{recipient_id}/toggle_typing_status",
                json={"typing_status": "on"}
            )
            
            import asyncio
            await asyncio.sleep(duration_ms / 1000)
            
            await client.post(
                f"/conversations/{recipient_id}/toggle_typing_status",
                json={"typing_status": "off"}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar typing Chatwoot: {e}")
            return False
    
    # ========================================
    # CHATWOOT SPECIFIC METHODS
    # ========================================
    
    async def assign_to_agent(self, conversation_id: str, agent_id: int) -> bool:
        """Atribui conversa a um agente."""
        try:
            client = await self._get_client()
            resp = await client.post(
                f"/conversations/{conversation_id}/assignments",
                json={"assignee_id": agent_id}
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Erro ao atribuir agente: {e}")
            return False
    
    async def add_labels(self, conversation_id: str, labels: List[str]) -> bool:
        """Adiciona labels à conversa."""
        try:
            client = await self._get_client()
            resp = await client.post(
                f"/conversations/{conversation_id}/labels",
                json={"labels": labels}
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar labels: {e}")
            return False
    
    async def update_custom_attributes(
        self,
        contact_id: int,
        attributes: Dict[str, Any]
    ) -> bool:
        """Atualiza atributos customizados do contato."""
        try:
            client = await self._get_client()
            resp = await client.patch(
                f"/contacts/{contact_id}",
                json={"custom_attributes": attributes}
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar atributos: {e}")
            return False
    
    async def handoff_to_human(self, conversation_id: str, reason: str) -> bool:
        """Escala conversa para atendimento humano."""
        try:
            # Adicionar label
            await self.add_labels(conversation_id, ["bot-handoff", reason])
            
            # Enviar nota interna
            client = await self._get_client()
            await client.post(
                f"/conversations/{conversation_id}/messages",
                json={
                    "content": f"🤖 Bot escalou: {reason}",
                    "message_type": "outgoing",
                    "private": True,
                }
            )
            
            # Remover bot como assignee (se configurado)
            # await self.assign_to_agent(conversation_id, None)
            
            return True
        except Exception as e:
            logger.error(f"Erro no handoff: {e}")
            return False


# ============================================
# INSTAGRAM ADAPTER
# ============================================

@dataclass
class InstagramConfig:
    """Configuração do Instagram."""
    access_token: str = ""
    page_id: str = ""
    app_secret: str = ""


class InstagramAdapter(ChannelAdapter):
    """
    Adaptador para Instagram Messaging API.
    
    DEPRECATED: Esta classe agora é um wrapper para o InstagramHubAdapter.
    Prefira usar InstagramHubAdapter diretamente.
    """
    
    def __init__(self, config: InstagramConfig):
        from .instagram_adapter import InstagramHubAdapter
        self.config = config
        # Configura o Hub singleton com as credenciais deste adapter
        self.hub = get_instagram_hub()
        self.hub.configure(
            access_token=config.access_token,
            page_id=config.page_id,
            app_secret=config.app_secret
        )
        self.adapter = InstagramHubAdapter(self.hub)
    
    async def close(self):
        # Hub é singleton, não fechamos aqui
        pass
    
    async def parse_incoming(
        self, payload: Dict[str, Any]
    ) -> Optional[IncomingMessage]:
        """Converte webhook usando o Hub."""
        return await self.adapter.parse_incoming(payload)
    
    async def send_response(
        self, response: BotResponse, recipient_id: str
    ) -> bool:
        """Envia resposta via Instagram Hub."""
        return await self.adapter.send_response(response, recipient_id)
    
    async def send_typing(
        self, recipient_id: str, duration_ms: int = 3000
    ) -> bool:
        """Envia indicador de digitação."""
        return await self.adapter.send_typing(recipient_id, duration_ms)


# ============================================
# TIKTOK ADAPTER
# ============================================

@dataclass
class TikTokConfig:
    """Configuração do TikTok."""
    headless: bool = True


class TikTokAdapter(ChannelAdapter):
    """
    Adaptador para TikTok.
    
    DEPRECATED: Esta classe agora é um wrapper para o TikTokHubAdapter.
    Prefira usar TikTokHubAdapter diretamente.
    
    Nota: Mensagens ainda não suportadas (TikTok não possui API oficial).
    """
    
    def __init__(self, config: TikTokConfig):
        from .tiktok_adapter import TikTokHubAdapter
        self.config = config
        self.hub = get_tiktok_hub()
        self.adapter = TikTokHubAdapter(self.hub)
    
    async def parse_incoming(
        self, payload: Dict[str, Any]
    ) -> Optional[IncomingMessage]:
        """Converte webhook do TikTok usando o Hub."""
        return await self.adapter.parse_incoming(payload)
    
    async def send_response(
        self, response: BotResponse, recipient_id: str
    ) -> bool:
        """Envia resposta via TikTok Hub."""
        return await self.adapter.send_response(response, recipient_id)
    
    async def send_typing(
        self, recipient_id: str, duration_ms: int = 3000
    ) -> bool:
        """Envia indicador de digitação."""
        return await self.adapter.send_typing(recipient_id, duration_ms)


# ============================================
# CHANNEL ROUTER
# ============================================

class ChannelRouter:
    """
    Router que gerencia múltiplos adaptadores de canal.
    
    Uso:
        router = ChannelRouter()
        router.register_adapter(MessageChannel.WHATSAPP, evolution_adapter)
        router.register_adapter(MessageChannel.INSTAGRAM, instagram_adapter)
        
        message = await router.parse_incoming(channel, payload)
        await router.send_response(channel, response, recipient_id)
    """
    
    def __init__(self):
        self._adapters: Dict[MessageChannel, ChannelAdapter] = {}
    
    def register_adapter(self, channel: MessageChannel, adapter: ChannelAdapter):
        """Registra adaptador para um canal."""
        self._adapters[channel] = adapter
        logger.info(f"Adaptador registrado para canal {channel.value}")
    
    def get_adapter(self, channel: MessageChannel) -> Optional[ChannelAdapter]:
        """Obtém adaptador para um canal."""
        return self._adapters.get(channel)
    
    async def parse_incoming(
        self,
        channel: MessageChannel,
        payload: Dict[str, Any]
    ) -> Optional[IncomingMessage]:
        """Parseia mensagem usando adaptador do canal."""
        adapter = self._adapters.get(channel)
        if not adapter:
            logger.warning(f"Nenhum adaptador para canal {channel.value}")
            return None
        return await adapter.parse_incoming(payload)
    
    async def send_response(
        self,
        channel: MessageChannel,
        response: BotResponse,
        recipient_id: str
    ) -> bool:
        """Envia resposta usando adaptador do canal."""
        adapter = self._adapters.get(channel)
        if not adapter:
            logger.warning(f"Nenhum adaptador para canal {channel.value}")
            return False
        return await adapter.send_response(response, recipient_id)
    
    async def send_typing(
        self,
        channel: MessageChannel,
        recipient_id: str,
        duration_ms: int = 3000
    ) -> bool:
        """Envia typing usando adaptador do canal."""
        adapter = self._adapters.get(channel)
        if not adapter:
            return False
        return await adapter.send_typing(recipient_id, duration_ms)
    
    async def close_all(self):
        """Fecha todos os adaptadores."""
        for adapter in self._adapters.values():
            await adapter.close()


# ============================================
# FACTORY FUNCTIONS
# ============================================

def create_evolution_adapter(
    api_url: str = "http://localhost:8080",
    api_key: str = "",
    instance_name: str = "tiktrend-bot"
) -> EvolutionAdapter:
    """Cria adaptador Evolution API."""
    config = EvolutionConfig(
        api_url=api_url,
        api_key=api_key,
        instance_name=instance_name
    )
    return EvolutionAdapter(config)


def create_chatwoot_adapter(
    api_url: str = "http://localhost:3000",
    api_token: str = "",
    account_id: int = 1
) -> ChatwootAdapter:
    """Cria adaptador Chatwoot."""
    config = ChatwootConfig(
        api_url=api_url,
        api_token=api_token,
        account_id=account_id
    )
    return ChatwootAdapter(config)


def create_instagram_adapter(
    access_token: str = "",
    page_id: str = ""
) -> InstagramAdapter:
    """Cria adaptador Instagram."""
    config = InstagramConfig(
        access_token=access_token,
        page_id=page_id
    )
    return InstagramAdapter(config)
