"""
Testes extended para api/routes/instagram.py

Cobertura: 64% → 85%+
"""

import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestInstagramSchemas:
    """Testes para schemas do Instagram."""
    
    def test_instagram_login_schema(self):
        """Test InstagramLogin schema."""
        from api.routes.instagram import InstagramLogin
        
        login = InstagramLogin(
            username="testuser",
            password="testpass123"
        )
        
        assert login.username == "testuser"
        assert login.password == "testpass123"
        assert login.verification_code is None
    
    def test_instagram_login_with_2fa(self):
        """Test InstagramLogin with 2FA code."""
        from api.routes.instagram import InstagramLogin
        
        login = InstagramLogin(
            username="testuser",
            password="testpass123",
            verification_code="123456"
        )
        
        assert login.verification_code == "123456"
    
    def test_instagram_challenge_schema(self):
        """Test InstagramChallenge schema."""
        from api.routes.instagram import InstagramChallenge
        
        challenge = InstagramChallenge(
            username="testuser",
            code="654321"
        )
        
        assert challenge.username == "testuser"
        assert challenge.code == "654321"
        assert challenge.method is None
    
    def test_instagram_post_schema(self):
        """Test InstagramPost schema."""
        from api.routes.instagram import InstagramPost
        
        post = InstagramPost(
            username="testuser",
            caption="Test caption"
        )
        
        assert post.username == "testuser"
        assert post.caption == "Test caption"
        assert post.media_type == "photo"


