"""
Analytics Pipeline Worker
Collects and aggregates social media metrics
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from shared.redis import redis_client, get_redis
from modules.analytics.social_analytics import Platform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyticsPipeline:
    """Pipeline for collecting and aggregating analytics data"""

    METRICS_PREFIX = "analytics:"

    def __init__(self):
        self.platforms = [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE]

    async def run_collection(self):
        """Run the data collection pipeline"""
        logger.info("🚀 Starting analytics collection pipeline")

        try:
            # 1. Collect raw metrics (Mock for now)
            metrics = await self._collect_metrics()

            # 2. Aggregate and store
            await self._store_metrics(metrics)

            logger.info("✅ Analytics collection completed successfully")

        except Exception as e:
            logger.error(f"❌ Error in analytics pipeline: {str(e)}")
            raise

    async def _collect_metrics(self) -> Dict[str, Dict]:
        """Collect metrics from all platforms"""
        # In production, this would call external APIs
        # For now, generate realistic mock data

        data = {}
        for platform in self.platforms:
            data[platform.value] = {
                "posts": random.randint(1, 5),
                "views": random.randint(1000, 50000),
                "likes": random.randint(100, 5000),
                "comments": random.randint(10, 500),
                "shares": random.randint(5, 200),
                "saves": random.randint(2, 100),
                "followers_gained": random.randint(5, 50),
                "followers_lost": random.randint(0, 10),
            }

        return data

    async def _store_metrics(self, metrics: Dict[str, Dict]):
        """Store aggregated metrics in Redis"""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # We need a user_id context. For the worker, we might iterate over all active users
        # For this implementation, we'll update a "global" or "demo" user
        # In a real scenario, we'd fetch active users from DB
        demo_user_id = "user_123"

        # Get the actual redis client from the manager
        redis = await get_redis()

        for platform, data in metrics.items():
            # Store daily platform stats
            key = f"{self.METRICS_PREFIX}platform:{demo_user_id}:{platform}:{today}"

            # Use hincrby to accumulate if running multiple times per day
            await redis.hincrby(key, "posts", data["posts"])
            await redis.hincrby(key, "views", data["views"])
            await redis.hincrby(key, "likes", data["likes"])
            await redis.hincrby(key, "comments", data["comments"])
            await redis.hincrby(key, "shares", data["shares"])

            # Update global daily stats
            daily_key = f"{self.METRICS_PREFIX}daily:{demo_user_id}:{today}"
            await redis.hincrby(daily_key, "posts", data["posts"])
            await redis.hincrby(daily_key, "views", data["views"])
            await redis.hincrby(
                daily_key,
                "engagement",
                data["likes"] + data["comments"] + data["shares"],
            )

            # Set expiry
            await redis.expire(key, 60 * 60 * 24 * 90)  # 90 days
            await redis.expire(daily_key, 60 * 60 * 24 * 90)


async def main():
    pipeline = AnalyticsPipeline()
    await pipeline.run_collection()


if __name__ == "__main__":
    asyncio.run(main())
