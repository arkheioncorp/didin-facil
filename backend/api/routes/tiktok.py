"""
TikTok Routes
Upload de vídeos para TikTok via Selenium
"""

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form
)
from pydantic import BaseModel
from typing import Optional, List
import shutil
import os
from datetime import datetime

from api.middleware.auth import get_current_user
from vendor.tiktok.client import (
    TikTokClient, TikTokConfig, VideoConfig, Privacy
)
from shared.config import settings
from api.services.tiktok_session import (
    TikTokSessionManager,
    TikTokSessionStatus
)

router = APIRouter()
session_manager = TikTokSessionManager()


class TikTokSessionSetup(BaseModel):
    """Request para configurar sessão TikTok."""
    account_name: str
    cookies: List[dict]


class TikTokUploadRequest(BaseModel):
    """Request para upload de vídeo."""
    account_name: str
    caption: str
    hashtags: Optional[List[str]] = None
    privacy: str = "public"
    schedule_time: Optional[datetime] = None


@router.post("/sessions")
async def create_session(
    data: TikTokSessionSetup,
    current_user=Depends(get_current_user)
):
    """
    Salva cookies de sessão do TikTok no Redis.
    
    O usuário deve exportar cookies do navegador usando extensão como
    'EditThisCookie' ou 'Cookie-Editor' e enviar aqui.
    
    A sessão é salva no Redis e pode ser restaurada automaticamente
    em caso de reinício do worker.
    """
    try:
        session = await session_manager.save_session(
            user_id=str(current_user.id),
            account_name=data.account_name,
            cookies=data.cookies,
            metadata={"source": "manual_import"}
        )
        
        return {
            "status": "success",
            "message": "Sessão salva com sucesso",
            "account_name": data.account_name,
            "session_id": session.id,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar sessão: {str(e)}"
        )


@router.get("/sessions")
async def list_sessions(current_user=Depends(get_current_user)):
    """Lista sessões TikTok do usuário."""
    sessions = await session_manager.list_sessions(str(current_user.id))
    
    return {
        "sessions": [
            {
                "account_name": s.account_name,
                "status": s.status.value,
                "created_at": s.created_at.isoformat(),
                "last_used": s.last_used.isoformat() if s.last_used else None,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                "upload_count": s.upload_count,
                "is_valid": s.status == TikTokSessionStatus.ACTIVE
            }
            for s in sessions
        ]
    }


@router.get("/sessions/{account_name}")
async def get_session(
    account_name: str,
    current_user=Depends(get_current_user)
):
    """Obtém detalhes de uma sessão específica."""
    health = await session_manager.get_session_health(
        str(current_user.id),
        account_name
    )
    
    if not health.get("exists"):
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    return health


@router.post("/sessions/{account_name}/backup")
async def backup_session(
    account_name: str,
    current_user=Depends(get_current_user)
):
    """Cria backup manual da sessão."""
    success = await session_manager.backup_session(
        str(current_user.id),
        account_name
    )
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Falha ao criar backup (sessão não encontrada?)"
        )
    
    return {"status": "success", "message": "Backup criado"}


@router.post("/sessions/{account_name}/restore")
async def restore_session(
    account_name: str,
    current_user=Depends(get_current_user)
):
    """Restaura sessão do backup mais recente."""
    session = await session_manager.restore_session(
        str(current_user.id),
        account_name
    )
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Nenhum backup encontrado"
        )
    
    return {
        "status": "success",
        "message": "Sessão restaurada",
        "account_name": session.account_name
    }


@router.put("/sessions/{account_name}/cookies")
async def update_cookies(
    account_name: str,
    cookies: List[dict],
    current_user=Depends(get_current_user)
):
    """
    Atualiza cookies de uma sessão existente.
    
    Cria backup da sessão antiga automaticamente.
    """
    success = await session_manager.update_cookies(
        str(current_user.id),
        account_name,
        cookies
    )
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Falha ao atualizar cookies"
        )
    
    return {"status": "success", "message": "Cookies atualizados"}


@router.delete("/sessions/{account_name}")
async def delete_session(
    account_name: str,
    keep_backups: bool = True,
    current_user=Depends(get_current_user)
):
    """Remove sessão (opcionalmente mantém backups)."""
    success = await session_manager.delete_session(
        str(current_user.id),
        account_name,
        keep_backups=keep_backups
    )
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Falha ao remover sessão"
        )
    
    return {"status": "success", "message": "Sessão removida"}


@router.post("/upload")
async def upload_video(
    account_name: str = Form(...),
    caption: str = Form(...),
    hashtags: str = Form(""),
    privacy: str = Form("public"),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    """
    Faz upload de vídeo para o TikTok.
    
    Args:
        account_name: Nome da conta configurada
        caption: Descrição do vídeo
        hashtags: Hashtags separadas por vírgula
        privacy: public, friends, private
        file: Arquivo de vídeo (mp4)
    """
    # Verificar sessão
    sessions_dir = os.path.join(settings.DATA_DIR, "tiktok_sessions")
    cookies_file = os.path.join(
        sessions_dir, 
        f"{current_user.id}_{account_name}.json"
    )
    
    if not os.path.exists(cookies_file):
        raise HTTPException(
            status_code=404,
            detail=f"Sessão '{account_name}' não encontrada"
        )
    
    # Salvar arquivo temporariamente
    temp_dir = os.path.join(settings.DATA_DIR, "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(temp_dir, f"tiktok_{timestamp}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Configurar cliente
        config = TikTokConfig(
            cookies_file=cookies_file,
            headless=True
        )
        client = TikTokClient(config)
        
        # Configurar vídeo
        hashtag_list = [h.strip() for h in hashtags.split(",") if h.strip()]
        
        privacy_map = {
            "public": Privacy.PUBLIC,
            "friends": Privacy.FRIENDS,
            "private": Privacy.PRIVATE
        }
        
        video_config = VideoConfig(
            caption=caption,
            hashtags=hashtag_list,
            privacy=privacy_map.get(privacy, Privacy.PUBLIC)
        )
        
        # Fazer upload
        result = await client.upload_video(file_path, video_config)
        
        if result.status.value == "failed":
            raise HTTPException(
                status_code=500,
                detail=result.error or "Upload falhou"
            )
        
        return {
            "status": result.status.value,
            "video_id": result.video_id,
            "url": result.url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Fechar driver se existir
        try:
            if hasattr(client, '_driver') and client._driver:
                client._driver.quit()
        except Exception:
            pass
