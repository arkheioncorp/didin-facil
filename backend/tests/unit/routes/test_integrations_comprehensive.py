"""
Comprehensive tests for integrations.py routes.
Target: Increase coverage from 41% to 90%+
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {"id": "user-123", "email": "test@example.com", "name": "Test User"}


@pytest.fixture
def mock_workflow():
    """Mock n8n workflow object."""
    return {
        "id": "wf-123",
        "name": "Test Workflow",
        "active": True,
        "nodes": []
    }


@pytest.fixture
def mock_execution():
    """Mock n8n execution object."""
    mock = MagicMock()
    mock.id = "exec-123"
    mock.workflow_id = "wf-123"
    mock.status = MagicMock(value="success")
    mock.started_at = datetime(2024, 1, 1, 12, 0)
    mock.finished_at = datetime(2024, 1, 1, 12, 5)
    mock.data = {"result": "success"}
    mock.error = None
    return mock


@pytest.fixture
def mock_typebot_session():
    """Mock Typebot session object."""
    mock = MagicMock()
    mock.session_id = "session-123"
    mock.messages = [
        MagicMock(type=MagicMock(value="text"), content="Hello", rich_content=None)
    ]
    mock.input_request = MagicMock(
        type=MagicMock(value="text"),
        options=[],
        placeholder="Type here..."
    )
    mock.is_completed = False
    mock.model_dump_json.return_value = '{"session_id": "session-123"}'
    return mock


# ============================================
# N8N CLIENT TESTS
# ============================================

class TestGetN8nClient:
    """Tests for get_n8n_client helper function."""
    
    def test_get_n8n_client_configured(self):
        """Test getting n8n client when properly configured."""
        with patch("api.routes.integrations.settings") as mock_settings:
            mock_settings.N8N_API_URL = "http://n8n.example.com"
            mock_settings.N8N_API_KEY = "api-key-123"
            
            from api.routes.integrations import get_n8n_client
            
            client = get_n8n_client()
            assert client is not None
    
    def test_get_n8n_client_not_configured(self):
        """Test error when n8n not configured."""
        with patch("api.routes.integrations.settings") as mock_settings:
            mock_settings.N8N_API_URL = None
            mock_settings.N8N_API_KEY = None
            
            from api.routes.integrations import get_n8n_client
            
            with pytest.raises(HTTPException) as exc:
                get_n8n_client()
            
            assert exc.value.status_code == 503
            assert "não configurado" in str(exc.value.detail)


class TestListN8nWorkflows:
    """Tests for GET /n8n/workflows endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_workflows_success(self, mock_user, mock_workflow):
        """Test listing n8n workflows."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.list_workflows = AsyncMock(return_value=[mock_workflow])
        
        with patch("api.routes.integrations.get_n8n_client", return_value=mock_client):
            from api.routes.integrations import list_n8n_workflows
            
            result = await list_n8n_workflows(active_only=True, current_user=mock_user)
            
            assert result["total"] == 1
            assert len(result["workflows"]) == 1
    
    @pytest.mark.asyncio
    async def test_list_workflows_error(self, mock_user):
        """Test error handling when listing fails."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.list_workflows = AsyncMock(side_effect=Exception("API Error"))
        
        with patch("api.routes.integrations.get_n8n_client", return_value=mock_client):
            from api.routes.integrations import list_n8n_workflows
            
            with pytest.raises(HTTPException) as exc:
                await list_n8n_workflows(active_only=True, current_user=mock_user)
            
            assert exc.value.status_code == 500


class TestTriggerN8nWorkflow:
    """Tests for POST /n8n/workflows/trigger endpoint."""
    
    @pytest.mark.asyncio
    async def test_trigger_workflow_success(self, mock_user, mock_execution):
        """Test triggering workflow successfully."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.execute_workflow = AsyncMock(return_value=mock_execution)
        
        with patch("api.routes.integrations.get_n8n_client", return_value=mock_client):
            from api.routes.integrations import (N8nWorkflowTrigger,
                                                 trigger_n8n_workflow)
            
            data = N8nWorkflowTrigger(
                workflow_id="wf-123",
                data={"key": "value"},
                wait_for_result=False
            )
            mock_bg = MagicMock()
            
            result = await trigger_n8n_workflow(data=data, background_tasks=mock_bg, current_user=mock_user)
            
            assert result["execution_id"] == "exec-123"
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_trigger_workflow_with_wait(self, mock_user, mock_execution):
        """Test triggering workflow and waiting for result."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.execute_workflow = AsyncMock(return_value=mock_execution)
        
        with patch("api.routes.integrations.get_n8n_client", return_value=mock_client):
            from api.routes.integrations import (N8nWorkflowTrigger,
                                                 trigger_n8n_workflow)
            
            data = N8nWorkflowTrigger(
                workflow_id="wf-123",
                data={},
                wait_for_result=True
            )
            mock_bg = MagicMock()
            
            result = await trigger_n8n_workflow(data=data, background_tasks=mock_bg, current_user=mock_user)
            
            assert result["data"] is not None


