"""
Tests for api/routes/integrations.py
n8n and Typebot integration routes testing
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from api.routes.integrations import (
    router,
    list_n8n_workflows,
    trigger_n8n_workflow,
    get_n8n_execution,
    trigger_n8n_webhook,
    start_typebot_chat,
    send_typebot_message,
    set_typebot_variable,
    get_typebot_session,
    get_integration_config,
    update_integration_config,
    get_n8n_client,
    get_typebot_client,
    N8nWorkflowTrigger,
    N8nWebhookTrigger,
    TypebotStartChat,
    TypebotSendMessage,
    TypebotSetVariable,
    IntegrationConfig,
)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "name": "Test User",
    }


@pytest.fixture
def mock_n8n_client():
    """Mock n8n client."""
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_typebot_client():
    """Mock Typebot client."""
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    return redis


@pytest.fixture
def n8n_workflow_trigger():
    """Sample n8n workflow trigger request."""
    return N8nWorkflowTrigger(
        workflow_id="workflow-123",
        data={"key": "value"},
        wait_for_result=False
    )


@pytest.fixture
def typebot_start_chat():
    """Sample Typebot start chat request."""
    return TypebotStartChat(
        bot_id="bot-123",
        user_id="user-456",
        initial_variables={"name": "Test User"}
    )


# ==================== N8N CLIENT TESTS ====================

class TestN8nClient:
    """Tests for n8n client creation."""

    @patch("api.routes.integrations.settings")
    def test_get_n8n_client_not_configured(self, mock_settings):
        """Test n8n client when not configured."""
        mock_settings.N8N_API_URL = None
        mock_settings.N8N_API_KEY = None

        with pytest.raises(HTTPException) as exc_info:
            get_n8n_client()

        assert exc_info.value.status_code == 503
        assert "n8n não configurado" in str(exc_info.value.detail)

    @patch("api.routes.integrations.settings")
    @patch("api.routes.integrations.N8nClient")
    def test_get_n8n_client_configured(self, mock_client_class, mock_settings):
        """Test n8n client when properly configured."""
        mock_settings.N8N_API_URL = "http://n8n.local"
        mock_settings.N8N_API_KEY = "api-key-123"

        client = get_n8n_client()

        mock_client_class.assert_called_once()


# ==================== N8N WORKFLOW TESTS ====================

class TestListN8nWorkflows:
    """Tests for listing n8n workflows."""

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_n8n_client")
    async def test_list_workflows_success(self, mock_get_client, mock_n8n_client, mock_current_user):
        """Test listing workflows successfully."""
        mock_get_client.return_value = mock_n8n_client
        mock_n8n_client.list_workflows = AsyncMock(return_value=[
            {"id": "wf-1", "name": "Workflow 1"},
            {"id": "wf-2", "name": "Workflow 2"}
        ])

        response = await list_n8n_workflows(
            active_only=True,
            current_user=mock_current_user
        )

        assert response["total"] == 2
        assert len(response["workflows"]) == 2

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_n8n_client")
    async def test_list_workflows_error(self, mock_get_client, mock_n8n_client, mock_current_user):
        """Test listing workflows with error."""
        mock_get_client.return_value = mock_n8n_client
        mock_n8n_client.list_workflows = AsyncMock(side_effect=Exception("Connection error"))

        with pytest.raises(HTTPException) as exc_info:
            await list_n8n_workflows(active_only=True, current_user=mock_current_user)

        assert exc_info.value.status_code == 500


class TestTriggerN8nWorkflow:
    """Tests for triggering n8n workflows."""

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_n8n_client")
    async def test_trigger_workflow_success(
        self, mock_get_client, mock_n8n_client, mock_current_user, n8n_workflow_trigger
    ):
        """Test triggering workflow successfully."""
        mock_get_client.return_value = mock_n8n_client
        
        mock_execution = MagicMock()
        mock_execution.id = "exec-123"
        mock_execution.status.value = "running"
        mock_execution.started_at = None
        mock_execution.finished_at = None
        mock_execution.data = None
        
        mock_n8n_client.execute_workflow = AsyncMock(return_value=mock_execution)
        
        background_tasks = MagicMock()

        response = await trigger_n8n_workflow(
            data=n8n_workflow_trigger,
            background_tasks=background_tasks,
            current_user=mock_current_user
        )

        assert response["execution_id"] == "exec-123"
        assert response["status"] == "running"

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_n8n_client")
    async def test_trigger_workflow_wait_for_result(
        self, mock_get_client, mock_n8n_client, mock_current_user
    ):
        """Test triggering workflow with wait_for_result."""
        mock_get_client.return_value = mock_n8n_client
        
        from datetime import datetime
        mock_execution = MagicMock()
        mock_execution.id = "exec-123"
        mock_execution.status.value = "success"
        mock_execution.started_at = datetime.now()
        mock_execution.finished_at = datetime.now()
        mock_execution.data = {"result": "completed"}
        
        mock_n8n_client.execute_workflow = AsyncMock(return_value=mock_execution)
        
        request = N8nWorkflowTrigger(
            workflow_id="wf-1",
            data={},
            wait_for_result=True
        )
        background_tasks = MagicMock()

        response = await trigger_n8n_workflow(
            data=request,
            background_tasks=background_tasks,
            current_user=mock_current_user
        )

        assert response["data"] == {"result": "completed"}

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_n8n_client")
    async def test_trigger_workflow_error(
        self, mock_get_client, mock_n8n_client, mock_current_user, n8n_workflow_trigger
    ):
        """Test triggering workflow with error."""
        mock_get_client.return_value = mock_n8n_client
        mock_n8n_client.execute_workflow = AsyncMock(side_effect=Exception("Workflow error"))
        
        background_tasks = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await trigger_n8n_workflow(
                data=n8n_workflow_trigger,
                background_tasks=background_tasks,
                current_user=mock_current_user
            )

        assert exc_info.value.status_code == 500


class TestGetN8nExecution:
    """Tests for getting n8n execution status."""

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_n8n_client")
    async def test_get_execution_success(self, mock_get_client, mock_n8n_client, mock_current_user):
        """Test getting execution status successfully."""
        mock_get_client.return_value = mock_n8n_client
        
        mock_execution = MagicMock()
        mock_execution.id = "exec-123"
        mock_execution.workflow_id = "wf-1"
        mock_execution.status.value = "success"
        mock_execution.started_at = None
        mock_execution.finished_at = None
        mock_execution.data = {"result": "done"}
        mock_execution.error = None
        
        mock_n8n_client.get_execution = AsyncMock(return_value=mock_execution)

        response = await get_n8n_execution(
            execution_id="exec-123",
            current_user=mock_current_user
        )

        assert response["execution_id"] == "exec-123"
        assert response["workflow_id"] == "wf-1"
        assert response["status"] == "success"

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_n8n_client")
    async def test_get_execution_error(self, mock_get_client, mock_n8n_client, mock_current_user):
        """Test getting execution with error."""
        mock_get_client.return_value = mock_n8n_client
        mock_n8n_client.get_execution = AsyncMock(side_effect=Exception("Not found"))

        with pytest.raises(HTTPException) as exc_info:
            await get_n8n_execution(
                execution_id="non-existent",
                current_user=mock_current_user
            )

        assert exc_info.value.status_code == 500


class TestTriggerN8nWebhook:
    """Tests for triggering n8n webhooks."""

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_n8n_client")
    async def test_trigger_webhook_success(self, mock_get_client, mock_n8n_client, mock_current_user):
        """Test triggering webhook successfully."""
        mock_get_client.return_value = mock_n8n_client
        mock_n8n_client.trigger_webhook = AsyncMock(return_value={"status": "ok"})

        request = N8nWebhookTrigger(
            webhook_url="http://n8n.local/webhook/abc",
            data={"event": "test"}
        )

        response = await trigger_n8n_webhook(data=request, current_user=mock_current_user)

        assert response["success"] is True
        assert response["response"] == {"status": "ok"}


# ==================== TYPEBOT CLIENT TESTS ====================

class TestTypebotClient:
    """Tests for Typebot client creation."""

    @patch("api.routes.integrations.settings")
    def test_get_typebot_client_not_configured(self, mock_settings):
        """Test Typebot client when not configured."""
        mock_settings.TYPEBOT_API_URL = None

        with pytest.raises(HTTPException) as exc_info:
            get_typebot_client()

        assert exc_info.value.status_code == 503
        assert "Typebot não configurado" in str(exc_info.value.detail)


# ==================== TYPEBOT CHAT TESTS ====================

class TestStartTypebotChat:
    """Tests for starting Typebot chat."""

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_redis")
    @patch("api.routes.integrations.get_typebot_client")
    async def test_start_chat_success(
        self, mock_get_client, mock_get_redis, mock_typebot_client, mock_redis, mock_current_user, typebot_start_chat
    ):
        """Test starting chat successfully."""
        mock_get_client.return_value = mock_typebot_client
        mock_get_redis.return_value = mock_redis

        mock_session = MagicMock()
        mock_session.session_id = "session-123"
        mock_session.messages = []
        mock_session.input_request = None
        mock_session.is_completed = False
        mock_session.model_dump_json = MagicMock(return_value='{}')
        
        mock_typebot_client.start_chat = AsyncMock(return_value=mock_session)

        response = await start_typebot_chat(
            data=typebot_start_chat,
            current_user=mock_current_user
        )

        assert response["session_id"] == "session-123"
        assert response["is_completed"] is False
        mock_redis.set.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_redis")
    @patch("api.routes.integrations.get_typebot_client")
    async def test_start_chat_with_messages(
        self, mock_get_client, mock_get_redis, mock_typebot_client, mock_redis, mock_current_user
    ):
        """Test starting chat with initial messages."""
        mock_get_client.return_value = mock_typebot_client
        mock_get_redis.return_value = mock_redis

        mock_message = MagicMock()
        mock_message.type.value = "text"
        mock_message.content = "Hello!"
        mock_message.rich_content = None

        mock_input = MagicMock()
        mock_input.type.value = "text"
        mock_input.options = None
        mock_input.placeholder = "Type here..."

        mock_session = MagicMock()
        mock_session.session_id = "session-123"
        mock_session.messages = [mock_message]
        mock_session.input_request = mock_input
        mock_session.is_completed = False
        mock_session.model_dump_json = MagicMock(return_value='{}')
        
        mock_typebot_client.start_chat = AsyncMock(return_value=mock_session)

        request = TypebotStartChat(bot_id="bot-1")

        response = await start_typebot_chat(
            data=request,
            current_user=mock_current_user
        )

        assert len(response["messages"]) == 1
        assert response["messages"][0]["content"] == "Hello!"
        assert response["input_request"]["type"] == "text"


class TestSendTypebotMessage:
    """Tests for sending Typebot messages."""

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_redis")
    @patch("api.routes.integrations.get_typebot_client")
    async def test_send_message_success(
        self, mock_get_client, mock_get_redis, mock_typebot_client, mock_redis, mock_current_user
    ):
        """Test sending message successfully."""
        mock_get_client.return_value = mock_typebot_client
        mock_get_redis.return_value = mock_redis

        mock_session = MagicMock()
        mock_session.session_id = "session-123"
        mock_session.messages = []
        mock_session.input_request = None
        mock_session.is_completed = False
        mock_session.model_dump_json = MagicMock(return_value='{}')
        
        mock_typebot_client.send_message = AsyncMock(return_value=mock_session)

        request = TypebotSendMessage(
            session_id="session-123",
            message="Hello bot!"
        )

        response = await send_typebot_message(
            data=request,
            current_user=mock_current_user
        )

        assert response["session_id"] == "session-123"

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_redis")
    @patch("api.routes.integrations.get_typebot_client")
    async def test_send_message_error(
        self, mock_get_client, mock_get_redis, mock_typebot_client, mock_current_user
    ):
        """Test sending message with error."""
        mock_get_client.return_value = mock_typebot_client
        mock_typebot_client.send_message = AsyncMock(side_effect=Exception("Session expired"))

        request = TypebotSendMessage(
            session_id="expired-session",
            message="Hello"
        )

        with pytest.raises(HTTPException) as exc_info:
            await send_typebot_message(
                data=request,
                current_user=mock_current_user
            )

        assert exc_info.value.status_code == 500


class TestSetTypebotVariable:
    """Tests for setting Typebot variables."""

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_typebot_client")
    async def test_set_variable_success(self, mock_get_client, mock_typebot_client, mock_current_user):
        """Test setting variable successfully."""
        mock_get_client.return_value = mock_typebot_client
        mock_typebot_client.set_variable = AsyncMock(return_value=True)

        request = TypebotSetVariable(
            session_id="session-123",
            variable_name="user_name",
            value="John Doe"
        )

        response = await set_typebot_variable(
            data=request,
            current_user=mock_current_user
        )

        assert response["success"] is True
        assert response["variable"] == "user_name"
        assert response["value"] == "John Doe"


class TestGetTypebotSession:
    """Tests for getting Typebot session."""

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_redis")
    async def test_get_session_success(self, mock_get_redis, mock_redis, mock_current_user):
        """Test getting session successfully."""
        mock_get_redis.return_value = mock_redis
        mock_redis.get = AsyncMock(return_value='{"session_id": "session-123", "is_completed": false}')

        response = await get_typebot_session(
            session_id="session-123",
            current_user=mock_current_user
        )

        assert response["session_id"] == "session-123"

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_redis")
    async def test_get_session_not_found(self, mock_get_redis, mock_redis, mock_current_user):
        """Test getting non-existent session."""
        mock_get_redis.return_value = mock_redis
        mock_redis.get = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_typebot_session(
                session_id="non-existent",
                current_user=mock_current_user
            )

        assert exc_info.value.status_code == 404
        assert "Sessão não encontrada" in str(exc_info.value.detail)


# ==================== CONFIGURATION TESTS ====================

class TestGetIntegrationConfig:
    """Tests for getting integration config."""

    @pytest.mark.asyncio
    @patch("api.routes.integrations.settings")
    async def test_get_config_all_configured(self, mock_settings, mock_current_user):
        """Test getting config when all integrations configured."""
        mock_settings.N8N_API_URL = "http://n8n.local"
        mock_settings.TYPEBOT_API_URL = "http://typebot.local"
        mock_settings.EVOLUTION_API_URL = "http://evolution.local"

        response = await get_integration_config(current_user=mock_current_user)

        assert response["n8n"]["configured"] is True
        assert response["typebot"]["configured"] is True
        assert response["evolution_api"]["configured"] is True

    @pytest.mark.asyncio
    @patch("api.routes.integrations.settings")
    async def test_get_config_none_configured(self, mock_settings, mock_current_user):
        """Test getting config when nothing configured."""
        mock_settings.N8N_API_URL = None
        mock_settings.TYPEBOT_API_URL = None
        mock_settings.EVOLUTION_API_URL = None

        response = await get_integration_config(current_user=mock_current_user)

        assert response["n8n"]["configured"] is False
        assert response["typebot"]["configured"] is False
        assert response["evolution_api"]["configured"] is False


class TestUpdateIntegrationConfig:
    """Tests for updating integration config."""

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_redis")
    async def test_update_config_success(self, mock_get_redis, mock_redis, mock_current_user):
        """Test updating config successfully."""
        mock_get_redis.return_value = mock_redis

        config = IntegrationConfig(
            n8n_url="http://new-n8n.local",
            n8n_api_key="new-api-key",
            typebot_url="http://new-typebot.local"
        )

        response = await update_integration_config(
            data=config,
            current_user=mock_current_user
        )

        assert response["status"] == "updated"
        assert mock_redis.set.await_count == 3

    @pytest.mark.asyncio
    @patch("api.routes.integrations.get_redis")
    async def test_update_config_partial(self, mock_get_redis, mock_redis, mock_current_user):
        """Test updating config partially."""
        mock_get_redis.return_value = mock_redis

        config = IntegrationConfig(n8n_url="http://n8n.local")

        response = await update_integration_config(
            data=config,
            current_user=mock_current_user
        )

        assert response["status"] == "updated"
        mock_redis.set.assert_awaited_once()


# ==================== MODEL VALIDATION TESTS ====================

class TestModels:
    """Tests for Pydantic models."""

    def test_n8n_workflow_trigger(self):
        """Test N8nWorkflowTrigger model."""
        trigger = N8nWorkflowTrigger(
            workflow_id="wf-1",
            data={"key": "value"},
            wait_for_result=True
        )
        assert trigger.workflow_id == "wf-1"
        assert trigger.wait_for_result is True

    def test_n8n_webhook_trigger(self):
        """Test N8nWebhookTrigger model."""
        trigger = N8nWebhookTrigger(
            webhook_url="http://webhook.local",
            data={}
        )
        assert trigger.webhook_url == "http://webhook.local"

    def test_typebot_start_chat(self):
        """Test TypebotStartChat model."""
        chat = TypebotStartChat(
            bot_id="bot-1",
            user_id="user-1",
            initial_variables={"name": "Test"}
        )
        assert chat.bot_id == "bot-1"
        assert chat.initial_variables["name"] == "Test"

    def test_typebot_send_message(self):
        """Test TypebotSendMessage model."""
        msg = TypebotSendMessage(
            session_id="session-1",
            message="Hello"
        )
        assert msg.session_id == "session-1"

    def test_typebot_set_variable(self):
        """Test TypebotSetVariable model."""
        var = TypebotSetVariable(
            session_id="session-1",
            variable_name="age",
            value=25
        )
        assert var.variable_name == "age"
        assert var.value == 25

    def test_integration_config(self):
        """Test IntegrationConfig model."""
        config = IntegrationConfig(
            n8n_url="http://n8n.local",
            typebot_url="http://typebot.local"
        )
        assert config.n8n_url == "http://n8n.local"


# ==================== ROUTER TESTS ====================

class TestRouter:
    """Tests for router configuration."""

    def test_router_has_n8n_endpoints(self):
        """Verify router has n8n endpoints."""
        routes = [r.path for r in router.routes]
        
        assert "/n8n/workflows" in routes
        assert "/n8n/workflows/trigger" in routes
        assert "/n8n/executions/{execution_id}" in routes
        assert "/n8n/webhooks/trigger" in routes

    def test_router_has_typebot_endpoints(self):
        """Verify router has Typebot endpoints."""
        routes = [r.path for r in router.routes]
        
        assert "/typebot/chat/start" in routes
        assert "/typebot/chat/send" in routes
        assert "/typebot/variables/set" in routes
        assert "/typebot/sessions/{session_id}" in routes

    def test_router_has_config_endpoints(self):
        """Verify router has config endpoints."""
        routes = [r.path for r in router.routes]
        
        assert "/config" in routes
