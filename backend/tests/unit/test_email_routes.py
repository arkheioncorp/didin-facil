"""
Tests for api/routes/email.py
Email marketing routes testing
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi import HTTPException

from api.routes.email import (
    router,
    EmailProviderEnum,
    EmailRecipient,
    SendEmailRequest,
    SendEmailResponse,
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailStatsResponse,
    ContactCreate,
    ContactResponse,
    ContactListCreate,
    ContactListResponse,
    EmailService,
)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    return {
        "id": "user-123",
        "email": "admin@example.com",
        "name": "Admin User",
    }


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    return redis


@pytest.fixture
def send_email_request():
    """Sample send email request."""
    return SendEmailRequest(
        to=[
            EmailRecipient(email="user1@example.com", name="User One"),
            EmailRecipient(email="user2@example.com", name="User Two"),
        ],
        subject="Test Email Subject",
        html="<h1>Hello!</h1><p>This is a test email.</p>",
        text="Hello! This is a test email."
    )


@pytest.fixture
def email_template_create():
    """Sample email template creation request."""
    return EmailTemplateCreate(
        name="Welcome Email",
        subject="Welcome to Didin Fácil, {{name}}!",
        html_content="<h1>Welcome, {{name}}!</h1><p>Thanks for signing up.</p>",
        text_content="Welcome, {{name}}! Thanks for signing up.",
        variables=["name"],
        category="onboarding"
    )


@pytest.fixture
def contact_create():
    """Sample contact creation request."""
    return ContactCreate(
        email="contact@example.com",
        name="New Contact",
        phone="+5511999999999",
        tags=["lead", "interested"],
        custom_fields={"source": "website"},
        subscribed=True
    )


@pytest.fixture
def contact_list_create():
    """Sample contact list creation request."""
    return ContactListCreate(
        name="Newsletter Subscribers",
        description="Users subscribed to our weekly newsletter"
    )


# ==================== EMAIL RECIPIENT TESTS ====================

class TestEmailRecipient:
    """Tests for EmailRecipient model."""

    def test_email_recipient_with_name(self):
        """Test creating recipient with name."""
        recipient = EmailRecipient(
            email="test@example.com",
            name="Test User"
        )
        assert recipient.email == "test@example.com"
        assert recipient.name == "Test User"

    def test_email_recipient_without_name(self):
        """Test creating recipient without name."""
        recipient = EmailRecipient(email="test@example.com")
        assert recipient.email == "test@example.com"
        assert recipient.name is None


# ==================== SEND EMAIL REQUEST TESTS ====================

class TestSendEmailRequest:
    """Tests for SendEmailRequest model."""

    def test_send_email_request_minimal(self):
        """Test minimal send email request."""
        request = SendEmailRequest(
            to=[EmailRecipient(email="user@example.com")],
            subject="Test Subject"
        )
        assert len(request.to) == 1
        assert request.html is None
        assert request.template_id is None

    def test_send_email_request_with_template(self):
        """Test send email request with template."""
        request = SendEmailRequest(
            to=[EmailRecipient(email="user@example.com")],
            subject="Template Email",
            template_id="tmpl-123",
            template_data={"name": "John", "product": "Widget"}
        )
        assert request.template_id == "tmpl-123"
        assert request.template_data["name"] == "John"

    def test_send_email_request_with_cc_bcc(self):
        """Test send email request with CC and BCC."""
        request = SendEmailRequest(
            to=[EmailRecipient(email="main@example.com")],
            subject="CC/BCC Test",
            cc=[EmailRecipient(email="cc@example.com")],
            bcc=[EmailRecipient(email="bcc@example.com")]
        )
        assert len(request.cc) == 1
        assert len(request.bcc) == 1

    def test_send_email_request_with_schedule(self):
        """Test send email request with scheduling."""
        schedule_time = datetime.now(timezone.utc)
        request = SendEmailRequest(
            to=[EmailRecipient(email="user@example.com")],
            subject="Scheduled Email",
            schedule_at=schedule_time
        )
        assert request.schedule_at == schedule_time

    def test_send_email_request_with_reply_to(self):
        """Test send email request with reply-to."""
        request = SendEmailRequest(
            to=[EmailRecipient(email="user@example.com")],
            subject="Reply Test",
            reply_to=EmailRecipient(email="reply@example.com", name="Support")
        )
        assert request.reply_to.email == "reply@example.com"

    def test_send_email_request_with_tags(self):
        """Test send email request with tags."""
        request = SendEmailRequest(
            to=[EmailRecipient(email="user@example.com")],
            subject="Tagged Email",
            tags=["marketing", "newsletter", "promo"]
        )
        assert len(request.tags) == 3
        assert "marketing" in request.tags


# ==================== SEND EMAIL RESPONSE TESTS ====================

class TestSendEmailResponse:
    """Tests for SendEmailResponse model."""

    def test_send_email_response_success(self):
        """Test successful send email response."""
        response = SendEmailResponse(
            success=True,
            message_id="msg-123456",
            status="sent",
            recipients_count=5
        )
        assert response.success is True
        assert response.message_id == "msg-123456"
        assert response.error is None

    def test_send_email_response_failure(self):
        """Test failed send email response."""
        response = SendEmailResponse(
            success=False,
            status="failed",
            recipients_count=0,
            error="SMTP connection failed"
        )
        assert response.success is False
        assert response.error == "SMTP connection failed"

    def test_send_email_response_scheduled(self):
        """Test scheduled send email response."""
        schedule_time = datetime.now(timezone.utc)
        response = SendEmailResponse(
            success=True,
            status="scheduled",
            recipients_count=10,
            scheduled_at=schedule_time
        )
        assert response.status == "scheduled"
        assert response.scheduled_at == schedule_time


# ==================== EMAIL TEMPLATE TESTS ====================

class TestEmailTemplateCreate:
    """Tests for EmailTemplateCreate model."""

    def test_template_create_full(self, email_template_create):
        """Test full template creation."""
        assert email_template_create.name == "Welcome Email"
        assert "{{name}}" in email_template_create.subject
        assert email_template_create.category == "onboarding"

    def test_template_create_minimal(self):
        """Test minimal template creation."""
        template = EmailTemplateCreate(
            name="Simple Template",
            subject="Simple Subject",
            html_content="<p>Content</p>"
        )
        assert template.text_content is None
        assert template.variables is None


class TestEmailTemplateResponse:
    """Tests for EmailTemplateResponse model."""

    def test_template_response(self):
        """Test template response model."""
        now = datetime.now(timezone.utc)
        response = EmailTemplateResponse(
            id="tmpl-123",
            name="Newsletter Template",
            subject="Weekly News",
            html_content="<h1>News</h1>",
            text_content="News",
            variables=["headline", "date"],
            category="newsletter",
            created_at=now,
            updated_at=now,
            usage_count=150
        )
        assert response.id == "tmpl-123"
        assert response.usage_count == 150


# ==================== EMAIL STATS TESTS ====================

class TestEmailStatsResponse:
    """Tests for EmailStatsResponse model."""

    def test_email_stats_response(self):
        """Test email stats response."""
        stats = EmailStatsResponse(
            total_sent=1000,
            total_delivered=980,
            total_opened=500,
            total_clicked=200,
            total_bounced=15,
            total_complained=5,
            open_rate=51.02,
            click_rate=20.41,
            bounce_rate=1.53,
            period="last_30_days"
        )
        assert stats.total_sent == 1000
        assert stats.open_rate == 51.02
        assert stats.period == "last_30_days"


# ==================== CONTACT TESTS ====================

class TestContactCreate:
    """Tests for ContactCreate model."""

    def test_contact_create_full(self, contact_create):
        """Test full contact creation."""
        assert contact_create.email == "contact@example.com"
        assert contact_create.subscribed is True
        assert "lead" in contact_create.tags

    def test_contact_create_minimal(self):
        """Test minimal contact creation."""
        contact = ContactCreate(email="minimal@example.com")
        assert contact.email == "minimal@example.com"
        assert contact.subscribed is True  # Default


class TestContactResponse:
    """Tests for ContactResponse model."""

    def test_contact_response(self):
        """Test contact response model."""
        now = datetime.now(timezone.utc)
        response = ContactResponse(
            id="contact-123",
            email="user@example.com",
            name="User Name",
            phone="+5511999999999",
            tags=["vip", "frequent"],
            custom_fields={"company": "Acme"},
            subscribed=True,
            created_at=now,
            last_email_sent=now,
            open_count=25,
            click_count=10
        )
        assert response.open_count == 25
        assert response.click_count == 10


# ==================== CONTACT LIST TESTS ====================

class TestContactListCreate:
    """Tests for ContactListCreate model."""

    def test_contact_list_create(self, contact_list_create):
        """Test contact list creation."""
        assert contact_list_create.name == "Newsletter Subscribers"
        assert "weekly newsletter" in contact_list_create.description


class TestContactListResponse:
    """Tests for ContactListResponse model."""

    def test_contact_list_response(self):
        """Test contact list response model."""
        now = datetime.now(timezone.utc)
        response = ContactListResponse(
            id="list-123",
            name="VIP Customers",
            description="High-value customers",
            contacts_count=500,
            created_at=now
        )
        assert response.contacts_count == 500


# ==================== EMAIL PROVIDER ENUM TESTS ====================

class TestEmailProviderEnum:
    """Tests for EmailProviderEnum."""

    def test_provider_values(self):
        """Test all provider values exist."""
        assert EmailProviderEnum.RESEND.value == "resend"
        assert EmailProviderEnum.SENDGRID.value == "sendgrid"
        assert EmailProviderEnum.MAILGUN.value == "mailgun"
        assert EmailProviderEnum.SES.value == "ses"


# ==================== EMAIL SERVICE TESTS ====================

class TestEmailService:
    """Tests for EmailService class."""

    @patch("api.routes.email.EmailConfig")
    @patch("api.routes.email.EmailClient")
    def test_service_initialization(self, mock_client_class, mock_config_class):
        """Test service initialization."""
        service = EmailService()
        mock_config_class.assert_called_once()
        mock_client_class.assert_called_once()

    @pytest.mark.asyncio
    @patch("api.routes.email.EmailClient")
    @patch("api.routes.email.EmailConfig")
    async def test_send_email_success(
        self, mock_config_class, mock_client_class, send_email_request
    ):
        """Test successful email sending."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.message_id = "msg-12345"
        mock_result.status.value = "sent"
        mock_client.send = AsyncMock(return_value=mock_result)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        service = EmailService()
        service._record_send = AsyncMock()

        response = await service.send_email("user-123", send_email_request)

        assert response.success is True
        assert response.message_id == "msg-12345"
        assert response.recipients_count == 2


# ==================== ROUTER TESTS ====================

class TestRouter:
    """Tests for router configuration."""

    def test_router_exists(self):
        """Verify router exists."""
        assert router is not None

    def test_router_has_routes(self):
        """Verify router has routes."""
        assert len(router.routes) > 0


# ==================== VALIDATION TESTS ====================

class TestValidation:
    """Tests for input validation."""

    def test_subject_max_length(self):
        """Test subject max length validation."""
        with pytest.raises(ValueError):
            SendEmailRequest(
                to=[EmailRecipient(email="user@example.com")],
                subject="x" * 201  # Exceeds 200 char limit
            )

    def test_template_name_max_length(self):
        """Test template name max length validation."""
        with pytest.raises(ValueError):
            EmailTemplateCreate(
                name="x" * 101,  # Exceeds 100 char limit
                subject="Test",
                html_content="<p>Content</p>"
            )

    def test_contact_list_name_max_length(self):
        """Test contact list name max length validation."""
        with pytest.raises(ValueError):
            ContactListCreate(
                name="x" * 101  # Exceeds 100 char limit
            )

    def test_email_validation(self):
        """Test email validation."""
        with pytest.raises(ValueError):
            EmailRecipient(email="not-an-email")
