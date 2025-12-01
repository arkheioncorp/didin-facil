"""
Testes para Email Routes
========================
Cobertura completa para api/routes/email.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import UUID

# Mock do vendor.email antes de importar
import sys

# Mock dos módulos necessários
mock_email_module = MagicMock()
mock_email_module.EmailClient = MagicMock()
mock_email_module.EmailConfig = MagicMock()
mock_email_module.EmailMessage = MagicMock()
mock_email_module.EmailAddress = MagicMock()
mock_email_module.EmailStatus = MagicMock()
mock_email_module.EmailStatus.DELIVERED = "delivered"
sys.modules["vendor.email"] = mock_email_module


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
    redis.scard = AsyncMock(return_value=0)
    redis.zadd = AsyncMock()
    redis.hincrby = AsyncMock()
    return redis


@pytest.fixture
def email_request_data():
    """Dados de request de email."""
    return {
        "to": [{"email": "test@example.com", "name": "Test User"}],
        "subject": "Test Subject",
        "html": "<h1>Test</h1>",
        "text": "Test",
    }


@pytest.fixture
def template_data():
    """Dados de template."""
    return {
        "name": "Welcome Template",
        "subject": "Welcome!",
        "html_content": "<h1>Welcome {{name}}</h1>",
        "text_content": "Welcome {{name}}",
        "variables": ["name"],
        "category": "onboarding",
    }


@pytest.fixture
def contact_list_data():
    """Dados de lista de contatos."""
    return {
        "name": "Newsletter",
        "description": "Main newsletter list",
    }


@pytest.fixture
def contact_data():
    """Dados de contato."""
    return {
        "email": "contact@example.com",
        "name": "Contact Name",
        "phone": "+5511999999999",
        "tags": ["lead", "premium"],
        "custom_fields": {"company": "Acme"},
        "subscribed": True,
    }


# ==================== EMAIL SERVICE TESTS ====================


class TestEmailService:
    """Testes do EmailService."""

    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_redis):
        """Testa envio de email com sucesso."""
        with patch("api.routes.email.get_redis", return_value=mock_redis):
            from api.routes.email import EmailService, SendEmailRequest

            service = EmailService()

            # Mock do client
            mock_result = MagicMock()
            mock_result.message_id = "msg-123"
            mock_result.status = MagicMock()
            mock_result.status.value = "sent"

            mock_client = AsyncMock()
            mock_client.send = AsyncMock(return_value=mock_result)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            service.client = mock_client

            request = SendEmailRequest(
                to=[{"email": "test@example.com", "name": "Test"}],
                subject="Test",
                html="<h1>Test</h1>",
            )

            with patch.object(service, "_record_send", new_callable=AsyncMock):
                result = await service.send_email("user-123", request)

            assert result.success is True
            assert result.message_id == "msg-123"
            assert result.recipients_count == 1

    @pytest.mark.asyncio
    async def test_send_email_with_template(self, mock_redis):
        """Testa envio com template."""
        template_data = {
            "html_content": "<h1>Hello {{name}}</h1>",
            "text_content": "Hello {{name}}",
        }
        mock_redis.hgetall = AsyncMock(return_value=template_data)

        with patch("api.routes.email.get_redis", return_value=mock_redis):
            from api.routes.email import EmailService, SendEmailRequest

            service = EmailService()

            mock_result = MagicMock()
            mock_result.message_id = "msg-456"
            mock_result.status = MagicMock()
            mock_result.status.value = "sent"

            mock_client = AsyncMock()
            mock_client.send = AsyncMock(return_value=mock_result)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            service.client = mock_client

            request = SendEmailRequest(
                to=[{"email": "test@example.com"}],
                subject="Test",
                template_id="template-123",
                template_data={"name": "John"},
            )

            with patch.object(service, "_record_send", new_callable=AsyncMock):
                result = await service.send_email("user-123", request)

            assert result.success is True

    @pytest.mark.asyncio
    async def test_send_email_scheduled(self, mock_redis):
        """Testa agendamento de email."""
        with patch("api.routes.email.get_redis", return_value=mock_redis):
            from api.routes.email import EmailService, SendEmailRequest

            service = EmailService()

            schedule_time = datetime(2025, 1, 15, 10, 0, 0)
            request = SendEmailRequest(
                to=[{"email": "test@example.com"}],
                subject="Test",
                html="<h1>Test</h1>",
                schedule_at=schedule_time,
            )

            result = await service.send_email("user-123", request)

            assert result.success is True
            assert result.status == "scheduled"
            assert result.scheduled_at == schedule_time

    @pytest.mark.asyncio
    async def test_send_email_failure(self, mock_redis):
        """Testa falha no envio."""
        with patch("api.routes.email.get_redis", return_value=mock_redis):
            from api.routes.email import EmailService, SendEmailRequest

            service = EmailService()

            mock_client = AsyncMock()
            mock_client.send = AsyncMock(side_effect=Exception("SMTP error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            service.client = mock_client

            request = SendEmailRequest(
                to=[{"email": "test@example.com"}],
                subject="Test",
                html="<h1>Test</h1>",
            )

            result = await service.send_email("user-123", request)

            assert result.success is False
            assert result.status == "failed"
            # O erro pode conter "SMTP error" ou outra msg do exception
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_render_template(self, mock_redis):
        """Testa renderização de template."""
        with patch("api.routes.email.get_redis", return_value=mock_redis):
            from api.routes.email import EmailService

            service = EmailService()

            template = "<h1>Hello {{name}}</h1>"
            data = {"name": "John"}

            result = service._render_template(template, data)

            assert result == "<h1>Hello John</h1>"


# ==================== SEND EMAIL ENDPOINT TESTS ====================


class TestSendEmailEndpoint:
    """Testes do endpoint de envio de email."""

    @pytest.mark.asyncio
    async def test_send_email_endpoint_success(self, mock_user, mock_redis, email_request_data):
        """Testa endpoint de envio com sucesso."""
        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis), \
             patch("api.routes.email.email_service") as mock_service:

            from api.routes.email import send_email, SendEmailRequest, SendEmailResponse
            from fastapi import BackgroundTasks

            mock_response = SendEmailResponse(
                success=True,
                message_id="msg-123",
                status="sent",
                recipients_count=1,
            )
            mock_service.send_email = AsyncMock(return_value=mock_response)

            request = SendEmailRequest(**email_request_data)
            background_tasks = BackgroundTasks()

            result = await send_email(request, background_tasks, mock_user)

            assert result.success is True
            assert result.message_id == "msg-123"

    @pytest.mark.asyncio
    async def test_send_email_endpoint_failure(self, mock_user, mock_redis, email_request_data):
        """Testa endpoint de envio com falha."""
        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis), \
             patch("api.routes.email.email_service") as mock_service:

            from api.routes.email import send_email, SendEmailRequest, SendEmailResponse
            from fastapi import BackgroundTasks, HTTPException

            mock_response = SendEmailResponse(
                success=False,
                status="failed",
                recipients_count=1,
                error="SMTP error",
            )
            mock_service.send_email = AsyncMock(return_value=mock_response)

            request = SendEmailRequest(**email_request_data)
            background_tasks = BackgroundTasks()

            with pytest.raises(HTTPException) as exc_info:
                await send_email(request, background_tasks, mock_user)

            assert exc_info.value.status_code == 500


class TestSendBatchEmails:
    """Testes do endpoint de envio em batch."""

    @pytest.mark.asyncio
    async def test_send_batch_success(self, mock_user, mock_redis):
        """Testa envio em batch com sucesso."""
        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis), \
             patch("api.routes.email.email_service") as mock_service:

            from api.routes.email import send_batch_emails, SendEmailRequest, SendEmailResponse
            from fastapi import BackgroundTasks

            mock_response = SendEmailResponse(
                success=True,
                message_id="msg-123",
                status="sent",
                recipients_count=1,
            )
            mock_service.send_email = AsyncMock(return_value=mock_response)

            emails = [
                SendEmailRequest(
                    to=[{"email": f"test{i}@example.com"}],
                    subject=f"Test {i}",
                    html=f"<h1>Test {i}</h1>",
                )
                for i in range(3)
            ]

            background_tasks = BackgroundTasks()
            result = await send_batch_emails(emails, background_tasks, mock_user)

            assert result["total"] == 3
            assert result["success"] == 3
            assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_send_batch_limit_exceeded(self, mock_user, mock_redis):
        """Testa limite de batch excedido."""
        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import send_batch_emails, SendEmailRequest
            from fastapi import BackgroundTasks, HTTPException

            emails = [
                SendEmailRequest(
                    to=[{"email": f"test{i}@example.com"}],
                    subject=f"Test {i}",
                    html=f"<h1>Test {i}</h1>",
                )
                for i in range(101)
            ]

            background_tasks = BackgroundTasks()

            with pytest.raises(HTTPException) as exc_info:
                await send_batch_emails(emails, background_tasks, mock_user)

            assert exc_info.value.status_code == 400
            assert "100 emails" in exc_info.value.detail


# ==================== TEMPLATE TESTS ====================


class TestTemplateEndpoints:
    """Testes dos endpoints de templates."""

    @pytest.mark.asyncio
    async def test_create_template(self, mock_user, mock_redis, template_data):
        """Testa criação de template."""
        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import create_template, EmailTemplateCreate

            template = EmailTemplateCreate(**template_data)
            result = await create_template(template, mock_user)

            assert result.name == template_data["name"]
            assert result.subject == template_data["subject"]
            assert result.html_content == template_data["html_content"]
            assert "name" in result.variables
            mock_redis.hset.assert_called_once()
            mock_redis.sadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_templates(self, mock_user, mock_redis):
        """Testa listagem de templates."""
        mock_redis.smembers = AsyncMock(return_value={"tmpl-1", "tmpl-2"})
        mock_redis.hgetall = AsyncMock(
            side_effect=[
                {
                    "id": "tmpl-1",
                    "name": "Template 1",
                    "subject": "Subject 1",
                    "html_content": "<h1>Test 1</h1>",
                    "variables": "name,email",
                    "category": "marketing",
                    "created_at": "2025-01-10T10:00:00",
                    "updated_at": "2025-01-10T10:00:00",
                    "usage_count": "5",
                },
                {
                    "id": "tmpl-2",
                    "name": "Template 2",
                    "subject": "Subject 2",
                    "html_content": "<h1>Test 2</h1>",
                    "variables": "",
                    "category": "transactional",
                    "created_at": "2025-01-10T11:00:00",
                    "updated_at": "2025-01-10T11:00:00",
                    "usage_count": "10",
                },
            ]
        )

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import list_templates

            result = await list_templates(None, mock_user)

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_templates_with_category_filter(self, mock_user, mock_redis):
        """Testa listagem com filtro de categoria."""
        mock_redis.smembers = AsyncMock(return_value={"tmpl-1"})
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "tmpl-1",
                "name": "Template 1",
                "subject": "Subject 1",
                "html_content": "<h1>Test 1</h1>",
                "variables": "",
                "category": "marketing",
                "created_at": "2025-01-10T10:00:00",
                "updated_at": "2025-01-10T10:00:00",
                "usage_count": "5",
            }
        )

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import list_templates

            # Filtro matching
            result = await list_templates("marketing", mock_user)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_template_success(self, mock_user, mock_redis):
        """Testa busca de template por ID."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "tmpl-1",
                "name": "Template 1",
                "subject": "Subject 1",
                "html_content": "<h1>Test 1</h1>",
                "variables": "name",
                "category": "marketing",
                "created_at": "2025-01-10T10:00:00",
                "updated_at": "2025-01-10T10:00:00",
                "usage_count": "5",
                "user_id": "user-123",
            }
        )

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import get_template

            result = await get_template("tmpl-1", mock_user)

            assert result.id == "tmpl-1"
            assert result.name == "Template 1"

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, mock_user, mock_redis):
        """Testa busca de template não encontrado."""
        mock_redis.hgetall = AsyncMock(return_value={})

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import get_template
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await get_template("tmpl-999", mock_user)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_template_wrong_user(self, mock_user, mock_redis):
        """Testa acesso a template de outro usuário."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "tmpl-1",
                "user_id": "other-user",
            }
        )

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import get_template
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await get_template("tmpl-1", mock_user)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_template_success(self, mock_user, mock_redis):
        """Testa remoção de template."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "tmpl-1",
                "user_id": "user-123",
            }
        )

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import delete_template

            result = await delete_template("tmpl-1", mock_user)

            assert result["status"] == "deleted"
            assert result["template_id"] == "tmpl-1"
            mock_redis.delete.assert_called_once()
            mock_redis.srem.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_template_not_found(self, mock_user, mock_redis):
        """Testa remoção de template não encontrado."""
        mock_redis.hgetall = AsyncMock(return_value={})

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import delete_template
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await delete_template("tmpl-999", mock_user)

            assert exc_info.value.status_code == 404


