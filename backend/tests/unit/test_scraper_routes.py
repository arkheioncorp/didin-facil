"""
Tests for Scraper Routes
Endpoints for product scraper control.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestScraperModels:
    """Tests for Scraper Pydantic models"""

    def test_scraper_config_full(self):
        """Test ScraperConfig with all fields"""
        from api.routes.scraper import ScraperConfig

        config = ScraperConfig(
            keywords=["laptop", "smartphone"],
            category="electronics",
            max_products=150,
            min_sales=10,
            min_rating=4.0
        )

        assert config.keywords == ["laptop", "smartphone"]
        assert config.category == "electronics"
        assert config.max_products == 150
        assert config.min_sales == 10
        assert config.min_rating == 4.0

    def test_scraper_config_defaults(self):
        """Test ScraperConfig default values"""
        from api.routes.scraper import ScraperConfig

        config = ScraperConfig()

        assert config.keywords == []
        assert config.category is None
        assert config.max_products is None  # Optional field defaults to None
        assert config.maxProducts == 100  # Preferred field
        assert config.min_sales == 0
        assert config.min_rating == 0.0

    def test_scraper_config_partial(self):
        """Test ScraperConfig with partial fields"""
        from api.routes.scraper import ScraperConfig

        config = ScraperConfig(
            keywords=["monitor"],
            max_products=50
        )

        assert config.keywords == ["monitor"]
        assert config.max_products == 50
        assert config.category is None

    def test_scraper_config_category_only(self):
        """Test ScraperConfig with category only"""
        from api.routes.scraper import ScraperConfig

        config = ScraperConfig(category="fashion")

        assert config.category == "fashion"
        assert config.keywords == []

    def test_scraper_status_full(self):
        """Test ScraperStatus with all fields"""
        from api.routes.scraper import ScraperStatus

        status = ScraperStatus(
            isRunning=True,
            productsFound=50,
            progress=0.5,
            currentProduct="Product XYZ",
            errors=["Error 1"],
            startedAt="2024-01-01T00:00:00",
            statusMessage="Processing...",
            logs=["Log 1", "Log 2"]
        )

        assert status.isRunning is True
        assert status.productsFound == 50
        assert status.progress == 0.5
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
        assert status.statusMessage == "Pronto para iniciar"


class TestGetScraperStatus:
    """Tests for get_scraper_status endpoint"""

    @pytest.mark.asyncio
    async def test_get_status_with_data(self):
        """Test getting status when data exists"""
        from api.routes.scraper import get_scraper_status

        mock_user = {"id": "user-123"}

        with patch('api.routes.scraper.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value=json.dumps({
                "isRunning": True,
                "productsFound": 25,
                "progress": 0.5,
                "statusMessage": "Running"
            }))
            mock_redis_getter.return_value = mock_redis

            result = await get_scraper_status(mock_user)

            assert result.isRunning is True
            assert result.productsFound == 25

    @pytest.mark.asyncio
    async def test_get_status_no_data(self):
        """Test getting status when no data exists"""
        from api.routes.scraper import get_scraper_status

        mock_user = {"id": "user-123"}

        with patch('api.routes.scraper.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(side_effect=[None, None])
            mock_redis_getter.return_value = mock_redis

            result = await get_scraper_status(mock_user)

            assert result.isRunning is False
            assert "Pronto" in result.statusMessage

    @pytest.mark.asyncio
    async def test_get_status_worker_running(self):
        """Test status when worker is running"""
        from api.routes.scraper import get_scraper_status

        mock_user = {"id": "user-123"}

        with patch('api.routes.scraper.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(side_effect=[None, "running"])
            mock_redis_getter.return_value = mock_redis

            result = await get_scraper_status(mock_user)

            assert result.isRunning is True
            assert "Aguardando" in result.statusMessage

    @pytest.mark.asyncio
    async def test_get_status_error(self):
        """Test status when error occurs"""
        from api.routes.scraper import get_scraper_status

        mock_user = {"id": "user-123"}

        with patch('api.routes.scraper.get_redis') as mock_redis_getter:
            mock_redis_getter.side_effect = Exception("Redis error")

            result = await get_scraper_status(mock_user)

            assert result.isRunning is False
            assert "Erro" in result.statusMessage


class TestStartScraper:
    """Tests for start_scraper endpoint"""

    @pytest.mark.asyncio
    async def test_start_scraper_success(self):
        """Test starting scraper successfully"""
        from api.routes.scraper import ScraperConfig, start_scraper

        mock_user = {"id": "user-123"}
        config = ScraperConfig(keywords=["tech"], max_products=50)

        with patch('api.routes.scraper.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.lpush = AsyncMock()
            mock_redis.set = AsyncMock()
            mock_redis_getter.return_value = mock_redis

            result = await start_scraper(config, mock_user)

            assert result.isRunning is True
            assert "Iniciando" in result.statusMessage
            mock_redis.lpush.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_scraper_error(self):
        """Test starting scraper with error"""
        from api.routes.scraper import ScraperConfig, start_scraper
        from fastapi import HTTPException

        mock_user = {"id": "user-123"}
        config = ScraperConfig()

        with patch('api.routes.scraper.get_redis') as mock_redis_getter:
            mock_redis_getter.side_effect = Exception("Redis error")

            with pytest.raises(HTTPException) as exc_info:
                await start_scraper(config, mock_user)

            assert exc_info.value.status_code == 500


class TestStopScraper:
    """Tests for stop_scraper endpoint"""

    @pytest.mark.asyncio
    async def test_stop_scraper_success(self):
        """Test stopping scraper successfully"""
        from api.routes.scraper import stop_scraper

        mock_user = {"id": "user-123"}

        with patch('api.routes.scraper.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.set = AsyncMock()
            mock_redis_getter.return_value = mock_redis

            result = await stop_scraper(mock_user)

            assert result["success"] is True
            assert "interrompido" in result["message"]

    @pytest.mark.asyncio
    async def test_stop_scraper_error(self):
        """Test stopping scraper with error"""
        from api.routes.scraper import stop_scraper
        from fastapi import HTTPException

        mock_user = {"id": "user-123"}

        with patch('api.routes.scraper.get_redis') as mock_redis_getter:
            mock_redis_getter.side_effect = Exception("Redis error")

            with pytest.raises(HTTPException) as exc_info:
                await stop_scraper(mock_user)

            assert exc_info.value.status_code == 500


class TestGetScraperJobs:
    """Tests for get_scraper_jobs endpoint"""

    @pytest.mark.asyncio
    async def test_get_jobs_success(self):
        """Test getting scraper jobs"""
        from api.routes.scraper import get_scraper_jobs

        mock_user = {"id": "user-123"}

        with patch('api.routes.scraper.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.lrange = AsyncMock(return_value=[
                json.dumps({"id": "job-1", "status": "completed"}),
                json.dumps({"id": "job-2", "status": "pending"})
            ])
            mock_redis_getter.return_value = mock_redis

            result = await get_scraper_jobs(mock_user)

            assert "jobs" in result
            assert len(result["jobs"]) == 2
            assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_get_jobs_empty(self):
        """Test getting jobs when empty"""
        from api.routes.scraper import get_scraper_jobs

        mock_user = {"id": "user-123"}

        with patch('api.routes.scraper.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.lrange = AsyncMock(return_value=[])
            mock_redis_getter.return_value = mock_redis

            result = await get_scraper_jobs(mock_user)

            assert result["jobs"] == []
            assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_get_jobs_with_invalid_json(self):
        """Test getting jobs with invalid JSON data"""
        from api.routes.scraper import get_scraper_jobs

        mock_user = {"id": "user-123"}

        with patch('api.routes.scraper.get_redis') as mock_redis_getter:
            mock_redis = MagicMock()
            mock_redis.lrange = AsyncMock(return_value=[
                "invalid json",
                json.dumps({"id": "job-1"})
            ])
            mock_redis_getter.return_value = mock_redis

            result = await get_scraper_jobs(mock_user)

            assert len(result["jobs"]) == 1

    @pytest.mark.asyncio
    async def test_get_jobs_error(self):
        """Test getting jobs with error"""
        from api.routes.scraper import get_scraper_jobs
        from fastapi import HTTPException

        mock_user = {"id": "user-123"}

        with patch('api.routes.scraper.get_redis') as mock_redis_getter:
            mock_redis_getter.side_effect = Exception("Redis error")

            with pytest.raises(HTTPException) as exc_info:
                await get_scraper_jobs(mock_user)

            assert exc_info.value.status_code == 500


class TestRouter:
    """Tests for router configuration"""

    def test_router_exists(self):
        """Test router is configured"""
        from api.routes.scraper import router

        assert router is not None

    def test_router_has_routes(self):
        """Test router has expected routes"""
        from api.routes.scraper import router

        routes = [getattr(r, 'path', '') for r in router.routes]
        assert "/status" in routes
        assert "/start" in routes
        assert "/stop" in routes
        assert "/jobs" in routes


class TestImports:
    """Tests for module imports"""

    def test_auth_import(self):
        """Test auth import is used correctly"""
        from api.middleware.auth import get_current_user
        assert get_current_user is not None

    def test_redis_import(self):
        """Test Redis import"""
        from shared.redis import get_redis
        assert get_redis is not None
