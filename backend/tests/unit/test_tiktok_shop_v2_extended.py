"""
Extended tests for TikTok Shop V2 routes.
Coverage target: 90%+
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ==================== FIXTURES ====================

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {"id": "user123", "email": "test@example.com"}


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def mock_credentials():
    """Mock TikTok Shop credentials."""
    return {
        "app_key": "test_app_key",
        "app_secret": "test_app_secret_long",
        "service_id": None
    }


@pytest.fixture
def mock_token_data():
    """Mock token data."""
    now = datetime.now(timezone.utc)
    return {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "access_token_expires_at": (now + timedelta(hours=4)).isoformat(),
        "refresh_token_expires_at": (now + timedelta(days=7)).isoformat(),
        "open_id": "open123",
        "seller_name": "Test Seller",
        "seller_base_region": "US",
        "user_type": 1
    }


@pytest.fixture
def mock_tiktok_service():
    """Mock TikTok Shop service."""
    service = MagicMock()
    service.get_auth_url = MagicMock(return_value="https://auth.tiktok.com/oauth")
    service.exchange_code = AsyncMock()
    service.refresh_token = AsyncMock()
    service.get_active_shops = AsyncMock(return_value=[])
    service.list_products = AsyncMock(return_value=([], None))
    service.close = AsyncMock()
    return service


# ==================== HELPER FUNCTION TESTS ====================

class TestHelpers:
    """Test helper functions."""
    
    def test_get_redis_key(self):
        """Test Redis key generation."""
        from api.routes.tiktok_shop_v2 import get_redis_key
        
        key = get_redis_key("user123", "credentials")
        assert key == "tiktok_shop:user123:credentials"
    
    @pytest.mark.asyncio
    async def test_get_user_credentials_not_found(self, mock_redis):
        """Test getting credentials when not found."""
        from api.routes.tiktok_shop_v2 import get_user_credentials
        
        mock_redis.get = AsyncMock(return_value=None)
        result = await get_user_credentials("user123", mock_redis)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_credentials_found(self, mock_redis, mock_credentials):
        """Test getting credentials when found."""
        from api.routes.tiktok_shop_v2 import get_user_credentials
        
        mock_redis.get = AsyncMock(return_value=json.dumps(mock_credentials))
        result = await get_user_credentials("user123", mock_redis)
        
        assert result is not None
        assert result.app_key == "test_app_key"
    
    @pytest.mark.asyncio
    async def test_save_user_credentials(self, mock_redis):
        """Test saving credentials."""
        from api.routes.tiktok_shop_v2 import (CredentialsInput,
                                               save_user_credentials)
        
        creds = CredentialsInput(
            app_key="test_key",
            app_secret="test_secret_long"
        )
        
        await save_user_credentials("user123", creds, mock_redis)
        
        mock_redis.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_user_token_not_found(self, mock_redis):
        """Test getting token when not found."""
        from api.routes.tiktok_shop_v2 import get_user_token
        
        mock_redis.get = AsyncMock(return_value=None)
        result = await get_user_token("user123", mock_redis)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_token_found(self, mock_redis, mock_token_data):
        """Test getting token when found."""
        from api.routes.tiktok_shop_v2 import get_user_token
        
        mock_redis.get = AsyncMock(return_value=json.dumps(mock_token_data))
        result = await get_user_token("user123", mock_redis)
        
        assert result is not None
        assert result.access_token == "test_access_token"
    
    @pytest.mark.asyncio
    async def test_get_service_for_user_no_credentials(self, mock_redis):
        """Test getting service without credentials."""
        from api.routes.tiktok_shop_v2 import get_service_for_user
        
        mock_redis.get = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_service_for_user("user123", mock_redis)
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_no_token(self, mock_redis):
        """Test ensure_valid_token without token."""
        from api.routes.tiktok_shop_v2 import ensure_valid_token
        
        mock_redis.get = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await ensure_valid_token("user123", mock_redis)
        
        assert exc_info.value.status_code == 401


# ==================== CREDENTIALS ENDPOINT TESTS ====================

class TestCredentialsEndpoints:
    """Test credentials endpoints."""
    
    @pytest.mark.asyncio
    async def test_set_credentials_success(self, mock_user, mock_redis):
        """Test setting credentials."""
        from api.routes.tiktok_shop_v2 import CredentialsInput, set_credentials
        
        with patch('api.routes.tiktok_shop_v2.save_user_credentials', new_callable=AsyncMock):
            result = await set_credentials(
                CredentialsInput(app_key="key123", app_secret="secret_long"),
                mock_user,
                mock_redis
            )
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_check_credentials_not_configured(self, mock_user, mock_redis):
        """Test checking credentials when not configured."""
        from api.routes.tiktok_shop_v2 import check_credentials
        
        with patch('api.routes.tiktok_shop_v2.get_user_credentials',
                   new_callable=AsyncMock, return_value=None):
            result = await check_credentials(mock_user, mock_redis)
            
            assert result["configured"] is False
            assert result["app_key"] is None
    
    @pytest.mark.asyncio
    async def test_check_credentials_configured(self, mock_user, mock_redis, mock_credentials):
        """Test checking credentials when configured."""
        from api.routes.tiktok_shop_v2 import check_credentials
        from integrations.tiktok_shop_service import TikTokShopCredentials
        
        mock_creds = TikTokShopCredentials(**mock_credentials)
        
        with patch('api.routes.tiktok_shop_v2.get_user_credentials',
                   new_callable=AsyncMock, return_value=mock_creds):
            result = await check_credentials(mock_user, mock_redis)
            
            assert result["configured"] is True
            assert "..." in result["app_key"]
    
    @pytest.mark.asyncio
    async def test_delete_credentials(self, mock_user, mock_redis):
        """Test deleting credentials."""
        from api.routes.tiktok_shop_v2 import delete_credentials
        
        result = await delete_credentials(mock_user, mock_redis)
        
        assert result["success"] is True
        assert mock_redis.delete.call_count == 3  # credentials, token, shops


# ==================== AUTH ENDPOINT TESTS ====================

class TestAuthEndpoints:
    """Test OAuth endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_auth_url_no_credentials(self, mock_user, mock_redis):
        """Test getting auth URL without credentials."""
        from api.routes.tiktok_shop_v2 import get_auth_url
        
        with patch('api.routes.tiktok_shop_v2.get_user_credentials',
                   new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_auth_url(mock_user, mock_redis)
            
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_auth_url_success(
        self, mock_user, mock_redis, mock_credentials, mock_tiktok_service
    ):
        """Test getting auth URL successfully."""
        from api.routes.tiktok_shop_v2 import get_auth_url
        from integrations.tiktok_shop_service import TikTokShopCredentials
        
        mock_creds = TikTokShopCredentials(**mock_credentials)
        
        with patch('api.routes.tiktok_shop_v2.get_user_credentials',
                   new_callable=AsyncMock, return_value=mock_creds), \
             patch('api.routes.tiktok_shop_v2.TikTokShopService',
                   return_value=mock_tiktok_service):
            
            result = await get_auth_url(mock_user, mock_redis)
            
            assert "auth_url" in result
            assert "state" in result
            assert result["expires_in"] == 600
    
    @pytest.mark.asyncio
    async def test_oauth_callback_invalid_state(self, mock_user, mock_redis):
        """Test OAuth callback with invalid state."""
        from api.routes.tiktok_shop_v2 import AuthCallbackInput, oauth_callback
        
        mock_redis.get = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await oauth_callback(
                AuthCallbackInput(code="auth_code", state="invalid_state"),
                mock_user,
                mock_redis
            )
        
        assert exc_info.value.status_code == 400


# ==================== CONNECTION STATUS TESTS ====================

class TestConnectionStatus:
    """Test connection status endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_status_not_connected(self, mock_user, mock_redis):
        """Test status when not connected."""
        from api.routes.tiktok_shop_v2 import get_connection_status
        
        with patch('api.routes.tiktok_shop_v2.get_user_token',
                   new_callable=AsyncMock, return_value=None):
            result = await get_connection_status(mock_user, mock_redis)
            
            assert result.connected is False
    
    @pytest.mark.asyncio
    async def test_get_status_connected(self, mock_user, mock_redis, mock_token_data, mock_credentials):
        """Test status when connected."""
        from api.routes.tiktok_shop_v2 import get_connection_status
        from integrations.tiktok_shop_service import (TikTokShopCredentials,
                                                      TikTokShopToken)
        
        now = datetime.now(timezone.utc)
        mock_token = TikTokShopToken(
            access_token="token",
            refresh_token="refresh",
            access_token_expires_at=now + timedelta(hours=4),
            refresh_token_expires_at=now + timedelta(days=7),
            open_id="open123",
            seller_name="Test Seller",
            seller_base_region="US",
            user_type=1
        )
        
        mock_creds = TikTokShopCredentials(**mock_credentials)
        
        # Mock get_user_credentials to return credentials
        # Mock get_user_token to return the token
        with patch('api.routes.tiktok_shop_v2.get_user_token',
                   new_callable=AsyncMock, return_value=mock_token), \
             patch('api.routes.tiktok_shop_v2.get_user_credentials',
                   new_callable=AsyncMock, return_value=mock_creds):
            
            mock_redis.get = AsyncMock(return_value=None)  # shops, product_count, last_sync
            
            result = await get_connection_status(mock_user, mock_redis)
            
            assert result.connected is True
            assert result.seller_name == "Test Seller"


# ==================== PRODUCTS ENDPOINT TESTS ====================

class TestProductsEndpoints:
    """Test products endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_products_not_connected(self, mock_user, mock_redis):
        """Test listing products when not connected."""
        from api.routes.tiktok_shop_v2 import list_products
        
        with patch('api.routes.tiktok_shop_v2.ensure_valid_token',
                   new_callable=AsyncMock,
                   side_effect=HTTPException(status_code=401, detail="Not connected")):
            with pytest.raises(HTTPException) as exc_info:
                await list_products(current_user=mock_user, redis=mock_redis)
            
            assert exc_info.value.status_code == 401


# ==================== SCHEMA TESTS ====================

class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_credentials_input_validation(self):
        """Test CredentialsInput validation."""
        from api.routes.tiktok_shop_v2 import CredentialsInput

        # Valid input
        creds = CredentialsInput(
            app_key="12345",
            app_secret="1234567890"
        )
        assert creds.app_key == "12345"
    
    def test_credentials_input_too_short(self):
        """Test CredentialsInput with too short values."""
        from api.routes.tiktok_shop_v2 import CredentialsInput
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            CredentialsInput(
                app_key="123",  # Too short (min 5)
                app_secret="1234567890"
            )
    
    def test_auth_callback_input(self):
        """Test AuthCallbackInput."""
        from api.routes.tiktok_shop_v2 import AuthCallbackInput
        
        callback = AuthCallbackInput(
            code="auth_code",
            state="state_value"
        )
        assert callback.code == "auth_code"
    
    def test_connection_status_model(self):
        """Test ConnectionStatus model."""
        from api.routes.tiktok_shop_v2 import ConnectionStatus
        
        status = ConnectionStatus(connected=True, seller_name="Test")
        assert status.connected is True
        assert status.seller_name == "Test"
    
    def test_product_list_response(self):
        """Test ProductListResponse model."""
        from api.routes.tiktok_shop_v2 import ProductListResponse
        
        response = ProductListResponse(
            products=[{"id": "1", "title": "Product"}],
            total=1
        )
        assert response.total == 1
    
    def test_sync_result_model(self):
        """Test SyncResult model."""
        from api.routes.tiktok_shop_v2 import SyncResult
        
        result = SyncResult(
            success=True,
            products_synced=10,
            duration_seconds=5.5
        )
        assert result.success is True
        assert result.products_synced == 10


# ==================== TOKEN EXCHANGE TESTS ====================

class TestTokenExchange:
    """Test token exchange endpoint."""
    
    @pytest.mark.asyncio
    async def test_exchange_token_success(self, mock_user, mock_redis, mock_tiktok_service):
        """Test successful token exchange."""
        from api.routes.tiktok_shop_v2 import (TokenExchangeInput,
                                               exchange_token)
        from integrations.tiktok_shop_service import TikTokShopToken
        
        now = datetime.now(timezone.utc)
        mock_token = TikTokShopToken(
            access_token="new_token",
            refresh_token="new_refresh",
            access_token_expires_at=now + timedelta(hours=4),
            refresh_token_expires_at=now + timedelta(days=7),
            open_id="open123",
            seller_name="Test Seller",
            seller_base_region="US",
            user_type=1
        )
        mock_tiktok_service.exchange_code = AsyncMock(return_value=mock_token)
        
        with patch('api.routes.tiktok_shop_v2.TikTokShopService',
                   return_value=mock_tiktok_service), \
             patch('api.routes.tiktok_shop_v2.save_user_credentials', new_callable=AsyncMock), \
             patch('api.routes.tiktok_shop_v2.save_user_token', new_callable=AsyncMock):
            
            result = await exchange_token(
                TokenExchangeInput(
                    app_key="test_key",
                    app_secret="test_secret_long",
                    code="auth_code"
                ),
                mock_user,
                mock_redis
            )
            
            assert result["success"] is True
            assert result["seller_name"] == "Test Seller"
    
    @pytest.mark.asyncio
    async def test_exchange_token_error(self, mock_user, mock_redis, mock_tiktok_service):
        """Test token exchange with error."""
        from api.routes.tiktok_shop_v2 import (TokenExchangeInput,
                                               exchange_token)
        from integrations.tiktok_shop_service import TikTokShopError
        
        mock_tiktok_service.exchange_code = AsyncMock(
            side_effect=TikTokShopError(400, "Invalid code", "req123")
        )
        
        with patch('api.routes.tiktok_shop_v2.TikTokShopService',
                   return_value=mock_tiktok_service), \
             patch('api.routes.tiktok_shop_v2.save_user_credentials', new_callable=AsyncMock):
            
            with pytest.raises(HTTPException) as exc_info:
                await exchange_token(
                    TokenExchangeInput(
                        app_key="test_key",
                        app_secret="test_secret_long",
                        code="invalid_code"
                    ),
                    mock_user,
                    mock_redis
                )
            
            assert exc_info.value.status_code == 400


# ==================== ROUTER TESTS ====================

class TestRouter:
    """Test router configuration."""
    
    def test_router_exists(self):
        """Test router is properly configured."""
        from api.routes.tiktok_shop_v2 import router
        
        assert router is not None
        assert router.tags == ["TikTok Shop V2"]
