"""
API Endpoints para busca unificada de marketplaces.

Permite buscar produtos em múltiplos e-commerces e comparar preços.
"""

from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from integrations.marketplaces import (
        MarketplaceManager,
        MarketplaceType,
        Product,
        SearchResult,
        get_marketplace_manager,
    )
except ImportError:
    # Fallback for missing module - define stubs
    MarketplaceManager = None
    MarketplaceType = None
    Product = None
    SearchResult = None
    get_marketplace_manager = None

router = APIRouter(prefix="/marketplaces", tags=["Marketplaces"])


# === Schemas ===

class ProductResponse(BaseModel):
    """Produto retornado pela API."""
    id: str
    marketplace: str
    title: str
    price: float
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    currency: str = "BRL"
    url: str
    thumbnail: Optional[str] = None
    free_shipping: bool = False
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    seller_name: Optional[str] = None
    is_official_store: bool = False
    
    @classmethod
    def from_product(cls, product: Product) -> "ProductResponse":
        return cls(
            id=product.id,
            marketplace=product.marketplace.value,
            title=product.title,
            price=float(product.price),
            original_price=float(product.original_price) if product.original_price else None,
            discount_percentage=product.discount_percentage,
            currency=product.currency,
            url=str(product.external_url),
            thumbnail=str(product.thumbnail) if product.thumbnail else None,
            free_shipping=product.free_shipping,
            rating=product.rating,
            reviews_count=product.reviews_count,
            seller_name=product.seller_name,
            is_official_store=product.is_official_store,
        )


class SearchResponse(BaseModel):
    """Resposta de busca."""
    query: str
    marketplace: str
    total_results: int
    page: int
    per_page: int
    products: list[ProductResponse]
    search_time_ms: float


class ComparisonResponse(BaseModel):
    """Resposta de comparação entre marketplaces."""
    query: str
    total_products: int
    search_time_ms: float
    best_price: Optional[ProductResponse] = None
    best_rating: Optional[ProductResponse] = None
    best_value: Optional[ProductResponse] = None
    by_marketplace: dict[str, list[ProductResponse]]
    errors: dict[str, str]


class MarketplaceInfo(BaseModel):
    """Informação de um marketplace."""
    id: str
    name: str
    country: str
    requires_auth: bool
    available: bool


# === Dependency ===

async def get_manager() -> MarketplaceManager:
    """Dependency para obter o manager."""
    return get_marketplace_manager()


# === Endpoints ===

@router.get("/", response_model=list[MarketplaceInfo])
async def list_marketplaces(
    manager: MarketplaceManager = Depends(get_manager)
):
    """
    Lista todos os marketplaces suportados.
    
    Retorna informações sobre cada marketplace, incluindo
    se está disponível e se requer autenticação.
    """
    marketplaces = [
        MarketplaceInfo(
            id=MarketplaceType.MERCADO_LIVRE.value,
            name="Mercado Livre",
            country="BR",
            requires_auth=False,
            available=True,
        ),
        MarketplaceInfo(
            id=MarketplaceType.AMAZON.value,
            name="Amazon",
            country="BR",
            requires_auth=True,
            available=MarketplaceType.AMAZON in manager.clients,
        ),
        MarketplaceInfo(
            id=MarketplaceType.SHOPEE.value,
            name="Shopee",
            country="BR",
            requires_auth=False,
            available=True,
        ),
        MarketplaceInfo(
            id=MarketplaceType.ALIEXPRESS.value,
            name="AliExpress",
            country="CN",
            requires_auth=False,
            available=False,  # Usa scraper, não API
        ),
        MarketplaceInfo(
            id=MarketplaceType.TIKTOK_SHOP.value,
            name="TikTok Shop",
            country="BR",
            requires_auth=False,
            available=False,  # Usa scraper
        ),
    ]
    
    return marketplaces


@router.get("/search", response_model=SearchResponse)
async def search_marketplace(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    marketplace: str = Query("mercado_livre", description="ID do marketplace"),
    page: int = Query(1, ge=1, description="Página"),
    per_page: int = Query(20, ge=1, le=50, description="Itens por página"),
    price_min: Optional[float] = Query(None, ge=0, description="Preço mínimo"),
    price_max: Optional[float] = Query(None, ge=0, description="Preço máximo"),
    sort: str = Query("relevance", description="Ordenação"),
    manager: MarketplaceManager = Depends(get_manager),
):
    """
    Busca produtos em um marketplace específico.
    
    Parâmetros:
    - **q**: Termo de busca (obrigatório)
    - **marketplace**: ID do marketplace (mercado_livre, amazon, shopee)
    - **page**: Número da página
    - **per_page**: Itens por página (máximo 50)
    - **price_min/price_max**: Filtro de preço
    - **sort**: relevance, price_asc, price_desc
    """
    # Validar marketplace
    try:
        mp_type = MarketplaceType(marketplace)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Marketplace inválido: {marketplace}"
        )
    
    # Verificar disponibilidade
    if mp_type not in manager.available_marketplaces:
        raise HTTPException(
            status_code=400,
            detail=f"Marketplace {marketplace} não disponível ou não configurado"
        )
    
    # Executar busca
    try:
        result = await manager.search(
            mp_type,
            q,
            page=page,
            per_page=per_page,
            price_min=price_min,
            price_max=price_max,
            sort=sort,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na busca: {str(e)}"
        )
    
    return SearchResponse(
        query=result.query,
        marketplace=result.marketplace.value,
        total_results=result.total_results,
        page=result.page,
        per_page=result.per_page,
        products=[ProductResponse.from_product(p) for p in result.products],
        search_time_ms=result.search_time_ms or 0,
    )


