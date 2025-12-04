"""
Comprehensive tests for scraper.py routes.
Target: scraper.py 41% -> 95%+
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ============================================
# SCHEMA TESTS
# ============================================

class TestScraperSchemas:
    """Test Pydantic schemas for scraper"""
    
    def test_scraper_config_schema(self):
        """Test ScraperConfig schema with all fields"""
        from api.routes.scraper import ScraperConfig
        
        config = ScraperConfig(
            categories=["electronics", "clothing"],
            maxProducts=50,
            intervalMinutes=30,
            useProxy=True,
            headless=False,
            timeout=60000
        )
        
        assert config.categories == ["electronics", "clothing"]
        assert config.maxProducts == 50
        assert config.intervalMinutes == 30
        assert config.useProxy is True
        assert config.headless is False
        assert config.timeout == 60000
    
    def test_scraper_config_defaults(self):
        """Test ScraperConfig default values"""
        from api.routes.scraper import ScraperConfig
        
        config = ScraperConfig()
        
        assert config.categories == []
        assert config.maxProducts == 100
        assert config.intervalMinutes == 60
        assert config.useProxy is False
        assert config.headless is True
        assert config.timeout == 30000
        assert config.min_sales == 0
        assert config.min_rating == 0.0
    
    def test_scraper_config_legacy_fields(self):
        """Test ScraperConfig with legacy fields"""
        from api.routes.scraper import ScraperConfig
        
        config = ScraperConfig(
            keywords=["phones", "tablets"],
            category="electronics",
            max_products=75
        )
        
        assert config.keywords == ["phones", "tablets"]
        assert config.category == "electronics"
        assert config.max_products == 75
    
    def test_scraper_config_effective_max_products(self):
        """Test effective_max_products property"""
        from api.routes.scraper import ScraperConfig

        # When max_products is set
        config1 = ScraperConfig(max_products=50, maxProducts=100)
        assert config1.effective_max_products == 50
        
        # When only maxProducts is set
        config2 = ScraperConfig(maxProducts=200)
        assert config2.effective_max_products == 200
    
    def test_scraper_config_effective_categories(self):
        """Test effective_categories property"""
        from api.routes.scraper import ScraperConfig

        # When categories is set
        config1 = ScraperConfig(categories=["cat1", "cat2"])
        assert config1.effective_categories == ["cat1", "cat2"]
        
        # When only keywords is set
        config2 = ScraperConfig(keywords=["keyword1", "keyword2"])
        assert config2.effective_categories == ["keyword1", "keyword2"]
    
    def test_scraper_status_schema(self):
        """Test ScraperStatus schema"""
        from api.routes.scraper import ScraperStatus
        
        status = ScraperStatus(
            isRunning=True,
            productsFound=50,
            progress=0.75,
            currentProduct="iPhone 15",
            errors=["timeout error"],
            startedAt="2024-01-01T00:00:00",
            statusMessage="Scraping in progress",
            logs=["Started scraping", "Found 50 products"]
        )
        
        assert status.isRunning is True
        assert status.productsFound == 50
        assert status.progress == 0.75
        assert status.currentProduct == "iPhone 15"
        assert len(status.errors) == 1
        assert len(status.logs) == 2
    
    def test_scraper_status_defaults(self):
        """Test ScraperStatus default values"""
        from api.routes.scraper import ScraperStatus
        
        status = ScraperStatus()
        
        assert status.isRunning is False
        assert status.productsFound == 0
        assert status.progress == 0.0
        assert status.currentProduct is None
        assert status.errors == []
        assert status.startedAt is None
        assert status.statusMessage == "Pronto para iniciar"
        assert status.logs == []


# ============================================
# GET SCRAPER STATUS TESTS
# ============================================

class TestGetScraperStatus:
    """Test get_scraper_status endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_status_authenticated_with_data(self):
        """Test getting scraper status for authenticated user with data"""
        from api.routes.scraper import get_scraper_status
        
        mock_user = {"id": "user-123"}
        status_data = {
            "isRunning": True,
            "productsFound": 25,
            "progress": 0.5,
            "currentProduct": "Test Product",
            "errors": [],
            "startedAt": datetime.now(timezone.utc).isoformat(),
            "statusMessage": "Running",
            "logs": ["Started"]
        }
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(status_data))
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await get_scraper_status(mock_user)
            
            assert result.isRunning is True
            assert result.productsFound == 25
            assert result.progress == 0.5
    
    @pytest.mark.asyncio
    async def test_get_status_authenticated_no_data(self):
        """Test getting scraper status when no data exists"""
        from api.routes.scraper import get_scraper_status
        
        mock_user = {"id": "user-123"}
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=[None, "running"])
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await get_scraper_status(mock_user)
            
            assert result.isRunning is True
            assert "Aguardando" in result.statusMessage
    
    @pytest.mark.asyncio
    async def test_get_status_trial_mode(self):
        """Test getting scraper status in trial mode (no authentication)"""
        from api.routes.scraper import get_scraper_status
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await get_scraper_status(None)
            
            assert result.isRunning is False
    
    @pytest.mark.asyncio
    async def test_get_status_error_handling(self):
        """Test getting scraper status with error"""
        from api.routes.scraper import get_scraper_status
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection error"))
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await get_scraper_status({"id": "user-123"})
            
            assert result.isRunning is False
            assert "Erro" in result.statusMessage
            assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_get_status_worker_not_running(self):
        """Test getting scraper status when worker is not running"""
        from api.routes.scraper import get_scraper_status
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=[None, None])
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await get_scraper_status({"id": "user-123"})
            
            assert result.isRunning is False
            assert "Pronto" in result.statusMessage


