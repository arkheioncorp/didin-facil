"""
Instagram Hub Adapter
====================
Adaptador para integrar o Seller Bot com o Hub Centralizado de Instagram.

Este adaptador implementa a interface ChannelAdapter do Seller Bot,
mas delega todas as operações para o InstagramHub centralizado.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .channel_integrations import ChannelAdapter
from .professional_seller_bot import (
    IncomingMessage,
    BotResponse,
    MessageChannel,
)
from integrations.instagram_hub import (
    InstagramHub,
    InstagramMessage,
    InstagramMessageType,
)

logger = logging.getLogger(__name__)


class InstagramHubAdapter(ChannelAdapter):
    """
    Adaptador que conecta o Seller Bot ao Instagram Hub.
    
    Substitui o antigo InstagramAdapter, centralizando a lógica
    no InstagramHub.
    """
    
    def __init__(self, hub: InstagramHub):
        self.hub = hub
        
    async def parse_incoming(
        self, payload: Dict[str, Any]
    ) -> Optional[IncomingMessage]:
        """
        Converte payload do webhook (via Hub) para IncomingMessage.
        """
        try:
            # O Hub normaliza o webhook do Instagram
            message = self.hub.normalize_webhook_event(payload)
            if not message:
                return None

            # Converter InstagramMessage para IncomingMessage (Seller Bot)
            return IncomingMessage(
                channel=MessageChannel.INSTAGRAM,
                sender_id=message.sender_id,
                sender_name=None,  # Instagram não fornece nome via webhook
                sender_phone=None,
                content=message.content or "",
                media_url=message.media_url,
                media_type=message.message_type.value,
                metadata={
                    "message_id": message.message_id,
                    "recipient_id": message.recipient_id,
                    "timestamp": message.timestamp.isoformat(),
                    "is_echo": message.is_echo
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao converter mensagem Instagram Hub: {e}")
            return None

    async def send_response(
        self, response: BotResponse, recipient_id: str
    ) -> bool:
        """Envia resposta usando o Hub."""
        try:
            # Enviar texto com quick replies
            if response.content and response.quick_replies:
                await self.hub.send_quick_replies(
                    recipient_id, 
                    response.content, 
                    response.quick_replies
                )
            elif response.content:
                await self.hub.send_message(recipient_id, response.content)
            
            # Enviar mídia se houver
            if response.media_url:
                media_type = response.media_type or "image"
                await self.hub.send_media(
                    recipient_id,
                    response.media_url,
                    media_type
                )
                
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar resposta via Instagram Hub: {e}")
            return False

    async def send_typing(
        self, recipient_id: str, duration_ms: int = 3000
    ) -> bool:
        """Envia status de digitando."""
        try:
            return await self.hub.send_typing(recipient_id, duration_ms)
        except Exception as e:
            logger.error(f"Erro ao enviar typing: {e}")
            return False
