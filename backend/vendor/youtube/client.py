"""
YouTube Uploader Module
========================
Upload automatizado de vídeos para YouTube.

Este módulo usa a API oficial do YouTube (OAuth2) para:
- Upload de vídeos (Shorts, Longform)
- Atualização de metadados
- Agendamento de publicação
- Gerenciamento de playlists
"""

from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from enum import Enum
import asyncio
from functools import partial
import logging

logger = logging.getLogger(__name__)

# Google API
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


class PrivacyStatus(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


class Category(Enum):
    """Categorias do YouTube."""
    FILM_ANIMATION = "1"
    AUTOS_VEHICLES = "2"
    MUSIC = "10"
    PETS_ANIMALS = "15"
    SPORTS = "17"
    GAMING = "20"
    VLOGS = "22"
    COMEDY = "23"
    ENTERTAINMENT = "24"
    NEWS = "25"
    HOWTO_STYLE = "26"
    EDUCATION = "27"
    SCIENCE_TECH = "28"
    NONPROFITS = "29"


@dataclass
class YouTubeConfig:
    """Configuração do cliente YouTube."""
    client_secrets_file: str  # credentials.json do Google Cloud
    token_file: str = "youtube_token.json"
    scopes: List[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.force-ssl"
    ])


@dataclass
class VideoMetadata:
    """Metadados do vídeo."""
    title: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    category: Category = Category.HOWTO_STYLE
    privacy: PrivacyStatus = PrivacyStatus.PRIVATE
    publish_at: Optional[datetime] = None  # Para agendamento
    made_for_kids: bool = False
    playlist_id: Optional[str] = None
    
    # Shorts específico
    is_short: bool = False
    
    # Thumbnail
    thumbnail_path: Optional[str] = None


@dataclass
class UploadResult:
    """Resultado do upload."""
    success: bool
    video_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


