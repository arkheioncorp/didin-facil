"""
Comprehensive tests for credits.py routes.
Target: Increase coverage from 40% to 90%+
"""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {"id": "user-123", "email": "test@example.com", "name": "Test User"}


@pytest.fixture
def mock_admin_user():
    """Mock admin user."""
    return {"id": "admin-123", "email": "admin@example.com", "name": "Admin", "is_admin": True}


@pytest.fixture
def mock_db():
    """Mock database session."""
    mock = AsyncMock()
    mock.fetch_one = AsyncMock()
    mock.fetch_all = AsyncMock()
    mock.execute = AsyncMock()
    mock.commit = AsyncMock()
    mock.add = MagicMock()
    return mock


@pytest.fixture
def mock_package():
    """Mock credit package."""
    mock = MagicMock()
    mock.id = uuid.uuid4()
    mock.name = "Pro Pack"
    mock.slug = "pro"
    mock.credits = 100
    mock.price_brl = Decimal("49.90")
    mock.price_per_credit = Decimal("0.50")
    mock.original_price = Decimal("59.90")
    mock.discount_percent = 15
    mock.description = "Best value pack"
    mock.badge = "Popular"
    mock.is_featured = True
    mock.is_active = True
    return mock


@pytest.fixture
def mock_inactive_package(mock_package):
    """Mock inactive credit package."""
    mock_package.is_active = False
    return mock_package


# ============================================
# GET PACKAGES TESTS
# ============================================

