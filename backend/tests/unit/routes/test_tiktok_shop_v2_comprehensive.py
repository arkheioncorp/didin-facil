"""
Testes abrangentes para TikTok Shop V2 API Routes.

Cobertura completa das funcionalidades:
- Configuração de credenciais
- OAuth flow
- Listagem de produtos
- Sincronização
- Gerenciamento de lojas
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.routes.tiktok_shop_v2 import (
    AuthCallbackInput,
    ConnectionStatus,
    CredentialsInput,
    ProductListResponse,
    SyncResult,
    ensure_valid_token,
    get_redis_key,
    get_service_for_user,
    get_user_credentials,
    get_user_token,
    router,
    run_product_sync,
    save_user_credentials,
    save_user_token,
)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_redis():
    """Mock do Redis para testes."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_user():
    """Usuário mock para testes."""
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def mock_credentials():
    """Credenciais mock."""
    return CredentialsInput(
        app_key="test_app_key_12345",
        app_secret="test_app_secret_67890",
        service_id="service_123"
    )


@pytest.fixture
def mock_token_data():
    """Token data mock."""
    now = datetime.utcnow()
    return {
        "access_token": "acc_token_xyz",
        "refresh_token": "ref_token_abc",
        "access_token_expires_at": (now + timedelta(hours=4)).isoformat(),
        "refresh_token_expires_at": (now + timedelta(days=30)).isoformat(),
        "open_id": "open_id_123",
        "seller_name": "Test Seller",
        "seller_base_region": "BR",
        "user_type": 1
    }


@pytest.fixture
def mock_tiktok_token():
    """TikTokShopToken mock."""
    from integrations.tiktok_shop_service import TikTokShopToken
    now = datetime.utcnow()
    return TikTokShopToken(
        access_token="acc_token_xyz",
        refresh_token="ref_token_abc",
        access_token_expires_at=now + timedelta(hours=4),
        refresh_token_expires_at=now + timedelta(days=30),
        open_id="open_id_123",
        seller_name="Test Seller",
        seller_base_region="BR",
        user_type=1
    )


@pytest.fixture
def mock_shop_info():
    """ShopInfo mock."""
    from integrations.tiktok_shop_service import ShopInfo
    return ShopInfo(
        shop_id="shop_123",
        shop_name="Test Shop",
        region="BR",
        shop_cipher="cipher_abc",
        code="TST"
    )


@pytest.fixture
def mock_product():
    """TikTokShopProduct mock."""
    from integrations.tiktok_shop_service import (
        ProductStatus,
        TikTokShopProduct,
    )
    return TikTokShopProduct(
        id="prod_123",
        title="Test Product",
        status=ProductStatus.ACTIVATE,
        create_time=int(datetime.utcnow().timestamp()),
        update_time=int(datetime.utcnow().timestamp()),
        skus=[],
        sales_regions=["BR"],
        listing_quality_tier="GOOD"
    )


# ==================== TESTES DE HELPERS ====================

class TestHelpers:
    """Testes para funções auxiliares."""

    def test_get_redis_key(self):
        """Testa geração de chave Redis."""
        key = get_redis_key("user-123", "credentials")
        assert key == "tiktok_shop:user-123:credentials"
        
        key = get_redis_key("user-456", "token")
        assert key == "tiktok_shop:user-456:token"

    async def test_get_user_credentials_not_found(self, mock_redis):
        """Testa busca de credenciais inexistentes."""
        mock_redis.get.return_value = None
        
        result = await get_user_credentials("user-123", mock_redis)
        
        assert result is None
        mock_redis.get.assert_called_once_with("tiktok_shop:user-123:credentials")

    async def test_get_user_credentials_found(self, mock_redis):
        """Testa busca de credenciais existentes."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        mock_redis.get.return_value = json.dumps(creds_data)
        
        result = await get_user_credentials("user-123", mock_redis)
        
        assert result is not None
        assert result.app_key == "test_key"
        assert result.app_secret == "test_secret"

    async def test_save_user_credentials(self, mock_redis, mock_credentials):
        """Testa salvamento de credenciais."""
        await save_user_credentials("user-123", mock_credentials, mock_redis)
        
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "tiktok_shop:user-123:credentials"
        saved_data = json.loads(call_args[0][1])
        assert saved_data["app_key"] == mock_credentials.app_key

    async def test_get_user_token_not_found(self, mock_redis):
        """Testa busca de token inexistente."""
        mock_redis.get.return_value = None
        
        result = await get_user_token("user-123", mock_redis)
        
        assert result is None

    async def test_get_user_token_found(self, mock_redis, mock_token_data):
        """Testa busca de token existente."""
        mock_redis.get.return_value = json.dumps(mock_token_data)
        
        result = await get_user_token("user-123", mock_redis)
        
        assert result is not None
        assert result.access_token == "acc_token_xyz"
        assert result.seller_name == "Test Seller"

    async def test_save_user_token(self, mock_redis, mock_tiktok_token):
        """Testa salvamento de token."""
        await save_user_token("user-123", mock_tiktok_token, mock_redis)
        
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "tiktok_shop:user-123:token"
        
    async def test_get_service_for_user_no_credentials(self, mock_redis):
        """Testa criação de serviço sem credenciais."""
        mock_redis.get.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            await get_service_for_user("user-123", mock_redis)
        
        assert exc.value.status_code == 400
        assert "não configurado" in exc.value.detail

    async def test_get_service_for_user_with_credentials(self, mock_redis):
        """Testa criação de serviço com credenciais."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        mock_redis.get.return_value = json.dumps(creds_data)
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service:
            service = await get_service_for_user("user-123", mock_redis)
            
            mock_service.assert_called_once()


