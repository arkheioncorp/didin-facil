"""
Hub Resilience - Rate Limiting & Circuit Breaker
=================================================
Módulo compartilhado para resiliência dos hubs de integração.

Implementa:
- Rate Limiting com Token Bucket
- Circuit Breaker com estados (closed, open, half-open)
- Retry com Exponential Backoff
- Métricas Prometheus (opcional)

Autor: Didin Fácil
Versão: 1.0.0
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Awaitable
from collections import deque

logger = logging.getLogger(__name__)


# ============================================
# RATE LIMITER
# ============================================

@dataclass
class RateLimiterConfig:
    """Configuração do Rate Limiter."""
    requests_per_minute: int = 60
    requests_per_second: int = 10
    burst_size: int = 5  # Permite burst de até 5 requisições
    window_size_seconds: int = 60


class TokenBucketRateLimiter:
    """
    Rate Limiter usando Token Bucket algorithm.
    
    - Mais suave que janela fixa
    - Permite bursts controlados
    - Thread-safe para async
    """
    
    def __init__(self, config: RateLimiterConfig):
        self.config = config
        self._tokens: Dict[str, float] = {}
        self._last_update: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        
        # Calcular taxa de reabastecimento
        self._refill_rate = config.requests_per_minute / 60.0  # tokens por segundo
        self._max_tokens = float(config.burst_size)
    
    async def acquire(self, key: str = "default") -> bool:
        """
        Tenta adquirir um token.
        
        Returns:
            True se permitido, False se rate limitado
        """
        async with self._lock:
            now = time.time()
            
            # Inicializar se primeira requisição
            if key not in self._tokens:
                self._tokens[key] = self._max_tokens
                self._last_update[key] = now
            
            # Calcular tokens reabastecidos
            elapsed = now - self._last_update[key]
            new_tokens = elapsed * self._refill_rate
            self._tokens[key] = min(self._max_tokens, self._tokens[key] + new_tokens)
            self._last_update[key] = now
            
            # Tentar consumir token
            if self._tokens[key] >= 1.0:
                self._tokens[key] -= 1.0
                return True
            
            return False
    
    async def wait_for_token(self, key: str = "default", timeout: float = 30.0) -> bool:
        """
        Aguarda até ter token disponível.
        
        Returns:
            True se conseguiu token, False se timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            if await self.acquire(key):
                return True
            await asyncio.sleep(0.1)
        return False
    
    def get_remaining_tokens(self, key: str = "default") -> float:
        """Retorna quantidade de tokens restantes."""
        return self._tokens.get(key, self._max_tokens)
    
    def reset(self, key: str = "default"):
        """Reset tokens para um key específico."""
        self._tokens[key] = self._max_tokens
        self._last_update[key] = time.time()


class SlidingWindowRateLimiter:
    """
    Rate Limiter usando Sliding Window.
    
    - Mais preciso que Token Bucket
    - Melhor para cenários com requisitos rígidos
    """
    
    def __init__(self, config: RateLimiterConfig):
        self.config = config
        self._windows: Dict[str, deque] = {}
        self._lock = asyncio.Lock()
    
    async def acquire(self, key: str = "default") -> bool:
        """Tenta adquirir permissão."""
        async with self._lock:
            now = time.time()
            
            if key not in self._windows:
                self._windows[key] = deque()
            
            window = self._windows[key]
            
            # Remover timestamps fora da janela
            cutoff = now - self.config.window_size_seconds
            while window and window[0] < cutoff:
                window.popleft()
            
            # Verificar limite
            if len(window) < self.config.requests_per_minute:
                window.append(now)
                return True
            
            return False
    
    def get_wait_time(self, key: str = "default") -> float:
        """Retorna tempo de espera estimado."""
        if key not in self._windows or not self._windows[key]:
            return 0.0
        
        oldest = self._windows[key][0]
        wait = (oldest + self.config.window_size_seconds) - time.time()
        return max(0.0, wait)


# ============================================
# CIRCUIT BREAKER
# ============================================

class CircuitState(Enum):
    """Estados do Circuit Breaker."""
    CLOSED = "closed"       # Normal, requisições passam
    OPEN = "open"           # Falha, requisições bloqueadas
    HALF_OPEN = "half_open" # Testando recuperação


