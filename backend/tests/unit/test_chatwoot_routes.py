"""
Tests for Chatwoot Routes
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


class MockUser:
    id = "user_123"
    email = "test@example.com"


@pytest.fixture
def mock_current_user():
    return MockUser()


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.CHATWOOT_ACCESS_TOKEN = "test_token"
    settings.CHATWOOT_API_URL = "https://chatwoot.example.com"
    settings.CHATWOOT_ACCOUNT_ID = 1
    return settings


@pytest.fixture
def mock_chatwoot_client():
    client = AsyncMock()
    client.list_inboxes.return_value = [
        {"id": 1, "name": "Inbox 1"},
        {"id": 2, "name": "Inbox 2"}
    ]
    client.create_contact.return_value = {"id": 123, "name": "Test Contact"}
    client.send_message.return_value = {"id": 456, "content": "Test message"}
    client.close = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_chatwoot_client_no_token():
    from api.routes.chatwoot import get_chatwoot_client
    
    mock_settings = MagicMock()
    mock_settings.CHATWOOT_ACCESS_TOKEN = None
    
    with patch("api.routes.chatwoot.settings", mock_settings):
        with pytest.raises(HTTPException) as exc_info:
            get_chatwoot_client()
        
        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_chatwoot_list_inboxes(
    mock_current_user,
    mock_settings,
    mock_chatwoot_client
):
    from api.routes.chatwoot import list_inboxes
    
    with patch("api.routes.chatwoot.settings", mock_settings), \
         patch("api.routes.chatwoot.get_chatwoot_client",
               return_value=mock_chatwoot_client):
        
        result = await list_inboxes(mock_current_user)
        
        assert len(result) == 2
        mock_chatwoot_client.list_inboxes.assert_called_once()
        mock_chatwoot_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_chatwoot_list_inboxes_error(
    mock_current_user,
    mock_settings,
    mock_chatwoot_client
):
    from api.routes.chatwoot import list_inboxes
    
    mock_chatwoot_client.list_inboxes.side_effect = Exception("API Error")
    
    with patch("api.routes.chatwoot.settings", mock_settings), \
         patch("api.routes.chatwoot.get_chatwoot_client",
               return_value=mock_chatwoot_client):
        
        with pytest.raises(HTTPException) as exc_info:
            await list_inboxes(mock_current_user)
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_chatwoot_create_contact(
    mock_current_user,
    mock_settings,
    mock_chatwoot_client
):
    from api.routes.chatwoot import create_contact, ChatwootContactCreate
    
    with patch("api.routes.chatwoot.settings", mock_settings), \
         patch("api.routes.chatwoot.get_chatwoot_client",
               return_value=mock_chatwoot_client):
        
        data = ChatwootContactCreate(
            name="Test Contact",
            email="test@example.com",
            phone_number="+5511999999999"
        )
        
        result = await create_contact(data, mock_current_user)
        
        assert result["id"] == 123
        mock_chatwoot_client.create_contact.assert_called_once()
        mock_chatwoot_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_chatwoot_create_contact_error(
    mock_current_user,
    mock_settings,
    mock_chatwoot_client
):
    from api.routes.chatwoot import create_contact, ChatwootContactCreate
    
    mock_chatwoot_client.create_contact.side_effect = Exception("API Error")
    
    with patch("api.routes.chatwoot.settings", mock_settings), \
         patch("api.routes.chatwoot.get_chatwoot_client",
               return_value=mock_chatwoot_client):
        
        data = ChatwootContactCreate(name="Test")
        
        with pytest.raises(HTTPException) as exc_info:
            await create_contact(data, mock_current_user)
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_chatwoot_send_message(
    mock_current_user,
    mock_settings,
    mock_chatwoot_client
):
    from api.routes.chatwoot import send_message, ChatwootMessageSend
    
    with patch("api.routes.chatwoot.settings", mock_settings), \
         patch("api.routes.chatwoot.get_chatwoot_client",
               return_value=mock_chatwoot_client):
        
        data = ChatwootMessageSend(conversation_id=1, content="Hello!")
        
        result = await send_message(1, data, mock_current_user)
        
        assert result["id"] == 456
        mock_chatwoot_client.send_message.assert_called_once_with(1, "Hello!")
        mock_chatwoot_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_chatwoot_send_message_error(
    mock_current_user,
    mock_settings,
    mock_chatwoot_client
):
    from api.routes.chatwoot import send_message, ChatwootMessageSend
    
    mock_chatwoot_client.send_message.side_effect = Exception("API Error")
    
    with patch("api.routes.chatwoot.settings", mock_settings), \
         patch("api.routes.chatwoot.get_chatwoot_client",
               return_value=mock_chatwoot_client):
        
        data = ChatwootMessageSend(conversation_id=1, content="Hello!")
        
        with pytest.raises(HTTPException) as exc_info:
            await send_message(1, data, mock_current_user)
        
        assert exc_info.value.status_code == 400
