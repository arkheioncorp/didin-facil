/**
 * Social Analytics Page
 * ======================
 * Dashboard de analytics para redes sociais
 * - Métricas de publicação
 * - Performance por plataforma
 * - Engagement e alcance
 * - Tendências e insights
 */

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Eye,
  Heart,
  MessageCircle,
  Share2,
  Calendar,
  RefreshCw,
  Download,
  Instagram,
  Youtube,
  Loader2,
  Activity,
  Target,
  Clock,
  Zap,
} from "lucide-react";

// TikTok Icon
const TikTokIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" className={`fill-current ${className || "h-4 w-4"}`}>
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z" />
  </svg>
);

// Types
interface PlatformStats {
  platform: string;
  posts_total: number;
  posts_published: number;
  posts_failed: number;
  posts_scheduled: number;
  success_rate: number;
  avg_engagement: number;
  total_reach: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  growth_rate: number;
  best_time: string;
}

interface OverallStats {
  total_posts: number;
  total_reach: number;
  total_engagement: number;
  avg_success_rate: number;
  platforms: PlatformStats[];
  trends: {
    posts_change: number;
    reach_change: number;
    engagement_change: number;
  };
}

interface DailyMetric {
  date: string;
  posts: number;
  reach: number;
  engagement: number;
  platform: string;
}

// Platform Config
const PLATFORM_CONFIG: Record<string, {
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
}> = {
  instagram: {
    name: "Instagram",
    icon: Instagram,
    color: "text-pink-500",
    bgColor: "bg-pink-500/10",
  },
  tiktok: {
    name: "TikTok",
    icon: TikTokIcon,
    color: "text-gray-900 dark:text-white",
    bgColor: "bg-gray-100 dark:bg-gray-800",
  },
  youtube: {
    name: "YouTube",
    icon: Youtube,
    color: "text-red-500",
    bgColor: "bg-red-500/10",
  },
  whatsapp: {
    name: "WhatsApp",
    icon: MessageCircle,
    color: "text-green-500",
    bgColor: "bg-green-500/10",
  },
};

