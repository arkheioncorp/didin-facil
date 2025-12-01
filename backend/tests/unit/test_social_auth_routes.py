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

            result = await init_oauth(request, user)

            assert "auth_url" in result
            assert "state" in result
            assert "expires_in" in result

    @pytest.mark.asyncio
    async def test_init_oauth_youtube(self):
        """Test init_oauth for YouTube (special params)"""
        from api.routes.social_auth import OAuthInitRequest, init_oauth

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

            result = await init_oauth(request, user)

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
                    state="invalid_state"
                )

            assert exc_info.value.status_code == 400
            assert "expirado" in exc_info.value.detail


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
