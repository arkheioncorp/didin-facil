import React, { useState, useEffect, useCallback } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { api } from "@/lib/api";
import { format, parseISO, formatDistanceToNow } from "date-fns";
import { ptBR } from "date-fns/locale";
import {
  Youtube,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCw,
  BarChart3,
  Loader2,
  Info,
  XCircle,
} from "lucide-react";

// Tipos - Estrutura retornada pelo backend
interface BackendQuotaInfo {
  daily_limit?: number;
  used?: number;
  remaining?: number;
  percentage_used?: number;
}

interface BackendQuotaResponse {
  quota?: BackendQuotaInfo;
  operations?: Record<string, number>;
  estimates?: {
    uploads_remaining?: number;
    updates_remaining?: number;
  };
  reset_time?: string;
  date?: string;
}

// Tipos normalizados para uso no componente
interface QuotaInfo {
  used: number;
  limit: number;
  percentage: number;
  reset_at: string;
  last_updated: string;
}

interface QuotaHistory {
  timestamp: string;
  used: number;
  operation: string;
  cost: number;
}

interface QuotaAlert {
  level: "info" | "warning" | "critical";
  message: string;
  timestamp: string;
}

interface QuotaData {
  quota: QuotaInfo;
  history: QuotaHistory[];
  alerts: QuotaAlert[];
}

// Helper para normalizar resposta do backend
function normalizeQuotaData(response: BackendQuotaResponse): QuotaData {
  const backendQuota = response.quota || {};
  const now = new Date();
  
  // Calcular reset_at (meia-noite PST = 08:00 UTC do próximo dia)
  const tomorrow = new Date(now);
  tomorrow.setUTCDate(tomorrow.getUTCDate() + 1);
  tomorrow.setUTCHours(8, 0, 0, 0);
  
  const quota: QuotaInfo = {
    used: backendQuota.used ?? 0,
    limit: backendQuota.daily_limit ?? 10000,
    percentage: backendQuota.percentage_used ?? 0,
    reset_at: tomorrow.toISOString(),
    last_updated: now.toISOString(),
  };

  // Converter operations para history
  const history: QuotaHistory[] = [];
  if (response.operations) {
    for (const [operation, cost] of Object.entries(response.operations)) {
      if (typeof cost === 'number' && cost > 0) {
        history.push({
          timestamp: now.toISOString(),
          used: cost,
          operation,
          cost,
        });
      }
    }
  }

  // Gerar alertas baseados no uso
  const alerts: QuotaAlert[] = [];
  const percentage = quota.percentage;
  
  if (percentage >= 90) {
    alerts.push({
      level: "critical",
      message: "Quota quase esgotada! Apenas " + (quota.limit - quota.used) + " unidades restantes.",
      timestamp: now.toISOString(),
    });
  } else if (percentage >= 75) {
    alerts.push({
      level: "warning",
      message: "Uso de quota acima de 75%. Considere otimizar operações.",
      timestamp: now.toISOString(),
    });
  }

  return { quota, history, alerts };
}

// Config de custos de operação YouTube
const OPERATION_COSTS: Record<string, { cost: number; label: string }> = {
  "videos.insert": { cost: 1600, label: "Upload de Vídeo" },
  "videos.update": { cost: 50, label: "Atualizar Vídeo" },
  "videos.delete": { cost: 50, label: "Excluir Vídeo" },
  "videos.list": { cost: 1, label: "Listar Vídeos" },
  "channels.list": { cost: 1, label: "Info do Canal" },
  "playlists.list": { cost: 1, label: "Listar Playlists" },
  "thumbnails.set": { cost: 50, label: "Definir Thumbnail" },
};

