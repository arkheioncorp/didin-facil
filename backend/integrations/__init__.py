"""
Backend Integrations Package.

Contém integrações com serviços externos:
- marketplaces: Mercado Livre, Amazon, Shopee
"""

from .marketplaces import (
    MarketplaceManager,
    MarketplaceType,
    Product,
    SearchResult,
    get_marketplace_manager,
    search_all_marketplaces,
)

__all__ = [
    "MarketplaceManager",
    "MarketplaceType",
    "Product",
    "SearchResult",
    "get_marketplace_manager",
    "search_all_marketplaces",
]
