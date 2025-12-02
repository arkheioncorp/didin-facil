"""
Comprehensive tests for TikTok Shop routes
Target: api/routes/tiktok_shop.py (currently 34.8% coverage)
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestTikTokShopClient:
    """Test TikTokShopClient class"""
    
    def test_generate_sign_basic(self):
        """Test signature generation"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.app_key = "test_key"
            client.app_secret = "test_secret"
            
            sign = client.generate_sign(
                path="/api/products/search",
                params={"a": "1", "b": "2"},
                timestamp=1234567890
            )
            
            assert isinstance(sign, str)
            assert len(sign) == 64  # SHA256 hex length
    
    def test_generate_sign_orders_params(self):
        """Test that params are ordered alphabetically"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.app_key = "test_key"
            client.app_secret = "test_secret"
            
            # Same params in different order should produce same sign
            sign1 = client.generate_sign(
                path="/api/test",
                params={"z": "3", "a": "1", "m": "2"},
                timestamp=1000
            )
            sign2 = client.generate_sign(
                path="/api/test",
                params={"a": "1", "m": "2", "z": "3"},
                timestamp=1000
            )
            
            assert sign1 == sign2
    
    def test_get_auth_url_basic(self):
        """Test auth URL generation"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.app_key = "test_app_key"
            client.service_id = None
            client.AUTH_URL = "https://services.tiktokshop.com/open/authorize"
            
            url = client.get_auth_url(
                redirect_uri="https://example.com/callback",
                state="test_state"
            )
            
            assert "app_key=test_app_key" in url
            assert "redirect_uri" in url
            assert "state=test_state" in url
    
    def test_get_auth_url_with_service_id(self):
        """Test auth URL with service ID"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.app_key = "test_app_key"
            client.service_id = "test_service_id"
            client.AUTH_URL = "https://services.tiktokshop.com/open/authorize"
            
            url = client.get_auth_url(
                redirect_uri="https://example.com/callback",
                state="test_state"
            )
            
            assert "service_id=test_service_id" in url
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self):
        """Test token exchange success"""
        from api.routes.tiktok_shop import TikTokShopAuth, TikTokShopClient
        
        mock_response_data = {
            "code": 0,
            "data": {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "access_token_expire_in": 3600,
                "refresh_token_expire_in": 86400,
                "open_id": "test_open_id",
                "seller_name": "Test Seller"
            }
        }
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.app_key = "test_key"
            client.app_secret = "test_secret"
            client.TOKEN_URL = "https://test.com/token"
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_instance = AsyncMock()
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_instance.get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value = mock_instance
                
                result = await client.exchange_code_for_token("test_code")
                
                assert isinstance(result, TikTokShopAuth)
                assert result.access_token == "test_access_token"
                assert result.refresh_token == "test_refresh_token"
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_error(self):
        """Test token exchange error handling"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        mock_response_data = {
            "code": 1001,
            "message": "Invalid authorization code"
        }
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.app_key = "test_key"
            client.app_secret = "test_secret"
            client.TOKEN_URL = "https://test.com/token"
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_instance = AsyncMock()
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_instance.get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value = mock_instance
                
                with pytest.raises(HTTPException) as exc_info:
                    await client.exchange_code_for_token("invalid_code")
                
                assert exc_info.value.status_code == 400
                assert "Invalid authorization code" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test refresh token success"""
        from api.routes.tiktok_shop import TikTokShopAuth, TikTokShopClient
        
        mock_response_data = {
            "code": 0,
            "data": {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "access_token_expire_in": 3600,
                "refresh_token_expire_in": 86400,
                "open_id": "test_open_id"
            }
        }
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.app_key = "test_key"
            client.app_secret = "test_secret"
            client.REFRESH_URL = "https://test.com/refresh"
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_instance = AsyncMock()
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_instance.get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value = mock_instance
                
                result = await client.refresh_token("old_refresh_token")
                
                assert isinstance(result, TikTokShopAuth)
                assert result.access_token == "new_access_token"
    
    @pytest.mark.asyncio
    async def test_refresh_token_error(self):
        """Test refresh token error handling"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        mock_response_data = {
            "code": 1002,
            "message": "Token expired"
        }
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.app_key = "test_key"
            client.app_secret = "test_secret"
            client.REFRESH_URL = "https://test.com/refresh"
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_instance = AsyncMock()
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_instance.get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value = mock_instance
                
                with pytest.raises(HTTPException) as exc_info:
                    await client.refresh_token("expired_token")
                
                assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_api_request_get(self):
        """Test GET API request"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        mock_response_data = {"code": 0, "data": {"test": "value"}}
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.app_key = "test_key"
            client.app_secret = "test_secret"
            client.BASE_URL = "https://test.com"
            client.generate_sign = MagicMock(return_value="test_sign")
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_instance = AsyncMock()
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_instance.get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value = mock_instance
                
                result = await client.api_request(
                    method="GET",
                    path="/api/test",
                    access_token="test_token",
                    shop_id="shop123"
                )
                
                assert result == mock_response_data
    
    @pytest.mark.asyncio
    async def test_api_request_post(self):
        """Test POST API request"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        mock_response_data = {"code": 0, "data": {"products": []}}
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.app_key = "test_key"
            client.app_secret = "test_secret"
            client.BASE_URL = "https://test.com"
            client.generate_sign = MagicMock(return_value="test_sign")
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_instance = AsyncMock()
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_instance.request = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value = mock_instance
                
                result = await client.api_request(
                    method="POST",
                    path="/api/products/search",
                    access_token="test_token",
                    shop_id="shop123",
                    body={"page_size": 50}
                )
                
                assert result == mock_response_data
    
    @pytest.mark.asyncio
    async def test_get_products_success(self):
        """Test get products success"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        mock_products = [
            {"product_id": "1", "title": "Product 1"},
            {"product_id": "2", "title": "Product 2"}
        ]
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.api_request = AsyncMock(return_value={
                "code": 0,
                "data": {"products": mock_products}
            })
            
            result = await client.get_products(
                access_token="test_token",
                shop_id="shop123"
            )
            
            assert result == mock_products
    
    @pytest.mark.asyncio
    async def test_get_products_error(self):
        """Test get products error"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.api_request = AsyncMock(return_value={
                "code": 1000,
                "message": "Shop not found"
            })
            
            with pytest.raises(HTTPException) as exc_info:
                await client.get_products(
                    access_token="test_token",
                    shop_id="invalid_shop"
                )
            
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_product_detail_success(self):
        """Test get product detail success"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        mock_product = {"product_id": "1", "title": "Test Product", "price": 99.99}
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.api_request = AsyncMock(return_value={
                "code": 0,
                "data": mock_product
            })
            
            result = await client.get_product_detail(
                access_token="test_token",
                shop_id="shop123",
                product_id="product123"
            )
            
            assert result == mock_product
    
    @pytest.mark.asyncio
    async def test_get_product_detail_error(self):
        """Test get product detail error"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.api_request = AsyncMock(return_value={
                "code": 1001,
                "message": "Product not found"
            })
            
            with pytest.raises(HTTPException) as exc_info:
                await client.get_product_detail(
                    access_token="test_token",
                    shop_id="shop123",
                    product_id="nonexistent"
                )
            
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_shop_info_success(self):
        """Test get shop info success"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        mock_shop = {"shop_id": "shop123", "name": "Test Shop"}
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.api_request = AsyncMock(return_value={
                "code": 0,
                "data": mock_shop
            })
            
            result = await client.get_shop_info(
                access_token="test_token",
                shop_id="shop123"
            )
            
            assert result == mock_shop
    
    @pytest.mark.asyncio
    async def test_get_shop_info_error(self):
        """Test get shop info error"""
        from api.routes.tiktok_shop import TikTokShopClient
        
        with patch.object(TikTokShopClient, '__init__', lambda x: None):
            client = TikTokShopClient()
            client.api_request = AsyncMock(return_value={
                "code": 1003,
                "message": "Access denied"
            })
            
            with pytest.raises(HTTPException) as exc_info:
                await client.get_shop_info(
                    access_token="test_token",
                    shop_id="shop123"
                )
            
            assert exc_info.value.status_code == 400


class TestTikTokShopRoutes:
    """Test TikTok Shop route endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_auth_url_success(self):
        """Test get auth URL endpoint success"""
        from api.routes.tiktok_shop import get_auth_url
        
        mock_user = {"id": "user123", "email": "test@test.com"}
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        
        with patch('api.routes.tiktok_shop.TikTokShopClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_auth_url.return_value = "https://tiktok.com/auth?code=xxx"
            mock_client_class.return_value = mock_client
            
            with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
                result = await get_auth_url(current_user=mock_user)
                
                assert "auth_url" in result
                assert result["expires_in"] == 600
                mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_auth_url_not_configured(self):
        """Test get auth URL when API not configured"""
        from api.routes.tiktok_shop import get_auth_url
        
        mock_user = {"id": "user123"}
        
        with patch('api.routes.tiktok_shop.TikTokShopClient') as mock_client_class:
            mock_client_class.side_effect = ValueError("Not configured")
            
            with pytest.raises(HTTPException) as exc_info:
                await get_auth_url(current_user=mock_user)
            
            assert exc_info.value.status_code == 503
    
    @pytest.mark.asyncio
    async def test_oauth_callback_invalid_state(self):
        """Test OAuth callback with invalid state"""
        from api.routes.tiktok_shop import oauth_callback
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await oauth_callback(code="test_code", state="invalid_state")
            
            assert exc_info.value.status_code == 400
            assert "Estado inválido" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_oauth_callback_success(self):
        """Test OAuth callback success"""
        from api.routes.tiktok_shop import TikTokShopAuth, oauth_callback
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "user_id": "user123",
            "created_at": datetime.now(timezone.utc).isoformat()
        }))
        mock_redis.delete = AsyncMock()
        mock_redis.set = AsyncMock()
        
        mock_auth = TikTokShopAuth(
            access_token="access",
            refresh_token="refresh",
            access_token_expire_in=3600,
            refresh_token_expire_in=86400,
            open_id="open_id",
            seller_name="Test Seller"
        )
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            with patch('api.routes.tiktok_shop.TikTokShopClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.exchange_code_for_token = AsyncMock(return_value=mock_auth)
                mock_client_class.return_value = mock_client
                
                result = await oauth_callback(code="valid_code", state="valid_state")
                
                assert result["success"] is True
                assert result["seller_name"] == "Test Seller"
    
    @pytest.mark.asyncio
    async def test_oauth_callback_api_not_configured(self):
        """Test OAuth callback when API not configured"""
        from api.routes.tiktok_shop import oauth_callback
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "user_id": "user123",
            "created_at": datetime.now(timezone.utc).isoformat()
        }))
        mock_redis.delete = AsyncMock()
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            with patch('api.routes.tiktok_shop.TikTokShopClient') as mock_client_class:
                mock_client_class.side_effect = ValueError("Not configured")
                
                with pytest.raises(HTTPException) as exc_info:
                    await oauth_callback(code="test_code", state="valid_state")
                
                assert exc_info.value.status_code == 503
    
    @pytest.mark.asyncio
    async def test_get_connection_status_not_connected(self):
        """Test connection status when not connected"""
        from api.routes.tiktok_shop import get_connection_status
        
        mock_user = {"id": "user123"}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            result = await get_connection_status(current_user=mock_user)
            
            assert result["connected"] is False
    
    @pytest.mark.asyncio
    async def test_get_connection_status_connected(self):
        """Test connection status when connected"""
        from api.routes.tiktok_shop import get_connection_status
        
        mock_user = {"id": "user123"}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "seller_name": "Test Seller",
            "open_id": "open123",
            "connected_at": "2024-01-01T00:00:00Z"
        }))
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            result = await get_connection_status(current_user=mock_user)
            
            assert result["connected"] is True
            assert result["seller_name"] == "Test Seller"
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnect endpoint"""
        from api.routes.tiktok_shop import disconnect
        
        mock_user = {"id": "user123"}
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            result = await disconnect(current_user=mock_user)
            
            assert "desconectado" in result["message"]
            mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_products_not_connected(self):
        """Test get products when not connected"""
        from api.routes.tiktok_shop import get_products
        
        mock_user = {"id": "user123"}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await get_products(
                    shop_id="shop123",
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_products_success(self):
        """Test get products success"""
        from api.routes.tiktok_shop import get_products
        
        mock_user = {"id": "user123"}
        mock_products = [{"product_id": "1", "title": "Test"}]
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "access_token": "token123"
        }))
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            with patch('api.routes.tiktok_shop.TikTokShopClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_products = AsyncMock(return_value=mock_products)
                mock_client_class.return_value = mock_client
                
                result = await get_products(
                    shop_id="shop123",
                    current_user=mock_user
                )
                
                assert result["products"] == mock_products
    
    @pytest.mark.asyncio
    async def test_get_products_api_error(self):
        """Test get products with API error"""
        from api.routes.tiktok_shop import get_products
        
        mock_user = {"id": "user123"}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "access_token": "token123"
        }))
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            with patch('api.routes.tiktok_shop.TikTokShopClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_products = AsyncMock(side_effect=Exception("API Error"))
                mock_client_class.return_value = mock_client
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_products(
                        shop_id="shop123",
                        current_user=mock_user
                    )
                
                assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_get_product_detail_not_connected(self):
        """Test get product detail when not connected"""
        from api.routes.tiktok_shop import get_product_detail
        
        mock_user = {"id": "user123"}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await get_product_detail(
                    product_id="product123",
                    shop_id="shop123",
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_product_detail_success(self):
        """Test get product detail success"""
        from api.routes.tiktok_shop import get_product_detail
        
        mock_user = {"id": "user123"}
        mock_product = {"product_id": "1", "title": "Test", "price": 99.99}
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "access_token": "token123"
        }))
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            with patch('api.routes.tiktok_shop.TikTokShopClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_product_detail = AsyncMock(return_value=mock_product)
                mock_client_class.return_value = mock_client
                
                result = await get_product_detail(
                    product_id="product123",
                    shop_id="shop123",
                    current_user=mock_user
                )
                
                assert result == mock_product
    
    @pytest.mark.asyncio
    async def test_get_product_detail_api_error(self):
        """Test get product detail with API error"""
        from api.routes.tiktok_shop import get_product_detail
        
        mock_user = {"id": "user123"}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "access_token": "token123"
        }))
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            with patch('api.routes.tiktok_shop.TikTokShopClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_product_detail = AsyncMock(side_effect=Exception("Not found"))
                mock_client_class.return_value = mock_client
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_product_detail(
                        product_id="invalid",
                        shop_id="shop123",
                        current_user=mock_user
                    )
                
                assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_get_shop_info_not_connected(self):
        """Test get shop info when not connected"""
        from api.routes.tiktok_shop import get_shop_info
        
        mock_user = {"id": "user123"}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await get_shop_info(
                    shop_id="shop123",
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_shop_info_success(self):
        """Test get shop info success"""
        from api.routes.tiktok_shop import get_shop_info
        
        mock_user = {"id": "user123"}
        mock_shop = {"shop_id": "shop123", "name": "My Shop"}
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "access_token": "token123"
        }))
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            with patch('api.routes.tiktok_shop.TikTokShopClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_shop_info = AsyncMock(return_value=mock_shop)
                mock_client_class.return_value = mock_client
                
                result = await get_shop_info(
                    shop_id="shop123",
                    current_user=mock_user
                )
                
                assert result == mock_shop
    
    @pytest.mark.asyncio
    async def test_get_shop_info_api_error(self):
        """Test get shop info with API error"""
        from api.routes.tiktok_shop import get_shop_info
        
        mock_user = {"id": "user123"}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "access_token": "token123"
        }))
        
        with patch('api.routes.tiktok_shop.get_redis', return_value=mock_redis):
            with patch('api.routes.tiktok_shop.TikTokShopClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_shop_info = AsyncMock(side_effect=Exception("Error"))
                mock_client_class.return_value = mock_client
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_shop_info(
                        shop_id="shop123",
                        current_user=mock_user
                    )
                
                assert exc_info.value.status_code == 500


class TestTikTokShopSchemas:
    """Test TikTok Shop Pydantic schemas"""
    
    def test_tiktok_shop_auth_schema(self):
        """Test TikTokShopAuth schema"""
        from api.routes.tiktok_shop import TikTokShopAuth
        
        auth = TikTokShopAuth(
            access_token="token",
            refresh_token="refresh",
            access_token_expire_in=3600,
            refresh_token_expire_in=86400,
            open_id="open_id"
        )
        
        assert auth.access_token == "token"
        assert auth.seller_name is None
    
    def test_tiktok_shop_auth_with_seller(self):
        """Test TikTokShopAuth with seller name"""
        from api.routes.tiktok_shop import TikTokShopAuth
        
        auth = TikTokShopAuth(
            access_token="token",
            refresh_token="refresh",
            access_token_expire_in=3600,
            refresh_token_expire_in=86400,
            open_id="open_id",
            seller_name="Test Seller"
        )
        
        assert auth.seller_name == "Test Seller"
    
    def test_tiktok_shop_product_schema(self):
        """Test TikTokShopProduct schema"""
        from api.routes.tiktok_shop import TikTokShopProduct
        
        product = TikTokShopProduct(
            product_id="123",
            title="Test Product",
            price=99.99
        )
        
        assert product.product_id == "123"
        assert product.currency == "BRL"
        assert product.stock_quantity == 0
        assert product.images == []
    
    def test_tiktok_shop_product_full(self):
        """Test TikTokShopProduct with all fields"""
        from api.routes.tiktok_shop import TikTokShopProduct
        
        product = TikTokShopProduct(
            product_id="123",
            title="Test Product",
            description="Description",
            price=99.99,
            original_price=149.99,
            currency="USD",
            stock_quantity=100,
            images=["img1.jpg", "img2.jpg"],
            category_id="cat123",
            status="draft"
        )
        
        assert product.description == "Description"
        assert product.original_price == 149.99
        assert len(product.images) == 2
    
    def test_tiktok_shop_config_schema(self):
        """Test TikTokShopConfig schema"""
        from api.routes.tiktok_shop import TikTokShopConfig
        
        config = TikTokShopConfig()
        
        assert config.shop_id is None
        assert config.categories == []
        assert config.max_products == 100
    
    def test_tiktok_shop_config_with_values(self):
        """Test TikTokShopConfig with values"""
        from api.routes.tiktok_shop import TikTokShopConfig
        
        config = TikTokShopConfig(
            shop_id="shop123",
            categories=["electronics", "fashion"],
            max_products=500
        )
        
        assert config.shop_id == "shop123"
        assert len(config.categories) == 2
        assert config.max_products == 500
        assert config.max_products == 500