// Componente de barra de progresso com gradiente
const QuotaProgressBar: React.FC<{ percentage: number }> = ({ percentage }) => {
  const getColor = () => {
    if (percentage >= 90) return "bg-red-500";
    if (percentage >= 75) return "bg-orange-500";
    if (percentage >= 50) return "bg-yellow-500";
    return "bg-green-500";
  };

  return (
    <div className="relative w-full h-4 bg-muted rounded-full overflow-hidden">
      <div
        className={`absolute left-0 top-0 h-full transition-all duration-500 ${getColor()}`}
        style={{ width: `${Math.min(percentage, 100)}%` }}
      />
      <div className="absolute inset-0 flex items-center justify-center text-xs font-medium">
        {percentage.toFixed(1)}%
      </div>
    </div>
  );
};

// Componente de histórico de uso
const QuotaHistoryItem: React.FC<{ item: QuotaHistory }> = ({ item }) => {
  const opConfig = OPERATION_COSTS[item.operation] || {
    cost: item.cost,
    label: item.operation,
  };

  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800 last:border-0">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-red-500" />
        <span className="text-sm">{opConfig.label}</span>
      </div>
      <div className="flex items-center gap-3">
        <Badge variant="outline" className="font-mono">
          -{item.cost}
        </Badge>
        <span className="text-xs text-muted-foreground">
          {formatDistanceToNow(parseISO(item.timestamp), {
            locale: ptBR,
            addSuffix: true,
          })}
        </span>
      </div>
    </div>
  );
};

// Componente de alerta
const QuotaAlertItem: React.FC<{ alert: QuotaAlert }> = ({ alert }) => {
  const config = {
    info: {
      icon: Info,
      color: "text-blue-500",
      bg: "bg-blue-50 dark:bg-blue-950",
    },
    warning: {
      icon: AlertTriangle,
      color: "text-yellow-500",
      bg: "bg-yellow-50 dark:bg-yellow-950",
    },
    critical: {
      icon: XCircle,
      color: "text-red-500",
      bg: "bg-red-50 dark:bg-red-950",
    },
  }[alert.level];

  const Icon = config.icon;

  return (
    <div className={`flex items-start gap-2 p-2 rounded-md ${config.bg}`}>
      <Icon className={`h-4 w-4 mt-0.5 ${config.color}`} />
      <div className="flex-1">
        <p className="text-sm">{alert.message}</p>
        <p className="text-xs text-muted-foreground mt-1">
          {formatDistanceToNow(parseISO(alert.timestamp), {
            locale: ptBR,
            addSuffix: true,
          })}
        </p>
      </div>
    </div>
  );
};

