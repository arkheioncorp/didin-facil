import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  RefreshCw,
  Server,
  Zap,
  Inbox,
  Users,
  ExternalLink,
} from "lucide-react";
import { api } from "@/lib/api";

interface SystemMetrics {
  workers_active: number;
  posts_pending: number;
  posts_processing: number;
  posts_completed: number;
  posts_failed: number;
  dlq_size: number;
  api_response_time_avg_ms: number;
  api_requests_total: number;
  api_errors_5xx: number;
  api_errors_4xx: number;
  rate_limit_blocked: number;
  youtube_quota_used: number;
  youtube_quota_limit: number;
  platforms: {
    youtube: { sessions: number; posts_today: number };
    instagram: { sessions: number; posts_today: number; challenges: number };
    tiktok: { sessions: number; posts_today: number };
    whatsapp: { sessions: number; messages_today: number };
  };
}

async function fetchMetrics(): Promise<SystemMetrics> {
  // Parse Prometheus format and convert to object
  const response = await api.get("/metrics");
  const text = response.data as string;
  
  // Helper to extract metric value
  const extractMetric = (name: string, labels?: string): number => {
    const pattern = labels 
      ? new RegExp(`${name}\\{[^}]*${labels}[^}]*\\}\\s+([\\d.]+)`)
      : new RegExp(`${name}\\s+([\\d.]+)`);
    const match = text.match(pattern);
    return match ? parseFloat(match[1]) : 0;
  };

  return {
    workers_active: extractMetric("tiktrend_workers_active"),
    posts_pending: extractMetric("tiktrend_posts_pending"),
    posts_processing: extractMetric("tiktrend_posts_processing"),
    posts_completed: extractMetric("tiktrend_posts_completed_total"),
    posts_failed: extractMetric("tiktrend_posts_failed_total"),
    dlq_size: extractMetric("tiktrend_dlq_size"),
    api_response_time_avg_ms: extractMetric("tiktrend_api_response_time_avg_ms"),
    api_requests_total: extractMetric("tiktrend_api_requests_total"),
    api_errors_5xx: extractMetric("tiktrend_api_errors_5xx_total"),
    api_errors_4xx: extractMetric("tiktrend_api_errors_4xx_total"),
    rate_limit_blocked: extractMetric("tiktrend_rate_limit_blocked_total"),
    youtube_quota_used: extractMetric("tiktrend_youtube_quota_used"),
    youtube_quota_limit: extractMetric("tiktrend_youtube_quota_limit"),
    platforms: {
      youtube: {
        sessions: extractMetric("tiktrend_platform_sessions_active", 'platform="youtube"'),
        posts_today: extractMetric("tiktrend_platform_posts_today", 'platform="youtube"'),
      },
      instagram: {
        sessions: extractMetric("tiktrend_platform_sessions_active", 'platform="instagram"'),
        posts_today: extractMetric("tiktrend_platform_posts_today", 'platform="instagram"'),
        challenges: extractMetric("tiktrend_instagram_challenges_pending"),
      },
      tiktok: {
        sessions: extractMetric("tiktrend_platform_sessions_active", 'platform="tiktok"'),
        posts_today: extractMetric("tiktrend_platform_posts_today", 'platform="tiktok"'),
      },
      whatsapp: {
        sessions: extractMetric("tiktrend_platform_sessions_active", 'platform="whatsapp"'),
        messages_today: extractMetric("tiktrend_platform_posts_today", 'platform="whatsapp"'),
      },
    },
  };
}

