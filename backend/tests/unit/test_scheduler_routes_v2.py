"""Testes abrangentes para Scheduler Routes."""

import os
from datetime import datetime, timedelta, timezone
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile


class MockPlatform:
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    WHATSAPP = "whatsapp"


class MockPostStatus:
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MockScheduledPost:
    """Mock de ScheduledPost."""
    def __init__(
        self,
        id="post-123",
        user_id="user-123",
        platform="instagram",
        scheduled_time=None,
        content_type="photo",
        caption="Test caption",
        status="scheduled",
        hashtags=None,
        retry_count=0
    ):
        self.id = id
        self.user_id = user_id
        self.platform = MagicMock()
        self.platform.value = platform
        self.scheduled_time = scheduled_time or datetime.now(timezone.utc) + timedelta(hours=1)
        self.content_type = content_type
        self.caption = caption
        self.status = MagicMock()
        self.status.value = status
        self.hashtags = hashtags or []
        self.created_at = datetime.now(timezone.utc)
        self.published_at = None
        self.retry_count = retry_count


@pytest.fixture
def mock_current_user():
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def mock_subscription_service():
    service = AsyncMock()
    service.can_use_feature = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_scheduler():
    scheduler = AsyncMock()
    mock_post = MockScheduledPost()
    scheduler.schedule = AsyncMock(return_value=mock_post)
    scheduler.get_user_posts = AsyncMock(return_value=[mock_post])
    scheduler.cancel = AsyncMock(return_value=True)
    scheduler.get_dlq_posts = AsyncMock(return_value=[])
    return scheduler


class TestModels:
    """Testes para os modelos."""

    def test_schedule_post_request(self):
        """Teste do modelo SchedulePostRequest."""
        from api.routes.scheduler import SchedulePostRequest
        
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        req = SchedulePostRequest(
            platform="instagram",
            scheduled_time=future_time,
            content_type="photo",
            caption="Test caption",
            hashtags=["#test"]
        )
        assert req.platform == "instagram"
        assert req.content_type == "photo"

    def test_schedule_post_response(self):
        """Teste do modelo SchedulePostResponse."""
        from api.routes.scheduler import SchedulePostResponse
        
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        resp = SchedulePostResponse(
            id="post-123",
            platform="instagram",
            scheduled_time=future_time,
            status="scheduled",
            content_type="photo"
        )
        assert resp.id == "post-123"


class TestSchedulePost:
    """Testes para schedule_post."""

    async def test_schedule_post_success(self, mock_current_user, mock_subscription_service, mock_scheduler):
        """Teste de agendamento bem-sucedido."""
        from api.routes.scheduler import SchedulePostRequest, schedule_post
        
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        request = SchedulePostRequest(
            platform="instagram",
            scheduled_time=future_time,
            content_type="photo",
            caption="Test"
        )
        
        with patch("api.routes.scheduler.scheduler", mock_scheduler):
            with patch("api.routes.scheduler.Platform") as mock_platform:
                mock_platform.return_value = "instagram"
                result = await schedule_post(
                    data=request,
                    current_user=mock_current_user,
                    service=mock_subscription_service
                )
        
        assert result.id == "post-123"
        assert result.status == "scheduled"

    async def test_schedule_post_limit_reached(self, mock_current_user, mock_subscription_service):
        """Teste de limite atingido."""
        from api.routes.scheduler import SchedulePostRequest, schedule_post
        
        mock_subscription_service.can_use_feature = AsyncMock(return_value=False)
        
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        request = SchedulePostRequest(
            platform="instagram",
            scheduled_time=future_time,
            content_type="photo"
        )
        
        with pytest.raises(HTTPException) as exc:
            await schedule_post(
                data=request,
                current_user=mock_current_user,
                service=mock_subscription_service
            )
        
        assert exc.value.status_code == 402

    async def test_schedule_post_invalid_platform(self, mock_current_user, mock_subscription_service):
        """Teste de plataforma inválida."""
        from api.routes.scheduler import SchedulePostRequest, schedule_post
        
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        request = SchedulePostRequest(
            platform="invalid_platform",
            scheduled_time=future_time,
            content_type="photo"
        )
        
        with patch("api.routes.scheduler.Platform") as mock_platform:
            mock_platform.side_effect = ValueError("Invalid platform")
            with pytest.raises(HTTPException) as exc:
                await schedule_post(
                    data=request,
                    current_user=mock_current_user,
                    service=mock_subscription_service
                )
        
        assert exc.value.status_code == 400

    async def test_schedule_post_past_date(self, mock_current_user, mock_subscription_service):
        """Teste de data passada."""
        from api.routes.scheduler import SchedulePostRequest, schedule_post
        
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        request = SchedulePostRequest(
            platform="instagram",
            scheduled_time=past_time,
            content_type="photo"
        )
        
        with patch("api.routes.scheduler.Platform"):
            with pytest.raises(HTTPException) as exc:
                await schedule_post(
                    data=request,
                    current_user=mock_current_user,
                    service=mock_subscription_service
                )
        
        assert exc.value.status_code == 400
        assert "futura" in exc.value.detail


