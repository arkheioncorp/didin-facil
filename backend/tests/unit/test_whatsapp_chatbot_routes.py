"""
Tests for WhatsApp Chatbot Routes
==================================
Comprehensive tests for chatbot message processing and webhook endpoints.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from api.routes.whatsapp_chatbot import (ChatbotRequest, ChatbotResponse,
                                         ProductSearchResult, WhatsAppChatbot,
                                         chatbot, router)
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
async def client(app):
    """Async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def mock_cache():
    """Mock cache service."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def chatbot_instance(mock_cache):
    """Create chatbot instance with mocked cache."""
    bot = WhatsAppChatbot()
    bot.cache = mock_cache
    return bot


# ============================================
# UNIT TESTS - Models
# ============================================

class TestModels:
    """Tests for Pydantic models."""

    def test_product_search_result(self):
        """Test ProductSearchResult model."""
        product = ProductSearchResult(
            id="1",
            title="Test Product",
            price=49.90,
            original_price=99.90,
            discount_percent=50,
            image_url="https://example.com/image.jpg",
            shop_name="TestShop",
            rating=4.5,
            sales_count=1000
        )
        assert product.id == "1"
        assert product.title == "Test Product"
        assert product.price == 49.90
        assert product.discount_percent == 50

    def test_product_search_result_defaults(self):
        """Test ProductSearchResult with defaults."""
        product = ProductSearchResult(
            id="1",
            title="Test Product",
            price=49.90
        )
        assert product.original_price is None
        assert product.discount_percent is None
        assert product.sales_count == 0

    def test_chatbot_request(self):
        """Test ChatbotRequest model."""
        request = ChatbotRequest(
            phone="5511999999999",
            message="Hello",
            instance_name="test-instance",
            push_name="John"
        )
        assert request.phone == "5511999999999"
        assert request.message == "Hello"
        assert request.push_name == "John"

    def test_chatbot_request_defaults(self):
        """Test ChatbotRequest with defaults."""
        request = ChatbotRequest(
            phone="5511999999999",
            message="Hello"
        )
        assert request.instance_name == "didin-whatsapp"
        assert request.push_name is None

    def test_chatbot_response(self):
        """Test ChatbotResponse model."""
        response = ChatbotResponse(
            response_text="Hello!",
            products=[
                ProductSearchResult(id="1", title="Test", price=10.0)
            ],
            action="show_menu",
            metadata={"key": "value"}
        )
        assert response.response_text == "Hello!"
        assert len(response.products) == 1
        assert response.action == "show_menu"

    def test_chatbot_response_minimal(self):
        """Test ChatbotResponse with only required fields."""
        response = ChatbotResponse(response_text="Hello!")
        assert response.products is None
        assert response.action is None


# ============================================
# UNIT TESTS - WhatsAppChatbot Class
# ============================================

class TestWhatsAppChatbot:
    """Tests for WhatsAppChatbot class."""

    @pytest.mark.asyncio
    async def test_show_welcome(self, chatbot_instance):
        """Test welcome message."""
        response = await chatbot_instance._show_welcome("João")
        assert "João" in response.response_text
        assert "Didin Fácil" in response.response_text
        assert response.action == "show_menu"

    @pytest.mark.asyncio
    async def test_show_main_menu(self, chatbot_instance):
        """Test main menu."""
        response = await chatbot_instance._show_main_menu("Maria")
        assert "Menu Principal" in response.response_text
        assert "Buscar Produtos" in response.response_text
        assert response.action == "show_menu"

    @pytest.mark.asyncio
    async def test_handle_product_search(self, chatbot_instance):
        """Test product search initiation."""
        response = await chatbot_instance._handle_product_search(
            phone="5511999999999",
            name="João",
            user_state=None
        )
        assert "Busca de Produtos" in response.response_text
        assert "João" in response.response_text
        assert response.action == "await_product_query"
        # Verify state was saved
        chatbot_instance.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_products_with_results(self, chatbot_instance):
        """Test product search with matching results."""
        response = await chatbot_instance._search_products(
            phone="5511999999999",
            query="fone",
            name="João"
        )
        assert "Encontrei" in response.response_text
        assert response.products is not None
        assert len(response.products) > 0
        assert response.action == "show_products"
        # Verify state was cleared
        chatbot_instance.cache.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_products_no_exact_match(self, chatbot_instance):
        """Test product search with no exact match."""
        response = await chatbot_instance._search_products(
            phone="5511999999999",
            query="xyz_nonexistent",
            name="João"
        )
        # Should return top products as fallback
        assert response.products is not None
        assert len(response.products) > 0

    @pytest.mark.asyncio
    async def test_handle_price_comparison(self, chatbot_instance):
        """Test price comparison."""
        response = await chatbot_instance._handle_price_comparison(
            phone="5511999999999",
            name="João"
        )
        assert "Comparação de Preços" in response.response_text
        assert "Menor preço" in response.response_text
        assert response.action == "show_comparison"

    @pytest.mark.asyncio
    async def test_handle_alerts(self, chatbot_instance):
        """Test price alerts handler."""
        response = await chatbot_instance._handle_alerts(
            phone="5511999999999",
            name="João"
        )
        assert "Alertas de Preço" in response.response_text
        assert "João" in response.response_text
        assert response.action == "show_alerts"

    @pytest.mark.asyncio
    async def test_handle_human_transfer(self, chatbot_instance):
        """Test human transfer handler."""
        response = await chatbot_instance._handle_human_transfer(
            phone="5511999999999",
            name="João"
        )
        assert "Transferência para Atendente" in response.response_text
        assert "João" in response.response_text
        assert response.action == "transfer_human"
        assert response.metadata is not None
        assert response.metadata["priority"] == "normal"

    @pytest.mark.asyncio
    async def test_process_message_menu_option_1(self, chatbot_instance):
        """Test processing menu option 1 (product search)."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="1",
            push_name="João"
        )
        assert "Busca de Produtos" in response.response_text

    @pytest.mark.asyncio
    async def test_process_message_menu_option_2(self, chatbot_instance):
        """Test processing menu option 2 (price comparison)."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="2",
            push_name="João"
        )
        assert "Comparação de Preços" in response.response_text

    @pytest.mark.asyncio
    async def test_process_message_menu_option_3(self, chatbot_instance):
        """Test processing menu option 3 (alerts)."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="3",
            push_name="João"
        )
        assert "Alertas de Preço" in response.response_text

    @pytest.mark.asyncio
    async def test_process_message_menu_option_4(self, chatbot_instance):
        """Test processing menu option 4 (human transfer)."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="4",
            push_name="João"
        )
        assert "Atendente" in response.response_text

    @pytest.mark.asyncio
    async def test_process_message_back_to_menu(self, chatbot_instance):
        """Test returning to menu."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="0",
            push_name="João"
        )
        assert "Menu Principal" in response.response_text

    @pytest.mark.asyncio
    async def test_process_message_keyword_produto(self, chatbot_instance):
        """Test keyword 'produto' triggers search."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="quero produto",
            push_name="João"
        )
        assert "Busca de Produtos" in response.response_text

    @pytest.mark.asyncio
    async def test_process_message_keyword_comparar(self, chatbot_instance):
        """Test keyword 'comparar' triggers comparison."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="quero comparar",
            push_name="João"
        )
        assert "Comparação de Preços" in response.response_text

    @pytest.mark.asyncio
    async def test_process_message_keyword_alerta(self, chatbot_instance):
        """Test keyword 'alerta' triggers alerts."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="criar alerta",
            push_name="João"
        )
        assert "Alertas de Preço" in response.response_text

    @pytest.mark.asyncio
    async def test_process_message_keyword_atendente(self, chatbot_instance):
        """Test keyword 'atendente' triggers transfer."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="falar com atendente",
            push_name="João"
        )
        assert "Atendente" in response.response_text

    @pytest.mark.asyncio
    async def test_process_message_with_state(self, chatbot_instance):
        """Test processing message with waiting state."""
        chatbot_instance.cache.get = AsyncMock(return_value={
            "waiting_for": "product_query",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="smartwatch",
            push_name="João"
        )
        # Should process as product search
        assert response.response_text is not None

    @pytest.mark.asyncio
    async def test_process_message_default_welcome(self, chatbot_instance):
        """Test default response shows welcome."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="olá",
            push_name="João"
        )
        assert "Bem-vindo" in response.response_text
        assert "Didin Fácil" in response.response_text

    @pytest.mark.asyncio
    async def test_process_message_no_push_name(self, chatbot_instance):
        """Test processing without push_name uses 'cliente'."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="olá",
            push_name=None
        )
        assert "cliente" in response.response_text

    @pytest.mark.asyncio
    async def test_process_message_case_insensitive(self, chatbot_instance):
        """Test message processing is case insensitive."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="MENU",
            push_name="João"
        )
        assert "Menu Principal" in response.response_text


# ============================================
# INTEGRATION TESTS - Process Endpoint
# ============================================

class TestProcessEndpoint:
    """Tests for /process endpoint."""

    @pytest.mark.asyncio
    async def test_process_message_success(self, client):
        """Test processing message successfully."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="Hello!",
                action="welcome"
            )
            
            response = await client.post("/whatsapp-bot/process", json={
                "phone": "5511999999999",
                "message": "olá"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["response_text"] == "Hello!"
            assert data["action"] == "welcome"

    @pytest.mark.asyncio
    async def test_process_message_with_push_name(self, client):
        """Test processing message with push_name."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="Hello João!",
                action="welcome"
            )
            
            response = await client.post("/whatsapp-bot/process", json={
                "phone": "5511999999999",
                "message": "olá",
                "push_name": "João"
            })
            
            assert response.status_code == 200
            mock_process.assert_called_once_with(
                phone="5511999999999",
                message="olá",
                push_name="João"
            )

    @pytest.mark.asyncio
    async def test_process_message_with_products(self, client):
        """Test processing message that returns products."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="Products found!",
                products=[
                    ProductSearchResult(id="1", title="Test", price=10.0)
                ],
                action="show_products"
            )
            
            response = await client.post("/whatsapp-bot/process", json={
                "phone": "5511999999999",
                "message": "buscar fone"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["products"] is not None
            assert len(data["products"]) == 1

    @pytest.mark.asyncio
    async def test_process_message_error(self, client):
        """Test processing message error handling."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.side_effect = Exception("Internal error")
            
            response = await client.post("/whatsapp-bot/process", json={
                "phone": "5511999999999",
                "message": "olá"
            })
            
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_process_message_validation_error(self, client):
        """Test processing with invalid request."""
        response = await client.post("/whatsapp-bot/process", json={
            "message": "olá"  # Missing phone
        })
        
        assert response.status_code == 422


# ============================================
# INTEGRATION TESTS - n8n Webhook Endpoint
# ============================================

class TestN8NWebhookEndpoint:
    """Tests for /webhook/n8n endpoint."""

    @pytest.mark.asyncio
    async def test_n8n_webhook_success(self, client):
        """Test n8n webhook successfully."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="Hello!",
                action="welcome"
            )
            
            response = await client.post(
                "/whatsapp-bot/webhook/n8n",
                json={
                    "phone": "5511999999999",
                    "message": "olá",
                    "pushName": "João"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["response_text"] == "Hello!"

    @pytest.mark.asyncio
    async def test_n8n_webhook_alt_fields(self, client):
        """Test n8n webhook with alternative field names."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="Hello!",
                action="welcome"
            )
            
            response = await client.post(
                "/whatsapp-bot/webhook/n8n",
                json={
                    "from": "5511999999999",
                    "text": "olá",
                    "senderName": "João"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_n8n_webhook_with_jid(self, client):
        """Test n8n webhook with remoteJid field."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="Hello!",
                action="welcome"
            )
            
            response = await client.post(
                "/whatsapp-bot/webhook/n8n",
                json={
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "body": "olá",
                    "name": "João"
                }
            )
            
            assert response.status_code == 200
            mock_process.assert_called()

    @pytest.mark.asyncio
    async def test_n8n_webhook_missing_phone(self, client):
        """Test n8n webhook with missing phone."""
        response = await client.post(
            "/whatsapp-bot/webhook/n8n",
            json={"message": "olá"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Missing phone or message" in data["error"]

    @pytest.mark.asyncio
    async def test_n8n_webhook_missing_message(self, client):
        """Test n8n webhook with missing message."""
        response = await client.post(
            "/whatsapp-bot/webhook/n8n",
            json={"phone": "5511999999999"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_n8n_webhook_with_products(self, client):
        """Test n8n webhook returns products."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="Products found!",
                products=[
                    ProductSearchResult(id="1", title="Test", price=10.0)
                ],
                action="show_products"
            )
            
            response = await client.post(
                "/whatsapp-bot/webhook/n8n",
                json={
                    "phone": "5511999999999",
                    "message": "buscar fone"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["products"] is not None
            assert len(data["products"]) == 1
            assert data["products"][0]["title"] == "Test"

    @pytest.mark.asyncio
    async def test_n8n_webhook_error(self, client):
        """Test n8n webhook error handling."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.side_effect = Exception("Internal error")
            
            response = await client.post(
                "/whatsapp-bot/webhook/n8n",
                json={
                    "phone": "5511999999999",
                    "message": "olá"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Internal error" in data["error"]
            assert "Desculpe" in data["response_text"]


# ============================================
# INTEGRATION TESTS - Health Endpoint
# ============================================

class TestHealthEndpoint:
    """Tests for /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/whatsapp-bot/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "whatsapp-chatbot"
        assert "timestamp" in data


# ============================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================

class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_empty_message(self, chatbot_instance):
        """Test processing empty message."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="   ",
            push_name="João"
        )
        # Should show welcome for empty/whitespace message
        assert response.response_text is not None

    @pytest.mark.asyncio
    async def test_very_long_message(self, chatbot_instance):
        """Test processing very long message."""
        long_message = "a" * 1000
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message=long_message,
            push_name="João"
        )
        assert response.response_text is not None

    @pytest.mark.asyncio
    async def test_special_characters(self, chatbot_instance):
        """Test processing message with special characters."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="🔥 emojis 💪 test!",
            push_name="João"
        )
        assert response.response_text is not None

    @pytest.mark.asyncio
    async def test_unicode_push_name(self, chatbot_instance):
        """Test processing with unicode push_name."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="olá",
            push_name="José 日本語"
        )
        assert "José" in response.response_text

    @pytest.mark.asyncio
    async def test_mock_products_structure(self):
        """Test mock products have correct structure."""
        bot = WhatsAppChatbot()
        assert len(bot.mock_products) > 0
        
        for product in bot.mock_products:
            assert "id" in product
            assert "title" in product
            assert "price" in product
            assert product["price"] > 0

    @pytest.mark.asyncio
    async def test_search_smartwatch(self, chatbot_instance):
        """Test searching for smartwatch in mock products."""
        response = await chatbot_instance._search_products(
            phone="5511999999999",
            query="smartwatch",
            name="João"
        )
        # Should find the smartwatch product
        assert response.products is not None

    @pytest.mark.asyncio
    async def test_search_carregador(self, chatbot_instance):
        """Test searching for carregador in mock products."""
        response = await chatbot_instance._search_products(
            phone="5511999999999",
            query="carregador",
            name="João"
        )
        assert response.products is not None