class TestGetCreditPackages:
    """Tests for GET /packages endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_packages_success(self, mock_db, mock_package):
        """Test getting credit packages."""
        with patch("api.routes.credits.AccountingService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_active_packages = AsyncMock(return_value=[mock_package])
            
            from api.routes.credits import get_credit_packages
            
            result = await get_credit_packages(db=mock_db)
            
            assert len(result) == 1
            assert result[0].name == "Pro Pack"
            assert result[0].credits == 100
    
    @pytest.mark.asyncio
    async def test_get_packages_with_savings(self, mock_db, mock_package):
        """Test packages show savings when discounted."""
        with patch("api.routes.credits.AccountingService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_active_packages = AsyncMock(return_value=[mock_package])
            
            from api.routes.credits import get_credit_packages
            
            result = await get_credit_packages(db=mock_db)
            
            assert result[0].savings == 10.0  # 59.90 - 49.90
    
    @pytest.mark.asyncio
    async def test_get_packages_no_original_price(self, mock_db, mock_package):
        """Test packages without original price."""
        mock_package.original_price = None
        
        with patch("api.routes.credits.AccountingService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_active_packages = AsyncMock(return_value=[mock_package])
            
            from api.routes.credits import get_credit_packages
            
            result = await get_credit_packages(db=mock_db)
            
            assert result[0].savings is None
    
    @pytest.mark.asyncio
    async def test_get_packages_empty(self, mock_db):
        """Test when no packages available."""
        with patch("api.routes.credits.AccountingService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_active_packages = AsyncMock(return_value=[])
            
            from api.routes.credits import get_credit_packages
            
            result = await get_credit_packages(db=mock_db)
            
            assert len(result) == 0


# ============================================
# PURCHASE CREDITS TESTS
# ============================================

class TestPurchaseCredits:
    """Tests for POST /purchase endpoint."""
    
    @pytest.mark.asyncio
    async def test_purchase_with_pix(self, mock_user, mock_db, mock_package):
        """Test purchasing credits with PIX."""
        pix_response = {
            "id": "pix-123",
            "qr_code": "00020126...",
            "qr_code_base64": "base64...",
            "copy_paste": "copia-e-cola...",
            "date_of_expiration": "2024-01-01T12:00:00Z"
        }
        
        with patch("api.routes.credits.AccountingService") as MockService, \
             patch("api.routes.credits.MercadoPagoService") as MockMP, \
             patch("api.routes.credits._store_pending_purchase", new_callable=AsyncMock):
            
            mock_service = MockService.return_value
            mock_service.get_package_by_slug = AsyncMock(return_value=mock_package)
            
            mock_mp = MockMP.return_value
            mock_mp.create_pix_payment = AsyncMock(return_value=pix_response)
            
            from api.routes.credits import (CreditsPurchaseRequest,
                                            purchase_credits)
            
            request = CreditsPurchaseRequest(
                package_slug="pro",
                payment_method="pix",
                cpf="12345678900"
            )
            
            result = await purchase_credits(
                request=request,
                current_user=mock_user,
                db=mock_db
            )
            
            assert "CRED-" in result.order_id
            assert result.status == "pending"
            assert result.pix_qr_code == "00020126..."
    
    @pytest.mark.asyncio
    async def test_purchase_with_card(self, mock_user, mock_db, mock_package):
        """Test purchasing credits with card."""
        preference_response = {
            "id": "pref-123",
            "init_point": "https://www.mercadopago.com/checkout/v1/redirect?pref_id=123"
        }
        
        with patch("api.routes.credits.AccountingService") as MockService, \
             patch("api.routes.credits.MercadoPagoService") as MockMP, \
             patch("api.routes.credits._store_pending_purchase", new_callable=AsyncMock):
            
            mock_service = MockService.return_value
            mock_service.get_package_by_slug = AsyncMock(return_value=mock_package)
            
            mock_mp = MockMP.return_value
            mock_mp.create_payment = AsyncMock(return_value=preference_response)
            
            from api.routes.credits import (CreditsPurchaseRequest,
                                            purchase_credits)
            
            request = CreditsPurchaseRequest(
                package_slug="pro",
                payment_method="card"
            )
            
            result = await purchase_credits(
                request=request,
                current_user=mock_user,
                db=mock_db
            )
            
            assert result.payment_url == preference_response["init_point"]
            assert result.status == "pending"
    
    @pytest.mark.asyncio
    async def test_purchase_package_not_found(self, mock_user, mock_db):
        """Test purchasing non-existent package."""
        with patch("api.routes.credits.AccountingService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_package_by_slug = AsyncMock(return_value=None)
            
            from api.routes.credits import (CreditsPurchaseRequest,
                                            purchase_credits)
            from fastapi import HTTPException
            
            request = CreditsPurchaseRequest(
                package_slug="nonexistent",
                payment_method="pix"
            )
            
            with pytest.raises(HTTPException) as exc:
                await purchase_credits(
                    request=request,
                    current_user=mock_user,
                    db=mock_db
                )
            
            assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_purchase_inactive_package(self, mock_user, mock_db, mock_inactive_package):
        """Test purchasing inactive package."""
        with patch("api.routes.credits.AccountingService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_package_by_slug = AsyncMock(return_value=mock_inactive_package)
            
            from api.routes.credits import (CreditsPurchaseRequest,
                                            purchase_credits)
            from fastapi import HTTPException
            
            request = CreditsPurchaseRequest(
                package_slug="pro",
                payment_method="pix"
            )
            
            with pytest.raises(HTTPException) as exc:
                await purchase_credits(
                    request=request,
                    current_user=mock_user,
                    db=mock_db
                )
            
            assert exc.value.status_code == 400
            assert "não está mais disponível" in str(exc.value.detail)
    
    @pytest.mark.asyncio
    async def test_purchase_payment_error(self, mock_user, mock_db, mock_package):
        """Test handling payment error."""
        with patch("api.routes.credits.AccountingService") as MockService, \
             patch("api.routes.credits.MercadoPagoService") as MockMP:
            
            mock_service = MockService.return_value
            mock_service.get_package_by_slug = AsyncMock(return_value=mock_package)
            
            mock_mp = MockMP.return_value
            mock_mp.create_pix_payment = AsyncMock(side_effect=Exception("API Error"))
            
            from api.routes.credits import (CreditsPurchaseRequest,
                                            purchase_credits)
            from fastapi import HTTPException
            
            request = CreditsPurchaseRequest(
                package_slug="pro",
                payment_method="pix"
            )
            
            with pytest.raises(HTTPException) as exc:
                await purchase_credits(
                    request=request,
                    current_user=mock_user,
                    db=mock_db
                )
            
            assert exc.value.status_code == 500


# ============================================
# GET BALANCE TESTS
# ============================================

class TestGetCreditBalance:
    """Tests for GET /balance endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_balance_success(self, mock_user, mock_db):
        """Test getting credit balance."""
        mock_db.fetch_one = AsyncMock(side_effect=[
            {"credits_balance": 100, "credits_purchased": 200, "credits_used": 100},
            {"last_purchase_at": datetime(2024, 1, 1)}
        ])
        
        from api.routes.credits import get_credit_balance
        
        result = await get_credit_balance(current_user=mock_user, db=mock_db)
        
        assert result.balance == 100
        assert result.total_purchased == 200
        assert result.total_used == 100
    
    @pytest.mark.asyncio
    async def test_get_balance_no_data(self, mock_user, mock_db):
        """Test getting balance when no user data."""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        from api.routes.credits import get_credit_balance
        
        result = await get_credit_balance(current_user=mock_user, db=mock_db)
        
        assert result.balance == 0
        assert result.total_purchased == 0
    
    @pytest.mark.asyncio
    async def test_get_balance_no_summary(self, mock_user, mock_db):
        """Test balance when no financial summary exists."""
        mock_db.fetch_one = AsyncMock(side_effect=[
            {"credits_balance": 50, "credits_purchased": 50, "credits_used": 0},
            None
        ])
        
        from api.routes.credits import get_credit_balance
        
        result = await get_credit_balance(current_user=mock_user, db=mock_db)
        
        assert result.balance == 50
        assert result.last_purchase_at is None


