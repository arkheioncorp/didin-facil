import React from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { YouTubeQuotaWidget } from "@/components/YouTubeQuotaWidget";
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
} from "lucide-react";

interface PlatformCard {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  connected: boolean;
  stats?: {
    posts: number;
    followers?: number;
    engagement?: number;
  };
  path: string;
}

const platforms: PlatformCard[] = [
  {
    id: "instagram",
    name: "Instagram",
    icon: <Instagram className="h-6 w-6" />,
    color: "from-pink-500 to-purple-500",
    connected: false,
    stats: { posts: 0 },
    path: "/social/instagram",
  },
  {
    id: "tiktok",
    name: "TikTok",
    icon: <Video className="h-6 w-6" />,
    color: "from-black to-gray-800",
    connected: false,
    stats: { posts: 0 },
    path: "/social/tiktok",
  },
  {
    id: "youtube",
    name: "YouTube",
    icon: <Youtube className="h-6 w-6" />,
    color: "from-red-500 to-red-600",
    connected: false,
    stats: { posts: 0 },
    path: "/social/youtube",
  },
  {
    id: "whatsapp",
    name: "WhatsApp",
    icon: <MessageCircle className="h-6 w-6" />,
    color: "from-green-500 to-green-600",
    connected: false,
    stats: { posts: 0 },
    path: "/whatsapp",
  },
];

const quickActions = [
  {
    title: "Agendar Post",
    description: "Programe publicações para todas as redes",
    icon: <Calendar className="h-5 w-5" />,
    action: "/scheduler",
  },
  {
    title: "Gerar Conteúdo",
    description: "Crie vídeos e imagens automaticamente",
    icon: <Sparkles className="h-5 w-5" />,
    action: "/content-generator",
  },
  {
    title: "Ver Analytics",
    description: "Métricas unificadas de performance",
    icon: <BarChart3 className="h-5 w-5" />,
    action: "/analytics",
  },
  {
    title: "Seller Bot",
    description: "Automatize sua Central do Vendedor",
    icon: <Zap className="h-5 w-5" />,
    action: "/seller-bot",
  },
];

export const SocialDashboard = () => {
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
        <Badge variant="secondary" className="flex items-center gap-1">
          <Crown className="h-3 w-3 text-yellow-500" />
          Premium
        </Badge>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Posts Agendados</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-muted-foreground">Para esta semana</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Contas Conectadas</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {platforms.filter((p) => p.connected).length}/{platforms.length}
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
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-muted-foreground">Nos últimos 30 dias</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Tarefas Ativas</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-muted-foreground">Em execução agora</p>
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
              <Card className="hover:shadow-lg transition-shadow cursor-pointer group">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div
                      className={`p-2 rounded-lg bg-gradient-to-r ${platform.color} text-white`}
                    >
                      {platform.icon}
                    </div>
                    {platform.connected ? (
                      <Badge variant="outline" className="text-green-600 border-green-600">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Conectado
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-muted-foreground">
                        Desconectado
                      </Badge>
                    )}
                  </div>
                  <CardTitle className="text-lg mt-3">{platform.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>{platform.stats?.posts || 0} posts</span>
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
          {quickActions.map((action, index) => (
            <Link key={index} to={action.action}>
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
          <CardTitle>Atividade Recente</CardTitle>
          <CardDescription>Últimas ações e publicações</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Clock className="h-12 w-12 mb-4 opacity-50" />
            <p>Nenhuma atividade recente</p>
            <p className="text-sm">Conecte suas redes sociais para começar</p>
          </div>
        </CardContent>
      </Card>

      {/* Getting Started */}
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-yellow-500" />
            Começando
          </CardTitle>
          <CardDescription>
            Complete os passos abaixo para configurar sua automação
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-medium">
              1
            </div>
            <div className="flex-1">
              <p className="font-medium">Conecte suas contas</p>
              <p className="text-sm text-muted-foreground">
                Instagram, TikTok, YouTube e WhatsApp
              </p>
            </div>
            <Progress value={0} className="w-24" />
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted text-muted-foreground text-sm font-medium">
              2
            </div>
            <div className="flex-1">
              <p className="font-medium">Configure o Seller Bot</p>
              <p className="text-sm text-muted-foreground">
                Automatize sua Central do Vendedor TikTok
              </p>
            </div>
            <Progress value={0} className="w-24" />
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted text-muted-foreground text-sm font-medium">
              3
            </div>
            <div className="flex-1">
              <p className="font-medium">Crie seu primeiro conteúdo</p>
              <p className="text-sm text-muted-foreground">
                Use o gerador para criar vídeos automaticamente
              </p>
            </div>
            <Progress value={0} className="w-24" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
