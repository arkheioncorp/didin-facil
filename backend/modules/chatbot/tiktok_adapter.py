"""
TikTok Hub Adapter
=================
Adaptador para integrar o Seller Bot com o Hub Centralizado de TikTok.

Este adaptador implementa a interface ChannelAdapter do Seller Bot,
mas delega todas as operações para o TikTokHub centralizado.

NOTA: TikTok não possui API oficial de mensagens diretas.
Este adapter é um placeholder para futuras integrações.
"""

import logging
from typing import Optional, Dict, Any

from .channel_integrations import ChannelAdapter
from .professional_seller_bot import (
    IncomingMessage,
    BotResponse,
    MessageChannel,
)
from integrations.tiktok_hub import TikTokHub

logger = logging.getLogger(__name__)


class TikTokHubAdapter(ChannelAdapter):
    """
    Adaptador que conecta o Seller Bot ao TikTok Hub.
    
    Substitui o antigo TikTokAdapter, centralizando a lógica
    no TikTokHub.
    
    IMPORTANTE: TikTok não possui API oficial de mensagens.
    """
    
    def __init__(self, hub: TikTokHub):
        self.hub = hub
        
    async def parse_incoming(
        self, payload: Dict[str, Any]
    ) -> Optional[IncomingMessage]:
        """
        Converte payload do webhook (via Hub) para IncomingMessage.
        
        NOTA: TikTok não possui webhooks oficiais de mensagens ainda.
        """
        logger.warning("TikTok não suporta webhooks de mensagens oficialmente")
        return None

    async def send_response(
        self, response: BotResponse, recipient_id: str
    ) -> bool:
        """
        Envia resposta usando o Hub.
        
        NOTA: TikTok não possui API oficial de mensagens diretas.
        """
        try:
            await self.hub.send_message(recipient_id, response.content)
            return True
        except NotImplementedError:
            logger.warning(
                "Envio de mensagens TikTok não implementado "
                "(API oficial não disponível)"
            )
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar resposta via TikTok Hub: {e}")
            return False

    async def send_typing(
        self, recipient_id: str, duration_ms: int = 3000
    ) -> bool:
        """
        Envia status de digitando.
        
        NOTA: Não suportado pelo TikTok.
        """
        return False
