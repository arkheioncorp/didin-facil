import * as React from "react";
import { cn } from "@/lib/utils";
import { 
  Eye, 
  MousePointer, 
  Share2, 
  ShoppingCart, 
  TrendingUp, 
  TrendingDown,
  Instagram,
  Youtube,
  MessageCircle,
  Sparkles,
  FileText,
  BarChart3,
  Activity,
} from "lucide-react";
import { useProductAnalyticsStore } from "@/stores/productAnalyticsStore";
import { Badge } from "@/components/ui/badge";
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from "@/components/ui/tooltip";
import { Progress } from "@/components/ui/progress";

// TikTok Icon
const TikTokIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" className={cn("fill-current", className)}>
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
  </svg>
);

// ============================================
// STAT CARD COMPONENT
// ============================================

interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  trend?: number;
  color?: "default" | "blue" | "green" | "yellow" | "pink" | "red";
  tooltip?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon,
  trend,
  color = "default",
  tooltip,
}) => {
  const colorClasses = {
    default: "bg-muted/50 text-foreground",
    blue: "bg-blue-500/10 text-blue-500 border-blue-500/20",
    green: "bg-green-500/10 text-green-500 border-green-500/20",
    yellow: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
    pink: "bg-pink-500/10 text-pink-500 border-pink-500/20",
    red: "bg-red-500/10 text-red-500 border-red-500/20",
  };

  const card = (
    <div className={cn("p-3 rounded-lg border transition-colors hover:bg-muted/80", colorClasses[color])}>
      <div className="flex items-center justify-between mb-2">
        <div className="p-1.5 rounded-md bg-background/50">
          {icon}
        </div>
        {trend !== undefined && (
          <div className={cn(
            "flex items-center gap-0.5 text-xs font-medium",
            trend > 0 ? "text-green-500" : trend < 0 ? "text-red-500" : "text-muted-foreground"
          )}>
            {trend > 0 ? <TrendingUp className="h-3 w-3" /> : trend < 0 ? <TrendingDown className="h-3 w-3" /> : null}
            {trend !== 0 && `${Math.abs(trend)}%`}
          </div>
        )}
      </div>
      <p className="text-lg font-bold">{typeof value === "number" ? value.toLocaleString() : value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );

  if (tooltip) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            {card}
          </TooltipTrigger>
          <TooltipContent>
            <p className="text-xs">{tooltip}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return card;
};

// ============================================
// PRODUCT ANALYTICS PANEL
// ============================================

interface ProductAnalyticsPanelProps {
  productId: string;
  className?: string;
  compact?: boolean;
}

export const ProductAnalyticsPanel: React.FC<ProductAnalyticsPanelProps> = ({
  productId,
  className,
  compact = false,
}) => {
  const { getProductStats, getProductAnalytics, getTrend } = useProductAnalyticsStore();
  
  const stats = getProductStats(productId);
  const analytics = getProductAnalytics(productId);
  
  const viewsTrend = getTrend(productId, "views", 7);
  const clicksTrend = getTrend(productId, "clicks", 7);
  const conversionsTrend = getTrend(productId, "conversions", 7);

  if (compact) {
    return (
      <div className={cn("flex items-center gap-4 text-sm", className)}>
        <div className="flex items-center gap-1">
          <Eye className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{stats.totalViews}</span>
        </div>
        <div className="flex items-center gap-1">
          <MousePointer className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{stats.totalClicks}</span>
        </div>
        <div className="flex items-center gap-1">
          <Share2 className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{stats.totalShares}</span>
        </div>
        {stats.engagementRate > 0 && (
          <Badge variant="secondary" className="text-xs">
            {stats.engagementRate}% engajamento
          </Badge>
        )}
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-tiktrend-primary" />
          <h3 className="font-semibold">Analytics do Produto</h3>
        </div>
        {analytics && (
          <span className="text-xs text-muted-foreground">
            Última atividade: {new Date(analytics.lastActivity).toLocaleDateString("pt-BR")}
          </span>
        )}
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          label="Visualizações"
          value={stats.totalViews}
          icon={<Eye className="h-4 w-4" />}
          trend={viewsTrend}
          color="blue"
          tooltip="Total de visualizações do produto"
        />
        <StatCard
          label="Cliques"
          value={stats.totalClicks}
          icon={<MousePointer className="h-4 w-4" />}
          trend={clicksTrend}
          color="green"
          tooltip="Total de cliques no produto"
        />
        <StatCard
          label="Compartilhamentos"
          value={stats.totalShares}
          icon={<Share2 className="h-4 w-4" />}
          color="yellow"
          tooltip="Total de compartilhamentos"
        />
        <StatCard
          label="Conversões"
          value={stats.totalConversions}
          icon={<ShoppingCart className="h-4 w-4" />}
          trend={conversionsTrend}
          color="pink"
          tooltip="Total de vendas/conversões"
        />
      </div>

      {/* Rates */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 rounded-lg bg-muted/30 border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Taxa de Engajamento</span>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex items-center gap-2">
            <Progress value={Math.min(stats.engagementRate, 100)} className="flex-1 h-2" />
            <span className="text-sm font-medium">{stats.engagementRate}%</span>
          </div>
        </div>
        <div className="p-3 rounded-lg bg-muted/30 border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Taxa de Conversão</span>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex items-center gap-2">
            <Progress value={Math.min(stats.conversionRate, 100)} className="flex-1 h-2" />
            <span className="text-sm font-medium">{stats.conversionRate}%</span>
          </div>
        </div>
      </div>

      {/* Social Media Stats */}
      {analytics && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground">Publicações por Plataforma</h4>
          <div className="grid grid-cols-4 gap-2">
            <div className="flex flex-col items-center p-2 rounded-lg bg-pink-500/10 border border-pink-500/20">
              <Instagram className="h-5 w-5 text-pink-500 mb-1" />
              <span className="text-lg font-bold text-pink-500">{analytics.instagramPosts}</span>
              <span className="text-[10px] text-muted-foreground">Instagram</span>
            </div>
            <div className="flex flex-col items-center p-2 rounded-lg bg-foreground/10 border border-foreground/20">
              <TikTokIcon className="h-5 w-5 mb-1" />
              <span className="text-lg font-bold">{analytics.tiktokPosts}</span>
              <span className="text-[10px] text-muted-foreground">TikTok</span>
            </div>
            <div className="flex flex-col items-center p-2 rounded-lg bg-red-500/10 border border-red-500/20">
              <Youtube className="h-5 w-5 text-red-500 mb-1" />
              <span className="text-lg font-bold text-red-500">{analytics.youtubePosts}</span>
              <span className="text-[10px] text-muted-foreground">YouTube</span>
            </div>
            <div className="flex flex-col items-center p-2 rounded-lg bg-green-500/10 border border-green-500/20">
              <MessageCircle className="h-5 w-5 text-green-500 mb-1" />
              <span className="text-lg font-bold text-green-500">{analytics.whatsappShares}</span>
              <span className="text-[10px] text-muted-foreground">WhatsApp</span>
            </div>
          </div>
        </div>
      )}

      {/* Action Stats */}
      {analytics && (
        <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-500" />
              <span className="text-sm">
                <span className="font-medium">{analytics.copiesGenerated}</span>
                <span className="text-muted-foreground ml-1">copies gerados</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-blue-500" />
              <span className="text-sm">
                <span className="font-medium">{analytics.templatesUsed}</span>
                <span className="text-muted-foreground ml-1">templates usados</span>
              </span>
            </div>
          </div>
          <Badge variant="outline">
            {analytics.actionsExecuted} ações
          </Badge>
        </div>
      )}

      {/* Revenue (if any) */}
      {stats.totalRevenue > 0 && (
        <div className="p-4 rounded-lg bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Receita Total</p>
              <p className="text-2xl font-bold text-green-500">
                R$ {stats.totalRevenue.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </p>
            </div>
            <ShoppingCart className="h-8 w-8 text-green-500/50" />
          </div>
        </div>
      )}

      {/* Empty State */}
      {!analytics && (
        <div className="text-center py-8 text-muted-foreground">
          <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">Nenhuma métrica registrada ainda</p>
          <p className="text-xs">Execute ações neste produto para começar a rastrear</p>
        </div>
      )}
    </div>
  );
};

// ============================================
// MINI ANALYTICS BADGE
// ============================================

interface MiniAnalyticsBadgeProps {
  productId: string;
  className?: string;
}

export const MiniAnalyticsBadge: React.FC<MiniAnalyticsBadgeProps> = ({
  productId,
  className,
}) => {
  const { getProductStats } = useProductAnalyticsStore();
  const stats = getProductStats(productId);

  if (stats.totalViews === 0 && stats.totalClicks === 0) {
    return null;
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn("flex items-center gap-1.5 text-xs", className)}>
            <Eye className="h-3 w-3 text-muted-foreground" />
            <span>{stats.totalViews}</span>
            {stats.engagementRate > 0 && (
              <>
                <span className="text-muted-foreground">•</span>
                <span className="text-green-500">{stats.engagementRate}%</span>
              </>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <div className="space-y-1 text-xs">
            <p>{stats.totalViews} visualizações</p>
            <p>{stats.totalClicks} cliques</p>
            <p>{stats.totalShares} compartilhamentos</p>
            {stats.engagementRate > 0 && (
              <p className="text-green-500">{stats.engagementRate}% de engajamento</p>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default ProductAnalyticsPanel;
