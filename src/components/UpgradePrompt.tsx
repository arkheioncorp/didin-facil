/**
 * UpgradePrompt Component
 * =======================
 * Modal/Banner para solicitar upgrade quando usuário atinge limite.
 * 
 * Uso:
 * ```tsx
 * <UpgradePrompt 
 *   feature="price_searches" 
 *   onClose={() => {}} 
 * />
 * 
 * // Ou como modal
 * <UpgradePromptModal 
 *   open={showModal}
 *   feature="chatbot_ai"
 *   onClose={() => setShowModal(false)}
 * />
 * ```
 */

import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Zap, 
  Crown, 
  Rocket, 
  ArrowRight,
  X,
  Lock,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSubscription } from "@/hooks/useSubscription";
import { useFeatureGate, getFeatureDisplayName } from "@/hooks/useFeatureGate";
import { formatPrice } from "@/services/subscription";
import type { PlanTier } from "@/types";

// ============================================
// TYPES
// ============================================

interface UpgradePromptProps {
  feature: string;
  variant?: 'inline' | 'card' | 'banner';
  showClose?: boolean;
  onClose?: () => void;
  className?: string;
}

interface UpgradePromptModalProps {
  open: boolean;
  feature: string;
  onClose: () => void;
}

// ============================================
// CONSTANTS
// ============================================

const PLAN_RECOMMENDATIONS: Record<string, PlanTier> = {
  // Free -> Starter
  price_searches: 'starter',
  price_alerts: 'starter',
  favorites: 'starter',
  social_posts: 'starter',
  social_accounts: 'starter',
  whatsapp_instances: 'starter',
  whatsapp_messages: 'starter',
  chatbot_flows: 'starter',
  crm_leads: 'starter',
  api_calls: 'starter',
  analytics_advanced: 'starter',
  offline_mode: 'starter',
  hybrid_sync: 'starter',
  api_access: 'starter',
  
  // Starter -> Business
  chatbot_ai: 'business',
  crm_automation: 'business',
  analytics_export: 'business',
  support_priority: 'business',
  support_phone: 'business',
};

const PLAN_ICONS: Record<PlanTier, React.ReactNode> = {
  free: <Zap className="w-5 h-5" />,
  starter: <Rocket className="w-5 h-5" />,
  business: <Crown className="w-5 h-5" />,
  enterprise: <Crown className="w-5 h-5" />,
};

const PLAN_PRICES: Record<PlanTier, number> = {
  free: 0,
  starter: 97,
  business: 297,
  enterprise: 0,
};

// ============================================
// INLINE COMPONENT
// ============================================