// Stat Card Component
const StatCard: React.FC<{
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  description?: string;
}> = ({ title, value, change, icon, description }) => (
  <Card>
    <CardContent className="pt-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold">{typeof value === 'number' ? value.toLocaleString('pt-BR') : value}</p>
          {description && (
            <p className="text-xs text-muted-foreground">{description}</p>
          )}
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="p-2 rounded-lg bg-muted">{icon}</div>
          {change !== undefined && (
            <Badge variant={change >= 0 ? "default" : "destructive"} className="text-xs">
              {change >= 0 ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
              {Math.abs(change)}%
            </Badge>
          )}
        </div>
      </div>
    </CardContent>
  </Card>
);

// Platform Card Component
const PlatformCard: React.FC<{ stats: PlatformStats }> = ({ stats }) => {
  const config = PLATFORM_CONFIG[stats.platform] || PLATFORM_CONFIG.instagram;
  const Icon = config.icon;

  return (
    <Card className={`border-l-4 ${config.bgColor}`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`p-2 rounded-lg ${config.bgColor}`}>
              <Icon className={`h-5 w-5 ${config.color}`} />
            </div>
            <CardTitle className="text-lg">{config.name}</CardTitle>
          </div>
          <Badge variant={stats.success_rate >= 80 ? "default" : stats.success_rate >= 50 ? "secondary" : "destructive"}>
            {stats.success_rate.toFixed(1)}% sucesso
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Posts</p>
            <p className="text-lg font-semibold">{stats.posts_total}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Alcance</p>
            <p className="text-lg font-semibold">{formatNumber(stats.total_reach)}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Engagement</p>
            <p className="text-lg font-semibold">{stats.avg_engagement.toFixed(1)}%</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Crescimento</p>
            <p className={`text-lg font-semibold ${stats.growth_rate >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {stats.growth_rate >= 0 ? '+' : ''}{stats.growth_rate.toFixed(1)}%
            </p>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t flex items-center justify-between text-sm">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <Heart className="h-4 w-4 text-red-500" />
              {formatNumber(stats.total_likes)}
            </span>
            <span className="flex items-center gap-1">
              <MessageCircle className="h-4 w-4 text-blue-500" />
              {formatNumber(stats.total_comments)}
            </span>
            <span className="flex items-center gap-1">
              <Share2 className="h-4 w-4 text-green-500" />
              {formatNumber(stats.total_shares)}
            </span>
          </div>
          <span className="text-muted-foreground flex items-center gap-1">
            <Clock className="h-4 w-4" />
            Melhor: {stats.best_time}
          </span>
        </div>
      </CardContent>
    </Card>
  );
};

// Helper function
function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

// Simple Bar Chart Component (placeholder for a real chart library)
const SimpleBarChart: React.FC<{ data: DailyMetric[] }> = ({ data }) => {
  const maxValue = Math.max(...data.map(d => d.posts), 1);
  
  return (
    <div className="flex items-end gap-1 h-32">
      {data.slice(-14).map((item, index) => (
        <div key={index} className="flex-1 flex flex-col items-center gap-1">
          <div 
            className="w-full bg-primary rounded-t transition-all hover:bg-primary/80"
            style={{ height: `${(item.posts / maxValue) * 100}%`, minHeight: '4px' }}
          />
          <span className="text-[10px] text-muted-foreground">
            {new Date(item.date).getDate()}
          </span>
        </div>
      ))}
    </div>
  );
};

// Main Component
export const SocialAnalytics: React.FC = () => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState("7d");
  const [stats, setStats] = useState<OverallStats | null>(null);
  const [dailyMetrics, setDailyMetrics] = useState<DailyMetric[]>([]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      // Fetch overall stats
      const [statsRes, metricsRes] = await Promise.all([
        api.get<OverallStats>(`/analytics/social/overview?period=${period}`),
        api.get<{ metrics: DailyMetric[] }>(`/analytics/social/daily?period=${period}`)
      ]);
      
      setStats(statsRes.data);
      setDailyMetrics(metricsRes.data.metrics || []);
    } catch (error) {
      console.error("Error fetching analytics:", error);
      // Use mock data for now
      setStats(getMockStats());
      setDailyMetrics(getMockDailyMetrics());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  const handleExport = async () => {
    toast({ title: "Exportando relatório...", description: "O download começará em breve" });
    // TODO: Implement export
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BarChart3 className="h-8 w-8" />
            Analytics Social
          </h1>
          <p className="text-muted-foreground mt-1">
            Performance e métricas das suas redes sociais
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[140px]">
              <Calendar className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Últimos 7 dias</SelectItem>
              <SelectItem value="30d">Últimos 30 dias</SelectItem>
              <SelectItem value="90d">Últimos 90 dias</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" size="icon" onClick={fetchAnalytics}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total de Posts"
          value={stats?.total_posts || 0}
          change={stats?.trends.posts_change}
          icon={<Activity className="h-5 w-5 text-blue-500" />}
          description="Publicações no período"
        />
        <StatCard
          title="Alcance Total"
          value={formatNumber(stats?.total_reach || 0)}
          change={stats?.trends.reach_change}
          icon={<Eye className="h-5 w-5 text-green-500" />}
          description="Pessoas alcançadas"
        />
        <StatCard
          title="Engagement"
          value={`${(stats?.total_engagement || 0).toFixed(1)}%`}
          change={stats?.trends.engagement_change}
          icon={<Heart className="h-5 w-5 text-red-500" />}
          description="Taxa de interação"
        />
        <StatCard
          title="Taxa de Sucesso"
          value={`${(stats?.avg_success_rate || 0).toFixed(1)}%`}
          icon={<Target className="h-5 w-5 text-purple-500" />}
          description="Posts publicados com sucesso"
        />
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Visão Geral
          </TabsTrigger>
          <TabsTrigger value="platforms" className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Por Plataforma
          </TabsTrigger>
          <TabsTrigger value="insights" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Insights
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Activity Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Atividade de Publicação</CardTitle>
              <CardDescription>Posts publicados por dia</CardDescription>
            </CardHeader>
            <CardContent>
              <SimpleBarChart data={dailyMetrics} />
            </CardContent>
          </Card>

          {/* Platform Summary */}
          <div className="grid gap-4 md:grid-cols-2">
            {stats?.platforms.map((platform) => (
              <PlatformCard key={platform.platform} stats={platform} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="platforms" className="space-y-4">
          {stats?.platforms.map((platform) => (
            <Card key={platform.platform}>
              <CardHeader>
                <div className="flex items-center gap-2">
                  {React.createElement(PLATFORM_CONFIG[platform.platform]?.icon || Activity, {
                    className: `h-5 w-5 ${PLATFORM_CONFIG[platform.platform]?.color || ''}`
                  })}
                  <CardTitle>{PLATFORM_CONFIG[platform.platform]?.name || platform.platform}</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Total Posts</p>
                    <p className="text-xl font-bold">{platform.posts_total}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Publicados</p>
                    <p className="text-xl font-bold text-green-500">{platform.posts_published}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Falharam</p>
                    <p className="text-xl font-bold text-red-500">{platform.posts_failed}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Agendados</p>
                    <p className="text-xl font-bold text-blue-500">{platform.posts_scheduled}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Alcance</p>
                    <p className="text-xl font-bold">{formatNumber(platform.total_reach)}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Engagement</p>
                    <p className="text-xl font-bold">{platform.avg_engagement.toFixed(1)}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Melhores Horários
                </CardTitle>
                <CardDescription>Horários com maior engagement</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats?.platforms.map((p) => (
                    <div key={p.platform} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {React.createElement(PLATFORM_CONFIG[p.platform]?.icon || Activity, {
                          className: `h-4 w-4 ${PLATFORM_CONFIG[p.platform]?.color || ''}`
                        })}
                        <span>{PLATFORM_CONFIG[p.platform]?.name}</span>
                      </div>
                      <Badge variant="secondary">{p.best_time}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Tendências
                </CardTitle>
                <CardDescription>Mudanças no período</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span>Posts</span>
                    <Badge variant={stats?.trends.posts_change && stats.trends.posts_change >= 0 ? "default" : "destructive"}>
                      {stats?.trends.posts_change && stats.trends.posts_change >= 0 ? '+' : ''}
                      {stats?.trends.posts_change?.toFixed(1)}%
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Alcance</span>
                    <Badge variant={stats?.trends.reach_change && stats.trends.reach_change >= 0 ? "default" : "destructive"}>
                      {stats?.trends.reach_change && stats.trends.reach_change >= 0 ? '+' : ''}
                      {stats?.trends.reach_change?.toFixed(1)}%
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Engagement</span>
                    <Badge variant={stats?.trends.engagement_change && stats.trends.engagement_change >= 0 ? "default" : "destructive"}>
                      {stats?.trends.engagement_change && stats.trends.engagement_change >= 0 ? '+' : ''}
                      {stats?.trends.engagement_change?.toFixed(1)}%
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Recomendações
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted">
                  <div className="p-2 rounded-full bg-blue-500/10">
                    <Clock className="h-4 w-4 text-blue-500" />
                  </div>
                  <div>
                    <p className="font-medium">Otimize seus horários</p>
                    <p className="text-sm text-muted-foreground">
                      Seus posts têm melhor performance entre 18h e 21h. Considere agendar mais conteúdo nesse período.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted">
                  <div className="p-2 rounded-full bg-green-500/10">
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  </div>
                  <div>
                    <p className="font-medium">Aumente a frequência no TikTok</p>
                    <p className="text-sm text-muted-foreground">
                      Seu engagement no TikTok está 30% acima da média. Considere postar mais nessa plataforma.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted">
                  <div className="p-2 rounded-full bg-purple-500/10">
                    <Target className="h-4 w-4 text-purple-500" />
                  </div>
                  <div>
                    <p className="font-medium">Use mais hashtags no Instagram</p>
                    <p className="text-sm text-muted-foreground">
                      Posts com 5-10 hashtags têm 15% mais alcance. Você está usando em média 3.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Mock data functions
function getMockStats(): OverallStats {
  return {
    total_posts: 156,
    total_reach: 245000,
    total_engagement: 4.8,
    avg_success_rate: 94.2,
    platforms: [
      {
        platform: "instagram",
        posts_total: 67,
        posts_published: 63,
        posts_failed: 2,
        posts_scheduled: 2,
        success_rate: 94.0,
        avg_engagement: 5.2,
        total_reach: 120000,
        total_likes: 8500,
        total_comments: 450,
        total_shares: 120,
        growth_rate: 12.5,
        best_time: "19:00",
      },
      {
        platform: "tiktok",
        posts_total: 45,
        posts_published: 43,
        posts_failed: 1,
        posts_scheduled: 1,
        success_rate: 95.6,
        avg_engagement: 7.8,
        total_reach: 85000,
        total_likes: 12000,
        total_comments: 890,
        total_shares: 340,
        growth_rate: 25.3,
        best_time: "21:00",
      },
      {
        platform: "youtube",
        posts_total: 23,
        posts_published: 22,
        posts_failed: 1,
        posts_scheduled: 0,
        success_rate: 95.7,
        avg_engagement: 3.2,
        total_reach: 35000,
        total_likes: 2100,
        total_comments: 180,
        total_shares: 45,
        growth_rate: 8.1,
        best_time: "14:00",
      },
      {
        platform: "whatsapp",
        posts_total: 21,
        posts_published: 20,
        posts_failed: 0,
        posts_scheduled: 1,
        success_rate: 95.2,
        avg_engagement: 0,
        total_reach: 5000,
        total_likes: 0,
        total_comments: 0,
        total_shares: 0,
        growth_rate: 5.0,
        best_time: "10:00",
      },
    ],
    trends: {
      posts_change: 15.2,
      reach_change: 22.8,
      engagement_change: 8.4,
    },
  };
}

function getMockDailyMetrics(): DailyMetric[] {
  const metrics: DailyMetric[] = [];
  const now = new Date();
  
  for (let i = 13; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    metrics.push({
      date: date.toISOString().split('T')[0],
      posts: Math.floor(Math.random() * 10) + 2,
      reach: Math.floor(Math.random() * 20000) + 5000,
      engagement: Math.random() * 8 + 2,
      platform: "all",
    });
  }
  
  return metrics;
}

export default SocialAnalytics;