class TestLoginEndpoint:
    """Testes para endpoint de login."""
    
    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login."""
        from api.routes.instagram import InstagramLogin, login
        
        data = InstagramLogin(username="test", password="pass123")
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.InstagramClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.login.return_value = True
            mock_client.get_settings.return_value = {"session": "data"}
            mock_client_cls.return_value = mock_client
            
            with patch('api.routes.instagram.get_redis') as mock_get_redis:
                mock_redis = AsyncMock()
                mock_get_redis.return_value = mock_redis
                
                result = await login(data, mock_user)
                
                assert result["status"] == "success"
                mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_failed(self):
        """Test failed login returns 400 with 401 detail."""
        from api.routes.instagram import InstagramLogin, login
        
        data = InstagramLogin(username="test", password="wrongpass")
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.InstagramClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.login.return_value = False
            mock_client_cls.return_value = mock_client
            
            with pytest.raises(HTTPException) as exc:
                await login(data, mock_user)
            
            # O código joga 401 dentro de try que é capturado por except
            # e re-jogado como 400 com a mensagem original
            assert exc.value.status_code == 400
            assert "Login failed" in exc.value.detail
    
    @pytest.mark.asyncio
    async def test_login_2fa_required(self):
        """Test login with 2FA challenge."""
        from api.routes.instagram import InstagramLogin, login
        
        data = InstagramLogin(username="test", password="pass123")
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.InstagramClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.login.side_effect = Exception("CHALLENGE_2FA_REQUIRED")
            mock_client_cls.return_value = mock_client
            
            with patch('api.routes.instagram.get_redis') as mock_get_redis:
                mock_redis = AsyncMock()
                mock_get_redis.return_value = mock_redis
                
                result = await login(data, mock_user)
                
                assert result["status"] == "challenge_required"
                assert result["challenge_type"] == "2fa"
    
    @pytest.mark.asyncio
    async def test_login_sms_challenge(self):
        """Test login with SMS challenge."""
        from api.routes.instagram import InstagramLogin, login
        
        data = InstagramLogin(username="test", password="pass123")
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.InstagramClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.login.side_effect = Exception("CHALLENGE_SMS_REQUIRED")
            mock_client_cls.return_value = mock_client
            
            with patch('api.routes.instagram.get_redis') as mock_get_redis:
                mock_redis = AsyncMock()
                mock_get_redis.return_value = mock_redis
                
                result = await login(data, mock_user)
                
                assert result["status"] == "challenge_required"
                assert result["challenge_type"] == "sms"
    
    @pytest.mark.asyncio
    async def test_login_email_challenge(self):
        """Test login with email challenge."""
        from api.routes.instagram import InstagramLogin, login
        
        data = InstagramLogin(username="test", password="pass123")
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.InstagramClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.login.side_effect = Exception("CHALLENGE_EMAIL_REQUIRED")
            mock_client_cls.return_value = mock_client
            
            with patch('api.routes.instagram.get_redis') as mock_get_redis:
                mock_redis = AsyncMock()
                mock_get_redis.return_value = mock_redis
                
                result = await login(data, mock_user)
                
                assert result["status"] == "challenge_required"
                assert result["challenge_type"] == "email"
    
    @pytest.mark.asyncio
    async def test_login_generic_error(self):
        """Test login with generic error."""
        from api.routes.instagram import InstagramLogin, login
        
        data = InstagramLogin(username="test", password="pass123")
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.InstagramClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.login.side_effect = Exception("Unknown error")
            mock_client_cls.return_value = mock_client
            
            with pytest.raises(HTTPException) as exc:
                await login(data, mock_user)
            
            assert exc.value.status_code == 400


class TestResolveChallengeEndpoint:
    """Testes para endpoint de resolver challenge."""
    
    @pytest.mark.asyncio
    async def test_resolve_no_pending_challenge(self):
        """Test resolving when no challenge exists."""
        from api.routes.instagram import InstagramChallenge, resolve_challenge
        
        data = InstagramChallenge(username="test", code="123456")
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            
            with pytest.raises(HTTPException) as exc:
                await resolve_challenge(data, mock_user)
            
            assert exc.value.status_code == 400
            assert "No pending challenge" in exc.value.detail
    
    @pytest.mark.asyncio
    async def test_resolve_challenge_success(self):
        """Test successful challenge resolution."""
        from api.routes.instagram import InstagramChallenge, resolve_challenge
        
        data = InstagramChallenge(username="test", code="123456")
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = json.dumps({
                "type": "2fa",
                "username": "test"
            })
            mock_get_redis.return_value = mock_redis
            
            with patch('api.routes.instagram.InstagramClient') as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.login.return_value = True
                mock_client.get_settings.return_value = {"session": "data"}
                mock_client_cls.return_value = mock_client
                
                result = await resolve_challenge(data, mock_user)
                
                assert result["status"] == "success"
                mock_redis.delete.assert_called()
    
    @pytest.mark.asyncio
    async def test_resolve_challenge_invalid_code(self):
        """Test challenge with invalid code."""
        from api.routes.instagram import InstagramChallenge, resolve_challenge
        
        data = InstagramChallenge(username="test", code="wrong")
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = json.dumps({
                "type": "2fa",
                "username": "test"
            })
            mock_get_redis.return_value = mock_redis
            
            with patch('api.routes.instagram.InstagramClient') as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.login.side_effect = Exception("CHALLENGE")
                mock_client_cls.return_value = mock_client
                
                result = await resolve_challenge(data, mock_user)
                
                assert result["status"] == "invalid_code"


class TestRequestChallengeEndpoint:
    """Testes para endpoint de requisição de código."""
    
    @pytest.mark.asyncio
    async def test_request_code_success(self):
        """Test successful code request."""
        from api.routes.instagram import request_challenge_code
        
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.InstagramClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.request_challenge_code.return_value = True
            mock_client_cls.return_value = mock_client
            
            result = await request_challenge_code("testuser", "email", mock_user)
            
            assert result["status"] == "success"
            assert "email" in result["message"]
    
    @pytest.mark.asyncio
    async def test_request_code_failed(self):
        """Test failed code request."""
        from api.routes.instagram import request_challenge_code
        
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.InstagramClient') as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.request_challenge_code.return_value = False
            mock_client_cls.return_value = mock_client
            
            with pytest.raises(HTTPException) as exc:
                await request_challenge_code("testuser", "email", mock_user)
            
            assert exc.value.status_code == 400


class TestUploadEndpoint:
    """Testes para endpoint de upload."""
    
    @pytest.mark.asyncio
    async def test_upload_limit_reached(self):
        """Test upload when limit reached."""
        from api.routes.instagram import upload_media
        
        mock_user = {"id": 123}
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.file = MagicMock()
        
        mock_service = AsyncMock()
        mock_service.can_use_feature.return_value = False
        
        with pytest.raises(HTTPException) as exc:
            await upload_media(
                username="test",
                caption="Test caption",
                media_type="photo",
                file=mock_file,
                current_user=mock_user,
                service=mock_service
            )
        
        assert exc.value.status_code == 402
    
    @pytest.mark.asyncio
    async def test_upload_not_logged_in(self):
        """Test upload when user not logged in."""
        from api.routes.instagram import upload_media
        
        mock_user = {"id": 123}
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.file = MagicMock()
        
        mock_service = AsyncMock()
        mock_service.can_use_feature.return_value = True
        
        with patch('api.routes.instagram.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            
            with pytest.raises(HTTPException) as exc:
                await upload_media(
                    username="test",
                    caption="Test caption",
                    media_type="photo",
                    file=mock_file,
                    current_user=mock_user,
                    service=mock_service
                )
            
            assert exc.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_upload_invalid_media_type(self):
        """Test upload with invalid media type."""
        from api.routes.instagram import upload_media
        
        mock_user = {"id": 123}
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.file = MagicMock()
        
        mock_service = AsyncMock()
        mock_service.can_use_feature.return_value = True
        
        with patch('api.routes.instagram.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = json.dumps({"session": "data"})
            mock_get_redis.return_value = mock_redis
            
            with patch('api.routes.instagram.InstagramClient') as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.load_settings.return_value = None
                mock_client_cls.return_value = mock_client
                
                with patch('os.makedirs'):
                    with patch('builtins.open', MagicMock()):
                        with patch('shutil.copyfileobj'):
                            with patch('os.path.exists', return_value=True):
                                with patch('os.remove'):
                                    with pytest.raises(HTTPException) as exc:
                                        await upload_media(
                                            username="test",
                                            caption="Test caption",
                                            media_type="invalid",
                                            file=mock_file,
                                            current_user=mock_user,
                                            service=mock_service
                                        )
                                    
                                    assert exc.value.status_code == 400


class TestSessionEndpoints:
    """Testes para endpoints de sessão."""
    
    @pytest.mark.asyncio
    async def test_list_sessions(self):
        """Test listing sessions."""
        from api.routes.instagram import list_sessions
        
        mock_user = {"id": 123}
        
        mock_session = MagicMock()
        mock_session.username = "testuser"
        mock_session.status = "active"
        mock_session.is_valid = True
        mock_session.last_used = datetime.now(timezone.utc)
        mock_session.created_at = datetime.now(timezone.utc) - timedelta(days=1)
        mock_session.expires_at = datetime.now(timezone.utc) + timedelta(days=29)
        
        with patch('api.routes.instagram.session_manager') as mock_mgr:
            mock_mgr.get_all_sessions = AsyncMock(return_value=[mock_session])
            mock_mgr.get_active_challenges = AsyncMock(return_value=[])
            
            result = await list_sessions(mock_user)
            
            assert "sessions" in result
            assert len(result["sessions"]) == 1
            assert result["sessions"][0]["username"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """Test getting non-existent session."""
        from api.routes.instagram import get_session
        
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.session_manager') as mock_mgr:
            mock_mgr.get_session = AsyncMock(return_value=None)
            
            with pytest.raises(HTTPException) as exc:
                await get_session("nonexistent", mock_user)
            
            assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_session_success(self):
        """Test getting existing session."""
        from api.routes.instagram import get_session
        
        mock_user = {"id": 123}
        
        mock_session = MagicMock()
        mock_session.username = "testuser"
        mock_session.status = "active"
        mock_session.is_valid = True
        mock_session.last_used = datetime.now(timezone.utc)
        mock_session.created_at = datetime.now(timezone.utc) - timedelta(days=1)
        mock_session.expires_at = datetime.now(timezone.utc) + timedelta(days=29)
        mock_session.metadata = {"key": "value"}
        
        with patch('api.routes.instagram.session_manager') as mock_mgr:
            mock_mgr.get_session = AsyncMock(return_value=mock_session)
            mock_mgr.get_active_challenges = AsyncMock(return_value=[])
            
            result = await get_session("testuser", mock_user)
            
            assert result["username"] == "testuser"
            assert result["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_backup_session_not_found(self):
        """Test backup when no session exists."""
        from api.routes.instagram import backup_session
        
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            
            with pytest.raises(HTTPException) as exc:
                await backup_session("testuser", mock_user)
            
            assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_backup_session_success(self):
        """Test successful session backup."""
        from api.routes.instagram import backup_session
        
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = json.dumps({"session": "data"})
            mock_get_redis.return_value = mock_redis
            
            with patch('api.routes.instagram.session_manager') as mock_mgr:
                mock_mgr.backup_session = AsyncMock(return_value=True)
                
                result = await backup_session("testuser", mock_user)
                
                assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_restore_session_not_found(self):
        """Test restore when no backup exists."""
        from api.routes.instagram import restore_session
        
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.session_manager') as mock_mgr:
            mock_mgr.restore_session = AsyncMock(return_value=None)
            
            with pytest.raises(HTTPException) as exc:
                await restore_session("testuser", mock_user)
            
            assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_session(self):
        """Test deleting session."""
        from api.routes.instagram import delete_session
        
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.keys.return_value = ["key1", "key2"]
            mock_get_redis.return_value = mock_redis
            
            result = await delete_session("testuser", mock_user)
            
            assert result["status"] == "success"


class TestChallengeEndpoints:
    """Testes para endpoints de challenges."""
    
    @pytest.mark.asyncio
    async def test_list_challenges(self):
        """Test listing challenges."""
        from api.routes.instagram import list_challenges
        
        mock_user = {"id": 123}
        
        mock_challenge = MagicMock()
        mock_challenge.id = "ch123"
        mock_challenge.username = "testuser"
        mock_challenge.challenge_type.value = "2fa"
        mock_challenge.status.value = "pending"
        mock_challenge.message = "Enter code"
        mock_challenge.created_at = datetime.now(timezone.utc)
        mock_challenge.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        mock_challenge.attempts = 0
        mock_challenge.max_attempts = 3
        
        with patch('api.routes.instagram.session_manager') as mock_mgr:
            mock_mgr.get_active_challenges = AsyncMock(return_value=[mock_challenge])
            
            result = await list_challenges(current_user=mock_user)
            
            assert "challenges" in result
            assert result["total"] == 1
    
    @pytest.mark.asyncio
    async def test_get_challenge_not_found(self):
        """Test getting non-existent challenge."""
        from api.routes.instagram import get_challenge
        
        mock_user = {"id": 123}
        
        with patch('api.routes.instagram.session_manager') as mock_mgr:
            mock_mgr.get_challenge = AsyncMock(return_value=None)
            
            with pytest.raises(HTTPException) as exc:
                await get_challenge("nonexistent", mock_user)
            
            assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_challenge_success(self):
        """Test getting existing challenge."""
        from api.routes.instagram import get_challenge
        
        mock_user = {"id": 123}
        
        mock_challenge = MagicMock()
        mock_challenge.id = "ch123"
        mock_challenge.username = "testuser"
        mock_challenge.challenge_type.value = "2fa"
        mock_challenge.status.value = "pending"
        mock_challenge.message = "Enter code"
        mock_challenge.created_at = datetime.now(timezone.utc)
        mock_challenge.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        mock_challenge.resolved_at = None
        mock_challenge.attempts = 0
        mock_challenge.max_attempts = 3
        mock_challenge.metadata = {}
        
        with patch('api.routes.instagram.session_manager') as mock_mgr:
            mock_mgr.get_challenge = AsyncMock(return_value=mock_challenge)
            
            result = await get_challenge("ch123", mock_user)
            
            assert result["id"] == "ch123"
            assert result["type"] == "2fa"


class TestRouterConfiguration:
    """Testes para configuração do router."""
    
    def test_router_exists(self):
        """Test that router exists."""
        from api.routes.instagram import router
        assert router is not None
    
    def test_router_has_routes(self):
        """Test that router has routes."""
        from api.routes.instagram import router
        
        paths = [r.path for r in router.routes if hasattr(r, 'path')]
        
        assert "/login" in paths
        assert "/upload" in paths
        assert "/sessions" in paths
        assert "/challenges" in paths
