"""
Tests for api/routes/social_auth.py
Social Media OAuth authentication routes testing
"""

import pytest
import json
import secrets
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi import HTTPException

from api.routes.social_auth import (
    router,
    init_oauth,
    oauth_callback,
    encrypt_token,
    decrypt_token,
    get_platform_config,
    get_client_credentials,
    PLATFORM_CONFIGS,
    OAuthInitRequest,
    OAuthCallbackData,
    TokenRefreshRequest,
    ConnectedAccount,
)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "name": "Test User",
    }


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    return redis


@pytest.fixture
def instagram_init_request():
    """Sample Instagram OAuth init request."""
    return OAuthInitRequest(
        platform="instagram",
        account_name="my_instagram_account",
        scopes=["user_profile", "user_media"]
    )


@pytest.fixture
def youtube_init_request():
    """Sample YouTube OAuth init request."""
    return OAuthInitRequest(
        platform="youtube",
        account_name="my_youtube_channel"
    )


@pytest.fixture
def tiktok_init_request():
    """Sample TikTok OAuth init request."""
    return OAuthInitRequest(
        platform="tiktok",
        account_name="my_tiktok_account"
    )


# ==================== ENCRYPTION TESTS ====================

class TestEncryption:
    """Tests for token encryption/decryption."""

    def test_encrypt_token(self):
        """Test token encryption."""
        token = "my-secret-token-12345"
        user_id = "user-123"

        encrypted = encrypt_token(token, user_id)

        assert encrypted != token
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0

    def test_decrypt_token(self):
        """Test token decryption."""
        token = "my-secret-token-12345"
        user_id = "user-123"

        encrypted = encrypt_token(token, user_id)
        decrypted = decrypt_token(encrypted, user_id)

        assert decrypted == token

    def test_encryption_different_users(self):
        """Test that different users get different encryptions."""
        token = "same-token"

        encrypted1 = encrypt_token(token, "user-1")
        encrypted2 = encrypt_token(token, "user-2")

        assert encrypted1 != encrypted2

    def test_decryption_wrong_user(self):
        """Test decryption with wrong user fails."""
        token = "my-token"
        encrypted = encrypt_token(token, "user-1")

        # Decrypting with wrong user should give garbage
        decrypted = decrypt_token(encrypted, "user-2")
        assert decrypted != token


# ==================== PLATFORM CONFIG TESTS ====================

class TestPlatformConfig:
    """Tests for platform configuration."""

    def test_get_platform_config_instagram(self):
        """Test getting Instagram config."""
        config = get_platform_config("instagram")

        assert config["auth_url"] == "https://api.instagram.com/oauth/authorize"
        assert "user_profile" in config["scopes"]

    def test_get_platform_config_youtube(self):
        """Test getting YouTube config."""
        config = get_platform_config("youtube")

        assert "google.com" in config["auth_url"]
        assert any("youtube" in scope for scope in config["scopes"])

    def test_get_platform_config_tiktok(self):
        """Test getting TikTok config."""
        config = get_platform_config("tiktok")

        assert "tiktok.com" in config["auth_url"]
        assert "video.upload" in config["scopes"]

    def test_get_platform_config_invalid(self):
        """Test getting config for invalid platform."""
        with pytest.raises(HTTPException) as exc_info:
            get_platform_config("facebook")

        assert exc_info.value.status_code == 400
        assert "não suportada" in str(exc_info.value.detail)

    def test_platform_configs_has_all_required_keys(self):
        """Test all platform configs have required keys."""
        required_keys = ["auth_url", "token_url", "refresh_url", "scopes", 
                        "client_id_env", "client_secret_env"]

        for platform, config in PLATFORM_CONFIGS.items():
            for key in required_keys:
                assert key in config, f"{platform} missing {key}"


