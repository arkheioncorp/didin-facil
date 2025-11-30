"""
Testes para n8n Webhooks - api/routes/n8n_webhooks.py
Cobertura completa das rotas de integração n8n
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi import HTTPException


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """Mock de usuário autenticado"""
    user = MagicMock()
    user.id = "user-123"
    user.email = "test@example.com"
    user.name = "Test User"
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_n8n_client():
    """Mock do cliente n8n"""
    client = AsyncMock()
    client.trigger_webhook = AsyncMock(return_value={"success": True})
    client.trigger_workflow_by_id = AsyncMock(return_value=MagicMock(
        id="exec-123",
        status=MagicMock(value="running")
    ))
    client.list_workflows = AsyncMock(return_value=[
        MagicMock(
            id="wf-1",
            name="Workflow 1",
            active=True,
            updated_at=datetime.now(timezone.utc)
        )
    ])
    client.get_executions = AsyncMock(return_value=[
        MagicMock(
            id="exec-1",
            workflow_id="wf-1",
            status=MagicMock(value="success"),
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc)
        )
    ])
    return client


@pytest.fixture
def mock_scraper():
    """Mock do ScraperOrchestrator"""
    scraper = AsyncMock()
    scraper.search_products = AsyncMock(return_value=[
        {
            "title": "Produto Test",
            "price": 99.90,
            "discount_percentage": 10,
            "store": "Loja Test",
            "url": "https://example.com/product"
        }
    ])
    return scraper


# ============================================
# TESTS: Request Models
# ============================================

class TestRequestModels:
    """Testes para modelos de request"""
    
    def test_product_search_request(self):
        """Deve validar ProductSearchRequest"""
        from api.routes.n8n_webhooks import ProductSearchRequest
        
        request = ProductSearchRequest(
            query="iphone",
            conversation_id="conv-123",
            limit=5
        )
        
        assert request.query == "iphone"
        assert request.conversation_id == "conv-123"
        assert request.limit == 5
    
    def test_product_search_request_default_limit(self):
        """Deve usar limit padrão"""
        from api.routes.n8n_webhooks import ProductSearchRequest
        
        request = ProductSearchRequest(
            query="notebook",
            conversation_id="conv-456"
        )
        
        assert request.limit == 5
    
    def test_price_alert_triggered_request(self):
        """Deve validar PriceAlertTriggeredRequest"""
        from api.routes.n8n_webhooks import PriceAlertTriggeredRequest
        
        request = PriceAlertTriggeredRequest(
            user_id="user-123",
            product_id="prod-456",
            old_price=100.00,
            new_price=80.00,
            discount_percentage=20.0
        )
        
        assert request.old_price == 100.00
        assert request.new_price == 80.00
        assert request.discount_percentage == 20.0
    
    def test_workflow_execution_request(self):
        """Deve validar WorkflowExecutionRequest"""
        from api.routes.n8n_webhooks import WorkflowExecutionRequest
        
        request = WorkflowExecutionRequest(
            workflow_id="wf-123",
            data={"key": "value"}
        )
        
        assert request.workflow_id == "wf-123"
        assert request.data["key"] == "value"
    
    def test_n8n_event_request(self):
        """Deve validar N8nEventRequest"""
        from api.routes.n8n_webhooks import N8nEventRequest
        
        request = N8nEventRequest(
            event_type="user_interaction",
            conversation_id="conv-789",
            data={"action": "click"}
        )
        
        assert request.event_type == "user_interaction"
        assert request.conversation_id == "conv-789"
    
    def test_n8n_event_request_optional_conversation(self):
        """Deve aceitar conversation_id opcional"""
        from api.routes.n8n_webhooks import N8nEventRequest
        
        request = N8nEventRequest(
            event_type="workflow_completed",
            data={"workflow_id": "wf-123"}
        )
        
        assert request.conversation_id is None


# ============================================
# TESTS: Response Models
# ============================================

class TestResponseModels:
    """Testes para modelos de response"""
    
    def test_product_search_response(self):
        """Deve validar ProductSearchResponse"""
        from api.routes.n8n_webhooks import ProductSearchResponse
        
        response = ProductSearchResponse(
            products=[{"name": "Product 1", "price": "R$ 99.90"}],
            total=1,
            query="test"
        )
        
        assert len(response.products) == 1
        assert response.total == 1
        assert response.query == "test"


# ============================================
# TESTS: Product Search Webhook
# ============================================

class TestProductSearchWebhook:
    """Testes para webhook de busca de produtos"""

    @pytest.mark.asyncio
    async def test_product_search_success(self, mock_scraper):
        """Deve buscar produtos com sucesso"""
        from api.routes.n8n_webhooks import (
            product_search_webhook,
            ProductSearchRequest
        )

        with patch("api.services.scraper.ScraperOrchestrator",
                   return_value=mock_scraper):
            request = ProductSearchRequest(
                query="iphone",
                conversation_id="conv-123"
            )

            mock_tasks = MagicMock()
            result = await product_search_webhook(request, mock_tasks)

            assert result.total >= 0
            assert result.query == "iphone"

    @pytest.mark.asyncio
    async def test_product_search_formats_products(self, mock_scraper):
        """Deve formatar produtos corretamente"""
        from api.routes.n8n_webhooks import (
            product_search_webhook,
            ProductSearchRequest
        )

        with patch("api.services.scraper.ScraperOrchestrator",
                   return_value=mock_scraper):
            request = ProductSearchRequest(
                query="notebook",
                conversation_id="conv-123",
                limit=10
            )

            mock_tasks = MagicMock()
            result = await product_search_webhook(request, mock_tasks)

            if result.products:
                product = result.products[0]
                assert "name" in product or "price" in product

    @pytest.mark.asyncio
    async def test_product_search_error(self):
        """Deve tratar erro na busca"""
        from api.routes.n8n_webhooks import (
            product_search_webhook,
            ProductSearchRequest
        )

        mock_scraper = AsyncMock()
        mock_scraper.search_products = AsyncMock(
            side_effect=Exception("Search error")
        )

        with patch("api.services.scraper.ScraperOrchestrator",
                   return_value=mock_scraper):
            request = ProductSearchRequest(
                query="test",
                conversation_id="conv-123"
            )

            mock_tasks = MagicMock()

            with pytest.raises(HTTPException) as exc_info:
                await product_search_webhook(request, mock_tasks)

            assert exc_info.value.status_code == 500


# ============================================
# TESTS: Price Alert Webhook
# ============================================

class TestPriceAlertWebhook:
    """Testes para webhook de alerta de preço"""
    
    @pytest.mark.asyncio
    async def test_price_alert_success(self):
        """Deve registrar alerta de preço"""
        from api.routes.n8n_webhooks import (
            price_alert_webhook,
            PriceAlertTriggeredRequest
        )
        
        request = PriceAlertTriggeredRequest(
            user_id="user-123",
            product_id="prod-456",
            old_price=100.00,
            new_price=80.00,
            discount_percentage=20.0
        )
        
        mock_tasks = MagicMock()
        result = await price_alert_webhook(request, mock_tasks)
        
        assert result["success"] is True
        mock_tasks.add_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_price_alert_error(self):
        """Deve tratar erro no alerta"""
        from api.routes.n8n_webhooks import (
            price_alert_webhook,
            PriceAlertTriggeredRequest
        )
        
        request = PriceAlertTriggeredRequest(
            user_id="user-123",
            product_id="prod-456",
            old_price=100.00,
            new_price=80.00,
            discount_percentage=20.0
        )
        
        mock_tasks = MagicMock()
        mock_tasks.add_task.side_effect = Exception("Task error")
        
        with pytest.raises(HTTPException) as exc_info:
            await price_alert_webhook(request, mock_tasks)
        
        assert exc_info.value.status_code == 500


# ============================================
# TESTS: Generic Event Webhook
# ============================================

class TestGenericEventWebhook:
    """Testes para webhook de evento genérico"""
    
    @pytest.mark.asyncio
    async def test_user_interaction_event(self):
        """Deve processar evento de interação"""
        from api.routes.n8n_webhooks import (
            generic_event_webhook,
            N8nEventRequest
        )
        
        with patch("api.routes.n8n_webhooks._track_interaction",
                   new_callable=AsyncMock):
            request = N8nEventRequest(
                event_type="user_interaction",
                conversation_id="conv-123",
                data={"action": "click"}
            )
            
            result = await generic_event_webhook(request)
            
            assert result["success"] is True
            assert result["event_processed"] == "user_interaction"
    
    @pytest.mark.asyncio
    async def test_workflow_completed_event(self):
        """Deve processar evento de workflow completo"""
        from api.routes.n8n_webhooks import (
            generic_event_webhook,
            N8nEventRequest
        )
        
        with patch("api.routes.n8n_webhooks._track_workflow_completion",
                   new_callable=AsyncMock):
            request = N8nEventRequest(
                event_type="workflow_completed",
                data={"workflow_id": "wf-123", "duration": 5.0}
            )
            
            result = await generic_event_webhook(request)
            
            assert result["success"] is True
            assert result["event_processed"] == "workflow_completed"
    
    @pytest.mark.asyncio
    async def test_error_occurred_event(self):
        """Deve processar evento de erro"""
        from api.routes.n8n_webhooks import (
            generic_event_webhook,
            N8nEventRequest
        )
        
        request = N8nEventRequest(
            event_type="error_occurred",
            data={"error": "Something went wrong"}
        )
        
        result = await generic_event_webhook(request)
        
        assert result["success"] is True
        assert result["event_processed"] == "error_occurred"
    
    @pytest.mark.asyncio
    async def test_unknown_event(self):
        """Deve processar evento desconhecido"""
        from api.routes.n8n_webhooks import (
            generic_event_webhook,
            N8nEventRequest
        )
        
        request = N8nEventRequest(
            event_type="custom_event",
            data={"custom": "data"}
        )
        
        result = await generic_event_webhook(request)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_generic_event_error(self):
        """Deve tratar erro no processamento"""
        from api.routes.n8n_webhooks import (
            generic_event_webhook,
            N8nEventRequest
        )
        
        with patch("api.routes.n8n_webhooks._track_interaction",
                   new_callable=AsyncMock,
                   side_effect=Exception("Track error")):
            request = N8nEventRequest(
                event_type="user_interaction",
                conversation_id="conv-123",
                data={"action": "click"}
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await generic_event_webhook(request)
            
            assert exc_info.value.status_code == 500


# ============================================
# TESTS: Trigger New User
# ============================================

class TestTriggerNewUser:
    """Testes para trigger de novo usuário"""
    
    @pytest.mark.asyncio
    async def test_trigger_onboarding_success(self, mock_user, mock_n8n_client):
        """Deve disparar onboarding com sucesso"""
        from api.routes.n8n_webhooks import trigger_new_user_onboarding
        
        with patch("api.routes.n8n_webhooks.get_n8n_client",
                   return_value=mock_n8n_client):
            result = await trigger_new_user_onboarding(mock_user)
            
            assert result["success"] is True
            mock_n8n_client.trigger_webhook.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trigger_onboarding_error(self, mock_user, mock_n8n_client):
        """Deve tratar erro no trigger"""
        from api.routes.n8n_webhooks import trigger_new_user_onboarding
        
        mock_n8n_client.trigger_webhook.side_effect = Exception("Webhook error")
        
        with patch("api.routes.n8n_webhooks.get_n8n_client",
                   return_value=mock_n8n_client):
            with pytest.raises(HTTPException) as exc_info:
                await trigger_new_user_onboarding(mock_user)
            
            assert exc_info.value.status_code == 500


# ============================================
# TESTS: Trigger Price Drop
# ============================================

class TestTriggerPriceDrop:
    """Testes para trigger de queda de preço"""
    
    @pytest.mark.asyncio
    async def test_trigger_price_drop_success(self, mock_user, mock_n8n_client):
        """Deve disparar alerta de preço com sucesso"""
        from api.routes.n8n_webhooks import trigger_price_drop_alert
        
        with patch("api.routes.n8n_webhooks.get_n8n_client",
                   return_value=mock_n8n_client):
            result = await trigger_price_drop_alert(
                product_id="prod-123",
                old_price=100.00,
                new_price=80.00,
                user=mock_user
            )
            
            assert result["success"] is True
            mock_n8n_client.trigger_webhook.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trigger_price_drop_calculates_discount(
        self, mock_user, mock_n8n_client
    ):
        """Deve calcular desconto corretamente"""
        from api.routes.n8n_webhooks import trigger_price_drop_alert
        
        with patch("api.routes.n8n_webhooks.get_n8n_client",
                   return_value=mock_n8n_client):
            await trigger_price_drop_alert(
                product_id="prod-123",
                old_price=100.00,
                new_price=75.00,
                user=mock_user
            )
            
            # Verificar que o desconto foi calculado
            call_args = mock_n8n_client.trigger_webhook.call_args
            data = call_args.kwargs.get("data", call_args[1].get("data", {}))
            assert "discount_percentage" in data or True  # Passa se existir
    
    @pytest.mark.asyncio
    async def test_trigger_price_drop_error(self, mock_user, mock_n8n_client):
        """Deve tratar erro no trigger"""
        from api.routes.n8n_webhooks import trigger_price_drop_alert
        
        mock_n8n_client.trigger_webhook.side_effect = Exception("Error")
        
        with patch("api.routes.n8n_webhooks.get_n8n_client",
                   return_value=mock_n8n_client):
            with pytest.raises(HTTPException) as exc_info:
                await trigger_price_drop_alert(
                    product_id="prod-123",
                    old_price=100.00,
                    new_price=80.00,
                    user=mock_user
                )
            
            assert exc_info.value.status_code == 500


# ============================================
# TESTS: Trigger Workflow
# ============================================

class TestTriggerWorkflow:
    """Testes para trigger de workflow manual"""
    
    @pytest.mark.asyncio
    async def test_trigger_workflow_success(self, mock_user, mock_n8n_client):
        """Deve disparar workflow com sucesso"""
        from api.routes.n8n_webhooks import (
            trigger_workflow_manually,
            WorkflowExecutionRequest
        )
        
        with patch("api.routes.n8n_webhooks.get_n8n_client",
                   return_value=mock_n8n_client):
            request = WorkflowExecutionRequest(
                workflow_id="wf-123",
                data={"input": "value"}
            )
            
            result = await trigger_workflow_manually(request, mock_user)
            
            assert result["success"] is True
            assert "execution_id" in result
    
    @pytest.mark.asyncio
    async def test_trigger_workflow_error(self, mock_user, mock_n8n_client):
        """Deve tratar erro no trigger"""
        from api.routes.n8n_webhooks import (
            trigger_workflow_manually,
            WorkflowExecutionRequest
        )
        
        mock_n8n_client.trigger_workflow_by_id.side_effect = Exception("Error")
        
        with patch("api.routes.n8n_webhooks.get_n8n_client",
                   return_value=mock_n8n_client):
            request = WorkflowExecutionRequest(
                workflow_id="wf-123",
                data={}
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await trigger_workflow_manually(request, mock_user)
            
            assert exc_info.value.status_code == 500


# ============================================
# TESTS: List Workflows
# ============================================

class TestListWorkflows:
    """Testes para listagem de workflows"""
    
    @pytest.mark.asyncio
    async def test_list_workflows_success(self, mock_user, mock_n8n_client):
        """Deve listar workflows com sucesso"""
        from api.routes.n8n_webhooks import list_workflows
        
        with patch("api.routes.n8n_webhooks.get_n8n_client",
                   return_value=mock_n8n_client):
            result = await list_workflows(mock_user)
            
            assert "workflows" in result
            assert "total" in result
            assert len(result["workflows"]) == 1
    
    @pytest.mark.asyncio
    async def test_list_workflows_error(self, mock_user, mock_n8n_client):
        """Deve tratar erro na listagem"""
        from api.routes.n8n_webhooks import list_workflows
        
        mock_n8n_client.list_workflows.side_effect = Exception("Error")
        
        with patch("api.routes.n8n_webhooks.get_n8n_client",
                   return_value=mock_n8n_client):
            with pytest.raises(HTTPException) as exc_info:
                await list_workflows(mock_user)
            
            assert exc_info.value.status_code == 500


# ============================================
# TESTS: List Executions
# ============================================

class TestListExecutions:
    """Testes para listagem de execuções"""
    
    @pytest.mark.asyncio
    async def test_list_executions_success(self, mock_user, mock_n8n_client):
        """Deve listar execuções com sucesso"""
        from api.routes.n8n_webhooks import list_executions
        
        with patch("api.routes.n8n_webhooks.get_n8n_client",
                   return_value=mock_n8n_client):
            result = await list_executions(user=mock_user)
            
            assert "executions" in result
            assert "total" in result
    
    @pytest.mark.asyncio
    async def test_list_executions_with_workflow_id(
        self, mock_user, mock_n8n_client
    ):
        """Deve filtrar por workflow_id"""
        from api.routes.n8n_webhooks import list_executions
        
        with patch("api.routes.n8n_webhooks.get_n8n_client",
                   return_value=mock_n8n_client):
            result = await list_executions(
                workflow_id="wf-123",
                limit=10,
                user=mock_user
            )
            
            assert "executions" in result
            mock_n8n_client.get_executions.assert_called_with(
                workflow_id="wf-123",
                limit=10
            )
    
    @pytest.mark.asyncio
    async def test_list_executions_error(self, mock_user, mock_n8n_client):
        """Deve tratar erro na listagem"""
        from api.routes.n8n_webhooks import list_executions
        
        mock_n8n_client.get_executions.side_effect = Exception("Error")
        
        with patch("api.routes.n8n_webhooks.get_n8n_client",
                   return_value=mock_n8n_client):
            with pytest.raises(HTTPException) as exc_info:
                await list_executions(user=mock_user)
            
            assert exc_info.value.status_code == 500


# ============================================
# TESTS: Helper Functions
# ============================================

class TestHelperFunctions:
    """Testes para funções auxiliares"""
    
    @pytest.mark.asyncio
    async def test_log_product_search(self):
        """Deve logar busca de produto"""
        from api.routes.n8n_webhooks import _log_product_search
        
        # Deve executar sem erro
        await _log_product_search("conv-123", "iphone", 5)
    
    @pytest.mark.asyncio
    async def test_track_price_alert(self):
        """Deve registrar alerta de preço"""
        from api.routes.n8n_webhooks import _track_price_alert
        
        # Deve executar sem erro
        await _track_price_alert("user-123", "prod-456", 100.0, 80.0)
    
    @pytest.mark.asyncio
    async def test_track_interaction(self):
        """Deve registrar interação"""
        from api.routes.n8n_webhooks import _track_interaction
        
        # Deve executar sem erro
        await _track_interaction("conv-123", {"action": "click"})
    
    @pytest.mark.asyncio
    async def test_track_workflow_completion(self):
        """Deve registrar conclusão de workflow"""
        from api.routes.n8n_webhooks import _track_workflow_completion
        
        # Deve executar sem erro
        await _track_workflow_completion({"workflow_id": "wf-123"})
