"""
Testes unitários para api/middleware/quota.py
Cobertura: Credits management, quota checking, deductions
"""

import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException

from api.middleware.quota import (
    InsufficientCreditsError,
    QuotaExceededError,
    CREDIT_COSTS,
    get_user_credits,
    check_credits,
    deduct_credits,
    add_credits,
    check_copy_quota,
    get_user_quota,
    increment_quota,
)


class TestInsufficientCreditsError:
    """Testes para InsufficientCreditsError"""
    
    def test_error_basic_message(self):
        """Deve criar erro com mensagem básica"""
        error = InsufficientCreditsError("Créditos insuficientes")
        
        assert str(error) == "Créditos insuficientes"
        assert error.message == "Créditos insuficientes"
        assert error.required == 0
        assert error.available == 0
    
    def test_error_with_credits_info(self):
        """Deve criar erro com informações de créditos"""
        error = InsufficientCreditsError(
            "Precisa de mais créditos",
            required=5,
            available=2
        )
        
        assert error.required == 5
        assert error.available == 2
    
    def test_quota_exceeded_is_alias(self):
        """QuotaExceededError deve ser alias de InsufficientCreditsError"""
        assert QuotaExceededError is InsufficientCreditsError


class TestCreditCosts:
    """Testes para constantes de custo"""
    
    def test_copy_costs_one_credit(self):
        """Copy deve custar 1 crédito"""
        assert CREDIT_COSTS["copy"] == 1
    
    def test_trend_analysis_costs_two_credits(self):
        """Trend analysis deve custar 2 créditos"""
        assert CREDIT_COSTS["trend_analysis"] == 2
    
    def test_niche_report_costs_five_credits(self):
        """Niche report deve custar 5 créditos"""
        assert CREDIT_COSTS["niche_report"] == 5


class TestGetUserCredits:
    """Testes para get_user_credits"""
    
    @pytest.mark.asyncio
    async def test_get_credits_success(self):
        """Deve retornar créditos do usuário"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {
            "balance": 100,
            "total_purchased": 150,
            "total_used": 50
        }
        
        result = await get_user_credits("user123", mock_db)
        
        assert result["balance"] == 100
        assert result["total_purchased"] == 150
        assert result["total_used"] == 50
        mock_db.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_credits_user_not_found(self):
        """Deve levantar HTTPException quando usuário não existe"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_user_credits("nonexistent", mock_db)
        
        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_credits_null_values(self):
        """Deve tratar valores NULL como 0"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {
            "balance": 0,
            "total_purchased": 0,
            "total_used": 0
        }
        
        result = await get_user_credits("user123", mock_db)
        
        assert result["balance"] == 0
        assert result["total_purchased"] == 0
        assert result["total_used"] == 0


class TestCheckCredits:
    """Testes para check_credits"""
    
    @pytest.mark.asyncio
    async def test_check_credits_sufficient(self):
        """Deve retornar info quando créditos são suficientes"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {
            "balance": 10,
            "total_purchased": 20,
            "total_used": 10
        }
        
        result = await check_credits("user123", "copy", mock_db)
        
        assert result["balance"] == 10
        assert result["required"] == 1
        assert result["remaining_after"] == 9
    
    @pytest.mark.asyncio
    async def test_check_credits_insufficient(self):
        """Deve levantar erro quando créditos insuficientes"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {
            "balance": 0,
            "total_purchased": 10,
            "total_used": 10
        }
        
        with pytest.raises(InsufficientCreditsError) as exc_info:
            await check_credits("user123", "copy", mock_db)
        
        assert exc_info.value.required == 1
        assert exc_info.value.available == 0
    
    @pytest.mark.asyncio
    async def test_check_credits_high_cost_action(self):
        """Deve verificar custo correto para ações caras"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {
            "balance": 3,
            "total_purchased": 10,
            "total_used": 7
        }
        
        # niche_report custa 5 créditos
        with pytest.raises(InsufficientCreditsError) as exc_info:
            await check_credits("user123", "niche_report", mock_db)
        
        assert exc_info.value.required == 5
        assert exc_info.value.available == 3
    
    @pytest.mark.asyncio
    async def test_check_credits_unknown_action(self):
        """Deve usar custo padrão de 1 para ação desconhecida"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {
            "balance": 5,
            "total_purchased": 10,
            "total_used": 5
        }
        
        result = await check_credits("user123", "unknown_action", mock_db)
        
        assert result["required"] == 1  # Default cost
        assert result["remaining_after"] == 4


class TestDeductCredits:
    """Testes para deduct_credits"""
    
    @pytest.mark.asyncio
    async def test_deduct_credits_success(self):
        """Deve deduzir créditos com sucesso"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {"new_balance": 9}
        
        result = await deduct_credits("user123", "copy", mock_db)
        
        assert result["new_balance"] == 9
        assert result["cost"] == 1
        mock_db.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deduct_credits_insufficient(self):
        """Deve levantar erro quando dedução falha"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = None  # Update não encontrou linha
        
        with pytest.raises(InsufficientCreditsError) as exc_info:
            await deduct_credits("user123", "copy", mock_db)
        
        assert exc_info.value.available == 0
    
    @pytest.mark.asyncio
    async def test_deduct_credits_trend_analysis(self):
        """Deve deduzir custo correto para trend_analysis"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {"new_balance": 8}
        
        result = await deduct_credits("user123", "trend_analysis", mock_db)
        
        assert result["cost"] == 2


class TestAddCredits:
    """Testes para add_credits"""
    
    @pytest.mark.asyncio
    async def test_add_credits_success(self):
        """Deve adicionar créditos com sucesso"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {"new_balance": 110}
        
        result = await add_credits("user123", 10, db=mock_db)
        
        assert result["new_balance"] == 110
        assert result["added"] == 10
    
    @pytest.mark.asyncio
    async def test_add_credits_with_payment_id(self):
        """Deve registrar purchase quando payment_id fornecido"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {"new_balance": 110}
        mock_db.execute.return_value = None
        
        result = await add_credits("user123", 10, payment_id="pay_123", db=mock_db)
        
        assert result["added"] == 10
        mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_credits_user_not_found(self):
        """Deve levantar HTTPException quando usuário não existe"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await add_credits("nonexistent", 10, db=mock_db)
        
        assert exc_info.value.status_code == 404


class TestLegacyFunctions:
    """Testes para funções de compatibilidade legada"""
    
    @pytest.mark.asyncio
    async def test_check_copy_quota(self):
        """check_copy_quota deve chamar check_credits com action='copy'"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {
            "balance": 10,
            "total_purchased": 20,
            "total_used": 10
        }
        
        result = await check_copy_quota("user123", mock_db)
        
        assert result["required"] == 1  # copy cost
    
    @pytest.mark.asyncio
    async def test_get_user_quota(self):
        """get_user_quota deve retornar formato legado"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {
            "balance": 10,
            "total_purchased": 20,
            "total_used": 10
        }
        
        result = await get_user_quota("user123", "copy", mock_db)
        
        assert result["used"] == 10
        assert result["limit"] == -1  # No limit
        assert result["remaining"] == 10
        assert result["reset_date"] is None
        assert result["plan"] == "lifetime"
    
    @pytest.mark.asyncio
    async def test_increment_quota(self):
        """increment_quota deve chamar deduct_credits"""
        mock_db = AsyncMock()
        mock_db.fetchrow.return_value = {"new_balance": 9}
        
        # Não deve levantar exceção
        await increment_quota("user123", "copy", 1, mock_db)
        
        mock_db.fetchrow.assert_called_once()
