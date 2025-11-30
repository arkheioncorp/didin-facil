"""
Tests for api/routes/campaigns.py
Email marketing campaigns routes testing
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from api.routes.campaigns import (
    router,
    CampaignStatus,
    CampaignType,
    TriggerType,
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignStats,
    ABTestVariant,
    AutomationCreate,
    AutomationResponse,
    CampaignService,
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
    redis.scard = AsyncMock(return_value=100)
    redis.hset = AsyncMock()
    redis.sadd = AsyncMock()
    redis.hgetall = AsyncMock(return_value={})
    return redis


@pytest.fixture
def campaign_create():
    """Sample campaign creation request."""
    return CampaignCreate(
        name="Summer Sale Campaign",
        subject="🔥 Summer Sale - Up to 50% Off!",
        preview_text="Don't miss our biggest sale of the year",
        list_ids=["list-1", "list-2"],
        type=CampaignType.REGULAR,
        trigger=TriggerType.SCHEDULED,
        schedule_at=datetime.now(timezone.utc) + timedelta(days=1),
        track_opens=True,
        track_clicks=True
    )


@pytest.fixture
def campaign_create_ab_test():
    """Sample A/B test campaign."""
    return CampaignCreate(
        name="A/B Test Campaign",
        subject="Test Subject A",
        list_ids=["list-1"],
        type=CampaignType.AB_TEST,
        ab_test={
            "variants": [
                {"name": "Variant A", "subject": "Subject A", "percentage": 50},
                {"name": "Variant B", "subject": "Subject B", "percentage": 50}
            ],
            "split_percentage": 50
        }
    )


@pytest.fixture
def automation_create():
    """Sample automation creation request."""
    return AutomationCreate(
        name="Welcome Series",
        description="Onboarding email sequence for new users",
        trigger_event="signup",
        delay_minutes=0,
        emails=[
            {"subject": "Welcome!", "delay_days": 0},
            {"subject": "Getting Started", "delay_days": 1},
            {"subject": "Pro Tips", "delay_days": 3}
        ],
        active=True
    )


# ==================== ENUM TESTS ====================

class TestEnums:
    """Tests for campaign enums."""

    def test_campaign_status_values(self):
        """Test all campaign status values."""
        assert CampaignStatus.DRAFT.value == "draft"
        assert CampaignStatus.SCHEDULED.value == "scheduled"
        assert CampaignStatus.SENDING.value == "sending"
        assert CampaignStatus.SENT.value == "sent"
        assert CampaignStatus.PAUSED.value == "paused"
        assert CampaignStatus.CANCELLED.value == "cancelled"

    def test_campaign_type_values(self):
        """Test all campaign type values."""
        assert CampaignType.REGULAR.value == "regular"
        assert CampaignType.AUTOMATED.value == "automated"
        assert CampaignType.AB_TEST.value == "ab_test"
        assert CampaignType.TRANSACTIONAL.value == "transactional"

    def test_trigger_type_values(self):
        """Test all trigger type values."""
        assert TriggerType.IMMEDIATE.value == "immediate"
        assert TriggerType.SCHEDULED.value == "scheduled"
        assert TriggerType.EVENT_BASED.value == "event_based"
        assert TriggerType.RECURRING.value == "recurring"


# ==================== CAMPAIGN CREATE TESTS ====================

class TestCampaignCreate:
    """Tests for CampaignCreate model."""

    def test_campaign_create_full(self, campaign_create):
        """Test full campaign creation."""
        assert campaign_create.name == "Summer Sale Campaign"
        assert campaign_create.type == CampaignType.REGULAR
        assert campaign_create.trigger == TriggerType.SCHEDULED
        assert len(campaign_create.list_ids) == 2
        assert campaign_create.track_opens is True

    def test_campaign_create_minimal(self):
        """Test minimal campaign creation."""
        campaign = CampaignCreate(
            name="Simple Campaign",
            subject="Test Subject",
            list_ids=["list-1"]
        )
        assert campaign.type == CampaignType.REGULAR  # Default
        assert campaign.trigger == TriggerType.IMMEDIATE  # Default
        assert campaign.track_opens is True  # Default
        assert campaign.schedule_at is None

    def test_campaign_create_with_template(self):
        """Test campaign creation with template."""
        campaign = CampaignCreate(
            name="Template Campaign",
            subject="Using Template",
            list_ids=["list-1"],
            template_id="tmpl-123"
        )
        assert campaign.template_id == "tmpl-123"
        assert campaign.html_content is None

    def test_campaign_create_with_html(self):
        """Test campaign creation with HTML content."""
        campaign = CampaignCreate(
            name="HTML Campaign",
            subject="HTML Email",
            list_ids=["list-1"],
            html_content="<h1>Hello!</h1>",
            text_content="Hello!"
        )
        assert campaign.html_content == "<h1>Hello!</h1>"

    def test_campaign_create_with_segment(self):
        """Test campaign with segment rules."""
        campaign = CampaignCreate(
            name="Segmented Campaign",
            subject="For VIP Only",
            list_ids=["list-1"],
            segment_rules={
                "tags": ["vip"],
                "last_purchase": {"days_ago": 30}
            }
        )
        assert campaign.segment_rules["tags"] == ["vip"]

    def test_campaign_create_ab_test(self, campaign_create_ab_test):
        """Test A/B test campaign creation."""
        assert campaign_create_ab_test.type == CampaignType.AB_TEST
        assert len(campaign_create_ab_test.ab_test["variants"]) == 2

    def test_campaign_create_with_reply_to(self):
        """Test campaign with reply-to settings."""
        campaign = CampaignCreate(
            name="Campaign",
            subject="Test",
            list_ids=["list-1"],
            reply_to_email="support@example.com",
            reply_to_name="Support Team"
        )
        assert campaign.reply_to_email == "support@example.com"
        assert campaign.reply_to_name == "Support Team"


# ==================== CAMPAIGN UPDATE TESTS ====================

class TestCampaignUpdate:
    """Tests for CampaignUpdate model."""

    def test_campaign_update_name(self):
        """Test updating campaign name."""
        update = CampaignUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.subject is None

    def test_campaign_update_schedule(self):
        """Test updating campaign schedule."""
        new_time = datetime.now(timezone.utc) + timedelta(hours=2)
        update = CampaignUpdate(schedule_at=new_time)
        assert update.schedule_at == new_time

    def test_campaign_update_all_fields(self):
        """Test updating all fields."""
        update = CampaignUpdate(
            name="Updated Name",
            subject="Updated Subject",
            preview_text="Updated preview",
            html_content="<p>Updated</p>"
        )
        assert all([
            update.name == "Updated Name",
            update.subject == "Updated Subject",
            update.preview_text == "Updated preview",
            update.html_content == "<p>Updated</p>"
        ])


# ==================== CAMPAIGN RESPONSE TESTS ====================

class TestCampaignResponse:
    """Tests for CampaignResponse model."""

    def test_campaign_response_draft(self):
        """Test draft campaign response."""
        now = datetime.now(timezone.utc)
        response = CampaignResponse(
            id="camp-123",
            name="Draft Campaign",
            subject="Subject",
            preview_text=None,
            status=CampaignStatus.DRAFT,
            type=CampaignType.REGULAR,
            trigger=TriggerType.IMMEDIATE,
            list_ids=["list-1"],
            recipients_count=500,
            schedule_at=None,
            sent_at=None,
            created_at=now,
            updated_at=now
        )
        assert response.status == CampaignStatus.DRAFT
        assert response.sent_at is None

    def test_campaign_response_sent_with_stats(self):
        """Test sent campaign with stats."""
        now = datetime.now(timezone.utc)
        response = CampaignResponse(
            id="camp-123",
            name="Sent Campaign",
            subject="Subject",
            preview_text="Preview",
            status=CampaignStatus.SENT,
            type=CampaignType.REGULAR,
            trigger=TriggerType.IMMEDIATE,
            list_ids=["list-1"],
            recipients_count=500,
            schedule_at=None,
            sent_at=now,
            created_at=now,
            updated_at=now,
            stats={
                "sent": 500,
                "delivered": 495,
                "opened": 200,
                "clicked": 50
            }
        )
        assert response.status == CampaignStatus.SENT
        assert response.stats["opened"] == 200


# ==================== CAMPAIGN STATS TESTS ====================

class TestCampaignStats:
    """Tests for CampaignStats model."""

    def test_campaign_stats_full(self):
        """Test full campaign stats."""
        stats = CampaignStats(
            campaign_id="camp-123",
            total_recipients=1000,
            total_sent=998,
            total_delivered=985,
            total_opened=450,
            unique_opens=400,
            total_clicked=120,
            unique_clicks=100,
            total_bounced=13,
            total_unsubscribed=5,
            total_complained=2,
            delivery_rate=98.7,
            open_rate=45.0,
            click_rate=12.0,
            click_to_open_rate=26.7,
            bounce_rate=1.3,
            unsubscribe_rate=0.5,
            first_open_at=datetime.now(timezone.utc),
            last_open_at=datetime.now(timezone.utc),
            avg_open_time_seconds=3600,
            top_links=[
                {"url": "https://example.com/1", "clicks": 50},
                {"url": "https://example.com/2", "clicks": 30}
            ],
            device_breakdown={"desktop": 300, "mobile": 150},
            location_breakdown={"US": 200, "BR": 150, "UK": 50}
        )
        assert stats.open_rate == 45.0
        assert stats.click_to_open_rate == 26.7
        assert len(stats.top_links) == 2


# ==================== AB TEST VARIANT TESTS ====================

class TestABTestVariant:
    """Tests for ABTestVariant model."""

    def test_variant_defaults(self):
        """Test variant with defaults."""
        variant = ABTestVariant(
            id="var-1",
            name="Variant A"
        )
        assert variant.percentage == 50
        assert variant.sent == 0
        assert variant.winner is False

    def test_variant_with_results(self):
        """Test variant with results."""
        variant = ABTestVariant(
            id="var-1",
            name="Variant A",
            subject="Subject A",
            percentage=50,
            sent=500,
            opened=200,
            clicked=50,
            winner=True
        )
        assert variant.winner is True
        assert variant.opened == 200


# ==================== AUTOMATION TESTS ====================

class TestAutomationCreate:
    """Tests for AutomationCreate model."""

    def test_automation_create(self, automation_create):
        """Test automation creation."""
        assert automation_create.name == "Welcome Series"
        assert automation_create.trigger_event == "signup"
        assert len(automation_create.emails) == 3
        assert automation_create.active is True

    def test_automation_create_with_conditions(self):
        """Test automation with trigger conditions."""
        automation = AutomationCreate(
            name="Cart Abandonment",
            trigger_event="abandoned_cart",
            trigger_conditions={
                "cart_value": {"min": 100},
                "items_count": {"min": 1}
            },
            delay_minutes=60,
            emails=[{"subject": "Did you forget something?"}]
        )
        assert automation.trigger_conditions["cart_value"]["min"] == 100
        assert automation.delay_minutes == 60


class TestAutomationResponse:
    """Tests for AutomationResponse model."""

    def test_automation_response(self):
        """Test automation response."""
        now = datetime.now(timezone.utc)
        response = AutomationResponse(
            id="auto-123",
            name="Welcome Series",
            description="Onboarding emails",
            trigger_event="signup",
            trigger_conditions=None,
            delay_minutes=0,
            emails_count=3,
            active=True,
            total_triggered=1500,
            total_completed=1400,
            created_at=now
        )
        assert response.total_triggered == 1500
        assert response.emails_count == 3


# ==================== CAMPAIGN SERVICE TESTS ====================

class TestCampaignService:
    """Tests for CampaignService class."""

    @pytest.mark.asyncio
    @patch("api.routes.campaigns.get_redis")
    async def test_create_campaign(self, mock_get_redis, mock_redis, campaign_create):
        """Test creating a campaign."""
        mock_get_redis.return_value = mock_redis

        service = CampaignService()
        response = await service.create_campaign("user-123", campaign_create)

        assert response.name == "Summer Sale Campaign"
        assert response.status == CampaignStatus.DRAFT
        assert response.recipients_count == 200  # 2 lists * 100 each
        mock_redis.hset.assert_awaited_once()
        mock_redis.sadd.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("api.routes.campaigns.get_redis")
    async def test_get_campaign_not_found(self, mock_get_redis, mock_redis):
        """Test getting non-existent campaign."""
        mock_get_redis.return_value = mock_redis
        mock_redis.hgetall = AsyncMock(return_value={})

        service = CampaignService()
        result = await service.get_campaign("user-123", "non-existent")

        assert result is None

    @pytest.mark.asyncio
    @patch("api.routes.campaigns.get_redis")
    async def test_get_campaign_wrong_user(self, mock_get_redis, mock_redis):
        """Test getting campaign belonging to different user."""
        mock_get_redis.return_value = mock_redis
        mock_redis.hgetall = AsyncMock(return_value={
            "user_id": "other-user",
            "name": "Campaign"
        })

        service = CampaignService()
        result = await service.get_campaign("user-123", "camp-1")

        assert result is None


# ==================== VALIDATION TESTS ====================

class TestValidation:
    """Tests for input validation."""

    def test_name_max_length(self):
        """Test name max length validation."""
        with pytest.raises(ValueError):
            CampaignCreate(
                name="x" * 201,  # Exceeds 200 char limit
                subject="Test",
                list_ids=["list-1"]
            )

    def test_subject_max_length(self):
        """Test subject max length validation."""
        with pytest.raises(ValueError):
            CampaignCreate(
                name="Campaign",
                subject="x" * 201,  # Exceeds 200 char limit
                list_ids=["list-1"]
            )

    def test_preview_text_max_length(self):
        """Test preview text max length validation."""
        with pytest.raises(ValueError):
            CampaignCreate(
                name="Campaign",
                subject="Subject",
                preview_text="x" * 151,  # Exceeds 150 char limit
                list_ids=["list-1"]
            )

    def test_list_ids_required(self):
        """Test that at least one list is required."""
        with pytest.raises(ValueError):
            CampaignCreate(
                name="Campaign",
                subject="Subject",
                list_ids=[]  # Empty list not allowed
            )


# ==================== ROUTER TESTS ====================

class TestRouter:
    """Tests for router configuration."""

    def test_router_exists(self):
        """Verify router exists."""
        assert router is not None

    def test_router_has_routes(self):
        """Verify router has routes."""
        assert len(router.routes) > 0
