import json
import os
import shutil
from typing import Optional

from api.middleware.auth import get_current_user
from api.middleware.subscription import get_subscription_service
from api.services.instagram_session import ChallengeStatus
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from integrations.instagram_hub import get_instagram_hub
from modules.subscription import SubscriptionService
from pydantic import BaseModel
from shared.redis import get_redis
from vendor.instagram.client import (InstagramClient, InstagramConfig,
                                     PostConfig)

router = APIRouter()
hub = get_instagram_hub()
session_manager = hub.session_manager


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
    current_user = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """Upload media to Instagram."""
    # Check subscription limits
    can_use = await service.can_use_feature(
        str(current_user["id"]),
        "social_posts"
    )
    if not can_use:
        raise HTTPException(
            status_code=402,
            detail="Limite de posts sociais atingido. Faça upgrade para continuar."
        )
    
    # Increment usage after successful check
    await service.increment_usage(str(current_user["id"]), "social_posts", 1)
    
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# =============================================================================
# Session Management Endpoints
# =============================================================================

@router.get("/sessions")
async def list_sessions(current_user=Depends(get_current_user)):
    """
    Lista todas as sessões Instagram do usuário.
    
    Retorna status de cada sessão (ativa, expirada, com challenge).
    """
    sessions = await session_manager.get_all_sessions()
    
    # Enriquecer com status de challenges
    result = []
    for session in sessions:
        challenges = await session_manager.get_active_challenges(session.username)
        result.append({
            "username": session.username,
            "status": session.status,
            "is_valid": session.is_valid,
            "last_used": session.last_used.isoformat() if session.last_used else None,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "active_challenges": len(challenges),
            "challenges": [
                {
                    "id": c.id,
                    "type": c.challenge_type.value,
                    "status": c.status.value,
                    "expires_at": c.expires_at.isoformat() if c.expires_at else None
                }
                for c in challenges
            ]
        })
    
    return {"sessions": result}


@router.get("/sessions/{username}")
async def get_session(username: str, current_user=Depends(get_current_user)):
    """
    Obtém detalhes de uma sessão específica.
    """
    session = await session_manager.get_session(username)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    challenges = await session_manager.get_active_challenges(username)
    
    return {
        "username": session.username,
        "status": session.status,
        "is_valid": session.is_valid,
        "last_used": session.last_used.isoformat() if session.last_used else None,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "metadata": session.metadata,
        "challenges": [
            {
                "id": c.id,
                "type": c.challenge_type.value,
                "status": c.status.value,
                "message": c.message,
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                "created_at": c.created_at.isoformat(),
                "attempts": c.attempts
            }
            for c in challenges
        ]
    }


@router.post("/sessions/{username}/backup")
async def backup_session(username: str, current_user=Depends(get_current_user)):
    """
    Força backup manual da sessão.
    
    Útil antes de operações de risco ou manutenção.
    """
    redis = await get_redis()
    session_data = await redis.get(f"instagram:session:{username}")
    
    if not session_data:
        raise HTTPException(status_code=404, detail="No active session to backup")
    
    settings = json.loads(session_data)
    success = await session_manager.backup_session(username, settings)
    
    if success:
        return {"status": "success", "message": "Session backed up successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to backup session")


@router.post("/sessions/{username}/restore")
async def restore_session(username: str, current_user=Depends(get_current_user)):
    """
    Restaura sessão do backup mais recente.
    
    Útil quando a sessão atual está corrompida ou expirada.
    """
    settings = await session_manager.restore_session(username)
    
    if not settings:
        raise HTTPException(status_code=404, detail="No backup found for this session")
    
    # Testar se a sessão restaurada é válida
    config = InstagramConfig(username=username, password="")
    client = InstagramClient(config)
    
    try:
        await client.load_settings(settings)
        
        # Salvar como sessão ativa
        redis = await get_redis()
        await redis.set(
            f"instagram:session:{username}",
            json.dumps(settings),
            ex=60*60*24*30
        )
        
        return {"status": "success", "message": "Session restored successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Restored session is invalid: {str(e)}")


@router.delete("/sessions/{username}")
async def delete_session(username: str, current_user=Depends(get_current_user)):
    """
    Remove sessão e todos os backups.
    
    CUIDADO: Operação irreversível.
    """
    redis = await get_redis()
    
    # Remover sessão ativa
    await redis.delete(f"instagram:session:{username}")
    
    # Remover challenges
    await redis.delete(f"instagram:challenge:{username}")
    
    # Remover backups (pattern matching)
    keys = await redis.keys(f"instagram:session:backup:{username}:*")
    if keys:
        await redis.delete(*keys)
    
    return {"status": "success", "message": "Session and all backups deleted"}


# =============================================================================
# Challenge Management Endpoints
# =============================================================================

