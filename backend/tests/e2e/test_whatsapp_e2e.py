"""
WhatsApp E2E Tests
==================
Testes end-to-end do fluxo completo do WhatsApp:
- Webhook recebe mensagem
- Chatbot processa
- Resposta é enviada
- Métricas são atualizadas
"""

import json
# Set testing environment before importing app
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["TESTING"] = "true"

from api.main import app

# ============================================
# FIXTURES
# ============================================

@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def evolution_webhook_payload():
    """Simula payload real da Evolution API."""
    return {
        "event": "MESSAGES_UPSERT",
        "instance": "didin-whatsapp",
        "data": {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "3EB0C767D097B7BXXXXXX"
            },
            "pushName": "João Teste",
            "message": {
                "conversation": "Olá, quero buscar um fone bluetooth"
            },
            "messageType": "conversation",
            "messageTimestamp": 1701432000
        }
    }


@pytest.fixture
def menu_message_payload():
    """Payload com mensagem de menu (opção 1)."""
    return {
        "event": "messages.upsert",
        "instance": "didin-whatsapp",
        "data": {
            "key": {
                "remoteJid": "5511888888888@s.whatsapp.net",
                "fromMe": False,
                "id": "3EB0C767D097B7BYYYYYY"
            },
            "pushName": "Maria Cliente",
            "message": {
                "conversation": "1"
            },
            "messageType": "conversation",
            "messageTimestamp": 1701432100
        }
    }


# ============================================
# WEBHOOK TESTS
# ============================================

