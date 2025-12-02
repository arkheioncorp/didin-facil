"""
TikTok Shop API Routes
======================
Endpoints para integração com TikTok Shop.

Usa o serviço TikTokShopService para todas as operações.
"""

import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from api.database.connection import get_db
from api.middleware.auth import get_current_user
from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException, Query,
                     Request)
from integrations.tiktok_shop_service import (ProductStatus, ShopInfo,
                                              TikTokShopCredentials,
                                              TikTokShopError,
                                              TikTokShopProduct,
                                              TikTokShopService,
                                              TikTokShopToken,
                                              create_tiktok_shop_service)
from pydantic import BaseModel, Field
from shared.config import settings
from shared.redis import get_redis
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(tags=["TikTok Shop V2"])


# ==================== SCHEMAS ====================

class CredentialsInput(BaseModel):
    """Input para configurar credenciais do usuário."""
    app_key: str = Field(..., min_length=5, description="App Key do TikTok Shop")
    app_secret: str = Field(..., min_length=10, description="App Secret")
    service_id: Optional[str] = Field(None, description="Service ID (opcional)")


class AuthCallbackInput(BaseModel):
    """Input do callback OAuth."""
    code: str = Field(..., description="Authorization code")
    state: str = Field(..., description="State para validação")


class ConnectionStatus(BaseModel):
    """Status da conexão com TikTok Shop."""
    connected: bool
    seller_name: Optional[str] = None
    seller_region: Optional[str] = None
    shops: List[dict] = []
    token_expires_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    product_count: int = 0


class ProductListResponse(BaseModel):
    """Resposta da listagem de produtos."""
    products: List[dict]
    total: int
    next_page_token: Optional[str] = None


class SyncResult(BaseModel):
    """Resultado da sincronização."""
    success: bool
    products_synced: int
    errors: List[str] = []
    duration_seconds: float


# ==================== HELPERS ====================

def get_redis_key(user_id: str, suffix: str) -> str:
    """Gera chave Redis para dados do usuário."""
    return f"tiktok_shop:{user_id}:{suffix}"


async def get_user_credentials(user_id: str, redis) -> Optional[TikTokShopCredentials]:
    """Recupera credenciais do usuário do Redis."""
    key = get_redis_key(user_id, "credentials")
    data = await redis.get(key)
    
    if not data:
        return None
    
    creds = json.loads(data)
    return TikTokShopCredentials(**creds)


async def save_user_credentials(user_id: str, credentials: CredentialsInput, redis):
    """Salva credenciais do usuário no Redis."""
    key = get_redis_key(user_id, "credentials")
    data = {
        "app_key": credentials.app_key,
        "app_secret": credentials.app_secret,
        "service_id": credentials.service_id
    }
    await redis.set(key, json.dumps(data))


async def get_user_token(user_id: str, redis) -> Optional[TikTokShopToken]:
    """Recupera token do usuário do Redis."""
    key = get_redis_key(user_id, "token")
    data = await redis.get(key)
    
    if not data:
        return None
    
    token_data = json.loads(data)
    return TikTokShopToken(
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        access_token_expires_at=datetime.fromisoformat(token_data["access_token_expires_at"]),
        refresh_token_expires_at=datetime.fromisoformat(token_data["refresh_token_expires_at"]),
        open_id=token_data.get("open_id", ""),
        seller_name=token_data.get("seller_name", ""),
        seller_base_region=token_data.get("seller_base_region", ""),
        user_type=token_data.get("user_type", 0)
    )


async def save_user_token(user_id: str, token: TikTokShopToken, redis):
    """Salva token do usuário no Redis."""
    key = get_redis_key(user_id, "token")
    data = {
        "access_token": token.access_token,
        "refresh_token": token.refresh_token,
        "access_token_expires_at": token.access_token_expires_at.isoformat(),
        "refresh_token_expires_at": token.refresh_token_expires_at.isoformat(),
        "open_id": token.open_id,
        "seller_name": token.seller_name,
        "seller_base_region": token.seller_base_region,
        "user_type": token.user_type
    }
    # Expira junto com refresh_token
    ttl = int((token.refresh_token_expires_at - datetime.utcnow()).total_seconds())
    await redis.set(key, json.dumps(data), ex=max(ttl, 3600))


