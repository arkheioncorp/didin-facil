"""
MarketplaceManager - Gerenciador unificado de marketplaces.

Permite buscar produtos em múltiplos marketplaces simultaneamente
e consolidar resultados para comparação de preços.
"""

import asyncio
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from .base import MarketplaceBase, MarketplaceType, Product, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class ComparisonResult:
    """Resultado de comparação entre marketplaces."""
    query: str
    total_products: int
    best_price: Optional[Product] = None
    best_rating: Optional[Product] = None
    best_value: Optional[Product] = None  # Melhor custo-benefício
    by_marketplace: dict[str, list[Product]] = None
    search_time_ms: float = 0
    errors: dict[str, str] = None
    
    def __post_init__(self):
        if self.by_marketplace is None:
            self.by_marketplace = {}
        if self.errors is None:
            self.errors = {}


class MarketplaceManager:
    """
    Gerencia múltiplos clientes de marketplace.
    
    Permite:
    - Buscar em todos os marketplaces simultaneamente
    - Comparar preços entre marketplaces
    - Encontrar melhores ofertas
    
    Exemplo:
        manager = MarketplaceManager()
        
        # Configurar credenciais (opcional)
        manager.configure_mercado_livre(client_id="...", client_secret="...")
        manager.configure_amazon(access_key="...", secret_key="...", partner_tag="...")
        
        # Buscar em todos
        comparison = await manager.search_all("iphone 15")
        
        print(f"Menor preço: {comparison.best_price.title} - R${comparison.best_price.price}")
    """
    
    def __init__(self):
        self.clients: dict[MarketplaceType, MarketplaceBase] = {}
        self._configs: dict[MarketplaceType, dict] = {}
    
    def configure_mercado_livre(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        site_id: str = "MLB",
    ):
        """Configura cliente do Mercado Livre."""
        from .mercadolivre import MercadoLivreClient
        
        self.clients[MarketplaceType.MERCADO_LIVRE] = MercadoLivreClient(
            client_id=client_id,
            client_secret=client_secret,
            site_id=site_id,
        )
        self._configs[MarketplaceType.MERCADO_LIVRE] = {
            "client_id": client_id,
            "site_id": site_id,
        }
    
    def configure_amazon(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        partner_tag: Optional[str] = None,
        country: str = "BR",
    ):
        """Configura cliente da Amazon."""
        from .amazon import AmazonClient
        
        self.clients[MarketplaceType.AMAZON] = AmazonClient(
            access_key=access_key,
            secret_key=secret_key,
            partner_tag=partner_tag,
            country=country,
        )
        self._configs[MarketplaceType.AMAZON] = {
            "partner_tag": partner_tag,
            "country": country,
        }
    
    def configure_shopee(
        self,
        partner_id: Optional[int] = None,
        partner_key: Optional[str] = None,
        shop_id: Optional[int] = None,
        access_token: Optional[str] = None,
    ):
        """Configura cliente da Shopee."""
        from .shopee import ShopeeClient
        
        self.clients[MarketplaceType.SHOPEE] = ShopeeClient(
            partner_id=partner_id,
            partner_key=partner_key,
            shop_id=shop_id,
            access_token=access_token,
        )
        self._configs[MarketplaceType.SHOPEE] = {
            "partner_id": partner_id,
            "shop_id": shop_id,
        }
    
    def get_client(self, marketplace: MarketplaceType) -> Optional[MarketplaceBase]:
        """Retorna cliente de um marketplace específico."""
        # Lazy loading de clientes não configurados
        if marketplace not in self.clients:
            self._create_default_client(marketplace)
        
        return self.clients.get(marketplace)
    
    def _create_default_client(self, marketplace: MarketplaceType):
        """Cria cliente com configuração padrão."""
        if marketplace == MarketplaceType.MERCADO_LIVRE:
            from .mercadolivre import MercadoLivreClient
            self.clients[marketplace] = MercadoLivreClient()
        
        elif marketplace == MarketplaceType.SHOPEE:
            from .shopee import ShopeeClient
            self.clients[marketplace] = ShopeeClient()
        
        elif marketplace == MarketplaceType.AMAZON:
            # Amazon requer credenciais, não criamos por padrão
            pass
    
    @property
    def available_marketplaces(self) -> list[MarketplaceType]:
        """Lista marketplaces com clientes disponíveis."""
        available = []
        
        # Sempre disponíveis (APIs públicas)
        available.append(MarketplaceType.MERCADO_LIVRE)
        available.append(MarketplaceType.SHOPEE)
        
        # Requer credenciais
        if MarketplaceType.AMAZON in self.clients:
            available.append(MarketplaceType.AMAZON)
        
        return available
    
    async def search(
        self,
        marketplace: MarketplaceType,
        query: str,
        **kwargs
    ) -> SearchResult:
        """
        Busca em um marketplace específico.
        
        Args:
            marketplace: Tipo do marketplace
            query: Termo de busca
            **kwargs: Parâmetros adicionais
            
        Returns:
            SearchResult
        """
        client = self.get_client(marketplace)
        if not client:
            raise ValueError(f"Marketplace {marketplace} não configurado")
        
        return await client.search(query, **kwargs)
    
    async def search_all(
        self,
        query: str,
        marketplaces: Optional[list[MarketplaceType]] = None,
        per_page: int = 20,
        timeout: float = 30.0,
        **kwargs
    ) -> ComparisonResult:
        """
        Busca em múltiplos marketplaces simultaneamente.
        
        Args:
            query: Termo de busca
            marketplaces: Lista de marketplaces (None = todos disponíveis)
            per_page: Itens por página por marketplace
            timeout: Timeout para cada busca
            **kwargs: Parâmetros adicionais
            
        Returns:
            ComparisonResult com produtos agregados
        """
        import time
        start_time = time.time()
        
        if marketplaces is None:
            marketplaces = self.available_marketplaces
        
        # Criar tasks para busca paralela
        tasks = []
        marketplace_list = []
        
        for mp in marketplaces:
            client = self.get_client(mp)
            if client:
                task = asyncio.create_task(
                    asyncio.wait_for(
                        client.search(query, per_page=per_page, **kwargs),
                        timeout=timeout
                    )
                )
                tasks.append(task)
                marketplace_list.append(mp)
        
        # Executar buscas em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        all_products: list[Product] = []
        by_marketplace: dict[str, list[Product]] = {}
        errors: dict[str, str] = {}
        
        for mp, result in zip(marketplace_list, results):
            mp_name = mp.value
            
            if isinstance(result, Exception):
                errors[mp_name] = str(result)
                logger.warning(f"Erro ao buscar em {mp_name}: {result}")
                by_marketplace[mp_name] = []
            else:
                products = result.products
                all_products.extend(products)
                by_marketplace[mp_name] = products
        
        # Encontrar melhores
        best_price = None
        best_rating = None
        best_value = None
        
        if all_products:
            # Menor preço
            products_with_price = [p for p in all_products if p.price > 0]
            if products_with_price:
                best_price = min(products_with_price, key=lambda p: p.price)
            
            # Melhor rating
            products_with_rating = [p for p in all_products if p.rating is not None]
            if products_with_rating:
                best_rating = max(products_with_rating, key=lambda p: p.rating)
            
            # Melhor custo-benefício (rating / preço normalizado)
            products_for_value = [
                p for p in all_products 
                if p.price > 0 and p.rating is not None and p.rating > 0
            ]
            if products_for_value:
                # Score = (rating * 20) / (preço / 100)
                # Normaliza para dar peso igual
                def value_score(p: Product) -> float:
                    normalized_rating = p.rating * 20  # 0-100
                    normalized_price = float(p.price) / 100  # escala menor
                    return normalized_rating / max(normalized_price, 1)
                
                best_value = max(products_for_value, key=value_score)
        
        search_time = (time.time() - start_time) * 1000
        
        return ComparisonResult(
            query=query,
            total_products=len(all_products),
            best_price=best_price,
            best_rating=best_rating,
            best_value=best_value,
            by_marketplace=by_marketplace,
            search_time_ms=search_time,
            errors=errors,
        )
    
    async def compare_product(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        """
        Compara produtos similares entre marketplaces.
        
        Retorna lista ordenada por preço.
        
        Args:
            query: Termo de busca específico (nome do produto)
            limit: Limite por marketplace
            
        Returns:
            Lista de dicts com comparação
        """
        comparison = await self.search_all(query, per_page=limit)
        
        # Flatten e ordenar
        all_products = []
        for mp_products in comparison.by_marketplace.values():
            all_products.extend(mp_products)
        
        # Ordenar por preço
        all_products.sort(key=lambda p: p.price if p.price > 0 else Decimal("999999"))
        
        # Converter para dict de comparação
        return [p.to_comparison_dict() for p in all_products[:limit * 3]]
    
    async def find_best_deal(
        self,
        query: str,
        min_rating: float = 4.0,
        max_price: Optional[float] = None,
    ) -> Optional[Product]:
        """
        Encontra a melhor oferta considerando preço e rating.
        
        Args:
            query: Termo de busca
            min_rating: Rating mínimo aceitável
            max_price: Preço máximo (opcional)
            
        Returns:
            Melhor produto encontrado ou None
        """
        comparison = await self.search_all(query, per_page=30)
        
        # Flatten
        all_products = []
        for mp_products in comparison.by_marketplace.values():
            all_products.extend(mp_products)
        
        # Filtrar
        filtered = [
            p for p in all_products
            if p.rating is not None 
            and p.rating >= min_rating
            and p.price > 0
            and (max_price is None or float(p.price) <= max_price)
        ]
        
        if not filtered:
            return None
        
        # Score: (rating * 20) + (desconto * 0.5) - (preço / 50)
        def score(p: Product) -> float:
            rating_score = (p.rating or 0) * 20
            discount_score = (p.discount_percentage or 0) * 0.5
            price_penalty = float(p.price) / 50
            free_shipping_bonus = 10 if p.free_shipping else 0
            
            return rating_score + discount_score - price_penalty + free_shipping_bonus
        
        return max(filtered, key=score)
    
    async def close(self):
        """Fecha todos os clientes."""
        for client in self.clients.values():
            if hasattr(client, 'close'):
                await client.close()


# Instância global para uso simples
_manager: Optional[MarketplaceManager] = None


def get_marketplace_manager() -> MarketplaceManager:
    """Retorna instância global do manager."""
    global _manager
    if _manager is None:
        _manager = MarketplaceManager()
    return _manager


async def search_all_marketplaces(query: str, **kwargs) -> ComparisonResult:
    """
    Helper para busca rápida em todos os marketplaces.
    
    Exemplo:
        from backend.integrations.marketplaces import search_all_marketplaces
        
        results = await search_all_marketplaces("iphone 15")
        print(f"Menor preço: R${results.best_price.price}")
    """
    manager = get_marketplace_manager()
    return await manager.search_all(query, **kwargs)
