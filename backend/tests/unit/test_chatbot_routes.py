"""
Testes para Chatbot Routes - api/routes/chatbot.py
Cobertura: start_chat, send_message, get_chat_session, list_typebots,
           get_typebot, get_typebot_results, list_templates, get_template, webhook
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI


# ============================================
# SETUP
# ============================================

@pytest.fixture
def mock_user():
    """Mock de usuário autenticado"""
    user = MagicMock()
    user.id = "user-123"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_typebot_client():
    """Mock do TypebotClient"""
    return AsyncMock()


@pytest.fixture
def mock_webhook_handler():
    """Mock do WebhookHandler"""
    return AsyncMock()


@pytest.fixture
def app(mock_user, mock_typebot_client, mock_webhook_handler):
    """App FastAPI para testes"""
    from fastapi import FastAPI
    
    app = FastAPI()
    
    with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
        with patch("api.routes.chatbot.typebot_client", mock_typebot_client):
            with patch("api.routes.chatbot.webhook_handler", mock_webhook_handler):
                from api.routes.chatbot import router
                app.include_router(router, prefix="/chatbot")
    
    return app


@pytest.fixture
def client(app):
    """Test client"""
    return TestClient(app)


# ============================================
# TESTS: Start Chat
# ============================================

class TestStartChat:
    """Testes do endpoint start_chat"""
    
    @pytest.mark.asyncio
    async def test_start_chat_success(self):
        """Deve iniciar chat com sucesso"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_session = MagicMock()
        mock_session.session_id = "session-abc"
        mock_session.status.value = "active"
        mock_session.messages = [
            MagicMock(id="msg1", type="text", content="Hello!")
        ]
        
        mock_client = AsyncMock()
        mock_client.start_chat.return_value = mock_session
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import start_chat, StartChatRequest
                
                request = StartChatRequest(
                    typebot_id="tb-123",
                    variables={"name": "Test User"}
                )
                
                response = await start_chat(data=request, current_user=mock_user)
                
                assert response["session_id"] == "session-abc"
                assert response["status"] == "active"
                assert len(response["messages"]) == 1
    
    @pytest.mark.asyncio
    async def test_start_chat_error(self):
        """Deve retornar erro 500 em caso de exceção"""
        from fastapi import HTTPException
        
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_client = AsyncMock()
        mock_client.start_chat.side_effect = Exception("API Error")
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import start_chat, StartChatRequest
                
                request = StartChatRequest(typebot_id="tb-123")
                
                with pytest.raises(HTTPException) as exc_info:
                    await start_chat(data=request, current_user=mock_user)
                
                assert exc_info.value.status_code == 500


# ============================================
# TESTS: Send Message
# ============================================

class TestSendMessage:
    """Testes do endpoint send_message"""
    
    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Deve enviar mensagem com sucesso"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_response = {
            "messages": [
                MagicMock(id="msg2", type="text", content="Response!")
            ],
            "input": {"type": "text"},
            "clientSideActions": []
        }
        
        mock_client = AsyncMock()
        mock_client.send_message.return_value = mock_response
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import send_message, SendMessageRequest
                
                request = SendMessageRequest(
                    session_id="session-abc",
                    message="Hello!"
                )
                
                response = await send_message(data=request, current_user=mock_user)
                
                assert len(response["messages"]) == 1
                assert response["input"] == {"type": "text"}
    
    @pytest.mark.asyncio
    async def test_send_message_error(self):
        """Deve retornar erro 500 em caso de exceção"""
        from fastapi import HTTPException
        
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_client = AsyncMock()
        mock_client.send_message.side_effect = Exception("Send error")
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import send_message, SendMessageRequest
                
                request = SendMessageRequest(session_id="session-abc", message="Hi")
                
                with pytest.raises(HTTPException) as exc_info:
                    await send_message(data=request, current_user=mock_user)
                
                assert exc_info.value.status_code == 500


# ============================================
# TESTS: Get Chat Session
# ============================================