async def get_service_for_user(user_id: str, redis) -> TikTokShopService:
    """Cria serviço TikTok Shop para o usuário."""
    credentials = await get_user_credentials(user_id, redis)
    
    if not credentials:
        raise HTTPException(
            status_code=400,
            detail="TikTok Shop não configurado. Configure suas credenciais primeiro."
        )
    
    return TikTokShopService(credentials)


async def ensure_valid_token(user_id: str, redis) -> TikTokShopToken:
    """Garante que o token do usuário é válido, renovando se necessário."""
    token = await get_user_token(user_id, redis)
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Não conectado ao TikTok Shop. Faça a autorização primeiro."
        )
    
    # Verifica se precisa renovar (5 minutos antes de expirar)
    if token.access_token_expires_at < datetime.utcnow() + timedelta(minutes=5):
        credentials = await get_user_credentials(user_id, redis)
        if not credentials:
            raise HTTPException(status_code=400, detail="Credenciais não encontradas")
        
        service = TikTokShopService(credentials)
        try:
            token = await service.refresh_token(token.refresh_token)
            await save_user_token(user_id, token, redis)
            logger.info(f"Token renovado para usuário {user_id}")
        except TikTokShopError as e:
            logger.error(f"Erro ao renovar token: {e}")
            raise HTTPException(
                status_code=401,
                detail="Sessão expirada. Reconecte ao TikTok Shop."
            )
        finally:
            await service.close()
    
    return token


# ==================== ENDPOINTS: CONFIGURAÇÃO ====================

@router.post("/credentials", summary="Configurar credenciais")
async def set_credentials(
    credentials: CredentialsInput,
    current_user: dict = Depends(get_current_user),
    redis=Depends(get_redis)
):
    """
    Salva as credenciais do TikTok Shop do usuário.
    
    O usuário deve obter app_key e app_secret no TikTok Shop Partner Center.
    """
    user_id = str(current_user["id"])
    
    await save_user_credentials(user_id, credentials, redis)
    
    logger.info(f"Credenciais TikTok Shop salvas para usuário {user_id}")
    
    return {
        "success": True,
        "message": "Credenciais salvas com sucesso"
    }


@router.get("/credentials/status", summary="Verificar credenciais")
async def check_credentials(
    current_user: dict = Depends(get_current_user),
    redis=Depends(get_redis)
):
    """Verifica se o usuário tem credenciais configuradas."""
    user_id = str(current_user["id"])
    credentials = await get_user_credentials(user_id, redis)
    
    return {
        "configured": credentials is not None,
        "app_key": credentials.app_key[:8] + "..." if credentials else None
    }


@router.delete("/credentials", summary="Remover credenciais")
async def delete_credentials(
    current_user: dict = Depends(get_current_user),
    redis=Depends(get_redis)
):
    """Remove credenciais e desconecta do TikTok Shop."""
    user_id = str(current_user["id"])
    
    await redis.delete(get_redis_key(user_id, "credentials"))
    await redis.delete(get_redis_key(user_id, "token"))
    await redis.delete(get_redis_key(user_id, "shops"))
    
    return {"success": True, "message": "Credenciais removidas"}


# ==================== ENDPOINTS: OAUTH ====================

@router.get("/auth/url", summary="Obter URL de autorização")
async def get_auth_url(
    current_user: dict = Depends(get_current_user),
    redis=Depends(get_redis)
):
    """
    Gera URL para autorização OAuth no TikTok Shop.
    
    O usuário deve ser redirecionado para esta URL para autorizar o app.
    """
    user_id = str(current_user["id"])
    
    credentials = await get_user_credentials(user_id, redis)
    if not credentials:
        raise HTTPException(
            status_code=400,
            detail="Configure suas credenciais primeiro"
        )
    
    # Gera state único para CSRF protection
    state = f"{user_id}:{secrets.token_urlsafe(16)}"
    await redis.set(f"tiktok_shop_state:{state}", user_id, ex=600)  # 10 min
    
    service = TikTokShopService(credentials)
    auth_url = service.get_auth_url(state=state)
    await service.close()
    
    return {
        "auth_url": auth_url,
        "state": state,
        "expires_in": 600
    }


