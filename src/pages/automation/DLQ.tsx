import React, { useState, useEffect, useCallback } from "react";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { format, formatDistanceToNow, parseISO } from "date-fns";
import { ptBR } from "date-fns/locale";
import {
  AlertCircle,
  RefreshCw,
  Trash2,
  Instagram,
  Youtube,
  MessageCircle,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Filter,
  RotateCcw,
  FileText,
  Image,
  Video,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

// TikTok icon
const TikTokIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" className={`fill-current ${className || "h-4 w-4"}`}>
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z" />
  </svg>
);

// Tipos
interface DLQPost {
  id: string;
  platform: string;
  scheduled_time: string;
  failed_at: string;
  attempts: number;
  max_attempts: number;
  last_error: string;
  error_type: string;
  content_type: string;
  caption: string;
  media_url?: string;
  original_post_id: string;
}

interface DLQStats {
  total: number;
  by_platform: Record<string, number>;
  by_error_type: Record<string, number>;
  oldest_failure: string | null;
}

// Config de plataformas
const PLATFORM_CONFIG: Record<
  string,
  {
    name: string;
    icon: React.ComponentType<{ className?: string }>;
    color: string;
    bgColor: string;
  }
> = {
  instagram: {
    name: "Instagram",
    icon: Instagram,
    color: "text-pink-500",
    bgColor: "bg-pink-50 dark:bg-pink-950",
  },
  youtube: {
    name: "YouTube",
    icon: Youtube,
    color: "text-red-500",
    bgColor: "bg-red-50 dark:bg-red-950",
  },
  tiktok: {
    name: "TikTok",
    icon: TikTokIcon,
    color: "text-gray-900 dark:text-white",
    bgColor: "bg-gray-100 dark:bg-gray-800",
  },
  whatsapp: {
    name: "WhatsApp",
    icon: MessageCircle,
    color: "text-green-500",
    bgColor: "bg-green-50 dark:bg-green-950",
  },
};

// Config de tipos de erro
const ERROR_TYPE_CONFIG: Record<
  string,
  { label: string; color: string; description: string }
> = {
  rate_limit: {
    label: "Rate Limit",
    color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
    description: "API excedeu limite de requisições",
  },
  auth_error: {
    label: "Autenticação",
    color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
    description: "Token expirado ou inválido",
  },
  network_error: {
    label: "Rede",
    color: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300",
    description: "Falha de conexão com a API",
  },
  content_error: {
    label: "Conteúdo",
    color: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
    description: "Mídia inválida ou rejeitada",
  },
  quota_exceeded: {
    label: "Quota",
    color: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
    description: "Quota de API excedida (ex: YouTube)",
  },
  unknown: {
    label: "Desconhecido",
    color: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300",
    description: "Erro não categorizado",
  },
};

