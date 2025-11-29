"""
Chatwoot Routes
Integration with Chatwoot API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from shared.config import settings
from vendor.support.chatwoot_lite.client import ChatwootClient, ChatwootConfig
from api.middleware.auth import get_current_user

router = APIRouter()

class ChatwootContactCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None

class ChatwootMessageSend(BaseModel):
    conversation_id: int
    content: str

def get_chatwoot_client() -> ChatwootClient:
    if not settings.CHATWOOT_ACCESS_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatwoot Access Token not configured"
        )
        
    config = ChatwootConfig(
        api_url=settings.CHATWOOT_API_URL,
        api_access_token=settings.CHATWOOT_ACCESS_TOKEN,
        account_id=settings.CHATWOOT_ACCOUNT_ID
    )
    return ChatwootClient(config)

@router.get("/inboxes")
async def list_inboxes(current_user = Depends(get_current_user)):
    """List available inboxes"""
    client = get_chatwoot_client()
    try:
        return await client.list_inboxes()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await client.close()

@router.post("/contacts")
async def create_contact(
    data: ChatwootContactCreate,
    current_user = Depends(get_current_user)
):
    """Create a contact in Chatwoot"""
    client = get_chatwoot_client()
    try:
        payload = data.model_dump(exclude_none=True)
        return await client.create_contact(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await client.close()

@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    data: ChatwootMessageSend,
    current_user = Depends(get_current_user)
):
    """Send a message to a conversation"""
    client = get_chatwoot_client()
    try:
        return await client.send_message(conversation_id, data.content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await client.close()
