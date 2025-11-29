"""
Tests for Metrics Routes
"""

import pytest
from unittest.mock import AsyncMock, patch
from api.routes.metrics import MetricsCollector


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_add_gauge_basic(self):
        """Test adding basic gauge metric."""
        collector = MetricsCollector()
        collector.add_gauge("test_metric", 42.0, "Test help text")
        
        output = collector.render()
        assert "# HELP test_metric Test help text" in output
        assert "# TYPE test_metric gauge" in output
        assert "test_metric 42.0" in output

    def test_add_gauge_with_labels(self):
        """Test adding gauge metric with labels."""
        collector = MetricsCollector()
        collector.add_gauge(
            "test_metric",
            42.0,
            "Test help text",
            labels={"instance": "localhost", "job": "test"}
        )
        
        output = collector.render()
        assert 'instance="localhost"' in output
        assert 'job="test"' in output

    def test_add_counter_basic(self):
        """Test adding basic counter metric."""
        collector = MetricsCollector()
        collector.add_counter("request_count", 100, "Total requests")
        
        output = collector.render()
        assert "# TYPE request_count counter" in output
        assert "request_count 100" in output

    def test_add_counter_with_labels(self):
        """Test adding counter metric with labels."""
        collector = MetricsCollector()
        collector.add_counter(
            "request_count",
            100,
            "Total requests",
            labels={"method": "GET", "status": "200"}
        )
        
        output = collector.render()
        assert 'method="GET"' in output
        assert 'status="200"' in output

    def test_add_histogram(self):
        """Test adding histogram metric."""
        collector = MetricsCollector()
        buckets = {"0.1": 10, "0.5": 50, "1.0": 80, "+Inf": 100}
        collector.add_histogram(
            "response_time",
            buckets,
            sum_val=75.5,
            count=100,
            help_text="Response time in seconds"
        )
        
        output = collector.render()
        assert "# TYPE response_time histogram" in output
        assert 'response_time_bucket{le="0.1"}' in output
        assert 'response_time_bucket{le="+Inf"}' in output
        assert "response_time_sum" in output
        assert "response_time_count" in output

    def test_add_histogram_with_labels(self):
        """Test adding histogram metric with labels."""
        collector = MetricsCollector()
        buckets = {"0.5": 50, "1.0": 80}
        collector.add_histogram(
            "response_time",
            buckets,
            sum_val=75.5,
            count=100,
            help_text="Response time",
            labels={"endpoint": "/api/test"}
        )
        
        output = collector.render()
        assert 'endpoint="/api/test"' in output

    def test_render_empty(self):
        """Test rendering empty metrics."""
        collector = MetricsCollector()
        output = collector.render()
        assert output == "\n"

    def test_render_multiple_metrics(self):
        """Test rendering multiple metrics."""
        collector = MetricsCollector()
        collector.add_gauge("metric1", 1.0, "First metric")
        collector.add_counter("metric2", 2, "Second metric")
        
        output = collector.render()
        assert "metric1 1.0" in output
        assert "metric2 2" in output


class TestGetWorkerMetrics:
    """Tests for worker metrics collection."""

    @pytest.mark.asyncio
    async def test_get_worker_metrics_redis_error(self):
        """Test worker metrics when Redis has errors."""
        from api.routes.metrics import get_worker_metrics
        
        with patch("api.routes.metrics.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(side_effect=Exception("Redis error"))
            
            metrics = await get_worker_metrics()
            
            # Should return defaults on error
            assert metrics["posts_scheduled"] == 0
            assert metrics["dlq_size"] == 0


class TestGetPlatformMetrics:
    """Tests for platform metrics collection."""

    @pytest.mark.asyncio
    async def test_get_platform_metrics_empty(self):
        """Test platform metrics when no data exists."""
        from api.routes.metrics import get_platform_metrics
        
        with patch("api.routes.metrics.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.keys = AsyncMock(return_value=[])
            
            metrics = await get_platform_metrics()
            
            assert "youtube" in metrics
            assert "instagram" in metrics
            assert metrics["youtube"]["quota_used"] == 0


class TestGetApiMetrics:
    """Tests for API metrics collection."""

    @pytest.mark.asyncio
    async def test_get_api_metrics_empty(self):
        """Test API metrics when no data exists."""
        from api.routes.metrics import get_api_metrics
        
        with patch("api.routes.metrics.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.lrange = AsyncMock(return_value=[])
            
            metrics = await get_api_metrics()
            
            assert metrics["requests_total"] == 0
            assert metrics["avg_response_time_ms"] == 0


class TestPrometheusMetricsEndpoint:
    """Tests for the /metrics HTTP endpoint."""

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        """Test the /metrics endpoint returns Prometheus format."""
        from api.routes.metrics import prometheus_metrics
        
        with patch("api.routes.metrics.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[])
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.lrange = AsyncMock(return_value=[])
            
            response = await prometheus_metrics()
            
            assert "text/plain" in response.media_type
            assert b"# HELP" in response.body
            assert b"didin_" in response.body
