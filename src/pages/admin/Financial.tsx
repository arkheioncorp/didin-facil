import * as React from "react";
import { Suspense, lazy, ComponentType } from "react";
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
import {
  getFinancialSummary,
  exportFinancialReport,
  generateDailyReport,
  type FinancialSummary,
  type DailyRevenueItem,
  type TopUser,
  type PackageSales,
  type OperationsBreakdown,
} from "@/services/accounting";
import { Download, FileSpreadsheet, FileJson, FileText, RefreshCw, Calendar } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";

// Lazy load recharts for better initial bundle size (-385KB)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyBarChart = lazy(() => import('recharts').then(m => ({ default: m.BarChart as unknown as ComponentType<any> })));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyBar = lazy(() => import('recharts').then(m => ({ default: m.Bar as unknown as ComponentType<any> })));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyLineChart = lazy(() => import('recharts').then(m => ({ default: m.LineChart as unknown as ComponentType<any> })));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyLine = lazy(() => import('recharts').then(m => ({ default: m.Line as unknown as ComponentType<any> })));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyXAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis as unknown as ComponentType<any> })));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyYAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis as unknown as ComponentType<any> })));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyCartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid as unknown as ComponentType<any> })));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyTooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip as unknown as ComponentType<any> })));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const LazyResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer as unknown as ComponentType<any> })));

// Chart loading skeleton
const ChartSkeleton = () => (
  <div className="h-[300px] w-full flex items-center justify-center bg-muted/20 rounded-lg">
    <div className="flex flex-col items-center gap-3">
      <Skeleton className="h-8 w-8 rounded-full" />
      <Skeleton className="h-4 w-32" />
    </div>
  </div>
);

