"""
Testes para License Routes - api/routes/license.py
Cobertura: validate_license, activate_license, deactivate_device, get_license_status, get_available_plans
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import uuid

# ============================================
# MOCKS & FIXTURES
# ============================================

@pytest.fixture
def mock_license_service():
    """Mock do LicenseService"""
    service = AsyncMock()
    
    # Mock de features
    service.get_plan_features.return_value = {
        "name": "Pro",
        "products_per_day": 100,
        "copies_per_month": 500,
        "favorites_limit": 1000,
        "export_formats": ["csv", "json"],
        "priority_support": True,
        "api_access": True
    }
    
    # Mock de validação de formato
    service.validate_key_format.return_value = True
    
    # Mock de criação de JWT
    service.create_license_jwt.return_value = "mock-jwt-token"
    
    return service

@pytest.fixture
def mock_license_info():
    """Mock de informações da licença"""
    return {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "plan": "pro",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
        "activated_at": datetime.now(timezone.utc) - timedelta(days=1),
        "max_devices": 3,
        "email": "test@example.com"
    }

@pytest.fixture
def mock_user():
    """Mock de usuário autenticado"""
    return {
        "id": uuid.uuid4(),
        "email": "test@example.com",
        "name": "Test User"
    }

# ============================================
# TESTS: Validate License
# ============================================

class TestValidateLicense:
    """Testes do endpoint validate_license"""
    
    @pytest.mark.asyncio
    async def test_validate_success(self, mock_license_service, mock_license_info):
        """Deve validar licença com sucesso"""
        mock_license_service.get_license_by_email.return_value = mock_license_info
        mock_license_service.validate_hwid.return_value = True
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import validate_license, ValidateLicenseRequest
            
            request = ValidateLicenseRequest(
                email="test@example.com",
                hwid="hwid-123",
                app_version="1.0.0"
            )
            
            response = await validate_license(request)
            
            assert response.valid is True
            assert response.plan == "pro"
            assert response.jwt == "mock-jwt-token"

    @pytest.mark.asyncio
    async def test_validate_no_license(self, mock_license_service):
        """Deve retornar erro se não houver licença"""
        mock_license_service.get_license_by_email.return_value = None
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import validate_license, ValidateLicenseRequest
            
            request = ValidateLicenseRequest(
                email="test@example.com",
                hwid="hwid-123",
                app_version="1.0.0"
            )
            
            with pytest.raises(HTTPException) as exc:
                await validate_license(request)
            
            assert exc.value.status_code == 402
            assert "No active license" in exc.value.detail

    @pytest.mark.asyncio
    async def test_validate_expired(self, mock_license_service, mock_license_info):
        """Deve retornar erro se licença expirada"""
        mock_license_info["expires_at"] = datetime.now(timezone.utc) - timedelta(days=1)
        mock_license_service.get_license_by_email.return_value = mock_license_info
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import validate_license, ValidateLicenseRequest
            
            request = ValidateLicenseRequest(
                email="test@example.com",
                hwid="hwid-123",
                app_version="1.0.0"
            )
            
            with pytest.raises(HTTPException) as exc:
                await validate_license(request)
            
            assert exc.value.status_code == 402
            assert "expired" in exc.value.detail

    @pytest.mark.asyncio
    async def test_validate_device_not_registered(self, mock_license_service, mock_license_info):
        """Deve retornar erro se dispositivo não registrado"""
        mock_license_service.get_license_by_email.return_value = mock_license_info
        mock_license_service.validate_hwid.return_value = False
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import validate_license, ValidateLicenseRequest
            
            request = ValidateLicenseRequest(
                email="test@example.com",
                hwid="hwid-123",
                app_version="1.0.0"
            )
            
            with pytest.raises(HTTPException) as exc:
                await validate_license(request)
            
            assert exc.value.status_code == 403
            assert exc.value.detail["code"] == "DEVICE_NOT_REGISTERED"

# ============================================
# TESTS: Activate License
# ============================================

class TestActivateLicense:
    """Testes do endpoint activate_license"""
    
    @pytest.mark.asyncio
    async def test_activate_first_time(self, mock_license_service, mock_license_info):
        """Deve ativar licença pela primeira vez"""
        mock_license_info["activated_at"] = None
        mock_license_service.get_license_by_key.return_value = mock_license_info
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import activate_license, ActivateLicenseRequest
            
            request = ActivateLicenseRequest(
                license_key="KEY-123",
                hwid="hwid-123",
                email="test@example.com"
            )
            
            response = await activate_license(request)
            
            assert response["message"] == "License activated successfully"
            mock_license_service.activate_license.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_add_device(self, mock_license_service, mock_license_info):
        """Deve adicionar novo dispositivo"""
        mock_license_service.get_license_by_key.return_value = mock_license_info
        mock_license_service.get_license_by_email.return_value = mock_license_info
        mock_license_service.validate_hwid.return_value = False
        mock_license_service.get_active_devices.return_value = []
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import activate_license, ActivateLicenseRequest
            
            request = ActivateLicenseRequest(
                license_key="KEY-123",
                hwid="hwid-123",
                email="test@example.com"
            )
            
            response = await activate_license(request)
            
            assert response["message"] == "New device registered successfully"
            mock_license_service.register_device.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_invalid_format(self, mock_license_service):
        """Deve retornar erro se formato inválido"""
        mock_license_service.validate_key_format.return_value = False
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import activate_license, ActivateLicenseRequest
            
            request = ActivateLicenseRequest(
                license_key="INVALID",
                hwid="hwid-123",
                email="test@example.com"
            )
            
            with pytest.raises(HTTPException) as exc:
                await activate_license(request)
            
            assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_activate_key_not_found(self, mock_license_service):
        """Deve retornar erro se chave não encontrada"""
        mock_license_service.get_license_by_key.return_value = None
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import activate_license, ActivateLicenseRequest
            
            request = ActivateLicenseRequest(
                license_key="KEY-123",
                hwid="hwid-123",
                email="test@example.com"
            )
            
            with pytest.raises(HTTPException) as exc:
                await activate_license(request)
            
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_activate_email_mismatch(self, mock_license_service, mock_license_info):
        """Deve retornar erro se email não corresponder"""
        mock_license_service.get_license_by_key.return_value = mock_license_info
        
        other_license = mock_license_info.copy()
        other_license["id"] = uuid.uuid4()
        mock_license_service.get_license_by_email.return_value = other_license
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import activate_license, ActivateLicenseRequest
            
            request = ActivateLicenseRequest(
                license_key="KEY-123",
                hwid="hwid-123",
                email="test@example.com"
            )
            
            with pytest.raises(HTTPException) as exc:
                await activate_license(request)
            
            assert exc.value.status_code == 403
            assert "does not match" in exc.value.detail

    @pytest.mark.asyncio
    async def test_activate_max_devices(self, mock_license_service, mock_license_info):
        """Deve retornar erro se limite de dispositivos atingido"""
        mock_license_service.get_license_by_key.return_value = mock_license_info
        mock_license_service.get_license_by_email.return_value = mock_license_info
        mock_license_service.validate_hwid.return_value = False
        mock_license_service.get_active_devices.return_value = ["dev1", "dev2", "dev3"]
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import activate_license, ActivateLicenseRequest
            
            request = ActivateLicenseRequest(
                license_key="KEY-123",
                hwid="hwid-123",
                email="test@example.com"
            )
            
            with pytest.raises(HTTPException) as exc:
                await activate_license(request)
            
            assert exc.value.status_code == 403
            assert "Maximum devices reached" in exc.value.detail["message"]

# ============================================
# TESTS: Deactivate License
# ============================================

class TestDeactivateLicense:
    """Testes do endpoint deactivate_device"""
    
    @pytest.mark.asyncio
    async def test_deactivate_success(self, mock_license_service, mock_license_info, mock_user):
        """Deve desativar dispositivo com sucesso"""
        mock_license_service.get_license_by_user.return_value = mock_license_info
        mock_license_service.deactivate_device.return_value = True
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import deactivate_device, DeactivateLicenseRequest
            
            request = DeactivateLicenseRequest(hwid="hwid-123")
            
            response = await deactivate_device(request, user=mock_user)
            
            assert response["message"] == "Device deactivated successfully"

    @pytest.mark.asyncio
    async def test_deactivate_no_license(self, mock_license_service, mock_user):
        """Deve retornar erro se usuário não tiver licença"""
        mock_license_service.get_license_by_user.return_value = None
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import deactivate_device, DeactivateLicenseRequest
            
            request = DeactivateLicenseRequest(hwid="hwid-123")
            
            with pytest.raises(HTTPException) as exc:
                await deactivate_device(request, user=mock_user)
            
            assert exc.value.status_code == 404
            assert "No license found" in exc.value.detail

    @pytest.mark.asyncio
    async def test_deactivate_device_not_found(self, mock_license_service, mock_license_info, mock_user):
        """Deve retornar erro se dispositivo não encontrado"""
        mock_license_service.get_license_by_user.return_value = mock_license_info
        mock_license_service.deactivate_device.return_value = False
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import deactivate_device, DeactivateLicenseRequest
            
            request = DeactivateLicenseRequest(hwid="hwid-123")
            
            with pytest.raises(HTTPException) as exc:
                await deactivate_device(request, user=mock_user)
            
            assert exc.value.status_code == 404
            assert "Device not found" in exc.value.detail

# ============================================
# TESTS: Get Status & Plans
# ============================================

class TestStatusPlans:
    """Testes de status e planos"""
    
    @pytest.mark.asyncio
    async def test_get_status_success(self, mock_license_service, mock_license_info, mock_user):
        """Deve retornar status da licença"""
        mock_license_service.get_license_by_user.return_value = mock_license_info
        mock_license_service.get_usage_stats.return_value = {"products": 10}
        mock_license_service.get_active_devices.return_value = ["dev1"]
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import get_license_status
            
            response = await get_license_status(user=mock_user)
            
            assert response["has_license"] is True
            assert response["plan"] == "pro"
            assert response["usage"]["products"] == 10
            assert response["devices"]["active"] == 1

    @pytest.mark.asyncio
    async def test_get_status_no_license(self, mock_license_service, mock_user):
        """Deve retornar status free se não tiver licença"""
        mock_license_service.get_license_by_user.return_value = None
        mock_license_service.get_plan_features.return_value = {"name": "Free"}
        
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import get_license_status
            
            response = await get_license_status(user=mock_user)
            
            assert response["has_license"] is False
            assert response["plan"] == "free"

    @pytest.mark.asyncio
    async def test_get_plans(self, mock_license_service):
        """Deve retornar planos disponíveis"""
        with patch("api.routes.license.LicenseService", return_value=mock_license_service):
            from api.routes.license import get_available_plans
            
            response = await get_available_plans()
            
            assert "plans" in response
            assert len(response["plans"]) > 0
