"""
Job Scheduler
Cron jobs for automated tasks
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from shared.redis import get_redis


class Job:
    """Represents a scheduled job"""
    
    def __init__(
        self,
        name: str,
        handler: Callable,
        interval_minutes: int = 60,
        cron_expression: Optional[str] = None,
        enabled: bool = True,
        retry_on_failure: bool = True,
        max_retries: int = 3,
    ):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.handler = handler
        self.interval_minutes = interval_minutes
        self.cron_expression = cron_expression
        self.enabled = enabled
        self.retry_on_failure = retry_on_failure
        self.max_retries = max_retries
        
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0
        self.failure_count = 0
        self.consecutive_failures = 0
    
    def should_run(self) -> bool:
        """Check if job should run now"""
        if not self.enabled:
            return False
        
        if self.next_run is None:
            return True
        
        return datetime.utcnow() >= self.next_run
    
    def schedule_next(self):
        """Calculate next run time"""
        now = datetime.utcnow()
        
        if self.cron_expression:
            self.next_run = self._parse_cron(self.cron_expression, now)
        else:
            self.next_run = now + timedelta(minutes=self.interval_minutes)
    
    def _parse_cron(self, expr: str, after: datetime) -> datetime:
        """Simple cron expression parser"""
        # Basic implementation - supports: minute hour day month weekday
        parts = expr.split()
        
        if len(parts) != 5:
            return after + timedelta(minutes=self.interval_minutes)
        
        minute, hour, day, month, weekday = parts
        
        # Simple case: specific minute and hour
        if minute.isdigit() and hour.isdigit():
            target = after.replace(
                hour=int(hour),
                minute=int(minute),
                second=0,
                microsecond=0
            )
            
            if target <= after:
                target += timedelta(days=1)
            
            return target
        
        # Default: use interval
        return after + timedelta(minutes=self.interval_minutes)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "interval_minutes": self.interval_minutes,
            "cron_expression": self.cron_expression,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
        }


class Scheduler:
    """Job scheduler for background tasks"""
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.running = False
        self._lock = asyncio.Lock()
    
    def add_job(self, job: Job):
        """Add a job to the scheduler"""
        self.jobs[job.name] = job
        job.schedule_next()
        print(f"[Scheduler] Added job: {job.name}")
    
    def remove_job(self, name: str):
        """Remove a job from the scheduler"""
        if name in self.jobs:
            del self.jobs[name]
            print(f"[Scheduler] Removed job: {name}")
    
    def enable_job(self, name: str):
        """Enable a job"""
        if name in self.jobs:
            self.jobs[name].enabled = True
    
    def disable_job(self, name: str):
        """Disable a job"""
        if name in self.jobs:
            self.jobs[name].enabled = False
    
    async def start(self):
        """Start the scheduler"""
        print(f"[{datetime.now()}] Scheduler starting...")
        self.running = True
        
        while self.running:
            try:
                await self._tick()
            except Exception as e:
                print(f"[Scheduler] Error in tick: {e}")
            
            await asyncio.sleep(10)  # Check every 10 seconds
        
        print(f"[{datetime.now()}] Scheduler stopped")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
    
    async def _tick(self):
        """Process one scheduler tick"""
        async with self._lock:
            for job in self.jobs.values():
                if job.should_run():
                    await self._run_job(job)
    
    async def _run_job(self, job: Job):
        """Execute a job"""
        job_start = datetime.utcnow()
        print(f"[Scheduler] Running job: {job.name}")
        
        try:
            # Run the job handler
            if asyncio.iscoroutinefunction(job.handler):
                await job.handler()
            else:
                job.handler()
            
            # Success
            job.run_count += 1
            job.consecutive_failures = 0
            job.last_run = job_start
            job.schedule_next()
            
            duration = (datetime.utcnow() - job_start).total_seconds()
            print(f"[Scheduler] Job {job.name} completed in {duration:.2f}s")
            
            # Store result in Redis
            await self._store_job_result(job, "success", duration)
            
        except Exception as e:
            job.failure_count += 1
            job.consecutive_failures += 1
            
            print(f"[Scheduler] Job {job.name} failed: {e}")
            
            # Store failure in Redis
            await self._store_job_result(job, "failed", 0, str(e))
            
            # Retry logic
            if job.retry_on_failure and job.consecutive_failures < job.max_retries:
                # Retry with backoff
                backoff = min(60, 5 * (2 ** job.consecutive_failures))
                job.next_run = datetime.utcnow() + timedelta(seconds=backoff)
                print(f"[Scheduler] Will retry {job.name} in {backoff}s")
            else:
                job.schedule_next()
    
    async def _store_job_result(
        self,
        job: Job,
        status: str,
        duration: float,
        error: str = None
    ):
        """Store job result in Redis"""
        try:
            redis = await get_redis()
            
            result = {
                "job_id": job.id,
                "job_name": job.name,
                "status": status,
                "duration": duration,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Store in list (keep last 100)
            key = f"scheduler:results:{job.name}"
            await redis.lpush(key, json.dumps(result))
            await redis.ltrim(key, 0, 99)
            
            # Update job status
            await redis.hset(
                "scheduler:jobs",
                job.name,
                json.dumps(job.to_dict())
            )
            
        except Exception as e:
            print(f"[Scheduler] Error storing result: {e}")
    
    async def run_job_now(self, name: str):
        """Manually trigger a job"""
        if name not in self.jobs:
            raise ValueError(f"Job not found: {name}")
        
        job = self.jobs[name]
        await self._run_job(job)
    
    def get_job_status(self) -> List[dict]:
        """Get status of all jobs"""
        return [job.to_dict() for job in self.jobs.values()]


# Pre-defined jobs
async def refresh_products_job():
    """Refresh product database from scrapers"""
    redis = await get_redis()
    
    job_data = {
        "id": str(uuid.uuid4()),
        "type": "refresh_products",
        "limit": 500,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    await redis.lpush("scraper:jobs", json.dumps(job_data))
    print(f"[Job] Queued refresh_products job: {job_data['id']}")


async def refresh_trending_job():
    """Refresh trending products"""
    redis = await get_redis()
    
    job_data = {
        "id": str(uuid.uuid4()),
        "type": "scrape_trending",
        "limit": 100,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    await redis.lpush("scraper:jobs", json.dumps(job_data))
    print(f"[Job] Queued scrape_trending job: {job_data['id']}")


async def cleanup_old_products_job():
    """Remove old/stale products from database"""
    from shared.postgres import get_db
    
    async with get_db() as db:
        # Remove products not updated in 30 days
        result = await db.execute(
            """
            DELETE FROM products
            WHERE updated_at < NOW() - INTERVAL '30 days'
            RETURNING id
            """
        )
        
        deleted = len(result) if result else 0
        print(f"[Job] Cleaned up {deleted} old products")


async def cleanup_expired_cache_job():
    """
    Cleanup expired cache entries.
    Note: Quotas are deprecated - using credits system now.
    """
    redis = await get_redis()

    # Cleanup old rate limit keys
    cursor = 0
    cleanup_count = 0

    while True:
        cursor, keys = await redis.scan(cursor, match="ratelimit:*")

        for key in keys:
            ttl = await redis.ttl(key)
            if ttl == -1:  # No expiry set, delete old keys
                await redis.delete(key)
                cleanup_count += 1

        if cursor == 0:
            break

    print(f"[Job] Cleaned up {cleanup_count} expired cache entries")


async def check_license_expiry_job():
    """Check and handle expired licenses"""
    from shared.postgres import get_db
    
    async with get_db() as db:
        # Find expired licenses
        expired = await db.fetch_all(
            """
            SELECT id, user_id, plan
            FROM licenses
            WHERE status = 'active'
            AND expires_at < NOW()
            """
        )
        
        for license in expired:
            # Update status
            await db.execute(
                """
                UPDATE licenses
                SET status = 'expired', updated_at = NOW()
                WHERE id = :id
                """,
                {"id": license["id"]}
            )
            
            # TODO: Send notification email
        
        print(f"[Job] Processed {len(expired)} expired licenses")


def create_default_scheduler() -> Scheduler:
    """Create scheduler with default jobs"""
    scheduler = Scheduler()
    
    # Add default jobs
    scheduler.add_job(Job(
        name="refresh_products",
        handler=refresh_products_job,
        interval_minutes=60,  # Every hour
    ))
    
    scheduler.add_job(Job(
        name="refresh_trending",
        handler=refresh_trending_job,
        interval_minutes=30,  # Every 30 minutes
    ))
    
    scheduler.add_job(Job(
        name="cleanup_old_products",
        handler=cleanup_old_products_job,
        cron_expression="0 3 * * *",  # Daily at 3 AM
        interval_minutes=1440,  # 24 hours fallback
    ))
    
    scheduler.add_job(Job(
        name="cleanup_expired_cache",
        handler=cleanup_expired_cache_job,
        cron_expression="0 4 * * *",  # Daily at 4 AM
        interval_minutes=1440,
    ))
    
    scheduler.add_job(Job(
        name="check_license_expiry",
        handler=check_license_expiry_job,
        interval_minutes=60,  # Every hour
    ))
    
    return scheduler


async def main():
    """Entry point for scheduler worker"""
    scheduler = create_default_scheduler()
    await scheduler.start()


if __name__ == "__main__":
    asyncio.run(main())
