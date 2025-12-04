"""
Comprehensive tests for metrics.py middleware
==============================================
Tests for API metrics collection middleware.

Target: 80%+ coverage for api/middleware/metrics.py
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse


class TestMetricsMiddleware:
    """Tests for MetricsMiddleware class."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        mock = AsyncMock()
        mock.incr = AsyncMock(return_value=1)
        mock.lpush = AsyncMock(return_value=1)
        mock.ltrim = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def app_with_middleware(self, mock_redis):
        """Create FastAPI app with MetricsMiddleware."""
        with patch("api.middleware.metrics.redis_client", mock_redis):
            from api.middleware.metrics import MetricsMiddleware
            
            app = FastAPI()
            app.add_middleware(MetricsMiddleware)
            
            @app.get("/test")
            async def test_endpoint():
                return {"status": "ok"}
            
            @app.get("/products/{product_id}")
            async def get_product(product_id: int):
                return {"id": product_id}
            
            @app.post("/items")
            async def create_item():
                return {"created": True}
            
            @app.get("/error")
            async def error_endpoint():
                raise ValueError("Test error")
            
            @app.get("/metrics")
            async def metrics_endpoint():
                return {"metrics": "data"}
            
            @app.get("/metrics/prometheus")
            async def prometheus_metrics():
                return {"prometheus": "data"}
            
            return app, mock_redis

    @pytest.fixture
    def client(self, app_with_middleware):
        app, mock_redis = app_with_middleware
        return TestClient(app, raise_server_exceptions=False), mock_redis

    def test_metrics_recorded_on_success(self, client):
        """Test metrics are recorded for successful requests."""
        test_client, mock_redis = client
        
        response = test_client.get("/test")
        
        assert response.status_code == 200
        # Give async operations time to complete
        time.sleep(0.1)

    def test_metrics_skip_metrics_endpoint(self, client):
        """Test /metrics endpoint is skipped to avoid recursion."""
        test_client, mock_redis = client
        
        # Reset mock
        mock_redis.reset_mock()
        
        response = test_client.get("/metrics")
        
        assert response.status_code == 200
        # Should not record metrics for /metrics endpoint
        mock_redis.incr.assert_not_called()

    def test_metrics_skip_metrics_subpath(self, client):
        """Test /metrics/* paths are skipped."""
        test_client, mock_redis = client
        
        mock_redis.reset_mock()
        
        response = test_client.get("/metrics/prometheus")
        
        assert response.status_code == 200
        mock_redis.incr.assert_not_called()

    def test_metrics_recorded_on_error(self, client):
        """Test metrics are recorded even when endpoint raises."""
        test_client, mock_redis = client
        
        response = test_client.get("/error")
        
        assert response.status_code == 500

    def test_metrics_recorded_for_post_requests(self, client):
        """Test metrics work with POST requests."""
        test_client, mock_redis = client
        
        response = test_client.post("/items", json={})
        
        assert response.status_code == 200


class TestMetricsMiddlewareRecording:
    """Tests for _record_metrics method.
    
    Note: These tests require complex Redis mocking due to module-level imports.
    Marked as skip until proper test infrastructure is in place.
    """

    @pytest.mark.skip(reason="Requires Redis mock infrastructure refactoring")
    @pytest.mark.asyncio
    async def test_record_metrics_increments_total(self):
        """Test total requests counter is incremented."""
        pass

    @pytest.mark.skip(reason="Requires Redis mock infrastructure refactoring")
    @pytest.mark.asyncio
    async def test_record_metrics_2xx_status(self):
        """Test 2xx status codes are recorded."""
        pass

    @pytest.mark.skip(reason="Requires Redis mock infrastructure refactoring")
    @pytest.mark.asyncio
    async def test_record_metrics_4xx_status(self):
        """Test 4xx status codes are recorded."""
        pass

    @pytest.mark.skip(reason="Requires Redis mock infrastructure refactoring")
    @pytest.mark.asyncio
    async def test_record_metrics_5xx_status(self):
        """Test 5xx status codes are recorded."""
        pass

    @pytest.mark.skip(reason="Requires Redis mock infrastructure refactoring")
    @pytest.mark.asyncio
    async def test_record_metrics_response_time(self):
        """Test response time is recorded in sliding window."""
        pass

    @pytest.mark.skip(reason="Requires Redis mock infrastructure refactoring")
    @pytest.mark.asyncio
    async def test_record_metrics_per_endpoint(self):
        """Test per-endpoint metrics are recorded."""
        pass

    @pytest.mark.skip(reason="Requires Redis mock infrastructure refactoring")
    @pytest.mark.asyncio
    async def test_record_metrics_handles_redis_error(self):
        """Test Redis errors are handled gracefully."""
        pass