@dataclass
class CircuitBreakerConfig:
    """Configuração do Circuit Breaker."""
    failure_threshold: int = 5          # Falhas antes de abrir
    success_threshold: int = 3          # Sucessos para fechar
    timeout_seconds: float = 30.0       # Tempo no estado OPEN
    half_open_max_calls: int = 3        # Requisições permitidas em half-open
    exclude_exceptions: tuple = ()       # Exceções que não contam como falha


@dataclass
class CircuitBreakerStats:
    """Estatísticas do Circuit Breaker."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
        }


class CircuitBreaker:
    """
    Circuit Breaker para proteção contra cascata de falhas.
    
    Estados:
    - CLOSED: Normal, requisições passam
    - OPEN: Serviço indisponível, requisições são bloqueadas
    - HALF_OPEN: Testando recuperação, permite algumas requisições
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self._stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        self._half_open_calls = 0
    
    @property
    def state(self) -> CircuitState:
        return self._stats.state
    
    @property
    def stats(self) -> CircuitBreakerStats:
        return self._stats
    
    async def _check_state_transition(self):
        """Verifica e executa transições de estado."""
        now = time.time()
        
        if self._stats.state == CircuitState.OPEN:
            # Verificar se deve mudar para HALF_OPEN
            if (self._stats.last_failure_time and 
                now - self._stats.last_failure_time >= self.config.timeout_seconds):
                self._stats.state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                self._stats.success_count = 0
                logger.info(f"Circuit {self.name}: OPEN -> HALF_OPEN")
    
    async def can_execute(self) -> bool:
        """Verifica se requisição pode ser executada."""
        async with self._lock:
            await self._check_state_transition()
            
            if self._stats.state == CircuitState.CLOSED:
                return True
            
            if self._stats.state == CircuitState.OPEN:
                return False
            
            # HALF_OPEN: permitir algumas requisições
            if self._half_open_calls < self.config.half_open_max_calls:
                self._half_open_calls += 1
                return True
            
            return False
    
    async def record_success(self):
        """Registra sucesso de requisição."""
        async with self._lock:
            self._stats.total_calls += 1
            self._stats.total_successes += 1
            self._stats.last_success_time = time.time()
            
            if self._stats.state == CircuitState.HALF_OPEN:
                self._stats.success_count += 1
                
                if self._stats.success_count >= self.config.success_threshold:
                    self._stats.state = CircuitState.CLOSED
                    self._stats.failure_count = 0
                    logger.info(f"Circuit {self.name}: HALF_OPEN -> CLOSED")
            
            elif self._stats.state == CircuitState.CLOSED:
                # Reset failure count em sucesso
                self._stats.failure_count = 0
    
    async def record_failure(self, exception: Optional[Exception] = None):
        """Registra falha de requisição."""
        # Verificar se exceção deve ser ignorada
        if exception and isinstance(exception, self.config.exclude_exceptions):
            return
        
        async with self._lock:
            self._stats.total_calls += 1
            self._stats.total_failures += 1
            self._stats.failure_count += 1
            self._stats.last_failure_time = time.time()
            
            if self._stats.state == CircuitState.HALF_OPEN:
                # Qualquer falha em HALF_OPEN volta para OPEN
                self._stats.state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name}: HALF_OPEN -> OPEN (failure)")
            
            elif self._stats.state == CircuitState.CLOSED:
                if self._stats.failure_count >= self.config.failure_threshold:
                    self._stats.state = CircuitState.OPEN
                    logger.warning(f"Circuit {self.name}: CLOSED -> OPEN (threshold reached)")
    
    def reset(self):
        """Reset manual do circuit breaker."""
        self._stats = CircuitBreakerStats()
        self._half_open_calls = 0
        logger.info(f"Circuit {self.name}: Reset to CLOSED")


class CircuitBreakerOpenError(Exception):
    """Exceção quando circuit breaker está aberto."""
    pass


# ============================================
# RETRY WITH EXPONENTIAL BACKOFF
# ============================================

@dataclass
class RetryConfig:
    """Configuração de retry."""
    max_retries: int = 3
    base_delay: float = 1.0  # segundos
    max_delay: float = 60.0  # segundos
    exponential_base: float = 2.0
    jitter: bool = True  # Adiciona aleatoriedade para evitar thundering herd
    retryable_exceptions: tuple = (Exception,)


