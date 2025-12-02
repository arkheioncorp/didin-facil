"""
Testes para api/routes/scheduler.py
Scheduler Routes - Agendamento de posts em redes sociais
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.scheduler import (BulkActionRequest, SchedulePostRequest,
                                  SchedulePostResponse, _classify_error)

# ==================== TEST MODELS ====================

class TestSchedulePostRequest:
    """Testes para modelo SchedulePostRequest."""

    def test_minimal_request(self):
        """Request com campos mínimos."""
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        request = SchedulePostRequest(
            platform="instagram",
            scheduled_time=future,
            content_type="photo"
        )
        
        assert request.platform == "instagram"
        assert request.caption == ""
        assert request.hashtags == []

    def test_full_request(self):
        """Request com todos os campos."""
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        request = SchedulePostRequest(
            platform="tiktok",
            scheduled_time=future,
            content_type="video",
            caption="Test caption",
            hashtags=["test", "video"],
            account_name="my_account",
            platform_config={"duration": 60}
        )
        
        assert request.caption == "Test caption"
        assert len(request.hashtags) == 2
        assert request.platform_config["duration"] == 60


class TestSchedulePostResponse:
    """Testes para modelo SchedulePostResponse."""

    def test_response(self):
        """Response completo."""
        response = SchedulePostResponse(
            id="post_123",
            platform="instagram",
            scheduled_time=datetime.now(timezone.utc),
            status="scheduled",
            content_type="reel"
        )
        
        assert response.id == "post_123"
        assert response.status == "scheduled"


class TestBulkActionRequest:
    """Testes para modelo BulkActionRequest."""

    def test_with_ids(self):
        """Request com lista de IDs."""
        request = BulkActionRequest(ids=["id1", "id2", "id3"])
        
        assert len(request.ids) == 3

    def test_empty_ids(self):
        """Request sem IDs."""
        request = BulkActionRequest(ids=[])
        
        assert request.ids == []


# ==================== TEST CLASSIFY ERROR ====================

class TestClassifyError:
    """Testes para função _classify_error."""

    def test_rate_limit_error(self):
        """Deve classificar erro de rate limit."""
        assert _classify_error("Rate limit exceeded") == "rate_limit"
        assert _classify_error("too many requests") == "rate_limit"
        assert _classify_error("HTTP 429 error") == "rate_limit"

    def test_auth_error(self):
        """Deve classificar erro de autenticação."""
        assert _classify_error("Authentication failed") == "auth_error"
        assert _classify_error("Invalid token") == "auth_error"
        assert _classify_error("HTTP 401 Unauthorized") == "auth_error"
        assert _classify_error("403 Forbidden") == "auth_error"
        assert _classify_error("Please login again") == "auth_error"

    def test_network_error(self):
        """Deve classificar erro de rede."""
        assert _classify_error("Network error") == "network_error"
        assert _classify_error("Connection timeout") == "network_error"
        assert _classify_error("Socket closed") == "network_error"

    def test_content_error(self):
        """Deve classificar erro de conteúdo."""
        assert _classify_error("Invalid media format") == "content_error"
        assert _classify_error("File too large") == "content_error"
        assert _classify_error("Invalid file size") == "content_error"

    def test_quota_error(self):
        """Deve classificar erro de quota."""
        assert _classify_error("Quota exceeded") == "quota_exceeded"
        assert _classify_error("Daily limit exceeded") == "quota_exceeded"

    def test_unknown_error(self):
        """Deve retornar unknown para erros não classificados."""
        assert _classify_error("Some random error") == "unknown"
        assert _classify_error("") == "unknown"


# ==================== TEST SCHEDULE POST ENDPOINT ====================

class TestSchedulePostEndpoint:
    """Testes para endpoint schedule_post."""

    @pytest.fixture
    def current_user(self):
        return {"id": "user_123"}

    @pytest.fixture
    def mock_scheduler(self):
        with patch('api.routes.scheduler.scheduler') as m:
            yield m

    @pytest.mark.asyncio
    async def test_schedule_post_success(self, mock_scheduler, current_user):
        """Deve agendar post com sucesso."""
        from api.routes.scheduler import schedule_post
        from workers.post_scheduler import Platform, PostStatus, ScheduledPost
        
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        
        mock_post = MagicMock()
        mock_post.id = "post_123"
        mock_post.platform = Platform.INSTAGRAM
        mock_post.scheduled_time = future
        mock_post.status = PostStatus.SCHEDULED
        mock_post.content_type = "photo"
        
        mock_scheduler.schedule = AsyncMock(return_value=mock_post)
        
        request = SchedulePostRequest(
            platform="instagram",
            scheduled_time=future,
            content_type="photo",
            caption="Test"
        )
        
        result = await schedule_post(request, current_user)
        
        assert result.id == "post_123"
        assert result.platform == "instagram"

    @pytest.mark.asyncio
    async def test_schedule_post_invalid_platform(self, mock_scheduler, current_user):
        """Plataforma inválida deve retornar 400."""
        from api.routes.scheduler import schedule_post
        from fastapi import HTTPException
        
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        
        request = SchedulePostRequest(
            platform="invalid_platform",
            scheduled_time=future,
            content_type="photo"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post(request, current_user)
        
        assert exc_info.value.status_code == 400
        assert "Plataforma inválida" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_schedule_post_past_time(self, mock_scheduler, current_user):
        """Data passada deve retornar 400."""
        from api.routes.scheduler import schedule_post
        from fastapi import HTTPException
        
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        
        request = SchedulePostRequest(
            platform="instagram",
            scheduled_time=past,
            content_type="photo"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post(request, current_user)
        
        assert exc_info.value.status_code == 400
        assert "deve ser futura" in exc_info.value.detail


# ==================== TEST LIST POSTS ENDPOINT ====================

class TestListPostsEndpoint:
    """Testes para endpoint list_scheduled_posts."""

    @pytest.fixture
    def current_user(self):
        return {"id": "user_123"}

    @pytest.mark.asyncio
    @patch('api.routes.scheduler.scheduler')
    async def test_list_posts_success(self, mock_scheduler, current_user):
        """Deve listar posts agendados."""
        from api.routes.scheduler import list_scheduled_posts
        from workers.post_scheduler import Platform, PostStatus
        
        mock_post = MagicMock()
        mock_post.id = "post_1"
        mock_post.platform = Platform.INSTAGRAM
        mock_post.scheduled_time = datetime.now(timezone.utc)
        mock_post.status = PostStatus.SCHEDULED
        mock_post.content_type = "photo"
        mock_post.caption = "Test caption"
        mock_post.created_at = datetime.now(timezone.utc)
        mock_post.published_at = None
        
        mock_scheduler.get_user_posts = AsyncMock(return_value=[mock_post])
        
        result = await list_scheduled_posts(
            status=None,
            limit=50,
            current_user=current_user
        )
        
        assert "posts" in result
        assert len(result["posts"]) == 1
        assert result["posts"][0]["id"] == "post_1"

    @pytest.mark.asyncio
    @patch('api.routes.scheduler.scheduler')
    async def test_list_posts_with_status_filter(self, mock_scheduler, current_user):
        """Deve filtrar por status."""
        from api.routes.scheduler import list_scheduled_posts
        
        mock_scheduler.get_user_posts = AsyncMock(return_value=[])
        
        result = await list_scheduled_posts(
            status="published",
            limit=50,
            current_user=current_user
        )
        
        assert result["posts"] == []

    @pytest.mark.asyncio
    @patch('api.routes.scheduler.scheduler')
    async def test_list_posts_invalid_status(self, mock_scheduler, current_user):
        """Status inválido deve retornar 400."""
        from api.routes.scheduler import list_scheduled_posts
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await list_scheduled_posts(
                status="invalid_status",
                limit=50,
                current_user=current_user
            )
        
        assert exc_info.value.status_code == 400


# ==================== TEST CANCEL POST ENDPOINT ====================

class TestCancelPostEndpoint:
    """Testes para endpoint cancel_post."""

    @pytest.fixture
    def current_user(self):
        return {"id": "user_123"}

    @pytest.mark.asyncio
    @patch('api.routes.scheduler.scheduler')
    async def test_cancel_post_success(self, mock_scheduler, current_user):
        """Deve cancelar post com sucesso."""
        from api.routes.scheduler import cancel_post
        
        mock_scheduler.cancel = AsyncMock(return_value=True)
        
        result = await cancel_post("post_123", current_user)
        
        assert result["status"] == "cancelled"
        assert result["id"] == "post_123"

    @pytest.mark.asyncio
    @patch('api.routes.scheduler.scheduler')
    async def test_cancel_post_not_found(self, mock_scheduler, current_user):
        """Post não encontrado deve retornar 404."""
        from api.routes.scheduler import cancel_post
        from fastapi import HTTPException
        
        mock_scheduler.cancel = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await cancel_post("nonexistent", current_user)
        
        assert exc_info.value.status_code == 404


# ==================== TEST GET STATS ENDPOINT ====================

class TestGetStatsEndpoint:
    """Testes para endpoint get_scheduler_stats."""

    @pytest.fixture
    def current_user(self):
        return {"id": "user_123"}

    @pytest.mark.asyncio
    @patch('api.routes.scheduler.scheduler')
    async def test_get_stats_success(self, mock_scheduler, current_user):
        """Deve retornar estatísticas corretas."""
        from api.routes.scheduler import get_scheduler_stats
        from workers.post_scheduler import Platform, PostStatus

        # Criar mock posts com diferentes status
        mock_posts = []
        
        # Post agendado
        p1 = MagicMock()
        p1.status = PostStatus.SCHEDULED
        p1.platform = Platform.INSTAGRAM
        p1.retry_count = 0
        mock_posts.append(p1)
        
        # Post publicado
        p2 = MagicMock()
        p2.status = PostStatus.PUBLISHED
        p2.platform = Platform.TIKTOK
        p2.retry_count = 0
        mock_posts.append(p2)
        
        # Post com retry
        p3 = MagicMock()
        p3.status = PostStatus.SCHEDULED
        p3.platform = Platform.INSTAGRAM
        p3.retry_count = 2
        mock_posts.append(p3)
        
        mock_scheduler.get_user_posts = AsyncMock(return_value=mock_posts)
        
        result = await get_scheduler_stats(current_user)
        
        assert result["total"] == 3
        assert result["scheduled"] == 1
        assert result["published"] == 1
        assert result["retrying"] == 1
        assert "instagram" in result["by_platform"]


# ==================== TEST DLQ ENDPOINTS ====================

class TestDLQEndpoints:
    """Testes para endpoints de Dead Letter Queue."""

    @pytest.fixture
    def current_user(self):
        return {"id": "user_123"}

    @pytest.mark.asyncio
    @patch('api.routes.scheduler.scheduler')
    async def test_get_dlq_posts(self, mock_scheduler, current_user):
        """Deve listar posts na DLQ."""
        from api.routes.scheduler import get_dlq_posts
        from workers.post_scheduler import Platform, PostStatus
        
        mock_post = MagicMock()
        mock_post.id = "dlq_post_1"
        mock_post.user_id = "user_123"
        mock_post.platform = Platform.INSTAGRAM
        mock_post.scheduled_time = datetime.now(timezone.utc)
        mock_post.retry_count = 3
        mock_post.error_message = "Rate limit exceeded"
        mock_post.content_type = "video"
        mock_post.caption = "Failed post"
        mock_post.platform_config = {}
        
        mock_scheduler.get_dlq_posts = AsyncMock(return_value=[mock_post])
        
        result = await get_dlq_posts(limit=50, current_user=current_user)
        
        assert len(result) == 1
        assert result[0]["id"] == "dlq_post_1"
        assert result[0]["error_type"] == "rate_limit"

    @pytest.mark.asyncio
    @patch('api.routes.scheduler.scheduler')
    async def test_get_dlq_stats(self, mock_scheduler, current_user):
        """Deve retornar estatísticas da DLQ."""
        from api.routes.scheduler import get_dlq_stats
        from workers.post_scheduler import Platform
        
        mock_post = MagicMock()
        mock_post.user_id = "user_123"
        mock_post.platform = Platform.INSTAGRAM
        mock_post.error_message = "Network error"
        mock_post.scheduled_time = datetime.now(timezone.utc)
        
        mock_scheduler.get_dlq_posts = AsyncMock(return_value=[mock_post])
        
        result = await get_dlq_stats(current_user)
        
        assert result["total"] == 1
        assert "instagram" in result["by_platform"]
        assert "network_error" in result["by_error_type"]

    @pytest.mark.asyncio
    @patch('shared.redis.get_redis')
    @patch('api.routes.scheduler.scheduler')
    async def test_retry_dlq_post_success(self, mock_scheduler, mock_get_redis, current_user):
        """Deve reagendar post da DLQ."""
        from api.routes.scheduler import retry_dlq_post
        from workers.post_scheduler import ScheduledPost
        
        mock_redis = AsyncMock()
        mock_post_data = {
            "id": "dlq_post_1",
            "user_id": "user_123",
            "platform": "instagram",
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "content_type": "photo",
            "caption": "test",
            "hashtags": [],
            "status": "failed",
            "retry_count": 3
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(mock_post_data))
        mock_get_redis.return_value = mock_redis
        
        mock_scheduler.retry_dlq_post = AsyncMock(return_value=True)
        
        result = await retry_dlq_post("dlq_post_1", current_user)
        
        assert result["status"] == "rescheduled"

    @pytest.mark.asyncio
    @patch('shared.redis.get_redis')
    async def test_retry_dlq_post_not_found(self, mock_get_redis, current_user):
        """Post não encontrado deve retornar 404."""
        from api.routes.scheduler import retry_dlq_post
        from fastapi import HTTPException
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_get_redis.return_value = mock_redis
        
        with pytest.raises(HTTPException) as exc_info:
            await retry_dlq_post("nonexistent", current_user)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch('shared.redis.get_redis')
    async def test_retry_dlq_post_unauthorized(self, mock_get_redis, current_user):
        """Usuário não autorizado deve retornar 403."""
        from api.routes.scheduler import retry_dlq_post
        from fastapi import HTTPException
        
        mock_redis = AsyncMock()
        mock_post_data = {
            "id": "dlq_post_1",
            "user_id": "other_user",  # Diferente do current_user
            "platform": "instagram",
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "content_type": "photo",
            "caption": "test",
            "hashtags": [],
            "status": "failed",
            "retry_count": 3
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(mock_post_data))
        mock_get_redis.return_value = mock_redis
        
        with pytest.raises(HTTPException) as exc_info:
            await retry_dlq_post("dlq_post_1", current_user)
        
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch('shared.redis.get_redis')
    async def test_remove_from_dlq_success(self, mock_get_redis, current_user):
        """Deve remover post da DLQ."""
        from api.routes.scheduler import remove_from_dlq
        
        mock_redis = AsyncMock()
        mock_post_data = {
            "id": "dlq_post_1",
            "user_id": "user_123",
            "platform": "instagram",
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "content_type": "photo",
            "caption": "test",
            "hashtags": [],
            "status": "failed",
            "retry_count": 3
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(mock_post_data))
        mock_redis.lrem = AsyncMock()
        mock_redis.delete = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        result = await remove_from_dlq("dlq_post_1", current_user)
        
        assert result["status"] == "deleted"
        mock_redis.lrem.assert_called_once()
        mock_redis.delete.assert_called_once()


# ==================== TEST BULK ACTIONS ====================

class TestBulkActions:
    """Testes para ações em massa na DLQ."""

    @pytest.fixture
    def current_user(self):
        return {"id": "user_123"}

    @pytest.mark.asyncio
    @patch('shared.redis.get_redis')
    @patch('api.routes.scheduler.scheduler')
    async def test_retry_all_dlq_posts(
        self, mock_scheduler, mock_get_redis, current_user
    ):
        """Deve reagendar múltiplos posts."""
        from api.routes.scheduler import retry_all_dlq_posts
        
        mock_redis = AsyncMock()
        mock_post_data = {
            "id": "post_1",
            "user_id": "user_123",
            "platform": "instagram",
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "content_type": "photo",
            "caption": "test",
            "hashtags": [],
            "status": "failed",
            "retry_count": 3
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(mock_post_data))
        mock_get_redis.return_value = mock_redis
        mock_scheduler.retry_dlq_post = AsyncMock(return_value=True)
        
        request = BulkActionRequest(ids=["post_1", "post_2"])
        
        result = await retry_all_dlq_posts(request, current_user)
        
        assert result["status"] == "completed"
        assert result["success"] >= 1

    @pytest.mark.asyncio
    @patch('shared.redis.get_redis')
    async def test_delete_all_dlq_posts(self, mock_get_redis, current_user):
        """Deve deletar múltiplos posts."""
        from api.routes.scheduler import delete_all_dlq_posts
        
        mock_redis = AsyncMock()
        mock_post_data = {
            "id": "post_1",
            "user_id": "user_123",
            "platform": "instagram",
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "content_type": "photo",
            "caption": "test",
            "hashtags": [],
            "status": "failed",
            "retry_count": 3
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(mock_post_data))
        mock_redis.lrem = AsyncMock()
        mock_redis.delete = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        request = BulkActionRequest(ids=["post_1"])
        
        result = await delete_all_dlq_posts(request, current_user)
        
        assert result["status"] == "completed"
        assert result["deleted"] == 1


# ==================== TEST SCHEDULE POST WITH FILE ====================

class TestSchedulePostWithFile:
    """Testes para endpoint schedule_post_with_file."""

    @pytest.fixture
    def current_user(self):
        return {"id": "user_123"}

    @pytest.mark.asyncio
    @patch('api.routes.scheduler.scheduler')
    @patch('api.routes.scheduler.shutil')
    @patch('api.routes.scheduler.os')
    async def test_schedule_with_file_invalid_platform(
        self, mock_os, mock_shutil, mock_scheduler, current_user
    ):
        """Plataforma inválida deve retornar 400."""
        from io import BytesIO

        from api.routes.scheduler import schedule_post_with_file
        from fastapi import HTTPException, UploadFile
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.mp4"
        mock_file.file = BytesIO(b"test content")
        
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post_with_file(
                platform="invalid",
                scheduled_time=future,
                content_type="video",
                caption="Test",
                hashtags="",
                account_name=None,
                file=mock_file,
                current_user=current_user
            )
        
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch('api.routes.scheduler.scheduler')
    async def test_schedule_with_file_invalid_date(
        self, mock_scheduler, current_user
    ):
        """Data inválida deve retornar 400."""
        from io import BytesIO

        from api.routes.scheduler import schedule_post_with_file
        from fastapi import HTTPException, UploadFile
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.mp4"
        mock_file.file = BytesIO(b"test content")
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post_with_file(
                platform="instagram",
                scheduled_time="invalid-date",
                content_type="video",
                caption="Test",
                hashtags="",
                account_name=None,
                file=mock_file,
                current_user=current_user
            )
        
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch('api.routes.scheduler.scheduler')
    async def test_schedule_with_file_past_date(
        self, mock_scheduler, current_user
    ):
        """Data passada deve retornar 400."""
        from io import BytesIO

        from api.routes.scheduler import schedule_post_with_file
        from fastapi import HTTPException, UploadFile
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.mp4"
        mock_file.file = BytesIO(b"test content")
        
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        with pytest.raises(HTTPException) as exc_info:
            await schedule_post_with_file(
                platform="instagram",
                scheduled_time=past,
                content_type="video",
                caption="Test",
                hashtags="",
                account_name=None,
                file=mock_file,
                current_user=current_user
            )
        
        assert exc_info.value.status_code == 400
