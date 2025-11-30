"""
Integração com Shopee usando a Partner API.

SDK: pyshopee (JimCurryWang/python-shopee)
Docs: https://open.shopee.com/documents

Instalação:
    pip install pyshopee

Autenticação:
    1. Registrar como Shopee Partner
    2. Obter Partner ID e Secret Key
    3. Usar OAuth para obter Shop Access Token

Módulos disponíveis:
    - Shop: Informações da loja
    - Item: Produtos
    - Order: Pedidos
    - Logistics: Envio
    - Returns: Devoluções

Nota: A API pública de busca é limitada.
      Para busca de produtos, usamos scraping como fallback.
"""

import asyncio
import hashlib
import hmac
import logging
import time
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


class ShopeeClient(MarketplaceBase):
    """
    Cliente para Shopee API.
    
    Usa combinação de:
    - Partner API (para lojistas autenticados)
    - API pública (busca limitada)
    - Scraping (fallback para busca)
    
    Exemplo:
        # Para lojistas
        client = ShopeeClient(
            partner_id=123456,
            partner_key="your_key",
            shop_id=789,
            access_token="shop_token"
        )
        
        # Para busca pública
        client = ShopeeClient()
        results = await client.search("tênis nike")
    """
    
    marketplace_type = MarketplaceType.SHOPEE
    
    # Endpoints
    BASE_URL = "https://partner.shopeemobile.com"
    PUBLIC_API = "https://shopee.com.br/api/v4"
    
    def __init__(
        self,
        partner_id: Optional[int] = None,
        partner_key: Optional[str] = None,
        shop_id: Optional[int] = None,
        access_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        super().__init__(api_key=partner_key)
        self.partner_id = partner_id
        self.partner_key = partner_key
        self.shop_id = shop_id
        self.access_token = access_token
        self.timeout = timeout
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Retorna cliente HTTP."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }
            )
        return self._http_client
    
    async def close(self):
        """Fecha cliente HTTP."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
    
    def _generate_sign(self, path: str, timestamp: int) -> str:
        """
        Gera assinatura HMAC para Partner API.
        
        sign = HMAC-SHA256(partner_id + path + timestamp, partner_key)
        """
        if not self.partner_key:
            return ""
        
        base_string = f"{self.partner_id}{path}{timestamp}"
        
        if self.access_token:
            base_string += f"{self.access_token}{self.shop_id}"
        
        signature = hmac.new(
            self.partner_key.encode(),
            base_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        category: Optional[int] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        sort: str = "relevancy",
        **filters
    ) -> SearchResult:
        """
        Busca produtos na Shopee.
        
        Args:
            query: Termo de busca
            page: Página (0-indexed internamente)
            per_page: Itens por página (max 60)
            category: ID da categoria
            price_min: Preço mínimo
            price_max: Preço máximo
            sort: "relevancy", "ctime" (newest), "sales", "price"
            
        Returns:
            SearchResult com produtos
        """
        start_time = time.time()
        
        client = await self._get_client()
        
        # Usar API pública de busca
        offset = (page - 1) * per_page
        
        params = {
            "keyword": query,
            "limit": min(per_page, 60),
            "offset": offset,
            "order": "desc",
            "page_type": "search",
            "scenario": "PAGE_GLOBAL_SEARCH",
            "version": 2,
        }
        
        # Ordenação
        sort_map = {
            "relevancy": "relevancy",
            "ctime": "ctime",
            "newest": "ctime",
            "sales": "sales",
            "price": "price",
            "price_asc": "price",
        }
        params["by"] = sort_map.get(sort, "relevancy")
        
        if sort == "price_asc":
            params["order"] = "asc"
        
        # Filtros de preço
        if price_min:
            params["price_min"] = int(price_min * 100000)  # Shopee usa centavos * 1000
        if price_max:
            params["price_max"] = int(price_max * 100000)
        
        if category:
            params["match_id"] = category
        
        try:
            response = await client.get(
                f"{self.PUBLIC_API}/search/search_items",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            products = []
            items = data.get("items", []) or []
            
            for item in items:
                try:
                    item_data = item.get("item_basic", item)
                    product = self._normalize_product(item_data)
                    products.append(product)
                except Exception as e:
                    logger.warning(f"Shopee: Erro ao normalizar: {e}")
            
            search_time = (time.time() - start_time) * 1000
            
            return SearchResult(
                query=query,
                marketplace=self.marketplace_type,
                total_results=data.get("total_count", len(products)),
                page=page,
                per_page=per_page,
                products=products,
                search_time_ms=search_time,
                filters_applied=filters,
            )
            
        except Exception as e:
            logger.error(f"Shopee: Erro na busca: {e}")
            # Fallback para resultado vazio em vez de falhar
            return SearchResult(
                query=query,
                marketplace=self.marketplace_type,
                total_results=0,
                page=page,
                per_page=per_page,
                products=[],
                search_time_ms=(time.time() - start_time) * 1000,
            )
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """
        Obtém detalhes de um produto.
        
        Args:
            product_id: Formato "shopid.itemid" ou apenas "itemid"
            
        Returns:
            Product ou None
        """
        client = await self._get_client()
        
        # Parse do ID
        if "." in product_id:
            shop_id, item_id = product_id.split(".", 1)
        else:
            # Sem shop_id, não conseguimos buscar detalhes
            logger.warning(f"Shopee: product_id deve ser 'shopid.itemid': {product_id}")
            return None
        
        try:
            params = {
                "itemid": item_id,
                "shopid": shop_id,
            }
            
            response = await client.get(
                f"{self.PUBLIC_API}/item/get",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("data"):
                return self._normalize_product(data["data"])
            
            return None
            
        except Exception as e:
            logger.error(f"Shopee: Erro ao buscar produto {product_id}: {e}")
            return None
    
    async def get_categories(self) -> list[dict]:
        """
        Lista categorias da Shopee Brasil.
        
        Returns:
            Lista de categorias com id, name
        """
        client = await self._get_client()
        
        try:
            response = await client.get(
                f"{self.PUBLIC_API}/category_list/get"
            )
            response.raise_for_status()
            data = response.json()
            
            categories = []
            for cat in data.get("data", {}).get("category_list", []):
                categories.append({
                    "id": cat.get("catid"),
                    "name": cat.get("name"),
                    "display_name": cat.get("display_name"),
                    "children": cat.get("children", []),
                })
            
            return categories
            
        except Exception as e:
            logger.error(f"Shopee: Erro ao buscar categorias: {e}")
            return []
    
    # === Partner API (para lojistas autenticados) ===
    
    async def get_shop_info(self) -> Optional[dict]:
        """
        Obtém informações da loja autenticada.
        
        Requer: partner_id, partner_key, shop_id, access_token
        """
        if not all([self.partner_id, self.partner_key, self.shop_id, self.access_token]):
            logger.error("Shopee: Credenciais de parceiro não configuradas")
            return None
        
        path = "/api/v2/shop/get_shop_info"
        timestamp = int(time.time())
        sign = self._generate_sign(path, timestamp)
        
        params = {
            "partner_id": self.partner_id,
            "timestamp": timestamp,
            "access_token": self.access_token,
            "shop_id": self.shop_id,
            "sign": sign,
        }
        
        client = await self._get_client()
        
        try:
            response = await client.get(
                f"{self.BASE_URL}{path}",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Shopee: Erro ao buscar shop info: {e}")
            return None
    
    async def list_items(
        self,
        offset: int = 0,
        page_size: int = 20,
        item_status: str = "NORMAL"
    ) -> list[dict]:
        """
        Lista itens da loja autenticada.
        
        Args:
            offset: Offset para paginação
            page_size: Itens por página (max 100)
            item_status: "NORMAL", "BANNED", "DELETED", etc.
        """
        if not all([self.partner_id, self.partner_key, self.shop_id, self.access_token]):
            return []
        
        path = "/api/v2/product/get_item_list"
        timestamp = int(time.time())
        sign = self._generate_sign(path, timestamp)
        
        params = {
            "partner_id": self.partner_id,
            "timestamp": timestamp,
            "access_token": self.access_token,
            "shop_id": self.shop_id,
            "sign": sign,
            "offset": offset,
            "page_size": min(page_size, 100),
            "item_status": item_status,
        }
        
        client = await self._get_client()
        
        try:
            response = await client.get(
                f"{self.BASE_URL}{path}",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", {}).get("item", [])
        except Exception as e:
            logger.error(f"Shopee: Erro ao listar itens: {e}")
            return []
    
    def _normalize_product(self, raw: dict) -> Product:
        """Normaliza produto da Shopee."""
        
        # IDs
        item_id = str(raw.get("itemid", raw.get("item_id", "")))
        shop_id = str(raw.get("shopid", raw.get("shop_id", "")))
        
        # URL
        name_slug = raw.get("name", "product").lower().replace(" ", "-")[:50]
        url = f"https://shopee.com.br/{name_slug}-i.{shop_id}.{item_id}"
        
        # Preço (Shopee usa valor * 100000)
        price_raw = raw.get("price", raw.get("price_min", 0))
        price = Decimal(str(price_raw)) / 100000 if price_raw else Decimal("0")
        
        original_price = None
        discount = None
        
        price_before = raw.get("price_before_discount", raw.get("price_max_before_discount", 0))
        if price_before and price_before > price_raw:
            original_price = Decimal(str(price_before)) / 100000
            if original_price > 0:
                discount = float(((original_price - price) / original_price) * 100)
        
        # Imagens
        thumbnail = None
        images = []
        
        image = raw.get("image", raw.get("item_cover"))
        if image:
            if not image.startswith("http"):
                image = f"https://cf.shopee.com.br/file/{image}"
            thumbnail = image
        
        for img in raw.get("images", []):
            if not img.startswith("http"):
                img = f"https://cf.shopee.com.br/file/{img}"
            images.append(img)
        
        # Rating
        rating = None
        reviews = None
        
        item_rating = raw.get("item_rating", {})
        if item_rating:
            rating = item_rating.get("rating_star")
            reviews = item_rating.get("rating_count", [0])
            if isinstance(reviews, list):
                reviews = sum(reviews)
        else:
            rating = raw.get("rating_star")
            reviews = raw.get("cmt_count", raw.get("comment_count"))
        
        # Vendas
        sales = raw.get("sold", raw.get("historical_sold", raw.get("sold_count")))
        
        # Frete grátis
        free_shipping = bool(raw.get("show_free_shipping", raw.get("free_shipping")))
        
        # Loja oficial
        is_official = bool(raw.get("is_official_shop", raw.get("shopee_verified")))
        
        # Estoque
        stock = raw.get("stock", raw.get("normal_stock"))
        
        return Product(
            id=f"{shop_id}.{item_id}",
            marketplace=self.marketplace_type,
            external_url=url,
            title=raw.get("name", ""),
            brand=raw.get("brand"),
            category=str(raw.get("catid", "")),
            condition=ProductCondition.NEW,
            price=price,
            original_price=original_price,
            currency="BRL",
            discount_percentage=discount,
            thumbnail=thumbnail,
            images=images,
            free_shipping=free_shipping,
            seller_id=shop_id,
            seller_name=raw.get("shop_name"),
            is_official_store=is_official,
            rating=rating,
            reviews_count=reviews,
            sales_count=sales,
            available_quantity=stock,
        )


# Função helper
async def search_shopee(query: str, **kwargs) -> SearchResult:
    """Busca rápida na Shopee."""
    client = ShopeeClient()
    try:
        return await client.search(query, **kwargs)
    finally:
        await client.close()
