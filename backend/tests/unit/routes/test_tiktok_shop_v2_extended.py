"""
Testes extensivos para api/routes/tiktok_shop_v2.py
Foco nas linhas não cobertas: 132-145, 158, 173-189, 332-334, 348-350, 373-401, 418, 477-509, 574-686, 697-714, 731-766
"""
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ==================== TESTES DE SCHEMAS ====================

class TestTikTokShopV2Schemas:
    """Testes para schemas do TikTok Shop V2."""
    
    def test_credentials_input_schema(self):
        """Test CredentialsInput schema."""
        from api.routes.tiktok_shop_v2 import CredentialsInput
        
        creds = CredentialsInput(
            app_key="test_app_key",
            app_secret="test_app_secret_long",
            service_id="service123"
        )
        assert creds.app_key == "test_app_key"
        assert creds.app_secret == "test_app_secret_long"
        assert creds.service_id == "service123"
    
    def test_credentials_input_validation(self):
        """Test CredentialsInput validation."""
        from api.routes.tiktok_shop_v2 import CredentialsInput
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            CredentialsInput(app_key="abc", app_secret="short")
    
    def test_auth_callback_input(self):
        """Test AuthCallbackInput schema."""
        from api.routes.tiktok_shop_v2 import AuthCallbackInput
        
        callback = AuthCallbackInput(
            code="auth_code_123",
            state="user123:random_state"
        )
        assert callback.code == "auth_code_123"
        assert callback.state == "user123:random_state"
    
    def test_connection_status_schema(self):
        """Test ConnectionStatus schema."""
        from api.routes.tiktok_shop_v2 import ConnectionStatus
        
        status = ConnectionStatus(
            connected=True,
            seller_name="Test Seller",
            seller_region="BR",
            shops=[{"id": "shop1"}],
            product_count=100
        )
        assert status.connected is True
        assert status.seller_name == "Test Seller"
        assert status.product_count == 100
    
    def test_product_list_response(self):
        """Test ProductListResponse schema."""
        from api.routes.tiktok_shop_v2 import ProductListResponse
        
        response = ProductListResponse(
            products=[{"id": "1", "title": "Product"}],
            total=1,
            next_page_token="token123"
        )
        assert len(response.products) == 1
        assert response.total == 1
    
    def test_sync_result_schema(self):
        """Test SyncResult schema."""
        from api.routes.tiktok_shop_v2 import SyncResult
        
        result = SyncResult(
            success=True,
            products_synced=50,
            errors=["error1"],
            duration_seconds=10.5
        )
        assert result.success is True
        assert result.products_synced == 50
    
    def test_token_exchange_input(self):
        """Test TokenExchangeInput schema."""
        from api.routes.tiktok_shop_v2 import TokenExchangeInput
        
        token_input = TokenExchangeInput(
            app_key="key123",
            app_secret="secret123",
            code="auth_code"
        )
        assert token_input.app_key == "key123"


# ==================== TESTES DE HELPERS ====================

