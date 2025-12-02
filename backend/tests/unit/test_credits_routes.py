"""
Testes para Credits Routes - api/routes/credits.py
Cobertura: get_credit_packages, purchase_credits, get_credit_balance,
           get_purchase_status, get_purchase_history, mercadopago_credits_webhook
"""
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ============================================
# MOCKS & FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """Mock de usuário autenticado"""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.name = "Test User"
    
    # Configurar __class__ para simular modelo SQLAlchemy
    # Usamos MagicMock para simular as colunas, não strings
    user_class = MagicMock()
    user_class.credits_balance = MagicMock()
    user_class.credits_purchased = MagicMock()
    user_class.credits_used = MagicMock()
    user_class.id = MagicMock()
    user.__class__ = user_class
    
    return user

@pytest.fixture
def mock_package():
    """Mock de pacote de créditos"""
    pkg = MagicMock()
    pkg.id = uuid.uuid4()
    pkg.name = "Starter Pack"
    pkg.slug = "starter"
    pkg.credits = 100
    pkg.price_brl = Decimal("50.00")
    pkg.price_per_credit = Decimal("0.50")
    pkg.original_price = Decimal("60.00")
    pkg.discount_percent = 10
    pkg.description = "Pacote inicial"
    pkg.badge = "Popular"
    pkg.is_featured = True
    pkg.is_active = True
    return pkg

@pytest.fixture
def mock_accounting_service(mock_package):
    """Mock do AccountingService"""
    service = AsyncMock()
    service.get_active_packages.return_value = [mock_package]
    service.get_package_by_slug.return_value = mock_package
    service._update_user_financial_summary.return_value = None
    return service

@pytest.fixture
def mock_mp_service():
    """Mock do MercadoPagoService"""
    service = AsyncMock()
    service.create_pix_payment.return_value = {
        "id": "123456",
        "qr_code": "pix-code",
        "qr_code_base64": "base64-code",
        "copy_paste": "copy-paste-code",
        "date_of_expiration": "2024-12-31T23:59:59"
    }
    service.create_payment.return_value = {
        "id": "123456",
        "init_point": "https://mercadopago.com/checkout/123"
    }
    service.get_payment.return_value = {
        "id": "123456",
        "status": "approved",
        "external_reference": "CRED-20240101-ABCDEF12"
    }
    return service

@pytest.fixture
def mock_db():
    """Mock do banco de dados"""
    db = AsyncMock()
    # Mock para execute/scalars/all
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    result_mock.scalar_one_or_none.return_value = None
    result_mock.fetchone.return_value = None
    db.execute.return_value = result_mock
    return db

# ============================================
# TESTS: Get Packages
# ============================================

class TestGetPackages:
    """Testes do endpoint get_credit_packages"""
    
    @pytest.mark.asyncio
    async def test_get_packages_success(self, mock_db, mock_accounting_service, mock_package):
        """Deve listar pacotes de créditos com sucesso"""
        with patch("api.routes.credits.AccountingService", return_value=mock_accounting_service):
            from api.routes.credits import get_credit_packages
            
            response = await get_credit_packages(db=mock_db)
            
            assert len(response) == 1
            assert response[0].slug == "starter"
            assert response[0].credits == 100
            assert response[0].savings == 10.0  # 60 - 50

# ============================================
# TESTS: Purchase Credits
# ============================================