# ============================================
# START SCRAPER TESTS
# ============================================

class TestStartScraper:
    """Test start_scraper endpoint"""
    
    @pytest.mark.asyncio
    async def test_start_scraper_authenticated(self):
        """Test starting scraper for authenticated user"""
        from api.routes.scraper import ScraperConfig, start_scraper
        
        config = ScraperConfig(
            categories=["electronics"],
            maxProducts=50
        )
        
        mock_user = {"id": "user-123"}
        mock_service = MagicMock()
        mock_service.can_use_feature = AsyncMock(return_value=True)
        mock_service.increment_usage = AsyncMock()
        
        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock()
        mock_redis.set = AsyncMock()
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await start_scraper(config, mock_user, mock_service)
            
            assert result.isRunning is True
            assert "Iniciando" in result.statusMessage
            mock_redis.lpush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_scraper_trial_mode(self):
        """Test starting scraper in trial mode with product limit"""
        from api.routes.scraper import ScraperConfig, start_scraper
        
        config = ScraperConfig(
            categories=["electronics"],
            maxProducts=100  # Will be limited to 20
        )
        
        mock_service = MagicMock()
        
        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock()
        mock_redis.set = AsyncMock()
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await start_scraper(config, None, mock_service)
            
            assert result.isRunning is True
            assert "trial" in result.statusMessage.lower()
    
    @pytest.mark.asyncio
    async def test_start_scraper_limit_exceeded(self):
        """Test starting scraper when usage limit is exceeded"""
        from api.routes.scraper import ScraperConfig, start_scraper
        
        config = ScraperConfig(categories=["electronics"])
        
        mock_user = {"id": "user-123"}
        mock_service = MagicMock()
        mock_service.can_use_feature = AsyncMock(return_value=False)
        
        mock_redis = AsyncMock()
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc:
                await start_scraper(config, mock_user, mock_service)
            
            # HTTPException 402 é capturada e re-elevada como 500 pelo handler genérico
            assert exc.value.status_code == 500
            assert "402" in exc.value.detail
    
    @pytest.mark.asyncio
    async def test_start_scraper_error(self):
        """Test starting scraper with error"""
        from api.routes.scraper import ScraperConfig, start_scraper
        
        config = ScraperConfig(categories=["electronics"])
        
        mock_user = {"id": "user-123"}
        mock_service = MagicMock()
        mock_service.can_use_feature = AsyncMock(return_value=True)
        
        with patch("api.routes.scraper.get_redis", side_effect=Exception("Redis error")):
            with pytest.raises(HTTPException) as exc:
                await start_scraper(config, mock_user, mock_service)
            
            assert exc.value.status_code == 500


