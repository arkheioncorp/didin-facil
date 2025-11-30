"""
Tests for Instagram Routes
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from io import BytesIO


class MockUser:
    id = "user_123"
    email = "test@example.com"


@pytest.fixture
def mock_current_user():
    return MockUser()


@pytest.fixture
def mock_instagram_client():
    client = AsyncMock()
    client.login.return_value = True
    client.get_settings.return_value = {"session": "data"}
    client.load_settings.return_value = None
    client.upload_photo.return_value = {"pk": "123456"}
    client.upload_video.return_value = {"pk": "789012"}
    client.upload_reel.return_value = {"pk": "345678"}
    return client


@pytest.mark.asyncio
async def test_instagram_login_success(mock_current_user, mock_instagram_client):
    from api.routes.instagram import login, InstagramLogin
    
    mock_redis = AsyncMock()
    
    with patch("api.routes.instagram.InstagramClient", return_value=mock_instagram_client), \
         patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.get_current_user", return_value=mock_current_user):
        
        data = InstagramLogin(username="testuser", password="testpass")
        result = await login(data, mock_current_user)
        
        assert result["status"] == "success"
        mock_instagram_client.login.assert_called_once()
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_instagram_login_failure(mock_current_user, mock_instagram_client):
    from api.routes.instagram import login, InstagramLogin
    
    mock_instagram_client.login.return_value = False
    
    with patch("api.routes.instagram.InstagramClient", return_value=mock_instagram_client), \
         patch("api.routes.instagram.get_current_user", return_value=mock_current_user):
        
        data = InstagramLogin(username="testuser", password="testpass")
        
        with pytest.raises(HTTPException) as exc_info:
            await login(data, mock_current_user)
        
        # Returns 400 when login returns False (caught by except block)
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_instagram_login_exception(mock_current_user, mock_instagram_client):
    from api.routes.instagram import login, InstagramLogin
    
    mock_instagram_client.login.side_effect = Exception("Connection error")
    
    with patch("api.routes.instagram.InstagramClient", return_value=mock_instagram_client), \
         patch("api.routes.instagram.get_current_user", return_value=mock_current_user):
        
        data = InstagramLogin(username="testuser", password="testpass")
        
        with pytest.raises(HTTPException) as exc_info:
            await login(data, mock_current_user)
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_instagram_upload_not_logged_in(mock_current_user):
    from api.routes.instagram import upload_media
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    
    mock_file = MagicMock()
    mock_file.filename = "test.jpg"
    mock_file.file = BytesIO(b"fake image data")
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.get_current_user", return_value=mock_current_user):
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_media(
                username="testuser",
                caption="Test caption",
                media_type="photo",
                file=mock_file,
                current_user=mock_current_user
            )
        
        assert exc_info.value.status_code == 401
        assert "not logged in" in exc_info.value.detail


@pytest.mark.asyncio
async def test_instagram_upload_photo_success(mock_current_user, mock_instagram_client):
    from api.routes.instagram import upload_media
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"session": "data"}'
    
    mock_file = MagicMock()
    mock_file.filename = "test.jpg"
    mock_file.file = BytesIO(b"fake image data")
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.InstagramClient", return_value=mock_instagram_client), \
         patch("api.routes.instagram.get_current_user", return_value=mock_current_user), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()), \
         patch("shutil.copyfileobj"), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove"):
        
        result = await upload_media(
            username="testuser",
            caption="Test caption",
            media_type="photo",
            file=mock_file,
            current_user=mock_current_user
        )
        
        assert result["status"] == "success"
        assert "media_pk" in result


@pytest.mark.asyncio
async def test_instagram_upload_video_success(mock_current_user, mock_instagram_client):
    from api.routes.instagram import upload_media
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"session": "data"}'
    
    mock_file = MagicMock()
    mock_file.filename = "test.mp4"
    mock_file.file = BytesIO(b"fake video data")
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.InstagramClient", return_value=mock_instagram_client), \
         patch("api.routes.instagram.get_current_user", return_value=mock_current_user), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()), \
         patch("shutil.copyfileobj"), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove"):
        
        result = await upload_media(
            username="testuser",
            caption="Test caption",
            media_type="video",
            file=mock_file,
            current_user=mock_current_user
        )
        
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_instagram_upload_reel_success(mock_current_user, mock_instagram_client):
    from api.routes.instagram import upload_media
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"session": "data"}'
    
    mock_file = MagicMock()
    mock_file.filename = "test.mp4"
    mock_file.file = BytesIO(b"fake video data")
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.InstagramClient", return_value=mock_instagram_client), \
         patch("api.routes.instagram.get_current_user", return_value=mock_current_user), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()), \
         patch("shutil.copyfileobj"), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove"):
        
        result = await upload_media(
            username="testuser",
            caption="Test caption",
            media_type="reel",
            file=mock_file,
            current_user=mock_current_user
        )
        
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_instagram_upload_invalid_media_type(
    mock_current_user,
    mock_instagram_client
):
    from api.routes.instagram import upload_media
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"session": "data"}'
    
    mock_file = MagicMock()
    mock_file.filename = "test.jpg"
    mock_file.file = BytesIO(b"fake data")
    
    # Mock load_settings to not raise
    mock_instagram_client.load_settings = AsyncMock()
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.InstagramClient",
               return_value=mock_instagram_client), \
         patch("api.routes.instagram.get_current_user",
               return_value=mock_current_user), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()), \
         patch("shutil.copyfileobj"), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove"):
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_media(
                username="testuser",
                caption="Test caption",
                media_type="invalid",
                file=mock_file,
                current_user=mock_current_user
            )
        
        # Note: due to exception handling in the route, HTTPException gets
        # caught by except block and re-raised as 500
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_instagram_login_2fa_challenge(mock_current_user):
    """Test login with 2FA challenge required."""
    from api.routes.instagram import login, InstagramLogin
    
    mock_redis = AsyncMock()
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.InstagramClient") as mock_client_class:
        
        # Simulate 2FA challenge
        mock_client = AsyncMock()
        mock_client.login.side_effect = Exception("CHALLENGE_2FA_REQUIRED")
        mock_client_class.return_value = mock_client
        
        data = InstagramLogin(username="testuser", password="testpass")
        result = await login(data, mock_current_user)
        
        assert result["status"] == "challenge_required"
        assert result["challenge_type"] == "2fa"
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_instagram_login_sms_challenge(mock_current_user):
    """Test login with SMS challenge required."""
    from api.routes.instagram import login, InstagramLogin
    
    mock_redis = AsyncMock()
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.InstagramClient") as mock_client_class:
        
        mock_client = AsyncMock()
        mock_client.login.side_effect = Exception("CHALLENGE_SMS_REQUIRED")
        mock_client_class.return_value = mock_client
        
        data = InstagramLogin(username="testuser", password="testpass")
        result = await login(data, mock_current_user)
        
        assert result["status"] == "challenge_required"
        assert result["challenge_type"] == "sms"


@pytest.mark.asyncio
async def test_instagram_login_email_challenge(mock_current_user):
    """Test login with email challenge required."""
    from api.routes.instagram import login, InstagramLogin
    
    mock_redis = AsyncMock()
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.InstagramClient") as mock_client_class:
        
        mock_client = AsyncMock()
        mock_client.login.side_effect = Exception("CHALLENGE_EMAIL_REQUIRED")
        mock_client_class.return_value = mock_client
        
        data = InstagramLogin(username="testuser", password="testpass")
        result = await login(data, mock_current_user)
        
        assert result["status"] == "challenge_required"
        assert result["challenge_type"] == "email"


@pytest.mark.asyncio
async def test_instagram_resolve_challenge_no_pending(mock_current_user):
    """Test resolving challenge without pending challenge."""
    from api.routes.instagram import resolve_challenge, InstagramChallenge
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # No pending challenge
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis):
        data = InstagramChallenge(username="testuser", code="123456")
        
        with pytest.raises(HTTPException) as exc_info:
            await resolve_challenge(data, mock_current_user)
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_instagram_resolve_challenge_success(mock_current_user):
    """Test resolving challenge successfully."""
    from api.routes.instagram import resolve_challenge, InstagramChallenge
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"type": "2fa", "username": "testuser"}'
    mock_redis.set.return_value = None
    mock_redis.delete.return_value = None
    
    mock_client = AsyncMock()
    mock_client.login.return_value = True
    mock_client.get_settings.return_value = {"user_id": "123", "session": "data"}
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.InstagramClient", return_value=mock_client):
        
        data = InstagramChallenge(username="testuser", code="123456")
        result = await resolve_challenge(data, mock_current_user)
        
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_instagram_resolve_challenge_invalid_code(mock_current_user):
    """Test resolving challenge with invalid code."""
    from api.routes.instagram import resolve_challenge, InstagramChallenge
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"type": "2fa", "username": "testuser"}'
    
    mock_client = AsyncMock()
    mock_client.login.side_effect = Exception("CHALLENGE_INVALID")
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.InstagramClient", return_value=mock_client):
        
        data = InstagramChallenge(username="testuser", code="wrong")
        result = await resolve_challenge(data, mock_current_user)
        
        assert result["status"] == "invalid_code"


@pytest.mark.asyncio
async def test_instagram_request_challenge_success(mock_current_user):
    """Test requesting a new challenge code."""
    from api.routes.instagram import request_challenge_code
    
    mock_client = AsyncMock()
    mock_client.request_challenge_code.return_value = True
    
    with patch("api.routes.instagram.InstagramClient", return_value=mock_client):
        result = await request_challenge_code("testuser", "email", mock_current_user)
        
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_instagram_request_challenge_failed(mock_current_user):
    """Test requesting challenge code fails."""
    from api.routes.instagram import request_challenge_code
    
    mock_client = AsyncMock()
    mock_client.request_challenge_code.return_value = False
    
    with patch("api.routes.instagram.InstagramClient", return_value=mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await request_challenge_code("testuser", "sms", mock_current_user)
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_instagram_request_challenge_exception(mock_current_user):
    """Test requesting challenge code raises exception."""
    from api.routes.instagram import request_challenge_code
    
    mock_client = AsyncMock()
    mock_client.request_challenge_code.side_effect = Exception("Error")
    
    with patch("api.routes.instagram.InstagramClient", return_value=mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await request_challenge_code("testuser", "email", mock_current_user)
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_instagram_list_sessions(mock_current_user):
    """Test listing all sessions."""
    from api.routes.instagram import list_sessions
    from datetime import datetime
    
    mock_session = MagicMock()
    mock_session.username = "testuser"
    mock_session.status = "active"
    mock_session.is_valid = True
    mock_session.last_used = datetime.now()
    mock_session.created_at = datetime.now()
    mock_session.expires_at = datetime.now()
    
    mock_manager = MagicMock()
    mock_manager.get_all_sessions = AsyncMock(return_value=[mock_session])
    mock_manager.get_active_challenges = AsyncMock(return_value=[])
    
    with patch("api.routes.instagram.session_manager", mock_manager):
        result = await list_sessions(mock_current_user)
        
        assert "sessions" in result
        assert len(result["sessions"]) == 1


@pytest.mark.asyncio
async def test_instagram_get_session_found(mock_current_user):
    """Test getting a specific session."""
    from api.routes.instagram import get_session
    from datetime import datetime
    
    mock_session = MagicMock()
    mock_session.username = "testuser"
    mock_session.status = "active"
    mock_session.is_valid = True
    mock_session.last_used = datetime.now()
    mock_session.created_at = datetime.now()
    mock_session.expires_at = datetime.now()
    mock_session.metadata = {}
    
    mock_manager = MagicMock()
    mock_manager.get_session = AsyncMock(return_value=mock_session)
    mock_manager.get_active_challenges = AsyncMock(return_value=[])
    
    with patch("api.routes.instagram.session_manager", mock_manager):
        result = await get_session("testuser", mock_current_user)
        
        assert result["username"] == "testuser"


@pytest.mark.asyncio
async def test_instagram_get_session_not_found(mock_current_user):
    """Test getting a non-existent session."""
    from api.routes.instagram import get_session
    
    mock_manager = MagicMock()
    mock_manager.get_session = AsyncMock(return_value=None)
    
    with patch("api.routes.instagram.session_manager", mock_manager):
        with pytest.raises(HTTPException) as exc_info:
            await get_session("nonexistent", mock_current_user)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_instagram_backup_session_success(mock_current_user):
    """Test backing up a session."""
    from api.routes.instagram import backup_session
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"user_id": "123"}'
    
    mock_manager = MagicMock()
    mock_manager.backup_session = AsyncMock(return_value=True)
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.session_manager", mock_manager):
        result = await backup_session("testuser", mock_current_user)
        
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_instagram_backup_session_not_found(mock_current_user):
    """Test backing up non-existent session."""
    from api.routes.instagram import backup_session
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis):
        with pytest.raises(HTTPException) as exc_info:
            await backup_session("nonexistent", mock_current_user)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_instagram_backup_session_failed(mock_current_user):
    """Test backup failure."""
    from api.routes.instagram import backup_session
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"user_id": "123"}'
    
    mock_manager = MagicMock()
    mock_manager.backup_session = AsyncMock(return_value=False)
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.session_manager", mock_manager):
        with pytest.raises(HTTPException) as exc_info:
            await backup_session("testuser", mock_current_user)
        
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_instagram_restore_session_success(mock_current_user):
    """Test restoring a session."""
    from api.routes.instagram import restore_session
    
    mock_redis = AsyncMock()
    mock_redis.set.return_value = None
    
    mock_manager = MagicMock()
    mock_manager.restore_session = AsyncMock(return_value={"user_id": "123"})
    
    mock_client = AsyncMock()
    mock_client.load_settings.return_value = None
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.session_manager", mock_manager), \
         patch("api.routes.instagram.InstagramClient", return_value=mock_client):
        result = await restore_session("testuser", mock_current_user)
        
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_instagram_restore_session_no_backup(mock_current_user):
    """Test restoring when no backup exists."""
    from api.routes.instagram import restore_session
    
    mock_manager = MagicMock()
    mock_manager.restore_session = AsyncMock(return_value=None)
    
    with patch("api.routes.instagram.session_manager", mock_manager):
        with pytest.raises(HTTPException) as exc_info:
            await restore_session("testuser", mock_current_user)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_instagram_restore_session_invalid(mock_current_user):
    """Test restoring invalid session."""
    from api.routes.instagram import restore_session
    
    mock_manager = MagicMock()
    mock_manager.restore_session = AsyncMock(return_value={"user_id": "123"})
    
    mock_client = AsyncMock()
    mock_client.load_settings.side_effect = Exception("Invalid session")
    
    with patch("api.routes.instagram.session_manager", mock_manager), \
         patch("api.routes.instagram.InstagramClient", return_value=mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await restore_session("testuser", mock_current_user)
        
        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_instagram_delete_session(mock_current_user):
    """Test deleting a session."""
    from api.routes.instagram import delete_session
    
    mock_redis = AsyncMock()
    mock_redis.delete.return_value = None
    mock_redis.keys.return_value = []
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis):
        result = await delete_session("testuser", mock_current_user)
        
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_instagram_delete_session_with_backups(mock_current_user):
    """Test deleting session with backups."""
    from api.routes.instagram import delete_session
    
    mock_redis = AsyncMock()
    mock_redis.delete.return_value = None
    mock_redis.keys.return_value = ["backup:1", "backup:2"]
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis):
        result = await delete_session("testuser", mock_current_user)
        
        assert result["status"] == "success"
        assert mock_redis.delete.call_count >= 2


@pytest.mark.asyncio
async def test_instagram_list_challenges(mock_current_user):
    """Test listing challenges."""
    from api.routes.instagram import list_challenges
    from datetime import datetime
    
    mock_challenge = MagicMock()
    mock_challenge.id = "challenge_1"
    mock_challenge.username = "testuser"
    mock_challenge.challenge_type = MagicMock()
    mock_challenge.challenge_type.value = "2fa"
    mock_challenge.status = MagicMock()
    mock_challenge.status.value = "pending"
    mock_challenge.message = "Enter code"
    mock_challenge.created_at = datetime.now()
    mock_challenge.expires_at = datetime.now()
    mock_challenge.attempts = 0
    mock_challenge.max_attempts = 3
    
    mock_manager = MagicMock()
    mock_manager.get_active_challenges = AsyncMock(return_value=[mock_challenge])
    
    with patch("api.routes.instagram.session_manager", mock_manager):
        result = await list_challenges(None, mock_current_user)
        
        assert "challenges" in result
        assert result["total"] == 1


@pytest.mark.asyncio
async def test_instagram_get_challenge_found(mock_current_user):
    """Test getting a specific challenge."""
    from api.routes.instagram import get_challenge
    from datetime import datetime
    
    mock_challenge = MagicMock()
    mock_challenge.id = "challenge_1"
    mock_challenge.username = "testuser"
    mock_challenge.challenge_type = MagicMock()
    mock_challenge.challenge_type.value = "2fa"
    mock_challenge.status = MagicMock()
    mock_challenge.status.value = "pending"
    mock_challenge.message = "Enter code"
    mock_challenge.created_at = datetime.now()
    mock_challenge.expires_at = datetime.now()
    mock_challenge.resolved_at = None
    mock_challenge.attempts = 0
    mock_challenge.max_attempts = 3
    mock_challenge.metadata = {}
    
    mock_manager = MagicMock()
    mock_manager.get_challenge = AsyncMock(return_value=mock_challenge)
    
    with patch("api.routes.instagram.session_manager", mock_manager):
        result = await get_challenge("challenge_1", mock_current_user)
        
        assert result["id"] == "challenge_1"


@pytest.mark.asyncio
async def test_instagram_get_challenge_not_found(mock_current_user):
    """Test getting non-existent challenge."""
    from api.routes.instagram import get_challenge
    
    mock_manager = MagicMock()
    mock_manager.get_challenge = AsyncMock(return_value=None)
    
    with patch("api.routes.instagram.session_manager", mock_manager):
        with pytest.raises(HTTPException) as exc_info:
            await get_challenge("nonexistent", mock_current_user)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_instagram_health(mock_current_user):
    """Test health check endpoint."""
    from api.routes.instagram import instagram_health
    from api.services.instagram_session import ChallengeStatus
    
    mock_session = MagicMock()
    mock_session.is_valid = True
    
    mock_challenge = MagicMock()
    mock_challenge.status = ChallengeStatus.PENDING
    mock_challenge.challenge_type = MagicMock()
    mock_challenge.challenge_type.value = "2fa"
    
    mock_manager = MagicMock()
    mock_manager.get_all_sessions = AsyncMock(return_value=[mock_session])
    mock_manager.get_active_challenges = AsyncMock(return_value=[mock_challenge])
    
    with patch("api.routes.instagram.session_manager", mock_manager):
        result = await instagram_health(mock_current_user)
        
        assert result["status"] == "healthy"
        assert "sessions" in result
        assert "challenges" in result


@pytest.mark.asyncio
async def test_instagram_upload_load_session_failed(mock_current_user):
    """Test upload with failed session load."""
    from api.routes.instagram import upload_media
    
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"session": "data"}'
    
    mock_client = AsyncMock()
    mock_client.load_settings.side_effect = Exception("Session expired")
    
    mock_file = MagicMock()
    mock_file.filename = "test.jpg"
    mock_file.file = BytesIO(b"fake data")
    
    with patch("api.routes.instagram.get_redis", return_value=mock_redis), \
         patch("api.routes.instagram.InstagramClient", return_value=mock_client):
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_media(
                username="testuser",
                caption="Test",
                media_type="photo",
                file=mock_file,
                current_user=mock_current_user
            )
        
        assert exc_info.value.status_code == 401
