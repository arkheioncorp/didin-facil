# 📋 Mapeamento Detalhado de Mudanças - SaaS Híbrido

> Este documento complementa o SAAS_HYBRID_ROADMAP.md com especificações técnicas detalhadas para cada arquivo.

---

## 🔴 PRIORIDADE ALTA - Backend

### 1. `backend/modules/subscription/plans.py`

**Status:** REFATORAR (513 → ~800 linhas)

**Mudanças Específicas:**

```python
# ADICIONAR: Novos enums (linhas ~25-50)
class ExecutionMode(str, Enum):
    WEB_ONLY = "web_only"
    HYBRID = "hybrid"
    LOCAL_FIRST = "local_first"

class MarketplaceAccess(str, Enum):
    TIKTOK = "tiktok"
    SHOPEE = "shopee"
    AMAZON = "amazon"
    MERCADO_LIVRE = "mercado_livre"
    HOTMART = "hotmart"
    ALIEXPRESS = "aliexpress"

# ADICIONAR: Novo dataclass (linhas ~60-100)
@dataclass
class PlanConfig:
    tier: PlanTier
    name: str
    description: str
    price_monthly: Decimal
    price_yearly: Decimal
    execution_modes: list[ExecutionMode]
    marketplaces: list[MarketplaceAccess]
    scraper_priority: int
    limits: dict[str, int]
    features: dict[str, bool]
    highlights: list[str]

# MANTER: PLANS dict original (compatibilidade)
# ADICIONAR: PLANS_V2 com nova estrutura (linhas ~200-400)
PLANS_V2: dict[PlanTier, PlanConfig] = {
    PlanTier.FREE: PlanConfig(...),
    PlanTier.STARTER: PlanConfig(...),
    PlanTier.BUSINESS: PlanConfig(...),
    PlanTier.ENTERPRISE: PlanConfig(...),
}

# ATUALIZAR: SubscriptionService (linhas ~350-513)
# - Adicionar get_marketplace_access()
# - Adicionar get_execution_mode()
# - Atualizar can_use_feature() para PLANS_V2
```

---

### 2. `backend/api/routes/subscription.py`

**Status:** REFATORAR (~300 linhas)

**Endpoints Atuais → Novos:**

| Atual | Novo | Ação |
|-------|------|------|
| GET /plans | GET /plans | Retornar PLANS_V2 |
| - | GET /current | Subscription do usuário |
| - | POST /create | Criar subscription (MercadoPago) |
| - | POST /upgrade | Upgrade de plano |
| - | POST /downgrade | Agendar downgrade |
| - | POST /cancel | Cancelar (manter até fim período) |
| - | GET /usage | Stats de uso |
| - | GET /usage/:feature | Uso específico |
| - | POST /validate | Validar subscription (Tauri) |

**Código Novo:**

```python
@router.get("/current")
async def get_current_subscription(
    user_id: str = Depends(get_current_user_id),
    service: SubscriptionService = Depends()
):
    """Retorna subscription atual do usuário."""
    subscription = await service.get_subscription(user_id)
    plan_config = PLANS_V2[subscription.plan]
    
    return {
        "subscription": subscription.dict(),
        "plan": {
            "tier": plan_config.tier.value,
            "name": plan_config.name,
            "execution_modes": [m.value for m in plan_config.execution_modes],
            "marketplaces": [m.value for m in plan_config.marketplaces],
            "limits": plan_config.limits,
            "features": plan_config.features,
        },
        "usage": await service.get_all_usage(user_id)
    }

@router.post("/create")
async def create_subscription(
    data: CreateSubscriptionRequest,
    user_id: str = Depends(get_current_user_id),
    mercadopago: MercadoPagoService = Depends(),
    service: SubscriptionService = Depends()
):
    """Cria nova subscription."""
    plan_config = PLANS_V2[PlanTier(data.plan_tier)]
    
    # Criar no MercadoPago
    price = plan_config.price_yearly if data.billing_cycle == "yearly" else plan_config.price_monthly
    
    checkout = await mercadopago.create_subscription(
        user_id=user_id,
        plan_name=plan_config.name,
        price=float(price),
        billing_cycle=data.billing_cycle
    )
    
    return {"checkout_url": checkout.init_point}
```

