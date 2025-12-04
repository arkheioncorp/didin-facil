"""
Extended tests for Scheduler Routes - DLQ and error classification.
Coverage target: Cover DLQ operations and _classify_error function.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

# ==================== FIXTURES ====================

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock()
    user.__getitem__ = lambda s, k: {"id": "user-123", "is_admin": False}.get(k)
    user.is_admin = False
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user."""
    user = MagicMock()
    user.__getitem__ = lambda s, k: {"id": "admin-123", "is_admin": True}.get(k)
    user.is_admin = True
    return user


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.lrem = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def mock_scheduled_post():
    """Create a mock ScheduledPost."""
    from workers.post_scheduler import Platform, PostStatus, ScheduledPost
    
    return ScheduledPost(
        id=str(uuid4()),
        user_id="user-123",
        platform=Platform.INSTAGRAM,
        scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
        content_type="photo",
        caption="Test caption",
        status=PostStatus.FAILED,
        error_message="Rate limit exceeded",
        retry_count=3
    )


@pytest.fixture
def mock_subscription_service():
    """Mock subscription service."""
    service = AsyncMock()
    service.can_use_feature = AsyncMock(return_value=True)
    service.increment_usage = AsyncMock()
    return service


# ==================== CLASSIFY ERROR TESTS ====================

class TestClassifyError:
    """Test _classify_error function."""
    
    def test_classify_rate_limit_error(self):
        """Test rate limit error classification."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("rate limit exceeded") == "rate_limit"
        assert _classify_error("too many requests") == "rate_limit"
        assert _classify_error("HTTP 429 Too Many Requests") == "rate_limit"
    
    def test_classify_auth_error(self):
        """Test auth error classification."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("authentication failed") == "auth_error"
        assert _classify_error("invalid token") == "auth_error"
        assert _classify_error("HTTP 401 Unauthorized") == "auth_error"
        assert _classify_error("HTTP 403 Forbidden") == "auth_error"
        assert _classify_error("please login again") == "auth_error"
    
    def test_classify_network_error(self):
        """Test network error classification."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("network connection failed") == "network_error"
        assert _classify_error("connection timeout") == "network_error"
        assert _classify_error("socket error") == "network_error"
    
    def test_classify_content_error(self):
        """Test content error classification."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("invalid media format") == "content_error"
        assert _classify_error("file too large") == "content_error"
        assert _classify_error("invalid file size") == "content_error"
    
    def test_classify_quota_error(self):
        """Test quota error classification."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("quota exceeded") == "quota_exceeded"
        assert _classify_error("daily limit exceeded") == "quota_exceeded"
    
    def test_classify_unknown_error(self):
        """Test unknown error classification."""
        from api.routes.scheduler import _classify_error
        
        assert _classify_error("something went wrong") == "unknown"
        assert _classify_error("") == "unknown"
        assert _classify_error("random error message") == "unknown"


# ==================== DLQ POSTS TESTS ====================

class TestGetDlqPosts:
    """Test get_dlq_posts endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_dlq_posts_empty(self, mock_user):
        """Test getting DLQ posts when none exist."""
        from api.routes.scheduler import get_dlq_posts
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_dlq_posts = AsyncMock(return_value=[])
            
            result = await get_dlq_posts(limit=50, current_user=mock_user)
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_dlq_posts_filters_by_user(self, mock_user, mock_scheduled_post):
        """Test DLQ posts are filtered by user."""
        from api.routes.scheduler import get_dlq_posts
        from workers.post_scheduler import Platform, PostStatus, ScheduledPost
        
        other_user_post = ScheduledPost(
            id=str(uuid4()),
            user_id="other-user",
            platform=Platform.INSTAGRAM,
            scheduled_time=datetime.now(timezone.utc),
            content_type="photo",
            caption="Other user post",
            status=PostStatus.FAILED,
            error_message="Error"
        )
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_dlq_posts = AsyncMock(return_value=[
                mock_scheduled_post,
                other_user_post
            ])
            
            result = await get_dlq_posts(limit=50, current_user=mock_user)
            
            # Only the user's post should be returned
            assert len(result) == 1
            assert result[0]["id"] == mock_scheduled_post.id
    
    @pytest.mark.asyncio
    async def test_get_dlq_posts_admin_sees_all(self, mock_admin_user, mock_scheduled_post):
        """Test admin sees all DLQ posts."""
        from api.routes.scheduler import get_dlq_posts
        from workers.post_scheduler import Platform, PostStatus, ScheduledPost
        
        other_user_post = ScheduledPost(
            id=str(uuid4()),
            user_id="other-user",
            platform=Platform.INSTAGRAM,
            scheduled_time=datetime.now(timezone.utc),
            content_type="photo",
            caption="Other user post",
            status=PostStatus.FAILED,
            error_message="Error"
        )
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_dlq_posts = AsyncMock(return_value=[
                mock_scheduled_post,
                other_user_post
            ])
            
            result = await get_dlq_posts(limit=50, current_user=mock_admin_user)
            
            # Admin should see both posts
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_get_dlq_posts_error_classification(self, mock_user, mock_scheduled_post):
        """Test DLQ posts include error classification."""
        from api.routes.scheduler import get_dlq_posts
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_dlq_posts = AsyncMock(return_value=[mock_scheduled_post])
            
            result = await get_dlq_posts(limit=50, current_user=mock_user)
            
            assert result[0]["error_type"] == "rate_limit"
            assert result[0]["last_error"] == "Rate limit exceeded"
            assert result[0]["attempts"] == 3