class TestClientCredentials:
    """Tests for client credentials retrieval."""

    @patch("api.routes.social_auth.settings")
    def test_get_client_credentials_instagram(self, mock_settings):
        """Test getting Instagram credentials."""
        mock_settings.INSTAGRAM_CLIENT_ID = "insta-client-id"
        mock_settings.INSTAGRAM_CLIENT_SECRET = "insta-secret"

        client_id, secret = get_client_credentials("instagram")

        assert client_id == "insta-client-id"
        assert secret == "insta-secret"

    @patch("api.routes.social_auth.settings")
    def test_get_client_credentials_missing(self, mock_settings):
        """Test getting credentials when not configured."""
        mock_settings.INSTAGRAM_CLIENT_ID = None
        mock_settings.INSTAGRAM_CLIENT_SECRET = None

        with pytest.raises(HTTPException) as exc_info:
            get_client_credentials("instagram")

        assert exc_info.value.status_code == 503
        assert "não configuradas" in str(exc_info.value.detail)


# ==================== OAUTH INIT TESTS ====================

class TestInitOAuth:
    """Tests for OAuth initialization."""

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    @patch("api.routes.social_auth.get_client_credentials")
    @patch("api.routes.social_auth.settings")
    async def test_init_oauth_instagram(
        self, mock_settings, mock_get_creds, mock_get_redis, 
        mock_redis, mock_current_user, instagram_init_request
    ):
        """Test initializing Instagram OAuth."""
        mock_get_creds.return_value = ("client-id", "client-secret")
        mock_get_redis.return_value = mock_redis
        mock_settings.API_URL = "http://api.local"

        response = await init_oauth(
            data=instagram_init_request,
            current_user=mock_current_user
        )

        assert "auth_url" in response
        assert "state" in response
        assert response["expires_in"] == 600
        assert "instagram.com" in response["auth_url"]
        mock_redis.set.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    @patch("api.routes.social_auth.get_client_credentials")
    @patch("api.routes.social_auth.settings")
    async def test_init_oauth_youtube(
        self, mock_settings, mock_get_creds, mock_get_redis,
        mock_redis, mock_current_user, youtube_init_request
    ):
        """Test initializing YouTube OAuth with offline access."""
        mock_get_creds.return_value = ("client-id", "client-secret")
        mock_get_redis.return_value = mock_redis
        mock_settings.API_URL = "http://api.local"

        response = await init_oauth(
            data=youtube_init_request,
            current_user=mock_current_user
        )

        assert "auth_url" in response
        assert "access_type=offline" in response["auth_url"]
        assert "prompt=consent" in response["auth_url"]

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    @patch("api.routes.social_auth.get_client_credentials")
    @patch("api.routes.social_auth.settings")
    async def test_init_oauth_tiktok(
        self, mock_settings, mock_get_creds, mock_get_redis,
        mock_redis, mock_current_user, tiktok_init_request
    ):
        """Test initializing TikTok OAuth with client_key."""
        mock_get_creds.return_value = ("client-key", "client-secret")
        mock_get_redis.return_value = mock_redis
        mock_settings.API_URL = "http://api.local"

        response = await init_oauth(
            data=tiktok_init_request,
            current_user=mock_current_user
        )

        assert "auth_url" in response
        assert "client_key=" in response["auth_url"]

    @pytest.mark.asyncio
    async def test_init_oauth_invalid_platform(self, mock_current_user):
        """Test initializing OAuth for invalid platform."""
        request = OAuthInitRequest(
            platform="invalid_platform",
            account_name="test"
        )

        with pytest.raises(HTTPException) as exc_info:
            await init_oauth(data=request, current_user=mock_current_user)

        assert exc_info.value.status_code == 400


# ==================== OAUTH CALLBACK TESTS ====================

