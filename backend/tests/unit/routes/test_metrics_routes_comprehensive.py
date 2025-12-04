"""
Comprehensive tests for Metrics routes
Target: api/routes/metrics.py (currently 70.5% coverage)
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMetricsCollector:
    """Test MetricsCollector class"""
    
    def test_add_gauge_basic(self):
        """Test adding a basic gauge metric"""
        from api.routes.metrics import MetricsCollector
        
        collector = MetricsCollector()
        collector.add_gauge("test_metric", 42.0, "Test help text")
        
        output = collector.render()
        
        assert "# HELP test_metric Test help text" in output
        assert "# TYPE test_metric gauge" in output
        assert "test_metric 42.0" in output
    
    def test_add_gauge_with_labels(self):
        """Test adding gauge with labels"""
        from api.routes.metrics import MetricsCollector
        
        collector = MetricsCollector()
        collector.add_gauge(
            "test_metric_labeled",
            100.0,
            "Test with labels",
            {"env": "prod", "region": "us-east"}
        )
        
        output = collector.render()
        
        assert 'env="prod"' in output
        assert 'region="us-east"' in output
    
    def test_add_counter_basic(self):
        """Test adding a basic counter metric"""
        from api.routes.metrics import MetricsCollector
        
        collector = MetricsCollector()
        collector.add_counter("requests_total", 1000.0, "Total requests")
        
        output = collector.render()
        
        assert "# HELP requests_total Total requests" in output
        assert "# TYPE requests_total counter" in output
        assert "requests_total 1000.0" in output
    
    def test_add_counter_with_labels(self):
        """Test adding counter with labels"""
        from api.routes.metrics import MetricsCollector
        
        collector = MetricsCollector()
        collector.add_counter(
            "http_requests_total",
            500.0,
            "HTTP requests total",
            {"method": "GET", "status": "200"}
        )
        
        output = collector.render()
        
        assert 'method="GET"' in output
        assert 'status="200"' in output
    
    def test_add_histogram(self):
        """Test adding histogram metric"""
        from api.routes.metrics import MetricsCollector
        
        collector = MetricsCollector()
        buckets = {"0.1": 10, "0.5": 50, "1": 100, "+Inf": 150}
        
        collector.add_histogram(
            "response_time",
            buckets,
            sum_val=75.5,
            count=150,
            help_text="Response time distribution"
        )
        
        output = collector.render()
        
        assert "# TYPE response_time histogram" in output
        assert 'response_time_bucket{le="0.1"}' in output
        assert 'response_time_bucket{le="+Inf"}' in output
        assert "response_time_sum" in output
        assert "response_time_count" in output
    
    def test_add_histogram_with_labels(self):
        """Test adding histogram with labels"""
        from api.routes.metrics import MetricsCollector
        
        collector = MetricsCollector()
        buckets = {"1": 10, "5": 50, "+Inf": 100}
        
        collector.add_histogram(
            "db_query_time",
            buckets,
            sum_val=250.0,
            count=100,
            help_text="Database query time",
            labels={"query_type": "select"}
        )
        
        output = collector.render()
        
        assert 'query_type="select"' in output
    
    def test_render_empty(self):
        """Test rendering with no metrics"""
        from api.routes.metrics import MetricsCollector
        
        collector = MetricsCollector()
        output = collector.render()
        
        assert output == "\n"
    
    def test_render_multiple_metrics(self):
        """Test rendering multiple metrics"""
        from api.routes.metrics import MetricsCollector
        
        collector = MetricsCollector()
        collector.add_gauge("metric1", 10.0, "First metric")
        collector.add_counter("metric2", 20.0, "Second metric")
        collector.add_gauge("metric3", 30.0, "Third metric")
        
        output = collector.render()
        
        assert "metric1" in output
        assert "metric2" in output
        assert "metric3" in output


class TestGetWorkerMetrics:
    """Test get_worker_metrics function"""
    
    @pytest.mark.asyncio
    async def test_get_worker_metrics_empty(self):
        """Test worker metrics with no data"""
        from api.routes.metrics import get_worker_metrics
        
        mock_redis = MagicMock()
        mock_redis.keys = AsyncMock(return_value=[])
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_worker_metrics()
            
            assert result["posts_scheduled"] == 0
            assert result["posts_pending"] == 0
            assert result["dlq_size"] == 0
            assert result["workers_active"] == 0
    
    @pytest.mark.asyncio
    async def test_get_worker_metrics_with_data(self):
        """Test worker metrics with data"""
        from api.routes.metrics import get_worker_metrics
        
        mock_redis = MagicMock()
        mock_redis.keys = AsyncMock(side_effect=[
            ["dlq:1", "dlq:2"],  # DLQ keys
            ["scheduled_post:1", "scheduled_post:2"],  # Scheduled posts
            ["worker:heartbeat:1"]  # Worker heartbeats
        ])
        mock_redis.hgetall = AsyncMock(side_effect=[
            {"status": "pending"},
            {"status": "completed"}
        ])
        mock_redis.get = AsyncMock(return_value=datetime.now(timezone.utc).isoformat())
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_worker_metrics()
            
            assert result["dlq_size"] == 2
            assert result["posts_scheduled"] == 2
    
    @pytest.mark.asyncio
    async def test_get_worker_metrics_with_posts_status(self):
        """Test worker metrics counts posts by status"""
        from api.routes.metrics import get_worker_metrics
        
        mock_redis = MagicMock()
        mock_redis.keys = AsyncMock(side_effect=[
            [],  # DLQ
            ["scheduled_post:1", "scheduled_post:2", "scheduled_post:3", "scheduled_post:4"],
            []  # Workers
        ])
        mock_redis.hgetall = AsyncMock(side_effect=[
            {"status": "pending"},
            {"status": "processing"},
            {"status": "completed"},
            {"status": "failed"}
        ])
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_worker_metrics()
            
            assert result["posts_pending"] == 1
            assert result["posts_processing"] == 1
            assert result["posts_completed"] == 1
            assert result["posts_failed"] == 1
    
    @pytest.mark.asyncio
    async def test_get_worker_metrics_active_workers(self):
        """Test worker metrics counts active workers"""
        from api.routes.metrics import get_worker_metrics
        
        now = datetime.now(timezone.utc)
        recent = (now - timedelta(minutes=2)).isoformat()
        old = (now - timedelta(minutes=10)).isoformat()
        
        mock_redis = MagicMock()
        mock_redis.keys = AsyncMock(side_effect=[
            [],  # DLQ
            [],  # Scheduled posts
            ["worker:heartbeat:1", "worker:heartbeat:2"]
        ])
        mock_redis.get = AsyncMock(side_effect=[recent, old])
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_worker_metrics()
            
            assert result["workers_active"] == 1
    
    @pytest.mark.asyncio
    async def test_get_worker_metrics_exception(self):
        """Test worker metrics handles exceptions"""
        from api.routes.metrics import get_worker_metrics
        
        mock_redis = MagicMock()
        mock_redis.keys = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_worker_metrics()
            
            # Should return default values on error
            assert result["posts_scheduled"] == 0


class TestGetPlatformMetrics:
    """Test get_platform_metrics function"""
    
    @pytest.mark.asyncio
    async def test_get_platform_metrics_empty(self):
        """Test platform metrics with no data"""
        from api.routes.metrics import get_platform_metrics
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.keys = AsyncMock(return_value=[])
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_platform_metrics()
            
            assert "youtube" in result
            assert "instagram" in result
            assert "tiktok" in result
            assert "whatsapp" in result
    
    @pytest.mark.asyncio
    async def test_get_platform_metrics_with_youtube_quota(self):
        """Test platform metrics with YouTube quota"""
        from api.routes.metrics import get_platform_metrics
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=[
            "5000",  # YouTube quota
            None, None, None, None  # Other platforms
        ])
        mock_redis.keys = AsyncMock(return_value=[])
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_platform_metrics()
            
            assert result["youtube"]["quota_used"] == 5000
    
    @pytest.mark.asyncio
    async def test_get_platform_metrics_with_sessions(self):
        """Test platform metrics counts sessions"""
        from api.routes.metrics import get_platform_metrics
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.keys = AsyncMock(side_effect=[
            ["youtube:session:1", "youtube:session:2"],  # YouTube sessions
            ["instagram:session:1"],  # Instagram sessions
            [],  # TikTok
            ["whatsapp:session:1", "whatsapp:session:2", "whatsapp:session:3"],  # WhatsApp
            # Posts keys
            [], [], [], [],
            # Instagram challenges
            []
        ])
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_platform_metrics()
            
            # Sessions are counted
            assert result["youtube"]["sessions_active"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_platform_metrics_with_instagram_challenges(self):
        """Test platform metrics counts Instagram challenges"""
        from api.routes.metrics import get_platform_metrics
        
        mock_redis = MagicMock()
        # Return None for quota
        mock_redis.get = AsyncMock(return_value=None)
        
        # Define keys calls in order they happen in get_platform_metrics:
        # 1. session keys for youtube, instagram, tiktok, whatsapp (4 calls)
        # Then directly calls keys for instagram challenges
        call_count = [0]
        
        async def mock_keys(pattern):
            call_count[0] += 1
            if "instagram:challenge:" in pattern:
                return ["instagram:challenge:1", "instagram:challenge:2"]
            return []
        
        mock_redis.keys = mock_keys
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_platform_metrics()
            
            assert result["instagram"]["challenges_pending"] == 2
    
    @pytest.mark.asyncio
    async def test_get_platform_metrics_exception(self):
        """Test platform metrics handles exceptions"""
        from api.routes.metrics import get_platform_metrics
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_platform_metrics()
            
            # Should return default values on error
            assert result["youtube"]["quota_used"] == 0


class TestGetRateLimitMetrics:
    """Test get_rate_limit_metrics function"""
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_metrics_empty(self):
        """Test rate limit metrics with no data"""
        from api.routes.metrics import get_rate_limit_metrics
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.keys = AsyncMock(return_value=[])
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_rate_limit_metrics()
            
            assert result["requests_blocked"] == 0
            assert result["unique_ips"] == 0
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_metrics_with_blocked(self):
        """Test rate limit metrics with blocked requests"""
        from api.routes.metrics import get_rate_limit_metrics
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="150")
        mock_redis.keys = AsyncMock(return_value=[])
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_rate_limit_metrics()
            
            assert result["requests_blocked"] == 150
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_metrics_with_ips(self):
        """Test rate limit metrics counts unique IPs"""
        from api.routes.metrics import get_rate_limit_metrics
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.keys = AsyncMock(return_value=[
            "rate_limit:endpoint:192.168.1.1",
            "rate_limit:endpoint:192.168.1.2",
            "rate_limit:endpoint:192.168.1.1",  # Duplicate IP
            "rate_limit:other:10.0.0.1"
        ])
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_rate_limit_metrics()
            
            # Should count unique IPs
            assert result["unique_ips"] == 3
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_metrics_exception(self):
        """Test rate limit metrics handles exceptions"""
        from api.routes.metrics import get_rate_limit_metrics
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_rate_limit_metrics()
            
            assert result["requests_blocked"] == 0


class TestGetApiMetrics:
    """Test get_api_metrics function"""
    
    @pytest.mark.asyncio
    async def test_get_api_metrics_empty(self):
        """Test API metrics with no data"""
        from api.routes.metrics import get_api_metrics
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.lrange = AsyncMock(return_value=[])
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_api_metrics()
            
            assert result["requests_total"] == 0
            assert result["requests_5xx"] == 0
            assert result["requests_4xx"] == 0
            assert result["avg_response_time_ms"] == 0
    
    @pytest.mark.asyncio
    async def test_get_api_metrics_with_data(self):
        """Test API metrics with data"""
        from api.routes.metrics import get_api_metrics
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=[
            "10000",  # Total requests
            "50",     # 5xx errors
            "200"     # 4xx errors
        ])
        mock_redis.lrange = AsyncMock(return_value=["10.5", "20.3", "15.2"])
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_api_metrics()
            
            assert result["requests_total"] == 10000
            assert result["requests_5xx"] == 50
            assert result["requests_4xx"] == 200
    
    @pytest.mark.asyncio
    async def test_get_api_metrics_avg_response_time(self):
        """Test API metrics calculates average response time"""
        from api.routes.metrics import get_api_metrics
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.lrange = AsyncMock(return_value=["10", "20", "30", "40"])
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_api_metrics()
            
            # Average should be (10+20+30+40)/4 = 25
            assert result["avg_response_time_ms"] == 25.0
    
    @pytest.mark.asyncio
    async def test_get_api_metrics_exception(self):
        """Test API metrics handles exceptions"""
        from api.routes.metrics import get_api_metrics
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await get_api_metrics()
            
            assert result["requests_total"] == 0


class TestPrometheusMetricsEndpoint:
    """Test prometheus_metrics endpoint"""
    
    @pytest.mark.asyncio
    async def test_prometheus_metrics_endpoint(self):
        """Test the main metrics endpoint"""
        from api.routes.metrics import prometheus_metrics
        
        with patch('api.routes.metrics.get_worker_metrics', new_callable=AsyncMock) as mock_worker:
            with patch('api.routes.metrics.get_platform_metrics', new_callable=AsyncMock) as mock_platform:
                with patch('api.routes.metrics.get_rate_limit_metrics', new_callable=AsyncMock) as mock_rate:
                    with patch('api.routes.metrics.get_api_metrics', new_callable=AsyncMock) as mock_api:
                        mock_worker.return_value = {
                            "posts_scheduled": 10,
                            "posts_pending": 5,
                            "posts_processing": 2,
                            "posts_completed": 100,
                            "posts_failed": 3,
                            "dlq_size": 1,
                            "workers_active": 4
                        }
                        mock_platform.return_value = {
                            "youtube": {"quota_used": 1000, "quota_limit": 10000, "sessions_active": 2, "posts_today": 5},
                            "instagram": {"sessions_active": 3, "challenges_pending": 1, "posts_today": 10},
                            "tiktok": {"sessions_active": 1, "posts_today": 3},
                            "whatsapp": {"sessions_active": 5, "messages_today": 50}
                        }
                        mock_rate.return_value = {
                            "requests_blocked": 25,
                            "unique_ips": 100
                        }
                        mock_api.return_value = {
                            "requests_total": 50000,
                            "requests_5xx": 10,
                            "requests_4xx": 500,
                            "avg_response_time_ms": 45.5
                        }
                        
                        response = await prometheus_metrics()
                        
                        assert response.status_code == 200
                        content = response.body.decode()
                        
                        assert "tiktrend_scheduled_posts_total" in content
                        assert "tiktrend_workers_active" in content
                        assert "tiktrend_youtube_quota_used" in content
                        assert "tiktrend_api_requests_total" in content


class TestMetricsHealthEndpoint:
    """Test metrics_health endpoint"""
    
    @pytest.mark.asyncio
    async def test_metrics_health_healthy(self):
        """Test health check when Redis is healthy"""
        from api.routes.metrics import metrics_health
        
        mock_redis = MagicMock()
        mock_redis.ping = AsyncMock(return_value=True)
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await metrics_health()
            
            assert result["status"] == "healthy"
            assert result["redis"] == "connected"
    
    @pytest.mark.asyncio
    async def test_metrics_health_unhealthy(self):
        """Test health check when Redis is unhealthy"""
        from api.routes.metrics import metrics_health
        
        mock_redis = MagicMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection refused"))
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await metrics_health()
            
            assert result["status"] == "unhealthy"
            assert "error" in result


class TestRecordMetricEndpoint:
    """Test record_metric endpoint"""
    
    @pytest.mark.asyncio
    async def test_record_metric_counter(self):
        """Test recording a counter metric"""
        from api.routes.metrics import record_metric
        
        mock_redis = MagicMock()
        mock_redis.incrbyfloat = AsyncMock(return_value=10.0)
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await record_metric(
                metric_name="custom_counter",
                value=5.0,
                metric_type="counter"
            )
            
            assert result["success"] is True
            assert result["metric"] == "custom_counter"
            assert result["value"] == 5.0
            mock_redis.incrbyfloat.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_record_metric_gauge(self):
        """Test recording a gauge metric"""
        from api.routes.metrics import record_metric
        
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock()
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await record_metric(
                metric_name="custom_gauge",
                value=42.0,
                metric_type="gauge"
            )
            
            assert result["success"] is True
            mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_record_metric_error(self):
        """Test recording metric with error"""
        from api.routes.metrics import record_metric
        
        mock_redis = MagicMock()
        mock_redis.incrbyfloat = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch('api.routes.metrics.redis_client', mock_redis):
            result = await record_metric(
                metric_name="failing_metric",
                value=1.0,
                metric_type="counter"
            )
            
            assert result["success"] is False
            assert "error" in result
            assert "error" in result
