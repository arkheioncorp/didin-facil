"""
Integração com Mercado Livre usando SDK oficial.

SDK: mercadolibre/python-sdk
Docs: https://developers.mercadolibre.com/

Instalação:
    pip install meli

Autenticação:
    1. Criar aplicação em developers.mercadolibre.com
    2. Obter client_id e client_secret
    3. Usar OAuth 2.0 para access_token

Endpoints principais:
    - /sites/{site_id}/search - Busca de produtos
    - /items/{item_id} - Detalhes do item
    - /categories/{category_id} - Categorias
    - /users/{user_id} - Informações do vendedor
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


# Mapeamento de condição ML -> ProductCondition
CONDITION_MAP = {
    "new": ProductCondition.NEW,
    "used": ProductCondition.USED,
    "refurbished": ProductCondition.REFURBISHED,
}


class MercadoLivreClient(MarketplaceBase):
    """
    Cliente para API do Mercado Livre.
    
    Usa a API REST oficial do Mercado Livre.
    Para operações que requerem autenticação, use OAuth 2.0.
    
    Exemplo:
        client = MercadoLivreClient(
            client_id="your_client_id",
            client_secret="your_client_secret"
        )
        
        # Busca pública (sem auth)
        results = await client.search("celular samsung")
        
        # Com autenticação (para mais rate limit)
        await client.authenticate()
        results = await client.search("celular samsung")
    """
    
    marketplace_type = MarketplaceType.MERCADO_LIVRE
    
    # URLs da API
    BASE_URL = "https://api.mercadolibre.com"
    AUTH_URL = "https://api.mercadolibre.com/oauth/token"
    
    # Sites por país
    SITES = {
        "brasil": "MLB",
        "argentina": "MLA",
        "mexico": "MLM",
        "chile": "MLC",
        "colombia": "MCO",
    }
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        site_id: str = "MLB",  # Brasil por padrão
        access_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        super().__init__(api_key=client_id)
        self.client_id = client_id
        self.client_secret = client_secret
        self.site_id = site_id
        self.access_token = access_token
        self.timeout = timeout
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Retorna cliente HTTP (lazy initialization)."""
        if self._http_client is None or self._http_client.is_closed:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
            
            self._http_client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers=headers,
                timeout=self.timeout,
            )
        return self._http_client
    
    async def close(self):
        """Fecha cliente HTTP."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
    
    async def authenticate(self) -> bool:
        """
        Autentica usando OAuth 2.0 Client Credentials.
        
        Requer client_id e client_secret configurados.
        """
        if not self.client_id or not self.client_secret:
            logger.warning("ML: client_id/client_secret não configurados")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.AUTH_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                self.access_token = data.get("access_token")
                self._is_authenticated = True
                
                logger.info("ML: Autenticado com sucesso")
                return True
                
        except Exception as e:
            logger.error(f"ML: Erro na autenticação: {e}")
            return False
    
    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        category: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        condition: Optional[str] = None,
        sort: str = "relevance",
        **filters
    ) -> SearchResult:
        """
        Busca produtos no Mercado Livre.
        
        Args:
            query: Termo de busca
            page: Página (1-indexed)
            per_page: Itens por página (max 50)
            category: ID da categoria
            price_min: Preço mínimo
            price_max: Preço máximo
            condition: "new", "used", "refurbished"
            sort: "relevance", "price_asc", "price_desc"
            
        Returns:
            SearchResult com produtos encontrados
        """
        import time
        start_time = time.time()
        
        client = await self._get_client()
        
        # Montar parâmetros
        params = {
            "q": query,
            "offset": (page - 1) * per_page,
            "limit": min(per_page, 50),
        }
        
        if category:
            params["category"] = category
        if price_min:
            params["price_min"] = price_min
        if price_max:
            params["price_max"] = price_max
        if condition:
            params["condition"] = condition
            
        # Ordenação
        sort_map = {
            "relevance": "relevance",
            "price_asc": "price_asc",
            "price_desc": "price_desc",
        }
        params["sort"] = sort_map.get(sort, "relevance")
        
        try:
            response = await client.get(
                f"/sites/{self.site_id}/search",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Processar produtos
            products = []
            for item in data.get("results", []):
                try:
                    product = self._normalize_product(item)
                    products.append(product)
                except Exception as e:
                    logger.warning(f"ML: Erro ao normalizar produto: {e}")
            
            search_time = (time.time() - start_time) * 1000
            
            return SearchResult(
                query=query,
                marketplace=self.marketplace_type,
                total_results=data.get("paging", {}).get("total", 0),
                page=page,
                per_page=per_page,
                products=products,
                search_time_ms=search_time,
                filters_applied=filters,
            )
            
        except Exception as e:
            logger.error(f"ML: Erro na busca: {e}")
            raise
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """
        Obtém detalhes completos de um produto.
        
        Args:
            product_id: ID do item (ex: MLB123456789)
            
        Returns:
            Product com todos os detalhes
        """
        client = await self._get_client()
        
        try:
            # Buscar item
            response = await client.get(f"/items/{product_id}")
            response.raise_for_status()
            item = response.json()
            
            # Buscar descrição
            try:
                desc_response = await client.get(f"/items/{product_id}/description")
                if desc_response.status_code == 200:
                    desc_data = desc_response.json()
                    item["description"] = desc_data.get("plain_text", "")
            except:
                pass
            
            return self._normalize_product(item)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            logger.error(f"ML: Erro ao buscar produto {product_id}: {e}")
            raise
    
    async def get_categories(self, parent_id: Optional[str] = None) -> list[dict]:
        """
        Lista categorias do site.
        
        Args:
            parent_id: ID da categoria pai (None = raiz)
            
        Returns:
            Lista de categorias com id, name, children_count
        """
        client = await self._get_client()
        
        try:
            if parent_id:
                response = await client.get(f"/categories/{parent_id}")
            else:
                response = await client.get(f"/sites/{self.site_id}/categories")
            
            response.raise_for_status()
            data = response.json()
            
            if parent_id:
                # Retorna subcategorias
                return data.get("children_categories", [])
            else:
                # Retorna categorias raiz
                return data
                
        except Exception as e:
            logger.error(f"ML: Erro ao buscar categorias: {e}")
            return []
    
    async def get_seller(self, seller_id: str) -> Optional[dict]:
        """
        Obtém informações do vendedor.
        
        Args:
            seller_id: ID do vendedor
            
        Returns:
            Dict com informações do vendedor
        """
        client = await self._get_client()
        
        try:
            response = await client.get(f"/users/{seller_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ML: Erro ao buscar vendedor {seller_id}: {e}")
            return None
    
    def _normalize_product(self, raw: dict) -> Product:
        """Normaliza dados do ML para Product."""
        
        # Preço
        price = Decimal(str(raw.get("price", 0)))
        original_price = None
        discount = None
        
        if "original_price" in raw and raw["original_price"]:
            original_price = Decimal(str(raw["original_price"]))
            if original_price > price:
                discount = float(((original_price - price) / original_price) * 100)
        
        # Parcelamento
        installments = None
        installment_value = None
        if raw.get("installments"):
            inst = raw["installments"]
            installments = inst.get("quantity")
            if inst.get("amount"):
                installment_value = Decimal(str(inst["amount"]))
        
        # Envio
        shipping = raw.get("shipping", {})
        free_shipping = shipping.get("free_shipping", False)
        
        # Imagens
        thumbnail = raw.get("thumbnail")
        images = [
            pic.get("secure_url") or pic.get("url")
            for pic in raw.get("pictures", [])
        ]
        
        # Vendedor
        seller = raw.get("seller", {})
        seller_rep = seller.get("seller_reputation", {})
        
        # Atributos
        attributes = {}
        for attr in raw.get("attributes", []):
            if attr.get("name") and attr.get("value_name"):
                attributes[attr["name"]] = attr["value_name"]
        
        # Condição
        condition = CONDITION_MAP.get(
            raw.get("condition", "new"),
            ProductCondition.NEW
        )
        
        return Product(
            id=raw.get("id", ""),
            marketplace=self.marketplace_type,
            external_url=raw.get("permalink", f"https://www.mercadolivre.com.br/p/{raw.get('id', '')}"),
            title=raw.get("title", ""),
            description=raw.get("description"),
            brand=attributes.get("Marca"),
            category=raw.get("category_id"),
            condition=condition,
            price=price,
            original_price=original_price,
            currency=raw.get("currency_id", "BRL"),
            discount_percentage=discount,
            installments=installments,
            installment_value=installment_value,
            thumbnail=thumbnail,
            images=images,
            free_shipping=free_shipping,
            seller_id=str(seller.get("id", "")),
            seller_name=seller.get("nickname", ""),
            seller_reputation=seller_rep.get("level_id"),
            is_official_store=raw.get("official_store_id") is not None,
            rating=raw.get("reviews", {}).get("rating_average"),
            reviews_count=raw.get("reviews", {}).get("total"),
            sales_count=raw.get("sold_quantity"),
            available_quantity=raw.get("available_quantity"),
            attributes=attributes,
        )


# Funções utilitárias
async def search_mercado_livre(
    query: str,
    **kwargs
) -> SearchResult:
    """
    Função helper para busca rápida.
    
    Exemplo:
        results = await search_mercado_livre("iphone 15")
    """
    client = MercadoLivreClient()
    try:
        return await client.search(query, **kwargs)
    finally:
        await client.close()
