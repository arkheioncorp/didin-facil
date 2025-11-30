"""
Integração com Amazon usando Product Advertising API 5.0.

SDK: python-amazon-paapi (wrapper) ou paapi5-python-sdk (oficial)
Docs: https://webservices.amazon.com/paapi5/documentation/

Instalação:
    pip install python-amazon-paapi

Autenticação:
    1. Criar conta no Amazon Associates
    2. Obter Access Key, Secret Key e Partner Tag
    3. Usar na configuração do cliente

Funcionalidades principais:
    - SearchItems: Busca de produtos
    - GetItems: Detalhes por ASIN
    - GetVariations: Variações de produtos
    - GetBrowseNodes: Navegação por categorias

Limitações:
    - 1 request/segundo (padrão)
    - Até 10 requests/segundo com mais vendas
    - Afiliado obrigatório
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

import httpx

from .base import (
    MarketplaceBase,
    MarketplaceType,
    Product,
    ProductCondition,
    SearchResult,
)

logger = logging.getLogger(__name__)


class AmazonClient(MarketplaceBase):
    """
    Cliente para Amazon Product Advertising API 5.0.
    
    Usa o wrapper python-amazon-paapi para facilitar autenticação
    e serialização de requests.
    
    Requisitos:
        - Conta Amazon Associates ativa
        - Access Key, Secret Key e Partner Tag
        
    Exemplo:
        client = AmazonClient(
            access_key="YOUR_ACCESS_KEY",
            secret_key="YOUR_SECRET_KEY",
            partner_tag="YOUR-TAG-20",
            country="BR"
        )
        
        results = await client.search("kindle paperwhite")
    """
    
    marketplace_type = MarketplaceType.AMAZON
    
    # Endpoints por região
    HOSTS = {
        "BR": "webservices.amazon.com.br",
        "US": "webservices.amazon.com",
        "MX": "webservices.amazon.com.mx",
        "ES": "webservices.amazon.es",
        "UK": "webservices.amazon.co.uk",
        "DE": "webservices.amazon.de",
        "FR": "webservices.amazon.fr",
        "IT": "webservices.amazon.it",
        "JP": "webservices.amazon.co.jp",
    }
    
    REGIONS = {
        "BR": "us-east-1",  # Brasil usa região US
        "US": "us-east-1",
        "MX": "us-east-1",
        "ES": "eu-west-1",
        "UK": "eu-west-1",
        "DE": "eu-west-1",
        "FR": "eu-west-1",
        "IT": "eu-west-1",
        "JP": "us-west-2",
    }
    
    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        partner_tag: Optional[str] = None,
        country: str = "BR",
        timeout: float = 30.0,
    ):
        super().__init__(api_key=access_key)
        self.access_key = access_key
        self.secret_key = secret_key
        self.partner_tag = partner_tag
        self.country = country.upper()
        self.timeout = timeout
        self._amazon_api = None
    
    def _get_amazon_api(self):
        """
        Retorna instância do python-amazon-paapi.
        
        Lazy loading para evitar import error se não instalado.
        """
        if self._amazon_api is None:
            try:
                from amazon_paapi import AmazonApi
                
                self._amazon_api = AmazonApi(
                    self.access_key,
                    self.secret_key,
                    self.partner_tag,
                    self.country,
                    throttling=1.0,  # 1 request/segundo
                )
            except ImportError:
                logger.error(
                    "python-amazon-paapi não instalado. "
                    "Instale com: pip install python-amazon-paapi"
                )
                raise
                
        return self._amazon_api
    
    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 10,
        category: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        sort: str = "Relevance",
        **filters
    ) -> SearchResult:
        """
        Busca produtos na Amazon.
        
        Args:
            query: Termo de busca
            page: Página (1-indexed, max 10)
            per_page: Itens por página (max 10)
            category: SearchIndex (ex: "Electronics", "Books")
            price_min: Preço mínimo em centavos
            price_max: Preço máximo em centavos
            sort: "Relevance", "Price:LowToHigh", "Price:HighToLow", "AvgCustomerReviews"
            
        Returns:
            SearchResult com produtos encontrados
        """
        import time
        start_time = time.time()
        
        # A API é síncrona, rodar em executor
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                None,
                self._search_sync,
                query, page, per_page, category, price_min, price_max, sort
            )
            
            search_time = (time.time() - start_time) * 1000
            
            products = []
            total = 0
            
            if result:
                for item in result:
                    try:
                        product = self._normalize_product(item)
                        products.append(product)
                    except Exception as e:
                        logger.warning(f"Amazon: Erro ao normalizar produto: {e}")
                
                # PAAPI não retorna total exato
                total = len(products) * 10  # Estimativa
            
            return SearchResult(
                query=query,
                marketplace=self.marketplace_type,
                total_results=total,
                page=page,
                per_page=per_page,
                products=products,
                search_time_ms=search_time,
                filters_applied=filters,
            )
            
        except Exception as e:
            logger.error(f"Amazon: Erro na busca: {e}")
            raise
    
    def _search_sync(
        self,
        query: str,
        page: int,
        per_page: int,
        category: Optional[str],
        price_min: Optional[float],
        price_max: Optional[float],
        sort: str,
    ):
        """Busca síncrona (chamada em executor)."""
        api = self._get_amazon_api()
        
        kwargs = {
            "keywords": query,
            "item_count": min(per_page, 10),
            "item_page": min(page, 10),
        }
        
        if category:
            kwargs["search_index"] = category
        
        if price_min:
            kwargs["min_price"] = int(price_min * 100)  # centavos
        if price_max:
            kwargs["max_price"] = int(price_max * 100)
            
        if sort != "Relevance":
            kwargs["sort_by"] = sort
        
        return api.search_items(**kwargs)
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """
        Obtém detalhes de um produto por ASIN.
        
        Args:
            product_id: ASIN do produto
            
        Returns:
            Product ou None
        """
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                None,
                self._get_product_sync,
                product_id
            )
            
            if result and len(result) > 0:
                return self._normalize_product(result[0])
            return None
            
        except Exception as e:
            logger.error(f"Amazon: Erro ao buscar produto {product_id}: {e}")
            return None
    
    def _get_product_sync(self, asin: str):
        """Get product síncrono (chamado em executor)."""
        api = self._get_amazon_api()
        return api.get_items([asin])
    
    async def get_variations(self, asin: str) -> list[Product]:
        """
        Obtém variações de um produto (cores, tamanhos, etc).
        
        Args:
            asin: ASIN do produto pai
            
        Returns:
            Lista de Products com variações
        """
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                None,
                self._get_variations_sync,
                asin
            )
            
            products = []
            if result and result.items:
                for item in result.items:
                    try:
                        product = self._normalize_product(item)
                        products.append(product)
                    except:
                        pass
            return products
            
        except Exception as e:
            logger.error(f"Amazon: Erro ao buscar variações de {asin}: {e}")
            return []
    
    def _get_variations_sync(self, asin: str):
        """Get variations síncrono."""
        api = self._get_amazon_api()
        return api.get_variations(asin)
    
    def _normalize_product(self, item) -> Product:
        """
        Normaliza produto da PAAPI para nosso modelo.
        
        O objeto item é um AmazonProduct do python-amazon-paapi.
        """
        # Acessar atributos do objeto
        asin = getattr(item, 'asin', '') or ''
        title = getattr(item, 'title', '') or ''
        url = getattr(item, 'url', '') or f'https://www.amazon.com.br/dp/{asin}'
        
        # Preços
        price = Decimal("0")
        original_price = None
        discount = None
        
        if hasattr(item, 'price') and item.price:
            price_str = str(item.price).replace('R$', '').replace(',', '.').strip()
            try:
                price = Decimal(price_str)
            except:
                pass
        
        if hasattr(item, 'price_savings') and item.price_savings:
            savings_str = str(item.price_savings).replace('R$', '').replace(',', '.').strip()
            try:
                savings = Decimal(savings_str)
                original_price = price + savings
                if original_price > 0:
                    discount = float((savings / original_price) * 100)
            except:
                pass
        
        # Imagens
        images = []
        thumbnail = None
        
        if hasattr(item, 'images') and item.images:
            if hasattr(item.images, 'primary') and item.images.primary:
                if hasattr(item.images.primary, 'large'):
                    thumbnail = item.images.primary.large
                elif hasattr(item.images.primary, 'medium'):
                    thumbnail = item.images.primary.medium
            
            if hasattr(item.images, 'variants') and item.images.variants:
                for variant in item.images.variants:
                    if hasattr(variant, 'large'):
                        images.append(variant.large)
        
        # Rating
        rating = None
        reviews = None
        if hasattr(item, 'customer_reviews'):
            if hasattr(item.customer_reviews, 'rating'):
                rating = float(item.customer_reviews.rating)
            if hasattr(item.customer_reviews, 'count'):
                reviews = int(item.customer_reviews.count)
        
        # Categoria
        category = None
        if hasattr(item, 'browse_node_info') and item.browse_node_info:
            nodes = getattr(item.browse_node_info, 'browse_nodes', [])
            if nodes:
                category = getattr(nodes[0], 'display_name', None)
        
        # Atributos
        attributes = {}
        if hasattr(item, 'item_info') and item.item_info:
            info = item.item_info
            
            if hasattr(info, 'by_line_info') and info.by_line_info:
                brand = getattr(info.by_line_info, 'brand', None)
                if brand:
                    attributes['brand'] = getattr(brand, 'display_value', str(brand))
            
            if hasattr(info, 'features') and info.features:
                attributes['features'] = info.features.display_values if hasattr(info.features, 'display_values') else []
        
        # Prime/Frete
        free_shipping = False
        if hasattr(item, 'offers') and item.offers:
            listings = getattr(item.offers, 'listings', [])
            if listings:
                delivery = getattr(listings[0], 'delivery_info', None)
                if delivery:
                    free_shipping = getattr(delivery, 'is_prime_eligible', False)
        
        return Product(
            id=asin,
            marketplace=self.marketplace_type,
            external_url=url,
            title=title,
            brand=attributes.get('brand'),
            category=category,
            condition=ProductCondition.NEW,
            price=price,
            original_price=original_price,
            currency="BRL",
            discount_percentage=discount,
            thumbnail=thumbnail,
            images=images,
            free_shipping=free_shipping,
            rating=rating,
            reviews_count=reviews,
            attributes=attributes,
        )


# Função helper
async def search_amazon(query: str, **kwargs) -> SearchResult:
    """
    Busca rápida na Amazon.
    
    Requer variáveis de ambiente:
        - AMAZON_ACCESS_KEY
        - AMAZON_SECRET_KEY
        - AMAZON_PARTNER_TAG
    """
    import os
    
    client = AmazonClient(
        access_key=os.getenv("AMAZON_ACCESS_KEY"),
        secret_key=os.getenv("AMAZON_SECRET_KEY"),
        partner_tag=os.getenv("AMAZON_PARTNER_TAG"),
    )
    
    return await client.search(query, **kwargs)
