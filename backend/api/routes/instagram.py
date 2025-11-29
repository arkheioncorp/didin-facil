from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import shutil
import os
import json

from api.middleware.auth import get_current_user
from vendor.instagram.client import InstagramClient, InstagramConfig, PostConfig
from shared.redis import get_redis

router = APIRouter()


class InstagramLogin(BaseModel):
    username: str
    password: str
    verification_code: Optional[str] = None  # Código 2FA se necessário


class InstagramChallenge(BaseModel):
    username: str
    code: str
    method: Optional[str] = None  # sms ou email


class InstagramPost(BaseModel):
    username: str
    caption: str
    media_type: str = "photo"  # photo, video, reel


@router.post("/login")
async def login(data: InstagramLogin, current_user=Depends(get_current_user)):
    """
    Login to Instagram and save session.
    
    Se 2FA estiver ativo, retorna status 'challenge_required'.
    Use /challenge/resolve para enviar o código.
    """
    config = InstagramConfig(
        username=data.username,
        password=data.password,
        verification_code=data.verification_code
    )
    client = InstagramClient(config)
    
    try:
        success = await client.login()
        if success:
            settings = await client.get_settings()
            redis = await get_redis()
            await redis.set(
                f"instagram:session:{data.username}",
                json.dumps(settings),
                ex=60*60*24*30  # 30 days expiration
            )
            return {"status": "success", "message": "Logged in successfully"}
        else:
            raise HTTPException(status_code=401, detail="Login failed")
            
    except Exception as e:
        error_msg = str(e)
        
        # Verificar se é challenge de 2FA
        if "CHALLENGE_2FA_REQUIRED" in error_msg:
            # Salvar estado do challenge
            redis = await get_redis()
            await redis.set(
                f"instagram:challenge:{data.username}",
                json.dumps({"type": "2fa", "username": data.username}),
                ex=600  # 10 minutos para resolver
            )
            return {
                "status": "challenge_required",
                "challenge_type": "2fa",
                "message": "Enter your 2FA code"
            }
        
        # Challenge de verificação (SMS/Email)
        if "CHALLENGE_SMS_REQUIRED" in error_msg:
            redis = await get_redis()
            await redis.set(
                f"instagram:challenge:{data.username}",
                json.dumps({"type": "sms", "username": data.username}),
                ex=600
            )
            return {
                "status": "challenge_required",
                "challenge_type": "sms",
                "message": "Verification code sent to your phone"
            }
        
        if "CHALLENGE_EMAIL_REQUIRED" in error_msg:
            redis = await get_redis()
            await redis.set(
                f"instagram:challenge:{data.username}",
                json.dumps({"type": "email", "username": data.username}),
                ex=600
            )
            return {
                "status": "challenge_required",
                "challenge_type": "email",
                "message": "Verification code sent to your email"
            }
        
        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/challenge/resolve")
async def resolve_challenge(
    data: InstagramChallenge,
    current_user=Depends(get_current_user)
):
    """
    Resolve Instagram challenge with verification code.
    
    Use após receber 'challenge_required' no login.
    """
    redis = await get_redis()
    
    # Verificar se há challenge pendente
    challenge_data = await redis.get(f"instagram:challenge:{data.username}")
    if not challenge_data:
        raise HTTPException(
            status_code=400,
            detail="No pending challenge. Try logging in again."
        )
    
    json.loads(challenge_data)
    
    # Criar cliente com código de verificação
    config = InstagramConfig(
        username=data.username,
        password="",  # Senha não é necessária para resolver challenge
        verification_code=data.code
    )
    client = InstagramClient(config)
    
    try:
        # Inicializar cliente
        await client.login()
        
        # Se chegou aqui, challenge resolvido
        settings = await client.get_settings()
        
        # Salvar sessão
        await redis.set(
            f"instagram:session:{data.username}",
            json.dumps(settings),
            ex=60*60*24*30
        )
        
        # Limpar challenge
        await redis.delete(f"instagram:challenge:{data.username}")
        
        return {
            "status": "success",
            "message": "Challenge resolved, logged in successfully"
        }
        
    except Exception as e:
        error_msg = str(e)
        
        if "CHALLENGE" in error_msg:
            return {
                "status": "invalid_code",
                "message": "Invalid verification code"
            }
        
        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/challenge/request")
async def request_challenge_code(
    username: str,
    method: str = "email",
    current_user=Depends(get_current_user)
):
    """
    Solicita reenvio de código de verificação.
    
    Args:
        username: Username da conta
        method: 'sms' ou 'email'
    """
    config = InstagramConfig(username=username, password="")
    client = InstagramClient(config)
    
    try:
        success = await client.request_challenge_code(method)
        if success:
            return {
                "status": "success",
                "message": f"Verification code sent via {method}"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to request verification code"
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload")
async def upload_media(
    username: str = Form(...),
    caption: str = Form(...),
    media_type: str = Form(...),
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Upload media to Instagram."""
    redis = await get_redis()
    session_data = await redis.get(f"instagram:session:{username}")
    
    if not session_data:
        raise HTTPException(status_code=401, detail="User not logged in")
    
    # Restore session
    config = InstagramConfig(username=username, password="")
    client = InstagramClient(config)
    
    try:
        settings = json.loads(session_data)
        await client.load_settings(settings)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Failed to load session: {str(e)}")

    # Save file temporarily
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        post_config = PostConfig(caption=caption)
        
        if media_type == "photo":
            result = await client.upload_photo(file_path, post_config)
        elif media_type == "video":
            result = await client.upload_video(file_path, post_config)
        elif media_type == "reel":
            result = await client.upload_reel(file_path, post_config)
        else:
            raise HTTPException(status_code=400, detail="Invalid media type")
            
        return {"status": "success", "media_pk": result.get("pk")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