class TokenExchangeInput(BaseModel):
    """Input para troca manual de código por token."""
    app_key: str = Field(..., description="App Key")
    app_secret: str = Field(..., description="App Secret")
    code: str = Field(..., description="Authorization code")


@router.post("/auth/token", summary="Trocar código por token")
async def exchange_token(
    data: TokenExchangeInput,
    current_user: dict = Depends(get_current_user),
    redis=Depends(get_redis)
):
    """
    Troca código de autorização por token (fluxo manual).
    
    Use este endpoint quando o callback OAuth é feito em uma URL externa
    (como Postman) e você precisa colar o código manualmente.
    """
    user_id = str(current_user["id"])
    
    # Cria credenciais temporárias
    credentials = TikTokShopCredentials(
        app_key=data.app_key,
        app_secret=data.app_secret
    )
    
    # Salva credenciais para uso futuro
    await save_user_credentials(
        user_id,
        CredentialsInput(app_key=data.app_key, app_secret=data.app_secret),
        redis
    )
    
    service = TikTokShopService(credentials)
    try:
        token = await service.exchange_code(data.code)
        await save_user_token(user_id, token, redis)
        
        # Busca lojas do seller
        try:
            shops = await service.get_active_shops(token.access_token)
            await redis.set(
                get_redis_key(user_id, "shops"),
                json.dumps([s.dict() for s in shops]),
                ex=86400  # 24h
            )
        except Exception as e:
            logger.warning(f"Erro ao buscar lojas: {e}")
            shops = []
        
        logger.info(f"TikTok Shop conectado via token manual: {token.seller_name}")
        
        return {
            "success": True,
            "message": "TikTok Shop conectado com sucesso!",
            "seller_name": token.seller_name,
            "seller_region": token.seller_base_region,
            "shops": [s.dict() for s in shops] if shops else []
        }
    except TikTokShopError as e:
        logger.error(f"Erro ao trocar código: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
    finally:
        await service.close()


@router.post("/auth/callback", summary="Callback OAuth")
async def oauth_callback(
    callback: AuthCallbackInput,
    current_user: dict = Depends(get_current_user),
    redis=Depends(get_redis)
):
    """
    Processa callback OAuth do TikTok Shop.
    
    Recebe o authorization code e troca por access token.
    """
    user_id = str(current_user["id"])
    
    # Valida state
    stored_user = await redis.get(f"tiktok_shop_state:{callback.state}")
    if not stored_user or stored_user != user_id:
        raise HTTPException(status_code=400, detail="State inválido ou expirado")
    
    await redis.delete(f"tiktok_shop_state:{callback.state}")
    
    # Troca code por token
    service = await get_service_for_user(user_id, redis)
    try:
        token = await service.exchange_code(callback.code)
        await save_user_token(user_id, token, redis)
        
        # Busca lojas do seller
        shops = await service.get_active_shops(token.access_token)
        await redis.set(
            get_redis_key(user_id, "shops"),
            json.dumps([s.dict() for s in shops]),
            ex=86400  # 24h
        )
        
        logger.info(f"TikTok Shop conectado: {token.seller_name} ({token.seller_base_region})")
        
        return {
            "success": True,
            "seller_name": token.seller_name,
            "seller_region": token.seller_base_region,
            "shops": [s.dict() for s in shops]
        }
    except TikTokShopError as e:
        logger.error(f"Erro OAuth: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await service.close()


@router.get("/status", summary="Status da conexão")
async def get_connection_status(
    current_user: dict = Depends(get_current_user),
    redis=Depends(get_redis)
) -> ConnectionStatus:
    """Retorna status da conexão com TikTok Shop."""
    user_id = str(current_user["id"])
    
    credentials = await get_user_credentials(user_id, redis)
    if not credentials:
        return ConnectionStatus(connected=False)
    
    token = await get_user_token(user_id, redis)
    if not token:
        return ConnectionStatus(connected=False)
    
    # Busca shops do cache
    shops_data = await redis.get(get_redis_key(user_id, "shops"))
    shops = json.loads(shops_data) if shops_data else []
    
    # Conta produtos sincronizados
    product_count = await redis.get(get_redis_key(user_id, "product_count"))
    
    # Último sync
    last_sync = await redis.get(get_redis_key(user_id, "last_sync"))
    
    return ConnectionStatus(
        connected=True,
        seller_name=token.seller_name,
        seller_region=token.seller_base_region,
        shops=shops,
        token_expires_at=token.access_token_expires_at,
        last_sync=datetime.fromisoformat(last_sync) if last_sync else None,
        product_count=int(product_count) if product_count else 0
    )


@router.post("/disconnect", summary="Desconectar")
async def disconnect(
    current_user: dict = Depends(get_current_user),
    redis=Depends(get_redis)
):
    """Desconecta do TikTok Shop (mantém credenciais)."""
    user_id = str(current_user["id"])
    
    await redis.delete(get_redis_key(user_id, "token"))
    await redis.delete(get_redis_key(user_id, "shops"))
    
    return {"success": True, "message": "Desconectado do TikTok Shop"}


# ==================== ENDPOINTS: PRODUTOS ====================

@router.get("/products", summary="Listar produtos")
async def list_products(
    page_size: int = Query(default=20, ge=1, le=100),
    page_token: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    shop_id: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
    redis=Depends(get_redis)
) -> ProductListResponse:
    """
    Lista produtos da loja TikTok Shop.
    
    - **page_size**: Número de produtos por página (1-100)
    - **page_token**: Token para próxima página
    - **status**: Filtrar por status (ACTIVATE, DRAFT, etc.)
    - **shop_id**: ID da loja (se multi-loja)
    """
    user_id = str(current_user["id"])
    
    token = await ensure_valid_token(user_id, redis)
    service = await get_service_for_user(user_id, redis)
    
    try:
        # Busca shop_cipher se necessário
        shop_cipher = None
        if shop_id:
            shops_data = await redis.get(get_redis_key(user_id, "shops"))
            if shops_data:
                shops = json.loads(shops_data)
                for shop in shops:
                    if shop["shop_id"] == shop_id:
                        shop_cipher = shop.get("shop_cipher")
                        break
        
        product_status = ProductStatus(status) if status else None
        
        products, next_token = await service.search_products(
            access_token=token.access_token,
            shop_cipher=shop_cipher,
            page_size=page_size,
            page_token=page_token,
            status=product_status
        )
        
        return ProductListResponse(
            products=[p.dict() for p in products],
            total=len(products),
            next_page_token=next_token
        )
    except TikTokShopError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await service.close()


@router.post("/products/sync", summary="Sincronizar produtos")
async def sync_products(
    background_tasks: BackgroundTasks,
    shop_id: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
    redis=Depends(get_redis)
):
    """
    Inicia sincronização de produtos do TikTok Shop para o banco local.
    
    A sincronização roda em background.
    """
    user_id = str(current_user["id"])
    
    # Verifica se já tem sync em andamento
    sync_key = get_redis_key(user_id, "sync_running")
    if await redis.get(sync_key):
        return {
            "success": False,
            "message": "Sincronização já em andamento"
        }
    
    # Marca sync como em andamento
    await redis.set(sync_key, "1", ex=300)  # 5 min timeout
    
    # Adiciona task em background
    background_tasks.add_task(
        run_product_sync,
        user_id=user_id,
        shop_id=shop_id,
        redis=redis
    )
    
    return {
        "success": True,
        "message": "Sincronização iniciada em background"
    }


@router.get("/products/sync/status", summary="Status da sincronização")
async def get_sync_status(
    current_user: dict = Depends(get_current_user),
    redis=Depends(get_redis)
):
    """Retorna status da última sincronização."""
    user_id = str(current_user["id"])
    
    running = await redis.get(get_redis_key(user_id, "sync_running"))
    last_result = await redis.get(get_redis_key(user_id, "sync_result"))
    
    return {
        "running": running is not None,
        "last_result": json.loads(last_result) if last_result else None
    }


# ==================== BACKGROUND TASKS ====================

async def run_product_sync(user_id: str, shop_id: Optional[str], redis):
    """
    Executa sincronização de produtos em background.
    """
    import time

    from api.services.database import async_session_maker
    from modules.products.models import Product
    
    start_time = time.time()
    errors = []
    synced_count = 0
    
    try:
        credentials = await get_user_credentials(user_id, redis)
        token = await get_user_token(user_id, redis)
        
        if not credentials or not token:
            errors.append("Credenciais ou token não encontrados")
            return
        
        service = TikTokShopService(credentials)
        
        # Busca shop_cipher
        shop_cipher = None
        if shop_id:
            shops_data = await redis.get(get_redis_key(user_id, "shops"))
            if shops_data:
                shops = json.loads(shops_data)
                for shop in shops:
                    if shop["shop_id"] == shop_id:
                        shop_cipher = shop.get("shop_cipher")
                        break
        
        # Busca todos os produtos ativos
        products = await service.get_all_products(
            access_token=token.access_token,
            shop_cipher=shop_cipher,
            status=ProductStatus.ACTIVATE,
            max_products=1000
        )
        
        logger.info(f"Encontrados {len(products)} produtos para sincronizar")
        
        # Salva no banco
        async with async_session_maker() as session:
            for tts_product in products:
                try:
                    # Pega primeiro SKU para preço
                    price = 0.0
                    if tts_product.skus:
                        sku = tts_product.skus[0]
                        price = float(sku.price.sale_price)
                    
                    # Cria/atualiza produto
                    product = Product(
                        external_id=tts_product.id,
                        source="tiktok_shop",
                        title=tts_product.title,
                        price=price,
                        currency="BRL",
                        user_id=user_id,
                        metadata={
                            "tiktok_shop": {
                                "status": tts_product.status.value,
                                "sales_regions": tts_product.sales_regions,
                                "skus": [s.dict() for s in tts_product.skus],
                                "quality_tier": tts_product.listing_quality_tier
                            }
                        }
                    )
                    
                    # Upsert
                    await session.merge(product)
                    synced_count += 1
                    
                except Exception as e:
                    errors.append(f"Erro produto {tts_product.id}: {str(e)}")
            
            await session.commit()
        
        await service.close()
        
    except Exception as e:
        logger.error(f"Erro na sincronização: {e}")
        errors.append(str(e))
    
    finally:
        duration = time.time() - start_time
        
        result = {
            "success": len(errors) == 0,
            "products_synced": synced_count,
            "errors": errors[:10],  # Limita erros
            "duration_seconds": round(duration, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Salva resultado
        await redis.set(
            get_redis_key(user_id, "sync_result"),
            json.dumps(result),
            ex=86400
        )
        await redis.set(
            get_redis_key(user_id, "last_sync"),
            datetime.utcnow().isoformat(),
            ex=86400 * 7
        )
        await redis.set(
            get_redis_key(user_id, "product_count"),
            str(synced_count),
            ex=86400 * 7
        )
        await redis.delete(get_redis_key(user_id, "sync_running"))
        
        logger.info(f"Sync completa: {synced_count} produtos em {duration:.1f}s")


# ==================== ENDPOINTS: LOJAS ====================

@router.get("/shops", summary="Listar lojas")
async def list_shops(
    current_user: dict = Depends(get_current_user),
    redis=Depends(get_redis)
):
    """Lista lojas ativas do seller."""
    user_id = str(current_user["id"])
    
    token = await ensure_valid_token(user_id, redis)
    service = await get_service_for_user(user_id, redis)
    
    try:
        shops = await service.get_active_shops(token.access_token)
        
        # Atualiza cache
        await redis.set(
            get_redis_key(user_id, "shops"),
            json.dumps([s.dict() for s in shops]),
            ex=86400
        )
        
        return {"shops": [s.dict() for s in shops]}
    except TikTokShopError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await service.close()