# ==================== DLQ STATS TESTS ====================

class TestGetDlqStats:
    """Test get_dlq_stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_dlq_stats_empty(self, mock_user):
        """Test DLQ stats with no posts."""
        from api.routes.scheduler import get_dlq_stats
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_dlq_posts = AsyncMock(return_value=[])
            
            result = await get_dlq_stats(current_user=mock_user)
            
            assert result["total"] == 0
            assert result["by_platform"] == {}
            assert result["by_error_type"] == {}
            assert result["oldest_failure"] is None
    
    @pytest.mark.asyncio
    async def test_get_dlq_stats_with_posts(self, mock_user, mock_scheduled_post):
        """Test DLQ stats with posts."""
        from api.routes.scheduler import get_dlq_stats
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_dlq_posts = AsyncMock(return_value=[mock_scheduled_post])
            
            result = await get_dlq_stats(current_user=mock_user)
            
            assert result["total"] == 1
            assert result["by_platform"]["instagram"] == 1
            assert result["by_error_type"]["rate_limit"] == 1


# ==================== RETRY DLQ POST TESTS ====================

class TestRetryDlqPost:
    """Test retry_dlq_post endpoint."""
    
    @pytest.mark.asyncio
    async def test_retry_dlq_post_success(self, mock_user, mock_redis, mock_scheduled_post):
        """Test successfully retrying a DLQ post."""
        from api.routes.scheduler import retry_dlq_post
        
        mock_redis.get = AsyncMock(return_value=mock_scheduled_post.model_dump_json())
        
        with patch("api.routes.scheduler.get_redis", return_value=mock_redis), \
             patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.retry_dlq_post = AsyncMock(return_value=True)
            
            result = await retry_dlq_post(
                post_id=mock_scheduled_post.id,
                current_user=mock_user
            )
            
            assert result["status"] == "rescheduled"
            assert result["id"] == mock_scheduled_post.id
    
    @pytest.mark.asyncio
    async def test_retry_dlq_post_not_found(self, mock_user, mock_redis):
        """Test retry when post not found."""
        from api.routes.scheduler import retry_dlq_post
        
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch("api.routes.scheduler.get_redis", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await retry_dlq_post(
                    post_id=str(uuid4()),
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_retry_dlq_post_unauthorized(self, mock_user, mock_redis):
        """Test retry when user is not owner."""
        from api.routes.scheduler import retry_dlq_post
        from workers.post_scheduler import Platform, PostStatus, ScheduledPost
        
        other_post = ScheduledPost(
            id=str(uuid4()),
            user_id="other-user",
            platform=Platform.INSTAGRAM,
            scheduled_time=datetime.now(timezone.utc),
            content_type="photo",
            caption="Other",
            status=PostStatus.FAILED
        )
        
        mock_redis.get = AsyncMock(return_value=other_post.model_dump_json())
        
        with patch("api.routes.scheduler.get_redis", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await retry_dlq_post(
                    post_id=other_post.id,
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_retry_dlq_post_scheduler_fails(self, mock_user, mock_redis, mock_scheduled_post):
        """Test retry when scheduler fails to reschedule."""
        from api.routes.scheduler import retry_dlq_post
        
        mock_redis.get = AsyncMock(return_value=mock_scheduled_post.model_dump_json())
        
        with patch("api.routes.scheduler.get_redis", return_value=mock_redis), \
             patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.retry_dlq_post = AsyncMock(return_value=False)
            
            with pytest.raises(HTTPException) as exc_info:
                await retry_dlq_post(
                    post_id=mock_scheduled_post.id,
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 400


# ==================== BULK RETRY TESTS ====================

class TestBulkRetryDlqPosts:
    """Test retry_all_dlq_posts endpoint."""
    
    @pytest.mark.asyncio
    async def test_bulk_retry_success(self, mock_user, mock_redis, mock_scheduled_post):
        """Test bulk retry with all successful."""
        from api.routes.scheduler import BulkActionRequest, retry_all_dlq_posts
        
        mock_redis.get = AsyncMock(return_value=mock_scheduled_post.model_dump_json())
        
        with patch("api.routes.scheduler.get_redis", return_value=mock_redis), \
             patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.retry_dlq_post = AsyncMock(return_value=True)
            
            request = BulkActionRequest(ids=[mock_scheduled_post.id])
            result = await retry_all_dlq_posts(
                request=request,
                current_user=mock_user
            )
            
            assert result["status"] == "completed"
            assert result["success"] == 1
            assert result["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_bulk_retry_partial_failure(self, mock_user, mock_redis, mock_scheduled_post):
        """Test bulk retry with some failures."""
        from api.routes.scheduler import BulkActionRequest, retry_all_dlq_posts

        # First call returns the post, second returns None (not found)
        mock_redis.get = AsyncMock(side_effect=[
            mock_scheduled_post.model_dump_json(),
            None
        ])
        
        with patch("api.routes.scheduler.get_redis", return_value=mock_redis), \
             patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.retry_dlq_post = AsyncMock(return_value=True)
            
            request = BulkActionRequest(ids=[mock_scheduled_post.id, str(uuid4())])
            result = await retry_all_dlq_posts(
                request=request,
                current_user=mock_user
            )
            
            assert result["status"] == "completed"
            assert result["success"] == 1
            assert result["errors"] == 1
    
    @pytest.mark.asyncio
    async def test_bulk_retry_unauthorized_skipped(self, mock_user, mock_redis):
        """Test bulk retry skips unauthorized posts."""
        from api.routes.scheduler import BulkActionRequest, retry_all_dlq_posts
        from workers.post_scheduler import Platform, PostStatus, ScheduledPost
        
        other_post = ScheduledPost(
            id=str(uuid4()),
            user_id="other-user",
            platform=Platform.INSTAGRAM,
            scheduled_time=datetime.now(timezone.utc),
            content_type="photo",
            caption="Other",
            status=PostStatus.FAILED
        )
        
        mock_redis.get = AsyncMock(return_value=other_post.model_dump_json())
        
        with patch("api.routes.scheduler.get_redis", return_value=mock_redis):
            request = BulkActionRequest(ids=[other_post.id])
            result = await retry_all_dlq_posts(
                request=request,
                current_user=mock_user
            )
            
            assert result["errors"] == 1
            assert result["success"] == 0


# ==================== BULK DELETE TESTS ====================

class TestBulkDeleteDlqPosts:
    """Test delete_all_dlq_posts endpoint."""
    
    @pytest.mark.asyncio
    async def test_bulk_delete_success(self, mock_user, mock_redis, mock_scheduled_post):
        """Test bulk delete with all successful."""
        from api.routes.scheduler import (BulkActionRequest,
                                          delete_all_dlq_posts)
        
        mock_redis.get = AsyncMock(return_value=mock_scheduled_post.model_dump_json())
        
        with patch("api.routes.scheduler.get_redis", return_value=mock_redis):
            request = BulkActionRequest(ids=[mock_scheduled_post.id])
            result = await delete_all_dlq_posts(
                request=request,
                current_user=mock_user
            )
            
            assert result["status"] == "completed"
            assert result["deleted"] == 1
            assert result["errors"] == 0
            mock_redis.lrem.assert_called()
            mock_redis.delete.assert_called()
    
    @pytest.mark.asyncio
    async def test_bulk_delete_not_found(self, mock_user, mock_redis):
        """Test bulk delete when posts not found."""
        from api.routes.scheduler import (BulkActionRequest,
                                          delete_all_dlq_posts)
        
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch("api.routes.scheduler.get_redis", return_value=mock_redis):
            request = BulkActionRequest(ids=[str(uuid4())])
            result = await delete_all_dlq_posts(
                request=request,
                current_user=mock_user
            )
            
            assert result["deleted"] == 0
            assert result["errors"] == 1


# ==================== REMOVE FROM DLQ TESTS ====================

class TestRemoveFromDlq:
    """Test remove_from_dlq endpoint."""
    
    @pytest.mark.asyncio
    async def test_remove_from_dlq_success(self, mock_user, mock_redis, mock_scheduled_post):
        """Test successfully removing from DLQ."""
        from api.routes.scheduler import remove_from_dlq
        
        mock_redis.get = AsyncMock(return_value=mock_scheduled_post.model_dump_json())
        
        with patch("api.routes.scheduler.get_redis", return_value=mock_redis):
            result = await remove_from_dlq(
                post_id=mock_scheduled_post.id,
                current_user=mock_user
            )
            
            assert result["status"] == "deleted"
            assert result["id"] == mock_scheduled_post.id
            mock_redis.lrem.assert_called_with("dlq_scheduled_posts", 0, mock_scheduled_post.id)
    
    @pytest.mark.asyncio
    async def test_remove_from_dlq_not_found(self, mock_user, mock_redis):
        """Test removing non-existent post from DLQ."""
        from api.routes.scheduler import remove_from_dlq
        
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch("api.routes.scheduler.get_redis", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await remove_from_dlq(
                    post_id=str(uuid4()),
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_remove_from_dlq_unauthorized(self, mock_user, mock_redis):
        """Test removing post when not owner."""
        from api.routes.scheduler import remove_from_dlq
        from workers.post_scheduler import Platform, PostStatus, ScheduledPost
        
        other_post = ScheduledPost(
            id=str(uuid4()),
            user_id="other-user",
            platform=Platform.INSTAGRAM,
            scheduled_time=datetime.now(timezone.utc),
            content_type="photo",
            caption="Other",
            status=PostStatus.FAILED
        )
        
        mock_redis.get = AsyncMock(return_value=other_post.model_dump_json())
        
        with patch("api.routes.scheduler.get_redis", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await remove_from_dlq(
                    post_id=other_post.id,
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 403


# ==================== SCHEDULE POST WITH FILE TESTS ====================

class TestSchedulePostWithFile:
    """Test schedule_post_with_file endpoint."""
    
    @pytest.mark.asyncio
    async def test_schedule_with_file_success(self, mock_user, mock_subscription_service):
        """Test scheduling post with file upload."""
        from api.routes.scheduler import schedule_post_with_file
        from workers.post_scheduler import Platform, PostStatus, ScheduledPost
        
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file = MagicMock()
        
        scheduled_post = ScheduledPost(
            id=str(uuid4()),
            user_id="user-123",
            platform=Platform.INSTAGRAM,
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="video",
            caption="Test",
            status=PostStatus.SCHEDULED
        )
        
        with patch("api.routes.scheduler.os.makedirs"), \
             patch("api.routes.scheduler.shutil.copyfileobj"), \
             patch("api.routes.scheduler.scheduler") as mock_scheduler, \
             patch("api.routes.scheduler.settings") as mock_settings:
            
            mock_settings.DATA_DIR = "/tmp/data"
            mock_scheduler.schedule = AsyncMock(return_value=scheduled_post)
            
            future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            
            result = await schedule_post_with_file(
                platform="instagram",
                scheduled_time=future_time,
                content_type="video",
                caption="Test caption",
                hashtags="tag1,tag2",
                account_name=None,
                file=mock_file,
                current_user=mock_user,
                service=mock_subscription_service
            )
            
            assert result.platform == "instagram"
            assert result.status == "scheduled"
    
    @pytest.mark.asyncio
    async def test_schedule_with_file_invalid_date_format(self, mock_user, mock_subscription_service):
        """Test scheduling with invalid date format."""
        from api.routes.scheduler import schedule_post_with_file
        
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post_with_file(
                platform="instagram",
                scheduled_time="invalid-date",
                content_type="video",
                caption="Test",
                hashtags="",
                account_name=None,
                file=mock_file,
                current_user=mock_user,
                service=mock_subscription_service
            )
        
        assert exc_info.value.status_code == 400
        assert "data" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_schedule_with_file_past_date(self, mock_user, mock_subscription_service):
        """Test scheduling with past date."""
        from api.routes.scheduler import schedule_post_with_file
        
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        
        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post_with_file(
                platform="instagram",
                scheduled_time=past_time,
                content_type="video",
                caption="Test",
                hashtags="",
                account_name=None,
                file=mock_file,
                current_user=mock_user,
                service=mock_subscription_service
            )
        
        assert exc_info.value.status_code == 400
        assert "futura" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_schedule_with_file_limit_exceeded(self, mock_user, mock_subscription_service):
        """Test scheduling when limit exceeded."""
        from api.routes.scheduler import schedule_post_with_file
        
        mock_subscription_service.can_use_feature = AsyncMock(return_value=False)
        
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        
        future_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post_with_file(
                platform="instagram",
                scheduled_time=future_time,
                content_type="video",
                caption="Test",
                hashtags="",
                account_name=None,
                file=mock_file,
                current_user=mock_user,
                service=mock_subscription_service
            )
        
        assert exc_info.value.status_code == 402


# ==================== STATS TESTS ====================

class TestGetSchedulerStatsExtended:
    """Extended tests for get_scheduler_stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_stats_counts_retrying_posts(self, mock_user):
        """Test stats correctly counts retrying posts."""
        from api.routes.scheduler import get_scheduler_stats
        from workers.post_scheduler import Platform, PostStatus, ScheduledPost

        # Post with retry_count > 0 but still scheduled
        retrying_post = ScheduledPost(
            id=str(uuid4()),
            user_id="user-123",
            platform=Platform.INSTAGRAM,
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="photo",
            caption="Test",
            status=PostStatus.SCHEDULED,
            retry_count=2
        )
        
        # Regular scheduled post
        regular_post = ScheduledPost(
            id=str(uuid4()),
            user_id="user-123",
            platform=Platform.TIKTOK,
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            content_type="video",
            caption="Test",
            status=PostStatus.SCHEDULED,
            retry_count=0
        )
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_user_posts = AsyncMock(return_value=[retrying_post, regular_post])
            
            result = await get_scheduler_stats(current_user=mock_user)
            
            assert result["retrying"] == 1
            assert result["scheduled"] == 1
    
    @pytest.mark.asyncio
    async def test_stats_counts_by_platform(self, mock_user):
        """Test stats counts posts by platform."""
        from api.routes.scheduler import get_scheduler_stats
        from workers.post_scheduler import Platform, PostStatus, ScheduledPost
        
        posts = [
            ScheduledPost(
                id=str(uuid4()),
                user_id="user-123",
                platform=Platform.INSTAGRAM,
                scheduled_time=datetime.now(timezone.utc),
                content_type="photo",
                caption="Test",
                status=PostStatus.PUBLISHED
            ),
            ScheduledPost(
                id=str(uuid4()),
                user_id="user-123",
                platform=Platform.INSTAGRAM,
                scheduled_time=datetime.now(timezone.utc),
                content_type="reel",
                caption="Test",
                status=PostStatus.SCHEDULED
            ),
            ScheduledPost(
                id=str(uuid4()),
                user_id="user-123",
                platform=Platform.TIKTOK,
                scheduled_time=datetime.now(timezone.utc),
                content_type="video",
                caption="Test",
                status=PostStatus.FAILED
            )
        ]
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_user_posts = AsyncMock(return_value=posts)
            
            result = await get_scheduler_stats(current_user=mock_user)
            
            assert result["by_platform"]["instagram"] == 2
            assert result["by_platform"]["tiktok"] == 1
    
    @pytest.mark.asyncio
    async def test_stats_counts_cancelled_posts(self, mock_user):
        """Test stats counts cancelled posts."""
        from api.routes.scheduler import get_scheduler_stats
        from workers.post_scheduler import Platform, PostStatus, ScheduledPost
        
        cancelled_post = ScheduledPost(
            id=str(uuid4()),
            user_id="user-123",
            platform=Platform.YOUTUBE,
            scheduled_time=datetime.now(timezone.utc),
            content_type="video",
            caption="Test",
            status=PostStatus.CANCELLED
        )
        
        with patch("api.routes.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.get_user_posts = AsyncMock(return_value=[cancelled_post])
            
            result = await get_scheduler_stats(current_user=mock_user)
            
            assert result["cancelled"] == 1
