"""
Marketplace Integrations Module
================================
Integra múltiplos e-commerces usando SDKs oficiais e APIs disponíveis.

SDKs Utilizados:
- Mercado Livre: SDK Oficial (mercadolibre/python-sdk)
- Amazon: python-amazon-paapi (Product Advertising API 5.0)
- Shopee: pyshopee (Shopee Partner API)
- AliExpress: Scraper próprio (já existente)
- TikTok Shop: Scraper próprio (já existente)

Instalação dos SDKs:
    pip install meli python-amazon-paapi pyshopee

Uso:
    from backend.integrations.marketplaces import MarketplaceManager

    manager = MarketplaceManager()
    products = await manager.search_all("celular samsung")
"""

from .base import MarketplaceBase, MarketplaceType, Product, SearchResult
from .mercadolivre import MercadoLivreClient
from .amazon import AmazonClient
from .shopee import ShopeeClient
from .manager import (
    MarketplaceManager,
    get_marketplace_manager,
    search_all_marketplaces,
)

__all__ = [
    "MarketplaceBase",
    "MarketplaceType",
    "Product",
    "SearchResult",
    "MercadoLivreClient",
    "AmazonClient",
    "ShopeeClient",
    "MarketplaceManager",
    "get_marketplace_manager",
    "search_all_marketplaces",
]
