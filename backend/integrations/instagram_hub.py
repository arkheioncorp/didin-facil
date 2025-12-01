"""
Instagram Integration Hub
=========================
Ponto central de integração do Instagram para o Didin Fácil.

Este módulo consolida todas as integrações com Instagram via Graph API:
- Envio de mensagens (Direct)
- Webhooks
- Gerenciamento de posts/comentários (futuro)

Autor: Didin Fácil
Versão: 1.1.0 (com alertas e métricas)
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx
from api.services.instagram_session import InstagramSessionManager

from .alerts import get_alert_manager
from .metrics import get_metrics_registry
from .resilience import (CircuitBreaker, CircuitBreakerConfig,
                         CircuitBreakerOpenError, RetryConfig,
                         retry_with_backoff)

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

@dataclass
class InstagramHubConfig:
    """Configuração centralizada do Instagram Hub."""
    access_token: str = ""
    page_id: str = ""
    app_secret: str = ""
    verify_token: str = ""  # Para verificação do webhook
    graph_version: str = "v18.0"
    
    # Private API config
    private_api_enabled: bool = False
    
    # Resilience config
    max_retries: int = 3
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 30.0

class InstagramMessageType(Enum):
    """Tipos de mensagem suportados."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    STORY_MENTION = "story_mention"
    REPLY = "reply"

@dataclass
class InstagramMessage:
    """Representação padronizada de uma mensagem Instagram."""
    message_id: str
    sender_id: str
    recipient_id: str
    timestamp: datetime
    message_type: InstagramMessageType
    content: Optional[str] = None
    media_url: Optional[str] = None
    is_echo: bool = False

# ============================================
# HUB CLASS
# ============================================

