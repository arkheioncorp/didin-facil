"""
Unified Social Media Manager
============================
Interface unificada para gerenciar todas as redes sociais.

Este módulo permite publicar conteúdo em múltiplas plataformas
simultaneamente com uma única interface.
"""

from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from enum import Enum
import asyncio
import logging

from .whatsapp.client import WhatsAppClient, WhatsAppConfig
from .instagram.client import (
    InstagramClient, InstagramConfig, 
    PostConfig as IGPostConfig
)
from .tiktok.client import (
    TikTokClient, TikTokConfig,
    VideoConfig as TikTokVideoConfig
)

logger = logging.getLogger(__name__)


class Platform(Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    WHATSAPP = "whatsapp"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"


class ContentType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    REEL = "reel"
    STORY = "story"
    CAROUSEL = "carousel"
    TEXT = "text"


@dataclass
class SocialMediaConfig:
    """Configuração consolidada para todas as plataformas."""
    
    # Instagram
    instagram_username: Optional[str] = None
    instagram_password: Optional[str] = None
    instagram_session_file: Optional[str] = None
    
    # TikTok
    tiktok_cookies_file: Optional[str] = None
    tiktok_headless: bool = True
    
    # WhatsApp
    whatsapp_api_url: Optional[str] = None
    whatsapp_api_key: Optional[str] = None
    whatsapp_instance: Optional[str] = None


@dataclass
class UnifiedPost:
    """Post unificado para múltiplas plataformas."""
    content_type: ContentType
    media_paths: List[Union[str, Path]]
    caption: str = ""
    hashtags: List[str] = field(default_factory=list)
    platforms: List[Platform] = field(default_factory=list)
    schedule_time: Optional[datetime] = None
    
    # Configurações específicas por plataforma
    instagram_location: Optional[int] = None
    tiktok_sound: Optional[str] = None
    whatsapp_recipients: List[str] = field(default_factory=list)


@dataclass
class PostResult:
    """Resultado de publicação."""
    platform: Platform
    success: bool
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


class SocialMediaManager:
    """
    Gerenciador unificado de redes sociais.
    
    Uso:
        config = SocialMediaConfig(
            instagram_username="tiktrend_facil",
            instagram_password="senha",
            tiktok_cookies_file="./sessions/tiktok.json",
            whatsapp_api_url="http://localhost:8080",
            whatsapp_api_key="api-key"
        )
        
        manager = SocialMediaManager(config)
        await manager.initialize()
        
        # Publicar em múltiplas plataformas
        results = await manager.publish(UnifiedPost(
            content_type=ContentType.REEL,
            media_paths=["/path/to/video.mp4"],
            caption="Confira essa oferta incrível!",
            hashtags=["ofertas", "promoção"],
            platforms=[Platform.INSTAGRAM, Platform.TIKTOK]
        ))
    """
    
    def __init__(self, config: SocialMediaConfig):
        self.config = config
        self._clients: Dict[Platform, Any] = {}
        self._initialized = False
    
    async def initialize(self, platforms: Optional[List[Platform]] = None):
        """
        Inicializa clientes para as plataformas configuradas.
        
        Args:
            platforms: Lista de plataformas para inicializar (default: todas configuradas)
        """
        if platforms is None:
            platforms = []
            
            if self.config.instagram_username:
                platforms.append(Platform.INSTAGRAM)
            if self.config.tiktok_cookies_file:
                platforms.append(Platform.TIKTOK)
            if self.config.whatsapp_api_url:
                platforms.append(Platform.WHATSAPP)
        
        for platform in platforms:
            await self._init_platform(platform)
        
        self._initialized = True
        logger.info(f"Plataformas inicializadas: {[p.value for p in self._clients.keys()]}")
    
    async def _init_platform(self, platform: Platform):
        """Inicializa cliente de uma plataforma específica."""
        
        if platform == Platform.INSTAGRAM:
            if not self.config.instagram_username:
                raise ValueError("Instagram não configurado")
            
            client = InstagramClient(InstagramConfig(
                username=self.config.instagram_username,
                password=self.config.instagram_password,
                session_file=self.config.instagram_session_file
            ))
            await client.login()
            self._clients[platform] = client
            
        elif platform == Platform.TIKTOK:
            if not self.config.tiktok_cookies_file:
                raise ValueError("TikTok não configurado")
            
            self._clients[platform] = TikTokClient(TikTokConfig(
                cookies_file=self.config.tiktok_cookies_file,
                headless=self.config.tiktok_headless
            ))
            
        elif platform == Platform.WHATSAPP:
            if not self.config.whatsapp_api_url:
                raise ValueError("WhatsApp não configurado")
            
            self._clients[platform] = WhatsAppClient(WhatsAppConfig(
                api_url=self.config.whatsapp_api_url,
                api_key=self.config.whatsapp_api_key,
                instance_name=self.config.whatsapp_instance or "default"
            ))
    
    async def close(self):
        """Fecha todos os clientes."""
        for platform, client in self._clients.items():
            try:
                if hasattr(client, 'logout'):
                    await client.logout()
                elif hasattr(client, 'close'):
                    await client.close()
            except Exception as e:
                logger.error(f"Erro ao fechar {platform.value}: {e}")
        
        self._clients.clear()
        self._initialized = False
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    # ==================== Publishing ====================
    
    async def publish(self, post: UnifiedPost) -> List[PostResult]:
        """
        Publica conteúdo em múltiplas plataformas.
        
        Args:
            post: Post unificado com configurações
            
        Returns:
            Lista de resultados por plataforma
        """
        if not self._initialized:
            raise RuntimeError("Manager não inicializado. Use 'await manager.initialize()'")
        
        results = []
        
        # Publicar em paralelo
        tasks = []
        for platform in post.platforms:
            if platform in self._clients:
                tasks.append(self._publish_to_platform(platform, post))
            else:
                results.append(PostResult(
                    platform=platform,
                    success=False,
                    error=f"Plataforma {platform.value} não inicializada"
                ))
        
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(task_results):
                if isinstance(result, Exception):
                    results.append(PostResult(
                        platform=post.platforms[i],
                        success=False,
                        error=str(result)
                    ))
                else:
                    results.append(result)
        
        return results
    
    async def _publish_to_platform(
        self,
        platform: Platform,
        post: UnifiedPost
    ) -> PostResult:
        """Publica em uma plataforma específica."""
        
        try:
            if platform == Platform.INSTAGRAM:
                return await self._publish_instagram(post)
            elif platform == Platform.TIKTOK:
                return await self._publish_tiktok(post)
            elif platform == Platform.WHATSAPP:
                return await self._publish_whatsapp(post)
            else:
                return PostResult(
                    platform=platform,
                    success=False,
                    error="Plataforma não suportada"
                )
        except Exception as e:
            logger.error(f"Erro ao publicar em {platform.value}: {e}")
            return PostResult(
                platform=platform,
                success=False,
                error=str(e)
            )
    
    async def _publish_instagram(self, post: UnifiedPost) -> PostResult:
        """Publica no Instagram."""
        client: InstagramClient = self._clients[Platform.INSTAGRAM]
        
        config = IGPostConfig(
            caption=post.caption,
            hashtags=post.hashtags,
            location=post.instagram_location
        )
        
        if post.content_type == ContentType.IMAGE:
            result = await client.upload_photo(post.media_paths[0], config)
            
        elif post.content_type == ContentType.VIDEO:
            result = await client.upload_video(post.media_paths[0], config)
            
        elif post.content_type == ContentType.REEL:
            result = await client.upload_reel(post.media_paths[0], config)
            
        elif post.content_type == ContentType.STORY:
            path = Path(post.media_paths[0])
            if path.suffix.lower() in ['.mp4', '.mov']:
                result = await client.upload_story_video(path)
            else:
                result = await client.upload_story_photo(path)
                
        elif post.content_type == ContentType.CAROUSEL:
            result = await client.upload_carousel(post.media_paths, config)
            
        else:
            return PostResult(
                platform=Platform.INSTAGRAM,
                success=False,
                error="Tipo de conteúdo não suportado"
            )
        
        return PostResult(
            platform=Platform.INSTAGRAM,
            success=True,
            post_id=result.get('id'),
            url=result.get('url')
        )
    
    async def _publish_tiktok(self, post: UnifiedPost) -> PostResult:
        """Publica no TikTok."""
        client: TikTokClient = self._clients[Platform.TIKTOK]
        
        # TikTok só suporta vídeos
        if post.content_type not in [ContentType.VIDEO, ContentType.REEL]:
            return PostResult(
                platform=Platform.TIKTOK,
                success=False,
                error="TikTok só suporta vídeos"
            )
        
        config = TikTokVideoConfig(
            caption=post.caption,
            hashtags=post.hashtags,
            sound=post.tiktok_sound,
            schedule_time=post.schedule_time
        )
        
        result = await client.upload_video(post.media_paths[0], config)
        
        return PostResult(
            platform=Platform.TIKTOK,
            success=result.status.value in ['published', 'scheduled'],
            post_id=result.video_id,
            url=result.url,
            error=result.error
        )
    
    async def _publish_whatsapp(self, post: UnifiedPost) -> PostResult:
        """Envia conteúdo via WhatsApp."""
        client: WhatsAppClient = self._clients[Platform.WHATSAPP]
        
        if not post.whatsapp_recipients:
            return PostResult(
                platform=Platform.WHATSAPP,
                success=False,
                error="Nenhum destinatário especificado"
            )
        
        success_count = 0
        errors = []
        
        for recipient in post.whatsapp_recipients:
            try:
                if post.content_type == ContentType.TEXT:
                    await client.send_text(recipient, post.caption)
                    
                elif post.content_type == ContentType.IMAGE:
                    await client.send_image(
                        recipient,
                        str(post.media_paths[0]),
                        caption=post.caption
                    )
                    
                elif post.content_type in [ContentType.VIDEO, ContentType.REEL]:
                    await client.send_video(
                        recipient,
                        str(post.media_paths[0]),
                        caption=post.caption
                    )
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"{recipient}: {e}")
        
        return PostResult(
            platform=Platform.WHATSAPP,
            success=success_count > 0,
            error="; ".join(errors) if errors else None
        )
    
    # ==================== Analytics ====================
    
    async def get_instagram_stats(self, post_id: str) -> Dict[str, Any]:
        """Obtém estatísticas de um post do Instagram."""
        if Platform.INSTAGRAM not in self._clients:
            raise ValueError("Instagram não inicializado")
        
        self._clients[Platform.INSTAGRAM]
        # instagrapi não tem método direto para isso, seria necessário
        # usar a API oficial com token de business
        
        return {"error": "Estatísticas requerem API Business"}
    
    # ==================== Helpers ====================
    
    def get_initialized_platforms(self) -> List[Platform]:
        """Retorna lista de plataformas inicializadas."""
        return list(self._clients.keys())
    
    async def test_connections(self) -> Dict[Platform, bool]:
        """Testa conexão com cada plataforma."""
        results = {}
        
        for platform, client in self._clients.items():
            try:
                if platform == Platform.INSTAGRAM:
                    # Tentar obter info do próprio usuário
                    user_id = await client.get_user_id(
                        self.config.instagram_username
                    )
                    results[platform] = user_id is not None
                    
                elif platform == Platform.WHATSAPP:
                    status = await client.get_instance_status()
                    results[platform] = status.get('state') == 'open'
                    
                elif platform == Platform.TIKTOK:
                    # TikTok não tem método de teste simples
                    results[platform] = True
                    
            except Exception as e:
                logger.error(f"Teste de {platform.value} falhou: {e}")
                results[platform] = False
        
        return results