class YouTubeClient:
    """
    Cliente para YouTube Data API.
    
    Uso:
        config = YouTubeConfig(
            client_secrets_file="./credentials.json",
            token_file="./sessions/youtube_token.json"
        )
        
        client = YouTubeClient(config)
        await client.authenticate()
        
        result = await client.upload_video(
            "/path/to/video.mp4",
            VideoMetadata(
                title="Melhores Ofertas da Semana!",
                description="Confira as ofertas que encontramos...",
                tags=["ofertas", "promoções", "economia"],
                privacy=PrivacyStatus.PUBLIC
            )
        )
    """
    
    def __init__(self, config: YouTubeConfig):
        if not GOOGLE_API_AVAILABLE:
            raise ImportError(
                "Google API não instalada. Execute:\n"
                "pip install google-auth-oauthlib google-api-python-client"
            )
        
        self.config = config
        self._service = None
        self._credentials = None
    
    async def authenticate(self) -> bool:
        """
        Autentica com o YouTube.
        
        Na primeira vez, abrirá um browser para autorização.
        Depois, usa o token salvo.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._authenticate_sync)
    
    def _authenticate_sync(self) -> bool:
        """Autenticação síncrona."""
        creds = None
        token_path = Path(self.config.token_file)
        
        # Carregar token existente
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(token_path), self.config.scopes
            )
        
        # Se não há credenciais válidas, obter novas
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not Path(self.config.client_secrets_file).exists():
                    raise FileNotFoundError(
                        f"Arquivo de credenciais não encontrado: "
                        f"{self.config.client_secrets_file}\n"
                        "Baixe em: https://console.cloud.google.com/apis/credentials"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.client_secrets_file,
                    self.config.scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Salvar token
            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, 'w') as f:
                f.write(creds.to_json())
        
        self._credentials = creds
        self._service = build('youtube', 'v3', credentials=creds)
        
        return True
    
    async def _run_sync(self, func, *args, **kwargs):
        """Executa função síncrona em thread."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))
    
    def _ensure_authenticated(self):
        if not self._service:
            raise RuntimeError("Não autenticado. Use 'await client.authenticate()' primeiro.")
    
    async def upload_video(
        self,
        video_path: Union[str, Path],
        metadata: VideoMetadata
    ) -> UploadResult:
        """
        Faz upload de vídeo para o YouTube.
        
        Args:
            video_path: Caminho do arquivo de vídeo
            metadata: Metadados do vídeo
            
        Returns:
            Resultado do upload
        """
        self._ensure_authenticated()
        video_path = Path(video_path)
        
        if not video_path.exists():
            return UploadResult(
                success=False,
                error=f"Arquivo não encontrado: {video_path}"
            )
        
        try:
            return await self._run_sync(
                self._upload_video_sync,
                str(video_path),
                metadata
            )
        except Exception as e:
            logger.error(f"Erro no upload: {e}")
            return UploadResult(success=False, error=str(e))
    
    def _upload_video_sync(
        self,
        video_path: str,
        metadata: VideoMetadata
    ) -> UploadResult:
        """Upload síncrono."""
        # Preparar body do request
        body = {
            "snippet": {
                "title": metadata.title[:100],  # Max 100 chars
                "description": metadata.description[:5000],  # Max 5000 chars
                "tags": metadata.tags[:500],  # Max 500 tags
                "categoryId": metadata.category.value
            },
            "status": {
                "privacyStatus": metadata.privacy.value,
                "selfDeclaredMadeForKids": metadata.made_for_kids
            }
        }
        
        # Agendamento
        if metadata.publish_at and metadata.privacy == PrivacyStatus.PRIVATE:
            body["status"]["publishAt"] = metadata.publish_at.isoformat() + "Z"
        
        # Shorts tag
        if metadata.is_short:
            body["snippet"]["title"] = f"{metadata.title} #Shorts"
        
        # Upload
        media = MediaFileUpload(
            video_path,
            mimetype="video/*",
            resumable=True,
            chunksize=1024*1024  # 1MB chunks
        )
        
        request = self._service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Upload {int(status.progress() * 100)}%")
        
        video_id = response.get("id")
        
        # Upload thumbnail se fornecido
        if metadata.thumbnail_path and Path(metadata.thumbnail_path).exists():
            try:
                self._service.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(
                        metadata.thumbnail_path,
                        mimetype="image/jpeg"
                    )
                ).execute()
            except Exception as e:
                logger.warning(f"Erro ao definir thumbnail: {e}")
        
        # Adicionar a playlist se especificado
        if metadata.playlist_id:
            try:
                self._service.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": metadata.playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": video_id
                            }
                        }
                    }
                ).execute()
            except Exception as e:
                logger.warning(f"Erro ao adicionar à playlist: {e}")
        
        return UploadResult(
            success=True,
            video_id=video_id,
            url=f"https://www.youtube.com/watch?v={video_id}"
        )
    
    async def update_video(
        self,
        video_id: str,
        metadata: VideoMetadata
    ) -> bool:
        """Atualiza metadados de um vídeo existente."""
        self._ensure_authenticated()
        
        try:
            body = {
                "id": video_id,
                "snippet": {
                    "title": metadata.title,
                    "description": metadata.description,
                    "tags": metadata.tags,
                    "categoryId": metadata.category.value
                }
            }
            
            await self._run_sync(
                self._service.videos().update,
                part="snippet",
                body=body
            )
            
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar vídeo: {e}")
            return False
    
    async def delete_video(self, video_id: str) -> bool:
        """Deleta um vídeo."""
        self._ensure_authenticated()
        
        try:
            await self._run_sync(
                self._service.videos().delete,
                id=video_id
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar vídeo: {e}")
            return False
    
    async def get_channel_info(self) -> Dict[str, Any]:
        """Obtém informações do canal autenticado."""
        self._ensure_authenticated()
        
        response = await self._run_sync(
            lambda: self._service.channels().list(
                part="snippet,statistics,contentDetails",
                mine=True
            ).execute()
        )
        
        if response.get("items"):
            channel = response["items"][0]
            return {
                "id": channel["id"],
                "title": channel["snippet"]["title"],
                "description": channel["snippet"]["description"],
                "subscribers": channel["statistics"].get("subscriberCount"),
                "views": channel["statistics"].get("viewCount"),
                "videos": channel["statistics"].get("videoCount"),
                "uploads_playlist": channel["contentDetails"]["relatedPlaylists"]["uploads"]
            }
        
        return {}
    
    async def get_playlists(self) -> List[Dict[str, Any]]:
        """Lista playlists do canal."""
        self._ensure_authenticated()
        
        response = await self._run_sync(
            lambda: self._service.playlists().list(
                part="snippet",
                mine=True,
                maxResults=50
            ).execute()
        )
        
        return [
            {
                "id": item["id"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"]
            }
            for item in response.get("items", [])
        ]
    
    async def create_playlist(
        self,
        title: str,
        description: str = "",
        privacy: PrivacyStatus = PrivacyStatus.PUBLIC
    ) -> Optional[str]:
        """Cria nova playlist."""
        self._ensure_authenticated()
        
        try:
            response = await self._run_sync(
                lambda: self._service.playlists().insert(
                    part="snippet,status",
                    body={
                        "snippet": {
                            "title": title,
                            "description": description
                        },
                        "status": {
                            "privacyStatus": privacy.value
                        }
                    }
                ).execute()
            )
            
            return response.get("id")
        except Exception as e:
            logger.error(f"Erro ao criar playlist: {e}")
            return None


# ==================== Shorts Generator ====================

@dataclass
class ShortsConfig:
    """Configuração para geração de Shorts."""
    max_duration: int = 60  # segundos (máximo para Shorts)
    aspect_ratio: str = "9:16"
    add_shorts_tag: bool = True


class YouTubeShortsUploader:
    """
    Uploader especializado para YouTube Shorts.
    
    Uso:
        uploader = YouTubeShortsUploader(youtube_client)
        
        result = await uploader.upload_short(
            "/path/to/short.mp4",
            title="Oferta IMPERDÍVEL!",
            description="Confira essa promoção incrível..."
        )
    """
    
    def __init__(self, client: YouTubeClient, config: Optional[ShortsConfig] = None):
        self.client = client
        self.config = config or ShortsConfig()
    
    async def upload_short(
        self,
        video_path: Union[str, Path],
        title: str,
        description: str = "",
        tags: List[str] = None,
        privacy: PrivacyStatus = PrivacyStatus.PUBLIC,
        publish_at: Optional[datetime] = None
    ) -> UploadResult:
        """
        Upload de YouTube Short.
        
        O vídeo deve:
        - Ser vertical (9:16)
        - Ter até 60 segundos
        - Ser em formato suportado (mp4, mov, etc.)
        """
        # Validar duração
        from pathlib import Path
        video_path = Path(video_path)
        
        # Preparar metadados
        final_tags = tags or []
        if "shorts" not in [t.lower() for t in final_tags]:
            final_tags.append("shorts")
        
        metadata = VideoMetadata(
            title=title,
            description=description,
            tags=final_tags,
            category=Category.ENTERTAINMENT,
            privacy=privacy,
            publish_at=publish_at,
            is_short=True
        )
        
        return await self.client.upload_video(video_path, metadata)
    
    async def upload_batch(
        self,
        videos: List[Dict[str, Any]],
        delay_seconds: int = 60
    ) -> List[UploadResult]:
        """
        Upload de múltiplos Shorts.
        
        Args:
            videos: Lista de dicts com 'path', 'title', 'description', 'tags'
            delay_seconds: Delay entre uploads
        """
        results = []
        
        for i, video in enumerate(videos):
            logger.info(f"Uploading {i+1}/{len(videos)}: {video['title']}")
            
            result = await self.upload_short(
                video['path'],
                video['title'],
                video.get('description', ''),
                video.get('tags', [])
            )
            results.append(result)
            
            # Delay entre uploads
            if i < len(videos) - 1:
                await asyncio.sleep(delay_seconds)
        
        return results


# ==================== Scheduler ====================

@dataclass
class ScheduledVideo:
    """Vídeo agendado."""
    video_path: str
    metadata: VideoMetadata
    scheduled_time: datetime
    id: Optional[str] = None


class YouTubeScheduler:
    """
    Agendador de uploads para YouTube.
    
    Nota: O YouTube suporta agendamento nativo, mas este scheduler
    permite agendar o UPLOAD (não apenas a publicação).
    """
    
    def __init__(self, client: YouTubeClient):
        self.client = client
        self._queue: List[ScheduledVideo] = []
        self._id_counter = 0
    
    def schedule(
        self,
        video_path: str,
        metadata: VideoMetadata,
        upload_at: datetime
    ) -> str:
        """Agenda um upload."""
        self._id_counter += 1
        video_id = f"yt_scheduled_{self._id_counter}"
        
        self._queue.append(ScheduledVideo(
            video_path=video_path,
            metadata=metadata,
            scheduled_time=upload_at,
            id=video_id
        ))
        
        self._queue.sort(key=lambda v: v.scheduled_time)
        return video_id
    
    async def process_queue(self) -> List[Dict[str, Any]]:
        """Processa vídeos prontos para upload."""
        now = datetime.now()
        results = []
        
        while self._queue and self._queue[0].scheduled_time <= now:
            scheduled = self._queue.pop(0)
            
            result = await self.client.upload_video(
                scheduled.video_path,
                scheduled.metadata
            )
            
            results.append({
                "id": scheduled.id,
                "scheduled_time": scheduled.scheduled_time.isoformat(),
                "result": {
                    "success": result.success,
                    "video_id": result.video_id,
                    "url": result.url,
                    "error": result.error
                }
            })
        
        return results
    
    def get_pending(self) -> List[ScheduledVideo]:
        """Retorna vídeos pendentes."""
        return list(self._queue)
    
    def cancel(self, video_id: str) -> bool:
        """Cancela um upload agendado."""
        for i, scheduled in enumerate(self._queue):
            if scheduled.id == video_id:
                self._queue.pop(i)
                return True
        return False
