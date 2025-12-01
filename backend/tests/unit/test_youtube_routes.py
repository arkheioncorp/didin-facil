"""
Tests for YouTube Routes
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException


@pytest.fixture
def mock_current_user():
    return {
        "id": str(uuid4()),
        "email": "test@example.com"
    }


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.DATA_DIR = "/tmp/test_data"
    return settings


@pytest.fixture
def mock_youtube_client():
    client = AsyncMock()
    client.authenticate.return_value = True
    client.upload_video.return_value = {"id": "video123"}
    return client


@pytest.mark.asyncio
async def test_youtube_init_auth_no_creds(mock_current_user, mock_settings):
    from api.routes.youtube import YouTubeAuthRequest, init_auth
    
    with patch("api.routes.youtube.settings", mock_settings), \
         patch("os.makedirs"), \
         patch("os.path.exists", return_value=False):
        
        data = YouTubeAuthRequest(account_name="myaccount")
        
        with pytest.raises(HTTPException) as exc_info:
            await init_auth(data, mock_current_user)
        
        assert exc_info.value.status_code == 400
        assert "credenciais" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_youtube_init_auth_success(
    mock_current_user,
    mock_settings,
    mock_youtube_client
):
    from api.routes.youtube import YouTubeAuthRequest, init_auth
    
    with patch("api.routes.youtube.settings", mock_settings), \
         patch("os.makedirs"), \
         patch("os.path.exists", return_value=True), \
         patch("api.routes.youtube.YouTubeClient",
               return_value=mock_youtube_client):
        
        data = YouTubeAuthRequest(account_name="myaccount")
        
        result = await init_auth(data, mock_current_user)
        
        assert result["status"] == "success"
        assert result["account_name"] == "myaccount"


@pytest.mark.asyncio
async def test_youtube_init_auth_exception(
    mock_current_user,
    mock_settings,
    mock_youtube_client
):
    from api.routes.youtube import YouTubeAuthRequest, init_auth
    
    mock_youtube_client.authenticate.side_effect = Exception("Auth failed")
    
    with patch("api.routes.youtube.settings", mock_settings), \
         patch("os.makedirs"), \
         patch("os.path.exists", return_value=True), \
         patch("api.routes.youtube.YouTubeClient",
               return_value=mock_youtube_client):
        
        data = YouTubeAuthRequest(account_name="myaccount")
        
        with pytest.raises(HTTPException) as exc_info:
            await init_auth(data, mock_current_user)
        
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_youtube_list_accounts_empty(mock_current_user, mock_settings):
    from api.routes.youtube import list_accounts
    
    with patch("api.routes.youtube.settings", mock_settings), \
         patch("os.path.exists", return_value=False):
        
        result = await list_accounts(mock_current_user)
        
        assert result["accounts"] == []


@pytest.mark.asyncio
async def test_youtube_list_accounts_with_data(
    mock_current_user,
    mock_settings
):
    from api.routes.youtube import list_accounts
    
    with patch("api.routes.youtube.settings", mock_settings), \
         patch("os.path.exists", return_value=True), \
         patch("os.listdir", return_value=[
             f"{mock_current_user['id']}_channel1.json",
             f"{mock_current_user['id']}_channel2.json",
             "other_user.json"
         ]):
        
        result = await list_accounts(mock_current_user)
        
        assert len(result["accounts"]) == 2


@pytest.mark.asyncio
async def test_youtube_upload_no_token(mock_current_user, mock_settings):
    """Test upload without token file."""
    from api.routes.youtube import upload_video
    
    mock_file = MagicMock()
    mock_file.filename = "test.mp4"
    mock_file.file = MagicMock()
    
    with patch("api.routes.youtube.settings", mock_settings), \
         patch("os.path.exists", return_value=False):
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_video(
                account_name="test",
                title="Test",
                description="Test",
                tags="tag1",
                privacy="private",
                category="26",
                is_short=False,
                file=mock_file,
                thumbnail=None,
                current_user=mock_current_user
            )
        
        assert exc_info.value.status_code == 404
        assert "não autenticada" in exc_info.value.detail


@pytest.mark.asyncio
async def test_youtube_get_quota_status_empty(mock_current_user, mock_settings):
    """Test quota status with no usage."""
    from api.routes.youtube import get_quota_status
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    
    with patch("api.routes.youtube.get_redis", return_value=mock_redis):
        result = await get_quota_status(mock_current_user)
        
        assert result["quota"]["used"] == 0
        assert result["quota"]["remaining"] == 10000


@pytest.mark.asyncio
async def test_youtube_get_quota_status_with_data(
    mock_current_user,
    mock_settings
):
    """Test quota status with existing usage."""
    import json

    from api.routes.youtube import get_quota_status
    
    usage = {"total": 1700, "operations": {"upload": 1600, "list": 100}}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(usage)
    
    with patch("api.routes.youtube.get_redis", return_value=mock_redis):
        result = await get_quota_status(mock_current_user)
        
        assert result["quota"]["used"] == 1700
        assert result["quota"]["remaining"] == 8300


@pytest.mark.asyncio
async def test_youtube_track_quota_new(mock_settings):
    """Test tracking quota for new user."""
    from api.routes.youtube import _track_quota_usage
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    
    with patch("api.routes.youtube.get_redis", return_value=mock_redis):
        await _track_quota_usage("user_123", "upload", 1600)
        
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_youtube_track_quota_existing(mock_settings):
    """Test tracking quota with existing usage."""
    import json

    from api.routes.youtube import _track_quota_usage
    
    usage = {"total": 100, "operations": {"list": 100}}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(usage)
    
    with patch("api.routes.youtube.get_redis", return_value=mock_redis):
        await _track_quota_usage("user_123", "upload", 1600)
        
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_youtube_quota_history_empty(mock_current_user, mock_settings):
    """Test quota history with no data."""
    from api.routes.youtube import get_quota_history
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    
    with patch("api.routes.youtube.get_redis", return_value=mock_redis):
        result = await get_quota_history(days=7, current_user=mock_current_user)
        
        assert len(result["history"]) == 7
        assert all(h["total_used"] == 0 for h in result["history"])


@pytest.mark.asyncio
async def test_youtube_quota_history_with_data(mock_current_user, mock_settings):
    """Test quota history with data."""
    import json

    from api.routes.youtube import get_quota_history
    
    usage = {"total": 500, "operations": {"list": 500}}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(usage)
    
    with patch("api.routes.youtube.get_redis", return_value=mock_redis):
        result = await get_quota_history(days=3, current_user=mock_current_user)
        
        assert len(result["history"]) == 3
        assert result["days"] == 3


@pytest.mark.asyncio
async def test_youtube_check_quota_alerts(mock_settings):
    """Test quota alert system."""
    from api.routes.youtube import _check_quota_alerts
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # No alert sent yet
    
    with patch("api.routes.youtube.get_redis", return_value=mock_redis):
        # 70% threshold = 7000 units
        await _check_quota_alerts("user_123", 7000)
        
        # Should have checked for alerts
        assert mock_redis.get.called


