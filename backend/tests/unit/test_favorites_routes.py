"""
Testes para Favorites Routes
=============================
Cobertura completa para api/routes/favorites.py
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


# Fixtures
@pytest.fixture
def mock_user():
    """Mock de usuário autenticado."""
    return {"id": str(uuid4()), "email": "test@example.com"}


@pytest.fixture
def mock_db():
    """Mock do database."""
    db = AsyncMock()
    db.fetch_all = AsyncMock(return_value=[])
    db.fetch_one = AsyncMock(return_value=None)
    db.execute = AsyncMock(return_value=1)
    return db


@pytest.fixture
def favorite_data():
    """Dados de favorito."""
    return {
        "product_id": str(uuid4()),
        "list_id": str(uuid4()),
        "notes": "Great product!",
    }


@pytest.fixture
def list_data():
    """Dados de lista de favoritos."""
    return {
        "name": "Wish List",
        "description": "My wish list",
        "color": "#FF5733",
        "icon": "heart",
    }


@pytest.fixture
def mock_cache():
    """Mock do CacheService."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete_pattern = AsyncMock(return_value=0)
    return cache


# ==================== GET FAVORITES TESTS ====================


class TestGetFavorites:
    """Testes do endpoint GET favorites."""

    @pytest.mark.asyncio
    async def test_get_favorites_empty(self, mock_user, mock_db, mock_cache):
        """Testa listagem vazia de favoritos."""
        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.cache", mock_cache):
            from api.routes.favorites import get_favorites

            result = await get_favorites(None, 100, 0, mock_user)

            assert result == []

    @pytest.mark.asyncio
    async def test_get_favorites_with_products(self, mock_user, mock_cache):
        """Testa listagem de favoritos com produtos."""
        now = datetime.now(timezone.utc)
        fav_id_1 = str(uuid4())
        fav_id_2 = str(uuid4())
        prod_id_1 = str(uuid4())
        prod_id_2 = str(uuid4())
        list_id_1 = str(uuid4())
        
        mock_db = MagicMock()
        mock_db.fetch_all = AsyncMock(
            return_value=[
                {
                    "id": fav_id_1,
                    "product_id": prod_id_1,
                    "list_id": None,
                    "notes": "Nice!",
                    "added_at": now,
                    "product_title": "Product 1",
                    "product_description": "Desc 1",
                    "product_price": 99.90,
                    "product_original_price": 129.90,
                    "currency": "BRL",
                    "product_image_url": "http://img.com/1.jpg",
                    "product_url": "http://shop.com/1",
                    "product_sales_count": 100,
                    "product_rating": 4.5,
                    "shop_name": "Shop 1",
                    "is_trending": True,
                },
                {
                    "id": fav_id_2,
                    "product_id": prod_id_2,
                    "list_id": list_id_1,
                    "notes": None,
                    "added_at": now,
                    "product_title": None,  # Produto não encontrado
                    "product_description": None,
                    "product_price": None,
                    "product_original_price": None,
                    "currency": None,
                    "product_image_url": None,
                    "product_url": None,
                    "product_sales_count": None,
                    "product_rating": None,
                    "shop_name": None,
                    "is_trending": None,
                },
            ]
        )

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.cache", mock_cache):
            from api.routes.favorites import get_favorites

            result = await get_favorites(None, 100, 0, mock_user)

            assert len(result) == 2
            assert result[0].product is not None
            assert result[0].product.title == "Product 1"
            assert result[1].product is None

    @pytest.mark.asyncio
    async def test_get_favorites_with_list_filter(self, mock_user, mock_db, mock_cache):
        """Testa listagem com filtro de lista."""
        mock_db.fetch_all = AsyncMock(return_value=[])
        list_id = str(uuid4())

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.cache", mock_cache):
            from api.routes.favorites import get_favorites

            result = await get_favorites(list_id, 100, 0, mock_user)

            assert result == []
            # Verificar que query inclui list_id
            call_args = mock_db.fetch_all.call_args
            assert "list_id" in call_args.kwargs.get("values", {})


# ==================== ADD FAVORITE TESTS ====================


