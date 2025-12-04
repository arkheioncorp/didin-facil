"""
Prometheus Metrics Endpoint
Exposes application metrics in Prometheus format
"""

from fastapi import APIRouter, Response
from datetime import datetime, timedelta, timezone
import asyncio
from typing import Dict, Any

from shared.redis import redis_client
from shared.config import settings

router = APIRouter()


class MetricsCollector:
    """Collect and format Prometheus metrics"""
    
    def __init__(self):
        self.metrics: list[str] = []
    
    def add_gauge(self, name: str, value: float, help_text: str, labels: Dict[str, str] = None):
        """Add a gauge metric"""
        self.metrics.append(f"# HELP {name} {help_text}")
        self.metrics.append(f"# TYPE {name} gauge")
        
        label_str = ""
        if labels:
            label_parts = [f'{k}="{v}"' for k, v in labels.items()]
            label_str = "{" + ",".join(label_parts) + "}"
        
        self.metrics.append(f"{name}{label_str} {value}")
    
    def add_counter(self, name: str, value: float, help_text: str, labels: Dict[str, str] = None):
        """Add a counter metric"""
        self.metrics.append(f"# HELP {name} {help_text}")
        self.metrics.append(f"# TYPE {name} counter")
        
        label_str = ""
        if labels:
            label_parts = [f'{k}="{v}"' for k, v in labels.items()]
            label_str = "{" + ",".join(label_parts) + "}"
        
        self.metrics.append(f"{name}{label_str} {value}")
    
    def add_histogram(self, name: str, buckets: Dict[str, float], sum_val: float, count: int, help_text: str, labels: Dict[str, str] = None):
        """Add a histogram metric"""
        self.metrics.append(f"# HELP {name} {help_text}")
        self.metrics.append(f"# TYPE {name} histogram")
        
        base_label_str = ""
        if labels:
            base_label_parts = [f'{k}="{v}"' for k, v in labels.items()]
            base_label_str = ",".join(base_label_parts) + ","
        
        for le, val in buckets.items():
            self.metrics.append(f'{name}_bucket{{{base_label_str}le="{le}"}} {val}')
        
        self.metrics.append(f'{name}_sum{{{base_label_str.rstrip(",")}}} {sum_val}')
        self.metrics.append(f'{name}_count{{{base_label_str.rstrip(",")}}} {count}')
    
    def render(self) -> str:
        """Render all metrics as Prometheus format text"""
        return "\n".join(self.metrics) + "\n"


async def get_worker_metrics() -> Dict[str, Any]:
    """Get worker-related metrics from Redis"""
    metrics = {
        "posts_scheduled": 0,
        "posts_pending": 0,
        "posts_processing": 0,
        "posts_completed": 0,
        "posts_failed": 0,
        "dlq_size": 0,
        "workers_active": 0,
    }
    
    try:
        # Get DLQ entries
        dlq_keys = await redis_client.keys("dlq:*")
        metrics["dlq_size"] = len(dlq_keys)
        
        # Get scheduled posts by status
        scheduled_keys = await redis_client.keys("scheduled_post:*")
        for key in scheduled_keys:
            try:
                data = await redis_client.hgetall(key)
                status = data.get("status", "pending")
                if status == "pending":
                    metrics["posts_pending"] += 1
                elif status == "processing":
                    metrics["posts_processing"] += 1
                elif status == "completed":
                    metrics["posts_completed"] += 1
                elif status == "failed":
                    metrics["posts_failed"] += 1
            except Exception:
                pass
        
        metrics["posts_scheduled"] = len(scheduled_keys)
        
        # Check worker heartbeats
        worker_keys = await redis_client.keys("worker:heartbeat:*")
        now = datetime.now(timezone.utc)
        for key in worker_keys:
            try:
                last_beat = await redis_client.get(key)
                if last_beat:
                    last_time = datetime.fromisoformat(last_beat)
                    if (now - last_time) < timedelta(minutes=5):
                        metrics["workers_active"] += 1
            except Exception:
                pass
                
    except Exception:
        pass
    
    return metrics