class TestTikTokShopV2Helpers:
    """Testes para funções helper."""
    
    def test_get_redis_key(self):
        """Test get_redis_key helper."""
        from api.routes.tiktok_shop_v2 import get_redis_key
        
        key = get_redis_key("user123", "credentials")
        assert key == "tiktok_shop:user123:credentials"
    
    @pytest.mark.asyncio
    async def test_get_user_credentials_exists(self):
        """Test get_user_credentials when credentials exist."""
        from api.routes.tiktok_shop_v2 import get_user_credentials
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps({
            "app_key": "key123",
            "app_secret": "secret123"
        })
        
        creds = await get_user_credentials("user123", mock_redis)
        assert creds is not None
        assert creds.app_key == "key123"
    
    @pytest.mark.asyncio
    async def test_get_user_credentials_not_exists(self):
        """Test get_user_credentials when credentials don't exist."""
        from api.routes.tiktok_shop_v2 import get_user_credentials
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        creds = await get_user_credentials("user123", mock_redis)
        assert creds is None
    
    @pytest.mark.asyncio
    async def test_save_user_credentials(self):
        """Test save_user_credentials."""
        from api.routes.tiktok_shop_v2 import (CredentialsInput,
                                               save_user_credentials)
        
        mock_redis = AsyncMock()
        creds = CredentialsInput(
            app_key="key12345",
            app_secret="secret12345"
        )
        
        await save_user_credentials("user123", creds, mock_redis)
        
        assert mock_redis.set.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_user_token_exists(self):
        """Test get_user_token when token exists."""
        from api.routes.tiktok_shop_v2 import get_user_token
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps({
            "access_token": "access123",
            "refresh_token": "refresh123",
            "access_token_expires_at": datetime.now(timezone.utc).isoformat(),
            "refresh_token_expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "open_id": "open123",
            "seller_name": "Test Seller",
            "seller_base_region": "BR",
            "user_type": 1
        })
        
        token = await get_user_token("user123", mock_redis)
        assert token is not None
        assert token.access_token == "access123"
    
    @pytest.mark.asyncio
    async def test_get_user_token_not_exists(self):
        """Test get_user_token when token doesn't exist."""
        from api.routes.tiktok_shop_v2 import get_user_token
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        token = await get_user_token("user123", mock_redis)
        assert token is None
    
    @pytest.mark.asyncio
    async def test_save_user_token(self):
        """Test save_user_token."""
        from api.routes.tiktok_shop_v2 import save_user_token
        from integrations.tiktok_shop_service import TikTokShopToken
        
        mock_redis = AsyncMock()
        token = TikTokShopToken(
            access_token="access123",
            refresh_token="refresh123",
            access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            refresh_token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            open_id="open123",
            seller_name="Test",
            seller_base_region="BR",
            user_type=1
        )
        
        await save_user_token("user123", token, mock_redis)
        mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_service_for_user_no_credentials(self):
        """Test get_service_for_user without credentials."""
        from api.routes.tiktok_shop_v2 import get_service_for_user
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            await get_service_for_user("user123", mock_redis)
        
        assert exc.value.status_code == 400
        assert "não configurado" in exc.value.detail
    
    @pytest.mark.asyncio
    async def test_ensure_valid_token_no_token(self):
        """Test ensure_valid_token without token."""
        from api.routes.tiktok_shop_v2 import ensure_valid_token
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            await ensure_valid_token("user123", mock_redis)
        
        assert exc.value.status_code == 401
        assert "Não conectado" in exc.value.detail


# ==================== TESTES DE ENDPOINTS ====================

class TestCredentialsEndpoints:
    """Testes para endpoints de credenciais."""
    
    @pytest.mark.asyncio
    async def test_set_credentials_success(self):
        """Test setting credentials successfully."""
        from api.routes.tiktok_shop_v2 import CredentialsInput, set_credentials
        
        mock_redis = AsyncMock()
        mock_user = {"id": 123}
        creds = CredentialsInput(
            app_key="key12345",
            app_secret="secret12345"
        )
        
        result = await set_credentials(creds, mock_user, mock_redis)
        
        assert result["success"] is True
        assert "salvas" in result["message"]
    
    @pytest.mark.asyncio
    async def test_check_credentials_configured(self):
        """Test checking configured credentials."""
        from api.routes.tiktok_shop_v2 import check_credentials
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps({
            "app_key": "key12345678",
            "app_secret": "secret123"
        })
        mock_user = {"id": 123}
        
        result = await check_credentials(mock_user, mock_redis)
        
        assert result["configured"] is True
        assert result["app_key"].endswith("...")
    
    @pytest.mark.asyncio
    async def test_check_credentials_not_configured(self):
        """Test checking unconfigured credentials."""
        from api.routes.tiktok_shop_v2 import check_credentials
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_user = {"id": 123}
        
        result = await check_credentials(mock_user, mock_redis)
        
        assert result["configured"] is False
        assert result["app_key"] is None
    
    @pytest.mark.asyncio
    async def test_delete_credentials(self):
        """Test deleting credentials."""
        from api.routes.tiktok_shop_v2 import delete_credentials
        
        mock_redis = AsyncMock()
        mock_user = {"id": 123}
        
        result = await delete_credentials(mock_user, mock_redis)
        
        assert result["success"] is True
        assert mock_redis.delete.call_count == 3


