"""
WhatsApp Integration Hub
========================
Ponto central de integração do WhatsApp para o Didin Fácil.

Este módulo consolida todas as integrações com WhatsApp via Evolution API:
- Gerenciamento de instâncias
- Envio de mensagens
- Webhooks
- Integração com Seller Bot
- Integração com Chatwoot

Autor: Didin Fácil
Versão: 1.2.0 (com alertas e métricas)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx

from .alerts import AlertSeverity, AlertType, get_alert_manager
from .metrics import get_metrics_registry, with_metrics
from .resilience import CircuitBreaker, CircuitBreakerConfig
from .resilience import CircuitBreakerOpenError as CircuitBreakerOpen
from .resilience import RetryConfig, retry_with_backoff

logger = logging.getLogger(__name__)


# ============================================
# CONFIGURATION
# ============================================

@dataclass
class WhatsAppHubConfig:
    """Configuração centralizada do WhatsApp Hub."""
    
    # Evolution API
    evolution_api_url: str = "http://localhost:8082"
    evolution_api_key: str = ""
    default_instance: str = "didin-bot"
    
    # Webhook callbacks
    on_message: Optional[Callable[[Dict], Awaitable[None]]] = None
    on_connection_update: Optional[Callable[[Dict], Awaitable[None]]] = None
    on_qr_code: Optional[Callable[[Dict], Awaitable[None]]] = None
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Rate limiting
    messages_per_minute: int = 60
    

class MessageType(Enum):
    """Tipos de mensagem suportados."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    BUTTONS = "buttons"
    LIST = "list"
    STICKER = "sticker"