class TestOAuthCallback:
    """Tests for OAuth callback handling."""

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_callback_with_error(self, mock_get_redis, mock_redis):
        """Test callback with error parameter."""
        with pytest.raises(HTTPException) as exc_info:
            await oauth_callback(
                platform="instagram",
                code="auth-code",
                state="state-123",
                error="access_denied"
            )

        assert exc_info.value.status_code == 400
        assert "Autorização negada" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_callback_invalid_state(self, mock_get_redis, mock_redis):
        """Test callback with invalid state."""
        mock_get_redis.return_value = mock_redis
        mock_redis.get = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await oauth_callback(
                platform="instagram",
                code="auth-code",
                state="invalid-state",
                error=None  # Explicitly pass None for error
            )

        assert exc_info.value.status_code == 400
        assert "inválido" in str(exc_info.value.detail) or "expirado" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_callback_platform_mismatch(self, mock_get_redis, mock_redis):
        """Test callback when platform doesn't match state."""
        mock_get_redis.return_value = mock_redis
        state_data = json.dumps({
            "user_id": "user-123",
            "platform": "youtube",  # Different platform
            "account_name": "test",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        mock_redis.get = AsyncMock(return_value=state_data)
        mock_redis.delete = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await oauth_callback(
                platform="instagram",  # Different from state
                code="auth-code",
                state="valid-state",
                error=None  # Explicitly pass None for error
            )

        assert exc_info.value.status_code == 400
        # Accept either message about platform mismatch
        detail = str(exc_info.value.detail)
        assert "corresponde" in detail or "plataforma" in detail.lower() or "platform" in detail.lower()


# ==================== MODEL TESTS ====================

class TestModels:
    """Tests for Pydantic models."""

    def test_oauth_init_request(self):
        """Test OAuthInitRequest model."""
        request = OAuthInitRequest(
            platform="instagram",
            account_name="test_account",
            scopes=["user_profile"]
        )
        assert request.platform == "instagram"
        assert request.account_name == "test_account"
        assert len(request.scopes) == 1

    def test_oauth_init_request_default_scopes(self):
        """Test OAuthInitRequest with default scopes."""
        request = OAuthInitRequest(
            platform="youtube",
            account_name="test"
        )
        assert request.scopes is None

    def test_oauth_callback_data(self):
        """Test OAuthCallbackData model."""
        data = OAuthCallbackData(
            code="auth-code-123",
            state="state-456"
        )
        assert data.code == "auth-code-123"
        assert data.state == "state-456"

    def test_token_refresh_request(self):
        """Test TokenRefreshRequest model."""
        request = TokenRefreshRequest(
            platform="instagram",
            account_name="my_account"
        )
        assert request.platform == "instagram"

    def test_connected_account(self):
        """Test ConnectedAccount model."""
        now = datetime.now(timezone.utc)
        account = ConnectedAccount(
            platform="instagram",
            account_name="test_account",
            username="@test",
            connected_at=now,
            expires_at=None,
            status="active"
        )
        assert account.platform == "instagram"
        assert account.status == "active"

    def test_connected_account_expired(self):
        """Test ConnectedAccount with expired status."""
        from datetime import timedelta
        past = datetime.now(timezone.utc) - timedelta(days=30)
        
        account = ConnectedAccount(
            platform="youtube",
            account_name="expired_account",
            connected_at=past,
            expires_at=past,
            status="expired"
        )
        assert account.status == "expired"


# ==================== ROUTER TESTS ====================

class TestRouter:
    """Tests for router configuration."""

    def test_router_has_endpoints(self):
        """Verify router has expected endpoints."""
        routes = [r.path for r in router.routes]
        
        assert "/init" in routes
        assert "/callback/{platform}" in routes


# ==================== INTEGRATION TESTS ====================

class TestIntegration:
    """Integration tests for OAuth flow."""

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    @patch("api.routes.social_auth.get_client_credentials")
    @patch("api.routes.social_auth.settings")
    async def test_full_oauth_init_flow(
        self, mock_settings, mock_get_creds, mock_get_redis, mock_redis, mock_current_user
    ):
        """Test complete OAuth initialization flow."""
        mock_get_creds.return_value = ("test-client", "test-secret")
        mock_get_redis.return_value = mock_redis
        mock_settings.API_URL = "http://localhost:8000"

        request = OAuthInitRequest(
            platform="instagram",
            account_name="business_account"
        )

        response = await init_oauth(data=request, current_user=mock_current_user)

        # Verify state was saved
        assert mock_redis.set.await_count == 1
        call_args = mock_redis.set.call_args

        # Verify state data structure
        state_key = call_args[0][0]
        state_value = json.loads(call_args[0][1])

        assert "oauth:state:" in state_key
        assert state_value["user_id"] == mock_current_user["id"]
        assert state_value["platform"] == "instagram"
        assert state_value["account_name"] == "business_account"
