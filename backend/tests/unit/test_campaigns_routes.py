"""
Testes para Campaigns Routes
=============================
Cobertura completa para api/routes/campaigns.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json


# Fixtures
@pytest.fixture
def mock_user():
    """Mock de usuário autenticado com suporte a dict e atributos."""
    class MockUser(dict):
        def __init__(self):
            super().__init__(id="user-123", email="test@example.com")
            self.id = "user-123"
            self.email = "test@example.com"
    return MockUser()


@pytest.fixture
def mock_redis():
    """Mock do Redis."""
    redis = AsyncMock()
    redis.hgetall = AsyncMock(return_value={})
    redis.hset = AsyncMock()
    redis.sadd = AsyncMock()
    redis.srem = AsyncMock()
    redis.delete = AsyncMock()
    redis.smembers = AsyncMock(return_value=set())
    redis.scard = AsyncMock(return_value=100)
    redis.zadd = AsyncMock()
    redis.lpush = AsyncMock()
    return redis


@pytest.fixture
def campaign_create_data():
    """Dados para criar campanha."""
    return {
        "name": "Black Friday Campaign",
        "subject": "Don't miss our deals!",
        "preview_text": "Up to 70% off",
        "html_content": "<h1>Black Friday</h1>",
        "list_ids": ["list-1", "list-2"],
        "type": "regular",
        "trigger": "immediate",
        "track_opens": True,
        "track_clicks": True,
    }


@pytest.fixture
def automation_create_data():
    """Dados para criar automação."""
    return {
        "name": "Welcome Series",
        "description": "Welcome new subscribers",
        "trigger_event": "signup",
        "delay_minutes": 0,
        "emails": [
            {"subject": "Welcome!", "template_id": "tmpl-1"},
            {"subject": "Getting Started", "template_id": "tmpl-2"},
        ],
        "active": True,
    }


# ==================== CAMPAIGN SERVICE TESTS ====================


class TestCampaignService:
    """Testes do CampaignService."""

    @pytest.mark.asyncio
    async def test_create_campaign(self, mock_redis, campaign_create_data):
        """Testa criação de campanha."""
        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import (
                CampaignService,
                CampaignCreate,
                CampaignStatus,
            )

            service = CampaignService()
            data = CampaignCreate(**campaign_create_data)

            result = await service.create_campaign("user-123", data)

            assert result.name == campaign_create_data["name"]
            assert result.subject == campaign_create_data["subject"]
            assert result.status == CampaignStatus.DRAFT
            assert result.recipients_count == 200  # 100 * 2 listas
            mock_redis.hset.assert_called_once()
            mock_redis.sadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_campaign_success(self, mock_redis):
        """Testa busca de campanha existente."""
        campaign_data = {
            "id": "camp-123",
            "user_id": "user-123",
            "name": "Test Campaign",
            "subject": "Test Subject",
            "preview_text": "",
            "status": "draft",
            "type": "regular",
            "trigger": "immediate",
            "list_ids": '["list-1"]',
            "recipients_count": "100",
            "schedule_at": "",
            "sent_at": "",
            "created_at": "2025-01-10T10:00:00",
            "updated_at": "2025-01-10T10:00:00",
        }
        mock_redis.hgetall = AsyncMock(return_value=campaign_data)

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService

            service = CampaignService()
            result = await service.get_campaign("user-123", "camp-123")

            assert result is not None
            assert result.id == "camp-123"
            assert result.name == "Test Campaign"

    @pytest.mark.asyncio
    async def test_get_campaign_not_found(self, mock_redis):
        """Testa busca de campanha não encontrada."""
        mock_redis.hgetall = AsyncMock(return_value={})

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService

            service = CampaignService()
            result = await service.get_campaign("user-123", "camp-999")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_campaign_wrong_user(self, mock_redis):
        """Testa busca de campanha de outro usuário."""
        campaign_data = {
            "id": "camp-123",
            "user_id": "other-user",
            "name": "Test Campaign",
        }
        mock_redis.hgetall = AsyncMock(return_value=campaign_data)

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService

            service = CampaignService()
            result = await service.get_campaign("user-123", "camp-123")

            assert result is None

    @pytest.mark.asyncio
    async def test_list_campaigns(self, mock_redis):
        """Testa listagem de campanhas."""
        mock_redis.smembers = AsyncMock(return_value={"camp-1", "camp-2"})
        mock_redis.hgetall = AsyncMock(
            side_effect=[
                {
                    "id": "camp-1",
                    "user_id": "user-123",
                    "name": "Campaign 1",
                    "subject": "Subject 1",
                    "status": "draft",
                    "type": "regular",
                    "trigger": "immediate",
                    "list_ids": "[]",
                    "recipients_count": "50",
                    "created_at": "2025-01-10T10:00:00",
                    "updated_at": "2025-01-10T10:00:00",
                },
                {
                    "id": "camp-2",
                    "user_id": "user-123",
                    "name": "Campaign 2",
                    "subject": "Subject 2",
                    "status": "sent",
                    "type": "regular",
                    "trigger": "immediate",
                    "list_ids": "[]",
                    "recipients_count": "100",
                    "created_at": "2025-01-10T11:00:00",
                    "updated_at": "2025-01-10T11:00:00",
                },
            ]
        )

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService

            service = CampaignService()
            result = await service.list_campaigns("user-123")

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_campaigns_with_status_filter(self, mock_redis):
        """Testa listagem com filtro de status."""
        mock_redis.smembers = AsyncMock(return_value={"camp-1"})
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-1",
                "user_id": "user-123",
                "name": "Campaign 1",
                "subject": "Subject 1",
                "status": "draft",
                "type": "regular",
                "trigger": "immediate",
                "list_ids": "[]",
                "recipients_count": "50",
                "created_at": "2025-01-10T10:00:00",
                "updated_at": "2025-01-10T10:00:00",
            }
        )

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService, CampaignStatus

            service = CampaignService()
            result = await service.list_campaigns(
                "user-123", status=CampaignStatus.DRAFT
            )

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_update_campaign_success(self, mock_redis):
        """Testa atualização de campanha."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "name": "Old Name",
                "subject": "Old Subject",
                "status": "draft",
                "type": "regular",
                "trigger": "immediate",
                "list_ids": "[]",
                "recipients_count": "50",
                "created_at": "2025-01-10T10:00:00",
                "updated_at": "2025-01-10T10:00:00",
            }
        )

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService, CampaignUpdate

            service = CampaignService()
            update_data = CampaignUpdate(name="New Name", subject="New Subject")

            result = await service.update_campaign("user-123", "camp-123", update_data)

            mock_redis.hset.assert_called()

    @pytest.mark.asyncio
    async def test_update_campaign_not_draft(self, mock_redis):
        """Testa atualização de campanha não-draft."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "status": "sent",
            }
        )

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService, CampaignUpdate
            from fastapi import HTTPException

            service = CampaignService()
            update_data = CampaignUpdate(name="New Name")

            with pytest.raises(HTTPException) as exc_info:
                await service.update_campaign("user-123", "camp-123", update_data)

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_send_campaign_success(self, mock_redis):
        """Testa envio de campanha."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "status": "draft",
            }
        )

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService
            from fastapi import BackgroundTasks

            service = CampaignService()
            background_tasks = BackgroundTasks()

            result = await service.send_campaign(
                "user-123", "camp-123", background_tasks
            )

            assert result["status"] == "sending"
            mock_redis.lpush.assert_called()

    @pytest.mark.asyncio
    async def test_send_campaign_already_sent(self, mock_redis):
        """Testa envio de campanha já enviada."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "status": "sent",
            }
        )

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService
            from fastapi import BackgroundTasks, HTTPException

            service = CampaignService()
            background_tasks = BackgroundTasks()

            with pytest.raises(HTTPException) as exc_info:
                await service.send_campaign("user-123", "camp-123", background_tasks)

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_schedule_campaign_success(self, mock_redis):
        """Testa agendamento de campanha."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "status": "draft",
            }
        )

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService

            service = CampaignService()
            schedule_time = datetime.now() + timedelta(days=1)

            result = await service.schedule_campaign(
                "user-123", "camp-123", schedule_time
            )

            assert result["status"] == "scheduled"
            mock_redis.zadd.assert_called()

    @pytest.mark.asyncio
    async def test_schedule_campaign_past_date(self, mock_redis):
        """Testa agendamento com data passada."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "status": "draft",
            }
        )

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService
            from fastapi import HTTPException

            service = CampaignService()
            schedule_time = datetime.now() - timedelta(days=1)

            with pytest.raises(HTTPException) as exc_info:
                await service.schedule_campaign(
                    "user-123", "camp-123", schedule_time
                )

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_campaign_stats(self, mock_redis):
        """Testa obtenção de estatísticas."""
        mock_redis.hgetall = AsyncMock(
            side_effect=[
                # Campaign data
                {"id": "camp-123", "user_id": "user-123"},
                # Stats data
                {
                    "total_recipients": "1000",
                    "total_sent": "1000",
                    "total_delivered": "950",
                    "total_opened": "400",
                    "unique_opens": "300",
                    "total_clicked": "100",
                    "unique_clicks": "80",
                    "total_bounced": "30",
                    "total_unsubscribed": "5",
                    "total_complained": "2",
                    "first_open_at": "2025-01-10T12:00:00",
                    "last_open_at": "2025-01-11T15:00:00",
                    "avg_open_time_seconds": "3600",
                    "top_links": "[]",
                    "device_breakdown": "{}",
                    "location_breakdown": "{}",
                },
            ]
        )

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService

            service = CampaignService()
            result = await service.get_campaign_stats("user-123", "camp-123")

            assert result is not None
            assert result.total_sent == 1000
            assert result.open_rate > 0

    @pytest.mark.asyncio
    async def test_get_campaign_stats_not_found(self, mock_redis):
        """Testa estatísticas não encontradas."""
        mock_redis.hgetall = AsyncMock(
            side_effect=[
                {"id": "camp-123", "user_id": "user-123"},
                {},  # No stats
            ]
        )

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService

            service = CampaignService()
            result = await service.get_campaign_stats("user-123", "camp-123")

            assert result is None


# ==================== CAMPAIGN ENDPOINT TESTS ====================


class TestCampaignEndpoints:
    """Testes dos endpoints de campanhas."""

    @pytest.mark.asyncio
    async def test_create_campaign_endpoint(
        self, mock_user, mock_redis, campaign_create_data
    ):
        """Testa endpoint de criação de campanha."""
        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import create_campaign, CampaignCreate

            data = CampaignCreate(**campaign_create_data)
            result = await create_campaign(data, mock_user)

            assert result.name == campaign_create_data["name"]

    @pytest.mark.asyncio
    async def test_list_campaigns_endpoint(self, mock_user, mock_redis):
        """Testa endpoint de listagem."""
        mock_redis.smembers = AsyncMock(return_value=set())

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import list_campaigns

            result = await list_campaigns(None, 1, 20, mock_user)

            assert result == []

    @pytest.mark.asyncio
    async def test_get_campaign_endpoint_success(self, mock_user, mock_redis):
        """Testa endpoint de busca de campanha."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "name": "Test Campaign",
                "subject": "Test Subject",
                "status": "draft",
                "type": "regular",
                "trigger": "immediate",
                "list_ids": "[]",
                "recipients_count": "50",
                "created_at": "2025-01-10T10:00:00",
                "updated_at": "2025-01-10T10:00:00",
            }
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import get_campaign

            result = await get_campaign("camp-123", mock_user)

            assert result.id == "camp-123"

    @pytest.mark.asyncio
    async def test_get_campaign_endpoint_not_found(self, mock_user, mock_redis):
        """Testa endpoint com campanha não encontrada."""
        mock_redis.hgetall = AsyncMock(return_value={})

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import get_campaign
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await get_campaign("camp-999", mock_user)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_campaign_success(self, mock_user, mock_redis):
        """Testa remoção de campanha."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "status": "draft",
            }
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import delete_campaign

            result = await delete_campaign("camp-123", mock_user)

            assert result["status"] == "deleted"
            mock_redis.delete.assert_called()

    @pytest.mark.asyncio
    async def test_delete_campaign_sending(self, mock_user, mock_redis):
        """Testa remoção de campanha em envio."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "status": "sending",
            }
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import delete_campaign
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await delete_campaign("camp-123", mock_user)

            assert exc_info.value.status_code == 400


