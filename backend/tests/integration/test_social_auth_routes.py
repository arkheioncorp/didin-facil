"""
Social Auth Routes Tests
Tests for OAuth authentication endpoints
"""

import pytest
import pytest_asyncio
import json
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta

from api.main import app
from api.routes.social_auth import encrypt_token, decrypt_token


@pytest_asyncio.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    from api.middleware.auth import get_current_user
    user = {
        "id": "user_123",
        "email": "test@example.com",
        "plan": "pro"
    }
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides = {}


class TestTokenEncryption:
    """Tests for token encryption/decryption."""

    def test_encrypt_decrypt_token(self):
        """Test token encryption and decryption."""
        original = "test_access_token_12345"
        user_id = "user_123"
        
        encrypted = encrypt_token(original, user_id)
        decrypted = decrypt_token(encrypted, user_id)
        
        assert decrypted == original
        assert encrypted != original

    def test_different_users_different_encryption(self):
        """Test that different users get different encryptions."""
        token = "same_token"
        
        enc1 = encrypt_token(token, "user_1")
        enc2 = encrypt_token(token, "user_2")
        
        assert enc1 != enc2


class TestOAuthInit:
    """Tests for OAuth initialization."""

    @pytest.mark.asyncio
    async def test_init_oauth_success(
        self,
        mock_auth_user,
        async_client
    ):
        """Test successful OAuth init."""
        with patch("api.routes.social_auth.get_redis") as mock_redis, \
             patch("api.routes.social_auth.settings") as mock_settings:
            
            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"
            mock_settings.GOOGLE_CLIENT_SECRET = "test_secret"
            mock_settings.API_URL = "http://test"
            mock_settings.JWT_SECRET_KEY = "test-secret"
            
            redis = AsyncMock()
            mock_redis.return_value = redis
            
            response = await async_client.post(
                "/social-auth/init",
                json={
                    "platform": "youtube",
                    "account_name": "my_channel"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "auth_url" in data
            assert "state" in data
            assert data["expires_in"] == 600

    @pytest.mark.asyncio
    async def test_init_oauth_invalid_platform(
        self,
        mock_auth_user,
        async_client
    ):
        """Test OAuth init with invalid platform."""
        response = await async_client.post(
            "/social-auth/init",
            json={
                "platform": "invalid_platform",
                "account_name": "test"
            }
        )
        
        assert response.status_code == 400
        assert "não suportada" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_init_oauth_unconfigured(
        self,
        mock_auth_user,
        async_client
    ):
        """Test OAuth init with unconfigured platform."""
        with patch("api.routes.social_auth.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = None
            mock_settings.GOOGLE_CLIENT_SECRET = None
            
            response = await async_client.post(
                "/social-auth/init",
                json={
                    "platform": "youtube",
                    "account_name": "test"
                }
            )
            
            assert response.status_code == 503


class TestOAuthCallback:
    """Tests for OAuth callback."""

    @pytest.mark.asyncio
    async def test_callback_invalid_state(self, async_client):
        """Test callback with invalid state."""
        with patch("api.routes.social_auth.get_redis") as mock_redis:
            redis = AsyncMock()
            redis.get.return_value = None  # State not found
            mock_redis.return_value = redis
            
            response = await async_client.get(
                "/social-auth/callback/youtube?"
                "code=test_code&state=invalid_state"
            )
            
            assert response.status_code == 400
            assert "inválido" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_callback_error_parameter(self, async_client):
        """Test callback with error from provider."""
        response = await async_client.get(
            "/social-auth/callback/youtube?"
            "code=x&error=access_denied&state=test"
        )
        
        assert response.status_code == 400
        assert "negada" in response.json()["detail"]


class TestTokenRefresh:
    """Tests for token refresh."""

    @pytest.mark.asyncio
    async def test_refresh_not_found(
        self,
        mock_auth_user,
        async_client
    ):
        """Test refresh for non-existent account."""
        with patch("api.routes.social_auth.get_redis") as mock_redis:
            redis = AsyncMock()
            redis.get.return_value = None
            mock_redis.return_value = redis
            
            response = await async_client.post(
                "/social-auth/refresh",
                json={
                    "platform": "youtube",
                    "account_name": "nonexistent"
                }
            )
            
            assert response.status_code == 404


class TestConnectedAccounts:
    """Tests for connected accounts management."""

    @pytest.mark.asyncio
    async def test_list_accounts_empty(
        self,
        mock_auth_user,
        async_client
    ):
        """Test listing accounts when none connected."""
        with patch("api.routes.social_auth.get_redis") as mock_redis:
            redis = AsyncMock()
            # Return empty scan result
            redis.scan.return_value = (0, [])
            mock_redis.return_value = redis
            
            response = await async_client.get("/social-auth/accounts")
            
            assert response.status_code == 200
            assert response.json()["accounts"] == []

    @pytest.mark.asyncio
    async def test_disconnect_account(
        self,
        mock_auth_user,
        async_client
    ):
        """Test disconnecting an account."""
        with patch("api.routes.social_auth.get_redis") as mock_redis:
            redis = AsyncMock()
            redis.exists.return_value = True
            mock_redis.return_value = redis
            
            response = await async_client.delete(
                "/social-auth/accounts/youtube/my_channel"
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent(
        self,
        mock_auth_user,
        async_client
    ):
        """Test disconnecting non-existent account."""
        with patch("api.routes.social_auth.get_redis") as mock_redis:
            redis = AsyncMock()
            redis.exists.return_value = False
            mock_redis.return_value = redis
            
            response = await async_client.delete(
                "/social-auth/accounts/youtube/nonexistent"
            )
            
            assert response.status_code == 404


class TestGetAccessToken:
    """Tests for getting access tokens."""

    @pytest.mark.asyncio
    async def test_get_token_not_found(
        self,
        mock_auth_user,
        async_client
    ):
        """Test getting token for non-existent account."""
        with patch("api.routes.social_auth.get_redis") as mock_redis:
            redis = AsyncMock()
            redis.get.return_value = None
            mock_redis.return_value = redis
            
            response = await async_client.get(
                "/social-auth/token/youtube/nonexistent"
            )
            
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_token_success(
        self,
        mock_auth_user,
        async_client
    ):
        """Test getting valid access token."""
        user_id = "user_123"
        original_token = "valid_access_token"
        encrypted = encrypt_token(original_token, user_id)
        
        token_data = {
            "access_token": encrypted,
            "token_type": "Bearer",
            "expires_at": (
                datetime.utcnow() + timedelta(hours=1)
            ).isoformat()
        }
        
        with patch("api.routes.social_auth.get_redis") as mock_redis:
            redis = AsyncMock()
            redis.get.return_value = json.dumps(token_data)
            mock_redis.return_value = redis
            
            response = await async_client.get(
                "/social-auth/token/youtube/my_channel"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == original_token
            assert data["token_type"] == "Bearer"


class TestPlatformsList:
    """Tests for platforms listing."""

    @pytest.mark.asyncio
    async def test_list_platforms(self, async_client):
        """Test listing supported platforms."""
        response = await async_client.get("/social-auth/platforms")
        
        assert response.status_code == 200
        data = response.json()
        
        platforms = {p["name"] for p in data["platforms"]}
        assert "instagram" in platforms
        assert "tiktok" in platforms
        assert "youtube" in platforms