function MetricCard({
  title,
  value,
  icon: Icon,
  description,
  status = "normal",
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  description?: string;
  status?: "normal" | "warning" | "error" | "success";
}) {
  const statusColors = {
    normal: "text-muted-foreground",
    warning: "text-yellow-500",
    error: "text-red-500",
    success: "text-green-500",
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-4 w-4 ${statusColors[status]}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

export function SystemMetricsDashboard() {
  const { data: metrics, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ["system-metrics"],
    queryFn: fetchMetrics,
    refetchInterval: 30000, // 30 segundos
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!metrics) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-8">
          <p className="text-muted-foreground">Não foi possível carregar métricas</p>
        </CardContent>
      </Card>
    );
  }

  const youtubeQuotaPercent = (metrics.youtube_quota_used / metrics.youtube_quota_limit) * 100;
  const errorRate = metrics.api_requests_total > 0 
    ? ((metrics.api_errors_5xx + metrics.api_errors_4xx) / metrics.api_requests_total) * 100 
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Métricas do Sistema</h2>
          <p className="text-muted-foreground">
            Monitoramento em tempo real da aplicação
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          <Button variant="outline" size="sm" asChild>
            <a href="http://localhost:3001" target="_blank" rel="noopener noreferrer">
              <ExternalLink className="h-4 w-4 mr-2" />
              Grafana
            </a>
          </Button>
        </div>
      </div>

      {/* Workers & Posts */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Workers Ativos"
          value={metrics.workers_active}
          icon={Server}
          description="Processos de background"
          status={metrics.workers_active > 0 ? "success" : "error"}
        />
        <MetricCard
          title="Posts Pendentes"
          value={metrics.posts_pending}
          icon={Clock}
          description="Aguardando processamento"
        />
        <MetricCard
          title="Posts Completos"
          value={metrics.posts_completed}
          icon={CheckCircle}
          status="success"
          description="Publicados com sucesso"
        />
        <MetricCard
          title="Dead Letter Queue"
          value={metrics.dlq_size}
          icon={Inbox}
          description="Posts com falha"
          status={metrics.dlq_size > 0 ? "error" : "normal"}
        />
      </div>

      {/* API Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Performance da API
          </CardTitle>
          <CardDescription>
            Métricas de latência e taxa de erros
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <p className="text-sm font-medium">Latência Média</p>
              <p className="text-2xl font-bold">
                {metrics.api_response_time_avg_ms.toFixed(1)}ms
              </p>
              <Badge
                variant={metrics.api_response_time_avg_ms < 100 ? "default" : "destructive"}
              >
                {metrics.api_response_time_avg_ms < 100 ? "Ótimo" : 
                 metrics.api_response_time_avg_ms < 300 ? "Bom" : "Lento"}
              </Badge>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Total Requests</p>
              <p className="text-2xl font-bold">
                {metrics.api_requests_total.toLocaleString()}
              </p>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Taxa de Erros</p>
              <p className="text-2xl font-bold">{errorRate.toFixed(2)}%</p>
              <div className="flex gap-2">
                <Badge variant="destructive">5xx: {metrics.api_errors_5xx}</Badge>
                <Badge variant="secondary">4xx: {metrics.api_errors_4xx}</Badge>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Rate Limit Bloqueados</p>
              <p className="text-2xl font-bold">{metrics.rate_limit_blocked}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* YouTube Quota */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-red-500" />
            YouTube API Quota
          </CardTitle>
          <CardDescription>
            Uso diário da quota da API do YouTube
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex justify-between text-sm">
            <span>Usado: {metrics.youtube_quota_used.toLocaleString()}</span>
            <span>Limite: {metrics.youtube_quota_limit.toLocaleString()}</span>
          </div>
          <Progress
            value={youtubeQuotaPercent}
            className={
              youtubeQuotaPercent > 90 ? "bg-red-200" :
              youtubeQuotaPercent > 70 ? "bg-yellow-200" : ""
            }
          />
          <div className="flex justify-between items-center">
            <Badge
              variant={
                youtubeQuotaPercent > 90 ? "destructive" :
                youtubeQuotaPercent > 70 ? "secondary" : "default"
              }
            >
              {youtubeQuotaPercent.toFixed(1)}% usado
            </Badge>
            <span className="text-sm text-muted-foreground">
              {(metrics.youtube_quota_limit - metrics.youtube_quota_used).toLocaleString()} restante
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Platforms */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Plataformas
          </CardTitle>
          <CardDescription>
            Sessões ativas e posts por plataforma
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            {/* YouTube */}
            <div className="space-y-2 p-4 border rounded-lg">
              <div className="flex items-center justify-between">
                <span className="font-medium">YouTube</span>
                <Badge variant={metrics.platforms.youtube.sessions > 0 ? "default" : "secondary"}>
                  {metrics.platforms.youtube.sessions} sessões
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                {metrics.platforms.youtube.posts_today} posts hoje
              </p>
            </div>

            {/* Instagram */}
            <div className="space-y-2 p-4 border rounded-lg">
              <div className="flex items-center justify-between">
                <span className="font-medium">Instagram</span>
                <Badge variant={metrics.platforms.instagram.sessions > 0 ? "default" : "secondary"}>
                  {metrics.platforms.instagram.sessions} sessões
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                {metrics.platforms.instagram.posts_today} posts hoje
              </p>
              {metrics.platforms.instagram.challenges > 0 && (
                <div className="flex items-center gap-1 text-yellow-500">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm">
                    {metrics.platforms.instagram.challenges} challenges
                  </span>
                </div>
              )}
            </div>

            {/* TikTok */}
            <div className="space-y-2 p-4 border rounded-lg">
              <div className="flex items-center justify-between">
                <span className="font-medium">TikTok</span>
                <Badge variant={metrics.platforms.tiktok.sessions > 0 ? "default" : "secondary"}>
                  {metrics.platforms.tiktok.sessions} sessões
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                {metrics.platforms.tiktok.posts_today} posts hoje
              </p>
            </div>

            {/* WhatsApp */}
            <div className="space-y-2 p-4 border rounded-lg">
              <div className="flex items-center justify-between">
                <span className="font-medium">WhatsApp</span>
                <Badge variant={metrics.platforms.whatsapp.sessions > 0 ? "default" : "secondary"}>
                  {metrics.platforms.whatsapp.sessions} sessões
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                {metrics.platforms.whatsapp.messages_today} msgs hoje
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default SystemMetricsDashboard;
