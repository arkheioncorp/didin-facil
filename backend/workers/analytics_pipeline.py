import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from api.database.connection import database
from modules.analytics.social_analytics import Platform
from shared.redis import get_redis, redis_client

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
            # 1. Fetch active users
            users = await self._get_active_users()
            logger.info(f"👥 Found {len(users)} active users")

            for user_id in users:
                # 2. Collect raw metrics (Mock for now)
                metrics = await self._collect_metrics()

                # 3. Aggregate and store for this user
                await self._store_metrics(user_id, metrics)

            logger.info("✅ Analytics collection completed successfully")

        except Exception as e:
            logger.error(f"❌ Error in analytics pipeline: {str(e)}")
            raise

    async def _get_active_users(self) -> List[str]:
        """Fetch all active user IDs from database"""
        try:
            query = "SELECT id FROM users WHERE is_active = true"
            rows = await database.fetch_all(query)
            return [str(row["id"]) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []

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

    async def _store_metrics(self, user_id: str, metrics: Dict[str, Dict]):
        """Store aggregated metrics in Redis"""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # Get the actual redis client from the manager
        redis = await get_redis()

        for platform, data in metrics.items():
            # Store daily platform stats
            key = f"{self.METRICS_PREFIX}platform:{user_id}:{platform}:{today}"

            # Use hincrby to accumulate if running multiple times per day
            await redis.hincrby(key, "posts", data["posts"])
            await redis.hincrby(key, "views", data["views"])
            await redis.hincrby(key, "likes", data["likes"])
            await redis.hincrby(key, "comments", data["comments"])
            await redis.hincrby(key, "shares", data["shares"])

            # Update global daily stats
            daily_key = f"{self.METRICS_PREFIX}daily:{user_id}:{today}"
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
            
            # Also populate "current" followers count for the dashboard to show something
            followers_key = f"followers:{user_id}:{platform}"
            # Random base followers + growth
            base_followers = random.randint(1000, 50000)
            await redis.set(f"{followers_key}:current", base_followers)
            
            # Populate history for trend chart (last 30 days)
            for i in range(30):
                date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
                hist_data = {
                    "total": base_followers - (i * random.randint(5, 20)),
                    "gained": random.randint(10, 50),
                    "lost": random.randint(0, 5)
                }
                import json
                await redis.set(f"{followers_key}:daily:{date}", json.dumps(hist_data))


async def main():
    # Connect to DB
    await database.connect()
    try:
        pipeline = AnalyticsPipeline()
        await pipeline.run_collection()
    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
