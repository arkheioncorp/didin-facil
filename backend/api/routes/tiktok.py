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
import json
from datetime import datetime

from api.middleware.auth import get_current_user
from vendor.tiktok.client import (
    TikTokClient, TikTokConfig, VideoConfig, Privacy
)
from shared.config import settings

router = APIRouter()


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
    Salva cookies de sessão do TikTok.
    
    O usuário deve exportar cookies do navegador usando extensão como
    'EditThisCookie' ou 'Cookie-Editor' e enviar aqui.
    """
    sessions_dir = os.path.join(settings.DATA_DIR, "tiktok_sessions")
    os.makedirs(sessions_dir, exist_ok=True)
    
    cookies_file = os.path.join(
        sessions_dir, 
        f"{current_user.id}_{data.account_name}.json"
    )
    
    with open(cookies_file, 'w') as f:
        json.dump(data.cookies, f)
    
    return {
        "status": "success",
        "message": "Sessão salva com sucesso",
        "account_name": data.account_name
    }


@router.get("/sessions")
async def list_sessions(current_user=Depends(get_current_user)):
    """Lista sessões TikTok do usuário."""
    sessions_dir = os.path.join(settings.DATA_DIR, "tiktok_sessions")
    
    if not os.path.exists(sessions_dir):
        return {"sessions": []}
    
    sessions = []
    prefix = f"{current_user.id}_"
    
    for filename in os.listdir(sessions_dir):
        if filename.startswith(prefix) and filename.endswith('.json'):
            account_name = filename[len(prefix):-5]
            sessions.append({
                "account_name": account_name,
                "file": filename
            })
    
    return {"sessions": sessions}


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
