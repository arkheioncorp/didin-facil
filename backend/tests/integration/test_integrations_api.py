"""
Integration Tests - API Integrations
====================================
Testes de integração para módulos de API externa.

Estes testes verificam a integração com APIs externas
usando mocks para simular respostas.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from vendor.integrations.typebot import (
    TypebotClient,
    TypebotConfig,
)
from vendor.integrations.n8n import (
    N8nClient,
    N8nConfig,
    ExecutionStatus,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def typebot_config() -> TypebotConfig:
    """Configuração do Typebot."""
    return TypebotConfig(
        api_url="https://typebot.example.com",
        api_token="test-token",
        public_id="tiktrend-bot"
    )


@pytest.fixture
def n8n_config() -> N8nConfig:
    """Configuração do n8n."""
    return N8nConfig(
        api_url="http://localhost:5678",
        api_key="n8n-api-key"
    )


# ============================================
# TYPEBOT CONVERSATION FLOW TESTS
# ============================================

class TestTypebotConversationFlow:
    """Testes de fluxo de conversa com Typebot."""
    
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self, typebot_config):
        """Deve executar fluxo completo de conversa."""
        # Mock das respostas do Typebot
        start_response = {
            "sessionId": "session-123",
            "messages": [
                {"type": "text", "content": "Olá! Bem-vindo ao TikTrend Finder!"},
                {"type": "text", "content": "Qual seu nome?"}
            ],
            "input": {"type": "text input", "placeholder": "Digite seu nome"},
            "isCompleted": False
        }
        
        name_response = {
            "messages": [
                {"type": "text", "content": "Prazer, João!"},
                {"type": "text", "content": "O que você está procurando?"}
            ],
            "input": {
                "type": "choice input",
                "options": ["Smartphones", "TVs", "Eletrodomésticos"]
            },
            "isCompleted": False
        }
        
        choice_response = {
            "messages": [
                {"type": "text", "content": "Ótimo! Vou te mostrar as melhores ofertas de Smartphones."},
                {"type": "text", "content": "Confira: https://tiktrendfinder.com/ofertas/smartphones"}
            ],
            "input": None,
            "isCompleted": True
        }
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            
            # Configurar respostas sequenciais
            mock_responses = [
                MagicMock(json=MagicMock(return_value=start_response)),
                MagicMock(json=MagicMock(return_value=name_response)),
                MagicMock(json=MagicMock(return_value=choice_response)),
            ]
            for resp in mock_responses:
                resp.raise_for_status = MagicMock()
            
            mock_client.post.side_effect = mock_responses
            mock_httpx.return_value = mock_client
            
            client = TypebotClient(typebot_config)
            
            # 1. Iniciar conversa
            session = await client.start_chat()
            assert session.session_id == "session-123"
            assert len(session.messages) == 2
            
            # 2. Responder com nome
            session = await client.send_message(session.session_id, "João")
            assert "Prazer, João!" in session.messages[0]["content"]
            
            # 3. Fazer escolha
            session = await client.send_message(session.session_id, "Smartphones")
            assert session.is_completed is True
    
    @pytest.mark.asyncio
    async def test_conversation_with_variables(self, typebot_config):
        """Deve iniciar conversa com variáveis pré-definidas."""
        response = {
            "sessionId": "session-vars",
            "messages": [
                {"type": "text", "content": "Olá João! Vejo que você é um cliente VIP!"}
            ],
            "input": None,
            "isCompleted": False
        }
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock(json=MagicMock(return_value=response))
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client
            
            client = TypebotClient(typebot_config)
            
            session = await client.start_chat(
                prefilted_variables={
                    "name": "João",
                    "customer_type": "VIP",
                    "last_purchase": "2025-01-01"
                }
            )
            
            assert "João" in session.messages[0]["content"]
            assert "VIP" in session.messages[0]["content"]


# ============================================
# N8N WORKFLOW TESTS
# ============================================

class TestN8nWorkflowFlow:
    """Testes de fluxo de workflow n8n."""
    
    @pytest.mark.asyncio
    async def test_workflow_execution_flow(self, n8n_config):
        """Deve executar fluxo completo de workflow."""
        # Mock das respostas do n8n
        workflow_response = {
            "id": "wf-deal-alert",
            "name": "Deal Alert Notification",
            "active": True,
            "nodes": [
                {"type": "webhook"},
                {"type": "set"},
                {"type": "whatsapp"}
            ]
        }
        
        execution_response = {
            "executionId": "exec-001",
            "finished": True,
            "data": {
                "notifications_sent": 150,
                "success_rate": 0.98
            },
            "startedAt": "2025-01-01T10:00:00Z",
            "stoppedAt": "2025-01-01T10:00:05Z"
        }
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            
            # Resposta do get_workflow
            get_response = MagicMock(json=MagicMock(return_value=workflow_response))
            get_response.raise_for_status = MagicMock()
            
            # Resposta do execute
            exec_response = MagicMock(json=MagicMock(return_value=execution_response))
            exec_response.raise_for_status = MagicMock()
            
            mock_client.get.return_value = get_response
            mock_client.post.return_value = exec_response
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            
            # 1. Obter detalhes do workflow
            workflow = await client.get_workflow("wf-deal-alert")
            assert workflow["name"] == "Deal Alert Notification"
            assert workflow["active"] is True
            
            # 2. Executar workflow
            execution = await client.execute_workflow(
                "wf-deal-alert",
                {
                    "product_name": "iPhone 15",
                    "price": 7999.00,
                    "discount": 15,
                    "store": "Amazon"
                }
            )
            
            assert execution.status == ExecutionStatus.SUCCESS
            assert execution.data["notifications_sent"] == 150
    
    @pytest.mark.asyncio
    async def test_workflow_management_flow(self, n8n_config):
        """Deve gerenciar workflows (ativar/desativar)."""
        list_response = {
            "data": [
                {"id": "wf-1", "name": "Active Workflow", "active": True},
                {"id": "wf-2", "name": "Inactive Workflow", "active": False},
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            
            # Resposta do list
            list_resp = MagicMock(json=MagicMock(return_value=list_response))
            list_resp.raise_for_status = MagicMock()
            mock_client.get.return_value = list_resp
            
            # Resposta do activate/deactivate
            action_resp = MagicMock()
            action_resp.raise_for_status = MagicMock()
            mock_client.post.return_value = action_resp
            
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            
            # 1. Listar workflows
            workflows = await client.list_workflows()
            assert len(workflows) == 2
            
            # 2. Ativar workflow inativo
            result = await client.activate_workflow("wf-2")
            assert result is True
            
            # 3. Desativar workflow ativo
            result = await client.deactivate_workflow("wf-1")
            assert result is True


# ============================================
# INTEGRATION BETWEEN SYSTEMS
# ============================================

class TestSystemIntegration:
    """Testes de integração entre sistemas."""
    
    @pytest.mark.asyncio
    async def test_typebot_to_n8n_flow(self, typebot_config, n8n_config):
        """Deve integrar Typebot com n8n."""
        # Simular coleta de dados via Typebot
        collected_data = {
            "name": "João Silva",
            "email": "joao@email.com",
            "phone": "5511999999999",
            "interest": "smartphones",
            "budget": "high"
        }
        
        # Mock do n8n para processar lead
        n8n_response = {
            "executionId": "exec-lead",
            "finished": True,
            "data": {
                "lead_created": True,
                "lead_id": "lead-123",
                "crm_synced": True
            }
        }
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_resp = MagicMock(json=MagicMock(return_value=n8n_response))
            mock_resp.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_resp
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            
            # Enviar dados do Typebot para n8n
            execution = await client.execute_workflow(
                "wf-process-lead",
                collected_data
            )
            
            assert execution.status == ExecutionStatus.SUCCESS
            assert execution.data["lead_created"] is True
    
    @pytest.mark.asyncio
    async def test_deal_alert_pipeline(self, n8n_config):
        """Deve executar pipeline de alerta de ofertas."""
        # Dados da oferta detectada
        deal_data = {
            "product_id": "prod-123",
            "product_name": "Samsung Galaxy S24",
            "current_price": 4499.00,
            "previous_price": 5999.00,
            "discount_percent": 25,
            "store": "Magazine Luiza",
            "url": "https://magalu.com/s24",
            "detected_at": "2025-01-01T10:00:00Z"
        }
        
        execution_response = {
            "executionId": "exec-alert",
            "finished": True,
            "data": {
                "instagram_posted": True,
                "tiktok_posted": True,
                "whatsapp_sent": True,
                "recipients_reached": 500
            }
        }
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_resp = MagicMock(json=MagicMock(return_value=execution_response))
            mock_resp.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_resp
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            
            # Disparar workflow de alerta
            execution = await client.execute_workflow(
                "wf-deal-alert-pipeline",
                deal_data
            )
            
            assert execution.status == ExecutionStatus.SUCCESS
            assert execution.data["instagram_posted"] is True
            assert execution.data["recipients_reached"] == 500


# ============================================
# ERROR RECOVERY TESTS
# ============================================

class TestErrorRecovery:
    """Testes de recuperação de erros."""
    
    @pytest.mark.asyncio
    async def test_typebot_session_recovery(self, typebot_config):
        """Deve recuperar sessão do Typebot."""
        # Primeira tentativa falha
        # Segunda tentativa sucede
        error_response = httpx.HTTPStatusError(
            "Service Unavailable",
            request=MagicMock(),
            response=MagicMock(status_code=503)
        )
        
        success_response = {
            "sessionId": "recovered-session",
            "messages": [{"type": "text", "content": "Bem-vindo de volta!"}],
            "input": None,
            "isCompleted": False
        }
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            
            # Simular falha e recuperação
            mock_success = MagicMock(json=MagicMock(return_value=success_response))
            mock_success.raise_for_status = MagicMock()
            
            mock_client.post.side_effect = [error_response, mock_success]
            mock_httpx.return_value = mock_client
            
            client = TypebotClient(typebot_config)
            
            # Primeira tentativa falha
            with pytest.raises(httpx.HTTPStatusError):
                await client.start_chat()
            
            # Segunda tentativa sucede
            session = await client.start_chat()
            assert session.session_id == "recovered-session"
    
    @pytest.mark.asyncio
    async def test_n8n_workflow_retry(self, n8n_config):
        """Deve tentar novamente workflow que falhou."""
        # Execução com erro retorna status de erro
        error_response = {
            "executionId": "exec-failed",
            "finished": True,
            "data": {},
            "error": "External API timeout"
        }
        
        # Verificação de status
        status_response = {
            "id": "exec-failed",
            "status": "error",
            "data": {},
            "error": "External API timeout"
        }
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            
            # Resposta de execução
            exec_resp = MagicMock(json=MagicMock(return_value=error_response))
            exec_resp.raise_for_status = MagicMock()
            mock_client.post.return_value = exec_resp
            
            # Resposta de status
            status_resp = MagicMock(json=MagicMock(return_value=status_response))
            status_resp.raise_for_status = MagicMock()
            mock_client.get.return_value = status_resp
            
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            
            # Verificar status de execução com erro
            execution = await client.get_execution("exec-failed")
            
            assert execution.status == ExecutionStatus.ERROR


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestPerformanceScenarios:
    """Testes de cenários de performance."""
    
    @pytest.mark.asyncio
    async def test_batch_workflow_execution(self, n8n_config):
        """Deve executar múltiplos workflows em batch."""
        # Dados de múltiplas ofertas
        deals = [
            {"id": f"deal-{i}", "product": f"Product {i}", "price": 100 * i}
            for i in range(1, 6)
        ]
        
        # Mock de execuções bem sucedidas
        execution_response = {
            "executionId": "exec-batch",
            "finished": True,
            "data": {"processed": True}
        }
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_resp = MagicMock(json=MagicMock(return_value=execution_response))
            mock_resp.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_resp
            mock_httpx.return_value = mock_client
            
            client = N8nClient(n8n_config)
            
            # Executar workflows em batch
            results = []
            for deal in deals:
                execution = await client.execute_workflow("wf-process-deal", deal)
                results.append(execution)
            
            # Verificar que todos foram processados
            assert len(results) == 5
            assert all(r.status == ExecutionStatus.SUCCESS for r in results)
