"""
Product Entity
==============

Entidade de produto do marketplace com regras de negócio relacionadas
a preços, estoque e trending.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from domain.value_objects import Money


@dataclass
class Product:
    """
    Entidade Product - representa um produto do marketplace.
    
    Invariantes:
    - Preço deve ser positivo
    - Contagens de vendas não podem ser negativas
    - Rating entre 0 e 5
    """
    
    id: UUID
    external_id: str  # ID no marketplace original
    title: str
    source: str  # tiktok_shop, aliexpress, etc.
    
    # Preços
    price: Money
    original_price: Optional[Money] = None
    
    # Métricas
    sales_count: int = 0
    sales_7d: int = 0
    sales_30d: int = 0
    review_count: int = 0
    rating: Optional[Decimal] = None
    
    # Categorização
    category: Optional[str] = None
    subcategory: Optional[str] = None
    
    # Vendedor
    seller_name: Optional[str] = None
    seller_rating: Optional[Decimal] = None
    
    # Mídia
    image_url: Optional[str] = None
    images: List[str] = field(default_factory=list)
    video_url: Optional[str] = None
    product_url: Optional[str] = None
    
    # Status
    in_stock: bool = True
    stock_level: Optional[int] = None
    is_trending: bool = False
    
    # Timestamps
    collected_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validar invariantes após criação."""
        if self.sales_count < 0:
            raise ValueError("Sales count cannot be negative")
        if self.rating is not None and not (0 <= self.rating <= 5):
            raise ValueError("Rating must be between 0 and 5")
    
    @classmethod
    def create(
        cls,
        external_id: str,
        title: str,
        source: str,
        price: Money,
        **kwargs,
    ) -> "Product":
        """Factory method para criar novo produto."""
        return cls(
            id=uuid4(),
            external_id=external_id,
            title=title,
            source=source,
            price=price,
            **kwargs,
        )
    
    def update_price(self, new_price: Money) -> None:
        """Atualizar preço do produto."""
        if self.price != new_price:
            self.original_price = self.price
            self.price = new_price
            self._touch()
    
    def update_sales(self, sales_7d: int, sales_30d: int) -> None:
        """Atualizar métricas de vendas."""
        if sales_7d < 0 or sales_30d < 0:
            raise ValueError("Sales cannot be negative")
        
        self.sales_7d = sales_7d
        self.sales_30d = sales_30d
        self.sales_count = sales_30d  # Usar 30d como total
        self._update_trending()
        self._touch()
    
    def mark_out_of_stock(self) -> None:
        """Marcar produto como fora de estoque."""
        self.in_stock = False
        self.stock_level = 0
        self._touch()
    
    def update_stock(self, level: int) -> None:
        """Atualizar nível de estoque."""
        if level < 0:
            raise ValueError("Stock level cannot be negative")
        
        self.stock_level = level
        self.in_stock = level > 0
        self._touch()
    
    def _update_trending(self) -> None:
        """Calcular se produto está em trending."""
        # Produto é trending se vendeu mais de 100 nos últimos 7 dias
        # ou se tem alta taxa de crescimento
        self.is_trending = self.sales_7d >= 100 or (
            self.sales_30d > 0 and self.sales_7d / (self.sales_30d / 4) > 1.5
        )
    
    def _touch(self) -> None:
        """Atualizar timestamp de modificação."""
        self.updated_at = datetime.now(timezone.utc)
    
    @property
    def discount_percentage(self) -> Optional[Decimal]:
        """Calcular porcentagem de desconto."""
        if not self.original_price:
            return None
        if self.original_price.amount <= self.price.amount:
            return None
        diff = self.original_price.amount - self.price.amount
        discount = diff / self.original_price.amount
        return discount * 100
    
    @property
    def is_on_sale(self) -> bool:
        """Verificar se produto está em promoção."""
        pct = self.discount_percentage
        return pct is not None and pct > 0
    
    @property
    def trending_score(self) -> float:
        """Calcular score de trending para ordenação."""
        base_score = self.sales_7d * 2 + self.sales_30d
        rating_multiplier = float(self.rating) / 5 if self.rating else 0.5
        return base_score * rating_multiplier
