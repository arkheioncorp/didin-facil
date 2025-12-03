"""
Testes abrangentes para api/routes/social_auth.py
Autenticação OAuth para redes sociais
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import Response as HttpxResponse

# ==================== FIXTURES ====================

@pytest.fixture
def mock_user():
    """Usuário autenticado mockado."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "name": "Test User"
    }


@pytest.fixture
def mock_redis():
    """Redis client mockado."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=True)
    redis.scan = AsyncMock(return_value=(0, []))
    return redis


@pytest.fixture
def mock_subscription_service():
    """Subscription service mockado."""
    service = AsyncMock()
    service.can_use_feature = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_httpx_client():
    """HTTP client mockado."""
    client = AsyncMock()
    return client


# ==================== TEST ENCRYPT/DECRYPT ====================

class TestEncryptDecrypt:
    """Testes para funções de criptografia."""

    def test_encrypt_token(self):
        """Testa encriptação de token."""
        from api.routes.social_auth import encrypt_token
        
        token = "test_access_token_123"
        user_id = "user-123"
        
        encrypted = encrypt_token(token, user_id)
        
        assert encrypted != token
        assert isinstance(encrypted, str)
        # Hex encoding
        assert all(c in '0123456789abcdef' for c in encrypted)

    def test_decrypt_token(self):
        """Testa decriptação de token."""
        from api.routes.social_auth import decrypt_token, encrypt_token
        
        token = "test_access_token_123"
        user_id = "user-123"
        
        encrypted = encrypt_token(token, user_id)
        decrypted = decrypt_token(encrypted, user_id)
        
        assert decrypted == token

    def test_encrypt_decrypt_different_users(self):
        """Testa que tokens encriptados são diferentes por usuário."""
        from api.routes.social_auth import decrypt_token, encrypt_token
        
        token = "same_token"
        
        encrypted1 = encrypt_token(token, "user-1")
        encrypted2 = encrypt_token(token, "user-2")
        
        # Mesmos tokens encriptados com usuários diferentes são diferentes
        assert encrypted1 != encrypted2
        
        # Cada um decripta corretamente com seu usuário
        assert decrypt_token(encrypted1, "user-1") == token
        assert decrypt_token(encrypted2, "user-2") == token


# ==================== TEST PLATFORM CONFIG ====================

class TestPlatformConfig:
    """Testes para configuração de plataformas."""

    def test_get_platform_config_instagram(self):
        """Testa config do Instagram."""
        from api.routes.social_auth import get_platform_config
        
        config = get_platform_config("instagram")
        
        assert "auth_url" in config
        assert "token_url" in config
        assert "scopes" in config
        assert "instagram.com" in config["auth_url"]

    def test_get_platform_config_tiktok(self):
        """Testa config do TikTok."""
        from api.routes.social_auth import get_platform_config
        
        config = get_platform_config("tiktok")
        
        assert "tiktok" in config["auth_url"]
        assert "user.info.basic" in config["scopes"]

    def test_get_platform_config_youtube(self):
        """Testa config do YouTube."""
        from api.routes.social_auth import get_platform_config
        
        config = get_platform_config("youtube")
        
        assert "google" in config["auth_url"]
        assert any("youtube" in s for s in config["scopes"])

    def test_get_platform_config_tiktok_shop(self):
        """Testa config do TikTok Shop."""
        from api.routes.social_auth import get_platform_config
        
        config = get_platform_config("tiktok_shop")
        
        assert "tiktokshop" in config["auth_url"]
        assert "product.read" in config["scopes"]

    def test_get_platform_config_invalid(self):
        """Testa plataforma inválida."""
        from api.routes.social_auth import get_platform_config
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            get_platform_config("invalid_platform")
        
        assert exc.value.status_code == 400
        assert "não suportada" in exc.value.detail

    @patch("api.routes.social_auth.settings")
    def test_get_client_credentials_success(self, mock_settings):
        """Testa obtenção de credenciais."""
        from api.routes.social_auth import get_client_credentials
        
        mock_settings.INSTAGRAM_CLIENT_ID = "client_123"
        mock_settings.INSTAGRAM_CLIENT_SECRET = "secret_456"
        
        client_id, client_secret = get_client_credentials("instagram")
        
        assert client_id == "client_123"
        assert client_secret == "secret_456"

    @patch("api.routes.social_auth.settings")
    def test_get_client_credentials_missing(self, mock_settings):
        """Testa credenciais não configuradas."""
        from api.routes.social_auth import get_client_credentials
        from fastapi import HTTPException
        
        mock_settings.INSTAGRAM_CLIENT_ID = None
        mock_settings.INSTAGRAM_CLIENT_SECRET = None
        
        with pytest.raises(HTTPException) as exc:
            get_client_credentials("instagram")
        
        assert exc.value.status_code == 503
        assert "não configuradas" in exc.value.detail


# ==================== TEST INIT OAUTH ====================

class TestInitOAuth:
    """Testes para iniciação do fluxo OAuth."""

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    @patch("api.routes.social_auth.get_client_credentials")
    @patch("api.routes.social_auth.settings")
    async def test_init_oauth_instagram(
        self, mock_settings, mock_get_creds, mock_get_redis, 
        mock_redis, mock_user, mock_subscription_service
    ):
        """Testa início do OAuth para Instagram."""
        from api.routes.social_auth import OAuthInitRequest, init_oauth
        
        mock_get_redis.return_value = mock_redis
        mock_get_creds.return_value = ("client_123", "secret_456")
        mock_settings.API_URL = "https://api.test.com"
        
        request = OAuthInitRequest(
            platform="instagram",
            account_name="my_account"
        )
        
        result = await init_oauth(
            data=request,
            current_user=mock_user,
            service=mock_subscription_service
        )
        
        assert "auth_url" in result
        assert "state" in result
        assert result["expires_in"] == 600
        assert "instagram" in result["auth_url"]
        
        # Verifica que state foi salvo no Redis
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert "oauth:state:" in call_args[0][0]

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    @patch("api.routes.social_auth.get_client_credentials")
    @patch("api.routes.social_auth.settings")
    async def test_init_oauth_youtube_params(
        self, mock_settings, mock_get_creds, mock_get_redis,
        mock_redis, mock_user, mock_subscription_service
    ):
        """Testa parâmetros específicos do YouTube."""
        from api.routes.social_auth import OAuthInitRequest, init_oauth
        
        mock_get_redis.return_value = mock_redis
        mock_get_creds.return_value = ("client_123", "secret_456")
        mock_settings.API_URL = "https://api.test.com"
        
        request = OAuthInitRequest(
            platform="youtube",
            account_name="my_channel"
        )
        
        result = await init_oauth(
            data=request,
            current_user=mock_user,
            service=mock_subscription_service
        )
        
        # YouTube adiciona access_type e prompt
        assert "access_type=offline" in result["auth_url"]
        assert "prompt=consent" in result["auth_url"]

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    @patch("api.routes.social_auth.get_client_credentials")
    @patch("api.routes.social_auth.settings")
    async def test_init_oauth_tiktok_params(
        self, mock_settings, mock_get_creds, mock_get_redis,
        mock_redis, mock_user, mock_subscription_service
    ):
        """Testa parâmetros específicos do TikTok."""
        from api.routes.social_auth import OAuthInitRequest, init_oauth
        
        mock_get_redis.return_value = mock_redis
        mock_get_creds.return_value = ("client_key_123", "secret_456")
        mock_settings.API_URL = "https://api.test.com"
        
        request = OAuthInitRequest(
            platform="tiktok",
            account_name="my_tiktok"
        )
        
        result = await init_oauth(
            data=request,
            current_user=mock_user,
            service=mock_subscription_service
        )
        
        # TikTok usa client_key ao invés de client_id
        assert "client_key=" in result["auth_url"]

    @pytest.mark.asyncio
    async def test_init_oauth_limit_reached(
        self, mock_user, mock_subscription_service
    ):
        """Testa limite de contas atingido."""
        from api.routes.social_auth import OAuthInitRequest, init_oauth
        from fastapi import HTTPException
        
        mock_subscription_service.can_use_feature = AsyncMock(return_value=False)
        
        request = OAuthInitRequest(
            platform="instagram",
            account_name="my_account"
        )
        
        with pytest.raises(HTTPException) as exc:
            await init_oauth(
                data=request,
                current_user=mock_user,
                service=mock_subscription_service
            )
        
        assert exc.value.status_code == 402
        assert "Limite" in exc.value.detail

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    @patch("api.routes.social_auth.get_client_credentials")
    @patch("api.routes.social_auth.settings")
    async def test_init_oauth_custom_scopes(
        self, mock_settings, mock_get_creds, mock_get_redis,
        mock_redis, mock_user, mock_subscription_service
    ):
        """Testa scopes customizados."""
        from api.routes.social_auth import OAuthInitRequest, init_oauth
        
        mock_get_redis.return_value = mock_redis
        mock_get_creds.return_value = ("client_123", "secret_456")
        mock_settings.API_URL = "https://api.test.com"
        
        request = OAuthInitRequest(
            platform="instagram",
            account_name="my_account",
            scopes=["user_profile", "user_media", "instagram_graph_user_profile"]
        )
        
        result = await init_oauth(
            data=request,
            current_user=mock_user,
            service=mock_subscription_service
        )
        
        assert "instagram_graph_user_profile" in result["auth_url"]


# ==================== TEST OAUTH CALLBACK ====================

class TestOAuthCallback:
    """Testes para callback OAuth."""

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    @patch("api.routes.social_auth.get_client_credentials")
    @patch("api.routes.social_auth.settings")
    @patch("api.routes.social_auth.httpx.AsyncClient")
    async def test_callback_success(
        self, mock_httpx, mock_settings, mock_get_creds, mock_get_redis,
        mock_redis
    ):
        """Testa callback bem sucedido."""
        from api.routes.social_auth import oauth_callback

        # Setup
        state_data = {
            "user_id": "user-123",
            "platform": "instagram",
            "account_name": "my_account",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(state_data))
        mock_get_redis.return_value = mock_redis
        mock_get_creds.return_value = ("client_123", "secret_456")
        mock_settings.API_URL = "https://api.test.com"
        mock_settings.FRONTEND_URL = "https://app.test.com"
        mock_settings.JWT_SECRET_KEY = "test_secret"
        
        # Mock HTTP response
        token_response = {
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_456",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_http_client = AsyncMock()
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = token_response
        mock_http_client.post = AsyncMock(return_value=mock_http_response)
        mock_httpx.return_value.__aenter__.return_value = mock_http_client
        
        # error=None indica que não houve erro no callback
        result = await oauth_callback(
            platform="instagram",
            code="auth_code_123",
            state="valid_state",
            error=None
        )
        
        assert result.status_code == 302
        assert "Location" in result.headers
        assert "platform=instagram" in result.headers["Location"]
        assert "status=connected" in result.headers["Location"]

    @pytest.mark.asyncio
    async def test_callback_with_error(self):
        """Testa callback com erro."""
        from api.routes.social_auth import oauth_callback
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await oauth_callback(
                platform="instagram",
                code="",
                state="state",
                error="access_denied"  # Erro da plataforma OAuth
            )
        
        assert exc.value.status_code == 400
        assert "negada" in exc.value.detail

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_callback_invalid_state(self, mock_get_redis, mock_redis):
        """Testa callback com state inválido."""
        from api.routes.social_auth import oauth_callback
        from fastapi import HTTPException
        
        mock_redis.get = AsyncMock(return_value=None)
        mock_get_redis.return_value = mock_redis
        
        with pytest.raises(HTTPException) as exc:
            await oauth_callback(
                platform="instagram",
                code="auth_code",
                state="invalid_state",
                error=None
            )
        
        assert exc.value.status_code == 400
        assert "inválido" in exc.value.detail or "expirado" in exc.value.detail

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_callback_platform_mismatch(self, mock_get_redis, mock_redis):
        """Testa callback com plataforma diferente do state."""
        from api.routes.social_auth import oauth_callback
        from fastapi import HTTPException
        
        state_data = {
            "user_id": "user-123",
            "platform": "instagram",
            "account_name": "my_account",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Configure mock_redis properly
        mock_redis.get = AsyncMock(return_value=json.dumps(state_data))
        mock_redis.delete = AsyncMock()
        mock_get_redis.return_value = AsyncMock(return_value=mock_redis)()
        
        with pytest.raises(HTTPException) as exc:
            await oauth_callback(
                platform="youtube",  # Plataforma diferente
                code="auth_code",
                state="valid_state",
                error=None
            )
        
        assert exc.value.status_code == 400
        assert "não corresponde" in exc.value.detail


# ==================== TEST REFRESH TOKEN ====================

class TestRefreshToken:
    """Testes para renovação de tokens."""

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    @patch("api.routes.social_auth.get_client_credentials")
    @patch("api.routes.social_auth.httpx.AsyncClient")
    @patch("api.routes.social_auth.decrypt_token")
    @patch("api.routes.social_auth.encrypt_token")
    @patch("api.routes.social_auth.settings")
    async def test_refresh_token_success(
        self, mock_settings, mock_encrypt, mock_decrypt,
        mock_httpx, mock_get_creds, mock_get_redis,
        mock_redis, mock_user
    ):
        """Testa refresh de token bem sucedido."""
        from api.routes.social_auth import TokenRefreshRequest, refresh_token
        
        mock_settings.JWT_SECRET_KEY = "test_secret"
        
        stored_data = {
            "access_token": "encrypted_access",
            "refresh_token": "encrypted_refresh",
            "token_type": "Bearer",
            "expires_in": 3600,
            "platform": "instagram",
            "account_name": "my_account"
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(stored_data))
        mock_get_redis.return_value = mock_redis
        mock_get_creds.return_value = ("client_123", "secret_456")
        mock_decrypt.return_value = "refresh_token_value"
        mock_encrypt.side_effect = lambda x, y: f"encrypted_{x}"
        
        # Mock HTTP response
        token_response = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 7200
        }
        mock_http_client = AsyncMock()
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = token_response
        mock_http_client.post = AsyncMock(return_value=mock_http_response)
        mock_httpx.return_value.__aenter__.return_value = mock_http_client
        
        request = TokenRefreshRequest(
            platform="instagram",
            account_name="my_account"
        )
        
        result = await refresh_token(data=request, current_user=mock_user)
        
        assert result["status"] == "refreshed"
        assert "expires_at" in result

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_refresh_token_account_not_found(
        self, mock_get_redis, mock_redis, mock_user
    ):
        """Testa refresh quando conta não existe."""
        from api.routes.social_auth import TokenRefreshRequest, refresh_token
        from fastapi import HTTPException
        
        mock_redis.get = AsyncMock(return_value=None)
        mock_get_redis.return_value = mock_redis
        
        request = TokenRefreshRequest(
            platform="instagram",
            account_name="nonexistent"
        )
        
        with pytest.raises(HTTPException) as exc:
            await refresh_token(data=request, current_user=mock_user)
        
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_refresh_token_no_refresh_available(
        self, mock_get_redis, mock_redis, mock_user
    ):
        """Testa refresh quando não há refresh token."""
        from api.routes.social_auth import TokenRefreshRequest, refresh_token
        from fastapi import HTTPException
        
        stored_data = {
            "access_token": "encrypted_access",
            "refresh_token": None,  # Sem refresh token
            "platform": "instagram"
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(stored_data))
        mock_get_redis.return_value = mock_redis
        
        request = TokenRefreshRequest(
            platform="instagram",
            account_name="my_account"
        )
        
        with pytest.raises(HTTPException) as exc:
            await refresh_token(data=request, current_user=mock_user)
        
        assert exc.value.status_code == 400
        assert "não disponível" in exc.value.detail


# ==================== TEST LIST ACCOUNTS ====================

class TestListAccounts:
    """Testes para listagem de contas."""

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_list_accounts_empty(self, mock_get_redis, mock_redis, mock_user):
        """Testa listagem sem contas."""
        from api.routes.social_auth import list_connected_accounts
        
        mock_redis.scan = AsyncMock(return_value=(0, []))
        mock_get_redis.return_value = mock_redis
        
        result = await list_connected_accounts(current_user=mock_user)
        
        assert "accounts" in result
        assert result["accounts"] == []

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_list_accounts_with_data(self, mock_get_redis, mock_redis, mock_user):
        """Testa listagem com contas."""
        from api.routes.social_auth import list_connected_accounts
        
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=1)
        
        account_data = {
            "platform": "instagram",
            "account_name": "my_account",
            "connected_at": now.isoformat(),
            "expires_at": future.isoformat()
        }
        
        # Simula scan retornando uma key na primeira vez
        mock_redis.scan = AsyncMock(
            side_effect=[
                (0, [f"oauth:tokens:user-123:instagram:my_account"]),
                (0, []),
                (0, []),
                (0, []),
                (0, [])
            ]
        )
        mock_redis.get = AsyncMock(return_value=json.dumps(account_data))
        mock_get_redis.return_value = mock_redis
        
        result = await list_connected_accounts(current_user=mock_user)
        
        assert len(result["accounts"]) == 1
        assert result["accounts"][0].platform == "instagram"
        assert result["accounts"][0].status == "active"

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_list_accounts_expired(self, mock_get_redis, mock_redis, mock_user):
        """Testa listagem com conta expirada."""
        from api.routes.social_auth import list_connected_accounts
        
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)
        
        account_data = {
            "platform": "youtube",
            "account_name": "expired_account",
            "connected_at": (now - timedelta(days=30)).isoformat(),
            "expires_at": past.isoformat()  # Expirado
        }
        
        mock_redis.scan = AsyncMock(
            side_effect=[
                (0, []),
                (0, []),
                (0, []),
                (0, [f"oauth:tokens:user-123:youtube:expired_account"]),
                (0, [])
            ]
        )
        mock_redis.get = AsyncMock(return_value=json.dumps(account_data))
        mock_get_redis.return_value = mock_redis
        
        result = await list_connected_accounts(current_user=mock_user)
        
        assert len(result["accounts"]) == 1
        assert result["accounts"][0].status == "expired"


# ==================== TEST DISCONNECT ACCOUNT ====================

class TestDisconnectAccount:
    """Testes para desconexão de contas."""

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_disconnect_success(self, mock_get_redis, mock_redis, mock_user):
        """Testa desconexão bem sucedida."""
        from api.routes.social_auth import disconnect_account
        
        mock_redis.exists = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_get_redis.return_value = mock_redis
        
        result = await disconnect_account(
            platform="instagram",
            account_name="my_account",
            current_user=mock_user
        )
        
        assert result["status"] == "disconnected"
        assert result["platform"] == "instagram"
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_disconnect_not_found(self, mock_get_redis, mock_redis, mock_user):
        """Testa desconexão de conta inexistente."""
        from api.routes.social_auth import disconnect_account
        from fastapi import HTTPException
        
        mock_redis.exists = AsyncMock(return_value=False)
        mock_get_redis.return_value = mock_redis
        
        with pytest.raises(HTTPException) as exc:
            await disconnect_account(
                platform="instagram",
                account_name="nonexistent",
                current_user=mock_user
            )
        
        assert exc.value.status_code == 404


# ==================== TEST GET ACCESS TOKEN ====================

class TestGetAccessToken:
    """Testes para obtenção de access token."""

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    @patch("api.routes.social_auth.decrypt_token")
    @patch("api.routes.social_auth.settings")
    async def test_get_token_valid(
        self, mock_settings, mock_decrypt, mock_get_redis, mock_redis, mock_user
    ):
        """Testa obtenção de token válido."""
        from api.routes.social_auth import get_access_token
        
        mock_settings.JWT_SECRET_KEY = "test_secret"
        
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        stored_data = {
            "access_token": "encrypted_token",
            "token_type": "Bearer",
            "expires_at": future.isoformat()
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(stored_data))
        mock_get_redis.return_value = mock_redis
        mock_decrypt.return_value = "decrypted_access_token"
        
        result = await get_access_token(
            platform="instagram",
            account_name="my_account",
            current_user=mock_user
        )
        
        assert result["access_token"] == "decrypted_access_token"
        assert result["token_type"] == "Bearer"

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    async def test_get_token_not_found(self, mock_get_redis, mock_redis, mock_user):
        """Testa obtenção de token para conta inexistente."""
        from api.routes.social_auth import get_access_token
        from fastapi import HTTPException
        
        mock_redis.get = AsyncMock(return_value=None)
        mock_get_redis.return_value = mock_redis
        
        with pytest.raises(HTTPException) as exc:
            await get_access_token(
                platform="instagram",
                account_name="nonexistent",
                current_user=mock_user
            )
        
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.get_redis")
    @patch("api.routes.social_auth.decrypt_token")
    @patch("api.routes.social_auth.refresh_token")
    @patch("api.routes.social_auth.settings")
    async def test_get_token_auto_refresh(
        self, mock_settings, mock_refresh, mock_decrypt, 
        mock_get_redis, mock_redis, mock_user
    ):
        """Testa auto-refresh de token prestes a expirar."""
        from api.routes.social_auth import get_access_token
        
        mock_settings.JWT_SECRET_KEY = "test_secret"
        
        # Token expira em 2 minutos (dentro do threshold de 5 min)
        soon = datetime.now(timezone.utc) + timedelta(minutes=2)
        stored_data = {
            "access_token": "old_encrypted",
            "refresh_token": "encrypted_refresh",
            "token_type": "Bearer",
            "expires_at": soon.isoformat()
        }
        
        # Após refresh, dados atualizados
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        refreshed_data = {
            "access_token": "new_encrypted",
            "token_type": "Bearer",
            "expires_at": future.isoformat()
        }
        
        mock_redis.get = AsyncMock(
            side_effect=[json.dumps(stored_data), json.dumps(refreshed_data)]
        )
        mock_get_redis.return_value = mock_redis
        mock_decrypt.return_value = "new_access_token"
        mock_refresh.return_value = {"status": "refreshed"}
        
        result = await get_access_token(
            platform="instagram",
            account_name="my_account",
            current_user=mock_user
        )
        
        # Verifica que refresh foi chamado
        mock_refresh.assert_called_once()
        assert result["access_token"] == "new_access_token"


# ==================== TEST LIST PLATFORMS ====================

class TestListPlatforms:
    """Testes para listagem de plataformas."""

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.settings")
    async def test_list_platforms_all_configured(self, mock_settings):
        """Testa listagem com todas plataformas configuradas."""
        from api.routes.social_auth import list_platforms
        
        mock_settings.INSTAGRAM_CLIENT_ID = "instagram_client"
        mock_settings.TIKTOK_CLIENT_KEY = "tiktok_client"
        mock_settings.TIKTOK_SHOP_APP_KEY = "tiktok_shop_client"
        mock_settings.GOOGLE_CLIENT_ID = "google_client"
        
        result = await list_platforms()
        
        assert "platforms" in result
        platforms = {p["name"]: p for p in result["platforms"]}
        
        assert "instagram" in platforms
        assert "tiktok" in platforms
        assert "youtube" in platforms

    @pytest.mark.asyncio
    @patch("api.routes.social_auth.settings")
    async def test_list_platforms_some_not_configured(self, mock_settings):
        """Testa listagem com algumas plataformas não configuradas."""
        from api.routes.social_auth import list_platforms
        
        mock_settings.INSTAGRAM_CLIENT_ID = "instagram_client"
        mock_settings.TIKTOK_CLIENT_KEY = None
        mock_settings.TIKTOK_SHOP_APP_KEY = None
        mock_settings.GOOGLE_CLIENT_ID = None
        
        result = await list_platforms()
        
        platforms = {p["name"]: p for p in result["platforms"]}
        
        assert platforms["instagram"]["configured"] is True
        assert platforms["tiktok"]["configured"] is False
        assert platforms["youtube"]["configured"] is False


# ==================== TEST SCHEMAS ====================

class TestSchemas:
    """Testes para schemas Pydantic."""

    def test_oauth_init_request_minimal(self):
        """Testa OAuthInitRequest com campos mínimos."""
        from api.routes.social_auth import OAuthInitRequest
        
        request = OAuthInitRequest(
            platform="instagram",
            account_name="my_account"
        )
        
        assert request.platform == "instagram"
        assert request.account_name == "my_account"
        assert request.scopes is None

    def test_oauth_init_request_with_scopes(self):
        """Testa OAuthInitRequest com scopes."""
        from api.routes.social_auth import OAuthInitRequest
        
        request = OAuthInitRequest(
            platform="instagram",
            account_name="my_account",
            scopes=["user_profile", "user_media"]
        )
        
        assert len(request.scopes) == 2

    def test_token_refresh_request(self):
        """Testa TokenRefreshRequest."""
        from api.routes.social_auth import TokenRefreshRequest
        
        request = TokenRefreshRequest(
            platform="youtube",
            account_name="my_channel"
        )
        
        assert request.platform == "youtube"

    def test_connected_account(self):
        """Testa ConnectedAccount."""
        from api.routes.social_auth import ConnectedAccount
        
        now = datetime.now(timezone.utc)
        
        account = ConnectedAccount(
            platform="tiktok",
            account_name="my_tiktok",
            username="@myuser",
            connected_at=now,
            expires_at=now + timedelta(hours=1),
            status="active"
        )
        
        assert account.platform == "tiktok"
        assert account.username == "@myuser"
        assert account.status == "active"

    def test_oauth_callback_data(self):
        """Testa OAuthCallbackData."""
        from api.routes.social_auth import OAuthCallbackData
        
        data = OAuthCallbackData(
            code="auth_code_123",
            state="state_token"
        )
        
        assert data.code == "auth_code_123"
        assert data.state == "state_token"
