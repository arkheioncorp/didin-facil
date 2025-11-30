"""
Analytics Routes
Engagement metrics and platform statistics
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from api.middleware.auth import get_current_user
from modules.analytics.social_analytics import (
    SocialAnalyticsService,
    MetricPeriod,
    Platform as SocialPlatform,
)

router = APIRouter()
analytics_service = SocialAnalyticsService()

# ============================================
# FRONTEND DATA MODELS
# ============================================


class Period(BaseModel):
    start: str
    end: str
    days: int


class PlatformMetrics(BaseModel):
    platform: str
    followers: int
    followers_change: float
    posts: int
    engagement_rate: float
    impressions: int
    reach: int


class EngagementStats(BaseModel):
    total_likes: int
    total_comments: int
    total_shares: int
    total_saves: int
    avg_engagement_rate: float
    best_performing_day: str
    best_performing_time: str


class ContentPerformance(BaseModel):
    id: str
    title: str
    platform: str
    type: str
    likes: int
    comments: int
    shares: int
    views: int
    engagement_rate: float
    posted_at: str


class Demographics(BaseModel):
    age_groups: Dict[str, int]
    gender: Dict[str, int]
    top_locations: Dict[str, int]


class AudienceInsights(BaseModel):
    total_audience: int
    growth_rate: float
    demographics: Demographics
    active_hours: List[int]


class AnalyticsOverview(BaseModel):
    period: Period
    platforms: List[PlatformMetrics]
    engagement: EngagementStats
    top_content: List[ContentPerformance]
    audience: AudienceInsights


# ============================================
# ROUTES
# ============================================


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    period: str = Query("30d", description="Time period (7d, 30d, 90d)"),
    platform: str = Query("all", description="Filter by platform"),
    current_user=Depends(get_current_user),
):
    """
    Get analytics overview matching the frontend interface.
    Aggregates data from SocialAnalyticsService.
    """
    # Map frontend period to MetricPeriod
    period_map = {
        "7d": MetricPeriod.LAST_7_DAYS,
        "30d": MetricPeriod.LAST_30_DAYS,
        "90d": MetricPeriod.LAST_90_DAYS,
    }

    metric_period = period_map.get(period, MetricPeriod.LAST_30_DAYS)
    days = int(period.replace("d", "")) if period.endswith("d") else 30

    # Get data from service
    dashboard_data = await analytics_service.get_dashboard_overview(
        str(current_user.id), metric_period
    )

    # Transform Platforms Data
    platforms_metrics = []
    for p_name, p_data in dashboard_data.by_platform.items():
        if platform != "all" and platform != p_name:
            continue

        platforms_metrics.append(
            PlatformMetrics(
                platform=p_name,
                followers=p_data.followers_end,
                followers_change=round(p_data.followers_growth_rate, 1),
                posts=p_data.total_posts,
                engagement_rate=round(p_data.avg_engagement_rate, 1),
                impressions=p_data.total_impressions,
                reach=p_data.total_reach,
            )
        )

    # Transform Engagement Stats
    # Calculate aggregates
    total_likes = sum(p.total_likes for p in dashboard_data.by_platform.values())
    total_comments = sum(p.total_comments for p in dashboard_data.by_platform.values())
    total_shares = sum(p.total_shares for p in dashboard_data.by_platform.values())
    # Saves not currently in PlatformAnalytics, using estimate or 0
    total_saves = sum(
        int(p.total_likes * 0.1) for p in dashboard_data.by_platform.values()
    )

    # Calculate average engagement rate across all platforms
    total_views = sum(p.total_views for p in dashboard_data.by_platform.values())
    total_eng = total_likes + total_comments + total_shares + total_saves
    avg_eng_rate = round((total_eng / total_views * 100), 2) if total_views > 0 else 0.0

    # Determine best time
    best_day = "Wednesday"
    best_time = "18:00"
    if dashboard_data.best_times:
        # Simple logic to pick first one for now
        best_day = list(dashboard_data.best_times.keys())[0]
        if dashboard_data.best_times[best_day]:
            best_time = f"{dashboard_data.best_times[best_day][0]}:00"

    engagement_stats = EngagementStats(
        total_likes=total_likes,
        total_comments=total_comments,
        total_shares=total_shares,
        total_saves=total_saves,
        avg_engagement_rate=avg_eng_rate,
        best_performing_day=best_day,
        best_performing_time=best_time,
    )

    # Transform Top Content
    top_content = []
    for post in dashboard_data.top_posts:
        top_content.append(
            ContentPerformance(
                id=post.post_id,
                title=(
                    post.caption[:50] + "..."
                    if len(post.caption) > 50
                    else post.caption
                ),
                platform=post.platform.value,
                type=post.content_type,
                likes=post.metrics.likes,
                comments=post.metrics.comments,
                shares=post.metrics.shares,
                views=post.metrics.views,
                engagement_rate=round(post.metrics.engagement_rate, 1),
                posted_at=post.published_at.isoformat(),
            )
        )

    # Transform Audience Insights
    # Mock demographics data as it's not in DashboardOverview yet
    audience_insights = AudienceInsights(
        total_audience=dashboard_data.total_followers,
        growth_rate=2.5,  # Mock growth rate
        demographics=Demographics(
            age_groups={"18-24": 30, "25-34": 45, "35-44": 15, "45+": 10},
            gender={"female": 55, "male": 45},
            top_locations={
                "São Paulo": 35,
                "Rio de Janeiro": 20,
                "Belo Horizonte": 10,
                "Outros": 35,
            },
        ),
        active_hours=[
            0,
            1,
            2,
            5,
            10,
            25,
            40,
            55,
            65,
            75,
            85,
            90,
            95,
            85,
            70,
            60,
            50,
            45,
            40,
            35,
            25,
            15,
            10,
            5,
        ],  # Mock activity curve
    )

    return AnalyticsOverview(
        period=Period(
            start=dashboard_data.start_date.isoformat(),
            end=dashboard_data.end_date.isoformat(),
            days=days,
        ),
        platforms=platforms_metrics,
        engagement=engagement_stats,
        top_content=top_content,
        audience=audience_insights,
    )


@router.get("/export")
async def export_analytics(
    format: str = "csv", period: str = "30d", current_user=Depends(get_current_user)
):
    """Export analytics report"""
    # Map frontend period to MetricPeriod
    period_map = {
        "7d": MetricPeriod.LAST_7_DAYS,
        "30d": MetricPeriod.LAST_30_DAYS,
        "90d": MetricPeriod.LAST_90_DAYS,
    }
    metric_period = period_map.get(period, MetricPeriod.LAST_30_DAYS)

    from fastapi import Response

    data = await analytics_service.export_report(
        str(current_user.id), metric_period, format
    )

    content_type = "application/json" if format == "json" else "text/csv"
    filename = f"analytics_report_{period}.{format}"

    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


class WebhookPayload(BaseModel):
    platform: str
    post_id: str
    metrics: Dict[str, Any]
    timestamp: Optional[str] = None


@router.post("/webhook")
async def analytics_webhook(
    payload: WebhookPayload, current_user=Depends(get_current_user)
):
    """
    Receive analytics data from N8N or other external sources.
    """
    # Validate platform
    try:
        platform_enum = SocialPlatform(payload.platform.lower())
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid platform: {payload.platform}"
        )

    # Record metrics via service
    await analytics_service.record_post(
        user_id=str(current_user.id),
        platform=platform_enum,
        post_id=payload.post_id,
        metrics=payload.metrics,
    )

    return {"status": "success", "message": "Metrics recorded"}
