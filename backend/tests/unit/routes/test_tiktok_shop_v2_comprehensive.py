"""Testes abrangentes para TikTok Shop V2 API Routes."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.tiktok_shop_v2 import (AuthCallbackInput, ConnectionStatus,
                                       CredentialsInput, ProductListResponse,
                                       SyncResult, ensure_valid_token,
                                       get_redis_key, get_service_for_user,
                                       get_user_credentials, get_user_token,
                                       router, save_user_credentials,
                                       save_user_token)
from fastapi import HTTPException


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_user():
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def mock_credentials():
    return CredentialsInput(
        app_key="test_app_key_12345",
        app_secret="test_app_secret_67890",
        service_id="service_123"
    )


@pytest.fixture
def mock_token_data():
    now = datetime.now(timezone.utc)
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


class TestHelpers:
    def test_get_redis_key(self):
        key = get_redis_key("user-123", "credentials")
        assert key == "tiktok_shop:user-123:credentials"

    async def test_get_user_credentials_not_found(self, mock_redis):
        mock_redis.get.return_value = None
        result = await get_user_credentials("user-123", mock_redis)
        assert result is None

    async def test_get_user_credentials_found(self, mock_redis):
        creds_data = {"app_key": "test_key", "app_secret": "test_secret", "service_id": None}
        mock_redis.get.return_value = json.dumps(creds_data)
        result = await get_user_credentials("user-123", mock_redis)
        assert result is not None
        assert result.app_key == "test_key"

    async def test_save_user_credentials(self, mock_redis, mock_credentials):
        await save_user_credentials("user-123", mock_credentials, mock_redis)
        # save_user_credentials faz 2 chamadas: uma para credentials e outra para o secret
        assert mock_redis.set.call_count == 2

    async def test_get_user_token_not_found(self, mock_redis):
        mock_redis.get.return_value = None
        result = await get_user_token("user-123", mock_redis)
        assert result is None

    async def test_get_user_token_found(self, mock_redis, mock_token_data):
        mock_redis.get.return_value = json.dumps(mock_token_data)
        result = await get_user_token("user-123", mock_redis)
        assert result is not None
        assert result.access_token == "acc_token_xyz"

    async def test_get_service_for_user_no_credentials(self, mock_redis):
        mock_redis.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            await get_service_for_user("user-123", mock_redis)
        assert exc.value.status_code == 400


class TestEnsureValidToken:
    async def test_ensure_valid_token_no_token(self, mock_redis):
        mock_redis.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            await ensure_valid_token("user-123", mock_redis)
        assert exc.value.status_code == 401

    async def test_ensure_valid_token_valid(self, mock_redis, mock_token_data):
        mock_redis.get.return_value = json.dumps(mock_token_data)
        token = await ensure_valid_token("user-123", mock_redis)
        assert token.access_token == "acc_token_xyz"


class TestSchemas:
    def test_credentials_input_valid(self):
        creds = CredentialsInput(app_key="12345", app_secret="1234567890", service_id="svc123")
        assert creds.app_key == "12345"

    def test_connection_status_disconnected(self):
        status = ConnectionStatus(connected=False)
        assert status.connected is False

    def test_connection_status_connected(self):
        status = ConnectionStatus(
            connected=True, seller_name="Test", seller_region="BR",
            shops=[{"shop_id": "123"}], product_count=50
        )
        assert status.product_count == 50

    def test_product_list_response(self):
        response = ProductListResponse(products=[{"id": "1"}], total=1, next_page_token="token")
        assert response.total == 1

    def test_sync_result(self):
        result = SyncResult(success=True, products_synced=100, errors=[], duration_seconds=5.5)
        assert result.success is True


class TestCredentialsEndpoints:
    async def test_set_credentials(self, mock_redis, mock_user, mock_credentials):
        with patch("api.routes.tiktok_shop_v2.save_user_credentials") as mock_save:
            mock_save.return_value = None
            from api.routes.tiktok_shop_v2 import set_credentials
            result = await set_credentials(credentials=mock_credentials, current_user=mock_user, redis=mock_redis)
            assert result["success"] is True

    async def test_check_credentials_not_configured(self, mock_redis, mock_user):
        mock_redis.get.return_value = None
        from api.routes.tiktok_shop_v2 import check_credentials
        result = await check_credentials(current_user=mock_user, redis=mock_redis)
        assert result["configured"] is False

    async def test_delete_credentials(self, mock_redis, mock_user):
        from api.routes.tiktok_shop_v2 import delete_credentials
        result = await delete_credentials(current_user=mock_user, redis=mock_redis)
        assert result["success"] is True


class TestOAuthEndpoints:
    async def test_get_auth_url_no_credentials(self, mock_redis, mock_user):
        mock_redis.get.return_value = None
        from api.routes.tiktok_shop_v2 import get_auth_url
        with pytest.raises(HTTPException) as exc:
            await get_auth_url(current_user=mock_user, redis=mock_redis)
        assert exc.value.status_code == 400

    async def test_oauth_callback_invalid_state(self, mock_redis, mock_user):
        mock_redis.get.return_value = None
        callback = AuthCallbackInput(code="code_123", state="invalid_state")
        from api.routes.tiktok_shop_v2 import oauth_callback
        with pytest.raises(HTTPException) as exc:
            await oauth_callback(callback=callback, current_user=mock_user, redis=mock_redis)
        assert exc.value.status_code == 400


class TestConnectionEndpoints:
    async def test_get_connection_status_not_configured(self, mock_redis, mock_user):
        mock_redis.get.return_value = None
        from api.routes.tiktok_shop_v2 import get_connection_status
        result = await get_connection_status(current_user=mock_user, redis=mock_redis)
        assert result.connected is False

    async def test_disconnect(self, mock_redis, mock_user):
        from api.routes.tiktok_shop_v2 import disconnect
        result = await disconnect(current_user=mock_user, redis=mock_redis)
        assert result["success"] is True


class TestSyncEndpoints:
    async def test_sync_products_already_running(self, mock_redis, mock_user):
        mock_redis.get.return_value = "1"
        from api.routes.tiktok_shop_v2 import sync_products
        from fastapi import BackgroundTasks
        bg_tasks = BackgroundTasks()
        result = await sync_products(background_tasks=bg_tasks, shop_id=None, current_user=mock_user, redis=mock_redis)
        assert result["success"] is False

    async def test_sync_products_start(self, mock_redis, mock_user):
        mock_redis.get.return_value = None
        from api.routes.tiktok_shop_v2 import sync_products
        from fastapi import BackgroundTasks
        bg_tasks = MagicMock(spec=BackgroundTasks)
        result = await sync_products(background_tasks=bg_tasks, shop_id="shop_123", current_user=mock_user, redis=mock_redis)
        assert result["success"] is True

    async def test_get_sync_status_running(self, mock_redis, mock_user):
        mock_redis.get.side_effect = ["1", None]
        from api.routes.tiktok_shop_v2 import get_sync_status
        result = await get_sync_status(current_user=mock_user, redis=mock_redis)
        assert result["running"] is True


class TestIntegration:
    def test_router_has_correct_prefix(self):
        # Router não define prefix diretamente, é definido no include
        assert router.prefix == "" or router.prefix == "/tiktok-shop"

    def test_router_has_correct_tags(self):
        assert "TikTok Shop V2" in router.tags
