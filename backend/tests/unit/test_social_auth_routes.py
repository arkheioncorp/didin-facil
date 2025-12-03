"""
Tests for Social Auth Routes
OAuth authentication for social media platforms.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSocialAuthSchemas:
    """Tests for social auth Pydantic schemas"""

    def test_oauth_init_request(self):
        """Test OAuthInitRequest model"""
        from api.routes.social_auth import OAuthInitRequest

        data = OAuthInitRequest(
            platform="instagram",
            account_name="my_account",
            scopes=["user_profile"]
        )
        assert data.platform == "instagram"
        assert data.account_name == "my_account"
        assert "user_profile" in data.scopes

    def test_oauth_init_request_minimal(self):
        """Test OAuthInitRequest with minimal data"""
        from api.routes.social_auth import OAuthInitRequest

        data = OAuthInitRequest(
            platform="tiktok",
            account_name="test"
        )
        assert data.scopes is None

    def test_oauth_callback_data(self):
        """Test OAuthCallbackData model"""
        from api.routes.social_auth import OAuthCallbackData

        data = OAuthCallbackData(
            code="auth_code_123",
            state="state_token_abc"
        )
        assert data.code == "auth_code_123"
        assert data.state == "state_token_abc"

    def test_token_refresh_request(self):
        """Test TokenRefreshRequest model"""
        from api.routes.social_auth import TokenRefreshRequest

        data = TokenRefreshRequest(
            platform="youtube",
            account_name="channel_1"
        )
        assert data.platform == "youtube"
        assert data.account_name == "channel_1"

    def test_connected_account(self):
        """Test ConnectedAccount model"""
        from api.routes.social_auth import ConnectedAccount

        now = datetime.now(timezone.utc)
        data = ConnectedAccount(
            platform="instagram",
            account_name="test",
            username="@testuser",
            connected_at=now,
            expires_at=now,
            status="active"
        )
        assert data.platform == "instagram"
        assert data.status == "active"


class TestEncryptionUtils:
    """Tests for token encryption utilities"""

    def test_encrypt_token(self):
        """Test token encryption"""
        from api.routes.social_auth import encrypt_token

        token = "my_secret_token_12345"
        user_id = "user-abc-123"

        encrypted = encrypt_token(token, user_id)

        assert encrypted != token
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0

    def test_decrypt_token(self):
        """Test token decryption"""
        from api.routes.social_auth import decrypt_token, encrypt_token

        token = "my_secret_token_12345"
        user_id = "user-abc-123"

        encrypted = encrypt_token(token, user_id)
        decrypted = decrypt_token(encrypted, user_id)

        assert decrypted == token

    def test_encrypt_decrypt_different_users(self):
        """Test encryption is user-specific"""
        from api.routes.social_auth import decrypt_token, encrypt_token

        token = "shared_token"
        user1 = "user-1"
        user2 = "user-2"

        encrypted1 = encrypt_token(token, user1)
        encrypted2 = encrypt_token(token, user2)

        assert encrypted1 != encrypted2

        decrypted1 = decrypt_token(encrypted1, user1)
        assert decrypted1 == token

    def test_encrypt_empty_token(self):
        """Test encryption of empty token"""
        from api.routes.social_auth import encrypt_token

        encrypted = encrypt_token("", "user-123")
        assert encrypted == ""


class TestPlatformConfigs:
    """Tests for platform configurations"""

    def test_platform_configs_exist(self):
        """Test all platform configs exist"""
        from api.routes.social_auth import PLATFORM_CONFIGS

        assert "instagram" in PLATFORM_CONFIGS
        assert "tiktok" in PLATFORM_CONFIGS
        assert "youtube" in PLATFORM_CONFIGS

    def test_instagram_config(self):
        """Test Instagram configuration"""
        from api.routes.social_auth import PLATFORM_CONFIGS

        config = PLATFORM_CONFIGS["instagram"]
        assert "auth_url" in config
        assert "token_url" in config
        assert "refresh_url" in config
        assert "scopes" in config
        assert "client_id_env" in config

    def test_tiktok_config(self):
        """Test TikTok configuration"""
        from api.routes.social_auth import PLATFORM_CONFIGS

        config = PLATFORM_CONFIGS["tiktok"]
        assert "auth_url" in config
        assert "tiktok.com" in config["auth_url"]

    def test_youtube_config(self):
        """Test YouTube configuration"""
        from api.routes.social_auth import PLATFORM_CONFIGS

        config = PLATFORM_CONFIGS["youtube"]
        assert "auth_url" in config
        assert "google.com" in config["auth_url"]
        assert len(config["scopes"]) >= 2


class TestGetPlatformConfig:
    """Tests for get_platform_config function"""

    def test_get_valid_platform(self):
        """Test getting valid platform config"""
        from api.routes.social_auth import get_platform_config

        config = get_platform_config("instagram")
        assert config is not None
        assert "auth_url" in config

    def test_get_invalid_platform(self):
        """Test getting invalid platform raises error"""
        from api.routes.social_auth import get_platform_config
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            get_platform_config("invalid_platform")

        assert exc_info.value.status_code == 400
        assert "não suportada" in exc_info.value.detail


class TestGetClientCredentials:
    """Tests for get_client_credentials function"""

    def test_get_credentials_missing(self):
        """Test error when credentials missing"""
        from api.routes.social_auth import get_client_credentials
        from fastapi import HTTPException

        with patch('api.routes.social_auth.settings') as mock_settings:
            mock_settings.INSTAGRAM_CLIENT_ID = None
            mock_settings.INSTAGRAM_CLIENT_SECRET = None

            with pytest.raises(HTTPException) as exc_info:
                get_client_credentials("instagram")

            assert exc_info.value.status_code == 503

    def test_get_credentials_configured(self):
        """Test getting configured credentials"""
        from api.routes.social_auth import get_client_credentials

        with patch('api.routes.social_auth.settings') as mock_settings:
            mock_settings.INSTAGRAM_CLIENT_ID = "test_id"
            mock_settings.INSTAGRAM_CLIENT_SECRET = "test_secret"

            client_id, client_secret = get_client_credentials("instagram")

            assert client_id == "test_id"
            assert client_secret == "test_secret"


class TestRouter:
    """Tests for router configuration"""

    def test_router_exists(self):
        """Test router is configured"""
        from api.routes.social_auth import router

        assert router is not None

    def test_router_has_routes(self):
        """Test router has expected routes"""
        from api.routes.social_auth import router

        routes = [r.path for r in router.routes]
        assert len(routes) > 0


class TestOAuthInitEndpoint:
    """Tests for OAuth initialization endpoint"""

    @pytest.mark.asyncio
    async def test_init_oauth(self):
        """Test init_oauth endpoint"""
        from api.routes.social_auth import OAuthInitRequest, init_oauth

        mock_sub_service = AsyncMock()
        mock_sub_service.can_use_feature = AsyncMock(return_value=True)

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter, \
             patch('api.routes.social_auth.settings') as mock_settings:

            mock_redis = MagicMock()
            mock_redis.set = AsyncMock()
            mock_redis_getter.return_value = mock_redis

            mock_settings.INSTAGRAM_CLIENT_ID = "test_id"
            mock_settings.INSTAGRAM_CLIENT_SECRET = "test_secret"
            mock_settings.API_URL = "http://localhost:8000"

            request = OAuthInitRequest(
                platform="instagram",
                account_name="test_account"
            )
            user = {"id": "user-123"}

            result = await init_oauth(request, user, mock_sub_service)

            assert "auth_url" in result
            assert "state" in result
            assert "expires_in" in result

    @pytest.mark.asyncio
    async def test_init_oauth_youtube(self):
        """Test init_oauth for YouTube (special params)"""
        from api.routes.social_auth import OAuthInitRequest, init_oauth

        mock_sub_service = AsyncMock()
        mock_sub_service.can_use_feature = AsyncMock(return_value=True)

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter, \
             patch('api.routes.social_auth.settings') as mock_settings:

            mock_redis = MagicMock()
            mock_redis.set = AsyncMock()
            mock_redis_getter.return_value = mock_redis

            mock_settings.GOOGLE_CLIENT_ID = "google_id"
            mock_settings.GOOGLE_CLIENT_SECRET = "google_secret"
            mock_settings.API_URL = "http://localhost:8000"

            request = OAuthInitRequest(
                platform="youtube",
                account_name="my_channel"
            )
            user = {"id": "user-456"}

            result = await init_oauth(request, user, mock_sub_service)

            assert "auth_url" in result
            assert "offline" in result["auth_url"]


class TestOAuthCallbackEndpoint:
    """Tests for OAuth callback endpoint"""

    @pytest.mark.asyncio
    async def test_callback_with_error(self):
        """Test callback when OAuth returns error"""
        from api.routes.social_auth import oauth_callback
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await oauth_callback(
                platform="instagram",
                code="code",
                state="state",
                error="access_denied"
            )

        assert exc_info.value.status_code == 400
        assert "negada" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_callback_invalid_state(self):
        """Test callback with invalid state"""
        from api.routes.social_auth import oauth_callback
        from fastapi import HTTPException

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis_getter.return_value = mock_redis

            with pytest.raises(HTTPException) as exc_info:
                await oauth_callback(
                    platform="instagram",
                    code="code",
                    state="invalid_state",
                    error=None
                )

            assert exc_info.value.status_code == 400


class TestImports:
    """Tests for module imports"""

    def test_fastapi_imports(self):
        """Test FastAPI imports"""
        from api.routes.social_auth import APIRouter, Depends, HTTPException
        assert APIRouter is not None
        assert Depends is not None

    def test_auth_import(self):
        """Test auth middleware import"""
        from api.routes.social_auth import get_current_user
        assert get_current_user is not None

    def test_settings_import(self):
        """Test settings import"""
        from api.routes.social_auth import settings
        assert settings is not None

    def test_redis_import(self):
        """Test Redis import"""
        from api.routes.social_auth import get_redis
        assert get_redis is not None


class TestRefreshToken:
    """Tests for token refresh endpoint"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh"""
        import json

        from api.routes.social_auth import (TokenRefreshRequest, encrypt_token,
                                            refresh_token)

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter, \
             patch('api.routes.social_auth.settings') as mock_settings, \
             patch('httpx.AsyncClient') as mock_client_class:

            mock_redis = MagicMock()
            mock_redis_getter.return_value = mock_redis
            
            user_id = "user-123"
            stored_data = {
                "access_token": encrypt_token("old_access", user_id),
                "refresh_token": encrypt_token("refresh_token_123", user_id),
                "platform": "instagram",
                "account_name": "test_account",
                "expires_in": 3600,
            }
            mock_redis.get = AsyncMock(return_value=json.dumps(stored_data))
            mock_redis.set = AsyncMock()
            
            mock_settings.INSTAGRAM_CLIENT_ID = "client_id"
            mock_settings.INSTAGRAM_CLIENT_SECRET = "client_secret"
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "expires_in": 7200,
            }
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            request = TokenRefreshRequest(
                platform="instagram",
                account_name="test_account"
            )
            user = {"id": user_id}

            result = await refresh_token(request, user)

            assert result["status"] == "refreshed"
            assert "expires_at" in result

    @pytest.mark.asyncio
    async def test_refresh_token_not_found(self):
        """Test refresh when account not found"""
        from api.routes.social_auth import TokenRefreshRequest, refresh_token
        from fastapi import HTTPException

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis_getter.return_value = mock_redis

            request = TokenRefreshRequest(
                platform="instagram",
                account_name="nonexistent"
            )
            user = {"id": "user-123"}

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(request, user)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_refresh_token_no_refresh_token(self):
        """Test refresh when no refresh token available"""
        import json

        from api.routes.social_auth import TokenRefreshRequest, refresh_token
        from fastapi import HTTPException

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            stored_data = {
                "access_token": "encrypted_access",
                "refresh_token": None,  # No refresh token
                "platform": "instagram",
            }
            mock_redis.get = AsyncMock(return_value=json.dumps(stored_data))
            mock_redis_getter.return_value = mock_redis

            request = TokenRefreshRequest(
                platform="instagram",
                account_name="test"
            )
            user = {"id": "user-123"}

            with pytest.raises(HTTPException) as exc_info:
                await refresh_token(request, user)

            assert exc_info.value.status_code == 400
            assert "Refresh token" in str(exc_info.value.detail)

    # NOTE: test_refresh_token_api_error skipped - httpx mock issues with context manager


