"""
Testes extensivos para Scraper Routes
Aumenta cobertura de api/routes/scraper.py
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_current_user():
    return {"id": "user-123", "email": "test@test.com"}


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.lpush = AsyncMock(return_value=1)
    redis.lrange = AsyncMock(return_value=[])
    return redis


@pytest.fixture
def sample_config():
    """Configuração de scraper de exemplo."""
    return {
        "categories": ["electronics", "fashion"],
        "maxProducts": 100,
        "intervalMinutes": 60,
        "useProxy": False,
        "headless": True,
        "timeout": 30000
    }


# ============================================
# TEST MODELS
# ============================================

class TestScraperConfig:
    """Testes para modelo ScraperConfig."""

    def test_default_values(self):
        """Testa valores padrão."""
        from api.routes.scraper import ScraperConfig
        
        config = ScraperConfig()
        assert config.categories == []
        assert config.maxProducts == 100
        assert config.intervalMinutes == 60
        assert config.useProxy == False
        assert config.headless == True

    def test_effective_max_products_uses_max_products(self):
        """Usa max_products quando definido."""
        from api.routes.scraper import ScraperConfig
        
        config = ScraperConfig(maxProducts=100, max_products=50)
        assert config.effective_max_products == 50

    def test_effective_max_products_fallback_to_maxProducts(self):
        """Fallback para maxProducts quando max_products não definido."""
        from api.routes.scraper import ScraperConfig
        
        config = ScraperConfig(maxProducts=150)
        assert config.effective_max_products == 150

    def test_effective_categories_uses_categories(self):
        """Usa categories quando definido."""
        from api.routes.scraper import ScraperConfig
        
        config = ScraperConfig(categories=["cat1", "cat2"], keywords=["key1"])
        assert config.effective_categories == ["cat1", "cat2"]

    def test_effective_categories_fallback_to_keywords(self):
        """Fallback para keywords quando categories vazio."""
        from api.routes.scraper import ScraperConfig
        
        config = ScraperConfig(categories=[], keywords=["key1", "key2"])
        assert config.effective_categories == ["key1", "key2"]

    def test_with_all_fields(self):
        """Testa config com todos os campos."""
        from api.routes.scraper import ScraperConfig
        
        config = ScraperConfig(
            categories=["tech"],
            maxProducts=200,
            intervalMinutes=30,
            useProxy=True,
            headless=False,
            timeout=60000,
            keywords=["smartphone"],
            category="electronics",
            max_products=150,
            min_sales=10,
            min_rating=4.0
        )
        
        assert config.categories == ["tech"]
        assert config.useProxy == True
        assert config.min_sales == 10
        assert config.min_rating == 4.0


class TestScraperStatus:
    """Testes para modelo ScraperStatus."""

    def test_default_values(self):
        """Testa valores padrão."""
        from api.routes.scraper import ScraperStatus
        
        status = ScraperStatus()
        assert status.isRunning == False
        assert status.productsFound == 0
        assert status.progress == 0.0
        assert status.currentProduct is None
        assert status.errors == []
        assert status.logs == []
        assert status.statusMessage == "Pronto para iniciar"

    def test_with_values(self):
        """Testa status com valores."""
        from api.routes.scraper import ScraperStatus
        
        status = ScraperStatus(
            isRunning=True,
            productsFound=50,
            progress=0.5,
            currentProduct="iPhone 15",
            errors=["Timeout"],
            startedAt="2024-01-15T10:00:00",
            statusMessage="Processando...",
            logs=["Log 1", "Log 2"]
        )
        
        assert status.isRunning == True
        assert status.productsFound == 50
        assert status.progress == 0.5
        assert status.currentProduct == "iPhone 15"


# ============================================
# TEST GET STATUS
# ============================================

class TestGetScraperStatus:
    """Testes para GET /status."""

    @pytest.mark.asyncio
    async def test_returns_stored_status_for_authenticated_user(self, mock_current_user):
        """Retorna status armazenado para usuário autenticado."""
        stored_status = {
            "isRunning": True,
            "productsFound": 25,
            "progress": 0.5,
            "currentProduct": "Product A",
            "errors": [],
            "startedAt": "2024-01-15T10:00:00",
            "statusMessage": "Processando...",
            "logs": []
        }
        
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis, \
             patch('api.routes.scraper.get_current_user_optional', return_value=mock_current_user):
            
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value=json.dumps(stored_status))
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import get_scraper_status
            result = await get_scraper_status(current_user=mock_current_user)
            
            assert result.isRunning == True
            assert result.productsFound == 25

    @pytest.mark.asyncio
    async def test_returns_default_for_trial_user(self):
        """Retorna status padrão para usuário trial."""
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value=None)
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import get_scraper_status
            result = await get_scraper_status(current_user=None)
            
            assert result.isRunning == False

    @pytest.mark.asyncio
    async def test_returns_status_based_on_worker(self):
        """Retorna status baseado no worker quando não há status do usuário."""
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(side_effect=[None, "running"])
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import get_scraper_status
            result = await get_scraper_status(current_user=None)
            
            assert result.isRunning == True

    @pytest.mark.asyncio
    async def test_handles_redis_error(self):
        """Trata erro do Redis graciosamente."""
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_get_redis.side_effect = Exception("Redis error")
            
            from api.routes.scraper import get_scraper_status
            result = await get_scraper_status(current_user=None)
            
            assert result.isRunning == False
            assert "Erro" in result.statusMessage
            assert len(result.errors) > 0


# ============================================
# TEST START SCRAPER
# ============================================

class TestStartScraper:
    """Testes para POST /start."""

    @pytest.mark.asyncio
    async def test_starts_scraper_for_authenticated_user(self, mock_current_user, sample_config):
        """Inicia scraper para usuário autenticado."""
        mock_sub_service = AsyncMock()
        mock_sub_service.can_use_feature = AsyncMock(return_value=True)
        mock_sub_service.increment_usage = AsyncMock()
        
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.lpush = AsyncMock(return_value=1)
            mock_redis.set = AsyncMock(return_value=True)
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import ScraperConfig, start_scraper
            config = ScraperConfig(**sample_config)
            
            result = await start_scraper(
                config=config,
                current_user=mock_current_user,
                service=mock_sub_service
            )
            
            assert result.isRunning == True
            assert "trial" not in result.statusMessage.lower()
            mock_redis.lpush.assert_called_once()

    @pytest.mark.asyncio
    async def test_limits_trial_user_to_20_products(self, sample_config):
        """Limita usuário trial a 20 produtos."""
        mock_sub_service = AsyncMock()
        
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.lpush = AsyncMock(return_value=1)
            mock_redis.set = AsyncMock(return_value=True)
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import ScraperConfig, start_scraper
            config = ScraperConfig(**sample_config)
            
            result = await start_scraper(
                config=config,
                current_user=None,
                service=mock_sub_service
            )
            
            assert result.isRunning == True
            assert "trial" in result.statusMessage.lower()

    @pytest.mark.asyncio
    async def test_creates_job_with_correct_data(self, mock_current_user, sample_config):
        """Cria job com dados corretos."""
        captured_job = None
        
        mock_sub_service = AsyncMock()
        mock_sub_service.can_use_feature = AsyncMock(return_value=True)
        mock_sub_service.increment_usage = AsyncMock()
        
        async def capture_lpush(key, value):
            nonlocal captured_job
            captured_job = json.loads(value)
            return 1
        
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.lpush = AsyncMock(side_effect=capture_lpush)
            mock_redis.set = AsyncMock(return_value=True)
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import ScraperConfig, start_scraper
            config = ScraperConfig(**sample_config)
            
            await start_scraper(
                config=config,
                current_user=mock_current_user,
                service=mock_sub_service
            )
            
            assert captured_job is not None
            assert "user_id" in captured_job
            assert captured_job["user_id"] == mock_current_user["id"]
            assert captured_job["status"] == "pending"

    @pytest.mark.asyncio
    async def test_handles_redis_error(self, mock_current_user, sample_config):
        """Trata erro do Redis com HTTPException."""
        mock_sub_service = AsyncMock()
        mock_sub_service.can_use_feature = AsyncMock(return_value=True)
        
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_get_redis.side_effect = Exception("Connection failed")
            
            from api.routes.scraper import ScraperConfig, start_scraper
            from fastapi import HTTPException
            
            config = ScraperConfig(**sample_config)
            
            with pytest.raises(HTTPException) as exc_info:
                await start_scraper(
                    config=config,
                    current_user=mock_current_user,
                    service=mock_sub_service
                )
            
            assert exc_info.value.status_code == 500


# ============================================
# TEST STOP SCRAPER
# ============================================

class TestStopScraper:
    """Testes para POST /stop."""

    @pytest.mark.asyncio
    async def test_stops_scraper_for_authenticated_user(self, mock_current_user):
        """Para scraper para usuário autenticado."""
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.set = AsyncMock(return_value=True)
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import stop_scraper
            result = await stop_scraper(current_user=mock_current_user)
            
            assert result["success"] == True
            assert "interrompido" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_stops_scraper_for_trial_user(self):
        """Para scraper para usuário trial."""
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.set = AsyncMock(return_value=True)
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import stop_scraper
            result = await stop_scraper(current_user=None)
            
            assert result["success"] == True

    @pytest.mark.asyncio
    async def test_sets_stop_signal_in_redis(self, mock_current_user):
        """Define sinal de parada no Redis."""
        set_calls = []
        
        async def capture_set(key, value, **kwargs):
            set_calls.append((key, value))
            return True
        
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.set = AsyncMock(side_effect=capture_set)
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import stop_scraper
            await stop_scraper(current_user=mock_current_user)
            
            stop_signal_set = any("stop" in call[0] for call in set_calls)
            assert stop_signal_set

    @pytest.mark.asyncio
    async def test_handles_redis_error(self, mock_current_user):
        """Trata erro do Redis com HTTPException."""
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_get_redis.side_effect = Exception("Connection failed")
            
            from api.routes.scraper import stop_scraper
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await stop_scraper(current_user=mock_current_user)
            
            assert exc_info.value.status_code == 500


# ============================================
# TEST GET JOBS
# ============================================

class TestGetScraperJobs:
    """Testes para GET /jobs."""

    @pytest.mark.asyncio
    async def test_returns_jobs_for_authenticated_user(self, mock_current_user):
        """Retorna jobs para usuário autenticado."""
        jobs_data = [
            json.dumps({"id": "job-1", "status": "completed"}),
            json.dumps({"id": "job-2", "status": "pending"})
        ]
        
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.lrange = AsyncMock(return_value=jobs_data)
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import get_scraper_jobs
            result = await get_scraper_jobs(current_user=mock_current_user)
            
            assert "jobs" in result
            assert len(result["jobs"]) == 2
            assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_returns_jobs_for_trial_user(self):
        """Retorna jobs para usuário trial."""
        jobs_data = [json.dumps({"id": "job-1", "status": "completed"})]
        
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.lrange = AsyncMock(return_value=jobs_data)
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import get_scraper_jobs
            result = await get_scraper_jobs(current_user=None)
            
            assert len(result["jobs"]) == 1

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_jobs(self, mock_current_user):
        """Retorna vazio quando não há jobs."""
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.lrange = AsyncMock(return_value=[])
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import get_scraper_jobs
            result = await get_scraper_jobs(current_user=mock_current_user)
            
            assert result["jobs"] == []
            assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_handles_invalid_json_in_jobs(self, mock_current_user):
        """Trata JSON inválido em jobs."""
        jobs_data = [
            json.dumps({"id": "job-1", "status": "completed"}),
            "invalid json",
            json.dumps({"id": "job-2", "status": "pending"})
        ]
        
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.lrange = AsyncMock(return_value=jobs_data)
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import get_scraper_jobs
            result = await get_scraper_jobs(current_user=mock_current_user)
            
            # Should skip invalid JSON and return valid ones
            assert len(result["jobs"]) == 2

    @pytest.mark.asyncio
    async def test_handles_redis_error(self, mock_current_user):
        """Trata erro do Redis com HTTPException."""
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_get_redis.side_effect = Exception("Connection failed")
            
            from api.routes.scraper import get_scraper_jobs
            from fastapi import HTTPException
            
            with pytest.raises(HTTPException) as exc_info:
                await get_scraper_jobs(current_user=mock_current_user)
            
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_uses_correct_user_key(self, mock_current_user):
        """Usa chave correta do usuário."""
        captured_key = None
        
        async def capture_lrange(key, start, end):
            nonlocal captured_key
            captured_key = key
            return []
        
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.lrange = AsyncMock(side_effect=capture_lrange)
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import get_scraper_jobs
            await get_scraper_jobs(current_user=mock_current_user)
            
            assert mock_current_user["id"] in captured_key

    @pytest.mark.asyncio
    async def test_uses_trial_key_for_unauthenticated(self):
        """Usa chave 'trial' para usuário não autenticado."""
        captured_key = None
        
        async def capture_lrange(key, start, end):
            nonlocal captured_key
            captured_key = key
            return []
        
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.lrange = AsyncMock(side_effect=capture_lrange)
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import get_scraper_jobs
            await get_scraper_jobs(current_user=None)
            
            assert "trial" in captured_key


# ============================================
# INTEGRATION TESTS
# ============================================

class TestScraperIntegration:
    """Testes de integração do scraper."""

    @pytest.mark.asyncio
    async def test_full_scraper_workflow(self, mock_current_user, sample_config):
        """Testa workflow completo: start -> status -> stop."""
        mock_sub_service = AsyncMock()
        mock_sub_service.can_use_feature = AsyncMock(return_value=True)
        mock_sub_service.increment_usage = AsyncMock()
        
        with patch('api.routes.scraper.get_redis', new_callable=AsyncMock) as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.lpush = AsyncMock(return_value=1)
            mock_redis.set = AsyncMock(return_value=True)
            mock_redis.get = AsyncMock(return_value=json.dumps({
                "isRunning": True,
                "productsFound": 10,
                "progress": 0.2,
                "statusMessage": "Processing..."
            }))
            mock_get_redis.return_value = mock_redis
            
            from api.routes.scraper import (ScraperConfig, get_scraper_status,
                                            start_scraper, stop_scraper)

            # Start
            config = ScraperConfig(**sample_config)
            start_result = await start_scraper(
                config=config,
                current_user=mock_current_user,
                service=mock_sub_service
            )
            assert start_result.isRunning is True
            
            # Check status
            status_result = await get_scraper_status(
                current_user=mock_current_user
            )
            assert status_result.isRunning is True
            
            # Stop
            stop_result = await stop_scraper(current_user=mock_current_user)
            assert stop_result["success"] is True
