"""
Social Media API Router
========================
Endpoints FastAPI para gerenciamento de redes sociais.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import logging

# Importar clientes
from backend.vendor.whatsapp.client import (
    WhatsAppClient, parse_webhook_message
)
from backend.vendor.instagram.client import (
    InstagramClient, PostConfig, StoryConfig
)
from backend.vendor.tiktok.client import (
    TikTokClient, VideoConfig as TikTokVideoConfig
)
from backend.vendor.social_media_manager import (
    SocialMediaManager, SocialMediaConfig,
    UnifiedPost, ContentType, Platform
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/social", tags=["Social Media"])


# ==================== Schemas ====================

class PlatformEnum(str, Enum):
    instagram = "instagram"
    tiktok = "tiktok"
    whatsapp = "whatsapp"


class ContentTypeEnum(str, Enum):
    image = "image"
    video = "video"
    reel = "reel"
    story = "story"
    carousel = "carousel"
    text = "text"


class WhatsAppMessageRequest(BaseModel):
    """Request para envio de mensagem WhatsApp."""
    to: str = Field(..., description="Número no formato 5511999999999")
    message: str = Field(..., max_length=4096)
    media_url: Optional[str] = None
    media_type: Optional[str] = None  # image, video, audio, document


class WhatsAppBulkRequest(BaseModel):
    """Request para envio em massa."""
    recipients: List[str]
    message: str
    media_url: Optional[str] = None


class InstagramPostRequest(BaseModel):
    """Request para post no Instagram."""
    media_path: str
    caption: str = ""
    hashtags: List[str] = []
    post_type: ContentTypeEnum = ContentTypeEnum.image


class TikTokUploadRequest(BaseModel):
    """Request para upload no TikTok."""
    video_path: str
    caption: str = ""
    hashtags: List[str] = []
    schedule_time: Optional[datetime] = None


class UnifiedPostRequest(BaseModel):
    """Request para post unificado."""
    content_type: ContentTypeEnum
    media_paths: List[str]
    caption: str = ""
    hashtags: List[str] = []
    platforms: List[PlatformEnum]
    schedule_time: Optional[datetime] = None
    # WhatsApp específico
    whatsapp_recipients: List[str] = []


class PostResponse(BaseModel):
    """Response de post."""
    success: bool
    platform: str
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


class WebhookPayload(BaseModel):
    """Payload genérico de webhook."""
    event: str
    data: dict


# ==================== Dependency Injection ====================

# Configuração global (em produção, use variáveis de ambiente)
_manager: Optional[SocialMediaManager] = None


async def get_social_manager() -> SocialMediaManager:
    """Dependency para obter o manager de redes sociais."""
    global _manager
    
    if _manager is None:
        # Em produção, carregar do settings/env
        from backend.api.config import settings
        
        config = SocialMediaConfig(
            instagram_username=getattr(settings, 'INSTAGRAM_USERNAME', None),
            instagram_password=getattr(settings, 'INSTAGRAM_PASSWORD', None),
            instagram_session_file=getattr(settings, 'INSTAGRAM_SESSION_FILE', None),
            tiktok_cookies_file=getattr(settings, 'TIKTOK_COOKIES_FILE', None),
            whatsapp_api_url=getattr(settings, 'WHATSAPP_API_URL', None),
            whatsapp_api_key=getattr(settings, 'WHATSAPP_API_KEY', None),
            whatsapp_instance=getattr(settings, 'WHATSAPP_INSTANCE', None),
        )
        
        _manager = SocialMediaManager(config)
        await _manager.initialize()
    
    return _manager


# ==================== WhatsApp Endpoints ====================

@router.post("/whatsapp/send", response_model=PostResponse)
async def send_whatsapp_message(
    request: WhatsAppMessageRequest,
    manager: SocialMediaManager = Depends(get_social_manager)
):
    """Envia mensagem via WhatsApp."""
    try:
        client: WhatsAppClient = manager._clients.get(Platform.WHATSAPP)
        if not client:
            raise HTTPException(status_code=503, detail="WhatsApp não configurado")
        
        if request.media_url:
            if request.media_type == "image":
                result = await client.send_image(
                    request.to, request.media_url, request.message
                )
            elif request.media_type == "video":
                result = await client.send_video(
                    request.to, request.media_url, request.message
                )
            elif request.media_type == "audio":
                result = await client.send_audio(request.to, request.media_url)
            else:
                result = await client.send_document(
                    request.to, request.media_url, "document"
                )
        else:
            result = await client.send_text(request.to, request.message)
        
        return PostResponse(
            success=True,
            platform="whatsapp",
            post_id=result.get("key", {}).get("id")
        )
        
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp: {e}")
        return PostResponse(
            success=False,
            platform="whatsapp",
            error=str(e)
        )


@router.post("/whatsapp/bulk")
async def send_whatsapp_bulk(
    request: WhatsAppBulkRequest,
    background_tasks: BackgroundTasks,
    manager: SocialMediaManager = Depends(get_social_manager)
):
    """Envia mensagem para múltiplos contatos (background)."""
    
    async def send_bulk():
        client: WhatsAppClient = manager._clients.get(Platform.WHATSAPP)
        if not client:
            return
        
        for recipient in request.recipients:
            try:
                if request.media_url:
                    await client.send_image(recipient, request.media_url, request.message)
                else:
                    await client.send_text(recipient, request.message)
                
                # Delay entre mensagens para evitar ban
                import asyncio
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Erro ao enviar para {recipient}: {e}")
    
    background_tasks.add_task(send_bulk)
    
    return {
        "status": "queued",
        "total_recipients": len(request.recipients)
    }


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(payload: WebhookPayload):
    """Webhook para receber mensagens do WhatsApp."""
    message = parse_webhook_message(payload.dict())
    
    if message:
        logger.info(f"Mensagem recebida de {message.from_number}: {message.content}")
        
        # Aqui você pode processar a mensagem
        # Por exemplo, integrar com um chatbot
        
        return {"status": "processed", "message_id": message.message_id}
    
    return {"status": "ignored"}


@router.get("/whatsapp/qrcode")
async def get_whatsapp_qrcode(
    manager: SocialMediaManager = Depends(get_social_manager)
):
    """Obtém QR Code para conectar WhatsApp."""
    client: WhatsAppClient = manager._clients.get(Platform.WHATSAPP)
    if not client:
        raise HTTPException(status_code=503, detail="WhatsApp não configurado")
    
    qr = await client.get_qr_code()
    return qr


# ==================== Instagram Endpoints ====================

@router.post("/instagram/post", response_model=PostResponse)
async def create_instagram_post(
    request: InstagramPostRequest,
    manager: SocialMediaManager = Depends(get_social_manager)
):
    """Cria post no Instagram."""
    try:
        client: InstagramClient = manager._clients.get(Platform.INSTAGRAM)
        if not client:
            raise HTTPException(status_code=503, detail="Instagram não configurado")
        
        config = PostConfig(
            caption=request.caption,
            hashtags=request.hashtags
        )
        
        if request.post_type == ContentTypeEnum.image:
            result = await client.upload_photo(request.media_path, config)
        elif request.post_type == ContentTypeEnum.video:
            result = await client.upload_video(request.media_path, config)
        elif request.post_type == ContentTypeEnum.reel:
            result = await client.upload_reel(request.media_path, config)
        else:
            raise HTTPException(status_code=400, detail="Tipo não suportado")
        
        return PostResponse(
            success=True,
            platform="instagram",
            post_id=result.get("id"),
            url=result.get("url")
        )
        
    except Exception as e:
        logger.error(f"Erro ao postar no Instagram: {e}")
        return PostResponse(
            success=False,
            platform="instagram",
            error=str(e)
        )


@router.post("/instagram/story", response_model=PostResponse)
async def create_instagram_story(
    media_path: str,
    link: Optional[str] = None,
    manager: SocialMediaManager = Depends(get_social_manager)
):
    """Cria story no Instagram."""
    try:
        client: InstagramClient = manager._clients.get(Platform.INSTAGRAM)
        if not client:
            raise HTTPException(status_code=503, detail="Instagram não configurado")
        
        story_config = StoryConfig(link=link)
        
        from pathlib import Path
        if Path(media_path).suffix.lower() in ['.mp4', '.mov']:
            result = await client.upload_story_video(media_path, story_config)
        else:
            result = await client.upload_story_photo(media_path, story_config)
        
        return PostResponse(
            success=True,
            platform="instagram",
            post_id=result.get("id")
        )
        
    except Exception as e:
        return PostResponse(
            success=False,
            platform="instagram",
            error=str(e)
        )


# ==================== TikTok Endpoints ====================

@router.post("/tiktok/upload", response_model=PostResponse)
async def upload_tiktok_video(
    request: TikTokUploadRequest,
    manager: SocialMediaManager = Depends(get_social_manager)
):
    """Faz upload de vídeo no TikTok."""
    try:
        client: TikTokClient = manager._clients.get(Platform.TIKTOK)
        if not client:
            raise HTTPException(status_code=503, detail="TikTok não configurado")
        
        config = TikTokVideoConfig(
            caption=request.caption,
            hashtags=request.hashtags,
            schedule_time=request.schedule_time
        )
        
        result = await client.upload_video(request.video_path, config)
        
        return PostResponse(
            success=result.status.value in ['published', 'scheduled'],
            platform="tiktok",
            post_id=result.video_id,
            url=result.url,
            error=result.error
        )
        
    except Exception as e:
        return PostResponse(
            success=False,
            platform="tiktok",
            error=str(e)
        )


# ==================== Unified Endpoints ====================

@router.post("/publish", response_model=List[PostResponse])
async def publish_to_platforms(
    request: UnifiedPostRequest,
    manager: SocialMediaManager = Depends(get_social_manager)
):
    """Publica conteúdo em múltiplas plataformas."""
    
    post = UnifiedPost(
        content_type=ContentType[request.content_type.value.upper()],
        media_paths=request.media_paths,
        caption=request.caption,
        hashtags=request.hashtags,
        platforms=[Platform[p.value.upper()] for p in request.platforms],
        schedule_time=request.schedule_time,
        whatsapp_recipients=request.whatsapp_recipients
    )
    
    results = await manager.publish(post)
    
    return [
        PostResponse(
            success=r.success,
            platform=r.platform.value,
            post_id=r.post_id,
            url=r.url,
            error=r.error
        )
        for r in results
    ]


@router.get("/status")
async def get_platforms_status(
    manager: SocialMediaManager = Depends(get_social_manager)
):
    """Retorna status de conexão das plataformas."""
    
    platforms = manager.get_initialized_platforms()
    status = await manager.test_connections()
    
    return {
        "initialized": [p.value for p in platforms],
        "connection_status": {p.value: s for p, s in status.items()}
    }


# ==================== Content Generation Endpoints ====================

@router.post("/content/generate-caption")
async def generate_caption(
    product_name: str,
    price: float,
    store: str = "",
    style: str = "promotional"
):
    """Gera legenda para produto."""
    from backend.vendor.content_generator.generator import (
        CaptionGenerator, ProductData
    )
    
    generator = CaptionGenerator()
    product = ProductData(name=product_name, price=price, store=store)
    
    caption = generator.generate_product_caption(product, style=style)
    
    return {"caption": caption}


@router.post("/content/generate-video")
async def generate_product_video(
    product_name: str,
    price: float,
    store: str = "",
    template: str = "deal_alert",
    background_tasks: BackgroundTasks = None
):
    """Gera vídeo promocional para produto (background task)."""
    from backend.vendor.content_generator.generator import (
        FFmpegVideoGenerator, VideoConfig, ProductData, TemplateStyle
    )
    import uuid
    from pathlib import Path
    
    output_dir = Path("./generated_content")
    output_dir.mkdir(exist_ok=True)
    
    video_id = str(uuid.uuid4())[:8]
    output_path = output_dir / f"video_{video_id}.mp4"
    
    async def generate():
        generator = FFmpegVideoGenerator(VideoConfig())
        product = ProductData(name=product_name, price=price, store=store)
        
        template_enum = TemplateStyle[template.upper()]
        await generator.create_product_video(product, output_path, template_enum)
    
    if background_tasks:
        background_tasks.add_task(generate)
        return {
            "status": "generating",
            "video_id": video_id,
            "path": str(output_path)
        }
    else:
        await generate()
        return {
            "status": "completed",
            "video_id": video_id,
            "path": str(output_path)
        }
