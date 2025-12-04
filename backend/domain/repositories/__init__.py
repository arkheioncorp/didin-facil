"""
Repository Interfaces
=====================

Interfaces (protocolos) para repositórios de acesso a dados.
A implementação real fica na camada de infraestrutura.

Princípios:
- Repositórios são definidos como Protocol (structural subtyping)
- Métodos são async para suportar I/O assíncrono
- Retornam entidades de domínio, não dicts ou rows

Repositórios planejados:
- UserRepository: CRUD de usuários
- ProductRepository: CRUD de produtos
- SubscriptionRepository: CRUD de assinaturas
"""

from .product_repository import ProductRepository
from .user_repository import UserRepository

__all__ = ["UserRepository", "ProductRepository"]
