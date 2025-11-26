"""
Authentication Service Unit Tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from api.services.auth import AuthService


class TestAuthService:
    """Tests for AuthService class"""

    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance for testing."""
        with patch("api.services.auth.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test-secret-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            return AuthService()

    # ============================================
    # PASSWORD HASHING TESTS
    # ============================================

    @pytest.mark.unit
    def test_hash_password_returns_hash(self, auth_service):
        """Should return a hashed password."""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    @pytest.mark.unit
    def test_hash_password_different_for_same_input(self, auth_service):
        """Same password should generate different hashes (salt)."""
        password = "test_password_123"
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)

        # Different hashes due to salt
        assert hash1 != hash2

    @pytest.mark.unit
    def test_verify_password_correct(self, auth_service):
        """Should verify correct password."""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True

    @pytest.mark.unit
    def test_verify_password_incorrect(self, auth_service):
        """Should reject incorrect password."""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password("wrong_password", hashed) is False

    # ============================================
    # AUTHENTICATION TESTS
    # ============================================

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_authenticate_valid_credentials(self, auth_service, mock_db, mock_user_data):
        """Should authenticate user with valid credentials."""
        mock_db.fetch_one.return_value = {
            **mock_user_data,
            "password_hash": auth_service.hash_password("correct_password")
        }

        with patch("api.services.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db

            result = await auth_service.authenticate("test@example.com", "correct_password")

            assert result is not None
            assert result["email"] == "test@example.com"
            assert "id" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_authenticate_invalid_password(self, auth_service, mock_db, mock_user_data):
        """Should return None for invalid password."""
        mock_db.fetch_one.return_value = {
            **mock_user_data,
            "password_hash": auth_service.hash_password("correct_password")
        }

        with patch("api.services.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db

            result = await auth_service.authenticate("test@example.com", "wrong_password")

            assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_db):
        """Should return None for non-existent user."""
        mock_db.fetch_one.return_value = None

        with patch("api.services.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db

            result = await auth_service.authenticate("nonexistent@example.com", "password")

            assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, auth_service, mock_db, mock_user_data):
        """Should return None for inactive user."""
        mock_user_data["is_active"] = False
        mock_db.fetch_one.return_value = mock_user_data

        with patch("api.services.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db

            result = await auth_service.authenticate("test@example.com", "password")

            assert result is None

    # ============================================
    # HWID VALIDATION TESTS
    # ============================================

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_hwid_first_device(self, auth_service, mock_db, mock_license_data):
        """Should allow first device registration."""
        # License exists but no devices
        mock_db.fetch_one.side_effect = [
            mock_license_data,  # License query
            None,  # Device query (no existing device)
            {"count": 0}  # Device count query
        ]

        with patch("api.services.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db

            result = await auth_service.validate_hwid("user-123", "new-hwid")

            assert result is True
            # Should have called execute to insert new device
            assert mock_db.execute.called

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_hwid_existing_device(self, auth_service, mock_db, mock_license_data):
        """Should allow existing registered device."""
        mock_db.fetch_one.side_effect = [
            mock_license_data,  # License query
            {"id": "device-123"}  # Device exists
        ]

        with patch("api.services.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db

            result = await auth_service.validate_hwid("user-123", "existing-hwid")

            assert result is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_hwid_max_devices_reached(self, auth_service, mock_db, mock_license_data):
        """Should reject when max devices reached."""
        mock_license_data["max_devices"] = 2
        mock_db.fetch_one.side_effect = [
            mock_license_data,  # License query
            None,  # Device query (no existing device)
            {"count": 2}  # Device count at max
        ]

        with patch("api.services.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db

            result = await auth_service.validate_hwid("user-123", "new-device")

            assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_hwid_no_license(self, auth_service, mock_db):
        """Should allow access with no license (free tier)."""
        mock_db.fetch_one.return_value = None  # No license

        with patch("api.services.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db

            result = await auth_service.validate_hwid("user-123", "any-hwid")

            assert result is True

    # ============================================
    # USER CREATION TESTS
    # ============================================

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_user_success(self, auth_service, mock_db):
        """Should create new user successfully."""
        mock_db.fetch_one.return_value = {
            "id": "new-user-123",
            "email": "new@example.com",
            "name": "New User",
            "plan": "free"
        }

        with patch("api.services.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db

            result = await auth_service.create_user(
                email="new@example.com",
                password="secure_password",
                name="New User"
            )

            assert result["email"] == "new@example.com"
            assert result["plan"] == "free"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_user_password_is_hashed(self, auth_service, mock_db):
        """Should hash password when creating user."""
        mock_db.fetch_one.return_value = {
            "id": "new-user-123",
            "email": "new@example.com",
            "name": "New User",
            "plan": "free"
        }

        with patch("api.services.auth.get_db") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db

            await auth_service.create_user(
                email="new@example.com",
                password="plain_password",
                name="New User"
            )

            # Verify password was hashed (not stored as plain text)
            call_args = mock_db.fetch_one.call_args
            # The password_hash should not be the plain password
            assert "plain_password" not in str(call_args)

    # ============================================
    # TOKEN TESTS
    # ============================================

    @pytest.mark.unit
    def test_create_token_valid(self, auth_service):
        """Should create valid JWT token."""
        user_id = "user-123"
        hwid = "test-hwid"
        expires_at = datetime.utcnow() + timedelta(hours=12)

        token = auth_service.create_token(user_id, hwid, expires_at)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.unit
    def test_create_token_includes_claims(self, auth_service):
        """Token should include required claims."""
        from jose import jwt

        user_id = "user-123"
        hwid = "test-hwid"
        expires_at = datetime.utcnow() + timedelta(hours=12)

        token = auth_service.create_token(user_id, hwid, expires_at)

        # Decode and verify claims
        payload = jwt.decode(
            token,
            "test-secret-key",
            algorithms=["HS256"]
        )

        assert payload["sub"] == user_id
        assert payload["hwid"] == hwid
        assert "exp" in payload

    # ============================================
    # EDGE CASES
    # ============================================

    @pytest.mark.unit
    def test_verify_empty_password(self, auth_service):
        """Should handle empty password verification."""
        hashed = auth_service.hash_password("test")

        assert auth_service.verify_password("", hashed) is False

    @pytest.mark.unit
    def test_hash_unicode_password(self, auth_service):
        """Should handle unicode characters in password."""
        password = "пароль123密码"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True

    @pytest.mark.unit
    def test_hash_very_long_password(self, auth_service):
        """Should handle very long passwords."""
        password = "a" * 1000
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True