export function FinancialDashboard() {
  const navigate = useNavigate();

  const [summary, setSummary] = React.useState<FinancialSummary | null>(null);
  const [periodDays, setPeriodDays] = React.useState(30);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [activeTab, setActiveTab] = React.useState("overview");

  // Export state
  const [isExportOpen, setIsExportOpen] = React.useState(false);
  const [exportFormat, setExportFormat] = React.useState<"csv" | "json" | "xlsx">("csv");
  const [exportStartDate, setExportStartDate] = React.useState(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split("T")[0]
  );
  const [exportEndDate, setExportEndDate] = React.useState(
    new Date().toISOString().split("T")[0]
  );
  const [isExporting, setIsExporting] = React.useState(false);
  const [isGenerating, setIsGenerating] = React.useState(false);

  React.useEffect(() => {
    loadDashboard();
  }, [periodDays]);

  const loadDashboard = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getFinancialSummary(periodDays);
      setSummary(data);
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

  const handleExport = async () => {
    try {
      setIsExporting(true);
      await exportFinancialReport(
        new Date(exportStartDate),
        new Date(exportEndDate),
        exportFormat
      );
      toast.success("Relatório exportado com sucesso!");
      setIsExportOpen(false);
    } catch (err) {
      console.error("Error exporting report:", err);
      toast.error("Erro ao exportar relatório");
    } finally {
      setIsExporting(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setIsGenerating(true);
      const result = await generateDailyReport();
      if (result.success) {
        toast.success(`Relatório gerado para ${result.report_date}`);
        loadDashboard(); // Reload data
      }
    } catch (err) {
      console.error("Error generating report:", err);
      toast.error("Erro ao gerar relatório diário");
    } finally {
      setIsGenerating(false);
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-tiktrend-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <p className="text-destructive">{error}</p>
        <Button onClick={() => navigate("/")}>Voltar ao Dashboard</Button>
      </div>
    );
  }

  if (!summary) return null;

  const { metrics, revenue_by_day, operations_breakdown, top_users, package_sales } = summary;

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">💰 Dashboard Financeiro</h1>
          <p className="text-muted-foreground">
            Visão geral de receita, custos e lucros ({metrics.period_days} dias)
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={periodDays}
            onChange={(e) => setPeriodDays(Number(e.target.value))}
            className="border rounded-md px-3 py-2 bg-background"
          >
            <option value={7}>7 dias</option>
            <option value={30}>30 dias</option>
            <option value={90}>90 dias</option>
          </select>
          <Button variant="outline" onClick={loadDashboard} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            Atualizar
          </Button>

          <Dialog open={isExportOpen} onOpenChange={setIsExportOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Exportar
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Exportar Relatório Financeiro</DialogTitle>
                <DialogDescription>
                  Selecione o período e o formato para exportação.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Data Inicial</Label>
                    <Input
                      type="date"
                      value={exportStartDate}
                      onChange={(e) => setExportStartDate(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Data Final</Label>
                    <Input
                      type="date"
                      value={exportEndDate}
                      onChange={(e) => setExportEndDate(e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Formato</Label>
                  <Select value={exportFormat} onValueChange={(v: any) => setExportFormat(v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="csv">
                        <div className="flex items-center">
                          <FileSpreadsheet className="mr-2 h-4 w-4 text-green-600" />
                          CSV (Excel)
                        </div>
                      </SelectItem>
                      <SelectItem value="xlsx">
                        <div className="flex items-center">
                          <FileText className="mr-2 h-4 w-4 text-blue-600" />
                          Excel (.xlsx)
                        </div>
                      </SelectItem>
                      <SelectItem value="json">
                        <div className="flex items-center">
                          <FileJson className="mr-2 h-4 w-4 text-yellow-600" />
                          JSON
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsExportOpen(false)}>Cancelar</Button>
                <Button onClick={handleExport} disabled={isExporting}>
                  {isExporting ? "Exportando..." : "Exportar"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Button onClick={handleGenerateReport} disabled={isGenerating}>
            <Calendar className="mr-2 h-4 w-4" />
            {isGenerating ? "Gerando..." : "Gerar Relatório Hoje"}
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        {/* Total Revenue */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Receita Total</CardDescription>
            <CardTitle className="text-2xl">
              {formatBRL(metrics.total_revenue)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              {metrics.transactions_count} transações
            </p>
          </CardContent>
        </Card>

        {/* Gross Profit */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Lucro Bruto</CardDescription>
            <CardTitle className="text-2xl text-green-600">
              {formatBRL(metrics.gross_profit)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Margem: {metrics.profit_margin_percent.toFixed(1)}%
            </p>
          </CardContent>
        </Card>

        {/* Total Costs */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Custos Totais</CardDescription>
            <CardTitle className="text-2xl text-red-600">
              {formatBRL(metrics.total_costs)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              OpenAI: {formatBRL(metrics.openai_costs)}
            </p>
          </CardContent>
        </Card>

        {/* Credits */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Créditos</CardDescription>
            <CardTitle className="text-2xl">
              {metrics.credits_sold.toLocaleString()}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Consumidos: {metrics.credits_consumed.toLocaleString()}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Visão Geral</TabsTrigger>
          <TabsTrigger value="operations">Operações</TabsTrigger>
          <TabsTrigger value="users">Top Usuários</TabsTrigger>
          <TabsTrigger value="packages">Pacotes</TabsTrigger>
          <TabsTrigger value="daily">Receita Diária</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Revenue Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Receita vs Custos (Últimos {periodDays} dias)</CardTitle>
            </CardHeader>
            <CardContent className="h-[300px]">
              <Suspense fallback={<ChartSkeleton />}>
                <LazyResponsiveContainer width="100%" height="100%">
                  <LazyBarChart data={revenue_by_day}>
                    <LazyCartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <LazyXAxis
                      dataKey="date"
                      tickFormatter={(value) => new Date(value).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                      className="text-xs"
                    />
                    <LazyYAxis
                      tickFormatter={(value) => `R$ ${value}`}
                      className="text-xs"
                    />
                    <LazyTooltip
                      formatter={(value) => formatBRL(Number(value))}
                      labelFormatter={(label) => new Date(label).toLocaleDateString('pt-BR')}
                      contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))' }}
                    />
                    <LazyBar dataKey="revenue" name="Receita" fill="#10b981" radius={[4, 4, 0, 0]} />
                    <LazyBar dataKey="costs" name="Custos" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </LazyBarChart>
                </LazyResponsiveContainer>
              </Suspense>
            </CardContent>
          </Card>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Key Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>📊 Métricas Principais</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Transações</span>
                  <span className="font-bold">
                    {metrics.transactions_count}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Ticket Médio</span>
                  <span className="font-bold">
                    {formatBRL(metrics.avg_transaction_value)}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Créditos Vendidos</span>
                  <span className="font-bold">
                    {metrics.credits_sold.toLocaleString()}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Créditos Consumidos</span>
                  <span className="font-bold">
                    {metrics.credits_consumed.toLocaleString()}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Taxa de Uso</span>
                  <span className="font-bold">
                    {metrics.credits_sold > 0
                      ? ((metrics.credits_consumed / metrics.credits_sold) * 100).toFixed(1)
                      : 0}%
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Operations Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>🔧 Breakdown de Operações</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Copy Generation</span>
                  <span className="font-bold">
                    {operations_breakdown.copy_generation}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Trend Analysis</span>
                  <span className="font-bold">
                    {operations_breakdown.trend_analysis}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Niche Report</span>
                  <span className="font-bold">
                    {operations_breakdown.niche_report}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">AI Chat</span>
                  <span className="font-bold">
                    {operations_breakdown.ai_chat}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Image Generation</span>
                  <span className="font-bold">
                    {operations_breakdown.image_generation}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* P&L Summary */}
          <Card>
            <CardHeader>
              <CardTitle>💵 Demonstração de Resultado</CardTitle>
              <CardDescription>Período: {metrics.period_days} dias</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3">Item</th>
                      <th className="text-right py-3">Valor</th>
                      <th className="text-right py-3">% da Receita</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b">
                      <td className="py-3">Receita Bruta</td>
                      <td className="text-right font-medium">
                        {formatBRL(metrics.total_revenue)}
                      </td>
                      <td className="text-right">100%</td>
                    </tr>
                    <tr className="border-b">
                      <td className="py-3 text-red-600">(-) Custos OpenAI</td>
                      <td className="text-right text-red-600">
                        {formatBRL(metrics.openai_costs)}
                      </td>
                      <td className="text-right text-muted-foreground">
                        {metrics.total_revenue > 0
                          ? ((metrics.openai_costs / metrics.total_revenue) * 100).toFixed(1)
                          : 0}%
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="py-3 text-red-600">(-) Outros Custos</td>
                      <td className="text-right text-red-600">
                        {formatBRL(metrics.total_costs - metrics.openai_costs)}
                      </td>
                      <td className="text-right text-muted-foreground">
                        {metrics.total_revenue > 0
                          ? (((metrics.total_costs - metrics.openai_costs) / metrics.total_revenue) * 100).toFixed(1)
                          : 0}%
                      </td>
                    </tr>
                    <tr className="bg-green-50 dark:bg-green-950">
                      <td className="py-3 font-bold text-green-700 dark:text-green-400">
                        Lucro Bruto
                      </td>
                      <td className="text-right font-bold text-green-700 dark:text-green-400">
                        {formatBRL(metrics.gross_profit)}
                      </td>
                      <td className="text-right">
                        <Badge variant="default" className="bg-green-600">
                          {metrics.profit_margin_percent.toFixed(1)}%
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
              <CardTitle>🔧 Detalhamento de Operações</CardTitle>
              <CardDescription>
                Distribuição de uso por tipo de operação
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {[
                  { name: "Copy Generation", value: operations_breakdown.copy_generation, icon: "📝" },
                  { name: "Trend Analysis", value: operations_breakdown.trend_analysis, icon: "📊" },
                  { name: "Niche Report", value: operations_breakdown.niche_report, icon: "📈" },
                  { name: "AI Chat", value: operations_breakdown.ai_chat, icon: "💬" },
                  { name: "Image Generation", value: operations_breakdown.image_generation, icon: "🖼️" },
                ].map((op) => (
                  <Card key={op.name}>
                    <CardHeader className="pb-2">
                      <CardDescription>{op.icon} {op.name}</CardDescription>
                      <CardTitle className="text-2xl">{op.value.toLocaleString()}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-tiktrend-primary h-2 rounded-full"
                          style={{
                            width: `${Math.min(
                              (op.value / Math.max(...Object.values(operations_breakdown))) * 100,
                              100
                            )}%`,
                          }}
                        />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users">
          <Card>
            <CardHeader>
              <CardTitle>👥 Top Usuários por Gasto</CardTitle>
              <CardDescription>
                Usuários que mais geraram receita
              </CardDescription>
            </CardHeader>
            <CardContent>
              {top_users.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  Nenhum dado de usuário disponível
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3">#</th>
                        <th className="text-left py-3">User ID</th>
                        <th className="text-right py-3">Total Gasto</th>
                        <th className="text-right py-3">Créditos</th>
                        <th className="text-right py-3">Compras</th>
                        <th className="text-right py-3">Lucro Gerado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {top_users.map((user, idx) => (
                        <tr key={user.user_id} className="border-b">
                          <td className="py-2">
                            <Badge variant="outline" className="text-xs">
                              #{idx + 1}
                            </Badge>
                          </td>
                          <td className="py-2 font-mono text-xs truncate max-w-[150px]">
                            {user.user_id}
                          </td>
                          <td className="text-right font-medium text-tiktrend-primary">
                            {formatBRL(user.total_spent)}
                          </td>
                          <td className="text-right">
                            {user.credits_purchased.toLocaleString()}
                            <span className="text-muted-foreground text-xs ml-1">
                              ({user.credits_used} usados)
                            </span>
                          </td>
                          <td className="text-right">{user.purchase_count}</td>
                          <td className="text-right font-medium text-green-600">
                            {formatBRL(user.lifetime_profit)}
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

        {/* Packages Tab */}
        <TabsContent value="packages">
          <Card>
            <CardHeader>
              <CardTitle>📦 Vendas por Pacote</CardTitle>
              <CardDescription>
                Performance de cada pacote de créditos
              </CardDescription>
            </CardHeader>
            <CardContent>
              {package_sales.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  Nenhum dado de pacote disponível
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3">Pacote</th>
                        <th className="text-right py-3">Vendas</th>
                        <th className="text-right py-3">Receita</th>
                        <th className="text-right py-3">Créditos</th>
                        <th className="text-right py-3">Ticket Médio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {package_sales.map((pkg) => (
                        <tr key={pkg.slug} className="border-b">
                          <td className="py-3">
                            <div>
                              <span className="font-medium">{pkg.name}</span>
                              <span className="text-xs text-muted-foreground ml-2">
                                ({pkg.slug})
                              </span>
                            </div>
                          </td>
                          <td className="text-right font-medium">
                            {pkg.sales}
                          </td>
                          <td className="text-right text-tiktrend-primary font-medium">
                            {formatBRL(pkg.revenue)}
                          </td>
                          <td className="text-right">
                            {pkg.credits.toLocaleString()}
                          </td>
                          <td className="text-right text-muted-foreground">
                            {pkg.sales > 0 ? formatBRL(pkg.revenue / pkg.sales) : "-"}
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

        {/* Daily Revenue Tab */}
        <TabsContent value="daily">
          <Card>
            <CardHeader>
              <CardTitle>📅 Receita Diária</CardTitle>
              <CardDescription>Últimos {metrics.period_days} dias</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="h-[300px]">
                <Suspense fallback={<ChartSkeleton />}>
                  <LazyResponsiveContainer width="100%" height="100%">
                    <LazyLineChart data={revenue_by_day}>
                      <LazyCartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <LazyXAxis
                        dataKey="date"
                        tickFormatter={(value) => new Date(value).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                        className="text-xs"
                      />
                      <LazyYAxis
                        tickFormatter={(value) => `R$ ${value}`}
                        className="text-xs"
                      />
                      <LazyTooltip
                        formatter={(value) => formatBRL(Number(value))}
                        labelFormatter={(label) => new Date(label).toLocaleDateString('pt-BR')}
                        contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))' }}
                      />
                      <LazyLine type="monotone" dataKey="revenue" name="Receita" stroke="#10b981" strokeWidth={2} dot={false} />
                      <LazyLine type="monotone" dataKey="profit" name="Lucro" stroke="#3b82f6" strokeWidth={2} dot={false} />
                    </LazyLineChart>
                  </LazyResponsiveContainer>
                </Suspense>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3">Data</th>
                      <th className="text-right py-3">Receita</th>
                      <th className="text-right py-3">Custos</th>
                      <th className="text-right py-3">Lucro</th>
                      <th className="text-right py-3">Margem</th>
                      <th className="text-center py-3">Transações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {revenue_by_day.map((day) => {
                      const margin = day.revenue > 0 ? (day.profit / day.revenue) * 100 : 0;
                      return (
                        <tr key={day.date} className="border-b">
                          <td className="py-2 font-medium">
                            {new Date(day.date).toLocaleDateString("pt-BR")}
                          </td>
                          <td className="text-right">
                            {formatBRL(day.revenue)}
                          </td>
                          <td className="text-right text-red-600">
                            {formatBRL(day.costs)}
                          </td>
                          <td className="text-right text-green-600 font-medium">
                            {formatBRL(day.profit)}
                          </td>
                          <td className="text-right">
                            <Badge variant={margin > 60 ? "default" : "secondary"}>
                              {margin.toFixed(1)}%
                            </Badge>
                          </td>
                          <td className="text-center">{day.transactions}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default FinancialDashboard;
