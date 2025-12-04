"""
Extended Tests for WhatsApp Chatbot Routes - Coverage Boost
============================================================
Tests for uncovered lines: verify_webhook_secret, n8n_webhook, process routes.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.whatsapp_chatbot import (ChatbotRequest, ChatbotResponse,
                                         ProductSearchResult, WhatsAppChatbot,
                                         chatbot, router,
                                         verify_webhook_secret)
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from shared.config import settings

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def app():
    """Create test FastAPI app with mocked auth."""
    app = FastAPI()
    
    # Override authentication dependency
    async def mock_verify():
        return True
    
    app.dependency_overrides[verify_webhook_secret] = mock_verify
    app.include_router(router)
    return app


@pytest.fixture
async def client(app):
    """Async test client with mocked auth."""
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
# VERIFY_WEBHOOK_SECRET TESTS (Lines 43-67)
# ============================================

class TestVerifyWebhookSecret:
    """Tests for webhook authentication function."""

    @pytest.mark.asyncio
    async def test_verify_with_x_webhook_secret_header_valid(self):
        """Test valid X-Webhook-Secret header."""
        with patch.object(settings, 'WEBHOOK_SECRET', 'test-secret-123'):
            with patch.object(settings, 'N8N_WEBHOOK_SECRET', None):
                result = await verify_webhook_secret(
                    x_webhook_secret="test-secret-123",
                    authorization=None
                )
                assert result is True

    @pytest.mark.asyncio
    async def test_verify_with_authorization_bearer_valid(self):
        """Test valid Authorization Bearer header."""
        with patch.object(settings, 'WEBHOOK_SECRET', 'test-secret-123'):
            result = await verify_webhook_secret(
                x_webhook_secret=None,
                authorization="Bearer test-secret-123"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_with_n8n_webhook_secret(self):
        """Test using N8N_WEBHOOK_SECRET as fallback."""
        with patch.object(settings, 'WEBHOOK_SECRET', None):
            with patch.object(settings, 'N8N_WEBHOOK_SECRET', 'n8n-secret-456'):
                result = await verify_webhook_secret(
                    x_webhook_secret="n8n-secret-456",
                    authorization=None
                )
                assert result is True

    @pytest.mark.asyncio
    async def test_verify_no_secret_dev_mode(self):
        """Test no secret configured in dev mode - should accept."""
        with patch.object(settings, 'WEBHOOK_SECRET', None):
            with patch.object(settings, 'N8N_WEBHOOK_SECRET', None):
                with patch.object(settings, 'ENVIRONMENT', 'development'):
                    result = await verify_webhook_secret(
                        x_webhook_secret=None,
                        authorization=None
                    )
                    assert result is True

    @pytest.mark.asyncio
    async def test_verify_no_secret_prod_mode_fails(self):
        """Test no secret configured in production - should fail."""
        with patch.object(settings, 'WEBHOOK_SECRET', None):
            with patch.object(settings, 'N8N_WEBHOOK_SECRET', None):
                with patch.object(settings, 'ENVIRONMENT', 'production'):
                    with pytest.raises(HTTPException) as exc_info:
                        await verify_webhook_secret(
                            x_webhook_secret=None,
                            authorization=None
                        )
                    assert exc_info.value.status_code == 401
                    assert "authentication required" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_verify_invalid_secret(self):
        """Test invalid secret - should fail."""
        with patch.object(settings, 'WEBHOOK_SECRET', 'correct-secret'):
            with pytest.raises(HTTPException) as exc_info:
                await verify_webhook_secret(
                    x_webhook_secret="wrong-secret",
                    authorization=None
                )
            assert exc_info.value.status_code == 401
            assert "Invalid webhook authentication" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_invalid_bearer(self):
        """Test invalid bearer token - should fail."""
        with patch.object(settings, 'WEBHOOK_SECRET', 'correct-secret'):
            with pytest.raises(HTTPException) as exc_info:
                await verify_webhook_secret(
                    x_webhook_secret=None,
                    authorization="Bearer wrong-secret"
                )
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_malformed_authorization(self):
        """Test malformed Authorization header (no Bearer)."""
        with patch.object(settings, 'WEBHOOK_SECRET', 'correct-secret'):
            with pytest.raises(HTTPException) as exc_info:
                await verify_webhook_secret(
                    x_webhook_secret=None,
                    authorization="Basic some-value"  # Not Bearer
                )
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_both_headers_x_webhook_wins(self):
        """Test both headers provided - X-Webhook-Secret is checked first."""
        with patch.object(settings, 'WEBHOOK_SECRET', 'test-secret'):
            # Valid X-Webhook-Secret should pass even with invalid Bearer
            result = await verify_webhook_secret(
                x_webhook_secret="test-secret",
                authorization="Bearer wrong-secret"
            )
            assert result is True


# ============================================
# PROCESS ENDPOINT TESTS (Lines 454-463)
# ============================================

class TestProcessEndpointComplete:
    """Complete tests for /process endpoint."""

    @pytest.mark.asyncio
    async def test_process_success_with_all_fields(self, client):
        """Test successful processing with all fields."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="Welcome João!",
                products=None,
                action="welcome",
                metadata={"key": "value"}
            )
            
            response = await client.post("/whatsapp-bot/process", json={
                "phone": "5511999999999",
                "message": "hello",
                "instance_name": "my-instance",
                "push_name": "João"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["response_text"] == "Welcome João!"
            assert data["action"] == "welcome"

    @pytest.mark.asyncio
    async def test_process_with_products_response(self, client):
        """Test processing that returns products."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="Found products!",
                products=[
                    ProductSearchResult(id="1", title="Product 1", price=10.99),
                    ProductSearchResult(id="2", title="Product 2", price=20.99)
                ],
                action="show_products"
            )
            
            response = await client.post("/whatsapp-bot/process", json={
                "phone": "5511999999999",
                "message": "buscar fone"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["products"]) == 2

    @pytest.mark.asyncio
    async def test_process_exception_handling(self, client):
        """Test exception handling in process endpoint."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.side_effect = ValueError("Processing failed")
            
            response = await client.post("/whatsapp-bot/process", json={
                "phone": "5511999999999",
                "message": "test"
            })
            
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_process_minimal_request(self, client):
        """Test processing with minimal required fields."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="Hello cliente!"
            )
            
            response = await client.post("/whatsapp-bot/process", json={
                "phone": "5511999999999",
                "message": "oi"
            })
            
            assert response.status_code == 200


# ============================================
# N8N WEBHOOK ENDPOINT TESTS (Lines 477-529)
# ============================================

class TestN8NWebhookComplete:
    """Complete tests for /webhook/n8n endpoint."""

    @pytest.mark.asyncio
    async def test_n8n_webhook_standard_payload(self, client):
        """Test n8n webhook with standard payload."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="OK",
                action="received"
            )
            
            response = await client.post("/whatsapp-bot/webhook/n8n", json={
                "phone": "5511999999999",
                "message": "hello",
                "pushName": "Test User"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["action"] == "received"

    @pytest.mark.asyncio
    async def test_n8n_webhook_alternative_from_field(self, client):
        """Test n8n webhook with 'from' field for phone."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(response_text="OK")
            
            response = await client.post("/whatsapp-bot/webhook/n8n", json={
                "from": "5511888888888",
                "text": "testing",
                "senderName": "Sender"
            })
            
            assert response.status_code == 200
            mock_process.assert_called_once()
            call_args = mock_process.call_args
            assert call_args[1]["phone"] == "5511888888888"
            assert call_args[1]["message"] == "testing"

    @pytest.mark.asyncio
    async def test_n8n_webhook_remote_jid_format(self, client):
        """Test n8n webhook with WhatsApp remoteJid format."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(response_text="OK")
            
            response = await client.post("/whatsapp-bot/webhook/n8n", json={
                "remoteJid": "5511777777777@s.whatsapp.net",
                "body": "test message",
                "name": "JID User"
            })
            
            assert response.status_code == 200
            # Phone should have @ part stripped
            call_args = mock_process.call_args
            assert call_args[1]["phone"] == "5511777777777"

    @pytest.mark.asyncio
    async def test_n8n_webhook_missing_phone_returns_error(self, client):
        """Test n8n webhook with missing phone returns error object."""
        response = await client.post("/whatsapp-bot/webhook/n8n", json={
            "message": "test"
        })
        
        assert response.status_code == 200  # Still 200, but error in body
        data = response.json()
        assert data["success"] is False
        assert "Missing phone or message" in data["error"]

    @pytest.mark.asyncio
    async def test_n8n_webhook_missing_message_returns_error(self, client):
        """Test n8n webhook with missing message returns error object."""
        response = await client.post("/whatsapp-bot/webhook/n8n", json={
            "phone": "5511999999999"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_n8n_webhook_with_products_serialization(self, client):
        """Test n8n webhook correctly serializes products."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="Found!",
                products=[
                    ProductSearchResult(
                        id="prod1",
                        title="Fone Bluetooth",
                        price=49.90,
                        original_price=99.90,
                        discount_percent=50,
                        image_url="https://example.com/fone.jpg",
                        shop_name="TechStore",
                        rating=4.5,
                        sales_count=1000
                    )
                ],
                action="show_products",
                metadata={"query": "fone"}
            )
            
            response = await client.post("/whatsapp-bot/webhook/n8n", json={
                "phone": "5511999999999",
                "message": "buscar fone"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["products"] is not None
            assert len(data["products"]) == 1
            product = data["products"][0]
            assert product["id"] == "prod1"
            assert product["price"] == 49.90
            assert product["discount_percent"] == 50

    @pytest.mark.asyncio
    async def test_n8n_webhook_exception_returns_friendly_error(self, client):
        """Test n8n webhook exception returns friendly error message."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.side_effect = Exception("Database error")
            
            response = await client.post("/whatsapp-bot/webhook/n8n", json={
                "phone": "5511999999999",
                "message": "test"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Database error" in data["error"]
            assert "Desculpe" in data["response_text"]

    @pytest.mark.asyncio
    async def test_n8n_webhook_empty_phone_string(self, client):
        """Test n8n webhook with empty phone string."""
        response = await client.post("/whatsapp-bot/webhook/n8n", json={
            "phone": "",
            "message": "test"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_n8n_webhook_whitespace_message(self, client):
        """Test n8n webhook with whitespace-only message."""
        response = await client.post("/whatsapp-bot/webhook/n8n", json={
            "phone": "5511999999999",
            "message": "   "
        })
        
        # Empty/whitespace message should still be processed
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_n8n_webhook_no_products(self, client):
        """Test n8n webhook response without products."""
        with patch.object(chatbot, "process_message") as mock_process:
            mock_process.return_value = ChatbotResponse(
                response_text="Menu shown",
                products=None,  # No products
                action="show_menu"
            )
            
            response = await client.post("/whatsapp-bot/webhook/n8n", json={
                "phone": "5511999999999",
                "message": "menu"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["products"] is None


# ============================================
# CHATBOT CLASS EXTENDED TESTS
# ============================================

class TestChatbotClassExtended:
    """Extended tests for WhatsAppChatbot class methods."""

    @pytest.mark.asyncio
    async def test_search_products_formats_output_correctly(self, chatbot_instance):
        """Test _search_products formats response correctly."""
        response = await chatbot_instance._search_products(
            phone="5511999999999",
            query="fone",
            name="João"
        )
        
        # Should contain product count
        assert "Encontrei" in response.response_text
        # Should have formatted product list
        assert "R$" in response.response_text
        # Should have navigation instructions
        assert "0" in response.response_text

    @pytest.mark.asyncio
    async def test_search_products_no_results_fallback(self, chatbot_instance):
        """Test _search_products fallback when no match."""
        response = await chatbot_instance._search_products(
            phone="5511999999999",
            query="xyznonexistent123",
            name="João"
        )
        
        # Should return top products as fallback
        assert response.products is not None
        assert len(response.products) >= 1

    @pytest.mark.asyncio
    async def test_handle_product_search_saves_state(self, chatbot_instance):
        """Test _handle_product_search correctly saves user state."""
        response = await chatbot_instance._handle_product_search(
            phone="5511999999999",
            name="Maria",
            user_state=None
        )
        
        # Verify cache.set was called with correct key
        chatbot_instance.cache.set.assert_called_once()
        call_args = chatbot_instance.cache.set.call_args
        assert "chatbot:state:5511999999999" in str(call_args)
        assert response.action == "await_product_query"

    @pytest.mark.asyncio
    async def test_search_products_clears_state(self, chatbot_instance):
        """Test _search_products clears user state after search."""
        await chatbot_instance._search_products(
            phone="5511999999999",
            query="fone",
            name="João"
        )
        
        # Verify cache.delete was called
        chatbot_instance.cache.delete.assert_called_once_with("chatbot:state:5511999999999")

    @pytest.mark.asyncio
    async def test_process_message_with_product_state(self, chatbot_instance):
        """Test process_message when user is in product query state."""
        # Setup state
        chatbot_instance.cache.get = AsyncMock(return_value={
            "waiting_for": "product_query",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="carregador portátil",
            push_name="João"
        )
        
        # Should process as product search
        assert response is not None
        # Should have searched for the product
        assert response.action == "show_products"

    @pytest.mark.asyncio
    async def test_price_comparison_shows_product_info(self, chatbot_instance):
        """Test _handle_price_comparison shows product details."""
        response = await chatbot_instance._handle_price_comparison(
            phone="5511999999999",
            name="João"
        )
        
        # Should show comparison info
        assert "Comparação de Preços" in response.response_text
        assert "Menor preço" in response.response_text
        assert "Economia" in response.response_text

    @pytest.mark.asyncio
    async def test_handle_alerts_shows_info(self, chatbot_instance):
        """Test _handle_alerts shows alert info."""
        response = await chatbot_instance._handle_alerts(
            phone="5511999999999",
            name="Maria"
        )
        
        assert "Alertas de Preço" in response.response_text
        assert "Maria" in response.response_text
        assert response.action == "show_alerts"

    @pytest.mark.asyncio
    async def test_handle_human_transfer_includes_metadata(self, chatbot_instance):
        """Test _handle_human_transfer includes proper metadata."""
        response = await chatbot_instance._handle_human_transfer(
            phone="5511999999999",
            name="Pedro"
        )
        
        assert response.action == "transfer_human"
        assert response.metadata is not None
        assert "priority" in response.metadata
        assert "department" in response.metadata

    @pytest.mark.asyncio
    async def test_process_keyword_buscar(self, chatbot_instance):
        """Test 'buscar' keyword triggers product search."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="buscar celular",
            push_name="Ana"
        )
        
        assert "Busca de Produtos" in response.response_text

    @pytest.mark.asyncio
    async def test_process_keyword_preco(self, chatbot_instance):
        """Test 'preço' keyword triggers comparison."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="ver preço",
            push_name="Ana"
        )
        
        assert "Comparação de Preços" in response.response_text

    @pytest.mark.asyncio
    async def test_process_keyword_humano(self, chatbot_instance):
        """Test 'humano' keyword triggers transfer."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="quero humano",
            push_name="Ana"
        )
        
        assert "Atendente" in response.response_text

    @pytest.mark.asyncio
    async def test_process_keyword_voltar(self, chatbot_instance):
        """Test 'voltar' keyword shows menu."""
        response = await chatbot_instance.process_message(
            phone="5511999999999",
            message="voltar",
            push_name="Ana"
        )
        
        assert "Menu Principal" in response.response_text


# ============================================
# HEALTH ENDPOINT TEST
# ============================================

class TestHealthEndpointComplete:
    """Complete tests for health endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_all_fields(self, client):
        """Test health endpoint returns all required fields."""
        response = await client.get("/whatsapp-bot/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
        assert data["service"] == "whatsapp-chatbot"


# ============================================
# MODEL VALIDATION TESTS
# ============================================

class TestModelValidation:
    """Tests for Pydantic model validation."""

    def test_chatbot_request_validates_phone(self):
        """Test ChatbotRequest requires phone."""
        with pytest.raises(ValueError):
            ChatbotRequest(message="test")  # Missing phone

    def test_chatbot_request_validates_message(self):
        """Test ChatbotRequest requires message."""
        with pytest.raises(ValueError):
            ChatbotRequest(phone="5511999999999")  # Missing message

    def test_product_search_result_requires_id(self):
        """Test ProductSearchResult requires id."""
        with pytest.raises(ValueError):
            ProductSearchResult(title="Test", price=10.0)  # Missing id

    def test_product_search_result_requires_title(self):
        """Test ProductSearchResult requires title."""
        with pytest.raises(ValueError):
            ProductSearchResult(id="1", price=10.0)  # Missing title

    def test_product_search_result_requires_price(self):
        """Test ProductSearchResult requires price."""
        with pytest.raises(ValueError):
            ProductSearchResult(id="1", title="Test")  # Missing price

    def test_chatbot_response_requires_response_text(self):
        """Test ChatbotResponse requires response_text."""
        with pytest.raises(ValueError):
            ChatbotResponse()  # Missing response_text

    def test_product_search_result_optional_fields(self):
        """Test ProductSearchResult optional fields default correctly."""
        product = ProductSearchResult(id="1", title="Test", price=10.0)
        
        assert product.original_price is None
        assert product.discount_percent is None
        assert product.image_url is None
        assert product.shop_name is None
        assert product.rating is None
        assert product.sales_count == 0
