"""
TikTok Routes
Upload de vídeos para TikTok via Selenium + API Scraping
"""

from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form, Query, BackgroundTasks
)
from pydantic import BaseModel, Field
from typing import Optional, List
import shutil
import os
from datetime import datetime

from api.middleware.auth import get_current_user
from vendor.tiktok.client import (
    TikTokClient, TikTokConfig, VideoConfig, Privacy
)
from shared.config import settings
from integrations.tiktok_hub import get_tiktok_hub
from api.services.tiktok_session import TikTokSessionStatus
from api.services.cache import CacheService
from scraper.tiktok.api_scraper import TikTokAPIScraper
from scraper.cache import ProductCacheManager

router = APIRouter()
hub = get_tiktok_hub()
session_manager = hub.session_manager


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


# ============================================================================
# TikTok API Scraper Endpoints
# ============================================================================


class TikTokSearchRequest(BaseModel):
    """Request model for TikTok product search."""
    query: str = Field(..., min_length=2, max_length=200)
    max_results: int = Field(default=20, ge=1, le=100)


class TikTokProductResponse(BaseModel):
    """TikTok product from API scraper."""
    id: str = Field(alias="tiktok_id")
    title: str
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount: Optional[str] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    shop_name: Optional[str] = Field(default=None, alias="seller_name")
    sales_count: Optional[int] = Field(default=None, alias="sold_count")
    rating: Optional[float] = None
    source: str = "tiktok_api"
    
    model_config = {"populate_by_name": True}


class TikTokSearchResponse(BaseModel):
    """Response for TikTok product search."""
    products: List[TikTokProductResponse]
    total: int
    cached: bool = False
    cache_ttl: Optional[int] = None
    scraper_type: str = "api"


class TikTokHealthResponse(BaseModel):
    """TikTok API Scraper health status."""
    status: str
    api_accessible: bool
    cookies_valid: bool
    cookie_expires: Optional[str] = None
    endpoints_tested: List[str] = []
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""
    total_keys: int
    hits: int
    misses: int
    hit_rate: float
    trending_cached: bool
    search_queries_cached: int
    memory_used_mb: Optional[float] = None


@router.get(
    "/api/health",
    response_model=TikTokHealthResponse,
    summary="TikTok API Scraper Health Check",
    description="""
    Verifica a saúde do scraper de API TikTok.
    
    Testa:
    - Conectividade com API TikTok
    - Validade dos cookies de autenticação
    - Tempo de resposta
    
    Returns:
        TikTokHealthResponse com status detalhado
    """
)
async def tiktok_api_health(
    current_user=Depends(get_current_user)
):
    """Check TikTok API scraper health status."""
    import time
    
    start_time = time.time()
    
    try:
        scraper = TikTokAPIScraper()
        health = await scraper.health_check()
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return TikTokHealthResponse(
            status="healthy" if health["healthy"] else "degraded",
            api_accessible=health["api_accessible"],
            cookies_valid=health["cookies_valid"],
            cookie_expires=health.get("expires"),
            endpoints_tested=health.get("endpoints_tested", []),
            response_time_ms=round(elapsed_ms, 2)
        )
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return TikTokHealthResponse(
            status="error",
            api_accessible=False,
            cookies_valid=False,
            response_time_ms=round(elapsed_ms, 2),
            error=str(e)
        )


@router.get(
    "/api/search",
    response_model=TikTokSearchResponse,
    summary="Search TikTok Products via API",
    description="""
    Busca produtos no TikTok Shop usando API direta (sem browser).
    
    - Bypass de CAPTCHA via cookies autenticados
    - Cache de resultados por 30 minutos
    - Fallback para browser se API falhar
    
    Args:
        q: Query de busca (mínimo 2 caracteres)
        max_results: Máximo de resultados (1-100, default 20)
    
    Returns:
        Lista de produtos com preços, vendas e URLs
    """
)
async def search_tiktok_products(
    q: str = Query(..., min_length=2, max_length=200),
    max_results: int = Query(default=20, ge=1, le=100),
    use_cache: bool = Query(default=True),
    current_user=Depends(get_current_user)
):
    """Search TikTok products using API scraper."""
    cache_manager = ProductCacheManager()
    
    # Check cache first
    if use_cache:
        cached = await cache_manager.get_search_results(q)
        if cached:
            return TikTokSearchResponse(
                products=[
                    TikTokProductResponse(**p) for p in cached[:max_results]
                ],
                total=len(cached),
                cached=True,
                cache_ttl=await cache_manager.get_ttl(f"search:{q}"),
                scraper_type="api"
            )
    
    # Fetch from API
    try:
        scraper = TikTokAPIScraper()
        products = await scraper.search_products(q, limit=max_results)
        
        # Cache results
        if products:
            await cache_manager.cache_search_results(q, products)
        
        return TikTokSearchResponse(
            products=[TikTokProductResponse(**p) for p in products],
            total=len(products),
            cached=False,
            scraper_type="api"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar produtos: {str(e)}"
        )


