"""
Testes Unitários - Resilience Module
=====================================
Testes para rate limiting, circuit breaker e retry.

Autor: Didin Fácil
Versão: 1.0.0
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import time

from integrations.resilience import (
    # Rate Limiting
    RateLimiterConfig,
    TokenBucketRateLimiter,
    SlidingWindowRateLimiter,
    RateLimitExceededError,
    # Circuit Breaker
    CircuitBreakerConfig,
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    # Retry
    RetryConfig,
    retry_with_backoff,
    # Decorators
    with_rate_limit,
    with_circuit_breaker,
    with_retry,
    # Mixin
    HubResilienceMixin,
)


# ============================================
# TESTES DE RATE LIMITER - TOKEN BUCKET
# ============================================

class TestTokenBucketRateLimiter:
    """Testes para Token Bucket Rate Limiter."""

    @pytest.fixture
    def limiter(self):
        config = RateLimiterConfig(
            requests_per_minute=60,
            requests_per_second=10,
            burst_size=5,
        )
        return TokenBucketRateLimiter(config)

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self, limiter):
        """Testa que requisições dentro do limite são permitidas."""
        result = await limiter.acquire("test")
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_multiple_within_burst(self, limiter):
        """Testa burst de requisições."""
        results = []
        for _ in range(5):  # burst_size = 5
            results.append(await limiter.acquire("test"))
        
        # Todas devem passar (burst)
        assert all(results)

    @pytest.mark.asyncio
    async def test_acquire_exceeds_burst(self, limiter):
        """Testa que exceder burst bloqueia."""
        # Consumir todos os tokens de burst
        for _ in range(5):
            await limiter.acquire("test")
        
        # Próxima requisição deve falhar (sem tempo para reabastecimento)
        result = await limiter.acquire("test")
        assert result is False

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self, limiter):
        """Testa que tokens são reabastecidos."""
        # Consumir todos os tokens
        for _ in range(5):
            await limiter.acquire("test")
        
        # Esperar tempo suficiente para 1 token
        await asyncio.sleep(1.1)  # 60 req/min = 1 req/seg
        
        result = await limiter.acquire("test")
        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_token(self, limiter):
        """Testa aguardar token disponível."""
        # Consumir todos os tokens
        for _ in range(5):
            await limiter.acquire("test")
        
        # Aguardar token com timeout curto
        start = time.time()
        result = await limiter.wait_for_token("test", timeout=2.0)
        elapsed = time.time() - start
        
        assert result is True
        assert elapsed >= 0.5  # Deve ter esperado algo

    @pytest.mark.asyncio
    async def test_get_remaining_tokens(self, limiter):
        """Testa consulta de tokens restantes."""
        initial = limiter.get_remaining_tokens("test")
        assert initial == 5.0  # burst_size
        
        await limiter.acquire("test")
        
        after = limiter.get_remaining_tokens("test")
        assert after < initial

    @pytest.mark.asyncio
    async def test_reset(self, limiter):
        """Testa reset de tokens."""
        # Consumir tokens
        for _ in range(3):
            await limiter.acquire("test")
        
        # Reset
        limiter.reset("test")
        
        # Deve ter todos os tokens novamente
        assert limiter.get_remaining_tokens("test") == 5.0


# ============================================
# TESTES DE RATE LIMITER - SLIDING WINDOW
# ============================================

class TestSlidingWindowRateLimiter:
    """Testes para Sliding Window Rate Limiter."""

    @pytest.fixture
    def limiter(self):
        config = RateLimiterConfig(
            requests_per_minute=10,
            window_size_seconds=10,
        )
        return SlidingWindowRateLimiter(config)

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self, limiter):
        """Testa que requisições dentro do limite são permitidas."""
        results = []
        for _ in range(10):
            results.append(await limiter.acquire("test"))
        
        assert all(results)

    @pytest.mark.asyncio
    async def test_acquire_exceeds_limit(self, limiter):
        """Testa que exceder limite bloqueia."""
        # Atingir limite
        for _ in range(10):
            await limiter.acquire("test")
        
        # Próxima deve falhar
        result = await limiter.acquire("test")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_wait_time(self, limiter):
        """Testa cálculo de tempo de espera."""
        # Sem requisições, sem espera
        wait = limiter.get_wait_time("test")
        assert wait == 0.0
        
        # Fazer requisições
        for _ in range(10):
            await limiter.acquire("test")
        
        # Deve ter tempo de espera
        wait = limiter.get_wait_time("test")
        assert wait > 0


# ============================================
# TESTES DE CIRCUIT BREAKER
# ============================================

class TestCircuitBreaker:
    """Testes para Circuit Breaker."""

    @pytest.fixture
    def circuit(self):
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=1.0,
            half_open_max_calls=2,
        )
        return CircuitBreaker("test-circuit", config)

    @pytest.mark.asyncio
    async def test_initial_state_closed(self, circuit):
        """Testa que estado inicial é CLOSED."""
        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_can_execute_when_closed(self, circuit):
        """Testa que execução é permitida quando CLOSED."""
        result = await circuit.can_execute()
        assert result is True

    @pytest.mark.asyncio
    async def test_opens_after_failures(self, circuit):
        """Testa que abre após atingir threshold de falhas."""
        # Registrar falhas
        for _ in range(3):  # failure_threshold = 3
            await circuit.record_failure()
        
        assert circuit.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_blocked_when_open(self, circuit):
        """Testa que execução é bloqueada quando OPEN."""
        # Forçar abertura
        for _ in range(3):
            await circuit.record_failure()
        
        result = await circuit.can_execute()
        assert result is False

    @pytest.mark.asyncio
    async def test_transitions_to_half_open(self, circuit):
        """Testa transição para HALF_OPEN após timeout."""
        # Abrir circuit
        for _ in range(3):
            await circuit.record_failure()
        
        assert circuit.state == CircuitState.OPEN
        
        # Aguardar timeout
        await asyncio.sleep(1.1)
        
        # Tentar executar (deve transicionar para HALF_OPEN)
        await circuit.can_execute()
        
        assert circuit.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_closes_after_successes_in_half_open(self, circuit):
        """Testa que fecha após sucessos em HALF_OPEN."""
        # Abrir
        for _ in range(3):
            await circuit.record_failure()
        
        # Aguardar timeout
        await asyncio.sleep(1.1)
        await circuit.can_execute()  # Transiciona para HALF_OPEN
        
        # Registrar sucessos
        for _ in range(2):  # success_threshold = 2
            await circuit.record_success()
        
        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reopens_on_failure_in_half_open(self, circuit):
        """Testa que reabre em falha durante HALF_OPEN."""
        # Abrir
        for _ in range(3):
            await circuit.record_failure()
        
        # Aguardar timeout
        await asyncio.sleep(1.1)
        await circuit.can_execute()  # HALF_OPEN
        
        # Falhar
        await circuit.record_failure()
        
        assert circuit.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_reset(self, circuit):
        """Testa reset manual."""
        # Abrir
        for _ in range(3):
            await circuit.record_failure()
        
        assert circuit.state == CircuitState.OPEN
        
        # Reset
        circuit.reset()
        
        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_stats_tracking(self, circuit):
        """Testa rastreamento de estatísticas."""
        await circuit.record_success()
        await circuit.record_failure()
        
        stats = circuit.stats.to_dict()
        
        assert stats["total_calls"] == 2
        assert stats["total_successes"] == 1
        assert stats["total_failures"] == 1


# ============================================
# TESTES DE RETRY
# ============================================

class TestRetryWithBackoff:
    """Testes para retry com exponential backoff."""

    @pytest.fixture
    def config(self):
        return RetryConfig(
            max_retries=3,
            base_delay=0.1,
            max_delay=1.0,
            jitter=False,
        )

    @pytest.mark.asyncio
    async def test_succeeds_first_try(self, config):
        """Testa sucesso na primeira tentativa."""
        mock_func = AsyncMock(return_value="success")
        
        result = await retry_with_backoff(mock_func, config)
        
        assert result == "success"
        mock_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_retries_on_failure(self, config):
        """Testa que retenta em caso de falha."""
        call_count = 0
        
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = await retry_with_backoff(failing_then_success, config)
        
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self, config):
        """Testa que levanta exceção após max retries."""
        mock_func = AsyncMock(side_effect=Exception("Persistent failure"))
        
        with pytest.raises(Exception) as exc_info:
            await retry_with_backoff(mock_func, config)
        
        assert "Persistent failure" in str(exc_info.value)
        assert mock_func.call_count == 4  # 1 original + 3 retries

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self, config):
        """Testa que delays aumentam exponencialmente."""
        delays = []
        original_sleep = asyncio.sleep
        
        async def mock_sleep(delay):
            delays.append(delay)
            await original_sleep(0.01)  # Delay mínimo real
        
        with patch('integrations.resilience.asyncio.sleep', mock_sleep):
            mock_func = AsyncMock(side_effect=Exception("Fail"))
            
            try:
                await retry_with_backoff(mock_func, config)
            except Exception:
                pass
        
        # Delays devem aumentar: 0.1, 0.2, 0.4
        assert len(delays) == 3
        assert delays[0] < delays[1] < delays[2]


# ============================================
# TESTES DE DECORATORS
# ============================================

class TestDecorators:
    """Testes para decorators de resiliência."""

    @pytest.mark.asyncio
    async def test_with_rate_limit_decorator(self):
        """Testa decorator de rate limit."""
        limiter = TokenBucketRateLimiter(
            RateLimiterConfig(burst_size=2)
        )
        
        @with_rate_limit(limiter)
        async def my_func():
            return "ok"
        
        # Primeiras 2 chamadas devem passar (burst)
        assert await my_func() == "ok"
        assert await my_func() == "ok"
        
        # Terceira deve falhar
        with pytest.raises(RateLimitExceededError):
            await my_func()

    @pytest.mark.asyncio
    async def test_with_circuit_breaker_decorator(self):
        """Testa decorator de circuit breaker."""
        circuit = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=2)
        )
        
        @with_circuit_breaker(circuit)
        async def my_func(should_fail=False):
            if should_fail:
                raise Exception("Fail")
            return "ok"
        
        # Sucesso
        assert await my_func() == "ok"
        
        # Falhas para abrir circuit
        try:
            await my_func(should_fail=True)
        except Exception:
            pass
        try:
            await my_func(should_fail=True)
        except Exception:
            pass
        
        # Agora circuit está aberto
        with pytest.raises(CircuitBreakerOpenError):
            await my_func()

    @pytest.mark.asyncio
    async def test_with_retry_decorator(self):
        """Testa decorator de retry."""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=2, base_delay=0.01))
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Fail")
            return "success"
        
        result = await failing_func()
        
        assert result == "success"
        assert call_count == 2


# ============================================
# TESTES DE HUB RESILIENCE MIXIN
# ============================================

class TestHubResilienceMixin:
    """Testes para o mixin de resiliência."""

    @pytest.fixture
    def hub_class(self):
        class TestHub(HubResilienceMixin):
            def __init__(self):
                self.init_resilience(
                    rate_limit_config=RateLimiterConfig(burst_size=3),
                    circuit_breaker_config=CircuitBreakerConfig(failure_threshold=2),
                    circuit_name="test-hub"
                )
        return TestHub

    @pytest.mark.asyncio
    async def test_check_rate_limit(self, hub_class):
        """Testa verificação de rate limit via mixin."""
        hub = hub_class()
        
        # Devem passar (burst)
        assert await hub.check_rate_limit() is True
        assert await hub.check_rate_limit() is True
        assert await hub.check_rate_limit() is True
        
        # Deve falhar
        assert await hub.check_rate_limit() is False

    @pytest.mark.asyncio
    async def test_check_circuit(self, hub_class):
        """Testa verificação de circuit via mixin."""
        hub = hub_class()
        
        # Deve passar
        assert await hub.check_circuit() is True
        
        # Registrar falhas para abrir
        await hub.record_failure()
        await hub.record_failure()
        
        # Deve falhar
        assert await hub.check_circuit() is False

    @pytest.mark.asyncio
    async def test_get_resilience_stats(self, hub_class):
        """Testa obtenção de estatísticas."""
        hub = hub_class()
        
        await hub.record_success()
        await hub.record_failure()
        
        stats = hub.get_resilience_stats()
        
        assert "rate_limiter" in stats
        assert "circuit_breaker" in stats
        assert stats["circuit_breaker"]["total_calls"] == 2

    @pytest.mark.asyncio
    async def test_mixin_without_config(self):
        """Testa mixin sem configuração (opcional)."""
        class MinimalHub(HubResilienceMixin):
            def __init__(self):
                self.init_resilience()  # Sem config
        
        hub = MinimalHub()
        
        # Deve passar (sem rate limiter configurado)
        assert await hub.check_rate_limit() is True
        assert await hub.check_circuit() is True
