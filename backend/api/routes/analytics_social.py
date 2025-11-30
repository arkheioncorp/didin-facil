"""
Social Analytics API Routes
============================
Endpoints para analytics de redes sociais.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from api.middleware.auth import get_current_user
from modules.analytics.social_analytics import (
    SocialAnalyticsService,
    MetricPeriod,
    Platform
)

router = APIRouter()
analytics_service = SocialAnalyticsService()


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class DateRangeRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class OverviewResponse(BaseModel):
    period: str
    start_date: datetime
    end_date: datetime
    total_posts: int
    total_engagement: int
    total_reach: int
    total_followers: int


# ============================================
# DASHBOARD ENDPOINTS
# ============================================

@router.get("/overview")
async def get_dashboard_overview(
    period: str = "last_30_days",
    current_user=Depends(get_current_user)
):
    """
    Obtém overview do dashboard de analytics.
    
    Períodos disponíveis:
    - today, yesterday
    - last_7_days, last_30_days, last_90_days
    - this_month, last_month, this_year
    """
    try:
        metric_period = MetricPeriod(period)
    except ValueError:
        raise HTTPException(status_code=400, detail="Período inválido")
    
    overview = await analytics_service.get_dashboard_overview(
        str(current_user.id),
        metric_period
    )
    
    return {
        "period": overview.period.value,
        "start_date": overview.start_date.isoformat(),
        "end_date": overview.end_date.isoformat(),
        "totals": {
            "posts": overview.total_posts,
            "engagement": overview.total_engagement,
            "reach": overview.total_reach,
            "followers": overview.total_followers
        },
        "by_platform": {
            platform: {
                "posts": data.total_posts,
                "likes": data.total_likes,
                "comments": data.total_comments,
                "shares": data.total_shares,
                "reach": data.total_reach,
                "engagement_rate": data.avg_engagement_rate,
                "followers": data.followers_end,
                "followers_growth": data.followers_growth_rate
            }
            for platform, data in overview.by_platform.items()
        },
        "best_times": overview.best_times
    }


@router.get("/platform/{platform}")
async def get_platform_analytics(
    platform: str,
    period: str = "last_30_days",
    current_user=Depends(get_current_user)
):
    """
    Obtém analytics de uma plataforma específica.
    """
    try:
        metric_period = MetricPeriod(period)
        platform_enum = Platform(platform)
    except ValueError:
        raise HTTPException(status_code=400, detail="Plataforma ou período inválido")
    
    analytics = await analytics_service.get_platform_analytics(
        str(current_user.id),
        platform_enum,
        metric_period
    )
    
    return {
        "platform": analytics.platform.value,
        "period": analytics.period.value,
        "date_range": {
            "start": analytics.start_date.isoformat(),
            "end": analytics.end_date.isoformat()
        },
        "content": {
            "posts": analytics.total_posts,
            "stories": analytics.total_stories,
            "reels": analytics.total_reels
        },
        "engagement": {
            "likes": analytics.total_likes,
            "comments": analytics.total_comments,
            "shares": analytics.total_shares,
            "views": analytics.total_views,
            "reach": analytics.total_reach,
            "impressions": analytics.total_impressions,
            "engagement_rate": analytics.avg_engagement_rate
        },
        "averages": {
            "likes_per_post": analytics.avg_likes_per_post,
            "comments_per_post": analytics.avg_comments_per_post
        },
        "followers": {
            "start": analytics.followers_start,
            "end": analytics.followers_end,
            "gained": analytics.followers_gained,
            "lost": analytics.followers_lost,
            "growth_rate": analytics.followers_growth_rate
        }
    }


# ============================================
# TRENDS ENDPOINTS
# ============================================

@router.get("/trends/engagement")
async def get_engagement_trend(
    period: str = "last_30_days",
    granularity: str = "day",
    current_user=Depends(get_current_user)
):
    """
    Obtém tendência de engajamento ao longo do tempo.
    """
    try:
        metric_period = MetricPeriod(period)
    except ValueError:
        raise HTTPException(status_code=400, detail="Período inválido")
    
    trend = await analytics_service.get_engagement_trend(
        str(current_user.id),
        metric_period,
        granularity
    )
    
    return {"trend": trend, "granularity": granularity}


@router.get("/trends/followers")
async def get_followers_trend(
    period: str = "last_30_days",
    platform: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """
    Obtém tendência de crescimento de seguidores.
    """
    try:
        metric_period = MetricPeriod(period)
        platform_enum = Platform(platform) if platform else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Período ou plataforma inválido")
    
    trend = await analytics_service.get_followers_trend(
        str(current_user.id),
        metric_period,
        platform_enum
    )
    
    return {"trend": trend}


# ============================================
# BEST TIMES & TOP CONTENT
# ============================================

@router.get("/best-times")
async def get_best_posting_times(
    period: str = "last_90_days",
    platform: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """
    Obtém melhores horários para postar.
    
    Baseado em análise de engajamento histórico.
    """
    try:
        metric_period = MetricPeriod(period)
        platform_enum = Platform(platform) if platform else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Período ou plataforma inválido")
    
    best_times = await analytics_service.get_best_posting_times(
        str(current_user.id),
        metric_period,
        platform_enum
    )
    
    return {"best_times": best_times}


@router.get("/top-posts")
async def get_top_posts(
    period: str = "last_30_days",
    platform: Optional[str] = None,
    sort_by: str = "engagement",
    limit: int = 10,
    current_user=Depends(get_current_user)
):
    """
    Obtém posts com melhor performance.
    """
    try:
        metric_period = MetricPeriod(period)
        platform_enum = Platform(platform) if platform else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Período ou plataforma inválido")
    
    top_posts = await analytics_service.get_top_posts(
        str(current_user.id),
        metric_period,
        platform_enum,
        limit,
        sort_by
    )
    
    return {"posts": top_posts}


# ============================================
# COMPARISON & REPORTS
# ============================================

@router.get("/compare")
async def compare_periods(
    period1: str = "last_30_days",
    period2: str = "last_month",
    platform: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """
    Compara métricas entre dois períodos.
    """
    try:
        p1 = MetricPeriod(period1)
        p2 = MetricPeriod(period2)
        platform_enum = Platform(platform) if platform else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Período ou plataforma inválido")
    
    comparison = await analytics_service.compare_periods(
        str(current_user.id),
        p1,
        p2,
        platform_enum
    )
    
    return comparison


@router.get("/scheduler-stats")
async def get_scheduler_stats(
    period: str = "last_30_days",
    current_user=Depends(get_current_user)
):
    """
    Obtém estatísticas do agendador de posts.
    """
    try:
        metric_period = MetricPeriod(period)
    except ValueError:
        raise HTTPException(status_code=400, detail="Período inválido")
    
    stats = await analytics_service.get_scheduler_stats(
        str(current_user.id),
        metric_period
    )
    
    return {
        "period": stats.period.value,
        "totals": {
            "scheduled": stats.total_scheduled,
            "published": stats.total_published,
            "failed": stats.total_failed,
            "pending": stats.total_pending
        },
        "success_rate": stats.success_rate,
        "by_platform": stats.by_platform,
        "by_status": stats.by_status
    }


@router.get("/export")
async def export_report(
    period: str = "last_30_days",
    format: str = "json",
    current_user=Depends(get_current_user)
):
    """
    Exporta relatório de analytics.
    
    Formatos: json, csv
    """
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Formato inválido")
    
    try:
        metric_period = MetricPeriod(period)
    except ValueError:
        raise HTTPException(status_code=400, detail="Período inválido")
    
    data = await analytics_service.export_report(
        str(current_user.id),
        metric_period,
        format
    )
    
    content_type = "application/json" if format == "json" else "text/csv"
    filename = f"analytics_report_{period}.{format}"
    
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
