/**
 * useFeatureGate Hook
 * ====================
 * Hook para verificar acesso a features baseado no plano.
 * 
 * Uso:
 * ```tsx
 * const { allowed, isNearLimit, isAtLimit, current, limit } = useFeatureGate('price_searches');
 * 
 * if (!allowed) {
 *   return <UpgradePrompt feature="price_searches" />;
 * }
 * 
 * // Ou use o componente wrapper
 * <FeatureGate feature="chatbot_ai" fallback={<UpgradePrompt />}>
 *   <ChatbotEditor />
 * </FeatureGate>
 * ```
 */

import { useCallback, useMemo } from 'react';
import { useSubscription } from './useSubscription';
import type { UsageStats } from '@/types';

// ============================================
// TYPES
// ============================================

interface FeatureGateResult {
  // Access
  allowed: boolean;
  
  // Usage (for metered features)
  current: number;
  limit: number;
  remaining: number;
  percentage: number;
  
  // Status
  isUnlimited: boolean;
  isNearLimit: boolean;   // > 80%
  isAtLimit: boolean;     // >= 100%
  
  // Meta
  feature: string;
  upgradeRequired: boolean;
  resetsAt: string | null;
}

interface FeatureGateOptions {
  /** Incrementar uso se permitido */
  increment?: number;
  /** Fallback se feature não existir */
  defaultAllowed?: boolean;
}

// ============================================
// HOOK
// ============================================

/**
 * Hook para verificar acesso a features baseado no plano.
 * 
 * Suporta:
 * - Features booleanas (chatbot_ai, analytics_export, etc.)
 * - Features com limite numérico (price_searches, whatsapp_messages, etc.)
 * 
 * @param feature Nome da feature
 * @param options Opções adicionais
 */
export function useFeatureGate(
  feature: string,
  options: FeatureGateOptions = {}
): FeatureGateResult {
  const { subscription, plan, usage } = useSubscription();
  const { defaultAllowed = false } = options;

  const result = useMemo((): FeatureGateResult => {
    // Default result
    const defaultResult: FeatureGateResult = {
      allowed: defaultAllowed,
      current: 0,
      limit: 0,
      remaining: 0,
      percentage: 0,
      isUnlimited: false,
      isNearLimit: false,
      isAtLimit: false,
      feature,
      upgradeRequired: !defaultAllowed,
      resetsAt: null,
    };

    if (!subscription || !plan) {
      return defaultResult;
    }

    // Check boolean features first
    if (feature in plan.features) {
      const isEnabled = plan.features[feature];
      return {
        ...defaultResult,
        allowed: isEnabled,
        isUnlimited: true,
        upgradeRequired: !isEnabled,
      };
    }

    // Check metered features (limits)
    if (feature in plan.limits) {
      const limit = plan.limits[feature];
      const usageItem = usage.find(u => u.feature === feature);
      const current = usageItem?.current ?? 0;
      
      const isUnlimited = limit === -1;
      const remaining = isUnlimited ? Infinity : Math.max(0, limit - current);
      const percentage = isUnlimited ? 0 : (limit > 0 ? (current / limit) * 100 : 0);
      
      const allowed = isUnlimited || current < limit;
      const isNearLimit = !isUnlimited && percentage >= 80;
      const isAtLimit = !isUnlimited && percentage >= 100;

      return {
        allowed,
        current,
        limit,
        remaining,
        percentage: Math.min(100, percentage),
        isUnlimited,
        isNearLimit,
        isAtLimit,
        feature,
        upgradeRequired: !allowed,
        resetsAt: usageItem?.resetsAt ?? null,
      };
    }

    // Feature not found in plan
    return defaultResult;
  }, [subscription, plan, usage, feature, defaultAllowed]);

  return result;
}

/**
 * Hook para verificar múltiplas features de uma vez.
 * 
 * Uso:
 * ```tsx
 * const gates = useMultiFeatureGate(['chatbot_ai', 'crm_automation']);
 * const allAllowed = gates.every(g => g.allowed);
 * ```
 */
