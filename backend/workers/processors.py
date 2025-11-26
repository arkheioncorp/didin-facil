"""
Job Processors
Process various background jobs
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Optional

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])
from shared.redis import get_redis
from shared.postgres import get_db


class JobProcessor:
    """Base class for job processors"""
    
    def __init__(self, name: str, queue_name: str):
        self.name = name
        self.queue_name = queue_name
        self.running = False
        self.current_job = None
    
    async def start(self):
        """Start processing jobs"""
        print(f"[{self.name}] Starting processor...")
        self.running = True
        
        while self.running:
            try:
                job = await self._get_next_job()
                
                if job:
                    await self._process_job(job)
                else:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"[{self.name}] Error: {e}")
                await asyncio.sleep(5)
    
    def stop(self):
        """Stop processing"""
        self.running = False
    
    async def _get_next_job(self) -> Optional[dict]:
        """Get next job from queue"""
        redis = await get_redis()
        
        result = await redis.brpop(self.queue_name, timeout=5)
        
        if result:
            _, job_data = result
            return json.loads(job_data)
        
        return None
    
    async def _process_job(self, job: dict):
        """Process a job - override in subclass"""
        raise NotImplementedError
    
    async def _update_job_status(
        self,
        job_id: str,
        status: str,
        result: Any = None,
        error: str = None,
    ):
        """Update job status in Redis"""
        redis = await get_redis()
        
        update = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        if result is not None:
            update["result"] = json.dumps(result)
        
        if error:
            update["error"] = error
        
        await redis.hset(f"job:{job_id}", mapping=update)


class CopyGenerationProcessor(JobProcessor):
    """Process copy generation jobs"""
    
    def __init__(self):
        super().__init__("CopyProcessor", "copy:jobs")
    
    async def _process_job(self, job: dict):
        """Generate marketing copy"""
        from api.services.openai import OpenAIService
        
        job_id = job.get("id")
        user_id = job.get("user_id")
        product_id = job.get("product_id")
        
        print(f"[CopyProcessor] Processing job {job_id}")
        
        await self._update_job_status(job_id, "processing")
        
        try:
            # Get product data
            async with get_db() as db:
                product = await db.fetch_one(
                    "SELECT * FROM products WHERE id = :id",
                    {"id": product_id}
                )
            
            if not product:
                raise ValueError(f"Product not found: {product_id}")
            
            # Generate copy
            openai_service = OpenAIService()
            
            copy_result = await openai_service.generate_copy(
                product=dict(product),
                platform=job.get("platform", "tiktok"),
                tone=job.get("tone", "engaging"),
                include_emojis=job.get("include_emojis", True),
                include_hashtags=job.get("include_hashtags", True),
            )
            
            # Save to database
            copy_id = str(uuid.uuid4())
            async with get_db() as db:
                await db.execute(
                    """
                    INSERT INTO copy_history (
                        id, user_id, product_id, platform, tone,
                        copy_text, metadata, created_at
                    ) VALUES (
                        :id, :user_id, :product_id, :platform, :tone,
                        :copy_text, :metadata, NOW()
                    )
                    """,
                    {
                        "id": copy_id,
                        "user_id": user_id,
                        "product_id": product_id,
                        "platform": job.get("platform"),
                        "tone": job.get("tone"),
                        "copy_text": copy_result["copy"],
                        "metadata": json.dumps(copy_result.get("metadata", {})),
                    }
                )
            
            await self._update_job_status(
                job_id,
                "completed",
                result={"copy_id": copy_id, **copy_result}
            )
            
            print(f"[CopyProcessor] Job {job_id} completed")
            
        except Exception as e:
            print(f"[CopyProcessor] Job {job_id} failed: {e}")
            await self._update_job_status(job_id, "failed", error=str(e))


class ImageProcessingProcessor(JobProcessor):
    """Process image download/optimization jobs"""
    
    def __init__(self):
        super().__init__("ImageProcessor", "images:jobs")
    
    async def _process_job(self, job: dict):
        """Process product images"""
        from scraper.utils.images import ImageProcessor
        
        job_id = job.get("id")
        product_id = job.get("product_id")
        image_urls = job.get("image_urls", [])
        
        print(f"[ImageProcessor] Processing job {job_id}")
        
        await self._update_job_status(job_id, "processing")
        
        try:
            processor = ImageProcessor(
                output_dir="./images",
                cdn_url=None,  # TODO: Add CDN URL from config
            )
            
            results = await processor.process_product_images(
                product_id=product_id,
                image_urls=image_urls,
                max_images=5,
            )
            
            # Update product with processed images
            successful = [r for r in results if r.get("success")]
            
            if successful:
                async with get_db() as db:
                    # Get first successful image as main
                    main_image = successful[0].get("cdn_urls", {}).get(
                        "detail",
                        successful[0].get("local_paths", {}).get("detail")
                    )
                    
                    await db.execute(
                        """
                        UPDATE products
                        SET processed_image_url = :url, updated_at = NOW()
                        WHERE id = :id
                        """,
                        {"id": product_id, "url": main_image}
                    )
            
            await self._update_job_status(
                job_id,
                "completed",
                result={"processed": len(successful), "total": len(image_urls)}
            )
            
            print(f"[ImageProcessor] Job {job_id} completed")
            
        except Exception as e:
            print(f"[ImageProcessor] Job {job_id} failed: {e}")
            await self._update_job_status(job_id, "failed", error=str(e))


class NotificationProcessor(JobProcessor):
    """Process notification jobs (email, push, etc.)"""
    
    def __init__(self):
        super().__init__("NotificationProcessor", "notifications:jobs")
    
    async def _process_job(self, job: dict):
        """Send notification"""
        job_id = job.get("id")
        notification_type = job.get("type")
        
        print(f"[NotificationProcessor] Processing {notification_type} job {job_id}")
        
        await self._update_job_status(job_id, "processing")
        
        try:
            if notification_type == "email":
                await self._send_email(job)
            elif notification_type == "push":
                await self._send_push(job)
            else:
                raise ValueError(f"Unknown notification type: {notification_type}")
            
            await self._update_job_status(job_id, "completed")
            print(f"[NotificationProcessor] Job {job_id} completed")
            
        except Exception as e:
            print(f"[NotificationProcessor] Job {job_id} failed: {e}")
            await self._update_job_status(job_id, "failed", error=str(e))
    
    async def _send_email(self, job: dict):
        """Send email notification"""
        # TODO: Implement email sending (e.g., via SendGrid, SES)
        recipient = job.get("recipient")
        subject = job.get("subject")
        job.get("body")
        
        print(f"[Email] Would send to {recipient}: {subject}")
        
        # Placeholder - implement actual email sending
        await asyncio.sleep(0.1)
    
    async def _send_push(self, job: dict):
        """Send push notification"""
        # TODO: Implement push notification
        user_id = job.get("user_id")
        title = job.get("title")
        job.get("message")
        
        print(f"[Push] Would send to user {user_id}: {title}")
        
        # Placeholder - implement actual push sending
        await asyncio.sleep(0.1)


class AnalyticsProcessor(JobProcessor):
    """Process analytics aggregation jobs"""
    
    def __init__(self):
        super().__init__("AnalyticsProcessor", "analytics:jobs")
    
    async def _process_job(self, job: dict):
        """Aggregate analytics data"""
        job_id = job.get("id")
        job_type = job.get("type")
        
        print(f"[AnalyticsProcessor] Processing {job_type} job {job_id}")
        
        await self._update_job_status(job_id, "processing")
        
        try:
            if job_type == "daily_stats":
                await self._aggregate_daily_stats()
            elif job_type == "product_trends":
                await self._calculate_product_trends()
            else:
                raise ValueError(f"Unknown analytics type: {job_type}")
            
            await self._update_job_status(job_id, "completed")
            print(f"[AnalyticsProcessor] Job {job_id} completed")
            
        except Exception as e:
            print(f"[AnalyticsProcessor] Job {job_id} failed: {e}")
            await self._update_job_status(job_id, "failed", error=str(e))
    
    async def _aggregate_daily_stats(self):
        """Aggregate daily usage statistics"""
        async with get_db() as db:
            # Count active users
            active_users = await db.fetch_one(
                """
                SELECT COUNT(DISTINCT user_id) as count
                FROM copy_history
                WHERE created_at > NOW() - INTERVAL '24 hours'
                """
            )
            
            # Count copies generated
            copies_generated = await db.fetch_one(
                """
                SELECT COUNT(*) as count
                FROM copy_history
                WHERE created_at > NOW() - INTERVAL '24 hours'
                """
            )
            
            # Count new products
            new_products = await db.fetch_one(
                """
                SELECT COUNT(*) as count
                FROM products
                WHERE collected_at > NOW() - INTERVAL '24 hours'
                """
            )
            
            # Store stats
            await db.execute(
                """
                INSERT INTO daily_stats (
                    date, active_users, copies_generated, new_products
                ) VALUES (
                    CURRENT_DATE, :active_users, :copies_generated, :new_products
                )
                ON CONFLICT (date) DO UPDATE SET
                    active_users = EXCLUDED.active_users,
                    copies_generated = EXCLUDED.copies_generated,
                    new_products = EXCLUDED.new_products
                """,
                {
                    "active_users": active_users["count"] if active_users else 0,
                    "copies_generated": copies_generated["count"] if copies_generated else 0,
                    "new_products": new_products["count"] if new_products else 0,
                }
            )
    
    async def _calculate_product_trends(self):
        """Calculate trending products"""
        async with get_db() as db:
            # Calculate trend score based on recent sales increase
            await db.execute(
                """
                UPDATE products
                SET is_trending = (
                    sales_7d > 100 AND
                    sales_7d > sales_30d / 4 * 1.5
                ),
                updated_at = NOW()
                WHERE updated_at > NOW() - INTERVAL '7 days'
                """
            )


async def run_all_processors():
    """Run all job processors"""
    processors = [
        CopyGenerationProcessor(),
        ImageProcessingProcessor(),
        NotificationProcessor(),
        AnalyticsProcessor(),
    ]
    
    print(f"[Workers] Starting {len(processors)} processors...")
    
    tasks = [asyncio.create_task(p.start()) for p in processors]
    
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        print("[Workers] Shutting down...")
        for p in processors:
            p.stop()


async def main():
    """Entry point for processors"""
    await run_all_processors()


if __name__ == "__main__":
    asyncio.run(main())