---

### 3. `backend/api/services/license.py`

**Status:** DEPRECAR + WRAPPER (528 linhas)

**Estratégia:** Manter API externa idêntica, redirecionar para SubscriptionService internamente.

```python
# ANTES
async def validate_license(hwid: str, license_key: str) -> LicenseValidation:
    # Lógica de validação de licença...

# DEPOIS
async def validate_license(hwid: str, license_key: str) -> LicenseValidation:
    """
    DEPRECATED: Use validate_subscription() instead.
    Mantido para compatibilidade com Tauri < v2.0
    """
    import warnings
    warnings.warn("validate_license is deprecated, use validate_subscription", DeprecationWarning)
    
    # Buscar usuário pela license_key (ou criar se não existir)
    user = await get_user_by_license(license_key)
    
    # Validar subscription do usuário
    subscription_service = SubscriptionService()
    subscription = await subscription_service.get_subscription(user.id)
    
    # Converter para formato de LicenseValidation (compatibilidade)
    return LicenseValidation(
        is_valid=subscription.status == "active",
        license_key=license_key,
        tier=subscription.plan.value,  # free, starter, business
        expires_at=subscription.current_period_end,
        features=PLANS_V2[subscription.plan].features,
        # ...
    )
```

---

### 4. `backend/api/routes/checkout.py`

**Status:** DEPRECAR (~200 linhas)

**Mudanças:**

```python
# MANTER: PRODUCTS dict com deprecation warning
PRODUCTS = {
    "tiktrend_lifetime": {
        "name": "TikTrend Lifetime (LEGACY)",
        "price": 49.90,
        "deprecated": True,
        "redirect_to": "/subscription"
    },
    # Credit packs podem ser mantidos
    "credits_100": {...},
    "credits_500": {...},
}

@router.post("/create")
async def create_checkout(request: CheckoutRequest):
    product = PRODUCTS.get(request.product_id)
    
    if product.get("deprecated"):
        return JSONResponse(
            status_code=301,
            content={
                "message": "Este produto foi descontinuado. Use a página de assinaturas.",
                "redirect_url": "/subscription"
            }
        )
    
    # Continuar com créditos normalmente
    ...
```

---

### 5. `backend/api/middleware/subscription.py` (NOVO)

**Status:** CRIAR (~150 linhas)

```python
"""
Middleware de Feature Gating para Subscription SaaS.
"""

from fastapi import Depends, HTTPException, status
from typing import List, Optional

from backend.modules.subscription.plans import (
    PlanTier, MarketplaceAccess, PLANS_V2
)
from backend.modules.subscription.service import SubscriptionService


class RequiresPlan:
    """Dependency que verifica plano mínimo."""
    
    def __init__(self, min_plan: PlanTier):
        self.min_plan = min_plan
        self.plan_order = [PlanTier.FREE, PlanTier.STARTER, PlanTier.BUSINESS, PlanTier.ENTERPRISE]
    
    async def __call__(self, user_id: str = Depends(get_current_user_id)):
        service = SubscriptionService()
        subscription = await service.get_subscription(user_id)
        
        current_idx = self.plan_order.index(subscription.plan)
        required_idx = self.plan_order.index(self.min_plan)
        
        if current_idx < required_idx:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "upgrade_required",
                    "current_plan": subscription.plan.value,
                    "required_plan": self.min_plan.value,
                    "upgrade_url": "/subscription/upgrade"
                }
            )
        
        return subscription


class RequiresMarketplace:
    """Dependency que verifica acesso a marketplace."""
    
    def __init__(self, marketplace: MarketplaceAccess):
        self.marketplace = marketplace
    
    async def __call__(self, user_id: str = Depends(get_current_user_id)):
        service = SubscriptionService()
        subscription = await service.get_subscription(user_id)
        plan_config = PLANS_V2[subscription.plan]
        
        if self.marketplace not in plan_config.marketplaces:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "marketplace_not_included",
                    "marketplace": self.marketplace.value,
                    "available_in": ["starter", "business"],
                    "upgrade_url": "/subscription/upgrade"
                }
            )
        
        return subscription


class RequiresFeature:
    """Dependency que verifica limite de feature."""
    
    def __init__(self, feature: str, increment: int = 1):
        self.feature = feature
        self.increment = increment
    
    async def __call__(self, user_id: str = Depends(get_current_user_id)):
        service = SubscriptionService()
        
        can_use = await service.can_use_feature(
            user_id, 
            self.feature, 
            increment=self.increment
        )
        
        if not can_use:
            subscription = await service.get_subscription(user_id)
            plan_config = PLANS_V2[subscription.plan]
            current_usage = await service.get_usage(user_id, self.feature)
            limit = plan_config.limits.get(self.feature, 0)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "limit_exceeded",
                    "feature": self.feature,
                    "current": current_usage,
                    "limit": limit,
                    "resets_at": get_period_end().isoformat(),
                    "upgrade_url": "/subscription/upgrade"
                }
            )
        
        return True


# Uso em routes:
@router.get("/search")
async def search_products(
    query: str,
    marketplace: str,
    _plan: Subscription = Depends(RequiresPlan(PlanTier.FREE)),
    _marketplace: Subscription = Depends(RequiresMarketplace(MarketplaceAccess(marketplace))),
    _feature: bool = Depends(RequiresFeature("price_searches")),
):
    # Já validado pelo middleware
    ...
```