export function useMultiFeatureGate(features: string[]): FeatureGateResult[] {
  const { subscription, plan, usage } = useSubscription();
  
  return useMemo(() => {
    return features.map(feature => {
      const defaultResult: FeatureGateResult = {
        allowed: false,
        current: 0,
        limit: 0,
        remaining: 0,
        percentage: 0,
        isUnlimited: false,
        isNearLimit: false,
        isAtLimit: false,
        feature,
        upgradeRequired: true,
        resetsAt: null,
      };

      if (!subscription || !plan) return defaultResult;

      if (feature in plan.features) {
        const isEnabled = plan.features[feature];
        return { ...defaultResult, allowed: isEnabled, isUnlimited: true, upgradeRequired: !isEnabled };
      }

      if (feature in plan.limits) {
        const limit = plan.limits[feature];
        const usageItem = usage.find(u => u.feature === feature);
        const current = usageItem?.current ?? 0;
        const isUnlimited = limit === -1;
        const remaining = isUnlimited ? Infinity : Math.max(0, limit - current);
        const percentage = isUnlimited ? 0 : (limit > 0 ? (current / limit) * 100 : 0);
        const allowed = isUnlimited || current < limit;

        return {
          ...defaultResult,
          allowed,
          current,
          limit,
          remaining,
          percentage: Math.min(100, percentage),
          isUnlimited,
          isNearLimit: !isUnlimited && percentage >= 80,
          isAtLimit: !isUnlimited && percentage >= 100,
          upgradeRequired: !allowed,
          resetsAt: usageItem?.resetsAt ?? null,
        };
      }

      return defaultResult;
    });
  }, [subscription, plan, usage, features]);
}

/**
 * Hook para verificar uso geral e alertas.
 */
export function useUsageAlerts(): {
  nearLimitFeatures: UsageStats[];
  atLimitFeatures: UsageStats[];
  hasAlerts: boolean;
} {
  const { usage } = useSubscription();

  return useMemo(() => {
    const nearLimitFeatures = usage.filter(u => 
      !u.isUnlimited && u.percentage >= 80 && u.percentage < 100
    );
    const atLimitFeatures = usage.filter(u => 
      !u.isUnlimited && u.percentage >= 100
    );

    return {
      nearLimitFeatures,
      atLimitFeatures,
      hasAlerts: nearLimitFeatures.length > 0 || atLimitFeatures.length > 0,
    };
  }, [usage]);
}

/**
 * Hook para executar ação com verificação de feature.
 * 
 * Uso:
 * ```tsx
 * const { execute, canExecute } = useFeatureAction('price_searches');
 * 
 * const handleSearch = () => {
 *   if (!execute()) {
 *     showUpgradeModal();
 *     return;
 *   }
 *   // Fazer busca...
 * };
 * ```
 */
export function useFeatureAction(feature: string): {
  canExecute: boolean;
  execute: () => boolean;
  gate: FeatureGateResult;
} {
  const gate = useFeatureGate(feature);

  const execute = useCallback((): boolean => {
    if (!gate.allowed) {
      return false;
    }
    // TODO: Incrementar uso via API
    return true;
  }, [gate.allowed]);

  return {
    canExecute: gate.allowed,
    execute,
    gate,
  };
}

// ============================================
// FEATURE NAMES (for display)
// ============================================

export const FEATURE_DISPLAY_NAMES: Record<string, string> = {
  // Comparador
  price_searches: 'Buscas de preço',
  price_alerts: 'Alertas de preço',
  favorites: 'Produtos favoritos',
  
  // Social Media
  social_posts: 'Posts agendados',
  social_accounts: 'Contas conectadas',
  
  // WhatsApp
  whatsapp_instances: 'Instâncias WhatsApp',
  whatsapp_messages: 'Mensagens WhatsApp',
  
  // Chatbot
  chatbot_flows: 'Fluxos de chatbot',
  chatbot_ai: 'Chatbot com IA',
  
  // CRM
  crm_leads: 'Leads no CRM',
  crm_automation: 'Automação de vendas',
  
  // Analytics
  analytics_basic: 'Analytics básico',
  analytics_advanced: 'Analytics avançado',
  analytics_export: 'Exportar relatórios',
  
  // API
  api_calls: 'Chamadas de API',
  api_access: 'Acesso à API',
  
  // Suporte
  support_email: 'Suporte por email',
  support_priority: 'Suporte prioritário',
  support_phone: 'Suporte por telefone',
  
  // Execution
  offline_mode: 'Modo offline',
  hybrid_sync: 'Sincronização híbrida',
};

export function getFeatureDisplayName(feature: string): string {
  return FEATURE_DISPLAY_NAMES[feature] ?? feature;
}

export default useFeatureGate;
