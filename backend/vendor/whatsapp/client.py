"""
WhatsApp Client Wrapper
=======================
Wrapper para Evolution API - a forma mais fácil de integrar WhatsApp.

Evolution API: https://github.com/EvolutionAPI/evolution-api
License: Apache 2.0

Este módulo fornece uma interface simplificada para:
- Envio de mensagens (texto, mídia, documentos)
- Gerenciamento de instâncias
- Webhooks para receber mensagens
- Integração com chatbots
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import httpx


class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    BUTTONS = "buttons"
    LIST = "list"


@dataclass
class WhatsAppConfig:
    """Configuração para conexão com Evolution API."""
    api_url: str
    api_key: str
    instance_name: str
    webhook_url: Optional[str] = None


@dataclass
class Message:
    """Representa uma mensagem do WhatsApp."""
    to: str  # Número no formato: 5511999999999
    type: MessageType
    content: str
    media_url: Optional[str] = None
    caption: Optional[str] = None
    filename: Optional[str] = None
    buttons: Optional[List[Dict[str, str]]] = None
    

class WhatsAppClient:
    """
    Cliente para Evolution API.
    
    Uso:
        config = WhatsAppConfig(
            api_url="http://localhost:8080",
            api_key="your-api-key",
            instance_name="tiktrend-facil"
        )
        client = WhatsAppClient(config)
        
        # Criar instância e conectar
        await client.create_instance()
        qr_code = await client.get_qr_code()
        
        # Enviar mensagem
        await client.send_text("5511999999999", "Olá! Bem-vindo ao TikTrend Finder!")
    """
    
    def __init__(self, config: WhatsAppConfig):
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.api_url,
            headers={"apikey": config.api_key},
            timeout=30.0
        )
    
    async def close(self):
        """Fecha o cliente HTTP."""
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    # ==================== Instance Management ====================
    
    async def create_instance(
        self,
        webhook_url: Optional[str] = None,
        webhook_events: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Cria uma nova instância do WhatsApp.
        
        Args:
            webhook_url: URL para receber webhooks
            webhook_events: Lista de eventos para receber
                ["messages.upsert", "connection.update", "qrcode.updated"]
        """
        payload = {
            "instanceName": self.config.instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }
        
        if webhook_url or self.config.webhook_url:
            payload["webhook"] = {
                "url": webhook_url or self.config.webhook_url,
                "byEvents": True,
                "events": webhook_events or [
                    "MESSAGES_UPSERT",
                    "CONNECTION_UPDATE",
                    "QRCODE_UPDATED"
                ]
            }
        
        response = await self._client.post("/instance/create", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def get_instance_status(self) -> Dict[str, Any]:
        """Retorna o status da instância."""
        response = await self._client.get(
            f"/instance/connectionState/{self.config.instance_name}"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_qr_code(self) -> Dict[str, Any]:
        """
        Obtém o QR Code para conectar o WhatsApp.
        
        Returns:
            Dict com 'base64' (imagem) e 'code' (texto)
        """
        response = await self._client.get(
            f"/instance/connect/{self.config.instance_name}"
        )
        response.raise_for_status()
        return response.json()
    
    async def logout(self) -> Dict[str, Any]:
        """Desconecta a instância do WhatsApp."""
        response = await self._client.delete(
            f"/instance/logout/{self.config.instance_name}"
        )
        response.raise_for_status()
        return response.json()
    
    async def delete_instance(self) -> Dict[str, Any]:
        """Remove a instância completamente."""
        response = await self._client.delete(
            f"/instance/delete/{self.config.instance_name}"
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Messaging ====================
    
    async def send_text(
        self,
        to: str,
        text: str,
        delay: int = 0
    ) -> Dict[str, Any]:
        """
        Envia mensagem de texto.
        
        Args:
            to: Número do destinatário (formato: 5511999999999)
            text: Texto da mensagem
            delay: Delay em ms antes de enviar (simula digitação)
        """
        payload = {
            "number": to,
            "text": text,
            "delay": delay
        }
        
        response = await self._client.post(
            f"/message/sendText/{self.config.instance_name}",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_image(
        self,
        to: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia imagem.
        
        Args:
            to: Número do destinatário
            image_url: URL da imagem
            caption: Legenda opcional
        """
        payload = {
            "number": to,
            "mediatype": "image",
            "media": image_url,
            "caption": caption or ""
        }
        
        response = await self._client.post(
            f"/message/sendMedia/{self.config.instance_name}",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_video(
        self,
        to: str,
        video_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envia vídeo."""
        payload = {
            "number": to,
            "mediatype": "video",
            "media": video_url,
            "caption": caption or ""
        }
        
        response = await self._client.post(
            f"/message/sendMedia/{self.config.instance_name}",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_audio(
        self,
        to: str,
        audio_url: str,
        as_ptt: bool = True
    ) -> Dict[str, Any]:
        """
        Envia áudio.
        
        Args:
            to: Número do destinatário
            audio_url: URL do áudio
            as_ptt: Se True, envia como mensagem de voz (push-to-talk)
        """
        endpoint = "sendWhatsAppAudio" if as_ptt else "sendMedia"
        
        if as_ptt:
            payload = {
                "number": to,
                "audio": audio_url
            }
        else:
            payload = {
                "number": to,
                "mediatype": "audio",
                "media": audio_url
            }
        
        response = await self._client.post(
            f"/message/{endpoint}/{self.config.instance_name}",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_document(
        self,
        to: str,
        document_url: str,
        filename: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envia documento."""
        payload = {
            "number": to,
            "mediatype": "document",
            "media": document_url,
            "fileName": filename,
            "caption": caption or ""
        }
        
        response = await self._client.post(
            f"/message/sendMedia/{self.config.instance_name}",
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
        address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envia localização."""
        payload = {
            "number": to,
            "latitude": latitude,
            "longitude": longitude,
            "name": name or "",
            "address": address or ""
        }
        
        response = await self._client.post(
            f"/message/sendLocation/{self.config.instance_name}",
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
        footer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem com botões.
        
        Args:
            buttons: Lista de dicts com 'buttonId' e 'buttonText'
                [{"buttonId": "1", "buttonText": {"displayText": "Opção 1"}}]
        """
        payload = {
            "number": to,
            "title": title,
            "description": description,
            "footer": footer or "",
            "buttons": buttons
        }
        
        response = await self._client.post(
            f"/message/sendButtons/{self.config.instance_name}",
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
        footer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia lista interativa.
        
        Args:
            sections: Lista de seções com 'title' e 'rows'
                [{
                    "title": "Produtos",
                    "rows": [
                        {"title": "Produto 1", "description": "R$ 10", "rowId": "1"}
                    ]
                }]
        """
        payload = {
            "number": to,
            "title": title,
            "description": description,
            "footer": footer or "",
            "buttonText": button_text,
            "sections": sections
        }
        
        response = await self._client.post(
            f"/message/sendList/{self.config.instance_name}",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Contacts & Groups ====================
    
    async def check_number(self, number: str) -> Dict[str, Any]:
        """Verifica se um número possui WhatsApp."""
        response = await self._client.post(
            f"/chat/whatsappNumbers/{self.config.instance_name}",
            json={"numbers": [number]}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_profile_picture(self, number: str) -> Optional[str]:
        """Obtém a foto de perfil de um contato."""
        response = await self._client.post(
            f"/chat/fetchProfilePicture/{self.config.instance_name}",
            json={"number": number}
        )
        response.raise_for_status()
        data = response.json()
        return data.get("profilePicture")
    
    async def get_contacts(self) -> List[Dict[str, Any]]:
        """Lista todos os contatos."""
        response = await self._client.post(
            f"/chat/findContacts/{self.config.instance_name}",
            json={}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_groups(self) -> List[Dict[str, Any]]:
        """Lista todos os grupos."""
        response = await self._client.get(
            f"/group/fetchAllGroups/{self.config.instance_name}?getParticipants=false"
        )
        response.raise_for_status()
        return response.json()


# ==================== Webhook Handler ====================

@dataclass
class IncomingMessage:
    """Mensagem recebida via webhook."""
    from_number: str
    from_name: str
    message_id: str
    message_type: str
    content: str
    timestamp: int
    is_group: bool
    group_id: Optional[str] = None
    quoted_message: Optional[str] = None
    media_url: Optional[str] = None


def parse_webhook_message(payload: Dict[str, Any]) -> Optional[IncomingMessage]:
    """
    Parseia payload do webhook da Evolution API.
    
    Use no endpoint de webhook:
        @app.post("/webhook/whatsapp")
        async def whatsapp_webhook(payload: dict):
            message = parse_webhook_message(payload)
            if message:
                # Processar mensagem
                pass
    """
    if payload.get("event") != "messages.upsert":
        return None
    
    data = payload.get("data", {})
    key = data.get("key", {})
    message_data = data.get("message", {})
    
    # Determinar tipo e conteúdo
    if "conversation" in message_data:
        msg_type = "text"
        content = message_data["conversation"]
    elif "extendedTextMessage" in message_data:
        msg_type = "text"
        content = message_data["extendedTextMessage"].get("text", "")
    elif "imageMessage" in message_data:
        msg_type = "image"
        content = message_data["imageMessage"].get("caption", "")
    elif "videoMessage" in message_data:
        msg_type = "video"
        content = message_data["videoMessage"].get("caption", "")
    elif "audioMessage" in message_data:
        msg_type = "audio"
        content = ""
    elif "documentMessage" in message_data:
        msg_type = "document"
        content = message_data["documentMessage"].get("fileName", "")
    else:
        return None
    
    remote_jid = key.get("remoteJid", "")
    is_group = "@g.us" in remote_jid
    
    return IncomingMessage(
        from_number=remote_jid.split("@")[0] if not is_group else data.get("pushName", ""),
        from_name=data.get("pushName", ""),
        message_id=key.get("id", ""),
        message_type=msg_type,
        content=content,
        timestamp=data.get("messageTimestamp", 0),
        is_group=is_group,
        group_id=remote_jid if is_group else None,
        quoted_message=message_data.get("extendedTextMessage", {}).get(
            "contextInfo", {}
        ).get("quotedMessage", {}).get("conversation")
    )


# ==================== Chatbot Integration ====================

class WhatsAppBot:
    """
    Bot simples para automatizar respostas.
    
    Uso:
        bot = WhatsAppBot(client)
        
        @bot.command("oi", "olá", "hey")
        async def greeting(message: IncomingMessage):
            return "Olá! Como posso ajudar?"
        
        @bot.command("preço", "quanto custa")
        async def price(message: IncomingMessage):
            return "Consulte nossos preços em: https://tiktrendfinder.com/precos"
        
        # No webhook:
        await bot.process(message)
    """
    
    def __init__(self, client: WhatsAppClient):
        self.client = client
        self._handlers: Dict[str, callable] = {}
        self._default_handler: Optional[callable] = None
    
    def command(self, *triggers: str):
        """Decorator para registrar handler de comando."""
        def decorator(func):
            for trigger in triggers:
                self._handlers[trigger.lower()] = func
            return func
        return decorator
    
    def default(self):
        """Decorator para handler padrão (quando nenhum comando é encontrado)."""
        def decorator(func):
            self._default_handler = func
            return func
        return decorator
    
    async def process(self, message: IncomingMessage) -> Optional[str]:
        """Processa uma mensagem e retorna resposta se houver."""
        content_lower = message.content.lower()
        
        # Verifica comandos
        for trigger, handler in self._handlers.items():
            if trigger in content_lower:
                response = await handler(message)
                if response:
                    await self.client.send_text(message.from_number, response)
                return response
        
        # Handler padrão
        if self._default_handler:
            response = await self._default_handler(message)
            if response:
                await self.client.send_text(message.from_number, response)
            return response
        
        return None