---

## 🔴 PRIORIDADE ALTA - Frontend

### 6. `src/stores/userStore.ts`

**Status:** REFATORAR (207 → ~350 linhas)

**Mudanças:**

```typescript
// REMOVER ou DEPRECAR
interface License {
  isValid: boolean;
  expiresAt: string | null;
  tier: string;
  // ...
}

const DEFAULT_LICENSE: License = {...}

// ADICIONAR
interface Subscription {
  id: string;
  userId: string;
  plan: 'free' | 'starter' | 'business' | 'enterprise';
  billingCycle: 'monthly' | 'yearly';
  executionMode: 'web_only' | 'hybrid' | 'local_first';
  status: 'active' | 'trialing' | 'past_due' | 'canceled' | 'expired';
  currentPeriodStart: string;
  currentPeriodEnd: string;
  marketplaces: string[];
  limits: Record<string, number>;
  features: Record<string, boolean>;
}

interface UsageStats {
  feature: string;
  current: number;
  limit: number;
  percentage: number;
}

interface UserState {
  user: User | null;
  subscription: Subscription | null;  // NOVO
  usage: UsageStats[];                 // NOVO
  isLoading: boolean;
  error: string | null;
}

// ADICIONAR: Actions
const useUserStore = create<UserState & Actions>()(
  persist(
    (set, get) => ({
      // ... existing state
      
      subscription: null,
      usage: [],
      
      // NOVO: Fetch subscription
      fetchSubscription: async () => {
        const response = await subscriptionApi.getCurrent();
        set({ 
          subscription: response.subscription,
          usage: response.usage
        });
      },
      
      // NOVO: Check feature access
      canUseFeature: (feature: string): boolean => {
        const { subscription, usage } = get();
        if (!subscription) return false;
        
        const limit = subscription.limits[feature];
        if (limit === -1) return true;
        
        const usageItem = usage.find(u => u.feature === feature);
        return !usageItem || usageItem.current < limit;
      },
      
      // NOVO: Check marketplace access
      hasMarketplaceAccess: (marketplace: string): boolean => {
        const { subscription } = get();
        if (!subscription) return false;
        return subscription.marketplaces.includes(marketplace);
      },
      
      // NOVO: Get usage percentage
      getUsagePercentage: (feature: string): number => {
        const { usage } = get();
        const usageItem = usage.find(u => u.feature === feature);
        return usageItem?.percentage ?? 0;
      },
    }),
    {
      name: 'user-storage',
      partialize: (state) => ({
        user: state.user,
        subscription: state.subscription,
        // NÃO persistir usage (sempre buscar fresh)
      }),
    }
  )
);
```

---

### 7. `src/pages/Subscription.tsx`

**Status:** REESCREVER (~300 → ~500 linhas)

**Layout Novo:**

