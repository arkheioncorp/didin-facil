"""
Favorites Routes
User favorites management API

Performance optimizations:
- Cache favorites list for 5 minutes
- Cache invalidation on add/remove
"""

from datetime import datetime, timezone
from typing import List, Optional, Union
from uuid import UUID

from api.database.connection import database
from api.middleware.auth import get_current_user
from api.services.cache import CacheService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter()
cache = CacheService()


def to_uuid(value: Union[str, UUID, "asyncpg.pgproto.pgproto.UUID"]) -> UUID:
    """Convert any UUID-like value to Python UUID"""
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


class ProductInfo(BaseModel):
    """Product info embedded in favorite"""
    id: str
    title: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    currency: str = "BRL"
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    sales_count: int = 0
    product_rating: Optional[float] = None
    shop_name: Optional[str] = None
    is_trending: bool = False


class FavoriteCreate(BaseModel):
    """Create favorite request"""
    product_id: str
    list_id: Optional[str] = None
    notes: Optional[str] = None


class FavoriteResponse(BaseModel):
    """Favorite response"""
    id: str
    product_id: str
    list_id: Optional[str] = None
    notes: Optional[str] = None
    added_at: datetime
    product: Optional[ProductInfo] = None


class FavoriteListCreate(BaseModel):
    """Create favorite list request"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None


class FavoriteListResponse(BaseModel):
    """Favorite list response"""
    id: str
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    item_count: int = 0
    created_at: datetime


# =====================================================
# ROUTES: Lists (MUST come before /{product_id})
# =====================================================

@router.get("/lists", response_model=List[FavoriteListResponse])
async def get_favorite_lists(
    user: dict = Depends(get_current_user),
):
    """Get user's favorite lists"""
    user_id = to_uuid(user["id"])

    query = """
        SELECT 
            fl.id,
            fl.name,
            fl.description,
            fl.color,
            fl.icon,
            fl.created_at,
            COUNT(f.id) as item_count
        FROM favorite_lists fl
        LEFT JOIN favorites f ON fl.id = f.list_id
        WHERE fl.user_id = :user_id
        GROUP BY fl.id
        ORDER BY fl.created_at DESC
    """

    rows = await database.fetch_all(query=query, values={"user_id": user_id})

    return [
        FavoriteListResponse(
            id=str(row["id"]),
            name=row["name"],
            description=row["description"],
            color=row["color"],
            icon=row["icon"],
            item_count=row["item_count"] or 0,
            created_at=row["created_at"],
        )
        for row in rows
    ]


@router.post("/lists", response_model=FavoriteListResponse, status_code=status.HTTP_201_CREATED)
async def create_favorite_list(
    request: FavoriteListCreate,
    user: dict = Depends(get_current_user),
):
    """Create a new favorite list"""
    import uuid

    user_id = to_uuid(user["id"])
    list_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    await database.execute(
        query="""
            INSERT INTO favorite_lists (id, user_id, name, description, color, icon, created_at)
            VALUES (:id, :user_id, :name, :description, :color, :icon, :created_at)
        """,
        values={
            "id": list_id,
            "user_id": user_id,
            "name": request.name,
            "description": request.description,
            "color": request.color,
            "icon": request.icon,
            "created_at": now,
        }
    )

    return FavoriteListResponse(
        id=str(list_id),
        name=request.name,
        description=request.description,
        color=request.color,
        icon=request.icon,
        item_count=0,
        created_at=now,
    )


