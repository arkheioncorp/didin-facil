"""
Automation Integration Tests
============================
Testes de integração para o sistema de automações n8n.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from modules.automation import (AutomationPriority, AutomationType,
                                ChannelType, N8nOrchestrator)
from modules.automation.scheduler import AutomationScheduler, ScheduleStatus

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_n8n_client():
    """Mock do cliente n8n."""
    client = MagicMock()
    client.trigger_webhook = AsyncMock(return_value={"success": True})
    client.execute_workflow = AsyncMock(return_value={"success": True})
    return client


@pytest.fixture
def orchestrator(mock_n8n_client):
    """Instância do orchestrator com mock."""
    return N8nOrchestrator(n8n_client=mock_n8n_client)


@pytest.fixture
def scheduler(orchestrator):
    """Instância do scheduler."""
    return AutomationScheduler(
        orchestrator=orchestrator,
        batch_size=10,
        poll_interval=1,
    )


@pytest.fixture
def sample_event_data():
    """Dados de exemplo para eventos."""
    return {
        "user_id": "test_user_123",
        "user_name": "João Teste",
        "user_email": "joao@teste.com",
        "channel": "whatsapp",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================
# ORCHESTRATOR TESTS
# ============================================

class TestN8nOrchestrator:
    """Testes do N8nOrchestrator."""

    def test_orchestrator_initialization(self, orchestrator):
        """Testa inicialização do orchestrator."""
        assert orchestrator is not None
        assert len(orchestrator.automations) > 0

    def test_automation_types_configured(self, orchestrator):
        """Testa se tipos principais estão configurados."""
        expected_types = [
            AutomationType.NEW_USER_WELCOME,
            AutomationType.NEW_LEAD_NURTURING,
            AutomationType.CART_ABANDONED,
            AutomationType.PRICE_DROP_ALERT,
            AutomationType.POST_PURCHASE_THANKS,
            AutomationType.COMPLAINT_ALERT,
            AutomationType.HUMAN_HANDOFF,
        ]
        
        for auto_type in expected_types:
            assert auto_type in orchestrator.automations

    @pytest.mark.asyncio
    async def test_trigger_onboarding(self, orchestrator, sample_event_data):
        """Testa trigger de onboarding."""
        result = await orchestrator.trigger_onboarding(
            user_id=sample_event_data["user_id"],
            name=sample_event_data["user_name"],
            channel=ChannelType.WHATSAPP,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_trigger_complaint_alert(self, orchestrator, sample_event_data):
        """Testa trigger de alerta de reclamação."""
        result = await orchestrator.trigger_complaint_alert(
            user_id=sample_event_data["user_id"],
            name=sample_event_data["user_name"],
            complaint="Produto com defeito!",
            channel=ChannelType.WHATSAPP,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_trigger_human_handoff(self, orchestrator, sample_event_data):
        """Testa trigger de handoff para humano."""
        result = await orchestrator.trigger_human_handoff(
            user_id=sample_event_data["user_id"],
            name=sample_event_data["user_name"],
            reason="User request",
            context_summary="Contexto do atendimento",
            channel=ChannelType.WHATSAPP,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_trigger_automation(self, orchestrator, sample_event_data):
        """Testa trigger de automação genérica."""
        result = await orchestrator.trigger_automation(
            automation_type=AutomationType.NEW_USER_WELCOME,
            user_id=sample_event_data["user_id"],
            data={"user_name": sample_event_data["user_name"]},
        )
        assert result is not None

    def test_rate_limiting_config(self, orchestrator):
        """Testa se rate limiting está configurado."""
        config = orchestrator.automations.get(AutomationType.NEW_USER_WELCOME)
        assert config is not None
        assert config.max_triggers_per_user_per_day > 0


# ============================================
# SCHEDULER TESTS
# ============================================

class TestAutomationScheduler:
    """Testes do AutomationScheduler."""

    def test_scheduler_initialization(self, scheduler):
        """Testa inicialização do scheduler."""
        assert scheduler is not None
        assert scheduler.batch_size == 10

    @pytest.mark.asyncio
    async def test_schedule_event(self, scheduler, sample_event_data):
        """Testa agendamento de evento."""
        event = await scheduler.schedule(
            automation_type=AutomationType.NEW_LEAD_NURTURING,
            user_id=sample_event_data["user_id"],
            data=sample_event_data,
            delay_minutes=5,
        )
        
        assert event is not None
        assert event.id is not None
        assert event.status == ScheduleStatus.PENDING

    @pytest.mark.asyncio
    async def test_schedule_immediate(self, scheduler, sample_event_data):
        """Testa agendamento imediato."""
        event = await scheduler.schedule(
            automation_type=AutomationType.COMPLAINT_ALERT,
            user_id=sample_event_data["user_id"],
            data=sample_event_data,
            delay_minutes=0,
        )
        
        assert event is not None
        assert event.scheduled_for <= datetime.now(timezone.utc) + timedelta(seconds=5)

    @pytest.mark.asyncio
    async def test_cancel_event(self, scheduler, sample_event_data):
        """Testa cancelamento de evento."""
        event = await scheduler.schedule(
            automation_type=AutomationType.NEW_LEAD_NURTURING,
            user_id=sample_event_data["user_id"],
            data=sample_event_data,
            delay_minutes=60,
        )
        
        success = await scheduler.cancel(event.id)
        assert success is True

    @pytest.mark.asyncio
    async def test_reschedule_event(self, scheduler, sample_event_data):
        """Testa reagendamento de evento."""
        event = await scheduler.schedule(
            automation_type=AutomationType.NEW_LEAD_NURTURING,
            user_id=sample_event_data["user_id"],
            data=sample_event_data,
            delay_minutes=60,
        )
        
        new_time = datetime.utcnow() + timedelta(hours=3)
        rescheduled = await scheduler.reschedule(event.id, new_time)
        
        assert rescheduled is not None
        assert rescheduled.scheduled_for == new_time

    @pytest.mark.asyncio
    async def test_get_pending_events(self, scheduler, sample_event_data):
        """Testa listagem de eventos pendentes."""
        for i in range(3):
            await scheduler.schedule(
                automation_type=AutomationType.NEW_LEAD_NURTURING,
                user_id=f"user_{i}",
                data=sample_event_data,
                delay_minutes=i + 1,
            )
        
        pending = scheduler.get_pending_events()
        assert len(pending) >= 3

    @pytest.mark.asyncio
    async def test_schedule_batch(self, scheduler, sample_event_data):
        """Testa agendamento em lote."""
        events_data = [
            {
                "automation_type": AutomationType.NEW_LEAD_NURTURING,
                "user_id": f"batch_user_{i}",
                "data": sample_event_data,
                "delay_minutes": i + 1,
            }
            for i in range(5)
        ]
        
        scheduled = await scheduler.schedule_batch(events_data)
        assert len(scheduled) == 5

    def test_queue_depth(self, scheduler):
        """Testa profundidade da fila."""
        depths = scheduler.get_queue_depth()
        
        assert "high" in depths
        assert "normal" in depths
        assert "low" in depths

    def test_stats(self, scheduler):
        """Testa estatísticas."""
        stats = scheduler.get_stats()
        
        assert hasattr(stats, "total_pending")
        assert hasattr(stats, "total_completed")

    @pytest.mark.asyncio
    async def test_process_now(self, scheduler, sample_event_data):
        """Testa processamento imediato."""
        event = await scheduler.schedule(
            automation_type=AutomationType.COMPLAINT_ALERT,
            user_id=sample_event_data["user_id"],
            data=sample_event_data,
            delay_minutes=60,
        )
        
        result = await scheduler.process_now(event.id)
        assert result is not None


# ============================================
# INTEGRATION TESTS
# ============================================

class TestAutomationIntegration:
    """Testes de integração do fluxo completo."""

    @pytest.mark.asyncio
    async def test_full_flow_welcome(self, scheduler, sample_event_data):
        """Testa fluxo completo de welcome."""
        event = await scheduler.schedule(
            automation_type=AutomationType.NEW_USER_WELCOME,
            user_id=sample_event_data["user_id"],
            data=sample_event_data,
            delay_minutes=0,
        )
        
        assert event.status == ScheduleStatus.PENDING
        result = await scheduler.process_now(event.id)
        assert result is not None

    @pytest.mark.asyncio
    async def test_full_flow_complaint(self, orchestrator, sample_event_data):
        """Testa fluxo completo de reclamação."""
        result = await orchestrator.trigger_complaint_alert(
            user_id=sample_event_data["user_id"],
            name=sample_event_data["user_name"],
            complaint="Produto chegou quebrado!",
            channel=ChannelType.WHATSAPP,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_full_flow_cart_abandoned(self, scheduler, sample_event_data):
        """Testa fluxo de carrinho abandonado."""
        cart_data = {
            **sample_event_data,
            "cart_id": "cart_123",
            "total_value": 9798.00,
        }
        
        event = await scheduler.schedule(
            automation_type=AutomationType.CART_ABANDONED,
            user_id=cart_data["user_id"],
            data=cart_data,
        )
        
        assert event.scheduled_for > datetime.now(timezone.utc)


# ============================================
# ERROR HANDLING TESTS
# ============================================

class TestErrorHandling:
    """Testes de tratamento de erros."""

    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self, scheduler):
        """Testa cancelar evento inexistente."""
        result = await scheduler.cancel("nonexistent_id")
        assert result is False

    @pytest.mark.asyncio
    async def test_reschedule_nonexistent(self, scheduler):
        """Testa reagendar evento inexistente."""
        result = await scheduler.reschedule(
            "nonexistent_id",
            datetime.utcnow() + timedelta(hours=1)
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_process_nonexistent(self, scheduler):
        """Testa processar evento inexistente."""
        result = await scheduler.process_now("nonexistent_id")
        assert result.get("success") is False
