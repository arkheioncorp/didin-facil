"""
Comprehensive tests for campaigns.py
=====================================
Tests for email campaign management routes.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.campaigns import (ABTestVariant, AutomationCreate,
                                  AutomationResponse, CampaignCreate,
                                  CampaignResponse, CampaignService,
                                  CampaignStats, CampaignStatus, CampaignType,
                                  CampaignUpdate, TriggerType, router)

# ==================== FIXTURES ====================


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock()
    user.__getitem__ = lambda self, key: {"id": "user123", "email": "test@test.com"}.get(key)
    user.get = lambda key, default=None: {"id": "user123", "email": "test@test.com"}.get(key, default)
    return user


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.hset = AsyncMock()
    redis.hgetall = AsyncMock(return_value={})
    redis.sadd = AsyncMock()
    redis.smembers = AsyncMock(return_value=set())
    redis.scard = AsyncMock(return_value=10)
    redis.lpush = AsyncMock()
    redis.zadd = AsyncMock()
    redis.delete = AsyncMock()
    redis.srem = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    return redis


@pytest.fixture
def sample_campaign_data():
    """Sample campaign data from Redis."""
    return {
        "id": "camp123",
        "user_id": "user123",
        "name": "Test Campaign",
        "subject": "Hello World",
        "preview_text": "Preview",
        "template_id": "",
        "html_content": "<p>Hello</p>",
        "text_content": "Hello",
        "list_ids": '["list1", "list2"]',
        "type": "regular",
        "trigger": "immediate",
        "status": "draft",
        "schedule_at": "",
        "recipients_count": "100",
        "segment_rules": "",
        "ab_test": "",
        "track_opens": "1",
        "track_clicks": "1",
        "reply_to_email": "",
        "reply_to_name": "",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def campaign_service():
    """Campaign service instance."""
    return CampaignService()


# ==================== SCHEMA TESTS ====================


class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_campaign_create_schema(self):
        """Test CampaignCreate schema."""
        data = CampaignCreate(
            name="Test Campaign",
            subject="Test Subject",
            list_ids=["list1", "list2"],
        )
        assert data.name == "Test Campaign"
        assert data.subject == "Test Subject"
        assert data.type == CampaignType.REGULAR
        assert data.trigger == TriggerType.IMMEDIATE
        assert data.track_opens is True
        assert data.track_clicks is True
    
    def test_campaign_create_with_ab_test(self):
        """Test CampaignCreate with A/B test."""
        data = CampaignCreate(
            name="AB Test Campaign",
            subject="Subject A",
            list_ids=["list1"],
            type=CampaignType.AB_TEST,
            ab_test={"variants": [], "split_percentage": 50},
        )
        assert data.type == CampaignType.AB_TEST
        assert data.ab_test is not None
    
    def test_campaign_create_with_schedule(self):
        """Test CampaignCreate with schedule."""
        future = datetime.now() + timedelta(days=1)
        data = CampaignCreate(
            name="Scheduled Campaign",
            subject="Test",
            list_ids=["list1"],
            trigger=TriggerType.SCHEDULED,
            schedule_at=future,
        )
        assert data.trigger == TriggerType.SCHEDULED
        assert data.schedule_at == future
    
    def test_campaign_update_schema(self):
        """Test CampaignUpdate schema."""
        data = CampaignUpdate(
            name="Updated Name",
            subject="Updated Subject",
        )
        assert data.name == "Updated Name"
        assert data.subject == "Updated Subject"
    
    def test_campaign_response_schema(self):
        """Test CampaignResponse schema."""
        data = CampaignResponse(
            id="camp123",
            name="Test",
            subject="Subject",
            preview_text=None,
            status=CampaignStatus.DRAFT,
            type=CampaignType.REGULAR,
            trigger=TriggerType.IMMEDIATE,
            list_ids=["list1"],
            recipients_count=100,
            schedule_at=None,
            sent_at=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert data.id == "camp123"
        assert data.status == CampaignStatus.DRAFT
    
    def test_campaign_stats_schema(self):
        """Test CampaignStats schema."""
        data = CampaignStats(
            campaign_id="camp123",
            total_recipients=1000,
            total_sent=950,
            total_delivered=900,
            total_opened=300,
            unique_opens=250,
            total_clicked=100,
            unique_clicks=80,
            total_bounced=50,
            total_unsubscribed=10,
            total_complained=2,
            delivery_rate=94.7,
            open_rate=27.8,
            click_rate=8.9,
            click_to_open_rate=32.0,
            bounce_rate=5.3,
            unsubscribe_rate=1.1,
            first_open_at=None,
            last_open_at=None,
            avg_open_time_seconds=None,
            top_links=[],
            device_breakdown={},
            location_breakdown={},
        )
        assert data.open_rate == 27.8
        assert data.delivery_rate == 94.7
    
    def test_ab_test_variant_schema(self):
        """Test ABTestVariant schema."""
        data = ABTestVariant(
            id="var1",
            name="Variant A",
            subject="Subject A",
            percentage=50,
        )
        assert data.sent == 0
        assert data.winner is False
    
    def test_automation_create_schema(self):
        """Test AutomationCreate schema."""
        data = AutomationCreate(
            name="Welcome Email",
            trigger_event="signup",
            emails=[{"subject": "Welcome!"}],
        )
        assert data.delay_minutes == 0
        assert data.active is True
    
    def test_automation_response_schema(self):
        """Test AutomationResponse schema."""
        data = AutomationResponse(
            id="auto123",
            name="Welcome",
            description=None,
            trigger_event="signup",
            trigger_conditions=None,
            delay_minutes=0,
            emails_count=3,
            active=True,
            total_triggered=100,
            total_completed=95,
            created_at=datetime.now(),
        )
        assert data.emails_count == 3


# ==================== ENUM TESTS ====================


class TestEnums:
    """Test enum values."""
    
    def test_campaign_status(self):
        """Test CampaignStatus enum."""
        assert CampaignStatus.DRAFT.value == "draft"
        assert CampaignStatus.SCHEDULED.value == "scheduled"
        assert CampaignStatus.SENDING.value == "sending"
        assert CampaignStatus.SENT.value == "sent"
        assert CampaignStatus.PAUSED.value == "paused"
        assert CampaignStatus.CANCELLED.value == "cancelled"
    
    def test_campaign_type(self):
        """Test CampaignType enum."""
        assert CampaignType.REGULAR.value == "regular"
        assert CampaignType.AUTOMATED.value == "automated"
        assert CampaignType.AB_TEST.value == "ab_test"
        assert CampaignType.TRANSACTIONAL.value == "transactional"
    
    def test_trigger_type(self):
        """Test TriggerType enum."""
        assert TriggerType.IMMEDIATE.value == "immediate"
        assert TriggerType.SCHEDULED.value == "scheduled"
        assert TriggerType.EVENT_BASED.value == "event_based"
        assert TriggerType.RECURRING.value == "recurring"


# ==================== CAMPAIGN SERVICE TESTS ====================


class TestCampaignService:
    """Test CampaignService methods."""
    
    @pytest.mark.asyncio
    async def test_create_campaign(self, campaign_service, mock_redis):
        """Test creating a campaign."""
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            data = CampaignCreate(
                name="New Campaign",
                subject="Test Subject",
                list_ids=["list1"],
            )
            
            result = await campaign_service.create_campaign("user123", data)
            
            assert result.name == "New Campaign"
            assert result.status == CampaignStatus.DRAFT
            mock_redis.hset.assert_called()
            mock_redis.sadd.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_campaign_found(self, campaign_service, mock_redis, sample_campaign_data):
        """Test getting an existing campaign."""
        mock_redis.hgetall = AsyncMock(return_value=sample_campaign_data)
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            result = await campaign_service.get_campaign("user123", "camp123")
            
            assert result is not None
            assert result.name == "Test Campaign"
    
    @pytest.mark.asyncio
    async def test_get_campaign_not_found(self, campaign_service, mock_redis):
        """Test getting non-existent campaign."""
        mock_redis.hgetall = AsyncMock(return_value={})
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            result = await campaign_service.get_campaign("user123", "unknown")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_campaign_wrong_user(self, campaign_service, mock_redis, sample_campaign_data):
        """Test getting campaign of another user."""
        sample_campaign_data["user_id"] = "otheruser"
        mock_redis.hgetall = AsyncMock(return_value=sample_campaign_data)
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            result = await campaign_service.get_campaign("user123", "camp123")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_list_campaigns(self, campaign_service, mock_redis, sample_campaign_data):
        """Test listing campaigns."""
        mock_redis.smembers = AsyncMock(return_value={"camp1", "camp2"})
        mock_redis.hgetall = AsyncMock(return_value=sample_campaign_data)
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            result = await campaign_service.list_campaigns("user123")
            
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_list_campaigns_with_status_filter(self, campaign_service, mock_redis, sample_campaign_data):
        """Test listing campaigns with status filter."""
        mock_redis.smembers = AsyncMock(return_value={"camp1"})
        mock_redis.hgetall = AsyncMock(return_value=sample_campaign_data)
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            result = await campaign_service.list_campaigns(
                "user123", 
                status=CampaignStatus.DRAFT
            )
            
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_list_campaigns_empty(self, campaign_service, mock_redis):
        """Test listing campaigns when empty."""
        mock_redis.smembers = AsyncMock(return_value=set())
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            result = await campaign_service.list_campaigns("user123")
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_update_campaign_success(self, campaign_service, mock_redis, sample_campaign_data):
        """Test updating a campaign."""
        mock_redis.hgetall = AsyncMock(return_value=sample_campaign_data)
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            update_data = CampaignUpdate(name="Updated Name")
            result = await campaign_service.update_campaign(
                "user123", "camp123", update_data
            )
            
            mock_redis.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_campaign_not_draft(self, campaign_service, mock_redis, sample_campaign_data):
        """Test updating a non-draft campaign fails."""
        sample_campaign_data["status"] = "sent"
        mock_redis.hgetall = AsyncMock(return_value=sample_campaign_data)
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            update_data = CampaignUpdate(name="Updated Name")
            
            with pytest.raises(Exception) as exc_info:
                await campaign_service.update_campaign(
                    "user123", "camp123", update_data
                )
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_send_campaign_success(self, campaign_service, mock_redis, sample_campaign_data):
        """Test sending a campaign."""
        mock_redis.hgetall = AsyncMock(return_value=sample_campaign_data)
        background_tasks = MagicMock()
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            result = await campaign_service.send_campaign(
                "user123", "camp123", background_tasks
            )
            
            assert result["status"] == "sending"
            mock_redis.lpush.assert_called()
    
    @pytest.mark.asyncio
    async def test_send_campaign_not_found(self, campaign_service, mock_redis):
        """Test sending non-existent campaign."""
        mock_redis.hgetall = AsyncMock(return_value={})
        background_tasks = MagicMock()
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            with pytest.raises(Exception) as exc_info:
                await campaign_service.send_campaign(
                    "user123", "unknown", background_tasks
                )
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_send_campaign_already_sent(self, campaign_service, mock_redis, sample_campaign_data):
        """Test sending already sent campaign fails."""
        sample_campaign_data["status"] = "sent"
        mock_redis.hgetall = AsyncMock(return_value=sample_campaign_data)
        background_tasks = MagicMock()
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            with pytest.raises(Exception) as exc_info:
                await campaign_service.send_campaign(
                    "user123", "camp123", background_tasks
                )
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_schedule_campaign_success(self, campaign_service, mock_redis, sample_campaign_data):
        """Test scheduling a campaign."""
        mock_redis.hgetall = AsyncMock(return_value=sample_campaign_data)
        future = datetime.now() + timedelta(days=1)
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            result = await campaign_service.schedule_campaign(
                "user123", "camp123", future
            )
            
            assert result["status"] == "scheduled"
            mock_redis.zadd.assert_called()
    
    @pytest.mark.asyncio
    async def test_schedule_campaign_past_date(self, campaign_service, mock_redis, sample_campaign_data):
        """Test scheduling campaign for past date fails."""
        mock_redis.hgetall = AsyncMock(return_value=sample_campaign_data)
        past = datetime.now() - timedelta(days=1)
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            with pytest.raises(Exception) as exc_info:
                await campaign_service.schedule_campaign(
                    "user123", "camp123", past
                )
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_schedule_campaign_not_draft(self, campaign_service, mock_redis, sample_campaign_data):
        """Test scheduling non-draft campaign fails."""
        sample_campaign_data["status"] = "sent"
        mock_redis.hgetall = AsyncMock(return_value=sample_campaign_data)
        future = datetime.now() + timedelta(days=1)
        
        with patch('api.routes.campaigns.get_redis', return_value=mock_redis):
            with pytest.raises(Exception) as exc_info:
                await campaign_service.schedule_campaign(
                    "user123", "camp123", future
                )
            assert exc_info.value.status_code == 400


# ==================== ROUTER TESTS ====================


class TestRouter:
    """Test router configuration."""
    
    def test_router_exists(self):
        """Test that router is defined."""
        assert router is not None
    
    def test_router_prefix(self):
        """Test router has expected routes."""
        routes = [r.path for r in router.routes if hasattr(r, 'path')]
        # Check some expected routes exist
        assert len(routes) > 0