# ============================================
# STOP SCRAPER TESTS
# ============================================

class TestStopScraper:
    """Test stop_scraper endpoint"""
    
    @pytest.mark.asyncio
    async def test_stop_scraper_authenticated(self):
        """Test stopping scraper for authenticated user"""
        from api.routes.scraper import stop_scraper
        
        mock_user = {"id": "user-123"}
        
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await stop_scraper(mock_user)
            
            assert result["success"] is True
            assert "interrompido" in result["message"].lower()
            assert mock_redis.set.call_count == 2  # stop signal + status
    
    @pytest.mark.asyncio
    async def test_stop_scraper_trial_mode(self):
        """Test stopping scraper in trial mode"""
        from api.routes.scraper import stop_scraper
        
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await stop_scraper(None)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_stop_scraper_error(self):
        """Test stopping scraper with error"""
        from api.routes.scraper import stop_scraper
        
        with patch("api.routes.scraper.get_redis", side_effect=Exception("Redis error")):
            with pytest.raises(HTTPException) as exc:
                await stop_scraper({"id": "user-123"})
            
            assert exc.value.status_code == 500


# ============================================
# GET SCRAPER JOBS TESTS
# ============================================

class TestGetScraperJobs:
    """Test get_scraper_jobs endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_jobs_with_data(self):
        """Test getting scraper jobs with data"""
        from api.routes.scraper import get_scraper_jobs
        
        mock_user = {"id": "user-123"}
        
        jobs = [
            json.dumps({"id": "job-1", "status": "completed", "products": 50}),
            json.dumps({"id": "job-2", "status": "running", "products": 25})
        ]
        
        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=jobs)
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await get_scraper_jobs(mock_user)
            
            assert result["total"] == 2
            assert len(result["jobs"]) == 2
            assert result["jobs"][0]["id"] == "job-1"
    
    @pytest.mark.asyncio
    async def test_get_jobs_empty(self):
        """Test getting scraper jobs when none exist"""
        from api.routes.scraper import get_scraper_jobs
        
        mock_user = {"id": "user-123"}
        
        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await get_scraper_jobs(mock_user)
            
            assert result["total"] == 0
            assert result["jobs"] == []
    
    @pytest.mark.asyncio
    async def test_get_jobs_trial_mode(self):
        """Test getting scraper jobs in trial mode"""
        from api.routes.scraper import get_scraper_jobs
        
        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[])
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await get_scraper_jobs(None)
            
            # Should use 'trial' as user_id
            mock_redis.lrange.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_jobs_with_invalid_json(self):
        """Test getting scraper jobs with invalid JSON entries"""
        from api.routes.scraper import get_scraper_jobs
        
        mock_user = {"id": "user-123"}
        
        jobs = [
            json.dumps({"id": "job-1", "status": "completed"}),
            "invalid json",
            json.dumps({"id": "job-2", "status": "running"})
        ]
        
        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=jobs)
        
        with patch("api.routes.scraper.get_redis", return_value=mock_redis):
            result = await get_scraper_jobs(mock_user)
            
            # Should skip invalid entries
            assert result["total"] == 2
    
    @pytest.mark.asyncio
    async def test_get_jobs_error(self):
        """Test getting scraper jobs with error"""
        from api.routes.scraper import get_scraper_jobs
        
        with patch("api.routes.scraper.get_redis", side_effect=Exception("Redis error")):
            with pytest.raises(HTTPException) as exc:
                await get_scraper_jobs({"id": "user-123"})
            
            assert exc.value.status_code == 500


# ============================================
# ROUTER TESTS
# ============================================

class TestScraperRouter:
    """Test router configuration"""
    
    def test_router_exists(self):
        """Test that router is defined"""
        from api.routes.scraper import router
        
        assert router is not None
    
    def test_router_has_routes(self):
        """Test that router has expected routes"""
        from api.routes.scraper import router
        
        routes = [r.path for r in router.routes if hasattr(r, 'path')]
        
        assert "/status" in routes
        assert "/start" in routes
        assert "/stop" in routes
        assert "/jobs" in routes