# ==================== CONTACT LIST TESTS ====================


class TestContactListEndpoints:
    """Testes dos endpoints de listas de contatos."""

    @pytest.mark.asyncio
    async def test_create_contact_list(self, mock_user, mock_redis, contact_list_data):
        """Testa criação de lista de contatos."""
        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import create_contact_list, ContactListCreate

            data = ContactListCreate(**contact_list_data)
            result = await create_contact_list(data, mock_user)

            assert result.name == contact_list_data["name"]
            assert result.description == contact_list_data["description"]
            assert result.contacts_count == 0
            mock_redis.hset.assert_called_once()
            mock_redis.sadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_contact_lists(self, mock_user, mock_redis):
        """Testa listagem de listas de contatos."""
        mock_redis.smembers = AsyncMock(return_value={"list-1", "list-2"})
        mock_redis.hgetall = AsyncMock(
            side_effect=[
                {
                    "id": "list-1",
                    "name": "Newsletter",
                    "description": "Main newsletter",
                    "created_at": "2025-01-10T10:00:00",
                },
                {
                    "id": "list-2",
                    "name": "Leads",
                    "description": "Lead list",
                    "created_at": "2025-01-10T11:00:00",
                },
            ]
        )
        mock_redis.scard = AsyncMock(side_effect=[100, 50])

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import list_contact_lists

            result = await list_contact_lists(mock_user)

            assert len(result) == 2
            assert result[0].contacts_count == 100
            assert result[1].contacts_count == 50