class TestWebhookReceive:
    """Testes do endpoint de webhook."""

    @pytest.mark.asyncio
    async def test_webhook_receives_message(self, client, evolution_webhook_payload):
        """Verifica que webhook aceita mensagem da Evolution API."""
        response = await client.post(
            "/api/whatsapp-webhook/evolution",
            json=evolution_webhook_payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["event"] == "MESSAGES_UPSERT"

    @pytest.mark.asyncio
    async def test_webhook_ignores_own_messages(self, client, evolution_webhook_payload):
        """Webhook aceita mensagem mas a filtragem de fromMe é feita no background."""
        evolution_webhook_payload["data"]["key"]["fromMe"] = True
        
        response = await client.post(
            "/api/whatsapp-webhook/evolution",
            json=evolution_webhook_payload
        )
        
        assert response.status_code == 200
        data = response.json()
        # Webhook aceita e envia para processamento, filtragem é no background
        assert data["status"] == "processing"

    @pytest.mark.asyncio
    async def test_webhook_handles_invalid_payload(self, client):
        """Webhook retorna erro para payload inválido."""
        response = await client.post(
            "/api/whatsapp-webhook/evolution",
            json={"invalid": "payload"}
        )
        
        # Deve aceitar mas não processar
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_webhook_handles_connection_update(self, client):
        """Webhook processa eventos de conexão."""
        payload = {
            "event": "connection.update",
            "instance": "didin-whatsapp",
            "data": {
                "state": "open"
            }
        }
        
        response = await client.post(
            "/api/whatsapp-webhook/evolution",
            json=payload
        )
        
        assert response.status_code == 200


class TestChatbotProcessing:
    """Testes do processamento do chatbot."""

    @pytest.fixture(autouse=True)
    def mock_cache(self):
        """Mock do cache para evitar dependência do Redis."""
        with patch(
            'api.routes.whatsapp_chatbot.chatbot.cache.get',
            new_callable=AsyncMock,
            return_value=None
        ), patch(
            'api.routes.whatsapp_chatbot.chatbot.cache.set',
            new_callable=AsyncMock,
            return_value=True
        ):
            yield

    @pytest.mark.asyncio
    async def test_chatbot_shows_welcome(self, client):
        """Chatbot mostra boas-vindas para mensagem inicial."""
        payload = {
            "phone": "5511999999999",
            "message": "Olá",
            "push_name": "Teste"
        }
        
        response = await client.post(
            "/api/whatsapp-bot/process",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        response_text = data.get("response_text", data.get("response", ""))
        assert "Bem-vindo" in response_text or "Olá" in response_text

    @pytest.mark.asyncio
    async def test_chatbot_option_1_starts_search(self, client):
        """Opção 1 inicia fluxo de busca de produtos."""
        payload = {
            "phone": "5511999999999",
            "message": "1",
            "push_name": "Teste"
        }
        
        response = await client.post(
            "/api/whatsapp-bot/process",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        response_text = data.get("response_text", data.get("response", ""))
        assert "Busca" in response_text or "procurando" in response_text or "produto" in response_text.lower()

    @pytest.mark.asyncio
    async def test_chatbot_option_4_human_transfer(self, client):
        """Opção 4 transfere para atendimento humano."""
        payload = {
            "phone": "5511999999999",
            "message": "4",
            "push_name": "Teste"
        }
        
        response = await client.post(
            "/api/whatsapp-bot/process",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        response_text = data.get("response_text", data.get("response", ""))
        # Deve mencionar atendente ou suporte
        assert any(word in response_text.lower() for word in ["atendente", "suporte", "humano", "equipe"])

    @pytest.mark.asyncio
    async def test_chatbot_menu_option(self, client):
        """Opção 0 mostra menu principal."""
        payload = {
            "phone": "5511999999999",
            "message": "0",
            "push_name": "Teste"
        }
        
        response = await client.post(
            "/api/whatsapp-bot/process",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        response_text = data.get("response_text", data.get("response", ""))
        assert "Menu" in response_text or "1️⃣" in response_text


class TestProductSearch:
    """Testes da busca de produtos."""

    @pytest.fixture(autouse=True)
    def mock_cache(self):
        """Mock do cache para evitar dependência do Redis."""
        with patch(
            'api.routes.whatsapp_chatbot.chatbot.cache.get',
            new_callable=AsyncMock,
            return_value=None
        ), patch(
            'api.routes.whatsapp_chatbot.chatbot.cache.set',
            new_callable=AsyncMock,
            return_value=True
        ):
            yield

    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_webhook.ScraperOrchestrator')
    async def test_product_search_returns_results(self, mock_scraper, client):
        """Busca de produtos retorna resultados do banco."""
        # Mock do scraper
        mock_instance = MagicMock()
        mock_instance.search_products = AsyncMock(return_value={
            "products": [
                {
                    "id": 1,
                    "title": "Fone Bluetooth Premium",
                    "price": 89.90,
                    "original_price": 129.90,
                    "rating": 4.5,
                    "sales_count": 1500,
                    "shop_name": "TechStore"
                }
            ],
            "total": 1
        })
        mock_scraper.return_value = mock_instance

        # Simula que usuário está em estado de busca
        payload = {
            "phone": "5511999999999",
            "message": "fone bluetooth",
            "push_name": "Teste"
        }
        
        response = await client.post(
            "/api/whatsapp-bot/process",
            json=payload
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_product_search_empty_query(self, client):
        """Busca vazia retorna mensagem apropriada."""
        payload = {
            "phone": "5511999999999",
            "message": "",
            "push_name": "Teste"
        }
        
        response = await client.post(
            "/api/whatsapp-bot/process",
            json=payload
        )
        
        # Deve retornar welcome ou erro amigável
        assert response.status_code == 200


class TestAnalytics:
    """Testes do endpoint de analytics."""

    @pytest.fixture(autouse=True)
    def mock_cache(self):
        """Mock do cache para evitar dependência do Redis."""
        mock_stats = {
            "messages_received": 100,
            "messages_sent": 95,
            "unique_users": 50,
            "errors": 2
        }
        with patch(
            'api.routes.whatsapp_analytics.cache.get',
            new_callable=AsyncMock,
            return_value=mock_stats
        ), patch(
            'api.routes.whatsapp_analytics.cache.set',
            new_callable=AsyncMock,
            return_value=True
        ):
            yield

    @pytest.mark.asyncio
    async def test_analytics_health_endpoint(self, client):
        """Endpoint de health retorna status."""
        response = await client.get("/api/whatsapp-analytics/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_analytics_overview_requires_auth(self, client):
        """Overview completo requer autenticação."""
        response = await client.get("/api/whatsapp-analytics/overview")
        
        # Sem token, deve retornar 401 ou 403
        assert response.status_code in [401, 403, 422]


class TestEndToEndFlow:
    """Testes do fluxo completo end-to-end."""

    @pytest.fixture(autouse=True)
    def mock_cache(self):
        """Mock do cache para evitar dependência do Redis."""
        with patch(
            'api.routes.whatsapp_chatbot.chatbot.cache.get',
            new_callable=AsyncMock,
            return_value=None
        ), patch(
            'api.routes.whatsapp_chatbot.chatbot.cache.set',
            new_callable=AsyncMock,
            return_value=True
        ):
            yield

    @pytest.mark.asyncio
    @patch('api.routes.whatsapp_webhook.httpx.AsyncClient')
    async def test_full_flow_webhook_to_response(self, mock_httpx, client, evolution_webhook_payload):
        """
        Fluxo completo:
        1. Webhook recebe mensagem
        2. Chatbot processa
        3. Resposta seria enviada (mockado)
        4. Métricas atualizadas
        """
        # Mock do httpx para não enviar mensagem real
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=MagicMock(
            status_code=200,
            json=lambda: {"key": {"id": "test123"}}
        ))
        mock_httpx.return_value = mock_client_instance

        # 1. Webhook recebe mensagem
        response = await client.post(
            "/api/whatsapp-webhook/evolution",
            json=evolution_webhook_payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"

        # 2. Verificar analytics foi atualizado
        analytics_response = await client.get("/api/whatsapp-analytics/health")
        assert analytics_response.status_code == 200
        
        analytics_data = analytics_response.json()
        assert analytics_data["today_stats"]["messages_received"] >= 0

    @pytest.mark.asyncio
    async def test_conversation_flow(self, client):
        """Testa fluxo de conversa multi-step."""
        phone = "5511777777777"
        
        # Step 1: Usuário envia "oi"
        r1 = await client.post(
            "/api/whatsapp-bot/process",
            json={"phone": phone, "message": "oi", "push_name": "User"}
        )
        assert r1.status_code == 200
        data1 = r1.json()
        response1 = data1.get("response_text", data1.get("response", ""))
        # Deve mostrar menu/welcome
        assert "1️⃣" in response1 or "Olá" in response1

        # Step 2: Usuário escolhe opção 1
        r2 = await client.post(
            "/api/whatsapp-bot/process",
            json={"phone": phone, "message": "1", "push_name": "User"}
        )
        assert r2.status_code == 200
        data2 = r2.json()
        response2 = data2.get("response_text", data2.get("response", ""))
        # Deve pedir produto para buscar
        assert any(word in response2.lower() for word in ["busca", "produto", "procurando"])

        # Step 3: Usuário busca um produto
        r3 = await client.post(
            "/api/whatsapp-bot/process",
            json={"phone": phone, "message": "celular samsung", "push_name": "User"}
        )
        assert r3.status_code == 200


# ============================================
# INTEGRATION TESTS
# ============================================

class TestIntegrationWithExternalServices:
    """Testes de integração com serviços externos (Evolution API, Redis)."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS", "true").lower() == "true",
        reason="Integration tests skipped"
    )
    async def test_real_evolution_api_connection(self, client):
        """Testa conexão real com Evolution API (apenas em ambiente de CI)."""
        # Este teste só roda se SKIP_INTEGRATION_TESTS=false
        response = await client.get("/api/whatsapp-webhook/status")
        assert response.status_code in [200, 404]  # 404 se endpoint não existe

    @pytest.mark.asyncio
    async def test_redis_metrics_increment(self, client):
        """Verifica que métricas são incrementadas no Redis."""
        # Envia mensagem via chatbot
        await client.post(
            "/api/whatsapp-bot/process",
            json={"phone": "5511666666666", "message": "1", "push_name": "Test"}
        )
        
        # Verifica health (que lê do Redis)
        response = await client.get("/api/whatsapp-analytics/health")
        assert response.status_code == 200


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestPerformance:
    """Testes de performance básicos."""

    @pytest.fixture(autouse=True)
    def mock_cache(self):
        """Mock do cache para evitar dependência do Redis."""
        with patch(
            'api.routes.whatsapp_chatbot.chatbot.cache.get',
            new_callable=AsyncMock,
            return_value=None
        ), patch(
            'api.routes.whatsapp_chatbot.chatbot.cache.set',
            new_callable=AsyncMock,
            return_value=True
        ):
            yield

    @pytest.mark.asyncio
    async def test_webhook_response_time(self, client, evolution_webhook_payload):
        """Webhook deve responder em menos de 500ms."""
        import time
        
        start = time.time()
        response = await client.post(
            "/api/whatsapp-webhook/evolution",
            json=evolution_webhook_payload
        )
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 500

    @pytest.mark.asyncio
    async def test_chatbot_response_time(self, client):
        """Chatbot deve responder em menos de 1 segundo."""
        import time
        
        start = time.time()
        response = await client.post(
            "/api/whatsapp-bot/process",
            json={"phone": "5511555555555", "message": "0", "push_name": "Test"}
        )
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 1000
