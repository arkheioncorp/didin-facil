"""
Tests for Favorites Use Cases
=============================

Unit tests for favorite management use cases.
Uses mock repositories to test business logic in isolation.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from domain.usecases.favorites import (AddFavoriteInput, AddFavoriteUseCase,
                                       GetFavoriteWithProductInput,
                                       GetFavoriteWithProductUseCase,
                                       ListFavoritesInput,
                                       ListFavoritesUseCase,
                                       RemoveFavoriteInput,
                                       RemoveFavoriteUseCase)

# ==================== Fixtures ====================

@pytest.fixture
def mock_favorite_repo():
    """Create mock favorite repository."""
    return AsyncMock()


@pytest.fixture
def mock_product_repo():
    """Create mock product repository."""
    return AsyncMock()


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return uuid4()


@pytest.fixture
def sample_product_id():
    """Sample product ID."""
    return uuid4()


@pytest.fixture
def sample_product(sample_product_id):
    """Sample product data."""
    return {
        "id": sample_product_id,
        "title": "Test Product",
        "description": "A great product",
        "price": 99.99,
        "image_url": "https://example.com/image.jpg",
        "source": "tiktok_shop",
    }


@pytest.fixture
def sample_favorite(sample_user_id, sample_product_id):
    """Sample favorite data."""
    return {
        "id": uuid4(),
        "user_id": sample_user_id,
        "product_id": sample_product_id,
        "notes": "Love this product!",
        "created_at": datetime.now(timezone.utc),
    }


# ==================== AddFavoriteUseCase Tests ====================

class TestAddFavoriteUseCase:
    """Tests for AddFavoriteUseCase."""
    
    @pytest.mark.asyncio
    async def test_add_favorite_success(
        self,
        mock_favorite_repo,
        mock_product_repo,
        sample_user_id,
        sample_product_id,
        sample_product,
        sample_favorite,
    ):
        """Should successfully add a favorite."""
        # Arrange
        mock_product_repo.get_by_id.return_value = sample_product
        mock_favorite_repo.get_by_user_and_product.return_value = None
        mock_favorite_repo.add.return_value = sample_favorite
        
        use_case = AddFavoriteUseCase(
            favorite_repo=mock_favorite_repo,
            product_repo=mock_product_repo,
        )
        
        input_data = AddFavoriteInput(
            user_id=sample_user_id,
            product_id=sample_product_id,
            notes="Love this product!",
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is True
        assert result.data is not None
        assert result.data.product_id == sample_product_id
        assert result.data.notes == "Love this product!"
        
        mock_favorite_repo.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_favorite_product_not_found(
        self,
        mock_favorite_repo,
        mock_product_repo,
        sample_user_id,
        sample_product_id,
    ):
        """Should fail if product doesn't exist."""
        # Arrange
        mock_product_repo.get_by_id.return_value = None
        
        use_case = AddFavoriteUseCase(
            favorite_repo=mock_favorite_repo,
            product_repo=mock_product_repo,
        )
        
        input_data = AddFavoriteInput(
            user_id=sample_user_id,
            product_id=sample_product_id,
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is False
        assert result.error_code == "PRODUCT_NOT_FOUND"
        mock_favorite_repo.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_add_favorite_already_exists(
        self,
        mock_favorite_repo,
        mock_product_repo,
        sample_user_id,
        sample_product_id,
        sample_product,
        sample_favorite,
    ):
        """Should fail if product is already favorited."""
        # Arrange
        mock_product_repo.get_by_id.return_value = sample_product
        mock_favorite_repo.get_by_user_and_product.return_value = sample_favorite
        
        use_case = AddFavoriteUseCase(
            favorite_repo=mock_favorite_repo,
            product_repo=mock_product_repo,
        )
        
        input_data = AddFavoriteInput(
            user_id=sample_user_id,
            product_id=sample_product_id,
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is False
        assert result.error_code == "ALREADY_FAVORITED"
        mock_favorite_repo.add.assert_not_called()


# ==================== RemoveFavoriteUseCase Tests ====================

class TestRemoveFavoriteUseCase:
    """Tests for RemoveFavoriteUseCase."""
    
    @pytest.mark.asyncio
    async def test_remove_favorite_success(
        self,
        mock_favorite_repo,
        sample_user_id,
        sample_product_id,
    ):
        """Should successfully remove a favorite."""
        # Arrange
        mock_favorite_repo.remove.return_value = True
        
        use_case = RemoveFavoriteUseCase(favorite_repo=mock_favorite_repo)
        
        input_data = RemoveFavoriteInput(
            user_id=sample_user_id,
            product_id=sample_product_id,
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is True
        assert result.data is True
        mock_favorite_repo.remove.assert_called_once_with(
            sample_user_id, sample_product_id
        )
    
    @pytest.mark.asyncio
    async def test_remove_favorite_idempotent(
        self,
        mock_favorite_repo,
        sample_user_id,
        sample_product_id,
    ):
        """Should succeed even if favorite doesn't exist (idempotent)."""
        # Arrange
        mock_favorite_repo.remove.return_value = False  # Didn't exist
        
        use_case = RemoveFavoriteUseCase(favorite_repo=mock_favorite_repo)
        
        input_data = RemoveFavoriteInput(
            user_id=sample_user_id,
            product_id=sample_product_id,
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is True  # Still success (idempotent)


# ==================== ListFavoritesUseCase Tests ====================

class TestListFavoritesUseCase:
    """Tests for ListFavoritesUseCase."""
    
    @pytest.mark.asyncio
    async def test_list_favorites_success(
        self,
        mock_favorite_repo,
        mock_product_repo,
        sample_user_id,
        sample_product_id,
        sample_product,
        sample_favorite,
    ):
        """Should successfully list favorites with products."""
        # Arrange
        mock_favorite_repo.list_by_user.return_value = [sample_favorite]
        mock_favorite_repo.count_by_user.return_value = 1
        mock_product_repo.get_by_id.return_value = sample_product
        
        use_case = ListFavoritesUseCase(
            favorite_repo=mock_favorite_repo,
            product_repo=mock_product_repo,
        )
        
        input_data = ListFavoritesInput(
            user_id=sample_user_id,
            limit=10,
            offset=0,
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is True
        assert len(result.data.items) == 1
        assert result.data.total == 1
        assert result.data.has_more is False
        assert result.data.items[0].product["title"] == "Test Product"
    
    @pytest.mark.asyncio
    async def test_list_favorites_empty(
        self,
        mock_favorite_repo,
        mock_product_repo,
        sample_user_id,
    ):
        """Should return empty list for user with no favorites."""
        # Arrange
        mock_favorite_repo.list_by_user.return_value = []
        mock_favorite_repo.count_by_user.return_value = 0
        
        use_case = ListFavoritesUseCase(
            favorite_repo=mock_favorite_repo,
            product_repo=mock_product_repo,
        )
        
        input_data = ListFavoritesInput(user_id=sample_user_id)
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is True
        assert len(result.data.items) == 0
        assert result.data.total == 0
    
    @pytest.mark.asyncio
    async def test_list_favorites_pagination(
        self,
        mock_favorite_repo,
        mock_product_repo,
        sample_user_id,
    ):
        """Should correctly indicate has_more for pagination."""
        # Arrange
        mock_favorite_repo.list_by_user.return_value = []
        mock_favorite_repo.count_by_user.return_value = 25  # More than returned
        
        use_case = ListFavoritesUseCase(
            favorite_repo=mock_favorite_repo,
            product_repo=mock_product_repo,
        )
        
        input_data = ListFavoritesInput(
            user_id=sample_user_id,
            limit=10,
            offset=0,
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is True
        assert result.data.has_more is True


# ==================== GetFavoriteWithProductUseCase Tests ====================

class TestGetFavoriteWithProductUseCase:
    """Tests for GetFavoriteWithProductUseCase."""
    
    @pytest.mark.asyncio
    async def test_get_favorite_success(
        self,
        mock_favorite_repo,
        mock_product_repo,
        sample_user_id,
        sample_product_id,
        sample_product,
        sample_favorite,
    ):
        """Should successfully get favorite with product."""
        # Arrange
        mock_favorite_repo.get_by_user_and_product.return_value = sample_favorite
        mock_product_repo.get_by_id.return_value = sample_product
        
        use_case = GetFavoriteWithProductUseCase(
            favorite_repo=mock_favorite_repo,
            product_repo=mock_product_repo,
        )
        
        input_data = GetFavoriteWithProductInput(
            user_id=sample_user_id,
            product_id=sample_product_id,
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is True
        assert result.data.favorite.product_id == sample_product_id
        assert result.data.product["title"] == "Test Product"
    
    @pytest.mark.asyncio
    async def test_get_favorite_not_found(
        self,
        mock_favorite_repo,
        mock_product_repo,
        sample_user_id,
        sample_product_id,
    ):
        """Should fail if favorite doesn't exist."""
        # Arrange
        mock_favorite_repo.get_by_user_and_product.return_value = None
        
        use_case = GetFavoriteWithProductUseCase(
            favorite_repo=mock_favorite_repo,
            product_repo=mock_product_repo,
        )
        
        input_data = GetFavoriteWithProductInput(
            user_id=sample_user_id,
            product_id=sample_product_id,
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is False
        assert result.error_code == "FAVORITE_NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_get_favorite_product_deleted(
        self,
        mock_favorite_repo,
        mock_product_repo,
        sample_user_id,
        sample_product_id,
        sample_favorite,
    ):
        """Should fail if product was deleted."""
        # Arrange
        mock_favorite_repo.get_by_user_and_product.return_value = sample_favorite
        mock_product_repo.get_by_id.return_value = None  # Product deleted
        
        use_case = GetFavoriteWithProductUseCase(
            favorite_repo=mock_favorite_repo,
            product_repo=mock_product_repo,
        )
        
        input_data = GetFavoriteWithProductInput(
            user_id=sample_user_id,
            product_id=sample_product_id,
        )
        
        # Act
        result = await use_case.execute(input_data)
        
        # Assert
        assert result.success is False
        assert result.error_code == "PRODUCT_DELETED"