# ==================== CONTACT TESTS ====================


class TestContactEndpoints:
    """Testes dos endpoints de contatos."""

    @pytest.mark.asyncio
    async def test_add_contact_to_list(self, mock_user, mock_redis, contact_data):
        """Testa adição de contato à lista."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "list-1",
                "user_id": "user-123",
            }
        )

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import add_contact_to_list, ContactCreate

            contact = ContactCreate(**contact_data)
            result = await add_contact_to_list("list-1", contact, mock_user)

            assert result.email == contact_data["email"]
            assert result.name == contact_data["name"]
            assert result.subscribed is True
            mock_redis.hset.assert_called_once()
            mock_redis.sadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_contact_list_not_found(self, mock_user, mock_redis, contact_data):
        """Testa adição de contato a lista inexistente."""
        mock_redis.hgetall = AsyncMock(return_value={})

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import add_contact_to_list, ContactCreate
            from fastapi import HTTPException

            contact = ContactCreate(**contact_data)

            with pytest.raises(HTTPException) as exc_info:
                await add_contact_to_list("list-999", contact, mock_user)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_add_contact_wrong_user(self, mock_user, mock_redis, contact_data):
        """Testa adição de contato a lista de outro usuário."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "list-1",
                "user_id": "other-user",
            }
        )

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import add_contact_to_list, ContactCreate
            from fastapi import HTTPException

            contact = ContactCreate(**contact_data)

            with pytest.raises(HTTPException) as exc_info:
                await add_contact_to_list("list-1", contact, mock_user)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_contacts(self, mock_user, mock_redis):
        """Testa listagem de contatos."""
        mock_redis.hgetall = AsyncMock(
            side_effect=[
                # Primeiro: dados da lista
                {"id": "list-1", "user_id": "user-123"},
                # Depois: dados dos contatos
                {
                    "id": "contact-1",
                    "email": "test1@example.com",
                    "name": "Test 1",
                    "phone": "",
                    "tags": "lead,premium",
                    "custom_fields": "{}",
                    "subscribed": "1",
                    "created_at": "2025-01-10T10:00:00",
                    "open_count": "5",
                    "click_count": "2",
                },
                {
                    "id": "contact-2",
                    "email": "test2@example.com",
                    "name": "",
                    "phone": "",
                    "tags": "",
                    "custom_fields": "{}",
                    "subscribed": "0",
                    "created_at": "2025-01-10T11:00:00",
                    "open_count": "0",
                    "click_count": "0",
                },
            ]
        )
        mock_redis.smembers = AsyncMock(return_value={"contact-1", "contact-2"})

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import list_contacts

            result = await list_contacts("list-1", 1, 50, mock_user)

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_contacts_list_not_found(self, mock_user, mock_redis):
        """Testa listagem de contatos de lista inexistente."""
        mock_redis.hgetall = AsyncMock(return_value={})

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import list_contacts
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await list_contacts("list-999", 1, 50, mock_user)

            assert exc_info.value.status_code == 404