```tsx
// Estrutura do componente
export default function SubscriptionPage() {
  const { subscription, usage } = useUserStore();
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  
  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header com plano atual */}
      <CurrentPlanBanner subscription={subscription} />
      
      {/* Toggle mensal/anual */}
      <BillingToggle value={billingCycle} onChange={setBillingCycle} />
      
      {/* Grid de planos */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
        {PLANS.map(plan => (
          <PlanCard
            key={plan.tier}
            plan={plan}
            billingCycle={billingCycle}
            isCurrentPlan={subscription?.plan === plan.tier}
            onSelect={() => setSelectedPlan(plan.tier)}
          />
        ))}
      </div>
      
      {/* Widget de uso atual */}
      <UsageWidget usage={usage} subscription={subscription} />
      
      {/* Modal de checkout */}
      <CheckoutModal
        isOpen={!!selectedPlan}
        plan={selectedPlan}
        onClose={() => setSelectedPlan(null)}
      />
    </div>
  );
}

// Subcomponentes
function PlanCard({ plan, billingCycle, isCurrentPlan, onSelect }) {
  const price = billingCycle === 'yearly' 
    ? plan.priceYearly / 12 
    : plan.priceMonthly;
  
  const savings = billingCycle === 'yearly' 
    ? ((plan.priceMonthly * 12 - plan.priceYearly) / (plan.priceMonthly * 12) * 100).toFixed(0)
    : 0;
  
  return (
    <div className={cn(
      "rounded-xl border p-6 relative",
      isCurrentPlan && "border-primary-500 bg-primary-50",
      plan.tier === 'business' && "ring-2 ring-primary-500" // Highlight recommended
    )}>
      {plan.tier === 'business' && (
        <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">
          Mais Popular
        </Badge>
      )}
      
      <h3 className="text-xl font-bold">{plan.name}</h3>
      <p className="text-gray-600 mt-1">{plan.description}</p>
      
      <div className="mt-4">
        <span className="text-4xl font-bold">R$ {price.toFixed(2)}</span>
        <span className="text-gray-600">/mês</span>
        {billingCycle === 'yearly' && (
          <Badge variant="success" className="ml-2">
            -{savings}%
          </Badge>
        )}
      </div>
      
      {/* Marketplaces */}
      <div className="flex gap-2 mt-4">
        {plan.marketplaces.map(mp => (
          <MarketplaceIcon key={mp} marketplace={mp} />
        ))}
      </div>
      
      {/* Features */}
      <ul className="mt-6 space-y-2">
        {plan.highlights.map((h, i) => (
          <li key={i} className="flex items-center gap-2">
            {h.startsWith('✓') ? <CheckIcon /> : <XIcon />}
            <span>{h.replace(/^[✓✗]\s*/, '')}</span>
          </li>
        ))}
      </ul>
      
      <Button
        className="w-full mt-6"
        variant={isCurrentPlan ? "outline" : "primary"}
        onClick={onSelect}
        disabled={isCurrentPlan}
      >
        {isCurrentPlan ? 'Plano Atual' : 'Assinar'}
      </Button>
    </div>
  );
}
```

---

### 8. `src/services/subscription.ts` (NOVO)

**Status:** CRIAR (~150 linhas)

