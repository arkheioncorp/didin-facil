"""
Social Media Authentication Routes
Autenticação OAuth centralizada para múltiplas plataformas
"""

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from api.middleware.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from shared.config import settings
from shared.redis import get_redis

router = APIRouter()


# ==================== SCHEMAS ====================

class OAuthInitRequest(BaseModel):
    """Request para iniciar autenticação OAuth."""
    platform: str  # instagram, tiktok, youtube
    account_name: str
    scopes: Optional[List[str]] = None


class OAuthCallbackData(BaseModel):
    """Dados do callback OAuth."""
    code: str
    state: str


class TokenRefreshRequest(BaseModel):
    """Request para refresh de token."""
    platform: str
    account_name: str


class ConnectedAccount(BaseModel):
    """Conta conectada."""
    platform: str
    account_name: str
    username: Optional[str] = None
    connected_at: datetime
    expires_at: Optional[datetime] = None
    status: str  # active, expired, revoked


# ==================== ENCRYPTION UTILS ====================

def encrypt_token(token: str, user_id: str) -> str:
    """Encripta token para armazenamento."""
    # Usar chave derivada do user_id + secret
    key = hashlib.sha256(
        f"{settings.JWT_SECRET_KEY}:{user_id}".encode()
    ).hexdigest()[:32]
    
    # Simple XOR encryption (use Fernet in production)
    encrypted = ''.join(
        chr(ord(c) ^ ord(key[i % len(key)]))
        for i, c in enumerate(token)
    )
    return encrypted.encode('utf-8').hex()


def decrypt_token(encrypted: str, user_id: str) -> str:
    """Decripta token armazenado."""
    key = hashlib.sha256(
        f"{settings.JWT_SECRET_KEY}:{user_id}".encode()
    ).hexdigest()[:32]
    
    decrypted_bytes = bytes.fromhex(encrypted)
    decrypted = ''.join(
        chr(b ^ ord(key[i % len(key)]))
        for i, b in enumerate(decrypted_bytes)
    )
    return decrypted


# ==================== PLATFORM CONFIGS ====================

PLATFORM_CONFIGS = {
    "instagram": {
        "auth_url": "https://api.instagram.com/oauth/authorize",
        "token_url": "https://api.instagram.com/oauth/access_token",
        "refresh_url": "https://graph.instagram.com/refresh_access_token",
        "scopes": ["user_profile", "user_media"],
        "client_id_env": "INSTAGRAM_CLIENT_ID",
        "client_secret_env": "INSTAGRAM_CLIENT_SECRET",
    },
    "tiktok": {
        "auth_url": "https://www.tiktok.com/v2/auth/authorize",
        "token_url": "https://open.tiktokapis.com/v2/oauth/token/",
        "refresh_url": "https://open.tiktokapis.com/v2/oauth/token/",
        "scopes": ["user.info.basic", "video.upload"],
        "client_id_env": "TIKTOK_CLIENT_KEY",
        "client_secret_env": "TIKTOK_CLIENT_SECRET",
    },
    "tiktok_shop": {
        "auth_url": "https://services.tiktokshop.com/open/authorize",
        "token_url": "https://auth.tiktok-shops.com/api/v2/token/get",
        "refresh_url": "https://auth.tiktok-shops.com/api/v2/token/refresh",
        "scopes": [
            "product.read",
            "product.write", 
            "order.read",
            "order.write",
            "shop.read",
            "inventory.read",
            "inventory.write"
        ],
        "client_id_env": "TIKTOK_SHOP_APP_KEY",
        "client_secret_env": "TIKTOK_SHOP_APP_SECRET",
    },
    "youtube": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "refresh_url": "https://oauth2.googleapis.com/token",
        "scopes": [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly"
        ],
        "client_id_env": "GOOGLE_CLIENT_ID",
        "client_secret_env": "GOOGLE_CLIENT_SECRET",
    },
}


def get_platform_config(platform: str) -> Dict[str, Any]:
    """Retorna configuração da plataforma."""
    if platform not in PLATFORM_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Plataforma '{platform}' não suportada"
        )
    return PLATFORM_CONFIGS[platform]


def get_client_credentials(platform: str) -> tuple[str, str]:
    """Retorna client_id e client_secret da plataforma."""
    config = get_platform_config(platform)
    
    client_id = getattr(settings, config["client_id_env"], None)
    client_secret = getattr(settings, config["client_secret_env"], None)
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=503,
            detail=f"Credenciais OAuth para {platform} não configuradas"
        )
    
    return client_id, client_secret


# ==================== OAUTH ROUTES ====================

