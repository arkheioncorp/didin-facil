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
        redis = await self._get_redis()
        
        # Buscar posts publicados do Redis
        start_ts = start_date.timestamp()
        end_ts = end_date.timestamp()
        
        # Buscar IDs de posts publicados no período
        published_key = f"published_posts:{user_id}:{platform.value}"
        post_ids = await redis.zrangebyscore(published_key, start_ts, end_ts) or []
        
        # Se não houver dados no Redis específico, tentar o geral
        if not post_ids:
            all_posts_key = f"published_posts:{user_id}"
            all_post_ids = await redis.zrangebyscore(all_posts_key, start_ts, end_ts) or []
            # Filtrar por plataforma
            for post_id in all_post_ids:
                post_data = await redis.get(f"post:{post_id}")
                if post_data:
                    import json
                    post = json.loads(post_data)
                    if post.get("platform") == platform.value:
                        post_ids.append(post_id)
        
        # Agregar métricas dos posts
        total_posts = len(post_ids)
        total_stories = 0
        total_reels = 0
        total_likes = 0
        total_comments = 0
        total_shares = 0
        total_views = 0
        total_reach = 0
        total_impressions = 0
        
        for post_id in post_ids:
            post_data = await redis.get(f"post:{post_id}")
            if post_data:
                import json
                post = json.loads(post_data)
                metrics = post.get("metrics", {})
                
                # Contar tipos de conteúdo
                content_type = post.get("content_type", "")
                if content_type == "story":
                    total_stories += 1
                elif content_type in ("reel", "video"):
                    total_reels += 1
                
                # Somar métricas
                total_likes += metrics.get("likes", 0)
                total_comments += metrics.get("comments", 0)
                total_shares += metrics.get("shares", 0)
                total_views += metrics.get("views", 0)
                total_reach += metrics.get("reach", 0)
                total_impressions += metrics.get("impressions", 0)
        
        # Buscar dados de seguidores
        followers_key = f"followers:{user_id}:{platform.value}"
        followers_start_data = await redis.get(f"{followers_key}:history:{start_date.strftime('%Y-%m-%d')}")
        followers_end_data = await redis.get(f"{followers_key}:current")
        
        followers_start = int(followers_start_data) if followers_start_data else 0
        followers_end = int(followers_end_data) if followers_end_data else 0
        
        # Calcular médias
        avg_likes = total_likes / total_posts if total_posts > 0 else 0
        avg_comments = total_comments / total_posts if total_posts > 0 else 0
        
        # Calcular engagement rate
        total_engagement = total_likes + total_comments + total_shares
        avg_engagement_rate = (total_engagement / total_reach * 100) if total_reach > 0 else 0
        
        return PlatformAnalytics(
            platform=platform,
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_posts=total_posts,
            total_stories=total_stories,
            total_reels=total_reels,
            total_likes=total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            total_views=total_views,
            total_reach=total_reach,
            total_impressions=total_impressions,
            avg_engagement_rate=round(avg_engagement_rate, 2),
            avg_likes_per_post=round(avg_likes, 2),
            avg_comments_per_post=round(avg_comments, 2),
            followers_start=followers_start,
            followers_end=followers_end,
            followers_gained=max(0, followers_end - followers_start),
            followers_lost=max(0, followers_start - followers_end) if followers_end < followers_start else 0
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
        """Obtém posts com melhor performance do Redis."""
        import json
        
        start_date, end_date = self._get_date_range(period)
        redis = await self._get_redis()
        
        start_ts = start_date.timestamp()
        end_ts = end_date.timestamp()
        
        # Buscar posts publicados no período
        published_key = f"published_posts:{user_id}"
        post_ids = await redis.zrangebyscore(
            published_key, start_ts, end_ts
        ) or []
        
        posts_with_metrics = []
        
        for post_id in post_ids:
            post_data = await redis.get(f"post:{post_id}")
            if not post_data:
                continue
                
            post = json.loads(post_data)
            
            # Filtrar por plataforma se especificada
            post_platform = post.get("platform")
            if platform and post_platform != platform.value:
                continue
            
            metrics_data = post.get("metrics", {})
            metrics = EngagementMetrics(
                likes=metrics_data.get("likes", 0),
                comments=metrics_data.get("comments", 0),
                shares=metrics_data.get("shares", 0),
                saves=metrics_data.get("saves", 0),
                views=metrics_data.get("views", 0),
                reach=metrics_data.get("reach", 0),
                impressions=metrics_data.get("impressions", 0)
            )
            
            # Calcular score de engagement para ordenação
            engagement_score = (
                metrics.likes + 
                (metrics.comments * 2) + 
                (metrics.shares * 3) + 
                (metrics.saves * 4)
            )
            
            # Parse da plataforma
            try:
                plat = Platform(post_platform)
            except ValueError:
                plat = Platform.INSTAGRAM
            
            published_at_str = post.get("published_at")
            published_at = (
                datetime.fromisoformat(published_at_str) 
                if published_at_str else datetime.utcnow()
            )
            
            posts_with_metrics.append({
                "post": PostAnalytics(
                    post_id=str(post_id),
                    platform=plat,
                    published_at=published_at,
                    content_type=post.get("content_type", "post"),
                    caption=post.get("caption", ""),
                    metrics=metrics,
                    thumbnail_url=post.get("thumbnail_url")
                ),
                "engagement_score": engagement_score,
                "likes": metrics.likes,
                "comments": metrics.comments,
                "views": metrics.views
            })
        
        # Ordenar pelo critério escolhido
        sort_key = sort_by if sort_by != "engagement" else "engagement_score"
        posts_with_metrics.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
        
        return [p["post"] for p in posts_with_metrics[:limit]]
    
    async def get_best_posting_times(
        self,
        user_id: str,
        period: MetricPeriod = MetricPeriod.LAST_90_DAYS,
        platform: Optional[Platform] = None
    ) -> Dict[str, List[int]]:
        """
        Calcula melhores horários para postar baseado em engagement histórico.

        Analisa posts anteriores e identifica horários com maior engagement.

        Returns:
            Dict mapeando dia da semana para lista de horários
            Ex: {"Monday": [9, 12, 18], "Tuesday": [10, 15, 20]}
        """
        import json
        from collections import defaultdict

        start_date, end_date = self._get_date_range(period)
        redis = await self._get_redis()

        # Buscar posts publicados no período
        published_key = f"published_posts:{user_id}"
        start_ts = start_date.timestamp()
        end_ts = end_date.timestamp()

        post_ids = await redis.zrangebyscore(
            published_key, start_ts, end_ts
        ) or []

        # Agregar engagement por dia da semana e hora
        # Estrutura: {day_name: {hour: [engagement_scores]}}
        engagement_by_time: Dict[str, Dict[int, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )

        for post_id in post_ids:
            post_data = await redis.get(f"post:{post_id}")
            if not post_data:
                continue

            post = json.loads(post_data)

            # Filtrar por plataforma se especificada
            if platform and post.get("platform") != platform.value:
                continue

            published_at_str = post.get("published_at")
            if not published_at_str:
                continue

            pub_date = datetime.fromisoformat(published_at_str)
            day_name = pub_date.strftime("%A")  # Monday, Tuesday, etc
            hour = pub_date.hour

            # Calcular engagement score
            metrics = post.get("metrics", {})
            engagement = (
                metrics.get("likes", 0) +
                metrics.get("comments", 0) * 2 +
                metrics.get("shares", 0) * 3
            )

            engagement_by_time[day_name][hour].append(engagement)

        # Calcular médias e encontrar melhores horários
        result: Dict[str, List[int]] = {}
        days_order = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        ]

        for day in days_order:
            if day not in engagement_by_time:
                # Retornar horários padrão se não houver dados
                result[day] = [9, 12, 18, 21]
                continue

            hour_data = engagement_by_time[day]
            # Calcular média de engagement por hora
            hour_avgs = []
            for hour, scores in hour_data.items():
                avg = sum(scores) / len(scores) if scores else 0
                hour_avgs.append((hour, avg))

            # Ordenar por engagement e pegar top 4 horários
            hour_avgs.sort(key=lambda x: x[1], reverse=True)
            top_hours = sorted([h for h, _ in hour_avgs[:4]])

            result[day] = top_hours if top_hours else [9, 12, 18, 21]

        return result
    
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
        Obtém tendência de engajamento ao longo do tempo do Redis.

        Returns:
            Lista de pontos com data e métricas
        """
        import json
        from collections import defaultdict

        start_date, end_date = self._get_date_range(period)
        redis = await self._get_redis()

        # Buscar posts publicados no período
        published_key = f"published_posts:{user_id}"
        start_ts = start_date.timestamp()
        end_ts = end_date.timestamp()

        post_ids = await redis.zrangebyscore(
            published_key, start_ts, end_ts
        ) or []

        # Agregar métricas por dia
        daily_metrics: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"likes": 0, "comments": 0, "shares": 0, "posts": 0}
        )

        for post_id in post_ids:
            post_data = await redis.get(f"post:{post_id}")
            if not post_data:
                continue

            post = json.loads(post_data)
            published_at = post.get("published_at")
            if not published_at:
                continue

            # Parse da data
            pub_date = datetime.fromisoformat(published_at)
            date_key = pub_date.strftime("%Y-%m-%d")

            metrics = post.get("metrics", {})
            daily_metrics[date_key]["likes"] += metrics.get("likes", 0)
            daily_metrics[date_key]["comments"] += metrics.get("comments", 0)
            daily_metrics[date_key]["shares"] += metrics.get("shares", 0)
            daily_metrics[date_key]["posts"] += 1

        # Construir trend com todos os dias do período
        trend = []
        current = start_date

        while current <= end_date:
            date_key = current.strftime("%Y-%m-%d")
            day_data = daily_metrics.get(date_key, {})

            total_engagement = (
                day_data.get("likes", 0) +
                day_data.get("comments", 0) +
                day_data.get("shares", 0)
            )
            posts_count = day_data.get("posts", 0)

            # Calcular engagement rate (engagement / posts)
            engagement_rate = (
                round(total_engagement / posts_count, 2)
                if posts_count > 0 else 0
            )

            trend.append({
                "date": current.isoformat(),
                "likes": day_data.get("likes", 0),
                "comments": day_data.get("comments", 0),
                "shares": day_data.get("shares", 0),
                "posts": posts_count,
                "engagement_rate": engagement_rate
            })
            current += timedelta(days=1)

        return trend
    
    async def get_followers_trend(
        self,
        user_id: str,
        period: MetricPeriod = MetricPeriod.LAST_30_DAYS,
        platform: Optional[Platform] = None
    ) -> List[Dict[str, Any]]:
        """Obtém tendência de crescimento de seguidores do Redis."""
        import json

        start_date, end_date = self._get_date_range(period)
        redis = await self._get_redis()

        # Determinar plataformas a consultar
        platforms = (
            [platform.value]
            if platform else ["instagram", "tiktok", "youtube"]
        )

        trend = []
        current = start_date

        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            total_followers = 0
            total_gained = 0
            total_lost = 0

            for plat in platforms:
                followers_key = f"followers:{user_id}:{plat}"

                # Tentar buscar dados históricos do dia
                day_data = await redis.get(f"{followers_key}:daily:{date_str}")
                if day_data:
                    data = json.loads(day_data)
                    total_followers += data.get("total", 0)
                    total_gained += data.get("gained", 0)
                    total_lost += data.get("lost", 0)
                else:
                    # Se não houver dados históricos, usar valor atual
                    current_val = await redis.get(f"{followers_key}:current")
                    if current_val:
                        total_followers += int(current_val)

            net_change = total_gained - total_lost

            trend.append({
                "date": current.isoformat(),
                "total": total_followers,
                "gained": total_gained,
                "lost": total_lost,
                "net": net_change
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
        """Obtém estatísticas do agendador de posts do Redis."""
        import json

        redis = await self._get_redis()

        # Buscar posts agendados do usuário
        scheduled_key = f"scheduled_posts:{user_id}"
        all_post_ids = await redis.zrange(scheduled_key, 0, -1) or []

        # Contadores
        total_scheduled = 0
        total_published = 0
        total_failed = 0
        total_pending = 0
        total_cancelled = 0
        total_processing = 0

        by_platform: Dict[str, Dict[str, int]] = {}
        by_status: Dict[str, int] = {
            "scheduled": 0,
            "published": 0,
            "failed": 0,
            "pending": 0,
            "cancelled": 0,
            "processing": 0
        }

        for post_id in all_post_ids:
            post_data = await redis.get(f"scheduled_post:{post_id}")
            if not post_data:
                continue

            post = json.loads(post_data)
            status = post.get("status", "scheduled").lower()
            platform = post.get("platform", "unknown")

            # Inicializar contagem da plataforma
            if platform not in by_platform:
                by_platform[platform] = {
                    "scheduled": 0,
                    "published": 0,
                    "failed": 0,
                    "pending": 0
                }

            total_scheduled += 1

            # Contar por status
            if status == "published":
                total_published += 1
                by_platform[platform]["published"] += 1
                by_status["published"] += 1
            elif status == "failed":
                total_failed += 1
                by_platform[platform]["failed"] += 1
                by_status["failed"] += 1
            elif status == "cancelled":
                total_cancelled += 1
                by_status["cancelled"] += 1
            elif status == "processing":
                total_processing += 1
                by_status["processing"] += 1
            else:  # scheduled ou pending
                total_pending += 1
                by_platform[platform]["pending"] += 1
                by_status["pending"] += 1
                by_platform[platform]["scheduled"] += 1
                by_status["scheduled"] += 1

        return SchedulerStats(
            period=period,
            total_scheduled=total_scheduled,
            total_published=total_published,
            total_failed=total_failed,
            total_pending=total_pending,
            by_platform=by_platform,
            by_status=by_status
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
