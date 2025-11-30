"""
Social Media Analytics
======================
Dashboard de analytics para redes sociais.

Métricas:
- Posts por plataforma
- Engagement rate
- Reach e impressões
- Melhores horários para postar
- Crescimento de seguidores
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MetricPeriod(str, Enum):
    """Período de métricas."""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"


class Platform(str, Enum):
    """Plataformas de social media."""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    WHATSAPP = "whatsapp"
    ALL = "all"


# ============================================
# DATA MODELS
# ============================================

@dataclass
class EngagementMetrics:
    """Métricas de engajamento."""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    views: int = 0
    reach: int = 0
    impressions: int = 0
    
    @property
    def engagement_rate(self) -> float:
        """Taxa de engajamento."""
        if self.reach == 0:
            return 0.0
        total_engagement = self.likes + self.comments + self.shares + self.saves
        return (total_engagement / self.reach) * 100
    
    @property
    def click_through_rate(self) -> float:
        """Taxa de clique."""
        if self.impressions == 0:
            return 0.0
        return (self.clicks / self.impressions) * 100


@dataclass
class PostAnalytics:
    """Analytics de um post individual."""
    post_id: str
    platform: Platform
    published_at: datetime
    content_type: str  # image, video, reel, story
    caption: str = ""
    
    # Métricas
    metrics: EngagementMetrics = field(default_factory=EngagementMetrics)
    
    # Metadata
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None


@dataclass
class PlatformAnalytics:
    """Analytics agregado por plataforma."""
    platform: Platform
    period: MetricPeriod
    start_date: datetime
    end_date: datetime
    
    # Contadores
    total_posts: int = 0
    total_stories: int = 0
    total_reels: int = 0
    
    # Métricas agregadas
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_views: int = 0
    total_reach: int = 0
    total_impressions: int = 0
    
    # Médias
    avg_engagement_rate: float = 0.0
    avg_likes_per_post: float = 0.0
    avg_comments_per_post: float = 0.0
    
    # Crescimento
    followers_start: int = 0
    followers_end: int = 0
    followers_gained: int = 0
    followers_lost: int = 0
    
    @property
    def followers_growth_rate(self) -> float:
        """Taxa de crescimento de seguidores."""
        if self.followers_start == 0:
            return 0.0
        return ((self.followers_end - self.followers_start) / self.followers_start) * 100


@dataclass
class DashboardOverview:
    """Overview do dashboard."""
    period: MetricPeriod
    start_date: datetime
    end_date: datetime
    
    # Totais
    total_posts: int = 0
    total_engagement: int = 0
    total_reach: int = 0
    total_followers: int = 0
    
    # Por plataforma
    by_platform: Dict[str, PlatformAnalytics] = field(default_factory=dict)
    
    # Top posts
    top_posts: List[PostAnalytics] = field(default_factory=list)
    
    # Melhores horários
    best_times: Dict[str, List[int]] = field(default_factory=dict)  # dia -> horas
    
    # Tendências
    engagement_trend: List[Dict[str, Any]] = field(default_factory=list)
    followers_trend: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SchedulerStats:
    """Estatísticas do agendador."""
    period: MetricPeriod
    
    # Contadores
    total_scheduled: int = 0
    total_published: int = 0
    total_failed: int = 0
    total_pending: int = 0
    
    # Por plataforma
    by_platform: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # Por status
    by_status: Dict[str, int] = field(default_factory=dict)
    
    # Taxa de sucesso
    @property
    def success_rate(self) -> float:
        if self.total_scheduled == 0:
            return 0.0
        return (self.total_published / self.total_scheduled) * 100


# ============================================
# ANALYTICS SERVICE
# ============================================

class SocialAnalyticsService:
    """
    Serviço de analytics para redes sociais.
    
    Uso:
        service = SocialAnalyticsService()
        
        # Overview do dashboard
        overview = await service.get_dashboard_overview(
            user_id, MetricPeriod.LAST_30_DAYS
        )
        
        # Analytics por plataforma
        instagram = await service.get_platform_analytics(
            user_id, Platform.INSTAGRAM, MetricPeriod.LAST_7_DAYS
        )
    """
    
    def __init__(self):
        self._redis = None
        self._db = None
    
    async def _get_redis(self):
        if self._redis is None:
            from shared.redis import get_redis
            self._redis = await get_redis()
        return self._redis
    
    def _get_date_range(
        self,
        period: MetricPeriod,
        custom_start: Optional[datetime] = None,
        custom_end: Optional[datetime] = None
    ) -> tuple[datetime, datetime]:
        """Calcula range de datas para o período."""
        now = datetime.utcnow()
        
        if period == MetricPeriod.TODAY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == MetricPeriod.YESTERDAY:
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == MetricPeriod.LAST_7_DAYS:
            start = now - timedelta(days=7)
            end = now
        elif period == MetricPeriod.LAST_30_DAYS:
            start = now - timedelta(days=30)
            end = now
        elif period == MetricPeriod.LAST_90_DAYS:
            start = now - timedelta(days=90)
            end = now
        elif period == MetricPeriod.THIS_MONTH:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == MetricPeriod.LAST_MONTH:
            first_of_month = now.replace(day=1)
            end = first_of_month - timedelta(days=1)
            start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == MetricPeriod.THIS_YEAR:
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == MetricPeriod.CUSTOM and custom_start and custom_end:
            start = custom_start
            end = custom_end
        else:
            start = now - timedelta(days=30)
            end = now
        
        return start, end
    
    # ========================================
    # DASHBOARD
    # ========================================
    
    async def get_dashboard_overview(
        self,
        user_id: str,
        period: MetricPeriod = MetricPeriod.LAST_30_DAYS,
        custom_start: Optional[datetime] = None,
        custom_end: Optional[datetime] = None
    ) -> DashboardOverview:
        """
        Obtém overview completo do dashboard.
        
        Args:
            user_id: ID do usuário
            period: Período de análise
        
        Returns:
            DashboardOverview com todas as métricas
        """
        start_date, end_date = self._get_date_range(period, custom_start, custom_end)
        
        # Buscar analytics de cada plataforma
        platforms = [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE]
        by_platform = {}
        
        total_posts = 0
        total_engagement = 0
        total_reach = 0
        total_followers = 0
        
        for platform in platforms:
            analytics = await self.get_platform_analytics(
                user_id, platform, period, custom_start, custom_end
            )
            by_platform[platform.value] = analytics
            
            total_posts += analytics.total_posts
            total_engagement += analytics.total_likes + analytics.total_comments + analytics.total_shares
            total_reach += analytics.total_reach
            total_followers += analytics.followers_end
        
        # Buscar top posts
        top_posts = await self.get_top_posts(user_id, period, limit=10)
        
        # Calcular melhores horários
        best_times = await self.get_best_posting_times(user_id, period)
        
        # Tendências
        engagement_trend = await self.get_engagement_trend(user_id, period)
        followers_trend = await self.get_followers_trend(user_id, period)
        
        return DashboardOverview(
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_posts=total_posts,
            total_engagement=total_engagement,
            total_reach=total_reach,
            total_followers=total_followers,
            by_platform=by_platform,
            top_posts=top_posts,
            best_times=best_times,
            engagement_trend=engagement_trend,
            followers_trend=followers_trend
        )
    
    async def get_platform_analytics(
        self,
        user_id: str,
        platform: Platform,
        period: MetricPeriod = MetricPeriod.LAST_30_DAYS,
        custom_start: Optional[datetime] = None,
        custom_end: Optional[datetime] = None
    ) -> PlatformAnalytics:
        """Obtém analytics de uma plataforma específica."""
        start_date, end_date = self._get_date_range(period, custom_start, custom_end)
        
        # TODO: Implementar query real no banco
        # Por enquanto, retorna dados mock
        
        return PlatformAnalytics(
            platform=platform,
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_posts=25,
            total_stories=15,
            total_reels=10,
            total_likes=1500,
            total_comments=200,
            total_shares=50,
            total_views=10000,
            total_reach=8000,
            total_impressions=15000,
            avg_engagement_rate=4.5,
            avg_likes_per_post=60,
            avg_comments_per_post=8,
            followers_start=5000,
            followers_end=5200,
            followers_gained=250,
            followers_lost=50
        )
    
    # ========================================
    # TOP CONTENT
    # ========================================
    
    async def get_top_posts(
        self,
        user_id: str,
        period: MetricPeriod = MetricPeriod.LAST_30_DAYS,
        platform: Optional[Platform] = None,
        limit: int = 10,
        sort_by: str = "engagement"  # engagement, likes, comments, views
    ) -> List[PostAnalytics]:
        """Obtém posts com melhor performance."""
        # Mock data for development
        mock_posts = []
        platforms = [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE]
        
        for i in range(limit):
            p = platform or platforms[i % 3]
            metrics = EngagementMetrics(
                likes=150 + (i * 10),
                comments=20 + i,
                shares=5 + i,
                saves=2 + i,
                views=1000 + (i * 100),
                reach=800 + (i * 80),
                impressions=1200 + (i * 120)
            )
            
            mock_posts.append(PostAnalytics(
                post_id=f"post_{i}",
                platform=p,
                published_at=datetime.utcnow() - timedelta(days=i),
                content_type="video",
                caption=f"Amazing content #{i} about dropshipping strategies 🚀",
                metrics=metrics,
                thumbnail_url=f"https://picsum.photos/seed/{i}/300/200"
            ))
            
        return mock_posts
    
    async def get_best_posting_times(
        self,
        user_id: str,
        period: MetricPeriod = MetricPeriod.LAST_90_DAYS,
        platform: Optional[Platform] = None
    ) -> Dict[str, List[int]]:
        """
        Calcula melhores horários para postar.
        
        Baseado em engagement histórico.
        
        Returns:
            Dict mapeando dia da semana para lista de horários
            Ex: {"monday": [9, 12, 18], "tuesday": [10, 15, 20]}
        """
        # Mock data based on general best practices
        return {
            "Monday": [9, 12, 18, 21],
            "Tuesday": [10, 13, 19, 21],
            "Wednesday": [9, 12, 18, 20],
            "Thursday": [10, 14, 19, 21],
            "Friday": [9, 12, 17, 20],
            "Saturday": [11, 15, 19, 21],
            "Sunday": [10, 14, 18, 20]
        }
    
    # ========================================
    # TRENDS
    # ========================================
    
    async def get_engagement_trend(
        self,
        user_id: str,
        period: MetricPeriod = MetricPeriod.LAST_30_DAYS,
        granularity: str = "day"  # day, week, month
    ) -> List[Dict[str, Any]]:
        """
        Obtém tendência de engajamento ao longo do tempo.
        
        Returns:
            Lista de pontos com data e métricas
        """
        start_date, end_date = self._get_date_range(period)
        
        # TODO: Implementar query real
        # Por enquanto, gera dados mock
        
        trend = []
        current = start_date
        
        while current <= end_date:
            trend.append({
                "date": current.isoformat(),
                "likes": 50 + (current.day * 2),
                "comments": 10 + current.day,
                "shares": 5 + (current.day // 2),
                "engagement_rate": 3.5 + (current.day % 10) / 10
            })
            current += timedelta(days=1)
        
        return trend
    
    async def get_followers_trend(
        self,
        user_id: str,
        period: MetricPeriod = MetricPeriod.LAST_30_DAYS,
        platform: Optional[Platform] = None
    ) -> List[Dict[str, Any]]:
        """Obtém tendência de crescimento de seguidores."""
        start_date, end_date = self._get_date_range(period)
        
        # TODO: Implementar query real
        trend = []
        current = start_date
        followers = 5000
        
        while current <= end_date:
            gained = 5 + (current.day % 10)
            lost = 1 + (current.day % 3)
            followers += gained - lost
            
            trend.append({
                "date": current.isoformat(),
                "total": followers,
                "gained": gained,
                "lost": lost,
                "net": gained - lost
            })
            current += timedelta(days=1)
        
        return trend
    
    # ========================================
    # SCHEDULER STATS
    # ========================================
    
    async def get_scheduler_stats(
        self,
        user_id: str,
        period: MetricPeriod = MetricPeriod.LAST_30_DAYS
    ) -> SchedulerStats:
        """Obtém estatísticas do agendador de posts."""
        await self._get_redis()
        
        # Buscar dados do Redis/banco
        # TODO: Implementar query real
        
        return SchedulerStats(
            period=period,
            total_scheduled=100,
            total_published=95,
            total_failed=3,
            total_pending=2,
            by_platform={
                "instagram": {"scheduled": 40, "published": 38, "failed": 1},
                "tiktok": {"scheduled": 35, "published": 34, "failed": 1},
                "youtube": {"scheduled": 25, "published": 23, "failed": 1}
            },
            by_status={
                "published": 95,
                "failed": 3,
                "pending": 2
            }
        )
    
    # ========================================
    # COMPARISON
    # ========================================
    
    async def compare_periods(
        self,
        user_id: str,
        period1: MetricPeriod,
        period2: MetricPeriod,
        platform: Optional[Platform] = None
    ) -> Dict[str, Any]:
        """
        Compara métricas entre dois períodos.
        
        Returns:
            Dict com métricas de ambos períodos e variação percentual
        """
        analytics1 = await self.get_platform_analytics(
            user_id, platform or Platform.ALL, period1
        )
        analytics2 = await self.get_platform_analytics(
            user_id, platform or Platform.ALL, period2
        )
        
        def calc_change(old: float, new: float) -> float:
            if old == 0:
                return 100.0 if new > 0 else 0.0
            return ((new - old) / old) * 100
        
        return {
            "period1": {
                "period": period1.value,
                "total_posts": analytics1.total_posts,
                "engagement_rate": analytics1.avg_engagement_rate,
                "reach": analytics1.total_reach,
                "followers": analytics1.followers_end
            },
            "period2": {
                "period": period2.value,
                "total_posts": analytics2.total_posts,
                "engagement_rate": analytics2.avg_engagement_rate,
                "reach": analytics2.total_reach,
                "followers": analytics2.followers_end
            },
            "changes": {
                "posts_change": calc_change(analytics1.total_posts, analytics2.total_posts),
                "engagement_change": calc_change(analytics1.avg_engagement_rate, analytics2.avg_engagement_rate),
                "reach_change": calc_change(analytics1.total_reach, analytics2.total_reach),
                "followers_change": calc_change(analytics1.followers_end, analytics2.followers_end)
            }
        }
    
    # ========================================
    # EXPORT
    # ========================================
    
    async def export_report(
        self,
        user_id: str,
        period: MetricPeriod,
        format: str = "json"  # json, csv, pdf
    ) -> bytes:
        """
        Exporta relatório de analytics.
        
        Args:
            user_id: ID do usuário
            period: Período do relatório
            format: Formato de saída
        
        Returns:
            Bytes do arquivo exportado
        """
        overview = await self.get_dashboard_overview(user_id, period)
        
        if format == "json":
            import json
            data = {
                "period": period.value,
                "start_date": overview.start_date.isoformat(),
                "end_date": overview.end_date.isoformat(),
                "total_posts": overview.total_posts,
                "total_engagement": overview.total_engagement,
                "total_reach": overview.total_reach,
                "total_followers": overview.total_followers,
                "best_times": overview.best_times
            }
            return json.dumps(data, indent=2).encode()
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Period", period.value])
            writer.writerow(["Total Posts", overview.total_posts])
            writer.writerow(["Total Engagement", overview.total_engagement])
            writer.writerow(["Total Reach", overview.total_reach])
            writer.writerow(["Total Followers", overview.total_followers])
            
            return output.getvalue().encode()
        
        # TODO: Implementar PDF export
        raise NotImplementedError(f"Export format {format} not implemented")
