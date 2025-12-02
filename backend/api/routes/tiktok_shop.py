"""
TikTok Shop API Integration
Endpoints para integração com a API oficial do TikTok Shop

Documentação: https://partner.tiktokshop.com/docv2/page/650aa5e04a0bb702c0570327
"""

import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from api.middleware.auth import get_current_user, get_current_user_optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from shared.config import settings
from shared.redis import get_redis

router = APIRouter()


# ==================== SCHEMAS ====================

class TikTokShopAuth(BaseModel):
    """Dados de autenticação TikTok Shop."""
    access_token: str
    refresh_token: str
    access_token_expire_in: int
    refresh_token_expire_in: int
    open_id: str
    seller_name: Optional[str] = None


class TikTokShopProduct(BaseModel):
    """Produto do TikTok Shop."""
    product_id: str
    title: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    currency: str = "BRL"
    stock_quantity: int = 0
    images: List[str] = []
    category_id: Optional[str] = None
    status: str = "active"


class TikTokShopConfig(BaseModel):
    """Configuração para scraping do TikTok Shop."""
    shop_id: Optional[str] = None
    categories: List[str] = []
    max_products: int = 100


# ==================== TIKTOK SHOP API CLIENT ====================

class TikTokShopClient:
    """
    Cliente para API oficial do TikTok Shop.
    
    Usa OAuth 2.0 para autenticação e assinatura HMAC para requests.
    """
    
    BASE_URL = "https://open-api.tiktokglobalshop.com"
    AUTH_URL = "https://services.tiktokshop.com/open/authorize"
    TOKEN_URL = "https://auth.tiktok-shops.com/api/v2/token/get"
    REFRESH_URL = "https://auth.tiktok-shops.com/api/v2/token/refresh"
    
    def __init__(self):
        self.app_key = settings.TIKTOK_SHOP_APP_KEY
        self.app_secret = settings.TIKTOK_SHOP_APP_SECRET
        self.service_id = settings.TIKTOK_SHOP_SERVICE_ID
        
        if not self.app_key or not self.app_secret:
            raise ValueError("TikTok Shop credentials not configured")
    
    def generate_sign(self, path: str, params: Dict, timestamp: int) -> str:
        """
        Gera assinatura HMAC-SHA256 para request.
        
        Formato: app_secret + path + params_ordenados + timestamp + app_secret
        """
        # Ordenar parâmetros alfabeticamente
        sorted_params = "&".join(
            f"{k}={v}" for k, v in sorted(params.items())
        )
        
        # Construir string base
        base_string = f"{self.app_secret}{path}{sorted_params}{timestamp}{self.app_secret}"
        
        # Gerar HMAC-SHA256
        signature = hmac.new(
            self.app_secret.encode(),
            base_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        """
        Gera URL de autorização OAuth para TikTok Shop.
        """
        params = {
            "app_key": self.app_key,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        
        if self.service_id:
            params["service_id"] = self.service_id
        
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    async def exchange_code_for_token(
        self, 
        code: str
    ) -> TikTokShopAuth:
        """
        Troca authorization code por access token.
        """
        params = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "auth_code": code,
            "grant_type": "authorized_code",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.TOKEN_URL,
                params=params,
                timeout=30.0
            )
            
            data = response.json()
            
            if data.get("code") != 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"TikTok Shop auth error: {data.get('message')}"
                )
            
            token_data = data.get("data", {})
            return TikTokShopAuth(
                access_token=token_data.get("access_token"),
                refresh_token=token_data.get("refresh_token"),
                access_token_expire_in=token_data.get("access_token_expire_in", 0),
                refresh_token_expire_in=token_data.get("refresh_token_expire_in", 0),
                open_id=token_data.get("open_id", ""),
                seller_name=token_data.get("seller_name"),
            )
    
    async def refresh_token(self, refresh_token: str) -> TikTokShopAuth:
        """
        Renova access token usando refresh token.
        """
        params = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.REFRESH_URL,
                params=params,
                timeout=30.0
            )
            
            data = response.json()
            
            if data.get("code") != 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Token refresh error: {data.get('message')}"
                )
            
            token_data = data.get("data", {})
            return TikTokShopAuth(
                access_token=token_data.get("access_token"),
                refresh_token=token_data.get("refresh_token"),
                access_token_expire_in=token_data.get("access_token_expire_in", 0),
                refresh_token_expire_in=token_data.get("refresh_token_expire_in", 0),
                open_id=token_data.get("open_id", ""),
            )
    
    async def api_request(
        self,
        method: str,
        path: str,
        access_token: str,
        shop_id: str,
        params: Optional[Dict] = None,
        body: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Faz request autenticada para API do TikTok Shop.
        """
        timestamp = int(time.time())
        
        # Parâmetros base
        query_params = {
            "app_key": self.app_key,
            "timestamp": str(timestamp),
            "shop_id": shop_id,
            "access_token": access_token,
            **(params or {})
        }
        
        # Gerar assinatura
        sign = self.generate_sign(path, query_params, timestamp)
        query_params["sign"] = sign
        
        url = f"{self.BASE_URL}{path}"
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(
                    url,
                    params=query_params,
                    timeout=30.0
                )
            else:
                response = await client.request(
                    method.upper(),
                    url,
                    params=query_params,
                    json=body,
                    timeout=30.0
                )
            
            return response.json()
    
    async def get_products(
        self,
        access_token: str,
        shop_id: str,
        page_size: int = 50,
        page_number: int = 1,
        status: str = "LIVE"
    ) -> List[Dict]:
        """
        Busca produtos da loja no TikTok Shop.
        
        Status: DRAFT, PENDING, LIVE, SUSPENDED, DELETED
        """
        body = {
            "page_size": page_size,
            "page_number": page_number,
            "search_status": status
        }
        
        response = await self.api_request(
            method="POST",
            path="/api/products/search",
            access_token=access_token,
            shop_id=shop_id,
            body=body
        )
        
        if response.get("code") != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Error fetching products: {response.get('message')}"
            )
        
        return response.get("data", {}).get("products", [])
    
    async def get_product_detail(
        self,
        access_token: str,
        shop_id: str,
        product_id: str
    ) -> Dict:
        """
        Busca detalhes de um produto específico.
        """
        response = await self.api_request(
            method="GET",
            path=f"/api/products/details",
            access_token=access_token,
            shop_id=shop_id,
            params={"product_id": product_id}
        )
        
        if response.get("code") != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Error fetching product: {response.get('message')}"
            )
        
        return response.get("data", {})
    
    async def get_shop_info(
        self,
        access_token: str,
        shop_id: str
    ) -> Dict:
        """
        Busca informações da loja.
        """
        response = await self.api_request(
            method="GET",
            path="/api/shop/get_authorized_shop",
            access_token=access_token,
            shop_id=shop_id
        )
        
        if response.get("code") != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Error fetching shop info: {response.get('message')}"
            )
        
        return response.get("data", {})


# ==================== ROUTES ====================

@router.get("/auth/url")
async def get_auth_url(
    current_user=Depends(get_current_user)
) -> Dict[str, str]:
    """
    Gera URL de autorização para TikTok Shop.
    
    O usuário deve ser redirecionado para esta URL para autorizar
    o acesso à sua loja TikTok Shop.
    """
    try:
        client = TikTokShopClient()
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail="TikTok Shop API não configurada. Configure TIKTOK_SHOP_APP_KEY e TIKTOK_SHOP_APP_SECRET."
        )
    
    # Gerar state para CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Salvar state no Redis
    redis = await get_redis()
    state_data = {
        "user_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await redis.set(
        f"tiktok_shop:state:{state}",
        json.dumps(state_data),
        ex=600  # 10 minutos
    )
    
    # URL de callback
    redirect_uri = f"https://arkheion-tiktrend.com.br/api/tiktok-shop/callback"
    
    auth_url = client.get_auth_url(redirect_uri, state)
    
    return {
        "auth_url": auth_url,
        "state": state,
        "redirect_uri": redirect_uri,
        "expires_in": 600
    }


@router.get("/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from TikTok"),
    state: str = Query(..., description="State for CSRF validation"),
):
    """
    Callback OAuth do TikTok Shop.
    
    Esta URL deve ser configurada no TikTok Shop Partner Center:
    https://arkheion-tiktrend.com.br/api/tiktok-shop/callback
    """
    # Validar state
    redis = await get_redis()
    state_data_raw = await redis.get(f"tiktok_shop:state:{state}")
    
    if not state_data_raw:
        raise HTTPException(
            status_code=400,
            detail="Estado inválido ou expirado. Por favor, tente novamente."
        )
    
    state_data = json.loads(state_data_raw)
    await redis.delete(f"tiktok_shop:state:{state}")
    
    # Trocar code por tokens
    try:
        client = TikTokShopClient()
        auth = await client.exchange_code_for_token(code)
    except ValueError:
        raise HTTPException(
            status_code=503,
            detail="TikTok Shop API não configurada"
        )
    
    # Salvar tokens no Redis (encriptados em produção)
    user_id = state_data["user_id"]
    token_data = {
        "access_token": auth.access_token,
        "refresh_token": auth.refresh_token,
        "access_token_expire_in": auth.access_token_expire_in,
        "refresh_token_expire_in": auth.refresh_token_expire_in,
        "open_id": auth.open_id,
        "seller_name": auth.seller_name,
        "connected_at": datetime.now(timezone.utc).isoformat()
    }
    
    await redis.set(
        f"tiktok_shop:tokens:{user_id}",
        json.dumps(token_data),
        ex=auth.refresh_token_expire_in or 86400 * 30  # 30 dias default
    )
    
    # Redirecionar para página de sucesso
    return {
        "success": True,
        "message": "TikTok Shop conectado com sucesso!",
        "seller_name": auth.seller_name,
        "open_id": auth.open_id
    }


@router.get("/status")
async def get_connection_status(
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verifica status da conexão com TikTok Shop.
    """
    redis = await get_redis()
    token_data_raw = await redis.get(f"tiktok_shop:tokens:{current_user['id']}")
    
    if not token_data_raw:
        return {
            "connected": False,
            "message": "TikTok Shop não conectado"
        }
    
    token_data = json.loads(token_data_raw)
    
    return {
        "connected": True,
        "seller_name": token_data.get("seller_name"),
        "open_id": token_data.get("open_id"),
        "connected_at": token_data.get("connected_at")
    }


@router.post("/disconnect")
async def disconnect(
    current_user=Depends(get_current_user)
) -> Dict[str, str]:
    """
    Desconecta TikTok Shop.
    """
    redis = await get_redis()
    await redis.delete(f"tiktok_shop:tokens:{current_user['id']}")
    
    return {"message": "TikTok Shop desconectado com sucesso"}


@router.get("/products")
async def get_products(
    shop_id: str = Query(..., description="ID da loja no TikTok Shop"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    status: str = Query("LIVE", description="DRAFT, PENDING, LIVE, SUSPENDED"),
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Lista produtos da loja no TikTok Shop.
    
    Retorna produtos reais com preços.
    """
    redis = await get_redis()
    token_data_raw = await redis.get(f"tiktok_shop:tokens:{current_user['id']}")
    
    if not token_data_raw:
        raise HTTPException(
            status_code=401,
            detail="TikTok Shop não conectado. Autorize primeiro em /auth/url"
        )
    
    token_data = json.loads(token_data_raw)
    
    try:
        client = TikTokShopClient()
        products = await client.get_products(
            access_token=token_data["access_token"],
            shop_id=shop_id,
            page_size=per_page,
            page_number=page,
            status=status
        )
        
        return {
            "products": products,
            "page": page,
            "per_page": per_page,
            "total": len(products)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar produtos: {str(e)}"
        )


@router.get("/products/{product_id}")
async def get_product_detail(
    product_id: str,
    shop_id: str = Query(..., description="ID da loja"),
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Busca detalhes de um produto específico.
    """
    redis = await get_redis()
    token_data_raw = await redis.get(f"tiktok_shop:tokens:{current_user['id']}")
    
    if not token_data_raw:
        raise HTTPException(
            status_code=401,
            detail="TikTok Shop não conectado"
        )
    
    token_data = json.loads(token_data_raw)
    
    try:
        client = TikTokShopClient()
        product = await client.get_product_detail(
            access_token=token_data["access_token"],
            shop_id=shop_id,
            product_id=product_id
        )
        
        return product
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar produto: {str(e)}"
        )


@router.get("/shop")
async def get_shop_info(
    shop_id: str = Query(..., description="ID da loja"),
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Busca informações da loja.
    """
    redis = await get_redis()
    token_data_raw = await redis.get(f"tiktok_shop:tokens:{current_user['id']}")
    
    if not token_data_raw:
        raise HTTPException(
            status_code=401,
            detail="TikTok Shop não conectado"
        )
    
    token_data = json.loads(token_data_raw)
    
    try:
        client = TikTokShopClient()
        shop = await client.get_shop_info(
            access_token=token_data["access_token"],
            shop_id=shop_id
        )
        
        return shop
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar informações da loja: {str(e)}"
        )


# ==================== LOCAL AUTH (User Credentials) ====================

class UserTikTokShopCredentials(BaseModel):
    """Credenciais do TikTok Shop fornecidas pelo usuário."""
    app_key: str
    app_secret: str
    code: str
    service_id: Optional[str] = None


class LocalAuthUrlRequest(BaseModel):
    """Request para gerar URL de autorização local."""
    app_key: str
    service_id: Optional[str] = None


@router.post("/local/auth-url")
async def get_local_auth_url(
    data: LocalAuthUrlRequest,
    current_user=Depends(get_current_user_optional)
) -> Dict[str, str]:
    """
    Gera URL de autorização usando credenciais do próprio usuário.
    
    Para uso local onde cada usuário tem suas próprias credenciais TikTok Shop.
    """
    state = secrets.token_urlsafe(16)
    
    # Salvar state no Redis (mesmo sem user logado, usar IP ou session)
    redis = await get_redis()
    user_id = current_user["id"] if current_user else "anonymous"
    
    await redis.set(
        f"tiktok_shop:local_state:{state}",
        json.dumps({
            "user_id": user_id,
            "app_key": data.app_key,
            "created_at": datetime.now(timezone.utc).isoformat()
        }),
        ex=600
    )
    
    params = {
        "app_key": data.app_key,
        "state": state,
    }
    
    if data.service_id:
        params["service_id"] = data.service_id
    
    auth_url = f"https://services.tiktokshop.com/open/authorize?{urlencode(params)}"
    
    return {
        "auth_url": auth_url,
        "state": state,
        "expires_in": 600,
        "instructions": "Após autorizar, copie o código da URL (após 'code=') e use no endpoint /token"
    }


@router.post("/token")
async def exchange_token_with_user_credentials(
    data: UserTikTokShopCredentials,
    current_user=Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Troca código por token usando credenciais fornecidas pelo usuário.
    
    Permite que cada usuário use suas próprias credenciais TikTok Shop.
    """
    params = {
        "app_key": data.app_key,
        "app_secret": data.app_secret,
        "auth_code": data.code,
        "grant_type": "authorized_code",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://auth.tiktok-shops.com/api/v2/token/get",
            params=params,
            timeout=30.0
        )
        
        result = response.json()
        
        if result.get("code") != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Erro na autenticação: {result.get('message', 'Código inválido')}"
            )
        
        token_data = result.get("data", {})
        
        # Salvar tokens no Redis para o usuário
        redis = await get_redis()
        user_id = current_user["id"] if current_user else "anonymous"
        
        save_data = {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "access_token_expire_in": token_data.get("access_token_expire_in", 0),
            "refresh_token_expire_in": token_data.get("refresh_token_expire_in", 0),
            "open_id": token_data.get("open_id", ""),
            "seller_name": token_data.get("seller_name"),
            "app_key": data.app_key,  # Salvar para uso futuro
            "connected_at": datetime.now(timezone.utc).isoformat()
        }
        
        ttl = token_data.get("refresh_token_expire_in", 86400 * 30)
        await redis.set(
            f"tiktok_shop:tokens:{user_id}",
            json.dumps(save_data),
            ex=ttl
        )
        
        return {
            "success": True,
            "message": "TikTok Shop conectado com sucesso!",
            "seller_name": token_data.get("seller_name"),
            "open_id": token_data.get("open_id"),
            "expires_in": token_data.get("access_token_expire_in", 0)
        }


@router.post("/local/refresh")
async def refresh_local_token(
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Renova token usando credenciais salvas do usuário.
    """
    redis = await get_redis()
    token_data_raw = await redis.get(f"tiktok_shop:tokens:{current_user['id']}")
    
    if not token_data_raw:
        raise HTTPException(
            status_code=401,
            detail="TikTok Shop não conectado"
        )
    
    token_data = json.loads(token_data_raw)
    
    # Precisamos do app_secret para refresh, que não está salvo por segurança
    # O usuário precisa fornecer novamente
    raise HTTPException(
        status_code=400,
        detail="Para renovar o token, reconecte usando /token com suas credenciais"
    )

