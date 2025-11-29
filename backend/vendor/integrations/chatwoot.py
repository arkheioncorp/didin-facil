"""
Chatwoot Integration Client
===========================
Cliente para integração com Chatwoot - plataforma de suporte ao cliente.

Baseado em: https://github.com/chatwoot/chatwoot
API Docs: https://www.chatwoot.com/developers/api/

Funcionalidades:
- Gerenciar conversas
- Enviar/receber mensagens
- Criar tickets de suporte
- Gerenciar contatos
- Webhooks para eventos em tempo real
"""

import os
import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConversationStatus(Enum):
    """Status de conversas no Chatwoot."""
    OPEN = "open"
    RESOLVED = "resolved"
    PENDING = "pending"
    SNOOZED = "snoozed"


class MessageType(Enum):
    """Tipos de mensagem."""
    INCOMING = 0
    OUTGOING = 1
    ACTIVITY = 2


class InboxType(Enum):
    """Tipos de inbox."""
    WEB = "Channel::WebWidget"
    WHATSAPP = "Channel::Whatsapp"
    API = "Channel::Api"
    EMAIL = "Channel::Email"
    FACEBOOK = "Channel::FacebookPage"
    INSTAGRAM = "Channel::Instagram"
    TELEGRAM = "Channel::Telegram"


@dataclass
class ChatwootConfig:
    """Configuração do Chatwoot."""
    api_url: str = field(default_factory=lambda: os.getenv("CHATWOOT_API_URL", "https://app.chatwoot.com"))
    api_token: str = field(default_factory=lambda: os.getenv("CHATWOOT_API_TOKEN", ""))
    account_id: str = field(default_factory=lambda: os.getenv("CHATWOOT_ACCOUNT_ID", ""))
    timeout: int = 30


@dataclass
class Contact:
    """Contato no Chatwoot."""
    id: int
    name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    identifier: Optional[str] = None
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None


@dataclass
class Conversation:
    """Conversa no Chatwoot."""
    id: int
    account_id: int
    inbox_id: int
    status: ConversationStatus
    contact: Optional[Contact] = None
    messages_count: int = 0
    unread_count: int = 0
    assignee_id: Optional[int] = None
    team_id: Optional[int] = None
    labels: List[str] = field(default_factory=list)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None


@dataclass
class Message:
    """Mensagem no Chatwoot."""
    id: int
    content: str
    message_type: MessageType
    conversation_id: int
    account_id: int
    sender_id: Optional[int] = None
    private: bool = False
    attachments: List[Dict] = field(default_factory=list)
    created_at: Optional[datetime] = None


