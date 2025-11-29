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