# ============================================
# USE CREDITS TESTS
# ============================================

class TestUseCredits:
    """Tests for POST /use endpoint."""
    
    @pytest.mark.asyncio
    async def test_use_credits_success(self, mock_user, mock_db):
        """Test using credits successfully."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(
            credits_balance=100,
            bonus_balance=50,
            bonus_expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        from api.routes.credits import UseCreditsRequest, use_credits
        
        request = UseCreditsRequest(
            amount=20,
            operation="ai_copy",
            resource_id="doc-123"
        )
        
        result = await use_credits(
            request=request,
            current_user=mock_user,
            db=mock_db
        )
        
        assert result.success is True
        assert result.credits_used == 20
    
    @pytest.mark.asyncio
    async def test_use_credits_bonus_first(self, mock_user, mock_db):
        """Test that bonus credits are used first."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(
            credits_balance=100,
            bonus_balance=30,
            bonus_expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        from api.routes.credits import UseCreditsRequest, use_credits
        
        request = UseCreditsRequest(
            amount=25,
            operation="search"
        )
        
        result = await use_credits(
            request=request,
            current_user=mock_user,
            db=mock_db
        )
        
        assert result.bonus_used == 25  # All from bonus (max 30)
    
    @pytest.mark.asyncio
    async def test_use_credits_insufficient(self, mock_user, mock_db):
        """Test using credits when insufficient balance."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(
            credits_balance=10,
            bonus_balance=5,
            bonus_expires_at=None
        )
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        from api.routes.credits import UseCreditsRequest, use_credits
        from fastapi import HTTPException
        
        request = UseCreditsRequest(
            amount=50,
            operation="export"
        )
        
        with pytest.raises(HTTPException) as exc:
            await use_credits(
                request=request,
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc.value.status_code == 402
        assert "insuficientes" in str(exc.value.detail)
    
    @pytest.mark.asyncio
    async def test_use_credits_user_not_found(self, mock_user, mock_db):
        """Test using credits when user not found."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        from api.routes.credits import UseCreditsRequest, use_credits
        from fastapi import HTTPException
        
        request = UseCreditsRequest(
            amount=10,
            operation="ai_copy"
        )
        
        with pytest.raises(HTTPException) as exc:
            await use_credits(
                request=request,
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_use_credits_expired_bonus(self, mock_user, mock_db):
        """Test that expired bonus credits are not used."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(
            credits_balance=50,
            bonus_balance=100,
            bonus_expires_at=datetime.now(timezone.utc) - timedelta(days=1)  # Expired
        )
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        from api.routes.credits import UseCreditsRequest, use_credits
        
        request = UseCreditsRequest(
            amount=10,
            operation="search"
        )
        
        result = await use_credits(
            request=request,
            current_user=mock_user,
            db=mock_db
        )
        
        # Bonus should be 0 due to expiration
        assert result.bonus_used == 0


# ============================================
# ADD BONUS CREDITS TESTS
# ============================================

class TestAddBonusCredits:
    """Tests for POST /bonus/add endpoint."""
    
    @pytest.mark.asyncio
    async def test_add_bonus_success(self, mock_admin_user, mock_db):
        """Test adding bonus credits as admin."""
        from api.routes.credits import AddBonusRequest, add_bonus_credits
        
        request = AddBonusRequest(
            user_id="user-456",
            amount=50,
            reason="Promotion",
            expires_in_days=30
        )
        
        result = await add_bonus_credits(
            request=request,
            current_user=mock_admin_user,
            db=mock_db
        )
        
        assert result["success"] is True
        assert result["bonus_added"] == 50
        assert result["user_id"] == "user-456"
    
    @pytest.mark.asyncio
    async def test_add_bonus_not_admin(self, mock_user, mock_db):
        """Test adding bonus credits as non-admin."""
        from api.routes.credits import AddBonusRequest, add_bonus_credits
        from fastapi import HTTPException
        
        request = AddBonusRequest(
            user_id="user-456",
            amount=50,
            reason="Promotion"
        )
        
        with pytest.raises(HTTPException) as exc:
            await add_bonus_credits(
                request=request,
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc.value.status_code == 403


# ============================================
# GET PURCHASE STATUS TESTS
# ============================================

class TestGetPurchaseStatus:
    """Tests for GET /status/{order_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_status_success(self, mock_user, mock_db):
        """Test getting purchase status."""
        mock_transaction = MagicMock()
        mock_transaction.payment_status = "approved"
        mock_transaction.credits_amount = 100
        mock_transaction.amount_brl = Decimal("49.90")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_transaction
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        from api.routes.credits import get_purchase_status
        
        result = await get_purchase_status(
            order_id="CRED-20240101-ABC123",
            current_user=mock_user,
            db=mock_db
        )
        
        assert result["status"] == "approved"
        assert result["credits"] == 100
    
    @pytest.mark.asyncio
    async def test_get_status_not_found(self, mock_user, mock_db):
        """Test getting status for non-existent order."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        from api.routes.credits import get_purchase_status
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await get_purchase_status(
                order_id="nonexistent",
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc.value.status_code == 404


# ============================================
# GET PURCHASE HISTORY TESTS
# ============================================

class TestGetPurchaseHistory:
    """Tests for GET /history endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_history_success(self, mock_user, mock_db):
        """Test getting purchase history."""
        mock_transaction = MagicMock()
        mock_transaction.id = uuid.uuid4()
        mock_transaction.transaction_type = "credit_purchase"
        mock_transaction.operation_type = "purchase"
        mock_transaction.credits_amount = 100
        mock_transaction.amount_brl = Decimal("49.90")
        mock_transaction.description = "Pro Pack"
        mock_transaction.payment_status = "approved"
        mock_transaction.created_at = datetime.now()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_transaction]
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        from api.routes.credits import get_purchase_history
        
        result = await get_purchase_history(
            limit=20,
            offset=0,
            current_user=mock_user,
            db=mock_db
        )
        
        assert len(result) == 1
        assert result[0]["type"] == "credit_purchase"
    
    @pytest.mark.asyncio
    async def test_get_history_empty(self, mock_user, mock_db):
        """Test getting empty history."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        from api.routes.credits import get_purchase_history
        
        result = await get_purchase_history(
            limit=20,
            offset=0,
            current_user=mock_user,
            db=mock_db
        )
        
        assert len(result) == 0


# ============================================
# WEBHOOK TESTS
# ============================================

class TestMercadoPagoWebhook:
    """Tests for POST /webhook/mercadopago endpoint."""
    
    @pytest.mark.asyncio
    async def test_webhook_approved_payment(self, mock_db):
        """Test webhook for approved payment."""
        mock_transaction = MagicMock()
        mock_transaction.user_id = uuid.uuid4()
        mock_transaction.credits_amount = 100
        mock_transaction.amount_brl = Decimal("49.90")
        mock_transaction.payment_status = "pending"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_transaction
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with patch("api.routes.credits.MercadoPagoService") as MockMP, \
             patch("api.routes.credits.AccountingService") as MockAccounting:
            mock_mp = MockMP.return_value
            mock_mp.get_payment = AsyncMock(return_value={
                "external_reference": "CRED-20240101-ABC",
                "status": "approved"
            })
            
            mock_accounting = MockAccounting.return_value
            mock_accounting._update_user_financial_summary = AsyncMock()
            
            from api.routes.credits import mercadopago_credits_webhook
            
            result = await mercadopago_credits_webhook(
                data={"type": "payment", "data": {"id": "pay-123"}},
                db=mock_db
            )
            
            assert result["status"] == "credits_added"
            assert result["credits"] == 100
    
    @pytest.mark.asyncio
    async def test_webhook_rejected_payment(self, mock_db):
        """Test webhook for rejected payment."""
        mock_transaction = MagicMock()
        mock_transaction.payment_status = "pending"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_transaction
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with patch("api.routes.credits.MercadoPagoService") as MockMP:
            mock_mp = MockMP.return_value
            mock_mp.get_payment = AsyncMock(return_value={
                "external_reference": "CRED-20240101-ABC",
                "status": "rejected"
            })
            
            from api.routes.credits import mercadopago_credits_webhook
            
            result = await mercadopago_credits_webhook(
                data={"type": "payment", "data": {"id": "pay-123"}},
                db=mock_db
            )
            
            assert result["status"] == "rejected"
    
    @pytest.mark.asyncio
    async def test_webhook_not_payment_type(self, mock_db):
        """Test webhook for non-payment event."""
        from api.routes.credits import mercadopago_credits_webhook
        
        result = await mercadopago_credits_webhook(
            data={"type": "test", "data": {}},
            db=mock_db
        )
        
        assert result["status"] == "ignored"
    
    @pytest.mark.asyncio
    async def test_webhook_no_payment_id(self, mock_db):
        """Test webhook without payment ID."""
        from api.routes.credits import mercadopago_credits_webhook
        
        result = await mercadopago_credits_webhook(
            data={"type": "payment", "data": {}},
            db=mock_db
        )
        
        assert result["status"] == "no_payment_id"
    
    @pytest.mark.asyncio
    async def test_webhook_payment_not_found(self, mock_db):
        """Test webhook when payment not found at MP."""
        with patch("api.routes.credits.MercadoPagoService") as MockMP:
            mock_mp = MockMP.return_value
            mock_mp.get_payment = AsyncMock(return_value=None)
            
            from api.routes.credits import mercadopago_credits_webhook
            
            result = await mercadopago_credits_webhook(
                data={"type": "payment", "data": {"id": "pay-123"}},
                db=mock_db
            )
            
            assert result["status"] == "payment_not_found"
    
    @pytest.mark.asyncio
    async def test_webhook_not_credits_purchase(self, mock_db):
        """Test webhook for non-credits purchase."""
        with patch("api.routes.credits.MercadoPagoService") as MockMP:
            mock_mp = MockMP.return_value
            mock_mp.get_payment = AsyncMock(return_value={
                "external_reference": "SUB-123",  # Not a credits purchase
                "status": "approved"
            })
            
            from api.routes.credits import mercadopago_credits_webhook
            
            result = await mercadopago_credits_webhook(
                data={"type": "payment", "data": {"id": "pay-123"}},
                db=mock_db
            )
            
            assert result["status"] == "not_credits_purchase"
    
    @pytest.mark.asyncio
    async def test_webhook_transaction_not_found(self, mock_db):
        """Test webhook when transaction not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with patch("api.routes.credits.MercadoPagoService") as MockMP:
            mock_mp = MockMP.return_value
            mock_mp.get_payment = AsyncMock(return_value={
                "external_reference": "CRED-20240101-ABC",
                "status": "approved"
            })
            
            from api.routes.credits import mercadopago_credits_webhook
            
            result = await mercadopago_credits_webhook(
                data={"type": "payment", "data": {"id": "pay-123"}},
                db=mock_db
            )
            
            assert result["status"] == "transaction_not_found"


# ============================================
# HELPER FUNCTION TESTS
# ============================================

class TestStorePendingPurchase:
    """Tests for _store_pending_purchase helper."""
    
    @pytest.mark.asyncio
    async def test_store_pending_purchase(self, mock_db):
        """Test storing pending purchase."""
        from api.routes.credits import _store_pending_purchase
        
        await _store_pending_purchase(
            db=mock_db,
            user_id=str(uuid.uuid4()),
            package_id=str(uuid.uuid4()),
            order_id="CRED-20240101-ABC",
            amount=Decimal("49.90"),
            credits=100,
            payment_method="pix",
            payment_id="pay-123"
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


# ============================================
# MODEL VALIDATION TESTS
# ============================================

class TestModelValidation:
    """Tests for Pydantic model validation."""
    
    def test_credits_purchase_request_valid(self):
        """Test valid purchase request."""
        from api.routes.credits import CreditsPurchaseRequest
        
        request = CreditsPurchaseRequest(
            package_slug="pro",
            payment_method="pix",
            email="test@example.com",
            name="Test User",
            cpf="12345678900"
        )
        
        assert request.package_slug == "pro"
        assert request.payment_method == "pix"
    
    def test_use_credits_request_valid(self):
        """Test valid use credits request."""
        from api.routes.credits import UseCreditsRequest
        
        request = UseCreditsRequest(
            amount=50,
            operation="ai_copy",
            resource_id="doc-123"
        )
        
        assert request.amount == 50
        assert request.operation == "ai_copy"
    
    def test_use_credits_request_min_amount(self):
        """Test minimum amount validation."""
        from api.routes.credits import UseCreditsRequest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            UseCreditsRequest(amount=0, operation="test")
    
    def test_add_bonus_request_valid(self):
        """Test valid add bonus request."""
        from api.routes.credits import AddBonusRequest
        
        request = AddBonusRequest(
            user_id="user-123",
            amount=100,
            reason="Promo",
            expires_in_days=60
        )
        
        assert request.amount == 100
        assert request.expires_in_days == 60
