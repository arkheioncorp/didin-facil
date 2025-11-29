"""
Instagram Client Wrapper
========================
Wrapper para instagrapi - API não oficial do Instagram.

Repository: https://github.com/subzeroid/instagrapi
License: MIT

Este módulo fornece uma interface simplificada para:
- Upload de fotos, vídeos, reels e stories
- Gerenciamento de DMs
- Interações (like, comment, follow)
- Análise de perfis e posts
"""

from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import asyncio
from functools import partial

# instagrapi é síncrona, vamos wrappear com asyncio
try:
    from instagrapi import Client as InstaClient
    from instagrapi.types import StoryMention, StoryLink, StoryHashtag
    INSTAGRAPI_AVAILABLE = True
except ImportError:
    INSTAGRAPI_AVAILABLE = False
    InstaClient = None


class MediaType(Enum):
    PHOTO = "photo"
    VIDEO = "video"
    REEL = "reel"
    STORY = "story"
    CAROUSEL = "carousel"


@dataclass
class InstagramConfig:
    """Configuração para cliente Instagram."""
    username: str
    password: str
    session_file: Optional[str] = None
    proxy: Optional[str] = None
    # Delays para evitar rate limiting (em segundos)
    delay_range: tuple = (1, 3)
    # 2FA/Challenge handlers
    verification_code: Optional[str] = None  # Código 2FA se conhecido
    challenge_handler: Optional[callable] = None  # Callback para challenges
    

@dataclass 
class PostConfig:
    """Configuração para um post."""
    caption: str = ""
    hashtags: List[str] = field(default_factory=list)
    location: Optional[int] = None  # Location ID
    usertags: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def full_caption(self) -> str:
        """Retorna caption com hashtags."""
        if self.hashtags:
            tags = " ".join(f"#{tag.strip('#')}" for tag in self.hashtags)
            return f"{self.caption}\n\n{tags}"
        return self.caption


@dataclass
class StoryConfig:
    """Configuração para story."""
    mentions: List[str] = field(default_factory=list)  # Usernames
    hashtags: List[str] = field(default_factory=list)
    location: Optional[int] = None
    link: Optional[str] = None
    link_text: Optional[str] = None


