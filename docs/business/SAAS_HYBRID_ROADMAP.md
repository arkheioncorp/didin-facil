# 🚀 ROADMAP COMPLETO: Migração para SaaS Híbrido

> **Projeto:** TikTrend Finder - Sistema de Comparação de Preços Multi-Marketplace  
> **Versão:** 2.0.0  
> **Data:** Dezembro 2024  
> **Modelo:** SaaS Híbrido (Local + Cloud)

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Arquitetura Atual vs Nova](#arquitetura-atual-vs-nova)
3. [Novo Sistema de Planos](#novo-sistema-de-planos)
4. [Mapa de Mudanças por Arquivo](#mapa-de-mudanças-por-arquivo)
5. [Roadmap de Implementação](#roadmap-de-implementação)
6. [Especificações Técnicas](#especificações-técnicas)
7. [Cronograma e Estimativas](#cronograma-e-estimativas)
8. [Riscos e Mitigações](#riscos-e-mitigações)

---

## 1. Visão Geral

### 1.1 Por que SaaS Híbrido?

Com a expansão para **5+ marketplaces** (TikTok Shop, Shopee, Amazon, Mercado Livre, Hotmart), o modelo SaaS Híbrido oferece:

| Aspecto | Lifetime Atual | SaaS Híbrido |
|---------|---------------|--------------|
| **Manutenção Scrapers** | Cada usuário atualiza | Centralizado no cloud |
| **Custos de Proxy** | Usuário paga | Compartilhado (economiza 80%) |
| **Tempo de Atualização** | Deploy manual | Instantâneo para todos |
| **Escalabilidade** | Limitada pelo PC | Ilimitada no cloud |
| **MRR Previsível** | R$ 0 após venda | R$ 97-297/mês recorrente |

### 1.2 Modos de Execução

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MODOS DE EXECUÇÃO                            │
├─────────────────┬──────────────────────┬───────────────────────────┤
│     LOCAL       │       HÍBRIDO        │          CLOUD            │
├─────────────────┼──────────────────────┼───────────────────────────┤
│ Tauri Desktop   │ Tauri + Backend API  │ Web App apenas            │
│ SQLite Local    │ SQLite + PostgreSQL  │ PostgreSQL apenas         │
│ Scraper local   │ Scraper cloud        │ Scraper cloud             │
│ Offline first   │ Sync when online     │ Requires connection       │
│ Baixa latência  │ Média latência       │ Alta latência             │
│ Privacidade +++ │ Privacidade ++       │ Privacidade +             │
└─────────────────┴──────────────────────┴───────────────────────────┘
```

---

## 2. Arquitetura Atual vs Nova

### 2.1 Arquitetura ATUAL

```
┌────────────────────────────────────────────────────────────┐
│                    ARQUITETURA ATUAL                       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────┐         ┌──────────────────────┐     │
│  │  Tauri Desktop  │────────▶│   FastAPI Backend    │     │
│  │   (Rust + Vue)  │         │   (Cloud/Local)      │     │
│  │                 │         │                      │     │
│  │  ┌───────────┐  │         │  ┌────────────────┐  │     │
│  │  │ SQLite DB │  │         │  │  PostgreSQL    │  │     │
│  │  │ (local)   │  │         │  │  + Redis       │  │     │
│  │  └───────────┘  │         │  └────────────────┘  │     │
│  │                 │         │                      │     │
│  │  ┌───────────┐  │         │  ┌────────────────┐  │     │
│  │  │ Scraper   │  │         │  │  License       │  │     │
│  │  │ TikTok    │◀─┼─────────┤  │  Validation    │  │     │
│  │  │ (local)   │  │         │  └────────────────┘  │     │
│  │  └───────────┘  │         │                      │     │
│  └─────────────────┘         └──────────────────────┘     │
│                                                            │
│  Modelo: Licença Vitalícia R$ 49,90 + Créditos             │
│  Problema: Não escala para multi-marketplace               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 2.2 Arquitetura NOVA (SaaS Híbrido)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        ARQUITETURA SAAS HÍBRIDO                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────┐      ┌─────────────────────────────────────┐│
│  │     TAURI DESKTOP        │      │           CLOUD BACKEND             ││
│  │                          │      │                                     ││
│  │  ┌────────────────────┐  │      │  ┌─────────────────────────────┐   ││
│  │  │ Mode: LOCAL        │  │      │  │        FastAPI              │   ││
│  │  │ - Favorites        │  │      │  │  ┌──────────────────────┐   │   ││
│  │  │ - History          │  │      │  │  │ Subscription Service │   │   ││
│  │  │ - Offline cache    │  │      │  │  │ - Plan validation    │   │   ││
│  │  │ - Price alerts     │  │      │  │  │ - Usage metering     │   │   ││
│  │  └────────────────────┘  │      │  │  │ - Feature gating     │   │   ││
│  │                          │      │  │  └──────────────────────┘   │   ││
│  │  ┌────────────────────┐  │      │  │                             │   ││
│  │  │ Mode: HYBRID       │◀─┼─────▶│  │  ┌──────────────────────┐   │   ││
│  │  │ - Sync products    │  │      │  │  │  Scraper Workers     │   │   ││
│  │  │ - Cloud scrapers   │  │      │  │  │  - TikTok Shop       │   │   ││
│  │  │ - AI analysis      │  │      │  │  │  - Shopee           │   │   ││
│  │  │ - Multi-marketplace│  │      │  │  │  - Amazon           │   │   ││
│  │  └────────────────────┘  │      │  │  │  - Mercado Livre    │   │   ││
│  │                          │      │  │  │  - Hotmart          │   │   ││
│  │  ┌────────────────────┐  │      │  │  └──────────────────────┘   │   ││
│  │  │ SQLite Database    │  │      │  │                             │   ││
│  │  │ - subscription_cache│ │      │  │  ┌──────────────────────┐   │   ││
│  │  │ - local_products   │  │      │  │  │  PostgreSQL + Redis  │   │   ││
│  │  │ - sync_queue       │  │      │  │  │  - subscriptions     │   │   ││
│  │  │ - feature_flags    │  │      │  │  │  - usage_records     │   │   ││
│  │  └────────────────────┘  │      │  │  │  - products_cloud    │   │   ││
│  │                          │      │  │  └──────────────────────┘   │   ││
│  └──────────────────────────┘      │  └─────────────────────────────┘   ││
│                                    │                                     ││
│  ┌──────────────────────────┐      │  ┌─────────────────────────────┐   ││
│  │      WEB APP (React)     │◀─────┼─▶│      MercadoPago            │   ││
│  │  - Dashboard             │      │  │  - Subscriptions            │   ││
│  │  - Comparador            │      │  │  - Webhooks                 │   ││
│  │  - Social Hub            │      │  └─────────────────────────────┘   ││
│  └──────────────────────────┘      └─────────────────────────────────────┘│
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Novo Sistema de Planos

### 3.1 Matriz de Planos × Modos

| Feature | FREE | STARTER (R$ 97/mês) | BUSINESS (R$ 297/mês) | ENTERPRISE |
|---------|------|---------------------|----------------------|------------|
| **Modo Execução** | Web Only | Web + Tauri Hybrid | Web + Tauri Full | Custom |
| **Marketplaces** | 1 (TikTok) | 3 | 5+ (todos) | Ilimitado |
| **Buscas/mês** | 50 | 500 | Ilimitado | Ilimitado |
| **Alertas de Preço** | 5 | 50 | Ilimitado | Ilimitado |
| **WhatsApp** | 1 instância | 3 instâncias | Ilimitado | Ilimitado |
| **Mensagens/mês** | 100 | 1.000 | Ilimitado | Ilimitado |
| **Chatbot** | ❌ | 5 fluxos | Ilimitado + IA | Custom |
| **CRM Leads** | ❌ | 500 | Ilimitado | Ilimitado |
| **Social Posts** | 10/mês | 100/mês | Ilimitado | Ilimitado |
| **Scraper Mode** | Cloud Shared | Cloud Dedicated | Cloud Premium | On-premise |
| **Analytics** | Básico | Avançado | BI + Export | Enterprise |
| **Suporte** | Email | Email + Chat | Prioritário + Phone | Dedicado |
| **Offline Mode** | ❌ | ✅ Básico | ✅ Completo | Custom |
| **API Access** | ❌ | Rate limited | Unlimited | Dedicated |

### 3.2 Estrutura de Código Nova

```python
# backend/modules/subscription/plans.py (NOVO)

class ExecutionMode(str, Enum):
    """Modo de execução do app."""
    WEB_ONLY = "web_only"        # Apenas navegador
    HYBRID = "hybrid"           # Tauri + Cloud
    LOCAL_FIRST = "local_first" # Tauri com cache offline

class MarketplaceAccess(str, Enum):
    """Acesso a marketplaces."""
    TIKTOK = "tiktok"
    SHOPEE = "shopee"
    AMAZON = "amazon"
    MERCADO_LIVRE = "mercado_livre"
    HOTMART = "hotmart"
    ALIEXPRESS = "aliexpress"

@dataclass
class PlanConfig:
    """Configuração completa de um plano."""
    tier: PlanTier
    name: str
    description: str
    
    # Preços
    price_monthly: Decimal
    price_yearly: Decimal
    
    # Execução
    execution_modes: list[ExecutionMode]
    marketplaces: list[MarketplaceAccess]
    scraper_priority: int  # 1=shared, 2=dedicated, 3=premium
    
    # Limites
    limits: dict[str, int]  # -1 = ilimitado
    
    # Features booleanas
    features: dict[str, bool]

PLANS_V2: dict[PlanTier, PlanConfig] = {
    PlanTier.FREE: PlanConfig(
        tier=PlanTier.FREE,
        name="Free",
        description="Perfeito para começar",
        price_monthly=Decimal("0"),
        price_yearly=Decimal("0"),
        execution_modes=[ExecutionMode.WEB_ONLY],
        marketplaces=[MarketplaceAccess.TIKTOK],
        scraper_priority=1,
        limits={
            "searches_per_month": 50,
            "price_alerts": 5,
            "favorites": 20,
            "whatsapp_instances": 1,
            "messages_per_month": 100,
            "chatbot_flows": 0,
            "crm_leads": 0,
            "social_posts_per_month": 10,
        },
        features={
            "offline_mode": False,
            "api_access": False,
            "analytics_advanced": False,
            "export_data": False,
            "white_label": False,
        }
    ),
    # ... STARTER, BUSINESS, ENTERPRISE
}
```

---

## 4. Mapa de Mudanças por Arquivo

### 4.1 BACKEND - Alta Prioridade 🔴

| Arquivo | Linhas | Mudança | Descrição |
|---------|--------|---------|-----------|
| `backend/modules/subscription/plans.py` | 513 | **REFATORAR** | Adicionar `ExecutionMode`, `MarketplaceAccess`, `PLANS_V2` |
| `backend/api/routes/subscription.py` | ~300 | **REFATORAR** | Novos endpoints para SaaS: `/plans`, `/subscribe`, `/usage`, `/upgrade` |
| `backend/api/routes/checkout.py` | ~200 | **DEPRECAR** | Substituir checkout lifetime por checkout subscription |
| `backend/api/services/license.py` | 528 | **REFATORAR** | Converter para `SubscriptionService` com validação de plano |
| `backend/api/routes/license.py` | ~150 | **DEPRECAR** | Manter compatibilidade, redirecionar para subscription |
| `backend/api/middleware/auth.py` | ~100 | **ATUALIZAR** | Adicionar verificação de plano e feature gating |

### 4.2 BACKEND - Média Prioridade 🟡

| Arquivo | Linhas | Mudança | Descrição |
|---------|--------|---------|-----------|
| `backend/api/routes/scraper.py` | ~200 | **ATUALIZAR** | Feature gating por marketplace e plano |
| `backend/integrations/marketplaces/manager.py` | 400 | **ATUALIZAR** | Adicionar verificação de acesso por marketplace |
| `backend/modules/subscription/__init__.py` | N/A | **CRIAR** | Expor `SubscriptionService` e modelos |
| `backend/api/routes/products.py` | ~250 | **ATUALIZAR** | Limitar buscas por plano |
| `backend/workers/scraper_worker.py` | ~150 | **ATUALIZAR** | Prioridade de jobs por plano |

### 4.3 BACKEND - Baixa Prioridade 🟢

| Arquivo | Linhas | Mudança | Descrição |
|---------|--------|---------|-----------|
| `backend/modules/chatbot/` | ~500 | **ATUALIZAR** | Feature gating para chatbot IA |
| `backend/modules/crm/` | ~800 | **ATUALIZAR** | Limite de leads por plano |
| `backend/modules/social_hub/` | ~600 | **ATUALIZAR** | Limite de posts por plano |
| `backend/integrations/whatsapp_hub.py` | ~400 | **ATUALIZAR** | Limite de instâncias/mensagens |

### 4.4 FRONTEND - Alta Prioridade 🔴

| Arquivo | Linhas | Mudança | Descrição |
|---------|--------|---------|-----------|
| `src/stores/userStore.ts` | 207 | **REFATORAR** | Adicionar `subscription`, `plan`, `usage`, `canUseFeature()` |
| `src/pages/Subscription.tsx` | ~300 | **REESCREVER** | Nova UI de planos SaaS com comparativo |
| `src/lib/constants.ts` | ~50 | **ATUALIZAR** | Remover `LICENSE_PRICE`, adicionar `SUBSCRIPTION_PLANS` |
| `src/services/subscription.ts` | N/A | **CRIAR** | Novo service para API de subscriptions |
| `src/services/license.ts` | ~100 | **DEPRECAR** | Manter compatibilidade, usar subscription internamente |

### 4.5 FRONTEND - Média Prioridade 🟡

| Arquivo | Linhas | Mudança | Descrição |
|---------|--------|---------|-----------|
| `src/pages/Products.tsx` | ~400 | **ATUALIZAR** | Mostrar badge de marketplace, verificar acesso |
| `src/pages/Dashboard.tsx` | ~300 | **ATUALIZAR** | Widget de uso do plano |
| `src/pages/Settings.tsx` | ~200 | **ATUALIZAR** | Gerenciar subscription |
| `src/components/UpgradePrompt.tsx` | N/A | **CRIAR** | Modal de upgrade quando atingir limite |
| `src/hooks/useSubscription.ts` | N/A | **CRIAR** | Hook para acessar subscription state |
| `src/hooks/useFeatureGate.ts` | N/A | **CRIAR** | Hook para verificar acesso a features |

### 4.6 TAURI - Alta Prioridade 🔴

| Arquivo | Linhas | Mudança | Descrição |
|---------|--------|---------|-----------|
| `src-tauri/src/commands.rs` | 792 | **REFATORAR** | Substituir `validate_license` por `validate_subscription` |
| `src-tauri/src/database.rs` | 882 | **ATUALIZAR** | Adicionar tabelas `subscription_cache`, `feature_flags` |
| `src-tauri/src/config.rs` | ~100 | **ATUALIZAR** | Configurações de execution mode |

### 4.7 TAURI - Média Prioridade 🟡

| Arquivo | Linhas | Mudança | Descrição |
|---------|--------|---------|-----------|
| `src-tauri/src/scraper/mod.rs` | ~300 | **ATUALIZAR** | Verificar permissão antes de scraping local |
| `src-tauri/src/sync.rs` | N/A | **CRIAR** | Sincronização híbrida (local ↔ cloud) |

### 4.8 DATABASE - Migrations

| Migration | Tipo | Descrição |
|-----------|------|-----------|
| `001_create_subscriptions.sql` | **CRIAR** | Tabela `subscriptions` com plano, status, datas |
| `002_create_usage_records.sql` | **CRIAR** | Tabela `usage_records` para metering |
| `003_add_plan_to_users.sql` | **ATUALIZAR** | Campo `current_plan` em users |
| `004_deprecate_licenses.sql` | **MIGRAR** | Converter licenças ativas em subscriptions |

---

## 5. Roadmap de Implementação

### FASE 1: Fundação (Semana 1-2) 🔴

```
┌─────────────────────────────────────────────────────────────────────┐
│ FASE 1: FUNDAÇÃO                                              2 sem│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ✅ Task 1.1: Novo sistema de planos                                 │
│    📁 backend/modules/subscription/plans.py                         │
│    - Criar ExecutionMode, MarketplaceAccess enums                   │
│    - Criar PlanConfig dataclass                                     │
│    - Definir PLANS_V2 com todos os tiers                           │
│    - Manter PLANS antigo para compatibilidade                       │
│    ⏱️ Estimativa: 4h                                                │
│                                                                     │
│ ✅ Task 1.2: Database migrations                                    │
│    📁 backend/alembic/versions/                                     │
│    - Criar tabela subscriptions                                     │
│    - Criar tabela usage_records                                     │
│    - Adicionar indexes                                              │
│    ⏱️ Estimativa: 2h                                                │
│                                                                     │
│ ✅ Task 1.3: Subscription Service                                   │
│    📁 backend/modules/subscription/service.py                       │
│    - create_subscription()                                          │
│    - get_subscription()                                             │
│    - validate_feature_access()                                      │
│    - record_usage()                                                 │
│    - get_usage_stats()                                              │
│    ⏱️ Estimativa: 6h                                                │
│                                                                     │
│ ✅ Task 1.4: API Routes                                             │
│    📁 backend/api/routes/subscription.py (refatorar)                │
│    - GET /subscription/plans                                        │
│    - GET /subscription/current                                      │
│    - POST /subscription/create                                      │
│    - POST /subscription/upgrade                                     │
│    - POST /subscription/cancel                                      │
│    - GET /subscription/usage                                        │
│    ⏱️ Estimativa: 6h                                                │
│                                                                     │
│ ✅ Task 1.5: Middleware Feature Gating                              │
│    📁 backend/api/middleware/subscription.py                        │
│    - Dependency injection para validar features                     │
│    - Rate limiting por plano                                        │
│    ⏱️ Estimativa: 4h                                                │
│                                                                     │
│ TOTAL FASE 1: 22h (~3 dias úteis)                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### FASE 2: Pagamentos (Semana 2-3) 🔴

```
┌─────────────────────────────────────────────────────────────────────┐
│ FASE 2: INTEGRAÇÃO DE PAGAMENTOS                              2 sem│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ✅ Task 2.1: MercadoPago Subscriptions                              │
│    📁 backend/api/services/mercadopago.py (atualizar)               │
│    - Criar preapproval_plan para cada tier                         │
│    - create_subscription() com plan_id                              │
│    - Tratamento de falha de pagamento                               │
│    ⏱️ Estimativa: 6h                                                │
│                                                                     │
│ ✅ Task 2.2: Webhooks                                               │
│    📁 backend/api/routes/webhooks.py                                │
│    - payment.created → ativar subscription                          │
│    - subscription.cancelled → desativar                             │
│    - payment.failed → notificar, dar grace period                   │
│    ⏱️ Estimativa: 4h                                                │
│                                                                     │
│ ✅ Task 2.3: Upgrade/Downgrade                                      │
│    📁 backend/api/services/subscription.py                          │
│    - Calcular pro-rata em upgrades                                  │
│    - Agendar downgrade para fim do período                          │
│    ⏱️ Estimativa: 4h                                                │
│                                                                     │
│ ✅ Task 2.4: Grace Period                                           │
│    - 3 dias após falha de pagamento                                 │
│    - Emails de notificação                                          │
│    - Downgrade automático para FREE                                 │
│    ⏱️ Estimativa: 3h                                                │
│                                                                     │
│ ✅ Task 2.5: Migrar checkout.py                                     │
│    📁 backend/api/routes/checkout.py                                │
│    - Manter endpoint antigo com deprecation warning                 │
│    - Redirecionar para nova subscription                            │
│    ⏱️ Estimativa: 2h                                                │
│                                                                     │
│ TOTAL FASE 2: 19h (~2.5 dias úteis)                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### FASE 3: Frontend (Semana 3-4) 🟡

```
┌─────────────────────────────────────────────────────────────────────┐
│ FASE 3: FRONTEND SAAS                                          2 sem│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ✅ Task 3.1: Store Refactoring                                      │
│    📁 src/stores/userStore.ts                                       │
│    - Remover license state antigo                                   │
│    - Adicionar subscription state                                   │
│    - Adicionar usage tracking                                       │
│    - Criar canUseFeature() selector                                 │
│    ⏱️ Estimativa: 4h                                                │
│                                                                     │
│ ✅ Task 3.2: Subscription Service                                   │
│    📁 src/services/subscription.ts (criar)                          │
│    - getPlans()                                                     │
│    - getCurrentSubscription()                                       │
│    - subscribe()                                                    │
│    - upgrade()                                                      │
│    - cancel()                                                       │
│    - getUsage()                                                     │
│    ⏱️ Estimativa: 3h                                                │
│                                                                     │
│ ✅ Task 3.3: Hooks                                                  │
│    📁 src/hooks/useSubscription.ts (criar)                          │
│    📁 src/hooks/useFeatureGate.ts (criar)                           │
│    - Acesso fácil ao estado de subscription                         │
│    - Verificação de features inline                                 │
│    ⏱️ Estimativa: 2h                                                │
│                                                                     │
│ ✅ Task 3.4: Página de Planos                                       │
│    📁 src/pages/Subscription.tsx (reescrever)                       │
│    - Grid comparativo de planos                                     │
│    - Toggle mensal/anual                                            │
│    - Highlight do plano atual                                       │
│    - CTAs de upgrade/downgrade                                      │
│    - Badge de economia anual                                        │
│    ⏱️ Estimativa: 8h                                                │
│                                                                     │
│ ✅ Task 3.5: Checkout Modal                                         │
│    📁 src/components/CheckoutModal.tsx                              │
│    - Integração MercadoPago SDK                                     │
│    - Loading states                                                 │
│    - Success/error handling                                         │
│    ⏱️ Estimativa: 4h                                                │
│                                                                     │
│ ✅ Task 3.6: Usage Dashboard                                        │
│    📁 src/components/UsageWidget.tsx                                │
│    - Barras de progresso de uso                                     │
│    - Alertas quando próximo do limite                               │
│    - Link para upgrade                                              │
│    ⏱️ Estimativa: 4h                                                │
│                                                                     │
│ ✅ Task 3.7: Upgrade Prompts                                        │
│    📁 src/components/UpgradePrompt.tsx                              │
│    - Modal quando atingir limite                                    │
│    - Inline prompt em features bloqueadas                           │
│    ⏱️ Estimativa: 3h                                                │
│                                                                     │
│ ✅ Task 3.8: Constants Update                                       │
│    📁 src/lib/constants.ts                                          │
│    - Remover LICENSE_PRICE                                          │
│    - Adicionar SUBSCRIPTION_PLANS                                   │
│    ⏱️ Estimativa: 1h                                                │
│                                                                     │
│ TOTAL FASE 3: 29h (~4 dias úteis)                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### FASE 4: Tauri Desktop (Semana 4-5) 🟡

```
┌─────────────────────────────────────────────────────────────────────┐
│ FASE 4: TAURI HYBRID MODE                                      2 sem│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ✅ Task 4.1: Subscription Commands                                  │
│    📁 src-tauri/src/commands.rs                                     │
│    - validate_subscription() -> SubscriptionState                   │
│    - sync_subscription() -> atualizar cache local                   │
│    - get_cached_subscription() -> offline access                    │
│    ⏱️ Estimativa: 4h                                                │
│                                                                     │
│ ✅ Task 4.2: Database Updates                                       │
│    📁 src-tauri/src/database.rs                                     │
│    - Tabela subscription_cache                                      │
│    - Tabela feature_flags                                           │
│    - Tabela sync_queue                                              │
│    ⏱️ Estimativa: 3h                                                │
│                                                                     │
│ ✅ Task 4.3: Execution Mode Logic                                   │
│    📁 src-tauri/src/config.rs                                       │
│    - Detectar modo baseado no plano                                 │
│    - Feature flags para cada modo                                   │
│    ⏱️ Estimativa: 2h                                                │
│                                                                     │
│ ✅ Task 4.4: Hybrid Sync                                            │
│    📁 src-tauri/src/sync.rs (criar)                                 │
│    - Sync products cloud ↔ local                                    │
│    - Conflict resolution                                            │
│    - Offline queue                                                  │
│    ⏱️ Estimativa: 6h                                                │
│                                                                     │
│ ✅ Task 4.5: Scraper Integration                                    │
│    📁 src-tauri/src/scraper/mod.rs                                  │
│    - Verificar permissão de marketplace                             │
│    - Fallback para cloud se sem permissão                          │
│    ⏱️ Estimativa: 3h                                                │
│                                                                     │
│ ✅ Task 4.6: Offline Grace                                          │
│    - Funcionar offline por X dias (por plano)                       │
│    - Alerta de reconexão necessária                                 │
│    ⏱️ Estimativa: 2h                                                │
│                                                                     │
│ TOTAL FASE 4: 20h (~3 dias úteis)                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### FASE 5: Feature Gating (Semana 5-6) 🟢

```
┌─────────────────────────────────────────────────────────────────────┐
│ FASE 5: FEATURE GATING EM TODOS OS MÓDULOS                    2 sem│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ✅ Task 5.1: Scraper/Products                                       │
│    📁 backend/api/routes/scraper.py                                 │
│    📁 backend/api/routes/products.py                                │
│    - Limitar buscas por plano                                       │
│    - Verificar acesso a marketplace                                 │
│    ⏱️ Estimativa: 3h                                                │
│                                                                     │
│ ✅ Task 5.2: WhatsApp Hub                                           │
│    📁 backend/integrations/whatsapp_hub.py                          │
│    - Limitar instâncias                                             │
│    - Limitar mensagens/mês                                          │
│    ⏱️ Estimativa: 2h                                                │
│                                                                     │
│ ✅ Task 5.3: Chatbot                                                │
│    📁 backend/modules/chatbot/                                      │
│    - Limitar fluxos                                                 │
│    - Gate IA features                                               │
│    ⏱️ Estimativa: 2h                                                │
│                                                                     │
│ ✅ Task 5.4: CRM                                                    │
│    📁 backend/modules/crm/                                          │
│    - Limitar leads                                                  │
│    - Gate automation features                                       │
│    ⏱️ Estimativa: 2h                                                │
│                                                                     │
│ ✅ Task 5.5: Social Hub                                             │
│    📁 backend/modules/social_hub/                                   │
│    - Limitar posts/mês                                              │
│    - Limitar contas conectadas                                      │
│    ⏱️ Estimativa: 2h                                                │
│                                                                     │
│ ✅ Task 5.6: Analytics                                              │
│    📁 backend/modules/analytics/                                    │
│    - Gate advanced analytics                                        │
│    - Gate export features                                           │
│    ⏱️ Estimativa: 2h                                                │
│                                                                     │
│ ✅ Task 5.7: Frontend Feature Gates                                 │
│    - Aplicar useFeatureGate em todas as páginas                     │
│    - Mostrar upgrade prompts apropriados                            │
│    ⏱️ Estimativa: 4h                                                │
│                                                                     │
│ TOTAL FASE 5: 17h (~2 dias úteis)                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### FASE 6: Migração e Testes (Semana 6-7) 🟢

```
┌─────────────────────────────────────────────────────────────────────┐
│ FASE 6: MIGRAÇÃO E TESTES                                      2 sem│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ✅ Task 6.1: Script de Migração                                     │
│    📁 backend/scripts/migrate_to_saas.py                            │
│    - Converter licenças lifetime → subscription BUSINESS (1 ano)    │
│    - Email de notificação para usuários                             │
│    ⏱️ Estimativa: 4h                                                │
│                                                                     │
│ ✅ Task 6.2: Testes Unitários                                       │
│    📁 backend/tests/test_subscription.py                            │
│    📁 tests/unit/subscription.spec.ts                               │
│    ⏱️ Estimativa: 6h                                                │
│                                                                     │
│ ✅ Task 6.3: Testes E2E                                             │
│    📁 tests/e2e/subscription.spec.ts                                │
│    - Fluxo completo de compra                                       │
│    - Upgrade/downgrade                                              │
│    - Feature gating                                                 │
│    ⏱️ Estimativa: 6h                                                │
│                                                                     │
│ ✅ Task 6.4: Documentação                                           │
│    📁 docs/api/subscription.md                                      │
│    📁 docs/product/pricing.md                                       │
│    ⏱️ Estimativa: 4h                                                │
│                                                                     │
│ ✅ Task 6.5: Rollout Plan                                           │
│    - Feature flags para gradual rollout                             │
│    - Monitoramento de erros                                         │
│    - Rollback plan                                                  │
│    ⏱️ Estimativa: 2h                                                │
│                                                                     │
│ TOTAL FASE 6: 22h (~3 dias úteis)                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Especificações Técnicas

### 6.1 Database Schema

```sql
-- backend/alembic/versions/xxx_create_subscriptions.sql

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Plano
    plan_tier VARCHAR(20) NOT NULL DEFAULT 'free',
    billing_cycle VARCHAR(20) NOT NULL DEFAULT 'monthly',
    execution_mode VARCHAR(20) NOT NULL DEFAULT 'web_only',
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    -- active, trialing, past_due, canceled, expired
    
    -- Datas
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    trial_ends_at TIMESTAMPTZ,
    canceled_at TIMESTAMPTZ,
    
    -- Pagamento
    mercadopago_subscription_id VARCHAR(100),
    last_payment_at TIMESTAMPTZ,
    next_payment_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    UNIQUE(user_id)
);

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_period_end ON subscriptions(current_period_end);

CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Feature usage
    feature VARCHAR(50) NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    
    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, feature, period_start)
);

CREATE INDEX idx_usage_user_period ON usage_records(user_id, period_start);
```

### 6.2 API Contracts

```typescript
// src/types/subscription.ts

export interface Plan {
  tier: 'free' | 'starter' | 'business' | 'enterprise';
  name: string;
  description: string;
  priceMonthly: number;
  priceYearly: number;
  executionModes: ExecutionMode[];
  marketplaces: MarketplaceAccess[];
  limits: Record<string, number>;
  features: Record<string, boolean>;
  highlights: string[];
}

export interface Subscription {
  id: string;
  userId: string;
  plan: Plan['tier'];
  billingCycle: 'monthly' | 'yearly';
  executionMode: ExecutionMode;
  status: 'active' | 'trialing' | 'past_due' | 'canceled' | 'expired';
  currentPeriodStart: string;
  currentPeriodEnd: string;
  trialEndsAt?: string;
  canceledAt?: string;
}

export interface UsageStats {
  feature: string;
  current: number;
  limit: number;
  percentage: number;
  resetsAt: string;
}

export type ExecutionMode = 'web_only' | 'hybrid' | 'local_first';

export type MarketplaceAccess = 
  | 'tiktok' 
  | 'shopee' 
  | 'amazon' 
  | 'mercado_livre' 
  | 'hotmart';

// API Endpoints
interface SubscriptionAPI {
  // GET /api/v1/subscription/plans
  getPlans(): Promise<Plan[]>;
  
  // GET /api/v1/subscription/current
  getCurrentSubscription(): Promise<Subscription>;
  
  // POST /api/v1/subscription/create
  createSubscription(data: {
    planTier: Plan['tier'];
    billingCycle: 'monthly' | 'yearly';
  }): Promise<{ checkoutUrl: string }>;
  
  // POST /api/v1/subscription/upgrade
  upgradeSubscription(data: {
    newPlanTier: Plan['tier'];
  }): Promise<{ checkoutUrl: string }>;
  
  // POST /api/v1/subscription/cancel
  cancelSubscription(): Promise<{ canceledAt: string }>;
  
  // GET /api/v1/subscription/usage
  getUsage(): Promise<UsageStats[]>;
  
  // GET /api/v1/subscription/can-use/:feature
  canUseFeature(feature: string): Promise<{ allowed: boolean; limit: number; current: number }>;
}
```

### 6.3 Tauri Commands

```rust
// src-tauri/src/commands.rs

#[derive(Debug, Serialize, Deserialize)]
pub struct SubscriptionState {
    pub plan_tier: String,
    pub execution_mode: String,
    pub status: String,
    pub marketplaces: Vec<String>,
    pub limits: HashMap<String, i32>,
    pub cached_at: String,
    pub valid_until: String,
}

#[tauri::command]
pub async fn validate_subscription(
    hwid: String,
    state: State<'_, AppState>,
) -> Result<SubscriptionState, String> {
    // 1. Check cached subscription
    let cached = get_cached_subscription(&state.db).await?;
    if cached.is_valid() {
        return Ok(cached);
    }
    
    // 2. Validate with cloud
    let client = reqwest::Client::new();
    let response = client
        .post(&format!("{}/api/v1/subscription/validate", API_URL))
        .json(&json!({ "hwid": hwid }))
        .send()
        .await?;
    
    let subscription: SubscriptionState = response.json().await?;
    
    // 3. Cache locally
    cache_subscription(&state.db, &subscription).await?;
    
    Ok(subscription)
}

#[tauri::command]
pub async fn can_use_feature(
    feature: String,
    state: State<'_, AppState>,
) -> Result<bool, String> {
    let subscription = get_cached_subscription(&state.db).await?;
    
    // Check limits
    if let Some(limit) = subscription.limits.get(&feature) {
        if *limit == -1 {
            return Ok(true);  // Unlimited
        }
        
        let usage = get_local_usage(&state.db, &feature).await?;
        return Ok(usage < *limit);
    }
    
    Ok(false)
}

#[tauri::command]
pub async fn get_execution_mode(
    state: State<'_, AppState>,
) -> Result<String, String> {
    let subscription = get_cached_subscription(&state.db).await?;
    Ok(subscription.execution_mode)
}
```

### 6.4 Feature Gating Middleware

```python
# backend/api/middleware/subscription.py

from functools import wraps
from fastapi import Depends, HTTPException, status
from typing import Callable, List, Optional

from backend.modules.subscription.service import SubscriptionService
from backend.modules.subscription.plans import MarketplaceAccess


class FeatureGate:
    """Dependency para verificar acesso a features."""
    
    def __init__(
        self,
        feature: Optional[str] = None,
        marketplaces: Optional[List[MarketplaceAccess]] = None,
        min_plan: Optional[str] = None,
    ):
        self.feature = feature
        self.marketplaces = marketplaces
        self.min_plan = min_plan
        self.subscription_service = SubscriptionService()
    
    async def __call__(self, user_id: str = Depends(get_current_user_id)):
        subscription = await self.subscription_service.get_subscription(user_id)
        
        # Check plan tier
        if self.min_plan:
            plan_order = ['free', 'starter', 'business', 'enterprise']
            if plan_order.index(subscription.plan.value) < plan_order.index(self.min_plan):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "error": "plan_required",
                        "required_plan": self.min_plan,
                        "current_plan": subscription.plan.value,
                        "upgrade_url": "/subscription/upgrade"
                    }
                )
        
        # Check marketplace access
        if self.marketplaces:
            plan_marketplaces = await self.subscription_service.get_marketplace_access(
                subscription.plan
            )
            for mp in self.marketplaces:
                if mp not in plan_marketplaces:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail={
                            "error": "marketplace_not_allowed",
                            "marketplace": mp.value,
                            "upgrade_url": "/subscription/upgrade"
                        }
                    )
        
        # Check feature limit
        if self.feature:
            can_use = await self.subscription_service.can_use_feature(
                user_id, self.feature, increment=1
            )
            if not can_use:
                usage = await self.subscription_service.get_usage(user_id, self.feature)
                limit = await self.subscription_service.get_feature_limit(
                    subscription.plan, self.feature
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "limit_exceeded",
                        "feature": self.feature,
                        "current": usage,
                        "limit": limit,
                        "resets_at": self._get_reset_date(),
                        "upgrade_url": "/subscription/upgrade"
                    }
                )
        
        return subscription


# Usage in routes
@router.get("/products/search")
async def search_products(
    query: str,
    marketplace: MarketplaceAccess,
    subscription: Subscription = Depends(FeatureGate(
        feature="price_searches",
        marketplaces=[MarketplaceAccess.TIKTOK]  # Will check dynamically
    ))
):
    # Feature already validated by middleware
    ...
```

---

## 7. Cronograma e Estimativas

### 7.1 Timeline Visual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CRONOGRAMA - 7 SEMANAS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ SEMANA 1  │████████████████████│ Fase 1: Fundação (22h)                     │
│           │ Plans, DB, Service │                                            │
│           │                    │                                            │
│ SEMANA 2  │████████████████████│ Fase 1 + 2: Fundação + Pagamentos         │
│           │ API, Middleware    │ MercadoPago Subscriptions                  │
│           │                    │                                            │
│ SEMANA 3  │████████████████████│ Fase 2: Pagamentos (19h)                   │
│           │ Webhooks, Upgrade  │                                            │
│           │                    │                                            │
│ SEMANA 4  │████████████████████│ Fase 3: Frontend (29h)                     │
│           │ Store, UI, Hooks   │                                            │
│           │                    │                                            │
│ SEMANA 5  │████████████████████│ Fase 3 + 4: Frontend + Tauri              │
│           │ Checkout, Usage    │ Commands, Database                         │
│           │                    │                                            │
│ SEMANA 6  │████████████████████│ Fase 4 + 5: Tauri + Feature Gating        │
│           │ Sync, Offline      │ All modules                                │
│           │                    │                                            │
│ SEMANA 7  │████████████████████│ Fase 6: Migração + Testes (22h)           │
│           │ Migration, E2E     │ Documentation                              │
│           │                    │                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TOTAL: 129 horas (~16 dias úteis = 3.5 semanas de trabalho efetivo)       │
│  COM BUFFER (30%): ~21 dias úteis = ~5 semanas                              │
│  TIMELINE CONSERVADORA: 7 semanas                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Resumo de Esforço

| Fase | Horas | Dias Úteis | Prioridade |
|------|-------|------------|------------|
| 1. Fundação | 22h | 3 | 🔴 Alta |
| 2. Pagamentos | 19h | 2.5 | 🔴 Alta |
| 3. Frontend | 29h | 4 | 🟡 Média |
| 4. Tauri | 20h | 3 | 🟡 Média |
| 5. Feature Gating | 17h | 2 | 🟢 Baixa |
| 6. Migração | 22h | 3 | 🟢 Baixa |
| **TOTAL** | **129h** | **17.5** | - |

---

## 8. Riscos e Mitigações

### 8.1 Matriz de Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Usuários rejeitam subscription** | Média | Alto | Oferecer 1 ano grátis para licenças vitalícias |
| **MercadoPago muda API** | Baixa | Alto | Abstração da integração, testes automatizados |
| **Performance em feature gating** | Média | Médio | Cache agressivo, Redis para limites |
| **Bugs em sync híbrido** | Alta | Médio | Conflict resolution bem definido, logs extensivos |
| **Downtime durante migração** | Baixa | Alto | Blue-green deployment, feature flags |

### 8.2 Rollback Plan

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ROLLBACK PLAN                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ TRIGGER: Erro crítico em produção OU >10% de falhas em pagamentos  │
│                                                                     │
│ PASSOS:                                                             │
│                                                                     │
│ 1. Desativar feature flag: ENABLE_SAAS_SUBSCRIPTION = false        │
│    - Sistema volta a usar license.py antigo                        │
│                                                                     │
│ 2. Reverter frontend deploy                                         │
│    - Restore de bundle anterior do S3/CDN                          │
│                                                                     │
│ 3. Notificar usuários afetados                                      │
│    - Email automático de "manutenção"                              │
│                                                                     │
│ 4. Analisar root cause                                              │
│    - Logs do Grafana/Prometheus                                    │
│    - Stack traces no Sentry                                        │
│                                                                     │
│ 5. Corrigir e re-deploy                                             │
│    - Novo rollout gradual (10% → 50% → 100%)                       │
│                                                                     │
│ TEMPO ESTIMADO DE ROLLBACK: 15 minutos                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📝 Checklist de Implementação

### Backend
- [ ] Criar `ExecutionMode` e `MarketplaceAccess` enums
- [ ] Criar `PLANS_V2` com nova estrutura
- [ ] Criar migration `subscriptions`
- [ ] Criar migration `usage_records`
- [ ] Implementar `SubscriptionService`
- [ ] Refatorar `/subscription` routes
- [ ] Implementar `FeatureGate` middleware
- [ ] Atualizar MercadoPago integration
- [ ] Implementar webhooks
- [ ] Criar script de migração

### Frontend
- [ ] Refatorar `userStore.ts`
- [ ] Criar `subscription.ts` service
- [ ] Criar `useSubscription` hook
- [ ] Criar `useFeatureGate` hook
- [ ] Redesenhar `Subscription.tsx`
- [ ] Criar `CheckoutModal`
- [ ] Criar `UsageWidget`
- [ ] Criar `UpgradePrompt`
- [ ] Atualizar `constants.ts`

### Tauri
- [ ] Criar `validate_subscription` command
- [ ] Atualizar `database.rs` com novas tabelas
- [ ] Criar `sync.rs` para modo híbrido
- [ ] Atualizar `config.rs` com execution modes
- [ ] Implementar offline grace period

### Testes
- [ ] Testes unitários backend
- [ ] Testes unitários frontend
- [ ] Testes E2E fluxo de compra
- [ ] Testes E2E feature gating
- [ ] Testes de migração

### Deploy
- [ ] Feature flags configurados
- [ ] Monitoramento de métricas
- [ ] Alertas configurados
- [ ] Rollback plan testado
- [ ] Documentação atualizada

---

## 🚀 Próximos Passos

1. **Validar este roadmap** com stakeholders
2. **Priorizar Fase 1** - começar pelo backend foundation
3. **Configurar feature flags** antes de iniciar implementação
4. **Criar issues no GitHub** para cada task

---

**Documento criado:** Dezembro 2024  
**Autor:** GitHub Copilot + TikTrend Finder Team  
**Versão:** 1.0.0
