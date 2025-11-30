import * as React from "react";
import { useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Badge,
  Separator,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Button,
} from "@/components/ui";
import { Layout } from "@/components/layout/Layout";
import {
  getAdminDashboard,
  getDailyReports,
  getUsersLTV,
  getOperationCosts,
  type DashboardMetrics,
  type DailyReport,
  type UserLTV,
  type OperationCost,
} from "@/services/accounting";

export function FinancialDashboard() {
  const navigate = useNavigate();
  
  const [dashboard, setDashboard] = React.useState<DashboardMetrics | null>(null);
  const [dailyReports, setDailyReports] = React.useState<DailyReport[]>([]);
  const [userLTV, setUserLTV] = React.useState<UserLTV[]>([]);
  const [operationCosts, setOperationCosts] = React.useState<OperationCost[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [activeTab, setActiveTab] = React.useState("overview");

  React.useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const [dashData, costs] = await Promise.all([
        getAdminDashboard(),
        getOperationCosts(),
      ]);
      
      setDashboard(dashData);
      setOperationCosts(costs);
      
      // Load last 7 days reports
      const endDate = new Date().toISOString().split("T")[0];
      const startDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0];
      const reports = await getDailyReports(startDate, endDate);
      setDailyReports(reports);
      
    } catch (err) {
      console.error("Error loading dashboard:", err);
      if (err instanceof Error && err.message === "Admin access required") {
        setError("Acesso administrativo necessário");
      } else {
        setError("Erro ao carregar dados financeiros");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const loadUserLTV = async () => {
    try {
      const ltv = await getUsersLTV(50);
      setUserLTV(ltv);
    } catch (err) {
      console.error("Error loading LTV:", err);
    }
  };

  // Format currency
  const formatBRL = (value: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value);
  };

  // Format percentage
  const formatPercent = (value: number) => {
    return `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;
  };

  // Growth indicator
  const GrowthBadge = ({ value }: { value: number }) => (
    <Badge variant={value >= 0 ? "default" : "destructive"} className="ml-2">
      {formatPercent(value)}
    </Badge>
  );

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-tiktrend-primary" />
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
          <p className="text-destructive">{error}</p>
          <Button onClick={() => navigate("/")}>Voltar ao Dashboard</Button>
        </div>
      </Layout>
    );
  }

  if (!dashboard) return null;

  return (
    <Layout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">💰 Dashboard Financeiro</h1>
            <p className="text-muted-foreground">
              Visão geral de receita, custos e lucros
            </p>
          </div>
          <Button variant="outline" onClick={loadDashboard}>
            🔄 Atualizar
          </Button>
        </div>

        {/* KPI Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          {/* Today Revenue */}
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Receita Hoje</CardDescription>
              <CardTitle className="text-2xl">
                {formatBRL(dashboard.today.revenue_brl)}
                <GrowthBadge value={dashboard.growth.revenue_day_over_day} />
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Ontem: {formatBRL(dashboard.yesterday.revenue_brl)}
              </p>
            </CardContent>
          </Card>

          {/* Today Profit */}
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Lucro Hoje</CardDescription>
              <CardTitle className="text-2xl text-green-600">
                {formatBRL(dashboard.today.profit_brl)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Margem: {dashboard.today.profit_margin.toFixed(1)}%
              </p>
            </CardContent>
          </Card>

          {/* Month Revenue */}
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Receita do Mês</CardDescription>
              <CardTitle className="text-2xl">
                {formatBRL(dashboard.this_month.revenue_brl)}
                <GrowthBadge value={dashboard.growth.revenue_month_over_month} />
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Mês anterior: {formatBRL(dashboard.last_month.revenue_brl)}
              </p>
            </CardContent>
          </Card>

          {/* Month Profit */}
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Lucro do Mês</CardDescription>
              <CardTitle className="text-2xl text-green-600">
                {formatBRL(dashboard.this_month.profit_brl)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Custo: {formatBRL(dashboard.this_month.cost_brl)}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="overview">Visão Geral</TabsTrigger>
            <TabsTrigger value="operations">Operações</TabsTrigger>
            <TabsTrigger value="users" onClick={loadUserLTV}>
              Usuários
            </TabsTrigger>
            <TabsTrigger value="daily">Relatórios Diários</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              {/* Today Details */}
              <Card>
                <CardHeader>
                  <CardTitle>📊 Métricas de Hoje</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Operações</span>
                    <span className="font-bold">
                      {dashboard.today.total_operations}
                    </span>
                  </div>
                  <Separator />
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Tokens usados</span>
                    <span className="font-bold">
                      {dashboard.today.total_tokens.toLocaleString()}
                    </span>
                  </div>
                  <Separator />
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">
                      Compras de crédito
                    </span>
                    <span className="font-bold">
                      {dashboard.today.credit_purchases}
                    </span>
                  </div>
                  <Separator />
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Créditos usados</span>
                    <span className="font-bold">
                      {dashboard.today.credits_used}
                    </span>
                  </div>
                  <Separator />
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Novos usuários</span>
                    <span className="font-bold text-green-600">
                      +{dashboard.today.new_users}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Usuários ativos</span>
                    <span className="font-bold">
                      {dashboard.today.active_users}
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Monthly Details */}
              <Card>
                <CardHeader>
                  <CardTitle>📈 Métricas do Mês</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">MRR</span>
                    <span className="font-bold text-tiktrend-primary">
                      {formatBRL(dashboard.this_month.mrr)}
                    </span>
                  </div>
                  <Separator />
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">ARPU</span>
                    <span className="font-bold">
                      {formatBRL(dashboard.this_month.arpu)}
                    </span>
                  </div>
                  <Separator />
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">
                      Total operações
                    </span>
                    <span className="font-bold">
                      {dashboard.this_month.total_operations}
                    </span>
                  </div>
                  <Separator />
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">
                      Compras de crédito
                    </span>
                    <span className="font-bold">
                      {dashboard.this_month.credit_purchases}
                    </span>
                  </div>
                  <Separator />
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Novos usuários</span>
                    <span className="font-bold text-green-600">
                      +{dashboard.this_month.new_users}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* P&L Summary */}
            <Card>
              <CardHeader>
                <CardTitle>💵 Demonstração de Resultado</CardTitle>
                <CardDescription>Este mês vs mês anterior</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3">Item</th>
                        <th className="text-right py-3">Este Mês</th>
                        <th className="text-right py-3">Mês Anterior</th>
                        <th className="text-right py-3">Variação</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b">
                        <td className="py-3">Receita Bruta</td>
                        <td className="text-right font-medium">
                          {formatBRL(dashboard.this_month.revenue_brl)}
                        </td>
                        <td className="text-right text-muted-foreground">
                          {formatBRL(dashboard.last_month.revenue_brl)}
                        </td>
                        <td className="text-right">
                          <GrowthBadge
                            value={dashboard.growth.revenue_month_over_month}
                          />
                        </td>
                      </tr>
                      <tr className="border-b">
                        <td className="py-3 text-red-600">(-) Custos OpenAI</td>
                        <td className="text-right text-red-600">
                          {formatBRL(dashboard.this_month.cost_brl)}
                        </td>
                        <td className="text-right text-muted-foreground">
                          {formatBRL(dashboard.last_month.cost_brl)}
                        </td>
                        <td className="text-right">-</td>
                      </tr>
                      <tr className="bg-green-50 dark:bg-green-950">
                        <td className="py-3 font-bold text-green-700 dark:text-green-400">
                          Lucro Líquido
                        </td>
                        <td className="text-right font-bold text-green-700 dark:text-green-400">
                          {formatBRL(dashboard.this_month.profit_brl)}
                        </td>
                        <td className="text-right text-muted-foreground">
                          {formatBRL(dashboard.last_month.profit_brl)}
                        </td>
                        <td className="text-right">
                          <Badge
                            variant="default"
                            className="bg-green-600"
                          >
                            {dashboard.this_month.profit_margin.toFixed(1)}%
                          </Badge>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Operations Tab */}
          <TabsContent value="operations">
            <Card>
              <CardHeader>
                <CardTitle>🔧 Custos por Operação</CardTitle>
                <CardDescription>
                  Análise de lucratividade por tipo de operação
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3">Operação</th>
                        <th className="text-center py-3">Créditos</th>
                        <th className="text-right py-3">Custo Médio</th>
                        <th className="text-right py-3">Total Ops</th>
                        <th className="text-right py-3">Receita</th>
                        <th className="text-right py-3">Custo</th>
                        <th className="text-right py-3">Margem</th>
                      </tr>
                    </thead>
                    <tbody>
                      {operationCosts.map((op) => (
                        <tr key={op.operation_type} className="border-b">
                          <td className="py-3 font-medium capitalize">
                            {op.operation_type.replace("_", " ")}
                          </td>
                          <td className="text-center">
                            <Badge variant="secondary">{op.credit_cost}</Badge>
                          </td>
                          <td className="text-right text-muted-foreground">
                            ${op.avg_token_cost_usd.toFixed(4)}
                          </td>
                          <td className="text-right">{op.total_operations}</td>
                          <td className="text-right">
                            {formatBRL(op.total_revenue_brl)}
                          </td>
                          <td className="text-right text-red-600">
                            {formatBRL(op.total_cost_brl)}
                          </td>
                          <td className="text-right">
                            <Badge
                              variant={
                                op.profit_margin > 50 ? "default" : "secondary"
                              }
                              className={
                                op.profit_margin > 70
                                  ? "bg-green-600"
                                  : op.profit_margin > 50
                                  ? "bg-yellow-600"
                                  : ""
                              }
                            >
                              {op.profit_margin.toFixed(1)}%
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users">
            <Card>
              <CardHeader>
                <CardTitle>👥 Análise de LTV (Lifetime Value)</CardTitle>
                <CardDescription>
                  Top 50 usuários por valor total gasto
                </CardDescription>
              </CardHeader>
              <CardContent>
                {userLTV.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    Carregando dados de LTV...
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-3">Usuário</th>
                          <th className="text-right py-3">Total Gasto</th>
                          <th className="text-right py-3">Créditos</th>
                          <th className="text-right py-3">Compras</th>
                          <th className="text-right py-3">Ticket Médio</th>
                          <th className="text-right py-3">LTV Previsto</th>
                          <th className="text-right py-3">Dias Ativo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {userLTV.map((user, idx) => (
                          <tr key={user.user_id} className="border-b">
                            <td className="py-2">
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="text-xs">
                                  #{idx + 1}
                                </Badge>
                                <span className="truncate max-w-[150px]">
                                  {user.email}
                                </span>
                              </div>
                            </td>
                            <td className="text-right font-medium text-tiktrend-primary">
                              {formatBRL(user.total_spent_brl)}
                            </td>
                            <td className="text-right">
                              {user.total_credits_purchased}
                              <span className="text-muted-foreground text-xs ml-1">
                                ({user.total_credits_used} usados)
                              </span>
                            </td>
                            <td className="text-right">{user.purchase_count}</td>
                            <td className="text-right">
                              {formatBRL(user.avg_purchase_value)}
                            </td>
                            <td className="text-right font-medium text-green-600">
                              {formatBRL(user.predicted_ltv)}
                            </td>
                            <td className="text-right text-muted-foreground">
                              {user.lifetime_days}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Daily Reports Tab */}
          <TabsContent value="daily">
            <Card>
              <CardHeader>
                <CardTitle>📅 Relatórios Diários</CardTitle>
                <CardDescription>Últimos 7 dias</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3">Data</th>
                        <th className="text-right py-3">Receita</th>
                        <th className="text-right py-3">Custo</th>
                        <th className="text-right py-3">Lucro</th>
                        <th className="text-right py-3">Margem</th>
                        <th className="text-center py-3">Copies</th>
                        <th className="text-center py-3">Análises</th>
                        <th className="text-center py-3">Relatórios</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dailyReports.map((report) => (
                        <tr key={report.date} className="border-b">
                          <td className="py-2 font-medium">
                            {new Date(report.date).toLocaleDateString("pt-BR")}
                          </td>
                          <td className="text-right">
                            {formatBRL(report.revenue_brl)}
                          </td>
                          <td className="text-right text-red-600">
                            {formatBRL(report.cost_brl)}
                          </td>
                          <td className="text-right text-green-600 font-medium">
                            {formatBRL(report.profit_brl)}
                          </td>
                          <td className="text-right">
                            <Badge
                              variant={
                                report.profit_margin > 60 ? "default" : "secondary"
                              }
                            >
                              {report.profit_margin.toFixed(1)}%
                            </Badge>
                          </td>
                          <td className="text-center">{report.operations.copy}</td>
                          <td className="text-center">
                            {report.operations.trend_analysis}
                          </td>
                          <td className="text-center">
                            {report.operations.niche_report}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}

export default FinancialDashboard;
