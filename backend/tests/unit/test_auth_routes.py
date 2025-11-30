"""
Tests for api/routes/auth.py
JWT authentication routes testing
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jose import jwt

# Import route functions directly
from api.routes.auth import (
    router,
    login,
    register,
    refresh_token,
    get_current_user_info,
    logout,
    verify_email,
    forgot_password,
    reset_password,
    LoginRequest,
    RegisterRequest,
    RefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_auth_service():
    """Mock AuthService."""
    with patch("api.routes.auth.AuthService") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


@pytest.fixture
def mock_user():
    """Sample authenticated user."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "name": "Test User",
        "plan": "premium",
    }


@pytest.fixture
def login_request():
    """Sample login request."""
    return LoginRequest(
        email="test@example.com",
        password="SecurePass123!",
        hwid="hwid-abc-123"
    )


@pytest.fixture
def register_request():
    """Sample register request."""
    return RegisterRequest(
        email="newuser@example.com",
        password="NewPass123!",
        name="New User"
    )


@pytest.fixture
def valid_jwt_token():
    """Generate a valid JWT token."""
    expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
    payload = {
        "sub": "user-123",
        "hwid": "hwid-abc-123",
        "exp": expires_at
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# ==================== LOGIN TESTS ====================

class TestLogin:
    """Tests for login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, mock_auth_service, login_request, mock_user):
        """Test successful login."""
        mock_auth_service.authenticate = AsyncMock(return_value=mock_user)
        mock_auth_service.validate_hwid = AsyncMock(return_value=True)
        mock_auth_service.create_token = MagicMock(return_value="jwt-token-123")

        response = await login(login_request)

        assert response.access_token == "jwt-token-123"
        assert response.token_type == "bearer"
        assert response.user["id"] == mock_user["id"]
        assert response.user["email"] == mock_user["email"]
        mock_auth_service.authenticate.assert_awaited_once_with(
            login_request.email, login_request.password
        )

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_auth_service, login_request):
        """Test login with invalid credentials."""
        mock_auth_service.authenticate = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await login(login_request)

        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_hwid_mismatch(self, mock_auth_service, login_request, mock_user):
        """Test login with HWID bound to another device."""
        mock_auth_service.authenticate = AsyncMock(return_value=mock_user)
        mock_auth_service.validate_hwid = AsyncMock(return_value=False)

        with pytest.raises(HTTPException) as exc_info:
            await login(login_request)

        assert exc_info.value.status_code == 403
        assert "bound to another device" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_login_returns_user_info(self, mock_auth_service, login_request, mock_user):
        """Test login returns correct user information."""
        mock_auth_service.authenticate = AsyncMock(return_value=mock_user)
        mock_auth_service.validate_hwid = AsyncMock(return_value=True)
        mock_auth_service.create_token = MagicMock(return_value="token")

        response = await login(login_request)

        assert response.user["name"] == "Test User"
        assert response.user["plan"] == "premium"


# ==================== REGISTER TESTS ====================

class TestRegister:
    """Tests for register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, mock_auth_service, register_request):
        """Test successful registration."""
        mock_auth_service.get_user_by_email = AsyncMock(return_value=None)
        mock_auth_service.create_user = AsyncMock(return_value={"id": "new-user-id"})

        response = await register(register_request)

        assert response["message"] == "User created successfully"
        assert response["user_id"] == "new-user-id"
        mock_auth_service.create_user.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_email_already_exists(self, mock_auth_service, register_request):
        """Test registration with existing email."""
        mock_auth_service.get_user_by_email = AsyncMock(
            return_value={"id": "existing-user"}
        )

        with pytest.raises(HTTPException) as exc_info:
            await register(register_request)

        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_register_creates_with_correct_data(self, mock_auth_service, register_request):
        """Test registration creates user with correct data."""
        mock_auth_service.get_user_by_email = AsyncMock(return_value=None)
        mock_auth_service.create_user = AsyncMock(return_value={"id": "user-123"})

        await register(register_request)

        mock_auth_service.create_user.assert_awaited_once_with(
            email=register_request.email,
            password=register_request.password,
            name=register_request.name
        )


# ==================== REFRESH TOKEN TESTS ====================

