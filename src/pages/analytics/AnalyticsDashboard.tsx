import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import {
  BarChart3,
  TrendingUp,
  Users,
  Eye,
  Heart,
  MessageCircle,
  Share2,
  Download,
  Calendar,
  Instagram,
  Youtube,
  Video,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { api } from '@/lib/api';

interface PlatformMetrics {
  platform: string;
  followers: number;
  followers_change: number;
  posts: number;
  engagement_rate: number;
  impressions: number;
  reach: number;
}

interface EngagementStats {
  total_likes: number;
  total_comments: number;
  total_shares: number;
  total_saves: number;
  avg_engagement_rate: number;
  best_performing_day: string;
  best_performing_time: string;
}

interface ContentPerformance {
  id: string;
  title: string;
  platform: string;
  type: string;
  likes: number;
  comments: number;
  shares: number;
  views: number;
  engagement_rate: number;
  posted_at: string;
}

interface AudienceInsights {
  total_audience: number;
  growth_rate: number;
  demographics: {
    age_groups: Record<string, number>;
    gender: Record<string, number>;
    top_locations: Record<string, number>;
  };
  active_hours: number[];
}

interface AnalyticsOverview {
  period: {
    start: string;
    end: string;
    days: number;
  };
  platforms: PlatformMetrics[];
  engagement: EngagementStats;
  top_content: ContentPerformance[];
  audience: AudienceInsights;
}

const platformIcons: Record<string, React.ReactNode> = {
  instagram: <Instagram className="h-4 w-4" />,
  youtube: <Youtube className="h-4 w-4" />,
  tiktok: <Video className="h-4 w-4" />,
};

const platformColors: Record<string, string> = {
  instagram: 'bg-gradient-to-r from-purple-500 to-pink-500',
  youtube: 'bg-red-500',
  tiktok: 'bg-black',
};

function MetricCard({
  title,
  value,
  change,
  icon,
  suffix = '',
}: {
  title: string;
  value: number | string;
  change?: number;
  icon: React.ReactNode;
  suffix?: string;
}) {
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {typeof value === 'number' ? value.toLocaleString('pt-BR') : value}
          {suffix}
        </div>
        {change !== undefined && (
          <p className={`text-xs flex items-center gap-1 ${isPositive ? 'text-green-500' : isNegative ? 'text-red-500' : 'text-muted-foreground'}`}>
            {isPositive ? <ArrowUpRight className="h-3 w-3" /> : isNegative ? <ArrowDownRight className="h-3 w-3" /> : null}
            {change > 0 ? '+' : ''}{change}% vs período anterior
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function PlatformCard({ platform }: { platform: PlatformMetrics }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-3 pb-2">
        <div className={`p-2 rounded-lg text-white ${platformColors[platform.platform] || 'bg-gray-500'}`}>
          {platformIcons[platform.platform] || <BarChart3 className="h-4 w-4" />}
        </div>
        <div>
          <CardTitle className="text-base capitalize">{platform.platform}</CardTitle>
          <CardDescription>
            {platform.followers.toLocaleString('pt-BR')} seguidores
          </CardDescription>
        </div>
        <Badge variant={platform.followers_change >= 0 ? 'default' : 'destructive'} className="ml-auto">
          {platform.followers_change >= 0 ? '+' : ''}{platform.followers_change}%
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Posts</span>
          <span className="font-medium">{platform.posts}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Engajamento</span>
          <span className="font-medium">{platform.engagement_rate}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Impressões</span>
          <span className="font-medium">{platform.impressions.toLocaleString('pt-BR')}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Alcance</span>
          <span className="font-medium">{platform.reach.toLocaleString('pt-BR')}</span>
        </div>
      </CardContent>
    </Card>
  );
}

function TopContentTable({ content }: { content: ContentPerformance[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Top Conteúdos
        </CardTitle>
        <CardDescription>Melhores posts por engajamento</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {content.map((item, index) => (
            <div key={item.id} className="flex items-center gap-4 p-3 rounded-lg bg-muted/50">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-bold">
                {index + 1}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{item.title}</p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="capitalize">{item.platform}</span>
                  <span>•</span>
                  <span>{new Date(item.posted_at).toLocaleDateString('pt-BR')}</span>
                </div>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1">
                  <Heart className="h-3 w-3 text-red-500" />
                  <span>{item.likes.toLocaleString('pt-BR')}</span>
                </div>
                <div className="flex items-center gap-1">
                  <MessageCircle className="h-3 w-3 text-blue-500" />
                  <span>{item.comments.toLocaleString('pt-BR')}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Eye className="h-3 w-3 text-green-500" />
                  <span>{item.views.toLocaleString('pt-BR')}</span>
                </div>
              </div>
              <Badge variant="outline">{item.engagement_rate}%</Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function AudienceCard({ audience }: { audience: AudienceInsights }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          Audiência
        </CardTitle>
        <CardDescription>Insights do seu público</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium">Total de Seguidores</span>
            <span className="text-sm text-muted-foreground">
              {audience.growth_rate >= 0 ? '+' : ''}{audience.growth_rate}% crescimento
            </span>
          </div>
          <p className="text-3xl font-bold">{audience.total_audience.toLocaleString('pt-BR')}</p>
        </div>

        <div>
          <h4 className="text-sm font-medium mb-3">Faixas Etárias</h4>
          <div className="space-y-2">
            {Object.entries(audience.demographics.age_groups).map(([age, percentage]) => (
              <div key={age} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>{age}</span>
                  <span>{percentage}%</span>
                </div>
                <Progress value={percentage} className="h-2" />
              </div>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-sm font-medium mb-3">Gênero</h4>
          <div className="flex gap-4">
            {Object.entries(audience.demographics.gender).map(([gender, percentage]) => (
              <div key={gender} className="flex-1 text-center p-3 rounded-lg bg-muted">
                <p className="text-2xl font-bold">{percentage}%</p>
                <p className="text-xs text-muted-foreground capitalize">{gender}</p>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-sm font-medium mb-3">Top Localizações</h4>
          <div className="space-y-2">
            {Object.entries(audience.demographics.top_locations).slice(0, 5).map(([location, count]) => (
              <div key={location} className="flex justify-between text-sm">
                <span>{location}</span>
                <span className="text-muted-foreground">{count.toLocaleString('pt-BR')}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function EngagementCard({ engagement }: { engagement: EngagementStats }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Heart className="h-5 w-5" />
          Engajamento
        </CardTitle>
        <CardDescription>Métricas de interação</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Heart className="h-4 w-4 text-red-500" />
              <span className="text-sm text-muted-foreground">Likes</span>
            </div>
            <p className="text-xl font-bold">{engagement.total_likes.toLocaleString('pt-BR')}</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <MessageCircle className="h-4 w-4 text-blue-500" />
              <span className="text-sm text-muted-foreground">Comentários</span>
            </div>
            <p className="text-xl font-bold">{engagement.total_comments.toLocaleString('pt-BR')}</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Share2 className="h-4 w-4 text-green-500" />
              <span className="text-sm text-muted-foreground">Compartilhamentos</span>
            </div>
            <p className="text-xl font-bold">{engagement.total_shares.toLocaleString('pt-BR')}</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Download className="h-4 w-4 text-purple-500" />
              <span className="text-sm text-muted-foreground">Salvos</span>
            </div>
            <p className="text-xl font-bold">{engagement.total_saves.toLocaleString('pt-BR')}</p>
          </div>
        </div>
        
        <div className="mt-6 pt-4 border-t space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Taxa média de engajamento</span>
            <span className="font-bold text-green-500">{engagement.avg_engagement_rate}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Melhor dia para postar</span>
            <span className="font-medium">{engagement.best_performing_day}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Melhor horário</span>
            <span className="font-medium">{engagement.best_performing_time}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function AnalyticsDashboard() {
  const [period, setPeriod] = useState('30d');
  const [_platform] = useState('all');

  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics', period, _platform],
    queryFn: async () => {
      const params = new URLSearchParams();
      
      // Calculate dates based on period
      const endDate = new Date();
      const startDate = new Date();
      
      if (period === '7d') startDate.setDate(startDate.getDate() - 7);
      else if (period === '30d') startDate.setDate(startDate.getDate() - 30);
      else if (period === '90d') startDate.setDate(startDate.getDate() - 90);
      
      params.set('start_date', startDate.toISOString().split('T')[0]);
      params.set('end_date', endDate.toISOString().split('T')[0]);
      
      const response = await api.get<AnalyticsOverview>(`/analytics/overview?${params}`);
      return response.data;
    },
  });

  const handleExport = async () => {
    try {
      const response = await api.get<Blob>('/analytics/export', {
        params: { format: 'csv' },
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data as BlobPart]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `analytics-${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  if (error) {
    return (
      <div className="p-6">
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">Erro ao carregar analytics. Tente novamente.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">
            Acompanhe o desempenho das suas redes sociais
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[180px]">
              <Calendar className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Período" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Últimos 7 dias</SelectItem>
              <SelectItem value="30d">Últimos 30 dias</SelectItem>
              <SelectItem value="90d">Últimos 90 dias</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array(4).fill(0).map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-32" />
                <Skeleton className="h-3 w-20 mt-2" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : data && (
        <>
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="Total de Seguidores"
              value={data.audience.total_audience}
              change={data.audience.growth_rate}
              icon={<Users className="h-4 w-4 text-muted-foreground" />}
            />
            <MetricCard
              title="Taxa de Engajamento"
              value={data.engagement.avg_engagement_rate}
              suffix="%"
              icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
            />
            <MetricCard
              title="Total de Likes"
              value={data.engagement.total_likes}
              icon={<Heart className="h-4 w-4 text-muted-foreground" />}
            />
            <MetricCard
              title="Total de Comentários"
              value={data.engagement.total_comments}
              icon={<MessageCircle className="h-4 w-4 text-muted-foreground" />}
            />
          </div>

          {/* Main Content */}
          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview">Visão Geral</TabsTrigger>
              <TabsTrigger value="platforms">Plataformas</TabsTrigger>
              <TabsTrigger value="content">Conteúdo</TabsTrigger>
              <TabsTrigger value="audience">Audiência</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {data.platforms.map((platform) => (
                  <PlatformCard key={platform.platform} platform={platform} />
                ))}
              </div>
              <TopContentTable content={data.top_content} />
            </TabsContent>

            <TabsContent value="platforms" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {data.platforms.map((platform) => (
                  <PlatformCard key={platform.platform} platform={platform} />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="content" className="space-y-4">
              <TopContentTable content={data.top_content} />
            </TabsContent>

            <TabsContent value="audience" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <AudienceCard audience={data.audience} />
                <EngagementCard engagement={data.engagement} />
              </div>
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
}
