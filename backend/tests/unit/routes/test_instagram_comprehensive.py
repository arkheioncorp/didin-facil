"""
Comprehensive tests for Instagram routes.
Coverage target: 90%+
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.instagram import (InstagramChallenge, InstagramLogin,
                                  InstagramPost, get_session, list_sessions,
                                  login, request_challenge_code,
                                  resolve_challenge, router, upload_media)
from fastapi import HTTPException

# ==================== FIXTURES ====================

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock()
    user.__getitem__ = lambda s, k: {"id": "user-123"}[k]
    return user


@pytest.fixture
def mock_subscription_service():
    """Mock subscription service."""
    service = AsyncMock()
    service.can_use_feature = AsyncMock(return_value=True)
    service.increment_usage = AsyncMock()
    return service


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def mock_instagram_client():
    """Mock Instagram client."""
    client = AsyncMock()
    client.login = AsyncMock(return_value=True)
    client.get_settings = AsyncMock(return_value={"session": "data"})
    client.load_settings = AsyncMock()
    client.upload_photo = AsyncMock(return_value={"pk": "123"})
    client.upload_video = AsyncMock(return_value={"pk": "456"})
    client.upload_reel = AsyncMock(return_value={"pk": "789"})
    client.request_challenge_code = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_session():
    """Mock Instagram session."""
    from datetime import datetime
    session = MagicMock()
    session.username = "testuser"
    session.status = "active"
    session.is_valid = True
    session.last_used = datetime.now()
    session.created_at = datetime.now()
    session.expires_at = datetime.now()
    session.metadata = {}
    return session


@pytest.fixture
def mock_challenge():
    """Mock Instagram challenge."""
    from datetime import datetime

    from api.services.instagram_session import ChallengeStatus
    
    challenge = MagicMock()
    challenge.id = "challenge-123"
    challenge.challenge_type = MagicMock(value="2fa")
    challenge.status = ChallengeStatus.PENDING
    challenge.message = "Enter code"
    challenge.expires_at = datetime.now()
    challenge.created_at = datetime.now()
    challenge.attempts = 0
    return challenge


# ==================== SCHEMA TESTS ====================

class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_instagram_login_schema(self):
        """Test InstagramLogin schema."""
        data = InstagramLogin(
            username="testuser",
            password="testpass"
        )
        assert data.username == "testuser"
        assert data.password == "testpass"
        assert data.verification_code is None
    
    def test_instagram_login_with_2fa(self):
        """Test InstagramLogin schema with 2FA code."""
        data = InstagramLogin(
            username="testuser",
            password="testpass",
            verification_code="123456"
        )
        assert data.verification_code == "123456"
    
    def test_instagram_challenge_schema(self):
        """Test InstagramChallenge schema."""
        data = InstagramChallenge(
            username="testuser",
            code="123456"
        )
        assert data.username == "testuser"
        assert data.code == "123456"
        assert data.method is None
    
    def test_instagram_post_schema(self):
        """Test InstagramPost schema."""
        data = InstagramPost(
            username="testuser",
            caption="Test caption"
        )
        assert data.username == "testuser"
        assert data.caption == "Test caption"
        assert data.media_type == "photo"


# ==================== LOGIN TESTS ====================

class TestLogin:
    """Test login endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, mock_user, mock_redis, mock_instagram_client):
        """Test successful login."""
        with patch('api.routes.instagram.get_redis', return_value=mock_redis), \
             patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client):
            
            data = InstagramLogin(username="testuser", password="testpass")
            result = await login(data, mock_user)
            
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_login_failed(self, mock_user, mock_redis, mock_instagram_client):
        """Test failed login."""
        mock_instagram_client.login = AsyncMock(return_value=False)
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis), \
             patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client):
            
            data = InstagramLogin(username="testuser", password="wrongpass")
            
            with pytest.raises(Exception) as exc_info:
                await login(data, mock_user)
            # API returns 400 for login failures
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_login_2fa_required(self, mock_user, mock_redis, mock_instagram_client):
        """Test login with 2FA challenge."""
        mock_instagram_client.login = AsyncMock(
            side_effect=Exception("CHALLENGE_2FA_REQUIRED")
        )
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis), \
             patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client):
            
            data = InstagramLogin(username="testuser", password="testpass")
            result = await login(data, mock_user)
            
            assert result["status"] == "challenge_required"
            assert result["challenge_type"] == "2fa"
    
    @pytest.mark.asyncio
    async def test_login_sms_challenge(self, mock_user, mock_redis, mock_instagram_client):
        """Test login with SMS challenge."""
        mock_instagram_client.login = AsyncMock(
            side_effect=Exception("CHALLENGE_SMS_REQUIRED")
        )
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis), \
             patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client):
            
            data = InstagramLogin(username="testuser", password="testpass")
            result = await login(data, mock_user)
            
            assert result["status"] == "challenge_required"
            assert result["challenge_type"] == "sms"
    
    @pytest.mark.asyncio
    async def test_login_email_challenge(self, mock_user, mock_redis, mock_instagram_client):
        """Test login with email challenge."""
        mock_instagram_client.login = AsyncMock(
            side_effect=Exception("CHALLENGE_EMAIL_REQUIRED")
        )
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis), \
             patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client):
            
            data = InstagramLogin(username="testuser", password="testpass")
            result = await login(data, mock_user)
            
            assert result["status"] == "challenge_required"
            assert result["challenge_type"] == "email"
    
    @pytest.mark.asyncio
    async def test_login_other_error(self, mock_user, mock_redis, mock_instagram_client):
        """Test login with other error."""
        mock_instagram_client.login = AsyncMock(
            side_effect=Exception("Unknown error")
        )
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis), \
             patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client):
            
            data = InstagramLogin(username="testuser", password="testpass")
            
            with pytest.raises(Exception) as exc_info:
                await login(data, mock_user)
            assert exc_info.value.status_code == 400