class TestRefreshToken:
    """Tests for token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_success(self, mock_auth_service, mock_user, valid_jwt_token):
        """Test successful token refresh."""
        mock_auth_service.get_user_by_id = AsyncMock(return_value=mock_user)
        mock_auth_service.create_token = MagicMock(return_value="new-token-456")

        # Create credentials mock
        credentials = MagicMock()
        credentials.credentials = valid_jwt_token

        request = RefreshRequest(hwid="hwid-abc-123")
        response = await refresh_token(request, credentials)

        assert response.access_token == "new-token-456"
        assert response.user["id"] == mock_user["id"]

    @pytest.mark.asyncio
    async def test_refresh_hwid_mismatch(self, mock_auth_service, valid_jwt_token):
        """Test refresh with mismatched HWID."""
        credentials = MagicMock()
        credentials.credentials = valid_jwt_token

        request = RefreshRequest(hwid="different-hwid")

        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(request, credentials)

        assert exc_info.value.status_code == 403
        assert "HWID mismatch" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_user_not_found(self, mock_auth_service, valid_jwt_token):
        """Test refresh when user no longer exists."""
        mock_auth_service.get_user_by_id = AsyncMock(return_value=None)

        credentials = MagicMock()
        credentials.credentials = valid_jwt_token

        request = RefreshRequest(hwid="hwid-abc-123")

        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(request, credentials)

        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, mock_auth_service):
        """Test refresh with invalid token."""
        credentials = MagicMock()
        credentials.credentials = "invalid-token"

        request = RefreshRequest(hwid="hwid-abc-123")

        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(request, credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)


# ==================== GET CURRENT USER TESTS ====================

class TestGetCurrentUser:
    """Tests for get current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_user):
        """Test getting current user info."""
        response = await get_current_user_info(user=mock_user)

        assert response == mock_user
        assert response["id"] == "user-123"
        assert response["email"] == "test@example.com"


# ==================== LOGOUT TESTS ====================

class TestLogout:
    """Tests for logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(self, mock_user):
        """Test successful logout."""
        response = await logout(user=mock_user)

        assert response["message"] == "Logged out successfully"


# ==================== VERIFY EMAIL TESTS ====================

class TestVerifyEmail:
    """Tests for email verification endpoint."""

    @pytest.mark.asyncio
    async def test_verify_email_success(self):
        """Test email verification."""
        response = await verify_email(token="verification-token-123")

        assert response["message"] == "Email verified successfully"


# ==================== FORGOT PASSWORD TESTS ====================

class TestForgotPassword:
    """Tests for forgot password endpoint."""

    @pytest.mark.asyncio
    async def test_forgot_password_success(self):
        """Test forgot password request."""
        request = ForgotPasswordRequest(email="user@example.com")
        response = await forgot_password(request)

        assert response["message"] == "Password reset email sent"


# ==================== RESET PASSWORD TESTS ====================

class TestResetPassword:
    """Tests for reset password endpoint."""

    @pytest.mark.asyncio
    async def test_reset_password_success(self):
        """Test successful password reset."""
        request = ResetPasswordRequest(
            token="reset-token-123",
            new_password="NewSecurePass123!",
            confirm_password="NewSecurePass123!"
        )
        response = await reset_password(request)

        assert response["message"] == "Password reset successfully"

    @pytest.mark.asyncio
    async def test_reset_password_mismatch(self):
        """Test password reset with mismatched passwords."""
        request = ResetPasswordRequest(
            token="reset-token-123",
            new_password="Password1",
            confirm_password="Password2"
        )

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(request)

        assert exc_info.value.status_code == 400
        assert "Passwords do not match" in str(exc_info.value.detail)


# ==================== MODEL VALIDATION TESTS ====================

class TestModels:
    """Tests for Pydantic models."""

    def test_login_request_validation(self):
        """Test LoginRequest model validation."""
        request = LoginRequest(
            email="test@example.com",
            password="password123",
            hwid="hwid-123"
        )
        assert request.email == "test@example.com"
        assert request.hwid == "hwid-123"

    def test_register_request_validation(self):
        """Test RegisterRequest model validation."""
        request = RegisterRequest(
            email="new@example.com",
            password="securepass",
            name="John Doe"
        )
        assert request.name == "John Doe"

    def test_refresh_request_validation(self):
        """Test RefreshRequest model validation."""
        request = RefreshRequest(hwid="device-hwid")
        assert request.hwid == "device-hwid"

    def test_forgot_password_request_validation(self):
        """Test ForgotPasswordRequest model validation."""
        request = ForgotPasswordRequest(email="forgot@example.com")
        assert request.email == "forgot@example.com"

    def test_reset_password_request_validation(self):
        """Test ResetPasswordRequest model validation."""
        request = ResetPasswordRequest(
            token="token123",
            new_password="newpass",
            confirm_password="newpass"
        )
        assert request.token == "token123"


# ==================== INTEGRATION TESTS ====================

class TestRouterIntegration:
    """Integration tests using TestClient."""

    def test_router_has_all_endpoints(self):
        """Verify router has all expected endpoints."""
        routes = [r.path for r in router.routes]
        
        assert "/login" in routes
        assert "/register" in routes
        assert "/refresh" in routes
        assert "/me" in routes
        assert "/logout" in routes
        assert "/verify-email" in routes
        assert "/forgot-password" in routes
        assert "/reset-password" in routes