class TestGetChatSession:
    """Testes do endpoint get_chat_session"""
    
    @pytest.mark.asyncio
    async def test_get_session_success(self):
        """Deve retornar sessão existente"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_session = {"id": "session-abc", "status": "active"}
        
        mock_client = AsyncMock()
        mock_client.get_session.return_value = mock_session
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import get_chat_session
                
                response = await get_chat_session(
                    session_id="session-abc",
                    current_user=mock_user
                )
                
                assert response["id"] == "session-abc"
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """Deve retornar 404 se sessão não encontrada"""
        from fastapi import HTTPException
        
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_client = AsyncMock()
        mock_client.get_session.return_value = None
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import get_chat_session
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_chat_session(
                        session_id="invalid",
                        current_user=mock_user
                    )
                
                assert exc_info.value.status_code == 404


# ============================================
# TESTS: List Typebots
# ============================================

class TestListTypebots:
    """Testes do endpoint list_typebots"""
    
    @pytest.mark.asyncio
    async def test_list_typebots_success(self):
        """Deve listar typebots com sucesso"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_typebots = [
            {
                "id": "tb1",
                "name": "Bot 1",
                "publicId": "public-tb1",
                "createdAt": "2024-01-01",
                "updatedAt": "2024-01-02"
            }
        ]
        
        mock_client = AsyncMock()
        mock_client.list_typebots.return_value = mock_typebots
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import list_typebots
                
                response = await list_typebots(current_user=mock_user)
                
                assert len(response["typebots"]) == 1
                assert response["typebots"][0]["id"] == "tb1"
    
    @pytest.mark.asyncio
    async def test_list_typebots_with_workspace(self):
        """Deve filtrar por workspace"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_client = AsyncMock()
        mock_client.list_typebots.return_value = []
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import list_typebots
                
                await list_typebots(workspace_id="ws-123", current_user=mock_user)
                
                mock_client.list_typebots.assert_called_once_with("ws-123")
    
    @pytest.mark.asyncio
    async def test_list_typebots_error(self):
        """Deve retornar 500 em caso de erro"""
        from fastapi import HTTPException
        
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_client = AsyncMock()
        mock_client.list_typebots.side_effect = Exception("API Error")
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import list_typebots
                
                with pytest.raises(HTTPException) as exc_info:
                    await list_typebots(current_user=mock_user)
                
                assert exc_info.value.status_code == 500


# ============================================
# TESTS: Get Typebot
# ============================================

class TestGetTypebot:
    """Testes do endpoint get_typebot"""
    
    @pytest.mark.asyncio
    async def test_get_typebot_success(self):
        """Deve retornar typebot existente"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_typebot = {"id": "tb1", "name": "Bot 1"}
        
        mock_client = AsyncMock()
        mock_client.get_typebot.return_value = mock_typebot
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import get_typebot
                
                response = await get_typebot(typebot_id="tb1", current_user=mock_user)
                
                assert response["id"] == "tb1"
    
    @pytest.mark.asyncio
    async def test_get_typebot_not_found(self):
        """Deve retornar 404 se não encontrado"""
        from fastapi import HTTPException
        
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_client = AsyncMock()
        mock_client.get_typebot.return_value = None
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import get_typebot
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_typebot(typebot_id="invalid", current_user=mock_user)
                
                assert exc_info.value.status_code == 404


# ============================================
# TESTS: Get Typebot Results
# ============================================

class TestGetTypebotResults:
    """Testes do endpoint get_typebot_results"""
    
    @pytest.mark.asyncio
    async def test_get_results_success(self):
        """Deve retornar resultados com sucesso"""
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_results = {
            "results": [{"id": "r1", "data": {}}],
            "nextCursor": None
        }
        
        mock_client = AsyncMock()
        mock_client.get_results.return_value = mock_results
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import get_typebot_results
                
                response = await get_typebot_results(
                    typebot_id="tb1",
                    limit=10,
                    current_user=mock_user
                )
                
                assert response == mock_results
    
    @pytest.mark.asyncio
    async def test_get_results_error(self):
        """Deve retornar 500 em caso de erro"""
        from fastapi import HTTPException
        
        mock_user = MagicMock()
        mock_user.id = "user-123"
        
        mock_client = AsyncMock()
        mock_client.get_results.side_effect = Exception("API Error")
        
        with patch("api.routes.chatbot.get_current_user", return_value=mock_user):
            with patch("api.routes.chatbot.typebot_client", mock_client):
                from api.routes.chatbot import get_typebot_results
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_typebot_results(
                        typebot_id="tb1",
                        current_user=mock_user
                    )
                
                assert exc_info.value.status_code == 500


