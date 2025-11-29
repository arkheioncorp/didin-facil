"""
Tests for Scheduler Routes
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from datetime import datetime, timedelta


class MockUser:
    id = "user_123"
    email = "test@example.com"


class MockScheduledPost:
    id = "post_123"
    platform = MagicMock(value="instagram")
    scheduled_time = datetime.utcnow() + timedelta(hours=1)
    status = MagicMock(value="scheduled")
    content_type = "photo"
    caption = "Test caption"
    created_at = datetime.utcnow()
    published_at = None


@pytest.fixture
def mock_current_user():
    return MockUser()


@pytest.fixture
def mock_scheduler():
    scheduler = AsyncMock()
    scheduler.schedule.return_value = MockScheduledPost()
    scheduler.get_user_posts.return_value = [MockScheduledPost()]
    scheduler.cancel.return_value = True
    return scheduler


@pytest.mark.asyncio
async def test_schedule_post_invalid_platform(mock_current_user):
    from api.routes.scheduler import schedule_post, SchedulePostRequest
    
    data = SchedulePostRequest(
        platform="invalid_platform",
        scheduled_time=datetime.utcnow() + timedelta(hours=1),
        content_type="photo",
        caption="Test"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await schedule_post(data, mock_current_user)
    
    assert exc_info.value.status_code == 400
    assert "Plataforma inválida" in exc_info.value.detail


@pytest.mark.asyncio
async def test_schedule_post_past_date(mock_current_user):
    from api.routes.scheduler import schedule_post, SchedulePostRequest
    
    with patch("api.routes.scheduler.Platform") as mock_platform:
        mock_platform.return_value = MagicMock(value="instagram")
        
        data = SchedulePostRequest(
            platform="instagram",
            scheduled_time=datetime.utcnow() - timedelta(hours=1),
            content_type="photo",
            caption="Test"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post(data, mock_current_user)
        
        assert exc_info.value.status_code == 400
        assert "futura" in exc_info.value.detail


@pytest.mark.asyncio
async def test_schedule_post_success(mock_current_user, mock_scheduler):
    from api.routes.scheduler import schedule_post, SchedulePostRequest
    
    with patch("api.routes.scheduler.Platform") as mock_platform, \
         patch("api.routes.scheduler.ScheduledPost"), \
         patch("api.routes.scheduler.scheduler", mock_scheduler):
        
        mock_platform.return_value = MagicMock(value="instagram")
        
        data = SchedulePostRequest(
            platform="instagram",
            scheduled_time=datetime.utcnow() + timedelta(hours=1),
            content_type="photo",
            caption="Test caption"
        )
        
        result = await schedule_post(data, mock_current_user)
        
        assert result.id == "post_123"
        assert result.status == "scheduled"


@pytest.mark.asyncio
async def test_list_scheduled_posts(mock_current_user, mock_scheduler):
    from api.routes.scheduler import list_scheduled_posts
    
    with patch("api.routes.scheduler.scheduler", mock_scheduler):
        result = await list_scheduled_posts(
            status=None,
            limit=50,
            current_user=mock_current_user
        )
        
        assert "posts" in result
        assert result["total"] == 1
        mock_scheduler.get_user_posts.assert_called_once()


@pytest.mark.asyncio
async def test_list_scheduled_posts_invalid_status(mock_current_user):
    from api.routes.scheduler import list_scheduled_posts
    
    with pytest.raises(HTTPException) as exc_info:
        await list_scheduled_posts(
            status="invalid_status",
            limit=50,
            current_user=mock_current_user
        )
    
    assert exc_info.value.status_code == 400
    assert "Status inválido" in exc_info.value.detail


@pytest.mark.asyncio
async def test_cancel_post_success(mock_current_user, mock_scheduler):
    from api.routes.scheduler import cancel_post
    
    with patch("api.routes.scheduler.scheduler", mock_scheduler):
        result = await cancel_post("post_123", mock_current_user)
        
        assert result["status"] == "cancelled"
        assert result["id"] == "post_123"
        mock_scheduler.cancel.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_post_not_found(mock_current_user, mock_scheduler):
    from api.routes.scheduler import cancel_post
    
    mock_scheduler.cancel.return_value = False
    
    with patch("api.routes.scheduler.scheduler", mock_scheduler):
        with pytest.raises(HTTPException) as exc_info:
            await cancel_post("nonexistent", mock_current_user)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_scheduler_stats(mock_current_user, mock_scheduler):
    from api.routes.scheduler import get_scheduler_stats
    
    with patch("api.routes.scheduler.scheduler", mock_scheduler):
        result = await get_scheduler_stats(mock_current_user)
        
        assert "total" in result
        assert "scheduled" in result
        assert "published" in result
        assert "failed" in result
        assert "by_platform" in result


@pytest.mark.asyncio
async def test_get_dlq_posts(mock_current_user, mock_scheduler):
    """Test getting posts from Dead Letter Queue."""
    from api.routes.scheduler import get_dlq_posts
    
    mock_post = MagicMock()
    mock_post.id = "dlq_post_123"
    mock_post.platform.value = "instagram"
    mock_post.scheduled_time.isoformat.return_value = "2024-01-01T12:00:00"
    mock_post.status.value = "failed"
    mock_post.content_type = "photo"
    mock_post.caption = "Test caption"
    mock_post.retry_count = 3
    mock_post.retry_errors = ["Error 1", "Error 2", "Error 3"]
    mock_post.error_message = "Final error"
    mock_post.user_id = "user_123"
    mock_post.platform_config = {}
    
    mock_scheduler.get_dlq_posts.return_value = [mock_post]
    
    with patch("api.routes.scheduler.scheduler", mock_scheduler):
        result = await get_dlq_posts(limit=50, current_user=mock_current_user)
        
        # A função retorna uma lista diretamente
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "dlq_post_123"
        mock_scheduler.get_dlq_posts.assert_called_once_with(limit=50)


@pytest.mark.asyncio
async def test_get_dlq_stats(mock_current_user, mock_scheduler):
    """Test getting DLQ statistics."""
    from api.routes.scheduler import get_dlq_stats
    
    mock_post = MagicMock()
    mock_post.platform.value = "instagram"
    mock_post.user_id = "user_123"
    mock_post.error_message = "RateLimitError: Too many requests"
    mock_post.scheduled_time = datetime.utcnow() - timedelta(hours=1)
    
    mock_scheduler.get_dlq_posts.return_value = [mock_post]
    
    with patch("api.routes.scheduler.scheduler", mock_scheduler):
        result = await get_dlq_stats(mock_current_user)
        
        assert "total" in result
        assert "by_platform" in result
        assert "by_error_type" in result
        assert result["total"] == 1


@pytest.mark.asyncio
async def test_retry_dlq_post_success(mock_current_user, mock_scheduler):
    """Test retrying a DLQ post."""
    from api.routes.scheduler import retry_dlq_post
    
    mock_post_data = '{"user_id": "user_123", "platform": "instagram", "scheduled_time": "2024-01-01T12:00:00", "content_type": "photo", "caption": "Test"}'
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = mock_post_data
    
    mock_scheduler.retry_dlq_post.return_value = True
    
    with patch("shared.redis.get_redis", return_value=mock_redis), \
         patch("api.routes.scheduler.scheduler", mock_scheduler), \
         patch("api.routes.scheduler.ScheduledPost") as mock_model:
        
        mock_model.model_validate_json.return_value = MagicMock(
            user_id="user_123"
        )
        
        result = await retry_dlq_post("post_123", mock_current_user)
        
        assert result["status"] == "rescheduled"
        assert result["id"] == "post_123"


@pytest.mark.asyncio
async def test_retry_dlq_post_not_found(mock_current_user, mock_scheduler):
    """Test retrying a non-existent DLQ post."""
    from api.routes.scheduler import retry_dlq_post
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    
    with patch("shared.redis.get_redis", return_value=mock_redis):
        with pytest.raises(HTTPException) as exc_info:
            await retry_dlq_post("nonexistent", mock_current_user)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_retry_dlq_post_unauthorized(mock_current_user, mock_scheduler):
    """Test retrying a DLQ post that belongs to another user."""
    from api.routes.scheduler import retry_dlq_post
    
    mock_post_data = '{"user_id": "other_user", "platform": "instagram", "scheduled_time": "2024-01-01T12:00:00", "content_type": "photo", "caption": "Test"}'
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = mock_post_data
    
    with patch("shared.redis.get_redis", return_value=mock_redis), \
         patch("api.routes.scheduler.ScheduledPost") as mock_model:
        
        mock_model.model_validate_json.return_value = MagicMock(
            user_id="other_user"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await retry_dlq_post("post_123", mock_current_user)
        
        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_retry_dlq_post_failure(mock_current_user, mock_scheduler):
    """Test retrying a DLQ post when scheduler fails."""
    from api.routes.scheduler import retry_dlq_post
    
    mock_post_data = '{"user_id": "user_123", "platform": "instagram", "scheduled_time": "2024-01-01T12:00:00", "content_type": "photo", "caption": "Test"}'
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = mock_post_data
    
    mock_scheduler.retry_dlq_post.return_value = False
    
    with patch("shared.redis.get_redis", return_value=mock_redis), \
         patch("api.routes.scheduler.scheduler", mock_scheduler), \
         patch("api.routes.scheduler.ScheduledPost") as mock_model:
        
        mock_model.model_validate_json.return_value = MagicMock(
            user_id="user_123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await retry_dlq_post("post_123", mock_current_user)
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_retry_all_dlq_posts(mock_current_user, mock_scheduler):
    """Test bulk retry of DLQ posts."""
    from api.routes.scheduler import retry_all_dlq_posts, BulkActionRequest
    
    mock_post_data = '{"user_id": "user_123", "platform": "instagram"}'
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = mock_post_data
    
    mock_scheduler.retry_dlq_post.return_value = True
    
    with patch("shared.redis.get_redis", return_value=mock_redis), \
         patch("api.routes.scheduler.scheduler", mock_scheduler), \
         patch("api.routes.scheduler.ScheduledPost") as mock_model:
        
        mock_model.model_validate_json.return_value = MagicMock(
            user_id="user_123"
        )
        
        request = BulkActionRequest(ids=["post_1", "post_2"])
        result = await retry_all_dlq_posts(request, mock_current_user)
        
        assert result["status"] == "completed"
        assert result["success"] == 2


@pytest.mark.asyncio
async def test_delete_all_dlq_posts(mock_current_user, mock_scheduler):
    """Test bulk delete of DLQ posts."""
    from api.routes.scheduler import delete_all_dlq_posts, BulkActionRequest
    
    mock_post_data = '{"user_id": "user_123", "platform": "instagram"}'
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = mock_post_data
    mock_redis.delete.return_value = True
    mock_redis.srem.return_value = True
    
    with patch("shared.redis.get_redis", return_value=mock_redis), \
         patch("api.routes.scheduler.ScheduledPost") as mock_model:
        
        mock_model.model_validate_json.return_value = MagicMock(
            user_id="user_123"
        )
        
        request = BulkActionRequest(ids=["post_1", "post_2"])
        result = await delete_all_dlq_posts(request, mock_current_user)
        
        assert result["status"] == "completed"
        assert result["deleted"] == 2