async def get_platform_metrics() -> Dict[str, Dict[str, Any]]:
    """Get platform-specific metrics"""
    platforms = {
        "youtube": {"quota_used": 0, "quota_limit": 10000, "sessions_active": 0, "posts_today": 0},
        "instagram": {"sessions_active": 0, "challenges_pending": 0, "posts_today": 0},
        "tiktok": {"sessions_active": 0, "posts_today": 0},
        "whatsapp": {"sessions_active": 0, "messages_today": 0},
    }
    
    try:
        # YouTube quota
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        quota_key = f"youtube:quota:{today}"
        quota_used = await redis_client.get(quota_key)
        if quota_used:
            platforms["youtube"]["quota_used"] = int(quota_used)
        
        # Count active sessions per platform
        for platform in platforms.keys():
            session_keys = await redis_client.keys(f"{platform}:session:*")
            platforms[platform]["sessions_active"] = len(session_keys)
        
        # Count posts today per platform
        for platform in platforms.keys():
            post_key = f"{platform}:posts:{today}"
            count = await redis_client.get(post_key)
            if count:
                platforms[platform]["posts_today"] = int(count)
        
        # Instagram challenges
        challenge_keys = await redis_client.keys("instagram:challenge:*")
        platforms["instagram"]["challenges_pending"] = len(challenge_keys)
        
    except Exception:
        pass
    
    return platforms


async def get_rate_limit_metrics() -> Dict[str, Any]:
    """Get rate limiting metrics"""
    metrics = {
        "requests_blocked": 0,
        "unique_ips": 0,
    }
    
    try:
        # Get blocked requests count
        blocked = await redis_client.get("metrics:rate_limit:blocked:total")
        if blocked:
            metrics["requests_blocked"] = int(blocked)
        
        # Count unique IPs tracked
        ip_keys = await redis_client.keys("rate_limit:*")
        unique_ips = set()
        for key in ip_keys:
            parts = key.split(":")
            if len(parts) >= 3:
                unique_ips.add(parts[2])
        metrics["unique_ips"] = len(unique_ips)
        
    except Exception:
        pass
    
    return metrics