// Componente de card de post com falha
const FailedPostCard: React.FC<{
  post: DLQPost;
  onRetry: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  isRetrying: boolean;
  isDeleting: boolean;
}> = ({ post, onRetry, onDelete, isRetrying, isDeleting }) => {
  const [expanded, setExpanded] = useState(false);
  const platform = PLATFORM_CONFIG[post.platform] || PLATFORM_CONFIG.instagram;
  const errorType = ERROR_TYPE_CONFIG[post.error_type] || ERROR_TYPE_CONFIG.unknown;
  const PlatformIcon = platform.icon;

  const ContentIcon = {
    image: Image,
    video: Video,
    text: FileText,
  }[post.content_type] || FileText;

  return (
    <Card className={`border-l-4 border-l-red-500 ${platform.bgColor}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          {/* Info Principal */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <div className={`p-1.5 rounded-full ${platform.bgColor}`}>
                <PlatformIcon className={`h-4 w-4 ${platform.color}`} />
              </div>
              <span className="font-medium">{platform.name}</span>
              <Badge variant="outline" className="ml-1">
                <ContentIcon className="h-3 w-3 mr-1" />
                {post.content_type}
              </Badge>
              <Badge className={errorType.color}>{errorType.label}</Badge>
            </div>

            {/* Caption preview */}
            <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
              {post.caption || "(Sem legenda)"}
            </p>

            {/* Meta info */}
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Agendado:{" "}
                {format(parseISO(post.scheduled_time), "dd/MM HH:mm", {
                  locale: ptBR,
                })}
              </span>
              <span className="flex items-center gap-1">
                <AlertCircle className="h-3 w-3 text-red-500" />
                Falhou:{" "}
                {formatDistanceToNow(parseISO(post.failed_at), {
                  locale: ptBR,
                  addSuffix: true,
                })}
              </span>
              <span className="flex items-center gap-1">
                <RotateCcw className="h-3 w-3" />
                {post.attempts}/{post.max_attempts} tentativas
              </span>
            </div>

            {/* Erro expandível */}
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 mt-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              {expanded ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
              Ver detalhes do erro
            </button>

            {expanded && (
              <div className="mt-2 p-3 bg-red-50 dark:bg-red-950 rounded-md border border-red-200 dark:border-red-800">
                <p className="text-xs font-mono text-red-700 dark:text-red-300 whitespace-pre-wrap">
                  {post.last_error}
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  {errorType.description}
                </p>
              </div>
            )}
          </div>

          {/* Ações */}
          <div className="flex flex-col gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => onRetry(post.id)}
              disabled={isRetrying || isDeleting}
            >
              {isRetrying ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              <span className="ml-1 hidden sm:inline">Retry</span>
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={() => onDelete(post.id)}
              disabled={isRetrying || isDeleting}
            >
              {isDeleting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
              <span className="ml-1 hidden sm:inline">Excluir</span>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Componente principal
export default function DLQPage() {
  const { toast } = useToast();
  const [posts, setPosts] = useState<DLQPost[]>([]);
  const [stats, setStats] = useState<DLQStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterPlatform, setFilterPlatform] = useState<string>("all");
  const [filterErrorType, setFilterErrorType] = useState<string>("all");
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [showBulkDialog, setShowBulkDialog] = useState(false);
  const [bulkAction, setBulkAction] = useState<"retry" | "delete" | null>(null);
  const [bulkLoading, setBulkLoading] = useState(false);

  // Carrega dados
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [postsRes, statsRes] = await Promise.all([
        api.get<DLQPost[]>("/scheduler/dlq"),
        api.get<DLQStats>("/scheduler/dlq/stats"),
      ]);
      setPosts(postsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Erro ao carregar DLQ:", error);
      toast({
        variant: "destructive",
        title: "Erro ao carregar",
        description: "Não foi possível carregar a fila de erros",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadData();
    // Auto-refresh a cada 30s
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Retry individual
  const handleRetry = async (id: string) => {
    try {
      setRetryingId(id);
      await api.post(`/scheduler/dlq/${id}/retry`);
      toast({
        title: "Reagendado",
        description: "Post foi movido de volta para a fila de publicação",
      });
      await loadData();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Erro ao reagendar",
        description: "Não foi possível reagendar o post",
      });
    } finally {
      setRetryingId(null);
    }
  };

  // Delete individual
  const handleDelete = async (id: string) => {
    try {
      setDeletingId(id);
      await api.delete(`/scheduler/dlq/${id}`);
      toast({
        title: "Excluído",
        description: "Post foi removido permanentemente",
      });
      await loadData();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Erro ao excluir",
        description: "Não foi possível excluir o post",
      });
    } finally {
      setDeletingId(null);
    }
  };

  // Bulk actions
  const handleBulkAction = async () => {
    if (!bulkAction) return;

    try {
      setBulkLoading(true);
      const filteredIds = filteredPosts.map((p) => p.id);

      if (bulkAction === "retry") {
        await api.post("/scheduler/dlq/retry-all", { ids: filteredIds });
        toast({
          title: "Todos reagendados",
          description: `${filteredIds.length} posts foram reagendados`,
        });
      } else {
        await api.post("/scheduler/dlq/delete-all", { ids: filteredIds });
        toast({
          title: "Todos excluídos",
          description: `${filteredIds.length} posts foram excluídos`,
        });
      }

      setShowBulkDialog(false);
      await loadData();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Erro na operação",
        description: "Não foi possível processar todos os itens",
      });
    } finally {
      setBulkLoading(false);
      setBulkAction(null);
    }
  };

  // Filtra posts
  const filteredPosts = posts.filter((post) => {
    if (filterPlatform !== "all" && post.platform !== filterPlatform)
      return false;
    if (filterErrorType !== "all" && post.error_type !== filterErrorType)
      return false;
    return true;
  });

  // Plataformas únicas para filtro
  const availablePlatforms = [...new Set(posts.map((p) => p.platform))];
  const availableErrorTypes = [...new Set(posts.map((p) => p.error_type))];

  if (loading && posts.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <AlertTriangle className="h-6 w-6 text-red-500" />
            Dead Letter Queue
          </h1>
          <p className="text-muted-foreground">
            Posts que falharam após múltiplas tentativas de publicação
          </p>
        </div>

        <Button onClick={loadData} variant="outline" disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Atualizar
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total na Fila</p>
                  <p className="text-2xl font-bold text-red-500">{stats.total}</p>
                </div>
                <AlertCircle className="h-8 w-8 text-red-500 opacity-50" />
              </div>
            </CardContent>
          </Card>

          {Object.entries(stats.by_platform || {}).map(([platform, count]) => {
            const config = PLATFORM_CONFIG[platform];
            if (!config) return null;
            const Icon = config.icon;
            return (
              <Card key={platform}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{config.name}</p>
                      <p className="text-2xl font-bold">{count}</p>
                    </div>
                    <Icon className={`h-8 w-8 ${config.color} opacity-50`} />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Filtros e Ações em Massa */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />

              <Select value={filterPlatform} onValueChange={setFilterPlatform}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Plataforma" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {availablePlatforms.map((platform) => (
                    <SelectItem key={platform} value={platform}>
                      {PLATFORM_CONFIG[platform]?.name || platform}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={filterErrorType} onValueChange={setFilterErrorType}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Tipo de Erro" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  {availableErrorTypes.map((errorType) => (
                    <SelectItem key={errorType} value={errorType}>
                      {ERROR_TYPE_CONFIG[errorType]?.label || errorType}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {(filterPlatform !== "all" || filterErrorType !== "all") && (
                <Badge variant="secondary">
                  {filteredPosts.length} de {posts.length}
                </Badge>
              )}
            </div>

            {filteredPosts.length > 0 && (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setBulkAction("retry");
                    setShowBulkDialog(true);
                  }}
                >
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Retry Todos ({filteredPosts.length})
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => {
                    setBulkAction("delete");
                    setShowBulkDialog(true);
                  }}
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Excluir Todos
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Lista de Posts */}
      {filteredPosts.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <CheckCircle2 className="h-12 w-12 mx-auto text-green-500 mb-4" />
            <h3 className="text-lg font-medium mb-2">Nenhum post com falha!</h3>
            <p className="text-muted-foreground">
              {posts.length > 0
                ? "Nenhum post corresponde aos filtros selecionados"
                : "Todos os posts agendados foram publicados com sucesso"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <ScrollArea className="h-[calc(100vh-400px)]">
          <div className="space-y-3">
            {filteredPosts.map((post) => (
              <FailedPostCard
                key={post.id}
                post={post}
                onRetry={handleRetry}
                onDelete={handleDelete}
                isRetrying={retryingId === post.id}
                isDeleting={deletingId === post.id}
              />
            ))}
          </div>
        </ScrollArea>
      )}

      {/* Dialog de confirmação bulk */}
      <Dialog open={showBulkDialog} onOpenChange={setShowBulkDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {bulkAction === "retry" ? "Reagendar Todos?" : "Excluir Todos?"}
            </DialogTitle>
            <DialogDescription>
              {bulkAction === "retry"
                ? `Isso irá mover ${filteredPosts.length} posts de volta para a fila de publicação. Eles serão processados novamente pelo scheduler.`
                : `Isso irá excluir permanentemente ${filteredPosts.length} posts. Esta ação não pode ser desfeita.`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowBulkDialog(false)}
              disabled={bulkLoading}
            >
              Cancelar
            </Button>
            <Button
              variant={bulkAction === "delete" ? "destructive" : "default"}
              onClick={handleBulkAction}
              disabled={bulkLoading}
            >
              {bulkLoading ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : null}
              {bulkAction === "retry" ? "Reagendar Todos" : "Excluir Todos"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
