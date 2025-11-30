"""
YouTube Routes
Upload de vídeos para YouTube via API oficial
"""

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form
)
from pydantic import BaseModel
from typing import Optional, List
import shutil
import os
import json
from datetime import datetime, timezone

from api.middleware.auth import get_current_user
from vendor.youtube.client import (
    YouTubeClient, YouTubeConfig, VideoMetadata,
    PrivacyStatus, Category
)
from shared.config import settings
from shared.redis import get_redis

router = APIRouter()


class YouTubeAuthRequest(BaseModel):
    """Request para iniciar autenticação OAuth."""
    account_name: str


class YouTubeUploadRequest(BaseModel):
    """Request para upload de vídeo."""
    account_name: str
    title: str
    description: str = ""
    tags: Optional[List[str]] = None
    privacy: str = "private"
    category: str = "26"  # HOWTO_STYLE
    is_short: bool = False
    publish_at: Optional[datetime] = None


@router.post("/auth/init")
async def init_auth(
    data: YouTubeAuthRequest,
    current_user=Depends(get_current_user)
):
    """
    Inicia processo de autenticação OAuth do YouTube.
    
    Retorna URL para autorização. Após autorizar, o token será salvo
    automaticamente.
    """
    tokens_dir = os.path.join(settings.DATA_DIR, "youtube_tokens")
    os.makedirs(tokens_dir, exist_ok=True)
    
    # Verificar se existe credentials.json
    creds_file = os.path.join(settings.DATA_DIR, "youtube_credentials.json")
    if not os.path.exists(creds_file):
        raise HTTPException(
            status_code=400,
            detail=(
                "Arquivo de credenciais do Google não encontrado. "
                "Configure em: data/youtube_credentials.json"
            )
        )
    
    token_file = os.path.join(
        tokens_dir,
        f"{current_user.id}_{data.account_name}.json"
    )
    
    try:
        config = YouTubeConfig(
            client_secrets_file=creds_file,
            token_file=token_file
        )
        client = YouTubeClient(config)
        await client.authenticate()
        
        return {
            "status": "success",
            "message": "Autenticação concluída",
            "account_name": data.account_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts")
async def list_accounts(current_user=Depends(get_current_user)):
    """Lista contas YouTube autenticadas do usuário."""
    tokens_dir = os.path.join(settings.DATA_DIR, "youtube_tokens")
    
    if not os.path.exists(tokens_dir):
        return {"accounts": []}
    
    accounts = []
    prefix = f"{current_user.id}_"
    
    for filename in os.listdir(tokens_dir):
        if filename.startswith(prefix) and filename.endswith('.json'):
            account_name = filename[len(prefix):-5]
            accounts.append({
                "account_name": account_name,
                "token_file": filename
            })
    
    return {"accounts": accounts}


@router.post("/upload")
async def upload_video(
    account_name: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    privacy: str = Form("private"),
    category: str = Form("26"),
    is_short: bool = Form(False),
    file: UploadFile = File(...),
    thumbnail: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_user)
):
    """
    Faz upload de vídeo para o YouTube.
    
    Args:
        account_name: Nome da conta configurada
        title: Título do vídeo (max 100 chars)
        description: Descrição (max 5000 chars)
        tags: Tags separadas por vírgula
        privacy: public, private, unlisted
        category: ID da categoria YouTube
        is_short: Se é um YouTube Short
        file: Arquivo de vídeo
        thumbnail: Thumbnail (opcional, jpg/png)
    """
    # Verificar token
    tokens_dir = os.path.join(settings.DATA_DIR, "youtube_tokens")
    token_file = os.path.join(
        tokens_dir,
        f"{current_user.id}_{account_name}.json"
    )
    
    if not os.path.exists(token_file):
        raise HTTPException(
            status_code=404,
            detail=f"Conta '{account_name}' não autenticada"
        )
    
    # Salvar arquivos temporariamente
    temp_dir = os.path.join(settings.DATA_DIR, "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = os.path.join(
        temp_dir, f"youtube_{timestamp}_{file.filename}"
    )
    thumb_path = None
    
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    if thumbnail:
        thumb_path = os.path.join(
            temp_dir, f"thumb_{timestamp}_{thumbnail.filename}"
        )
        with open(thumb_path, "wb") as buffer:
            shutil.copyfileobj(thumbnail.file, buffer)
    
    try:
        # Configurar cliente
        creds_file = os.path.join(settings.DATA_DIR, "youtube_credentials.json")
        config = YouTubeConfig(
            client_secrets_file=creds_file,
            token_file=token_file
        )
        client = YouTubeClient(config)
        await client.authenticate()
        
        # Mapear privacy
        privacy_map = {
            "public": PrivacyStatus.PUBLIC,
            "private": PrivacyStatus.PRIVATE,
            "unlisted": PrivacyStatus.UNLISTED
        }
        
        # Mapear categoria
        category_map = {c.value: c for c in Category}
        
        # Configurar metadados
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        metadata = VideoMetadata(
            title=title,
            description=description,
            tags=tag_list,
            category=category_map.get(category, Category.HOWTO_STYLE),
            privacy=privacy_map.get(privacy, PrivacyStatus.PRIVATE),
            is_short=is_short,
            thumbnail_path=thumb_path
        )
        
        # Fazer upload
        result = await client.upload_video(video_path, metadata)
        
        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=result.error or "Upload falhou"
            )
        
        # Track quota usage
        await _track_quota_usage(str(current_user.id), "upload", 1600)
        
        return {
            "status": "success",
            "video_id": result.video_id,
            "url": result.url or f"https://youtube.com/watch?v={result.video_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Limpar arquivos temporários
        if os.path.exists(video_path):
            os.remove(video_path)
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)