```typescript
import { api } from './api';

export interface Plan {
  tier: 'free' | 'starter' | 'business' | 'enterprise';
  name: string;
  description: string;
  priceMonthly: number;
  priceYearly: number;
  executionModes: string[];
  marketplaces: string[];
  limits: Record<string, number>;
  features: Record<string, boolean>;
  highlights: string[];
}

export interface Subscription {
  id: string;
  userId: string;
  plan: Plan['tier'];
  billingCycle: 'monthly' | 'yearly';
  executionMode: string;
  status: string;
  currentPeriodStart: string;
  currentPeriodEnd: string;
}

export interface UsageStats {
  feature: string;
  current: number;
  limit: number;
  percentage: number;
  resetsAt: string;
}

export const subscriptionApi = {
  /**
   * Lista todos os planos disponíveis
   */
  async getPlans(): Promise<Plan[]> {
    const response = await api.get('/subscription/plans');
    return response.data;
  },
  
  /**
   * Obtém subscription atual do usuário
   */
  async getCurrent(): Promise<{
    subscription: Subscription;
    plan: Plan;
    usage: UsageStats[];
  }> {
    const response = await api.get('/subscription/current');
    return response.data;
  },
  
  /**
   * Cria nova subscription
   */
  async create(data: {
    planTier: Plan['tier'];
    billingCycle: 'monthly' | 'yearly';
  }): Promise<{ checkoutUrl: string }> {
    const response = await api.post('/subscription/create', data);
    return response.data;
  },
  
  /**
   * Upgrade de plano
   */
  async upgrade(newPlanTier: Plan['tier']): Promise<{ checkoutUrl: string }> {
    const response = await api.post('/subscription/upgrade', { newPlanTier });
    return response.data;
  },
  
  /**
   * Cancela subscription
   */
  async cancel(): Promise<{ canceledAt: string }> {
    const response = await api.post('/subscription/cancel');
    return response.data;
  },
  
  /**
   * Obtém estatísticas de uso
   */
  async getUsage(): Promise<UsageStats[]> {
    const response = await api.get('/subscription/usage');
    return response.data;
  },
  
  /**
   * Verifica se pode usar uma feature
   */
  async canUseFeature(feature: string): Promise<{
    allowed: boolean;
    limit: number;
    current: number;
  }> {
    const response = await api.get(`/subscription/can-use/${feature}`);
    return response.data;
  },
};
```

---

### 9. `src/hooks/useFeatureGate.ts` (NOVO)

**Status:** CRIAR (~50 linhas)

```typescript
import { useUserStore } from '@/stores/userStore';
import { useCallback, useMemo } from 'react';

interface FeatureGateResult {
  allowed: boolean;
  limit: number;
  current: number;
  percentage: number;
  isNearLimit: boolean;  // > 80%
  isAtLimit: boolean;    // >= 100%
  upgradeRequired: boolean;
}

/**
 * Hook para verificar acesso a features baseado no plano
 * 
 * @example
 * const { allowed, isNearLimit } = useFeatureGate('price_searches');
 * 
 * if (!allowed) {
 *   return <UpgradePrompt feature="price_searches" />;
 * }
 */
export function useFeatureGate(feature: string): FeatureGateResult {
  const { subscription, usage, canUseFeature } = useUserStore();
  
  const result = useMemo(() => {
    if (!subscription) {
      return {
        allowed: false,
        limit: 0,
        current: 0,
        percentage: 0,
        isNearLimit: false,
        isAtLimit: true,
        upgradeRequired: true,
      };
    }
    
    const limit = subscription.limits[feature] ?? 0;
    const usageItem = usage.find(u => u.feature === feature);
    const current = usageItem?.current ?? 0;
    
    const percentage = limit === -1 ? 0 : (current / limit) * 100;
    const isUnlimited = limit === -1;
    
    return {
      allowed: isUnlimited || current < limit,
      limit: isUnlimited ? Infinity : limit,
      current,
      percentage,
      isNearLimit: !isUnlimited && percentage >= 80,
      isAtLimit: !isUnlimited && current >= limit,
      upgradeRequired: !isUnlimited && current >= limit,
    };
  }, [subscription, usage, feature]);
  
  return result;
}

/**
 * Hook para verificar acesso a marketplace
 */
export function useMarketplaceAccess(marketplace: string): boolean {
  const { subscription } = useUserStore();
  return subscription?.marketplaces.includes(marketplace) ?? false;
}
```

---

## 🔴 PRIORIDADE ALTA - Tauri

### 10. `src-tauri/src/commands.rs`

**Status:** REFATORAR (792 → ~900 linhas)

**Mudanças Principais:**

