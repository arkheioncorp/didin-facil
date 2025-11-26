import * as React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingIcon, ProductsIcon, FavoritesIcon, SearchIcon, SparkleIcon } from "@/components/icons";
import { ScraperControl } from "@/components/ScraperControl";
import { getUserStats, getSearchHistory } from "@/lib/tauri";
import type { DashboardStats } from "@/types";
import type { SearchHistoryItem } from "@/types";
import { useNavigate } from "react-router-dom";

const StatCard: React.FC<{
  title: string;
  value: string | number;
  description?: string;
  icon: React.ReactNode;
  trend?: { value: number; isPositive: boolean };
  isLoading?: boolean;
}> = ({ title, value, description, icon, trend, isLoading }) => (
  <Card data-testid="stats-card">
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      <div className="h-8 w-8 rounded-lg bg-tiktrend-primary/10 flex items-center justify-center text-tiktrend-primary">
        {icon}
      </div>
    </CardHeader>
    <CardContent>
      {isLoading ? (
        <Skeleton className="h-8 w-24" />
      ) : (
        <div className="text-2xl font-bold">{typeof value === 'number' ? value.toLocaleString("pt-BR") : value}</div>
      )}
      {description && (
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      )}
      {trend && (
        <div className="flex items-center gap-1 mt-2">
          <Badge variant={trend.isPositive ? "success" : "destructive"}>
            {trend.isPositive ? "+" : ""}{trend.value}%
          </Badge>
          <span className="text-xs text-muted-foreground">vs última semana</span>
        </div>
      )}
    </CardContent>
  </Card>
);

export const Dashboard: React.FC = () => {
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
        setError("Erro ao carregar dados do dashboard");
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
  }, []);

  const handleSearch = () => navigate("/search");
  const handleTrending = () => navigate("/products?trending=true");
  const handleCopy = () => navigate("/copy");

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="flex flex-col gap-2" data-testid="welcome-message">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Bem-vindo ao TikTrend Finder! Encontre os produtos mais vendidos do TikTok Shop.
        </p>
      </div>

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-4">
            <p className="text-destructive text-sm">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Produtos Coletados"
          value={stats?.totalProducts ?? 0}
          description="Total na base de dados"
          icon={<ProductsIcon size={18} />}
          isLoading={isLoading}
        />
        <StatCard
          title="Em Alta"
          value={stats?.trendingProducts ?? 0}
          description="Produtos trending agora"
          icon={<TrendingIcon size={18} />}
          trend={{ value: 12, isPositive: true }}
          isLoading={isLoading}
        />
        <StatCard
          title="Favoritos"
          value={stats?.favoriteCount ?? 0}
          description="Salvos para análise"
          icon={<FavoritesIcon size={18} />}
          isLoading={isLoading}
        />
        <StatCard
          title="Copies Geradas"
          value={stats?.copiesGenerated ?? 0}
          description="Textos criados com IA"
          icon={<SparkleIcon size={18} />}
          isLoading={isLoading}
        />
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="col-span-2" data-testid="quick-actions">
          <CardHeader>
            <CardTitle>Ações Rápidas</CardTitle>
            <CardDescription>
              Comece sua pesquisa de produtos ou gere copies para vendas
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-3 flex-wrap">
            <Button variant="tiktrend" className="gap-2" onClick={handleSearch}>
              <SearchIcon size={16} />
              Nova Busca
            </Button>
            <Button variant="outline" className="gap-2" onClick={handleTrending}>
              <TrendingIcon size={16} />
              Ver Trending
            </Button>
            <Button variant="outline" className="gap-2" onClick={handleCopy}>
              <SparkleIcon size={16} />
              Gerar Copy
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Scraper Control */}
      <div className="grid gap-4 md:grid-cols-3">
        <ScraperControl />

        <Card data-testid="trending-products">
          <CardHeader>
            <CardTitle>Top Categorias</CardTitle>
            <CardDescription>Mais produtos coletados</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-6 w-full" />
                ))}
              </div>
            ) : stats?.topCategories && stats.topCategories.length > 0 ? (
              <div className="space-y-3">
                {stats.topCategories.map((category, index) => (
                  <div key={category.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-muted-foreground">
                        {index + 1}.
                      </span>
                      <span className="text-sm">{category.name}</span>
                    </div>
                    <Badge variant="secondary">{category.count}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">
                Nenhuma categoria encontrada
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card data-testid="recent-products">
        <CardHeader>
          <CardTitle>Atividade Recente</CardTitle>
          <CardDescription>
            Suas últimas buscas e ações na plataforma
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : searchHistory.length > 0 ? (
            <div className="space-y-3">
              {searchHistory.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-3">
                    <SearchIcon size={16} className="text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{item.query || "Busca sem termo"}</p>
                      <div className="text-xs text-muted-foreground">
                        {item.resultsCount} resultados • {new Date(item.searchedAt).toLocaleDateString("pt-BR")}
                      </div>
                    </div>
                  </div>
                  <Badge variant="outline">{item.resultsCount}</Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <SearchIcon size={48} className="mx-auto mb-4 opacity-50" />
              <p>Nenhuma atividade recente</p>
              <p className="text-sm">Faça sua primeira busca para ver resultados aqui</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
