/**
 * Subscription Page - SaaS Híbrido
 * =================================
 * Página de gerenciamento de assinaturas com suporte a:
 * - Comparação de planos (FREE, STARTER, BUSINESS, ENTERPRISE)
 * - Ciclo de billing (mensal/anual com desconto)
 * - Modo de execução (web_only, hybrid, local_first)
 * - Estatísticas de uso em tempo real
 * - Upgrade/Downgrade/Cancel
 */

import * as React from "react";
import { useTranslation } from "react-i18next";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle,
  CardFooter,
} from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { TikTrendIcon } from "@/components/icons";
import { useNavigate } from "react-router-dom";
import { useSubscription, useUsageAlerts, useFeatureGate } from "@/hooks";
import { subscriptionApi, formatPrice, getPlanDisplayName, getPlanColor } from "@/services/subscription";
import { useToast } from "@/hooks/use-toast";
import type { PlanTier, BillingCycle, PlanInfo, ExecutionMode } from "@/types";
import {
  Crown,
  Zap,
  Building2,
  Sparkles,
  Check,
  X,
  ArrowRight,
  AlertTriangle,
  Clock,
  Globe,
  Monitor,
  Server,
  CreditCard,
  Calendar,
  RefreshCw,
  Shield,
  Star,
} from "lucide-react";

// ============================================
// PLAN ICONS
// ============================================

const PlanIcon: React.FC<{ tier: PlanTier; className?: string }> = ({ tier, className = "h-6 w-6" }) => {
  const icons = {
    free: <Zap className={className} />,
    starter: <Star className={className} />,
    business: <Building2 className={className} />,
    enterprise: <Crown className={className} />,
  };
  return icons[tier];
};

// ============================================
// EXECUTION MODE ICONS
// ============================================

const ExecutionModeIcon: React.FC<{ mode: ExecutionMode; className?: string }> = ({ mode, className = "h-5 w-5" }) => {
  const icons = {
    web_only: <Globe className={className} />,
    hybrid: <RefreshCw className={className} />,
    local_first: <Monitor className={className} />,
  };
  return icons[mode];
};

const EXECUTION_MODE_LABELS: Record<ExecutionMode, { name: string; description: string }> = {
  web_only: {
    name: "Somente Web",
    description: "Processamento 100% na nuvem, sempre online",
  },
  hybrid: {
    name: "Híbrido",
    description: "Sincroniza entre nuvem e desktop, funciona offline",
  },
  local_first: {
    name: "Local Primeiro",
    description: "Prioridade para processamento local, sync ocasional",
  },
};

// ============================================
// MAIN COMPONENT
// ============================================