class InstagramHub:
    """
    Hub central para operações do Instagram.
    """
    
    def __init__(self, config: Optional[InstagramHubConfig] = None):
        self.config = config or InstagramHubConfig()
        self.base_url = f"https://graph.facebook.com/{self.config.graph_version}"
        self._client: Optional[httpx.AsyncClient] = None
        self.session_manager = InstagramSessionManager()
        
        # Resiliência: Circuit Breaker para Graph API
        cb_config = CircuitBreakerConfig(
            failure_threshold=self.config.circuit_breaker_threshold,
            timeout_seconds=self.config.circuit_breaker_timeout,
            half_open_max_calls=3
        )
        self._circuit_breaker = CircuitBreaker(
            name="instagram_hub",
            config=cb_config
        )
        
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def configure(self, access_token: str, page_id: str, app_secret: str = ""):
        """Reconfigura o hub dinamicamente."""
        self.config.access_token = access_token
        self.config.page_id = page_id
        self.config.app_secret = app_secret

    # ============================================
    # SESSION MANAGEMENT (Private API)
    # ============================================

    async def get_session(self, username: str):
        """Recupera sessão privada."""
        return await self.session_manager.get_session(username)

    async def save_session(self, username: str, settings: Dict):
        """Salva sessão privada."""
        return await self.session_manager.save_session(username, settings)

    # ============================================
    # MESSAGING API
    # ============================================

    async def send_message(self, recipient_id: str, text: str) -> Dict[str, Any]:
        """Envia mensagem de texto."""
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }
        return await self._send_api_request(payload)

    async def send_quick_replies(self, recipient_id: str, text: str, options: List[str]) -> Dict[str, Any]:
        """Envia mensagem com respostas rápidas."""
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "text": text,
                "quick_replies": [
                    {
                        "content_type": "text",
                        "title": opt[:20],  # Limite de 20 chars
                        "payload": opt
                    }
                    for opt in options[:13]  # Limite de 13 opções
                ]
            }
        }
        return await self._send_api_request(payload)

    async def send_media(self, recipient_id: str, media_url: str, media_type: str = "image") -> Dict[str, Any]:
        """Envia mídia (imagem, vídeo, etc)."""
        attachment_type = "image" if media_type == "image" else "video" # Simplificação
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": attachment_type,
                    "payload": {
                        "url": media_url,
                        "is_reusable": True
                    }
                }
            }
        }
        return await self._send_api_request(payload)

    async def send_typing(self, recipient_id: str, duration_ms: int = 3000) -> bool:
        """Envia indicador de digitação."""
        try:
            # Typing ON
            await self._send_api_request({
                "recipient": {"id": recipient_id},
                "sender_action": "typing_on"
            })
            
            # Wait
            await asyncio.sleep(duration_ms / 1000)
            
            # Typing OFF (opcional, geralmente desliga sozinho ao enviar msg)
            # await self._send_api_request({
            #     "recipient": {"id": recipient_id},
            #     "sender_action": "typing_off"
            # })
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar typing Instagram: {e}")
            return False

    async def _send_api_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método interno para chamadas API com resiliência.
        Aplica circuit breaker + retry com exponential backoff.
        Inclui métricas e alertas automáticos.
        """
        if not self.config.access_token or not self.config.page_id:
            raise ValueError("Instagram Hub não configurado")

        metrics = get_metrics_registry()
        start_time = asyncio.get_event_loop().time()

        async def _make_request():
            state_before = self._circuit_breaker.state
            
            # Verifica circuit breaker
            if not await self._circuit_breaker.can_execute():
                stats = self._circuit_breaker.stats
                raise CircuitBreakerOpenError(
                    f"Instagram Hub circuit breaker is open "
                    f"(failures: {stats.failure_count})"
                )
            
            try:
                client = await self._get_client()
                response = await client.post(
                    f"/{self.config.page_id}/messages",
                    params={"access_token": self.config.access_token},
                    json=payload
                )
                response.raise_for_status()
                
                # Sucesso - registra no circuit breaker
                await self._circuit_breaker.record_success()
                
                # Verifica recuperação
                state_after = self._circuit_breaker.state
                if state_before.value != "closed" and state_after.value == "closed":
                    await get_alert_manager().send_circuit_breaker_closed("instagram")
                
                # Registra métrica de sucesso
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                metrics.record_request("instagram", "send_message")
                metrics.record_success("instagram", "send_message", elapsed)
                
                return response.json()
                
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                # Falha - registra no circuit breaker
                state_before = self._circuit_breaker.state
                await self._circuit_breaker.record_failure()
                state_after = self._circuit_breaker.state
                
                # Registra métrica de falha
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                metrics.record_request("instagram", "send_message")
                metrics.record_failure("instagram", "send_message")
                
                # Alertas para mudança de estado
                if state_before.value != "open" and state_after.value == "open":
                    await get_alert_manager().send_circuit_breaker_open(
                        hub="instagram",
                        failure_count=self._circuit_breaker.stats.failure_count,
                        threshold=self._circuit_breaker.config.failure_threshold
                    )
                elif (state_before.value != "half_open" and 
                      state_after.value == "half_open"):
                    await get_alert_manager().send_circuit_breaker_half_open(
                        "instagram"
                    )
                
                logger.warning(f"Instagram API request failed: {e}")
                raise
        
        # Aplica retry com exponential backoff
        retry_config = RetryConfig(
            max_retries=self.config.max_retries,
            base_delay=self.config.retry_delay,
            max_delay=30.0,
            retryable_exceptions=(httpx.RequestError, httpx.HTTPStatusError)
        )
        return await retry_with_backoff(_make_request, retry_config)

    # ============================================
    # WEBHOOK HANDLING
    # ============================================

    def normalize_webhook_event(self, payload: Dict[str, Any]) -> Optional[InstagramMessage]:
        """Normaliza evento de webhook para objeto padronizado."""
        try:
            entry = payload.get("entry", [{}])[0]
            messaging = entry.get("messaging", [{}])[0]
            
            sender_id = messaging.get("sender", {}).get("id")
            recipient_id = messaging.get("recipient", {}).get("id")
            timestamp_ms = messaging.get("timestamp", 0)
            
            if not sender_id:
                return None

            message_data = messaging.get("message", {})
            is_echo = message_data.get("is_echo", False)
            mid = message_data.get("mid", "")
            
            # Determinar tipo e conteúdo
            msg_type = InstagramMessageType.TEXT
            content = message_data.get("text")
            media_url = None
            
            if "attachments" in message_data:
                atts = message_data["attachments"]
                if atts:
                    first = atts[0]
                    type_str = first.get("type")
                    media_url = first.get("payload", {}).get("url")
                    
                    if type_str == "image":
                        msg_type = InstagramMessageType.IMAGE
                    elif type_str == "video":
                        msg_type = InstagramMessageType.VIDEO
                    elif type_str == "audio":
                        msg_type = InstagramMessageType.AUDIO
                    elif type_str == "file":
                        msg_type = InstagramMessageType.FILE
            
            return InstagramMessage(
                message_id=mid,
                sender_id=sender_id,
                recipient_id=recipient_id,
                timestamp=datetime.fromtimestamp(timestamp_ms / 1000),
                message_type=msg_type,
                content=content,
                media_url=media_url,
                is_echo=is_echo
            )
            
        except Exception as e:
            logger.error(f"Erro ao normalizar webhook Instagram: {e}")
            return None

# Singleton global
_instagram_hub: Optional[InstagramHub] = None

def get_instagram_hub() -> InstagramHub:
    """Retorna instância singleton do Instagram Hub."""
    global _instagram_hub
    if _instagram_hub is None:
        _instagram_hub = InstagramHub()
    return _instagram_hub
