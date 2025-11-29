"""
Chatwoot Lite Client
====================
Wrapper para integração com Chatwoot API.

Permite gerenciar contatos, conversas e mensagens.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
import httpx

@dataclass
class ChatwootConfig:
    api_url: str
    api_access_token: str
    account_id: int = 1

class ChatwootClient:
    """
    Cliente para Chatwoot API.
    """
    
    def __init__(self, config: ChatwootConfig):
        self.config = config
        self.base_url = f"{config.api_url}/api/v1/accounts/{config.account_id}"
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"api_access_token": config.api_access_token},
            timeout=30.0
        )

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    # ==================== Contacts ====================

    async def create_contact(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um contato no Chatwoot.
        Payload: { "name": "John", "email": "...", "phone_number": "..." }
        """
        response = await self._client.post("/contacts", json=payload)
        response.raise_for_status()
        return response.json()

    async def search_contact(self, query: str) -> Dict[str, Any]:
        """Busca contato por email ou telefone."""
        response = await self._client.get(f"/contacts/search?q={query}")
        response.raise_for_status()
        return response.json()

    # ==================== Conversations ====================

    async def create_conversation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma conversa.
        Payload: { "source_id": "...", "inbox_id": "...", "contact_id": "..." }
        """
        response = await self._client.post("/conversations", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_conversations(self, status: str = "open") -> Dict[str, Any]:
        """Lista conversas por status."""
        response = await self._client.get(f"/conversations?status={status}")
        response.raise_for_status()
        return response.json()

    # ==================== Messages ====================

    async def send_message(self, conversation_id: int, content: str, message_type: str = "outgoing") -> Dict[str, Any]:
        """Envia mensagem em uma conversa."""
        payload = {
            "content": content,
            "message_type": message_type,
            "private": False
        }
        response = await self._client.post(f"/conversations/{conversation_id}/messages", json=payload)
        response.raise_for_status()
        return response.json()

    # ==================== Inboxes ====================
    
    async def list_inboxes(self) -> List[Dict[str, Any]]:
        """Lista caixas de entrada disponíveis."""
        response = await self._client.get("/inboxes")
        response.raise_for_status()
        return response.json().get("payload", [])