# ==================== Quota Monitoring ====================

YOUTUBE_DAILY_QUOTA = 10000  # YouTube API quota diária padrão
QUOTA_COSTS = {
    "upload": 1600,          # Upload de vídeo
    "update": 50,            # Atualizar metadados
    "delete": 50,            # Deletar vídeo
    "list": 1,               # Listar vídeos
    "read": 1,               # Ler informações
    "thumbnail": 50,         # Definir thumbnail
    "playlist_insert": 50,   # Adicionar a playlist
}


async def _track_quota_usage(
    user_id: str,
    operation: str,
    cost: int = None
):
    """
    Rastreia uso de quota do YouTube.
    
    Args:
        user_id: ID do usuário
        operation: Tipo de operação (upload, update, etc)
        cost: Custo em unidades de quota (usa padrão se None)
    """
    import json
    
    redis = await get_redis()
    
    # Calcular custo
    quota_cost = cost or QUOTA_COSTS.get(operation, 1)
    
    # Chave por dia
    today = datetime.now().strftime("%Y-%m-%d")
    quota_key = f"youtube:quota:{user_id}:{today}"
    
    # Incrementar contador
    current_usage = await redis.get(quota_key)
    if current_usage:
        usage_data = json.loads(current_usage)
    else:
        usage_data = {"total": 0, "operations": {}}
    
    usage_data["total"] += quota_cost
    
    if operation not in usage_data["operations"]:
        usage_data["operations"][operation] = 0
    usage_data["operations"][operation] += quota_cost
    
    # Salvar com expiração de 2 dias
    await redis.set(quota_key, json.dumps(usage_data), ex=172800)
    
    # Verificar alertas
    await _check_quota_alerts(user_id, usage_data["total"])


async def _check_quota_alerts(user_id: str, current_usage: int):
    """
    Verifica e dispara alertas de quota.
    """
    
    redis = await get_redis()
    
    # Thresholds de alerta (70%, 85%, 95%)
    thresholds = [
        (0.70, "warning"),
        (0.85, "critical"),
        (0.95, "exhausted")
    ]
    
    for threshold, level in thresholds:
        limit = int(YOUTUBE_DAILY_QUOTA * threshold)
        
        if current_usage >= limit:
            alert_key = f"youtube:quota_alert:{user_id}:{level}"
            
            # Verificar se alerta já foi enviado hoje
            already_sent = await redis.get(alert_key)
            if not already_sent:
                # Marcar como enviado
                await redis.set(alert_key, "1", ex=86400)  # 24 horas
                
                # Salvar alerta para notificação
                await redis.lpush(
                    f"notifications:{user_id}",
                    json.dumps({
                        "type": "youtube_quota",
                        "level": level,
                        "usage": current_usage,
                        "limit": YOUTUBE_DAILY_QUOTA,
                        "percentage": int((current_usage / YOUTUBE_DAILY_QUOTA) * 100),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                )


@router.get("/quota")
async def get_quota_status(current_user=Depends(get_current_user)):
    """
    Retorna status atual da quota do YouTube.
    
    A quota do YouTube é de 10.000 unidades por dia.
    Upload de vídeo consome ~1.600 unidades.
    """
    import json
    
    redis = await get_redis()
    
    today = datetime.now().strftime("%Y-%m-%d")
    quota_key = f"youtube:quota:{current_user.id}:{today}"
    
    usage_data = await redis.get(quota_key)
    
    if usage_data:
        data = json.loads(usage_data)
        total_used = data.get("total", 0)
        operations = data.get("operations", {})
    else:
        total_used = 0
        operations = {}
    
    remaining = YOUTUBE_DAILY_QUOTA - total_used
    percentage_used = (total_used / YOUTUBE_DAILY_QUOTA) * 100
    
    # Estimar uploads restantes
    uploads_remaining = remaining // QUOTA_COSTS["upload"]
    
    return {
        "quota": {
            "daily_limit": YOUTUBE_DAILY_QUOTA,
            "used": total_used,
            "remaining": remaining,
            "percentage_used": round(percentage_used, 1)
        },
        "operations": operations,
        "estimates": {
            "uploads_remaining": uploads_remaining,
            "updates_remaining": remaining // QUOTA_COSTS["update"]
        },
        "reset_time": "00:00 PST (Pacific Time)",
        "date": today
    }


@router.get("/quota/history")
async def get_quota_history(
    days: int = 7,
    current_user=Depends(get_current_user)
):
    """
    Retorna histórico de uso de quota dos últimos N dias.
    """
    import json
    from datetime import timedelta
    
    redis = await get_redis()
    
    history = []
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        quota_key = f"youtube:quota:{current_user.id}:{date}"
        
        usage_data = await redis.get(quota_key)
        
        if usage_data:
            data = json.loads(usage_data)
            history.append({
                "date": date,
                "total_used": data.get("total", 0),
                "operations": data.get("operations", {})
            })
        else:
            history.append({
                "date": date,
                "total_used": 0,
                "operations": {}
            })
    
    return {"history": history, "days": days}
