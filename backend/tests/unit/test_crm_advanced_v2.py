"""
Testes para api/routers/crm_advanced.py
CRM Advanced Router - Risk Detection, NBA, Workflows
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routers.crm_advanced import (NextActionResponse,
                                      RiskAssessmentResponse,
                                      ScoreDecayConfigRequest,
                                      WorkflowActionSchema,
                                      WorkflowConditionSchema,
                                      WorkflowCreateRequest)

# ==================== TEST MODELS ====================

class TestRiskAssessmentResponse:
    """Testes para modelo RiskAssessmentResponse."""

    def test_valid_response(self):
        """Response válida."""
        response = RiskAssessmentResponse(
            deal_id="deal_123",
            risk_level="high",
            risk_score=75,
            signals=[{"type": "stalled", "severity": "high"}],
            recommendations=["Contact customer", "Offer discount"],
            assessed_at="2025-01-01T00:00:00Z"
        )
        
        assert response.deal_id == "deal_123"
        assert response.risk_level == "high"
        assert response.risk_score == 75
        assert len(response.signals) == 1
        assert len(response.recommendations) == 2


class TestNextActionResponse:
    """Testes para modelo NextActionResponse."""

    def test_valid_response(self):
        """Response válida."""
        response = NextActionResponse(
            action_type="call",
            action_label="Ligar para cliente",
            reason="Sem contato há 7 dias",
            priority="high",
            suggested_timing="today",
            entity_type="lead",
            entity_id="lead_123",
            metadata={"phone": "123456"}
        )
        
        assert response.action_type == "call"
        assert response.priority == "high"
        assert response.metadata["phone"] == "123456"

    def test_empty_metadata(self):
        """Metadata vazio."""
        response = NextActionResponse(
            action_type="email",
            action_label="Enviar email",
            reason="Follow up",
            priority="medium",
            suggested_timing="tomorrow",
            entity_type="deal",
            entity_id="deal_123"
        )
        
        assert response.metadata == {}


class TestWorkflowConditionSchema:
    """Testes para modelo WorkflowConditionSchema."""

    def test_string_value(self):
        """Condition com valor string."""
        condition = WorkflowConditionSchema(
            field="status",
            operator="equals",
            value="hot"
        )
        
        assert condition.field == "status"
        assert condition.value == "hot"

    def test_numeric_value(self):
        """Condition com valor numérico."""
        condition = WorkflowConditionSchema(
            field="value",
            operator="greater_than",
            value=10000
        )
        
        assert condition.value == 10000

    def test_list_value(self):
        """Condition com lista."""
        condition = WorkflowConditionSchema(
            field="tags",
            operator="contains",
            value=["vip", "priority"]
        )
        
        assert len(condition.value) == 2


class TestWorkflowActionSchema:
    """Testes para modelo WorkflowActionSchema."""

    def test_with_config(self):
        """Action com configuração."""
        action = WorkflowActionSchema(
            action_type="notify_user",
            config={"message": "New lead!", "channel": "email"}
        )
        
        assert action.action_type == "notify_user"
        assert action.config["channel"] == "email"

    def test_empty_config(self):
        """Action sem configuração."""
        action = WorkflowActionSchema(action_type="add_tag")
        
        assert action.config == {}


class TestWorkflowCreateRequest:
    """Testes para modelo WorkflowCreateRequest."""

    def test_minimal_request(self):
        """Request mínima."""
        request = WorkflowCreateRequest(
            name="My Workflow",
            event_type="lead_created",
            actions=[WorkflowActionSchema(action_type="notify_user")]
        )
        
        assert request.name == "My Workflow"
        assert request.description == ""
        assert request.is_active is True
        assert len(request.conditions) == 0

    def test_full_request(self):
        """Request completa."""
        request = WorkflowCreateRequest(
            name="Hot Lead Alert",
            description="Notify on hot leads",
            event_type="lead_temperature_changed",
            conditions=[
                WorkflowConditionSchema(
                    field="temperature",
                    operator="equals",
                    value="hot"
                )
            ],
            actions=[
                WorkflowActionSchema(action_type="notify_user"),
                WorkflowActionSchema(action_type="add_tag", config={"tag": "priority"})
            ],
            is_active=True,
            run_once_per_entity=True
        )
        
        assert len(request.conditions) == 1
        assert len(request.actions) == 2
        assert request.run_once_per_entity is True


class TestScoreDecayConfigRequest:
    """Testes para modelo ScoreDecayConfigRequest."""

    def test_defaults(self):
        """Configuração padrão."""
        config = ScoreDecayConfigRequest()
        
        assert config.decay_rate_per_week == 5.0
        assert config.max_decay_percent == 70.0
        assert config.grace_period_days == 7
        assert config.minimum_score == 5

    def test_custom_config(self):
        """Configuração customizada."""
        config = ScoreDecayConfigRequest(
            decay_rate_per_week=10.0,
            max_decay_percent=50.0,
            grace_period_days=14,
            minimum_score=10
        )
        
        assert config.decay_rate_per_week == 10.0
        assert config.grace_period_days == 14


# ==================== TEST RISK DETECTION ENDPOINTS ====================

# Helper para criar async mock de get_db
async def async_mock_db():
    return MagicMock()


class TestAssessDealRisk:
    """Testes para endpoint assess_deal_risk."""

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.DealRiskDetectionService')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_assess_deal_risk_success(self, mock_db, mock_service_class):
        """Deve avaliar risco com sucesso."""
        from api.routers.crm_advanced import assess_deal_risk
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_assessment = MagicMock()
        mock_assessment.to_dict.return_value = {
            "deal_id": "deal_123",
            "risk_level": "high",
            "risk_score": 75,
            "signals": [],
            "recommendations": []
        }
        
        mock_service = MagicMock()
        mock_service.assess_deal_risk = AsyncMock(return_value=mock_assessment)
        mock_service_class.return_value = mock_service
        
        result = await assess_deal_risk("deal_123", "user_123")
        
        assert result["deal_id"] == "deal_123"
        assert result["risk_level"] == "high"

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.DealRiskDetectionService')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_assess_deal_risk_not_found(self, mock_db, mock_service_class):
        """Deal não encontrado retorna 404."""
        from api.routers.crm_advanced import assess_deal_risk
        from fastapi import HTTPException
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_service = MagicMock()
        mock_service.assess_deal_risk = AsyncMock(side_effect=ValueError("Deal not found"))
        mock_service_class.return_value = mock_service
        
        with pytest.raises(HTTPException) as exc_info:
            await assess_deal_risk("invalid", "user_123")
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.DealRiskDetectionService')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_assess_deal_risk_error(self, mock_db, mock_service_class):
        """Erro interno retorna 500."""
        from api.routers.crm_advanced import assess_deal_risk
        from fastapi import HTTPException
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_service = MagicMock()
        mock_service.assess_deal_risk = AsyncMock(side_effect=Exception("DB error"))
        mock_service_class.return_value = mock_service
        
        with pytest.raises(HTTPException) as exc_info:
            await assess_deal_risk("deal_123", "user_123")
        
        assert exc_info.value.status_code == 500


class TestGetDealsAtRisk:
    """Testes para endpoint get_deals_at_risk."""

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.DealRiskDetectionService')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_get_deals_at_risk_success(self, mock_db, mock_service_class):
        """Deve retornar deals em risco."""
        from api.routers.crm_advanced import get_deals_at_risk
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_service = MagicMock()
        mock_service.assess_all_deals = AsyncMock(return_value={
            "critical": [{"deal_id": "d1"}],
            "high": [{"deal_id": "d2"}],
            "medium": [{"deal_id": "d3"}],
            "low": [{"deal_id": "d4"}],
            "summary": {"total_assessed": 4, "at_risk": 4}
        })
        mock_service_class.return_value = mock_service
        
        result = await get_deals_at_risk("user_123", None, "medium")
        
        assert len(result["critical"]) == 1
        assert len(result["high"]) == 1
        assert len(result["medium"]) == 1
        assert len(result["low"]) == 0  # Filtered out

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.DealRiskDetectionService')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_get_deals_at_risk_high_only(self, mock_db, mock_service_class):
        """Filtro high só retorna critical e high."""
        from api.routers.crm_advanced import get_deals_at_risk
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_service = MagicMock()
        mock_service.assess_all_deals = AsyncMock(return_value={
            "critical": [{"deal_id": "d1"}],
            "high": [{"deal_id": "d2"}],
            "medium": [{"deal_id": "d3"}],
            "low": [{"deal_id": "d4"}],
            "summary": {}
        })
        mock_service_class.return_value = mock_service
        
        result = await get_deals_at_risk("user_123", None, "high")
        
        assert len(result["critical"]) == 1
        assert len(result["high"]) == 1
        assert len(result["medium"]) == 0
        assert len(result["low"]) == 0


# ==================== TEST NEXT BEST ACTION ENDPOINTS ====================

class TestGetNextActionForLead:
    """Testes para endpoint get_next_action_for_lead."""

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.NextBestActionEngine')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_get_next_action_success(self, mock_db, mock_engine_class):
        """Deve retornar próxima ação para lead."""
        from api.routers.crm_advanced import get_next_action_for_lead
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_action = MagicMock()
        mock_action.to_dict.return_value = {
            "action_type": "call",
            "action_label": "Ligar",
            "reason": "Follow up",
            "priority": "high"
        }
        
        mock_engine = MagicMock()
        mock_engine.get_next_action_for_lead = AsyncMock(return_value=mock_action)
        mock_engine_class.return_value = mock_engine
        
        result = await get_next_action_for_lead("lead_123", "user_123")
        
        assert result["action_type"] == "call"
        assert result["priority"] == "high"

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.NextBestActionEngine')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_get_next_action_lead_not_found(self, mock_db, mock_engine_class):
        """Lead não encontrado retorna 404."""
        from api.routers.crm_advanced import get_next_action_for_lead
        from fastapi import HTTPException
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_engine = MagicMock()
        mock_engine.get_next_action_for_lead = AsyncMock(
            side_effect=ValueError("Lead not found")
        )
        mock_engine_class.return_value = mock_engine
        
        with pytest.raises(HTTPException) as exc_info:
            await get_next_action_for_lead("invalid", "user_123")
        
        assert exc_info.value.status_code == 404


class TestGetNextActionForDeal:
    """Testes para endpoint get_next_action_for_deal."""

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.NextBestActionEngine')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_get_next_action_success(self, mock_db, mock_engine_class):
        """Deve retornar próxima ação para deal."""
        from api.routers.crm_advanced import get_next_action_for_deal
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_action = MagicMock()
        mock_action.to_dict.return_value = {
            "action_type": "meeting",
            "action_label": "Agendar reunião",
            "reason": "Deal em negociação",
            "priority": "medium"
        }
        
        mock_engine = MagicMock()
        mock_engine.get_next_action_for_deal = AsyncMock(return_value=mock_action)
        mock_engine_class.return_value = mock_engine
        
        result = await get_next_action_for_deal("deal_123", "user_123")
        
        assert result["action_type"] == "meeting"

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.NextBestActionEngine')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_get_next_action_error(self, mock_db, mock_engine_class):
        """Erro interno retorna 500."""
        from api.routers.crm_advanced import get_next_action_for_deal
        from fastapi import HTTPException
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_engine = MagicMock()
        mock_engine.get_next_action_for_deal = AsyncMock(
            side_effect=Exception("DB error")
        )
        mock_engine_class.return_value = mock_engine
        
        with pytest.raises(HTTPException) as exc_info:
            await get_next_action_for_deal("deal_123", "user_123")
        
        assert exc_info.value.status_code == 500


class TestGetPrioritizedActions:
    """Testes para endpoint get_prioritized_actions."""

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.NextBestActionEngine')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_get_prioritized_actions_success(self, mock_db, mock_engine_class):
        """Deve retornar ações priorizadas."""
        from api.routers.crm_advanced import get_prioritized_actions
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_action1 = MagicMock()
        mock_action1.to_dict.return_value = {"action_type": "call", "priority": "high"}
        mock_action2 = MagicMock()
        mock_action2.to_dict.return_value = {"action_type": "email", "priority": "medium"}
        
        mock_engine = MagicMock()
        mock_engine.get_prioritized_actions = AsyncMock(
            return_value=[mock_action1, mock_action2]
        )
        mock_engine_class.return_value = mock_engine
        
        result = await get_prioritized_actions("user_123", 10)
        
        assert result["total"] == 2
        assert len(result["actions"]) == 2


# ==================== TEST WORKFLOW ENDPOINTS ====================

class TestCreateWorkflow:
    """Testes para endpoint create_workflow."""

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.WorkflowEngine')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_create_workflow_success(self, mock_db, mock_engine_class):
        """Deve criar workflow com sucesso."""
        from api.routers.crm_advanced import create_workflow
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_engine = MagicMock()
        mock_engine.register_workflow = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        request = WorkflowCreateRequest(
            name="Test Workflow",
            event_type="lead_created",
            actions=[WorkflowActionSchema(action_type="notify_user")]
        )
        
        with patch('api.routers.crm_advanced.Workflow') as mock_workflow:
            mock_wf_instance = MagicMock()
            mock_wf_instance.to_dict.return_value = {
                "name": "Test Workflow",
                "event_type": "lead_created"
            }
            mock_workflow.return_value = mock_wf_instance
            
            result = await create_workflow(request, "user_123")
        
        assert result["name"] == "Test Workflow"

    @pytest.mark.asyncio
    async def test_create_workflow_invalid_event_type(self):
        """Event type inválido retorna 400."""
        from api.routers.crm_advanced import create_workflow
        from fastapi import HTTPException
        
        request = WorkflowCreateRequest(
            name="Test Workflow",
            event_type="invalid_event",
            actions=[WorkflowActionSchema(action_type="notify_user")]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await create_workflow(request, "user_123")
        
        assert exc_info.value.status_code == 400
        assert "Event type inválido" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_create_workflow_invalid_action_type(self, mock_db):
        """Action type inválido retorna 400."""
        from api.routers.crm_advanced import create_workflow
        from fastapi import HTTPException
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        request = WorkflowCreateRequest(
            name="Test Workflow",
            event_type="lead_created",
            actions=[WorkflowActionSchema(action_type="invalid_action")]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await create_workflow(request, "user_123")
        
        assert exc_info.value.status_code == 400
        assert "Action type inválido" in exc_info.value.detail


class TestListWorkflowTemplates:
    """Testes para endpoint list_workflow_templates."""

    @pytest.mark.asyncio
    async def test_list_templates(self):
        """Deve listar templates disponíveis."""
        from api.routers.crm_advanced import list_workflow_templates
        
        result = await list_workflow_templates()
        
        assert "templates" in result
        assert len(result["templates"]) >= 4
        
        template_ids = [t["id"] for t in result["templates"]]
        assert "hot_lead_notification" in template_ids
        assert "deal_won_celebration" in template_ids
        assert "stalled_deal_alert" in template_ids
        assert "high_value_lead" in template_ids


class TestApplyWorkflowTemplate:
    """Testes para endpoint apply_workflow_template."""

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.WorkflowTemplates')
    @patch('api.routers.crm_advanced.WorkflowEngine')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_apply_hot_lead_template(
        self, mock_db, mock_engine_class, mock_templates
    ):
        """Deve aplicar template hot_lead_notification."""
        from api.routers.crm_advanced import apply_workflow_template
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_engine = MagicMock()
        mock_engine.register_workflow = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        mock_workflow = MagicMock()
        mock_workflow.to_dict.return_value = {
            "name": "Hot Lead Notification",
            "event_type": "lead_temperature_changed"
        }
        mock_templates.hot_lead_notification.return_value = mock_workflow
        
        result = await apply_workflow_template("hot_lead_notification", "user_123")
        
        assert result["name"] == "Hot Lead Notification"
        mock_templates.hot_lead_notification.assert_called_once_with("user_123")

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.WorkflowTemplates')
    @patch('api.routers.crm_advanced.WorkflowEngine')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_apply_high_value_template_with_threshold(
        self, mock_db, mock_engine_class, mock_templates
    ):
        """Deve aplicar template high_value_lead com threshold."""
        from api.routers.crm_advanced import apply_workflow_template
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        mock_workflow = MagicMock()
        mock_workflow.to_dict.return_value = {"name": "High Value Lead"}
        mock_templates.high_value_lead.return_value = mock_workflow
        
        result = await apply_workflow_template("high_value_lead", "user_123", 50000)
        
        mock_templates.high_value_lead.assert_called_once_with("user_123", 50000)

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.WorkflowEngine')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_apply_invalid_template(self, mock_db, mock_engine_class):
        """Template inexistente retorna 404."""
        from api.routers.crm_advanced import apply_workflow_template
        from fastapi import HTTPException
        
        mock_db.return_value = MagicMock()
        mock_engine_class.return_value = MagicMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await apply_workflow_template("invalid_template", "user_123")
        
        assert exc_info.value.status_code == 404


class TestListEventTypes:
    """Testes para endpoint list_event_types."""

    @pytest.mark.asyncio
    async def test_list_event_types(self):
        """Deve listar tipos de eventos."""
        from api.routers.crm_advanced import list_event_types
        
        result = await list_event_types()
        
        assert "event_types" in result
        assert len(result["event_types"]) > 0
        
        # Verifica estrutura
        event = result["event_types"][0]
        assert "value" in event
        assert "name" in event


class TestListActionTypes:
    """Testes para endpoint list_action_types."""

    @pytest.mark.asyncio
    async def test_list_action_types(self):
        """Deve listar tipos de ações."""
        from api.routers.crm_advanced import list_action_types
        
        result = await list_action_types()
        
        assert "action_types" in result
        assert len(result["action_types"]) > 0


# ==================== TEST SCORE DECAY ENDPOINT ====================

class TestRunScoreDecay:
    """Testes para endpoint run_score_decay."""

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.ScoreDecayService')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_run_score_decay_success(self, mock_db, mock_service_class):
        """Deve executar decay com sucesso."""
        from api.routers.crm_advanced import run_score_decay
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_service = MagicMock()
        mock_service.run_decay_batch = AsyncMock(return_value={
            "processed": 10,
            "decayed": 5,
            "skipped": 5
        })
        mock_service_class.return_value = mock_service
        
        result = await run_score_decay("user_123", None)
        
        assert result["processed"] == 10
        assert result["decayed"] == 5

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.ScoreDecayService')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_run_score_decay_with_config(
        self, mock_db, mock_service_class
    ):
        """Deve executar decay com configuração customizada."""
        from api.routers.crm_advanced import run_score_decay
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_service = MagicMock()
        mock_service.run_decay_batch = AsyncMock(return_value={"processed": 5})
        mock_service_class.return_value = mock_service
        
        config = ScoreDecayConfigRequest(
            decay_rate_per_week=10.0,
            grace_period_days=14
        )
        
        result = await run_score_decay("user_123", config)
        
        assert result["processed"] == 5

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.ScoreDecayService')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_run_score_decay_error(self, mock_db, mock_service_class):
        """Erro interno retorna 500."""
        from api.routers.crm_advanced import run_score_decay
        from fastapi import HTTPException
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_service = MagicMock()
        mock_service.run_decay_batch = AsyncMock(
            side_effect=Exception("Error")
        )
        mock_service_class.return_value = mock_service
        
        with pytest.raises(HTTPException) as exc_info:
            await run_score_decay("user_123", None)
        
        assert exc_info.value.status_code == 500


# ==================== TEST DASHBOARD ENDPOINT ====================

class TestGetAdvancedDashboard:
    """Testes para endpoint get_advanced_dashboard."""

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.NextBestActionEngine')
    @patch('api.routers.crm_advanced.DealRiskDetectionService')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_get_dashboard_success(
        self, mock_db, mock_risk_class, mock_nba_class
    ):
        """Deve retornar dashboard completo."""
        from api.routers.crm_advanced import get_advanced_dashboard
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        # Mock risk service
        mock_risk = MagicMock()
        mock_risk.assess_all_deals = AsyncMock(return_value={
            "critical": [{
                "deal": {"id": "d1", "title": "Deal 1", "value": 1000},
                "assessment": {"risk_level": "critical", "risk_score": 90}
            }],
            "high": [],
            "medium": [],
            "low": [],
            "summary": {
                "total_assessed": 10,
                "at_risk": 1,
                "total_value_at_risk": 1000
            }
        })
        mock_risk_class.return_value = mock_risk
        
        # Mock NBA engine
        mock_action = MagicMock()
        mock_action.to_dict.return_value = {
            "action_type": "call",
            "priority": "high"
        }
        mock_action.priority = MagicMock(value="high")
        
        mock_nba = MagicMock()
        mock_nba.get_prioritized_actions = AsyncMock(
            return_value=[mock_action]
        )
        mock_nba_class.return_value = mock_nba
        
        result = await get_advanced_dashboard("user_123")
        
        assert "risk_summary" in result
        assert "top_risks" in result
        assert "priority_actions" in result
        assert "action_breakdown" in result
        
        assert result["risk_summary"]["total_assessed"] == 10
        assert result["risk_summary"]["critical_count"] == 1
        assert result["action_breakdown"]["high"] == 1

    @pytest.mark.asyncio
    @patch('api.routers.crm_advanced.DealRiskDetectionService')
    @patch('api.routers.crm_advanced.get_db', new_callable=AsyncMock)
    async def test_get_dashboard_error(self, mock_db, mock_risk_class):
        """Erro interno retorna 500."""
        from api.routers.crm_advanced import get_advanced_dashboard
        from fastapi import HTTPException
        
        mock_pool = MagicMock()
        mock_db.return_value = mock_pool
        
        mock_risk = MagicMock()
        mock_risk.assess_all_deals = AsyncMock(
            side_effect=Exception("DB error")
        )
        mock_risk_class.return_value = mock_risk
        
        with pytest.raises(HTTPException) as exc_info:
            await get_advanced_dashboard("user_123")
        
        assert exc_info.value.status_code == 500