@router.post("/init")
async def init_oauth(
    data: OAuthInitRequest,
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Inicia fluxo OAuth para plataforma.
    
    Retorna URL de autorização para redirecionar o usuário.
    """
    config = get_platform_config(data.platform)
    client_id, _ = get_client_credentials(data.platform)
    
    # Gerar state único para segurança
    state = secrets.token_urlsafe(32)
    
    # Salvar state no Redis para validação posterior
    redis = await get_redis()
    state_data = {
        "user_id": current_user["id"],
        "platform": data.platform,
        "account_name": data.account_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await redis.set(
        f"oauth:state:{state}",
        json.dumps(state_data),
        ex=600  # 10 minutos para completar
    )
    
    # Construir URL de autorização
    scopes = data.scopes or config["scopes"]
    redirect_uri = f"{settings.API_URL}/social-auth/callback/{data.platform}"
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes) if isinstance(scopes, list) else scopes,
        "state": state,
    }
    
    # Parâmetros específicos por plataforma
    if data.platform == "youtube":
        params["access_type"] = "offline"
        params["prompt"] = "consent"
    elif data.platform == "tiktok":
        params["client_key"] = client_id
        del params["client_id"]
    
    # Construir URL
    query = "&".join(f"{k}={v}" for k, v in params.items())
    auth_url = f"{config['auth_url']}?{query}"
    
    return {
        "auth_url": auth_url,
        "state": state,
        "expires_in": 600
    }


@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None)
):
    """
    Callback OAuth após autorização do usuário.
    
    Troca código por tokens e armazena de forma segura.
    """
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Autorização negada: {error}"
        )
    
    # Validar state
    redis = await get_redis()
    state_data_raw = await redis.get(f"oauth:state:{state}")
    
    if not state_data_raw:
        raise HTTPException(
            status_code=400,
            detail="Estado inválido ou expirado"
        )
    
    state_data = json.loads(state_data_raw)
    await redis.delete(f"oauth:state:{state}")
    
    # Verificar plataforma
    if state_data["platform"] != platform:
        raise HTTPException(
            status_code=400,
            detail="Plataforma não corresponde ao state"
        )
    
    # Trocar código por tokens
    config = get_platform_config(platform)
    client_id, client_secret = get_client_credentials(platform)
    redirect_uri = f"{settings.API_URL}/social-auth/callback/{platform}"
    
    token_data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    
    # TikTok usa client_key
    if platform == "tiktok":
        token_data["client_key"] = client_id
        del token_data["client_id"]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            config["token_url"],
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao obter tokens: {response.text}"
            )
        
        tokens = response.json()
    
    # Armazenar tokens de forma segura
    user_id = state_data["user_id"]
    account_name = state_data["account_name"]
    
    # Encriptar tokens sensíveis
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    
    stored_data = {
        "access_token": encrypt_token(access_token, user_id),
        "refresh_token": (
            encrypt_token(refresh_token, user_id)
            if refresh_token else None
        ),
        "token_type": tokens.get("token_type", "Bearer"),
        "expires_in": tokens.get("expires_in"),
        "scope": tokens.get("scope"),
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform,
        "account_name": account_name,
    }
    
    # Calcular expiração
    if stored_data["expires_in"]:
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=stored_data["expires_in"]
        )
        stored_data["expires_at"] = expires_at.isoformat()
    
    # Salvar no Redis com TTL apropriado
    ttl = stored_data["expires_in"] or 3600 * 24 * 90  # 90 dias default
    await redis.set(
        f"oauth:tokens:{user_id}:{platform}:{account_name}",
        json.dumps(stored_data),
        ex=ttl
    )
    
    # Redirecionar para frontend com sucesso
    frontend_url = settings.FRONTEND_URL or settings.APP_URL
    return Response(
        status_code=302,
        headers={
            "Location": f"{frontend_url}/settings/accounts?"
                       f"platform={platform}&status=connected"
        }
    )


@router.post("/refresh")
async def refresh_token(
    data: TokenRefreshRequest,
    current_user=Depends(get_current_user)
):
    """
    Atualiza access_token usando refresh_token.
    """
    redis = await get_redis()
    user_id = current_user["id"]
    
    # Buscar tokens atuais
    token_key = f"oauth:tokens:{user_id}:{data.platform}:{data.account_name}"
    stored_raw = await redis.get(token_key)
    
    if not stored_raw:
        raise HTTPException(
            status_code=404,
            detail="Conta não encontrada"
        )
    
    stored = json.loads(stored_raw)
    
    if not stored.get("refresh_token"):
        raise HTTPException(
            status_code=400,
            detail="Refresh token não disponível para esta conta"
        )
    
    # Decriptar refresh token
    refresh_token = decrypt_token(stored["refresh_token"], user_id)
    
    # Fazer refresh
    config = get_platform_config(data.platform)
    client_id, client_secret = get_client_credentials(data.platform)
    
    refresh_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            config["refresh_url"],
            data=refresh_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao renovar token: {response.text}"
            )
        
        tokens = response.json()
    
    # Atualizar tokens armazenados
    new_access = tokens.get("access_token")
    new_refresh = tokens.get("refresh_token", refresh_token)
    
    stored["access_token"] = encrypt_token(new_access, user_id)
    stored["refresh_token"] = encrypt_token(new_refresh, user_id)
    stored["expires_in"] = tokens.get("expires_in")
    stored["refreshed_at"] = datetime.now(timezone.utc).isoformat()
    
    if stored["expires_in"]:
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=stored["expires_in"]
        )
        stored["expires_at"] = expires_at.isoformat()
    
    ttl = stored["expires_in"] or 3600 * 24 * 90
    await redis.set(token_key, json.dumps(stored), ex=ttl)
    
    return {
        "status": "refreshed",
        "expires_at": stored.get("expires_at")
    }


@router.get("/accounts")
async def list_connected_accounts(
    current_user=Depends(get_current_user)
) -> Dict[str, List[ConnectedAccount]]:
    """
    Lista todas as contas conectadas do usuário.
    """
    redis = await get_redis()
    user_id = current_user["id"]
    
    accounts = []
    
    # Buscar todas as contas por plataforma
    for platform in PLATFORM_CONFIGS.keys():
        pattern = f"oauth:tokens:{user_id}:{platform}:*"
        
        # Usar scan para buscar keys
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern)
            
            for key in keys:
                data_raw = await redis.get(key)
                if data_raw:
                    data = json.loads(data_raw)
                    
                    # Determinar status
                    status = "active"
                    expires_at = None
                    if data.get("expires_at"):
                        expires_at = datetime.fromisoformat(data["expires_at"])
                        if expires_at < datetime.now(timezone.utc):
                            status = "expired"
                    
                    accounts.append(ConnectedAccount(
                        platform=data["platform"],
                        account_name=data["account_name"],
                        connected_at=datetime.fromisoformat(
                            data["connected_at"]
                        ),
                        expires_at=expires_at,
                        status=status
                    ))
            
            if cursor == 0:
                break
    
    return {"accounts": accounts}


@router.delete("/accounts/{platform}/{account_name}")
async def disconnect_account(
    platform: str,
    account_name: str,
    current_user=Depends(get_current_user)
):
    """
    Desconecta uma conta.
    """
    redis = await get_redis()
    user_id = current_user["id"]
    
    token_key = f"oauth:tokens:{user_id}:{platform}:{account_name}"
    
    # Verificar se existe
    if not await redis.exists(token_key):
        raise HTTPException(
            status_code=404,
            detail="Conta não encontrada"
        )
    
    # Deletar tokens
    await redis.delete(token_key)
    
    return {
        "status": "disconnected",
        "platform": platform,
        "account_name": account_name
    }


@router.get("/token/{platform}/{account_name}")
async def get_access_token(
    platform: str,
    account_name: str,
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retorna access token válido para uso interno.
    
    Faz refresh automático se necessário.
    """
    redis = await get_redis()
    user_id = current_user["id"]
    
    token_key = f"oauth:tokens:{user_id}:{platform}:{account_name}"
    stored_raw = await redis.get(token_key)
    
    if not stored_raw:
        raise HTTPException(
            status_code=404,
            detail="Conta não encontrada"
        )
    
    stored = json.loads(stored_raw)
    
    # Verificar se precisa refresh
    needs_refresh = False
    if stored.get("expires_at"):
        expires_at = datetime.fromisoformat(stored["expires_at"])
        # Refresh 5 minutos antes de expirar
        if expires_at < datetime.now(timezone.utc) + timedelta(minutes=5):
            needs_refresh = True
    
    if needs_refresh and stored.get("refresh_token"):
        # Fazer refresh automático
        await refresh_token(
            TokenRefreshRequest(
                platform=platform,
                account_name=account_name
            ),
            current_user
        )
        # Buscar tokens atualizados
        stored_raw = await redis.get(token_key)
        stored = json.loads(stored_raw)
    
    # Decriptar e retornar access token
    access_token = decrypt_token(stored["access_token"], user_id)
    
    return {
        "access_token": access_token,
        "token_type": stored.get("token_type", "Bearer"),
        "expires_at": stored.get("expires_at")
    }


# ==================== HEALTH CHECK ====================

@router.get("/platforms")
async def list_platforms():
    """Lista plataformas suportadas e status de configuração."""
    platforms = []
    
    for name, config in PLATFORM_CONFIGS.items():
        client_id = getattr(settings, config["client_id_env"], None)
        configured = bool(client_id)
        
        platforms.append({
            "name": name,
            "configured": configured,
            "scopes": config["scopes"]
        })
    
    return {"platforms": platforms}
