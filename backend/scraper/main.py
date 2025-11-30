"""
Centralized Scraper Worker
Entry point for the scraper service
"""

import asyncio
import json
import signal
import sys
from datetime import datetime, timezone

from .config import ScraperConfig
from .tiktok.scraper import TikTokScraper
from .aliexpress.scraper import AliExpressScraper
from .utils.proxy import ProxyPool

from pathlib import Path

# Add backend directory to sys.path to allow importing shared modules
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from shared.redis import get_redis  # noqa: E402
from shared.postgres import get_db  # noqa: E402


class ScraperWorker:
    """Main scraper worker that processes jobs from queue"""
    
    MAX_JOBS_BEFORE_RESTART = 50
    
    def __init__(self):
        self.config = ScraperConfig()
        self.running = False
        self.current_job = None
        self.jobs_processed = 0
        
        # Initialize scrapers
        self.proxy_pool = ProxyPool(self.config.proxies)
        self.tiktok_scraper = TikTokScraper(self.proxy_pool, self.config)
        self.aliexpress_scraper = AliExpressScraper(self.proxy_pool, self.config)
        
        # Job queue
        self.job_queue = "scraper:jobs"
        self.results_queue = "scraper:results"
    
    async def start(self):
        """Start the worker"""
        print(f"[{datetime.now()}] Scraper worker starting...")
        
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        # Initialize scrapers
        await self._init_scrapers()
        
        print(f"[{datetime.now()}] Worker ready, waiting for jobs...")
        
        # Main loop
        while self.running:
            try:
                # Check if we need to restart browsers to prevent memory leaks
                if self.jobs_processed >= self.MAX_JOBS_BEFORE_RESTART:
                    print(f"[{datetime.now()}] Restarting browsers after {self.jobs_processed} jobs...")
                    await self._restart_scrapers()
                    self.jobs_processed = 0

                job = await self._get_next_job()
                
                if job:
                    await self._process_job(job)
                    self.jobs_processed += 1
                else:
                    # No job, wait a bit
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"[{datetime.now()}] Error in main loop: {e}")
                await asyncio.sleep(5)
        
        # Cleanup
        await self._shutdown()

    async def _init_scrapers(self):
        """Initialize scraper instances"""
        await self.tiktok_scraper.start()
        await self.aliexpress_scraper.start()

    async def _restart_scrapers(self):
        """Restart scraper instances to clear memory"""
        await self.tiktok_scraper.stop()
        await self.aliexpress_scraper.stop()
        await asyncio.sleep(2) # Give time for processes to die
        await self._init_scrapers()

    
    async def _get_next_job(self) -> dict | None:
        """Get next job from queue"""
        redis = await get_redis()
        
        # Blocking pop with timeout
        result = await redis.brpop(self.job_queue, timeout=5)
        
        if result:
            _, job_data = result
            return json.loads(job_data)
        
        return None
    
    async def _process_job(self, job: dict):
        """Process a scraping job"""
        job_id = job.get("id")
        job_type = job.get("type")
        
        print(f"[{datetime.now()}] Processing job {job_id}: {job_type}")
        
        self.current_job = job
        redis = await get_redis()
        
        # Update job status
        await redis.hset(f"job:{job_id}", "status", "running")
        await redis.hset(f"job:{job_id}", "started_at", datetime.now(timezone.utc).isoformat())
        
        try:
            products = []
            
            if job_type == "refresh_products":
                products = await self._scrape_products(job)
            elif job_type == "scrape_category":
                products = await self._scrape_category(job)
            elif job_type == "scrape_trending":
                products = await self._scrape_trending(job)
            else:
                raise ValueError(f"Unknown job type: {job_type}")
            
            # Save products to database
            saved_count = await self._save_products(products)
            
            # Update job status
            await redis.hset(f"job:{job_id}", mapping={
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "products_count": str(saved_count)
            })
            
            print(f"[{datetime.now()}] Job {job_id} completed: {saved_count} products saved")
            
        except Exception as e:
            print(f"[{datetime.now()}] Job {job_id} failed: {e}")
            
            await redis.hset(f"job:{job_id}", mapping={
                "status": "failed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            })
        
        finally:
            self.current_job = None
    
    async def _scrape_products(self, job: dict) -> list:
        """Scrape products based on job parameters"""
        category = job.get("category")
        limit = job.get("limit", 100)
        
        products = []
        
        # Try TikTok first
        try:
            products = await self.tiktok_scraper.scrape_products(
                category=category,
                limit=limit
            )
        except Exception as e:
            print(f"[{datetime.now()}] TikTok scraping failed: {e}")
            
            # Fallback to AliExpress
            if self.config.use_fallback:
                try:
                    products = await self.aliexpress_scraper.scrape_products(
                        category=category,
                        limit=limit
                    )
                except Exception as e2:
                    print(f"[{datetime.now()}] AliExpress fallback failed: {e2}")
        
        return products
    
    async def _scrape_category(self, job: dict) -> list:
        """Scrape products from a specific category"""
        category = job.get("category")
        limit = job.get("limit", 50)
        
        return await self.tiktok_scraper.scrape_category(
            category=category,
            limit=limit
        )
    
    async def _scrape_trending(self, job: dict) -> list:
        """Scrape trending products"""
        limit = job.get("limit", 50)
        
        return await self.tiktok_scraper.scrape_trending(limit=limit)
    
    async def _save_products(self, products: list) -> int:
        """Save products to database"""
        if not products:
            return 0
        
        async with get_db() as db:
            saved = 0
            
            for product in products:
                try:
                    await db.execute(
                        """
                        INSERT INTO products (
                            id, tiktok_id, title, description, price, original_price,
                            currency, category, subcategory, seller_name, seller_rating,
                            product_rating, reviews_count, sales_count, sales_7d, sales_30d,
                            commission_rate, image_url, images, video_url, product_url,
                            affiliate_url, has_free_shipping, is_trending, is_on_sale,
                            in_stock, collected_at, updated_at
                        ) VALUES (
                            :id, :tiktok_id, :title, :description, :price, :original_price,
                            :currency, :category, :subcategory, :seller_name, :seller_rating,
                            :product_rating, :reviews_count, :sales_count, :sales_7d, :sales_30d,
                            :commission_rate, :image_url, :images, :video_url, :product_url,
                            :affiliate_url, :has_free_shipping, :is_trending, :is_on_sale,
                            :in_stock, :collected_at, NOW()
                        )
                        ON CONFLICT (tiktok_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            price = EXCLUDED.price,
                            sales_count = EXCLUDED.sales_count,
                            sales_7d = EXCLUDED.sales_7d,
                            sales_30d = EXCLUDED.sales_30d,
                            is_trending = EXCLUDED.is_trending,
                            updated_at = NOW()
                        """,
                        product
                    )
                    saved += 1
                except Exception as e:
                    print(f"Error saving product: {e}")
            
            return saved
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n[{datetime.now()}] Shutdown signal received, stopping...")
        self.running = False
    
    async def _shutdown(self):
        """Cleanup on shutdown"""
        print(f"[{datetime.now()}] Shutting down scrapers...")
        
        await self.tiktok_scraper.stop()
        await self.aliexpress_scraper.stop()
        
        print(f"[{datetime.now()}] Worker stopped")


async def main():
    """Entry point"""
    worker = ScraperWorker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
