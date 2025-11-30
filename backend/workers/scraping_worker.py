"""
TikTok Scraping Worker
Automated background scraping with configurable intervals and caching
"""

import asyncio
import json
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

# Add backend to path (needed for standalone execution)
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from shared.redis import get_redis  # noqa: E402
from scraper.cache import get_product_cache  # noqa: E402
from scraper.tiktok import TikTokAPIScraper, get_api_scraper  # noqa: E402


@dataclass
class ScraperJobConfig:
    """Configuration for a scraping job"""
    name: str
    enabled: bool = True
    interval_minutes: int = 30
    keywords: Optional[List[str]] = None
    limit: int = 50
    priority: int = 1  # Lower = higher priority
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ScraperJobResult:
    """Result of a scraping job execution"""
    job_name: str
    success: bool
    products_found: int
    products_cached: int
    duration_seconds: float
    error: Optional[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class TikTokScrapingWorker:
    """
    Background worker for automated TikTok product scraping.
    
    Features:
    - Configurable scraping jobs (trending, search, categories)
    - Redis-based job queue and state management
    - Automatic caching of scraped products
    - Health monitoring and metrics
    - Graceful shutdown handling
    """
    
    REDIS_PREFIX = "worker:scraper:"
    
    # Default job configurations
    DEFAULT_JOBS = [
        ScraperJobConfig(
            name="trending",
            enabled=True,
            interval_minutes=30,
            limit=50,
            priority=1,
        ),
        ScraperJobConfig(
            name="search_fashion",
            enabled=True,
            interval_minutes=60,
            keywords=["moda feminina", "tendência 2025", "fashion viral"],
            limit=30,
            priority=2,
        ),
        ScraperJobConfig(
            name="search_beauty",
            enabled=True,
            interval_minutes=60,
            keywords=["maquiagem", "skincare", "beleza viral"],
            limit=30,
            priority=2,
        ),
        ScraperJobConfig(
            name="search_tech",
            enabled=True,
            interval_minutes=90,
            keywords=["gadgets", "tech viral", "eletrônicos tiktok"],
            limit=30,
            priority=3,
        ),
        ScraperJobConfig(
            name="search_home",
            enabled=True,
            interval_minutes=120,
            keywords=["decoração", "organização casa", "achados casa"],
            limit=20,
            priority=3,
        ),
    ]
    
    def __init__(self):
        self.running = False
        self.scraper: Optional[TikTokAPIScraper] = None
        self.cache = get_product_cache()
        self.jobs: Dict[str, ScraperJobConfig] = {}
        self._results: List[ScraperJobResult] = []
        self._shutdown_event = asyncio.Event()
        
        # Initialize default jobs
        for job in self.DEFAULT_JOBS:
            self.jobs[job.name] = job
    
    async def _get_redis(self):
        """Get Redis connection"""
        return await get_redis()
    
    async def _get_scraper(self) -> TikTokAPIScraper:
        """Get or create scraper instance"""
        if self.scraper is None:
            self.scraper = get_api_scraper()
        return self.scraper
    
    async def start(self):
        """Start the worker"""
        print(f"[{datetime.now()}] TikTok Scraping Worker starting...")
        
        self.running = True
        
        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.stop())
            )
        
        # Load state from Redis
        await self._load_state()
        
        # Initial status
        await self._update_status("running")
        
        # Main loop
        while self.running:
            try:
                await self._run_tick()
            except Exception as e:
                print(f"[Worker] Error in tick: {e}")
                await self._log_error(str(e))
            
            # Wait for next tick or shutdown
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=60.0  # Check every minute
                )
                break  # Shutdown requested
            except asyncio.TimeoutError:
                pass  # Continue loop
        
        await self._cleanup()
        print(f"[{datetime.now()}] Worker stopped")
    
    async def stop(self):
        """Stop the worker gracefully"""
        print("[Worker] Shutdown requested...")
        self.running = False
        self._shutdown_event.set()
        await self._update_status("stopping")
    
    async def _cleanup(self):
        """Cleanup resources"""
        await self._update_status("stopped")
        await self._save_state()
    
    async def _run_tick(self):
        """Execute one tick of the worker"""
        redis = await self._get_redis()
        now = datetime.now(timezone.utc)
        
        # Sort jobs by priority
        sorted_jobs = sorted(
            self.jobs.values(),
            key=lambda j: j.priority
        )
        
        for job in sorted_jobs:
            if not job.enabled:
                continue
            
            # Check if job should run
            last_run_key = f"{self.REDIS_PREFIX}last_run:{job.name}"
            last_run_str = await redis.get(last_run_key)
            
            should_run = False
            if last_run_str is None:
                should_run = True
            else:
                try:
                    last_run = datetime.fromisoformat(last_run_str)
                    elapsed = (now - last_run).total_seconds() / 60
                    should_run = elapsed >= job.interval_minutes
                except ValueError:
                    should_run = True
            
            if should_run:
                result = await self._execute_job(job)
                self._results.append(result)
                
                # Update last run time
                await redis.set(last_run_key, now.isoformat())
                
                # Save result to Redis
                await self._save_result(result)
                
                # Rate limiting between jobs
                await asyncio.sleep(5)
    
    async def _execute_job(self, job: ScraperJobConfig) -> ScraperJobResult:
        """Execute a single scraping job"""
        print(f"[Worker] Executing job: {job.name}")
        start_time = datetime.now(timezone.utc)
        
        try:
            scraper = await self._get_scraper()
            products = []
            
            if job.name == "trending":
                # Trending products
                products = await scraper.get_trending_products(limit=job.limit)
                
                # Cache as trending
                if products:
                    await self.cache.set_trending(products)
                    
            elif job.keywords:
                # Keyword-based search
                for keyword in job.keywords:
                    try:
                        results = await scraper.search_products(
                            keyword,
                            limit=job.limit // len(job.keywords)
                        )
                        products.extend(results)
                        
                        # Cache search results
                        if results:
                            await self.cache.set_search_results(
                                keyword, results
                            )
                        
                        await asyncio.sleep(2)  # Rate limit
                        
                    except Exception as e:
                        print(f"[Worker] Search error for '{keyword}': {e}")
            
            # Cache individual products
            cached = 0
            if products:
                cached = await self.cache.set_products_batch(products)
            
            duration = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()
            
            result = ScraperJobResult(
                job_name=job.name,
                success=True,
                products_found=len(products),
                products_cached=cached,
                duration_seconds=duration,
            )
            
            print(
                f"[Worker] Job {job.name} completed: "
                f"{len(products)} products, {cached} cached"
            )
            
            return result
            
        except Exception as e:
            duration = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()
            
            print(f"[Worker] Job {job.name} failed: {e}")
            
            return ScraperJobResult(
                job_name=job.name,
                success=False,
                products_found=0,
                products_cached=0,
                duration_seconds=duration,
                error=str(e),
            )
    
    async def _load_state(self):
        """Load worker state from Redis"""
        redis = await self._get_redis()
        
        # Load job configurations
        jobs_data = await redis.get(f"{self.REDIS_PREFIX}jobs")
        if jobs_data:
            try:
                jobs_list = json.loads(jobs_data)
                for job_dict in jobs_list:
                    name = job_dict.get("name")
                    if name:
                        self.jobs[name] = ScraperJobConfig(**job_dict)
            except Exception as e:
                print(f"[Worker] Error loading jobs: {e}")
        
        print(f"[Worker] Loaded {len(self.jobs)} jobs")
    
    async def _save_state(self):
        """Save worker state to Redis"""
        redis = await self._get_redis()
        
        # Save job configurations
        jobs_data = [job.to_dict() for job in self.jobs.values()]
        await redis.set(
            f"{self.REDIS_PREFIX}jobs",
            json.dumps(jobs_data)
        )
    
    async def _save_result(self, result: ScraperJobResult):
        """Save job result to Redis"""
        redis = await self._get_redis()
        
        # Save latest result for this job
        key = f"{self.REDIS_PREFIX}result:{result.job_name}"
        await redis.set(key, json.dumps(asdict(result)), ex=86400)
        
        # Add to results list (keep last 100)
        list_key = f"{self.REDIS_PREFIX}results"
        await redis.lpush(list_key, json.dumps(asdict(result)))
        await redis.ltrim(list_key, 0, 99)
    
    async def _update_status(self, status: str):
        """Update worker status in Redis"""
        redis = await self._get_redis()
        
        status_data = {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "jobs_count": len(self.jobs),
            "enabled_jobs": sum(1 for j in self.jobs.values() if j.enabled),
        }
        
        await redis.set(
            f"{self.REDIS_PREFIX}status",
            json.dumps(status_data)
        )
    
    async def _log_error(self, error: str):
        """Log error to Redis"""
        redis = await self._get_redis()
        
        error_data = {
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        await redis.lpush(
            f"{self.REDIS_PREFIX}errors",
            json.dumps(error_data)
        )
        await redis.ltrim(f"{self.REDIS_PREFIX}errors", 0, 49)
    
    # ============ Management Methods ============
    
    async def add_job(self, job: ScraperJobConfig) -> bool:
        """Add a new scraping job"""
        self.jobs[job.name] = job
        await self._save_state()
        print(f"[Worker] Added job: {job.name}")
        return True
    
    async def remove_job(self, name: str) -> bool:
        """Remove a scraping job"""
        if name in self.jobs:
            del self.jobs[name]
            await self._save_state()
            print(f"[Worker] Removed job: {name}")
            return True
        return False
    
    async def enable_job(self, name: str) -> bool:
        """Enable a job"""
        if name in self.jobs:
            self.jobs[name].enabled = True
            await self._save_state()
            return True
        return False
    
    async def disable_job(self, name: str) -> bool:
        """Disable a job"""
        if name in self.jobs:
            self.jobs[name].enabled = False
            await self._save_state()
            return True
        return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get worker status and metrics"""
        redis = await self._get_redis()
        
        # Get status
        status_data = await redis.get(f"{self.REDIS_PREFIX}status")
        status = json.loads(status_data) if status_data else {}
        
        # Get recent results
        results_data = await redis.lrange(f"{self.REDIS_PREFIX}results", 0, 9)
        recent_results = [
            json.loads(r) for r in results_data
        ] if results_data else []
        
        # Get cache stats
        cache_info = await self.cache.get_cache_info()
        
        # Get scraper stats
        scraper = await self._get_scraper()
        scraper_stats = scraper.get_stats()
        
        return {
            "worker": status,
            "jobs": [job.to_dict() for job in self.jobs.values()],
            "recent_results": recent_results,
            "cache": cache_info,
            "scraper": scraper_stats,
        }
    
    async def force_run(self, job_name: str) -> Optional[ScraperJobResult]:
        """Force immediate execution of a job"""
        if job_name not in self.jobs:
            return None
        
        job = self.jobs[job_name]
        result = await self._execute_job(job)
        
        # Update last run
        redis = await self._get_redis()
        await redis.set(
            f"{self.REDIS_PREFIX}last_run:{job_name}",
            datetime.now(timezone.utc).isoformat()
        )
        
        await self._save_result(result)
        return result


# ============ Singleton and Runner ============

_worker_instance: Optional[TikTokScrapingWorker] = None


def get_scraping_worker() -> TikTokScrapingWorker:
    """Get the singleton worker instance"""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = TikTokScrapingWorker()
    return _worker_instance


async def run_worker():
    """Main entry point for running the worker"""
    worker = get_scraping_worker()
    await worker.start()


if __name__ == "__main__":
    print("Starting TikTok Scraping Worker...")
    asyncio.run(run_worker())
