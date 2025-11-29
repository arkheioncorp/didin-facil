"""
Tests for Chatwoot Integration
"""

import pytest


class TestChatwootClient:
    """Tests for the Chatwoot Client."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        from vendor.integrations.chatwoot import ChatwootConfig
        return ChatwootConfig(
            api_url="https://app.chatwoot.com",
            api_token="test-token",
            account_id="1"
        )

    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_config):
        """Test client can be initialized."""
        from vendor.integrations.chatwoot import ChatwootClient
        
        client = ChatwootClient(mock_config)
        assert client.config.api_url == "https://app.chatwoot.com"
        assert client.config.account_id == "1"

    @pytest.mark.asyncio
    async def test_create_contact_method_exists(self, mock_config):
        """Test create_contact method exists."""
        from vendor.integrations.chatwoot import ChatwootClient
        
        client = ChatwootClient(mock_config)
        assert hasattr(client, "create_contact")

    @pytest.mark.asyncio
    async def test_create_conversation_method_exists(self, mock_config):
        """Test create_conversation method exists."""
        from vendor.integrations.chatwoot import ChatwootClient
        
        client = ChatwootClient(mock_config)
        assert hasattr(client, "create_conversation")

    @pytest.mark.asyncio
    async def test_send_message_method_exists(self, mock_config):
        """Test send_message method exists."""
        from vendor.integrations.chatwoot import ChatwootClient
        
        client = ChatwootClient(mock_config)
        assert hasattr(client, "send_message")


class TestConversationStatus:
    """Tests for ConversationStatus enum."""

    def test_statuses_defined(self):
        """Test all conversation statuses are defined."""
        from vendor.integrations.chatwoot import ConversationStatus
        
        assert ConversationStatus.OPEN
        assert ConversationStatus.RESOLVED
        assert ConversationStatus.PENDING
        assert ConversationStatus.SNOOZED


class TestMessageType:
    """Tests for MessageType enum."""

    def test_message_types_defined(self):
        """Test message types are defined."""
        from vendor.integrations.chatwoot import MessageType
        
        assert MessageType.INCOMING.value == 0
        assert MessageType.OUTGOING.value == 1
        assert MessageType.ACTIVITY.value == 2


class TestChatwootWebhookHandler:
    """Tests for Chatwoot Webhook Handler."""

    def test_handler_initialization(self):
        """Test webhook handler initialization."""
        from vendor.integrations.chatwoot import ChatwootWebhookHandler
        
        handler = ChatwootWebhookHandler()
        assert handler._handlers == {}

    def test_register_handler(self):
        """Test registering an event handler."""
        from vendor.integrations.chatwoot import ChatwootWebhookHandler
        
        handler = ChatwootWebhookHandler()
        
        @handler.on("message_created")
        async def on_message(data):
            pass
        
        assert "message_created" in handler._handlers
        assert len(handler._handlers["message_created"]) == 1

    @pytest.mark.asyncio
    async def test_process_webhook(self):
        """Test processing a webhook."""
        from vendor.integrations.chatwoot import ChatwootWebhookHandler
        
        handler = ChatwootWebhookHandler()
        processed = []
        
        @handler.on("message_created")
        async def on_message(data):
            processed.append(data)
        
        await handler.process({
            "event": "message_created",
            "content": "Hello"
        })
        
        assert len(processed) == 1
        assert processed[0]["content"] == "Hello"


class TestContact:
    """Tests for Contact dataclass."""

    def test_contact_creation(self):
        """Test creating a contact."""
        from vendor.integrations.chatwoot import Contact
        
        contact = Contact(
            id=1,
            name="João Silva",
            email="joao@example.com",
            phone_number="+5511999999999"
        )
        
        assert contact.id == 1
        assert contact.name == "João Silva"
        assert contact.email == "joao@example.com"


class TestConversation:
    """Tests for Conversation dataclass."""

    def test_conversation_creation(self):
        """Test creating a conversation."""
        from vendor.integrations.chatwoot import (
            Conversation, ConversationStatus
        )
        
        conv = Conversation(
            id=1,
            account_id=1,
            inbox_id=1,
            status=ConversationStatus.OPEN
        )
        
        assert conv.id == 1
        assert conv.status == ConversationStatus.OPEN
