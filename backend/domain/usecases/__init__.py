"""
Use Cases Layer
===============

Application business logic organized by feature.
Each use case represents a single action that can be performed in the system.

Following Clean Architecture / Hexagonal Architecture principles:
- Use cases depend only on domain entities and repository interfaces
- Infrastructure details are injected via dependency injection
- Each use case has a single responsibility

Organization:
- favorites/: Favorite products management
- copy/: AI copy generation
- products/: Product search and management
- auth/: Authentication workflows
"""

from .base import UseCase, UseCaseResult
from .copy import (CopyHistoryItem, CopyHistoryOutput, GenerateCopyInput,
                   GenerateCopyUseCase, GeneratedCopyOutput,
                   GetCopyHistoryInput, GetCopyHistoryUseCase)
from .favorites import (AddFavoriteInput, AddFavoriteUseCase,
                        FavoriteListOutput, FavoriteOutput,
                        FavoriteWithProductOutput, GetFavoriteWithProductInput,
                        GetFavoriteWithProductUseCase, ListFavoritesInput,
                        ListFavoritesUseCase, RemoveFavoriteInput,
                        RemoveFavoriteUseCase)

__all__ = [
    # Base
    "UseCase",
    "UseCaseResult",
    # Favorites
    "AddFavoriteUseCase",
    "RemoveFavoriteUseCase",
    "ListFavoritesUseCase",
    "GetFavoriteWithProductUseCase",
    "AddFavoriteInput",
    "RemoveFavoriteInput",
    "ListFavoritesInput",
    "GetFavoriteWithProductInput",
    "FavoriteOutput",
    "FavoriteWithProductOutput",
    "FavoriteListOutput",
    # Copy
    "GenerateCopyUseCase",
    "GetCopyHistoryUseCase",
    "GenerateCopyInput",
    "GetCopyHistoryInput",
    "GeneratedCopyOutput",
    "CopyHistoryOutput",
    "CopyHistoryItem",
]
