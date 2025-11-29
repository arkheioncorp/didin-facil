"""
Integration Routes Tests
Tests for n8n and Typebot integration endpoints
"""

import pytest
import pytest_asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from api.main import app


@pytest_asyncio.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    from api.middleware.auth import get_current_user
    user = {
        "id": "user_123",
        "email": "test@example.com",
        "plan": "pro"
    }
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides = {}


@pytest.fixture
def mock_n8n_configured():
    """Mock n8n configuration."""
    with patch("api.routes.integrations.settings") as mock_settings:
        mock_settings.N8N_API_URL = "http://localhost:5678"
        mock_settings.N8N_API_KEY = "test-api-key"
        mock_settings.TYPEBOT_API_URL = "http://localhost:3000"
        mock_settings.TYPEBOT_PUBLIC_ID = "test-bot"
        yield mock_settings


class TestN8nIntegration:
    """Tests for n8n integration endpoints."""

    @pytest.mark.asyncio
    async def test_list_workflows(
        self,
        mock_auth_user,
        async_client
    ):
        """Test listing n8n workflows."""
        with patch("api.routes.integrations.get_n8n_client") as mock_client:
            client = AsyncMock()
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=None)
            client.list_workflows.return_value = [
                {"id": "wf1", "name": "Workflow 1", "active": True},
                {"id": "wf2", "name": "Workflow 2", "active": True}
            ]
            mock_client.return_value = client

            response = await async_client.get("/integrations/n8n/workflows")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert len(data["workflows"]) == 2

    @pytest.mark.asyncio
    async def test_trigger_workflow(
        self,
        mock_auth_user,
        async_client
    ):
        """Test triggering n8n workflow."""
        with patch("api.routes.integrations.get_n8n_client") as mock_client:
            # Mock WorkflowExecution result
            mock_execution = MagicMock()
            mock_execution.id = "exec_123"
            mock_execution.status.value = "success"
            mock_execution.started_at = None
            mock_execution.finished_at = None
            mock_execution.data = {"result": "ok"}
            
            client = AsyncMock()
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=None)
            client.execute_workflow.return_value = mock_execution
            mock_client.return_value = client

            response = await async_client.post(
                "/integrations/n8n/workflows/trigger",
                json={
                    "workflow_id": "wf1",
                    "data": {"key": "value"},
                    "wait_for_result": True
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["execution_id"] == "exec_123"
            assert data["status"] == "success"

    @pytest.mark.asyncio
    async def test_get_execution(
        self,
        mock_auth_user,
        async_client
    ):
        """Test getting n8n execution status."""
        with patch("api.routes.integrations.get_n8n_client") as mock_client:
            mock_execution = MagicMock()
            mock_execution.id = "exec_123"
            mock_execution.workflow_id = "wf1"
            mock_execution.status.value = "success"
            mock_execution.started_at = None
            mock_execution.finished_at = None
            mock_execution.data = {"result": "done"}
            mock_execution.error = None
            
            client = AsyncMock()
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=None)
            client.get_execution.return_value = mock_execution
            mock_client.return_value = client

            response = await async_client.get(
                "/integrations/n8n/executions/exec_123"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["execution_id"] == "exec_123"

    @pytest.mark.asyncio
    async def test_trigger_webhook(
        self,
        mock_auth_user,
        async_client
    ):
        """Test triggering n8n webhook."""
        with patch("api.routes.integrations.get_n8n_client") as mock_client:
            client = AsyncMock()
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=None)
            client.trigger_webhook.return_value = {"status": "triggered"}
            mock_client.return_value = client

            response = await async_client.post(
                "/integrations/n8n/webhooks/trigger",
                json={
                    "webhook_url": "https://n8n.example.com/webhook/abc",
                    "data": {"event": "test"}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestTypebotIntegration:
    """Tests for Typebot integration endpoints."""

    @pytest.mark.asyncio
    async def test_start_chat(
        self,
        mock_auth_user,
        async_client
    ):
        """Test starting Typebot chat."""
        with patch("api.routes.integrations.get_typebot_client") as mock_client, \
             patch("api.routes.integrations.get_redis") as mock_redis:
            # Mock message
            mock_msg = MagicMock()
            mock_msg.type.value = "text"
            mock_msg.content = "Olá! Como posso ajudar?"
            mock_msg.rich_content = None
            
            # Mock input request
            mock_input = MagicMock()
            mock_input.type.value = "text"
            mock_input.options = None
            mock_input.placeholder = "Digite sua mensagem..."
            
            # Mock session
            mock_session = MagicMock()
            mock_session.session_id = "session_123"
            mock_session.messages = [mock_msg]
            mock_session.input_request = mock_input
            mock_session.is_completed = False
            mock_session.model_dump_json.return_value = '{"session_id": "session_123"}'
            
            client = AsyncMock()
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=None)
            client.start_chat.return_value = mock_session
            mock_client.return_value = client
            
            redis_mock = AsyncMock()
            mock_redis.return_value = redis_mock

            response = await async_client.post(
                "/integrations/typebot/chat/start",
                json={
                    "bot_id": "bot_123",
                    "initial_variables": {"name": "Test"}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "session_123"
            assert len(data["messages"]) == 1
            assert data["is_completed"] is False

    @pytest.mark.asyncio
    async def test_send_message(
        self,
        mock_auth_user,
        async_client
    ):
        """Test sending message to Typebot."""
        with patch("api.routes.integrations.get_typebot_client") as mock_client, \
             patch("api.routes.integrations.get_redis") as mock_redis:
            # Mock message
            mock_msg = MagicMock()
            mock_msg.type.value = "text"
            mock_msg.content = "Entendi! Aqui está sua resposta."
            mock_msg.rich_content = None
            
            # Mock session
            mock_session = MagicMock()
            mock_session.session_id = "session_123"
            mock_session.messages = [mock_msg]
            mock_session.input_request = None
            mock_session.is_completed = False
            mock_session.model_dump_json.return_value = '{"session_id": "session_123"}'
            
            client = AsyncMock()
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=None)
            client.send_message.return_value = mock_session
            mock_client.return_value = client
            
            redis_mock = AsyncMock()
            mock_redis.return_value = redis_mock

            response = await async_client.post(
                "/integrations/typebot/chat/send",
                json={
                    "session_id": "session_123",
                    "message": "Olá"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "session_123"

    @pytest.mark.asyncio
    async def test_set_variable(
        self,
        mock_auth_user,
        async_client
    ):
        """Test setting Typebot variable."""
        with patch("api.routes.integrations.get_typebot_client") as mock_client:
            client = AsyncMock()
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=None)
            client.set_variable.return_value = True
            mock_client.return_value = client

            response = await async_client.post(
                "/integrations/typebot/variables/set",
                json={
                    "session_id": "session_123",
                    "variable_name": "user_name",
                    "value": "John"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["variable"] == "user_name"

    @pytest.mark.asyncio
    async def test_get_session(
        self,
        mock_auth_user,
        async_client
    ):
        """Test getting Typebot session."""
        session_data = {
            "session_id": "session_123",
            "messages": [],
            "is_completed": False
        }

        with patch("api.routes.integrations.get_redis") as mock_redis:
            redis_mock = AsyncMock()
            redis_mock.get.return_value = json.dumps(session_data)
            mock_redis.return_value = redis_mock

            response = await async_client.get(
                "/integrations/typebot/sessions/session_123"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session_123"

    @pytest.mark.asyncio
    async def test_get_session_not_found(
        self,
        mock_auth_user,
        async_client
    ):
        """Test getting non-existent session."""
        with patch("api.routes.integrations.get_redis") as mock_redis:
            redis_mock = AsyncMock()
            redis_mock.get.return_value = None
            mock_redis.return_value = redis_mock

            response = await async_client.get(
                "/integrations/typebot/sessions/invalid"
            )

        assert response.status_code == 404


class TestConfigEndpoints:
    """Tests for configuration endpoints."""

    @pytest.mark.asyncio
    async def test_get_config(self, mock_auth_user, async_client):
        """Test getting integration config."""
        response = await async_client.get("/integrations/config")

        assert response.status_code == 200
        data = response.json()
        assert "n8n" in data
        assert "typebot" in data
        assert "evolution_api" in data

    @pytest.mark.asyncio
    async def test_update_config(self, mock_auth_user, async_client):
        """Test updating integration config."""
        with patch("api.routes.integrations.get_redis") as mock_redis:
            redis_mock = AsyncMock()
            mock_redis.return_value = redis_mock

            response = await async_client.post(
                "/integrations/config",
                json={
                    "n8n_url": "https://n8n.example.com",
                    "typebot_url": "https://typebot.example.com"
                }
            )

        assert response.status_code == 200
        assert response.json()["status"] == "updated"
