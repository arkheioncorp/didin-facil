/**
 * Subscription Page - SaaS Híbrido
 * =================================
 * Página de planos e assinatura com:
 * - Grid comparativo de planos
 * - Toggle mensal/anual
 * - Destaque do plano atual
 * - Dashboard de uso
 * - Checkout MercadoPago
 */

import React from "react";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { 
  Check, 
  X, 
  Zap, 
  Crown, 
  Building2, 
  Rocket,
  AlertTriangle,
  TrendingUp,
  MessageSquare,
  BarChart3,
  Globe,
  Bot,
  Users,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSubscription } from "@/hooks/useSubscription";
import { useUsageAlerts, getFeatureDisplayName } from "@/hooks/useFeatureGate";
import { 
  subscriptionApi, 
  formatPrice, 
  calculateYearlySavings,
  getPlanColor,
} from "@/services/subscription";
import type { PlanInfo, PlanTier, BillingCycle, UsageStats, Subscription as SubscriptionType } from "@/types";

// ============================================
// CONSTANTS
// ============================================

const PLAN_ICONS: Record<PlanTier, React.ReactNode> = {
  free: <Zap className="w-6 h-6" />,
  starter: <Rocket className="w-6 h-6" />,
  business: <Crown className="w-6 h-6" />,
  enterprise: <Building2 className="w-6 h-6" />,
};

const MARKETPLACE_LABELS: Record<string, string> = {
  tiktok: "TikTok Shop",
  shopee: "Shopee",
  amazon: "Amazon",
  mercado_livre: "Mercado Livre",
  hotmart: "Hotmart",
  aliexpress: "AliExpress",
};

// ============================================
// MAIN COMPONENT
// ============================================