class TestAddFavorite:
    """Testes do endpoint POST favorites."""

    @pytest.mark.asyncio
    async def test_add_favorite_success(self, mock_user, favorite_data, mock_cache):
        """Testa adição de favorito com sucesso."""
        mock_db = MagicMock()
        mock_db.fetch_one = AsyncMock(return_value=None)  # Não existe
        mock_db.execute = AsyncMock(return_value=1)

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.cache", mock_cache):
            from api.routes.favorites import FavoriteCreate, add_favorite

            request = FavoriteCreate(**favorite_data)
            result = await add_favorite(request, mock_user)

            assert result.product_id == favorite_data["product_id"]
            assert result.list_id == favorite_data["list_id"]
            assert result.notes == favorite_data["notes"]
            mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_favorite_already_exists(
        self, mock_user, mock_db, favorite_data, mock_cache
    ):
        """Testa adição de favorito já existente."""
        mock_db.fetch_one = AsyncMock(return_value={"id": str(uuid4())})

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.cache", mock_cache):
            from api.routes.favorites import FavoriteCreate, add_favorite
            from fastapi import HTTPException

            request = FavoriteCreate(**favorite_data)

            with pytest.raises(HTTPException) as exc_info:
                await add_favorite(request, mock_user)

            assert exc_info.value.status_code == 409
            assert "already in favorites" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_add_favorite_without_list(self, mock_user, mock_cache):
        """Testa adição de favorito sem lista."""
        mock_db = MagicMock()
        mock_db.fetch_one = AsyncMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=1)

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.cache", mock_cache):
            from api.routes.favorites import FavoriteCreate, add_favorite

            # product_id must be a valid UUID
            request = FavoriteCreate(product_id=str(uuid4()))
            result = await add_favorite(request, mock_user)

            assert result.list_id is None
            assert result.notes is None


# ==================== REMOVE FAVORITE TESTS ====================


class TestRemoveFavorite:
    """Testes do endpoint DELETE favorites."""

    @pytest.mark.asyncio
    async def test_remove_favorite_success(self, mock_user, mock_db, mock_cache):
        """Testa remoção de favorito com sucesso."""
        mock_db.execute = AsyncMock(return_value=1)  # 1 row affected

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.cache", mock_cache):
            from api.routes.favorites import remove_favorite

            result = await remove_favorite(str(uuid4()), mock_user)

            assert result is None
            mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_favorite_not_found(self, mock_user, mock_cache):
        """Testa remoção de favorito não encontrado."""
        mock_db = MagicMock()
        mock_db.execute = AsyncMock(return_value=0)  # No rows affected

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.cache", mock_cache):
            from api.routes.favorites import remove_favorite
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await remove_favorite(str(uuid4()), mock_user)

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail


# ==================== FAVORITE LISTS TESTS ====================


class TestFavoriteLists:
    """Testes dos endpoints de listas de favoritos."""

    @pytest.mark.asyncio
    async def test_get_favorite_lists_empty(self, mock_user, mock_db):
        """Testa listagem vazia de listas."""
        mock_db.fetch_all = AsyncMock(return_value=[])

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.get_current_user",
                   return_value=mock_user):
            from api.routes.favorites import get_favorite_lists

            result = await get_favorite_lists(mock_user)

            assert result == []

    @pytest.mark.asyncio
    async def test_get_favorite_lists_with_data(self, mock_user, mock_db):
        """Testa listagem de listas com dados."""
        now = datetime.now(timezone.utc)
        list_id_1 = str(uuid4())
        list_id_2 = str(uuid4())
        
        mock_db.fetch_all = AsyncMock(
            return_value=[
                {
                    "id": list_id_1,
                    "name": "Wish List",
                    "description": "My wishes",
                    "color": "#FF0000",
                    "icon": "heart",
                    "item_count": 5,
                    "created_at": now,
                },
                {
                    "id": list_id_2,
                    "name": "To Buy",
                    "description": None,
                    "color": None,
                    "icon": None,
                    "item_count": 0,
                    "created_at": now,
                },
            ]
        )

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.get_current_user",
                   return_value=mock_user):
            from api.routes.favorites import get_favorite_lists

            result = await get_favorite_lists(mock_user)

            assert len(result) == 2
            assert result[0].name == "Wish List"
            assert result[0].item_count == 5
            assert result[1].item_count == 0

    @pytest.mark.asyncio
    async def test_create_favorite_list(self, mock_user, mock_db, list_data):
        """Testa criação de lista de favoritos."""
        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.get_current_user", return_value=mock_user):
            from api.routes.favorites import (FavoriteListCreate,
                                              create_favorite_list)

            request = FavoriteListCreate(**list_data)
            result = await create_favorite_list(request, mock_user)

            assert result.name == list_data["name"]
            assert result.description == list_data["description"]
            assert result.color == list_data["color"]
            assert result.icon == list_data["icon"]
            assert result.item_count == 0
            mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_favorite_list_minimal(self, mock_user, mock_db):
        """Testa criação de lista com dados mínimos."""
        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.get_current_user", return_value=mock_user):
            from api.routes.favorites import (FavoriteListCreate,
                                              create_favorite_list)

            request = FavoriteListCreate(name="Simple List")
            result = await create_favorite_list(request, mock_user)

            assert result.name == "Simple List"
            assert result.description is None
            assert result.color is None

    @pytest.mark.asyncio
    async def test_delete_favorite_list_success(self, mock_user, mock_db):
        """Testa remoção de lista com sucesso."""
        mock_db.execute = AsyncMock(return_value=1)
        list_id = str(uuid4())

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.get_current_user",
                   return_value=mock_user):
            from api.routes.favorites import delete_favorite_list

            result = await delete_favorite_list(list_id, mock_user)

            assert result is None
            # Deve chamar execute 2 vezes: update + delete
            assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_delete_favorite_list_not_found(self, mock_user, mock_db):
        """Testa remoção de lista não encontrada."""
        # Primeiro execute (update) retorna ok, segundo (delete) retorna 0
        mock_db.execute = AsyncMock(side_effect=[1, 0])
        list_id = str(uuid4())

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.get_current_user",
                   return_value=mock_user):
            from api.routes.favorites import delete_favorite_list
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await delete_favorite_list(list_id, mock_user)

            assert exc_info.value.status_code == 404


