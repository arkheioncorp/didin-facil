import * as React from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingIcon, ProductsIcon, FavoritesIcon, SearchIcon, SparkleIcon } from "@/components/icons";
import { getUserStats, getSearchHistory } from "@/lib/tauri";
import type { DashboardStats } from "@/types";
import type { SearchHistoryItem } from "@/types";
import { useNavigate } from "react-router-dom";
import { UsageWidget } from "@/components/UsageWidget";

// Melhoria #22: Mini sparkline chart component
const MiniSparkline: React.FC<{ data: number[]; color?: string; height?: number }> = ({
  data,
  color = "var(--tiktrend-primary)",
  height = 32
}) => {
  if (data.length < 2) return null;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((value, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  const areaPoints = `0,${height} ${points} 100,${height}`;

  return (
    <svg viewBox={`0 0 100 ${height}`} className="w-full h-8 overflow-visible" preserveAspectRatio="none">
      <defs>
        <linearGradient id="sparklineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon
        points={areaPoints}
        fill="url(#sparklineGradient)"
      />
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
      {/* Last point indicator */}
      <circle
        cx="100"
        cy={height - ((data[data.length - 1] - min) / range) * height}
        r="3"
        fill={color}
        className="animate-pulse"
      />
    </svg>
  );
};

// Melhoria #4, #11: StatCard com gradiente e melhor espaçamento
const StatCard: React.FC<{
  title: string;
  value: string | number;
  description?: string;
  icon: React.ReactNode;
  trend?: { value: number; isPositive: boolean };
  sparklineData?: number[];
  isLoading?: boolean;
  gradient?: boolean;
  delay?: number;
}> = ({ title, value, description, icon, trend, sparklineData, isLoading, gradient, delay = 0 }) => (
  <Card
    data-testid="stats-card"
    className={`relative overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 ${gradient ? 'bg-gradient-to-br from-tiktrend-primary/5 via-transparent to-tiktrend-secondary/5' : ''}`}
    style={{ animationDelay: `${delay}ms` }}
  >
    {/* Decorative gradient blob */}
    {gradient && (
      <div className="absolute -top-10 -right-10 w-32 h-32 bg-gradient-to-br from-tiktrend-primary/10 to-tiktrend-secondary/10 rounded-full blur-2xl" />
    )}
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
      <CardTitle data-testid="stat-label" className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-tiktrend-primary/10 to-tiktrend-secondary/10 flex items-center justify-center text-tiktrend-primary shadow-sm">
        {icon}
      </div>
    </CardHeader>
    <CardContent>
      {isLoading ? (
        <Skeleton className="h-9 w-28" />
      ) : (
        <div data-testid="stat-value" className="text-3xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
          {typeof value === 'number' ? value.toLocaleString("pt-BR") : value}
        </div>
      )}
      {description && (
        <p className="text-sm text-muted-foreground mt-1.5">{description}</p>
      )}
      {/* Melhoria #22: Sparkline trend chart */}
      {sparklineData && sparklineData.length > 1 && (
        <div className="mt-3 opacity-70">
          <MiniSparkline
            data={sparklineData}
            color={trend?.isPositive ? "rgb(34, 197, 94)" : trend?.isPositive === false ? "rgb(239, 68, 68)" : "hsl(var(--tiktrend-primary))"}
          />
        </div>
      )}
      {trend && (
        <div className="flex items-center gap-2 mt-3">
          <Badge
            variant={trend.isPositive ? "success" : "destructive"}
            size="sm"
            className="font-medium"
          >
            {trend.isPositive ? "↑" : "↓"} {Math.abs(trend.value)}%
          </Badge>
          <span className="text-xs text-muted-foreground">vs última semana</span>
        </div>
      )}
    </CardContent>
  </Card>
);

export const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [stats, setStats] = React.useState<DashboardStats | null>(null);
  const [searchHistory, setSearchHistory] = React.useState<SearchHistoryItem[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const [statsData, historyData] = await Promise.all([
          getUserStats(),
          getSearchHistory(5),
        ]);

        setStats(statsData);
        setSearchHistory(historyData);
      } catch (err) {
        console.error("Error fetching dashboard data:", err);
        setError(t("errors.generic"));
        // Set default values on error
        setStats({
          totalProducts: 0,
          trendingProducts: 0,
          favoriteCount: 0,
          searchesToday: 0,
          copiesGenerated: 0,
          topCategories: [],
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [t]);

  const handleSearch = () => navigate("/search");
  const handleTrending = () => navigate("/products?trending=true");
  const handleCopy = () => navigate("/copy");

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Section - Melhoria #21: Onboarding visual */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4" data-testid="welcome-message">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
            {t("dashboard.title")}
          </h1>
          <p className="text-muted-foreground mt-1">
            {t("dashboard.subtitle")}
          </p>
        </div>
        {/* Quick action pill - Melhoria #21 */}
        <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-tiktrend-primary/10 to-tiktrend-secondary/10 border border-tiktrend-primary/20">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-tiktrend-primary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-tiktrend-primary"></span>
          </span>
          <span className="text-sm font-medium text-tiktrend-primary">{t("common.loading").replace("...", "")}</span>
        </div>
      </div>

      {error && (
        <Card className="border-destructive/50 bg-destructive/5 overflow-visible">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-destructive/10 flex items-center justify-center flex-shrink-0">
              <span className="text-destructive text-lg">!</span>
            </div>
            <p className="text-destructive text-sm break-words">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Stats Grid - Melhoria #4, #11 */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" data-testid="stats-grid">
        <StatCard
          title="Produtos Coletados"
          value={stats?.totalProducts ?? 0}
          description="Total na base de dados"
          icon={<ProductsIcon size={20} />}
          isLoading={isLoading}
          delay={0}
        />
        <StatCard
          title="Em Alta"
          value={stats?.trendingProducts ?? 0}
          description="Produtos trending agora"
          icon={<TrendingIcon size={20} />}
          trend={{ value: 12, isPositive: true }}
          sparklineData={[15, 23, 18, 35, 42, 38, 52]}
          isLoading={isLoading}
          gradient
          delay={50}
        />
        <StatCard
          title="Favoritos"
          value={stats?.favoriteCount ?? 0}
          description="Salvos para análise"
          icon={<FavoritesIcon size={20} />}
          sparklineData={[8, 12, 10, 15, 14, 18, 22]}
          isLoading={isLoading}
          delay={100}
        />
        <StatCard
          title="Copies Geradas"
          value={stats?.copiesGenerated ?? 0}
          description="Textos criados com IA"
          icon={<SparkleIcon size={20} />}
          isLoading={isLoading}
          delay={150}
        />
      </div>

      {/* Usage Widget */}
      <div className="w-full">
        <UsageWidget />
      </div>

      {/* Quick Actions - Melhoria visual */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="col-span-full lg:col-span-2 overflow-hidden relative" data-testid="quick-actions">
          <div className="absolute inset-0 bg-gradient-to-br from-tiktrend-primary/5 via-transparent to-tiktrend-secondary/5 pointer-events-none" />
          <CardHeader className="relative">
            <CardTitle className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-tiktrend-primary to-tiktrend-secondary flex items-center justify-center text-white text-sm">
                ⚡
              </span>
              Ações Rápidas
            </CardTitle>
            <CardDescription>
              Comece sua pesquisa de produtos ou gere copies para vendas
            </CardDescription>
          </CardHeader>
          <CardContent className="relative flex gap-3 flex-wrap">
            <Button variant="tiktrend" size="lg" className="gap-2 shadow-lg" onClick={handleSearch} data-testid="quick-search-btn" data-action="new-search">
              <SearchIcon size={18} />
              Nova Busca
            </Button>
            <Button variant="outline" size="lg" className="gap-2" onClick={handleTrending} data-testid="quick-trending-btn" data-action="trending">
              <TrendingIcon size={18} />
              Ver Trending
            </Button>
            <Button variant="outline" size="lg" className="gap-2" onClick={handleCopy} data-testid="quick-copy-btn" data-action="generate-copy">
              <SparkleIcon size={18} />
              Gerar Copy
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Quick Access to Collection & Categories */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Quick Access Card - Links to /coleta */}
        <Card className="group hover:border-tiktrend-primary/50 transition-all cursor-pointer" onClick={() => navigate("/coleta")} data-testid="quick-collect">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 group-hover:text-tiktrend-primary transition-colors">
              <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-tiktrend-primary to-tiktrend-secondary flex items-center justify-center text-white text-sm">
                🕷️
              </span>
              Coletar Produtos
            </CardTitle>
            <CardDescription>
              Acesse o painel de coleta do TikTok Shop
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Status:</span>
                <Badge variant="secondary">Pronto</Badge>
              </div>
              <Button variant="tiktrend" className="w-full gap-2">
                <ProductsIcon size={16} />
                Ir para Coleta
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card data-testid="trending-products" className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-tiktrend-primary animate-pulse" />
              Top Categorias
            </CardTitle>
            <CardDescription>Categorias com mais produtos coletados</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex items-center gap-3">
                    <Skeleton className="h-8 w-8 rounded-lg" />
                    <Skeleton className="h-4 flex-1" />
                    <Skeleton className="h-6 w-12 rounded-full" />
                  </div>
                ))}
              </div>
            ) : stats?.topCategories && stats.topCategories.length > 0 ? (
              <div className="space-y-2">
                {stats.topCategories.map((category, index) => (
                  <div
                    key={category.name}
                    className="flex items-center justify-between p-3 rounded-xl bg-muted/50 hover:bg-muted transition-colors cursor-pointer group"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-tiktrend-primary/20 to-tiktrend-secondary/20 flex items-center justify-center text-sm font-bold text-tiktrend-primary">
                        {index + 1}
                      </span>
                      <span className="font-medium group-hover:text-tiktrend-primary transition-colors">{category.name}</span>
                    </div>
                    <Badge variant="secondary" className="font-mono">{category.count}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state py-8">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4 mx-auto">
                  <TrendingIcon size={24} className="text-muted-foreground" />
                </div>
                <p className="text-muted-foreground">Nenhuma categoria encontrada</p>
                <p className="text-sm text-muted-foreground/60 mt-1">Execute o scraper para coletar produtos</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity - Melhoria #15: Empty states melhorados */}
      <Card data-testid="recent-products" className="overflow-hidden">
        <CardHeader className="border-b bg-muted/30">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Atividade Recente</CardTitle>
              <CardDescription>
                Suas últimas buscas e ações na plataforma
              </CardDescription>
            </div>
            {searchHistory.length > 0 && (
              <Badge variant="secondary" className="font-mono">{searchHistory.length}</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-4 p-3">
                  <Skeleton className="h-10 w-10 rounded-xl" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-1/3" />
                    <Skeleton className="h-3 w-1/4" />
                  </div>
                  <Skeleton className="h-6 w-16 rounded-full" />
                </div>
              ))}
            </div>
          ) : searchHistory.length > 0 ? (
            <div className="space-y-2">
              {searchHistory.map((item, index) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-4 rounded-xl bg-muted/30 hover:bg-muted/50 transition-all cursor-pointer group animate-slide-up"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-tiktrend-primary/10 to-tiktrend-secondary/10 flex items-center justify-center text-tiktrend-primary group-hover:scale-110 transition-transform">
                      <SearchIcon size={18} />
                    </div>
                    <div>
                      <p className="font-medium group-hover:text-tiktrend-primary transition-colors">
                        {item.query || "Busca sem termo"}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {item.resultsCount} resultados • {new Date(item.searchedAt).toLocaleDateString("pt-BR", { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline" className="font-mono group-hover:border-tiktrend-primary group-hover:text-tiktrend-primary transition-colors">
                    {item.resultsCount}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state py-12">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-tiktrend-primary/10 to-tiktrend-secondary/10 flex items-center justify-center mb-6 mx-auto">
                <SearchIcon size={32} className="text-tiktrend-primary/50" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Nenhuma atividade recente</h3>
              <p className="text-muted-foreground max-w-sm mx-auto">
                Faça sua primeira busca para ver os resultados aqui
              </p>
              <Button variant="tiktrend" className="mt-6" onClick={handleSearch}>
                <SearchIcon size={16} className="mr-2" />
                Começar Busca
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
