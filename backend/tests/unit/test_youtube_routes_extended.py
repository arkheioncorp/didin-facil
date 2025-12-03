"""
Extended tests for YouTube routes.
Coverage target: 90%+
"""

import json
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ==================== FIXTURES ====================

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {"id": "user123", "email": "test@example.com"}


@pytest.fixture
def mock_subscription_service():
    """Mock subscription service."""
    service = MagicMock()
    service.can_use_feature = AsyncMock(return_value=True)
    service.increment_usage = AsyncMock()
    return service


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    return redis


@pytest.fixture
def mock_youtube_client():
    """Mock YouTube client."""
    client = MagicMock()
    client.authenticate = AsyncMock()
    
    result = MagicMock()
    result.success = True
    result.video_id = "abc123"
    result.url = "https://youtube.com/watch?v=abc123"
    result.error = None
    
    client.upload_video = AsyncMock(return_value=result)
    return client


# ==================== AUTH TESTS ====================

class TestInitAuth:
    """Test init_auth endpoint."""
    
    @pytest.mark.asyncio
    async def test_init_auth_no_credentials(self, mock_user):
        """Test init auth without credentials file."""
        from api.routes.youtube import YouTubeAuthRequest, init_auth
        
        with patch('os.path.exists', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await init_auth(
                    YouTubeAuthRequest(account_name="test"),
                    mock_user
                )
            
            assert exc_info.value.status_code == 400
            assert "credenciais" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_init_auth_success(self, mock_user, mock_youtube_client):
        """Test successful auth initialization."""
        from api.routes.youtube import YouTubeAuthRequest, init_auth
        
        with patch('os.path.exists', return_value=True), \
             patch('os.makedirs'), \
             patch('api.routes.youtube.YouTubeClient', return_value=mock_youtube_client):
            
            result = await init_auth(
                YouTubeAuthRequest(account_name="myaccount"),
                mock_user
            )
            
            assert result["status"] == "success"
            assert result["account_name"] == "myaccount"
    
    @pytest.mark.asyncio
    async def test_init_auth_error(self, mock_user, mock_youtube_client):
        """Test auth initialization error."""
        from api.routes.youtube import YouTubeAuthRequest, init_auth
        
        mock_youtube_client.authenticate = AsyncMock(
            side_effect=Exception("OAuth failed")
        )
        
        with patch('os.path.exists', return_value=True), \
             patch('os.makedirs'), \
             patch('api.routes.youtube.YouTubeClient', return_value=mock_youtube_client):
            
            with pytest.raises(HTTPException) as exc_info:
                await init_auth(
                    YouTubeAuthRequest(account_name="test"),
                    mock_user
                )
            
            assert exc_info.value.status_code == 500


# ==================== ACCOUNTS TESTS ====================

class TestListAccounts:
    """Test list_accounts endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_accounts_no_user(self):
        """Test listing accounts without user (trial mode)."""
        from api.routes.youtube import list_accounts
        
        result = await list_accounts(None)
        assert result == {"accounts": []}
    
    @pytest.mark.asyncio
    async def test_list_accounts_no_tokens_dir(self, mock_user):
        """Test listing accounts when tokens dir doesn't exist."""
        from api.routes.youtube import list_accounts
        
        with patch('os.path.exists', return_value=False):
            result = await list_accounts(mock_user)
            assert result == {"accounts": []}
    
    @pytest.mark.asyncio
    async def test_list_accounts_with_tokens(self, mock_user):
        """Test listing accounts with existing tokens."""
        from api.routes.youtube import list_accounts
        
        mock_files = ["user123_account1.json", "user123_account2.json", "other_user.json"]
        
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=mock_files):
            
            result = await list_accounts(mock_user)
            
            assert "accounts" in result
            assert len(result["accounts"]) == 2
            assert result["accounts"][0]["account_name"] == "account1"


