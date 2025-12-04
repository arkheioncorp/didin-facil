"""
Domain Layer - TikTrend Finder
==========================

Este pacote contém a camada de domínio da aplicação, seguindo os princípios
da Clean Architecture e Domain-Driven Design (DDD).

Estrutura:
- entities/: Entidades de domínio com identidade e regras de negócio
- value_objects/: Objetos de valor imutáveis
- repositories/: Interfaces/protocolos para acesso a dados
- services/: Serviços de domínio para lógica que não pertence a entidades
- events/: Eventos de domínio para comunicação assíncrona
- exceptions/: Exceções específicas do domínio

Princípios:
1. Domain Layer não tem dependências externas (frameworks, DB, etc.)
2. Todas as regras de negócio ficam aqui
3. Entidades e Value Objects são imutáveis quando possível
4. Repositórios são apenas interfaces (implementação na infrastructure)

Roadmap Q1 2025:
- [x] Estrutura inicial de pastas
- [ ] Entidades: User, Product, Subscription, Lead
- [ ] Value Objects: Money, Email, DeviceId
- [ ] Repository Interfaces
- [ ] Domain Services
- [ ] Domain Events

Exemplo de uso:
    from domain.entities import User
    from domain.value_objects import Email, Money
    from domain.repositories import UserRepository
    
    email = Email("user@example.com")
    user = User.create(email=email, name="John")
"""

__version__ = "0.1.0"
__author__ = "TikTrend Finder Team"