```rust
// ADICIONAR: Estruturas novas (após linha ~50)
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SubscriptionState {
    pub plan_tier: String,
    pub execution_mode: String,
    pub status: String,
    pub marketplaces: Vec<String>,
    pub limits: HashMap<String, i32>,  // -1 = unlimited
    pub features: HashMap<String, bool>,
    pub current_period_end: String,
    pub cached_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct FeatureCheckResult {
    pub allowed: bool,
    pub current: i32,
    pub limit: i32,
    pub message: Option<String>,
}

// ADICIONAR: Novos commands (após validate_license)

#[tauri::command]
pub async fn validate_subscription(
    hwid: String,
    state: State<'_, AppState>,
) -> Result<SubscriptionState, String> {
    // 1. Verificar cache local primeiro
    let cached = get_cached_subscription(&state.db).await?;
    
    if cached.is_some() && is_cache_valid(&cached.as_ref().unwrap()) {
        return Ok(cached.unwrap());
    }
    
    // 2. Validar com cloud
    let client = reqwest::Client::new();
    let response = client
        .post(&format!("{}/api/v1/subscription/validate", get_api_url()))
        .json(&serde_json::json!({
            "hwid": hwid,
            "app_version": env!("CARGO_PKG_VERSION")
        }))
        .timeout(std::time::Duration::from_secs(10))
        .send()
        .await
        .map_err(|e| format!("Network error: {}", e))?;
    
    if !response.status().is_success() {
        // Offline mode: usar cache mesmo expirado (grace period)
        if let Some(c) = cached {
            if is_within_grace_period(&c) {
                return Ok(c);
            }
        }
        return Err("Subscription validation failed".to_string());
    }
    
    let subscription: SubscriptionState = response
        .json()
        .await
        .map_err(|e| format!("Parse error: {}", e))?;
    
    // 3. Salvar no cache local
    cache_subscription(&state.db, &subscription).await?;
    
    Ok(subscription)
}

#[tauri::command]
pub async fn can_use_feature(
    feature: String,
    state: State<'_, AppState>,
) -> Result<FeatureCheckResult, String> {
    let subscription = get_cached_subscription(&state.db)
        .await?
        .ok_or("No subscription cached")?;
    
    // Verificar limite
    let limit = subscription.limits.get(&feature).copied().unwrap_or(0);
    
    if limit == -1 {
        return Ok(FeatureCheckResult {
            allowed: true,
            current: 0,
            limit: -1,
            message: None,
        });
    }
    
    let current = get_local_usage(&state.db, &feature).await?;
    
    Ok(FeatureCheckResult {
        allowed: current < limit,
        current,
        limit,
        message: if current >= limit {
            Some(format!("Limite de {} atingido. Faça upgrade para continuar.", feature))
        } else {
            None
        },
    })
}

#[tauri::command]
pub async fn get_execution_mode(
    state: State<'_, AppState>,
) -> Result<String, String> {
    let subscription = get_cached_subscription(&state.db)
        .await?
        .ok_or("No subscription cached")?;
    
    Ok(subscription.execution_mode)
}

#[tauri::command]
pub async fn has_marketplace_access(
    marketplace: String,
    state: State<'_, AppState>,
) -> Result<bool, String> {
    let subscription = get_cached_subscription(&state.db)
        .await?
        .ok_or("No subscription cached")?;
    
    Ok(subscription.marketplaces.contains(&marketplace))
}

#[tauri::command]
pub async fn increment_local_usage(
    feature: String,
    amount: i32,
    state: State<'_, AppState>,
) -> Result<i32, String> {
    let conn = state.db.lock().await;
    
    sqlx::query(
        "INSERT INTO local_usage (feature, count, period_start)
         VALUES (?, ?, date('now', 'start of month'))
         ON CONFLICT(feature, period_start) DO UPDATE SET count = count + ?"
    )
    .bind(&feature)
    .bind(amount)
    .bind(amount)
    .execute(&*conn)
    .await
    .map_err(|e| e.to_string())?;
    
    get_local_usage(&*conn, &feature).await
}

// MANTER: validate_license (com deprecation warning no log)
#[tauri::command]
pub async fn validate_license(
    hwid: String,
    license_key: String,
    state: State<'_, AppState>,
) -> Result<LicenseValidation, String> {
    log::warn!("validate_license is deprecated, use validate_subscription");
    
    // Wrapper que chama validate_subscription internamente
    let subscription = validate_subscription(hwid, state).await?;
    
    // Converter para formato antigo (compatibilidade)
    Ok(LicenseValidation {
        is_valid: subscription.status == "active",
        tier: subscription.plan_tier,
        expires_at: subscription.current_period_end,
        // ...
    })
}
```

