"""
Testes para integrações de marketplaces.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from backend.integrations.marketplaces.base import (
    MarketplaceType,
    Product,
    ProductCondition,
    SearchResult,
)
from backend.integrations.marketplaces.mercadolivre import MercadoLivreClient
from backend.integrations.marketplaces.shopee import ShopeeClient
from backend.integrations.marketplaces.manager import MarketplaceManager


# === Fixtures ===

@pytest.fixture
def sample_ml_product():
    """Produto de exemplo do Mercado Livre."""
    return {
        "id": "MLB123456789",
        "title": "iPhone 15 128GB Preto",
        "price": 5499.00,
        "original_price": 6999.00,
        "currency_id": "BRL",
        "permalink": "https://www.mercadolivre.com.br/p/MLB123456789",
        "thumbnail": "https://http2.mlstatic.com/D_123456-MLA123456789_123456-O.jpg",
        "pictures": [
            {"secure_url": "https://http2.mlstatic.com/D_123456-MLA123456789_123456-F.jpg"}
        ],
        "condition": "new",
        "shipping": {"free_shipping": True},
        "seller": {
            "id": 123456,
            "nickname": "APPLE_OFICIAL",
        },
        "official_store_id": 123,
        "sold_quantity": 1500,
        "available_quantity": 50,
        "reviews": {
            "rating_average": 4.8,
            "total": 250,
        },
        "attributes": [
            {"name": "Marca", "value_name": "Apple"},
            {"name": "Modelo", "value_name": "iPhone 15"},
        ],
        "installments": {
            "quantity": 12,
            "amount": 458.25,
        }
    }


@pytest.fixture
def sample_shopee_product():
    """Produto de exemplo da Shopee."""
    return {
        "itemid": 123456789,
        "shopid": 987654321,
        "name": "Capa iPhone 15 Silicone Premium",
        "price": 4990000000,  # Shopee usa valor * 100000
        "price_before_discount": 7990000000,
        "image": "abc123def456",
        "images": ["abc123def456", "ghi789jkl012"],
        "item_rating": {
            "rating_star": 4.9,
            "rating_count": [0, 1, 5, 20, 150],  # 1-5 estrelas
        },
        "sold": 5000,
        "stock": 200,
        "show_free_shipping": True,
        "is_official_shop": False,
        "shop_name": "Capas Premium BR",
    }


@pytest.fixture
def ml_client():
    """Cliente ML para testes."""
    return MercadoLivreClient(site_id="MLB")


@pytest.fixture
def shopee_client():
    """Cliente Shopee para testes."""
    return ShopeeClient()


@pytest.fixture
def manager():
    """Manager para testes."""
    return MarketplaceManager()


# === Testes MercadoLivreClient ===

class TestMercadoLivreClient:
    """Testes para cliente do Mercado Livre."""
    
    def test_normalize_product(self, ml_client, sample_ml_product):
        """Testa normalização de produto ML."""
        product = ml_client._normalize_product(sample_ml_product)
        
        assert product.id == "MLB123456789"
        assert product.marketplace == MarketplaceType.MERCADO_LIVRE
        assert product.title == "iPhone 15 128GB Preto"
        assert product.price == Decimal("5499.00")
        assert product.original_price == Decimal("6999.00")
        assert product.condition == ProductCondition.NEW
        assert product.free_shipping is True
        assert product.is_official_store is True
        assert product.seller_name == "APPLE_OFICIAL"
        assert product.sales_count == 1500
        assert product.rating == 4.8
        assert product.reviews_count == 250
        assert product.installments == 12
        assert product.installment_value == Decimal("458.25")
        assert product.attributes["Marca"] == "Apple"
    
    def test_normalize_product_minimal(self, ml_client):
        """Testa normalização com dados mínimos."""
        minimal = {
            "id": "MLB1",
            "title": "Produto Teste",
            "price": 100,
            "permalink": "https://ml.com/p/MLB1",
        }
        
        product = ml_client._normalize_product(minimal)
        
        assert product.id == "MLB1"
        assert product.price == Decimal("100")
        assert product.free_shipping is False
        assert product.original_price is None
    
    def test_discount_calculation(self, ml_client, sample_ml_product):
        """Testa cálculo de desconto."""
        product = ml_client._normalize_product(sample_ml_product)
        
        # (6999 - 5499) / 6999 = 21.43%
        assert product.discount_percentage is not None
        assert 21 < product.discount_percentage < 22
    
    @pytest.mark.asyncio
    async def test_search_builds_correct_params(self, ml_client):
        """Testa que search monta parâmetros corretos."""
        with patch.object(ml_client, '_get_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.get.return_value = MagicMock(
                json=lambda: {"results": [], "paging": {"total": 0}}
            )
            mock_get.return_value = mock_client
            
            await ml_client.search(
                "celular",
                page=2,
                per_page=30,
                price_min=1000,
                price_max=5000,
                condition="new",
            )
            
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            
            assert call_args[0][0] == "/sites/MLB/search"
            params = call_args[1]["params"]
            assert params["q"] == "celular"
            assert params["offset"] == 30  # (page-1) * per_page
            assert params["limit"] == 30
            assert params["price_min"] == 1000
            assert params["price_max"] == 5000
            assert params["condition"] == "new"


# === Testes ShopeeClient ===

class TestShopeeClient:
    """Testes para cliente da Shopee."""
    
    def test_normalize_product(self, shopee_client, sample_shopee_product):
        """Testa normalização de produto Shopee."""
        product = shopee_client._normalize_product(sample_shopee_product)
        
        assert product.id == "987654321.123456789"
        assert product.marketplace == MarketplaceType.SHOPEE
        assert product.title == "Capa iPhone 15 Silicone Premium"
        
        # Preço: 4990000000 / 100000 = 49900
        assert product.price == Decimal("49900")
        
        assert product.free_shipping is True
        assert product.is_official_store is False
        assert product.seller_name == "Capas Premium BR"
        assert product.sales_count == 5000
        assert product.rating == 4.9
        
        # Total de reviews: 0+1+5+20+150 = 176
        assert product.reviews_count == 176
    
    def test_normalize_product_image_url(self, shopee_client, sample_shopee_product):
        """Testa que URLs de imagem são montadas corretamente."""
        product = shopee_client._normalize_product(sample_shopee_product)
        
        assert product.thumbnail is not None
        assert "cf.shopee.com.br/file/" in product.thumbnail
    
    def test_price_conversion(self, shopee_client):
        """Testa conversão de preço da Shopee."""
        data = {
            "itemid": 1,
            "shopid": 1,
            "name": "Teste",
            "price": 2990000000,  # R$ 29.900,00 no formato Shopee
        }
        
        product = shopee_client._normalize_product(data)
        
        # 2990000000 / 100000 = 29900
        assert product.price == Decimal("29900")
    
    def test_hmac_signature(self, shopee_client):
        """Testa geração de assinatura."""
        shopee_client.partner_id = 123456
        shopee_client.partner_key = "test_key"
        
        sign = shopee_client._generate_sign("/api/v2/shop/get_shop_info", 1699999999)
        
        assert sign is not None
        assert len(sign) == 64  # SHA256 hex


# === Testes MarketplaceManager ===

class TestMarketplaceManager:
    """Testes para o gerenciador de marketplaces."""
    
    def test_configure_mercado_livre(self, manager):
        """Testa configuração do ML."""
        manager.configure_mercado_livre(
            client_id="test_id",
            client_secret="test_secret",
        )
        
        assert MarketplaceType.MERCADO_LIVRE in manager.clients
        client = manager.clients[MarketplaceType.MERCADO_LIVRE]
        assert client.client_id == "test_id"
    
    def test_configure_shopee(self, manager):
        """Testa configuração da Shopee."""
        manager.configure_shopee(
            partner_id=123,
            partner_key="key",
        )
        
        assert MarketplaceType.SHOPEE in manager.clients
    
    def test_available_marketplaces(self, manager):
        """Testa lista de marketplaces disponíveis."""
        available = manager.available_marketplaces
        
        # ML e Shopee são sempre disponíveis (APIs públicas)
        assert MarketplaceType.MERCADO_LIVRE in available
        assert MarketplaceType.SHOPEE in available
        
        # Amazon não está disponível sem configuração
        assert MarketplaceType.AMAZON not in available
    
    def test_get_client_lazy_loading(self, manager):
        """Testa que clientes são criados sob demanda."""
        # Não há clientes inicialmente
        assert len(manager.clients) == 0
        
        # Solicitar cliente ML
        client = manager.get_client(MarketplaceType.MERCADO_LIVRE)
        
        assert client is not None
        assert MarketplaceType.MERCADO_LIVRE in manager.clients
    
    @pytest.mark.asyncio
    async def test_search_all_parallel(self, manager):
        """Testa que busca é feita em paralelo."""
        # Mock dos clientes
        ml_mock = AsyncMock()
        ml_mock.search.return_value = SearchResult(
            query="teste",
            marketplace=MarketplaceType.MERCADO_LIVRE,
            total_results=1,
            products=[
                Product(
                    id="ML1",
                    marketplace=MarketplaceType.MERCADO_LIVRE,
                    external_url="https://ml.com/p/1",
                    title="Produto ML",
                    price=Decimal("100"),
                )
            ],
            page=1,
            per_page=10,
        )
        
        shopee_mock = AsyncMock()
        shopee_mock.search.return_value = SearchResult(
            query="teste",
            marketplace=MarketplaceType.SHOPEE,
            total_results=1,
            products=[
                Product(
                    id="S1",
                    marketplace=MarketplaceType.SHOPEE,
                    external_url="https://shopee.com/p/1",
                    title="Produto Shopee",
                    price=Decimal("90"),
                )
            ],
            page=1,
            per_page=10,
        )
        
        manager.clients = {
            MarketplaceType.MERCADO_LIVRE: ml_mock,
            MarketplaceType.SHOPEE: shopee_mock,
        }
        
        result = await manager.search_all("teste")
        
        assert result.total_products == 2
        assert len(result.by_marketplace) == 2
        assert "mercado_livre" in result.by_marketplace
        assert "shopee" in result.by_marketplace
        
        # Best price deve ser Shopee (90 < 100)
        assert result.best_price is not None
        assert result.best_price.price == Decimal("90")
    
    @pytest.mark.asyncio
    async def test_search_all_handles_errors(self, manager):
        """Testa que erros são capturados sem quebrar a busca."""
        ml_mock = AsyncMock()
        ml_mock.search.side_effect = Exception("Erro de conexão")
        
        shopee_mock = AsyncMock()
        shopee_mock.search.return_value = SearchResult(
            query="teste",
            marketplace=MarketplaceType.SHOPEE,
            total_results=1,
            products=[
                Product(
                    id="S1",
                    marketplace=MarketplaceType.SHOPEE,
                    external_url="https://shopee.com/p/1",
                    title="Produto",
                    price=Decimal("100"),
                )
            ],
            page=1,
            per_page=10,
        )
        
        manager.clients = {
            MarketplaceType.MERCADO_LIVRE: ml_mock,
            MarketplaceType.SHOPEE: shopee_mock,
        }
        
        result = await manager.search_all("teste")
        
        # Deve ter erro do ML
        assert "mercado_livre" in result.errors
        assert "Erro de conexão" in result.errors["mercado_livre"]
        
        # Shopee deve ter funcionado
        assert len(result.by_marketplace["shopee"]) == 1


# === Testes de Integração (marcados como skip por padrão) ===

@pytest.mark.skip(reason="Requer conexão com APIs reais")
class TestIntegration:
    """Testes de integração com APIs reais."""
    
    @pytest.mark.asyncio
    async def test_ml_real_search(self):
        """Testa busca real no ML."""
        client = MercadoLivreClient()
        
        result = await client.search("iphone", per_page=5)
        
        assert result.total_results > 0
        assert len(result.products) <= 5
        
        for product in result.products:
            assert product.id.startswith("MLB")
            assert product.price > 0
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_shopee_real_search(self):
        """Testa busca real na Shopee."""
        client = ShopeeClient()
        
        result = await client.search("fone bluetooth", per_page=5)
        
        # Shopee pode bloquear, então apenas verificamos a estrutura
        assert result.query == "fone bluetooth"
        
        await client.close()
