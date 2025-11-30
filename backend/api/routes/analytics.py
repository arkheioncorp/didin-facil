"""
Analytics Routes
Engagement metrics and platform statistics
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from enum import Enum

from api.middleware.auth import get_current_user
from shared.redis import redis_client

router = APIRouter()


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    ALL = "all"


class TimeRange(str, Enum):
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"


class EngagementMetrics(BaseModel):
    """Engagement metrics for a platform"""
    platform: str
    posts_count: int = 0
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    engagement_rate: float = 0.0
    reach: int = 0
    impressions: int = 0


class DailyStats(BaseModel):
    """Daily statistics"""
    date: str
    posts: int = 0
    engagement: int = 0
    views: int = 0


class TopContent(BaseModel):
    """Top performing content"""
    id: str
    platform: str
    caption: str
    thumbnail_url: Optional[str] = None
    views: int = 0
    likes: int = 0
    engagement_rate: float = 0.0
    posted_at: datetime


class AnalyticsOverview(BaseModel):
    """Complete analytics overview"""
    period: str
    total_posts: int
    total_views: int
    total_engagement: int
    avg_engagement_rate: float
    platforms: List[EngagementMetrics]
    daily_stats: List[DailyStats]
    top_content: List[TopContent]
    growth: Dict[str, float]


class AnalyticsService:
    """Service for analytics data"""
    
    METRICS_PREFIX = "analytics:"
    
    async def record_post(
        self,
        user_id: str,
        platform: str,
        post_id: str,
        metrics: Dict
    ):
        """Record post metrics"""
        key = f"{self.METRICS_PREFIX}posts:{user_id}:{platform}:{post_id}"
        data = {
            "platform": platform,
            "post_id": post_id,
            "views": metrics.get("views", 0),
            "likes": metrics.get("likes", 0),
            "comments": metrics.get("comments", 0),
            "shares": metrics.get("shares", 0),
            "saves": metrics.get("saves", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        await redis_client.hset(key, mapping=data)
        await redis_client.expire(key, 60 * 60 * 24 * 90)  # 90 days
        
        # Update daily counter
        today = datetime.utcnow().strftime("%Y-%m-%d")
        daily_key = f"{self.METRICS_PREFIX}daily:{user_id}:{today}"
        await redis_client.hincrby(daily_key, "posts", 1)
        await redis_client.hincrby(daily_key, "views", metrics.get("views", 0))
        await redis_client.hincrby(daily_key, "engagement", 
            metrics.get("likes", 0) + metrics.get("comments", 0) + metrics.get("shares", 0))
        await redis_client.expire(daily_key, 60 * 60 * 24 * 90)
    
    async def get_overview(
        self,
        user_id: str,
        platform: Platform,
        time_range: TimeRange
    ) -> AnalyticsOverview:
        """Get analytics overview"""
        days = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}[time_range.value]
        
        # Get daily stats
        daily_stats = []
        total_posts = 0
        total_views = 0
        total_engagement = 0
        
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_key = f"{self.METRICS_PREFIX}daily:{user_id}:{date}"
            
            data = await redis_client.hgetall(daily_key)
            if data:
                posts = int(data.get("posts", 0))
                views = int(data.get("views", 0))
                engagement = int(data.get("engagement", 0))
                
                daily_stats.append(DailyStats(
                    date=date,
                    posts=posts,
                    views=views,
                    engagement=engagement
                ))
                
                total_posts += posts
                total_views += views
                total_engagement += engagement
            else:
                daily_stats.append(DailyStats(date=date))
        
        # Calculate engagement rate
        avg_engagement_rate = 0.0
        if total_views > 0:
            avg_engagement_rate = round((total_engagement / total_views) * 100, 2)
        
        # Platform breakdown
        platforms = []
        for p in [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE]:
            if platform == Platform.ALL or platform == p:
                platforms.append(await self._get_platform_metrics(user_id, p, days))
        
        # Top content (mock for now)
        top_content = await self._get_top_content(user_id, platform, days)
        
        # Growth calculation
        growth = await self._calculate_growth(user_id, days)
        
        return AnalyticsOverview(
            period=time_range.value,
            total_posts=total_posts,
            total_views=total_views,
            total_engagement=total_engagement,
            avg_engagement_rate=avg_engagement_rate,
            platforms=platforms,
            daily_stats=list(reversed(daily_stats)),
            top_content=top_content,
            growth=growth
        )
    
    async def _get_platform_metrics(
        self,
        user_id: str,
        platform: Platform,
        days: int
    ) -> EngagementMetrics:
        """Get metrics for a specific platform"""
        # Aggregate from daily stats
        total_views = 0
        total_likes = 0
        total_comments = 0
        total_shares = 0
        post_count = 0
        
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            key = f"{self.METRICS_PREFIX}platform:{user_id}:{platform.value}:{date}"
            data = await redis_client.hgetall(key)
            if data:
                total_views += int(data.get("views", 0))
                total_likes += int(data.get("likes", 0))
                total_comments += int(data.get("comments", 0))
                total_shares += int(data.get("shares", 0))
                post_count += int(data.get("posts", 0))
        
        engagement_rate = 0.0
        if total_views > 0:
            engagement_rate = round(
                ((total_likes + total_comments + total_shares) / total_views) * 100, 2
            )
        
        return EngagementMetrics(
            platform=platform.value,
            posts_count=post_count,
            views=total_views,
            likes=total_likes,
            comments=total_comments,
            shares=total_shares,
            engagement_rate=engagement_rate,
            reach=int(total_views * 0.8),  # Estimated
            impressions=int(total_views * 1.2)  # Estimated
        )
    
    async def _get_top_content(
        self,
        user_id: str,
        platform: Platform,
        days: int
    ) -> List[TopContent]:
        """Get top performing content"""
        # In production, would query from database
        # For now, return empty list
        return []
    
    async def _calculate_growth(
        self,
        user_id: str,
        days: int
    ) -> Dict[str, float]:
        """Calculate growth compared to previous period"""
        # Current period
        current_posts = 0
        current_views = 0
        current_engagement = 0
        
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            key = f"{self.METRICS_PREFIX}daily:{user_id}:{date}"
            data = await redis_client.hgetall(key)
            if data:
                current_posts += int(data.get("posts", 0))
                current_views += int(data.get("views", 0))
                current_engagement += int(data.get("engagement", 0))
        
        # Previous period
        prev_posts = 0
        prev_views = 0
        prev_engagement = 0
        
        for i in range(days, days * 2):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            key = f"{self.METRICS_PREFIX}daily:{user_id}:{date}"
            data = await redis_client.hgetall(key)
            if data:
                prev_posts += int(data.get("posts", 0))
                prev_views += int(data.get("views", 0))
                prev_engagement += int(data.get("engagement", 0))
        
        def calc_growth(current: int, previous: int) -> float:
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return round(((current - previous) / previous) * 100, 1)
        
        return {
            "posts": calc_growth(current_posts, prev_posts),
            "views": calc_growth(current_views, prev_views),
            "engagement": calc_growth(current_engagement, prev_engagement)
        }


analytics_service = AnalyticsService()


# ============= Routes =============

@router.get("/overview")
async def get_analytics_overview(
    platform: Platform = Query(Platform.ALL),
    time_range: TimeRange = Query(TimeRange.WEEK),
    current_user=Depends(get_current_user)
):
    """
    Get analytics overview with engagement metrics.
    
    - **platform**: Filter by platform (instagram, tiktok, youtube, all)
    - **time_range**: Time period (24h, 7d, 30d, 90d)
    """
    return await analytics_service.get_overview(
        str(current_user.id),
        platform,
        time_range
    )


@router.get("/platforms/{platform}")
async def get_platform_analytics(
    platform: Platform,
    time_range: TimeRange = Query(TimeRange.WEEK),
    current_user=Depends(get_current_user)
):
    """Get detailed analytics for a specific platform."""
    if platform == Platform.ALL:
        from fastapi import HTTPException
        raise HTTPException(400, "Specify a single platform")
    
    days = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}[time_range.value]
    metrics = await analytics_service._get_platform_metrics(
        str(current_user.id),
        platform,
        days
    )
    
    return {
        "platform": platform.value,
        "period": time_range.value,
        "metrics": metrics
    }


@router.get("/daily")
async def get_daily_stats(
    time_range: TimeRange = Query(TimeRange.WEEK),
    current_user=Depends(get_current_user)
):
    """Get daily statistics for charts."""
    days = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}[time_range.value]
    user_id = str(current_user.id)
    
    daily_stats = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        key = f"{analytics_service.METRICS_PREFIX}daily:{user_id}:{date}"
        
        data = await redis_client.hgetall(key)
        if data:
            daily_stats.append({
                "date": date,
                "posts": int(data.get("posts", 0)),
                "views": int(data.get("views", 0)),
                "engagement": int(data.get("engagement", 0))
            })
        else:
            daily_stats.append({
                "date": date,
                "posts": 0,
                "views": 0,
                "engagement": 0
            })
    
    return {"daily": list(reversed(daily_stats))}


@router.post("/record")
async def record_metrics(
    platform: str,
    post_id: str,
    views: int = 0,
    likes: int = 0,
    comments: int = 0,
    shares: int = 0,
    current_user=Depends(get_current_user)
):
    """Record metrics for a post (used by workers)."""
    await analytics_service.record_post(
        str(current_user.id),
        platform,
        post_id,
        {
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares
        }
    )
    
    return {"status": "recorded"}


@router.get("/growth")
async def get_growth_stats(
    time_range: TimeRange = Query(TimeRange.WEEK),
    current_user=Depends(get_current_user)
):
    """Get growth statistics compared to previous period."""
    days = {"24h": 1, "7d": 7, "30d": 30, "90d": 90}[time_range.value]
    growth = await analytics_service._calculate_growth(
        str(current_user.id),
        days
    )
    
    return {
        "period": time_range.value,
        "compared_to": f"previous {time_range.value}",
        "growth": growth
    }


@router.get("/top-posts")
async def get_top_posts(
    platform: Platform = Query(Platform.ALL),
    limit: int = Query(10, ge=1, le=50),
    current_user=Depends(get_current_user)
):
    """Get top performing posts."""
    # Would query from database in production
    return {
        "platform": platform.value,
        "posts": [],
        "message": "Connect platform to see top posts"
    }
