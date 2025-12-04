import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { YouTubeQuotaWidget } from "@/components/YouTubeQuotaWidget";
import { api } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { ptBR } from "date-fns/locale";
import {
  Instagram,
  Youtube,
  Video,
  MessageCircle,
  TrendingUp,
  Calendar,
  Users,
  BarChart3,
  ArrowRight,
  CheckCircle2,
  Clock,
  Zap,
  Crown,
  Sparkles,
  RefreshCw,
  AlertCircle,
  XCircle,
  Play,
  Loader2,
} from "lucide-react";

// ==================== Types ====================

interface ConnectedAccount {
  platform: string;
  account_name: string;
  username?: string;
  connected_at: string;
  expires_at?: string;
  status: "active" | "expired" | "revoked";
}

interface SchedulerStats {
  total: number;
  scheduled: number;
  published: number;
  failed: number;
  cancelled: number;
  retrying?: number;
  by_platform: Record<string, number>;
}

interface RecentActivity {
  id: string;
  type: "post_scheduled" | "post_published" | "post_failed" | "account_connected" | "account_disconnected";
  platform: string;
  title: string;
  timestamp: string;
  status?: string;
}

interface PlatformCard {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  connected: boolean;
  accountName?: string;
  stats: {
    posts: number;
    followers?: number;
    engagement?: number;
  };
  path: string;
  status?: "active" | "expired" | "revoked";
}

// ==================== Constants ====================

const PLATFORM_ICONS: Record<string, React.ReactNode> = {
  instagram: <Instagram className="h-6 w-6" />,
  tiktok: <Video className="h-6 w-6" />,
  youtube: <Youtube className="h-6 w-6" />,
  whatsapp: <MessageCircle className="h-6 w-6" />,
};

const PLATFORM_COLORS: Record<string, string> = {
  instagram: "from-pink-500 to-purple-500",
  tiktok: "from-black to-gray-800",
  youtube: "from-red-500 to-red-600",
  whatsapp: "from-green-500 to-green-600",
};

const PLATFORM_PATHS: Record<string, string> = {
  instagram: "/social/instagram",
  tiktok: "/social/tiktok",
  youtube: "/social/youtube",
  whatsapp: "/whatsapp",
};

const QUICK_ACTIONS = [
  {
    title: "Agendar Post",
    description: "Programe publicações para todas as redes",
    icon: <Calendar className="h-5 w-5" />,
    path: "/automation/scheduler",
  },
  {
    title: "Templates",
    description: "Crie e gerencie templates de conteúdo",
    icon: <Sparkles className="h-5 w-5" />,
    path: "/templates",
  },
  {
    title: "Ver Analytics",
    description: "Métricas unificadas de performance",
    icon: <BarChart3 className="h-5 w-5" />,
    path: "/admin/analytics",
  },
  {
    title: "Seller Bot",
    description: "Automatize sua Central do Vendedor",
    icon: <Zap className="h-5 w-5" />,
    path: "/seller-bot",
  },
];

const ACTIVITY_ICONS: Record<string, React.ReactNode> = {
  post_scheduled: <Calendar className="h-4 w-4 text-blue-500" />,
  post_published: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  post_failed: <XCircle className="h-4 w-4 text-red-500" />,
  account_connected: <Users className="h-4 w-4 text-green-500" />,
  account_disconnected: <Users className="h-4 w-4 text-orange-500" />,
};

// ==================== Component ====================