export const Subscription: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  // Subscription state
  const { 
    subscription, 
    plan: currentPlan, 
    usage, 
    isLoading, 
    error, 
    isActive, 
    isPaid,
    planTier,
    refresh,
    upgrade,
    cancel: cancelSubscription,
  } = useSubscription();
  
  const { nearLimitFeatures, atLimitFeatures, hasAlerts } = useUsageAlerts();
  
  // Local state
  const [plans, setPlans] = React.useState<PlanInfo[]>([]);
  const [billingCycle, setBillingCycle] = React.useState<BillingCycle>('monthly');
  const [selectedPlan, setSelectedPlan] = React.useState<PlanTier | null>(null);
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [showCancelDialog, setShowCancelDialog] = React.useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState<'plans' | 'usage' | 'billing'>('plans');

  // Load plans
  React.useEffect(() => {
    subscriptionApi.getPlans().then(setPlans).catch(console.error);
  }, []);

  // Handlers
  const handleSelectPlan = async (tier: PlanTier) => {
    if (!subscription) return;
    
    if (tier === planTier) {
      toast({ 
        title: "Plano atual", 
        description: "Você já está neste plano",
        variant: "default" 
      });
      return;
    }
    
    const isUpgrade = subscriptionApi.isPlanSuperior(tier, planTier || 'free');
    
    setSelectedPlan(tier);
    
    if (isUpgrade) {
      setShowUpgradeModal(true);
    } else {
      // Downgrade - schedule for end of period
      setIsProcessing(true);
      try {
        const result = await subscriptionApi.downgradeSubscription(tier);
        toast({
          title: "Downgrade agendado",
          description: `Seu plano mudará para ${getPlanDisplayName(tier)} em ${new Date(result.effectiveAt).toLocaleDateString('pt-BR')}`,
        });
        await refresh();
      } catch (err) {
        toast({ 
          title: "Erro", 
          description: "Falha ao agendar downgrade",
          variant: "destructive" 
        });
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const handleConfirmUpgrade = async () => {
    if (!selectedPlan) return;
    
    setIsProcessing(true);
    try {
      const checkoutUrl = await upgrade(selectedPlan);
      
      if (checkoutUrl) {
        // Redirect to MercadoPago checkout
        window.location.href = checkoutUrl;
      } else {
        // Direct upgrade (dev mode)
        toast({
          title: "Upgrade realizado!",
          description: `Seu plano foi atualizado para ${getPlanDisplayName(selectedPlan)}`,
        });
        setShowUpgradeModal(false);
        await refresh();
      }
    } catch (err) {
      toast({ 
        title: "Erro no upgrade", 
        description: err instanceof Error ? err.message : "Tente novamente",
        variant: "destructive" 
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCancelSubscription = async () => {
    setIsProcessing(true);
    try {
      const success = await cancelSubscription();
      if (success) {
        toast({
          title: "Assinatura cancelada",
          description: "Você ainda terá acesso até o fim do período pago",
        });
        setShowCancelDialog(false);
        await refresh();
      }
    } catch (err) {
      toast({ 
        title: "Erro", 
        description: "Falha ao cancelar assinatura",
        variant: "destructive" 
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSetExecutionMode = async (mode: ExecutionMode) => {
    try {
      await subscriptionApi.setExecutionMode(mode);
      toast({
        title: "Modo atualizado",
        description: `Agora usando: ${EXECUTION_MODE_LABELS[mode].name}`,
      });
      await refresh();
    } catch (err) {
      toast({ 
        title: "Erro", 
        description: "Seu plano não suporta este modo",
        variant: "destructive" 
      });
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-muted" />
          <div className="h-4 w-32 rounded bg-muted" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 p-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <TikTrendIcon size={40} />
            <span className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              Didin Fácil
            </span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Sua Assinatura</h1>
          <p className="text-muted-foreground">
            Gerencie seu plano e acompanhe seu uso
          </p>
        </div>

        {/* Current Plan Status */}
        <Card className="mb-8">
          <CardContent className="py-6">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-full ${getPlanColor(planTier || 'free')}`}>
                  <PlanIcon tier={planTier || 'free'} className="h-6 w-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold">
                      Plano {getPlanDisplayName(planTier || 'free')}
                    </h2>
                    <Badge variant={isActive ? "default" : "destructive"}>
                      {subscription?.status === 'trialing' ? 'Trial' : 
                       isActive ? 'Ativo' : 'Inativo'}
                    </Badge>
                  </div>
                  {subscription?.currentPeriodEnd && (
                    <p className="text-sm text-muted-foreground">
                      {subscription.status === 'canceled' ? 'Acesso até: ' : 'Renova em: '}
                      {new Date(subscription.currentPeriodEnd).toLocaleDateString('pt-BR')}
                    </p>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                {subscription?.executionMode && (
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted">
                    <ExecutionModeIcon mode={subscription.executionMode} />
                    <span className="text-sm font-medium">
                      {EXECUTION_MODE_LABELS[subscription.executionMode].name}
                    </span>
                  </div>
                )}
                
                {isPaid && subscription?.status !== 'canceled' && (
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setShowCancelDialog(true)}
                  >
                    Cancelar Assinatura
                  </Button>
                )}
              </div>
            </div>

            {/* Usage Alerts */}
            {hasAlerts && (
              <div className="mt-4 p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-amber-600 dark:text-amber-400">
                      Atenção ao seu uso
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {atLimitFeatures.length > 0 && (
                        <span className="text-red-500">
                          {atLimitFeatures.length} recurso(s) no limite. 
                        </span>
                      )}
                      {nearLimitFeatures.length > 0 && (
                        <span>
                          {nearLimitFeatures.length} recurso(s) próximo(s) do limite.
                        </span>
                      )}
                      {' '}Considere fazer upgrade.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="plans">Planos</TabsTrigger>
            <TabsTrigger value="usage">Uso</TabsTrigger>
            <TabsTrigger value="billing">Faturamento</TabsTrigger>
          </TabsList>

          {/* Plans Tab */}
          <TabsContent value="plans" className="space-y-6">
            {/* Billing Toggle */}
            <div className="flex items-center justify-center gap-4">
              <Label 
                htmlFor="billing-toggle" 
                className={billingCycle === 'monthly' ? 'font-bold' : 'text-muted-foreground'}
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
                className={billingCycle === 'yearly' ? 'font-bold' : 'text-muted-foreground'}
              >
                Anual
                <Badge variant="secondary" className="ml-2">
                  -20%
                </Badge>
              </Label>
            </div>

            {/* Plan Cards */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {plans.map((planInfo) => {
                const tier = planInfo.tier;
                const isCurrentPlan = tier === planTier;
                const isUpgrade = subscriptionApi.isPlanSuperior(tier, planTier || 'free');
                const price = billingCycle === 'yearly' 
                  ? planInfo.priceYearly / 12 
                  : planInfo.priceMonthly;
                const isBusiness = tier === 'business';
                
                return (
                  <Card 
                    key={tier}
                    className={`relative flex flex-col ${
                      isBusiness ? 'border-primary shadow-lg' : ''
                    } ${isCurrentPlan ? 'ring-2 ring-primary' : ''}`}
                  >
                    {isBusiness && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                        <Badge className="bg-primary text-primary-foreground px-4">
                          Recomendado
                        </Badge>
                      </div>
                    )}
                    
                    {isCurrentPlan && (
                      <div className="absolute -top-3 right-4">
                        <Badge variant="outline" className="bg-background">
                          Atual
                        </Badge>
                      </div>
                    )}
                    
                    <CardHeader className="text-center pb-2">
                      <div className={`mx-auto p-3 rounded-full w-fit ${getPlanColor(tier)}`}>
                        <PlanIcon tier={tier} className="h-6 w-6" />
                      </div>
                      <CardTitle className="mt-3">{getPlanDisplayName(tier)}</CardTitle>
                      <CardDescription>{planInfo.description}</CardDescription>
                    </CardHeader>
                    
                    <CardContent className="flex-1">
                      <div className="text-center mb-6">
                        <span className="text-4xl font-bold">
                          {tier === 'free' ? 'Grátis' : formatPrice(price)}
                        </span>
                        {tier !== 'free' && (
                          <span className="text-muted-foreground">/mês</span>
                        )}
                        {billingCycle === 'yearly' && tier !== 'free' && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Cobrado {formatPrice(planInfo.priceYearly)}/ano
                          </p>
                        )}
                      </div>
                      
                      <Separator className="my-4" />
                      
                      <ul className="space-y-3">
                        {/* Key features */}
                        {Object.entries(planInfo.features).slice(0, 6).map(([feature, enabled]) => (
                          <li key={feature} className="flex items-center gap-2 text-sm">
                            {enabled ? (
                              <Check className="h-4 w-4 text-green-500" />
                            ) : (
                              <X className="h-4 w-4 text-muted-foreground" />
                            )}
                            <span className={!enabled ? 'text-muted-foreground' : ''}>
                              {formatFeatureName(feature)}
                            </span>
                          </li>
                        ))}
                        
                        {/* Key limits */}
                        {Object.entries(planInfo.limits).slice(0, 3).map(([limit, value]) => (
                          <li key={limit} className="flex items-center gap-2 text-sm">
                            <Check className="h-4 w-4 text-green-500" />
                            <span>
                              {value === -1 ? 'Ilimitado' : value} {formatLimitName(limit)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                    
                    <CardFooter>
                      <Button 
                        className="w-full"
                        variant={isBusiness ? "default" : isUpgrade ? "secondary" : "outline"}
                        disabled={isCurrentPlan || isProcessing}
                        onClick={() => handleSelectPlan(tier)}
                      >
                        {isCurrentPlan ? (
                          'Plano Atual'
                        ) : isUpgrade ? (
                          <>
                            Fazer Upgrade <ArrowRight className="ml-2 h-4 w-4" />
                          </>
                        ) : (
                          'Downgrade'
                        )}
                      </Button>
                    </CardFooter>
                  </Card>
                );
              })}
            </div>

            {/* Execution Mode Section (for paid plans) */}
            {isPaid && (
              <Card className="mt-8">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Server className="h-5 w-5" />
                    Modo de Execução
                  </CardTitle>
                  <CardDescription>
                    Escolha como o Didin Fácil processa seus dados
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-3 gap-4">
                    {(['web_only', 'hybrid', 'local_first'] as ExecutionMode[]).map((mode) => {
                      const isCurrentMode = subscription?.executionMode === mode;
                      const modeInfo = EXECUTION_MODE_LABELS[mode];
                      
                      // Check if mode is available for current plan
                      const availableModes = currentPlan?.executionModes || ['web_only'];
                      const isAvailable = availableModes.includes(mode);
                      
                      return (
                        <Card
                          key={mode}
                          className={`cursor-pointer transition-all ${
                            isCurrentMode ? 'ring-2 ring-primary' : ''
                          } ${!isAvailable ? 'opacity-50' : 'hover:shadow-md'}`}
                          onClick={() => isAvailable && handleSetExecutionMode(mode)}
                        >
                          <CardContent className="pt-6">
                            <div className="flex items-center gap-3 mb-3">
                              <ExecutionModeIcon mode={mode} className="h-6 w-6" />
                              <span className="font-semibold">{modeInfo.name}</span>
                              {isCurrentMode && (
                                <Badge variant="secondary" className="ml-auto">Ativo</Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {modeInfo.description}
                            </p>
                            {!isAvailable && (
                              <p className="text-xs text-amber-500 mt-2">
                                Disponível no plano Business+
                              </p>
                            )}
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
          {/* Usage Tab */}
          <TabsContent value="usage" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Uso do Período Atual</CardTitle>
                <CardDescription>
                  Acompanhe o consumo dos recursos do seu plano
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {usage.length === 0 ? (
                  <p className="text-center text-muted-foreground py-8">
                    Nenhum dado de uso disponível
                  </p>
                ) : (
                  usage.map((stat) => (
                    <div key={stat.feature} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{formatFeatureName(stat.feature)}</span>
                        <span className="text-sm text-muted-foreground">
                          {stat.isUnlimited ? (
                            '∞ Ilimitado'
                          ) : (
                            `${stat.current} / ${stat.limit}`
                          )}
                        </span>
                      </div>
                      {!stat.isUnlimited && (
                        <Progress 
                          value={stat.percentage} 
                          className={`h-2 ${
                            stat.percentage >= 100 ? '[&>div]:bg-red-500' :
                            stat.percentage >= 80 ? '[&>div]:bg-amber-500' : ''
                          }`}
                        />
                      )}
                      {stat.resetsAt && (
                        <p className="text-xs text-muted-foreground">
                          Renova em: {new Date(stat.resetsAt).toLocaleDateString('pt-BR')}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Marketplace Access */}
            <Card>
              <CardHeader>
                <CardTitle>Acesso a Marketplaces</CardTitle>
                <CardDescription>
                  Marketplaces habilitados no seu plano
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {['tiktok', 'aliexpress', 'shopee', 'amazon', 'mercadolivre'].map((mp) => {
                    const hasAccess = subscription?.marketplaces?.includes(mp as any);
                    return (
                      <div
                        key={mp}
                        className={`p-4 rounded-lg border text-center ${
                          hasAccess 
                            ? 'bg-green-500/10 border-green-500/30' 
                            : 'bg-muted/50 border-muted opacity-50'
                        }`}
                      >
                        <span className="text-2xl mb-2 block">
                          {getMarketplaceEmoji(mp)}
                        </span>
                        <span className={`text-sm font-medium ${
                          hasAccess ? '' : 'text-muted-foreground'
                        }`}>
                          {mp.charAt(0).toUpperCase() + mp.slice(1)}
                        </span>
                        {hasAccess && (
                          <Check className="h-4 w-4 text-green-500 mx-auto mt-1" />
                        )}
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Billing Tab */}
          <TabsContent value="billing" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CreditCard className="h-5 w-5" />
                  Informações de Pagamento
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {subscription ? (
                  <>
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Plano</span>
                      <span className="font-medium">{getPlanDisplayName(planTier || 'free')}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Ciclo</span>
                      <span className="font-medium">
                        {subscription.billingCycle === 'yearly' ? 'Anual' : 'Mensal'}
                      </span>
                    </div>
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Início do Período</span>
                      <span className="font-medium">
                        {new Date(subscription.currentPeriodStart).toLocaleDateString('pt-BR')}
                      </span>
                    </div>
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Fim do Período</span>
                      <span className="font-medium">
                        {new Date(subscription.currentPeriodEnd).toLocaleDateString('pt-BR')}
                      </span>
                    </div>
                    <div className="flex justify-between py-2">
                      <span className="text-muted-foreground">Status</span>
                      <Badge variant={isActive ? "default" : "destructive"}>
                        {subscription.status === 'active' ? 'Ativo' :
                         subscription.status === 'trialing' ? 'Trial' :
                         subscription.status === 'canceled' ? 'Cancelado' :
                         subscription.status === 'past_due' ? 'Atrasado' :
                         subscription.status}
                      </Badge>
                    </div>
                    
                    {subscription.status === 'canceled' && (
                      <div className="mt-4 p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                        <p className="text-sm text-amber-600 dark:text-amber-400">
                          <Clock className="h-4 w-4 inline mr-2" />
                          Sua assinatura foi cancelada. Acesso disponível até {' '}
                          {new Date(subscription.currentPeriodEnd).toLocaleDateString('pt-BR')}.
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-center text-muted-foreground py-4">
                    Nenhuma assinatura ativa
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Payment Method */}
            <Card>
              <CardHeader>
                <CardTitle>Método de Pagamento</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between p-4 rounded-lg border">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded bg-blue-500/10">
                      <CreditCard className="h-5 w-5 text-blue-500" />
                    </div>
                    <div>
                      <p className="font-medium">Mercado Pago</p>
                      <p className="text-sm text-muted-foreground">
                        Pix, Cartão ou Boleto
                      </p>
                    </div>
                  </div>
                  <Shield className="h-5 w-5 text-green-500" />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Back Button */}
        <div className="mt-8 text-center">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            ← Voltar
          </Button>
        </div>
      </div>

      {/* Upgrade Confirmation Modal */}
      <Dialog open={showUpgradeModal} onOpenChange={setShowUpgradeModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar Upgrade</DialogTitle>
            <DialogDescription>
              Você está prestes a fazer upgrade para o plano {getPlanDisplayName(selectedPlan || 'free')}.
            </DialogDescription>
          </DialogHeader>
          
          {selectedPlan && (
            <div className="py-4">
              <div className="flex items-center justify-between p-4 rounded-lg bg-muted">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-full ${getPlanColor(selectedPlan)}`}>
                    <PlanIcon tier={selectedPlan} className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium">{getPlanDisplayName(selectedPlan)}</p>
                    <p className="text-sm text-muted-foreground">
                      {billingCycle === 'yearly' ? 'Cobrança anual' : 'Cobrança mensal'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold">
                    {formatPrice(
                      plans.find(p => p.name === selectedPlan)?.[
                        billingCycle === 'yearly' ? 'priceYearly' : 'priceMonthly'
                      ] || 0
                    )}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {billingCycle === 'yearly' ? '/ano' : '/mês'}
                  </p>
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUpgradeModal(false)}>
              Cancelar
            </Button>
            <Button onClick={handleConfirmUpgrade} disabled={isProcessing}>
              {isProcessing ? (
                <LoadingSpinner text="Processando..." />
              ) : (
                <>
                  Confirmar Upgrade <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cancel Confirmation Dialog */}
      <AlertDialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancelar Assinatura?</AlertDialogTitle>
            <AlertDialogDescription>
              Você manterá acesso até o final do período pago atual 
              ({subscription?.currentPeriodEnd 
                ? new Date(subscription.currentPeriodEnd).toLocaleDateString('pt-BR')
                : 'data não disponível'
              }). Após isso, seu plano será revertido para o Free.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Voltar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-500 hover:bg-red-600"
              onClick={handleCancelSubscription}
              disabled={isProcessing}
            >
              {isProcessing ? 'Cancelando...' : 'Sim, Cancelar'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

// ============================================
// HELPER COMPONENTS
// ============================================

const LoadingSpinner: React.FC<{ text: string }> = ({ text }) => (
  <span className="flex items-center gap-2">
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
        fill="none"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
    {text}
  </span>
);

// ============================================
// HELPER FUNCTIONS
// ============================================

function formatFeatureName(feature: string): string {
  const names: Record<string, string> = {
    price_searches: 'Buscas de preço',
    price_alerts: 'Alertas de preço',
    favorites: 'Favoritos',
    social_posts: 'Posts agendados',
    social_accounts: 'Contas sociais',
    whatsapp_instances: 'Instâncias WhatsApp',
    whatsapp_messages: 'Mensagens WhatsApp',
    chatbot_flows: 'Fluxos de chatbot',
    chatbot_ai: 'IA no Chatbot',
    crm_leads: 'Leads no CRM',
    crm_automation: 'Automação CRM',
    analytics_basic: 'Analytics básico',
    analytics_advanced: 'Analytics avançado',
    analytics_export: 'Exportar relatórios',
    api_calls: 'Chamadas API',
    api_access: 'Acesso à API',
    offline_mode: 'Modo offline',
    hybrid_sync: 'Sync híbrido',
  };
  return names[feature] || feature.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function formatLimitName(limit: string): string {
  const names: Record<string, string> = {
    price_searches: 'buscas/mês',
    favorites: 'favoritos',
    whatsapp_messages: 'mensagens/mês',
    api_calls: 'chamadas/mês',
    crm_leads: 'leads',
    chatbot_flows: 'fluxos',
    social_posts: 'posts/mês',
  };
  return names[limit] || limit.replace(/_/g, ' ');
}

function getMarketplaceEmoji(marketplace: string): string {
  const emojis: Record<string, string> = {
    tiktok: '🎵',
    aliexpress: '📦',
    shopee: '🛒',
    amazon: '📦',
    mercadolivre: '🟡',
  };
  return emojis[marketplace] || '🏪';
}

export default Subscription;