@router.get(
    "/api/trending",
    response_model=TikTokSearchResponse,
    summary="Get Trending TikTok Products",
    description="""
    Retorna produtos em alta no TikTok Shop.
    
    - Atualizado automaticamente a cada 30 minutos
    - Baseado em vendas recentes e engajamento
    - Cache agressivo para performance
    
    Args:
        category: Filtrar por categoria (opcional)
        max_results: Máximo de resultados (1-50, default 20)
    
    Returns:
        Lista de produtos trending
    """
)
async def get_trending_tiktok_products(
    category: Optional[str] = Query(None),
    max_results: int = Query(default=20, ge=1, le=50),
    use_cache: bool = Query(default=True),
    current_user=Depends(get_current_user)
):
    """Get trending TikTok products."""
    cache_manager = ProductCacheManager()
    
    # Check cache
    if use_cache:
        cached = await cache_manager.get_trending(category)
        if cached:
            return TikTokSearchResponse(
                products=[
                    TikTokProductResponse(**p) for p in cached[:max_results]
                ],
                total=len(cached),
                cached=True,
                cache_ttl=await cache_manager.get_ttl("trending"),
                scraper_type="api"
            )
    
    # Fetch from API
    try:
        scraper = TikTokAPIScraper()
        products = await scraper.get_trending_products(
            max_results=max_results,
            category=category
        )
        
        # Cache trending results (longer TTL)
        if products:
            await cache_manager.cache_trending(products, category)
        
        return TikTokSearchResponse(
            products=[TikTokProductResponse(**p) for p in products],
            total=len(products),
            cached=False,
            scraper_type="api"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar trending: {str(e)}"
        )


@router.get(
    "/api/cache/stats",
    response_model=CacheStatsResponse,
    summary="Get Cache Statistics",
    description="""
    Retorna estatísticas do cache de produtos TikTok.
    
    Inclui:
    - Taxa de acerto (hit rate)
    - Número de queries cacheadas
    - Uso de memória
    """
)
async def get_cache_stats(
    current_user=Depends(get_current_user)
):
    """Get TikTok product cache statistics."""
    try:
        cache_manager = ProductCacheManager()
        stats = await cache_manager.get_stats()
        
        return CacheStatsResponse(
            total_keys=stats.get("total_keys", 0),
            hits=stats.get("hits", 0),
            misses=stats.get("misses", 0),
            hit_rate=stats.get("hit_rate", 0.0),
            trending_cached=stats.get("trending_cached", False),
            search_queries_cached=stats.get("search_queries_cached", 0),
            memory_used_mb=stats.get("memory_used_mb")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter estatísticas: {str(e)}"
        )


@router.post(
    "/api/cache/clear",
    summary="Clear Product Cache",
    description="""
    Limpa o cache de produtos TikTok.
    
    Opções:
    - pattern: Padrão de chaves a limpar (ex: "search:*", "trending:*")
    - all: Limpa todo o cache de produtos
    
    Apenas usuários Pro/Enterprise podem limpar cache.
    """
)
async def clear_cache(
    pattern: Optional[str] = Query(None),
    all_cache: bool = Query(default=False, alias="all"),
    current_user=Depends(get_current_user)
):
    """Clear TikTok product cache."""
    # Verify premium user
    if current_user.get("plan") not in ["pro", "enterprise"]:
        raise HTTPException(
            status_code=403,
            detail="Limpeza de cache disponível apenas para Pro/Enterprise"
        )
    
    try:
        cache_manager = ProductCacheManager()
        
        if all_cache:
            deleted = await cache_manager.clear_all()
            return {
                "status": "success",
                "message": f"Cache limpo: {deleted} chaves removidas"
            }
        elif pattern:
            deleted = await cache_manager.clear_pattern(pattern)
            return {
                "status": "success",
                "message": f"Padrão '{pattern}': {deleted} chaves removidas"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Especifique 'pattern' ou 'all=true'"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao limpar cache: {str(e)}"
        )


@router.post(
    "/api/refresh",
    summary="Force Product Data Refresh",
    description="""
    Força atualização dos dados de produtos do TikTok.
    
    - Invalida cache existente
    - Busca dados frescos da API
    - Atualiza trending e categorias
    
    Apenas usuários Pro/Enterprise. Rate limited: 5/hora.
    """
)
async def refresh_products(
    background_tasks: BackgroundTasks,
    category: Optional[str] = Query(None),
    current_user=Depends(get_current_user)
):
    """Force refresh of TikTok product data."""
    # Verify premium user
    if current_user.get("plan") not in ["pro", "enterprise"]:
        raise HTTPException(
            status_code=403,
            detail="Refresh disponível apenas para Pro/Enterprise"
        )
    
    # Rate limit check
    cache = CacheService()
    rate_key = f"refresh_rate:{current_user.get('id')}"
    
    count = await cache.get(rate_key)
    if count and int(count) >= 5:
        raise HTTPException(
            status_code=429,
            detail="Rate limit: máximo 5 refreshes por hora"
        )
    
    # Increment rate counter
    await cache.incr(rate_key)
    
    # Queue background refresh
    async def do_refresh():
        try:
            cache_manager = ProductCacheManager()
            scraper = TikTokAPIScraper()
            
            # Clear relevant cache
            if category:
                await cache_manager.clear_pattern(f"*:{category}:*")
            else:
                await cache_manager.clear_pattern("trending:*")
            
            # Fetch fresh data
            products = await scraper.get_trending_products(
                max_results=50,
                category=category
            )
            
            # Cache new data
            if products:
                await cache_manager.cache_trending(products, category)
                
        except Exception:
            pass  # Log error in production
    
    background_tasks.add_task(do_refresh)
    
    return {
        "status": "queued",
        "message": "Refresh agendado em background",
        "category": category or "all"
    }
