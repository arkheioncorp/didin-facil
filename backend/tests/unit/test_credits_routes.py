"""
Testes para Credits Routes - api/routes/credits.py
Cobertura: get_credit_packages, purchase_credits, get_credit_balance,
           get_purchase_status, get_purchase_history, mercadopago_credits_webhook
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException
import uuid

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
            
            from api.routes.credits import purchase_credits, CreditsPurchaseRequest
            
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
            
            from api.routes.credits import purchase_credits, CreditsPurchaseRequest
            
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
            from api.routes.credits import purchase_credits, CreditsPurchaseRequest
            
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
            from api.routes.credits import purchase_credits, CreditsPurchaseRequest
            
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
            
            from api.routes.credits import purchase_credits, CreditsPurchaseRequest
            
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
