"""
Tests for License Routes (Extended Coverage)
Tests for license validation, activation, and management endpoints.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestLicenseModels:
    """Tests for License Pydantic models"""

    def test_validate_license_request(self):
        """Test ValidateLicenseRequest model"""
        from api.routes.license import ValidateLicenseRequest

        request = ValidateLicenseRequest(
            email="test@example.com",
            hwid="abc123def456",
            app_version="1.0.0"
        )

        assert request.email == "test@example.com"
        assert request.hwid == "abc123def456"
        assert request.app_version == "1.0.0"

    def test_validate_license_response(self):
        """Test ValidateLicenseResponse model"""
        from api.routes.license import ValidateLicenseResponse

        response = ValidateLicenseResponse(
            valid=True,
            plan="pro",
            features={"products_per_day": 100},
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            jwt="test-jwt-token",
            jwt_expires_at=datetime.now(timezone.utc) + timedelta(hours=12)
        )

        assert response.valid is True
        assert response.plan == "pro"
        assert "products_per_day" in response.features

    def test_activate_license_request(self):
        """Test ActivateLicenseRequest model"""
        from api.routes.license import ActivateLicenseRequest

        request = ActivateLicenseRequest(
            license_key="DIDIN-XXXX-YYYY-ZZZZ",
            hwid="abc123def456",
            email="test@example.com"
        )

        assert request.license_key == "DIDIN-XXXX-YYYY-ZZZZ"
        assert request.hwid == "abc123def456"

    def test_deactivate_license_request(self):
        """Test DeactivateLicenseRequest model"""
        from api.routes.license import DeactivateLicenseRequest

        request = DeactivateLicenseRequest(
            hwid="abc123def456",
            reason="Changing device"
        )

        assert request.hwid == "abc123def456"
        assert request.reason == "Changing device"

    def test_deactivate_license_request_defaults(self):
        """Test DeactivateLicenseRequest default values"""
        from api.routes.license import DeactivateLicenseRequest

        request = DeactivateLicenseRequest(hwid="abc123")

        assert request.reason is None

    def test_plan_features(self):
        """Test PlanFeatures model"""
        from api.routes.license import PlanFeatures

        features = PlanFeatures(
            name="Pro",
            products_per_day=100,
            copies_per_month=500,
            favorites_limit=1000,
            export_formats=["csv", "excel", "json"],
            priority_support=True,
            api_access=True
        )

        assert features.name == "Pro"
        assert features.products_per_day == 100
        assert features.api_access is True


class TestValidateLicenseEndpoint:
    """Tests for validate_license endpoint"""

    @pytest.mark.asyncio
    async def test_validate_license_success(self):
        """Test successful license validation"""
        from api.routes.license import ValidateLicenseRequest, validate_license

        request = ValidateLicenseRequest(
            email="test@example.com",
            hwid="abc123",
            app_version="1.0.0"
        )

        mock_license_info = {
            "id": "license-123",
            "user_id": "user-123",
            "plan": "pro",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "activated_at": datetime.now(timezone.utc)
        }

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_license_by_email = AsyncMock(return_value=mock_license_info)
            mock_service.validate_hwid = AsyncMock(return_value=True)
            mock_service.create_license_jwt = MagicMock(return_value="jwt-token")
            mock_service.get_plan_features = MagicMock(return_value={"products_per_day": 100})

            result = await validate_license(request)

        assert result.valid is True
        assert result.plan == "pro"
        assert result.jwt == "jwt-token"

    @pytest.mark.asyncio
    async def test_validate_license_no_license(self):
        """Test validation with no license found"""
        from api.routes.license import ValidateLicenseRequest, validate_license

        request = ValidateLicenseRequest(
            email="noexist@example.com",
            hwid="abc123",
            app_version="1.0.0"
        )

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_license_by_email = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await validate_license(request)

            assert exc_info.value.status_code == 402
            assert "No active license" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_validate_license_expired(self):
        """Test validation with expired license"""
        from api.routes.license import ValidateLicenseRequest, validate_license

        request = ValidateLicenseRequest(
            email="test@example.com",
            hwid="abc123",
            app_version="1.0.0"
        )

        mock_license_info = {
            "id": "license-123",
            "user_id": "user-123",
            "plan": "pro",
            "expires_at": datetime.now(timezone.utc) - timedelta(days=1),  # Expired
            "activated_at": datetime.now(timezone.utc)
        }

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_license_by_email = AsyncMock(return_value=mock_license_info)

            with pytest.raises(HTTPException) as exc_info:
                await validate_license(request)

            assert exc_info.value.status_code == 402
            assert "expired" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_validate_license_naive_datetime(self):
        """Test validation with naive datetime from database"""
        from api.routes.license import ValidateLicenseRequest, validate_license

        request = ValidateLicenseRequest(
            email="test@example.com",
            hwid="abc123",
            app_version="1.0.0"
        )

        # Naive datetime (no timezone)
        mock_license_info = {
            "id": "license-123",
            "user_id": "user-123",
            "plan": "pro",
            "expires_at": datetime.now() + timedelta(days=30),  # Naive
            "activated_at": datetime.now()
        }

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_license_by_email = AsyncMock(return_value=mock_license_info)
            mock_service.validate_hwid = AsyncMock(return_value=True)
            mock_service.create_license_jwt = MagicMock(return_value="jwt-token")
            mock_service.get_plan_features = MagicMock(return_value={})

            result = await validate_license(request)

        assert result.valid is True

    @pytest.mark.asyncio
    async def test_validate_license_device_not_registered(self):
        """Test validation with unregistered device"""
        from api.routes.license import ValidateLicenseRequest, validate_license

        request = ValidateLicenseRequest(
            email="test@example.com",
            hwid="new-device-hwid",
            app_version="1.0.0"
        )

        mock_license_info = {
            "id": "license-123",
            "user_id": "user-123",
            "plan": "pro",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "activated_at": datetime.now(timezone.utc)
        }

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_license_by_email = AsyncMock(return_value=mock_license_info)
            mock_service.validate_hwid = AsyncMock(return_value=False)

            with pytest.raises(HTTPException) as exc_info:
                await validate_license(request)

            assert exc_info.value.status_code == 403
            assert "DEVICE_NOT_REGISTERED" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_license_no_expiration(self):
        """Test validation with no expiration date (lifetime license)"""
        from api.routes.license import ValidateLicenseRequest, validate_license

        request = ValidateLicenseRequest(
            email="test@example.com",
            hwid="abc123",
            app_version="1.0.0"
        )

        mock_license_info = {
            "id": "license-123",
            "user_id": "user-123",
            "plan": "enterprise",
            "expires_at": None,  # Lifetime license
            "activated_at": datetime.now(timezone.utc)
        }

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_license_by_email = AsyncMock(return_value=mock_license_info)
            mock_service.validate_hwid = AsyncMock(return_value=True)
            mock_service.create_license_jwt = MagicMock(return_value="jwt-token")
            mock_service.get_plan_features = MagicMock(return_value={})

            result = await validate_license(request)

        assert result.valid is True
        assert result.expires_at is None


class TestActivateLicenseEndpoint:
    """Tests for activate_license endpoint"""

    @pytest.mark.asyncio
    async def test_activate_license_first_time(self):
        """Test first time license activation"""
        from api.routes.license import ActivateLicenseRequest, activate_license

        request = ActivateLicenseRequest(
            license_key="DIDIN-XXXX-YYYY-ZZZZ",
            hwid="abc123",
            email="test@example.com"
        )

        mock_license_info = {
            "id": "license-123",
            "plan": "pro",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "activated_at": None  # Not activated yet
        }

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.validate_key_format = MagicMock(return_value=True)
            mock_service.get_license_by_key = AsyncMock(return_value=mock_license_info)
            mock_service.activate_license = AsyncMock()

            result = await activate_license(request)

        assert result["message"] == "License activated successfully"
        assert result["plan"] == "pro"

    @pytest.mark.asyncio
    async def test_activate_license_invalid_format(self):
        """Test activation with invalid key format"""
        from api.routes.license import ActivateLicenseRequest, activate_license

        request = ActivateLicenseRequest(
            license_key="invalid-key",
            hwid="abc123",
            email="test@example.com"
        )

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.validate_key_format = MagicMock(return_value=False)

            with pytest.raises(HTTPException) as exc_info:
                await activate_license(request)

            assert exc_info.value.status_code == 400
            assert "Invalid license key format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_activate_license_key_not_found(self):
        """Test activation with non-existent key"""
        from api.routes.license import ActivateLicenseRequest, activate_license

        request = ActivateLicenseRequest(
            license_key="DIDIN-XXXX-YYYY-ZZZZ",
            hwid="abc123",
            email="test@example.com"
        )

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.validate_key_format = MagicMock(return_value=True)
            mock_service.get_license_by_key = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await activate_license(request)

            assert exc_info.value.status_code == 404
            assert "License key not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_activate_license_device_already_registered(self):
        """Test activation when device is already registered"""
        from api.routes.license import ActivateLicenseRequest, activate_license

        request = ActivateLicenseRequest(
            license_key="DIDIN-XXXX-YYYY-ZZZZ",
            hwid="abc123",
            email="test@example.com"
        )

        mock_license_info = {
            "id": "license-123",
            "plan": "pro",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "activated_at": datetime.now(timezone.utc),
            "max_devices": 3
        }

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.validate_key_format = MagicMock(return_value=True)
            mock_service.get_license_by_key = AsyncMock(return_value=mock_license_info)
            mock_service.get_license_by_email = AsyncMock(return_value=mock_license_info)
            mock_service.validate_hwid = AsyncMock(return_value=True)

            result = await activate_license(request)

        assert result["message"] == "Device already registered"

    @pytest.mark.asyncio
    async def test_activate_license_max_devices_reached(self):
        """Test activation when max devices reached"""
        from api.routes.license import ActivateLicenseRequest, activate_license

        request = ActivateLicenseRequest(
            license_key="DIDIN-XXXX-YYYY-ZZZZ",
            hwid="new-device",
            email="test@example.com"
        )

        mock_license_info = {
            "id": "license-123",
            "plan": "pro",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "activated_at": datetime.now(timezone.utc),
            "max_devices": 2
        }

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.validate_key_format = MagicMock(return_value=True)
            mock_service.get_license_by_key = AsyncMock(return_value=mock_license_info)
            mock_service.get_license_by_email = AsyncMock(return_value=mock_license_info)
            mock_service.validate_hwid = AsyncMock(return_value=False)
            mock_service.get_active_devices = AsyncMock(return_value=["device1", "device2"])  # Max reached

            with pytest.raises(HTTPException) as exc_info:
                await activate_license(request)

            assert exc_info.value.status_code == 403
            assert "Maximum devices reached" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_activate_license_add_new_device(self):
        """Test adding new device to existing license"""
        from api.routes.license import ActivateLicenseRequest, activate_license

        request = ActivateLicenseRequest(
            license_key="DIDIN-XXXX-YYYY-ZZZZ",
            hwid="new-device",
            email="test@example.com"
        )

        mock_license_info = {
            "id": "license-123",
            "plan": "pro",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "activated_at": datetime.now(timezone.utc),
            "max_devices": 3
        }

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.validate_key_format = MagicMock(return_value=True)
            mock_service.get_license_by_key = AsyncMock(return_value=mock_license_info)
            mock_service.get_license_by_email = AsyncMock(return_value=mock_license_info)
            mock_service.validate_hwid = AsyncMock(return_value=False)
            mock_service.get_active_devices = AsyncMock(return_value=["device1"])  # 1 of 3
            mock_service.register_device = AsyncMock()

            result = await activate_license(request)

        assert result["message"] == "New device registered successfully"

    @pytest.mark.asyncio
    async def test_activate_license_email_mismatch(self):
        """Test activation with email not matching license"""
        from api.routes.license import ActivateLicenseRequest, activate_license

        request = ActivateLicenseRequest(
            license_key="DIDIN-XXXX-YYYY-ZZZZ",
            hwid="abc123",
            email="different@example.com"
        )

        mock_license_info = {
            "id": "license-123",
            "plan": "pro",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "activated_at": datetime.now(timezone.utc),
            "max_devices": 3
        }

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.validate_key_format = MagicMock(return_value=True)
            mock_service.get_license_by_key = AsyncMock(return_value=mock_license_info)
            mock_service.get_license_by_email = AsyncMock(return_value=None)  # Different email

            with pytest.raises(HTTPException) as exc_info:
                await activate_license(request)

            assert exc_info.value.status_code == 403
            assert "does not match" in exc_info.value.detail


class TestDeactivateDeviceEndpoint:
    """Tests for deactivate_device endpoint"""

    @pytest.mark.asyncio
    async def test_deactivate_device_success(self):
        """Test successful device deactivation"""
        from api.routes.license import (DeactivateLicenseRequest,
                                        deactivate_device)

        request = DeactivateLicenseRequest(
            hwid="device-to-remove",
            reason="Changing computer"
        )

        mock_user = {"id": "user-123"}
        mock_license_info = {"id": "license-123"}

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_license_by_user = AsyncMock(return_value=mock_license_info)
            mock_service.deactivate_device = AsyncMock(return_value=True)

            result = await deactivate_device(request, mock_user)

        assert result["message"] == "Device deactivated successfully"

    @pytest.mark.asyncio
    async def test_deactivate_device_no_license(self):
        """Test deactivation when user has no license"""
        from api.routes.license import (DeactivateLicenseRequest,
                                        deactivate_device)

        request = DeactivateLicenseRequest(hwid="abc123")
        mock_user = {"id": "user-123"}

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_license_by_user = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await deactivate_device(request, mock_user)

            assert exc_info.value.status_code == 404
            assert "No license found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_deactivate_device_not_found(self):
        """Test deactivation when device not found"""
        from api.routes.license import (DeactivateLicenseRequest,
                                        deactivate_device)

        request = DeactivateLicenseRequest(hwid="nonexistent-device")
        mock_user = {"id": "user-123"}
        mock_license_info = {"id": "license-123"}

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_license_by_user = AsyncMock(return_value=mock_license_info)
            mock_service.deactivate_device = AsyncMock(return_value=False)

            with pytest.raises(HTTPException) as exc_info:
                await deactivate_device(request, mock_user)

            assert exc_info.value.status_code == 404
            assert "Device not found" in exc_info.value.detail


class TestGetLicenseStatusEndpoint:
    """Tests for get_license_status endpoint"""

    @pytest.mark.asyncio
    async def test_get_status_with_license(self):
        """Test getting status with active license"""
        from api.routes.license import get_license_status

        mock_user = {"id": "user-123"}
        mock_license_info = {
            "id": "license-123",
            "plan": "pro",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "max_devices": 3
        }
        mock_usage = {"products_scraped": 50, "copies_generated": 10}
        mock_devices = ["device1", "device2"]

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_license_by_user = AsyncMock(return_value=mock_license_info)
            mock_service.get_usage_stats = AsyncMock(return_value=mock_usage)
            mock_service.get_active_devices = AsyncMock(return_value=mock_devices)
            mock_service.get_plan_features = MagicMock(return_value={"products_per_day": 100})

            result = await get_license_status(mock_user)

        assert result["has_license"] is True
        assert result["plan"] == "pro"
        assert result["devices"]["active"] == 2
        assert result["devices"]["max"] == 3

    @pytest.mark.asyncio
    async def test_get_status_without_license(self):
        """Test getting status without license (free plan)"""
        from api.routes.license import get_license_status

        mock_user = {"id": "user-123"}

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_license_by_user = AsyncMock(return_value=None)
            mock_service.get_plan_features = MagicMock(return_value={"products_per_day": 10})

            result = await get_license_status(mock_user)

        assert result["has_license"] is False
        assert result["plan"] == "free"


class TestGetAvailablePlansEndpoint:
    """Tests for get_available_plans endpoint"""

    @pytest.mark.asyncio
    async def test_get_available_plans(self):
        """Test getting all available plans"""
        from api.routes.license import get_available_plans

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_plan_features = MagicMock(return_value={
                "products_per_day": 100,
                "copies_per_month": 500
            })

            result = await get_available_plans()

        assert "plans" in result
        assert len(result["plans"]) == 4
        
        plan_ids = [p["id"] for p in result["plans"]]
        assert "free" in plan_ids
        assert "starter" in plan_ids
        assert "pro" in plan_ids
        assert "enterprise" in plan_ids

    @pytest.mark.asyncio
    async def test_plan_prices(self):
        """Test plan prices are correct"""
        from api.routes.license import get_available_plans

        with patch('api.routes.license.LicenseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_plan_features = MagicMock(return_value={})

            result = await get_available_plans()

        plans_by_id = {p["id"]: p for p in result["plans"]}
        
        assert plans_by_id["free"]["price"] == 0
        assert plans_by_id["starter"]["price"] == 29.90
        assert plans_by_id["pro"]["price"] == 79.90
        assert plans_by_id["enterprise"]["price"] == 199.90


class TestRouterConfiguration:
    """Tests for router configuration"""

    def test_router_exists(self):
        """Test router exists"""
        from api.routes.license import router

        assert router is not None

    def test_router_routes(self):
        """Test router has expected routes"""
        from api.routes.license import router

        route_paths = [r.path for r in router.routes if hasattr(r, 'path')]
        
        assert "/validate" in route_paths
        assert "/activate" in route_paths
        assert "/deactivate" in route_paths
        assert "/status" in route_paths
        assert "/plans" in route_paths


class TestConstants:
    """Tests for constants"""

    def test_jwt_secret_key(self):
        """Test JWT secret key constant"""
        from api.routes.license import JWT_SECRET_KEY

        assert JWT_SECRET_KEY is not None
        assert isinstance(JWT_SECRET_KEY, str)