class TestDeleteAccount:
    """Test delete_account endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_account_not_found(self, mock_user):
        """Test deleting non-existent account."""
        from api.routes.youtube import delete_account
        
        with patch('os.path.exists', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await delete_account("nonexistent", mock_user)
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_account_success(self, mock_user):
        """Test successful account deletion."""
        from api.routes.youtube import delete_account
        
        with patch('os.path.exists', return_value=True), \
             patch('os.remove'):
            
            result = await delete_account("myaccount", mock_user)
            
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_delete_account_error(self, mock_user):
        """Test deletion error."""
        from api.routes.youtube import delete_account
        
        with patch('os.path.exists', return_value=True), \
             patch('os.remove', side_effect=OSError("Permission denied")):
            
            with pytest.raises(HTTPException) as exc_info:
                await delete_account("myaccount", mock_user)
            
            assert exc_info.value.status_code == 500


# ==================== UPLOAD TESTS ====================

class TestUploadVideo:
    """Test upload_video endpoint."""
    
    @pytest.mark.asyncio
    async def test_upload_video_limit_reached(self, mock_user, mock_subscription_service):
        """Test upload when subscription limit reached."""
        from api.routes.youtube import upload_video
        
        mock_subscription_service.can_use_feature = AsyncMock(return_value=False)
        
        mock_file = MagicMock()
        mock_file.filename = "video.mp4"
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_video(
                account_name="test",
                title="Test Video",
                file=mock_file,
                current_user=mock_user,
                service=mock_subscription_service
            )
        
        assert exc_info.value.status_code == 402
    
    @pytest.mark.asyncio
    async def test_upload_video_no_token(self, mock_user, mock_subscription_service):
        """Test upload when account not authenticated."""
        from api.routes.youtube import upload_video
        
        mock_file = MagicMock()
        mock_file.filename = "video.mp4"
        
        with patch('os.path.exists', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await upload_video(
                    account_name="test",
                    title="Test Video",
                    file=mock_file,
                    current_user=mock_user,
                    service=mock_subscription_service
                )
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_upload_video_success(
        self, mock_user, mock_subscription_service, mock_youtube_client
    ):
        """Test successful video upload."""
        from api.routes.youtube import upload_video
        
        mock_file = MagicMock()
        mock_file.filename = "video.mp4"
        mock_file.file = MagicMock()
        
        with patch('os.path.exists', return_value=True), \
             patch('os.makedirs'), \
             patch('builtins.open', MagicMock()), \
             patch('shutil.copyfileobj'), \
             patch('os.remove'), \
             patch('api.routes.youtube.YouTubeClient', return_value=mock_youtube_client), \
             patch('api.routes.youtube._track_quota_usage', new_callable=AsyncMock):
            
            result = await upload_video(
                account_name="test",
                title="Test Video",
                description="Test description",
                tags="test,video",
                privacy="private",
                file=mock_file,
                thumbnail=None,
                current_user=mock_user,
                service=mock_subscription_service
            )
            
            assert result["status"] == "success"
            assert result["video_id"] == "abc123"
    
    @pytest.mark.asyncio
    async def test_upload_video_with_thumbnail(
        self, mock_user, mock_subscription_service, mock_youtube_client
    ):
        """Test video upload with thumbnail."""
        from api.routes.youtube import upload_video
        
        mock_file = MagicMock()
        mock_file.filename = "video.mp4"
        mock_file.file = MagicMock()
        
        mock_thumb = MagicMock()
        mock_thumb.filename = "thumb.jpg"
        mock_thumb.file = MagicMock()
        
        with patch('os.path.exists', return_value=True), \
             patch('os.makedirs'), \
             patch('builtins.open', MagicMock()), \
             patch('shutil.copyfileobj'), \
             patch('os.remove'), \
             patch('api.routes.youtube.YouTubeClient', return_value=mock_youtube_client), \
             patch('api.routes.youtube._track_quota_usage', new_callable=AsyncMock):
            
            result = await upload_video(
                account_name="test",
                title="Test Video",
                tags="test",
                file=mock_file,
                thumbnail=mock_thumb,
                current_user=mock_user,
                service=mock_subscription_service
            )
            
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_upload_video_failure(
        self, mock_user, mock_subscription_service, mock_youtube_client
    ):
        """Test video upload failure."""
        from api.routes.youtube import upload_video
        
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Upload failed"
        mock_youtube_client.upload_video = AsyncMock(return_value=mock_result)
        
        mock_file = MagicMock()
        mock_file.filename = "video.mp4"
        mock_file.file = MagicMock()
        
        with patch('os.path.exists', return_value=True), \
             patch('os.makedirs'), \
             patch('builtins.open', MagicMock()), \
             patch('shutil.copyfileobj'), \
             patch('os.remove'), \
             patch('api.routes.youtube.YouTubeClient', return_value=mock_youtube_client):
            
            with pytest.raises(HTTPException) as exc_info:
                await upload_video(
                    account_name="test",
                    title="Test Video",
                    tags="test",
                    file=mock_file,
                    thumbnail=None,
                    current_user=mock_user,
                    service=mock_subscription_service
                )
            
            assert exc_info.value.status_code == 500


# ==================== QUOTA TESTS ====================

class TestQuotaTracking:
    """Test quota tracking functions."""
    
    @pytest.mark.asyncio
    async def test_track_quota_usage_new(self, mock_redis):
        """Test tracking quota for first time."""
        from api.routes.youtube import _track_quota_usage
        
        with patch('api.routes.youtube.get_redis', new_callable=AsyncMock,
                   return_value=mock_redis), \
             patch('api.routes.youtube._check_quota_alerts', new_callable=AsyncMock):
            
            await _track_quota_usage("user123", "upload", 1600)
            
            mock_redis.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_track_quota_usage_existing(self, mock_redis):
        """Test tracking quota with existing data."""
        from api.routes.youtube import _track_quota_usage
        
        existing_data = {"total": 500, "operations": {"list": 500}}
        mock_redis.get = AsyncMock(return_value=json.dumps(existing_data))
        
        with patch('api.routes.youtube.get_redis', new_callable=AsyncMock,
                   return_value=mock_redis), \
             patch('api.routes.youtube._check_quota_alerts', new_callable=AsyncMock):
            
            await _track_quota_usage("user123", "upload", 1600)
            
            mock_redis.set.assert_called()
    
    def test_quota_costs_defined(self):
        """Test quota costs are defined."""
        from api.routes.youtube import QUOTA_COSTS
        
        assert "upload" in QUOTA_COSTS
        assert QUOTA_COSTS["upload"] == 1600
        assert "list" in QUOTA_COSTS
        assert QUOTA_COSTS["list"] == 1


# ==================== SCHEMA TESTS ====================

class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_youtube_auth_request(self):
        """Test YouTubeAuthRequest schema."""
        from api.routes.youtube import YouTubeAuthRequest
        
        request = YouTubeAuthRequest(account_name="test")
        assert request.account_name == "test"
    
    def test_youtube_upload_request(self):
        """Test YouTubeUploadRequest schema."""
        from api.routes.youtube import YouTubeUploadRequest
        
        request = YouTubeUploadRequest(
            account_name="test",
            title="Video Title",
            description="Description",
            tags=["tag1", "tag2"],
            privacy="private",
            is_short=True
        )
        
        assert request.title == "Video Title"
        assert request.is_short is True
    
    def test_youtube_upload_request_defaults(self):
        """Test YouTubeUploadRequest default values."""
        from api.routes.youtube import YouTubeUploadRequest
        
        request = YouTubeUploadRequest(
            account_name="test",
            title="Title"
        )
        
        assert request.description == ""
        assert request.privacy == "private"
        assert request.is_short is False
        assert request.category == "26"


# ==================== ROUTER TESTS ====================

class TestRouter:
    """Test router configuration."""
    
    def test_router_exists(self):
        """Test router is properly configured."""
        from api.routes.youtube import router
        
        assert router is not None


# ==================== PRIVACY AND CATEGORY TESTS ====================

class TestPrivacyAndCategory:
    """Test privacy and category mapping."""
    
    def test_privacy_mapping(self):
        """Test privacy status mapping exists."""
        from vendor.youtube.client import PrivacyStatus
        
        assert PrivacyStatus.PUBLIC is not None
        assert PrivacyStatus.PRIVATE is not None
        assert PrivacyStatus.UNLISTED is not None
    
    def test_category_enum(self):
        """Test category enum exists."""
        from vendor.youtube.client import Category
        
        assert Category.HOWTO_STYLE is not None
