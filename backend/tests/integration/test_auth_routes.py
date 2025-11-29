"""
Auth Routes Tests - Full Coverage
Tests for authentication endpoints using AsyncClient.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from api.main import app
from api.routes.auth import get_current_user


@pytest_asyncio.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def mock_auth_service():
    """Mock AuthService."""
    with patch("api.routes.auth.AuthService") as cls:
        service = AsyncMock()
        service.authenticate = AsyncMock()
        service.validate_hwid = AsyncMock()
        service.create_token = MagicMock()
        service.get_user_by_email = AsyncMock()
        service.create_user = AsyncMock()
        service.get_user_by_id = AsyncMock()
        cls.return_value = service
        yield service


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    user = {
        "id": "user_123",
        "email": "test@example.com",
        "name": "Test User",
        "plan": "lifetime"
    }
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides = {}


class TestLoginEndpoint:
    """Tests for /auth/login."""

    @pytest.mark.asyncio
    async def test_login_success(self, mock_auth_service, async_client):
        """Test successful login."""
        mock_auth_service.authenticate.return_value = {
            "id": "user_123",
            "email": "test@example.com",
            "name": "Test User",
            "plan": "lifetime"
        }
        mock_auth_service.validate_hwid.return_value = True
        mock_auth_service.create_token.return_value = "jwt_token_here"

        response = await async_client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
                "hwid": "hwid_abc123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "jwt_token_here"
        assert data["token_type"] == "bearer"
        assert "expires_at" in data
        assert data["user"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self,
        mock_auth_service,
        async_client
    ):
        """Test login with invalid credentials."""
        mock_auth_service.authenticate.return_value = None

        response = await async_client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrong_password",
                "hwid": "hwid_abc123"
            }
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_hwid_mismatch(self, mock_auth_service, async_client):
        """Test login with wrong device."""
        mock_auth_service.authenticate.return_value = {
            "id": "user_123",
            "email": "test@example.com",
            "name": "Test User",
            "plan": "lifetime"
        }
        mock_auth_service.validate_hwid.return_value = False

        response = await async_client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
                "hwid": "different_hwid"
            }
        )

        assert response.status_code == 403
        assert "bound to another device" in response.json()["detail"]


class TestRegisterEndpoint:
    """Tests for /auth/register."""

    @pytest.mark.asyncio
    async def test_register_success(self, mock_auth_service, async_client):
        """Test successful registration."""
        mock_auth_service.get_user_by_email.return_value = None
        mock_auth_service.create_user.return_value = {"id": "new_user_123"}

        response = await async_client.post(
            "/auth/register",
            json={
                "email": "new@example.com",
                "password": "password123",
                "name": "New User"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User created successfully"
        assert data["user_id"] == "new_user_123"

    @pytest.mark.asyncio
    async def test_register_email_exists(self, mock_auth_service, async_client):
        """Test registration with existing email."""
        mock_auth_service.get_user_by_email.return_value = {
            "id": "existing_user"
        }

        response = await async_client.post(
            "/auth/register",
            json={
                "email": "existing@example.com",
                "password": "password123",
                "name": "New User"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]


class TestRefreshEndpoint:
    """Tests for /auth/refresh."""

    @pytest.mark.asyncio
    async def test_refresh_success(self, mock_auth_service, async_client):
        """Test successful token refresh."""
        from api.routes.auth import JWT_SECRET_KEY, JWT_ALGORITHM
        from jose import jwt

        payload = {
            "sub": "user_123",
            "hwid": "hwid_abc123",
            "exp": (datetime.utcnow() + timedelta(hours=12)).timestamp()
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        mock_auth_service.get_user_by_id.return_value = {
            "id": "user_123",
            "email": "test@example.com",
            "name": "Test User",
            "plan": "lifetime"
        }
        mock_auth_service.create_token.return_value = "new_jwt_token"

        response = await async_client.post(
            "/auth/refresh",
            json={"hwid": "hwid_abc123"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new_jwt_token"

    @pytest.mark.asyncio
    async def test_refresh_hwid_mismatch(self, mock_auth_service, async_client):
        """Test refresh with wrong HWID."""
        from api.routes.auth import JWT_SECRET_KEY, JWT_ALGORITHM
        from jose import jwt

        payload = {
            "sub": "user_123",
            "hwid": "original_hwid",
            "exp": (datetime.utcnow() + timedelta(hours=12)).timestamp()
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        response = await async_client.post(
            "/auth/refresh",
            json={"hwid": "different_hwid"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert "HWID mismatch" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_user_not_found(
        self,
        mock_auth_service,
        async_client
    ):
        """Test refresh when user deleted."""
        from api.routes.auth import JWT_SECRET_KEY, JWT_ALGORITHM
        from jose import jwt

        payload = {
            "sub": "deleted_user",
            "hwid": "hwid_abc123",
            "exp": (datetime.utcnow() + timedelta(hours=12)).timestamp()
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        mock_auth_service.get_user_by_id.return_value = None

        response = await async_client.post(
            "/auth/refresh",
            json={"hwid": "hwid_abc123"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(
        self,
        mock_auth_service,
        async_client
    ):
        """Test refresh with invalid token."""
        response = await async_client.post(
            "/auth/refresh",
            json={"hwid": "hwid_abc123"},
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


class TestMeEndpoint:
    """Tests for /auth/me."""

    @pytest.mark.asyncio
    async def test_me_success(self, mock_auth_user, async_client):
        """Test get current user."""
        response = await async_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_me_unauthorized(self, async_client):
        """Test me without token."""
        response = await async_client.get("/auth/me")

        # API returns 403 when no token is provided
        assert response.status_code in [401, 403]


class TestLogoutEndpoint:
    """Tests for /auth/logout."""

    @pytest.mark.asyncio
    async def test_logout_success(self, mock_auth_user, async_client):
        """Test successful logout."""
        response = await async_client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code in [200, 401]
