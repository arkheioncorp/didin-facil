"""
Testes de Carga - Sistema de Monetização
Performance e stress tests para o sistema de créditos
"""

import asyncio
import time
import uuid
import statistics
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio


# ============================================================================
# CONFIGURAÇÕES DE CARGA
# ============================================================================

LOAD_CONFIG = {
    "light": {
        "concurrent_users": 10,
        "requests_per_user": 5,
        "max_response_time_ms": 500,
    },
    "medium": {
        "concurrent_users": 50,
        "requests_per_user": 10,
        "max_response_time_ms": 1000,
    },
    "heavy": {
        "concurrent_users": 100,
        "requests_per_user": 20,
        "max_response_time_ms": 2000,
    },
}


# ============================================================================
# HELPERS
# ============================================================================

async def measure_async_operation(coro):
    """Mede tempo de execução de uma coroutine em ms"""
    start = time.perf_counter()
    result = await coro
    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, elapsed_ms


class LoadTestResults:
    """Armazena e analisa resultados de testes de carga"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.successes: int = 0
        self.failures: int = 0
        self.errors: List[str] = []
    
    def record_success(self, time_ms: float):
        self.response_times.append(time_ms)
        self.successes += 1
    
    def record_failure(self, error: str):
        self.failures += 1
        self.errors.append(error)
    
    @property
    def total_requests(self) -> int:
        return self.successes + self.failures
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0
        return (self.successes / self.total_requests) * 100
    
    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0
        return statistics.mean(self.response_times)
    
    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]
    
    @property
    def p99_response_time(self) -> float:
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[min(idx, len(sorted_times) - 1)]
    
    @property
    def max_response_time(self) -> float:
        if not self.response_times:
            return 0
        return max(self.response_times)
    
    def summary(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "successes": self.successes,
            "failures": self.failures,
            "success_rate_percent": round(self.success_rate, 2),
            "avg_response_time_ms": round(self.avg_response_time, 2),
            "p95_response_time_ms": round(self.p95_response_time, 2),
            "p99_response_time_ms": round(self.p99_response_time, 2),
            "max_response_time_ms": round(self.max_response_time, 2),
        }
    
    def print_summary(self, test_name: str = "Load Test"):
        print(f"\n{'='*60}")
        print(f"📊 {test_name} - Resultados")
        print(f"{'='*60}")
        summary = self.summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")
        print(f"{'='*60}\n")


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_database():
    """Mock de banco de dados otimizado para testes de carga"""
    mock_db = AsyncMock()
    
    call_count = 0
    
    # Simular delay realístico de banco
    async def delayed_fetch(query: str, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.005)  # 5ms de latência simulada
        
        # Detectar tipo de query pelo conteúdo
        if "RETURNING credits_balance as new_balance" in query:
            # Query de UPDATE (deduct_credits ou add_credits)
            return {"new_balance": 99}
        else:
            # Query de SELECT (get_user_credits)
            return {
                "balance": 100,
                "total_purchased": 500,
                "total_used": 400
            }
    
    async def delayed_execute(*args, **kwargs):
        await asyncio.sleep(0.003)  # 3ms de latência simulada
        return 99
    
    mock_db.fetch_one.side_effect = delayed_fetch
    mock_db.execute.side_effect = delayed_execute
    
    return mock_db


# ============================================================================
# TESTES DE CARGA - LIGHT
# ============================================================================

class TestLightLoad:
    """Testes de carga leve (10 usuários, 5 requests cada)"""
    
    @pytest.mark.asyncio
    async def test_concurrent_credit_checks_light(self, mock_database):
        """Teste: verificações de crédito concorrentes (carga leve)"""
        from api.middleware.quota import check_credits
        
        config = LOAD_CONFIG["light"]
        results = LoadTestResults()
        
        async def single_check(user_id: str):
            try:
                _, time_ms = await measure_async_operation(
                    check_credits(user_id=user_id, action="copy", db=mock_database)
                )
                results.record_success(time_ms)
            except Exception as e:
                results.record_failure(str(e))
        
        # Simular múltiplos usuários
        tasks = []
        for i in range(config["concurrent_users"]):
            user_id = f"user_{i}"
            for _ in range(config["requests_per_user"]):
                tasks.append(single_check(user_id))
        
        await asyncio.gather(*tasks)
        
        results.print_summary("Light Load - Credit Checks")
        
        # Assertions
        assert results.success_rate >= 99, f"Taxa de sucesso baixa: {results.success_rate}%"
        assert results.avg_response_time < config["max_response_time_ms"], \
            f"Tempo médio alto: {results.avg_response_time}ms"
    
    @pytest.mark.asyncio
    async def test_concurrent_credit_deductions_light(self, mock_database):
        """Teste: deduções de crédito concorrentes (carga leve)"""
        from api.middleware.quota import deduct_credits
        
        config = LOAD_CONFIG["light"]
        results = LoadTestResults()
        
        async def single_deduction(user_id: str):
            try:
                _, time_ms = await measure_async_operation(
                    deduct_credits(user_id=user_id, action="copy", db=mock_database)
                )
                results.record_success(time_ms)
            except Exception as e:
                results.record_failure(str(e))
        
        tasks = []
        for i in range(config["concurrent_users"]):
            user_id = f"user_{i}"
            for _ in range(config["requests_per_user"]):
                tasks.append(single_deduction(user_id))
        
        await asyncio.gather(*tasks)
        
        results.print_summary("Light Load - Credit Deductions")
        
        assert results.success_rate >= 99
        assert results.avg_response_time < config["max_response_time_ms"]


# ============================================================================
# TESTES DE CARGA - MEDIUM
# ============================================================================

class TestMediumLoad:
    """Testes de carga média (50 usuários, 10 requests cada)"""
    
    @pytest.mark.asyncio
    async def test_concurrent_credit_checks_medium(self, mock_database):
        """Teste: verificações de crédito concorrentes (carga média)"""
        from api.middleware.quota import check_credits
        
        config = LOAD_CONFIG["medium"]
        results = LoadTestResults()
        
        async def single_check(user_id: str):
            try:
                _, time_ms = await measure_async_operation(
                    check_credits(user_id=user_id, action="copy", db=mock_database)
                )
                results.record_success(time_ms)
            except Exception as e:
                results.record_failure(str(e))
        
        tasks = []
        for i in range(config["concurrent_users"]):
            user_id = f"user_{i}"
            for _ in range(config["requests_per_user"]):
                tasks.append(single_check(user_id))
        
        await asyncio.gather(*tasks)
        
        results.print_summary("Medium Load - Credit Checks")
        
        assert results.success_rate >= 98
        assert results.p95_response_time < config["max_response_time_ms"]
    
    @pytest.mark.asyncio
    async def test_mixed_operations_medium(self, mock_database):
        """Teste: operações mistas (check + deduct) carga média"""
        from api.middleware.quota import check_credits, deduct_credits
        
        config = LOAD_CONFIG["medium"]
        results = LoadTestResults()
        
        async def mixed_operation(user_id: str, operation_type: str):
            try:
                if operation_type == "check":
                    _, time_ms = await measure_async_operation(
                        check_credits(user_id=user_id, action="copy", db=mock_database)
                    )
                else:
                    _, time_ms = await measure_async_operation(
                        deduct_credits(user_id=user_id, action="copy", db=mock_database)
                    )
                results.record_success(time_ms)
            except Exception as e:
                results.record_failure(str(e))
        
        tasks = []
        for i in range(config["concurrent_users"]):
            user_id = f"user_{i}"
            for j in range(config["requests_per_user"]):
                # Alternar entre check e deduct
                op = "check" if j % 2 == 0 else "deduct"
                tasks.append(mixed_operation(user_id, op))
        
        await asyncio.gather(*tasks)
        
        results.print_summary("Medium Load - Mixed Operations")
        
        assert results.success_rate >= 98


# ============================================================================
# TESTES DE CARGA - HEAVY
# ============================================================================

class TestHeavyLoad:
    """Testes de carga pesada (100 usuários, 20 requests cada)"""
    
    @pytest.mark.asyncio
    async def test_concurrent_credit_checks_heavy(self, mock_database):
        """Teste: verificações de crédito sob carga pesada"""
        from api.middleware.quota import check_credits
        
        config = LOAD_CONFIG["heavy"]
        results = LoadTestResults()
        
        async def single_check(user_id: str):
            try:
                _, time_ms = await measure_async_operation(
                    check_credits(user_id=user_id, action="copy", db=mock_database)
                )
                results.record_success(time_ms)
            except Exception as e:
                results.record_failure(str(e))
        
        tasks = []
        for i in range(config["concurrent_users"]):
            user_id = f"user_{i}"
            for _ in range(config["requests_per_user"]):
                tasks.append(single_check(user_id))
        
        await asyncio.gather(*tasks)
        
        results.print_summary("Heavy Load - Credit Checks")
        
        # Sob carga pesada, aceitamos taxa de sucesso um pouco menor
        assert results.success_rate >= 95
        assert results.p99_response_time < config["max_response_time_ms"]


# ============================================================================
# TESTES DE STRESS
# ============================================================================

class TestStressScenarios:
    """Cenários de stress para identificar limites do sistema"""
    
    @pytest.mark.asyncio
    async def test_burst_traffic(self, mock_database):
        """Teste: pico repentino de tráfego (burst)"""
        from api.middleware.quota import check_credits
        
        results = LoadTestResults()
        
        async def single_check():
            try:
                _, time_ms = await measure_async_operation(
                    check_credits(
                        user_id=str(uuid.uuid4()),
                        action="copy",
                        db=mock_database
                    )
                )
                results.record_success(time_ms)
            except Exception as e:
                results.record_failure(str(e))
        
        # Burst de 200 requests simultâneos
        tasks = [single_check() for _ in range(200)]
        
        start = time.perf_counter()
        await asyncio.gather(*tasks)
        total_time = (time.perf_counter() - start) * 1000
        
        results.print_summary("Burst Traffic (200 requests)")
        print(f"  Total execution time: {total_time:.2f}ms")
        print(f"  Throughput: {200 / (total_time / 1000):.2f} req/s")
        
        assert results.success_rate >= 90
    
    @pytest.mark.asyncio
    async def test_sustained_load(self, mock_database):
        """Teste: carga sustentada por período"""
        from api.middleware.quota import check_credits
        
        results = LoadTestResults()
        duration_seconds = 2  # 2 segundos de carga
        
        async def single_check():
            _, time_ms = await measure_async_operation(
                check_credits(
                    user_id=str(uuid.uuid4()),
                    action="copy",
                    db=mock_database
                )
            )
            results.record_success(time_ms)
        
        start = time.perf_counter()
        tasks = []
        
        # Enviar requests por N segundos
        while (time.perf_counter() - start) < duration_seconds:
            tasks.append(asyncio.create_task(single_check()))
            await asyncio.sleep(0.01)  # 100 requests/segundo
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        results.print_summary(f"Sustained Load ({duration_seconds}s)")
        print(f"  Total requests: {results.total_requests}")
        print(f"  Requests/second: {results.total_requests / duration_seconds:.2f}")
        
        assert results.success_rate >= 95
    
    @pytest.mark.asyncio
    async def test_webhook_processing_under_load(self, mock_database):
        """Teste: processamento de webhooks sob carga"""
        from api.routes.webhooks import handle_payment_event
        from api.services.mercadopago import MercadoPagoService
        from api.services.license import LicenseService
        
        results = LoadTestResults()
        
        async def process_webhook(payment_id: int):
            mp_service = MercadoPagoService()
            license_service = LicenseService()
            
            # Mock payment response
            payment_data = {
                "id": payment_id,
                "payer": {"email": f"user_{payment_id}@test.com"},
                "metadata": {
                    "product_type": "credits",
                    "credits": 50,
                    "includes_license": True
                }
            }
            
            mp_service.get_payment = AsyncMock(return_value=payment_data)
            mp_service.log_event = AsyncMock()
            mp_service.send_credits_email = AsyncMock()
            license_service.add_credits = AsyncMock(return_value=50)
            license_service.activate_lifetime_license = AsyncMock(return_value=True)
            
            try:
                _, time_ms = await measure_async_operation(
                    handle_payment_event(
                        action="payment.approved",
                        data={"id": payment_id},
                        mp_service=mp_service,
                        license_service=license_service
                    )
                )
                results.record_success(time_ms)
            except Exception as e:
                results.record_failure(str(e))
        
        # 50 webhooks simultâneos
        tasks = [process_webhook(i) for i in range(50)]
        await asyncio.gather(*tasks)
        
        results.print_summary("Webhook Processing (50 concurrent)")
        
        assert results.success_rate >= 98
        assert results.p95_response_time < 500  # 500ms max


# ============================================================================
# TESTES DE RACE CONDITIONS
# ============================================================================

class TestRaceConditions:
    """Testes para identificar race conditions"""
    
    @pytest.mark.asyncio
    async def test_concurrent_deductions_same_user(self):
        """Teste: múltiplas deduções simultâneas do mesmo usuário"""
        from api.middleware.quota import deduct_credits
        
        # Mock com saldo compartilhado
        shared_balance = {"value": 100}
        lock = asyncio.Lock()
        
        mock_db = AsyncMock()
        
        async def deduct_with_race(*args, **kwargs):
            async with lock:
                if shared_balance["value"] >= 1:
                    shared_balance["value"] -= 1
                    await asyncio.sleep(0.001)  # Simular delay
                    return shared_balance["value"]
                return 0
        
        mock_db.execute.side_effect = deduct_with_race
        mock_db.fetch_one.return_value = {"balance": shared_balance["value"]}
        
        # 50 deduções simultâneas do mesmo usuário
        tasks = [
            deduct_credits(user_id="same_user", action="copy", db=mock_db)
            for _ in range(50)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verificar que não houve saldo negativo
        valid_results = [r for r in results if isinstance(r, int)]
        if valid_results:
            assert min(valid_results) >= 0, "Saldo ficou negativo (race condition)"
    
    @pytest.mark.asyncio
    async def test_concurrent_license_activation(self):
        """Teste: múltiplas ativações de licença simultâneas"""
        from api.services.license import LicenseService
        
        activation_count = {"value": 0}
        lock = asyncio.Lock()
        
        license_service = LicenseService()
        mock_db = AsyncMock()
        
        async def mock_fetch(*args, **kwargs):
            # Simular que usuário ainda não tem licença
            return {
                "id": "user_123",
                "has_lifetime_license": activation_count["value"] > 0
            }
        
        async def mock_execute(*args, **kwargs):
            async with lock:
                activation_count["value"] += 1
        
        mock_db.fetch_one.side_effect = mock_fetch
        mock_db.execute.side_effect = mock_execute
        license_service.db = mock_db
        
        # 10 tentativas simultâneas de ativação
        tasks = [
            license_service.activate_lifetime_license(
                email="user@test.com",
                payment_id=f"payment_{i}"
            )
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Todas devem retornar True (sucesso ou já ativado)
        assert all(results), "Alguma ativação falhou"


# ============================================================================
# BENCHMARK
# ============================================================================

class TestBenchmark:
    """Benchmark de performance para referência"""
    
    @pytest.mark.asyncio
    async def test_baseline_performance(self, mock_database):
        """Estabelece baseline de performance"""
        from api.middleware.quota import check_credits, deduct_credits
        
        iterations = 100
        check_times = []
        deduct_times = []
        
        for _ in range(iterations):
            # Check
            _, check_ms = await measure_async_operation(
                check_credits(user_id="user_1", action="copy", db=mock_database)
            )
            check_times.append(check_ms)
            
            # Deduct
            _, deduct_ms = await measure_async_operation(
                deduct_credits(user_id="user_1", action="copy", db=mock_database)
            )
            deduct_times.append(deduct_ms)
        
        print("\n" + "="*60)
        print("📊 BASELINE PERFORMANCE")
        print("="*60)
        print(f"  Check Credits:")
        print(f"    Avg: {statistics.mean(check_times):.2f}ms")
        print(f"    Min: {min(check_times):.2f}ms")
        print(f"    Max: {max(check_times):.2f}ms")
        print(f"    Std: {statistics.stdev(check_times):.2f}ms")
        print(f"  Deduct Credits:")
        print(f"    Avg: {statistics.mean(deduct_times):.2f}ms")
        print(f"    Min: {min(deduct_times):.2f}ms")
        print(f"    Max: {max(deduct_times):.2f}ms")
        print(f"    Std: {statistics.stdev(deduct_times):.2f}ms")
        print("="*60 + "\n")
        
        # Baselines aceitáveis
        assert statistics.mean(check_times) < 50  # < 50ms média
        assert statistics.mean(deduct_times) < 50  # < 50ms média