async def get_api_metrics() -> Dict[str, Any]:
    """Get API performance metrics"""
    metrics = {
        "requests_total": 0,
        "requests_5xx": 0,
        "requests_4xx": 0,
        "avg_response_time_ms": 0,
    }
    
    try:
        # Get from Redis metrics store
        total = await redis_client.get("metrics:api:requests:total")
        if total:
            metrics["requests_total"] = int(total)
        
        errors_5xx = await redis_client.get("metrics:api:requests:5xx")
        if errors_5xx:
            metrics["requests_5xx"] = int(errors_5xx)
        
        errors_4xx = await redis_client.get("metrics:api:requests:4xx")
        if errors_4xx:
            metrics["requests_4xx"] = int(errors_4xx)
        
        # Average response time from sliding window
        response_times = await redis_client.lrange("metrics:api:response_times", 0, 99)
        if response_times:
            times = [float(t) for t in response_times]
            metrics["avg_response_time_ms"] = sum(times) / len(times)
            
    except Exception:
        pass
    
    return metrics


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus exposition format
    """
    collector = MetricsCollector()
    
    # Collect all metrics in parallel
    worker_metrics, platform_metrics, rate_limit_metrics, api_metrics = await asyncio.gather(
        get_worker_metrics(),
        get_platform_metrics(),
        get_rate_limit_metrics(),
        get_api_metrics(),
    )
    
    # === Worker Metrics ===
    collector.add_gauge(
        "tiktrend_scheduled_posts_total",
        worker_metrics["posts_scheduled"],
        "Total number of scheduled posts"
    )
    
    collector.add_gauge(
        "tiktrend_posts_pending",
        worker_metrics["posts_pending"],
        "Posts waiting to be processed"
    )
    
    collector.add_gauge(
        "tiktrend_posts_processing",
        worker_metrics["posts_processing"],
        "Posts currently being processed"
    )
    
    collector.add_counter(
        "tiktrend_posts_completed_total",
        worker_metrics["posts_completed"],
        "Total posts completed successfully"
    )
    
    collector.add_counter(
        "tiktrend_posts_failed_total",
        worker_metrics["posts_failed"],
        "Total posts failed"
    )
    
    collector.add_gauge(
        "tiktrend_dlq_size",
        worker_metrics["dlq_size"],
        "Number of entries in Dead Letter Queue"
    )
    
    collector.add_gauge(
        "tiktrend_workers_active",
        worker_metrics["workers_active"],
        "Number of active worker processes"
    )
    
    # === Platform Metrics ===
    for platform, data in platform_metrics.items():
        collector.add_gauge(
            "tiktrend_platform_sessions_active",
            data["sessions_active"],
            "Active sessions per platform",
            {"platform": platform}
        )
        
        collector.add_gauge(
            "tiktrend_platform_posts_today",
            data.get("posts_today", 0),
            "Posts published today per platform",
            {"platform": platform}
        )
    
    # YouTube specific
    collector.add_gauge(
        "tiktrend_youtube_quota_used",
        platform_metrics["youtube"]["quota_used"],
        "YouTube API quota used today"
    )
    
    collector.add_gauge(
        "tiktrend_youtube_quota_limit",
        platform_metrics["youtube"]["quota_limit"],
        "YouTube API daily quota limit"
    )
    
    collector.add_gauge(
        "tiktrend_youtube_quota_remaining",
        platform_metrics["youtube"]["quota_limit"] - platform_metrics["youtube"]["quota_used"],
        "YouTube API quota remaining"
    )
    
    # Instagram specific
    collector.add_gauge(
        "tiktrend_instagram_challenges_pending",
        platform_metrics["instagram"]["challenges_pending"],
        "Instagram security challenges awaiting resolution"
    )
    
    # === Rate Limiting Metrics ===
    collector.add_counter(
        "tiktrend_rate_limit_blocked_total",
        rate_limit_metrics["requests_blocked"],
        "Total requests blocked by rate limiter"
    )
    
    collector.add_gauge(
        "tiktrend_rate_limit_unique_ips",
        rate_limit_metrics["unique_ips"],
        "Unique IPs tracked by rate limiter"
    )
    
    # === API Metrics ===
    collector.add_counter(
        "tiktrend_api_requests_total",
        api_metrics["requests_total"],
        "Total API requests"
    )
    
    collector.add_counter(
        "tiktrend_api_errors_5xx_total",
        api_metrics["requests_5xx"],
        "Total 5xx server errors"
    )
    
    collector.add_counter(
        "tiktrend_api_errors_4xx_total",
        api_metrics["requests_4xx"],
        "Total 4xx client errors"
    )
    
    collector.add_gauge(
        "tiktrend_api_response_time_avg_ms",
        api_metrics["avg_response_time_ms"],
        "Average API response time in milliseconds"
    )
    
    # === Application Info ===
    collector.add_gauge(
        "tiktrend_app_info",
        1,
        "Application information",
        {"version": "2.0.0", "env": settings.environment if hasattr(settings, 'environment') else "production"}
    )
    
    return Response(
        content=collector.render(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@router.get("/metrics/health")
async def metrics_health():
    """Health check for metrics collection"""
    try:
        # Test Redis connection
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "redis": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.post("/metrics/record")
async def record_metric(
    metric_name: str,
    value: float,
    metric_type: str = "counter"
):
    """
    Record a custom metric
    
    Used by workers and other services to report metrics
    """
    try:
        key = f"metrics:custom:{metric_name}"
        
        if metric_type == "counter":
            await redis_client.incrbyfloat(key, value)
        else:
            await redis_client.set(key, str(value))
        
        return {"success": True, "metric": metric_name, "value": value}
    except Exception as e:
        return {"success": False, "error": str(e)}