class TestGetN8nExecution:
    """Tests for GET /n8n/executions/{execution_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_execution_success(self, mock_user, mock_execution):
        """Test getting execution status."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get_execution = AsyncMock(return_value=mock_execution)
        
        with patch("api.routes.integrations.get_n8n_client", return_value=mock_client):
            from api.routes.integrations import get_n8n_execution
            
            result = await get_n8n_execution(execution_id="exec-123", current_user=mock_user)
            
            assert result["execution_id"] == "exec-123"
            assert result["workflow_id"] == "wf-123"
    
    @pytest.mark.asyncio
    async def test_get_execution_error(self, mock_user):
        """Test error handling when getting execution fails."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get_execution = AsyncMock(side_effect=Exception("Not found"))
        
        with patch("api.routes.integrations.get_n8n_client", return_value=mock_client):
            from api.routes.integrations import get_n8n_execution
            
            with pytest.raises(HTTPException) as exc:
                await get_n8n_execution(execution_id="nonexistent", current_user=mock_user)
            
            assert exc.value.status_code == 500


class TestTriggerN8nWebhook:
    """Tests for POST /n8n/webhooks/trigger endpoint."""
    
    @pytest.mark.asyncio
    async def test_trigger_webhook_success(self, mock_user):
        """Test triggering webhook successfully."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.trigger_webhook = AsyncMock(return_value={"status": "ok"})
        
        with patch("api.routes.integrations.get_n8n_client", return_value=mock_client):
            from api.routes.integrations import (N8nWebhookTrigger,
                                                 trigger_n8n_webhook)
            
            data = N8nWebhookTrigger(
                webhook_url="https://n8n.example.com/webhook/123",
                data={"event": "test"}
            )
            
            result = await trigger_n8n_webhook(data=data, current_user=mock_user)
            
            assert result["success"] is True


# ============================================
# TYPEBOT CLIENT TESTS
# ============================================

class TestGetTypebotClient:
    """Tests for get_typebot_client helper function."""
    
    def test_get_typebot_client_configured(self):
        """Test getting Typebot client when configured."""
        with patch("api.routes.integrations.settings") as mock_settings:
            mock_settings.TYPEBOT_API_URL = "http://typebot.example.com"
            mock_settings.TYPEBOT_PUBLIC_ID = "public-123"
            
            from api.routes.integrations import get_typebot_client
            
            client = get_typebot_client()
            assert client is not None
    
    def test_get_typebot_client_not_configured(self):
        """Test error when Typebot not configured."""
        with patch("api.routes.integrations.settings") as mock_settings:
            mock_settings.TYPEBOT_API_URL = None
            
            from api.routes.integrations import get_typebot_client
            
            with pytest.raises(HTTPException) as exc:
                get_typebot_client()
            
            assert exc.value.status_code == 503


class TestStartTypebotChat:
    """Tests for POST /typebot/chat/start endpoint."""
    
    @pytest.mark.asyncio
    async def test_start_chat_success(self, mock_user, mock_typebot_session):
        """Test starting Typebot chat successfully."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.start_chat = AsyncMock(return_value=mock_typebot_session)
        
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        
        with patch("api.routes.integrations.get_typebot_client", return_value=mock_client), \
             patch("api.routes.integrations.get_redis", return_value=mock_redis):
            
            from api.routes.integrations import (TypebotStartChat,
                                                 start_typebot_chat)
            
            data = TypebotStartChat(
                bot_id="bot-123",
                user_id="user-456",
                initial_variables={"name": "John"}
            )
            
            result = await start_typebot_chat(data=data, current_user=mock_user)
            
            assert result["session_id"] == "session-123"
            assert len(result["messages"]) == 1
    
    @pytest.mark.asyncio
    async def test_start_chat_error(self, mock_user):
        """Test error handling when starting chat fails."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.start_chat = AsyncMock(side_effect=Exception("Bot not found"))
        
        with patch("api.routes.integrations.get_typebot_client", return_value=mock_client):
            from api.routes.integrations import (TypebotStartChat,
                                                 start_typebot_chat)
            
            data = TypebotStartChat(bot_id="invalid")
            
            with pytest.raises(HTTPException) as exc:
                await start_typebot_chat(data=data, current_user=mock_user)
            
            assert exc.value.status_code == 500


