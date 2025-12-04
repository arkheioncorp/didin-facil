/**
 * UsageWidget Component
 * =====================
 * Widget de dashboard mostrando barras de uso e alertas.
 * 
 * Uso:
 * ```tsx
 * <UsageWidget />
 * 
 * // Com opções
 * <UsageWidget 
 *   showAlerts={true}
 *   compact={false}
 *   onUpgrade={() => navigate('/subscription')}
 * />
 * ```
 */

import React, { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2, 
  Zap,
  Clock,
  RefreshCcw,
  ArrowRight,
  Search,
  Bot,
  ShoppingBag,
  Target,
  Bell,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSubscription } from "@/hooks/useSubscription";
import type { UsageStats } from "@/types";

// ============================================
// TYPES
// ============================================

interface UsageWidgetProps {
  showAlerts?: boolean;
  compact?: boolean;
  showTitle?: boolean;
  onUpgrade?: () => void;
  className?: string;
}

interface UsageItemProps {
  featureId: string;
  label: string;
  current: number;
  limit: number;
  icon: React.ReactNode;
  resetsAt?: string;
  compact?: boolean;
}

interface QuickStatsProps {
  usage: UsageStats[];
}

// ============================================
// FEATURE ICONS
// ============================================

const FEATURE_ICONS: Record<string, React.ReactNode> = {
  price_searches: <Search className="w-4 h-4" />,
  price_alerts: <Bell className="w-4 h-4" />,
  chatbot_queries: <Bot className="w-4 h-4" />,
  marketplace_listings: <ShoppingBag className="w-4 h-4" />,
  competitor_tracking: <Target className="w-4 h-4" />,
  ai_suggestions: <Sparkles className="w-4 h-4" />,
};

const FEATURE_LABELS: Record<string, string> = {
  price_searches: "Buscas de Preço",
  price_alerts: "Alertas de Preço",
  chatbot_queries: "Consultas ao Chatbot",
  marketplace_listings: "Anúncios Ativos",
  competitor_tracking: "Monitoramentos",
  ai_suggestions: "Sugestões IA",
};

// ============================================
// HELPER FUNCTIONS
// ============================================

function getPercentage(current: number, limit: number): number {
  if (limit === 0) return 0;
  if (limit === -1) return 0; // Unlimited
  return Math.min(100, Math.round((current / limit) * 100));
}

function getStatusColor(percentage: number): {
  progress: string;
  text: string;
  bg: string;
} {
  if (percentage >= 100) {
    return {
      progress: "bg-red-500",
      text: "text-red-600 dark:text-red-400",
      bg: "bg-red-50 dark:bg-red-900/20",
    };
  }
  if (percentage >= 80) {
    return {
      progress: "bg-amber-500",
      text: "text-amber-600 dark:text-amber-400",
      bg: "bg-amber-50 dark:bg-amber-900/20",
    };
  }
  return {
    progress: "bg-emerald-500",
    text: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-emerald-50 dark:bg-emerald-900/20",
  };
}

function formatResetTime(resetAt: string | undefined): string | null {
  if (!resetAt) return null;
  
  const date = new Date(resetAt);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  
  if (diffMs <= 0) return "Renovando...";
  
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  
  if (diffDays > 0) {
    return `Renova em ${diffDays}d ${diffHours}h`;
  }
  return `Renova em ${diffHours}h`;
}

// ============================================
// USAGE ITEM COMPONENT
// ============================================