export const SocialDashboard = () => {
  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  
  const [schedulerStats, setSchedulerStats] = useState<SchedulerStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [platforms, setPlatforms] = useState<PlatformCard[]>([]);

  // Fetch all data
  const fetchData = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      // Fetch connected accounts
      const accountsResponse = await api.get<{ accounts: ConnectedAccount[] }>("/social-auth/accounts").catch(() => ({ data: { accounts: [] } }));
      const accounts = accountsResponse.data.accounts || [];

      // Fetch scheduler stats
      const statsResponse = await api.get<SchedulerStats>("/scheduler/stats").catch(() => ({ data: null }));
      setSchedulerStats(statsResponse.data);

      // Fetch recent posts for activity
      const postsResponse = await api.get<{ posts: Array<{ id: string; platform: string; status: string; caption: string; created_at: string; published_at?: string }> }>("/scheduler/posts?limit=10").catch(() => ({ data: { posts: [] } }));
      
      // Transform posts to activity
      const activities: RecentActivity[] = (postsResponse.data.posts || []).map(post => ({
        id: post.id,
        type: (post.status === "published" ? "post_published" : post.status === "failed" ? "post_failed" : "post_scheduled") as RecentActivity["type"],
        platform: post.platform,
        title: post.caption?.substring(0, 50) || "Post sem legenda",
        timestamp: post.published_at || post.created_at,
        status: post.status,
      }));
      setRecentActivity(activities);

      // Build platform cards
      const platformIds = ["instagram", "tiktok", "youtube", "whatsapp"];
      const platformCards: PlatformCard[] = platformIds.map(id => {
        const connectedAccount = accounts.find(a => a.platform === id);
        const postCount = statsResponse.data?.by_platform?.[id] || 0;
        
        return {
          id,
          name: id.charAt(0).toUpperCase() + id.slice(1),
          icon: PLATFORM_ICONS[id],
          color: PLATFORM_COLORS[id],
          connected: !!connectedAccount && connectedAccount.status === "active",
          accountName: connectedAccount?.username || connectedAccount?.account_name,
          stats: { posts: postCount },
          path: PLATFORM_PATHS[id],
          status: connectedAccount?.status,
        };
      });
      setPlatforms(platformCards);

    } catch (err) {
      console.error("Error fetching social dashboard data:", err);
      setError("Erro ao carregar dados. Tente novamente.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Calculate onboarding progress
  const connectedCount = platforms.filter(p => p.connected).length;
  const hasScheduledPosts = (schedulerStats?.scheduled || 0) > 0;
  const hasPublishedPosts = (schedulerStats?.published || 0) > 0;

  const onboardingSteps = [
    {
      title: "Conecte suas contas",
      description: "Instagram, TikTok, YouTube e WhatsApp",
      completed: connectedCount > 0,
      progress: Math.min((connectedCount / 4) * 100, 100),
    },
    {
      title: "Agende seu primeiro post",
      description: "Use o agendador para programar publicações",
      completed: hasScheduledPosts || hasPublishedPosts,
      progress: hasScheduledPosts || hasPublishedPosts ? 100 : 0,
    },
    {
      title: "Publique conteúdo",
      description: "Seu primeiro post será publicado automaticamente",
      completed: hasPublishedPosts,
      progress: hasPublishedPosts ? 100 : 0,
    },
  ];

  const overallProgress = Math.round(
    onboardingSteps.reduce((acc, step) => acc + step.progress, 0) / onboardingSteps.length
  );

  // Render loading skeleton
  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-9 w-64" />
            <Skeleton className="h-5 w-96 mt-2" />
          </div>
          <Skeleton className="h-6 w-20" />
        </div>
        <div className="grid gap-4 md:grid-cols-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-3 w-32 mt-2" />
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}>
              <CardHeader className="pb-3">
                <Skeleton className="h-10 w-10 rounded-lg" />
                <Skeleton className="h-5 w-24 mt-3" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Social Hub Central</h1>
          <p className="text-muted-foreground mt-1">
            Gerencie todas as suas redes sociais em um só lugar
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchData(true)}
            disabled={refreshing}
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            <span className="ml-2 hidden sm:inline">Atualizar</span>
          </Button>
          <Badge variant="secondary" className="flex items-center gap-1">
            <Crown className="h-3 w-3 text-yellow-500" />
            Premium
          </Badge>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <p className="text-sm text-destructive">{error}</p>
            <Button variant="outline" size="sm" onClick={() => fetchData(true)} className="ml-auto">
              Tentar novamente
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Posts Agendados</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{schedulerStats?.scheduled || 0}</div>
            <p className="text-xs text-muted-foreground">Aguardando publicação</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Contas Conectadas</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {connectedCount}/{platforms.length}
            </div>
            <p className="text-xs text-muted-foreground">Plataformas ativas</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Posts Publicados</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{schedulerStats?.published || 0}</div>
            <p className="text-xs text-muted-foreground">Total publicado</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              {(schedulerStats?.failed || 0) > 0 ? "Posts com Erro" : "Em Processamento"}
            </CardTitle>
            {(schedulerStats?.failed || 0) > 0 ? (
              <AlertCircle className="h-4 w-4 text-destructive" />
            ) : (
              <Clock className="h-4 w-4 text-muted-foreground" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(schedulerStats?.failed || 0) > 0 
                ? schedulerStats?.failed 
                : (schedulerStats?.retrying || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {(schedulerStats?.failed || 0) > 0 
                ? <Link to="/automation/dlq" className="text-destructive hover:underline">Ver na DLQ</Link>
                : "Em execução agora"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* YouTube Quota Widget */}
      <div className="grid gap-4 md:grid-cols-2">
        <YouTubeQuotaWidget compact className="md:col-span-1" />
      </div>

      {/* Platform Cards */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Suas Plataformas</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {platforms.map((platform) => (
            <Link key={platform.id} to={platform.path}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer group h-full">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div
                      className={`p-2 rounded-lg bg-gradient-to-r ${platform.color} text-white`}
                    >
                      {platform.icon}
                    </div>
                    {platform.connected ? (
                      <Badge 
                        variant="outline" 
                        className={
                          platform.status === "expired" 
                            ? "text-orange-600 border-orange-600" 
                            : "text-green-600 border-green-600"
                        }
                      >
                        {platform.status === "expired" ? (
                          <>
                            <AlertCircle className="h-3 w-3 mr-1" />
                            Expirado
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Conectado
                          </>
                        )}
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-muted-foreground">
                        Desconectado
                      </Badge>
                    )}
                  </div>
                  <CardTitle className="text-lg mt-3">{platform.name}</CardTitle>
                  {platform.accountName && (
                    <CardDescription className="text-xs">
                      @{platform.accountName}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>{platform.stats.posts} posts agendados</span>
                    <ArrowRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Ações Rápidas</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {QUICK_ACTIONS.map((action, index) => (
            <Link key={index} to={action.path}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10 text-primary">
                      {action.icon}
                    </div>
                    <div>
                      <CardTitle className="text-base">{action.title}</CardTitle>
                      <CardDescription className="text-xs">
                        {action.description}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Atividade Recente</CardTitle>
              <CardDescription>Últimas ações e publicações</CardDescription>
            </div>
            {recentActivity.length > 0 && (
              <Link to="/automation/scheduler">
                <Button variant="ghost" size="sm">
                  Ver tudo
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              </Link>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {recentActivity.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <Clock className="h-12 w-12 mb-4 opacity-50" />
              <p>Nenhuma atividade recente</p>
              <p className="text-sm">Conecte suas redes sociais para começar</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentActivity.slice(0, 5).map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                >
                  {ACTIVITY_ICONS[activity.type]}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{activity.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {activity.platform.charAt(0).toUpperCase() + activity.platform.slice(1)}
                    </p>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {formatDistanceToNow(new Date(activity.timestamp), {
                      addSuffix: true,
                      locale: ptBR,
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Getting Started / Onboarding */}
      {overallProgress < 100 && (
        <Card className="border-dashed">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-yellow-500" />
                  Começando
                </CardTitle>
                <CardDescription>
                  Complete os passos abaixo para configurar sua automação
                </CardDescription>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold">{overallProgress}%</div>
                <p className="text-xs text-muted-foreground">Progresso total</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {onboardingSteps.map((step, index) => (
              <div key={index} className="flex items-center gap-4">
                <div
                  className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                    step.completed
                      ? "bg-green-500 text-white"
                      : index === 0 || onboardingSteps[index - 1].completed
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {step.completed ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : (
                    index + 1
                  )}
                </div>
                <div className="flex-1">
                  <p className={`font-medium ${step.completed ? "text-muted-foreground line-through" : ""}`}>
                    {step.title}
                  </p>
                  <p className="text-sm text-muted-foreground">{step.description}</p>
                </div>
                <Progress value={step.progress} className="w-24" />
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Success State - All Setup Complete */}
      {overallProgress === 100 && (
        <Card className="border-green-500 bg-green-50 dark:bg-green-950/20">
          <CardContent className="flex items-center gap-4 py-6">
            <div className="p-3 rounded-full bg-green-500 text-white">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-green-700 dark:text-green-400">
                Configuração completa!
              </h3>
              <p className="text-sm text-green-600 dark:text-green-500">
                Você está pronto para automatizar suas redes sociais.
              </p>
            </div>
            <Link to="/automation/scheduler">
              <Button className="bg-green-600 hover:bg-green-700">
                <Play className="h-4 w-4 mr-2" />
                Agendar Post
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SocialDashboard;
