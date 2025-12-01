"""
Social Media Metrics for Prometheus
===================================
Métricas para monitoramento das integrações de redes sociais
"""

import time
from enum import Enum
from functools import wraps
from typing import Optional

from prometheus_client import Counter, Gauge, Histogram, Info

# ==============================================================================
# Platform Enum
# ==============================================================================

class SocialPlatform(str, Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    WHATSAPP = "whatsapp"


# ==============================================================================
# Counters - Eventos incrementais
# ==============================================================================

# Posts
POSTS_SCHEDULED = Counter(
    'social_posts_scheduled_total',
    'Total de posts agendados',
    ['platform', 'content_type']
)

POSTS_PUBLISHED = Counter(
    'social_posts_published_total',
    'Total de posts publicados com sucesso',
    ['platform', 'content_type']
)

POSTS_FAILED = Counter(
    'social_posts_failed_total',
    'Total de posts que falharam',
    ['platform', 'error_type']
)

POSTS_RETRIED = Counter(
    'social_posts_retried_total',
    'Total de tentativas de retry',
    ['platform']
)

# Autenticação
AUTH_ATTEMPTS = Counter(
    'social_auth_attempts_total',
    'Total de tentativas de autenticação',
    ['platform', 'status']
)

CHALLENGES_RECEIVED = Counter(
    'social_challenges_received_total',
    'Total de challenges de verificação recebidos',
    ['platform', 'challenge_type']
)

CHALLENGES_RESOLVED = Counter(
    'social_challenges_resolved_total',
    'Total de challenges resolvidos',
    ['platform', 'challenge_type', 'success']
)

# Sessions
SESSION_CREATED = Counter(
    'social_sessions_created_total',
    'Total de sessões criadas',
    ['platform']
)

SESSION_EXPIRED = Counter(
    'social_sessions_expired_total',
    'Total de sessões expiradas',
    ['platform']
)

SESSION_REFRESHED = Counter(
    'social_sessions_refreshed_total',
    'Total de sessões renovadas',
    ['platform']
)

# API Calls
API_CALLS = Counter(
    'social_api_calls_total',
    'Total de chamadas a APIs de plataformas',
    ['platform', 'endpoint', 'status_code']
)

# Rate Limits
RATE_LIMITS_HIT = Counter(
    'social_rate_limits_hit_total',
    'Total de rate limits atingidos',
    ['platform']
)


# ==============================================================================
# Histograms - Duração de operações
# ==============================================================================

# Duração de upload
UPLOAD_DURATION = Histogram(
    'social_upload_duration_seconds',
    'Tempo de upload de mídia',
    ['platform', 'content_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

# Duração de login
LOGIN_DURATION = Histogram(
    'social_login_duration_seconds',
    'Tempo de processo de login',
    ['platform'],
    buckets=[0.5, 1, 2, 5, 10, 30, 60]
)

# Duração de publicação completa (incluindo processamento)
PUBLISH_DURATION = Histogram(
    'social_publish_duration_seconds',
    'Tempo total de publicação',
    ['platform'],
    buckets=[5, 15, 30, 60, 120, 300, 600]
)

# Latência de API
API_LATENCY = Histogram(
    'social_api_latency_seconds',
    'Latência de chamadas às APIs',
    ['platform', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1, 2.5, 5, 10]
)

# Tamanho de arquivos uploadados
FILE_SIZE = Histogram(
    'social_file_size_bytes',
    'Tamanho dos arquivos de mídia',
    ['platform', 'content_type'],
    buckets=[100_000, 500_000, 1_000_000, 5_000_000, 10_000_000, 50_000_000, 100_000_000]
)


# ==============================================================================
# Gauges - Valores atuais
# ==============================================================================

# Sessions ativas
ACTIVE_SESSIONS = Gauge(
    'social_active_sessions',
    'Número de sessões ativas',
    ['platform']
)

# Posts agendados pendentes
PENDING_POSTS = Gauge(
    'social_pending_posts',
    'Número de posts agendados pendentes',
    ['platform']
)

# Posts na DLQ
DLQ_SIZE = Gauge(
    'social_dlq_size',
    'Número de posts na Dead Letter Queue',
    ['platform']
)

# Quota de API
YOUTUBE_QUOTA_USED = Gauge(
    'youtube_quota_used',
    'Quota de API do YouTube usada hoje',
    ['user_id']
)

YOUTUBE_QUOTA_REMAINING = Gauge(
    'youtube_quota_remaining',
    'Quota de API do YouTube restante',
    ['user_id']
)

# Worker status
WORKER_STATUS = Gauge(
    'social_worker_status',
    'Status do worker de publicação (1=running, 0=stopped)',
    ['worker_name']
)

WORKER_LAST_RUN = Gauge(
    'social_worker_last_run_timestamp',
    'Timestamp da última execução do worker',
    ['worker_name']
)


# ==============================================================================
# Info - Metadados
# ==============================================================================

SERVICE_INFO = Info(
    'social_service',
    'Informações do serviço de redes sociais'
)


# ==============================================================================
# Helper Functions
# ==============================================================================

def track_post_scheduled(platform: str, content_type: str):
    """Registra um post agendado."""
    POSTS_SCHEDULED.labels(platform=platform, content_type=content_type).inc()


def track_post_published(platform: str, content_type: str):
    """Registra um post publicado com sucesso."""
    POSTS_PUBLISHED.labels(platform=platform, content_type=content_type).inc()


def track_post_failed(platform: str, error_type: str):
    """Registra uma falha de publicação."""
    POSTS_FAILED.labels(platform=platform, error_type=error_type).inc()


def track_auth_attempt(platform: str, success: bool):
    """Registra uma tentativa de autenticação."""
    status = "success" if success else "failed"
    AUTH_ATTEMPTS.labels(platform=platform, status=status).inc()


def track_challenge(platform: str, challenge_type: str, resolved: bool = False, success: bool = False):
    """Registra um challenge de verificação."""
    if not resolved:
        CHALLENGES_RECEIVED.labels(platform=platform, challenge_type=challenge_type).inc()
    else:
        CHALLENGES_RESOLVED.labels(
            platform=platform, 
            challenge_type=challenge_type,
            success=str(success).lower()
        ).inc()


def track_api_call(platform: str, endpoint: str, status_code: int, duration: float):
    """Registra uma chamada de API."""
    API_CALLS.labels(
        platform=platform, 
        endpoint=endpoint, 
        status_code=str(status_code)
    ).inc()
    API_LATENCY.labels(platform=platform, endpoint=endpoint).observe(duration)


def update_active_sessions(platform: str, count: int):
    """Atualiza contagem de sessões ativas."""
    ACTIVE_SESSIONS.labels(platform=platform).set(count)


def update_pending_posts(platform: str, count: int):
    """Atualiza contagem de posts pendentes."""
    PENDING_POSTS.labels(platform=platform).set(count)


def update_dlq_size(platform: str, count: int):
    """Atualiza tamanho da DLQ."""
    DLQ_SIZE.labels(platform=platform).set(count)


def update_youtube_quota(user_id: str, used: int, remaining: int):
    """Atualiza métricas de quota do YouTube."""
    YOUTUBE_QUOTA_USED.labels(user_id=user_id).set(used)
    YOUTUBE_QUOTA_REMAINING.labels(user_id=user_id).set(remaining)


def update_worker_status(worker_name: str, is_running: bool):
    """Atualiza status do worker."""
    WORKER_STATUS.labels(worker_name=worker_name).set(1 if is_running else 0)
    if is_running:
        WORKER_LAST_RUN.labels(worker_name=worker_name).set(time.time())


# ==============================================================================
# Decorators
# ==============================================================================

def track_upload_duration(platform: str, content_type: str):
    """Decorator para medir duração de uploads."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                UPLOAD_DURATION.labels(
                    platform=platform, 
                    content_type=content_type
                ).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                UPLOAD_DURATION.labels(
                    platform=platform, 
                    content_type=content_type
                ).observe(duration)
                raise
        return wrapper
    return decorator


def track_publish_duration(platform: str):
    """Decorator para medir duração de publicação."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                PUBLISH_DURATION.labels(platform=platform).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                PUBLISH_DURATION.labels(platform=platform).observe(duration)
                raise
        return wrapper
    return decorator


def track_login_duration(platform: str):
    """Decorator para medir duração de login."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                LOGIN_DURATION.labels(platform=platform).observe(duration)
                track_auth_attempt(platform, success=True)
                return result
            except Exception:
                duration = time.time() - start_time
                LOGIN_DURATION.labels(platform=platform).observe(duration)
                track_auth_attempt(platform, success=False)
                raise
        return wrapper
    return decorator


# ==============================================================================
# Collector para métricas agregadas
# ==============================================================================

class SocialMetricsCollector:
    """Coletor de métricas agregadas de redes sociais."""
    
    def __init__(self):
        self._redis = None
    
    async def _get_redis(self):
        if self._redis is None:
            from shared.redis import get_redis
            self._redis = await get_redis()
        return self._redis
    
    async def collect_all_metrics(self):
        """Coleta todas as métricas e atualiza gauges."""
        try:
            await self._collect_session_metrics()
            await self._collect_post_metrics()
            await self._collect_dlq_metrics()
            await self._collect_quota_metrics()
        except Exception as e:
            import logging
            logging.error(f"Erro ao coletar métricas: {e}")
    
    async def _collect_session_metrics(self):
        """Coleta métricas de sessões."""
        redis = await self._get_redis()
        
        for platform in SocialPlatform:
            # Contar sessões ativas no Redis
            pattern = f"{platform.value}:session:*"
            keys = await redis.keys(pattern)
            update_active_sessions(platform.value, len(keys))
    
    async def _collect_post_metrics(self):
        """Coleta métricas de posts agendados."""
        redis = await self._get_redis()
        
        for platform in SocialPlatform:
            # Contar posts pendentes
            pattern = f"scheduled:post:{platform.value}:*"
            keys = await redis.keys(pattern)
            update_pending_posts(platform.value, len(keys))
    
    async def _collect_dlq_metrics(self):
        """Coleta métricas da DLQ."""
        redis = await self._get_redis()
        
        for platform in SocialPlatform:
            # Contar itens na DLQ
            dlq_key = f"dlq:{platform.value}"
            count = await redis.llen(dlq_key)
            update_dlq_size(platform.value, count)
    
    async def _collect_quota_metrics(self):
        """Coleta métricas de quota do YouTube."""
        redis = await self._get_redis()
        
        # Buscar todas as quotas de YouTube
        pattern = "youtube:quota:*"
        keys = await redis.keys(pattern)
        
        for key in keys:
            parts = key.split(":")
            if len(parts) >= 3:
                user_id = parts[2]
                data = await redis.get(key)
                if data:
                    import json
                    try:
                        quota_data = json.loads(data)
                        used = quota_data.get("total", 0)
                        remaining = 10000 - used  # Quota padrão do YouTube
                        update_youtube_quota(user_id, used, remaining)
                    except json.JSONDecodeError:
                        pass


# Instância global do coletor
metrics_collector = SocialMetricsCollector()


# ==============================================================================
# Inicialização
# ==============================================================================

def init_metrics():
    """Inicializa métricas com valores padrão."""
    SERVICE_INFO.info({
        'version': '1.0.0',
        'service': 'didin-facil-social',
        'platforms': 'instagram,tiktok,youtube,whatsapp'
    })
    
    # Inicializar gauges com 0
    for platform in SocialPlatform:
        update_active_sessions(platform.value, 0)
        update_pending_posts(platform.value, 0)
        update_dlq_size(platform.value, 0)
    
    # Worker status
    update_worker_status("post_scheduler", False)
    update_worker_status("session_monitor", False)