export const UpgradePrompt: React.FC<UpgradePromptProps> = ({
  feature,
  variant = 'inline',
  showClose = false,
  onClose,
  className,
}) => {
  const navigate = useNavigate();
  
  const recommendedPlan = PLAN_RECOMMENDATIONS[feature] || 'starter';
  const featureName = getFeatureDisplayName(feature);
  
  const handleUpgrade = () => {
    navigate('/subscription');
  };

  if (variant === 'inline') {
    return (
      <div className={cn(
        "flex items-center gap-3 p-3 rounded-lg bg-amber-50 border border-amber-200 dark:bg-amber-900/20 dark:border-amber-800",
        className
      )}>
        <Lock className="w-4 h-4 text-amber-600 flex-shrink-0" />
        <p className="text-sm text-amber-800 dark:text-amber-200 flex-1">
          <strong>{featureName}</strong> requer upgrade para o plano{' '}
          <span className="font-semibold capitalize">{recommendedPlan}</span>.
        </p>
        <Button size="sm" variant="default" onClick={handleUpgrade}>
          Upgrade
        </Button>
        {showClose && onClose && (
          <Button size="icon" variant="ghost" className="h-6 w-6" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        )}
      </div>
    );
  }

  if (variant === 'card') {
    return (
      <Card className={cn("border-amber-200 bg-amber-50 dark:bg-amber-900/20", className)}>
        <CardContent className="py-4">
          <div className="flex items-center gap-4">
            <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-800">
              {PLAN_ICONS[recommendedPlan]}
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-amber-900 dark:text-amber-100">
                Upgrade para desbloquear {featureName}
              </h4>
              <p className="text-sm text-amber-700 dark:text-amber-300">
                Disponível a partir do plano {recommendedPlan.charAt(0).toUpperCase() + recommendedPlan.slice(1)} 
                {PLAN_PRICES[recommendedPlan] > 0 && ` por ${formatPrice(PLAN_PRICES[recommendedPlan])}/mês`}
              </p>
            </div>
            <Button onClick={handleUpgrade}>
              Ver Planos
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Banner variant
  return (
    <div className={cn(
      "relative overflow-hidden rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 p-6 text-white",
      className
    )}>
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/10 rounded-full translate-y-1/2 -translate-x-1/2" />
      
      <div className="relative flex flex-col md:flex-row items-center gap-6">
        <div className="flex-1 text-center md:text-left">
          <Badge variant="secondary" className="mb-3 bg-white/20 text-white border-none">
            Recurso Premium
          </Badge>
          <h3 className="text-2xl font-bold mb-2">
            Desbloqueie {featureName}
          </h3>
          <p className="text-white/80 max-w-md">
            Faça upgrade para o plano {recommendedPlan.charAt(0).toUpperCase() + recommendedPlan.slice(1)} e tenha acesso a recursos avançados para impulsionar suas vendas.
          </p>
        </div>
        <div className="flex flex-col items-center gap-2">
          {PLAN_PRICES[recommendedPlan] > 0 && (
            <div className="text-center">
              <span className="text-3xl font-bold">{formatPrice(PLAN_PRICES[recommendedPlan])}</span>
              <span className="text-white/80">/mês</span>
            </div>
          )}
          <Button size="lg" variant="secondary" onClick={handleUpgrade}>
            Ver Planos
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </div>
      
      {showClose && onClose && (
        <Button 
          size="icon" 
          variant="ghost" 
          className="absolute top-2 right-2 text-white hover:bg-white/20" 
          onClick={onClose}
        >
          <X className="w-5 h-5" />
        </Button>
      )}
    </div>
  );
};

// ============================================
// MODAL COMPONENT
// ============================================

export const UpgradePromptModal: React.FC<UpgradePromptModalProps> = ({
  open,
  feature,
  onClose,
}) => {
  const navigate = useNavigate();
  const { subscription } = useSubscription();
  
  const recommendedPlan = PLAN_RECOMMENDATIONS[feature] || 'starter';
  const featureName = getFeatureDisplayName(feature);
  const currentPlan = subscription?.plan || 'free';
  
  const handleUpgrade = () => {
    onClose();
    navigate('/subscription');
  };

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md" data-testid="upgrade-prompt-modal">
        <DialogHeader>
          <div className="mx-auto p-3 rounded-full bg-amber-100 dark:bg-amber-900 mb-4">
            <Lock className="w-6 h-6 text-amber-600" />
          </div>
          <DialogTitle className="text-center">
            Limite Atingido
          </DialogTitle>
          <DialogDescription className="text-center">
            <strong className="text-foreground">{featureName}</strong> não está incluído no seu plano atual.
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <div className="flex items-center justify-between p-4 rounded-lg bg-muted">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-background">
                {PLAN_ICONS[currentPlan as PlanTier]}
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Plano atual</p>
                <p className="font-semibold capitalize">{currentPlan}</p>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-muted-foreground" />
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                {PLAN_ICONS[recommendedPlan]}
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Recomendado</p>
                <p className="font-semibold capitalize">{recommendedPlan}</p>
              </div>
            </div>
          </div>
          
          {PLAN_PRICES[recommendedPlan] > 0 && (
            <p className="text-center text-sm text-muted-foreground mt-4">
              A partir de <strong>{formatPrice(PLAN_PRICES[recommendedPlan])}/mês</strong>
            </p>
          )}
        </div>
        
        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button variant="outline" onClick={onClose} className="w-full sm:w-auto">
            Agora não
          </Button>
          <Button onClick={handleUpgrade} className="w-full sm:w-auto">
            Ver Planos
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// ============================================
// FEATURE GATE WRAPPER
// ============================================

interface FeatureGateProps {
  feature: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * Wrapper component that shows upgrade prompt if feature is not available.
 * 
 * ```tsx
 * <FeatureGate feature="chatbot_ai">
 *   <ChatbotEditor />
 * </FeatureGate>
 * ```
 */
export const FeatureGate: React.FC<FeatureGateProps> = ({
  feature,
  children,
  fallback,
}) => {
  const { allowed } = useFeatureGate(feature);
  
  if (!allowed) {
    return fallback || <UpgradePrompt feature={feature} variant="card" />;
  }
  
  return <>{children}</>;
};

export default UpgradePrompt;
