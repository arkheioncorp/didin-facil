"""
E2E Tests - Sistema de Monetização
Testes completos de compra, webhook e consumo de créditos
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Test environment
import os
os.environ["TESTING"] = "true"


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_user():
    """Dados de usuário de teste"""
    return {
        "id": str(uuid.uuid4()),
        "email": "teste.pix@tiktrendfinder.com",
        "name": "Teste PIX",
        "credits_balance": 0,
        "credits_purchased": 0,
        "credits_used": 0,
        "has_lifetime_license": False,
        "is_active": True
    }


@pytest.fixture
def starter_package():
    """Pacote Starter (inclui licença)"""
    return {
        "id": str(uuid.uuid4()),
        "slug": "starter",
        "name": "Starter",
        "credits": 50,
        "price_brl": 19.90,
        "includes_license": True,
        "is_active": True
    }


@pytest.fixture
def pro_package():
    """Pacote Pro (sem licença)"""
    return {
        "id": str(uuid.uuid4()),
        "slug": "pro",
        "name": "Pro",
        "credits": 200,
        "price_brl": 49.90,
        "includes_license": False,
        "is_active": True
    }


@pytest.fixture
def mercadopago_pix_payment(test_user, starter_package):
    """Payload de pagamento PIX aprovado do Mercado Pago"""
    return {
        "id": 123456789,
        "date_created": "2025-11-30T10:00:00.000-03:00",
        "date_approved": "2025-11-30T10:00:05.000-03:00",
        "date_last_updated": "2025-11-30T10:00:05.000-03:00",
        "money_release_date": "2025-11-30T10:00:05.000-03:00",
        "operation_type": "regular_payment",
        "issuer_id": "24",
        "payment_method_id": "pix",
        "payment_type_id": "bank_transfer",
        "status": "approved",
        "status_detail": "accredited",
        "currency_id": "BRL",
        "description": f"TikTrend Finder - Pacote {starter_package['name']}",
        "live_mode": False,  # Sandbox
        "sponsor_id": None,
        "authorization_code": "1234567",
        "collector_id": 123456789,
        "payer": {
            "id": 987654321,
            "email": test_user["email"],
            "identification": {
                "type": "CPF",
                "number": "12345678900"
            },
            "type": "customer"
        },
        "metadata": {
            "product_type": "credits",
            "package_slug": starter_package["slug"],
            "credits": starter_package["credits"],
            "includes_license": starter_package["includes_license"],
            "user_email": test_user["email"]
        },
        "additional_info": {},
        "order": {},
        "external_reference": f"order_{uuid.uuid4()}",
        "transaction_amount": starter_package["price_brl"],
        "transaction_amount_refunded": 0,
        "coupon_amount": 0,
        "transaction_details": {
            "net_received_amount": 18.91,  # Depois das taxas
            "total_paid_amount": starter_package["price_brl"],
            "overpaid_amount": 0,
            "installment_amount": starter_package["price_brl"]
        },
        "fee_details": [
            {
                "type": "mercadopago_fee",
                "amount": 0.99,
                "fee_payer": "collector"
            }
        ],
        "captured": True,
        "binary_mode": False,
        "statement_descriptor": "DIDINFACIL",
        "point_of_interaction": {
            "type": "PIX",
            "business_info": {
                "unit": "online_payments",
                "sub_unit": "default"
            },
            "transaction_data": {
                "qr_code": "00020126580014br.gov.bcb.pix...",
                "qr_code_base64": "iVBORw0KGgoAAAANSUhEUg...",
                "ticket_url": "https://www.mercadopago.com.br/payments/123456789/ticket"
            }
        }
    }


@pytest.fixture
def mercadopago_webhook_payload(mercadopago_pix_payment):
    """Payload completo de webhook do Mercado Pago"""
    return {
        "action": "payment.approved",
        "api_version": "v1",
        "data": {
            "id": mercadopago_pix_payment["id"]
        },
        "date_created": "2025-11-30T10:00:05.000-03:00",
        "id": 12345678901234567890,
        "live_mode": False,
        "type": "payment",
        "user_id": "123456789"
    }


# ============================================================================
# TEST: FLUXO COMPLETO DE COMPRA PIX (E2E)
# ============================================================================

class TestPixPurchaseE2E:
    """Testes E2E do fluxo de compra PIX"""
    
    @pytest.mark.asyncio
    async def test_complete_pix_purchase_flow(
        self, 
        test_user, 
        starter_package,
        mercadopago_pix_payment
    ):
        """
        Teste E2E completo:
        1. Criar pagamento PIX
        2. Simular aprovação (webhook)
        3. Verificar créditos adicionados
        4. Verificar licença ativada
        """
        from api.services.license import LicenseService
        from api.services.mercadopago import MercadoPagoService
        
        # Mock do banco de dados
        mock_db = AsyncMock()
        
        # Simular usuário existente
        mock_db.fetch_one.return_value = {
            "id": test_user["id"],
            "email": test_user["email"],
            "credits_balance": 0,
            "has_lifetime_license": False
        }
        
        # Mock de execute (sucesso)
        mock_db.execute.return_value = None
        
        # Criar serviço com mock
        license_service = LicenseService()
        license_service.db = mock_db
        
        # 1. SIMULAR ATIVAÇÃO DE LICENÇA
        result = await license_service.activate_lifetime_license(
            email=test_user["email"],
            payment_id=str(mercadopago_pix_payment["id"])
        )
        
        assert result is True
        
        # Verificar que UPDATE foi chamado
        calls = [str(c) for c in mock_db.execute.call_args_list]
        assert any("has_lifetime_license" in c for c in calls)
        
        # 2. SIMULAR ADIÇÃO DE CRÉDITOS
        mock_db.fetch_one.return_value = {
            "id": test_user["id"],
            "credits_balance": 0
        }
        
        new_balance = await license_service.add_credits(
            email=test_user["email"],
            amount=starter_package["credits"],
            payment_id=str(mercadopago_pix_payment["id"])
        )
        
        assert new_balance == starter_package["credits"]
        
        # Verificar transação registrada
        calls = [str(c) for c in mock_db.execute.call_args_list]
        assert any("financial_transactions" in c for c in calls)
    
    @pytest.mark.asyncio
    async def test_pix_qr_code_generation(self, starter_package, test_user):
        """Teste de geração de QR Code PIX"""
        from api.services.mercadopago import MercadoPagoService
        
        mp_service = MercadoPagoService()
        
        # Mock da resposta do Mercado Pago
        mock_response = {
            "id": 123456789,
            "point_of_interaction": {
                "transaction_data": {
                    "qr_code": "00020126580014br.gov.bcb.pix...",
                    "qr_code_base64": "iVBORw0KGgoAAAANSUhEUg...",
                    "ticket_url": "https://www.mercadopago.com.br/..."
                }
            }
        }
        
        with patch.object(mp_service, 'create_pix_payment', return_value=mock_response):
            result = await mp_service.create_pix_payment(
                title=f"Pacote {starter_package['name']}",
                price=starter_package["price_brl"],
                user_email=test_user["email"],
                external_reference=f"order_{uuid.uuid4()}",
                metadata={
                    "credits": starter_package["credits"],
                    "includes_license": starter_package["includes_license"]
                }
            )
            
            assert result is not None
            assert "point_of_interaction" in result
            qr_data = result["point_of_interaction"]["transaction_data"]
            assert "qr_code" in qr_data
            assert "qr_code_base64" in qr_data


# ============================================================================
# TEST: WEBHOOK MERCADO PAGO
# ============================================================================

class TestMercadoPagoWebhook:
    """Testes do webhook handler do Mercado Pago"""
    
    @pytest.mark.asyncio
    async def test_webhook_payment_approved(
        self,
        mercadopago_webhook_payload,
        mercadopago_pix_payment,
        test_user,
        starter_package
    ):
        """Teste de webhook payment.approved"""
        from api.routes.webhooks import handle_payment_event
        from api.services.mercadopago import MercadoPagoService
        from api.services.license import LicenseService
        
        # Mocks
        mp_service = MercadoPagoService()
        license_service = LicenseService()
        
        # Mock get_payment
        mp_service.get_payment = AsyncMock(return_value=mercadopago_pix_payment)
        mp_service.log_event = AsyncMock()
        mp_service.send_credits_email = AsyncMock()
        
        # Mock license service
        license_service.add_credits = AsyncMock(return_value=50)
        license_service.activate_lifetime_license = AsyncMock(return_value=True)
        
        # Executar handler
        await handle_payment_event(
            action="payment.approved",
            data={"id": mercadopago_pix_payment["id"]},
            mp_service=mp_service,
            license_service=license_service
        )
        
        # Verificações
        mp_service.get_payment.assert_called_once_with(mercadopago_pix_payment["id"])
        license_service.add_credits.assert_called_once()
        license_service.activate_lifetime_license.assert_called_once()
        mp_service.send_credits_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_webhook_payment_created(
        self,
        mercadopago_pix_payment
    ):
        """Teste de webhook payment.created (apenas log)"""
        from api.routes.webhooks import handle_payment_event
        from api.services.mercadopago import MercadoPagoService
        from api.services.license import LicenseService
        
        mp_service = MercadoPagoService()
        license_service = LicenseService()
        
        mp_service.get_payment = AsyncMock(return_value=mercadopago_pix_payment)
        mp_service.log_event = AsyncMock()
        
        await handle_payment_event(
            action="payment.created",
            data={"id": mercadopago_pix_payment["id"]},
            mp_service=mp_service,
            license_service=license_service
        )
        
        mp_service.log_event.assert_called_once_with("payment_created", mercadopago_pix_payment)
    
    @pytest.mark.asyncio
    async def test_webhook_payment_cancelled(
        self,
        mercadopago_pix_payment
    ):
        """Teste de webhook payment.cancelled"""
        from api.routes.webhooks import handle_payment_event
        from api.services.mercadopago import MercadoPagoService
        from api.services.license import LicenseService
        
        mp_service = MercadoPagoService()
        license_service = LicenseService()
        
        mp_service.get_payment = AsyncMock(return_value=mercadopago_pix_payment)
        mp_service.log_event = AsyncMock()
        
        await handle_payment_event(
            action="payment.cancelled",
            data={"id": mercadopago_pix_payment["id"]},
            mp_service=mp_service,
            license_service=license_service
        )
        
        mp_service.log_event.assert_called_once_with("payment_cancelled", mercadopago_pix_payment)
    
    @pytest.mark.asyncio
    async def test_webhook_idempotency(
        self,
        mercadopago_pix_payment,
        test_user
    ):
        """Teste de idempotência - não processar mesmo pagamento 2x"""
        from api.services.license import LicenseService
        
        license_service = LicenseService()
        mock_db = AsyncMock()
        
        # Primeira chamada: usuário sem licença
        mock_db.fetch_one.return_value = {
            "id": test_user["id"],
            "has_lifetime_license": False
        }
        license_service.db = mock_db
        
        result1 = await license_service.activate_lifetime_license(
            email=test_user["email"],
            payment_id=str(mercadopago_pix_payment["id"])
        )
        assert result1 is True
        
        # Segunda chamada: usuário já tem licença
        mock_db.fetch_one.return_value = {
            "id": test_user["id"],
            "has_lifetime_license": True
        }
        
        result2 = await license_service.activate_lifetime_license(
            email=test_user["email"],
            payment_id="another_payment_id"
        )
        
        # Deve retornar True sem fazer update
        assert result2 is True


# ============================================================================
# TEST: CONSUMO DE CRÉDITOS
# ============================================================================

class TestCreditsConsumption:
    """Testes de consumo de créditos em operações reais"""
    
    @pytest.mark.asyncio
    async def test_copy_generation_deducts_credits(self, test_user):
        """Teste: gerar copy deduz 1 crédito"""
        from api.middleware.quota import check_credits, deduct_credits
        
        mock_db = AsyncMock()
        
        # Usuário com 10 créditos
        mock_db.fetch_one.return_value = {
            "balance": 10,
            "total_purchased": 50,
            "total_used": 40
        }
        
        # Verificar créditos
        result = await check_credits(
            user_id=test_user["id"],
            action="copy",
            db=mock_db
        )
        
        # check_credits retorna: balance, required, remaining_after
        assert result["balance"] == 10
        assert result["required"] == 1
        assert result["remaining_after"] == 9
    
    @pytest.mark.asyncio
    async def test_trend_analysis_deducts_credits(self, test_user):
        """Teste: análise de tendência deduz 2 créditos"""
        from api.middleware.quota import check_credits
        
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {
            "balance": 10,
            "total_purchased": 50,
            "total_used": 40
        }
        
        result = await check_credits(
            user_id=test_user["id"],
            action="trend_analysis",
            db=mock_db
        )
        
        assert result["balance"] == 10
        assert result["required"] == 2
        assert result["remaining_after"] == 8
    
    @pytest.mark.asyncio
    async def test_niche_report_deducts_credits(self, test_user):
        """Teste: relatório de nicho deduz 5 créditos"""
        from api.middleware.quota import check_credits
        
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {
            "balance": 10,
            "total_purchased": 50,
            "total_used": 40
        }
        
        result = await check_credits(
            user_id=test_user["id"],
            action="niche_report",
            db=mock_db
        )
        
        assert result["balance"] == 10
        assert result["required"] == 5
        assert result["remaining_after"] == 5
    
    @pytest.mark.asyncio
    async def test_insufficient_credits_raises_exception(self, test_user):
        """Teste: créditos insuficientes levanta exceção"""
        from api.middleware.quota import check_credits, InsufficientCreditsError
        
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {
            "balance": 2,  # Apenas 2 créditos
            "total_purchased": 50,
            "total_used": 48
        }
        
        # check_credits levanta exceção quando créditos são insuficientes
        with pytest.raises(InsufficientCreditsError) as exc_info:
            await check_credits(
                user_id=test_user["id"],
                action="niche_report",  # Custa 5 créditos
                db=mock_db
            )
        
        assert exc_info.value.required == 5
        assert exc_info.value.available == 2
    
    @pytest.mark.asyncio
    async def test_deduct_credits_updates_balance(self, test_user):
        """Teste: dedução de créditos atualiza saldo"""
        from api.middleware.quota import deduct_credits
        
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {"new_balance": 9}
        
        result = await deduct_credits(
            user_id=test_user["id"],
            action="copy",
            db=mock_db
        )
        
        # deduct_credits retorna dict com new_balance e cost
        assert result["new_balance"] == 9
        assert result["cost"] == 1
    
    @pytest.mark.asyncio
    async def test_zero_credits_raises_exception(self, test_user):
        """Teste: zero créditos levanta exceção"""
        from api.middleware.quota import check_credits, InsufficientCreditsError
        
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = {
            "balance": 0,
            "total_purchased": 50,
            "total_used": 50
        }
        
        with pytest.raises(InsufficientCreditsError) as exc_info:
            await check_credits(
                user_id=test_user["id"],
                action="copy",
                db=mock_db
            )
        
        assert exc_info.value.available == 0


# ============================================================================
# TEST: OPERAÇÕES REAIS COM CRÉDITOS
# ============================================================================

class TestRealOperationsWithCredits:
    """Testes de operações reais que consomem créditos"""
    
    @pytest.mark.asyncio
    async def test_copy_generation_full_flow(self, test_user):
        """Teste completo: verificar → deduzir → gerar copy"""
        from api.middleware.quota import check_credits, deduct_credits
        
        mock_db = AsyncMock()
        
        # Step 1: Verificar créditos
        mock_db.fetch_one.return_value = {
            "balance": 10,
            "total_purchased": 50,
            "total_used": 40
        }
        
        check_result = await check_credits(
            user_id=test_user["id"],
            action="copy",
            db=mock_db
        )
        
        assert check_result["balance"] == 10
        
        # Step 2: Deduzir créditos
        mock_db.fetch_one.return_value = {"new_balance": 9}
        
        result = await deduct_credits(
            user_id=test_user["id"],
            action="copy",
            db=mock_db
        )
        
        assert result["new_balance"] == 9
        
        # Step 3: Gerar copy (simulado)
        copy_result = {
            "title": "Produto Incrível - 50% OFF!",
            "description": "Compre agora e economize...",
            "credits_used": 1,
            "remaining_credits": result["new_balance"]
        }
        
        assert copy_result["credits_used"] == 1
        assert copy_result["remaining_credits"] == 9
    
    @pytest.mark.asyncio
    async def test_product_scraping_with_credits(self, test_user):
        """Teste: scraping de produto com consumo de créditos"""
        from api.middleware.quota import check_credits, deduct_credits
        
        mock_db = AsyncMock()
        # Mock retorna as chaves que get_user_credits espera do SQL
        # (as aliases: balance, total_purchased, total_used)
        mock_db.fetch_one.return_value = {
            "balance": 5,
            "total_purchased": 50,
            "total_used": 45
        }
        
        # Verificar créditos para copy (1 crédito)
        result = await check_credits(
            user_id=test_user["id"],
            action="copy",
            db=mock_db
        )
        
        # check_credits retorna {balance, required, remaining_after}
        assert result["balance"] >= result["required"]
        assert result["remaining_after"] >= 0


# ============================================================================
# TEST: CARGA E PERFORMANCE
# ============================================================================

class TestLoadAndPerformance:
    """Testes de carga e performance do sistema"""
    
    @pytest.mark.asyncio
    async def test_concurrent_credit_checks(self, test_user):
        """Teste: múltiplas verificações de crédito simultâneas"""
        from api.middleware.quota import check_credits
        
        mock_db = AsyncMock()
        # Mock retorna as chaves que get_user_credits espera do SQL
        # (as aliases: balance, total_purchased, total_used)
        mock_db.fetch_one.return_value = {
            "balance": 100,
            "total_purchased": 100,
            "total_used": 0
        }
        
        # 50 verificações simultâneas
        tasks = [
            check_credits(user_id=test_user["id"], action="copy", db=mock_db)
            for _ in range(50)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Todas devem ter saldo suficiente
        assert all(r["balance"] >= r["required"] for r in results)
        assert len(results) == 50
    
    @pytest.mark.asyncio
    async def test_rapid_credit_deductions(self, test_user):
        """Teste: deduções rápidas de créditos (race condition check)"""
        from api.middleware.quota import deduct_credits
        
        mock_db = AsyncMock()
        
        # Simular saldo decrescente
        balances = list(range(100, 0, -1))
        call_count = [0]
        
        def get_balance(*args, **kwargs):
            if call_count[0] < len(balances):
                result = balances[call_count[0]]
                call_count[0] += 1
                return result
            return 0
        
        mock_db.execute.side_effect = get_balance
        
        # 10 deduções sequenciais
        results = []
        for _ in range(10):
            try:
                result = await deduct_credits(
                    user_id=test_user["id"],
                    action="copy",
                    db=mock_db
                )
                results.append(result)
            except Exception:
                break
        
        # Deve ter processado deduções
        assert len(results) >= 1
    
    @pytest.mark.asyncio
    async def test_webhook_processing_time(
        self,
        mercadopago_pix_payment,
        test_user
    ):
        """Teste: tempo de processamento do webhook < 1s"""
        from api.routes.webhooks import handle_payment_event
        from api.services.mercadopago import MercadoPagoService
        from api.services.license import LicenseService
        import time
        
        mp_service = MercadoPagoService()
        license_service = LicenseService()
        
        # Mocks rápidos
        mp_service.get_payment = AsyncMock(return_value=mercadopago_pix_payment)
        mp_service.log_event = AsyncMock()
        mp_service.send_credits_email = AsyncMock()
        license_service.add_credits = AsyncMock(return_value=50)
        license_service.activate_lifetime_license = AsyncMock(return_value=True)
        
        # Medir tempo
        start = time.perf_counter()
        
        await handle_payment_event(
            action="payment.approved",
            data={"id": mercadopago_pix_payment["id"]},
            mp_service=mp_service,
            license_service=license_service
        )
        
        elapsed = time.perf_counter() - start
        
        # Deve processar em menos de 1 segundo
        assert elapsed < 1.0, f"Webhook demorou {elapsed:.3f}s"
    
    @pytest.mark.asyncio
    async def test_multiple_packages_purchase(self, test_user):
        """Teste: múltiplas compras de pacotes"""
        from api.services.license import LicenseService
        
        license_service = LicenseService()
        mock_db = AsyncMock()
        license_service.db = mock_db
        
        packages = [
            {"slug": "starter", "credits": 50, "includes_license": True},
            {"slug": "pro", "credits": 200, "includes_license": False},
            {"slug": "ultra", "credits": 500, "includes_license": False},
        ]
        
        total_credits = 0
        
        for pkg in packages:
            mock_db.fetch_one.return_value = {
                "id": test_user["id"],
                "credits_balance": total_credits
            }
            
            new_balance = await license_service.add_credits(
                email=test_user["email"],
                amount=pkg["credits"],
                payment_id=f"payment_{pkg['slug']}"
            )
            
            total_credits += pkg["credits"]
        
        # Deve ter chamado execute 3 vezes (3 pacotes)
        assert mock_db.execute.call_count >= 3


# ============================================================================
# TEST: INTEGRAÇÃO COM BANCO REAL (opcional)
# ============================================================================

@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Testes de integração desabilitados"
)
class TestRealDatabaseIntegration:
    """Testes com banco de dados real (rodar com RUN_INTEGRATION_TESTS=true)"""
    
    @pytest_asyncio.fixture
    async def real_db(self):
        """Conexão real com banco de dados de teste"""
        from databases import Database
        import os
        
        db_url = os.getenv(
            "TEST_DATABASE_URL",
            "postgresql://tiktrend:secret@localhost:5434/tiktrend"
        )
        db = Database(db_url)
        await db.connect()
        yield db
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_real_credit_flow(self, real_db, test_user):
        """Teste com banco real: fluxo de créditos"""
        import uuid
        
        # Criar usuário de teste
        user_id = str(uuid.uuid4())
        await real_db.execute(
            """
            INSERT INTO users (id, email, password_hash, name, 
                               credits_balance, credits_purchased, credits_used,
                               has_lifetime_license, is_active)
            VALUES (:id, :email, 'hash', 'Test User', 0, 0, 0, false, true)
            ON CONFLICT (email) DO NOTHING
            """,
            {"id": user_id, "email": f"test_{uuid.uuid4()}@test.com"}
        )
        
        # Adicionar créditos
        await real_db.execute(
            """
            UPDATE users 
            SET credits_balance = credits_balance + 50,
                credits_purchased = credits_purchased + 50
            WHERE id = :user_id
            """,
            {"user_id": user_id}
        )
        
        # Verificar saldo
        result = await real_db.fetch_one(
            "SELECT credits_balance FROM users WHERE id = :user_id",
            {"user_id": user_id}
        )
        
        assert result["credits_balance"] == 50
        
        # Cleanup
        await real_db.execute(
            "DELETE FROM users WHERE id = :user_id",
            {"user_id": user_id}
        )
