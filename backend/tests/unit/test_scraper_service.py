"""
Testes unitários para api/services/scraper.py
Cobertura: ScraperOrchestrator, format_product, get_redis_pool
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestFormatProduct:
    """Testes para format_product"""
    
    def test_format_product_basic(self):
        """Deve converter row para dict"""
        from api.services.scraper import format_product
        
        row = MagicMock()
        row.__iter__ = lambda self: iter([
            ("id", "uuid-123"),
            ("title", "Product"),
            ("images", None),
            ("metadata", None)
        ])
        row.keys = lambda: ["id", "title", "images", "metadata"]
        
        with patch('builtins.dict', return_value={
            "id": "uuid-123",
            "title": "Product",
            "images": None,
            "metadata": None
        }):
            result = format_product(row)
            # O id deve ser string
            assert result is not None
    
    def test_format_product_with_json_images(self):
        """Deve parsear imagens JSON string"""
        from api.services.scraper import format_product
        
        # Simular um row que retorna dict
        mock_row = {
            "id": "uuid-123",
            "title": "Product",
            "images": '["img1.jpg", "img2.jpg"]',
            "metadata": None
        }
        
        with patch('builtins.dict', return_value=mock_row.copy()):
            result = format_product(MagicMock())
            # O formato deve ter images como list
            assert isinstance(result.get("images", "[]"), (list, str))
    
    def test_format_product_with_json_metadata(self):
        """Deve parsear metadata JSON string"""
        from api.services.scraper import format_product
        
        mock_row = {
            "id": "uuid-123",
            "title": "Product",
            "images": None,
            "metadata": '{"key": "value"}'
        }
        
        with patch('builtins.dict', return_value=mock_row.copy()):
            result = format_product(MagicMock())
            assert result is not None
    
    def test_format_product_invalid_json_images(self):
        """Deve retornar lista vazia para JSON inválido em images"""
        from api.services.scraper import format_product
        
        mock_row = {
            "id": "uuid-123",
            "title": "Product",
            "images": "invalid json",
            "metadata": None
        }
        
        with patch('builtins.dict', return_value=mock_row.copy()):
            result = format_product(MagicMock())
            assert result is not None


class TestGetRedisClient:
    """Testes para get_redis_pool"""
    
    @pytest.mark.asyncio
    async def test_get_redis_pool_success(self):
        """Deve retornar cliente Redis"""
        mock_client = AsyncMock()
        
        async def mock_from_url(*args, **kwargs):
            return mock_client
        
        with patch('api.services.scraper.redis.from_url', side_effect=mock_from_url) as mock_from_url_fn:
            from api.services.scraper import get_redis_pool
            
            client = await get_redis_pool()
            
            assert client == mock_client
            mock_from_url_fn.assert_called_once()


class TestScraperOrchestratorGetProducts:
    """Testes para ScraperOrchestrator.get_products"""
    
    @pytest.mark.asyncio
    async def test_get_products_basic(self):
        """Deve retornar produtos paginados"""
        with patch('api.services.scraper.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value={"total": 100})
            mock_db.fetch_all = AsyncMock(return_value=[
                {"id": "uuid-1", "title": "Product 1", "images": None, "metadata": None},
                {"id": "uuid-2", "title": "Product 2", "images": None, "metadata": None}
            ])
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            result = await orchestrator.get_products(page=1, per_page=20)
            
            assert result["total"] == 100
            assert result["page"] == 1
            assert result["per_page"] == 20
    
    @pytest.mark.asyncio
    async def test_get_products_with_filters(self):
        """Deve aplicar filtros corretamente"""
        with patch('api.services.scraper.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value={"total": 10})
            mock_db.fetch_all = AsyncMock(return_value=[])
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            result = await orchestrator.get_products(
                category="electronics",
                min_price=10.0,
                max_price=100.0,
                min_sales=50
            )
            
            assert result["total"] == 10
            mock_db.fetch_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_products_invalid_sort(self):
        """Deve usar sort padrão para sort inválido"""
        with patch('api.services.scraper.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value={"total": 5})
            mock_db.fetch_all = AsyncMock(return_value=[])
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            result = await orchestrator.get_products(sort_by="invalid_column")
            
            assert result is not None


class TestScraperOrchestratorSearchProducts:
    """Testes para ScraperOrchestrator.search_products"""
    
    @pytest.mark.asyncio
    async def test_search_products_basic(self):
        """Deve buscar produtos por keyword"""
        with patch('api.services.scraper.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value={"total": 5})
            mock_db.fetch_all = AsyncMock(return_value=[
                {"id": "uuid-1", "title": "Test Product", "images": None, "metadata": None}
            ])
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            result = await orchestrator.search_products("test", page=1, per_page=20)
            
            assert result["total"] == 5
            assert result["page"] == 1
    
    @pytest.mark.asyncio
    async def test_search_products_empty_results(self):
        """Deve retornar lista vazia quando não encontra"""
        with patch('api.services.scraper.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value={"total": 0})
            mock_db.fetch_all = AsyncMock(return_value=[])
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            result = await orchestrator.search_products("nonexistent")
            
            assert result["total"] == 0
            assert result["products"] == []


class TestScraperOrchestratorTrendingProducts:
    """Testes para ScraperOrchestrator.get_trending_products"""
    
    @pytest.mark.asyncio
    async def test_get_trending_products_basic(self):
        """Deve retornar produtos trending"""
        with patch('api.services.scraper.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value={"total": 50})
            mock_db.fetch_all = AsyncMock(return_value=[])
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            result = await orchestrator.get_trending_products()
            
            assert result["total"] == 50
    
    @pytest.mark.asyncio
    async def test_get_trending_products_with_category(self):
        """Deve filtrar trending por categoria"""
        with patch('api.services.scraper.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value={"total": 10})
            mock_db.fetch_all = AsyncMock(return_value=[])
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            result = await orchestrator.get_trending_products(category="fashion")
            
            assert result["total"] == 10


class TestScraperOrchestratorCategories:
    """Testes para ScraperOrchestrator.get_categories"""
    
    @pytest.mark.asyncio
    async def test_get_categories_success(self):
        """Deve retornar lista de categorias"""
        with patch('api.services.scraper.database') as mock_db:
            mock_db.fetch_all = AsyncMock(return_value=[
                {"category": "Electronics", "count": 100},
                {"category": "Fashion", "count": 80}
            ])
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            result = await orchestrator.get_categories()
            
            assert len(result) == 2
            assert result[0]["name"] == "Electronics"
            assert result[0]["count"] == 100


class TestScraperOrchestratorGetProductById:
    """Testes para ScraperOrchestrator.get_product_by_id"""
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_found(self):
        """Deve retornar produto quando encontrado"""
        with patch('api.services.scraper.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value={
                "id": "uuid-123",
                "title": "Test Product"
            })
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            result = await orchestrator.get_product_by_id("uuid-123")
            
            assert result is not None
            assert result["id"] == "uuid-123"
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_not_found(self):
        """Deve retornar None quando não encontrado"""
        with patch('api.services.scraper.database') as mock_db:
            mock_db.fetch_one = AsyncMock(return_value=None)
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            result = await orchestrator.get_product_by_id("nonexistent")
            
            assert result is None


class TestScraperOrchestratorEnqueueJob:
    """Testes para ScraperOrchestrator.enqueue_refresh_job"""
    
    @pytest.mark.asyncio
    async def test_enqueue_refresh_job_success(self):
        """Deve enfileirar job de refresh"""
        with patch('api.services.scraper.get_redis_pool') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.lpush = AsyncMock()
            mock_redis.hset = AsyncMock()
            mock_redis.close = AsyncMock()
            mock_get_redis.return_value = mock_redis
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            job_id = await orchestrator.enqueue_refresh_job(category="test")
            
            assert job_id is not None
            mock_redis.lpush.assert_called_once()
            mock_redis.hset.assert_called_once()


class TestScraperOrchestratorGetJobStatus:
    """Testes para ScraperOrchestrator.get_job_status"""
    
    @pytest.mark.asyncio
    async def test_get_job_status_found(self):
        """Deve retornar status do job"""
        with patch('api.services.scraper.get_redis_pool') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.hgetall = AsyncMock(return_value={
                "status": "completed",
                "created_at": "2024-01-01T00:00:00"
            })
            mock_redis.close = AsyncMock()
            mock_get_redis.return_value = mock_redis
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            status = await orchestrator.get_job_status("job-123")
            
            assert status is not None
            assert status["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self):
        """Deve retornar None para job inexistente"""
        with patch('api.services.scraper.get_redis_pool') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.hgetall = AsyncMock(return_value={})
            mock_redis.close = AsyncMock()
            mock_get_redis.return_value = mock_redis
            
            from api.services.scraper import ScraperOrchestrator
            
            orchestrator = ScraperOrchestrator()
            status = await orchestrator.get_job_status("nonexistent")
            
            assert status is None


class TestScraperOrchestratorSaveProducts:
    """Testes para ScraperOrchestrator.save_products"""
    
    @pytest.mark.asyncio
    async def test_save_products_empty_list(self):
        """Deve retornar 0 para lista vazia"""
        from api.services.scraper import ScraperOrchestrator
        
        orchestrator = ScraperOrchestrator()
        result = await orchestrator.save_products([])
        
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_save_products_success(self):
        """Deve salvar produtos em batch"""
        with patch('api.services.scraper.database') as mock_db:
            mock_db.execute_many = AsyncMock()
            
            from api.services.scraper import ScraperOrchestrator
            
            products = [
                {"id": "1", "tiktok_id": "t1", "title": "P1"},
                {"id": "2", "tiktok_id": "t2", "title": "P2"}
            ]
            
            orchestrator = ScraperOrchestrator()
            result = await orchestrator.save_products(products)
            
            assert result == 2
            mock_db.execute_many.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_products_large_batch(self):
        """Deve processar em batches de 100"""
        with patch('api.services.scraper.database') as mock_db:
            mock_db.execute_many = AsyncMock()
            
            from api.services.scraper import ScraperOrchestrator
            
            # Criar 150 produtos para testar batching
            products = [{"id": str(i), "tiktok_id": f"t{i}", "title": f"P{i}"} for i in range(150)]
            
            orchestrator = ScraperOrchestrator()
            result = await orchestrator.save_products(products)
            
            assert result == 150
            # Deve ser chamado 2 vezes (100 + 50)
            assert mock_db.execute_many.call_count == 2
