/**
 * Subscription Service - SaaS Híbrido
 * =====================================
 * API client para gerenciamento de assinaturas e planos.
 * 
 * Endpoints:
 * - GET /subscription/plans - Lista planos
 * - GET /subscription/current - Subscription atual
 * - POST /subscription/create - Criar subscription
 * - POST /subscription/upgrade - Upgrade de plano
 * - POST /subscription/downgrade - Agendar downgrade
 * - POST /subscription/cancel - Cancelar subscription
 * - GET /subscription/usage - Estatísticas de uso
 * - POST /subscription/validate - Validar (Tauri)
 * - POST /subscription/set-mode - Definir modo de execução
 */

import { api } from "@/lib/api";
import type {
  BillingCycle,
  ExecutionMode,
  PlanInfo,
  PlanTier,
  Subscription,
  SubscriptionWithPlan,
  UsageStats,
} from "@/types";

// ============================================
// RESPONSE TYPES
// ============================================

interface CheckoutResponse {
  status: 'redirect' | 'success';
  checkoutUrl?: string;
  preferenceId?: string;
  plan?: PlanTier;
  price?: number;
  message?: string;
  subscription?: Partial<Subscription>;
}

interface UpgradeResponse extends CheckoutResponse {
  fromPlan?: PlanTier;
  toPlan?: PlanTier;
}

interface DowngradeResponse {
  status: 'scheduled';
  message: string;
  currentPlan: PlanTier;
  newPlan: PlanTier;
  effectiveAt: string;
}

interface CancelResponse {
  status: 'canceled';
  message: string;
  accessUntil: string;
}

interface ExecutionModeResponse {
  currentMode: ExecutionMode;
  availableModes: ExecutionMode[];
}

interface SetModeResponse {
  status: 'success';
  executionMode: ExecutionMode;
}

interface FeatureCheckResponse {
  feature: string;
  canUse: boolean;
  current: number;
  limit: number;
  percentage: number;
  isUnlimited: boolean;
}

interface ValidateSubscriptionResponse {
  isValid: boolean;
  planTier: PlanTier;
  executionMode: ExecutionMode;
  status: string;
  marketplaces: string[];
  limits: Record<string, number>;
  features: Record<string, boolean>;
  currentPeriodEnd: string;
  offlineDays: number;
  gracePeriodDays: number;
  cachedAt: string;
  reason?: string;
  message?: string;
}

// ============================================
// API FUNCTIONS
// ============================================

/**
 * Lista todos os planos disponíveis.
 */
export async function getPlans(): Promise<PlanInfo[]> {
  const response = await api.get<PlanInfo[]>("/subscription/plans");
  return response.data;
}

/**
 * Obtém detalhes de um plano específico.
 */
export async function getPlanDetails(tier: PlanTier): Promise<PlanInfo> {
  const response = await api.get<PlanInfo>(`/subscription/plans/${tier}`);
  return response.data;
}

/**
 * Obtém subscription atual do usuário com plano e uso.
 */
export async function getCurrentSubscription(): Promise<SubscriptionWithPlan> {
  const response = await api.get<SubscriptionWithPlan>("/subscription/current");
  return response.data;
}

/**
 * Obtém apenas a subscription (sem detalhes do plano).
 */
export async function getSubscription(): Promise<Subscription> {
  const response = await api.get<Subscription>("/subscription/subscription");
  return response.data;
}

/**
 * Obtém estatísticas de uso de todas as features.
 */
export async function getUsageStats(): Promise<UsageStats[]> {
  const response = await api.get<UsageStats[]>("/subscription/usage");
  return response.data;
}

/**
 * Obtém uso de uma feature específica.
 */
export async function getFeatureUsage(feature: string): Promise<FeatureCheckResponse> {
  const response = await api.get<FeatureCheckResponse>(`/subscription/usage/${feature}`);
  return response.data;
}

/**
 * Verifica se pode usar uma feature.
 */
export async function checkFeatureAccess(feature: string): Promise<{ feature: string; canUse: boolean }> {
  const response = await api.post<{ feature: string; canUse: boolean }>(
    "/subscription/check-feature",
    null,
    { params: { feature } }
  );
  return response.data;
}

/**
 * Cria nova subscription (redireciona para checkout).
 */
export async function createSubscription(
  planTier: PlanTier,
  billingCycle: BillingCycle = 'monthly'
): Promise<CheckoutResponse> {
  const response = await api.post<CheckoutResponse>("/subscription/create", {
    plan_tier: planTier,
    billing_cycle: billingCycle,
  });
  return response.data;
}

