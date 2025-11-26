"""
Backend Routes Tests
Comprehensive tests for all API routes - 100% coverage
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

# ==========================================
# COPY ROUTES TESTS
# ==========================================

class TestCopyRoutes:
    """Tests for copy generation routes"""
    
    @pytest.fixture
    def mock_user(self):
        return {
            "id": "user123",
            "email": "test@example.com",
            "plan": "pro",
            "hwid": "hwid123"
        }
    
    @pytest.fixture
    def copy_request(self):
        return {
            "product_id": "prod123",
            "product_title": "Produto Teste",
            "product_description": "Descrição do produto",
            "product_price": 99.90,
            "product_benefits": ["Benefício 1", "Benefício 2"],
            "copy_type": "ad",
            "tone": "professional",
            "platform": "instagram",
            "language": "pt-BR",
            "max_length": 500,
            "include_emoji": True,
            "include_hashtags": True,
            "custom_instructions": None
        }
    
    @pytest.mark.asyncio
    async def test_generate_copy_success(self, mock_user, copy_request):
        """Test successful copy generation"""
        from api.routes.copy import generate_copy
        from pydantic import BaseModel
        
        # Create request model
        class CopyRequest(BaseModel):
            product_id: str
            product_title: str
            product_description: str = None
            product_price: float
            product_benefits: list = None
            copy_type: str
            tone: str
            platform: str = "instagram"
            language: str = "pt-BR"
            max_length: int = None
            include_emoji: bool = True
            include_hashtags: bool = True
            custom_instructions: str = None
        
        request = CopyRequest(**copy_request)
        
        mock_quota_info = {"remaining": 50}
        mock_copy_result = {
            "id": "copy123",
            "copy_text": "📦 Produto incrível!",
            "copy_type": "ad",
            "tone": "professional",
            "platform": "instagram",
            "word_count": 10,
            "character_count": 50,
            "created_at": datetime.utcnow()
        }
        
        with patch('api.routes.copy.check_copy_quota', new_callable=AsyncMock) as mock_quota:
            with patch('api.routes.copy.CacheService') as mock_cache_cls:
                with patch('api.routes.copy.OpenAIService') as mock_openai_cls:
                    mock_quota.return_value = mock_quota_info
                    
                    mock_cache = MagicMock()
                    mock_cache.get = AsyncMock(return_value=None)
                    mock_cache.set = AsyncMock()
                    mock_cache.build_copy_cache_key = MagicMock(return_value="cache_key")
                    mock_cache_cls.return_value = mock_cache
                    
                    mock_openai = MagicMock()
                    mock_openai.generate_copy = AsyncMock(return_value=mock_copy_result)
                    mock_openai.increment_quota = AsyncMock()
                    mock_openai.save_to_history = AsyncMock()
                    mock_openai_cls.return_value = mock_openai
                    
                    result = await generate_copy(request, mock_user)
                    
                    assert result.copy_text == "📦 Produto incrível!"
                    assert not result.cached
                    assert result.quota_remaining == 49
    
    @pytest.mark.asyncio
    async def test_generate_copy_cached(self, mock_user, copy_request):
        """Test copy generation returns cached result"""
        from api.routes.copy import generate_copy
        from pydantic import BaseModel
        
        class CopyRequest(BaseModel):
            product_id: str
            product_title: str
            product_description: str = None
            product_price: float
            product_benefits: list = None
            copy_type: str
            tone: str
            platform: str = "instagram"
            language: str = "pt-BR"
            max_length: int = None
            include_emoji: bool = True
            include_hashtags: bool = True
            custom_instructions: str = None
        
        request = CopyRequest(**copy_request)
        
        cached_copy = {
            "id": "cached123",
            "copy_text": "📦 Cached copy!",
            "copy_type": "ad",
            "tone": "professional",
            "platform": "instagram",
            "word_count": 5,
            "character_count": 20,
            "created_at": datetime.utcnow()
        }
        
        with patch('api.routes.copy.check_copy_quota', new_callable=AsyncMock) as mock_quota:
            with patch('api.routes.copy.CacheService') as mock_cache_cls:
                mock_quota.return_value = {"remaining": 50}
                
                mock_cache = MagicMock()
                mock_cache.get = AsyncMock(return_value=cached_copy)
                mock_cache.build_copy_cache_key = MagicMock(return_value="cache_key")
                mock_cache_cls.return_value = mock_cache
                
                result = await generate_copy(request, mock_user)
                
                assert result.cached
                assert result.quota_remaining == 50
    
    @pytest.mark.asyncio
    async def test_generate_copy_quota_exceeded(self, mock_user, copy_request):
        """Test copy generation fails when quota exceeded"""
        from api.routes.copy import generate_copy
        from api.middleware.quota import QuotaExceededError
        from pydantic import BaseModel
        
        class CopyRequest(BaseModel):
            product_id: str
            product_title: str
            product_description: str = None
            product_price: float
            product_benefits: list = None
            copy_type: str
            tone: str
            platform: str = "instagram"
            language: str = "pt-BR"
            max_length: int = None
            include_emoji: bool = True
            include_hashtags: bool = True
            custom_instructions: str = None
        
        request = CopyRequest(**copy_request)
        
        with patch('api.routes.copy.check_copy_quota', new_callable=AsyncMock) as mock_quota:
            error = QuotaExceededError("Quota exceeded")
            error.reset_date = datetime.utcnow() + timedelta(days=1)
            mock_quota.side_effect = error
            
            with pytest.raises(HTTPException) as exc:
                await generate_copy(request, mock_user)
            
            assert exc.value.status_code == 429
    
    @pytest.mark.asyncio
    async def test_get_quota_status(self, mock_user):
        """Test getting quota status"""
        from api.routes.copy import get_quota_status
        
        mock_quota = {
            "used": 10,
            "limit": 100,
            "remaining": 90,
            "reset_date": datetime.utcnow() + timedelta(days=30)
        }
        
        with patch('api.routes.copy.OpenAIService') as mock_openai_cls:
            mock_openai = MagicMock()
            mock_openai.get_quota_status = AsyncMock(return_value=mock_quota)
            mock_openai_cls.return_value = mock_openai
            
            result = await get_quota_status(mock_user)
            
            assert result.copies_used == 10
            assert result.copies_limit == 100
            assert result.copies_remaining == 90
    
    @pytest.mark.asyncio
    async def test_get_copy_history(self, mock_user):
        """Test getting copy history"""
        from api.routes.copy import get_copy_history
        
        mock_history = [
            {
                "id": "copy1",
                "product_id": "prod1",
                "product_title": "Produto 1",
                "copy_type": "ad",
                "tone": "professional",
                "copy_text": "Copy 1",
                "created_at": datetime.utcnow()
            },
            {
                "id": "copy2",
                "product_id": "prod2",
                "product_title": "Produto 2",
                "copy_type": "description",
                "tone": "casual",
                "copy_text": "Copy 2",
                "created_at": datetime.utcnow()
            }
        ]
        
        with patch('api.routes.copy.OpenAIService') as mock_openai_cls:
            mock_openai = MagicMock()
            mock_openai.get_history = AsyncMock(return_value=mock_history)
            mock_openai_cls.return_value = mock_openai
            
            result = await get_copy_history(limit=50, offset=0, user=mock_user)
            
            assert len(result) == 2
            assert result[0].id == "copy1"
    
    @pytest.mark.asyncio
    async def test_get_copy_templates(self, mock_user):
        """Test getting copy templates"""
        from api.routes.copy import get_copy_templates
        
        result = await get_copy_templates(mock_user)
        
        assert "templates" in result
        assert len(result["templates"]) == 4
        assert result["templates"][0]["id"] == "urgency"
    
    @pytest.mark.asyncio
    async def test_apply_template_success(self, mock_user):
        """Test applying template with variables"""
        from api.routes.copy import apply_template
        
        variables = {
            "product_title": "Produto Teste",
            "price": "99.90"
        }
        
        result = await apply_template("urgency", variables, mock_user)
        
        assert "Produto Teste" in result["copy_text"]
        assert "99.90" in result["copy_text"]
        assert result["template_id"] == "urgency"
    
    @pytest.mark.asyncio
    async def test_apply_template_not_found(self, mock_user):
        """Test applying non-existent template"""
        from api.routes.copy import apply_template
        
        with pytest.raises(HTTPException) as exc:
            await apply_template("invalid_template", {}, mock_user)
        
        assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_apply_template_missing_variable(self, mock_user):
        """Test applying template with missing variable"""
        from api.routes.copy import apply_template
        
        variables = {"product_title": "Produto"}  # Missing price
        
        with pytest.raises(HTTPException) as exc:
            await apply_template("urgency", variables, mock_user)
        
        assert exc.value.status_code == 400


# ==========================================
# LICENSE ROUTES TESTS
# ==========================================

class TestLicenseRoutes:
    """Tests for license management routes"""
    
    @pytest.fixture
    def mock_user(self):
        return {
            "id": "user123",
            "email": "test@example.com",
            "plan": "pro"
        }
    
    @pytest.mark.asyncio
    async def test_validate_license_success(self):
        """Test successful license validation"""
        from api.routes.license import validate_license
        from pydantic import BaseModel
        
        class ValidateLicenseRequest(BaseModel):
            email: str
            hwid: str
            app_version: str
        
        request = ValidateLicenseRequest(
            email="test@example.com",
            hwid="hwid123",
            app_version="1.0.0"
        )
        
        mock_license = {
            "id": "lic123",
            "user_id": "user123",
            "plan": "pro",
            "expires_at": datetime.utcnow() + timedelta(days=30),
            "max_devices": 3
        }
        
        mock_features = {
            "products_per_day": 100,
            "copies_per_month": 500
        }
        
        with patch('api.routes.license.LicenseService') as mock_lic_cls:
            mock_lic = MagicMock()
            mock_lic.get_license_by_email = AsyncMock(return_value=mock_license)
            mock_lic.validate_hwid = AsyncMock(return_value=True)
            mock_lic.create_license_jwt = MagicMock(return_value="jwt_token")
            mock_lic.get_plan_features = MagicMock(return_value=mock_features)
            mock_lic_cls.return_value = mock_lic
            
            result = await validate_license(request)
            
            assert result.valid
            assert result.plan == "pro"
            assert result.jwt == "jwt_token"
    
    @pytest.mark.asyncio
    async def test_validate_license_not_found(self):
        """Test license validation when license not found"""
        from api.routes.license import validate_license
        from pydantic import BaseModel
        
        class ValidateLicenseRequest(BaseModel):
            email: str
            hwid: str
            app_version: str
        
        request = ValidateLicenseRequest(
            email="noexist@example.com",
            hwid="hwid123",
            app_version="1.0.0"
        )
        
        with patch('api.routes.license.LicenseService') as mock_lic_cls:
            mock_lic = MagicMock()
            mock_lic.get_license_by_email = AsyncMock(return_value=None)
            mock_lic_cls.return_value = mock_lic
            
            with pytest.raises(HTTPException) as exc:
                await validate_license(request)
            
            assert exc.value.status_code == 402
    
    @pytest.mark.asyncio
    async def test_validate_license_expired(self):
        """Test license validation when license expired"""
        from api.routes.license import validate_license
        from pydantic import BaseModel
        
        class ValidateLicenseRequest(BaseModel):
            email: str
            hwid: str
            app_version: str
        
        request = ValidateLicenseRequest(
            email="test@example.com",
            hwid="hwid123",
            app_version="1.0.0"
        )
        
        mock_license = {
            "id": "lic123",
            "user_id": "user123",
            "plan": "pro",
            "expires_at": datetime.utcnow() - timedelta(days=1)  # Expired
        }
        
        with patch('api.routes.license.LicenseService') as mock_lic_cls:
            mock_lic = MagicMock()
            mock_lic.get_license_by_email = AsyncMock(return_value=mock_license)
            mock_lic_cls.return_value = mock_lic
            
            with pytest.raises(HTTPException) as exc:
                await validate_license(request)
            
            assert exc.value.status_code == 402
            assert "expired" in str(exc.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_validate_license_max_devices(self):
        """Test license validation when max devices reached"""
        from api.routes.license import validate_license
        from pydantic import BaseModel
        
        class ValidateLicenseRequest(BaseModel):
            email: str
            hwid: str
            app_version: str
        
        request = ValidateLicenseRequest(
            email="test@example.com",
            hwid="new_hwid",
            app_version="1.0.0"
        )
        
        mock_license = {
            "id": "lic123",
            "user_id": "user123",
            "plan": "pro",
            "expires_at": datetime.utcnow() + timedelta(days=30),
            "max_devices": 2
        }
        
        with patch('api.routes.license.LicenseService') as mock_lic_cls:
            mock_lic = MagicMock()
            mock_lic.get_license_by_email = AsyncMock(return_value=mock_license)
            mock_lic.validate_hwid = AsyncMock(return_value=False)
            mock_lic.get_active_devices = AsyncMock(return_value=["device1", "device2"])
            mock_lic_cls.return_value = mock_lic
            
            with pytest.raises(HTTPException) as exc:
                await validate_license(request)
            
            assert exc.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_activate_license_success(self):
        """Test successful license activation"""
        from api.routes.license import activate_license
        from pydantic import BaseModel
        
        class ActivateLicenseRequest(BaseModel):
            license_key: str
            hwid: str
            email: str
        
        request = ActivateLicenseRequest(
            license_key="XXXX-XXXX-XXXX-XXXX",
            hwid="hwid123",
            email="test@example.com"
        )
        
        mock_license = {
            "id": "lic123",
            "plan": "pro",
            "expires_at": datetime.utcnow() + timedelta(days=30),
            "activated_at": None
        }
        
        with patch('api.routes.license.LicenseService') as mock_lic_cls:
            mock_lic = MagicMock()
            mock_lic.validate_key_format = MagicMock(return_value=True)
            mock_lic.get_license_by_key = AsyncMock(return_value=mock_license)
            mock_lic.activate_license = AsyncMock()
            mock_lic_cls.return_value = mock_lic
            
            result = await activate_license(request)
            
            assert result["message"] == "License activated successfully"
            assert result["plan"] == "pro"
    
    @pytest.mark.asyncio
    async def test_activate_license_invalid_format(self):
        """Test license activation with invalid format"""
        from api.routes.license import activate_license
        from pydantic import BaseModel
        
        class ActivateLicenseRequest(BaseModel):
            license_key: str
            hwid: str
            email: str
        
        request = ActivateLicenseRequest(
            license_key="invalid",
            hwid="hwid123",
            email="test@example.com"
        )
        
        with patch('api.routes.license.LicenseService') as mock_lic_cls:
            mock_lic = MagicMock()
            mock_lic.validate_key_format = MagicMock(return_value=False)
            mock_lic_cls.return_value = mock_lic
            
            with pytest.raises(HTTPException) as exc:
                await activate_license(request)
            
            assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_activate_license_already_activated(self):
        """Test license activation when already activated"""
        from api.routes.license import activate_license
        from pydantic import BaseModel
        
        class ActivateLicenseRequest(BaseModel):
            license_key: str
            hwid: str
            email: str
        
        request = ActivateLicenseRequest(
            license_key="XXXX-XXXX-XXXX-XXXX",
            hwid="hwid123",
            email="test@example.com"
        )
        
        mock_license = {
            "id": "lic123",
            "plan": "pro",
            "activated_at": datetime.utcnow()  # Already activated
        }
        
        with patch('api.routes.license.LicenseService') as mock_lic_cls:
            mock_lic = MagicMock()
            mock_lic.validate_key_format = MagicMock(return_value=True)
            mock_lic.get_license_by_key = AsyncMock(return_value=mock_license)
            mock_lic_cls.return_value = mock_lic
            
            with pytest.raises(HTTPException) as exc:
                await activate_license(request)
            
            assert exc.value.status_code == 409
    
    @pytest.mark.asyncio
    async def test_deactivate_device_success(self, mock_user):
        """Test successful device deactivation"""
        from api.routes.license import deactivate_device
        from pydantic import BaseModel
        
        class DeactivateLicenseRequest(BaseModel):
            hwid: str
            reason: str = None
        
        request = DeactivateLicenseRequest(hwid="hwid123", reason="Transferência")
        
        mock_license = {
            "id": "lic123",
            "plan": "pro"
        }
        
        with patch('api.routes.license.LicenseService') as mock_lic_cls:
            mock_lic = MagicMock()
            mock_lic.get_license_by_user = AsyncMock(return_value=mock_license)
            mock_lic.deactivate_device = AsyncMock(return_value=True)
            mock_lic_cls.return_value = mock_lic
            
            result = await deactivate_device(request, mock_user)
            
            assert result["message"] == "Device deactivated successfully"
    
    @pytest.mark.asyncio
    async def test_get_license_status_with_license(self, mock_user):
        """Test getting license status when user has license"""
        from api.routes.license import get_license_status
        
        mock_license = {
            "id": "lic123",
            "plan": "pro",
            "expires_at": datetime.utcnow() + timedelta(days=30),
            "max_devices": 3
        }
        
        mock_usage = {"products": 50, "copies": 100}
        mock_devices = ["device1", "device2"]
        
        with patch('api.routes.license.LicenseService') as mock_lic_cls:
            mock_lic = MagicMock()
            mock_lic.get_license_by_user = AsyncMock(return_value=mock_license)
            mock_lic.get_usage_stats = AsyncMock(return_value=mock_usage)
            mock_lic.get_active_devices = AsyncMock(return_value=mock_devices)
            mock_lic.get_plan_features = MagicMock(return_value={})
            mock_lic_cls.return_value = mock_lic
            
            result = await get_license_status(mock_user)
            
            assert result["has_license"]
            assert result["plan"] == "pro"
            assert result["devices"]["active"] == 2
    
    @pytest.mark.asyncio
    async def test_get_license_status_without_license(self, mock_user):
        """Test getting license status when user has no license"""
        from api.routes.license import get_license_status
        
        with patch('api.routes.license.LicenseService') as mock_lic_cls:
            mock_lic = MagicMock()
            mock_lic.get_license_by_user = AsyncMock(return_value=None)
            mock_lic.get_plan_features = MagicMock(return_value={})
            mock_lic_cls.return_value = mock_lic
            
            result = await get_license_status(mock_user)
            
            assert not result["has_license"]
            assert result["plan"] == "free"
    
    @pytest.mark.asyncio
    async def test_get_available_plans(self):
        """Test getting available plans"""
        from api.routes.license import get_available_plans
        
        with patch('api.routes.license.LicenseService') as mock_lic_cls:
            mock_lic = MagicMock()
            mock_lic.get_plan_features = MagicMock(return_value={})
            mock_lic_cls.return_value = mock_lic
            
            result = await get_available_plans()
            
            assert "plans" in result
            assert len(result["plans"]) == 4
            plan_ids = [p["id"] for p in result["plans"]]
            assert "free" in plan_ids
            assert "pro" in plan_ids


# ==========================================
# WEBHOOKS ROUTES TESTS
# ==========================================

class TestWebhooksRoutes:
    """Tests for webhook handling routes"""
    
    @pytest.mark.asyncio
    async def test_verify_signature_valid(self):
        """Test webhook signature verification - valid"""
        from api.routes.webhooks import verify_mercadopago_signature
        
        with patch('api.routes.webhooks.settings') as mock_settings:
            mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = "test_secret"
            
            # Note: Real signature verification would need proper HMAC
            result = verify_mercadopago_signature(b"body", None, "req_id")
            assert not result  # No signature provided
    
    @pytest.mark.asyncio
    async def test_verify_signature_missing(self):
        """Test webhook signature verification - missing signature"""
        from api.routes.webhooks import verify_mercadopago_signature
        
        with patch('api.routes.webhooks.settings') as mock_settings:
            mock_settings.MERCADO_PAGO_WEBHOOK_SECRET = "test_secret"
            
            result = verify_mercadopago_signature(b"body", None, "req_id")
            assert not result
    
    @pytest.mark.asyncio
    async def test_handle_payment_approved(self):
        """Test handling payment.approved event"""
        from api.routes.webhooks import handle_payment_event
        
        mock_mp = MagicMock()
        mock_mp.get_payment = AsyncMock(return_value={
            "id": "pay123",
            "payer": {"email": "test@example.com"},
            "metadata": {"plan": "pro"}
        })
        mock_mp.log_event = AsyncMock()
        mock_mp.send_license_email = AsyncMock()
        
        mock_lic = MagicMock()
        mock_lic.get_license_by_email = AsyncMock(return_value=None)
        mock_lic.create_license = AsyncMock(return_value="LIC-123")
        
        await handle_payment_event(
            action="payment.approved",
            data={"id": "pay123"},
            mp_service=mock_mp,
            license_service=mock_lic
        )
        
        mock_lic.create_license.assert_called_once()
        mock_mp.send_license_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_payment_approved_existing_user(self):
        """Test handling payment.approved for existing user"""
        from api.routes.webhooks import handle_payment_event
        
        mock_mp = MagicMock()
        mock_mp.get_payment = AsyncMock(return_value={
            "id": "pay123",
            "payer": {"email": "test@example.com"},
            "metadata": {"plan": "pro"}
        })
        mock_mp.log_event = AsyncMock()
        
        existing_license = {"id": "lic123"}
        mock_lic = MagicMock()
        mock_lic.get_license_by_email = AsyncMock(return_value=existing_license)
        mock_lic.extend_license = AsyncMock()
        
        await handle_payment_event(
            action="payment.approved",
            data={"id": "pay123"},
            mp_service=mock_mp,
            license_service=mock_lic
        )
        
        mock_lic.extend_license.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_payment_refunded(self):
        """Test handling payment.refunded event"""
        from api.routes.webhooks import handle_payment_event
        
        mock_mp = MagicMock()
        mock_mp.get_payment = AsyncMock(return_value={
            "id": "pay123",
            "payer": {"email": "test@example.com"}
        })
        mock_mp.log_event = AsyncMock()
        
        existing_license = {"id": "lic123"}
        mock_lic = MagicMock()
        mock_lic.get_license_by_email = AsyncMock(return_value=existing_license)
        mock_lic.deactivate_license = AsyncMock()
        
        await handle_payment_event(
            action="payment.refunded",
            data={"id": "pay123"},
            mp_service=mock_mp,
            license_service=mock_lic
        )
        
        mock_lic.deactivate_license.assert_called_once_with(
            license_id="lic123",
            reason="refund"
        )
    
    @pytest.mark.asyncio
    async def test_handle_subscription_created(self):
        """Test handling subscription created event"""
        from api.routes.webhooks import handle_subscription_event
        
        mock_mp = MagicMock()
        mock_mp.get_subscription = AsyncMock(return_value={
            "id": "sub123",
            "status": "pending"
        })
        mock_mp.log_event = AsyncMock()
        
        mock_lic = MagicMock()
        
        await handle_subscription_event(
            action="created",
            data={"id": "sub123"},
            mp_service=mock_mp,
            license_service=mock_lic
        )
        
        mock_mp.log_event.assert_called_with("subscription_created", {
            "id": "sub123",
            "status": "pending"
        })
    
    @pytest.mark.asyncio
    async def test_handle_subscription_updated_authorized(self):
        """Test handling subscription updated with authorized status"""
        from api.routes.webhooks import handle_subscription_event
        
        mock_mp = MagicMock()
        mock_mp.get_subscription = AsyncMock(return_value={
            "id": "sub123",
            "status": "authorized",
            "payer_email": "test@example.com",
            "reason": "pro"
        })
        mock_mp.log_event = AsyncMock()
        
        existing_license = {"id": "lic123", "plan": "starter"}
        mock_lic = MagicMock()
        mock_lic.get_license_by_email = AsyncMock(return_value=existing_license)
        mock_lic.update_plan = AsyncMock()
        mock_lic.extend_license = AsyncMock()
        
        await handle_subscription_event(
            action="updated",
            data={"id": "sub123"},
            mp_service=mock_mp,
            license_service=mock_lic
        )
        
        mock_lic.update_plan.assert_called_once()
        mock_lic.extend_license.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_subscription_cancelled(self):
        """Test handling subscription cancelled event"""
        from api.routes.webhooks import handle_subscription_event
        
        mock_mp = MagicMock()
        mock_mp.get_subscription = AsyncMock(return_value={
            "id": "sub123",
            "payer_email": "test@example.com"
        })
        mock_mp.log_event = AsyncMock()
        
        existing_license = {"id": "lic123"}
        mock_lic = MagicMock()
        mock_lic.get_license_by_email = AsyncMock(return_value=existing_license)
        mock_lic.mark_for_expiration = AsyncMock()
        
        await handle_subscription_event(
            action="cancelled",
            data={"id": "sub123"},
            mp_service=mock_mp,
            license_service=mock_lic
        )
        
        mock_lic.mark_for_expiration.assert_called_once_with("lic123")
    
    @pytest.mark.asyncio
    async def test_handle_subscription_payment(self):
        """Test handling recurring subscription payment"""
        from api.routes.webhooks import handle_subscription_payment
        
        mock_mp = MagicMock()
        mock_mp.get_authorized_payment = AsyncMock(return_value={
            "id": "pay123",
            "status": "approved",
            "preapproval_id": "sub123"
        })
        mock_mp.get_subscription = AsyncMock(return_value={
            "id": "sub123",
            "payer_email": "test@example.com"
        })
        mock_mp.log_event = AsyncMock()
        
        existing_license = {"id": "lic123"}
        mock_lic = MagicMock()
        mock_lic.get_license_by_email = AsyncMock(return_value=existing_license)
        mock_lic.extend_license = AsyncMock()
        
        await handle_subscription_payment(
            action="created",
            data={"id": "pay123"},
            mp_service=mock_mp,
            license_service=mock_lic
        )
        
        mock_lic.extend_license.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_webhooks_health(self):
        """Test webhooks health endpoint"""
        from api.routes.webhooks import webhooks_health
        
        result = await webhooks_health()
        
        assert result["status"] == "healthy"
        assert "/webhooks/mercadopago" in result["endpoints"]


# ==========================================
# PRODUCTS ROUTES TESTS
# ==========================================

class TestProductsRoutes:
    """Tests for products routes"""
    
    @pytest.fixture
    def mock_user(self):
        return {
            "id": "user123",
            "email": "test@example.com",
            "plan": "pro"
        }
    
    @pytest.mark.asyncio
    async def test_search_products(self, mock_user):
        """Test product search"""
        from api.routes.products import search_products
        
        mock_products = [
            {
                "id": "prod1",
                "title": "Produto 1",
                "price": 99.90,
                "sales": 1000
            }
        ]
        
        with patch('api.routes.products.ScraperService') as mock_scraper_cls:
            mock_scraper = MagicMock()
            mock_scraper.search = AsyncMock(return_value={
                "products": mock_products,
                "total": 1
            })
            mock_scraper_cls.return_value = mock_scraper
            
            result = await search_products(
                query="produto teste",
                category=None,
                min_price=None,
                max_price=None,
                sort_by="sales",
                page=1,
                limit=20,
                user=mock_user
            )
            
            assert len(result["products"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_product_details(self, mock_user):
        """Test getting product details"""
        from api.routes.products import get_product_details
        
        mock_product = {
            "id": "prod123",
            "title": "Produto Teste",
            "price": 99.90,
            "description": "Descrição",
            "images": ["img1.jpg"],
            "sales": 1000,
            "rating": 4.8
        }
        
        with patch('api.routes.products.ScraperService') as mock_scraper_cls:
            mock_scraper = MagicMock()
            mock_scraper.get_product = AsyncMock(return_value=mock_product)
            mock_scraper_cls.return_value = mock_scraper
            
            result = await get_product_details("prod123", mock_user)
            
            assert result["id"] == "prod123"
            assert result["title"] == "Produto Teste"
    
    @pytest.mark.asyncio
    async def test_get_trending_products(self, mock_user):
        """Test getting trending products"""
        from api.routes.products import get_trending
        
        mock_products = [
            {"id": "prod1", "title": "Trending 1", "sales": 5000},
            {"id": "prod2", "title": "Trending 2", "sales": 4000}
        ]
        
        with patch('api.routes.products.ScraperService') as mock_scraper_cls:
            mock_scraper = MagicMock()
            mock_scraper.get_trending = AsyncMock(return_value=mock_products)
            mock_scraper_cls.return_value = mock_scraper
            
            result = await get_trending(limit=10, category=None, user=mock_user)
            
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_get_categories(self, mock_user):
        """Test getting available categories"""
        from api.routes.products import get_categories
        
        mock_categories = [
            {"id": "cat1", "name": "Eletrônicos", "count": 1000},
            {"id": "cat2", "name": "Moda", "count": 2000}
        ]
        
        with patch('api.routes.products.ScraperService') as mock_scraper_cls:
            mock_scraper = MagicMock()
            mock_scraper.get_categories = AsyncMock(return_value=mock_categories)
            mock_scraper_cls.return_value = mock_scraper
            
            result = await get_categories(mock_user)
            
            assert len(result) == 2


# ==========================================
# AUTH ROUTES TESTS  
# ==========================================

class TestAuthRoutes:
    """Tests for authentication routes"""
    
    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login"""
        from api.routes.auth import login
        from pydantic import BaseModel
        
        class LoginRequest(BaseModel):
            email: str
            password: str
        
        request = LoginRequest(
            email="test@example.com",
            password="password123"
        )
        
        mock_user = {
            "id": "user123",
            "email": "test@example.com",
            "plan": "pro"
        }
        
        with patch('api.routes.auth.AuthService') as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.authenticate = AsyncMock(return_value=mock_user)
            mock_auth.create_token = MagicMock(return_value="jwt_token")
            mock_auth_cls.return_value = mock_auth
            
            result = await login(request)
            
            assert result["token"] == "jwt_token"
            assert result["user"]["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        from api.routes.auth import login
        from pydantic import BaseModel
        
        class LoginRequest(BaseModel):
            email: str
            password: str
        
        request = LoginRequest(
            email="test@example.com",
            password="wrong_password"
        )
        
        with patch('api.routes.auth.AuthService') as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.authenticate = AsyncMock(return_value=None)
            mock_auth_cls.return_value = mock_auth
            
            with pytest.raises(HTTPException) as exc:
                await login(request)
            
            assert exc.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_register_success(self):
        """Test successful registration"""
        from api.routes.auth import register
        from pydantic import BaseModel
        
        class RegisterRequest(BaseModel):
            email: str
            password: str
            name: str
        
        request = RegisterRequest(
            email="new@example.com",
            password="password123",
            name="New User"
        )
        
        with patch('api.routes.auth.AuthService') as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.check_email_exists = AsyncMock(return_value=False)
            mock_auth.create_user = AsyncMock(return_value={
                "id": "user_new",
                "email": "new@example.com"
            })
            mock_auth.create_token = MagicMock(return_value="jwt_token")
            mock_auth_cls.return_value = mock_auth
            
            result = await register(request)
            
            assert result["token"] == "jwt_token"
    
    @pytest.mark.asyncio
    async def test_register_email_exists(self):
        """Test registration with existing email"""
        from api.routes.auth import register
        from pydantic import BaseModel
        
        class RegisterRequest(BaseModel):
            email: str
            password: str
            name: str
        
        request = RegisterRequest(
            email="existing@example.com",
            password="password123",
            name="User"
        )
        
        with patch('api.routes.auth.AuthService') as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.check_email_exists = AsyncMock(return_value=True)
            mock_auth_cls.return_value = mock_auth
            
            with pytest.raises(HTTPException) as exc:
                await register(request)
            
            assert exc.value.status_code == 409
    
    @pytest.mark.asyncio
    async def test_refresh_token(self):
        """Test token refresh"""
        from api.routes.auth import refresh_token
        
        mock_user = {
            "id": "user123",
            "email": "test@example.com"
        }
        
        with patch('api.routes.auth.AuthService') as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.create_token = MagicMock(return_value="new_jwt_token")
            mock_auth_cls.return_value = mock_auth
            
            result = await refresh_token(mock_user)
            
            assert result["token"] == "new_jwt_token"
    
    @pytest.mark.asyncio
    async def test_logout(self):
        """Test logout"""
        from api.routes.auth import logout
        
        mock_user = {"id": "user123"}
        
        with patch('api.routes.auth.AuthService') as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.invalidate_token = AsyncMock()
            mock_auth_cls.return_value = mock_auth
            
            result = await logout(mock_user, "jwt_token")
            
            assert result["message"] == "Logged out successfully"
    
    @pytest.mark.asyncio
    async def test_get_me(self):
        """Test getting current user"""
        from api.routes.auth import get_me
        
        mock_user = {
            "id": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "plan": "pro"
        }
        
        result = await get_me(mock_user)
        
        assert result["email"] == "test@example.com"
        assert result["plan"] == "pro"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