class TestPurchaseCredits:
    """Testes do endpoint purchase_credits"""
    
    @pytest.mark.asyncio
    async def test_purchase_pix_success(self, mock_user, mock_db, mock_accounting_service, mock_mp_service):
        """Deve criar pagamento PIX com sucesso"""
        with patch("api.routes.credits.AccountingService", return_value=mock_accounting_service),              patch("api.routes.credits.MercadoPagoService", return_value=mock_mp_service),              patch("api.routes.credits._store_pending_purchase", new_callable=AsyncMock) as mock_store:
            
            from api.routes.credits import (CreditsPurchaseRequest,
                                            purchase_credits)
            
            request = CreditsPurchaseRequest(
                package_slug="starter",
                payment_method="pix",
                cpf="12345678900"
            )
            
            response = await purchase_credits(request, current_user=mock_user, db=mock_db)
            
            assert response.status == "pending"
            assert response.pix_qr_code == "pix-code"
            assert response.amount == 47.5  # 50 * 0.95 (5% discount)
            mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_purchase_card_success(self, mock_user, mock_db, mock_accounting_service, mock_mp_service):
        """Deve criar preferência de cartão com sucesso"""
        with patch("api.routes.credits.AccountingService", return_value=mock_accounting_service),              patch("api.routes.credits.MercadoPagoService", return_value=mock_mp_service),              patch("api.routes.credits._store_pending_purchase", new_callable=AsyncMock) as mock_store:
            
            from api.routes.credits import (CreditsPurchaseRequest,
                                            purchase_credits)
            
            request = CreditsPurchaseRequest(
                package_slug="starter",
                payment_method="card"
            )
            
            response = await purchase_credits(request, current_user=mock_user, db=mock_db)
            
            assert response.status == "pending"
            assert response.payment_url == "https://mercadopago.com/checkout/123"
            assert response.amount == 50.0  # Sem desconto
            mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_purchase_package_not_found(self, mock_user, mock_db, mock_accounting_service):
        """Deve retornar erro se pacote não encontrado"""
        mock_accounting_service.get_package_by_slug.return_value = None
        
        with patch("api.routes.credits.AccountingService", return_value=mock_accounting_service):
            from api.routes.credits import (CreditsPurchaseRequest,
                                            purchase_credits)
            
            request = CreditsPurchaseRequest(package_slug="invalid", payment_method="pix")
            
            with pytest.raises(HTTPException) as exc:
                await purchase_credits(request, current_user=mock_user, db=mock_db)
            
            assert exc.value.status_code == 400
            assert "não encontrado" in exc.value.detail

    @pytest.mark.asyncio
    async def test_purchase_package_inactive(self, mock_user, mock_db, mock_accounting_service, mock_package):
        """Deve retornar erro se pacote inativo"""
        mock_package.is_active = False
        mock_accounting_service.get_package_by_slug.return_value = mock_package
        
        with patch("api.routes.credits.AccountingService", return_value=mock_accounting_service):
            from api.routes.credits import (CreditsPurchaseRequest,
                                            purchase_credits)
            
            request = CreditsPurchaseRequest(package_slug="starter", payment_method="pix")
            
            with pytest.raises(HTTPException) as exc:
                await purchase_credits(request, current_user=mock_user, db=mock_db)
            
            assert exc.value.status_code == 400
            assert "não está mais disponível" in exc.value.detail

    @pytest.mark.asyncio
    async def test_purchase_error(self, mock_user, mock_db, mock_accounting_service, mock_mp_service):
        """Deve retornar erro 500 se falhar ao processar pagamento"""
        mock_mp_service.create_pix_payment.side_effect = Exception("Payment error")
        
        with patch("api.routes.credits.AccountingService", return_value=mock_accounting_service),              patch("api.routes.credits.MercadoPagoService", return_value=mock_mp_service):
            
            from api.routes.credits import (CreditsPurchaseRequest,
                                            purchase_credits)
            
            request = CreditsPurchaseRequest(package_slug="starter", payment_method="pix")
            
            with pytest.raises(HTTPException) as exc:
                await purchase_credits(request, current_user=mock_user, db=mock_db)
            
            assert exc.value.status_code == 500
            assert "Erro ao processar pagamento" in exc.value.detail

# ============================================
# TESTS: Get Balance
# ============================================

class TestGetBalance:
    """Testes do endpoint get_credit_balance"""
    
    @pytest.mark.asyncio
    async def test_get_balance_success(self, mock_user, mock_db):
        """Deve retornar saldo do usuário"""
        # Mock do resultado da query de usuário (db.fetch_one retorna dict-like)
        user_row = {
            "credits_balance": 500,
            "credits_purchased": 1000,
            "credits_used": 500
        }
        
        # Mock do resultado da query de resumo
        summary_row = {"last_purchase_at": datetime(2024, 1, 1)}
        
        # Configurar db.fetch_one para retornar os mocks em sequência
        mock_db.fetch_one = AsyncMock(side_effect=[user_row, summary_row])
        
        from api.routes.credits import get_credit_balance
        
        response = await get_credit_balance(current_user=mock_user, db=mock_db)
        
        assert response.balance == 500
        assert response.total_purchased == 1000
        assert response.last_purchase_at == str(datetime(2024, 1, 1))

    @pytest.mark.asyncio
    async def test_get_balance_no_data(self, mock_user, mock_db):
        """Deve retornar zeros se não houver dados"""
        # Configurar db.fetch_one para retornar None
        mock_db.fetch_one = AsyncMock(side_effect=[None, None])
        
        from api.routes.credits import get_credit_balance
        
        response = await get_credit_balance(
            current_user=mock_user, db=mock_db
        )
        
        assert response.balance == 0
        assert response.total_purchased == 0
        assert response.last_purchase_at is None


