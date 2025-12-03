"""
Extended tests for scheduler routes.
Coverage target: 90%+
"""

import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


# ==================== FIXTURES ====================

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {"id": "user123", "email": "test@example.com", "is_admin": False}


@pytest.fixture
def mock_admin_user():
    """Mock admin user."""
    user = MagicMock()
    user.__getitem__ = lambda self, key: {"id": "admin123", "email": "admin@example.com"}[key]
    user.is_admin = True
    return user


@pytest.fixture
def mock_subscription_service():
    """Mock subscription service."""
    service = MagicMock()
    service.can_use_feature = AsyncMock(return_value=True)
    service.increment_usage = AsyncMock()
    return service


@pytest.fixture
def mock_scheduler():
    """Mock scheduler service."""
    from workers.post_scheduler import Platform, PostStatus, ScheduledPost
    
    mock_post = MagicMock()
    mock_post.id = "post123"
    mock_post.user_id = "user123"
    mock_post.platform = Platform.INSTAGRAM
    mock_post.scheduled_time = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_post.status = PostStatus.SCHEDULED
    mock_post.content_type = "photo"
    mock_post.caption = "Test caption"
    mock_post.hashtags = ["test"]
    mock_post.created_at = datetime.now(timezone.utc)
    mock_post.published_at = None
    mock_post.retry_count = 0
    mock_post.error_message = None
    mock_post.platform_config = {}
    
    scheduler = MagicMock()
    scheduler.schedule = AsyncMock(return_value=mock_post)
    scheduler.get_user_posts = AsyncMock(return_value=[mock_post])
    scheduler.cancel = AsyncMock(return_value=True)
    scheduler.get_dlq_posts = AsyncMock(return_value=[])
    
    return scheduler


# ==================== SCHEDULE POST TESTS ====================