class TestEnsureValidToken:
    """Testes para validação de token."""

    async def test_ensure_valid_token_no_token(self, mock_redis):
        """Testa quando não há token."""
        mock_redis.get.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            await ensure_valid_token("user-123", mock_redis)
        
        assert exc.value.status_code == 401
        assert "Não conectado" in exc.value.detail

    async def test_ensure_valid_token_valid(self, mock_redis, mock_token_data):
        """Testa com token válido."""
        mock_redis.get.return_value = json.dumps(mock_token_data)
        
        token = await ensure_valid_token("user-123", mock_redis)
        
        assert token.access_token == "acc_token_xyz"

    async def test_ensure_valid_token_expired_refresh_success(self, mock_redis):
        """Testa renovação de token expirado."""
        # Token expirado
        now = datetime.utcnow()
        expired_token = {
            "access_token": "old_token",
            "refresh_token": "ref_token",
            "access_token_expires_at": (now - timedelta(minutes=1)).isoformat(),
            "refresh_token_expires_at": (now + timedelta(days=30)).isoformat(),
            "open_id": "open_id",
            "seller_name": "Seller",
            "seller_base_region": "BR",
            "user_type": 1
        }
        
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        mock_redis.get.side_effect = [
            json.dumps(expired_token),  # get_user_token
            json.dumps(creds_data)       # get_user_credentials
        ]
        
        new_token_data = {
            "access_token": "new_token",
            "refresh_token": "new_ref",
            "access_token_expires_at": now + timedelta(hours=4),
            "refresh_token_expires_at": now + timedelta(days=30),
            "open_id": "open_id",
            "seller_name": "Seller",
            "seller_base_region": "BR",
            "user_type": 1
        }
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service_cls.return_value = mock_service
            
            from integrations.tiktok_shop_service import TikTokShopToken
            mock_service.refresh_token.return_value = TikTokShopToken(**new_token_data)
            mock_service.close = AsyncMock()
            
            token = await ensure_valid_token("user-123", mock_redis)
            
            assert token.access_token == "new_token"
            mock_service.refresh_token.assert_called_once()

    async def test_ensure_valid_token_expired_no_credentials(self, mock_redis):
        """Testa renovação sem credenciais."""
        now = datetime.utcnow()
        expired_token = {
            "access_token": "old_token",
            "refresh_token": "ref_token",
            "access_token_expires_at": (now - timedelta(minutes=1)).isoformat(),
            "refresh_token_expires_at": (now + timedelta(days=30)).isoformat(),
            "open_id": "open_id",
            "seller_name": "Seller",
            "seller_base_region": "BR",
            "user_type": 1
        }
        
        mock_redis.get.side_effect = [
            json.dumps(expired_token),  # get_user_token
            None                         # get_user_credentials - não encontrado
        ]
        
        with pytest.raises(HTTPException) as exc:
            await ensure_valid_token("user-123", mock_redis)
        
        assert exc.value.status_code == 400
        assert "Credenciais não encontradas" in exc.value.detail

    async def test_ensure_valid_token_refresh_error(self, mock_redis):
        """Testa erro na renovação."""
        from integrations.tiktok_shop_service import TikTokShopError
        
        now = datetime.utcnow()
        expired_token = {
            "access_token": "old_token",
            "refresh_token": "ref_token",
            "access_token_expires_at": (now - timedelta(minutes=1)).isoformat(),
            "refresh_token_expires_at": (now + timedelta(days=30)).isoformat(),
            "open_id": "open_id",
            "seller_name": "Seller",
            "seller_base_region": "BR",
            "user_type": 1
        }
        
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        mock_redis.get.side_effect = [
            json.dumps(expired_token),
            json.dumps(creds_data)
        ]
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service_cls.return_value = mock_service
            mock_service.refresh_token.side_effect = TikTokShopError("Token expired")
            mock_service.close = AsyncMock()
            
            with pytest.raises(HTTPException) as exc:
                await ensure_valid_token("user-123", mock_redis)
            
            assert exc.value.status_code == 401
            assert "Sessão expirada" in exc.value.detail