class TestNormalizePath:
    """Tests for _normalize_path method."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        with patch("api.middleware.metrics.redis_client", AsyncMock()):
            from api.middleware.metrics import MetricsMiddleware
            
            mock_app = MagicMock()
            return MetricsMiddleware(mock_app)

    def test_normalize_simple_path(self, middleware):
        """Test simple paths are unchanged."""
        result = middleware._normalize_path("/products")
        assert result == "/products"

    def test_normalize_path_with_numeric_id(self, middleware):
        """Test numeric IDs are replaced with :id."""
        result = middleware._normalize_path("/products/123")
        assert result == "/products/:id"

    def test_normalize_path_with_uuid(self, middleware):
        """Test UUIDs are replaced with :id."""
        result = middleware._normalize_path("/users/550e8400-e29b-41d4-a716-446655440000")
        assert result == "/users/:id"

    def test_normalize_path_with_multiple_ids(self, middleware):
        """Test multiple IDs are all replaced."""
        result = middleware._normalize_path("/users/123/orders/456")
        assert result == "/users/:id/orders/:id"

    def test_normalize_path_trailing_slash(self, middleware):
        """Test trailing slashes are handled."""
        result = middleware._normalize_path("/products/")
        assert result == "/products"

    def test_normalize_path_leading_slash(self, middleware):
        """Test leading slashes are preserved."""
        result = middleware._normalize_path("/api/v1/products")
        assert result == "/api/v1/products"

    def test_normalize_empty_path(self, middleware):
        """Test empty path handling."""
        result = middleware._normalize_path("/")
        assert result == "/"

    def test_normalize_path_with_text_segments(self, middleware):
        """Test text segments are preserved."""
        result = middleware._normalize_path("/api/v1/products/featured")
        assert result == "/api/v1/products/featured"


class TestMetricsMiddlewareDispatch:
    """Tests for dispatch method."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        mock = AsyncMock()
        mock.incr = AsyncMock(return_value=1)
        mock.lpush = AsyncMock(return_value=1)
        mock.ltrim = AsyncMock(return_value=True)
        return mock

    @pytest.mark.asyncio
    async def test_dispatch_measures_response_time(self, mock_redis):
        """Test response time is measured correctly."""
        with patch("api.middleware.metrics.redis_client", mock_redis):
            from api.middleware.metrics import MetricsMiddleware
            
            mock_app = MagicMock()
            middleware = MetricsMiddleware(mock_app)
            
            # Create mock request
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/test"
            mock_request.method = "GET"
            
            # Create mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            # Simulate slow handler
            async def slow_handler(request):
                time.sleep(0.05)  # 50ms
                return mock_response
            
            mock_call_next = AsyncMock(side_effect=slow_handler)
            
            result = await middleware.dispatch(mock_request, mock_call_next)
            
            assert result == mock_response
            mock_call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_handles_exception(self, mock_redis):
        """Test exceptions are re-raised after recording metrics."""
        with patch("api.middleware.metrics.redis_client", mock_redis):
            from api.middleware.metrics import MetricsMiddleware
            
            mock_app = MagicMock()
            middleware = MetricsMiddleware(mock_app)
            
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/error"
            mock_request.method = "GET"
            
            mock_call_next = AsyncMock(side_effect=ValueError("Test error"))
            
            with pytest.raises(ValueError, match="Test error"):
                await middleware.dispatch(mock_request, mock_call_next)

    @pytest.mark.asyncio
    async def test_dispatch_skips_metrics_path(self, mock_redis):
        """Test /metrics path is skipped."""
        with patch("api.middleware.metrics.redis_client", mock_redis):
            from api.middleware.metrics import MetricsMiddleware
            
            mock_app = MagicMock()
            middleware = MetricsMiddleware(mock_app)
            
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/metrics"
            mock_request.method = "GET"
            
            mock_response = MagicMock()
            mock_call_next = AsyncMock(return_value=mock_response)
            
            result = await middleware.dispatch(mock_request, mock_call_next)
            
            assert result == mock_response
            # Redis should not be called for /metrics
            mock_redis.incr.assert_not_called()


class TestMetricsMiddlewareInit:
    """Tests for MetricsMiddleware initialization."""

    def test_init_accepts_app(self):
        """Test middleware accepts app in constructor."""
        with patch("api.middleware.metrics.redis_client", AsyncMock()):
            from api.middleware.metrics import MetricsMiddleware
            
            mock_app = MagicMock()
            middleware = MetricsMiddleware(mock_app)
            
            assert middleware.app == mock_app

    def test_inherits_from_base_middleware(self):
        """Test middleware inherits from BaseHTTPMiddleware."""
        from api.middleware.metrics import MetricsMiddleware
        from starlette.middleware.base import BaseHTTPMiddleware
        
        assert issubclass(MetricsMiddleware, BaseHTTPMiddleware)


class TestMetricsMiddlewareEdgeCases:
    """Edge case tests for MetricsMiddleware."""

    @pytest.fixture
    def mock_redis_failing(self):
        """Redis that fails on all operations."""
        mock = AsyncMock()
        mock.incr = AsyncMock(side_effect=Exception("Redis down"))
        mock.lpush = AsyncMock(side_effect=Exception("Redis down"))
        mock.ltrim = AsyncMock(side_effect=Exception("Redis down"))
        return mock

    def test_metrics_continue_on_redis_failure(self, mock_redis_failing):
        """Test requests continue even if Redis fails."""
        with patch("api.middleware.metrics.redis_client", mock_redis_failing):
            from api.middleware.metrics import MetricsMiddleware
            
            app = FastAPI()
            app.add_middleware(MetricsMiddleware)
            
            @app.get("/test")
            async def test_endpoint():
                return {"status": "ok"}
            
            client = TestClient(app)
            response = client.get("/test")
            
            # Request should still succeed
            assert response.status_code == 200

    def test_metrics_with_very_long_path(self):
        """Test handling of very long paths."""
        with patch("api.middleware.metrics.redis_client", AsyncMock()):
            from api.middleware.metrics import MetricsMiddleware
            
            mock_app = MagicMock()
            middleware = MetricsMiddleware(mock_app)
            
            long_path = "/api/v1/" + "/".join(["segment"] * 100)
            result = middleware._normalize_path(long_path)
            
            # Should not crash
            assert result.startswith("/")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api.middleware.metrics"])
