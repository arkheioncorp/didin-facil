"""
License Routes Tests - Full Coverage
Tests for license management endpoints using AsyncClient
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from api.main import app
from api.routes.license import get_current_user


@pytest_asyncio.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def mock_license_service():
    """Mock LicenseService."""
    with patch("api.routes.license.LicenseService") as service_cls:
        service = AsyncMock()
        service.create_license_jwt = MagicMock()
        service.validate_key_format = MagicMock()
        service.get_plan_features = MagicMock()
        service_cls.return_value = service
        yield service


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    user = {"id": "user_123", "email": "test@example.com"}
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_validate_license_success(mock_license_service, async_client):
    """Test successful license validation."""
    mock_license_service.get_license_by_email.return_value = {
        "id": "lic_123",
        "user_id": "user_123",
        "plan": "pro",
        "expires_at": datetime.utcnow() + timedelta(days=30)
    }
    mock_license_service.validate_hwid.return_value = True
    mock_license_service.create_license_jwt.return_value = "jwt_token"
    mock_license_service.get_plan_features.return_value = {"feature": True}

    payload = {
        "email": "test@example.com",
        "hwid": "hwid_123",
        "app_version": "1.0.0"
    }

    response = await async_client.post("/license/validate", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["jwt"] == "jwt_token"
    assert data["plan"] == "pro"


@pytest.mark.asyncio
async def test_validate_license_not_found(mock_license_service, async_client):
    """Test license validation when not found."""
    mock_license_service.get_license_by_email.return_value = None

    payload = {
        "email": "unknown@example.com",
        "hwid": "hwid_123",
        "app_version": "1.0.0"
    }

    response = await async_client.post("/license/validate", json=payload)

    assert response.status_code == 402
    assert "No active license" in response.json()["detail"]


@pytest.mark.asyncio
async def test_validate_license_expired(mock_license_service, async_client):
    """Test license validation when expired."""
    mock_license_service.get_license_by_email.return_value = {
        "id": "lic_123",
        "expires_at": datetime.utcnow() - timedelta(days=1)
    }

    payload = {
        "email": "test@example.com",
        "hwid": "hwid_123",
        "app_version": "1.0.0"
    }

    response = await async_client.post("/license/validate", json=payload)

    assert response.status_code == 402
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_validate_license_device_not_registered(
    mock_license_service,
    async_client
):
    """Test license validation when device not registered."""
    mock_license_service.get_license_by_email.return_value = {
        "id": "lic_123",
        "expires_at": datetime.utcnow() + timedelta(days=30)
    }
    mock_license_service.validate_hwid.return_value = False

    payload = {
        "email": "test@example.com",
        "hwid": "new_hwid",
        "app_version": "1.0.0"
    }

    response = await async_client.post("/license/validate", json=payload)

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "DEVICE_NOT_REGISTERED"


@pytest.mark.asyncio
async def test_activate_license_first_time(mock_license_service, async_client):
    """Test first time license activation."""
    mock_license_service.validate_key_format.return_value = True
    mock_license_service.get_license_by_key.return_value = {
        "id": "lic_123",
        "plan": "pro",
        "activated_at": None,
        "expires_at": None
    }

    payload = {
        "license_key": "KEY-123",
        "hwid": "hwid_123",
        "email": "test@example.com"
    }

    response = await async_client.post("/license/activate", json=payload)

    assert response.status_code == 200
    assert "activated" in response.json()["message"].lower()
    mock_license_service.activate_license.assert_called_with(
        license_id="lic_123",
        email="test@example.com",
        hwid="hwid_123"
    )


@pytest.mark.asyncio
async def test_activate_license_add_device(mock_license_service, async_client):
    """Test adding new device to existing license."""
    mock_license_service.validate_key_format.return_value = True
    mock_license_service.get_license_by_key.return_value = {
        "id": "lic_123",
        "plan": "pro",
        "activated_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=30),
        "max_devices": 2
    }
    mock_license_service.get_license_by_email.return_value = {"id": "lic_123"}
    mock_license_service.validate_hwid.return_value = False
    mock_license_service.get_active_devices.return_value = ["device1"]

    payload = {
        "license_key": "KEY-123",
        "hwid": "hwid_new",
        "email": "test@example.com"
    }

    response = await async_client.post("/license/activate", json=payload)

    assert response.status_code == 200
    assert "device" in response.json()["message"].lower()
    mock_license_service.register_device.assert_called()


@pytest.mark.asyncio
async def test_activate_license_max_devices_reached(
    mock_license_service,
    async_client
):
    """Test activation when max devices reached."""
    mock_license_service.validate_key_format.return_value = True
    mock_license_service.get_license_by_key.return_value = {
        "id": "lic_123",
        "plan": "pro",
        "activated_at": datetime.utcnow(),
        "max_devices": 1
    }
    mock_license_service.get_license_by_email.return_value = {"id": "lic_123"}
    mock_license_service.validate_hwid.return_value = False
    mock_license_service.get_active_devices.return_value = ["device1"]

    payload = {
        "license_key": "KEY-123",
        "hwid": "hwid_new",
        "email": "test@example.com"
    }

    response = await async_client.post("/license/activate", json=payload)

    assert response.status_code == 403
    assert "Maximum devices" in response.json()["detail"]["message"]


@pytest.mark.asyncio
async def test_deactivate_device(
    mock_license_service,
    mock_auth_user,
    async_client
):
    """Test device deactivation."""
    mock_license_service.get_license_by_user.return_value = {"id": "lic_123"}
    mock_license_service.deactivate_device.return_value = True

    payload = {"hwid": "hwid_123", "reason": "sold"}

    response = await async_client.post("/license/deactivate", json=payload)

    assert response.status_code == 200
    assert "deactivated" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_get_license_status(
    mock_license_service,
    mock_auth_user,
    async_client
):
    """Test getting license status."""
    mock_license_service.get_license_by_user.return_value = {
        "id": "lic_123",
        "plan": "pro",
        "expires_at": "2025-12-31T00:00:00",
        "max_devices": 3
    }
    mock_license_service.get_usage_stats.return_value = {"usage": 10}
    mock_license_service.get_active_devices.return_value = ["d1", "d2"]
    mock_license_service.get_plan_features.return_value = {}

    response = await async_client.get("/license/status")

    assert response.status_code == 200
    data = response.json()
    assert data["has_license"] is True
    assert data["devices"]["active"] == 2


@pytest.mark.asyncio
async def test_get_plans(mock_license_service, async_client):
    """Test getting available plans."""
    mock_license_service.get_plan_features.return_value = {}

    response = await async_client.get("/license/plans")

    assert response.status_code == 200
    data = response.json()
    assert len(data["plans"]) == 4


class TestLicenseEdgeCases:
    """Tests for license edge cases."""

    @pytest.mark.asyncio
    async def test_free_plan_max_one_device(
        self,
        mock_license_service,
        async_client
    ):
        """Test free plan allows only 1 device."""
        mock_license_service.validate_key_format.return_value = True
        mock_license_service.get_license_by_key.return_value = {
            "id": "lic_free",
            "plan": "free",
            "activated_at": datetime.utcnow(),
            "max_devices": 1,
            "expires_at": datetime.utcnow() + timedelta(days=30)
        }
        mock_license_service.get_license_by_email.return_value = {
            "id": "lic_free"
        }
        mock_license_service.validate_hwid.return_value = False
        mock_license_service.get_active_devices.return_value = [
            {"hwid": "device_A"}
        ]

        payload = {
            "license_key": "FREE-KEY-123",
            "hwid": "device_B",
            "email": "free@example.com"
        }

        response = await async_client.post("/license/activate", json=payload)

        assert response.status_code == 403
        assert "Maximum devices" in response.json()["detail"]["message"]

    @pytest.mark.asyncio
    async def test_invalid_license_key_format(
        self,
        mock_license_service,
        async_client
    ):
        """Test activation with invalid license key format."""
        mock_license_service.validate_key_format.return_value = False

        payload = {
            "license_key": "INVALID",
            "hwid": "hwid_123",
            "email": "test@example.com"
        }

        response = await async_client.post("/license/activate", json=payload)

        assert response.status_code == 400
        assert "Invalid license key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_license_key_not_found(
        self,
        mock_license_service,
        async_client
    ):
        """Test activation with non-existent license key."""
        mock_license_service.validate_key_format.return_value = True
        mock_license_service.get_license_by_key.return_value = None

        payload = {
            "license_key": "XXXX-XXXX-XXXX-XXXX",
            "hwid": "hwid_123",
            "email": "test@example.com"
        }

        response = await async_client.post("/license/activate", json=payload)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
