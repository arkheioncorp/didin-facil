"""
Base classes e tipos compartilhados para integrações de marketplaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_serializer


class MarketplaceType(str, Enum):
    """Tipos de marketplace suportados."""
    MERCADO_LIVRE = "mercado_livre"
    AMAZON = "amazon"
    SHOPEE = "shopee"
    ALIEXPRESS = "aliexpress"
    TIKTOK_SHOP = "tiktok_shop"
    MAGALU = "magalu"


class ProductCondition(str, Enum):
    """Condição do produto."""
    NEW = "new"
    USED = "used"
    REFURBISHED = "refurbished"


@dataclass
class Seller:
    """Informações do vendedor."""
    id: str
    name: str
    reputation_score: Optional[float] = None
    total_sales: Optional[int] = None
    is_official_store: bool = False
    location: Optional[str] = None


@dataclass
class PriceInfo:
    """Informações de preço completas."""
    current_price: Decimal
    original_price: Optional[Decimal] = None
    currency: str = "BRL"
    discount_percentage: Optional[float] = None
    installments: Optional[int] = None
    installment_value: Optional[Decimal] = None
    
    @property
    def has_discount(self) -> bool:
        return self.original_price is not None and self.current_price < self.original_price


@dataclass
class ShippingInfo:
    """Informações de envio."""
    is_free: bool = False
    estimated_days: Optional[int] = None
    price: Optional[Decimal] = None
    method: Optional[str] = None


class Product(BaseModel):
    """Modelo unificado de produto para todos os marketplaces."""
    
    # Identificação
    id: str = Field(..., description="ID do produto no marketplace")
    marketplace: MarketplaceType = Field(..., description="Marketplace de origem")
    external_url: HttpUrl = Field(..., description="URL do produto")
    
    # Informações básicas
    title: str = Field(..., description="Título do produto")
    description: Optional[str] = Field(None, description="Descrição")
    brand: Optional[str] = Field(None, description="Marca")
    category: Optional[str] = Field(None, description="Categoria")
    condition: ProductCondition = Field(default=ProductCondition.NEW)
    
    # Preço
    price: Decimal = Field(..., description="Preço atual")
    original_price: Optional[Decimal] = Field(None, description="Preço original")
    currency: str = Field(default="BRL")
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    
    # Parcelamento
    installments: Optional[int] = Field(None, ge=1)
    installment_value: Optional[Decimal] = Field(None)
    
    # Imagens
    thumbnail: Optional[HttpUrl] = Field(None)
    images: list[HttpUrl] = Field(default_factory=list)
    
    # Envio
    free_shipping: bool = Field(default=False)
    shipping_price: Optional[Decimal] = Field(None)
    estimated_delivery_days: Optional[int] = Field(None)
    
    # Vendedor
    seller_id: Optional[str] = Field(None)
    seller_name: Optional[str] = Field(None)
    seller_reputation: Optional[float] = Field(None, ge=0, le=5)
    is_official_store: bool = Field(default=False)
    
    # Métricas
    rating: Optional[float] = Field(None, ge=0, le=5)
    reviews_count: Optional[int] = Field(None, ge=0)
    sales_count: Optional[int] = Field(None, ge=0)
    available_quantity: Optional[int] = Field(None, ge=0)
    
    # Metadados
    attributes: dict[str, Any] = Field(default_factory=dict)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(ser_json_timedelta="iso8601")
    
    @field_serializer("price", "original_price")
    def serialize_decimal(self, v: Decimal | None) -> str | None:
        return str(v) if v is not None else None
    
    @field_serializer("fetched_at")
    def serialize_datetime(self, v: datetime) -> str:
        return v.isoformat()
    
    @property
    def has_discount(self) -> bool:
        return (
            self.original_price is not None 
            and self.price < self.original_price
        )
    
    def to_comparison_dict(self) -> dict:
        """Retorna dict para comparação entre marketplaces."""
        return {
            "marketplace": self.marketplace.value,
            "title": self.title,
            "price": float(self.price),
            "original_price": float(self.original_price) if self.original_price else None,
            "discount": self.discount_percentage,
            "free_shipping": self.free_shipping,
            "rating": self.rating,
            "reviews": self.reviews_count,
            "url": str(self.external_url),
        }


class SearchResult(BaseModel):
    """Resultado de busca unificado."""
    query: str
    marketplace: MarketplaceType
    total_results: int
    page: int = 1
    per_page: int = 20
    products: list[Product] = Field(default_factory=list)
    search_time_ms: Optional[float] = None
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    
    @property
    def has_more(self) -> bool:
        return len(self.products) == self.per_page


class MarketplaceBase(ABC):
    """
    Classe base abstrata para integrações de marketplace.
    
    Cada marketplace deve implementar:
    - search(): Buscar produtos
    - get_product(): Obter detalhes de um produto
    - get_categories(): Listar categorias (opcional)
    """
    
    marketplace_type: MarketplaceType
    
    def __init__(self, api_key: Optional[str] = None, **config):
        self.api_key = api_key
        self.config = config
        self._is_authenticated = False
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        page: int = 1, 
        per_page: int = 20,
        **filters
    ) -> SearchResult:
        """
        Busca produtos no marketplace.
        
        Args:
            query: Termo de busca
            page: Página (1-indexed)
            per_page: Itens por página
            **filters: Filtros específicos do marketplace
            
        Returns:
            SearchResult com lista de produtos
        """
        pass
    
    @abstractmethod
    async def get_product(self, product_id: str) -> Optional[Product]:
        """
        Obtém detalhes completos de um produto.
        
        Args:
            product_id: ID do produto no marketplace
            
        Returns:
            Product ou None se não encontrado
        """
        pass
    
    async def get_categories(self) -> list[dict]:
        """
        Lista categorias disponíveis.
        
        Returns:
            Lista de categorias
        """
        return []
    
    async def authenticate(self) -> bool:
        """
        Autentica com a API do marketplace.
        
        Returns:
            True se autenticado com sucesso
        """
        self._is_authenticated = True
        return True
    
    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated
    
    def _normalize_product(self, raw_data: dict) -> Product:
        """
        Normaliza dados brutos do marketplace para Product.
        
        Cada subclasse deve sobrescrever este método para
        mapear os campos específicos do marketplace.
        """
        raise NotImplementedError("Subclass must implement _normalize_product")