export const Subscription: React.FC = () => {
  const { subscription, plan, usage, isLoading, upgrade, cancel } = useSubscription();
  const { nearLimitFeatures, atLimitFeatures, hasAlerts } = useUsageAlerts();
  
  const [billingCycle, setBillingCycle] = React.useState<BillingCycle>('monthly');
  const [plans, setPlans] = React.useState<PlanInfo[]>([]);
  const [plansLoading, setPlansLoading] = React.useState(true);
  const [processingPlan, setProcessingPlan] = React.useState<PlanTier | null>(null);
  const [showCancelDialog, setShowCancelDialog] = React.useState(false);

  // Load plans
  React.useEffect(() => {
    async function loadPlans() {
      try {
        const data = await subscriptionApi.getPlans();
        setPlans(data);
      } catch (err) {
        console.error("Error loading plans:", err);
      } finally {
        setPlansLoading(false);
      }
    }
    loadPlans();
  }, []);

  // Handle plan selection
  const handleSelectPlan = async (tier: PlanTier) => {
    if (tier === 'enterprise') {
      // Redirect to contact
      window.open('mailto:contato@didin.com.br?subject=Interesse no Plano Enterprise', '_blank');
      return;
    }

    if (tier === subscription?.plan) return;

    setProcessingPlan(tier);
    try {
      const checkoutUrl = await upgrade(tier);
      if (checkoutUrl) {
        window.location.href = checkoutUrl;
      }
    } catch (err) {
      console.error("Error upgrading:", err);
    } finally {
      setProcessingPlan(null);
    }
  };

  // Handle cancel
  const handleCancel = async () => {
    const success = await cancel();
    if (success) {
      setShowCancelDialog(false);
    }
  };

  if (isLoading || plansLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 p-4 py-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
            Escolha seu Plano
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Desbloqueie todo o potencial do Didin Fácil com recursos avançados de comparação de preços, automação e muito mais.
          </p>
        </div>

        {/* Current Plan Status */}
        {subscription && (
          <CurrentPlanCard 
            subscription={subscription} 
            plan={plan}
            onCancel={() => setShowCancelDialog(true)}
          />
        )}

        {/* Usage Alerts */}
        {hasAlerts && (
          <UsageAlerts 
            nearLimit={nearLimitFeatures} 
            atLimit={atLimitFeatures} 
          />
        )}

        {/* Billing Toggle */}
        <div className="flex items-center justify-center gap-4">
          <Label 
            htmlFor="billing-toggle" 
            className={cn(
              "text-sm font-medium cursor-pointer",
              billingCycle === 'monthly' ? 'text-foreground' : 'text-muted-foreground'
            )}
          >
            Mensal
          </Label>
          <Switch
            id="billing-toggle"
            checked={billingCycle === 'yearly'}
            onCheckedChange={(checked) => setBillingCycle(checked ? 'yearly' : 'monthly')}
          />
          <Label 
            htmlFor="billing-toggle"
            className={cn(
              "text-sm font-medium cursor-pointer flex items-center gap-2",
              billingCycle === 'yearly' ? 'text-foreground' : 'text-muted-foreground'
            )}
          >
            Anual
            <Badge variant="secondary" className="bg-green-100 text-green-700">
              2 meses grátis
            </Badge>
          </Label>
        </div>

        {/* Plans Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((planInfo) => (
            <PlanCard
              key={planInfo.tier}
              plan={planInfo}
              billingCycle={billingCycle}
              isCurrentPlan={subscription?.plan === planInfo.tier}
              isProcessing={processingPlan === planInfo.tier}
              onSelect={() => handleSelectPlan(planInfo.tier)}
            />
          ))}
        </div>

        {/* Usage Dashboard */}
        {usage.length > 0 && (
          <UsageDashboard usage={usage} />
        )}

        {/* Features Comparison */}
        <FeaturesComparison plans={plans} currentPlan={subscription?.plan} />

        {/* FAQ */}
        <FAQ />

        {/* Cancel Dialog */}
        <AlertDialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Cancelar Assinatura?</AlertDialogTitle>
              <AlertDialogDescription>
                Você continuará tendo acesso até o final do período atual 
                ({subscription?.currentPeriodEnd ? new Date(subscription.currentPeriodEnd).toLocaleDateString('pt-BR') : ''}).
                Após isso, será rebaixado para o plano Free.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Manter Assinatura</AlertDialogCancel>
              <AlertDialogAction onClick={handleCancel} className="bg-destructive text-destructive-foreground">
                Confirmar Cancelamento
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
};

// ============================================
// SUB-COMPONENTS
// ============================================

interface CurrentPlanCardProps {
  subscription: SubscriptionType;
  plan: PlanInfo | null;
  onCancel: () => void;
}

const CurrentPlanCard: React.FC<CurrentPlanCardProps> = ({ subscription, plan, onCancel }) => {
  const isActive = subscription.status === 'active' || subscription.status === 'trialing';
  const isCanceled = subscription.status === 'canceled';
  
  return (
    <Card className="border-primary/50 bg-primary/5">
      <CardContent className="py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className={cn("p-2 rounded-lg", getPlanColor(subscription.plan))}>
              {PLAN_ICONS[subscription.plan as PlanTier]}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold">Plano {plan?.name || subscription.plan}</h3>
                <Badge variant={isActive ? "default" : "secondary"}>
                  {isActive ? 'Ativo' : isCanceled ? 'Cancelado' : subscription.status}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                {isCanceled 
                  ? `Acesso até ${new Date(subscription.currentPeriodEnd).toLocaleDateString('pt-BR')}`
                  : subscription.billingCycle === 'yearly' ? 'Cobrança anual' : 'Cobrança mensal'
                }
              </p>
            </div>
          </div>
          
          {subscription.plan !== 'free' && !isCanceled && (
            <Button variant="ghost" size="sm" onClick={onCancel}>
              Cancelar assinatura
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

interface PlanCardProps {
  plan: PlanInfo;
  billingCycle: BillingCycle;
  isCurrentPlan: boolean;
  isProcessing: boolean;
  onSelect: () => void;
}

const PlanCard: React.FC<PlanCardProps> = ({ 
  plan, 
  billingCycle, 
  isCurrentPlan,
  isProcessing,
  onSelect,
}) => {
  const price = billingCycle === 'yearly' ? plan.priceYearly / 12 : plan.priceMonthly;
  const savings = billingCycle === 'yearly' ? calculateYearlySavings(plan.priceMonthly, plan.priceYearly) : null;
  const isPopular = plan.tier === 'business';
  const isFree = plan.tier === 'free';
  const isEnterprise = plan.tier === 'enterprise';

  return (
    <Card className={cn(
      "relative flex flex-col transition-all hover:shadow-lg",
      isCurrentPlan && "ring-2 ring-primary",
      isPopular && !isCurrentPlan && "ring-2 ring-purple-500",
    )}>
      {/* Popular Badge */}
      {isPopular && !isCurrentPlan && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <Badge className="bg-purple-500 text-white px-3">
            Mais Popular
          </Badge>
        </div>
      )}

      {/* Current Plan Badge */}
      {isCurrentPlan && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <Badge variant="default" className="px-3">
            Plano Atual
          </Badge>
        </div>
      )}

      <CardHeader className="text-center pt-8">
        <div className={cn("mx-auto p-3 rounded-xl w-fit mb-2", getPlanColor(plan.tier))}>
          {PLAN_ICONS[plan.tier]}
        </div>
        <CardTitle className="text-xl">{plan.name}</CardTitle>
        <CardDescription>{plan.description}</CardDescription>
      </CardHeader>

      <CardContent className="flex-1 space-y-4">
        {/* Price */}
        <div className="text-center">
          {isEnterprise ? (
            <p className="text-2xl font-bold">Sob Consulta</p>
          ) : isFree ? (
            <p className="text-3xl font-bold">Grátis</p>
          ) : (
            <>
              <p className="text-3xl font-bold">
                {formatPrice(price)}
                <span className="text-sm font-normal text-muted-foreground">/mês</span>
              </p>
              {billingCycle === 'yearly' && savings && (
                <p className="text-sm text-green-600">
                  Economia de {savings.savingsPercent}% ({formatPrice(savings.savingsAmount)}/ano)
                </p>
              )}
            </>
          )}
        </div>

        <Separator />

        {/* Highlights */}
        <ul className="space-y-2">
          {plan.highlights.slice(0, 8).map((highlight, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm">
              {highlight.startsWith('✓') ? (
                <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              ) : (
                <X className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              )}
              <span>{highlight.replace(/^[✓✗]\s*/, '')}</span>
            </li>
          ))}
        </ul>

        {/* Marketplaces */}
        <div className="pt-2">
          <p className="text-xs text-muted-foreground mb-2">Marketplaces:</p>
          <div className="flex flex-wrap gap-1">
            {plan.marketplaces.map((mp) => (
              <Badge key={mp} variant="outline" className="text-xs">
                {MARKETPLACE_LABELS[mp] || mp}
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>

      <CardFooter>
        <Button
          className="w-full"
          variant={isCurrentPlan ? "outline" : isPopular ? "default" : "secondary"}
          disabled={isCurrentPlan || isProcessing}
          onClick={onSelect}
        >
          {isProcessing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : isCurrentPlan ? (
            "Plano Atual"
          ) : isEnterprise ? (
            "Falar com Vendas"
          ) : isFree ? (
            "Começar Grátis"
          ) : (
            "Assinar Agora"
          )}
        </Button>
      </CardFooter>
    </Card>
  );
};

interface UsageAlertsProps {
  nearLimit: UsageStats[];
  atLimit: UsageStats[];
}

const UsageAlerts: React.FC<UsageAlertsProps> = ({ nearLimit, atLimit }) => {
  return (
    <Card className="border-yellow-500/50 bg-yellow-50 dark:bg-yellow-900/20">
      <CardContent className="py-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
          <div className="space-y-1">
            <p className="font-medium text-yellow-800 dark:text-yellow-200">
              Atenção ao uso
            </p>
            {atLimit.length > 0 && (
              <p className="text-sm text-yellow-700 dark:text-yellow-300">
                <strong>Limite atingido:</strong> {atLimit.map(u => getFeatureDisplayName(u.feature)).join(', ')}
              </p>
            )}
            {nearLimit.length > 0 && (
              <p className="text-sm text-yellow-700 dark:text-yellow-300">
                <strong>Próximo do limite:</strong> {nearLimit.map(u => getFeatureDisplayName(u.feature)).join(', ')}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

interface UsageDashboardProps {
  usage: UsageStats[];
}

const UsageDashboard: React.FC<UsageDashboardProps> = ({ usage }) => {
  const relevantUsage = usage.filter(u => !u.isUnlimited && u.limit > 0);
  
  if (relevantUsage.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Uso do Mês
        </CardTitle>
        <CardDescription>
          Resets em {relevantUsage[0]?.resetsAt ? new Date(relevantUsage[0].resetsAt).toLocaleDateString('pt-BR') : 'próximo mês'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {relevantUsage.map((item) => (
            <div key={item.feature} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{getFeatureDisplayName(item.feature)}</span>
                <span className="text-muted-foreground">
                  {item.current} / {item.limit}
                </span>
              </div>
              <Progress 
                value={item.percentage} 
                className={cn(
                  "h-2",
                  item.percentage >= 100 && "[&>div]:bg-red-500",
                  item.percentage >= 80 && item.percentage < 100 && "[&>div]:bg-yellow-500"
                )}
              />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

interface FeaturesComparisonProps {
  plans: PlanInfo[];
  currentPlan?: PlanTier;
}

const FeaturesComparison: React.FC<FeaturesComparisonProps> = ({ plans, currentPlan }) => {
  const featureCategories = [
    { 
      name: "Comparador de Preços",
      icon: <TrendingUp className="w-4 h-4" />,
      features: ['price_searches', 'price_alerts', 'favorites']
    },
    { 
      name: "Marketplaces",
      icon: <Globe className="w-4 h-4" />,
      features: ['marketplaces']
    },
    { 
      name: "WhatsApp & Social",
      icon: <MessageSquare className="w-4 h-4" />,
      features: ['whatsapp_instances', 'social_posts', 'social_accounts']
    },
    { 
      name: "Chatbot & Automação",
      icon: <Bot className="w-4 h-4" />,
      features: ['chatbot_flows', 'chatbot_ai', 'crm_automation']
    },
    { 
      name: "CRM & Leads",
      icon: <Users className="w-4 h-4" />,
      features: ['crm_leads']
    },
    { 
      name: "Analytics",
      icon: <BarChart3 className="w-4 h-4" />,
      features: ['analytics_advanced', 'analytics_export']
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Comparação Completa</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-2">Recurso</th>
                {plans.map(p => (
                  <th key={p.tier} className={cn(
                    "text-center py-3 px-4",
                    currentPlan === p.tier && "bg-primary/10"
                  )}>
                    {p.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {featureCategories.map((category) => (
                <React.Fragment key={category.name}>
                  <tr className="bg-muted/50">
                    <td colSpan={plans.length + 1} className="py-2 px-2">
                      <div className="flex items-center gap-2 font-medium">
                        {category.icon}
                        {category.name}
                      </div>
                    </td>
                  </tr>
                  {category.features.map((feature) => (
                    <tr key={feature} className="border-b">
                      <td className="py-2 px-2">{getFeatureDisplayName(feature)}</td>
                      {plans.map(p => {
                        const limit = p.limits[feature];
                        const enabled = p.features[feature];
                        
                        let display: React.ReactNode;
                        if (feature === 'marketplaces') {
                          display = `${p.marketplaces.length} marketplace${p.marketplaces.length > 1 ? 's' : ''}`;
                        } else if (limit !== undefined) {
                          display = limit === -1 ? 'Ilimitado' : limit === 0 ? <X className="w-4 h-4 text-muted-foreground mx-auto" /> : limit;
                        } else if (enabled !== undefined) {
                          display = enabled ? <Check className="w-4 h-4 text-green-500 mx-auto" /> : <X className="w-4 h-4 text-muted-foreground mx-auto" />;
                        } else {
                          display = '-';
                        }
                        
                        return (
                          <td key={p.tier} className={cn(
                            "text-center py-2 px-4",
                            currentPlan === p.tier && "bg-primary/10"
                          )}>
                            {display}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};

const FAQ: React.FC = () => {
  const faqs = [
    {
      q: "Posso trocar de plano a qualquer momento?",
      a: "Sim! Você pode fazer upgrade imediatamente ou agendar um downgrade para o final do período atual."
    },
    {
      q: "Como funciona a cobrança anual?",
      a: "Ao escolher o plano anual, você paga por 10 meses e ganha 2 meses grátis. A cobrança é feita uma única vez por ano."
    },
    {
      q: "Posso cancelar minha assinatura?",
      a: "Sim, você pode cancelar a qualquer momento. Seu acesso permanece até o final do período já pago."
    },
    {
      q: "O que acontece se eu atingir o limite?",
      a: "Você receberá um aviso e poderá fazer upgrade para continuar usando. Dados anteriores são mantidos."
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Perguntas Frequentes</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid md:grid-cols-2 gap-6">
          {faqs.map((faq, idx) => (
            <div key={idx} className="space-y-2">
              <h4 className="font-medium">{faq.q}</h4>
              <p className="text-sm text-muted-foreground">{faq.a}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default Subscription;
