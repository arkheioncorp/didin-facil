"""
Domain Entities
===============

Entidades são objetos com identidade única que persistem ao longo do tempo.
Elas encapsulam regras de negócio e garantem invariantes.

Entidades planejadas:
- User: Usuário do sistema
- Product: Produto do marketplace
- Subscription: Assinatura SaaS
- Lead: Lead do CRM
- Deal: Negociação do CRM
"""

from .product import Product
from .user import User

__all__ = ["User", "Product"]