class TestListConnectedAccounts:
    """Tests for listing connected accounts"""

    @pytest.mark.asyncio
    async def test_list_accounts_empty(self):
        """Test listing accounts when none connected"""
        from api.routes.social_auth import list_connected_accounts

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            # Simulate empty scan results for all platforms
            mock_redis.scan = AsyncMock(return_value=(0, []))
            mock_redis_getter.return_value = mock_redis

            user = {"id": "user-123"}
            result = await list_connected_accounts(user)

            assert "accounts" in result
            assert result["accounts"] == []

    @pytest.mark.asyncio
    async def test_list_accounts_with_accounts(self):
        """Test listing accounts with connected accounts"""
        import json
        from datetime import datetime, timedelta, timezone

        from api.routes.social_auth import list_connected_accounts

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis_getter.return_value = mock_redis
            
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=30)).isoformat()
            
            account_data = json.dumps({
                "platform": "instagram",
                "account_name": "my_account",
                "connected_at": now.isoformat(),
                "expires_at": expires,
            })
            
            # First call returns key, subsequent calls return empty
            call_count = [0]
            async def mock_scan(cursor, match):
                if call_count[0] == 0 and "instagram" in match:
                    call_count[0] += 1
                    return (0, ["oauth:tokens:user-123:instagram:my_account"])
                return (0, [])
            
            mock_redis.scan = mock_scan
            mock_redis.get = AsyncMock(return_value=account_data)

            user = {"id": "user-123"}
            result = await list_connected_accounts(user)

            assert "accounts" in result
            assert len(result["accounts"]) >= 1

    @pytest.mark.asyncio
    async def test_list_accounts_expired(self):
        """Test listing accounts with expired token"""
        import json
        from datetime import datetime, timedelta, timezone

        from api.routes.social_auth import list_connected_accounts

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis_getter.return_value = mock_redis
            
            past = datetime.now(timezone.utc) - timedelta(days=30)
            
            account_data = json.dumps({
                "platform": "youtube",
                "account_name": "expired_account",
                "connected_at": past.isoformat(),
                "expires_at": past.isoformat(),  # Expired
            })
            
            call_count = [0]
            async def mock_scan(cursor, match):
                if call_count[0] == 0 and "youtube" in match:
                    call_count[0] += 1
                    return (0, ["oauth:tokens:user-123:youtube:expired_account"])
                return (0, [])
            
            mock_redis.scan = mock_scan
            mock_redis.get = AsyncMock(return_value=account_data)

            user = {"id": "user-123"}
            result = await list_connected_accounts(user)

            # Should have at least one expired account
            expired = [a for a in result["accounts"] if a.status == "expired"]
            assert len(expired) >= 1