# ==================== CHALLENGE TESTS ====================

class TestChallenge:
    """Test challenge endpoints."""
    
    @pytest.mark.asyncio
    async def test_resolve_challenge_success(self, mock_user, mock_redis, mock_instagram_client):
        """Test resolving challenge successfully."""
        mock_redis.get = AsyncMock(return_value=json.dumps({"type": "2fa"}))
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis), \
             patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client):
            
            data = InstagramChallenge(username="testuser", code="123456")
            result = await resolve_challenge(data, mock_user)
            
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_resolve_challenge_no_pending(self, mock_user, mock_redis):
        """Test resolving challenge with no pending challenge."""
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis):
            data = InstagramChallenge(username="testuser", code="123456")
            
            with pytest.raises(Exception) as exc_info:
                await resolve_challenge(data, mock_user)
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_resolve_challenge_invalid_code(self, mock_user, mock_redis, mock_instagram_client):
        """Test resolving challenge with invalid code."""
        mock_redis.get = AsyncMock(return_value=json.dumps({"type": "2fa"}))
        mock_instagram_client.login = AsyncMock(
            side_effect=Exception("CHALLENGE_INVALID_CODE")
        )
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis), \
             patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client):
            
            data = InstagramChallenge(username="testuser", code="wrong")
            result = await resolve_challenge(data, mock_user)
            
            assert result["status"] == "invalid_code"
    
    @pytest.mark.asyncio
    async def test_request_challenge_code_success(self, mock_user, mock_instagram_client):
        """Test requesting challenge code."""
        with patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client):
            result = await request_challenge_code(
                username="testuser",
                method="email",
                current_user=mock_user
            )
            
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_request_challenge_code_failed(self, mock_user, mock_instagram_client):
        """Test requesting challenge code failure."""
        mock_instagram_client.request_challenge_code = AsyncMock(return_value=False)
        
        with patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client):
            with pytest.raises(Exception) as exc_info:
                await request_challenge_code(
                    username="testuser",
                    method="sms",
                    current_user=mock_user
                )
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_request_challenge_code_error(self, mock_user, mock_instagram_client):
        """Test requesting challenge code with error."""
        mock_instagram_client.request_challenge_code = AsyncMock(
            side_effect=Exception("Network error")
        )
        
        with patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client):
            with pytest.raises(Exception) as exc_info:
                await request_challenge_code(
                    username="testuser",
                    method="email",
                    current_user=mock_user
                )
            assert exc_info.value.status_code == 400


# ==================== UPLOAD TESTS ====================