# ==================== STATISTICS TESTS ====================


class TestStatisticsEndpoints:
    """Testes dos endpoints de estatísticas."""

    @pytest.mark.asyncio
    async def test_get_email_stats(self, mock_user, mock_redis):
        """Testa obtenção de estatísticas."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "sent": "100",
                "delivered": "95",
                "opened": "50",
                "clicked": "20",
                "bounced": "3",
                "complained": "1",
            }
        )

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import get_email_stats

            result = await get_email_stats("7d", mock_user)

            assert result.total_sent > 0
            assert result.total_delivered > 0
            assert result.period == "7d"
            assert result.open_rate >= 0
            assert result.click_rate >= 0
            assert result.bounce_rate >= 0

    @pytest.mark.asyncio
    async def test_get_email_stats_no_data(self, mock_user, mock_redis):
        """Testa estatísticas sem dados."""
        mock_redis.hgetall = AsyncMock(return_value={})

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import get_email_stats

            result = await get_email_stats("1d", mock_user)

            assert result.total_sent == 0
            assert result.open_rate == 0
            assert result.click_rate == 0
            assert result.bounce_rate == 0

    @pytest.mark.asyncio
    async def test_get_email_stats_different_periods(self, mock_user, mock_redis):
        """Testa diferentes períodos de estatísticas."""
        mock_redis.hgetall = AsyncMock(return_value={"sent": "10", "delivered": "10"})

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import get_email_stats

            for period in ["1d", "7d", "30d", "90d"]:
                result = await get_email_stats(period, mock_user)
                assert result.period == period


# ==================== WEBHOOK TESTS ====================


class TestWebhookEndpoints:
    """Testes dos endpoints de webhooks."""

    @pytest.mark.asyncio
    async def test_resend_webhook(self, mock_redis):
        """Testa webhook do Resend."""
        with patch("api.routes.email.get_redis", return_value=mock_redis):
            from api.routes.email import handle_email_webhook, EmailProviderEnum

            payload = {
                "type": "email.delivered",
                "data": {"email": "test@example.com"},
            }

            result = await handle_email_webhook(EmailProviderEnum.RESEND, payload)

            assert result["status"] == "received"
            mock_redis.hincrby.assert_called()

    @pytest.mark.asyncio
    async def test_sendgrid_webhook(self, mock_redis):
        """Testa webhook do SendGrid."""
        with patch("api.routes.email.get_redis", return_value=mock_redis):
            from api.routes.email import handle_email_webhook, EmailProviderEnum

            payload = [
                {"event": "delivered", "email": "test@example.com"},
                {"event": "open", "email": "test@example.com"},
            ]

            result = await handle_email_webhook(EmailProviderEnum.SENDGRID, payload)

            assert result["status"] == "received"

    @pytest.mark.asyncio
    async def test_sendgrid_webhook_single_event(self, mock_redis):
        """Testa webhook do SendGrid com evento único."""
        with patch("api.routes.email.get_redis", return_value=mock_redis):
            from api.routes.email import handle_email_webhook, EmailProviderEnum

            payload = {"event": "click", "email": "test@example.com"}

            result = await handle_email_webhook(EmailProviderEnum.SENDGRID, payload)

            assert result["status"] == "received"

    @pytest.mark.asyncio
    async def test_webhook_bounce_event(self, mock_redis):
        """Testa processamento de evento de bounce."""
        with patch("api.routes.email.get_redis", return_value=mock_redis):
            from api.routes.email import handle_email_webhook, EmailProviderEnum

            payload = {"event": "bounce", "email": "invalid@example.com"}

            result = await handle_email_webhook(EmailProviderEnum.SENDGRID, payload)

            assert result["status"] == "received"

    @pytest.mark.asyncio
    async def test_webhook_spamreport_event(self, mock_redis):
        """Testa processamento de evento de spam."""
        with patch("api.routes.email.get_redis", return_value=mock_redis):
            from api.routes.email import handle_email_webhook, EmailProviderEnum

            payload = {"event": "spamreport", "email": "complainer@example.com"}

            result = await handle_email_webhook(EmailProviderEnum.SENDGRID, payload)

            assert result["status"] == "received"

    @pytest.mark.asyncio
    async def test_webhook_unknown_event(self, mock_redis):
        """Testa evento desconhecido."""
        with patch("api.routes.email.get_redis", return_value=mock_redis):
            from api.routes.email import handle_email_webhook, EmailProviderEnum

            payload = {"event": "unknown_event", "email": "test@example.com"}

            result = await handle_email_webhook(EmailProviderEnum.SENDGRID, payload)

            assert result["status"] == "received"


# ==================== SCHEMA TESTS ====================


class TestSchemas:
    """Testes dos schemas."""

    def test_email_recipient_schema(self):
        """Testa schema de destinatário."""
        from api.routes.email import EmailRecipient

        recipient = EmailRecipient(email="test@example.com", name="Test")
        assert recipient.email == "test@example.com"
        assert recipient.name == "Test"

        recipient_no_name = EmailRecipient(email="test@example.com")
        assert recipient_no_name.name is None

    def test_send_email_request_schema(self):
        """Testa schema de request de envio."""
        from api.routes.email import SendEmailRequest

        request = SendEmailRequest(
            to=[{"email": "test@example.com"}],
            subject="Test Subject",
            html="<h1>Test</h1>",
        )
        assert len(request.to) == 1
        assert request.subject == "Test Subject"

    def test_email_template_create_schema(self):
        """Testa schema de criação de template."""
        from api.routes.email import EmailTemplateCreate

        template = EmailTemplateCreate(
            name="Welcome",
            subject="Welcome!",
            html_content="<h1>Welcome</h1>",
            variables=["name", "company"],
        )
        assert template.name == "Welcome"
        assert "name" in template.variables

    def test_contact_create_schema(self):
        """Testa schema de criação de contato."""
        from api.routes.email import ContactCreate

        contact = ContactCreate(
            email="test@example.com",
            name="Test User",
            tags=["lead"],
            subscribed=True,
        )
        assert contact.email == "test@example.com"
        assert contact.subscribed is True

    def test_email_stats_response_schema(self):
        """Testa schema de resposta de estatísticas."""
        from api.routes.email import EmailStatsResponse

        stats = EmailStatsResponse(
            total_sent=100,
            total_delivered=95,
            total_opened=50,
            total_clicked=20,
            total_bounced=3,
            total_complained=1,
            open_rate=52.63,
            click_rate=40.0,
            bounce_rate=3.0,
            period="7d",
        )
        assert stats.total_sent == 100
        assert stats.open_rate == 52.63


# ==================== EDGE CASES ====================


class TestEdgeCases:
    """Testes de casos extremos."""

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self, mock_redis):
        """Testa envio com CC e BCC."""
        with patch("api.routes.email.get_redis", return_value=mock_redis):
            from api.routes.email import EmailService, SendEmailRequest

            service = EmailService()

            mock_result = MagicMock()
            mock_result.message_id = "msg-123"
            mock_result.status = MagicMock()
            mock_result.status.value = "sent"

            mock_client = AsyncMock()
            mock_client.send = AsyncMock(return_value=mock_result)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            service.client = mock_client

            request = SendEmailRequest(
                to=[{"email": "test@example.com"}],
                subject="Test",
                html="<h1>Test</h1>",
                cc=[{"email": "cc@example.com", "name": "CC User"}],
                bcc=[{"email": "bcc@example.com"}],
                reply_to={"email": "reply@example.com", "name": "Reply User"},
            )

            with patch.object(service, "_record_send", new_callable=AsyncMock):
                result = await service.send_email("user-123", request)

            assert result.success is True

    @pytest.mark.asyncio
    async def test_empty_template_list(self, mock_user, mock_redis):
        """Testa listagem vazia de templates."""
        mock_redis.smembers = AsyncMock(return_value=set())

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import list_templates

            result = await list_templates(None, mock_user)

            assert result == []

    @pytest.mark.asyncio
    async def test_contact_with_empty_optional_fields(self, mock_user, mock_redis):
        """Testa contato com campos opcionais vazios."""
        mock_redis.hgetall = AsyncMock(
            return_value={
                "id": "list-1",
                "user_id": "user-123",
            }
        )

        with patch("api.routes.email.get_current_user", return_value=mock_user), \
             patch("api.routes.email.get_redis", return_value=mock_redis):

            from api.routes.email import add_contact_to_list, ContactCreate

            contact = ContactCreate(
                email="minimal@example.com",
                subscribed=True,
            )
            result = await add_contact_to_list("list-1", contact, mock_user)

            assert result.email == "minimal@example.com"
            assert result.name is None
            assert result.tags == []