# ============================================
# TESTS: Get Status & History
# ============================================

class TestStatusHistory:
    """Testes de status e histórico"""
    
    @pytest.mark.asyncio
    async def test_get_status_success(self, mock_user, mock_db):
        """Deve retornar status do pedido"""
        transaction = MagicMock()
        transaction.payment_status = "approved"
        transaction.credits_amount = 100
        transaction.amount_brl = Decimal("50.00")
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = transaction
        
        # Patch select para evitar erro do SQLAlchemy com MagicMock
        with patch("sqlalchemy.select") as mock_select:
            from api.routes.credits import get_purchase_status
            
            response = await get_purchase_status("ORDER-123", current_user=mock_user, db=mock_db)
            
            assert response["status"] == "approved"
            assert response["credits"] == 100
            assert response["amount"] == 50.0

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, mock_user, mock_db):
        """Deve retornar 404 se pedido não encontrado"""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Patch select para evitar erro do SQLAlchemy com MagicMock
        with patch("sqlalchemy.select") as mock_select:
            from api.routes.credits import get_purchase_status
            
            with pytest.raises(HTTPException) as exc:
                await get_purchase_status("ORDER-123", current_user=mock_user, db=mock_db)
            
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_history_success(self, mock_user, mock_db):
        """Deve retornar histórico de compras"""
        transaction = MagicMock()
        transaction.id = uuid.uuid4()
        transaction.transaction_type = "credit_purchase"
        transaction.operation_type = "purchase"
        transaction.credits_amount = 100
        transaction.amount_brl = Decimal("50.00")
        transaction.description = "Compra de créditos"
        transaction.payment_status = "approved"
        transaction.created_at = datetime(2024, 1, 1)
        
        mock_db.execute.return_value.scalars.return_value.all.return_value = [transaction]
        
        # Patch select para evitar erro do SQLAlchemy com MagicMock
        with patch("sqlalchemy.select") as mock_select:
            from api.routes.credits import get_purchase_history

            # Passar limit e offset explicitamente para evitar erro com Query()
            response = await get_purchase_history(
                limit=20, 
                offset=0, 
                current_user=mock_user, 
                db=mock_db
            )
            
            assert len(response) == 1
            assert response[0]["credits"] == 100
            assert response[0]["status"] == "approved"

# ============================================
# TESTS: Webhook
# ============================================

