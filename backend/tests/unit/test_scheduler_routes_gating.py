from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_schedule_post_limit_exceeded():
    """Test schedule_post when limit is exceeded"""
    from api.routes.scheduler import SchedulePostRequest, schedule_post

    # Mock dependencies
    mock_service = AsyncMock()
    mock_service.can_use_feature = AsyncMock(return_value=False)
    
    current_user = {"id": "user-123"}
    
    data = SchedulePostRequest(
        platform="instagram",
        scheduled_time=datetime.now(timezone.utc) + timedelta(days=1),
        content_type="photo",
        caption="Test post"
    )
    
    # Expect HTTPException 402
    with pytest.raises(HTTPException) as exc_info:
        await schedule_post(
            data=data,
            current_user=current_user,
            service=mock_service
        )
    
    assert exc_info.value.status_code == 402
    assert "Limite de posts atingido" in exc_info.value.detail
    
    # Verify service call
    mock_service.can_use_feature.assert_called_once_with(
        "user-123",
        "social_posts",
        increment=1
    )

@pytest.mark.asyncio
async def test_schedule_post_success():
    """Test schedule_post when limit is not exceeded"""
    from api.routes.scheduler import SchedulePostRequest, schedule_post
    from workers.post_scheduler import Platform, PostStatus

    # Mock dependencies
    mock_service = AsyncMock()
    mock_service.can_use_feature = AsyncMock(return_value=True)
    
    current_user = {"id": "user-123"}
    
    data = SchedulePostRequest(
        platform="instagram",
        scheduled_time=datetime.now(timezone.utc) + timedelta(days=1),
        content_type="photo",
        caption="Test post"
    )
    
    # Mock scheduler service
    with patch('api.routes.scheduler.scheduler') as mock_scheduler:
        mock_scheduled_post = MagicMock()
        mock_scheduled_post.id = "post-123"
        mock_scheduled_post.platform = Platform.INSTAGRAM
        mock_scheduled_post.scheduled_time = data.scheduled_time
        mock_scheduled_post.status = PostStatus.SCHEDULED
        mock_scheduled_post.content_type = "photo"
        
        mock_scheduler.schedule = AsyncMock(return_value=mock_scheduled_post)
        
        response = await schedule_post(
            data=data,
            current_user=current_user,
            service=mock_service
        )
        
        assert response.platform == "instagram"
        
        # Verify service call
        mock_service.can_use_feature.assert_called_once_with(
            "user-123",
            "social_posts",
            increment=1
        )