async def retry_with_backoff(
    func: Callable[..., Awaitable[Any]],
    config: RetryConfig,
    *args,
    **kwargs
) -> Any:
    """
    Executa função com retry e exponential backoff.
    
    Args:
        func: Função assíncrona a executar
        config: Configuração de retry
        *args, **kwargs: Argumentos para a função
    
    Returns:
        Resultado da função
    
    Raises:
        A última exceção se todos os retries falharem
    """
    import random
    
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt == config.max_retries:
                break
            
            # Calcular delay
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            # Adicionar jitter
            if config.jitter:
                delay *= (0.5 + random.random())
            
            logger.warning(
                f"Retry {attempt + 1}/{config.max_retries} após {delay:.2f}s: {e}"
            )
            await asyncio.sleep(delay)
    
    raise last_exception


# ============================================
# DECORATORS
# ============================================

T = TypeVar('T')


def with_rate_limit(
    limiter: TokenBucketRateLimiter,
    key_func: Optional[Callable[..., str]] = None
):
    """
    Decorator para aplicar rate limiting.
    
    Usage:
        @with_rate_limit(my_limiter)
        async def my_function():
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            key = key_func(*args, **kwargs) if key_func else "default"
            
            if not await limiter.acquire(key):
                raise RateLimitExceededError(
                    f"Rate limit exceeded for key: {key}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def with_circuit_breaker(circuit: CircuitBreaker):
    """
    Decorator para aplicar circuit breaker.
    
    Usage:
        @with_circuit_breaker(my_circuit)
        async def my_function():
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if not await circuit.can_execute():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{circuit.name}' is OPEN"
                )
            
            try:
                result = await func(*args, **kwargs)
                await circuit.record_success()
                return result
            except Exception as e:
                await circuit.record_failure(e)
                raise
        return wrapper
    return decorator


def with_retry(config: RetryConfig):
    """
    Decorator para aplicar retry com backoff.
    
    Usage:
        @with_retry(RetryConfig(max_retries=3))
        async def my_function():
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_with_backoff(func, config, *args, **kwargs)
        return wrapper
    return decorator


# ============================================
# EXCEPTIONS
# ============================================

class RateLimitExceededError(Exception):
    """Exceção quando rate limit é excedido."""
    pass


# ============================================
# HUB RESILIENCE MIXIN
# ============================================

class HubResilienceMixin:
    """
    Mixin que adiciona rate limiting e circuit breaker a um hub.
    
    Usage:
        class MyHub(HubResilienceMixin):
            def __init__(self):
                self.init_resilience(
                    rate_limit_config=RateLimiterConfig(requests_per_minute=60),
                    circuit_breaker_config=CircuitBreakerConfig(failure_threshold=5)
                )
    """
    
    _rate_limiter: Optional[TokenBucketRateLimiter] = None
    _circuit_breaker: Optional[CircuitBreaker] = None
    
    def init_resilience(
        self,
        rate_limit_config: Optional[RateLimiterConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        circuit_name: str = "default"
    ):
        """Inicializa rate limiter e circuit breaker."""
        if rate_limit_config:
            self._rate_limiter = TokenBucketRateLimiter(rate_limit_config)
        
        if circuit_breaker_config:
            self._circuit_breaker = CircuitBreaker(circuit_name, circuit_breaker_config)
    
    async def check_rate_limit(self, key: str = "default") -> bool:
        """Verifica se requisição é permitida pelo rate limiter."""
        if self._rate_limiter:
            return await self._rate_limiter.acquire(key)
        return True
    
    async def check_circuit(self) -> bool:
        """Verifica se circuit breaker permite execução."""
        if self._circuit_breaker:
            return await self._circuit_breaker.can_execute()
        return True
    
    async def record_success(self):
        """Registra sucesso no circuit breaker."""
        if self._circuit_breaker:
            await self._circuit_breaker.record_success()
    
    async def record_failure(self, exception: Optional[Exception] = None):
        """Registra falha no circuit breaker."""
        if self._circuit_breaker:
            await self._circuit_breaker.record_failure(exception)
    
    def get_resilience_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de resiliência."""
        stats = {}
        
        if self._rate_limiter:
            stats["rate_limiter"] = {
                "remaining_tokens": self._rate_limiter.get_remaining_tokens()
            }
        
        if self._circuit_breaker:
            stats["circuit_breaker"] = self._circuit_breaker.stats.to_dict()
        
        return stats
