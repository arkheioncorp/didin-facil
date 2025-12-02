/**
 * useSubscription Hook
 * ====================
 * Hook para acessar e gerenciar o estado da subscription.
 * 
 * Uso:
 * ```tsx
 * const { subscription, plan, usage, isLoading, refresh } = useSubscription();
 * 
 * // Verificar plano
 * if (subscription?.plan === 'business') { ... }
 * 
 * // Verificar feature
 * if (plan?.features.chatbot_ai) { ... }
 * ```
 */

import { useCallback, useEffect, useState } from 'react';
import { useUserStore } from '@/stores/userStore';
import { subscriptionApi } from '@/services/subscription';
import type {
  PlanInfo,
  PlanTier,
  Subscription,
  SubscriptionWithPlan,
  UsageStats,
} from '@/types';

interface UseSubscriptionReturn {
  // Data
  subscription: Subscription | null;
  plan: PlanInfo | null;
  usage: UsageStats[];
  
  // State
  isLoading: boolean;
  error: string | null;
  
  // Computed
  isActive: boolean;
  isPaid: boolean;
  isFree: boolean;
  planTier: PlanTier | null;
  
  // Actions
  refresh: () => Promise<void>;
  upgrade: (newPlan: PlanTier) => Promise<string | null>;
  cancel: () => Promise<boolean>;
}

export function useSubscription(): UseSubscriptionReturn {
  const { user } = useUserStore();
  
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [plan, setPlan] = useState<PlanInfo | null>(null);
  const [usage, setUsage] = useState<UsageStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch subscription data
  const refresh = useCallback(async () => {
    if (!user) {
      setSubscription(null);
      setPlan(null);
      setUsage([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data: SubscriptionWithPlan = await subscriptionApi.getCurrentSubscription();
      setSubscription(data.subscription);
      setPlan(data.plan);
      setUsage(data.usage);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao carregar subscription';
      setError(message);
      console.error('[useSubscription] Error:', err);
      
      // Fallback para plano FREE
      setSubscription({
        id: 'free',
        plan: 'free',
        status: 'active',
        billingCycle: 'monthly',
        executionMode: 'web_only',
        currentPeriodStart: new Date().toISOString(),
        currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        marketplaces: ['tiktok'],
        limits: {},
        features: {},
      });
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  // Upgrade subscription
  const upgrade = useCallback(async (newPlan: PlanTier): Promise<string | null> => {
    try {
      const result = await subscriptionApi.upgradeSubscription(newPlan);
      
      if (result.status === 'redirect' && result.checkoutUrl) {
        return result.checkoutUrl;
      }
      
      // Upgrade direto (modo dev)
      await refresh();
      return null;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao fazer upgrade';
      setError(message);
      throw err;
    }
  }, [refresh]);

  // Cancel subscription
  const cancel = useCallback(async (): Promise<boolean> => {
    try {
      await subscriptionApi.cancelSubscription();
      await refresh();
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao cancelar';
      setError(message);
      return false;
    }
  }, [refresh]);

  // Load on mount and when user changes
  useEffect(() => {
    refresh();
  }, [refresh]);

  // Computed values
  const isActive = subscription?.status === 'active' || subscription?.status === 'trialing';
  const isPaid = subscription?.plan !== 'free';
  const isFree = subscription?.plan === 'free';
  const planTier = subscription?.plan ?? null;

  return {
    subscription,
    plan,
    usage,
    isLoading,
    error,
    isActive,
    isPaid,
    isFree,
    planTier,
    refresh,
    upgrade,
    cancel,
  };
}

/**
 * Hook simplificado para verificar plano mínimo.
 * 
 * Uso:
 * ```tsx
 * const hasAccess = usePlanAccess('starter');
 * ```
 */
export function usePlanAccess(minPlan: PlanTier): boolean {
  const { subscription } = useSubscription();
  
  if (!subscription) return false;
  
  return subscriptionApi.isPlanSuperior(subscription.plan, minPlan) || 
         subscription.plan === minPlan;
}

/**
 * Hook para verificar acesso a marketplace.
 * 
 * Uso:
 * ```tsx
 * const hasShopee = useMarketplaceAccess('shopee');
 * ```
 */
export function useMarketplaceAccess(marketplace: string): boolean {
  const { subscription } = useSubscription();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return subscription?.marketplaces?.includes(marketplace as unknown as MarketplaceAccess) ?? false;
}

export default useSubscription;