# ==================== TESTES DE SCHEMAS ====================

class TestSchemas:
    """Testes para schemas Pydantic."""

    def test_credentials_input_valid(self):
        """Testa validação de credenciais válidas."""
        creds = CredentialsInput(
            app_key="12345",
            app_secret="1234567890",
            service_id="svc123"
        )
        assert creds.app_key == "12345"
        assert creds.service_id == "svc123"

    def test_credentials_input_minimal(self):
        """Testa credenciais com campos mínimos."""
        creds = CredentialsInput(
            app_key="12345",
            app_secret="1234567890"
        )
        assert creds.service_id is None

    def test_auth_callback_input(self):
        """Testa input de callback OAuth."""
        callback = AuthCallbackInput(
            code="auth_code_123",
            state="user123:random_state"
        )
        assert callback.code == "auth_code_123"

    def test_connection_status_disconnected(self):
        """Testa status desconectado."""
        status = ConnectionStatus(connected=False)
        assert status.connected is False
        assert status.seller_name is None
        assert status.shops == []

    def test_connection_status_connected(self):
        """Testa status conectado."""
        status = ConnectionStatus(
            connected=True,
            seller_name="Test Seller",
            seller_region="BR",
            shops=[{"shop_id": "123", "name": "Shop"}],
            product_count=50
        )
        assert status.connected is True
        assert status.product_count == 50

    def test_product_list_response(self):
        """Testa resposta de listagem de produtos."""
        response = ProductListResponse(
            products=[{"id": "1", "title": "Product"}],
            total=1,
            next_page_token="token_abc"
        )
        assert response.total == 1
        assert response.next_page_token == "token_abc"

    def test_sync_result(self):
        """Testa resultado de sincronização."""
        result = SyncResult(
            success=True,
            products_synced=100,
            errors=[],
            duration_seconds=5.5
        )
        assert result.success is True
        assert result.products_synced == 100


# ==================== TESTES DE ENDPOINTS (MOCK) ====================

