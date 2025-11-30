/**
 * CRM Dashboard
 * 
 * Dashboard principal do CRM com métricas, cards de resumo,
 * e acesso rápido às principais funcionalidades.
 */

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Users, UserPlus, Target, DollarSign, TrendingUp, ArrowRight,
  Plus, Activity, CheckCircle2, XCircle,
  ArrowUpRight, ArrowDownRight, Flame, Thermometer
} from "lucide-react";
import { Link } from "react-router-dom";

// Types
interface DashboardStats {
  contacts: {
    total: number;
    active: number;
    subscribed: number;
    new_30d: number;
  };
  leads: {
    total: number;
    new: number;
    qualified: number;
    won: number;
    lost: number;
    hot: number;
    warm: number;
    cold: number;
    pipeline_value: number;
  };
  deals: {
    total: number;
    open: number;
    won: number;
    lost: number;
    open_value: number;
    won_value: number;
    win_rate: number;
  };
  summary: {
    total_contacts: number;
    active_leads: number;
    open_deals: number;
    pipeline_value: number;
    win_rate: number;
    won_value: number;
  };
}

interface RecentActivity {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
}

// Mock data for development
const mockStats: DashboardStats = {
  contacts: {
    total: 1247,
    active: 1089,
    subscribed: 892,
    new_30d: 156,
  },
  leads: {
    total: 342,
    new: 45,
    qualified: 89,
    won: 67,
    lost: 23,
    hot: 28,
    warm: 56,
    cold: 50,
    pipeline_value: 245800.00,
  },
  deals: {
    total: 156,
    open: 42,
    won: 98,
    lost: 16,
    open_value: 187500.00,
    won_value: 523400.00,
    win_rate: 86,
  },
  summary: {
    total_contacts: 1247,
    active_leads: 134,
    open_deals: 42,
    pipeline_value: 187500.00,
    win_rate: 86,
    won_value: 523400.00,
  },
};

const mockActivities: RecentActivity[] = [
  {
    id: "1",
    type: "deal_won",
    title: "Deal fechado!",
    description: "Proposta #127 - João Silva - R$ 12.500,00",
    timestamp: "2 min atrás",
  },
  {
    id: "2",
    type: "lead_created",
    title: "Novo lead qualificado",
    description: "Maria Oliveira via Instagram",
    timestamp: "15 min atrás",
  },
  {
    id: "3",
    type: "contact_added",
    title: "Contato importado",
    description: "Pedro Santos - TechCorp LTDA",
    timestamp: "1 hora atrás",
  },
  {
    id: "4",
    type: "stage_changed",
    title: "Deal movido para Negociação",
    description: "Proposta #125 - Ana Costa",
    timestamp: "2 horas atrás",
  },
];

// Components
const StatCard = ({
  title,
  value,
  description,
  icon: Icon,
  trend,
  trendValue,
  variant = "default",
}: {
  title: string;
  value: string | number;
  description?: string;
  icon: React.ElementType;
  trend?: "up" | "down";
  trendValue?: string;
  variant?: "default" | "success" | "warning" | "danger";
}) => {
  const variantStyles = {
    default: "bg-card",
    success: "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800",
    warning: "bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800",
    danger: "bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800",
  };

  const iconStyles = {
    default: "bg-primary/10 text-primary",
    success: "bg-emerald-100 text-emerald-600 dark:bg-emerald-900 dark:text-emerald-400",
    warning: "bg-amber-100 text-amber-600 dark:bg-amber-900 dark:text-amber-400",
    danger: "bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400",
  };

  return (
    <Card className={variantStyles[variant]}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <div className="flex items-baseline gap-2 mt-1">
              <h3 className="text-2xl font-bold">{value}</h3>
              {trend && trendValue && (
                <span
                  className={`text-xs font-medium flex items-center ${
                    trend === "up" ? "text-emerald-600" : "text-red-600"
                  }`}
                >
                  {trend === "up" ? (
                    <ArrowUpRight className="w-3 h-3" />
                  ) : (
                    <ArrowDownRight className="w-3 h-3" />
                  )}
                  {trendValue}
                </span>
              )}
            </div>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          <div className={`p-3 rounded-full ${iconStyles[variant]}`}>
            <Icon className="w-5 h-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const LeadTemperatureCard = ({
  hot,
  warm,
  cold,
}: {
  hot: number;
  warm: number;
  cold: number;
}) => {
  const total = hot + warm + cold;
  
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <Thermometer className="w-4 h-4" />
          Temperatura dos Leads
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <Flame className="w-4 h-4 text-red-500" />
              <span>Hot</span>
            </div>
            <span className="font-medium">{hot}</span>
          </div>
          <Progress value={(hot / total) * 100} className="h-2 bg-red-100" />
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-amber-500" />
              <span>Warm</span>
            </div>
            <span className="font-medium">{warm}</span>
          </div>
          <Progress value={(warm / total) * 100} className="h-2 bg-amber-100" />
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-blue-500" />
              <span>Cold</span>
            </div>
            <span className="font-medium">{cold}</span>
          </div>
          <Progress value={(cold / total) * 100} className="h-2 bg-blue-100" />
        </div>
      </CardContent>
    </Card>
  );
};

