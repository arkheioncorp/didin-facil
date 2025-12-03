"""
Comprehensive Tests for Scheduler Routes
=========================================
Tests for social media post scheduling endpoints.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {
        "id": str(uuid4()),
        "email": "test@example.com",
        "name": "Test User",
        "is_admin": False
    }


@pytest.fixture
def mock_admin_user():
    """Mock admin user."""
    return {
        "id": str(uuid4()),
        "email": "admin@example.com",
        "name": "Admin User",
        "is_admin": True
    }


@pytest.fixture
def mock_service():
    """Mock SubscriptionService."""
    service = MagicMock()
    service.can_use_feature = AsyncMock(return_value=True)
    service.increment_usage = AsyncMock()
    return service


@pytest.fixture
def mock_scheduled_post():
    """Mock ScheduledPost."""
    from workers.post_scheduler import Platform, PostStatus, ScheduledPost
    
    return ScheduledPost(
        id=str(uuid4()),
        user_id=str(uuid4()),
        platform=Platform.INSTAGRAM,
        scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
        content_type="photo",
        caption="Test caption",
        status=PostStatus.SCHEDULED
    )


# ============================================
# SCHEDULE POST TESTS
# ============================================

class TestSchedulePost:
    """Tests for POST /posts endpoint."""
    
    @pytest.mark.asyncio
    async def test_schedule_post_success(self, mock_user, mock_service, mock_scheduled_post):
        """Should schedule post successfully."""
        from api.routes.scheduler import SchedulePostRequest, schedule_post
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler_instance:
            mock_scheduler_instance.schedule = AsyncMock(return_value=mock_scheduled_post)
            
            data = SchedulePostRequest(
                platform="instagram",
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
                content_type="photo",
                caption="Test post"
            )
            
            result = await schedule_post(
                data=data,
                current_user=mock_user,
                service=mock_service
            )
            
            assert result.platform == "instagram"
            assert result.status == "scheduled"
    
    @pytest.mark.asyncio
    async def test_schedule_post_limit_reached(self, mock_user, mock_service):
        """Should reject when post limit reached."""
        from api.routes.scheduler import SchedulePostRequest, schedule_post
        
        mock_service.can_use_feature.return_value = False
        
        data = SchedulePostRequest(
            platform="instagram",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="photo",
            caption="Test post"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post(
                data=data,
                current_user=mock_user,
                service=mock_service
            )
        
        assert exc_info.value.status_code == 402
        assert "Limite" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_schedule_post_invalid_platform(self, mock_user, mock_service):
        """Should reject invalid platform."""
        from api.routes.scheduler import SchedulePostRequest, schedule_post
        
        data = SchedulePostRequest(
            platform="invalid_platform",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="photo",
            caption="Test post"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post(
                data=data,
                current_user=mock_user,
                service=mock_service
            )
        
        assert exc_info.value.status_code == 400
        assert "inválida" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_schedule_post_past_date_rejected(self, mock_user, mock_service):
        """Should reject scheduling in the past."""
        from api.routes.scheduler import SchedulePostRequest, schedule_post
        
        data = SchedulePostRequest(
            platform="instagram",
            scheduled_time=datetime.now(timezone.utc) - timedelta(hours=1),
            content_type="photo",
            caption="Test post"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post(
                data=data,
                current_user=mock_user,
                service=mock_service
            )
        
        assert exc_info.value.status_code == 400
        assert "futura" in exc_info.value.detail


# ============================================
# LIST SCHEDULED POSTS TESTS
# ============================================

class TestListScheduledPosts:
    """Tests for GET /posts endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_scheduled_posts_empty(self, mock_user):
        """Should return empty list when no posts."""
        from api.routes.scheduler import list_scheduled_posts
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_user_posts = AsyncMock(return_value=[])
            
            result = await list_scheduled_posts(
                status=None,
                limit=50,
                current_user=mock_user
            )
            
            assert result["posts"] == []
            assert result["total"] == 0
    
    @pytest.mark.asyncio
    async def test_list_scheduled_posts_with_filter(self, mock_user, mock_scheduled_post):
        """Should filter posts by status."""
        from api.routes.scheduler import list_scheduled_posts
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_user_posts = AsyncMock(return_value=[mock_scheduled_post])
            
            result = await list_scheduled_posts(
                status="scheduled",
                limit=50,
                current_user=mock_user
            )
            
            assert len(result["posts"]) == 1
    
    @pytest.mark.asyncio
    async def test_list_scheduled_posts_invalid_status(self, mock_user):
        """Should reject invalid status filter."""
        from api.routes.scheduler import list_scheduled_posts
        
        with pytest.raises(HTTPException) as exc_info:
            await list_scheduled_posts(
                status="invalid_status",
                limit=50,
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 400
        assert "inválido" in exc_info.value.detail


# ============================================
# CANCEL POST TESTS
# ============================================

class TestCancelPost:
    """Tests for DELETE /posts/{post_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_cancel_post_success(self, mock_user):
        """Should cancel post successfully."""
        from api.routes.scheduler import cancel_post
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.cancel = AsyncMock(return_value=True)
            
            post_id = str(uuid4())
            result = await cancel_post(
                post_id=post_id,
                current_user=mock_user
            )
            
            assert result["status"] == "cancelled"
            assert result["id"] == post_id
    
    @pytest.mark.asyncio
    async def test_cancel_post_not_found(self, mock_user):
        """Should return 404 when post not found."""
        from api.routes.scheduler import cancel_post
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.cancel = AsyncMock(return_value=False)
            
            with pytest.raises(HTTPException) as exc_info:
                await cancel_post(
                    post_id=str(uuid4()),
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 404


# ============================================
# SCHEDULER STATS TESTS
# ============================================

class TestGetSchedulerStats:
    """Tests for GET /stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_scheduler_stats_empty(self, mock_user):
        """Should return zero stats when no posts."""
        from api.routes.scheduler import get_scheduler_stats
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_user_posts = AsyncMock(return_value=[])
            
            result = await get_scheduler_stats(current_user=mock_user)
            
            assert result["total"] == 0
            assert result["scheduled"] == 0
            assert result["published"] == 0
            assert result["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_get_scheduler_stats_with_posts(self, mock_user):
        """Should calculate stats correctly."""
        from api.routes.scheduler import get_scheduler_stats
        from workers.post_scheduler import Platform, PostStatus, ScheduledPost
        
        posts = [
            ScheduledPost(
                id=str(uuid4()),
                user_id=mock_user["id"],
                platform=Platform.INSTAGRAM,
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
                content_type="photo",
                caption="Test",
                status=PostStatus.SCHEDULED
            ),
            ScheduledPost(
                id=str(uuid4()),
                user_id=mock_user["id"],
                platform=Platform.TIKTOK,
                scheduled_time=datetime.now(timezone.utc) - timedelta(hours=1),
                content_type="video",
                caption="Test",
                status=PostStatus.PUBLISHED
            ),
            ScheduledPost(
                id=str(uuid4()),
                user_id=mock_user["id"],
                platform=Platform.INSTAGRAM,
                scheduled_time=datetime.now(timezone.utc) - timedelta(hours=2),
                content_type="photo",
                caption="Test",
                status=PostStatus.FAILED
            )
        ]
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_user_posts = AsyncMock(return_value=posts)
            
            result = await get_scheduler_stats(current_user=mock_user)
            
            assert result["total"] == 3
            assert result["scheduled"] == 1
            assert result["published"] == 1
            assert result["failed"] == 1
            assert "instagram" in result["by_platform"]
            assert "tiktok" in result["by_platform"]


# ============================================
# DLQ STATS TESTS
# ============================================

class TestGetDLQStats:
    """Tests for GET /dlq/stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_dlq_stats_empty(self, mock_user):
        """Should return zero stats when no DLQ posts."""
        from api.routes.scheduler import get_dlq_stats
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_dlq_posts = AsyncMock(return_value=[])
            
            result = await get_dlq_stats(current_user=mock_user)
            
            assert result["total"] == 0
            assert result["by_platform"] == {}
            assert result["by_error_type"] == {}
    
    @pytest.mark.asyncio
    async def test_get_dlq_stats_with_errors(self, mock_user):
        """Should categorize errors correctly."""
        from api.routes.scheduler import get_dlq_stats
        from workers.post_scheduler import Platform, PostStatus, ScheduledPost
        
        posts = [
            ScheduledPost(
                id=str(uuid4()),
                user_id=mock_user["id"],
                platform=Platform.INSTAGRAM,
                scheduled_time=datetime.now(timezone.utc),
                content_type="photo",
                caption="Test",
                status=PostStatus.FAILED,
                error_message="Rate limit exceeded"
            ),
            ScheduledPost(
                id=str(uuid4()),
                user_id=mock_user["id"],
                platform=Platform.INSTAGRAM,
                scheduled_time=datetime.now(timezone.utc),
                content_type="photo",
                caption="Test",
                status=PostStatus.FAILED,
                error_message="Authentication failed 401"
            )
        ]
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_dlq_posts = AsyncMock(return_value=posts)
            
            result = await get_dlq_stats(current_user=mock_user)
            
            assert result["total"] == 2
            assert "instagram" in result["by_platform"]
            assert "rate_limit" in result["by_error_type"]
            assert "auth_error" in result["by_error_type"]


# ============================================
# ERROR CLASSIFICATION TESTS
# ============================================

class TestClassifyError:
    """Tests for _classify_error helper function."""
    
    def test_classify_rate_limit(self):
        """Should classify rate limit errors."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("Rate limit exceeded") == "rate_limit"
        assert _classify_error("Too many requests") == "rate_limit"
        assert _classify_error("Error 429") == "rate_limit"
    
    def test_classify_auth_error(self):
        """Should classify authentication errors."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("Authentication failed") == "auth_error"
        assert _classify_error("Token expired") == "auth_error"
        assert _classify_error("Error 401") == "auth_error"
        assert _classify_error("Error 403 Forbidden") == "auth_error"
    
    def test_classify_network_error(self):
        """Should classify network errors."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("Network timeout") == "network_error"
        assert _classify_error("Connection refused") == "network_error"
        assert _classify_error("Socket error") == "network_error"
    
    def test_classify_content_error(self):
        """Should classify content errors."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("Invalid media format") == "content_error"
        assert _classify_error("File too large") == "content_error"
        assert _classify_error("Invalid file size") == "content_error"
    
    def test_classify_quota_error(self):
        """Should classify quota errors."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("Quota exceeded") == "quota_exceeded"
        assert _classify_error("Daily limit exceeded") == "quota_exceeded"
    
    def test_classify_unknown_error(self):
        """Should return unknown for unrecognized errors."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("Something went wrong") == "unknown"
        assert _classify_error("") == "unknown"


# ============================================
# PLATFORM ENUM TESTS
# ============================================

class TestPlatformEnum:
    """Tests for Platform enum."""
    
    def test_valid_platforms(self):
        """Should have all expected platforms."""
        from workers.post_scheduler import Platform
        
        assert Platform.INSTAGRAM.value == "instagram"
        assert Platform.TIKTOK.value == "tiktok"
        assert Platform.YOUTUBE.value == "youtube"
        assert Platform.WHATSAPP.value == "whatsapp"


class TestPostStatusEnum:
    """Tests for PostStatus enum."""
    
    def test_valid_statuses(self):
        """Should have all expected statuses."""
        from workers.post_scheduler import PostStatus
        
        assert PostStatus.SCHEDULED.value == "scheduled"
        assert PostStatus.PUBLISHED.value == "published"
        assert PostStatus.FAILED.value == "failed"
        assert PostStatus.CANCELLED.value == "cancelled"


# ============================================
# SCHEMA TESTS
# ============================================

class TestSchedulePostRequest:
    """Tests for SchedulePostRequest schema."""
    
    def test_valid_request(self):
        """Should validate correct request."""
        from api.routes.scheduler import SchedulePostRequest
        
        request = SchedulePostRequest(
            platform="instagram",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="photo",
            caption="Test post",
            hashtags=["test", "post"]
        )
        
        assert request.platform == "instagram"
        assert request.content_type == "photo"
        assert len(request.hashtags) == 2
    
    def test_default_values(self):
        """Should have correct default values."""
        from api.routes.scheduler import SchedulePostRequest
        
        request = SchedulePostRequest(
            platform="instagram",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="photo"
        )
        
        assert request.caption == ""
        assert request.hashtags == []
        assert request.account_name is None
        assert request.platform_config == {}


class TestSchedulePostResponse:
    """Tests for SchedulePostResponse schema."""
    
    def test_valid_response(self):
        """Should validate correct response."""
        from api.routes.scheduler import SchedulePostResponse
        
        response = SchedulePostResponse(
            id=str(uuid4()),
            platform="instagram",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            status="scheduled",
            content_type="photo"
        )
        
        assert response.platform == "instagram"
        assert response.status == "scheduled"


class TestBulkActionRequest:
    """Tests for BulkActionRequest schema."""
    
    def test_valid_request(self):
        """Should validate bulk action request."""
        from api.routes.scheduler import BulkActionRequest
        
        request = BulkActionRequest(ids=[str(uuid4()), str(uuid4())])
        
        assert len(request.ids) == 2
    
    def test_empty_request(self):
        """Should allow empty list."""
        from api.routes.scheduler import BulkActionRequest
        
        request = BulkActionRequest(ids=[])
        
        assert len(request.ids) == 0
