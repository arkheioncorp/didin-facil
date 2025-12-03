"""
Tests for Social Media Feature Gating
Tests for Instagram, TikTok, and YouTube upload limits
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


@pytest.fixture
def mock_subscription_service():
    """Mock SubscriptionService."""
    service = MagicMock()
    service.can_use_feature = AsyncMock(return_value=False)
    service.increment_usage = AsyncMock()
    return service


@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    return {"id": "user-123", "email": "test@example.com"}


class TestInstagramGating:
    """Tests for Instagram upload gating."""

    @pytest.mark.asyncio
    async def test_instagram_upload_limit_exceeded(
        self,
        mock_subscription_service,
        mock_current_user
    ):
        """Test that Instagram upload returns 402 when limit exceeded."""
        from api.routes.instagram import upload_media

        # Mock Redis
        with patch('api.routes.instagram.get_redis') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get = AsyncMock(
                return_value='{"session": "data"}'
            )
            mock_redis.return_value = mock_redis_instance
            
            # Mock file upload
            mock_file = MagicMock()
            mock_file.filename = "test.jpg"
            mock_file.file = MagicMock()
            
            with pytest.raises(HTTPException) as exc_info:
                await upload_media(
                    username="test_user",
                    caption="Test caption",
                    media_type="photo",
                    file=mock_file,
                    current_user=mock_current_user,
                    service=mock_subscription_service
                )
            
            assert exc_info.value.status_code == 402
            assert "Limite de posts sociais" in exc_info.value.detail
            
            mock_subscription_service.can_use_feature.assert_called_once_with(
                "user-123",
                "social_posts"
            )


class TestTikTokGating:
    """Tests for TikTok upload gating."""

    @pytest.mark.asyncio
    async def test_tiktok_upload_limit_exceeded(
        self,
        mock_subscription_service,
        mock_current_user
    ):
        """Test that TikTok upload returns 402 when limit exceeded."""
        from api.routes.tiktok import upload_video

        # Mock file upload
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file = MagicMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_video(
                account_name="test_account",
                caption="Test caption",
                hashtags="test,video",
                privacy="public",
                file=mock_file,
                current_user=mock_current_user,
                service=mock_subscription_service
            )
        
        assert exc_info.value.status_code == 402
        assert "Limite de posts sociais" in exc_info.value.detail
        
        mock_subscription_service.can_use_feature.assert_called_once_with(
            "user-123",
            "social_posts"
        )


class TestYouTubeGating:
    """Tests for YouTube upload gating."""

    @pytest.mark.asyncio
    async def test_youtube_upload_limit_exceeded(
        self,
        mock_subscription_service,
        mock_current_user
    ):
        """Test that YouTube upload returns 402 when limit exceeded."""
        from api.routes.youtube import upload_video

        # Mock file upload
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file = MagicMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_video(
                account_name="test_account",
                title="Test Video",
                description="Test description",
                tags="test,video",
                privacy="private",
                category="26",
                is_short=False,
                file=mock_file,
                thumbnail=None,
                current_user=mock_current_user,
                service=mock_subscription_service
            )
        
        assert exc_info.value.status_code == 402
        assert "Limite de posts sociais" in exc_info.value.detail
        
        mock_subscription_service.can_use_feature.assert_called_once_with(
            "user-123",
            "social_posts"
        )
