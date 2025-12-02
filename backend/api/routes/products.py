"""
Products Routes
Product search and retrieval endpoints
"""

from datetime import datetime
from typing import List, Optional

from api.middleware.auth import get_current_user, get_current_user_optional
from api.services.cache import CacheService
from api.services.scraper import ScraperOrchestrator
from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException, Query,
                     Response)
from pydantic import BaseModel, Field

router = APIRouter()


class ProductFilters(BaseModel):
    """Product search filters"""

    query: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    min_sales: Optional[int] = Field(None, ge=0)
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    is_trending: Optional[bool] = None
    has_video: Optional[bool] = None
    sort_by: str = "sales_30d"
    sort_order: str = "desc"


class Product(BaseModel):
    """Product response model"""

    id: str
    external_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    category: Optional[str] = None
    shop_name: Optional[str] = None
    shop_url: Optional[str] = None
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[List[str]] = []
    sales_count: int = 0
    review_count: int = 0
    rating: Optional[float] = None
    trending_score: Optional[float] = None
    source: Optional[str] = "tiktok_shop"
    status: Optional[str] = "active"
    metadata: Optional[dict] = None
    last_scraped_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductsResponse(BaseModel):
    """Paginated products response"""

    products: List[Product]
    total: int
    page: int
    per_page: int
    has_more: bool
    cached: bool = False
    cache_expires_at: Optional[datetime] = None


class ExportRequest(BaseModel):
    """Export products request"""

    product_ids: List[str]
    format: str = "csv"


@router.get("", response_model=ProductsResponse)
async def get_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_sales: Optional[int] = Query(None, ge=0),
    sort_by: str = "sales_30d",
    sort_order: str = "desc",
    user: Optional[dict] = Depends(get_current_user_optional),
    background_tasks: BackgroundTasks = None,
):
    """
    Get paginated list of products with optional filters.
    Results are cached for 1 hour.
    Works in trial mode (without auth) with limited results.
    """
    cache = CacheService()

    # Build cache key from filters
    cache_key = cache.build_products_cache_key(
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_sales=min_sales,
        sort_by=sort_by,
        page=page,
        per_page=per_page,
    )

    # Check cache
    cached_result = await cache.get(cache_key)
    if cached_result:
        cached_result["cached"] = True
        return ProductsResponse(**cached_result)

    # Fetch from database/scraper
    orchestrator = ScraperOrchestrator()
    result = await orchestrator.get_products(
        page=page,
        per_page=per_page,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_sales=min_sales,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    # Cache result
    await cache.set(cache_key, result, ttl=3600)  # 1 hour

    return ProductsResponse(**result, cached=False)


@router.get("/search", response_model=ProductsResponse)
async def search_products(
    q: str = Query(..., min_length=2, max_length=200),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Search products by keyword.
    Searches in title and description.
    Works in trial mode.
    """
    cache = CacheService()
    orchestrator = ScraperOrchestrator()

    # Check cache
    cache_key = f"search:{q}:{page}:{per_page}"
    cached = await cache.get(cache_key)
    if cached:
        cached["cached"] = True
        return ProductsResponse(**cached)

    # Search
    result = await orchestrator.search_products(query=q, page=page, per_page=per_page)

    # Cache for 30 minutes
    await cache.set(cache_key, result, ttl=1800)

    return ProductsResponse(**result, cached=False)


@router.get("/trending", response_model=ProductsResponse)
async def get_trending_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    category: Optional[str] = None,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Get trending products (high sales velocity).
    Updated every 30 minutes.
    Works in trial mode.
    """
    cache = CacheService()
    orchestrator = ScraperOrchestrator()

    cache_key = f"trending:{category or 'all'}:{page}:{per_page}"
    cached = await cache.get(cache_key)
    if cached:
        cached["cached"] = True
        return ProductsResponse(**cached)

    result = await orchestrator.get_trending_products(
        page=page, per_page=per_page, category=category
    )

    # Cache for 30 minutes
    await cache.set(cache_key, result, ttl=1800)

    return ProductsResponse(**result, cached=False)


@router.get("/categories")
async def get_categories(user: Optional[dict] = Depends(get_current_user_optional)):
    """Get list of available product categories. Works in trial mode."""
    cache = CacheService()

    cached = await cache.get("categories")
    if cached:
        return cached

    orchestrator = ScraperOrchestrator()
    categories = await orchestrator.get_categories()

    # Cache for 24 hours
    await cache.set("categories", categories, ttl=86400)

    return categories


@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """Get single product by ID. Works in trial mode."""
    cache = CacheService()

    cache_key = f"product:{product_id}"
    cached = await cache.get(cache_key)
    if cached:
        return Product(**cached)

    orchestrator = ScraperOrchestrator()
    product = await orchestrator.get_product_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Cache for 1 hour
    await cache.set(cache_key, product, ttl=3600)

    return Product(**product)


@router.post("/refresh")
async def refresh_products(
    background_tasks: BackgroundTasks,
    category: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """
    Trigger a product refresh job.
    Only available for premium users.
    """
    if user.get("plan") not in ["pro", "enterprise"]:
        raise HTTPException(
            status_code=403,
            detail="Product refresh is only available for Pro and Enterprise plans",
        )

    orchestrator = ScraperOrchestrator()
    job_id = await orchestrator.enqueue_refresh_job(
        category=category, user_id=user["id"]
    )

    return {"message": "Refresh job enqueued", "job_id": job_id}


@router.post("/export")
async def export_products(
    request: ExportRequest, user: dict = Depends(get_current_user)
):
    """Export products to CSV/Excel"""
    # Stub implementation - returning a dummy file content
    return Response(
        content="id,title,price\n1,Test Product,10.00",
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"},
    )


@router.get("/stats")
async def get_product_stats(user: Optional[dict] = Depends(get_current_user_optional)):
    """Get product statistics. Works in trial mode."""
    # Stub implementation
    return {
        "total": 100,
        "trending": 10,
        "categories": {"electronics": 50, "fashion": 50},
        "avgPrice": 49.90,
        "totalSales": 5000,
    }