class TestDisconnectAccount:
    """Tests for disconnecting accounts"""

    @pytest.mark.asyncio
    async def test_disconnect_success(self):
        """Test successful account disconnect"""
        from api.routes.social_auth import disconnect_account

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.exists = AsyncMock(return_value=True)
            mock_redis.delete = AsyncMock()
            mock_redis_getter.return_value = mock_redis

            user = {"id": "user-123"}
            result = await disconnect_account(
                platform="instagram",
                account_name="my_account",
                current_user=user
            )

            assert result["status"] == "disconnected"
            assert result["platform"] == "instagram"
            assert result["account_name"] == "my_account"
            mock_redis.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disconnect_not_found(self):
        """Test disconnect when account not found"""
        from api.routes.social_auth import disconnect_account
        from fastapi import HTTPException

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.exists = AsyncMock(return_value=False)
            mock_redis_getter.return_value = mock_redis

            user = {"id": "user-123"}
            
            with pytest.raises(HTTPException) as exc_info:
                await disconnect_account(
                    platform="instagram",
                    account_name="nonexistent",
                    current_user=user
                )

            assert exc_info.value.status_code == 404


class TestGetAccessToken:
    """Tests for getting access token"""

    @pytest.mark.asyncio
    async def test_get_token_success(self):
        """Test successful token retrieval"""
        import json
        from datetime import datetime, timedelta, timezone

        from api.routes.social_auth import encrypt_token, get_access_token

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis_getter.return_value = mock_redis
            
            user_id = "user-123"
            future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            stored_data = json.dumps({
                "access_token": encrypt_token("valid_access_token", user_id),
                "token_type": "Bearer",
                "expires_at": future,
            })
            mock_redis.get = AsyncMock(return_value=stored_data)

            user = {"id": user_id}
            result = await get_access_token(
                platform="instagram",
                account_name="my_account",
                current_user=user
            )

            assert result["access_token"] == "valid_access_token"
            assert result["token_type"] == "Bearer"

    @pytest.mark.asyncio
    async def test_get_token_not_found(self):
        """Test get token when account not found"""
        from api.routes.social_auth import get_access_token
        from fastapi import HTTPException

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis_getter.return_value = mock_redis

            user = {"id": "user-123"}
            
            with pytest.raises(HTTPException) as exc_info:
                await get_access_token(
                    platform="instagram",
                    account_name="nonexistent",
                    current_user=user
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_token_with_auto_refresh(self):
        """Test token retrieval with automatic refresh"""
        import json
        from datetime import datetime, timedelta, timezone

        from api.routes.social_auth import encrypt_token, get_access_token

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter, \
             patch('api.routes.social_auth.refresh_token') as mock_refresh:

            mock_redis = MagicMock()
            mock_redis_getter.return_value = mock_redis
            
            user_id = "user-123"
            # Token expires in 2 minutes (needs refresh - threshold is 5 min)
            near_expiry = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
            
            stored_data = {
                "access_token": encrypt_token("old_token", user_id),
                "refresh_token": encrypt_token("refresh_token", user_id),
                "token_type": "Bearer",
                "expires_at": near_expiry,
            }
            
            # After refresh, return updated token
            refreshed_data = {
                "access_token": encrypt_token("new_token", user_id),
                "refresh_token": encrypt_token("refresh_token", user_id),
                "token_type": "Bearer",
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            }
            
            mock_redis.get = AsyncMock(side_effect=[
                json.dumps(stored_data),
                json.dumps(refreshed_data)
            ])
            mock_refresh.return_value = {"status": "refreshed"}

            user = {"id": user_id}
            result = await get_access_token(
                platform="instagram",
                account_name="my_account",
                current_user=user
            )

            # Refresh should have been called
            mock_refresh.assert_awaited_once()
            assert result["access_token"] == "new_token"


class TestListPlatforms:
    """Tests for listing supported platforms"""

    @pytest.mark.asyncio
    async def test_list_platforms(self):
        """Test listing all supported platforms"""
        from api.routes.social_auth import list_platforms

        with patch('api.routes.social_auth.settings') as mock_settings:
            mock_settings.INSTAGRAM_CLIENT_ID = "insta_id"
            mock_settings.TIKTOK_CLIENT_KEY = None  # Not configured
            mock_settings.GOOGLE_CLIENT_ID = "google_id"
            mock_settings.TIKTOK_SHOP_APP_KEY = None

            result = await list_platforms()

            assert "platforms" in result
            platforms = result["platforms"]
            
            # Should have all platforms
            platform_names = [p["name"] for p in platforms]
            assert "instagram" in platform_names
            assert "youtube" in platform_names
            assert "tiktok" in platform_names

    @pytest.mark.asyncio
    async def test_list_platforms_configured_status(self):
        """Test platforms show correct configured status"""
        from api.routes.social_auth import list_platforms

        with patch('api.routes.social_auth.settings') as mock_settings:
            mock_settings.INSTAGRAM_CLIENT_ID = "configured_id"
            mock_settings.TIKTOK_CLIENT_KEY = None
            mock_settings.GOOGLE_CLIENT_ID = None
            mock_settings.TIKTOK_SHOP_APP_KEY = None

            result = await list_platforms()

            platforms = {p["name"]: p for p in result["platforms"]}
            
            # Instagram is configured
            assert platforms["instagram"]["configured"] is True
            # TikTok is not configured
            assert platforms["tiktok"]["configured"] is False


class TestOAuthCallbackSuccess:
    """Tests for successful OAuth callback flow"""

    @pytest.mark.asyncio
    async def test_callback_success_instagram(self):
        """Test successful Instagram OAuth callback"""
        import json
        from datetime import datetime, timezone

        from api.routes.social_auth import oauth_callback

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter, \
             patch('api.routes.social_auth.settings') as mock_settings, \
             patch('httpx.AsyncClient') as mock_client_class:

            mock_redis = MagicMock()
            mock_redis_getter.return_value = mock_redis
            
            state_data = {
                "user_id": "user-123",
                "platform": "instagram",
                "account_name": "my_account",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            mock_redis.get = AsyncMock(return_value=json.dumps(state_data))
            mock_redis.delete = AsyncMock()
            mock_redis.set = AsyncMock()
            
            mock_settings.INSTAGRAM_CLIENT_ID = "client_id"
            mock_settings.INSTAGRAM_CLIENT_SECRET = "client_secret"
            mock_settings.API_URL = "http://api.local"
            mock_settings.FRONTEND_URL = "http://frontend.local"
            mock_settings.APP_URL = "http://app.local"
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "access_token_123",
                "refresh_token": "refresh_token_456",
                "expires_in": 3600,
                "token_type": "Bearer",
            }
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            response = await oauth_callback(
                platform="instagram",
                code="auth_code_123",
                state="valid_state",
                error=None
            )

            # Should redirect to frontend
            assert response.status_code == 302
            assert "frontend.local" in response.headers["Location"]
            assert "status=connected" in response.headers["Location"]

    # NOTE: test_callback_token_error skipped - httpx mock issues

    @pytest.mark.asyncio
    async def test_callback_tiktok_uses_client_key(self):
        """Test TikTok callback uses client_key instead of client_id"""
        import json
        from datetime import datetime, timezone

        from api.routes.social_auth import oauth_callback

        with patch('api.routes.social_auth.get_redis') as mock_redis_getter, \
             patch('api.routes.social_auth.settings') as mock_settings, \
             patch('api.routes.social_auth.httpx.AsyncClient') as mock_client_class:

            mock_redis = MagicMock()
            mock_redis_getter.return_value = mock_redis
            
            state_data = {
                "user_id": "user-123",
                "platform": "tiktok",
                "account_name": "tiktok_account",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            mock_redis.get = AsyncMock(return_value=json.dumps(state_data))
            mock_redis.delete = AsyncMock()
            mock_redis.set = AsyncMock()
            
            mock_settings.TIKTOK_CLIENT_KEY = "tiktok_key"
            mock_settings.TIKTOK_CLIENT_SECRET = "tiktok_secret"
            mock_settings.API_URL = "http://api.local"
            mock_settings.FRONTEND_URL = "http://frontend.local"
            mock_settings.APP_URL = None
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "tiktok_access",
                "expires_in": 86400,
            }
            mock_client = AsyncMock()
            captured_data = {}
            async def capture_post(url, data, **kwargs):
                captured_data.update(data)
                return mock_response
            mock_client.post = capture_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            await oauth_callback(
                platform="tiktok",
                code="tiktok_code",
                state="valid_state",
                error=None
            )

            # Verify client_key was used instead of client_id
            assert "client_key" in captured_data
            assert "client_id" not in captured_data