class TestCampaignActions:
    """Testes de ações de campanha."""

    @pytest.mark.asyncio
    async def test_send_campaign_endpoint(self, mock_user, mock_redis):
        """Testa endpoint de envio."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "status": "draft",
            }
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import send_campaign
            from fastapi import BackgroundTasks

            background_tasks = BackgroundTasks()
            result = await send_campaign("camp-123", background_tasks, mock_user)

            assert result["status"] == "sending"

    @pytest.mark.asyncio
    async def test_pause_campaign(self, mock_user, mock_redis):
        """Testa pausa de campanha."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "status": "sending",
            }
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import pause_campaign

            result = await pause_campaign("camp-123", mock_user)

            assert result["status"] == "paused"

    @pytest.mark.asyncio
    async def test_pause_campaign_not_sending(self, mock_user, mock_redis):
        """Testa pausa de campanha não em envio."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "status": "draft",
            }
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import pause_campaign
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await pause_campaign("camp-123", mock_user)

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_resume_campaign(self, mock_user, mock_redis):
        """Testa retomada de campanha."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "status": "paused",
            }
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import resume_campaign
            from fastapi import BackgroundTasks

            background_tasks = BackgroundTasks()
            result = await resume_campaign("camp-123", background_tasks, mock_user)

            assert result["status"] == "resumed"

    @pytest.mark.asyncio
    async def test_resume_campaign_not_paused(self, mock_user, mock_redis):
        """Testa retomada de campanha não pausada."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "status": "sending",
            }
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import resume_campaign
            from fastapi import BackgroundTasks, HTTPException

            background_tasks = BackgroundTasks()

            with pytest.raises(HTTPException) as exc_info:
                await resume_campaign("camp-123", background_tasks, mock_user)

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_duplicate_campaign(self, mock_user, mock_redis):
        """Testa duplicação de campanha."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "camp-123",
                "user_id": "user-123",
                "name": "Original Campaign",
                "subject": "Subject",
                "preview_text": "",
                "html_content": "<h1>Test</h1>",
                "text_content": "",
                "list_ids": '["list-1"]',
                "type": "regular",
                "trigger": "immediate",
                "track_opens": "1",
                "track_clicks": "1",
                "status": "sent",
                "recipients_count": "100",
                "created_at": "2025-01-10T10:00:00",
                "updated_at": "2025-01-10T10:00:00",
            }
        )
        mock_redis.scard = AsyncMock(return_value=100)

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import duplicate_campaign

            result = await duplicate_campaign("camp-123", mock_user)

            assert "(Cópia)" in result.name

    @pytest.mark.asyncio
    async def test_get_campaign_stats_endpoint(self, mock_user, mock_redis):
        """Testa endpoint de estatísticas."""
        mock_redis.hgetall = AsyncMock(
            side_effect=[
                {"id": "camp-123", "user_id": "user-123"},
                {
                    "total_recipients": "1000",
                    "total_sent": "1000",
                    "total_delivered": "950",
                    "total_opened": "400",
                    "unique_opens": "300",
                    "total_clicked": "100",
                    "unique_clicks": "80",
                    "total_bounced": "30",
                    "total_unsubscribed": "5",
                    "total_complained": "2",
                    "top_links": "[]",
                    "device_breakdown": "{}",
                    "location_breakdown": "{}",
                },
            ]
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import get_campaign_stats

            result = await get_campaign_stats("camp-123", mock_user)

            assert result.total_sent == 1000


# ==================== AUTOMATION TESTS ====================


class TestAutomationEndpoints:
    """Testes dos endpoints de automações."""

    @pytest.mark.asyncio
    async def test_create_automation(
        self, mock_user, mock_redis, automation_create_data
    ):
        """Testa criação de automação."""
        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import create_automation, AutomationCreate

            data = AutomationCreate(**automation_create_data)
            result = await create_automation(data, mock_user)

            assert result.name == automation_create_data["name"]
            assert result.trigger_event == "signup"
            assert result.emails_count == 2

    @pytest.mark.asyncio
    async def test_list_automations(self, mock_user, mock_redis):
        """Testa listagem de automações."""
        mock_redis.smembers = AsyncMock(return_value={"auto-1"})
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "auto-1",
                "user_id": "user-123",
                "name": "Welcome",
                "trigger_event": "signup",
                "trigger_conditions": "",
                "delay_minutes": "0",
                "emails": '[{"subject": "Welcome!"}]',
                "active": "1",
                "total_triggered": "50",
                "total_completed": "45",
                "created_at": "2025-01-10T10:00:00",
            }
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import list_automations

            result = await list_automations(mock_user)

            assert len(result) == 1
            assert result[0].name == "Welcome"

    @pytest.mark.asyncio
    async def test_toggle_automation_activate(self, mock_user, mock_redis):
        """Testa ativação de automação."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "auto-1",
                "user_id": "user-123",
                "active": "0",
            }
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import toggle_automation

            result = await toggle_automation("auto-1", mock_user)

            assert result["active"] is True
            mock_redis.sadd.assert_called()

    @pytest.mark.asyncio
    async def test_toggle_automation_deactivate(self, mock_user, mock_redis):
        """Testa desativação de automação."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "auto-1",
                "user_id": "user-123",
                "active": "1",
            }
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import toggle_automation

            result = await toggle_automation("auto-1", mock_user)

            assert result["active"] is False
            mock_redis.srem.assert_called()

    @pytest.mark.asyncio
    async def test_toggle_automation_not_found(self, mock_user, mock_redis):
        """Testa toggle de automação não encontrada."""
        mock_redis.hgetall = AsyncMock(return_value={})

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import toggle_automation
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await toggle_automation("auto-999", mock_user)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_automation(self, mock_user, mock_redis):
        """Testa remoção de automação."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "auto-1",
                "user_id": "user-123",
            }
        )

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import delete_automation

            result = await delete_automation("auto-1", mock_user)

            assert result["status"] == "deleted"
            mock_redis.delete.assert_called()

    @pytest.mark.asyncio
    async def test_delete_automation_not_found(self, mock_user, mock_redis):
        """Testa remoção de automação não encontrada."""
        mock_redis.hgetall = AsyncMock(return_value={})

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import delete_automation
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await delete_automation("auto-999", mock_user)

            assert exc_info.value.status_code == 404


# ==================== SCHEMA TESTS ====================


class TestSchemas:
    """Testes dos schemas."""

    def test_campaign_status_enum(self):
        """Testa enum de status."""
        from api.routes.campaigns import CampaignStatus

        assert CampaignStatus.DRAFT == "draft"
        assert CampaignStatus.SENT == "sent"
        assert CampaignStatus.SENDING == "sending"

    def test_campaign_type_enum(self):
        """Testa enum de tipo."""
        from api.routes.campaigns import CampaignType

        assert CampaignType.REGULAR == "regular"
        assert CampaignType.AB_TEST == "ab_test"

    def test_trigger_type_enum(self):
        """Testa enum de trigger."""
        from api.routes.campaigns import TriggerType

        assert TriggerType.IMMEDIATE == "immediate"
        assert TriggerType.SCHEDULED == "scheduled"

    def test_campaign_create_schema(self):
        """Testa schema de criação."""
        from api.routes.campaigns import CampaignCreate

        campaign = CampaignCreate(
            name="Test",
            subject="Subject",
            list_ids=["list-1"],
        )
        assert campaign.name == "Test"
        assert campaign.track_opens is True

    def test_automation_create_schema(self):
        """Testa schema de automação."""
        from api.routes.campaigns import AutomationCreate

        automation = AutomationCreate(
            name="Welcome",
            trigger_event="signup",
            emails=[{"subject": "Welcome!"}],
        )
        assert automation.name == "Welcome"
        assert automation.active is True


# ==================== EDGE CASES ====================


class TestEdgeCases:
    """Testes de casos extremos."""

    @pytest.mark.asyncio
    async def test_create_campaign_with_ab_test(self, mock_redis, campaign_create_data):
        """Testa criação com A/B test."""
        campaign_create_data["ab_test"] = {
            "variants": [
                {"id": "A", "subject": "Subject A"},
                {"id": "B", "subject": "Subject B"},
            ],
            "split_percentage": 50,
        }

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService, CampaignCreate

            service = CampaignService()
            data = CampaignCreate(**campaign_create_data)

            result = await service.create_campaign("user-123", data)

            assert result is not None

    @pytest.mark.asyncio
    async def test_create_campaign_with_segment(self, mock_redis, campaign_create_data):
        """Testa criação com segmentação."""
        campaign_create_data["segment_rules"] = {
            "conditions": [
                {"field": "tags", "operator": "contains", "value": "premium"}
            ]
        }

        with patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import CampaignService, CampaignCreate

            service = CampaignService()
            data = CampaignCreate(**campaign_create_data)

            result = await service.create_campaign("user-123", data)

            assert result is not None

    @pytest.mark.asyncio
    async def test_empty_campaign_list(self, mock_user, mock_redis):
        """Testa listagem vazia."""
        mock_redis.smembers = AsyncMock(return_value=set())

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import list_campaigns

            result = await list_campaigns(None, 1, 20, mock_user)

            assert result == []

    @pytest.mark.asyncio
    async def test_automation_with_conditions(
        self, mock_user, mock_redis, automation_create_data
    ):
        """Testa automação com condições."""
        automation_create_data["trigger_conditions"] = {
            "product_id": "prod-123",
            "min_value": 100,
        }

        with patch("api.routes.campaigns.get_current_user", return_value=mock_user), \
             patch("api.routes.campaigns.get_redis", return_value=mock_redis):
            from api.routes.campaigns import create_automation, AutomationCreate

            data = AutomationCreate(**automation_create_data)
            result = await create_automation(data, mock_user)

            assert result.trigger_conditions is not None
