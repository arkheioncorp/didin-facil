"""
Tests for TikTok Routes
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException
from io import BytesIO
from datetime import datetime, timedelta

from api.services.tiktok_session import TikTokSession, TikTokSessionStatus


class MockUser(dict):
    """Mock user that supports both attribute and dict access."""
    def __init__(self):
        super().__init__(id="user_123", email="test@example.com")
        self.id = "user_123"
        self.email = "test@example.com"


@pytest.fixture
def mock_current_user():
    return MockUser()


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.DATA_DIR = "/tmp/test_data"
    return settings


@pytest.fixture
def mock_session_manager():
    """Mock TikTokSessionManager"""
    manager = MagicMock()
    manager.save_session = AsyncMock()
    manager.list_sessions = AsyncMock(return_value=[])
    manager.get_cookies = AsyncMock(return_value=None)
    manager.get_session_health = AsyncMock(return_value={"exists": False})
    return manager


@pytest.mark.asyncio
async def test_tiktok_create_session(mock_current_user, mock_session_manager):
    from api.routes.tiktok import create_session, TikTokSessionSetup
    
    # Create mock session to return
    mock_session = TikTokSession(
        user_id="user_123",
        account_name="myaccount",
        cookies=[{"name": "cookie1", "value": "val1"}],
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    mock_session_manager.save_session.return_value = mock_session
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        data = TikTokSessionSetup(
            account_name="myaccount",
            cookies=[{"name": "cookie1", "value": "val1"}]
        )
        
        result = await create_session(data, mock_current_user)
        
        assert result["status"] == "success"
        assert result["account_name"] == "myaccount"
        mock_session_manager.save_session.assert_called_once()


@pytest.mark.asyncio
async def test_tiktok_list_sessions_empty(mock_current_user, mock_session_manager):
    from api.routes.tiktok import list_sessions
    
    mock_session_manager.list_sessions.return_value = []
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        result = await list_sessions(mock_current_user)
        
        assert result["sessions"] == []


@pytest.mark.asyncio
async def test_tiktok_list_sessions_with_data(
    mock_current_user,
    mock_session_manager
):
    from api.routes.tiktok import list_sessions
    
    # Create mock sessions
    mock_sessions = [
        TikTokSession(
            user_id="user_123",
            account_name="account1",
            cookies=[],
            status=TikTokSessionStatus.ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=15)
        ),
        TikTokSession(
            user_id="user_123",
            account_name="account2",
            cookies=[],
            status=TikTokSessionStatus.ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=20)
        )
    ]
    mock_session_manager.list_sessions.return_value = mock_sessions
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        result = await list_sessions(mock_current_user)
        
        assert len(result["sessions"]) == 2
        assert result["sessions"][0]["account_name"] == "account1"
        assert result["sessions"][1]["account_name"] == "account2"


@pytest.mark.asyncio
async def test_tiktok_upload_session_not_found(
    mock_current_user,
    mock_settings,
    mock_session_manager
):
    from api.routes.tiktok import upload_video
    
    mock_file = MagicMock()
    mock_file.filename = "test.mp4"
    mock_file.file = BytesIO(b"fake video")
    
    mock_session_manager.get_cookies.return_value = None
    
    with patch("api.routes.tiktok.settings", mock_settings), \
         patch("api.routes.tiktok.session_manager", mock_session_manager):
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_video(
                account_name="nonexistent",
                caption="Test",
                hashtags="",
                privacy="public",
                file=mock_file,
                current_user=mock_current_user
            )
        
        assert exc_info.value.status_code == 404
        assert "não encontrada" in exc_info.value.detail


@pytest.mark.asyncio
async def test_tiktok_create_session_error(mock_current_user, mock_session_manager):
    """Test session creation failure."""
    from api.routes.tiktok import create_session, TikTokSessionSetup
    
    mock_session_manager.save_session.side_effect = Exception("Redis error")
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        data = TikTokSessionSetup(
            account_name="myaccount",
            cookies=[{"name": "cookie1", "value": "val1"}]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await create_session(data, mock_current_user)
        
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_tiktok_get_session_found(mock_current_user, mock_session_manager):
    """Test getting a specific session."""
    from api.routes.tiktok import get_session
    
    mock_session_manager.get_session_health.return_value = {
        "exists": True,
        "status": "active",
        "account_name": "testaccount"
    }
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        result = await get_session("testaccount", mock_current_user)
        
        assert result["exists"] is True
        assert result["account_name"] == "testaccount"


@pytest.mark.asyncio
async def test_tiktok_get_session_not_found(mock_current_user, mock_session_manager):
    """Test getting a non-existent session."""
    from api.routes.tiktok import get_session
    
    mock_session_manager.get_session_health.return_value = {"exists": False}
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        with pytest.raises(HTTPException) as exc_info:
            await get_session("nonexistent", mock_current_user)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_tiktok_backup_session_success(mock_current_user, mock_session_manager):
    """Test session backup success."""
    from api.routes.tiktok import backup_session
    
    mock_session_manager.backup_session = AsyncMock(return_value=True)
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        result = await backup_session("testaccount", mock_current_user)
        
        assert result["status"] == "success"
        mock_session_manager.backup_session.assert_called_once()


@pytest.mark.asyncio
async def test_tiktok_backup_session_failure(mock_current_user, mock_session_manager):
    """Test session backup failure."""
    from api.routes.tiktok import backup_session
    
    mock_session_manager.backup_session = AsyncMock(return_value=False)
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        with pytest.raises(HTTPException) as exc_info:
            await backup_session("testaccount", mock_current_user)
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_tiktok_restore_session_success(mock_current_user, mock_session_manager):
    """Test session restore success."""
    from api.routes.tiktok import restore_session
    
    restored_session = TikTokSession(
        user_id="user_123",
        account_name="testaccount",
        cookies=[]
    )
    mock_session_manager.restore_session = AsyncMock(return_value=restored_session)
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        result = await restore_session("testaccount", mock_current_user)
        
        assert result["status"] == "success"
        assert result["account_name"] == "testaccount"


@pytest.mark.asyncio
async def test_tiktok_restore_session_no_backup(mock_current_user, mock_session_manager):
    """Test session restore with no backup."""
    from api.routes.tiktok import restore_session
    
    mock_session_manager.restore_session = AsyncMock(return_value=None)
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        with pytest.raises(HTTPException) as exc_info:
            await restore_session("testaccount", mock_current_user)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_tiktok_update_cookies_success(mock_current_user, mock_session_manager):
    """Test updating session cookies."""
    from api.routes.tiktok import update_cookies
    
    mock_session_manager.update_cookies = AsyncMock(return_value=True)
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        result = await update_cookies(
            account_name="testaccount",
            cookies=[{"name": "new_cookie", "value": "new_value"}],
            current_user=mock_current_user
        )
        
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_tiktok_update_cookies_failure(mock_current_user, mock_session_manager):
    """Test failure when updating cookies."""
    from api.routes.tiktok import update_cookies
    
    mock_session_manager.update_cookies = AsyncMock(return_value=False)
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        with pytest.raises(HTTPException) as exc_info:
            await update_cookies(
                account_name="testaccount",
                cookies=[{"name": "cookie", "value": "value"}],
                current_user=mock_current_user
            )
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_tiktok_delete_session_success(mock_current_user, mock_session_manager):
    """Test deleting a session."""
    from api.routes.tiktok import delete_session
    
    mock_session_manager.delete_session = AsyncMock(return_value=True)
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        result = await delete_session(
            account_name="testaccount",
            keep_backups=True,
            current_user=mock_current_user
        )
        
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_tiktok_delete_session_failure(mock_current_user, mock_session_manager):
    """Test failure when deleting session."""
    from api.routes.tiktok import delete_session
    
    mock_session_manager.delete_session = AsyncMock(return_value=False)
    
    with patch("api.routes.tiktok.session_manager", mock_session_manager):
        with pytest.raises(HTTPException) as exc_info:
            await delete_session(
                account_name="testaccount",
                keep_backups=True,
                current_user=mock_current_user
            )
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_tiktok_upload_success(mock_current_user, mock_settings, mock_session_manager):
    """Test successful video upload."""
    from api.routes.tiktok import upload_video
    
    mock_file = MagicMock()
    mock_file.filename = "test.mp4"
    mock_file.file = BytesIO(b"fake video content")
    
    # Mock upload result with proper enum
    mock_status = MagicMock()
    mock_status.value = "published"
    
    mock_result = MagicMock()
    mock_result.status = mock_status
    mock_result.video_id = "video_123"
    mock_result.url = "https://tiktok.com/video/123"
    
    mock_client = MagicMock()
    mock_client.upload_video = AsyncMock(return_value=mock_result)
    mock_client._driver = None
    
    with patch("api.routes.tiktok.settings", mock_settings), \
         patch("api.routes.tiktok.session_manager", mock_session_manager), \
         patch("api.routes.tiktok.TikTokClient", return_value=mock_client), \
         patch("os.path.exists", return_value=True), \
         patch("os.makedirs"), \
         patch("os.remove"), \
         patch("builtins.open", MagicMock()):
        
        result = await upload_video(
            account_name="testaccount",
            caption="Test video",
            hashtags="test,video",
            privacy="public",
            file=mock_file,
            current_user=mock_current_user
        )
        
        assert result["status"] == "published"
        assert result["video_id"] == "video_123"


@pytest.mark.asyncio
async def test_tiktok_upload_failure(mock_current_user, mock_settings, mock_session_manager):
    """Test video upload failure."""
    from api.routes.tiktok import upload_video
    
    mock_file = MagicMock()
    mock_file.filename = "test.mp4"
    mock_file.file = BytesIO(b"fake video content")
    
    # Mock failed upload result with proper enum-like mock
    mock_status = MagicMock()
    mock_status.value = "failed"
    
    mock_result = MagicMock()
    mock_result.status = mock_status
    mock_result.error = "Upload failed"
    
    mock_client = MagicMock()
    mock_client.upload_video = AsyncMock(return_value=mock_result)
    mock_client._driver = None
    
    with patch("api.routes.tiktok.settings", mock_settings), \
         patch("api.routes.tiktok.session_manager", mock_session_manager), \
         patch("api.routes.tiktok.TikTokClient", return_value=mock_client), \
         patch("os.path.exists", return_value=True), \
         patch("os.makedirs"), \
         patch("os.remove"), \
         patch("builtins.open", MagicMock()):
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_video(
                account_name="testaccount",
                caption="Test video",
                hashtags="",
                privacy="public",
                file=mock_file,
                current_user=mock_current_user
            )
        
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_tiktok_upload_exception(mock_current_user, mock_settings, mock_session_manager):
    """Test exception during upload."""
    from api.routes.tiktok import upload_video
    
    mock_file = MagicMock()
    mock_file.filename = "test.mp4"
    mock_file.file = BytesIO(b"fake video content")
    
    mock_client = MagicMock()
    mock_client.upload_video = AsyncMock(side_effect=Exception("Connection error"))
    mock_client._driver = None
    
    with patch("api.routes.tiktok.settings", mock_settings), \
         patch("api.routes.tiktok.session_manager", mock_session_manager), \
         patch("api.routes.tiktok.TikTokClient", return_value=mock_client), \
         patch("os.path.exists", return_value=True), \
         patch("os.makedirs"), \
         patch("os.remove"), \
         patch("builtins.open", MagicMock()):
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_video(
                account_name="testaccount",
                caption="Test video",
                hashtags="",
                privacy="public",
                file=mock_file,
                current_user=mock_current_user
            )
        
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_tiktok_upload_with_hashtags_and_privacy(
    mock_current_user,
    mock_settings,
    mock_session_manager
):
    """Test upload with specific hashtags and privacy settings."""
    from api.routes.tiktok import upload_video
    
    mock_file = MagicMock()
    mock_file.filename = "test.mp4"
    mock_file.file = BytesIO(b"fake video content")
    
    mock_status = MagicMock()
    mock_status.value = "published"
    
    mock_result = MagicMock()
    mock_result.status = mock_status
    mock_result.video_id = "video_456"
    mock_result.url = "https://tiktok.com/video/456"
    
    mock_client = MagicMock()
    mock_client.upload_video = AsyncMock(return_value=mock_result)
    mock_client._driver = None
    
    with patch("api.routes.tiktok.settings", mock_settings), \
         patch("api.routes.tiktok.session_manager", mock_session_manager), \
         patch("api.routes.tiktok.TikTokClient", return_value=mock_client), \
         patch("os.path.exists", return_value=True), \
         patch("os.makedirs"), \
         patch("os.remove"), \
         patch("builtins.open", MagicMock()):
        
        result = await upload_video(
            account_name="testaccount",
            caption="Private video",
            hashtags="private,test,video",
            privacy="friends",
            file=mock_file,
            current_user=mock_current_user
        )
        
        assert result["status"] == "published"