class TestSchedulePost:
    """Test schedule_post endpoint."""
    
    @pytest.mark.asyncio
    async def test_schedule_post_success(self, mock_user, mock_subscription_service, mock_scheduler):
        """Test successful post scheduling."""
        from api.routes.scheduler import schedule_post, SchedulePostRequest
        
        with patch('api.routes.scheduler.scheduler', mock_scheduler):
            request = SchedulePostRequest(
                platform="instagram",
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
                content_type="photo",
                caption="Test"
            )
            
            result = await schedule_post(request, mock_user, mock_subscription_service)
            
            assert result.id == "post123"
            assert result.platform == "instagram"
    
    @pytest.mark.asyncio
    async def test_schedule_post_limit_reached(self, mock_user, mock_subscription_service):
        """Test scheduling when limit is reached."""
        from api.routes.scheduler import schedule_post, SchedulePostRequest
        
        mock_subscription_service.can_use_feature = AsyncMock(return_value=False)
        
        request = SchedulePostRequest(
            platform="instagram",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="photo"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post(request, mock_user, mock_subscription_service)
        
        assert exc_info.value.status_code == 402
    
    @pytest.mark.asyncio
    async def test_schedule_post_invalid_platform(self, mock_user, mock_subscription_service):
        """Test scheduling with invalid platform."""
        from api.routes.scheduler import schedule_post, SchedulePostRequest
        
        request = SchedulePostRequest(
            platform="invalid_platform",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="photo"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post(request, mock_user, mock_subscription_service)
        
        assert exc_info.value.status_code == 400
        assert "Plataforma inválida" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_schedule_post_past_date(self, mock_user, mock_subscription_service):
        """Test scheduling with past date."""
        from api.routes.scheduler import schedule_post, SchedulePostRequest
        
        request = SchedulePostRequest(
            platform="instagram",
            scheduled_time=datetime.now(timezone.utc) - timedelta(hours=1),
            content_type="photo"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post(request, mock_user, mock_subscription_service)
        
        assert exc_info.value.status_code == 400
        assert "futura" in str(exc_info.value.detail)


# ==================== SCHEDULE POST WITH FILE TESTS ====================

class TestSchedulePostWithFile:
    """Test schedule_post_with_file endpoint."""
    
    @pytest.mark.asyncio
    async def test_schedule_with_file_success(
        self, mock_user, mock_subscription_service, mock_scheduler
    ):
        """Test scheduling with file upload."""
        from api.routes.scheduler import schedule_post_with_file
        
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.file = MagicMock()
        
        future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        
        with patch('api.routes.scheduler.scheduler', mock_scheduler), \
             patch('os.makedirs'), \
             patch('builtins.open', MagicMock()), \
             patch('shutil.copyfileobj'):
            
            result = await schedule_post_with_file(
                platform="instagram",
                scheduled_time=future_time,
                content_type="photo",
                caption="Test",
                hashtags="test,photo",
                account_name="account1",
                file=mock_file,
                current_user=mock_user,
                service=mock_subscription_service
            )
            
            assert result.id == "post123"
    
    @pytest.mark.asyncio
    async def test_schedule_with_file_invalid_date_format(
        self, mock_user, mock_subscription_service
    ):
        """Test with invalid date format."""
        from api.routes.scheduler import schedule_post_with_file
        
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post_with_file(
                platform="instagram",
                scheduled_time="invalid-date",
                content_type="photo",
                file=mock_file,
                current_user=mock_user,
                service=mock_subscription_service
            )
        
        assert exc_info.value.status_code == 400
        assert "Formato de data" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_schedule_with_file_past_date(
        self, mock_user, mock_subscription_service
    ):
        """Test with past date."""
        from api.routes.scheduler import schedule_post_with_file
        
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        
        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post_with_file(
                platform="instagram",
                scheduled_time=past_time,
                content_type="photo",
                file=mock_file,
                current_user=mock_user,
                service=mock_subscription_service
            )
        
        assert exc_info.value.status_code == 400


# ==================== LIST POSTS TESTS ====================

class TestListScheduledPosts:
    """Test list_scheduled_posts endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_posts_success(self, mock_user, mock_scheduler):
        """Test listing scheduled posts."""
        from api.routes.scheduler import list_scheduled_posts
        
        with patch('api.routes.scheduler.scheduler', mock_scheduler):
            result = await list_scheduled_posts(current_user=mock_user)
            
            assert "posts" in result
            assert "total" in result
            assert result["total"] >= 0
    
    @pytest.mark.asyncio
    async def test_list_posts_with_status_filter(self, mock_user, mock_scheduler):
        """Test listing with status filter."""
        from api.routes.scheduler import list_scheduled_posts
        
        with patch('api.routes.scheduler.scheduler', mock_scheduler):
            result = await list_scheduled_posts(
                status="scheduled",
                current_user=mock_user
            )
            
            assert "posts" in result
    
    @pytest.mark.asyncio
    async def test_list_posts_invalid_status(self, mock_user):
        """Test with invalid status."""
        from api.routes.scheduler import list_scheduled_posts
        
        with pytest.raises(HTTPException) as exc_info:
            await list_scheduled_posts(status="invalid_status", current_user=mock_user)
        
        assert exc_info.value.status_code == 400


# ==================== CANCEL POST TESTS ====================

class TestCancelPost:
    """Test cancel_post endpoint."""
    
    @pytest.mark.asyncio
    async def test_cancel_post_success(self, mock_user, mock_scheduler):
        """Test successful cancellation."""
        from api.routes.scheduler import cancel_post
        
        with patch('api.routes.scheduler.scheduler', mock_scheduler):
            result = await cancel_post("post123", mock_user)
            
            assert result["status"] == "cancelled"
            assert result["id"] == "post123"
    
    @pytest.mark.asyncio
    async def test_cancel_post_not_found(self, mock_user, mock_scheduler):
        """Test cancellation of non-existent post."""
        from api.routes.scheduler import cancel_post
        
        mock_scheduler.cancel = AsyncMock(return_value=False)
        
        with patch('api.routes.scheduler.scheduler', mock_scheduler):
            with pytest.raises(HTTPException) as exc_info:
                await cancel_post("nonexistent", mock_user)
            
            assert exc_info.value.status_code == 404


# ==================== STATS TESTS ====================

class TestSchedulerStats:
    """Test get_scheduler_stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_stats(self, mock_user, mock_scheduler):
        """Test getting scheduler stats."""
        from api.routes.scheduler import get_scheduler_stats
        
        with patch('api.routes.scheduler.scheduler', mock_scheduler):
            result = await get_scheduler_stats(mock_user)
            
            assert "total" in result
            assert "scheduled" in result
            assert "published" in result
            assert "failed" in result
            assert "by_platform" in result
    
    @pytest.mark.asyncio
    async def test_get_stats_with_various_statuses(self, mock_user):
        """Test stats with various post statuses."""
        from api.routes.scheduler import get_scheduler_stats
        from workers.post_scheduler import Platform, PostStatus
        
        posts = []
        for status in [PostStatus.SCHEDULED, PostStatus.PUBLISHED, PostStatus.FAILED]:
            mock_post = MagicMock()
            mock_post.status = status
            mock_post.platform = Platform.INSTAGRAM
            mock_post.retry_count = 0
            posts.append(mock_post)
        
        mock_scheduler = MagicMock()
        mock_scheduler.get_user_posts = AsyncMock(return_value=posts)
        
        with patch('api.routes.scheduler.scheduler', mock_scheduler):
            result = await get_scheduler_stats(mock_user)
            
            assert result["scheduled"] == 1
            assert result["published"] == 1
            assert result["failed"] == 1


# ==================== DLQ TESTS ====================

class TestDLQ:
    """Test Dead Letter Queue endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_dlq_posts_empty(self, mock_user, mock_scheduler):
        """Test getting empty DLQ."""
        from api.routes.scheduler import get_dlq_posts
        
        with patch('api.routes.scheduler.scheduler', mock_scheduler):
            result = await get_dlq_posts(current_user=mock_user)
            
            assert isinstance(result, list)
            assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_dlq_posts_with_items(self, mock_user):
        """Test getting DLQ with items."""
        from api.routes.scheduler import get_dlq_posts
        from workers.post_scheduler import Platform, PostStatus
        
        mock_post = MagicMock()
        mock_post.id = "dlq_post1"
        mock_post.user_id = "user123"
        mock_post.platform = Platform.INSTAGRAM
        mock_post.scheduled_time = datetime.now(timezone.utc)
        mock_post.retry_count = 3
        mock_post.error_message = "Rate limit exceeded"
        mock_post.content_type = "photo"
        mock_post.caption = "Test"
        mock_post.platform_config = {}
        
        mock_scheduler = MagicMock()
        mock_scheduler.get_dlq_posts = AsyncMock(return_value=[mock_post])
        
        with patch('api.routes.scheduler.scheduler', mock_scheduler):
            result = await get_dlq_posts(current_user=mock_user)
            
            assert len(result) == 1
            assert result[0]["id"] == "dlq_post1"
            assert result[0]["error_type"] == "rate_limit"
    
    @pytest.mark.asyncio
    async def test_get_dlq_stats(self, mock_user, mock_scheduler):
        """Test DLQ stats."""
        from api.routes.scheduler import get_dlq_stats
        
        with patch('api.routes.scheduler.scheduler', mock_scheduler):
            result = await get_dlq_stats(mock_user)
            
            assert "total" in result
            assert "by_platform" in result
            assert "by_error_type" in result


# ==================== CLASSIFY ERROR TESTS ====================

class TestClassifyError:
    """Test _classify_error helper function."""
    
    def test_classify_rate_limit(self):
        """Test rate limit error classification."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("Rate limit exceeded") == "rate_limit"
        assert _classify_error("Too many requests") == "rate_limit"
        assert _classify_error("Error 429") == "rate_limit"
    
    def test_classify_auth_error(self):
        """Test auth error classification."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("Authentication failed") == "auth_error"
        assert _classify_error("Token expired") == "auth_error"
        assert _classify_error("401 Unauthorized") == "auth_error"
    
    def test_classify_network_error(self):
        """Test network error classification."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("Network error") == "network_error"
        assert _classify_error("Connection timeout") == "network_error"
        assert _classify_error("Socket error") == "network_error"
    
    def test_classify_content_error(self):
        """Test content error classification."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("Invalid media format") == "content_error"
        assert _classify_error("File too large") == "content_error"
    
    def test_classify_quota_error(self):
        """Test quota error classification."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("Daily quota exceeded") == "quota_exceeded"
        assert _classify_error("Limit exceeded") == "quota_exceeded"
    
    def test_classify_unknown_error(self):
        """Test unknown error classification."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("Some random error") == "unknown"
        assert _classify_error("") == "unknown"


# ==================== PLATFORM ENUM TESTS ====================

class TestPlatformEnum:
    """Test Platform enum handling."""
    
    def test_valid_platforms(self):
        """Test all valid platforms."""
        from workers.post_scheduler import Platform
        
        valid_platforms = ["instagram", "tiktok", "youtube", "whatsapp"]
        for p in valid_platforms:
            platform = Platform(p)
            assert platform.value == p
    
    def test_invalid_platform(self):
        """Test invalid platform raises error."""
        from workers.post_scheduler import Platform
        
        with pytest.raises(ValueError):
            Platform("invalid")


# ==================== POST STATUS TESTS ====================

class TestPostStatus:
    """Test PostStatus enum."""
    
    def test_valid_statuses(self):
        """Test all valid statuses."""
        from workers.post_scheduler import PostStatus
        
        valid_statuses = ["scheduled", "published", "failed", "cancelled"]
        for s in valid_statuses:
            status = PostStatus(s)
            assert status.value == s