class ConnectionState(Enum):
    """Estados de conexão da instância."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AWAITING_SCAN = "awaiting_scan"
    ERROR = "error"


@dataclass
class WhatsAppMessage:
    """Representação padronizada de uma mensagem."""
    message_id: str
    remote_jid: str  # Número no formato 5511999999999@s.whatsapp.net
    from_me: bool
    timestamp: datetime
    message_type: MessageType
    content: str
    media_url: Optional[str] = None
    caption: Optional[str] = None
    quoted_message_id: Optional[str] = None
    instance_name: Optional[str] = None
    push_name: Optional[str] = None
    
    @property
    def phone_number(self) -> str:
        """Extrai número de telefone do JID."""
        return self.remote_jid.split("@")[0] if "@" in self.remote_jid else self.remote_jid
    
    @property
    def is_group(self) -> bool:
        """Verifica se é mensagem de grupo."""
        return "@g.us" in self.remote_jid


@dataclass  
class InstanceInfo:
    """Informações de uma instância WhatsApp."""
    name: str
    state: ConnectionState
    phone_connected: Optional[str] = None
    webhook_url: Optional[str] = None
    created_at: Optional[datetime] = None
    

# ============================================
# WHATSAPP HUB - CLASSE PRINCIPAL
# ============================================

class WhatsAppHub:
    """
    Hub central para todas as operações de WhatsApp.
    
    Uso:
        hub = WhatsAppHub.from_settings()
        
        # Gerenciar instâncias
        await hub.create_instance("minha-loja")
        qr = await hub.get_qr_code("minha-loja")
        
        # Enviar mensagens
        await hub.send_text("5511999999999", "Olá!")
        await hub.send_image("5511999999999", "https://...", "Veja!")
        
        # Processar webhooks
        message = hub.parse_webhook(payload)
    """
    
    _instance: Optional["WhatsAppHub"] = None
    
    def __init__(self, config: WhatsAppHubConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._message_handlers: List[Callable[[WhatsAppMessage], Awaitable[None]]] = []
        self._connection_handlers: List[Callable[[str, ConnectionState], Awaitable[None]]] = []
        self._instances: Dict[str, InstanceInfo] = {}
        self._rate_limiter: Dict[str, List[datetime]] = {}
        
        # Resiliência: Circuit Breaker para Evolution API
        cb_config = CircuitBreakerConfig(
            failure_threshold=5,
            timeout_seconds=30.0,
            half_open_max_calls=3
        )
        self._circuit_breaker = CircuitBreaker(
            name="whatsapp_hub",
            config=cb_config
        )
        
    @classmethod
    def from_settings(cls) -> "WhatsAppHub":
        """Cria instância a partir das configurações do projeto."""
        from shared.config import settings
        
        config = WhatsAppHubConfig(
            evolution_api_url=getattr(settings, 'EVOLUTION_API_URL', 'http://localhost:8082'),
            evolution_api_key=getattr(settings, 'EVOLUTION_API_KEY', ''),
            default_instance=getattr(settings, 'EVOLUTION_INSTANCE', 'didin-bot'),
        )
        return cls(config)
    
    @classmethod
    def get_instance(cls) -> "WhatsAppHub":
        """Obtém instância singleton do hub."""
        if cls._instance is None:
            cls._instance = cls.from_settings()
        return cls._instance
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtém cliente HTTP (lazy initialization)."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.evolution_api_url,
                headers={
                    "apikey": self.config.evolution_api_key,
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self._client
    
    async def _api_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa requisição HTTP com resiliência (circuit breaker + retry).
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API (ex: /instance/create)
            **kwargs: Argumentos adicionais para httpx
            
        Returns:
            Dict com a resposta JSON
            
        Raises:
            CircuitBreakerOpen: Se o circuit breaker estiver aberto
            httpx.HTTPError: Para erros de rede/HTTP
        """
        # Registrar métrica
        metrics = get_metrics_registry()
        start_time = asyncio.get_event_loop().time()
        
        async def _make_request():
            # Captura estado antes
            state_before = self._circuit_breaker.state
            
            # Verifica circuit breaker
            if not await self._circuit_breaker.can_execute():
                stats = self._circuit_breaker.stats
                raise CircuitBreakerOpen(
                    f"WhatsApp Hub circuit breaker is open "
                    f"(failures: {stats.failure_count})"
                )
            
            try:
                client = await self._get_client()
                resp = await getattr(client, method.lower())(endpoint, **kwargs)
                resp.raise_for_status()
                
                # Sucesso - registra no circuit breaker
                await self._circuit_breaker.record_success()
                
                # Verifica se circuit breaker fechou (recuperação)
                state_after = self._circuit_breaker.state
                if state_before.value != "closed" and state_after.value == "closed":
                    await get_alert_manager().send_circuit_breaker_closed("whatsapp")
                
                # Registra métrica de sucesso
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                metrics.record_request("whatsapp", method)
                metrics.record_success("whatsapp", method, elapsed)
                
                return resp.json()
                
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                # Falha - registra no circuit breaker
                state_before = self._circuit_breaker.state
                await self._circuit_breaker.record_failure()
                state_after = self._circuit_breaker.state
                
                # Registra métrica de falha
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                metrics.record_request("whatsapp", method)
                metrics.record_failure("whatsapp", method)
                
                # Alerta se circuit breaker abriu
                if state_before.value != "open" and state_after.value == "open":
                    await get_alert_manager().send_circuit_breaker_open(
                        hub="whatsapp",
                        failure_count=self._circuit_breaker.stats.failure_count,
                        threshold=self._circuit_breaker.config.failure_threshold
                    )
                elif state_before.value != "half_open" and state_after.value == "half_open":
                    await get_alert_manager().send_circuit_breaker_half_open("whatsapp")
                
                logger.warning(
                    f"API request failed: {method} {endpoint} - {e}"
                )
                raise
        
        # Aplica retry com exponential backoff
        retry_config = RetryConfig(
            max_retries=self.config.max_retries,
            base_delay=self.config.retry_delay,
            max_delay=30.0,
            retryable_exceptions=(httpx.RequestError, httpx.HTTPStatusError)
        )
        return await retry_with_backoff(_make_request, retry_config)
    
    async def close(self):
        """Fecha conexões."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()

    # ============================================
    # INSTANCE MANAGEMENT
    # ============================================
    
    async def create_instance(
        self,
        instance_name: Optional[str] = None,
        webhook_url: Optional[str] = None,
        webhook_events: Optional[List[str]] = None
    ) -> InstanceInfo:
        """
        Cria uma nova instância do WhatsApp.
        
        Args:
            instance_name: Nome da instância (usa default se não fornecido)
            webhook_url: URL para receber webhooks
            webhook_events: Lista de eventos para receber
        """
        name = instance_name or self.config.default_instance
        
        payload = {
            "instanceName": name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }
        
        if webhook_url:
            payload["webhook"] = {
                "url": webhook_url,
                "webhook_by_events": False,
                "webhook_base64": False,
                "events": webhook_events or [
                    "MESSAGES_UPSERT",
                    "CONNECTION_UPDATE",
                    "QRCODE_UPDATED"
                ]
            }
        
        try:
            await self._api_request("POST", "/instance/create", json=payload)
            
            instance = InstanceInfo(
                name=name,
                state=ConnectionState.AWAITING_SCAN,
                created_at=datetime.now(timezone.utc)
            )
            self._instances[name] = instance
            
            logger.info(f"Instância '{name}' criada com sucesso")
            return instance
            
        except CircuitBreakerOpen as e:
            logger.error(f"Circuit breaker aberto ao criar instância: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro ao criar instância: {e}")
            raise
    
    async def get_instance_status(
        self,
        instance_name: Optional[str] = None
    ) -> InstanceInfo:
        """Retorna o status da instância."""
        name = instance_name or self.config.default_instance
        
        data = await self._api_request(
            "GET", f"/instance/connectionState/{name}"
        )
        
        state_map = {
            "open": ConnectionState.CONNECTED,
            "close": ConnectionState.DISCONNECTED,
            "connecting": ConnectionState.CONNECTING,
        }
        
        instance_data = data.get("instance", data)
        state_str = instance_data.get("state", "disconnected")
        
        instance = InstanceInfo(
            name=name,
            state=state_map.get(state_str, ConnectionState.DISCONNECTED)
        )
        self._instances[name] = instance
        
        return instance
    
    async def get_qr_code(
        self,
        instance_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Obtém o QR Code para conectar.
        
        Returns:
            Dict com 'base64' (imagem) e 'code' (texto)
        """
        name = instance_name or self.config.default_instance
        return await self._api_request("GET", f"/instance/connect/{name}")
    
    async def disconnect_instance(
        self,
        instance_name: Optional[str] = None
    ) -> bool:
        """Desconecta a instância do WhatsApp."""
        name = instance_name or self.config.default_instance
        
        try:
            await self._api_request("DELETE", f"/instance/logout/{name}")
            
            if name in self._instances:
                self._instances[name].state = ConnectionState.DISCONNECTED
                
            logger.info(f"Instância '{name}' desconectada")
            return True
        except Exception as e:
            logger.error(f"Erro ao desconectar: {e}")
            return False
    
    async def delete_instance(
        self,
        instance_name: Optional[str] = None
    ) -> bool:
        """Remove a instância completamente."""
        name = instance_name or self.config.default_instance
        
        try:
            await self._api_request("DELETE", f"/instance/delete/{name}")
            
            if name in self._instances:
                del self._instances[name]
                
            logger.info(f"Instância '{name}' removida")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover instância: {e}")
            return False
    
    async def list_instances(self) -> List[InstanceInfo]:
        """Lista todas as instâncias."""
        data = await self._api_request("GET", "/instance/fetchInstances")
        
        instances = []
        for item in data:
            instance_data = item.get("instance", {})
            state_str = instance_data.get("state", "disconnected")
            
            state_map = {
                "open": ConnectionState.CONNECTED,
                "close": ConnectionState.DISCONNECTED,
                "connecting": ConnectionState.CONNECTING,
            }
            
            instance = InstanceInfo(
                name=instance_data.get("instanceName", "unknown"),
                state=state_map.get(state_str, ConnectionState.DISCONNECTED),
                phone_connected=instance_data.get("owner")
            )
            instances.append(instance)
            self._instances[instance.name] = instance
            
        return instances

    # ============================================
    # WEBHOOK CONFIGURATION
    # ============================================
    
    async def configure_webhook(
        self,
        webhook_url: str,
        instance_name: Optional[str] = None,
        events: Optional[List[str]] = None
    ) -> bool:
        """
        Configura o webhook para uma instância.
        
        Args:
            webhook_url: URL do webhook
            instance_name: Nome da instância
            events: Lista de eventos
        """
        name = instance_name or self.config.default_instance
        
        payload = {
            "url": webhook_url,
            "webhook_by_events": False,
            "webhook_base64": False,
            "events": events or [
                "MESSAGES_UPSERT",
                "MESSAGES_UPDATE",
                "CONNECTION_UPDATE",
                "QRCODE_UPDATED"
            ]
        }
        
        try:
            await self._api_request(
                "POST", f"/webhook/set/{name}", json=payload
            )
            logger.info(f"Webhook configurado para '{name}': {webhook_url}")
            return True
        except Exception as e:
            logger.error(f"Erro ao configurar webhook: {e}")
            return False
    
    async def get_webhook_config(
        self,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retorna a configuração atual do webhook."""
        name = instance_name or self.config.default_instance
        return await self._api_request("GET", f"/webhook/find/{name}")

    # ============================================
    # MESSAGING
    # ============================================
    
    def _format_phone(self, phone: str) -> str:
        """Formata número de telefone para o padrão do WhatsApp."""
        # Remove caracteres não numéricos
        phone = "".join(filter(str.isdigit, phone))
        
        # Adiciona código do país se não tiver
        if not phone.startswith("55"):
            phone = "55" + phone
            
        return phone
    
    async def _check_rate_limit(self, instance_name: str) -> bool:
        """Verifica rate limit antes de enviar."""
        now = datetime.now(timezone.utc)
        window_start = now.replace(second=0, microsecond=0)
        
        if instance_name not in self._rate_limiter:
            self._rate_limiter[instance_name] = []
        
        # Remove mensagens antigas
        self._rate_limiter[instance_name] = [
            ts for ts in self._rate_limiter[instance_name]
            if ts >= window_start
        ]
        
        if len(self._rate_limiter[instance_name]) >= self.config.messages_per_minute:
            return False
            
        self._rate_limiter[instance_name].append(now)
        return True
    
    async def send_text(
        self,
        to: str,
        text: str,
        instance_name: Optional[str] = None,
        delay_ms: int = 0
    ) -> Dict[str, Any]:
        """
        Envia mensagem de texto.
        
        Args:
            to: Número do destinatário
            text: Texto da mensagem
            instance_name: Instância a usar
            delay_ms: Delay antes de enviar (simula digitação)
        """
        name = instance_name or self.config.default_instance
        
        if not await self._check_rate_limit(name):
            raise Exception("Rate limit exceeded")
        
        phone = self._format_phone(to)
        
        payload = {
            "number": phone,
            "text": text,
            "delay": delay_ms
        }
        
        result = await self._api_request(
            "POST", f"/message/sendText/{name}", json=payload
        )
        
        logger.debug(f"Mensagem enviada para {phone}")
        return result
    
    async def send_image(
        self,
        to: str,
        image_url: str,
        caption: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envia imagem."""
        name = instance_name or self.config.default_instance
        
        if not await self._check_rate_limit(name):
            raise Exception("Rate limit exceeded")
        
        phone = self._format_phone(to)
        
        payload = {
            "number": phone,
            "mediatype": "image",
            "media": image_url,
            "caption": caption or ""
        }
        
        return await self._api_request(
            "POST", f"/message/sendMedia/{name}", json=payload
        )
    
    async def send_video(
        self,
        to: str,
        video_url: str,
        caption: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envia vídeo."""
        name = instance_name or self.config.default_instance
        
        if not await self._check_rate_limit(name):
            raise Exception("Rate limit exceeded")
        
        client = await self._get_client()
        phone = self._format_phone(to)
        
        payload = {
            "number": phone,
            "mediatype": "video",
            "media": video_url,
            "caption": caption or ""
        }
        
        response = await client.post(
            f"/message/sendMedia/{name}",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_audio(
        self,
        to: str,
        audio_url: str,
        as_voice_message: bool = True,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia áudio.
        
        Args:
            to: Número do destinatário
            audio_url: URL do áudio
            as_voice_message: Se True, envia como mensagem de voz
            instance_name: Instância a usar
        """
        name = instance_name or self.config.default_instance
        
        if not await self._check_rate_limit(name):
            raise Exception("Rate limit exceeded")
        
        client = await self._get_client()
        phone = self._format_phone(to)
        
        if as_voice_message:
            payload = {"number": phone, "audio": audio_url}
            endpoint = f"/message/sendWhatsAppAudio/{name}"
        else:
            payload = {
                "number": phone,
                "mediatype": "audio",
                "media": audio_url
            }
            endpoint = f"/message/sendMedia/{name}"
        
        response = await client.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def send_document(
        self,
        to: str,
        document_url: str,
        filename: str,
        caption: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envia documento."""
        name = instance_name or self.config.default_instance
        
        if not await self._check_rate_limit(name):
            raise Exception("Rate limit exceeded")
        
        client = await self._get_client()
        phone = self._format_phone(to)
        
        payload = {
            "number": phone,
            "mediatype": "document",
            "media": document_url,
            "fileName": filename,
            "caption": caption or ""
        }
        
        response = await client.post(
            f"/message/sendMedia/{name}",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_location(
        self,
        to: str,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envia localização."""
        inst_name = instance_name or self.config.default_instance
        
        if not await self._check_rate_limit(inst_name):
            raise Exception("Rate limit exceeded")
        
        client = await self._get_client()
        phone = self._format_phone(to)
        
        payload = {
            "number": phone,
            "latitude": latitude,
            "longitude": longitude,
            "name": name or "",
            "address": address or ""
        }
        
        response = await client.post(
            f"/message/sendLocation/{inst_name}",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_buttons(
        self,
        to: str,
        title: str,
        description: str,
        buttons: List[Dict[str, str]],
        footer: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem com botões.
        
        Args:
            to: Número do destinatário
            title: Título da mensagem
            description: Descrição
            buttons: Lista de botões [{"buttonId": "1", "buttonText": {"displayText": "Opção 1"}}]
            footer: Rodapé opcional
            instance_name: Instância a usar
        """
        name = instance_name or self.config.default_instance
        
        if not await self._check_rate_limit(name):
            raise Exception("Rate limit exceeded")
        
        client = await self._get_client()
        phone = self._format_phone(to)
        
        payload = {
            "number": phone,
            "title": title,
            "description": description,
            "footer": footer or "",
            "buttons": buttons
        }
        
        response = await client.post(
            f"/message/sendButtons/{name}",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_list(
        self,
        to: str,
        title: str,
        description: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        footer: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem com lista.
        
        Args:
            to: Número do destinatário
            title: Título
            description: Descrição
            button_text: Texto do botão
            sections: Seções da lista
            footer: Rodapé opcional
            instance_name: Instância a usar
        """
        name = instance_name or self.config.default_instance
        
        if not await self._check_rate_limit(name):
            raise Exception("Rate limit exceeded")
        
        client = await self._get_client()
        phone = self._format_phone(to)
        
        payload = {
            "number": phone,
            "title": title,
            "description": description,
            "buttonText": button_text,
            "footer": footer or "",
            "sections": sections
        }
        
        response = await client.post(
            f"/message/sendList/{name}",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_template(
        self,
        to: str,
        template_name: str,
        template_data: Dict[str, Any],
        instance_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem baseada em template.
        
        Args:
            to: Número do destinatário
            template_name: Nome do template
            template_data: Dados para substituição no template
            instance_name: Instância a usar
        """
        # TODO: Implementar sistema de templates
        # Por enquanto, usa send_text com formatação
        
        from shared.templates import get_whatsapp_template
        text = get_whatsapp_template(template_name, template_data)
        
        return await self.send_text(to, text, instance_name)

    # ============================================
    # WEBHOOK PROCESSING
    # ============================================
    
    def parse_webhook(self, payload: Dict[str, Any]) -> Optional[WhatsAppMessage]:
        """
        Converte webhook da Evolution API para WhatsAppMessage.
        
        Args:
            payload: Payload do webhook
            
        Returns:
            WhatsAppMessage ou None se não for mensagem válida
        """
        event = payload.get("event")
        
        # Só processa eventos de mensagem
        if event not in ("MESSAGES_UPSERT", "messages.upsert"):
            return None
        
        data = payload.get("data", {})
        message_data = data.get("message", data)
        key = data.get("key", {})
        
        # Ignora mensagens enviadas por nós
        if key.get("fromMe", False):
            return None
        
        # Extrai conteúdo baseado no tipo
        content = ""
        message_type = MessageType.TEXT
        media_url = None
        caption = None
        
        if "conversation" in message_data:
            content = message_data["conversation"]
        elif "extendedTextMessage" in message_data:
            content = message_data["extendedTextMessage"].get("text", "")
        elif "imageMessage" in message_data:
            message_type = MessageType.IMAGE
            media_url = message_data["imageMessage"].get("url")
            caption = message_data["imageMessage"].get("caption", "")
            content = caption
        elif "videoMessage" in message_data:
            message_type = MessageType.VIDEO
            media_url = message_data["videoMessage"].get("url")
            caption = message_data["videoMessage"].get("caption", "")
            content = caption
        elif "audioMessage" in message_data:
            message_type = MessageType.AUDIO
            media_url = message_data["audioMessage"].get("url")
        elif "documentMessage" in message_data:
            message_type = MessageType.DOCUMENT
            media_url = message_data["documentMessage"].get("url")
            content = message_data["documentMessage"].get("fileName", "")
        
        if not content and not media_url:
            return None
        
        return WhatsAppMessage(
            message_id=key.get("id", ""),
            remote_jid=key.get("remoteJid", ""),
            from_me=key.get("fromMe", False),
            timestamp=datetime.now(timezone.utc),
            message_type=message_type,
            content=content,
            media_url=media_url,
            caption=caption,
            instance_name=payload.get("instance"),
            push_name=data.get("pushName")
        )
    
    def parse_connection_update(
        self, 
        payload: Dict[str, Any]
    ) -> Optional[tuple[str, ConnectionState]]:
        """
        Processa atualização de conexão.
        
        Returns:
            Tuple (instance_name, state) ou None
        """
        event = payload.get("event")
        
        if event not in ("CONNECTION_UPDATE", "connection.update"):
            return None
        
        instance_name = payload.get("instance", self.config.default_instance)
        data = payload.get("data", {})
        state_str = data.get("state", "")
        
        state_map = {
            "open": ConnectionState.CONNECTED,
            "close": ConnectionState.DISCONNECTED,
            "connecting": ConnectionState.CONNECTING,
            "refused": ConnectionState.ERROR,
        }
        
        state = state_map.get(state_str, ConnectionState.DISCONNECTED)
        
        # Atualiza cache
        if instance_name in self._instances:
            self._instances[instance_name].state = state
        
        return (instance_name, state)

    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    def on_message(
        self, 
        handler: Callable[[WhatsAppMessage], Awaitable[None]]
    ):
        """Registra handler para novas mensagens."""
        self._message_handlers.append(handler)
    
    def on_connection_change(
        self,
        handler: Callable[[str, ConnectionState], Awaitable[None]]
    ):
        """Registra handler para mudanças de conexão."""
        self._connection_handlers.append(handler)
    
    async def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa webhook e dispara handlers apropriados.
        
        Este é o ponto central de entrada para todos os webhooks do WhatsApp.
        """
        event = payload.get("event", "")
        
        # Processa mensagem
        if event in ("MESSAGES_UPSERT", "messages.upsert"):
            message = self.parse_webhook(payload)
            if message:
                for handler in self._message_handlers:
                    try:
                        await handler(message)
                    except Exception as e:
                        logger.error(f"Erro no handler de mensagem: {e}")
                
                return {
                    "status": "processed",
                    "event": "message",
                    "message_id": message.message_id
                }
        
        # Processa atualização de conexão
        if event in ("CONNECTION_UPDATE", "connection.update"):
            result = self.parse_connection_update(payload)
            if result:
                instance_name, state = result
                for handler in self._connection_handlers:
                    try:
                        await handler(instance_name, state)
                    except Exception as e:
                        logger.error(f"Erro no handler de conexão: {e}")
                
                return {
                    "status": "processed",
                    "event": "connection",
                    "instance": instance_name,
                    "state": state.value
                }
        
        # QR Code
        if event in ("QRCODE_UPDATED", "qrcode.updated"):
            if self.config.on_qr_code:
                await self.config.on_qr_code(payload)
            return {"status": "processed", "event": "qrcode"}
        
        return {"status": "ignored", "event": event}

    # ============================================
    # UTILITIES
    # ============================================
    
    async def check_number(
        self,
        phone: str,
        instance_name: Optional[str] = None
    ) -> bool:
        """Verifica se um número tem WhatsApp."""
        name = instance_name or self.config.default_instance
        client = await self._get_client()
        formatted = self._format_phone(phone)
        
        try:
            response = await client.post(
                f"/chat/whatsappNumbers/{name}",
                json={"numbers": [formatted]}
            )
            response.raise_for_status()
            data = response.json()
            
            for number_data in data:
                if number_data.get("exists"):
                    return True
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar número: {e}")
            return False
    
    async def get_profile_picture(
        self,
        phone: str,
        instance_name: Optional[str] = None
    ) -> Optional[str]:
        """Obtém foto de perfil do contato."""
        name = instance_name or self.config.default_instance
        client = await self._get_client()
        formatted = self._format_phone(phone)
        
        try:
            response = await client.post(
                f"/chat/fetchProfilePictureUrl/{name}",
                json={"number": formatted}
            )
            response.raise_for_status()
            return response.json().get("profilePictureUrl")
        except Exception:
            return None
    
    async def mark_as_read(
        self,
        remote_jid: str,
        instance_name: Optional[str] = None
    ) -> bool:
        """Marca mensagens como lidas."""
        name = instance_name or self.config.default_instance
        client = await self._get_client()
        
        try:
            response = await client.post(
                f"/chat/markMessageAsRead/{name}",
                json={"remoteJid": remote_jid}
            )
            response.raise_for_status()
            return True
        except Exception:
            return False
    
    async def archive_chat(
        self,
        remote_jid: str,
        archive: bool = True,
        instance_name: Optional[str] = None
    ) -> bool:
        """Arquiva ou desarquiva um chat."""
        name = instance_name or self.config.default_instance
        client = await self._get_client()
        
        try:
            response = await client.post(
                f"/chat/archiveChat/{name}",
                json={
                    "lastMessage": {"key": {"remoteJid": remote_jid}},
                    "archive": archive
                }
            )
            response.raise_for_status()
            return True
        except Exception:
            return False


# ============================================
# SINGLETON ACCESSORS
# ============================================

def get_whatsapp_hub() -> WhatsAppHub:
    """Obtém instância singleton do WhatsApp Hub."""
    return WhatsAppHub.get_instance()


async def send_whatsapp_message(
    to: str,
    text: str,
    instance_name: Optional[str] = None
) -> Dict[str, Any]:
    """Função helper para enviar mensagem rapidamente."""
    hub = get_whatsapp_hub()
    return await hub.send_text(to, text, instance_name)


# ============================================
# EXPORTS
# ============================================

__all__ = [
    # Classes principais
    "WhatsAppHub",
    "WhatsAppHubConfig",
    "WhatsAppMessage",
    "InstanceInfo",
    
    # Enums
    "MessageType",
    "ConnectionState",
    
    # Funções helper
    "get_whatsapp_hub",
    "send_whatsapp_message",
]