class InstagramClient:
    """
    Cliente assíncrono para Instagram.
    
    Uso:
        config = InstagramConfig(
            username="didin_facil",
            password="senha",
            session_file="./sessions/instagram.json"
        )
        
        async with InstagramClient(config) as client:
            # Upload de foto
            await client.upload_photo(
                "/path/to/photo.jpg",
                PostConfig(caption="Confira as ofertas!", hashtags=["ofertas", "promoção"])
            )
            
            # Upload de reel
            await client.upload_reel(
                "/path/to/video.mp4",
                PostConfig(caption="Novo reel!")
            )
    """
    
    def __init__(self, config: InstagramConfig):
        if not INSTAGRAPI_AVAILABLE:
            raise ImportError(
                "instagrapi não está instalado. "
                "Execute: pip install instagrapi"
            )
        
        self.config = config
        self._client: Optional[InstaClient] = None
        self._logged_in = False
        self._challenge_pending = False
        self._challenge_type = None
    
    async def _run_sync(self, func, *args, **kwargs):
        """Executa função síncrona em thread separada."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(func, *args, **kwargs)
        )
    
    def _setup_challenge_handlers(self):
        """Configura handlers para challenges do Instagram."""
        if self._client is None:
            return
        
        # Handler para 2FA via código
        def totp_code_handler(username: str) -> str:
            """Retorna código 2FA se disponível."""
            if self.config.verification_code:
                return self.config.verification_code
            raise Exception("CHALLENGE_2FA_REQUIRED")
        
        # Handler para challenge genérico (verificação de segurança)
        def challenge_code_handler(username: str, choice: int) -> str:
            """
            Handler para challenge de verificação.
            
            Args:
                username: Username da conta
                choice: 0 = SMS, 1 = Email
            """
            if self.config.verification_code:
                return self.config.verification_code
            
            # Registra que há um challenge pendente
            self._challenge_pending = True
            self._challenge_type = "sms" if choice == 0 else "email"
            raise Exception(f"CHALLENGE_{self._challenge_type.upper()}_REQUIRED")
        
        # Configurar handlers no cliente
        self._client.challenge_code_handler = challenge_code_handler
        self._client.totp_code_handler = totp_code_handler
    
    async def login(self) -> bool:
        """
        Realiza login no Instagram.
        
        Tenta usar sessão salva primeiro, depois faz login normal.
        Suporta 2FA e challenges de verificação.
        
        Raises:
            Exception: CHALLENGE_2FA_REQUIRED, CHALLENGE_SMS_REQUIRED, 
                      CHALLENGE_EMAIL_REQUIRED se verificação necessária
        """
        self._client = InstaClient()
        self._setup_challenge_handlers()
        
        if self.config.proxy:
            self._client.set_proxy(self.config.proxy)
        
        # Tentar carregar sessão
        if self.config.session_file:
            session_path = Path(self.config.session_file)
            if session_path.exists():
                try:
                    await self._run_sync(
                        self._client.load_settings,
                        session_path
                    )
                    await self._run_sync(
                        self._client.login,
                        self.config.username,
                        self.config.password
                    )
                    self._logged_in = True
                    return True
                except Exception:
                    pass  # Sessão inválida, fazer login normal
        
        # Login normal
        await self._run_sync(
            self._client.login,
            self.config.username,
            self.config.password
        )
        
        # Salvar sessão
        if self.config.session_file:
            session_path = Path(self.config.session_file)
            session_path.parent.mkdir(parents=True, exist_ok=True)
            await self._run_sync(
                self._client.dump_settings,
                session_path
            )
        
        self._logged_in = True
        return True
    
    async def get_challenge_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre challenge pendente.
        
        Use quando login retornar CHALLENGE_*_REQUIRED.
        """
        return {
            "pending": self._challenge_pending,
            "type": self._challenge_type,
            "username": self.config.username
        }
    
    async def resolve_challenge(self, code: str) -> bool:
        """
        Resolve challenge com código de verificação.
        
        Args:
            code: Código recebido por SMS/Email/2FA
            
        Returns:
            True se challenge resolvido com sucesso
        """
        if not self._client:
            raise RuntimeError("Cliente não inicializado")
        
        try:
            # Atualizar config com código
            self.config.verification_code = code
            self._setup_challenge_handlers()
            
            # Tentar login novamente
            await self._run_sync(
                self._client.login,
                self.config.username,
                self.config.password
            )
            
            self._logged_in = True
            self._challenge_pending = False
            self._challenge_type = None
            
            # Salvar sessão após resolver challenge
            if self.config.session_file:
                session_path = Path(self.config.session_file)
                session_path.parent.mkdir(parents=True, exist_ok=True)
                await self._run_sync(
                    self._client.dump_settings,
                    session_path
                )
            
            return True
            
        except Exception as e:
            if "CHALLENGE" in str(e):
                raise  # Ainda precisa de verificação
            raise
    
    async def request_challenge_code(self, method: str = "email") -> bool:
        """
        Solicita envio de código de verificação.
        
        Args:
            method: "sms" ou "email"
            
        Returns:
            True se código foi enviado
        """
        if not self._client:
            raise RuntimeError("Cliente não inicializado")
        
        try:
            choice = 0 if method == "sms" else 1
            await self._run_sync(
                self._client.challenge_resolve,
                choice
            )
            return True
        except Exception:
            return False
    
    async def get_settings(self) -> Dict[str, Any]:
        """Retorna configurações/sessão do cliente."""
        if not self._client:
            return {}
        
        try:
            settings = self._client.get_settings()
            return settings
        except Exception:
            return {}
    
    async def load_settings(self, settings: Dict[str, Any]) -> bool:
        """Carrega configurações/sessão no cliente."""
        if not self._client:
            self._client = InstaClient()
            self._setup_challenge_handlers()
        
        try:
            self._client.set_settings(settings)
            self._logged_in = True
            return True
        except Exception:
            return False
    
    async def logout(self):
        """Realiza logout."""
        if self._client and self._logged_in:
            await self._run_sync(self._client.logout)
            self._logged_in = False
    
    async def __aenter__(self):
        await self.login()
        return self
    
    async def __aexit__(self, *args):
        await self.logout()
    
    def _ensure_logged_in(self):
        if not self._logged_in:
            raise RuntimeError("Não está logado. Use 'await client.login()' primeiro.")
    
    # ==================== Upload ====================
    
    async def upload_photo(
        self,
        photo_path: Union[str, Path],
        config: PostConfig
    ) -> Dict[str, Any]:
        """
        Upload de foto no feed.
        
        Args:
            photo_path: Caminho para a imagem
            config: Configurações do post
            
        Returns:
            Dados da mídia criada
        """
        self._ensure_logged_in()
        
        kwargs = {
            "path": str(photo_path),
            "caption": config.full_caption,
        }
        
        if config.location:
            location = await self._run_sync(
                self._client.location_info,
                config.location
            )
            kwargs["location"] = location
        
        if config.usertags:
            kwargs["usertags"] = config.usertags
        
        media = await self._run_sync(
            self._client.photo_upload,
            **kwargs
        )
        
        return self._media_to_dict(media)
    
    async def upload_video(
        self,
        video_path: Union[str, Path],
        config: PostConfig,
        thumbnail_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """Upload de vídeo no feed."""
        self._ensure_logged_in()
        
        kwargs = {
            "path": str(video_path),
            "caption": config.full_caption,
        }
        
        if thumbnail_path:
            kwargs["thumbnail"] = str(thumbnail_path)
        
        if config.location:
            location = await self._run_sync(
                self._client.location_info,
                config.location
            )
            kwargs["location"] = location
        
        media = await self._run_sync(
            self._client.video_upload,
            **kwargs
        )
        
        return self._media_to_dict(media)
    
    async def upload_reel(
        self,
        video_path: Union[str, Path],
        config: PostConfig,
        thumbnail_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Upload de Reel.
        
        Args:
            video_path: Caminho para o vídeo (max 90 segundos, formato 9:16)
            config: Configurações do post
            thumbnail_path: Thumbnail opcional
        """
        self._ensure_logged_in()
        
        kwargs = {
            "path": str(video_path),
            "caption": config.full_caption,
        }
        
        if thumbnail_path:
            kwargs["thumbnail"] = str(thumbnail_path)
        
        media = await self._run_sync(
            self._client.clip_upload,
            **kwargs
        )
        
        return self._media_to_dict(media)
    
    async def upload_story_photo(
        self,
        photo_path: Union[str, Path],
        config: Optional[StoryConfig] = None
    ) -> Dict[str, Any]:
        """Upload de foto nos stories."""
        self._ensure_logged_in()
        config = config or StoryConfig()
        
        kwargs = {"path": str(photo_path)}
        
        # Adicionar mentions
        if config.mentions:
            mentions = []
            for username in config.mentions:
                user = await self._run_sync(
                    self._client.user_info_by_username,
                    username
                )
                mentions.append(StoryMention(user=user, x=0.5, y=0.5))
            kwargs["mentions"] = mentions
        
        # Adicionar hashtags
        if config.hashtags:
            hashtags = [
                StoryHashtag(hashtag=tag, x=0.5, y=0.7)
                for tag in config.hashtags
            ]
            kwargs["hashtags"] = hashtags
        
        # Adicionar link
        if config.link:
            kwargs["links"] = [StoryLink(
                webUri=config.link,
                text=config.link_text or "Saiba mais"
            )]
        
        story = await self._run_sync(
            self._client.photo_upload_to_story,
            **kwargs
        )
        
        return self._story_to_dict(story)
    
    async def upload_story_video(
        self,
        video_path: Union[str, Path],
        config: Optional[StoryConfig] = None
    ) -> Dict[str, Any]:
        """Upload de vídeo nos stories."""
        self._ensure_logged_in()
        config = config or StoryConfig()
        
        kwargs = {"path": str(video_path)}
        
        if config.mentions:
            mentions = []
            for username in config.mentions:
                user = await self._run_sync(
                    self._client.user_info_by_username,
                    username
                )
                mentions.append(StoryMention(user=user, x=0.5, y=0.5))
            kwargs["mentions"] = mentions
        
        if config.link:
            kwargs["links"] = [StoryLink(
                webUri=config.link,
                text=config.link_text or "Saiba mais"
            )]
        
        story = await self._run_sync(
            self._client.video_upload_to_story,
            **kwargs
        )
        
        return self._story_to_dict(story)
    
    async def upload_carousel(
        self,
        media_paths: List[Union[str, Path]],
        config: PostConfig
    ) -> Dict[str, Any]:
        """
        Upload de carrossel (múltiplas fotos/vídeos).
        
        Args:
            media_paths: Lista de caminhos para fotos/vídeos
            config: Configurações do post
        """
        self._ensure_logged_in()
        
        paths = [str(p) for p in media_paths]
        
        media = await self._run_sync(
            self._client.album_upload,
            paths,
            config.full_caption
        )
        
        return self._media_to_dict(media)
    
    # ==================== Direct Messages ====================
    
    async def send_direct_message(
        self,
        user_ids: List[int],
        text: str
    ) -> Dict[str, Any]:
        """
        Envia mensagem direta.
        
        Args:
            user_ids: Lista de IDs dos usuários
            text: Texto da mensagem
        """
        self._ensure_logged_in()
        
        thread = await self._run_sync(
            self._client.direct_send,
            text,
            user_ids
        )
        
        return {"thread_id": thread.id if hasattr(thread, 'id') else str(thread)}
    
    async def send_direct_photo(
        self,
        user_ids: List[int],
        photo_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """Envia foto via DM."""
        self._ensure_logged_in()
        
        result = await self._run_sync(
            self._client.direct_send_photo,
            str(photo_path),
            user_ids
        )
        
        return {"success": True, "result": str(result)}
    
    async def send_direct_video(
        self,
        user_ids: List[int],
        video_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """Envia vídeo via DM."""
        self._ensure_logged_in()
        
        result = await self._run_sync(
            self._client.direct_send_video,
            str(video_path),
            user_ids
        )
        
        return {"success": True, "result": str(result)}
    
    async def get_direct_threads(self, amount: int = 20) -> List[Dict[str, Any]]:
        """Lista conversas do Direct."""
        self._ensure_logged_in()
        
        threads = await self._run_sync(
            self._client.direct_threads,
            amount
        )
        
        return [self._thread_to_dict(t) for t in threads]
    
    # ==================== Interactions ====================
    
    async def like_media(self, media_id: str) -> bool:
        """Curte uma mídia."""
        self._ensure_logged_in()
        return await self._run_sync(self._client.media_like, media_id)
    
    async def unlike_media(self, media_id: str) -> bool:
        """Remove curtida de uma mídia."""
        self._ensure_logged_in()
        return await self._run_sync(self._client.media_unlike, media_id)
    
    async def comment_media(self, media_id: str, text: str) -> Dict[str, Any]:
        """Comenta em uma mídia."""
        self._ensure_logged_in()
        
        comment = await self._run_sync(
            self._client.media_comment,
            media_id,
            text
        )
        
        return self._comment_to_dict(comment)
    
    async def follow_user(self, user_id: int) -> bool:
        """Segue um usuário."""
        self._ensure_logged_in()
        return await self._run_sync(self._client.user_follow, user_id)
    
    async def unfollow_user(self, user_id: int) -> bool:
        """Deixa de seguir um usuário."""
        self._ensure_logged_in()
        return await self._run_sync(self._client.user_unfollow, user_id)
    
    # ==================== User Info ====================
    
    async def get_user_id(self, username: str) -> int:
        """Obtém ID do usuário pelo username."""
        self._ensure_logged_in()
        return await self._run_sync(
            self._client.user_id_from_username,
            username
        )
    
    async def get_user_info(self, user_id: int) -> Dict[str, Any]:
        """Obtém informações do usuário."""
        self._ensure_logged_in()
        
        user = await self._run_sync(
            self._client.user_info,
            user_id
        )
        
        return self._user_to_dict(user)
    
    async def get_user_medias(
        self,
        user_id: int,
        amount: int = 20
    ) -> List[Dict[str, Any]]:
        """Lista mídias de um usuário."""
        self._ensure_logged_in()
        
        medias = await self._run_sync(
            self._client.user_medias,
            user_id,
            amount
        )
        
        return [self._media_to_dict(m) for m in medias]
    
    async def get_user_followers(
        self,
        user_id: int,
        amount: int = 100
    ) -> List[Dict[str, Any]]:
        """Lista seguidores de um usuário."""
        self._ensure_logged_in()
        
        followers = await self._run_sync(
            self._client.user_followers,
            user_id,
            amount=amount
        )
        
        return [self._user_to_dict(u) for u in followers.values()]
    
    async def get_user_following(
        self,
        user_id: int,
        amount: int = 100
    ) -> List[Dict[str, Any]]:
        """Lista quem o usuário segue."""
        self._ensure_logged_in()
        
        following = await self._run_sync(
            self._client.user_following,
            user_id,
            amount=amount
        )
        
        return [self._user_to_dict(u) for u in following.values()]
    
    # ==================== Hashtag & Location ====================
    
    async def search_hashtag(
        self,
        hashtag: str,
        amount: int = 20
    ) -> List[Dict[str, Any]]:
        """Busca mídias por hashtag."""
        self._ensure_logged_in()
        
        medias = await self._run_sync(
            self._client.hashtag_medias_recent,
            hashtag,
            amount
        )
        
        return [self._media_to_dict(m) for m in medias]
    
    async def search_location(
        self,
        latitude: float,
        longitude: float
    ) -> List[Dict[str, Any]]:
        """Busca locais próximos."""
        self._ensure_logged_in()
        
        locations = await self._run_sync(
            self._client.location_search,
            latitude,
            longitude
        )
        
        return [{"pk": loc.pk, "name": loc.name} for loc in locations]
    
    # ==================== Helper Methods ====================
    
    def _media_to_dict(self, media) -> Dict[str, Any]:
        """Converte Media para dict."""
        return {
            "id": media.id if hasattr(media, 'id') else str(media.pk),
            "pk": str(media.pk),
            "code": media.code,
            "media_type": media.media_type,
            "caption": media.caption_text if hasattr(media, 'caption_text') else "",
            "like_count": media.like_count,
            "comment_count": media.comment_count,
            "taken_at": str(media.taken_at) if media.taken_at else None,
            "thumbnail_url": str(media.thumbnail_url) if media.thumbnail_url else None,
            "url": f"https://instagram.com/p/{media.code}/"
        }
    
    def _story_to_dict(self, story) -> Dict[str, Any]:
        """Converte Story para dict."""
        return {
            "id": str(story.id) if hasattr(story, 'id') else str(story.pk),
            "pk": str(story.pk),
            "media_type": story.media_type,
            "taken_at": str(story.taken_at) if story.taken_at else None,
        }
    
    def _user_to_dict(self, user) -> Dict[str, Any]:
        """Converte User para dict."""
        return {
            "pk": str(user.pk),
            "username": user.username,
            "full_name": user.full_name,
            "is_private": user.is_private,
            "is_verified": user.is_verified,
            "follower_count": getattr(user, 'follower_count', 0),
            "following_count": getattr(user, 'following_count', 0),
            "media_count": getattr(user, 'media_count', 0),
            "biography": getattr(user, 'biography', ''),
            "profile_pic_url": str(user.profile_pic_url) if user.profile_pic_url else None
        }
    
    def _comment_to_dict(self, comment) -> Dict[str, Any]:
        """Converte Comment para dict."""
        return {
            "pk": str(comment.pk),
            "text": comment.text,
            "created_at": str(comment.created_at) if comment.created_at else None,
            "user": self._user_to_dict(comment.user) if comment.user else None
        }
    
    def _thread_to_dict(self, thread) -> Dict[str, Any]:
        """Converte DirectThread para dict."""
        return {
            "id": thread.id,
            "users": [self._user_to_dict(u) for u in thread.users],
            "is_group": thread.is_group,
            "thread_title": thread.thread_title,
            "last_activity_at": str(thread.last_activity_at) if thread.last_activity_at else None
        }


# ==================== Scheduler ====================

@dataclass
class ScheduledPost:
    """Post agendado."""
    media_path: Union[str, Path]
    media_type: MediaType
    config: PostConfig
    scheduled_time: str  # ISO format
    extra_media: Optional[List[Union[str, Path]]] = None  # Para carrossel


class InstagramScheduler:
    """
    Agendador de posts para Instagram.
    
    Uso:
        scheduler = InstagramScheduler(client)
        
        # Agendar post
        scheduler.schedule(ScheduledPost(
            media_path="/path/to/video.mp4",
            media_type=MediaType.REEL,
            config=PostConfig(caption="Novo reel!"),
            scheduled_time="2024-12-01T10:00:00"
        ))
        
        # Processar fila (rodar periodicamente)
        await scheduler.process_queue()
    """
    
    def __init__(self, client: InstagramClient):
        self.client = client
        self._queue: List[ScheduledPost] = []
    
    def schedule(self, post: ScheduledPost):
        """Adiciona post à fila."""
        self._queue.append(post)
        self._queue.sort(key=lambda p: p.scheduled_time)
    
    async def process_queue(self) -> List[Dict[str, Any]]:
        """
        Processa posts prontos para publicar.
        
        Retorna lista de posts publicados.
        """
        from datetime import datetime
        
        now = datetime.now().isoformat()
        results = []
        
        while self._queue and self._queue[0].scheduled_time <= now:
            post = self._queue.pop(0)
            
            try:
                if post.media_type == MediaType.PHOTO:
                    result = await self.client.upload_photo(
                        post.media_path, post.config
                    )
                elif post.media_type == MediaType.VIDEO:
                    result = await self.client.upload_video(
                        post.media_path, post.config
                    )
                elif post.media_type == MediaType.REEL:
                    result = await self.client.upload_reel(
                        post.media_path, post.config
                    )
                elif post.media_type == MediaType.STORY:
                    # Detectar tipo de mídia
                    path = Path(post.media_path)
                    if path.suffix.lower() in ['.mp4', '.mov', '.avi']:
                        result = await self.client.upload_story_video(
                            post.media_path
                        )
                    else:
                        result = await self.client.upload_story_photo(
                            post.media_path
                        )
                elif post.media_type == MediaType.CAROUSEL:
                    paths = [post.media_path] + (post.extra_media or [])
                    result = await self.client.upload_carousel(
                        paths, post.config
                    )
                else:
                    continue
                
                results.append({
                    "status": "success",
                    "scheduled_time": post.scheduled_time,
                    "result": result
                })
                
            except Exception as e:
                results.append({
                    "status": "error",
                    "scheduled_time": post.scheduled_time,
                    "error": str(e)
                })
        
        return results
    
    def get_pending(self) -> List[ScheduledPost]:
        """Retorna posts pendentes."""
        return list(self._queue)
    
    def cancel(self, scheduled_time: str) -> bool:
        """Cancela um post agendado."""
        for i, post in enumerate(self._queue):
            if post.scheduled_time == scheduled_time:
                self._queue.pop(i)
                return True
        return False