@router.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite_list(
    list_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete a favorite list (favorites are moved to default)"""
    user_id = to_uuid(user["id"])
    list_uuid = to_uuid(list_id)

    # Move favorites to null (default)
    await database.execute(
        query="UPDATE favorites SET list_id = NULL WHERE list_id = :list_id AND user_id = :user_id",
        values={"list_id": list_uuid, "user_id": user_id}
    )

    # Delete the list
    result = await database.execute(
        query="DELETE FROM favorite_lists WHERE id = :list_id AND user_id = :user_id",
        values={"list_id": list_uuid, "user_id": user_id}
    )

    if result == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite list not found"
        )

    return None


# =====================================================
# ROUTES: Favorites (after /lists routes)
# =====================================================

@router.get("", response_model=List[FavoriteResponse])
async def get_favorites(
    list_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    """Get user's favorites with product info (cached for 5 minutes)"""
    user_id = to_uuid(user["id"])
    
    # Check cache first
    cache_key = f"favorites:{user['id']}:{list_id or 'all'}:{limit}:{offset}"
    cached = await cache.get(cache_key)
    if cached:
        return [FavoriteResponse(**f) for f in cached]

    # Build query
    if list_id:
        list_uuid = to_uuid(list_id)
        query = """
            SELECT 
                f.id,
                f.product_id,
                f.list_id,
                f.notes,
                f.created_at as added_at,
                p.title as product_title,
                p.description as product_description,
                p.price as product_price,
                p.original_price as product_original_price,
                p.currency,
                p.image_url as product_image_url,
                p.product_url,
                p.sales_count as product_sales_count,
                p.product_rating,
                p.shop_name,
                p.is_trending
            FROM favorites f
            LEFT JOIN products p ON f.product_id = p.id
            WHERE f.user_id = :user_id AND f.list_id = :list_id
            ORDER BY f.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        rows = await database.fetch_all(
            query=query,
            values={"user_id": user_id, "list_id": list_uuid, "limit": limit, "offset": offset}
        )
    else:
        query = """
            SELECT 
                f.id,
                f.product_id,
                f.list_id,
                f.notes,
                f.created_at as added_at,
                p.title as product_title,
                p.description as product_description,
                p.price as product_price,
                p.original_price as product_original_price,
                p.currency,
                p.image_url as product_image_url,
                p.product_url,
                p.sales_count as product_sales_count,
                p.product_rating,
                p.shop_name,
                p.is_trending
            FROM favorites f
            LEFT JOIN products p ON f.product_id = p.id
            WHERE f.user_id = :user_id
            ORDER BY f.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        rows = await database.fetch_all(
            query=query,
            values={"user_id": user_id, "limit": limit, "offset": offset}
        )

    # Map to response
    favorites = []
    for row in rows:
        product = None
        if row["product_title"]:
            product = ProductInfo(
                id=str(row["product_id"]),
                title=row["product_title"],
                description=row["product_description"],
                price=float(row["product_price"]) if row["product_price"] else 0,
                original_price=float(row["product_original_price"]) if row["product_original_price"] else None,
                currency=row["currency"] or "BRL",
                image_url=row["product_image_url"],
                product_url=row["product_url"],
                sales_count=row["product_sales_count"] or 0,
                product_rating=float(row["product_rating"]) if row["product_rating"] else None,
                shop_name=row["shop_name"],
                is_trending=row["is_trending"] or False,
            )

        favorites.append(FavoriteResponse(
            id=str(row["id"]),
            product_id=str(row["product_id"]),
            list_id=str(row["list_id"]) if row["list_id"] else None,
            notes=row["notes"],
            added_at=row["added_at"],
            product=product,
        ))

    # Cache the result for 5 minutes
    await cache.set(cache_key, [f.model_dump() for f in favorites], ttl=300)

    return favorites


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    request: FavoriteCreate,
    user: dict = Depends(get_current_user),
):
    """Add a product to favorites"""
    import uuid

    user_id = to_uuid(user["id"])
    product_uuid = to_uuid(request.product_id)
    favorite_id = uuid.uuid4()
    
    # Invalidate cache when adding
    await cache.delete_pattern(f"favorites:{user['id']}:*")
    now = datetime.now(timezone.utc)

    # Check if already favorited
    existing = await database.fetch_one(
        query="SELECT id FROM favorites WHERE user_id = :user_id AND product_id = :product_id",
        values={"user_id": user_id, "product_id": product_uuid}
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already in favorites"
        )

    # Insert favorite
    if request.list_id:
        list_uuid = to_uuid(request.list_id)
        await database.execute(
            query="""
                INSERT INTO favorites (id, user_id, product_id, list_id, notes, created_at)
                VALUES (:id, :user_id, :product_id, :list_id, :notes, :created_at)
            """,
            values={
                "id": favorite_id,
                "user_id": user_id,
                "product_id": product_uuid,
                "list_id": list_uuid,
                "notes": request.notes,
                "created_at": now,
            }
        )
    else:
        await database.execute(
            query="""
                INSERT INTO favorites (id, user_id, product_id, notes, created_at)
                VALUES (:id, :user_id, :product_id, :notes, :created_at)
            """,
            values={
                "id": favorite_id,
                "user_id": user_id,
                "product_id": product_uuid,
                "notes": request.notes,
                "created_at": now,
            }
        )

    return FavoriteResponse(
        id=str(favorite_id),
        product_id=request.product_id,
        list_id=request.list_id,
        notes=request.notes,
        added_at=now,
        product=None,
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    product_id: str,
    user: dict = Depends(get_current_user),
):
    """Remove a product from favorites"""
    user_id = to_uuid(user["id"])
    product_uuid = to_uuid(product_id)
    
    # Invalidate cache before delete
    await cache.delete_pattern(f"favorites:{user['id']}:*")

    result = await database.execute(
        query="DELETE FROM favorites WHERE user_id = :user_id AND product_id = :product_id",
        values={"user_id": user_id, "product_id": product_uuid}
    )

    if result == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )

    return None