class TestUpload:
    """Test upload endpoints."""
    
    @pytest.mark.asyncio
    async def test_upload_photo_success(self, mock_user, mock_redis, 
                                        mock_subscription_service, mock_instagram_client):
        """Test uploading photo."""
        mock_redis.get = AsyncMock(return_value=json.dumps({"session": "data"}))
        
        # Mock file upload
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.file = MagicMock()
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis), \
             patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client), \
             patch('shutil.copyfileobj'), \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove'), \
             patch('builtins.open', MagicMock()):
            
            result = await upload_media(
                username="testuser",
                caption="Test caption",
                media_type="photo",
                file=mock_file,
                current_user=mock_user,
                service=mock_subscription_service
            )
            
            assert result["status"] == "success"
            assert result["media_pk"] == "123"
    
    @pytest.mark.asyncio
    async def test_upload_video_success(self, mock_user, mock_redis,
                                        mock_subscription_service, mock_instagram_client):
        """Test uploading video."""
        mock_redis.get = AsyncMock(return_value=json.dumps({"session": "data"}))
        
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file = MagicMock()
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis), \
             patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client), \
             patch('shutil.copyfileobj'), \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove'), \
             patch('builtins.open', MagicMock()):
            
            result = await upload_media(
                username="testuser",
                caption="Test video",
                media_type="video",
                file=mock_file,
                current_user=mock_user,
                service=mock_subscription_service
            )
            
            assert result["status"] == "success"
            assert result["media_pk"] == "456"
    
    @pytest.mark.asyncio
    async def test_upload_reel_success(self, mock_user, mock_redis,
                                       mock_subscription_service, mock_instagram_client):
        """Test uploading reel."""
        mock_redis.get = AsyncMock(return_value=json.dumps({"session": "data"}))
        
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file = MagicMock()
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis), \
             patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client), \
             patch('shutil.copyfileobj'), \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove'), \
             patch('builtins.open', MagicMock()):
            
            result = await upload_media(
                username="testuser",
                caption="Test reel",
                media_type="reel",
                file=mock_file,
                current_user=mock_user,
                service=mock_subscription_service
            )
            
            assert result["status"] == "success"
            assert result["media_pk"] == "789"
    
    @pytest.mark.asyncio
    async def test_upload_invalid_type(self, mock_user, mock_redis,
                                       mock_subscription_service, mock_instagram_client):
        """Test uploading with invalid media type returns error."""
        mock_redis.get = AsyncMock(return_value=json.dumps({"session": "data"}))
        mock_instagram_client.load_settings = AsyncMock()
        
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.file = MagicMock()
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis), \
             patch('api.routes.instagram.InstagramClient', return_value=mock_instagram_client), \
             patch('api.routes.instagram.shutil.copyfileobj'), \
             patch('api.routes.instagram.os.makedirs'), \
             patch('api.routes.instagram.os.path.exists', return_value=True), \
             patch('api.routes.instagram.os.remove'), \
             patch('builtins.open', MagicMock()):
            
            with pytest.raises(HTTPException) as exc_info:
                await upload_media(
                    username="testuser",
                    caption="Test",
                    media_type="invalid",
                    file=mock_file,
                    current_user=mock_user,
                    service=mock_subscription_service
                )
            # Invalid type returns 400 or 500 depending on error handling
            assert exc_info.value.status_code in [400, 500]
    
    @pytest.mark.asyncio
    async def test_upload_not_logged_in(self, mock_user, mock_redis,
                                        mock_subscription_service):
        """Test uploading without session."""
        mock_redis.get = AsyncMock(return_value=None)
        
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.file = MagicMock()
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis):
            with pytest.raises(Exception) as exc_info:
                await upload_media(
                    username="testuser",
                    caption="Test",
                    media_type="photo",
                    file=mock_file,
                    current_user=mock_user,
                    service=mock_subscription_service
                )
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_upload_limit_exceeded(self, mock_user, mock_redis,
                                         mock_subscription_service):
        """Test uploading when limit exceeded."""
        mock_subscription_service.can_use_feature = AsyncMock(return_value=False)
        
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.file = MagicMock()
        
        with patch('api.routes.instagram.get_redis', return_value=mock_redis):
            with pytest.raises(Exception) as exc_info:
                await upload_media(
                    username="testuser",
                    caption="Test",
                    media_type="photo",
                    file=mock_file,
                    current_user=mock_user,
                    service=mock_subscription_service
                )
            assert exc_info.value.status_code == 402


# ==================== SESSION TESTS ====================

class TestSessions:
    """Test session management endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_sessions(self, mock_user, mock_session, mock_challenge):
        """Test listing sessions."""
        mock_session_manager = AsyncMock()
        mock_session_manager.get_all_sessions = AsyncMock(return_value=[mock_session])
        mock_session_manager.get_active_challenges = AsyncMock(return_value=[mock_challenge])
        
        with patch('api.routes.instagram.session_manager', mock_session_manager):
            result = await list_sessions(current_user=mock_user)
            
            assert "sessions" in result
            assert len(result["sessions"]) == 1
    
    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, mock_user):
        """Test listing sessions when empty."""
        mock_session_manager = AsyncMock()
        mock_session_manager.get_all_sessions = AsyncMock(return_value=[])
        
        with patch('api.routes.instagram.session_manager', mock_session_manager):
            result = await list_sessions(current_user=mock_user)
            
            assert result["sessions"] == []
    
    @pytest.mark.asyncio
    async def test_get_session_found(self, mock_user, mock_session, mock_challenge):
        """Test getting a specific session."""
        mock_session_manager = AsyncMock()
        mock_session_manager.get_session = AsyncMock(return_value=mock_session)
        mock_session_manager.get_active_challenges = AsyncMock(return_value=[mock_challenge])
        
        with patch('api.routes.instagram.session_manager', mock_session_manager):
            result = await get_session("testuser", current_user=mock_user)
            
            assert result["username"] == "testuser"
            assert result["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_user):
        """Test getting non-existent session."""
        mock_session_manager = AsyncMock()
        mock_session_manager.get_session = AsyncMock(return_value=None)
        
        with patch('api.routes.instagram.session_manager', mock_session_manager):
            with pytest.raises(Exception) as exc_info:
                await get_session("unknown", current_user=mock_user)
            assert exc_info.value.status_code == 404


# ==================== ROUTER TESTS ====================

class TestRouter:
    """Test router configuration."""
    
    def test_router_exists(self):
        """Test that router is defined."""
        assert router is not None
    
    def test_router_has_routes(self):
        """Test that router has routes defined."""
        routes = [r.path for r in router.routes]
        assert "/login" in routes
        assert "/upload" in routes
        assert "/sessions" in routes