// Widget principal de quota
export const YouTubeQuotaWidget: React.FC<{
  compact?: boolean;
  className?: string;
}> = ({ compact = false, className = "" }) => {
  const [data, setData] = useState<QuotaData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadQuota = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get<BackendQuotaResponse>("/youtube/quota");
      // Normalizar resposta do backend para estrutura esperada
      const normalizedData = normalizeQuotaData(response.data);
      setData(normalizedData);
    } catch (err) {
      console.error("Erro ao carregar quota:", err);
      setError("Não foi possível carregar dados de quota");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQuota();
    // Refresh a cada 5 minutos
    const interval = setInterval(loadQuota, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadQuota]);

  if (loading && !data) {
    return (
      <Card className={className}>
        <CardContent className="p-6 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data || !data.quota) {
    return (
      <Card className={className}>
        <CardContent className="p-6 text-center">
          <XCircle className="h-8 w-8 mx-auto text-red-500 mb-2" />
          <p className="text-sm text-muted-foreground">{error || "Dados não disponíveis"}</p>
          <Button variant="ghost" size="sm" onClick={loadQuota} className="mt-2">
            <RefreshCw className="h-4 w-4 mr-1" />
            Tentar novamente
          </Button>
        </CardContent>
      </Card>
    );
  }

  const { quota, history = [], alerts = [] } = data;
  const isWarning = (quota.percentage ?? 0) >= 75;
  const isCritical = (quota.percentage ?? 0) >= 90;

  // Versão compacta para dashboard
  if (compact) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Card
              className={`cursor-pointer transition-colors hover:bg-accent ${className} ${
                isCritical
                  ? "border-red-500"
                  : isWarning
                  ? "border-yellow-500"
                  : ""
              }`}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Youtube className="h-5 w-5 text-red-500" />
                    <span className="font-medium">Quota YouTube</span>
                  </div>
                  {isCritical ? (
                    <AlertTriangle className="h-5 w-5 text-red-500" />
                  ) : isWarning ? (
                    <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  ) : (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  )}
                </div>
                <QuotaProgressBar percentage={quota.percentage ?? 0} />
                <p className="text-xs text-muted-foreground mt-2">
                  {(quota.used ?? 0).toLocaleString()} / {(quota.limit ?? 10000).toLocaleString()} unidades
                </p>
              </CardContent>
            </Card>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="max-w-xs">
            <p>
              Reset em:{" "}
              {quota.reset_at ? formatDistanceToNow(parseISO(quota.reset_at), {
                locale: ptBR,
                addSuffix: true,
              }) : "N/A"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Última atualização:{" "}
              {quota.last_updated ? format(parseISO(quota.last_updated), "HH:mm", { locale: ptBR }) : "N/A"}
            </p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Versão completa
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Youtube className="h-6 w-6 text-red-500" />
            <div>
              <CardTitle className="text-lg">YouTube API Quota</CardTitle>
              <CardDescription>
                Monitoramento de uso diário da API
              </CardDescription>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={loadQuota}>
            <RefreshCw
              className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
            />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Status principal */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Uso atual</span>
            <span className="font-mono font-medium">
              {(quota.used ?? 0).toLocaleString()} / {(quota.limit ?? 10000).toLocaleString()}
            </span>
          </div>
          <QuotaProgressBar percentage={quota.percentage ?? 0} />
        </div>

        {/* Info de reset */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-1 text-muted-foreground">
            <Clock className="h-4 w-4" />
            Reset da quota
          </div>
          <span>
            {quota.reset_at ? formatDistanceToNow(parseISO(quota.reset_at), {
              locale: ptBR,
              addSuffix: true,
            }) : "N/A"}
          </span>
        </div>

        {/* Estimativa de uploads restantes */}
        <div className="p-3 bg-muted/50 rounded-md">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              Uploads disponíveis
            </span>
            <Badge variant={isCritical ? "destructive" : isWarning ? "outline" : "default"}>
              ~{Math.floor(((quota.limit ?? 10000) - (quota.used ?? 0)) / 1600)} vídeos
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Cada upload consome 1.600 unidades de quota
          </p>
        </div>

        {/* Alertas */}
        {alerts && alerts.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium flex items-center gap-1">
              <AlertTriangle className="h-4 w-4" />
              Alertas
            </h4>
            <div className="space-y-2">
              {alerts.slice(0, 3).map((alert, idx) => (
                <QuotaAlertItem key={idx} alert={alert} />
              ))}
            </div>
          </div>
        )}

        {/* Histórico recente */}
        {history && history.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium flex items-center gap-1">
              <BarChart3 className="h-4 w-4" />
              Uso recente
            </h4>
            <div className="max-h-32 overflow-y-auto">
              {history.slice(0, 5).map((item, idx) => (
                <QuotaHistoryItem key={idx} item={item} />
              ))}
            </div>
          </div>
        )}

        {/* Custos de operação */}
        <details className="text-sm">
          <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
            Ver custos de operação
          </summary>
          <div className="mt-2 p-3 bg-muted/50 rounded-md">
            <div className="grid grid-cols-2 gap-2 text-xs">
              {Object.entries(OPERATION_COSTS).map(([op, config]) => (
                <div key={op} className="flex justify-between">
                  <span className="text-muted-foreground">{config.label}</span>
                  <span className="font-mono">{config.cost}</span>
                </div>
              ))}
            </div>
          </div>
        </details>
      </CardContent>
    </Card>
  );
};

export default YouTubeQuotaWidget;