---

### 11. `src-tauri/src/database.rs`

**Status:** ATUALIZAR (882 → ~950 linhas)

**Mudanças:**

```rust
// ADICIONAR: Novas tabelas no init_database() (após linha ~50)

pub async fn init_database(db_path: &str) -> Result<SqlitePool, String> {
    // ... existing code ...
    
    // NOVO: Tabela de cache de subscription
    sqlx::query(
        "CREATE TABLE IF NOT EXISTS subscription_cache (
            id INTEGER PRIMARY KEY,
            plan_tier TEXT NOT NULL,
            execution_mode TEXT NOT NULL,
            status TEXT NOT NULL,
            marketplaces TEXT NOT NULL,  -- JSON array
            limits TEXT NOT NULL,         -- JSON object
            features TEXT NOT NULL,       -- JSON object
            current_period_end TEXT NOT NULL,
            cached_at TEXT NOT NULL,
            UNIQUE(id)
        )"
    )
    .execute(&pool)
    .await
    .map_err(|e| e.to_string())?;
    
    // NOVO: Tabela de uso local
    sqlx::query(
        "CREATE TABLE IF NOT EXISTS local_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            period_start TEXT NOT NULL,  -- YYYY-MM-01
            UNIQUE(feature, period_start)
        )"
    )
    .execute(&pool)
    .await
    .map_err(|e| e.to_string())?;
    
    // NOVO: Tabela de sync queue (para modo híbrido)
    sqlx::query(
        "CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,      -- 'create', 'update', 'delete'
            entity_type TEXT NOT NULL, -- 'product', 'favorite', 'alert'
            entity_id TEXT NOT NULL,
            payload TEXT NOT NULL,     -- JSON
            created_at TEXT NOT NULL,
            synced_at TEXT,
            retry_count INTEGER DEFAULT 0
        )"
    )
    .execute(&pool)
    .await
    .map_err(|e| e.to_string())?;
    
    Ok(pool)
}

// ADICIONAR: Funções auxiliares

pub async fn cache_subscription(
    pool: &SqlitePool,
    subscription: &SubscriptionState,
) -> Result<(), String> {
    sqlx::query(
        "INSERT OR REPLACE INTO subscription_cache 
         (id, plan_tier, execution_mode, status, marketplaces, limits, features, current_period_end, cached_at)
         VALUES (1, ?, ?, ?, ?, ?, ?, ?, datetime('now'))"
    )
    .bind(&subscription.plan_tier)
    .bind(&subscription.execution_mode)
    .bind(&subscription.status)
    .bind(serde_json::to_string(&subscription.marketplaces).unwrap())
    .bind(serde_json::to_string(&subscription.limits).unwrap())
    .bind(serde_json::to_string(&subscription.features).unwrap())
    .bind(&subscription.current_period_end)
    .execute(pool)
    .await
    .map_err(|e| e.to_string())?;
    
    Ok(())
}

pub async fn get_cached_subscription(
    pool: &SqlitePool,
) -> Result<Option<SubscriptionState>, String> {
    let row = sqlx::query_as::<_, (String, String, String, String, String, String, String, String)>(
        "SELECT plan_tier, execution_mode, status, marketplaces, limits, features, current_period_end, cached_at
         FROM subscription_cache WHERE id = 1"
    )
    .fetch_optional(pool)
    .await
    .map_err(|e| e.to_string())?;
    
    match row {
        Some((plan_tier, execution_mode, status, marketplaces, limits, features, period_end, cached_at)) => {
            Ok(Some(SubscriptionState {
                plan_tier,
                execution_mode,
                status,
                marketplaces: serde_json::from_str(&marketplaces).unwrap_or_default(),
                limits: serde_json::from_str(&limits).unwrap_or_default(),
                features: serde_json::from_str(&features).unwrap_or_default(),
                current_period_end: period_end,
                cached_at,
            }))
        }
        None => Ok(None),
    }
}

pub async fn get_local_usage(
    pool: &SqlitePool,
    feature: &str,
) -> Result<i32, String> {
    let row = sqlx::query_scalar::<_, i32>(
        "SELECT COALESCE(count, 0) FROM local_usage 
         WHERE feature = ? AND period_start = date('now', 'start of month')"
    )
    .bind(feature)
    .fetch_optional(pool)
    .await
    .map_err(|e| e.to_string())?;
    
    Ok(row.unwrap_or(0))
}
```

