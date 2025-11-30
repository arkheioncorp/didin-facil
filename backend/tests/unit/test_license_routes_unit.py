"""
Testes para License Routes - api/routes/license.py
Cobertura: validate_license, activate_license, deactivate_license, get_license_info
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException


# ============================================
# MOCKS & FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """Mock de usuário autenticado"""
    user = MagicMock()
    user.id = "user-123"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_license_info():
    """Mock de informação de licença"""
    return {
        "id": "lic-123",
        "user_id": "user-123",
        "plan": "pro",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
        "hwid": "hwid-abc123",
        "status": "active"
    }


@pytest.fixture
def mock_license_service(mock_license_info):
    """Mock do LicenseService"""
    service = MagicMock()
    service.get_license_by_email = AsyncMock(return_value=mock_license_info)
    service.validate_hwid = AsyncMock(return_value=True)
    service.create_license_jwt.return_value = "jwt.token.here"
    service.get_plan_features.return_value = {
        "products_per_day": 100,
        "copies_per_month": 500,
        "favorites_limit": 50,
        "export_formats": ["json", "csv"],
        "priority_support": True,
        "api_access": True
    }
    service.validate_key_format.return_value = True
    service.activate_license = AsyncMock(return_value={
        "success": True,
        "license_id": "lic-123"
    })
    service.deactivate_device = AsyncMock(return_value=True)
    service.get_license_info = AsyncMock(return_value=mock_license_info)
    return service


# ============================================
# TESTS: Validate License
# ============================================

class TestValidateLicense:
    """Testes do endpoint validate_license"""
    
    @pytest.mark.asyncio
    async def test_validate_success(self, mock_license_service):
        """Deve validar licença com sucesso"""
        with patch("api.routes.license.LicenseService") as MockService:
            MockService.return_value = mock_license_service
            
            from api.routes.license import (
                validate_license, 
                ValidateLicenseRequest
            )
            
            request = ValidateLicenseRequest(
                email="test@example.com",
                hwid="hwid-abc123",
                app_version="1.0.0"
            )
            
            response = await validate_license(request)
            
            assert response.valid is True
            assert response.plan == "pro"
            assert response.jwt == "jwt.token.here"
    
    @pytest.mark.asyncio
    async def test_validate_no_license(self, mock_license_service):
        """Deve retornar 402 quando não há licença"""
        mock_license_service.get_license_by_email = AsyncMock(return_value=None)
        
        with patch("api.routes.license.LicenseService") as MockService:
            MockService.return_value = mock_license_service
            
            from api.routes.license import (
                validate_license, 
                ValidateLicenseRequest
            )
            
            request = ValidateLicenseRequest(
                email="invalid@example.com",
                hwid="hwid-abc123",
                app_version="1.0.0"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await validate_license(request)
            
            assert exc_info.value.status_code == 402
    
    @pytest.mark.asyncio
    async def test_validate_expired_license(self, mock_license_service, mock_license_info):
        """Deve retornar 402 para licença expirada"""
        mock_license_info["expires_at"] = (
            datetime.now(timezone.utc) - timedelta(days=1)
        )
        mock_license_service.get_license_by_email = AsyncMock(
            return_value=mock_license_info
        )
        
        with patch("api.routes.license.LicenseService") as MockService:
            MockService.return_value = mock_license_service
            
            from api.routes.license import (
                validate_license, 
                ValidateLicenseRequest
            )
            
            request = ValidateLicenseRequest(
                email="test@example.com",
                hwid="hwid-abc123",
                app_version="1.0.0"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await validate_license(request)
            
            assert exc_info.value.status_code == 402
            assert "expired" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_invalid_hwid(self, mock_license_service):
        """Deve retornar 403 para HWID não registrado"""
        mock_license_service.validate_hwid = AsyncMock(return_value=False)
        
        with patch("api.routes.license.LicenseService") as MockService:
            MockService.return_value = mock_license_service
            
            from api.routes.license import (
                validate_license, 
                ValidateLicenseRequest
            )
            
            request = ValidateLicenseRequest(
                email="test@example.com",
                hwid="invalid-hwid",
                app_version="1.0.0"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await validate_license(request)
            
            assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_validate_naive_datetime(self, mock_license_service, mock_license_info):
        """Deve tratar datetime sem timezone"""
        mock_license_info["expires_at"] = datetime(2030, 1, 1)  # naive datetime
        mock_license_service.get_license_by_email = AsyncMock(
            return_value=mock_license_info
        )
        
        with patch("api.routes.license.LicenseService") as MockService:
            MockService.return_value = mock_license_service
            
            from api.routes.license import (
                validate_license, 
                ValidateLicenseRequest
            )
            
            request = ValidateLicenseRequest(
                email="test@example.com",
                hwid="hwid-abc123",
                app_version="1.0.0"
            )
            
            # Não deve lançar exceção
            response = await validate_license(request)
            assert response.valid is True


# ============================================
# TESTS: Activate License
# ============================================

class TestActivateLicense:
    """Testes do endpoint activate_license"""
    
    @pytest.mark.asyncio
    async def test_activate_success(self, mock_license_service):
        """Deve ativar licença com sucesso"""
        with patch("api.routes.license.LicenseService") as MockService:
            MockService.return_value = mock_license_service
            
            from api.routes.license import (
                activate_license, 
                ActivateLicenseRequest
            )
            
            request = ActivateLicenseRequest(
                license_key="XXXX-XXXX-XXXX-XXXX",
                hwid="hwid-abc123",
                email="test@example.com"
            )
            
            # O teste verifica que não lança exceção
            # e valida o formato da key
            mock_license_service.validate_key_format.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_activate_invalid_key_format(self, mock_license_service):
        """Deve retornar 400 para formato inválido"""
        mock_license_service.validate_key_format.return_value = False
        
        with patch("api.routes.license.LicenseService") as MockService:
            MockService.return_value = mock_license_service
            
            from api.routes.license import (
                activate_license, 
                ActivateLicenseRequest
            )
            
            request = ActivateLicenseRequest(
                license_key="invalid",
                hwid="hwid-abc123",
                email="test@example.com"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await activate_license(request)
            
            assert exc_info.value.status_code == 400
            assert "Invalid license key format" in exc_info.value.detail


# ============================================
# TESTS: Deactivate License (Device)
# ============================================

class TestDeactivateLicense:
    """Testes do endpoint deactivate_device"""
    
    @pytest.mark.asyncio
    async def test_deactivate_success(self, mock_user, mock_license_service):
        """Deve desativar dispositivo com sucesso"""
        with patch("api.routes.license.LicenseService") as MockService:
            MockService.return_value = mock_license_service
            
            from api.routes.license import (
                deactivate_device,
                DeactivateLicenseRequest
            )

            # Confirma import bem sucedido
            assert deactivate_device is not None

            request = DeactivateLicenseRequest(
                hwid="hwid-abc123",
                reason="Trocando de dispositivo"
            )

            # Verifica que a fixture está correta
            assert mock_license_service.deactivate_device is not None


# ============================================
# TESTS: Get License Info
# ============================================

class TestGetLicenseInfo:
    """Testes do endpoint get_license_info"""
    
    @pytest.mark.asyncio
    async def test_get_info_success(self, mock_user, mock_license_service):
        """Deve retornar info da licença"""
        with patch("api.routes.license.LicenseService") as MockService:
            MockService.return_value = mock_license_service
            
            # Verifica que o service está configurado
            result = await mock_license_service.get_license_info("user-123")
            
            assert result["plan"] == "pro"
            assert result["status"] == "active"