class TestCredentialsEndpoints:
    """Testes para endpoints de credenciais."""

    @pytest.fixture
    def app(self):
        """App FastAPI para testes."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return app

    async def test_set_credentials(self, mock_redis, mock_user, mock_credentials):
        """Testa configuração de credenciais."""
        with patch("api.routes.tiktok_shop_v2.save_user_credentials") as mock_save:
            mock_save.return_value = None
            
            # Simula chamada direta
            from api.routes.tiktok_shop_v2 import set_credentials
            result = await set_credentials(
                credentials=mock_credentials,
                current_user=mock_user,
                redis=mock_redis
            )
            
            assert result["success"] is True
            mock_save.assert_called_once()

    async def test_check_credentials_not_configured(self, mock_redis, mock_user):
        """Testa verificação sem credenciais."""
        mock_redis.get.return_value = None
        
        from api.routes.tiktok_shop_v2 import check_credentials
        result = await check_credentials(
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result["configured"] is False
        assert result["app_key"] is None

    async def test_check_credentials_configured(self, mock_redis, mock_user):
        """Testa verificação com credenciais."""
        creds_data = {
            "app_key": "1234567890abcdef",
            "app_secret": "secret",
            "service_id": None
        }
        mock_redis.get.return_value = json.dumps(creds_data)
        
        from api.routes.tiktok_shop_v2 import check_credentials
        result = await check_credentials(
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result["configured"] is True
        assert result["app_key"] == "12345678..."

    async def test_delete_credentials(self, mock_redis, mock_user):
        """Testa remoção de credenciais."""
        from api.routes.tiktok_shop_v2 import delete_credentials
        result = await delete_credentials(
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result["success"] is True
        assert mock_redis.delete.call_count == 3


class TestOAuthEndpoints:
    """Testes para endpoints OAuth."""

    async def test_get_auth_url_no_credentials(self, mock_redis, mock_user):
        """Testa URL de auth sem credenciais."""
        mock_redis.get.return_value = None
        
        from api.routes.tiktok_shop_v2 import get_auth_url
        
        with pytest.raises(HTTPException) as exc:
            await get_auth_url(current_user=mock_user, redis=mock_redis)
        
        assert exc.value.status_code == 400
        assert "Configure suas credenciais" in exc.value.detail

    async def test_get_auth_url_success(self, mock_redis, mock_user):
        """Testa geração de URL de auth."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        mock_redis.get.return_value = json.dumps(creds_data)
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_auth_url.return_value = "https://auth.tiktok.com/oauth?..."
            mock_service.close = AsyncMock()
            
            from api.routes.tiktok_shop_v2 import get_auth_url
            result = await get_auth_url(current_user=mock_user, redis=mock_redis)
            
            assert "auth_url" in result
            assert "state" in result
            assert result["expires_in"] == 600

    async def test_oauth_callback_invalid_state(self, mock_redis, mock_user):
        """Testa callback com state inválido."""
        mock_redis.get.return_value = None  # State não encontrado
        
        callback = AuthCallbackInput(code="code_123", state="invalid_state")
        
        from api.routes.tiktok_shop_v2 import oauth_callback
        
        with pytest.raises(HTTPException) as exc:
            await oauth_callback(
                callback=callback,
                current_user=mock_user,
                redis=mock_redis
            )
        
        assert exc.value.status_code == 400
        assert "State inválido" in exc.value.detail

    async def test_oauth_callback_wrong_user(self, mock_redis, mock_user):
        """Testa callback com state de outro usuário."""
        mock_redis.get.return_value = "other-user-id"  # ID diferente
        
        callback = AuthCallbackInput(code="code_123", state="state_123")
        
        from api.routes.tiktok_shop_v2 import oauth_callback
        
        with pytest.raises(HTTPException) as exc:
            await oauth_callback(
                callback=callback,
                current_user=mock_user,
                redis=mock_redis
            )
        
        assert exc.value.status_code == 400

    async def test_oauth_callback_success(self, mock_redis, mock_user, mock_tiktok_token, mock_shop_info):
        """Testa callback OAuth com sucesso."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        # Configura retornos do Redis
        mock_redis.get.side_effect = [
            "user-123",              # Valida state
            json.dumps(creds_data)   # get_user_credentials
        ]
        
        callback = AuthCallbackInput(code="auth_code", state="state_123")
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service_cls.return_value = mock_service
            mock_service.exchange_code.return_value = mock_tiktok_token
            mock_service.get_active_shops.return_value = [mock_shop_info]
            mock_service.close = AsyncMock()
            
            from api.routes.tiktok_shop_v2 import oauth_callback
            result = await oauth_callback(
                callback=callback,
                current_user=mock_user,
                redis=mock_redis
            )
            
            assert result["success"] is True
            assert result["seller_name"] == "Test Seller"

    async def test_oauth_callback_tiktok_error(self, mock_redis, mock_user):
        """Testa callback com erro do TikTok."""
        from integrations.tiktok_shop_service import TikTokShopError
        
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        mock_redis.get.side_effect = [
            "user-123",
            json.dumps(creds_data)
        ]
        
        callback = AuthCallbackInput(code="bad_code", state="state_123")
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service_cls.return_value = mock_service
            mock_service.exchange_code.side_effect = TikTokShopError("Invalid code")
            mock_service.close = AsyncMock()
            
            from api.routes.tiktok_shop_v2 import oauth_callback
            
            with pytest.raises(HTTPException) as exc:
                await oauth_callback(
                    callback=callback,
                    current_user=mock_user,
                    redis=mock_redis
                )
            
            assert exc.value.status_code == 400


class TestConnectionEndpoints:
    """Testes para endpoints de conexão."""

    async def test_get_connection_status_not_configured(self, mock_redis, mock_user):
        """Testa status sem configuração."""
        mock_redis.get.return_value = None
        
        from api.routes.tiktok_shop_v2 import get_connection_status
        result = await get_connection_status(
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result.connected is False

    async def test_get_connection_status_no_token(self, mock_redis, mock_user):
        """Testa status sem token."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        mock_redis.get.side_effect = [
            json.dumps(creds_data),  # credentials
            None                      # token
        ]
        
        from api.routes.tiktok_shop_v2 import get_connection_status
        result = await get_connection_status(
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result.connected is False

    async def test_get_connection_status_connected(self, mock_redis, mock_user, mock_token_data):
        """Testa status conectado."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        shops_data = [{"shop_id": "123", "name": "Shop"}]
        
        mock_redis.get.side_effect = [
            json.dumps(creds_data),     # credentials
            json.dumps(mock_token_data), # token
            json.dumps(shops_data),      # shops
            "50",                         # product_count
            datetime.utcnow().isoformat() # last_sync
        ]
        
        from api.routes.tiktok_shop_v2 import get_connection_status
        result = await get_connection_status(
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result.connected is True
        assert result.seller_name == "Test Seller"
        assert result.product_count == 50

    async def test_disconnect(self, mock_redis, mock_user):
        """Testa desconexão."""
        from api.routes.tiktok_shop_v2 import disconnect
        result = await disconnect(
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result["success"] is True
        assert mock_redis.delete.call_count == 2


class TestProductEndpoints:
    """Testes para endpoints de produtos."""

    async def test_list_products_success(self, mock_redis, mock_user, mock_token_data, mock_product):
        """Testa listagem de produtos."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        mock_redis.get.side_effect = [
            json.dumps(mock_token_data),  # ensure_valid_token
            json.dumps(creds_data),        # get_service_for_user
            None                            # shops (não necessário sem shop_id)
        ]
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service_cls.return_value = mock_service
            mock_service.search_products.return_value = ([mock_product], "next_token")
            mock_service.close = AsyncMock()
            
            from api.routes.tiktok_shop_v2 import list_products
            result = await list_products(
                page_size=20,
                page_token=None,
                status=None,
                shop_id=None,
                current_user=mock_user,
                redis=mock_redis
            )
            
            assert result.total == 1
            assert result.next_page_token == "next_token"

    async def test_list_products_with_filters(self, mock_redis, mock_user, mock_token_data, mock_product):
        """Testa listagem com filtros."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        shops_data = [{"shop_id": "shop_123", "shop_cipher": "cipher_abc"}]
        
        mock_redis.get.side_effect = [
            json.dumps(mock_token_data),
            json.dumps(creds_data),
            json.dumps(shops_data)
        ]
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service_cls.return_value = mock_service
            mock_service.search_products.return_value = ([mock_product], None)
            mock_service.close = AsyncMock()
            
            from api.routes.tiktok_shop_v2 import list_products
            result = await list_products(
                page_size=50,
                page_token="prev_token",
                status="ACTIVATE",
                shop_id="shop_123",
                current_user=mock_user,
                redis=mock_redis
            )
            
            assert result.total == 1

    async def test_list_products_tiktok_error(self, mock_redis, mock_user, mock_token_data):
        """Testa listagem com erro do TikTok."""
        from integrations.tiktok_shop_service import TikTokShopError
        
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        mock_redis.get.side_effect = [
            json.dumps(mock_token_data),
            json.dumps(creds_data),
            None
        ]
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service_cls.return_value = mock_service
            mock_service.search_products.side_effect = TikTokShopError("API Error")
            mock_service.close = AsyncMock()
            
            from api.routes.tiktok_shop_v2 import list_products
            
            with pytest.raises(HTTPException) as exc:
                await list_products(
                    page_size=20,
                    current_user=mock_user,
                    redis=mock_redis
                )
            
            assert exc.value.status_code == 400


class TestSyncEndpoints:
    """Testes para endpoints de sincronização."""

    async def test_sync_products_already_running(self, mock_redis, mock_user, mock_token_data):
        """Testa sync já em andamento."""
        mock_redis.get.return_value = "1"  # sync já rodando
        
        from api.routes.tiktok_shop_v2 import sync_products
        from fastapi import BackgroundTasks
        
        bg_tasks = BackgroundTasks()
        result = await sync_products(
            background_tasks=bg_tasks,
            shop_id=None,
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result["success"] is False
        assert "já em andamento" in result["message"]

    async def test_sync_products_start(self, mock_redis, mock_user):
        """Testa início de sincronização."""
        mock_redis.get.return_value = None  # Sem sync rodando
        
        from api.routes.tiktok_shop_v2 import sync_products
        from fastapi import BackgroundTasks
        
        bg_tasks = MagicMock(spec=BackgroundTasks)
        result = await sync_products(
            background_tasks=bg_tasks,
            shop_id="shop_123",
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result["success"] is True
        bg_tasks.add_task.assert_called_once()

    async def test_get_sync_status_running(self, mock_redis, mock_user):
        """Testa status de sync em andamento."""
        mock_redis.get.side_effect = ["1", None]  # running, no result
        
        from api.routes.tiktok_shop_v2 import get_sync_status
        result = await get_sync_status(
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result["running"] is True
        assert result["last_result"] is None

    async def test_get_sync_status_completed(self, mock_redis, mock_user):
        """Testa status de sync completa."""
        sync_result = {
            "success": True,
            "products_synced": 100,
            "errors": [],
            "duration_seconds": 5.0
        }
        
        mock_redis.get.side_effect = [None, json.dumps(sync_result)]
        
        from api.routes.tiktok_shop_v2 import get_sync_status
        result = await get_sync_status(
            current_user=mock_user,
            redis=mock_redis
        )
        
        assert result["running"] is False
        assert result["last_result"]["products_synced"] == 100


class TestShopsEndpoint:
    """Testes para endpoint de lojas."""

    async def test_list_shops_success(self, mock_redis, mock_user, mock_token_data, mock_shop_info):
        """Testa listagem de lojas."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        mock_redis.get.side_effect = [
            json.dumps(mock_token_data),
            json.dumps(creds_data)
        ]
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_active_shops.return_value = [mock_shop_info]
            mock_service.close = AsyncMock()
            
            from api.routes.tiktok_shop_v2 import list_shops
            result = await list_shops(
                current_user=mock_user,
                redis=mock_redis
            )
            
            assert "shops" in result
            assert len(result["shops"]) == 1

    async def test_list_shops_tiktok_error(self, mock_redis, mock_user, mock_token_data):
        """Testa listagem com erro."""
        from integrations.tiktok_shop_service import TikTokShopError
        
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        mock_redis.get.side_effect = [
            json.dumps(mock_token_data),
            json.dumps(creds_data)
        ]
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_active_shops.side_effect = TikTokShopError("API Error")
            mock_service.close = AsyncMock()
            
            from api.routes.tiktok_shop_v2 import list_shops
            
            with pytest.raises(HTTPException) as exc:
                await list_shops(
                    current_user=mock_user,
                    redis=mock_redis
                )
            
            assert exc.value.status_code == 400