const UsageItem: React.FC<UsageItemProps> = ({
  featureId,
  label,
  current,
  limit,
  icon,
  resetsAt,
  compact = false,
}) => {
  const isUnlimited = limit === -1;
  const percentage = getPercentage(current, limit);
  const colors = getStatusColor(percentage);
  const resetText = formatResetTime(resetsAt);
  
  if (compact) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div 
              data-testid={`usage-widget-${featureId}`}
              className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted/50 transition-colors cursor-default"
            >
              <div className={cn("p-1.5 rounded-md", colors.bg)}>
                {icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium truncate">{label}</span>
                  <span className={cn("text-xs font-semibold", colors.text)}>
                    {isUnlimited ? "∞" : `${current}/${limit}`}
                  </span>
                </div>
                {!isUnlimited && (
                  <Progress 
                    value={percentage} 
                    className="h-1.5 mt-1"
                  />
                )}
              </div>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <p>{label}</p>
            {!isUnlimited && <p className="text-xs text-muted-foreground">{percentage}% usado</p>}
            {resetText && <p className="text-xs text-muted-foreground">{resetText}</p>}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }
  
  return (
    <div data-testid={`usage-widget-${featureId}`} className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={cn("p-2 rounded-lg", colors.bg)}>
            {icon}
          </div>
          <div>
            <p className="text-sm font-medium">{label}</p>
            {resetText && (
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {resetText}
              </p>
            )}
          </div>
        </div>
        <div className="text-right">
          <p className={cn("text-sm font-semibold", colors.text)}>
            {isUnlimited ? (
              <span className="flex items-center gap-1">
                <span>Ilimitado</span>
                <CheckCircle2 className="w-4 h-4" />
              </span>
            ) : (
              `${current} / ${limit}`
            )}
          </p>
          {!isUnlimited && (
            <p className="text-xs text-muted-foreground">{percentage}%</p>
          )}
        </div>
      </div>
      {!isUnlimited && (
        <Progress 
          value={percentage} 
          className="h-2"
        />
      )}
    </div>
  );
};

// ============================================
// QUICK STATS COMPONENT
// ============================================

const QuickStats: React.FC<QuickStatsProps> = ({ usage }) => {
  const stats = useMemo(() => {
    const atLimit = usage.filter(u => u.limit !== -1 && u.current >= u.limit).length;
    const nearLimit = usage.filter(u => {
      if (u.limit === -1) return false;
      const pct = (u.current / u.limit) * 100;
      return pct >= 80 && pct < 100;
    }).length;
    const healthy = usage.filter(u => {
      if (u.limit === -1) return true;
      return (u.current / u.limit) * 100 < 80;
    }).length;
    
    return { atLimit, nearLimit, healthy };
  }, [usage]);
  
  return (
    <div className="flex items-center gap-4 text-sm">
      {stats.healthy > 0 && (
        <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
          <CheckCircle2 className="w-4 h-4" />
          <span>{stats.healthy} ok</span>
        </div>
      )}
      {stats.nearLimit > 0 && (
        <div className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
          <TrendingUp className="w-4 h-4" />
          <span>{stats.nearLimit} próximo</span>
        </div>
      )}
      {stats.atLimit > 0 && (
        <div className="flex items-center gap-1.5 text-red-600 dark:text-red-400">
          <AlertTriangle className="w-4 h-4" />
          <span>{stats.atLimit} no limite</span>
        </div>
      )}
    </div>
  );
};

// ============================================
// USAGE ALERTS COMPONENT
// ============================================

interface UsageAlertsDisplayProps {
  onUpgrade?: () => void;
  nearLimitFeatures: UsageStats[];
  atLimitFeatures: UsageStats[];
}

