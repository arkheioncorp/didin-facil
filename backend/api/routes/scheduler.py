"""
Scheduler Routes
Endpoints para agendamento de posts em redes sociais
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import os
import shutil

from api.middleware.auth import get_current_user
from workers.post_scheduler import (
    PostSchedulerService, ScheduledPost, Platform, PostStatus
)
from shared.config import settings

router = APIRouter()

# Instância do serviço
scheduler = PostSchedulerService()


class SchedulePostRequest(BaseModel):
    """Request para agendar um post."""
    platform: str  # instagram, tiktok, youtube, whatsapp
    scheduled_time: datetime
    content_type: str  # photo, video, reel, story, text, short
    caption: str = ""
    hashtags: List[str] = []
    account_name: Optional[str] = None
    platform_config: dict = {}


class SchedulePostResponse(BaseModel):
    """Response do agendamento."""
    id: str
    platform: str
    scheduled_time: datetime
    status: str
    content_type: str


@router.post("/posts", response_model=SchedulePostResponse)
async def schedule_post(
    data: SchedulePostRequest,
    current_user=Depends(get_current_user)
):
    """
    Agenda um post para publicação futura.
    
    Plataformas suportadas:
    - instagram: photo, video, reel, story
    - tiktok: video
    - youtube: video, short
    - whatsapp: text
    """
    try:
        platform = Platform(data.platform)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Plataforma inválida: {data.platform}"
        )
    
    if data.scheduled_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="A data de agendamento deve ser futura"
        )
    
    post = ScheduledPost(
        user_id=str(current_user.id),
        platform=platform,
        scheduled_time=data.scheduled_time,
        content_type=data.content_type,
        caption=data.caption,
        hashtags=data.hashtags,
        account_name=data.account_name,
        platform_config=data.platform_config
    )
    
    scheduled = await scheduler.schedule(post)
    
    return SchedulePostResponse(
        id=scheduled.id,
        platform=scheduled.platform.value,
        scheduled_time=scheduled.scheduled_time,
        status=scheduled.status.value,
        content_type=scheduled.content_type
    )


@router.post("/posts/with-file", response_model=SchedulePostResponse)
async def schedule_post_with_file(
    platform: str = Form(...),
    scheduled_time: str = Form(...),
    content_type: str = Form(...),
    caption: str = Form(""),
    hashtags: str = Form(""),
    account_name: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    """Agenda um post com upload de arquivo."""
    try:
        platform_enum = Platform(platform)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Plataforma inválida: {platform}"
        )
    
    # Parse da data
    try:
        scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato de data inválido"
        )
    
    if scheduled_dt <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="A data de agendamento deve ser futura"
        )
    
    # Salvar arquivo
    upload_dir = os.path.join(
        settings.DATA_DIR, "scheduled_uploads", str(current_user.id)
    )
    os.makedirs(upload_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(upload_dir, f"{timestamp}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Criar post
    hashtag_list = [h.strip() for h in hashtags.split(",") if h.strip()]
    
    post = ScheduledPost(
        user_id=str(current_user.id),
        platform=platform_enum,
        scheduled_time=scheduled_dt,
        content_type=content_type,
        caption=caption,
        hashtags=hashtag_list,
        file_path=file_path,
        account_name=account_name
    )
    
    scheduled = await scheduler.schedule(post)
    
    return SchedulePostResponse(
        id=scheduled.id,
        platform=scheduled.platform.value,
        scheduled_time=scheduled.scheduled_time,
        status=scheduled.status.value,
        content_type=scheduled.content_type
    )


@router.get("/posts")
async def list_scheduled_posts(
    status: Optional[str] = None,
    limit: int = 50,
    current_user=Depends(get_current_user)
):
    """Lista posts agendados do usuário."""
    status_filter = None
    if status:
        try:
            status_filter = PostStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Status inválido: {status}"
            )
    
    posts = await scheduler.get_user_posts(
        user_id=str(current_user.id),
        status=status_filter,
        limit=limit
    )
    
    return {
        "posts": [
            {
                "id": p.id,
                "platform": p.platform.value,
                "scheduled_time": p.scheduled_time.isoformat(),
                "status": p.status.value,
                "content_type": p.content_type,
                "caption": p.caption[:100] + "..." if len(p.caption) > 100 else p.caption,
                "created_at": p.created_at.isoformat(),
                "published_at": p.published_at.isoformat() if p.published_at else None
            }
            for p in posts
        ],
        "total": len(posts)
    }


@router.delete("/posts/{post_id}")
async def cancel_post(
    post_id: str,
    current_user=Depends(get_current_user)
):
    """Cancela um post agendado."""
    success = await scheduler.cancel(post_id, str(current_user.id))
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Post não encontrado ou não pode ser cancelado"
        )
    
    return {"status": "cancelled", "id": post_id}


@router.get("/stats")
async def get_scheduler_stats(current_user=Depends(get_current_user)):
    """Retorna estatísticas do agendador."""
    posts = await scheduler.get_user_posts(str(current_user.id), limit=1000)
    
    stats = {
        "total": len(posts),
        "scheduled": 0,
        "published": 0,
        "failed": 0,
        "cancelled": 0,
        "retrying": 0,
        "by_platform": {}
    }
    
    for post in posts:
        # Por status
        if post.status == PostStatus.SCHEDULED:
            if post.retry_count > 0:
                stats["retrying"] += 1
            else:
                stats["scheduled"] += 1
        elif post.status == PostStatus.PUBLISHED:
            stats["published"] += 1
        elif post.status == PostStatus.FAILED:
            stats["failed"] += 1
        elif post.status == PostStatus.CANCELLED:
            stats["cancelled"] += 1
        
        # Por plataforma
        platform = post.platform.value
        if platform not in stats["by_platform"]:
            stats["by_platform"][platform] = 0
        stats["by_platform"][platform] += 1
    
    return stats


@router.get("/dlq")
async def get_dlq_posts(
    limit: int = 50,
    current_user=Depends(get_current_user)
):
    """
    Lista posts na Dead Letter Queue.
    
    Posts que falharam após múltiplas tentativas são movidos para cá.
    """
    posts = await scheduler.get_dlq_posts(limit=limit)
    
    # Filtrar apenas posts do usuário atual (admin vê todos)
    user_posts = [
        p for p in posts 
        if p.user_id == str(current_user.id) or getattr(current_user, 'is_admin', False)
    ]
    
    return [
        {
            "id": p.id,
            "platform": p.platform.value,
            "scheduled_time": p.scheduled_time.isoformat(),
            "failed_at": getattr(p, 'last_error_at', p.scheduled_time).isoformat(),
            "attempts": p.retry_count,
            "max_attempts": 3,
            "last_error": p.error_message or "Erro desconhecido",
            "error_type": _classify_error(p.error_message or ""),
            "content_type": p.content_type,
            "caption": p.caption,
            "media_url": p.platform_config.get("media_url"),
            "original_post_id": p.id
        }
        for p in user_posts
    ]


def _classify_error(error_message: str) -> str:
    """Classifica o tipo de erro baseado na mensagem."""
    error_lower = error_message.lower()
    
    if any(x in error_lower for x in ["rate limit", "too many", "429"]):
        return "rate_limit"
    if any(x in error_lower for x in ["auth", "token", "401", "403", "login"]):
        return "auth_error"
    if any(x in error_lower for x in ["network", "timeout", "connection", "socket"]):
        return "network_error"
    if any(x in error_lower for x in ["media", "file", "format", "size", "invalid"]):
        return "content_error"
    if any(x in error_lower for x in ["quota", "limit exceeded", "daily"]):
        return "quota_exceeded"
    
    return "unknown"


@router.get("/dlq/stats")
async def get_dlq_stats(
    current_user=Depends(get_current_user)
):
    """
    Retorna estatísticas da Dead Letter Queue.
    """
    posts = await scheduler.get_dlq_posts(limit=1000)
    
    # Filtrar por usuário
    user_posts = [
        p for p in posts 
        if p.user_id == str(current_user.id) or getattr(current_user, 'is_admin', False)
    ]
    
    # Calcular estatísticas
    by_platform = {}
    by_error_type = {}
    oldest_failure = None
    
    for post in user_posts:
        # Por plataforma
        platform = post.platform.value
        by_platform[platform] = by_platform.get(platform, 0) + 1
        
        # Por tipo de erro
        error_type = _classify_error(post.error_message or "")
        by_error_type[error_type] = by_error_type.get(error_type, 0) + 1
        
        # Mais antigo
        failure_time = getattr(post, 'last_error_at', post.scheduled_time)
        if oldest_failure is None or failure_time < oldest_failure:
            oldest_failure = failure_time
    
    return {
        "total": len(user_posts),
        "by_platform": by_platform,
        "by_error_type": by_error_type,
        "oldest_failure": oldest_failure.isoformat() if oldest_failure else None
    }


@router.post("/dlq/{post_id}/retry")
async def retry_dlq_post(
    post_id: str,
    current_user=Depends(get_current_user)
):
    """
    Reprocessa um post da Dead Letter Queue.
    
    Reseta o contador de retry e reagenda o post.
    """
    # Verificar se o post pertence ao usuário
    from shared.redis import get_redis
    redis = await get_redis()
    
    data = await redis.get(f"scheduled_post:{post_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    post = ScheduledPost.model_validate_json(data)
    
    if post.user_id != str(current_user.id) and not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    success = await scheduler.retry_dlq_post(post_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível reagendar o post"
        )
    
    return {"status": "rescheduled", "id": post_id}


class BulkActionRequest(BaseModel):
    """Request para ações em massa na DLQ."""
    ids: List[str]


@router.post("/dlq/retry-all")
async def retry_all_dlq_posts(
    request: BulkActionRequest,
    current_user=Depends(get_current_user)
):
    """
    Reagenda múltiplos posts da DLQ.
    """
    from shared.redis import get_redis
    redis = await get_redis()
    
    success_count = 0
    error_count = 0
    
    for post_id in request.ids:
        try:
            data = await redis.get(f"scheduled_post:{post_id}")
            if not data:
                error_count += 1
                continue
            
            post = ScheduledPost.model_validate_json(data)
            
            # Verificar permissão
            is_admin = getattr(current_user, 'is_admin', False)
            if post.user_id != str(current_user.id) and not is_admin:
                error_count += 1
                continue
            
            success = await scheduler.retry_dlq_post(post_id)
            if success:
                success_count += 1
            else:
                error_count += 1
                
        except Exception:
            error_count += 1
    
    return {
        "status": "completed",
        "success": success_count,
        "errors": error_count
    }


@router.post("/dlq/delete-all")
async def delete_all_dlq_posts(
    request: BulkActionRequest,
    current_user=Depends(get_current_user)
):
    """
    Remove permanentemente múltiplos posts da DLQ.
    """
    from shared.redis import get_redis
    redis = await get_redis()
    
    success_count = 0
    error_count = 0
    
    for post_id in request.ids:
        try:
            data = await redis.get(f"scheduled_post:{post_id}")
            if not data:
                error_count += 1
                continue
            
            post = ScheduledPost.model_validate_json(data)
            
            # Verificar permissão
            is_admin = getattr(current_user, 'is_admin', False)
            if post.user_id != str(current_user.id) and not is_admin:
                error_count += 1
                continue
            
            # Remover
            await redis.lrem("dlq_scheduled_posts", 0, post_id)
            await redis.delete(f"scheduled_post:{post_id}")
            success_count += 1
            
        except Exception:
            error_count += 1
    
    return {
        "status": "completed",
        "deleted": success_count,
        "errors": error_count
    }


@router.delete("/dlq/{post_id}")
async def remove_from_dlq(
    post_id: str,
    current_user=Depends(get_current_user)
):
    """Remove permanentemente um post da DLQ."""
    from shared.redis import get_redis
    redis = await get_redis()
    
    data = await redis.get(f"scheduled_post:{post_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    post = ScheduledPost.model_validate_json(data)
    
    if post.user_id != str(current_user.id) and not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # Remover da DLQ e do Redis
    await redis.lrem("dlq_scheduled_posts", 0, post_id)
    await redis.delete(f"scheduled_post:{post_id}")
    
    return {"status": "deleted", "id": post_id}

