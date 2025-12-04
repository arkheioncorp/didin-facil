# Decision Log - Didin Fácil

**Última Atualização:** 4 de Dezembro de 2025

---

## Decisões Arquiteturais

| Data | Decisão | Contexto | Status |
|------|---------|----------|--------|
| Nov 2025 | Monolito Modular | Equipe pequena, domínio em evolução | ✅ Aprovado |
| Nov 2025 | Hybrid Desktop-Cloud (Tauri + FastAPI) | Proteção de IP, scraping centralizado | ✅ Aprovado |
| Nov 2025 | PostgreSQL + Redis + MeiliSearch | Performance de busca, cache eficiente | ✅ Aprovado |
| Nov 2025 | React + Zustand | Estado global simples e type-safe | ✅ Aprovado |
| Dez 2025 | Evoluir para Clean Architecture | Melhor separação de responsabilidades | 📋 Planejado |

---

## Decisões Técnicas Recentes

### 2025-12-04: Revisão Arquitetural Completa

**Contexto:** Revisão para polimento do projeto.

**Decisões:**
1. Corrigir configuração Ruff no `pyproject.toml`
2. Planejar Domain Layer para Q1 2025
3. Unificar Repository Pattern
4. Habilitar TypeScript strict mode gradualmente

**Documento:** `docs/technical/ARCHITECTURE_REVIEW.md`

---

### 2025-11-30: Sistema de Subscriptions SaaS

**Contexto:** Migração de licenças perpétuas para modelo SaaS.

**Decisões:**
1. Planos: FREE, STARTER, PROFESSIONAL, ENTERPRISE
2. Limites por feature (metered)
3. Billing cycle: monthly/yearly
4. Migração de dados de licenças existentes

---

### 2025-11-26: CRM Module

**Contexto:** Necessidade de gestão de leads e contatos.

**Decisões:**
1. Repository pattern com asyncpg
2. Event-driven para notificações
3. Integração com WhatsApp e Email

---

## Template de Decisão

```markdown
### [DATA]: [TÍTULO]

**Contexto:** [Por que essa decisão foi necessária]

**Opções Consideradas:**
1. Opção A - Prós/Contras
2. Opção B - Prós/Contras

**Decisão:** [Opção escolhida]

**Consequências:**
- ✅ [Benefício 1]
- ⚠️ [Trade-off aceito]

**Status:** Aprovado | Pendente | Revertido
```