# ============================================
# TESTS: Templates
# ============================================

class TestTemplates:
    """Testes dos endpoints de templates"""
    
    @pytest.mark.asyncio
    async def test_list_templates(self):
        """Deve listar templates disponíveis"""
        mock_templates = {
            "welcome": {
                "name": "Welcome Bot",
                "description": "Bot de boas-vindas",
                "blocks": []
            }
        }
        
        with patch("api.routes.chatbot.DIDIN_TYPEBOT_TEMPLATES", mock_templates, create=True):
            # Import after patch to get the mocked templates
            with patch.dict("integrations.typebot.__dict__", {"DIDIN_TYPEBOT_TEMPLATES": mock_templates}):
                from api.routes.chatbot import list_chatbot_templates
                
                response = await list_chatbot_templates()
                
                assert "templates" in response
    
    @pytest.mark.asyncio
    async def test_get_template_success(self):
        """Deve retornar template existente"""
        mock_templates = {
            "welcome": {
                "name": "Welcome Bot",
                "description": "Bot de boas-vindas",
                "blocks": []
            }
        }
        
        with patch("integrations.typebot.DIDIN_TYPEBOT_TEMPLATES", mock_templates):
            from api.routes.chatbot import get_template
            
            response = await get_template("welcome")
            assert response["name"] == "Welcome Bot"
    
    @pytest.mark.asyncio
    async def test_get_template_not_found(self):
        """Deve retornar 404 para template inexistente"""
        from fastapi import HTTPException
        
        mock_templates = {}
        
        with patch.dict("integrations.typebot.__dict__", {"DIDIN_TYPEBOT_TEMPLATES": mock_templates}):
            from api.routes.chatbot import get_template
            
            with pytest.raises(HTTPException) as exc_info:
                await get_template("nonexistent")
            
            assert exc_info.value.status_code == 404


# ============================================
# TESTS: Webhook
# ============================================

class TestTypebotWebhook:
    """Testes do webhook do Typebot"""
    
    @pytest.mark.asyncio
    async def test_webhook_success(self):
        """Deve processar webhook com sucesso"""
        from fastapi import Request
        
        mock_request = AsyncMock(spec=Request)
        mock_request.json.return_value = {"event": "conversation.started"}
        
        mock_handler = AsyncMock()
        mock_handler.process_webhook.return_value = {"status": "ok"}
        
        with patch("api.routes.chatbot.webhook_handler", mock_handler):
            from api.routes.chatbot import typebot_webhook
            
            response = await typebot_webhook(mock_request)
            
            assert response["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_webhook_error(self):
        """Deve retornar erro ao falhar processamento"""
        from fastapi import Request
        
        mock_request = AsyncMock(spec=Request)
        mock_request.json.side_effect = Exception("Parse error")
        
        with patch("api.routes.chatbot.webhook_handler", AsyncMock()):
            from api.routes.chatbot import typebot_webhook
            
            response = await typebot_webhook(mock_request)
            
            assert "error" in response


# ============================================
# TESTS: Webhook Handlers
# ============================================

class TestWebhookHandlers:
    """Testes dos handlers de webhook"""
    
    @pytest.mark.asyncio
    async def test_on_conversation_started(self):
        """Handler de início de conversa"""
        from api.routes.chatbot import on_conversation_started
        
        payload = {"sessionId": "session-123"}
        
        result = await on_conversation_started(payload)
        
        assert result["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_on_conversation_completed(self):
        """Handler de fim de conversa"""
        from api.routes.chatbot import on_conversation_completed
        
        payload = {
            "sessionId": "session-123",
            "variables": {"name": "Test"}
        }
        
        result = await on_conversation_completed(payload)
        
        assert result["status"] == "ok"