class ChatwootClient:
    """
    Cliente assíncrono para Chatwoot API.
    
    Uso:
        config = ChatwootConfig()
        async with ChatwootClient(config) as client:
            conversations = await client.list_conversations()
    """
    
    def __init__(self, config: Optional[ChatwootConfig] = None):
        self.config = config or ChatwootConfig()
        self.client: Optional[httpx.AsyncClient] = None
        self._base_url = f"{self.config.api_url}/api/v1/accounts/{self.config.account_id}"
    
    async def __aenter__(self):
        headers = {
            "api_access_token": self.config.api_token,
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=self.config.timeout
        )
        return self
    
    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()
    
    # ==================== Contacts ====================
    
    async def create_contact(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        identifier: Optional[str] = None,
        custom_attributes: Optional[Dict] = None
    ) -> Contact:
        """
        Cria um novo contato.
        
        Args:
            name: Nome do contato
            email: Email (opcional)
            phone: Telefone com código do país (ex: +5511999999999)
            identifier: ID externo único
            custom_attributes: Atributos customizados
        """
        payload = {"name": name}
        
        if email:
            payload["email"] = email
        if phone:
            payload["phone_number"] = phone
        if identifier:
            payload["identifier"] = identifier
        if custom_attributes:
            payload["custom_attributes"] = custom_attributes
        
        response = await self.client.post(
            f"{self._base_url}/contacts",
            json=payload
        )
        response.raise_for_status()
        data = response.json()["payload"]["contact"]
        
        return Contact(
            id=data["id"],
            name=data["name"],
            email=data.get("email"),
            phone_number=data.get("phone_number"),
            identifier=data.get("identifier"),
            custom_attributes=data.get("custom_attributes", {})
        )
    
    async def get_contact(self, contact_id: int) -> Contact:
        """Obtém detalhes de um contato."""
        response = await self.client.get(
            f"{self._base_url}/contacts/{contact_id}"
        )
        response.raise_for_status()
        data = response.json()["payload"]
        
        return Contact(
            id=data["id"],
            name=data["name"],
            email=data.get("email"),
            phone_number=data.get("phone_number"),
            identifier=data.get("identifier"),
            custom_attributes=data.get("custom_attributes", {})
        )
    
    async def search_contacts(
        self,
        query: str,
        page: int = 1
    ) -> List[Contact]:
        """Busca contatos por nome, email ou telefone."""
        response = await self.client.get(
            f"{self._base_url}/contacts/search",
            params={"q": query, "page": page}
        )
        response.raise_for_status()
        data = response.json()["payload"]
        
        return [
            Contact(
                id=c["id"],
                name=c["name"],
                email=c.get("email"),
                phone_number=c.get("phone_number")
            )
            for c in data
        ]
    
    async def update_contact(
        self,
        contact_id: int,
        **kwargs
    ) -> Contact:
        """Atualiza dados de um contato."""
        response = await self.client.patch(
            f"{self._base_url}/contacts/{contact_id}",
            json=kwargs
        )
        response.raise_for_status()
        data = response.json()["payload"]["contact"]
        
        return Contact(
            id=data["id"],
            name=data["name"],
            email=data.get("email"),
            phone_number=data.get("phone_number"),
            custom_attributes=data.get("custom_attributes", {})
        )
    
    # ==================== Conversations ====================
    
    async def create_conversation(
        self,
        inbox_id: int,
        contact_id: int,
        source_id: Optional[str] = None,
        status: ConversationStatus = ConversationStatus.OPEN,
        assignee_id: Optional[int] = None,
        team_id: Optional[int] = None,
        custom_attributes: Optional[Dict] = None
    ) -> Conversation:
        """
        Cria uma nova conversa.
        
        Args:
            inbox_id: ID do inbox (canal)
            contact_id: ID do contato
            source_id: ID da fonte externa
            status: Status inicial
            assignee_id: ID do agente responsável
            team_id: ID do time responsável
        """
        payload = {
            "inbox_id": inbox_id,
            "contact_id": contact_id,
            "status": status.value
        }
        
        if source_id:
            payload["source_id"] = source_id
        if assignee_id:
            payload["assignee_id"] = assignee_id
        if team_id:
            payload["team_id"] = team_id
        if custom_attributes:
            payload["custom_attributes"] = custom_attributes
        
        response = await self.client.post(
            f"{self._base_url}/conversations",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        return Conversation(
            id=data["id"],
            account_id=data["account_id"],
            inbox_id=data["inbox_id"],
            status=ConversationStatus(data["status"])
        )
    
    async def list_conversations(
        self,
        inbox_id: Optional[int] = None,
        status: Optional[ConversationStatus] = None,
        assignee_id: Optional[int] = None,
        labels: Optional[List[str]] = None,
        page: int = 1
    ) -> List[Conversation]:
        """Lista conversas com filtros."""
        params = {"page": page}
        
        if inbox_id:
            params["inbox_id"] = inbox_id
        if status:
            params["status"] = status.value
        if assignee_id:
            params["assignee_id"] = assignee_id
        if labels:
            params["labels"] = labels
        
        response = await self.client.get(
            f"{self._base_url}/conversations",
            params=params
        )
        response.raise_for_status()
        data = response.json()["data"]["payload"]
        
        return [
            Conversation(
                id=c["id"],
                account_id=c["account_id"],
                inbox_id=c["inbox_id"],
                status=ConversationStatus(c["status"]),
                messages_count=c.get("messages_count", 0),
                unread_count=c.get("unread_count", 0),
                labels=c.get("labels", [])
            )
            for c in data
        ]
    
    async def get_conversation(self, conversation_id: int) -> Conversation:
        """Obtém detalhes de uma conversa."""
        response = await self.client.get(
            f"{self._base_url}/conversations/{conversation_id}"
        )
        response.raise_for_status()
        data = response.json()
        
        contact_data = data.get("meta", {}).get("sender")
        contact = None
        if contact_data:
            contact = Contact(
                id=contact_data["id"],
                name=contact_data["name"],
                email=contact_data.get("email"),
                phone_number=contact_data.get("phone_number")
            )
        
        return Conversation(
            id=data["id"],
            account_id=data["account_id"],
            inbox_id=data["inbox_id"],
            status=ConversationStatus(data["status"]),
            contact=contact,
            messages_count=data.get("messages_count", 0),
            unread_count=data.get("unread_count", 0),
            assignee_id=data.get("meta", {}).get("assignee", {}).get("id"),
            labels=data.get("labels", [])
        )
    
    async def update_conversation(
        self,
        conversation_id: int,
        status: Optional[ConversationStatus] = None,
        assignee_id: Optional[int] = None,
        team_id: Optional[int] = None,
        labels: Optional[List[str]] = None
    ) -> Conversation:
        """Atualiza uma conversa."""
        payload = {}
        
        if status:
            payload["status"] = status.value
        if assignee_id is not None:
            payload["assignee_id"] = assignee_id
        if team_id is not None:
            payload["team_id"] = team_id
        if labels is not None:
            payload["labels"] = labels
        
        response = await self.client.patch(
            f"{self._base_url}/conversations/{conversation_id}",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        return Conversation(
            id=data["id"],
            account_id=data["account_id"],
            inbox_id=data["inbox_id"],
            status=ConversationStatus(data["status"])
        )
    
    async def toggle_status(
        self,
        conversation_id: int,
        status: ConversationStatus
    ) -> Conversation:
        """Altera o status de uma conversa."""
        response = await self.client.post(
            f"{self._base_url}/conversations/{conversation_id}/toggle_status",
            json={"status": status.value}
        )
        response.raise_for_status()
        data = response.json()["payload"]
        
        return Conversation(
            id=data["id"],
            account_id=data["account_id"],
            inbox_id=data["inbox_id"],
            status=ConversationStatus(data["status"])
        )
    
    async def assign_agent(
        self,
        conversation_id: int,
        assignee_id: int
    ) -> bool:
        """Atribui um agente a uma conversa."""
        response = await self.client.post(
            f"{self._base_url}/conversations/{conversation_id}/assignments",
            json={"assignee_id": assignee_id}
        )
        response.raise_for_status()
        return True
    
    async def add_labels(
        self,
        conversation_id: int,
        labels: List[str]
    ) -> List[str]:
        """Adiciona labels a uma conversa."""
        response = await self.client.post(
            f"{self._base_url}/conversations/{conversation_id}/labels",
            json={"labels": labels}
        )
        response.raise_for_status()
        return response.json()["payload"]
    
    # ==================== Messages ====================
    
    async def send_message(
        self,
        conversation_id: int,
        content: str,
        message_type: MessageType = MessageType.OUTGOING,
        private: bool = False,
        attachments: Optional[List[str]] = None
    ) -> Message:
        """
        Envia mensagem em uma conversa.
        
        Args:
            conversation_id: ID da conversa
            content: Conteúdo da mensagem
            message_type: Tipo (entrada/saída/atividade)
            private: Se é nota interna (não visível para cliente)
            attachments: Lista de URLs de arquivos
        """
        payload = {
            "content": content,
            "message_type": message_type.value,
            "private": private
        }
        
        if attachments:
            payload["attachments"] = attachments
        
        response = await self.client.post(
            f"{self._base_url}/conversations/{conversation_id}/messages",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        return Message(
            id=data["id"],
            content=data["content"],
            message_type=MessageType(data["message_type"]),
            conversation_id=data["conversation_id"],
            account_id=data["account_id"],
            private=data.get("private", False),
            attachments=data.get("attachments", [])
        )
    
    async def list_messages(
        self,
        conversation_id: int,
        before: Optional[int] = None
    ) -> List[Message]:
        """Lista mensagens de uma conversa."""
        params = {}
        if before:
            params["before"] = before
        
        response = await self.client.get(
            f"{self._base_url}/conversations/{conversation_id}/messages",
            params=params
        )
        response.raise_for_status()
        data = response.json()["payload"]
        
        return [
            Message(
                id=m["id"],
                content=m.get("content", ""),
                message_type=MessageType(m["message_type"]),
                conversation_id=m["conversation_id"],
                account_id=m["account_id"],
                private=m.get("private", False),
                attachments=m.get("attachments", [])
            )
            for m in data
        ]
    
    # ==================== Inboxes ====================
    
    async def list_inboxes(self) -> List[Dict]:
        """Lista todos os inboxes (canais) da conta."""
        response = await self.client.get(
            f"{self._base_url}/inboxes"
        )
        response.raise_for_status()
        return response.json()["payload"]
    
    async def get_inbox(self, inbox_id: int) -> Dict:
        """Obtém detalhes de um inbox."""
        response = await self.client.get(
            f"{self._base_url}/inboxes/{inbox_id}"
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Teams ====================
    
    async def list_teams(self) -> List[Dict]:
        """Lista times da conta."""
        response = await self.client.get(
            f"{self._base_url}/teams"
        )
        response.raise_for_status()
        return response.json()
    
    async def list_team_members(self, team_id: int) -> List[Dict]:
        """Lista membros de um time."""
        response = await self.client.get(
            f"{self._base_url}/teams/{team_id}/team_members"
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Agents ====================
    
    async def list_agents(self) -> List[Dict]:
        """Lista agentes da conta."""
        response = await self.client.get(
            f"{self._base_url}/agents"
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Labels ====================
    
    async def list_labels(self) -> List[Dict]:
        """Lista labels disponíveis."""
        response = await self.client.get(
            f"{self._base_url}/labels"
        )
        response.raise_for_status()
        return response.json()["payload"]
    
    async def create_label(
        self,
        title: str,
        description: Optional[str] = None,
        color: str = "#1f93ff"
    ) -> Dict:
        """Cria uma nova label."""
        response = await self.client.post(
            f"{self._base_url}/labels",
            json={
                "title": title,
                "description": description,
                "color": color
            }
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Canned Responses ====================
    
    async def list_canned_responses(self) -> List[Dict]:
        """Lista respostas prontas."""
        response = await self.client.get(
            f"{self._base_url}/canned_responses"
        )
        response.raise_for_status()
        return response.json()
    
    async def create_canned_response(
        self,
        short_code: str,
        content: str
    ) -> Dict:
        """Cria uma resposta pronta."""
        response = await self.client.post(
            f"{self._base_url}/canned_responses",
            json={
                "short_code": short_code,
                "content": content
            }
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Reports ====================
    
    async def get_account_summary(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict:
        """Obtém resumo de métricas da conta."""
        params = {}
        if since:
            params["since"] = int(since.timestamp())
        if until:
            params["until"] = int(until.timestamp())
        
        response = await self.client.get(
            f"{self._base_url}/reports/summary",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def get_agent_summary(
        self,
        agent_id: int,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict:
        """Obtém métricas de um agente específico."""
        params = {"type": "agent", "id": agent_id}
        if since:
            params["since"] = int(since.timestamp())
        if until:
            params["until"] = int(until.timestamp())
        
        response = await self.client.get(
            f"{self._base_url}/reports/summary",
            params=params
        )
        response.raise_for_status()
        return response.json()


# ==================== Webhook Handler ====================

class ChatwootWebhookHandler:
    """
    Handler para webhooks do Chatwoot.
    
    Configure o webhook URL no Chatwoot para receber eventos.
    
    Uso:
        handler = ChatwootWebhookHandler()
        
        @handler.on("message_created")
        async def on_new_message(data):
            print(f"Nova mensagem: {data['content']}")
        
        # No FastAPI:
        @app.post("/webhook/chatwoot")
        async def chatwoot_webhook(request: Request):
            data = await request.json()
            await handler.process(data)
    """
    
    def __init__(self):
        self._handlers: Dict[str, List] = {}
    
    def on(self, event_type: str):
        """Decorator para registrar handler de evento."""
        def decorator(func):
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(func)
            return func
        return decorator
    
    async def process(self, payload: Dict) -> None:
        """
        Processa um webhook recebido.
        
        Eventos suportados:
        - message_created: Nova mensagem
        - message_updated: Mensagem atualizada
        - conversation_created: Nova conversa
        - conversation_status_changed: Status alterado
        - conversation_updated: Conversa atualizada
        - webwidget_triggered: Widget ativado
        """
        event_type = payload.get("event")
        
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    await handler(payload)
                except Exception as e:
                    logger.error(f"Erro ao processar webhook {event_type}: {e}")


# ==================== Helper: Ticket Creator ====================

async def create_support_ticket(
    client: ChatwootClient,
    inbox_id: int,
    customer_name: str,
    customer_email: str,
    subject: str,
    message: str,
    priority: str = "normal",
    labels: Optional[List[str]] = None
) -> Conversation:
    """
    Função helper para criar um ticket de suporte completo.
    
    Args:
        client: ChatwootClient conectado
        inbox_id: ID do inbox (API channel recomendado)
        customer_name: Nome do cliente
        customer_email: Email do cliente
        subject: Assunto do ticket
        message: Mensagem inicial
        priority: Prioridade (low, normal, high, urgent)
        labels: Labels para categorização
    
    Returns:
        Conversation: Conversa criada
    """
    # 1. Busca ou cria contato
    contacts = await client.search_contacts(customer_email)
    
    if contacts:
        contact = contacts[0]
    else:
        contact = await client.create_contact(
            name=customer_name,
            email=customer_email,
            custom_attributes={
                "source": "support_ticket"
            }
        )
    
    # 2. Cria conversa
    conversation = await client.create_conversation(
        inbox_id=inbox_id,
        contact_id=contact.id,
        custom_attributes={
            "subject": subject,
            "priority": priority
        }
    )
    
    # 3. Envia mensagem inicial
    await client.send_message(
        conversation_id=conversation.id,
        content=f"**Assunto:** {subject}\n\n{message}",
        message_type=MessageType.INCOMING
    )
    
    # 4. Adiciona labels
    if labels:
        await client.add_labels(conversation.id, labels)
    
    # 5. Adiciona label de prioridade
    priority_label = f"priority:{priority}"
    await client.add_labels(conversation.id, [priority_label])
    
    logger.info(f"Ticket criado: Conversation #{conversation.id}")
    
    return conversation


# ==================== Exemplo de Uso ====================

async def example_usage():
    """Exemplo de uso do Chatwoot Client."""
    config = ChatwootConfig(
        api_url="https://app.chatwoot.com",
        api_token="your_api_token",
        account_id="1"
    )
    
    async with ChatwootClient(config) as client:
        # Criar contato
        contact = await client.create_contact(
            name="João Silva",
            email="joao@example.com",
            phone="+5511999999999"
        )
        print(f"Contato criado: {contact.id}")
        
        # Listar inboxes
        inboxes = await client.list_inboxes()
        api_inbox = next(
            (i for i in inboxes if i["channel_type"] == "Channel::Api"),
            None
        )
        
        if api_inbox:
            # Criar ticket
            conversation = await create_support_ticket(
                client=client,
                inbox_id=api_inbox["id"],
                customer_name="João Silva",
                customer_email="joao@example.com",
                subject="Problema com pedido",
                message="Meu pedido #12345 não chegou ainda.",
                priority="high",
                labels=["pedido", "urgente"]
            )
            print(f"Ticket criado: #{conversation.id}")
        
        # Listar conversas abertas
        open_conversations = await client.list_conversations(
            status=ConversationStatus.OPEN
        )
        print(f"Conversas abertas: {len(open_conversations)}")
        
        # Métricas
        summary = await client.get_account_summary()
        print(f"Métricas: {summary}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
