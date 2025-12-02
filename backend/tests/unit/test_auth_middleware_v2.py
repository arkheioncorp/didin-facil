"""
Testes para Auth Middleware
===========================
Cobertura completa para api/middleware/auth.py
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# ==================== FIXTURES ====================

@pytest.fixture
def valid_user():
    """Usuário válido para testes."""
    return {
        "id": str(uuid4()),
        "email": "user@test.com",
        "name": "Test User",
        "plan": "free",
        "is_admin": False,
        "credits_balance": 100,
    }


@pytest.fixture
def admin_user():
    """Usuário admin para testes."""
    return {
        "id": str(uuid4()),
        "email": "admin@test.com",
        "name": "Admin User",
        "plan": "premium",
        "is_admin": True,
        "credits_balance": 1000,
    }


@pytest.fixture
def jwt_secret():
    """Secret para JWT."""
    return "test-secret-key-for-testing"


@pytest.fixture
def valid_token(valid_user, jwt_secret):
    """Token JWT válido."""
    payload = {
        "sub": valid_user["id"],
        "hwid": "test-hwid-123",
        "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        "iat": datetime.now(timezone.utc).timestamp(),
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


@pytest.fixture
def admin_token(admin_user, jwt_secret):
    """Token JWT de admin válido."""
    payload = {
        "sub": admin_user["id"],
        "hwid": "admin-hwid-123",
        "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        "iat": datetime.now(timezone.utc).timestamp(),
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


@pytest.fixture
def expired_token(valid_user, jwt_secret):
    """Token JWT expirado."""
    payload = {
        "sub": valid_user["id"],
        "hwid": "test-hwid-123",
        "exp": (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp(),
        "iat": (datetime.now(timezone.utc) - timedelta(hours=2)).timestamp(),
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


# ==================== GET CURRENT USER TESTS ====================

class TestGetCurrentUser:
    """Testes do get_current_user."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, valid_user, jwt_secret):
        """Testa autenticação bem sucedida."""
        payload = {
            "sub": valid_user["id"],
            "hwid": "test-hwid-123",
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
            "iat": datetime.now(timezone.utc).timestamp(),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret), \
             patch("api.middleware.auth.get_user_by_id",
                   new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = valid_user

            from api.middleware.auth import get_current_user

            result = await get_current_user(credentials)

            assert result["id"] == valid_user["id"]
            assert result["email"] == valid_user["email"]

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, jwt_secret):
        """Testa token inválido."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid-token"
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret):
            from api.middleware.auth import get_current_user

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)

            assert exc_info.value.status_code == 401
            assert "Invalid token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_missing_sub(self, jwt_secret):
        """Testa token sem subject."""
        payload = {
            "hwid": "test-hwid-123",
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret):
            from api.middleware.auth import get_current_user

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)

            assert exc_info.value.status_code == 401
            assert "Invalid token payload" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(
        self, valid_user, jwt_secret
    ):
        """Testa token expirado."""
        payload = {
            "sub": valid_user["id"],
            "hwid": "test-hwid-123",
            "exp": (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp(),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret), \
             patch("api.middleware.auth.get_user_by_id",
                   new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = valid_user

            from api.middleware.auth import get_current_user

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)

            assert exc_info.value.status_code == 401
            assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, jwt_secret):
        """Testa usuário não encontrado."""
        user_id = str(uuid4())
        payload = {
            "sub": user_id,
            "hwid": "test-hwid-123",
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret), \
             patch("api.middleware.auth.get_user_by_id",
                   new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = None

            from api.middleware.auth import get_current_user

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)

            assert exc_info.value.status_code == 401
            assert "User not found" in exc_info.value.detail


# ==================== REQUIRE ADMIN TESTS ====================

class TestRequireAdmin:
    """Testes do require_admin."""

    @pytest.mark.asyncio
    async def test_require_admin_success(self, admin_user, jwt_secret):
        """Testa autenticação admin bem sucedida."""
        payload = {
            "sub": admin_user["id"],
            "hwid": "admin-hwid-123",
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
            "iat": datetime.now(timezone.utc).timestamp(),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret), \
             patch("api.middleware.auth.get_user_by_id",
                   new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = admin_user

            from api.middleware.auth import require_admin

            result = await require_admin(credentials)

            assert result["id"] == admin_user["id"]
            assert result["is_admin"] is True

    @pytest.mark.asyncio
    async def test_require_admin_not_admin(self, valid_user, jwt_secret):
        """Testa usuário não-admin tentando acessar admin."""
        payload = {
            "sub": valid_user["id"],
            "hwid": "test-hwid-123",
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret), \
             patch("api.middleware.auth.get_user_by_id",
                   new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = valid_user

            from api.middleware.auth import require_admin

            with pytest.raises(HTTPException) as exc_info:
                await require_admin(credentials)

            assert exc_info.value.status_code == 403
            assert "Admin access required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_admin_invalid_token(self, jwt_secret):
        """Testa token inválido para admin."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid-token"
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret):
            from api.middleware.auth import require_admin

            with pytest.raises(HTTPException) as exc_info:
                await require_admin(credentials)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_require_admin_user_not_found(self, jwt_secret):
        """Testa admin com usuário não encontrado."""
        user_id = str(uuid4())
        payload = {
            "sub": user_id,
            "hwid": "test-hwid-123",
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret), \
             patch("api.middleware.auth.get_user_by_id",
                   new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = None

            from api.middleware.auth import require_admin

            with pytest.raises(HTTPException) as exc_info:
                await require_admin(credentials)

            assert exc_info.value.status_code == 401


# ==================== GET CURRENT USER OPTIONAL TESTS ====================

class TestGetCurrentUserOptional:
    """Testes do get_current_user_optional."""

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_credentials(
        self, valid_user, jwt_secret
    ):
        """Testa autenticação opcional com credenciais."""
        payload = {
            "sub": valid_user["id"],
            "hwid": "test-hwid-123",
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret), \
             patch("api.middleware.auth.get_user_by_id",
                   new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = valid_user

            from api.middleware.auth import get_current_user_optional

            result = await get_current_user_optional(credentials)

            assert result is not None
            assert result["id"] == valid_user["id"]

    @pytest.mark.asyncio
    async def test_get_current_user_optional_no_credentials(self):
        """Testa autenticação opcional sem credenciais."""
        from api.middleware.auth import get_current_user_optional

        result = await get_current_user_optional(None)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_invalid_token(self, jwt_secret):
        """Testa autenticação opcional com token inválido."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid-token"
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret):
            from api.middleware.auth import get_current_user_optional

            result = await get_current_user_optional(credentials)

            assert result is None


# ==================== CREATE ACCESS TOKEN TESTS ====================

class TestCreateAccessToken:
    """Testes do create_access_token."""

    def test_create_access_token_success(self, jwt_secret):
        """Testa criação de token."""
        user_id = str(uuid4())
        hwid = "test-hwid-123"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret):
            from api.middleware.auth import create_access_token

            token = create_access_token(user_id, hwid, expires_at)

            assert isinstance(token, str)
            assert len(token) > 0

            # Decodificar e verificar
            payload = jwt.decode(
                token, jwt_secret, algorithms=["HS256"]
            )
            assert payload["sub"] == user_id
            assert payload["hwid"] == hwid

    def test_create_access_token_contains_expiration(self, jwt_secret):
        """Testa que token contém expiração."""
        user_id = str(uuid4())
        hwid = "test-hwid"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret):
            from api.middleware.auth import create_access_token

            token = create_access_token(user_id, hwid, expires_at)

            payload = jwt.decode(
                token, jwt_secret, algorithms=["HS256"]
            )
            assert "exp" in payload
            assert "iat" in payload

    def test_create_access_token_different_users(self, jwt_secret):
        """Testa tokens diferentes para usuários diferentes."""
        user1_id = str(uuid4())
        user2_id = str(uuid4())
        hwid = "test-hwid"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret):
            from api.middleware.auth import create_access_token

            token1 = create_access_token(user1_id, hwid, expires_at)
            token2 = create_access_token(user2_id, hwid, expires_at)

            assert token1 != token2


# ==================== EDGE CASES ====================

class TestEdgeCases:
    """Testes de casos extremos."""

    @pytest.mark.asyncio
    async def test_token_without_expiration(self, valid_user, jwt_secret):
        """Testa token sem campo exp (ainda válido)."""
        payload = {
            "sub": valid_user["id"],
            "hwid": "test-hwid-123",
            # Sem exp
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret), \
             patch("api.middleware.auth.get_user_by_id",
                   new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = valid_user

            from api.middleware.auth import get_current_user

            result = await get_current_user(credentials)

            # Token sem exp deve funcionar
            assert result["id"] == valid_user["id"]

    @pytest.mark.asyncio
    async def test_token_with_extra_claims(self, valid_user, jwt_secret):
        """Testa token com claims extras."""
        payload = {
            "sub": valid_user["id"],
            "hwid": "test-hwid-123",
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
            "extra_claim": "extra_value",
            "role": "user",
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret), \
             patch("api.middleware.auth.get_user_by_id",
                   new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = valid_user

            from api.middleware.auth import get_current_user

            result = await get_current_user(credentials)

            assert result["id"] == valid_user["id"]

    @pytest.mark.asyncio
    async def test_hwid_in_response(self, valid_user, jwt_secret):
        """Testa que hwid é incluído na resposta."""
        hwid = "specific-hwid-value"
        payload = {
            "sub": valid_user["id"],
            "hwid": hwid,
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret), \
             patch("api.middleware.auth.get_user_by_id",
                   new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = valid_user

            from api.middleware.auth import get_current_user

            result = await get_current_user(credentials)

            assert result["hwid"] == hwid

    @pytest.mark.asyncio
    async def test_admin_returns_correct_fields(self, admin_user, jwt_secret):
        """Testa campos retornados para admin."""
        payload = {
            "sub": admin_user["id"],
            "hwid": "admin-hwid",
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret), \
             patch("api.middleware.auth.get_user_by_id",
                   new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = admin_user

            from api.middleware.auth import require_admin

            result = await require_admin(credentials)

            assert "id" in result
            assert "email" in result
            assert "name" in result
            assert result["is_admin"] is True
            assert "hwid" in result

    @pytest.mark.asyncio
    async def test_wrong_algorithm_token(self, valid_user, jwt_secret):
        """Testa token com algoritmo diferente."""
        # Criar token com algoritmo diferente
        payload = {
            "sub": valid_user["id"],
            "hwid": "test-hwid",
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        }
        # Usar HS384 em vez de HS256
        token = jwt.encode(payload, jwt_secret, algorithm="HS384")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        with patch("api.middleware.auth.JWT_SECRET_KEY", jwt_secret):
            from api.middleware.auth import get_current_user

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)

            assert exc_info.value.status_code == 401