const UsageAlertsDisplay: React.FC<UsageAlertsDisplayProps> = ({ 
  onUpgrade,
  nearLimitFeatures,
  atLimitFeatures,
}) => {
  const navigate = useNavigate();
  
  const handleUpgrade = () => {
    if (onUpgrade) {
      onUpgrade();
    } else {
      navigate('/subscription');
    }
  };
  
  if (nearLimitFeatures.length === 0 && atLimitFeatures.length === 0) return null;
  
  return (
    <div className="space-y-3">
      {atLimitFeatures.length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Limites atingidos</AlertTitle>
          <AlertDescription>
            <ul className="list-disc list-inside mt-1 text-sm">
              {atLimitFeatures.map(stat => (
                <li key={stat.feature}>
                  {FEATURE_LABELS[stat.feature] || stat.feature}: {stat.current}/{stat.limit} ({stat.percentage}%)
                </li>
              ))}
            </ul>
            <Button 
              variant="outline" 
              size="sm" 
              className="mt-2"
              onClick={handleUpgrade}
            >
              <Zap className="w-3 h-3 mr-1" />
              Fazer Upgrade
            </Button>
          </AlertDescription>
        </Alert>
      )}
      
      {nearLimitFeatures.length > 0 && (
        <Alert>
          <TrendingUp className="h-4 w-4" />
          <AlertTitle>Uso elevado</AlertTitle>
          <AlertDescription>
            <ul className="list-disc list-inside mt-1 text-sm">
              {nearLimitFeatures.map(stat => (
                <li key={stat.feature}>
                  {FEATURE_LABELS[stat.feature] || stat.feature}: {stat.current}/{stat.limit} ({stat.percentage}%)
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================

export const UsageWidget: React.FC<UsageWidgetProps> = ({
  showAlerts = true,
  compact = false,
  showTitle = true,
  onUpgrade,
  className,
}) => {
  const navigate = useNavigate();
  const { subscription, usage, plan, isLoading } = useSubscription();
  
  const handleUpgrade = () => {
    if (onUpgrade) {
      onUpgrade();
    } else {
      navigate('/subscription');
    }
  };
  
  // Calculate alerts from usage
  const nearLimitFeatures = useMemo(() => {
    return usage.filter(u => !u.isUnlimited && u.percentage >= 80 && u.percentage < 100);
  }, [usage]);
  
  const atLimitFeatures = useMemo(() => {
    return usage.filter(u => !u.isUnlimited && u.percentage >= 100);
  }, [usage]);
  
  // Filter to show only metered features
  const meteredUsage = useMemo(() => {
    return usage.filter(u => u.limit !== 0);
  }, [usage]);
  
  if (isLoading) {
    return (
      <Card className={cn("animate-pulse", className)}>
        <CardHeader className={compact ? "pb-2" : undefined}>
          <div className="h-5 bg-muted rounded w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="space-y-2">
                <div className="h-4 bg-muted rounded w-24" />
                <div className="h-2 bg-muted rounded w-full" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }
  
  if (!subscription) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <div className="text-center">
            <Zap className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="font-semibold mb-2">Nenhuma assinatura ativa</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Escolha um plano para começar a usar o TikTrend Finder.
            </p>
            <Button onClick={handleUpgrade}>
              Ver Planos
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  if (compact) {
    return (
      <Card className={cn("p-3", className)}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="capitalize">
              {plan?.tier || 'free'}
            </Badge>
            <QuickStats usage={meteredUsage} />
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <RefreshCcw className="w-4 h-4" />
          </Button>
        </div>
        <div className="grid grid-cols-2 gap-1">
          {meteredUsage.slice(0, 4).map(stat => (
            <UsageItem
              key={stat.feature}
              featureId={stat.feature}
              label={FEATURE_LABELS[stat.feature] || stat.feature}
              current={stat.current}
              limit={stat.limit}
              icon={FEATURE_ICONS[stat.feature] || <Zap className="w-4 h-4" />}
              resetsAt={stat.resetsAt}
              compact
            />
          ))}
        </div>
      </Card>
    );
  }
  
  return (
    <Card className={className}>
      {showTitle && (
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Uso do Plano</CardTitle>
              <CardDescription className="flex items-center gap-2 mt-1">
                <Badge variant="secondary" className="capitalize">
                  {plan?.tier || 'free'}
                </Badge>
                <QuickStats usage={meteredUsage} />
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={handleUpgrade}>
              <Zap className="w-4 h-4 mr-2" />
              Upgrade
            </Button>
          </div>
        </CardHeader>
      )}
      <CardContent className={showTitle ? undefined : "pt-6"}>
        {showAlerts && (
          <UsageAlertsDisplay 
            onUpgrade={onUpgrade}
            nearLimitFeatures={nearLimitFeatures}
            atLimitFeatures={atLimitFeatures}
          />
        )}
        
        <div className="space-y-6 mt-4">
          {meteredUsage.map(stat => (
            <UsageItem
              key={stat.feature}
              featureId={stat.feature}
              label={FEATURE_LABELS[stat.feature] || stat.feature}
              current={stat.current}
              limit={stat.limit}
              icon={FEATURE_ICONS[stat.feature] || <Zap className="w-4 h-4" />}
              resetsAt={stat.resetsAt}
            />
          ))}
        </div>
        
        {meteredUsage.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <CheckCircle2 className="w-12 h-12 mx-auto mb-4 text-emerald-500" />
            <p>Todos os recursos disponíveis!</p>
            <p className="text-sm">Seu plano {plan?.name || plan?.tier || 'atual'} não tem limites de uso.</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// ============================================
// MINI USAGE BADGE COMPONENT
// ============================================

interface UsageBadgeProps {
  feature: string;
  showLabel?: boolean;
  className?: string;
}

/**
 * Mini badge showing usage for a specific feature.
 * 
 * Usage:
 * ```tsx
 * <UsageBadge feature="price_searches" />
 * ```
 */
export const UsageBadge: React.FC<UsageBadgeProps> = ({
  feature,
  showLabel = false,
  className,
}) => {
  const { usage } = useSubscription();
  
  const stat = usage.find(u => u.feature === feature);
  
  if (!stat) return null;
  
  const isUnlimited = stat.limit === -1;
  const percentage = getPercentage(stat.current, stat.limit);
  const colors = getStatusColor(percentage);
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge 
            variant="outline" 
            className={cn("gap-1", colors.bg, className)}
          >
            {FEATURE_ICONS[feature]}
            {showLabel && <span>{FEATURE_LABELS[feature]}</span>}
            <span className={cn("font-mono text-xs", colors.text)}>
              {isUnlimited ? "∞" : `${stat.current}/${stat.limit}`}
            </span>
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <p>{FEATURE_LABELS[feature] || feature}</p>
          {!isUnlimited && <p className="text-xs">{percentage}% usado</p>}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

// ============================================
// USAGE PROGRESS INLINE COMPONENT
// ============================================

interface UsageProgressInlineProps {
  feature: string;
  showLabel?: boolean;
  className?: string;
}

/**
 * Inline progress bar for a specific feature.
 * 
 * Usage:
 * ```tsx
 * <UsageProgressInline feature="price_searches" />
 * ```
 */
export const UsageProgressInline: React.FC<UsageProgressInlineProps> = ({
  feature,
  showLabel = true,
  className,
}) => {
  const { usage } = useSubscription();
  
  const stat = usage.find(u => u.feature === feature);
  
  if (!stat) return null;
  
  const isUnlimited = stat.limit === -1;
  const percentage = getPercentage(stat.current, stat.limit);
  const colors = getStatusColor(percentage);
  
  if (isUnlimited) {
    return (
      <div className={cn("flex items-center gap-2 text-sm", className)}>
        {showLabel && (
          <span className="text-muted-foreground">
            {FEATURE_LABELS[feature] || feature}:
          </span>
        )}
        <span className="text-emerald-600 flex items-center gap-1">
          <CheckCircle2 className="w-4 h-4" />
          Ilimitado
        </span>
      </div>
    );
  }
  
  return (
    <div className={cn("space-y-1", className)}>
      <div className="flex items-center justify-between text-sm">
        {showLabel && (
          <span className="text-muted-foreground">
            {FEATURE_LABELS[feature] || feature}
          </span>
        )}
        <span className={cn("font-medium", colors.text)}>
          {stat.current} / {stat.limit}
        </span>
      </div>
      <Progress value={percentage} className="h-1.5" />
    </div>
  );
};

export default UsageWidget;
