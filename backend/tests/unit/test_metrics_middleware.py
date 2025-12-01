"""
Unit tests for Metrics Middleware
Tests for API request metrics collection
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.middleware.metrics import MetricsMiddleware
from fastapi import FastAPI, Request, Response
from starlette.testclient import TestClient


class TestMetricsMiddleware:
    """Tests for MetricsMiddleware class"""

    @pytest.fixture
    def mock_redis(self):
        """Mock redis client"""
        with patch("api.middleware.metrics.redis_client") as mock:
            mock.incr = AsyncMock()
            mock.lpush = AsyncMock()
            mock.ltrim = AsyncMock()
            yield mock

    @pytest.fixture
    def app(self):
        """Create test FastAPI app"""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        @app.get("/products/{product_id}")
        async def get_product(product_id: str):
            return {"id": product_id}

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        return app

    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance"""
        return MetricsMiddleware(app)

    def test_middleware_initialization(self, middleware):
        """Test middleware initializes correctly"""
        assert middleware is not None

    def test_normalize_path_simple(self, middleware):
        """Test path normalization for simple paths"""
        assert middleware._normalize_path("/test") == "/test"
        assert middleware._normalize_path("/api/v1/test") == "/api/v1/test"

    def test_normalize_path_with_numeric_id(self, middleware):
        """Test path normalization with numeric IDs"""
        assert middleware._normalize_path("/products/123") == "/products/:id"
        assert middleware._normalize_path("/users/456/orders") == "/users/:id/orders"

    def test_normalize_path_with_uuid(self, middleware):
        """Test path normalization with UUIDs"""
        uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        result = middleware._normalize_path(f"/users/{uuid}")
        assert result == "/users/:id"

    def test_normalize_path_multiple_ids(self, middleware):
        """Test path normalization with multiple IDs"""
        result = middleware._normalize_path("/users/123/orders/456")
        assert result == "/users/:id/orders/:id"

    def test_normalize_path_empty(self, middleware):
        """Test path normalization for root"""
        assert middleware._normalize_path("/") == "/"

    def test_normalize_path_preserves_text(self, middleware):
        """Test path normalization preserves text parts"""
        result = middleware._normalize_path("/api/v1/products/list")
        assert result == "/api/v1/products/list"

    @pytest.mark.asyncio
    async def test_dispatch_normal_request(self, mock_redis, app):
        """Test dispatch records metrics for normal request"""
        middleware = MetricsMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/test"
        mock_request.method = "GET"

        mock_response = Response(content=b"test", status_code=200)
        mock_call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200
        mock_redis.incr.assert_called()

    @pytest.mark.asyncio
    async def test_dispatch_skips_metrics_endpoint(self, mock_redis, app):
        """Test dispatch skips /metrics endpoint"""
        middleware = MetricsMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/metrics"
        mock_request.method = "GET"

        mock_response = Response(content=b"metrics", status_code=200)
        mock_call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200
        # Should not record metrics for /metrics endpoint
        mock_redis.incr.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_skips_metrics_subpaths(self, mock_redis, app):
        """Test dispatch skips /metrics/* endpoints"""
        middleware = MetricsMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/metrics/prometheus"
        mock_request.method = "GET"

        mock_response = Response(content=b"prometheus", status_code=200)
        mock_call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, mock_call_next)

        mock_redis.incr.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_handles_exception(self, mock_redis, app):
        """Test dispatch handles exception and records error"""
        middleware = MetricsMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/error"
        mock_request.method = "GET"

        mock_call_next = AsyncMock(side_effect=ValueError("Test error"))

        with pytest.raises(ValueError):
            await middleware.dispatch(mock_request, mock_call_next)

        # Should still record metrics for error
        mock_redis.incr.assert_called()

    @pytest.mark.asyncio
    async def test_record_metrics_success(self, mock_redis, middleware):
        """Test _record_metrics for successful request"""
        await middleware._record_metrics(
            method="GET",
            path="/test",
            status_code=200,
            response_time_ms=50.0
        )

        mock_redis.incr.assert_any_call("metrics:api:requests:total")
        mock_redis.incr.assert_any_call("metrics:api:requests:2xx")
        mock_redis.lpush.assert_called_once()
        mock_redis.ltrim.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_metrics_4xx(self, mock_redis, middleware):
        """Test _record_metrics for 4xx status"""
        await middleware._record_metrics(
            method="GET",
            path="/notfound",
            status_code=404,
            response_time_ms=10.0
        )

        mock_redis.incr.assert_any_call("metrics:api:requests:4xx")

    @pytest.mark.asyncio
    async def test_record_metrics_5xx(self, mock_redis, middleware):
        """Test _record_metrics for 5xx status"""
        await middleware._record_metrics(
            method="GET",
            path="/error",
            status_code=500,
            response_time_ms=100.0
        )

        mock_redis.incr.assert_any_call("metrics:api:requests:5xx")

    @pytest.mark.asyncio
    async def test_record_metrics_redis_error_handled(self, middleware):
        """Test _record_metrics handles Redis errors gracefully"""
        with patch("api.middleware.metrics.redis_client") as mock_redis:
            mock_redis.incr = AsyncMock(
                side_effect=Exception("Redis unavailable")
            )

            # Should not raise exception
            await middleware._record_metrics(
                method="GET",
                path="/test",
                status_code=200,
                response_time_ms=50.0
            )

    @pytest.mark.asyncio
    async def test_record_metrics_endpoint_key(self, mock_redis, middleware):
        """Test _record_metrics creates correct endpoint key"""
        await middleware._record_metrics(
            method="POST",
            path="/api/users",
            status_code=201,
            response_time_ms=75.0
        )

        # Should call incr with endpoint key
        calls = [call.args[0] for call in mock_redis.incr.call_args_list]
        assert any("endpoint:POST" in call for call in calls)

    @pytest.mark.asyncio
    async def test_record_metrics_response_time_window(
        self, mock_redis, middleware
    ):
        """Test _record_metrics maintains response time window"""
        await middleware._record_metrics(
            method="GET",
            path="/test",
            status_code=200,
            response_time_ms=123.45
        )

        mock_redis.lpush.assert_called_with(
            "metrics:api:response_times",
            "123.45"
        )
        mock_redis.ltrim.assert_called_with(
            "metrics:api:response_times",
            0,
            99
        )

    @pytest.mark.asyncio
    async def test_dispatch_records_method(self, mock_redis, app):
        """Test dispatch correctly records HTTP method"""
        middleware = MetricsMiddleware(app)

        for method in ["GET", "POST", "PUT", "DELETE"]:
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/test"
            mock_request.method = method

            mock_response = Response(content=b"test", status_code=200)
            mock_call_next = AsyncMock(return_value=mock_response)

            await middleware.dispatch(mock_request, mock_call_next)

    @pytest.mark.asyncio
    async def test_dispatch_calculates_response_time(
        self, mock_redis, app
    ):
        """Test dispatch calculates response time correctly"""
        middleware = MetricsMiddleware(app)

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/test"
        mock_request.method = "GET"

        async def slow_response(request):
            import asyncio
            await asyncio.sleep(0.01)  # 10ms delay
            return Response(content=b"test", status_code=200)

        mock_call_next = AsyncMock(side_effect=slow_response)

        response = await middleware.dispatch(mock_request, mock_call_next)

        # Response time should be recorded
        assert mock_redis.lpush.called

    @pytest.mark.asyncio
    async def test_dispatch_metric_error_doesnt_break_request(
        self, app
    ):
        """Test that metric recording errors don't break the request"""
        middleware = MetricsMiddleware(app)

        with patch("api.middleware.metrics.redis_client") as mock_redis:
            mock_redis.incr = AsyncMock(
                side_effect=Exception("Redis error")
            )

            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/test"
            mock_request.method = "GET"

            mock_response = Response(content=b"test", status_code=200)
            mock_call_next = AsyncMock(return_value=mock_response)

            # Should not raise, request should complete
            response = await middleware.dispatch(mock_request, mock_call_next)
            assert response.status_code == 200


class TestNormalizePath:
    """Additional tests for path normalization edge cases"""

    @pytest.fixture
    def middleware(self):
        app = FastAPI()
        return MetricsMiddleware(app)

    def test_normalize_very_long_path(self, middleware):
        """Test normalization of very long paths"""
        long_path = "/a/b/c/d/e/f/g/h/i/j/k/l/m/n/o/p"
        result = middleware._normalize_path(long_path)
        assert result.startswith("/")

    def test_normalize_path_with_query_params_stripped(self, middleware):
        """Test that path without query params works"""
        result = middleware._normalize_path("/test")
        assert "?" not in result

    def test_normalize_mixed_ids(self, middleware):
        """Test path with mixed ID formats"""
        # Mix of numeric and text
        result = middleware._normalize_path("/users/123/settings")
        assert result == "/users/:id/settings"

    def test_normalize_preserves_version(self, middleware):
        """Test that API version is preserved"""
        result = middleware._normalize_path("/api/v1/users/123")
        assert "v1" in result
        assert ":id" in result
