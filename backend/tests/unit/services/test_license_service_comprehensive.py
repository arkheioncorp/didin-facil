"""
Comprehensive tests for LicenseService
Tests for license management, validation, and device registration
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestLicenseServiceInit:
    """Tests for LicenseService initialization"""

    def test_init_sets_attributes(self):
        """Test LicenseService initializes correctly"""
        with patch("api.services.license.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            mock_settings.JWT_ALGORITHM = "HS256"

            from api.services.license import LicenseService

            service = LicenseService()

            assert service.secret_key == "test_secret"
            assert service.algorithm == "HS256"


class TestLicenseServiceGetLicense:
    """Tests for license retrieval methods"""

    @pytest.fixture
    def license_service(self):
        with patch("api.services.license.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            mock_settings.JWT_ALGORITHM = "HS256"

            with patch("api.services.license.database") as mock_db:
                from api.services.license import LicenseService

                service = LicenseService()
                service.db = mock_db
                yield service

    @pytest.mark.asyncio
    async def test_get_license_by_email_found(self, license_service):
        """Test getting license by email when exists"""
        mock_license = {
            "id": str(uuid.uuid4()),
            "license_key": "LIC-XXXX-XXXX-XXXX",
            "plan": "pro",
            "is_active": True,
            "email": "user@example.com",
            "name": "Test User",
        }
        license_service.db.fetch_one = AsyncMock(return_value=mock_license)

        result = await license_service.get_license_by_email("user@example.com")

        assert result is not None
        assert result["email"] == "user@example.com"
        assert result["plan"] == "pro"

    @pytest.mark.asyncio
    async def test_get_license_by_email_not_found(self, license_service):
        """Test getting license by email when not exists"""
        license_service.db.fetch_one = AsyncMock(return_value=None)

        result = await license_service.get_license_by_email("nobody@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_license_by_key_found(self, license_service):
        """Test getting license by key when exists"""
        mock_license = {
            "id": str(uuid.uuid4()),
            "license_key": "LIC-XXXX-XXXX-XXXX",
            "plan": "enterprise",
            "is_active": True,
        }
        license_service.db.fetch_one = AsyncMock(return_value=mock_license)

        result = await license_service.get_license_by_key("LIC-XXXX-XXXX-XXXX")

        assert result is not None
        assert result["license_key"] == "LIC-XXXX-XXXX-XXXX"

    @pytest.mark.asyncio
    async def test_get_license_by_key_not_found(self, license_service):
        """Test getting license by invalid key"""
        license_service.db.fetch_one = AsyncMock(return_value=None)

        result = await license_service.get_license_by_key("INVALID-KEY")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_license_by_user_found(self, license_service):
        """Test getting license by user ID"""
        user_id = str(uuid.uuid4())
        mock_license = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "license_key": "LIC-YYYY-YYYY-YYYY",
            "is_active": True,
        }
        license_service.db.fetch_one = AsyncMock(return_value=mock_license)

        result = await license_service.get_license_by_user(user_id)

        assert result is not None
        assert result["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_get_license_by_user_not_found(self, license_service):
        """Test getting license for user without license"""
        license_service.db.fetch_one = AsyncMock(return_value=None)

        result = await license_service.get_license_by_user("nonexistent_user")

        assert result is None


class TestLicenseServiceHWID:
    """Tests for HWID validation"""

    @pytest.fixture
    def license_service(self):
        with patch("api.services.license.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            mock_settings.JWT_ALGORITHM = "HS256"

            with patch("api.services.license.database") as mock_db:
                from api.services.license import LicenseService

                service = LicenseService()
                service.db = mock_db
                yield service

    @pytest.mark.asyncio
    async def test_validate_hwid_registered(self, license_service):
        """Test HWID validation for registered device"""
        license_service.db.fetch_one = AsyncMock(
            return_value={"id": str(uuid.uuid4())}
        )

        result = await license_service.validate_hwid("license_123", "hwid_abc")

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_hwid_not_registered(self, license_service):
        """Test HWID validation for unregistered device"""
        license_service.db.fetch_one = AsyncMock(return_value=None)

        result = await license_service.validate_hwid("license_123", "unknown_hwid")

        assert result is False


class TestLicenseServiceDevices:
    """Tests for device management"""

    @pytest.fixture
    def license_service(self):
        with patch("api.services.license.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            mock_settings.JWT_ALGORITHM = "HS256"

            with patch("api.services.license.database") as mock_db:
                from api.services.license import LicenseService

                service = LicenseService()
                service.db = mock_db
                yield service

    @pytest.mark.asyncio
    async def test_get_active_devices_found(self, license_service):
        """Test getting active devices for license"""
        mock_devices = [
            {
                "id": str(uuid.uuid4()),
                "hwid": "device_1",
                "first_seen_at": datetime.now(timezone.utc),
                "last_seen_at": datetime.now(timezone.utc),
            },
            {
                "id": str(uuid.uuid4()),
                "hwid": "device_2",
                "first_seen_at": datetime.now(timezone.utc),
                "last_seen_at": datetime.now(timezone.utc),
            },
        ]
        license_service.db.fetch_all = AsyncMock(return_value=mock_devices)

        result = await license_service.get_active_devices("license_123")

        assert len(result) == 2
        assert result[0]["hwid"] == "device_1"

    @pytest.mark.asyncio
    async def test_get_active_devices_empty(self, license_service):
        """Test getting devices when none registered"""
        license_service.db.fetch_all = AsyncMock(return_value=[])

        result = await license_service.get_active_devices("license_123")

        assert result == []

    @pytest.mark.asyncio
    async def test_register_device(self, license_service):
        """Test registering a new device"""
        license_service.db.execute = AsyncMock()

        await license_service.register_device(
            license_id="license_123",
            hwid="new_device_hwid",
            app_version="1.0.0",
        )

        license_service.db.execute.assert_called_once()


class TestLicenseServiceValidation:
    """Tests for license validation"""

    @pytest.fixture
    def license_service(self):
        with patch("api.services.license.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            mock_settings.JWT_ALGORITHM = "HS256"

            with patch("api.services.license.database") as mock_db:
                from api.services.license import LicenseService

                service = LicenseService()
                service.db = mock_db
                yield service

    @pytest.mark.asyncio
    async def test_validate_active_license(self, license_service):
        """Test validating an active license"""
        mock_license = {
            "id": str(uuid.uuid4()),
            "is_active": True,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
        }
        license_service.db.fetch_one = AsyncMock(return_value=mock_license)

        result = await license_service.get_license_by_key("valid_key")

        assert result is not None
        assert result["is_active"] is True

    @pytest.mark.asyncio
    async def test_validate_inactive_license(self, license_service):
        """Test that inactive licenses return from DB but can be checked"""
        # get_license_by_key doesn't filter by is_active
        mock_license = {
            "id": str(uuid.uuid4()),
            "is_active": False,
            "expires_at": datetime.now(timezone.utc) - timedelta(days=1),
        }
        license_service.db.fetch_one = AsyncMock(return_value=mock_license)

        result = await license_service.get_license_by_key("expired_key")

        # Returns the license, caller should check is_active
        assert result is not None
        assert result["is_active"] is False


class TestLicenseServiceTokens:
    """Tests for token generation"""

    @pytest.fixture
    def license_service(self):
        with patch("api.services.license.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "super_secret_key_12345"
            mock_settings.JWT_ALGORITHM = "HS256"

            with patch("api.services.license.database"):
                from api.services.license import LicenseService

                yield LicenseService()

    def test_token_attributes_set(self, license_service):
        """Test that token attributes are properly set"""
        assert license_service.secret_key == "super_secret_key_12345"
        assert license_service.algorithm == "HS256"


class TestLicenseServiceEdgeCases:
    """Edge cases and error handling"""

    @pytest.fixture
    def license_service(self):
        with patch("api.services.license.settings") as mock_settings:
            mock_settings.JWT_SECRET_KEY = "test_secret"
            mock_settings.JWT_ALGORITHM = "HS256"

            with patch("api.services.license.database") as mock_db:
                from api.services.license import LicenseService

                service = LicenseService()
                service.db = mock_db
                yield service

    @pytest.mark.asyncio
    async def test_database_error_handling(self, license_service):
        """Test handling of database errors"""
        license_service.db.fetch_one = AsyncMock(
            side_effect=Exception("Database error")
        )

        with pytest.raises(Exception, match="Database error"):
            await license_service.get_license_by_email("user@example.com")

    @pytest.mark.asyncio
    async def test_empty_email(self, license_service):
        """Test handling of empty email"""
        license_service.db.fetch_one = AsyncMock(return_value=None)

        result = await license_service.get_license_by_email("")

        assert result is None

    @pytest.mark.asyncio
    async def test_empty_license_key(self, license_service):
        """Test handling of empty license key"""
        license_service.db.fetch_one = AsyncMock(return_value=None)

        result = await license_service.get_license_by_key("")

        assert result is None

    @pytest.mark.asyncio
    async def test_special_characters_in_hwid(self, license_service):
        """Test HWID with special characters"""
        license_service.db.fetch_one = AsyncMock(return_value={"id": "123"})

        result = await license_service.validate_hwid(
            "license_123", "hwid:with:colons-and_underscores"
        )

        assert result is True
