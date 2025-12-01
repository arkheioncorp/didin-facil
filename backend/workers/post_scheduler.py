"""
Social Post Scheduler
Agendamento de publicações para redes sociais

Inclui:
- Retry com exponential backoff
- Dead letter queue para posts que falharam múltiplas vezes
- Métricas de processamento
- Notificações WebSocket
"""

import asyncio
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Prometheus Metrics
try:
    from monitoring.social_metrics import (DLQ_SIZE, PENDING_POSTS,
                                           POSTS_RETRIED, PUBLISH_DURATION,
                                           WORKER_LAST_RUN, WORKER_STATUS,
                                           track_post_failed,
                                           track_post_published,
                                           track_post_scheduled)
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    logger.warning("Prometheus metrics not available")

# WebSocket Notifications
try:
    from api.routes.websocket_notifications import (NotificationType,
                                                    publish_notification)
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    logger.warning("WebSocket notifications not available")

# Configurações de retry
MAX_RETRY_ATTEMPTS = 3
BASE_RETRY_DELAY = 60  # segundos
MAX_RETRY_DELAY = 3600  # 1 hora


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    WHATSAPP = "whatsapp"


class PostStatus(str, Enum):
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledPost(BaseModel):
    """Representa um post agendado."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    platform: Platform
    scheduled_time: datetime
    status: PostStatus = PostStatus.SCHEDULED
    
    # Conteúdo
    content_type: str  # photo, video, reel, story, text
    caption: str = ""
    hashtags: List[str] = []
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    
    # Configurações específicas
    platform_config: Dict[str, Any] = {}
    
    # Metadados
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    # Conta específica
    account_name: Optional[str] = None
    
    # Retry tracking
    retry_count: int = 0
    last_retry_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    retry_errors: List[str] = []


class PostSchedulerService:
    """
    Serviço de agendamento de posts.
    
    Usa Redis para persistir posts agendados e
    um worker para processar na hora certa.
    """
    
    def __init__(self):
        self._redis = None
        self._running = False
        self._worker_task = None
    
    async def _get_redis(self):
        if self._redis is None:
            from shared.redis import get_redis
            self._redis = await get_redis()
        return self._redis
    
    async def schedule(self, post: ScheduledPost) -> ScheduledPost:
        """Agenda um novo post."""
        redis = await self._get_redis()
        
        # Salvar no Redis
        key = f"scheduled_post:{post.id}"
        await redis.set(key, post.model_dump_json())
        
        # Adicionar ao sorted set para ordenação por tempo
        score = post.scheduled_time.timestamp()
        await redis.zadd(
            f"scheduled_posts:{post.user_id}",
            {post.id: score}
        )
        
        # Adicionar ao set global
        await redis.zadd("all_scheduled_posts", {post.id: score})
        
        # Track metrics
        if METRICS_AVAILABLE:
            track_post_scheduled(post.platform.value, post.content_type)
            await self._update_pending_metrics()
        
        logger.info(
            f"Post {post.id} agendado para {post.scheduled_time} "
            f"em {post.platform.value}"
        )
        
        return post
    
    async def cancel(self, post_id: str, user_id: str) -> bool:
        """Cancela um post agendado."""
        redis = await self._get_redis()
        
        key = f"scheduled_post:{post_id}"
        data = await redis.get(key)
        
        if not data:
            return False
        
        post = ScheduledPost.model_validate_json(data)
        
        if post.user_id != user_id:
            return False
        
        if post.status != PostStatus.SCHEDULED:
            return False
        
        # Atualizar status
        post.status = PostStatus.CANCELLED
        await redis.set(key, post.model_dump_json())
        
        # Remover dos sets
        await redis.zrem(f"scheduled_posts:{user_id}", post_id)
        await redis.zrem("all_scheduled_posts", post_id)
        
        logger.info(f"Post {post_id} cancelado")
        return True
    
    async def get_user_posts(
        self,
        user_id: str,
        status: Optional[PostStatus] = None,
        limit: int = 50
    ) -> List[ScheduledPost]:
        """Lista posts do usuário."""
        redis = await self._get_redis()
        
        # Buscar IDs do sorted set
        post_ids = await redis.zrange(
            f"scheduled_posts:{user_id}",
            0, limit - 1
        )
        
        posts = []
        for pid in post_ids:
            data = await redis.get(f"scheduled_post:{pid}")
            if data:
                post = ScheduledPost.model_validate_json(data)
                if status is None or post.status == status:
                    posts.append(post)
        
        return posts
    
    async def get_pending_posts(self) -> List[ScheduledPost]:
        """Busca posts prontos para publicar (incluindo retries)."""
        redis = await self._get_redis()
        now = datetime.now(timezone.utc).timestamp()
        
        # Buscar posts com scheduled_time <= now
        post_ids = await redis.zrangebyscore(
            "all_scheduled_posts",
            "-inf",
            now
        )
        
        posts = []
        for pid in post_ids:
            data = await redis.get(f"scheduled_post:{pid}")
            if data:
                post = ScheduledPost.model_validate_json(data)
                if post.status == PostStatus.SCHEDULED:
                    posts.append(post)
        
        # Também buscar posts em retry
        retry_ids = await redis.zrangebyscore(
            "retry_scheduled_posts",
            "-inf",
            now
        )
        
        for pid in retry_ids:
            data = await redis.get(f"scheduled_post:{pid}")
            if data:
                post = ScheduledPost.model_validate_json(data)
                if post.status == PostStatus.SCHEDULED and post.retry_count > 0:
                    posts.append(post)
        
        return posts
    
    def _calculate_retry_delay(self, retry_count: int) -> int:
        """
        Calcula delay para próximo retry usando exponential backoff com jitter.
        
        Formula: min(MAX_DELAY, BASE_DELAY * 2^retry_count + random_jitter)
        """
        delay = BASE_RETRY_DELAY * (2 ** retry_count)
        # Adiciona jitter de até 25% para evitar thundering herd
        jitter = random.uniform(0, delay * 0.25)
        return min(MAX_RETRY_DELAY, int(delay + jitter))
    
    async def _schedule_retry(self, post: ScheduledPost, error: str) -> bool:
        """
        Agenda retry para um post que falhou.
        
        Returns:
            True se retry foi agendado, False se max retries atingido
        """
        redis = await self._get_redis()
        
        if post.retry_count >= MAX_RETRY_ATTEMPTS:
            # Move para dead letter queue
            await self._move_to_dlq(post, error)
            return False
        
        # Incrementar contador e registrar erro
        post.retry_count += 1
        post.last_retry_at = datetime.now(timezone.utc)
        post.retry_errors.append(
            f"[{datetime.now(timezone.utc).isoformat()}] {error}"
        )
        
        # Calcular próximo retry
        delay = self._calculate_retry_delay(post.retry_count)
        post.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        post.status = PostStatus.SCHEDULED  # Volta para scheduled
        
        # Track retry metric
        if METRICS_AVAILABLE:
            POSTS_RETRIED.labels(platform=post.platform.value).inc()
        
        # Atualizar no Redis
        await redis.set(
            f"scheduled_post:{post.id}",
            post.model_dump_json()
        )
        
        # Adicionar ao sorted set de retries
        await redis.zadd(
            "retry_scheduled_posts",
            {post.id: post.next_retry_at.timestamp()}
        )
        
        logger.warning(
            f"Post {post.id} agendado para retry #{post.retry_count} "
            f"em {delay}s (próximo: {post.next_retry_at})"
        )
        
        return True
    
    async def _move_to_dlq(self, post: ScheduledPost, final_error: str):
        """Move post para Dead Letter Queue após esgotar retries."""
        redis = await self._get_redis()
        
        post.status = PostStatus.FAILED
        post.error_message = (
            f"Max retries ({MAX_RETRY_ATTEMPTS}) exceeded. "
            f"Last error: {final_error}"
        )
        
        # Track failure metric
        if METRICS_AVAILABLE:
            track_post_failed(post.platform.value, "max_retries")
            await self._update_dlq_metrics()
        
        # Send WebSocket notification
        if NOTIFICATIONS_AVAILABLE:
            await publish_notification(
                notification_type=NotificationType.POST_FAILED,
                title="Publicação Falhou",
                message=f"Post para {post.platform.value} falhou após "
                        f"{MAX_RETRY_ATTEMPTS} tentativas",
                user_id=post.user_id,
                platform=post.platform.value,
                data={"post_id": post.id, "error": final_error},
            )
        
        # Salvar estado final
        await redis.set(
            f"scheduled_post:{post.id}",
            post.model_dump_json()
        )
        
        # Adicionar à DLQ para análise posterior
        await redis.lpush("dlq_scheduled_posts", post.id)
        
        # Remover de todos os sets de scheduling
        await redis.zrem("all_scheduled_posts", post.id)
        await redis.zrem("retry_scheduled_posts", post.id)
        
        logger.error(
            f"Post {post.id} movido para DLQ após {post.retry_count} tentativas."
        )
    
    async def get_dlq_posts(self, limit: int = 50) -> List[ScheduledPost]:
        """Lista posts na Dead Letter Queue."""
        redis = await self._get_redis()
        
        post_ids = await redis.lrange("dlq_scheduled_posts", 0, limit - 1)
        
        posts = []
        for pid in post_ids:
            data = await redis.get(f"scheduled_post:{pid}")
            if data:
                posts.append(ScheduledPost.model_validate_json(data))
        
        return posts
    
    async def retry_dlq_post(self, post_id: str) -> bool:
        """Reprocessa um post da DLQ manualmente."""
        redis = await self._get_redis()
        
        data = await redis.get(f"scheduled_post:{post_id}")
        if not data:
            return False
        
        post = ScheduledPost.model_validate_json(data)
        
        # Reset retry count e status
        post.retry_count = 0
        post.retry_errors = []
        post.status = PostStatus.SCHEDULED
        post.scheduled_time = datetime.now(timezone.utc)
        
        # Remover da DLQ
        await redis.lrem("dlq_scheduled_posts", 0, post_id)
        
        # Reagendar
        await redis.set(f"scheduled_post:{post.id}", post.model_dump_json())
        await redis.zadd("all_scheduled_posts", {post.id: post.scheduled_time.timestamp()})
        
        logger.info(f"Post {post_id} removido da DLQ e reagendado")
        return True

    async def process_post(self, post: ScheduledPost) -> bool:
        """Processa e publica um post com suporte a retry."""
        redis = await self._get_redis()
        start_time = datetime.now(timezone.utc)
        
        # Atualizar status
        post.status = PostStatus.PROCESSING
        await redis.set(
            f"scheduled_post:{post.id}",
            post.model_dump_json()
        )
        
        try:
            result = await self._publish(post)
            
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.now(timezone.utc)
            post.result = result
            
            # Track success metrics
            if METRICS_AVAILABLE:
                track_post_published(post.platform.value, post.content_type)
                duration = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds()
                PUBLISH_DURATION.labels(
                    platform=post.platform.value
                ).observe(duration)
                await self._update_pending_metrics()
            
            # Send WebSocket notification
            if NOTIFICATIONS_AVAILABLE:
                await publish_notification(
                    notification_type=NotificationType.POST_PUBLISHED,
                    title="Post Publicado!",
                    message=f"Seu post foi publicado no {post.platform.value}",
                    user_id=post.user_id,
                    platform=post.platform.value,
                    data={
                        "post_id": post.id,
                        "result": result,
                    },
                )
            
            logger.info(
                f"Post {post.id} publicado com sucesso "
                f"em {post.platform.value}"
            )
            
            # Remover de todos os sets
            await redis.zrem("all_scheduled_posts", post.id)
            await redis.zrem("retry_scheduled_posts", post.id)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erro ao publicar post {post.id}: {error_msg}")
            
            # Tentar agendar retry
            retry_scheduled = await self._schedule_retry(post, error_msg)
            
            if not retry_scheduled:
                # Post foi para DLQ, não salvar novamente
                return False
        
        finally:
            # Salvar resultado final (se não foi para DLQ)
            if post.status != PostStatus.FAILED:
                await redis.set(
                    f"scheduled_post:{post.id}",
                    post.model_dump_json()
                )
        
        return post.status == PostStatus.PUBLISHED
    
    async def _publish(self, post: ScheduledPost) -> Dict[str, Any]:
        """Publica o post na plataforma apropriada."""
        if post.platform == Platform.INSTAGRAM:
            return await self._publish_instagram(post)
        elif post.platform == Platform.TIKTOK:
            return await self._publish_tiktok(post)
        elif post.platform == Platform.YOUTUBE:
            return await self._publish_youtube(post)
        elif post.platform == Platform.WHATSAPP:
            return await self._publish_whatsapp(post)
        else:
            raise ValueError(f"Plataforma não suportada: {post.platform}")
    
    async def _publish_instagram(self, post: ScheduledPost) -> Dict[str, Any]:
        """Publica no Instagram."""
        from vendor.instagram.client import (InstagramClient, InstagramConfig,
                                             PostConfig)
        
        config = InstagramConfig(
            username=post.account_name or "",
            password="",
            session_file=post.platform_config.get("session_file")
        )
        
        async with InstagramClient(config) as client:
            if not await client.login():
                raise Exception("Falha no login do Instagram")
            
            post_config = PostConfig(
                caption=post.caption,
                hashtags=post.hashtags
            )
            
            if post.content_type == "photo":
                return await client.upload_photo(
                    post.file_path, post_config
                )
            elif post.content_type == "video":
                return await client.upload_video(
                    post.file_path, post_config
                )
            elif post.content_type == "reel":
                return await client.upload_reel(
                    post.file_path, post_config
                )
            else:
                raise ValueError(
                    f"Tipo de conteúdo não suportado: {post.content_type}"
                )
    
    async def _publish_tiktok(self, post: ScheduledPost) -> Dict[str, Any]:
        """Publica no TikTok."""
        from vendor.tiktok.client import (TikTokClient, TikTokConfig,
                                          VideoConfig)
        
        config = TikTokConfig(
            cookies_file=post.platform_config.get("cookies_file", "")
        )
        
        client = TikTokClient(config)
        
        video_config = VideoConfig(
            caption=post.caption,
            hashtags=post.hashtags
        )
        
        result = await client.upload_video(post.file_path, video_config)
        
        return {
            "status": result.status.value,
            "video_id": result.video_id,
            "url": result.url
        }
    
    async def _publish_youtube(self, post: ScheduledPost) -> Dict[str, Any]:
        """Publica no YouTube."""
        from vendor.youtube.client import (PrivacyStatus, VideoMetadata,
                                           YouTubeClient, YouTubeConfig)
        
        config = YouTubeConfig(
            client_secrets_file=post.platform_config.get(
                "client_secrets_file", ""
            ),
            token_file=post.platform_config.get("token_file", "")
        )
        
        client = YouTubeClient(config)
        await client.authenticate()
        
        metadata = VideoMetadata(
            title=post.caption[:100],
            description=post.caption,
            tags=post.hashtags,
            privacy=PrivacyStatus.PUBLIC,
            is_short=post.content_type == "short"
        )
        
        result = await client.upload_video(post.file_path, metadata)
        
        return {
            "success": result.success,
            "video_id": result.video_id,
            "url": result.url
        }
    
    async def _publish_whatsapp(self, post: ScheduledPost) -> Dict[str, Any]:
        """Envia mensagem via WhatsApp."""
        from vendor.whatsapp.client import WhatsAppClient, WhatsAppConfig
        
        config = WhatsAppConfig(
            api_url=post.platform_config.get("api_url", ""),
            api_key=post.platform_config.get("api_key", ""),
            instance_name=post.account_name or ""
        )
        
        async with WhatsAppClient(config) as client:
            recipients = post.platform_config.get("recipients", [])
            results = []
            
            for phone in recipients:
                result = await client.send_text(phone, post.caption)
                results.append(result)
            
            return {"messages_sent": len(results), "results": results}
    
    async def _update_pending_metrics(self):
        """Atualiza métricas de posts pendentes."""
        if not METRICS_AVAILABLE:
            return
        
        redis = await self._get_redis()
        
        # Contar posts por plataforma
        platforms = ["instagram", "tiktok", "youtube", "whatsapp"]
        for platform in platforms:
            # Buscar todos os posts agendados
            post_ids = await redis.zrange("all_scheduled_posts", 0, -1)
            count = 0
            for pid in post_ids:
                data = await redis.get(f"scheduled_post:{pid}")
                if data:
                    post = ScheduledPost.model_validate_json(data)
                    if post.platform.value == platform:
                        count += 1
            PENDING_POSTS.labels(platform=platform).set(count)
    
    async def _update_dlq_metrics(self):
        """Atualiza métricas da DLQ."""
        if not METRICS_AVAILABLE:
            return
        
        redis = await self._get_redis()
        
        # Contar posts na DLQ por plataforma
        platforms = ["instagram", "tiktok", "youtube", "whatsapp"]
        post_ids = await redis.lrange("dlq_scheduled_posts", 0, -1)
        
        counts = {p: 0 for p in platforms}
        for pid in post_ids:
            data = await redis.get(f"scheduled_post:{pid}")
            if data:
                post = ScheduledPost.model_validate_json(data)
                if post.platform.value in counts:
                    counts[post.platform.value] += 1
        
        for platform, count in counts.items():
            DLQ_SIZE.labels(platform=platform).set(count)
    
    async def start_worker(self):
        """Inicia worker de processamento."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        
        # Track worker status
        if METRICS_AVAILABLE:
            WORKER_STATUS.labels(worker_name="post_scheduler").set(1)
        
        logger.info("Post Scheduler Worker iniciado")
    
    async def stop_worker(self):
        """Para worker de processamento."""
        self._running = False
        
        # Track worker status
        if METRICS_AVAILABLE:
            WORKER_STATUS.labels(worker_name="post_scheduler").set(0)
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Post Scheduler Worker parado")
    
    async def _worker_loop(self):
        """Loop principal do worker."""
        while self._running:
            try:
                # Track last run time
                if METRICS_AVAILABLE:
                    WORKER_LAST_RUN.labels(
                        worker_name="post_scheduler"
                    ).set(datetime.now(timezone.utc).timestamp())
                
                # Buscar posts pendentes
                posts = await self.get_pending_posts()
                
                for post in posts:
                    await self.process_post(post)
                
                # Update metrics after processing
                if METRICS_AVAILABLE:
                    await self._update_pending_metrics()
                    await self._update_dlq_metrics()
                
                # Aguardar antes da próxima verificação
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Erro no worker: {e}")
                await asyncio.sleep(60)


# Instância global
post_scheduler = PostSchedulerService()
