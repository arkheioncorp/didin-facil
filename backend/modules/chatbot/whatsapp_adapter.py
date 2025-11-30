"""
WhatsApp Hub Adapter
===================
Adaptador para integrar o Seller Bot com o Hub Centralizado de WhatsApp.

Este adaptador implementa a interface ChannelAdapter do Seller Bot,
mas delega todas as operações para o WhatsAppHub centralizado.
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
from integrations.whatsapp_hub import WhatsAppHub, WhatsAppMessage, MessageType

logger = logging.getLogger(__name__)

class WhatsAppHubAdapter(ChannelAdapter):
    """
    Adaptador que conecta o Seller Bot ao WhatsApp Hub.
    
    Substitui o antigo EvolutionAdapter, centralizando a lógica
    no WhatsAppHub.
    """
    
    def __init__(self, hub: WhatsAppHub, instance_name: str):
        self.hub = hub
        self.instance_name = instance_name
        
    async def parse_incoming(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """
        Converte payload do webhook (via Hub) para IncomingMessage.
        
        Nota: O Hub já normaliza as mensagens, então aqui podemos
        receber tanto o payload bruto quanto um objeto WhatsAppMessage
        se o Hub já tiver processado.
        """
        try:
            # Se recebermos o payload bruto do webhook
            if isinstance(payload, dict) and "data" in payload:
                # O Hub tem método para normalizar webhook
                normalized = self.hub._normalize_webhook_message(payload)
                if not normalized:
                    return None
                message = normalized
            # Se já recebermos um objeto WhatsAppMessage (uso interno)
            elif isinstance(payload, WhatsAppMessage):
                message = payload
            else:
                # Tenta processar como payload bruto da Evolution
                normalized = self.hub._normalize_webhook_message(payload)
                if not normalized:
                    return None
                message = normalized

            # Converter WhatsAppMessage para IncomingMessage (Seller Bot)
            return IncomingMessage(
                channel=MessageChannel.WHATSAPP,
                sender_id=message.phone_number,
                sender_name=message.push_name or message.phone_number,
                sender_phone=message.phone_number,
                content=message.content or "",
                metadata={
                    "instance": self.instance_name,
                    "is_group": message.is_group,
                    "type": message.message_type.value,
                    "message_id": message.message_id,
                    "remote_jid": message.remote_jid
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao converter mensagem WhatsApp Hub: {e}")
            return None

    async def send_response(self, response: BotResponse, recipient_id: str) -> bool:
        """Envia resposta usando o Hub."""
        try:
            # Enviar texto
            if response.content:
                await self.hub.send_message(
                    instance_name=self.instance_name,
                    to=recipient_id,
                    message=response.content
                )
            
            # Enviar mídia se houver
            if response.media_url:
                media_type = response.media_type or "image"
                await self.hub.send_media(
                    instance_name=self.instance_name,
                    to=recipient_id,
                    media_url=response.media_url,
                    media_type=media_type,
                    caption=response.content if not response.content else None # Se já enviou texto, não manda caption
                )
                
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar resposta via WhatsApp Hub: {e}")
            return False

    async def send_typing(self, recipient_id: str, duration_ms: int = 3000) -> bool:
        """Envia status de digitando."""
        try:
            # O Hub ainda não tem método explícito de typing na interface pública,
            # mas podemos implementar se necessário ou ignorar por enquanto.
            # A Evolution API suporta presence update.
            
            # Implementação futura no Hub
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar typing: {e}")
            return False
