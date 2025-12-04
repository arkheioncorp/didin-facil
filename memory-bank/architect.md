# System Architect - Didin Fácil

**Última Atualização:** 4 de Dezembro de 2025

---

## Overview

Este arquivo contém as decisões arquiteturais e padrões de design do projeto Didin Fácil.

---

## Architectural Decisions

### ADR-001: Monolito Modular

**Data:** Novembro 2025  
**Status:** Aprovado  

**Decisão:** Iniciar com arquitetura de Monolito Modular.

**Contexto:** Projeto em fase inicial com equipe pequena.

**Consequências:**
- ✅ Deploy simples
- ✅ Transações ACID nativas
- ✅ Sem overhead de comunicação distribuída
- ⚠️ Escala vertical limitada

---

### ADR-002: Hybrid Desktop-Cloud

**Data:** Novembro 2025  
**Status:** Aprovado  

**Decisão:** Frontend Tauri (desktop) + Backend FastAPI (cloud).

**Contexto:** Necessidade de proteger IP do usuário e controlar scraping centralmente.

**Consequências:**
- ✅ Proteção de identidade do usuário
- ✅ Scraping centralizado e controlado
- ✅ Desktop nativo com Rust
- ⚠️ Complexidade de sincronização

---

### ADR-003: PostgreSQL + Redis + MeiliSearch

**Data:** Novembro 2025  
**Status:** Aprovado  

**Decisão:** Stack de dados com PostgreSQL (primary), Redis (cache/sessions), MeiliSearch (search).

**Contexto:** Necessidade de busca full-text rápida e cache distribuído.

**Consequências:**
- ✅ Performance de busca excelente
- ✅ Cache eficiente
- ✅ ACID compliance
- ⚠️ Múltiplos sistemas para gerenciar

---

### ADR-004: React + Zustand (Frontend)

**Data:** Dezembro 2025  
**Status:** Aprovado  

**Decisão:** Usar React com Zustand para gerenciamento de estado.

**Contexto:** Necessidade de estado global simples e type-safe.

**Consequências:**
- ✅ Simplicidade vs Redux
- ✅ Persistência built-in
- ✅ DevTools suportado
- ⚠️ Menor ecossistema que Redux

---

### ADR-005: Clean Architecture Evolution (PLANEJADO)

**Data:** Dezembro 2025  
**Status:** Planejado  

**Decisão:** Evoluir para Clean Architecture com Domain Layer.

**Contexto:** Necessidade de melhor separação de responsabilidades.

**Estrutura Proposta:**
```
backend/
├── domain/           # Entities, Value Objects, Domain Services
├── application/      # Use Cases, DTOs
├── infrastructure/   # Persistence, External APIs
└── api/              # Presentation (routes, schemas, middleware)
```

---

## Design Considerations

### 1. Camadas e Dependências

```
┌─────────────────────────────────────────┐
│          API/Presentation               │
│    (Routes, Schemas, Middleware)        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Application                    │
│    (Use Cases, DTOs, Orchestration)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            Domain                       │
│  (Entities, Value Objects, Rules)       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Infrastructure                  │
│  (Database, Cache, External APIs)       │
└─────────────────────────────────────────┘
```

**Regras:**
- Camadas externas dependem de camadas internas
- Domain layer não tem dependências externas
- Inversão de dependência via interfaces

### 2. Padrões em Uso

| Padrão | Uso | Localização |
|--------|-----|-------------|
| Repository | Acesso a dados | `shared/postgres.py`, `modules/crm/repository.py` |
| Factory | Criação de objetos | `api/dependencies.py` |
| Strategy | Pricing, Scraping | `scraper/`, `api/config/pricing.py` |
| Observer | Eventos | `modules/crm/events.py` |
| Middleware | Cross-cutting | `api/middleware/` |

### 3. Segurança

- JWT para autenticação
- HWID binding para licenças
- Rate limiting por IP e usuário
- Security headers (CSP, HSTS, XSS)
- Validação com Pydantic
- Prepared statements (sem SQL injection)

---

## Components

### Backend Components

| Componente | Responsabilidade |
|------------|------------------|
| **API** | Gateway principal, routes, schemas |
| **Scraper** | Worker de scraping (Playwright) |
| **Workers** | Background jobs (Redis queues) |
| **Modules** | Domínios específicos (CRM, Automation) |
| **Shared** | Config, DB, Redis, Storage |

### Frontend Components

| Componente | Responsabilidade |
|------------|------------------|
| **Pages** | Rotas e layouts de página |
| **Components** | UI reutilizáveis |
| **Stores** | Estado global (Zustand) |
| **Services** | API clients |
| **Hooks** | Lógica reutilizável |

---

## Roadmap de Melhorias

1. **Q1 2025:** Implementar Domain Layer
2. **Q1 2025:** Adicionar Use Cases
3. **Q2 2025:** Unificar Repository Pattern
4. **Q2 2025:** Migrar para Event-Driven quando necessário

---

**Mantido por:** Time de Arquitetura  
**Próxima Revisão:** Janeiro 2026