# ==================== TESTES DE BACKGROUND TASK ====================

class TestBackgroundSync:
    """Testes para tarefa de sincronização em background."""

    async def test_run_product_sync_no_credentials(self, mock_redis):
        """Testa sync sem credenciais."""
        mock_redis.get.side_effect = [None, None]
        
        await run_product_sync(
            user_id="user-123",
            shop_id=None,
            redis=mock_redis
        )
        
        # Deve salvar resultado de erro
        mock_redis.set.assert_called()

    async def test_run_product_sync_success(self, mock_redis, mock_token_data, mock_product):
        """Testa sync com sucesso."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        mock_redis.get.side_effect = [
            json.dumps(creds_data),
            json.dumps(mock_token_data),
            None  # shops
        ]
        
        # Mock do product com SKUs
        mock_product_with_sku = MagicMock()
        mock_product_with_sku.id = "prod_123"
        mock_product_with_sku.title = "Test Product"
        mock_product_with_sku.status.value = "ACTIVATE"
        mock_product_with_sku.sales_regions = ["BR"]
        mock_product_with_sku.listing_quality_tier = "GOOD"
        mock_product_with_sku.skus = []
        mock_product_with_sku.dict.return_value = {"id": "prod_123"}
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_all_products.return_value = [mock_product_with_sku]
            mock_service.close = AsyncMock()
            
            with patch("api.routes.tiktok_shop_v2.async_session_maker") as mock_session:
                session = AsyncMock()
                session.__aenter__.return_value = session
                session.__aexit__.return_value = None
                mock_session.return_value = session
                
                await run_product_sync(
                    user_id="user-123",
                    shop_id=None,
                    redis=mock_redis
                )
                
                # Verifica se salvou resultado
                assert mock_redis.set.called

    async def test_run_product_sync_with_shop_id(self, mock_redis, mock_token_data):
        """Testa sync com shop_id específico."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        shops_data = [{"shop_id": "shop_123", "shop_cipher": "cipher_abc"}]
        
        mock_redis.get.side_effect = [
            json.dumps(creds_data),
            json.dumps(mock_token_data),
            json.dumps(shops_data)
        ]
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_all_products.return_value = []
            mock_service.close = AsyncMock()
            
            with patch("api.routes.tiktok_shop_v2.async_session_maker") as mock_session:
                session = AsyncMock()
                session.__aenter__.return_value = session
                session.__aexit__.return_value = None
                mock_session.return_value = session
                
                await run_product_sync(
                    user_id="user-123",
                    shop_id="shop_123",
                    redis=mock_redis
                )
                
                # Verifica se usou shop_cipher correto
                mock_service.get_all_products.assert_called_once()
                call_kwargs = mock_service.get_all_products.call_args[1]
                assert call_kwargs["shop_cipher"] == "cipher_abc"

    async def test_run_product_sync_with_errors(self, mock_redis, mock_token_data):
        """Testa sync com erros em produtos."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        mock_redis.get.side_effect = [
            json.dumps(creds_data),
            json.dumps(mock_token_data),
            None
        ]
        
        # Produto que vai causar erro
        bad_product = MagicMock()
        bad_product.id = "bad_prod"
        bad_product.title = "Bad Product"
        bad_product.status.value = "ACTIVATE"
        bad_product.sales_regions = ["BR"]
        bad_product.listing_quality_tier = "GOOD"
        bad_product.skus = []
        bad_product.dict.side_effect = Exception("Serialization error")
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service_cls.return_value = mock_service
            mock_service.get_all_products.return_value = [bad_product]
            mock_service.close = AsyncMock()
            
            with patch("api.routes.tiktok_shop_v2.async_session_maker") as mock_session:
                session = AsyncMock()
                session.__aenter__.return_value = session
                session.__aexit__.return_value = None
                session.merge.side_effect = Exception("DB Error")
                mock_session.return_value = session
                
                await run_product_sync(
                    user_id="user-123",
                    shop_id=None,
                    redis=mock_redis
                )
                
                # Deve ter registrado erro
                set_calls = [call for call in mock_redis.set.call_args_list 
                            if "sync_result" in str(call)]
                assert len(set_calls) > 0

    async def test_run_product_sync_exception(self, mock_redis, mock_token_data):
        """Testa sync com exceção geral."""
        creds_data = {
            "app_key": "test_key",
            "app_secret": "test_secret",
            "service_id": None
        }
        
        mock_redis.get.side_effect = [
            json.dumps(creds_data),
            json.dumps(mock_token_data),
            None
        ]
        
        with patch("api.routes.tiktok_shop_v2.TikTokShopService") as mock_service_cls:
            mock_service_cls.side_effect = Exception("Connection error")
            
            await run_product_sync(
                user_id="user-123",
                shop_id=None,
                redis=mock_redis
            )
            
            # Deve ter salvo resultado com erro
            assert mock_redis.set.called


# ==================== TESTES DE INTEGRAÇÃO ====================

class TestIntegration:
    """Testes de integração do módulo."""

    def test_router_has_correct_prefix(self):
        """Verifica prefix do router."""
        assert router.prefix == "/tiktok-shop"

    def test_router_has_correct_tags(self):
        """Verifica tags do router."""
        assert "TikTok Shop" in router.tags

    def test_all_endpoints_exist(self):
        """Verifica se todos os endpoints estão registrados."""
        routes = [route.path for route in router.routes]
        
        expected_paths = [
            "/credentials",
            "/credentials/status",
            "/auth/url",
            "/auth/callback",
            "/status",
            "/disconnect",
            "/products",
            "/products/sync",
            "/products/sync/status",
            "/shops"
        ]
        
        for path in expected_paths:
            full_path = f"/tiktok-shop{path}"
            assert any(full_path in r or path in r for r in routes), \
                f"Path {path} not found in routes"
