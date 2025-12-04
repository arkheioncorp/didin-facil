"""
Product Repository Interface
============================

Interface para acesso a dados de produtos.
"""

from typing import List, Optional, Protocol
from uuid import UUID

from domain.entities import Product


class ProductRepository(Protocol):
    """
    Interface para repositório de produtos.
    
    Implementações devem ser criadas na camada de infraestrutura.
    """
    
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """
        Buscar produto por ID.
        
        Args:
            product_id: UUID do produto
        
        Returns:
            Product se encontrado, None caso contrário
        """
        ...
    
    async def get_by_external_id(
        self,
        external_id: str,
        source: str,
    ) -> Optional[Product]:
        """
        Buscar produto por ID externo (do marketplace).
        
        Args:
            external_id: ID no marketplace original
            source: Nome do marketplace (tiktok_shop, aliexpress)
        
        Returns:
            Product se encontrado, None caso contrário
        """
        ...
    
    async def save(self, product: Product) -> Product:
        """
        Salvar produto (criar ou atualizar).
        
        Args:
            product: Entidade Product
        
        Returns:
            Product salvo
        """
        ...
    
    async def save_many(self, products: List[Product]) -> List[Product]:
        """
        Salvar múltiplos produtos em batch.
        
        Args:
            products: Lista de produtos
        
        Returns:
            Lista de produtos salvos
        """
        ...
    
    async def delete(self, product_id: UUID) -> bool:
        """
        Deletar produto por ID.
        
        Args:
            product_id: UUID do produto
        
        Returns:
            True se deletado, False se não encontrado
        """
        ...
    
    async def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_sales: Optional[int] = None,
        source: Optional[str] = None,
        in_stock_only: bool = False,
        trending_only: bool = False,
        sort_by: str = "sales_30d",
        sort_order: str = "desc",
        limit: int = 20,
        offset: int = 0,
    ) -> List[Product]:
        """
        Buscar produtos com filtros.
        
        Args:
            query: Termo de busca (título/descrição)
            category: Filtrar por categoria
            min_price: Preço mínimo
            max_price: Preço máximo
            min_sales: Mínimo de vendas
            source: Filtrar por marketplace
            in_stock_only: Apenas em estoque
            trending_only: Apenas trending
            sort_by: Campo para ordenação
            sort_order: asc ou desc
            limit: Máximo de resultados
            offset: Offset para paginação
        
        Returns:
            Lista de produtos
        """
        ...
    
    async def count(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
    ) -> int:
        """
        Contar produtos com filtros.
        
        Args:
            query: Termo de busca
            category: Filtrar por categoria
            source: Filtrar por marketplace
        
        Returns:
            Número de produtos
        """
        ...
    
    async def get_trending(self, limit: int = 20) -> List[Product]:
        """
        Buscar produtos em trending.
        
        Args:
            limit: Máximo de resultados
        
        Returns:
            Lista de produtos trending ordenados por score
        """
        ...
    
    async def get_categories(self, source: Optional[str] = None) -> List[str]:
        """
        Listar categorias disponíveis.
        
        Args:
            source: Filtrar por marketplace
        
        Returns:
            Lista de nomes de categorias
        """
        ...