# ==================== Scheduler ====================

@dataclass
class ScheduledUnifiedPost:
    """Post agendado."""
    post: UnifiedPost
    scheduled_time: datetime
    id: Optional[str] = None


class UnifiedScheduler:
    """
    Agendador unificado para todas as plataformas.
    
    Uso:
        scheduler = UnifiedScheduler(manager)
        
        # Agendar post
        scheduler.schedule(UnifiedPost(
            content_type=ContentType.REEL,
            media_paths=["/path/to/video.mp4"],
            caption="Post agendado!",
            platforms=[Platform.INSTAGRAM, Platform.TIKTOK]
        ), scheduled_time=datetime(2024, 12, 1, 10, 0))
        
        # Processar fila (rodar periodicamente)
        results = await scheduler.process_queue()
    """
    
    def __init__(self, manager: SocialMediaManager):
        self.manager = manager
        self._queue: List[ScheduledUnifiedPost] = []
        self._id_counter = 0
    
    def schedule(
        self,
        post: UnifiedPost,
        scheduled_time: datetime
    ) -> str:
        """Agenda um post e retorna o ID."""
        self._id_counter += 1
        post_id = f"scheduled_{self._id_counter}"
        
        self._queue.append(ScheduledUnifiedPost(
            post=post,
            scheduled_time=scheduled_time,
            id=post_id
        ))
        
        # Ordenar por horário
        self._queue.sort(key=lambda p: p.scheduled_time)
        
        return post_id
    
    async def process_queue(self) -> List[Dict[str, Any]]:
        """Processa posts prontos para publicar."""
        now = datetime.now()
        results = []
        
        while self._queue and self._queue[0].scheduled_time <= now:
            scheduled = self._queue.pop(0)
            
            post_results = await self.manager.publish(scheduled.post)
            
            results.append({
                "id": scheduled.id,
                "scheduled_time": scheduled.scheduled_time.isoformat(),
                "results": [
                    {
                        "platform": r.platform.value,
                        "success": r.success,
                        "post_id": r.post_id,
                        "url": r.url,
                        "error": r.error
                    }
                    for r in post_results
                ]
            })
        
        return results
    
    def get_pending(self) -> List[ScheduledUnifiedPost]:
        """Retorna posts pendentes."""
        return list(self._queue)
    
    def cancel(self, post_id: str) -> bool:
        """Cancela um post agendado."""
        for i, scheduled in enumerate(self._queue):
            if scheduled.id == post_id:
                self._queue.pop(i)
                return True
        return False
    
    def reschedule(self, post_id: str, new_time: datetime) -> bool:
        """Reagenda um post."""
        for scheduled in self._queue:
            if scheduled.id == post_id:
                scheduled.scheduled_time = new_time
                self._queue.sort(key=lambda p: p.scheduled_time)
                return True
        return False