const ActivityFeed = ({ activities }: { activities: RecentActivity[] }) => {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case "deal_won":
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case "deal_lost":
        return <XCircle className="w-4 h-4 text-red-500" />;
      case "lead_created":
        return <UserPlus className="w-4 h-4 text-blue-500" />;
      case "stage_changed":
        return <ArrowRight className="w-4 h-4 text-amber-500" />;
      default:
        return <Activity className="w-4 h-4 text-muted-foreground" />;
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <Activity className="w-4 h-4" />
          Atividades Recentes
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((activity) => (
            <div
              key={activity.id}
              className="flex items-start gap-3 pb-3 border-b last:border-0"
            >
              <div className="mt-1">{getActivityIcon(activity.type)}</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{activity.title}</p>
                <p className="text-xs text-muted-foreground truncate">
                  {activity.description}
                </p>
              </div>
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {activity.timestamp}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

const QuickActions = () => {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Ações Rápidas</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-2">
        <Button variant="outline" size="sm" className="justify-start" asChild>
          <Link to="/crm/contacts/new">
            <UserPlus className="w-4 h-4 mr-2" />
            Novo Contato
          </Link>
        </Button>
        <Button variant="outline" size="sm" className="justify-start" asChild>
          <Link to="/crm/deals/new">
            <Plus className="w-4 h-4 mr-2" />
            Novo Deal
          </Link>
        </Button>
        <Button variant="outline" size="sm" className="justify-start" asChild>
          <Link to="/crm/pipeline">
            <Target className="w-4 h-4 mr-2" />
            Ver Pipeline
          </Link>
        </Button>
        <Button variant="outline" size="sm" className="justify-start" asChild>
          <Link to="/crm/contacts">
            <Users className="w-4 h-4 mr-2" />
            Ver Contatos
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
};

// Main Component
export const CRMDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activities, setActivities] = useState<RecentActivity[]>([]);

  useEffect(() => {
    // Simulate API call
    const fetchData = async () => {
      try {
        // TODO: Replace with actual API call
        // const response = await fetch('/api/crm/dashboard');
        // const data = await response.json();
        
        // Using mock data for now
        await new Promise((resolve) => setTimeout(resolve, 500));
        setStats(mockStats);
        setActivities(mockActivities);
      } catch (error) {
        console.error("Failed to fetch CRM dashboard:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Erro ao carregar dados do CRM.</p>
        <Button onClick={() => window.location.reload()} className="mt-4">
          Tentar novamente
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">CRM Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Visão geral do seu funil de vendas e relacionamento com clientes
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to="/crm/pipeline">
              <Target className="w-4 h-4 mr-2" />
              Pipeline
            </Link>
          </Button>
          <Button asChild>
            <Link to="/crm/deals/new">
              <Plus className="w-4 h-4 mr-2" />
              Novo Deal
            </Link>
          </Button>
        </div>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total de Contatos"
          value={stats.summary.total_contacts.toLocaleString()}
          description={`${stats.contacts.new_30d} novos nos últimos 30 dias`}
          icon={Users}
          trend="up"
          trendValue="+12%"
        />
        <StatCard
          title="Leads Ativos"
          value={stats.summary.active_leads}
          description={`${stats.leads.hot} leads quentes`}
          icon={Target}
          variant={stats.leads.hot > 20 ? "success" : "default"}
          trend="up"
          trendValue="+8%"
        />
        <StatCard
          title="Deals Abertos"
          value={stats.summary.open_deals}
          description={formatCurrency(stats.summary.pipeline_value)}
          icon={DollarSign}
          variant="warning"
        />
        <StatCard
          title="Taxa de Conversão"
          value={`${stats.summary.win_rate}%`}
          description={`${formatCurrency(stats.summary.won_value)} ganhos`}
          icon={TrendingUp}
          variant="success"
          trend="up"
          trendValue="+3%"
        />
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Pipeline Summary */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Pipeline de Vendas</CardTitle>
                  <CardDescription>
                    Valor total: {formatCurrency(stats.deals.open_value)}
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm" asChild>
                  <Link to="/crm/pipeline">
                    Ver Pipeline Completo
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-4 text-center">
                <div className="p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
                  <p className="text-2xl font-bold">{stats.deals.open}</p>
                  <p className="text-xs text-muted-foreground">Em Andamento</p>
                </div>
                <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg">
                  <p className="text-2xl font-bold text-emerald-600">{stats.deals.won}</p>
                  <p className="text-xs text-muted-foreground">Ganhos</p>
                </div>
                <div className="p-4 bg-red-50 dark:bg-red-950/30 rounded-lg">
                  <p className="text-2xl font-bold text-red-600">{stats.deals.lost}</p>
                  <p className="text-xs text-muted-foreground">Perdidos</p>
                </div>
                <div className="p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">{stats.deals.total}</p>
                  <p className="text-xs text-muted-foreground">Total</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Leads Summary */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Leads por Status</CardTitle>
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/crm/leads">Ver Todos</Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline" className="px-3 py-1">
                  <span className="w-2 h-2 rounded-full bg-blue-500 mr-2" />
                  Novos: {stats.leads.new}
                </Badge>
                <Badge variant="outline" className="px-3 py-1">
                  <span className="w-2 h-2 rounded-full bg-amber-500 mr-2" />
                  Qualificados: {stats.leads.qualified}
                </Badge>
                <Badge variant="outline" className="px-3 py-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2" />
                  Convertidos: {stats.leads.won}
                </Badge>
                <Badge variant="outline" className="px-3 py-1">
                  <span className="w-2 h-2 rounded-full bg-red-500 mr-2" />
                  Perdidos: {stats.leads.lost}
                </Badge>
              </div>
              <div className="mt-4">
                <p className="text-sm text-muted-foreground">
                  Valor potencial no pipeline:{" "}
                  <span className="font-semibold text-foreground">
                    {formatCurrency(stats.leads.pipeline_value)}
                  </span>
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Contact Sources */}
          <Card>
            <CardHeader>
              <CardTitle>Contatos por Fonte</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { source: "Instagram", count: 342, icon: "📷" },
                  { source: "TikTok", count: 256, icon: "🎵" },
                  { source: "WhatsApp", count: 189, icon: "💬" },
                  { source: "Orgânico", count: 460, icon: "🌐" },
                ].map((item) => (
                  <div
                    key={item.source}
                    className="text-center p-3 border rounded-lg"
                  >
                    <span className="text-2xl">{item.icon}</span>
                    <p className="font-semibold mt-1">{item.count}</p>
                    <p className="text-xs text-muted-foreground">{item.source}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Sidebar */}
        <div className="space-y-6">
          <QuickActions />
          <LeadTemperatureCard
            hot={stats.leads.hot}
            warm={stats.leads.warm}
            cold={stats.leads.cold}
          />
          <ActivityFeed activities={activities} />
        </div>
      </div>
    </div>
  );
};

export default CRMDashboard;