class TestWebhook:
    """Testes do webhook do MercadoPago"""
    
    @pytest.mark.asyncio
    async def test_webhook_approved(self, mock_db, mock_mp_service, mock_accounting_service):
        """Deve processar pagamento aprovado"""
        # Mock da transação pendente
        transaction = MagicMock()
        transaction.user_id = uuid.uuid4()
        transaction.payment_id = "123456"
        transaction.credits_amount = 100
        transaction.amount_brl = Decimal("50.00")
        transaction.payment_status = "pending"
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = transaction
        
        # Patch select para evitar erro do SQLAlchemy com MagicMock
        with patch("sqlalchemy.select") as mock_select,              patch("api.routes.credits.MercadoPagoService", return_value=mock_mp_service),              patch("api.routes.credits.AccountingService", return_value=mock_accounting_service):
            
            from api.routes.credits import mercadopago_credits_webhook
            
            data = {
                "type": "payment",
                "data": {"id": "123456"}
            }
            
            response = await mercadopago_credits_webhook(data, db=mock_db)
            
            assert response["status"] == "credits_added"
            assert response["credits"] == 100
            assert transaction.payment_status == "approved"
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_webhook_ignored_type(self, mock_db):
        """Deve ignorar tipos diferentes de payment"""
        from api.routes.credits import mercadopago_credits_webhook
        
        response = await mercadopago_credits_webhook({"type": "subscription"}, db=mock_db)
        
        assert response["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_webhook_no_payment_id(self, mock_db):
        """Deve retornar erro se não houver ID de pagamento"""
        from api.routes.credits import mercadopago_credits_webhook
        
        response = await mercadopago_credits_webhook({"type": "payment", "data": {}}, db=mock_db)
        
        assert response["status"] == "no_payment_id"

    @pytest.mark.asyncio
    async def test_webhook_payment_not_found(self, mock_db, mock_mp_service):
        """Deve retornar erro se pagamento não encontrado no MP"""
        mock_mp_service.get_payment.return_value = None
        
        with patch("api.routes.credits.MercadoPagoService", return_value=mock_mp_service):
            from api.routes.credits import mercadopago_credits_webhook
            
            response = await mercadopago_credits_webhook(
                {"type": "payment", "data": {"id": "123"}}, 
                db=mock_db
            )
            
            assert response["status"] == "payment_not_found"

    @pytest.mark.asyncio
    async def test_webhook_not_credits_purchase(self, mock_db, mock_mp_service):
        """Deve retornar erro se não for compra de créditos"""
        mock_mp_service.get_payment.return_value = {
            "external_reference": "SUBS-123",
            "status": "approved"
        }
        
        with patch("api.routes.credits.MercadoPagoService", return_value=mock_mp_service):
            from api.routes.credits import mercadopago_credits_webhook
            
            response = await mercadopago_credits_webhook(
                {"type": "payment", "data": {"id": "123"}}, 
                db=mock_db
            )
            
            assert response["status"] == "not_credits_purchase"

    @pytest.mark.asyncio
    async def test_webhook_transaction_not_found(self, mock_db, mock_mp_service):
        """Deve retornar erro se transação não encontrada no DB"""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Patch select para evitar erro do SQLAlchemy com MagicMock
        with patch("sqlalchemy.select") as mock_select,              patch("api.routes.credits.MercadoPagoService", return_value=mock_mp_service):
            
            from api.routes.credits import mercadopago_credits_webhook
            
            response = await mercadopago_credits_webhook(
                {"type": "payment", "data": {"id": "123"}}, 
                db=mock_db
            )
            
            assert response["status"] == "transaction_not_found"

    @pytest.mark.asyncio
    async def test_webhook_rejected(self, mock_db, mock_mp_service):
        """Deve processar pagamento rejeitado"""
        transaction = MagicMock()
        transaction.payment_status = "pending"
        mock_db.execute.return_value.scalar_one_or_none.return_value = transaction
        
        mock_mp_service.get_payment.return_value = {
            "external_reference": "CRED-123",
            "status": "rejected"
        }
        
        # Patch select para evitar erro do SQLAlchemy com MagicMock
        with patch("sqlalchemy.select") as mock_select,              patch("api.routes.credits.MercadoPagoService", return_value=mock_mp_service):
            
            from api.routes.credits import mercadopago_credits_webhook
            
            response = await mercadopago_credits_webhook(
                {"type": "payment", "data": {"id": "123"}}, 
                db=mock_db
            )
            
            assert response["status"] == "rejected"
            assert transaction.payment_status == "rejected"
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_webhook_cancelled(self, mock_db, mock_mp_service):
        """Deve processar pagamento cancelado"""
        transaction = MagicMock()
        transaction.payment_status = "pending"
        mock_db.execute.return_value.scalar_one_or_none.return_value = transaction
        
        mock_mp_service.get_payment.return_value = {
            "external_reference": "CRED-123",
            "status": "cancelled"
        }
        
        with patch("sqlalchemy.select") as mock_select,              patch("api.routes.credits.MercadoPagoService", return_value=mock_mp_service):
            
            from api.routes.credits import mercadopago_credits_webhook
            
            response = await mercadopago_credits_webhook(
                {"type": "payment", "data": {"id": "123"}}, 
                db=mock_db
            )
            
            assert response["status"] == "cancelled"
            assert transaction.payment_status == "cancelled"

    @pytest.mark.asyncio
    async def test_webhook_pending_status(self, mock_db, mock_mp_service):
        """Deve retornar pending para status não final"""
        transaction = MagicMock()
        transaction.payment_status = "pending"
        mock_db.execute.return_value.scalar_one_or_none.return_value = transaction
        
        mock_mp_service.get_payment.return_value = {
            "external_reference": "CRED-123",
            "status": "in_process"
        }
        
        with patch("sqlalchemy.select") as mock_select,              patch("api.routes.credits.MercadoPagoService", return_value=mock_mp_service):
            
            from api.routes.credits import mercadopago_credits_webhook
            
            response = await mercadopago_credits_webhook(
                {"type": "payment", "data": {"id": "123"}}, 
                db=mock_db
            )
            
            assert response["status"] == "pending"


# ============================================
# TESTS: Use Credits
# ============================================

class TestUseCredits:
    """Testes do endpoint use_credits"""
    
    @pytest.fixture
    def mock_user_dict(self):
        """Mock de usuário como dict"""
        return {
            "id": uuid.uuid4(),
            "email": "test@example.com",
            "name": "Test User",
            "is_admin": False
        }
    
    @pytest.mark.asyncio
    async def test_use_credits_success(self, mock_db, mock_user_dict):
        """Deve consumir créditos com sucesso"""
        from datetime import datetime, timedelta, timezone

        # Mock resultado da query com saldo
        row = MagicMock()
        row.credits_balance = 100
        row.bonus_balance = 50
        row.bonus_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        mock_db.execute.return_value.fetchone.return_value = row
        
        with patch("sqlalchemy.select"), patch("sqlalchemy.update"):
            from api.routes.credits import UseCreditsRequest, use_credits
            
            request = UseCreditsRequest(
                amount=20,
                operation="ai_copy",
                resource_id="test-123"
            )
            
            response = await use_credits(request, current_user=mock_user_dict, db=mock_db)
            
            assert response.success is True
            assert response.credits_used == 20
            assert response.bonus_used == 20  # Usa bonus primeiro
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_use_credits_regular_credits(self, mock_db, mock_user_dict):
        """Deve consumir créditos regulares quando bonus não é suficiente"""
        from datetime import datetime, timedelta, timezone
        
        row = MagicMock()
        row.credits_balance = 100
        row.bonus_balance = 10
        row.bonus_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        mock_db.execute.return_value.fetchone.return_value = row
        
        with patch("sqlalchemy.select"), patch("sqlalchemy.update"):
            from api.routes.credits import UseCreditsRequest, use_credits
            
            request = UseCreditsRequest(amount=50, operation="search")
            
            response = await use_credits(request, current_user=mock_user_dict, db=mock_db)
            
            assert response.success is True
            assert response.credits_used == 50
            assert response.bonus_used == 10
            assert response.new_balance == 60  # 100 - 40 + 0 bonus

    @pytest.mark.asyncio
    async def test_use_credits_insufficient_balance(self, mock_db, mock_user_dict):
        """Deve retornar erro quando saldo é insuficiente"""
        row = MagicMock()
        row.credits_balance = 10
        row.bonus_balance = 5
        row.bonus_expires_at = None
        mock_db.execute.return_value.fetchone.return_value = row
        
        with patch("sqlalchemy.select"):
            from api.routes.credits import UseCreditsRequest, use_credits
            
            request = UseCreditsRequest(amount=100, operation="ai_copy")
            
            with pytest.raises(HTTPException) as exc:
                await use_credits(request, current_user=mock_user_dict, db=mock_db)
            
            assert exc.value.status_code == 402
            assert "Créditos insuficientes" in exc.value.detail

    @pytest.mark.asyncio
    async def test_use_credits_expired_bonus(self, mock_db, mock_user_dict):
        """Deve ignorar bonus expirado"""
        from datetime import datetime, timedelta, timezone
        
        row = MagicMock()
        row.credits_balance = 100
        row.bonus_balance = 500  # Muito bonus, mas expirado
        row.bonus_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        mock_db.execute.return_value.fetchone.return_value = row
        
        with patch("sqlalchemy.select"), patch("sqlalchemy.update"):
            from api.routes.credits import UseCreditsRequest, use_credits
            
            request = UseCreditsRequest(amount=50, operation="export")
            
            response = await use_credits(request, current_user=mock_user_dict, db=mock_db)
            
            assert response.success is True
            assert response.bonus_used == 0  # Bonus expirado não foi usado
            assert response.new_balance == 50  # 100 - 50

    @pytest.mark.asyncio
    async def test_use_credits_user_not_found(self, mock_db, mock_user_dict):
        """Deve retornar 404 se usuário não encontrado"""
        mock_db.execute.return_value.fetchone.return_value = None
        
        with patch("sqlalchemy.select"):
            from api.routes.credits import UseCreditsRequest, use_credits
            
            request = UseCreditsRequest(amount=10, operation="ai_copy")
            
            with pytest.raises(HTTPException) as exc:
                await use_credits(request, current_user=mock_user_dict, db=mock_db)
            
            assert exc.value.status_code == 404
            assert "Usuário não encontrado" in exc.value.detail


# ============================================
# TESTS: Add Bonus Credits
# ============================================

class TestAddBonusCredits:
    """Testes do endpoint add_bonus_credits"""
    
    @pytest.fixture
    def mock_admin_user(self):
        """Mock de usuário admin"""
        return {
            "id": uuid.uuid4(),
            "email": "admin@example.com",
            "name": "Admin User",
            "is_admin": True
        }
    
    @pytest.fixture
    def mock_regular_user(self):
        """Mock de usuário regular"""
        return {
            "id": uuid.uuid4(),
            "email": "user@example.com",
            "name": "Regular User",
            "is_admin": False
        }
    
    @pytest.mark.asyncio
    async def test_add_bonus_success(self, mock_db, mock_admin_user):
        """Admin deve adicionar bonus com sucesso"""
        target_user_id = str(uuid.uuid4())
        
        with patch("sqlalchemy.select"), patch("sqlalchemy.update"):
            from api.routes.credits import AddBonusRequest, add_bonus_credits
            
            request = AddBonusRequest(
                user_id=target_user_id,
                amount=100,
                reason="Promoção especial",
                expires_in_days=60
            )
            
            response = await add_bonus_credits(request, current_user=mock_admin_user, db=mock_db)
            
            assert response["success"] is True
            assert response["bonus_added"] == 100
            assert response["user_id"] == target_user_id
            assert response["reason"] == "Promoção especial"
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_add_bonus_forbidden_non_admin(self, mock_db, mock_regular_user):
        """Usuário não-admin deve receber erro 403"""
        from api.routes.credits import AddBonusRequest, add_bonus_credits
        
        request = AddBonusRequest(
            user_id=str(uuid.uuid4()),
            amount=100,
            reason="Tentativa não autorizada"
        )
        
        with pytest.raises(HTTPException) as exc:
            await add_bonus_credits(request, current_user=mock_regular_user, db=mock_db)
        
        assert exc.value.status_code == 403
        assert "administradores" in exc.value.detail

    @pytest.mark.asyncio
    async def test_add_bonus_default_expiry(self, mock_db, mock_admin_user):
        """Deve usar expiração padrão de 30 dias"""
        from datetime import datetime, timedelta, timezone
        
        with patch("sqlalchemy.select"), patch("sqlalchemy.update"):
            from api.routes.credits import AddBonusRequest, add_bonus_credits
            
            request = AddBonusRequest(
                user_id=str(uuid.uuid4()),
                amount=50,
                reason="Teste default"
            )
            
            response = await add_bonus_credits(request, current_user=mock_admin_user, db=mock_db)
            
            expires_at = datetime.fromisoformat(response["expires_at"].replace("Z", "+00:00"))
            expected_min = datetime.now(timezone.utc) + timedelta(days=29)
            expected_max = datetime.now(timezone.utc) + timedelta(days=31)
            
            assert expected_min < expires_at < expected_max


# ============================================
# TESTS: Store Pending Purchase (Helper)
# ============================================

class TestStorePendingPurchase:
    """Testes da função _store_pending_purchase"""
    
    @pytest.mark.asyncio
    async def test_store_pending_purchase_success(self, mock_db):
        """Deve armazenar transação pendente com sucesso"""
        from api.routes.credits import _store_pending_purchase
        
        await _store_pending_purchase(
            db=mock_db,
            user_id=str(uuid.uuid4()),
            package_id=str(uuid.uuid4()),
            order_id="CRED-20240101-ABC123",
            amount=Decimal("50.00"),
            credits=100,
            payment_method="pix",
            payment_id="mp-payment-123"
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verificar que transação foi criada corretamente
        call_args = mock_db.add.call_args[0][0]
        assert call_args.credits_amount == 100
        assert call_args.amount_brl == Decimal("50.00")
        assert call_args.payment_method == "pix"

    @pytest.mark.asyncio
    async def test_store_pending_purchase_card_method(self, mock_db):
        """Deve armazenar transação com cartão"""
        from api.routes.credits import _store_pending_purchase
        
        await _store_pending_purchase(
            db=mock_db,
            user_id=str(uuid.uuid4()),
            package_id=str(uuid.uuid4()),
            order_id="CRED-20240101-DEF456",
            amount=Decimal("100.00"),
            credits=200,
            payment_method="card",
            payment_id="mp-card-456"
        )
        
        call_args = mock_db.add.call_args[0][0]
        assert call_args.payment_method == "card"
        assert call_args.credits_amount == 200


# ============================================
# TESTS: Package Edge Cases
# ============================================

class TestPackageEdgeCases:
    """Testes de casos específicos de pacotes"""
    
    @pytest.mark.asyncio
    async def test_package_without_original_price(self, mock_db):
        """Pacote sem preço original não deve ter savings"""
        pkg = MagicMock()
        pkg.id = uuid.uuid4()
        pkg.name = "Basic"
        pkg.slug = "basic"
        pkg.credits = 50
        pkg.price_brl = Decimal("25.00")
        pkg.price_per_credit = Decimal("0.50")
        pkg.original_price = None
        pkg.discount_percent = 0
        pkg.description = None
        pkg.badge = None
        pkg.is_featured = False
        
        mock_service = AsyncMock()
        mock_service.get_active_packages.return_value = [pkg]
        
        with patch("api.routes.credits.AccountingService", return_value=mock_service):
            from api.routes.credits import get_credit_packages
            
            response = await get_credit_packages(db=mock_db)
            
            assert len(response) == 1
            assert response[0].savings is None
            assert response[0].discount_percent == 0

    @pytest.mark.asyncio
    async def test_package_same_price_no_savings(self, mock_db):
        """Pacote com mesmo preço original não deve ter savings"""
        pkg = MagicMock()
        pkg.id = uuid.uuid4()
        pkg.name = "Standard"
        pkg.slug = "standard"
        pkg.credits = 100
        pkg.price_brl = Decimal("50.00")
        pkg.price_per_credit = Decimal("0.50")
        pkg.original_price = Decimal("50.00")  # Mesmo preço
        pkg.discount_percent = 0
        pkg.description = "Sem desconto"
        pkg.badge = None
        pkg.is_featured = False
        
        mock_service = AsyncMock()
        mock_service.get_active_packages.return_value = [pkg]
        
        with patch("api.routes.credits.AccountingService", return_value=mock_service):
            from api.routes.credits import get_credit_packages
            
            response = await get_credit_packages(db=mock_db)
            
            assert len(response) == 1
            # Savings deve ser None pois preço original não é maior
            assert response[0].savings is None

    @pytest.mark.asyncio
    async def test_empty_packages_list(self, mock_db):
        """Deve retornar lista vazia se não houver pacotes"""
        mock_service = AsyncMock()
        mock_service.get_active_packages.return_value = []
        
        with patch("api.routes.credits.AccountingService", return_value=mock_service):
            from api.routes.credits import get_credit_packages
            
            response = await get_credit_packages(db=mock_db)
            
            assert response == []


# ============================================
# TESTS: Purchase with Boleto
# ============================================

class TestPurchaseBoleto:
    """Testes de compra com boleto"""
    
    @pytest.fixture
    def mock_user_dict(self):
        return {
            "id": uuid.uuid4(),
            "email": "user@test.com",
            "name": "Test User",
            "is_admin": False
        }
    
    @pytest.mark.asyncio
    async def test_purchase_boleto_success(self, mock_user_dict, mock_db, mock_accounting_service, mock_mp_service):
        """Deve criar preferência de boleto com sucesso"""
        with patch("api.routes.credits.AccountingService", return_value=mock_accounting_service),              patch("api.routes.credits.MercadoPagoService", return_value=mock_mp_service),              patch("api.routes.credits._store_pending_purchase", new_callable=AsyncMock):
            
            from api.routes.credits import (CreditsPurchaseRequest,
                                            purchase_credits)
            
            request = CreditsPurchaseRequest(
                package_slug="starter",
                payment_method="boleto"
            )
            
            response = await purchase_credits(request, current_user=mock_user_dict, db=mock_db)
            
            assert response.status == "pending"
            assert response.payment_url == "https://mercadopago.com/checkout/123"