class TestOAuthEndpoints:
    """Testes para endpoints OAuth."""
    
    @pytest.mark.asyncio
    async def test_get_auth_url_no_credentials(self):
        """Test get auth URL without credentials."""
        from api.routes.tiktok_shop_v2 import get_auth_url
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_user = {"id": 123}
        
        with pytest.raises(HTTPException) as exc:
            await get_auth_url(mock_user, mock_redis)
        
        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_auth_url_success(self):
        """Test get auth URL successfully."""
        from api.routes.tiktok_shop_v2 import get_auth_url
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps({
            "app_key": "key12345",
            "app_secret": "secret12345"
        })
        mock_user = {"id": 123}
        
        with patch('api.routes.tiktok_shop_v2.TikTokShopService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_auth_url.return_value = "https://auth.tiktok.com/..."
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service
            
            result = await get_auth_url(mock_user, mock_redis)
            
            assert "auth_url" in result
            assert "state" in result
    
    @pytest.mark.asyncio
    async def test_exchange_token_success(self):
        """Test token exchange success."""
        from api.routes.tiktok_shop_v2 import (TokenExchangeInput,
                                               exchange_token)
        from integrations.tiktok_shop_service import TikTokShopToken
        
        mock_redis = AsyncMock()
        mock_user = {"id": 123}
        # app_secret precisa ter pelo menos 10 caracteres
        data = TokenExchangeInput(
            app_key="key123456789",
            app_secret="secret1234567890",
            code="auth_code_123"
        )
        
        mock_token = TikTokShopToken(
            access_token="access123",
            refresh_token="refresh123",
            access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            refresh_token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            open_id="open123",
            seller_name="Test Seller",
            seller_base_region="BR",
            user_type=1
        )
        
        with patch('api.routes.tiktok_shop_v2.TikTokShopService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.exchange_code.return_value = mock_token
            mock_service.get_active_shops.return_value = []
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service
            
            result = await exchange_token(data, mock_user, mock_redis)
            
            assert result["success"] is True
            assert result["seller_name"] == "Test Seller"
    
    @pytest.mark.asyncio
    async def test_exchange_token_error(self):
        """Test token exchange with error."""
        from api.routes.tiktok_shop_v2 import (TokenExchangeInput,
                                               exchange_token)
        from integrations.tiktok_shop_service import TikTokShopError
        
        mock_redis = AsyncMock()
        mock_user = {"id": 123}
        # app_secret precisa ter pelo menos 10 caracteres
        data = TokenExchangeInput(
            app_key="key123456789",
            app_secret="secret1234567890",
            code="invalid_code"
        )
        
        with patch('api.routes.tiktok_shop_v2.TikTokShopService') as mock_service_class:
            mock_service = AsyncMock()
            # TikTokShopError requer (code: int, message: str, request_id: str)
            mock_service.exchange_code.side_effect = TikTokShopError(
                400, "Invalid code", "req123"
            )
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service
            
            with pytest.raises(HTTPException) as exc:
                await exchange_token(data, mock_user, mock_redis)
            
            assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_oauth_callback_invalid_state(self):
        """Test OAuth callback with invalid state."""
        from api.routes.tiktok_shop_v2 import AuthCallbackInput, oauth_callback
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_user = {"id": 123}
        callback = AuthCallbackInput(code="code123", state="invalid_state")
        
        with pytest.raises(HTTPException) as exc:
            await oauth_callback(callback, mock_user, mock_redis)
        
        assert exc.value.status_code == 400
        assert "State inválido" in exc.value.detail


class TestConnectionStatusEndpoints:
    """Testes para endpoints de status de conexão."""
    
    @pytest.mark.asyncio
    async def test_get_connection_status_not_connected(self):
        """Test connection status when not connected."""
        from api.routes.tiktok_shop_v2 import get_connection_status
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_user = {"id": 123}
        
        result = await get_connection_status(mock_user, mock_redis)
        
        assert result.connected is False
    
    @pytest.mark.asyncio
    async def test_get_connection_status_connected(self):
        """Test connection status when connected."""
        from api.routes.tiktok_shop_v2 import get_connection_status
        
        mock_redis = AsyncMock()
        
        def mock_get(key):
            if "credentials" in key:
                return json.dumps({"app_key": "key", "app_secret": "secret"})
            elif "token" in key:
                return json.dumps({
                    "access_token": "access",
                    "refresh_token": "refresh",
                    "access_token_expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                    "refresh_token_expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                    "open_id": "open",
                    "seller_name": "Seller",
                    "seller_base_region": "BR",
                    "user_type": 1
                })
            elif "shops" in key:
                return json.dumps([{"shop_id": "shop1"}])
            elif "product_count" in key:
                return "100"
            elif "last_sync" in key:
                return datetime.now(timezone.utc).isoformat()
            return None
        
        mock_redis.get = AsyncMock(side_effect=mock_get)
        mock_user = {"id": 123}
        
        result = await get_connection_status(mock_user, mock_redis)
        
        assert result.connected is True
        assert result.seller_name == "Seller"
        assert result.product_count == 100
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnect endpoint."""
        from api.routes.tiktok_shop_v2 import disconnect
        
        mock_redis = AsyncMock()
        mock_user = {"id": 123}
        
        result = await disconnect(mock_user, mock_redis)
        
        assert result["success"] is True
        assert mock_redis.delete.call_count == 2


class TestProductsEndpoints:
    """Testes para endpoints de produtos."""
    
    @pytest.mark.asyncio
    async def test_list_products_success(self):
        """Test listing products successfully."""
        from api.routes.tiktok_shop_v2 import list_products
        
        mock_redis = AsyncMock()
        
        def mock_get(key):
            if "token" in key:
                return json.dumps({
                    "access_token": "access",
                    "refresh_token": "refresh",
                    "access_token_expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                    "refresh_token_expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                    "open_id": "open",
                    "seller_name": "Seller",
                    "seller_base_region": "BR",
                    "user_type": 1
                })
            elif "credentials" in key:
                return json.dumps({"app_key": "key", "app_secret": "secret"})
            return None
        
        mock_redis.get = AsyncMock(side_effect=mock_get)
        mock_user = {"id": 123}
        
        mock_product = MagicMock()
        mock_product.model_dump.return_value = {"id": "prod1", "title": "Test Product"}
        
        with patch('api.routes.tiktok_shop_v2.TikTokShopService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.search_products.return_value = ([mock_product], None)
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service
            
            result = await list_products(
                page_size=20,
                page_token=None,
                status=None,
                shop_id=None,
                current_user=mock_user,
                redis=mock_redis
            )
            
            assert len(result.products) == 1
            assert result.total == 1
    
    @pytest.mark.asyncio
    async def test_sync_products_already_running(self):
        """Test sync products when already running."""
        from api.routes.tiktok_shop_v2 import sync_products
        from fastapi import BackgroundTasks
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "1"  # sync running
        mock_user = {"id": 123}
        
        result = await sync_products(
            background_tasks=BackgroundTasks(),
            shop_id=None,
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result["success"] is False
        assert "em andamento" in result["message"]
    
    @pytest.mark.asyncio
    async def test_sync_products_start(self):
        """Test starting sync products."""
        from api.routes.tiktok_shop_v2 import sync_products
        from fastapi import BackgroundTasks
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # no sync running
        mock_user = {"id": 123}
        mock_bg = MagicMock()
        
        result = await sync_products(
            background_tasks=mock_bg,
            shop_id=None,
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result["success"] is True
        mock_bg.add_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_sync_status(self):
        """Test get sync status."""
        from api.routes.tiktok_shop_v2 import get_sync_status
        
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = [
            None,  # not running
            json.dumps({"success": True, "products_synced": 50})
        ]
        mock_user = {"id": 123}
        
        result = await get_sync_status(mock_user, mock_redis)
        
        assert result["running"] is False
        assert result["last_result"]["success"] is True


class TestShopsEndpoints:
    """Testes para endpoints de lojas."""
    
    @pytest.mark.asyncio
    async def test_list_shops_success(self):
        """Test listing shops successfully."""
        from api.routes.tiktok_shop_v2 import list_shops
        
        mock_redis = AsyncMock()
        
        def mock_get(key):
            if "token" in key:
                return json.dumps({
                    "access_token": "access",
                    "refresh_token": "refresh",
                    "access_token_expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                    "refresh_token_expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                    "open_id": "open",
                    "seller_name": "Seller",
                    "seller_base_region": "BR",
                    "user_type": 1
                })
            elif "credentials" in key:
                return json.dumps({"app_key": "key", "app_secret": "secret"})
            return None
        
        mock_redis.get = AsyncMock(side_effect=mock_get)
        mock_user = {"id": 123}
        
        mock_shop = MagicMock()
        mock_shop.model_dump.return_value = {"shop_id": "shop1", "name": "Test Shop"}
        
        with patch('api.routes.tiktok_shop_v2.TikTokShopService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_active_shops.return_value = [mock_shop]
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service
            
            result = await list_shops(mock_user, mock_redis)
            
            assert len(result["shops"]) == 1


class TestWebhookEndpoint:
    """Testes para endpoint de webhook."""
    
    @pytest.mark.asyncio
    async def test_webhook_missing_signature(self):
        """Test webhook with missing signature."""
        from api.routes.tiktok_shop_v2 import tiktok_webhook
        
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_redis = AsyncMock()
        
        with pytest.raises(HTTPException) as exc:
            await tiktok_webhook(
                request=mock_request,
                app_key="key123",
                background_tasks=None,
                redis=mock_redis
            )
        
        assert exc.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_webhook_unknown_app_key(self):
        """Test webhook with unknown app key."""
        from api.routes.tiktok_shop_v2 import tiktok_webhook
        
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "signature123"
        mock_request.body = AsyncMock(return_value=b'{}')
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            await tiktok_webhook(
                request=mock_request,
                app_key="unknown_key",
                background_tasks=None,
                redis=mock_redis
            )
        
        assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_webhook_invalid_signature(self):
        """Test webhook with invalid signature."""
        from api.routes.tiktok_shop_v2 import tiktok_webhook
        
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "invalid_signature"
        mock_request.body = AsyncMock(return_value=b'{}')
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "secret123"
        
        with patch('api.routes.tiktok_shop_v2.create_tiktok_shop_service') as mock_create:
            mock_service = MagicMock()
            mock_service.verify_webhook_signature.return_value = False
            mock_create.return_value = mock_service
            
            with pytest.raises(HTTPException) as exc:
                await tiktok_webhook(
                    request=mock_request,
                    app_key="key123",
                    background_tasks=None,
                    redis=mock_redis
                )
            
            assert exc.value.status_code == 401


class TestBackgroundSync:
    """Testes para sincronização em background."""
    
    @pytest.mark.asyncio
    async def test_run_product_sync_imports(self):
        """Test run_product_sync function exists and signature is correct."""
        import inspect

        from api.routes.tiktok_shop_v2 import run_product_sync

        # Verifica que a função existe e tem a assinatura correta
        sig = inspect.signature(run_product_sync)
        params = list(sig.parameters.keys())
        
        assert "user_id" in params
        assert "shop_id" in params
        assert "redis" in params


class TestRouterConfiguration:
    """Testes para configuração do router."""
    
    def test_router_exists(self):
        """Test that router exists."""
        from api.routes.tiktok_shop_v2 import router
        assert router is not None
    
    def test_router_has_routes(self):
        """Test that router has routes."""
        from api.routes.tiktok_shop_v2 import router
        routes = [r.path for r in router.routes if hasattr(r, 'path')]
        
        assert "/credentials" in routes
        assert "/auth/url" in routes
        assert "/products" in routes
        assert "/status" in routes