# ==================== SCHEMA TESTS ====================


class TestSchemas:
    """Testes dos schemas."""

    def test_product_info_schema(self):
        """Testa schema de ProductInfo."""
        from api.routes.favorites import ProductInfo

        product_id = str(uuid4())
        product = ProductInfo(
            id=product_id,
            title="Test Product",
            price=99.90,
        )
        assert product.id == product_id
        assert product.currency == "BRL"
        assert product.is_trending is False

    def test_favorite_create_schema(self):
        """Testa schema de FavoriteCreate."""
        from api.routes.favorites import FavoriteCreate

        product_id = str(uuid4())
        fav = FavoriteCreate(product_id=product_id)
        assert fav.product_id == product_id
        assert fav.list_id is None
        assert fav.notes is None

    def test_favorite_response_schema(self):
        """Testa schema de FavoriteResponse."""
        from api.routes.favorites import FavoriteResponse

        now = datetime.now(timezone.utc)
        fav = FavoriteResponse(
            id="fav-1",
            product_id="prod-1",
            added_at=now,
        )
        assert fav.id == "fav-1"
        assert fav.product is None

    def test_favorite_list_create_schema(self):
        """Testa schema de FavoriteListCreate."""
        from api.routes.favorites import FavoriteListCreate

        lst = FavoriteListCreate(name="My List")
        assert lst.name == "My List"
        assert lst.color is None

    def test_favorite_list_create_with_color(self):
        """Testa schema com cor válida."""
        from api.routes.favorites import FavoriteListCreate

        lst = FavoriteListCreate(name="List", color="#AABBCC")
        assert lst.color == "#AABBCC"

    def test_favorite_list_response_schema(self):
        """Testa schema de FavoriteListResponse."""
        from api.routes.favorites import FavoriteListResponse

        now = datetime.now(timezone.utc)
        list_id = str(uuid4())
        lst = FavoriteListResponse(
            id=list_id,
            name="My List",
            created_at=now,
        )
        assert lst.item_count == 0


# ==================== EDGE CASES ====================


class TestEdgeCases:
    """Testes de casos extremos."""

    @pytest.mark.asyncio
    async def test_get_favorites_with_pagination(
        self, mock_user, mock_db, mock_cache
    ):
        """Testa paginação de favoritos."""
        mock_db.fetch_all = AsyncMock(return_value=[])

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.cache", mock_cache):
            from api.routes.favorites import get_favorites

            _ = await get_favorites(None, 10, 20, mock_user)

            # Verificar que offset/limit são passados
            call_args = mock_db.fetch_all.call_args
            values = call_args.kwargs.get("values", {})
            assert values.get("limit") == 10
            assert values.get("offset") == 20

    @pytest.mark.asyncio
    async def test_product_with_null_values(self, mock_user, mock_cache):
        """Testa produto com valores nulos."""
        now = datetime.now(timezone.utc)
        fav_id = str(uuid4())
        product_id = str(uuid4())
        mock_db = MagicMock()
        mock_db.fetch_all = AsyncMock(
            return_value=[
                {
                    "id": fav_id,
                    "product_id": product_id,
                    "list_id": None,
                    "notes": None,
                    "added_at": now,
                    "product_title": "Product",
                    "product_description": None,
                    "product_price": None,
                    "product_original_price": None,
                    "currency": None,
                    "product_image_url": None,
                    "product_url": None,
                    "product_sales_count": None,
                    "product_rating": None,
                    "shop_name": None,
                    "is_trending": None,
                }
            ]
        )

        with patch("api.routes.favorites.database", mock_db), \
             patch("api.routes.favorites.cache", mock_cache):
            from api.routes.favorites import get_favorites

            result = await get_favorites(None, 100, 0, mock_user)

            assert len(result) == 1
            assert result[0].product is not None
            assert result[0].product.price == 0
            assert result[0].product.currency == "BRL"
