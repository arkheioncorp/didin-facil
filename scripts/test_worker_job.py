import asyncio
import json
import uuid
from datetime import datetime, timezone
from redis.asyncio import Redis

async def push_job():
    redis = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    
    job_id = str(uuid.uuid4())
    job_data = {
        "id": job_id,
        "type": "scrape_trending",
        "limit": 10,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    print(f"Pushing job {job_id} to scraper:jobs...")
    await redis.lpush("scraper:jobs", json.dumps(job_data))
    print("Job pushed!")
    
    await redis.close()

if __name__ == "__main__":
    asyncio.run(push_job())