@router.get("/challenges")
async def list_challenges(
    username: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """
    Lista todos os challenges ativos.
    
    Pode filtrar por username específico.
    """
    challenges = await session_manager.get_active_challenges(username)
    
    return {
        "challenges": [
            {
                "id": c.id,
                "username": c.username,
                "type": c.challenge_type.value,
                "status": c.status.value,
                "message": c.message,
                "created_at": c.created_at.isoformat(),
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                "attempts": c.attempts,
                "max_attempts": c.max_attempts
            }
            for c in challenges
        ],
        "total": len(challenges)
    }


@router.get("/challenges/{challenge_id}")
async def get_challenge(challenge_id: str, current_user=Depends(get_current_user)):
    """
    Obtém detalhes de um challenge específico.
    """
    challenge = await session_manager.get_challenge(challenge_id)
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    return {
        "id": challenge.id,
        "username": challenge.username,
        "type": challenge.challenge_type.value,
        "status": challenge.status.value,
        "message": challenge.message,
        "created_at": challenge.created_at.isoformat(),
        "expires_at": challenge.expires_at.isoformat() if challenge.expires_at else None,
        "resolved_at": challenge.resolved_at.isoformat() if challenge.resolved_at else None,
        "attempts": challenge.attempts,
        "max_attempts": challenge.max_attempts,
        "metadata": challenge.metadata
    }


@router.post("/challenges/{challenge_id}/resolve")
async def resolve_challenge_by_id(
    challenge_id: str,
    code: str,
    current_user=Depends(get_current_user)
):
    """
    Resolve um challenge pelo ID.
    
    Endpoint alternativo ao /challenge/resolve que usa o ID do challenge.
    """
    challenge = await session_manager.get_challenge(challenge_id)
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    if challenge.status != ChallengeStatus.PENDING and challenge.status != ChallengeStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=400,
            detail=f"Challenge is {challenge.status.value}, cannot resolve"
        )
    
    if challenge.attempts >= challenge.max_attempts:
        await session_manager.update_challenge_status(
            challenge_id, ChallengeStatus.FAILED, "Max attempts exceeded"
        )
        raise HTTPException(status_code=400, detail="Max attempts exceeded")
    
    # Incrementar tentativas
    await session_manager.increment_challenge_attempts(challenge_id)
    
    # Tentar resolver via cliente Instagram
    config = InstagramConfig(
        username=challenge.username,
        password="",
        verification_code=code
    )
    client = InstagramClient(config)
    
    try:
        await client.login()
        settings = await client.get_settings()
        
        # Salvar sessão
        redis = await get_redis()
        await redis.set(
            f"instagram:session:{challenge.username}",
            json.dumps(settings),
            ex=60*60*24*30
        )
        
        # Backup automático
        await session_manager.backup_session(challenge.username, settings)
        
        # Marcar challenge como resolvido
        await session_manager.update_challenge_status(
            challenge_id, ChallengeStatus.RESOLVED
        )
        
        return {
            "status": "success",
            "message": "Challenge resolved successfully"
        }
        
    except Exception as e:
        error_msg = str(e)
        
        if "INVALID_CODE" in error_msg or "CHALLENGE" in error_msg:
            return {
                "status": "invalid_code",
                "message": "Invalid verification code",
                "attempts_remaining": challenge.max_attempts - challenge.attempts - 1
            }
        
        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/challenges/{challenge_id}/request-code")
async def request_challenge_code_by_id(
    challenge_id: str,
    method: str = "email",
    current_user=Depends(get_current_user)
):
    """
    Solicita reenvio de código para um challenge.
    """
    challenge = await session_manager.get_challenge(challenge_id)
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    config = InstagramConfig(username=challenge.username, password="")
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


# =============================================================================
# Health Check & Status
# =============================================================================

@router.get("/health")
async def instagram_health(current_user=Depends(get_current_user)):
    """
    Status geral do serviço Instagram.
    
    Retorna métricas de sessões e challenges.
    """
    sessions = await session_manager.get_all_sessions()
    all_challenges = await session_manager.get_active_challenges()
    
    valid_sessions = [s for s in sessions if s.is_valid]
    pending_challenges = [c for c in all_challenges if c.status == ChallengeStatus.PENDING]
    
    return {
        "status": "healthy",
        "sessions": {
            "total": len(sessions),
            "valid": len(valid_sessions),
            "expired": len(sessions) - len(valid_sessions)
        },
        "challenges": {
            "total": len(all_challenges),
            "pending": len(pending_challenges),
            "by_type": _count_by_type(all_challenges)
        }
    }


def _count_by_type(challenges: list) -> dict:
    """Helper para contar challenges por tipo."""
    counts = {}
    for c in challenges:
        type_name = c.challenge_type.value
        counts[type_name] = counts.get(type_name, 0) + 1
    return counts