class TestListScheduledPosts:
    """Testes para list_scheduled_posts."""

    async def test_list_posts_success(self, mock_current_user, mock_scheduler):
        """Teste de listagem bem-sucedida."""
        from api.routes.scheduler import list_scheduled_posts
        
        with patch("api.routes.scheduler.scheduler", mock_scheduler):
            result = await list_scheduled_posts(
                current_user=mock_current_user
            )
        
        assert "posts" in result
        assert "total" in result
        assert result["total"] == 1

    async def test_list_posts_with_status(self, mock_current_user, mock_scheduler):
        """Teste de listagem com filtro de status."""
        from api.routes.scheduler import list_scheduled_posts
        
        with patch("api.routes.scheduler.scheduler", mock_scheduler):
            with patch("api.routes.scheduler.PostStatus") as mock_status:
                mock_status.return_value = "scheduled"
                result = await list_scheduled_posts(
                    status="scheduled",
                    current_user=mock_current_user
                )
        
        assert "posts" in result

    async def test_list_posts_invalid_status(self, mock_current_user, mock_scheduler):
        """Teste de status inválido."""
        from api.routes.scheduler import list_scheduled_posts
        
        with patch("api.routes.scheduler.scheduler", mock_scheduler):
            with patch("api.routes.scheduler.PostStatus") as mock_status:
                mock_status.side_effect = ValueError("Invalid status")
                with pytest.raises(HTTPException) as exc:
                    await list_scheduled_posts(
                        status="invalid",
                        current_user=mock_current_user
                    )
        
        assert exc.value.status_code == 400


class TestCancelPost:
    """Testes para cancel_post."""

    async def test_cancel_post_success(self, mock_current_user, mock_scheduler):
        """Teste de cancelamento bem-sucedido."""
        from api.routes.scheduler import cancel_post
        
        with patch("api.routes.scheduler.scheduler", mock_scheduler):
            result = await cancel_post(
                post_id="post-123",
                current_user=mock_current_user
            )
        
        assert result["status"] == "cancelled"
        assert result["id"] == "post-123"

    async def test_cancel_post_not_found(self, mock_current_user, mock_scheduler):
        """Teste de post não encontrado."""
        from api.routes.scheduler import cancel_post
        
        mock_scheduler.cancel = AsyncMock(return_value=False)
        
        with patch("api.routes.scheduler.scheduler", mock_scheduler):
            with pytest.raises(HTTPException) as exc:
                await cancel_post(
                    post_id="invalid-id",
                    current_user=mock_current_user
                )
        
        assert exc.value.status_code == 404


class TestGetSchedulerStats:
    """Testes para get_scheduler_stats."""

    async def test_get_stats_empty(self, mock_current_user, mock_scheduler):
        """Teste de estatísticas vazio."""
        from api.routes.scheduler import get_scheduler_stats
        
        mock_scheduler.get_user_posts = AsyncMock(return_value=[])
        
        with patch("api.routes.scheduler.scheduler", mock_scheduler):
            result = await get_scheduler_stats(current_user=mock_current_user)
        
        assert result["total"] == 0
        assert result["scheduled"] == 0

    async def test_get_stats_with_posts(self, mock_current_user, mock_scheduler):
        """Teste de estatísticas com posts."""
        from api.routes.scheduler import get_scheduler_stats
        from workers.post_scheduler import PostStatus

        # Create mock posts with different statuses
        mock_posts = [
            MockScheduledPost(id="1", status="scheduled"),
            MockScheduledPost(id="2", status="published"),
            MockScheduledPost(id="3", status="failed"),
        ]
        
        # Need to set proper status objects
        for post in mock_posts:
            if post.status.value == "scheduled":
                post.status = PostStatus.SCHEDULED
            elif post.status.value == "published":
                post.status = PostStatus.PUBLISHED
            elif post.status.value == "failed":
                post.status = PostStatus.FAILED
        
        mock_scheduler.get_user_posts = AsyncMock(return_value=mock_posts)
        
        with patch("api.routes.scheduler.scheduler", mock_scheduler):
            result = await get_scheduler_stats(current_user=mock_current_user)
        
        assert result["total"] == 3


class TestGetDLQPosts:
    """Testes para get_dlq_posts."""

    async def test_get_dlq_empty(self, mock_current_user, mock_scheduler):
        """Teste de DLQ vazio."""
        from api.routes.scheduler import get_dlq_posts
        
        with patch("api.routes.scheduler.scheduler", mock_scheduler):
            result = await get_dlq_posts(current_user=mock_current_user)
        
        # Result is just from scheduler.get_dlq_posts
        assert result == []


class TestRouterConfig:
    """Testes para configuração do router."""

    def test_router_exists(self):
        """Teste se router existe."""
        from api.routes.scheduler import router
        assert router is not None

    def test_scheduler_exists(self):
        """Teste se scheduler existe."""
        from api.routes.scheduler import scheduler
        assert scheduler is not None