/**
 * Faz upgrade do plano.
 */
export async function upgradeSubscription(
  newPlan: PlanTier,
  billingCycle?: BillingCycle
): Promise<UpgradeResponse> {
  const response = await api.post<UpgradeResponse>("/subscription/upgrade", {
    plan: newPlan,
    billing_cycle: billingCycle,
  });
  return response.data;
}

/**
 * Agenda downgrade para o final do período.
 */
export async function downgradeSubscription(newPlan: PlanTier): Promise<DowngradeResponse> {
  const response = await api.post<DowngradeResponse>("/subscription/downgrade", {
    plan: newPlan,
  });
  return response.data;
}

/**
 * Cancela subscription (mantém até o final do período).
 */
export async function cancelSubscription(): Promise<CancelResponse> {
  const response = await api.post<CancelResponse>("/subscription/cancel");
  return response.data;
}

/**
 * Obtém modo de execução atual.
 */
export async function getExecutionMode(): Promise<ExecutionModeResponse> {
  const response = await api.get<ExecutionModeResponse>("/subscription/execution-mode");
  return response.data;
}

/**
 * Define modo de execução (se suportado pelo plano).
 */
export async function setExecutionMode(mode: ExecutionMode): Promise<SetModeResponse> {
  const response = await api.post<SetModeResponse>("/subscription/set-mode", {
    mode,
  });
  return response.data;
}

/**
 * Valida subscription para app Tauri (retorna dados para cache local).
 */
export async function validateSubscription(hwid: string, appVersion?: string): Promise<ValidateSubscriptionResponse> {
  const response = await api.post<ValidateSubscriptionResponse>("/subscription/validate", {
    hwid,
    app_version: appVersion,
  });
  return response.data;
}

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Calcula preço com desconto anual.
 */
export function calculateYearlySavings(priceMonthly: number, priceYearly: number): {
  savingsPercent: number;
  savingsAmount: number;
  monthlyEquivalent: number;
} {
  const yearlyFull = priceMonthly * 12;
  const savingsAmount = yearlyFull - priceYearly;
  const savingsPercent = (savingsAmount / yearlyFull) * 100;
  const monthlyEquivalent = priceYearly / 12;

  return {
    savingsPercent: Math.round(savingsPercent),
    savingsAmount,
    monthlyEquivalent,
  };
}

/**
 * Formata preço em BRL.
 */
export function formatPrice(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
}

/**
 * Verifica se plano é superior a outro.
 */
export function isPlanSuperior(planA: PlanTier, planB: PlanTier): boolean {
  const order: PlanTier[] = ['free', 'starter', 'business', 'enterprise'];
  return order.indexOf(planA) > order.indexOf(planB);
}

/**
 * Obtém nome amigável do plano.
 */
export function getPlanDisplayName(tier: PlanTier): string {
  const names: Record<PlanTier, string> = {
    free: 'Free',
    starter: 'Starter',
    business: 'Business',
    enterprise: 'Enterprise',
  };
  return names[tier];
}

/**
 * Obtém cor do plano para badges.
 */
export function getPlanColor(tier: PlanTier): string {
  const colors: Record<PlanTier, string> = {
    free: 'bg-gray-100 text-gray-800',
    starter: 'bg-blue-100 text-blue-800',
    business: 'bg-purple-100 text-purple-800',
    enterprise: 'bg-amber-100 text-amber-800',
  };
  return colors[tier];
}

/**
 * Verifica se feature está próxima do limite (>80%).
 */
export function isNearLimit(usage: UsageStats): boolean {
  return !usage.isUnlimited && usage.percentage >= 80;
}

/**
 * Verifica se feature atingiu o limite.
 */
export function isAtLimit(usage: UsageStats): boolean {
  return !usage.isUnlimited && usage.percentage >= 100;
}

// ============================================
// EXPORT DEFAULT OBJECT
// ============================================

export const subscriptionApi = {
  // Plans
  getPlans,
  getPlanDetails,
  
  // Subscription
  getCurrentSubscription,
  getSubscription,
  createSubscription,
  upgradeSubscription,
  downgradeSubscription,
  cancelSubscription,
  
  // Usage
  getUsageStats,
  getFeatureUsage,
  checkFeatureAccess,
  
  // Execution Mode
  getExecutionMode,
  setExecutionMode,
  
  // Validation
  validateSubscription,
  
  // Helpers
  calculateYearlySavings,
  formatPrice,
  isPlanSuperior,
  getPlanDisplayName,
  getPlanColor,
  isNearLimit,
  isAtLimit,
};

export default subscriptionApi;
