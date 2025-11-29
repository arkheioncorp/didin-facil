"""
Tests for Typebot and n8n Integrations
"""

import pytest


class TestTypebotClient:
    """Tests for the Typebot Client."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        from vendor.integrations.typebot import TypebotConfig
        return TypebotConfig(
            api_url="https://typebot.io",
            api_token="test-token",
            public_id="test-bot"
        )

    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_config):
        """Test client can be initialized."""
        from vendor.integrations.typebot import TypebotClient
        
        client = TypebotClient(mock_config)
        assert client.config.api_url == "https://typebot.io"

    @pytest.mark.asyncio
    async def test_start_chat_method_exists(self, mock_config):
        """Test start_chat method exists."""
        from vendor.integrations.typebot import TypebotClient
        
        client = TypebotClient(mock_config)
        assert hasattr(client, "start_chat")

    @pytest.mark.asyncio
    async def test_send_message_method_exists(self, mock_config):
        """Test send_message method exists."""
        from vendor.integrations.typebot import TypebotClient
        
        client = TypebotClient(mock_config)
        assert hasattr(client, "send_message")


class TestN8nClient:
    """Tests for the n8n Client."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        from vendor.integrations.n8n import N8nConfig
        return N8nConfig(
            api_url="https://n8n.example.com",
            api_key="test-api-key"
        )

    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_config):
        """Test client can be initialized."""
        from vendor.integrations.n8n import N8nClient
        
        client = N8nClient(mock_config)
        assert client.config.api_url == "https://n8n.example.com"

    @pytest.mark.asyncio
    async def test_trigger_webhook_method_exists(self, mock_config):
        """Test trigger_webhook method exists."""
        from vendor.integrations.n8n import N8nClient
        
        client = N8nClient(mock_config)
        assert hasattr(client, "trigger_webhook")

    @pytest.mark.asyncio
    async def test_execute_workflow_method_exists(self, mock_config):
        """Test execute_workflow method exists."""
        from vendor.integrations.n8n import N8nClient
        
        client = N8nClient(mock_config)
        assert hasattr(client, "execute_workflow")


class TestChatSession:
    """Tests for Typebot ChatSession dataclass."""

    def test_session_creation(self):
        """Test creating a session."""
        from vendor.integrations.typebot import ChatSession
        
        session = ChatSession(
            session_id="sess-123",
            typebot_id="bot-456",
            messages=[{"type": "text", "content": "Hello"}],
            current_input=None,
            is_completed=False
        )
        
        assert session.session_id == "sess-123"
        assert len(session.messages) == 1
        assert session.is_completed is False


class TestWorkflowExecution:
    """Tests for n8n WorkflowExecution dataclass."""

    def test_execution_creation(self):
        """Test creating an execution."""
        from vendor.integrations.n8n import (
            WorkflowExecution,
            ExecutionStatus
        )
        
        execution = WorkflowExecution(
            execution_id="exec-123",
            status=ExecutionStatus.SUCCESS,
            data={"result": "ok"}
        )
        
        assert execution.execution_id == "exec-123"
        assert execution.status == ExecutionStatus.SUCCESS


class TestExecutionStatus:
    """Tests for ExecutionStatus enum."""

    def test_statuses_defined(self):
        """Test all execution statuses are defined."""
        from vendor.integrations.n8n import ExecutionStatus
        
        assert ExecutionStatus.WAITING
        assert ExecutionStatus.RUNNING
        assert ExecutionStatus.SUCCESS
        assert ExecutionStatus.ERROR
