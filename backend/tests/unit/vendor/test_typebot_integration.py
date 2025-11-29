"""
Unit Tests - Typebot Integration
================================
Testes unitários para integração com Typebot.

Cobertura:
- TypebotConfig dataclass
- ChatSession dataclass
- TypebotClient métodos
- Tratamento de erros
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from vendor.integrations.typebot import (
    TypebotClient,
    TypebotConfig,
    ChatSession,
    BotMessage,
    InputRequest,
    InputType,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def typebot_config() -> TypebotConfig:
    """Configuração padrão do Typebot."""
    return TypebotConfig(
        api_url="https://typebot.example.com",
        api_token="test-token",
        public_id="test-bot-id"
    )


@pytest.fixture
def chat_session() -> ChatSession:
    """Sessão de chat para testes."""
    return ChatSession(
        session_id="session-123",
        typebot_id="test-bot-id",
        messages=[{"type": "text", "content": "Hello!"}],
        current_input=None,
        is_completed=False
    )


@pytest.fixture
def mock_httpx_client():
    """Mock do httpx.AsyncClient."""
    with patch("httpx.AsyncClient") as mock:
        client_instance = AsyncMock()
        mock.return_value = client_instance
        yield client_instance


# ============================================
# DATACLASS TESTS
# ============================================

class TestTypebotConfig:
    """Testes para TypebotConfig dataclass."""
    
    def test_config_creation(self, typebot_config):
        """Deve criar config com valores."""
        assert typebot_config.api_url == "https://typebot.example.com"
        assert typebot_config.api_token == "test-token"
        assert typebot_config.public_id == "test-bot-id"
    
    def test_config_without_token(self):
        """Deve criar config sem token."""
        config = TypebotConfig(
            api_url="https://typebot.io",
            public_id="my-bot"
        )
        
        assert config.api_token is None
    
    def test_config_without_public_id(self):
        """Deve criar config sem public_id."""
        config = TypebotConfig(
            api_url="https://typebot.io"
        )
        
        assert config.public_id is None


class TestChatSession:
    """Testes para ChatSession dataclass."""
    
    def test_session_creation(self, chat_session):
        """Deve criar sessão com valores."""
        assert chat_session.session_id == "session-123"
        assert chat_session.typebot_id == "test-bot-id"
        assert len(chat_session.messages) == 1
        assert chat_session.is_completed is False
    
    def test_session_completed(self):
        """Deve criar sessão completada."""
        session = ChatSession(
            session_id="session-456",
            typebot_id="bot-id",
            messages=[],
            is_completed=True
        )
        
        assert session.is_completed is True
    
    def test_session_with_input(self):
        """Deve criar sessão com input request."""
        session = ChatSession(
            session_id="session-789",
            typebot_id="bot-id",
            messages=[],
            current_input={"type": "text input", "placeholder": "Nome"}
        )
        
        assert session.current_input is not None
        assert session.current_input["type"] == "text input"


class TestBotMessage:
    """Testes para BotMessage dataclass."""
    
    def test_text_message(self):
        """Deve criar mensagem de texto."""
        msg = BotMessage(
            content="Hello!",
            type="text"
        )
        
        assert msg.content == "Hello!"
        assert msg.type == "text"
        assert msg.rich_content is None
    
    def test_rich_message(self):
        """Deve criar mensagem com rich content."""
        msg = BotMessage(
            content="Click the button",
            type="rich",
            rich_content={"buttons": [{"label": "OK"}]}
        )
        
        assert msg.rich_content is not None
        assert "buttons" in msg.rich_content


class TestInputRequest:
    """Testes para InputRequest dataclass."""
    
    def test_text_input(self):
        """Deve criar solicitação de texto."""
        req = InputRequest(
            input_type=InputType.TEXT,
            placeholder="Digite seu nome"
        )
        
        assert req.input_type == InputType.TEXT
        assert req.placeholder == "Digite seu nome"
    
    def test_choice_input(self):
        """Deve criar solicitação de escolha."""
        req = InputRequest(
            input_type=InputType.CHOICE,
            options=["Sim", "Não", "Talvez"]
        )
        
        assert req.input_type == InputType.CHOICE
        assert len(req.options) == 3


class TestInputType:
    """Testes para InputType enum."""
    
    def test_all_input_types(self):
        """Deve ter todos os tipos de input."""
        expected_types = [
            "TEXT", "NUMBER", "EMAIL", "URL", "DATE",
            "PHONE", "CHOICE", "PAYMENT", "FILE"
        ]
        
        actual_types = [t.name for t in InputType]
        
        for expected in expected_types:
            assert expected in actual_types


# ============================================
# CLIENT TESTS
# ============================================

class TestTypebotClient:
    """Testes para TypebotClient."""
    
    def test_client_creation(self, typebot_config):
        """Deve criar cliente com configuração."""
        with patch("httpx.AsyncClient"):
            client = TypebotClient(typebot_config)
            assert client.config == typebot_config
    
    @pytest.mark.asyncio
    async def test_start_chat(self, typebot_config):
        """Deve iniciar conversa."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sessionId": "new-session",
            "messages": [{"type": "text", "content": "Olá!"}],
            "input": None,
            "isCompleted": False
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = TypebotClient(typebot_config)
            session = await client.start_chat()
            
            assert session.session_id == "new-session"
            assert len(session.messages) == 1
    
    @pytest.mark.asyncio
    async def test_start_chat_with_variables(self, typebot_config):
        """Deve iniciar conversa com variáveis pré-definidas."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sessionId": "session-with-vars",
            "messages": [],
            "input": None,
            "isCompleted": False
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = TypebotClient(typebot_config)
            session = await client.start_chat(
                prefilted_variables={"name": "João", "email": "joao@email.com"}
            )
            
            assert session.session_id == "session-with-vars"
    
    @pytest.mark.asyncio
    async def test_start_chat_without_bot_id(self):
        """Deve lançar erro sem bot_id."""
        config = TypebotConfig(api_url="https://typebot.io")
        
        with patch("httpx.AsyncClient"):
            client = TypebotClient(config)
            
            with pytest.raises(ValueError, match="typebot_id"):
                await client.start_chat()
    
    @pytest.mark.asyncio
    async def test_send_message(self, typebot_config):
        """Deve enviar mensagem."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "messages": [{"type": "text", "content": "Resposta do bot"}],
            "input": {"type": "text input"},
            "isCompleted": False
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = TypebotClient(typebot_config)
            session = await client.send_message("session-123", "Olá!")
            
            assert len(session.messages) == 1
            assert session.current_input is not None
    
    @pytest.mark.asyncio
    async def test_set_variable(self, typebot_config):
        """Deve definir variável na sessão."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = TypebotClient(typebot_config)
            result = await client.set_variable("session-123", "nome", "João")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_set_variable_error(self, typebot_config):
        """Deve tratar erro ao definir variável."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("API Error")
            mock_httpx.return_value = mock_client
            
            client = TypebotClient(typebot_config)
            result = await client.set_variable("session-123", "nome", "João")
            
            assert result is False


# ============================================
# ERROR HANDLING TESTS
# ============================================

class TestTypebotClientErrors:
    """Testes de tratamento de erros."""
    
    @pytest.mark.asyncio
    async def test_start_chat_http_error(self, typebot_config):
        """Deve tratar erro HTTP ao iniciar chat."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404)
            )
            mock_httpx.return_value = mock_client
            
            client = TypebotClient(typebot_config)
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.start_chat()
    
    @pytest.mark.asyncio
    async def test_send_message_network_error(self, typebot_config):
        """Deve tratar erro de rede ao enviar mensagem."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_httpx.return_value = mock_client
            
            client = TypebotClient(typebot_config)
            
            with pytest.raises(httpx.ConnectError):
                await client.send_message("session-123", "teste")


# ============================================
# CONTEXT MANAGER TESTS
# ============================================

class TestTypebotClientContextManager:
    """Testes de context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self, typebot_config):
        """Deve funcionar como context manager."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_httpx.return_value = mock_client
            
            async with TypebotClient(typebot_config) as client:
                assert client is not None
            
            mock_client.aclose.assert_called_once()
