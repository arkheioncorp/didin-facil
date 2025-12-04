"""
Favorites Use Cases
===================

Business logic for managing user favorites.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Protocol
from uuid import UUID

from domain.usecases.base import UseCase, UseCaseResult

# ==================== Repository Interface ====================

class FavoriteRepository(Protocol):
    """Interface for favorite repository."""
    
    async def get_by_user_and_product(
        self, user_id: UUID, product_id: UUID
    ) -> Optional[dict]:
        """Get favorite by user and product."""
        ...
    
    async def add(
        self,
        user_id: UUID,
        product_id: UUID,
        notes: Optional[str] = None,
    ) -> dict:
        """Add a new favorite."""
        ...
    
    async def remove(self, user_id: UUID, product_id: UUID) -> bool:
        """Remove a favorite."""
        ...
    
    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        """List favorites for a user."""
        ...
    
    async def count_by_user(self, user_id: UUID) -> int:
        """Count favorites for a user."""
        ...


class ProductRepository(Protocol):
    """Interface for product repository."""
    
    async def get_by_id(self, product_id: UUID) -> Optional[dict]:
        """Get product by ID."""
        ...


# ==================== Input/Output DTOs ====================

@dataclass(frozen=True)
class AddFavoriteInput:
    """Input for adding a favorite."""
    user_id: UUID
    product_id: UUID
    notes: Optional[str] = None


@dataclass(frozen=True)
class RemoveFavoriteInput:
    """Input for removing a favorite."""
    user_id: UUID
    product_id: UUID


@dataclass(frozen=True)
class ListFavoritesInput:
    """Input for listing favorites."""
    user_id: UUID
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class GetFavoriteWithProductInput:
    """Input for getting favorite with product details."""
    user_id: UUID
    product_id: UUID


@dataclass
class FavoriteOutput:
    """Output for favorite operations."""
    id: UUID
    user_id: UUID
    product_id: UUID
    notes: Optional[str]
    created_at: datetime


@dataclass
class FavoriteWithProductOutput:
    """Output for favorite with product details."""
    favorite: FavoriteOutput
    product: dict


@dataclass
class FavoriteListOutput:
    """Output for listing favorites."""
    items: List[FavoriteWithProductOutput]
    total: int
    has_more: bool


# ==================== Use Cases ====================

class AddFavoriteUseCase(UseCase[AddFavoriteInput, FavoriteOutput]):
    """
    Add a product to user's favorites.
    
    Business Rules:
    - User can only favorite existing products
    - User cannot favorite the same product twice
    - Notes are optional
    """
    
    def __init__(
        self,
        favorite_repo: FavoriteRepository,
        product_repo: ProductRepository,
    ):
        self.favorite_repo = favorite_repo
        self.product_repo = product_repo
    
    async def execute(
        self, input: AddFavoriteInput
    ) -> UseCaseResult[FavoriteOutput]:
        # Check if product exists
        product = await self.product_repo.get_by_id(input.product_id)
        if not product:
            return UseCaseResult.fail(
                "Product not found",
                error_code="PRODUCT_NOT_FOUND"
            )
        
        # Check if already favorited
        existing = await self.favorite_repo.get_by_user_and_product(
            input.user_id, input.product_id
        )
        if existing:
            return UseCaseResult.fail(
                "Product already in favorites",
                error_code="ALREADY_FAVORITED"
            )
        
        # Add favorite
        favorite = await self.favorite_repo.add(
            user_id=input.user_id,
            product_id=input.product_id,
            notes=input.notes,
        )
        
        output = FavoriteOutput(
            id=favorite["id"],
            user_id=favorite["user_id"],
            product_id=favorite["product_id"],
            notes=favorite.get("notes"),
            created_at=favorite["created_at"],
        )
        
        return UseCaseResult.ok(output)


class RemoveFavoriteUseCase(UseCase[RemoveFavoriteInput, bool]):
    """
    Remove a product from user's favorites.
    
    Business Rules:
    - Only the owner can remove their favorites
    - Returns success even if favorite didn't exist (idempotent)
    """
    
    def __init__(self, favorite_repo: FavoriteRepository):
        self.favorite_repo = favorite_repo
    
    async def execute(
        self, input: RemoveFavoriteInput
    ) -> UseCaseResult[bool]:
        await self.favorite_repo.remove(input.user_id, input.product_id)
        return UseCaseResult.ok(True)


class ListFavoritesUseCase(UseCase[ListFavoritesInput, FavoriteListOutput]):
    """
    List user's favorites with product details.
    
    Business Rules:
    - Returns paginated results
    - Includes product details for each favorite
    - Orders by most recently added
    """
    
    def __init__(
        self,
        favorite_repo: FavoriteRepository,
        product_repo: ProductRepository,
    ):
        self.favorite_repo = favorite_repo
        self.product_repo = product_repo
    
    async def execute(
        self, input: ListFavoritesInput
    ) -> UseCaseResult[FavoriteListOutput]:
        # Get favorites
        favorites = await self.favorite_repo.list_by_user(
            user_id=input.user_id,
            limit=input.limit,
            offset=input.offset,
        )
        
        # Get total count
        total = await self.favorite_repo.count_by_user(input.user_id)
        
        # Enrich with product details
        items: List[FavoriteWithProductOutput] = []
        for fav in favorites:
            product = await self.product_repo.get_by_id(fav["product_id"])
            if product:
                items.append(FavoriteWithProductOutput(
                    favorite=FavoriteOutput(
                        id=fav["id"],
                        user_id=fav["user_id"],
                        product_id=fav["product_id"],
                        notes=fav.get("notes"),
                        created_at=fav["created_at"],
                    ),
                    product=product,
                ))
        
        output = FavoriteListOutput(
            items=items,
            total=total,
            has_more=input.offset + len(items) < total,
        )
        
        return UseCaseResult.ok(output)


class GetFavoriteWithProductUseCase(
    UseCase[GetFavoriteWithProductInput, FavoriteWithProductOutput]
):
    """
    Get a single favorite with product details.
    
    Business Rules:
    - Returns 404 if favorite doesn't exist
    - Returns 404 if product was deleted
    """
    
    def __init__(
        self,
        favorite_repo: FavoriteRepository,
        product_repo: ProductRepository,
    ):
        self.favorite_repo = favorite_repo
        self.product_repo = product_repo
    
    async def execute(
        self, input: GetFavoriteWithProductInput
    ) -> UseCaseResult[FavoriteWithProductOutput]:
        # Get favorite
        fav = await self.favorite_repo.get_by_user_and_product(
            input.user_id, input.product_id
        )
        if not fav:
            return UseCaseResult.fail(
                "Favorite not found",
                error_code="FAVORITE_NOT_FOUND"
            )
        
        # Get product
        product = await self.product_repo.get_by_id(fav["product_id"])
        if not product:
            return UseCaseResult.fail(
                "Product no longer exists",
                error_code="PRODUCT_DELETED"
            )
        
        output = FavoriteWithProductOutput(
            favorite=FavoriteOutput(
                id=fav["id"],
                user_id=fav["user_id"],
                product_id=fav["product_id"],
                notes=fav.get("notes"),
                created_at=fav["created_at"],
            ),
            product=product,
        )
        
        return UseCaseResult.ok(output)