---

## 🗄️ Database Migrations

### 12. `backend/alembic/versions/001_create_subscriptions.py`

**Status:** CRIAR

```python
"""Create subscriptions table

Revision ID: 001_subscriptions
Create Date: 2024-12-XX
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '001_subscriptions'
down_revision = None  # ou a última migration
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'subscriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        
        # Plano
        sa.Column('plan_tier', sa.String(20), nullable=False, server_default='free'),
        sa.Column('billing_cycle', sa.String(20), nullable=False, server_default='monthly'),
        sa.Column('execution_mode', sa.String(20), nullable=False, server_default='web_only'),
        
        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        
        # Datas
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True)),
        sa.Column('canceled_at', sa.DateTime(timezone=True)),
        
        # Pagamento
        sa.Column('mercadopago_subscription_id', sa.String(100)),
        sa.Column('last_payment_at', sa.DateTime(timezone=True)),
        sa.Column('next_payment_at', sa.DateTime(timezone=True)),
        
        # Metadata
        sa.Column('metadata', JSONB, server_default='{}'),
    )
    
    # Indexes
    op.create_index('idx_subscriptions_user', 'subscriptions', ['user_id'], unique=True)
    op.create_index('idx_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('idx_subscriptions_period_end', 'subscriptions', ['current_period_end'])
    op.create_index('idx_subscriptions_mp_id', 'subscriptions', ['mercadopago_subscription_id'])


def downgrade():
    op.drop_table('subscriptions')
```

### 13. `backend/alembic/versions/002_create_usage_records.py`

**Status:** CRIAR

```python
"""Create usage_records table

Revision ID: 002_usage_records
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '002_usage_records'
down_revision = '001_subscriptions'


def upgrade():
    op.create_table(
        'usage_records',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('feature', sa.String(50), nullable=False),
        sa.Column('count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        
        sa.UniqueConstraint('user_id', 'feature', 'period_start', name='uq_usage_user_feature_period'),
    )
    
    op.create_index('idx_usage_user_period', 'usage_records', ['user_id', 'period_start'])
    op.create_index('idx_usage_feature', 'usage_records', ['feature'])


def downgrade():
    op.drop_table('usage_records')
```

---

## 📊 Resumo de Arquivos

| Prioridade | Arquivo | Ação | Complexidade |
|------------|---------|------|--------------|
| 🔴 | `backend/modules/subscription/plans.py` | REFATORAR | Alta |
| 🔴 | `backend/api/routes/subscription.py` | REFATORAR | Alta |
| 🔴 | `backend/api/services/license.py` | DEPRECAR | Média |
| 🔴 | `backend/api/routes/checkout.py` | DEPRECAR | Baixa |
| 🔴 | `backend/api/middleware/subscription.py` | CRIAR | Média |
| 🔴 | `src/stores/userStore.ts` | REFATORAR | Alta |
| 🔴 | `src/pages/Subscription.tsx` | REESCREVER | Alta |
| 🔴 | `src/services/subscription.ts` | CRIAR | Média |
| 🔴 | `src/hooks/useFeatureGate.ts` | CRIAR | Baixa |
| 🔴 | `src-tauri/src/commands.rs` | REFATORAR | Alta |
| 🔴 | `src-tauri/src/database.rs` | ATUALIZAR | Média |
| 🟡 | `backend/api/routes/scraper.py` | ATUALIZAR | Baixa |
| 🟡 | `backend/integrations/whatsapp_hub.py` | ATUALIZAR | Baixa |
| 🟡 | `backend/modules/chatbot/` | ATUALIZAR | Baixa |
| 🟡 | `backend/modules/crm/` | ATUALIZAR | Baixa |
| 🟢 | Migrations | CRIAR | Média |
| 🟢 | Testes | CRIAR | Média |

---

**Total de arquivos a modificar:** 25-30 arquivos
**Linhas de código estimadas:** ~4.000 novas/modificadas