@router.get("/compare", response_model=ComparisonResponse)
async def compare_marketplaces(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    marketplaces: Optional[str] = Query(
        None, 
        description="IDs separados por vírgula (ex: mercado_livre,shopee)"
    ),
    per_page: int = Query(10, ge=1, le=30, description="Itens por marketplace"),
    manager: MarketplaceManager = Depends(get_manager),
):
    """
    Busca e compara produtos em múltiplos marketplaces.
    
    Retorna o melhor preço, melhor avaliação e melhor custo-benefício.
    
    Parâmetros:
    - **q**: Termo de busca (obrigatório)
    - **marketplaces**: Lista de marketplaces (opcional, todos se omitido)
    - **per_page**: Itens por marketplace
    """
    # Parse marketplaces
    mp_list = None
    if marketplaces:
        try:
            mp_list = [MarketplaceType(m.strip()) for m in marketplaces.split(",")]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Marketplace inválido: {e}")
    
    # Executar comparação
    try:
        result = await manager.search_all(q, marketplaces=mp_list, per_page=per_page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na comparação: {str(e)}")
    
    return ComparisonResponse(
        query=result.query,
        total_products=result.total_products,
        search_time_ms=result.search_time_ms,
        best_price=ProductResponse.from_product(result.best_price) if result.best_price else None,
        best_rating=ProductResponse.from_product(result.best_rating) if result.best_rating else None,
        best_value=ProductResponse.from_product(result.best_value) if result.best_value else None,
        by_marketplace={
            mp: [ProductResponse.from_product(p) for p in products]
            for mp, products in result.by_marketplace.items()
        },
        errors=result.errors,
    )


@router.get("/best-deal")
async def find_best_deal(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    min_rating: float = Query(4.0, ge=0, le=5, description="Rating mínimo"),
    max_price: Optional[float] = Query(None, ge=0, description="Preço máximo"),
    manager: MarketplaceManager = Depends(get_manager),
):
    """
    Encontra a melhor oferta considerando preço, rating e frete.
    
    Algoritmo considera:
    - Rating do produto
    - Desconto aplicado
    - Preço final
    - Frete grátis
    
    Parâmetros:
    - **q**: Termo de busca específico
    - **min_rating**: Rating mínimo aceitável (padrão: 4.0)
    - **max_price**: Preço máximo (opcional)
    """
    try:
        product = await manager.find_best_deal(
            q,
            min_rating=min_rating,
            max_price=max_price,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
    
    if not product:
        return {
            "found": False,
            "message": "Nenhum produto encontrado com os critérios especificados",
            "query": q,
            "criteria": {
                "min_rating": min_rating,
                "max_price": max_price,
            }
        }
    
    return {
        "found": True,
        "product": ProductResponse.from_product(product),
    }


@router.get("/{marketplace}/product/{product_id}")
async def get_product_details(
    marketplace: str,
    product_id: str,
    manager: MarketplaceManager = Depends(get_manager),
):
    """
    Obtém detalhes completos de um produto específico.
    
    Parâmetros:
    - **marketplace**: ID do marketplace
    - **product_id**: ID do produto no marketplace
    """
    try:
        mp_type = MarketplaceType(marketplace)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Marketplace inválido: {marketplace}")
    
    client = manager.get_client(mp_type)
    if not client:
        raise HTTPException(status_code=400, detail=f"Marketplace não disponível: {marketplace}")
    
    try:
        product = await client.get_product(product_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar produto: {str(e)}")
    
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    return ProductResponse.from_product(product)


@router.get("/{marketplace}/categories")
async def get_categories(
    marketplace: str,
    parent_id: Optional[str] = Query(None, description="ID da categoria pai"),
    manager: MarketplaceManager = Depends(get_manager),
):
    """
    Lista categorias de um marketplace.
    
    Parâmetros:
    - **marketplace**: ID do marketplace
    - **parent_id**: ID da categoria pai (opcional, raiz se omitido)
    """
    try:
        mp_type = MarketplaceType(marketplace)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Marketplace inválido: {marketplace}")
    
    client = manager.get_client(mp_type)
    if not client:
        raise HTTPException(status_code=400, detail=f"Marketplace não disponível: {marketplace}")
    
    try:
        categories = await client.get_categories(parent_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar categorias: {str(e)}")
    
    return {"categories": categories}