class TestSendTypebotMessage:
    """Tests for POST /typebot/chat/send endpoint."""
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_user, mock_typebot_session):
        """Test sending message to Typebot."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.send_message = AsyncMock(return_value=mock_typebot_session)
        
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        
        with patch("api.routes.integrations.get_typebot_client", return_value=mock_client), \
             patch("api.routes.integrations.get_redis", return_value=mock_redis):
            
            from api.routes.integrations import (TypebotSendMessage,
                                                 send_typebot_message)
            
            data = TypebotSendMessage(
                session_id="session-123",
                message="Hello bot"
            )
            
            result = await send_typebot_message(data=data, current_user=mock_user)
            
            assert result["session_id"] == "session-123"


class TestSetTypebotVariable:
    """Tests for POST /typebot/variables/set endpoint."""
    
    @pytest.mark.asyncio
    async def test_set_variable_success(self, mock_user):
        """Test setting Typebot variable."""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.set_variable = AsyncMock(return_value=True)
        
        with patch("api.routes.integrations.get_typebot_client", return_value=mock_client):
            from api.routes.integrations import (TypebotSetVariable,
                                                 set_typebot_variable)
            
            data = TypebotSetVariable(
                session_id="session-123",
                variable_name="user_name",
                value="John Doe"
            )
            
            result = await set_typebot_variable(data=data, current_user=mock_user)
            
            assert result["success"] is True
            assert result["variable"] == "user_name"


class TestGetTypebotSession:
    """Tests for GET /typebot/sessions/{session_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_session_success(self, mock_user):
        """Test getting Typebot session."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value='{"session_id": "session-123"}')
        
        with patch("api.routes.integrations.get_redis", return_value=mock_redis):
            from api.routes.integrations import get_typebot_session
            
            result = await get_typebot_session(session_id="session-123", current_user=mock_user)
            
            assert result["session_id"] == "session-123"
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_user):
        """Test error when session not found."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch("api.routes.integrations.get_redis", return_value=mock_redis):
            from api.routes.integrations import get_typebot_session
            
            with pytest.raises(HTTPException) as exc:
                await get_typebot_session(session_id="nonexistent", current_user=mock_user)
            
            assert exc.value.status_code == 404


# ============================================
# CONFIGURATION TESTS
# ============================================

class TestGetIntegrationConfig:
    """Tests for GET /config endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_config_all_configured(self, mock_user):
        """Test getting config when all integrations configured."""
        with patch("api.routes.integrations.settings") as mock_settings:
            mock_settings.N8N_API_URL = "http://n8n.example.com"
            mock_settings.TYPEBOT_API_URL = "http://typebot.example.com"
            mock_settings.EVOLUTION_API_URL = "http://evolution.example.com"
            
            from api.routes.integrations import get_integration_config
            
            result = await get_integration_config(current_user=mock_user)
            
            assert result["n8n"]["configured"] is True
            assert result["typebot"]["configured"] is True
            assert result["evolution_api"]["configured"] is True
    
    @pytest.mark.asyncio
    async def test_get_config_none_configured(self, mock_user):
        """Test getting config when nothing configured."""
        with patch("api.routes.integrations.settings") as mock_settings:
            mock_settings.N8N_API_URL = None
            mock_settings.TYPEBOT_API_URL = None
            mock_settings.EVOLUTION_API_URL = None
            
            from api.routes.integrations import get_integration_config
            
            result = await get_integration_config(current_user=mock_user)
            
            assert result["n8n"]["configured"] is False
            assert result["typebot"]["configured"] is False


class TestUpdateIntegrationConfig:
    """Tests for POST /config endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_config_success(self, mock_user):
        """Test updating integration config."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        
        with patch("api.routes.integrations.get_redis", return_value=mock_redis):
            from api.routes.integrations import (IntegrationConfig,
                                                 update_integration_config)
            
            data = IntegrationConfig(
                n8n_url="http://new-n8n.example.com",
                n8n_api_key="new-api-key",
                typebot_url="http://new-typebot.example.com",
                typebot_public_id="new-public-id"
            )
            
            result = await update_integration_config(data=data, current_user=mock_user)
            
            assert result["status"] == "updated"
            assert mock_redis.set.call_count >= 1


# ============================================
# PYDANTIC MODEL TESTS
# ============================================

class TestPydanticModels:
    """Tests for Pydantic request models."""
    
    def test_n8n_workflow_trigger_defaults(self):
        """Test N8nWorkflowTrigger with defaults."""
        from api.routes.integrations import N8nWorkflowTrigger
        
        trigger = N8nWorkflowTrigger(workflow_id="wf-123")
        
        assert trigger.data == {}
        assert trigger.wait_for_result is False
    
    def test_typebot_start_chat_defaults(self):
        """Test TypebotStartChat with defaults."""
        from api.routes.integrations import TypebotStartChat
        
        chat = TypebotStartChat(bot_id="bot-123")
        
        assert chat.user_id is None
        assert chat.initial_variables == {}
    
    def test_integration_config_all_optional(self):
        """Test IntegrationConfig with all optional fields."""
        from api.routes.integrations import IntegrationConfig
        
        config = IntegrationConfig()
        
        assert config.n8n_url is None
        assert config.n8n_api_key is None
        assert config.typebot_url is None
