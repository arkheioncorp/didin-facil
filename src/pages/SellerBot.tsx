import React, { useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Square,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Package,
  MessageSquare,
  BarChart3,
  Truck,
  Chrome,
  Eye,
  Plus,
  Trash2,
  Monitor,
  Settings,
  Crown,
  Instagram,
  Youtube,
  Video,
  Smartphone,
  Play,
  StopCircle,
  Wifi,
  WifiOff,
} from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { BrowserViewer } from "@/components/scraper/BrowserViewer";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";
import { useWebSocket, type WebSocketNotification } from "@/services/websocket";

import { api } from "@/lib/api";

// ============================================
// Types - Automação Browser (/bot)
// ============================================

interface BotTask {
  id: string;
  task_type: string;
  state: "queued" | "running" | "completed" | "failed" | "cancelled";
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  screenshots: string[];
  logs: string[];
}

interface BotQueueStats {
  total_queued: number;
  total_running: number;
  total_completed: number;
  total_failed: number;
  by_task_type: Record<string, number>;
}

interface BotProfile {
  id: string;
  name: string;
  is_logged_in: boolean;
  last_used_at?: string;
  created_at: string;
}

// ============================================
// API Functions - Automação Browser (/bot)
// ============================================

async function fetchBotTasks(): Promise<BotTask[]> {
  try {
    const response = await api.get<BotTask[]>("/bot/tasks");
    return response.data;
  } catch (error) {
    console.error("Failed to fetch bot tasks:", error);
    return [];
  }
}

async function fetchBotStats(): Promise<BotQueueStats> {
  try {
    const response = await api.get<BotQueueStats>("/bot/stats");
    return response.data;
  } catch (error) {
    console.error("Failed to fetch bot stats:", error);
    return {
      total_queued: 0,
      total_running: 0,
      total_completed: 0,
      total_failed: 0,
      by_task_type: {},
    };
  }
}

async function fetchBotProfiles(): Promise<BotProfile[]> {
  try {
    const response = await api.get<BotProfile[]>("/bot/profiles");
    return response.data;
  } catch (error) {
    console.error("Failed to fetch bot profiles:", error);
    return [];
  }
}

async function createBotTask(data: { 
  task_type: string; 
  task_description?: string;
  task_data?: Record<string, unknown>;
  priority?: string;
}): Promise<BotTask> {
  const response = await api.post<BotTask>("/bot/tasks", data);
  return response.data;
}

async function cancelBotTask(taskId: string): Promise<void> {
  await api.delete(`/bot/tasks/${taskId}`);
}

async function createBotProfile(data: { 
  name: string; 
  clone_from_system: boolean;
}): Promise<BotProfile> {
  const response = await api.post<BotProfile>("/bot/profiles", data);
  return response.data;
}

async function deleteBotProfile(profileId: string): Promise<void> {
  await api.delete(`/bot/profiles/${profileId}`);
}

async function verifyBotProfile(profileId: string): Promise<{ is_logged_in: boolean }> {
  const response = await api.post<{ is_logged_in: boolean }>(`/bot/profiles/${profileId}/verify`);
  return response.data;
}

async function startBotWorker(): Promise<void> {
  await api.post("/bot/start");
}

async function stopBotWorker(): Promise<void> {
  await api.post("/bot/stop");
}

// ============================================
// Components
// ============================================

const TaskTypeIcon: React.FC<{ type: string }> = ({ type }) => {
  switch (type) {
    case "post_product":
      return <Package className="h-4 w-4" />;
    case "manage_orders":
      return <Truck className="h-4 w-4" />;
    case "reply_messages":
      return <MessageSquare className="h-4 w-4" />;
    case "analytics":
      return <BarChart3 className="h-4 w-4" />;
    case "instagram_post":
      return <Instagram className="h-4 w-4" />;
    case "tiktok_upload":
      return <Video className="h-4 w-4" />;
    case "youtube_upload":
      return <Youtube className="h-4 w-4" />;
    case "whatsapp_message":
      return <Smartphone className="h-4 w-4" />;
    default:
      return <Settings className="h-4 w-4" />;
  }
};

const TaskStatusBadge: React.FC<{ state: BotTask["state"] }> = ({ state }) => {
  const variants: Record<BotTask["state"], { 
    variant: "default" | "secondary" | "destructive" | "outline"; 
    icon: React.ReactNode;
    label: string;
  }> = {
    queued: { variant: "secondary", icon: <Clock className="h-3 w-3" />, label: "Na Fila" },
    running: { variant: "default", icon: <Loader2 className="h-3 w-3 animate-spin" />, label: "Executando" },
    completed: { variant: "outline", icon: <CheckCircle2 className="h-3 w-3 text-green-500" />, label: "Concluída" },
    failed: { variant: "destructive", icon: <XCircle className="h-3 w-3" />, label: "Falhou" },
    cancelled: { variant: "secondary", icon: <Square className="h-3 w-3" />, label: "Cancelada" },
  };

  const { variant, icon, label } = variants[state];

  return (
    <Badge variant={variant} className="gap-1">
      {icon}
      {label}
    </Badge>
  );
};

const TaskCard: React.FC<{ task: BotTask; onCancel: () => void }> = ({ task, onCancel }) => {
  const taskTypeLabels: Record<string, string> = {
    post_product: "Publicar Produto",
    manage_orders: "Gerenciar Pedidos",
    reply_messages: "Responder Mensagens",
    analytics: "Extrair Analytics",
    instagram_post: "Postar no Instagram",
    tiktok_upload: "Upload TikTok",
    youtube_upload: "Upload YouTube",
    whatsapp_message: "Mensagem WhatsApp",
  };

  return (
    <Card className="mb-3">
      <CardHeader className="py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TaskTypeIcon type={task.task_type} />
            <CardTitle className="text-sm">
              {taskTypeLabels[task.task_type] || task.task_type}
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <TaskStatusBadge state={task.state} />
            {(task.state === "queued" || task.state === "running") && (
              <Button variant="ghost" size="icon" onClick={onCancel} title="Cancelar">
                <Square className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="py-2">
        <div className="text-xs text-muted-foreground space-y-1">
          <p>ID: {task.id.slice(0, 8)}...</p>
          <p>Criado: {new Date(task.created_at).toLocaleString("pt-BR")}</p>
          {task.started_at && (
            <p>Iniciado: {new Date(task.started_at).toLocaleString("pt-BR")}</p>
          )}
          {task.completed_at && (
            <p>Concluído: {new Date(task.completed_at).toLocaleString("pt-BR")}</p>
          )}
          {task.error_message && (
            <p className="text-destructive">Erro: {task.error_message}</p>
          )}
        </div>
        {task.logs.length > 0 && (
          <ScrollArea className="h-24 mt-2 rounded border p-2 bg-muted/50">
            {task.logs.map((log, i) => (
              <p key={i} className="text-xs font-mono">{log}</p>
            ))}
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
};

const QuickActionCard: React.FC<{
  title: string;
  description: string;
  icon: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
}> = ({ title, description, icon, onClick, disabled }) => (
  <Card
    className={`cursor-pointer transition-all hover:border-primary hover:shadow-md ${
      disabled ? "opacity-50 cursor-not-allowed" : ""
    }`}
    onClick={disabled ? undefined : onClick}
  >
    <CardHeader className="pb-2">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-primary/10 text-primary">
          {icon}
        </div>
        <div>
          <CardTitle className="text-sm">{title}</CardTitle>
          <CardDescription className="text-xs">{description}</CardDescription>
        </div>
      </div>
    </CardHeader>
  </Card>
);

// ============================================
// Main Page Component
// ============================================

export const SellerBot: React.FC = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  
  // WebSocket connection for real-time updates
  const { isConnected: wsConnected, notifications } = useWebSocket({ 
    autoConnect: true 
  });
  
  // Dialog states
  const [isNewProfileOpen, setIsNewProfileOpen] = React.useState(false);
  const [newProfileName, setNewProfileName] = React.useState("");
  const [cloneFromSystem, setCloneFromSystem] = React.useState(true);
  const [profileToDelete, setProfileToDelete] = React.useState<string | null>(null);
  const [profileToView, setProfileToView] = React.useState<BotProfile | null>(null);
  
  // Browser viewer state
  const [browserViewerData, setBrowserViewerData] = React.useState<{
    isActive: boolean;
    currentUrl?: string;
    screenshot?: string;
    status?: string;
  }>({ isActive: false });

  // ============================================
  // WebSocket Event Handlers
  // ============================================
  
  // Handle real-time bot notifications
  const handleBotNotification = useCallback(
    (notification: WebSocketNotification) => {
      const botEvents = [
        "bot_task_started",
        "bot_task_completed", 
        "bot_task_failed",
        "bot_task_progress",
        "bot_stats_update",
        "bot_screenshot",
        "bot_worker_started",
        "bot_worker_stopped",
      ];
      
      if (botEvents.includes(notification.type)) {
        // Invalidate queries to refresh data
        queryClient.invalidateQueries({ queryKey: ["bot-tasks"] });
        queryClient.invalidateQueries({ queryKey: ["bot-stats"] });
        
        // Update browser viewer if screenshot
        if (notification.type === "bot_screenshot" && notification.data) {
          setBrowserViewerData((prev) => ({
            ...prev,
            screenshot: notification.data?.screenshot as string,
            status: notification.data?.status as string,
          }));
        }
        
        // Show toast for important events
        if (notification.type === "bot_task_completed") {
          toast({
            title: "Tarefa Concluída!",
            description: notification.message,
          });
        } else if (notification.type === "bot_task_failed") {
          toast({
            title: "Tarefa Falhou",
            description: notification.message,
            variant: "destructive",
          });
        }
      }
    },
    [queryClient, toast]
  );
  
  // Subscribe to bot notifications
  useEffect(() => {
    const latestNotification = notifications[0];
    if (latestNotification) {
      handleBotNotification(latestNotification);
    }
  }, [notifications, handleBotNotification]);

  // ============================================
  // Queries - Automação Browser (with WebSocket fallback)
  // ============================================
  
  // Reduce polling interval when WebSocket is connected
  const pollingInterval = wsConnected ? 30000 : 3000; // 30s vs 3s
  
  const { data: botTasks = [], isLoading: botTasksLoading } = useQuery({
    queryKey: ["bot-tasks"],
    queryFn: fetchBotTasks,
    refetchInterval: pollingInterval,
  });

  const { data: botStats } = useQuery({
    queryKey: ["bot-stats"],
    queryFn: fetchBotStats,
    refetchInterval: pollingInterval,
  });

  const { data: botProfiles = [], isLoading: profilesLoading } = useQuery({
    queryKey: ["bot-profiles"],
    queryFn: fetchBotProfiles,
  });

  // ============================================
  // Mutations - Automação Browser
  // ============================================

  const createTaskMutation = useMutation({
    mutationFn: createBotTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bot-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["bot-stats"] });
      toast({ title: "Tarefa criada!", description: "A tarefa foi adicionada à fila." });
    },
    onError: (error: Error) => {
      toast({ 
        title: "Erro ao criar tarefa", 
        description: error.message,
        variant: "destructive" 
      });
    },
  });

  const cancelTaskMutation = useMutation({
    mutationFn: cancelBotTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bot-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["bot-stats"] });
      toast({ title: "Tarefa cancelada" });
    },
  });

  const createProfileMutation = useMutation({
    mutationFn: createBotProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bot-profiles"] });
      setIsNewProfileOpen(false);
      setNewProfileName("");
      toast({ title: "Perfil criado!", description: "O perfil foi criado com sucesso." });
    },
    onError: (error: Error) => {
      toast({ 
        title: "Erro ao criar perfil", 
        description: error.message,
        variant: "destructive" 
      });
    },
  });

  const deleteProfileMutation = useMutation({
    mutationFn: deleteBotProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bot-profiles"] });
      setProfileToDelete(null);
      toast({ title: "Perfil deletado" });
    },
  });

  const verifyProfileMutation = useMutation({
    mutationFn: verifyBotProfile,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["bot-profiles"] });
      toast({ 
        title: data.is_logged_in ? "Perfil verificado!" : "Login necessário",
        description: data.is_logged_in 
          ? "O perfil está logado corretamente." 
          : "Por favor, faça login no navegador.",
        variant: data.is_logged_in ? "default" : "destructive",
      });
    },
  });

  const startBotMutation = useMutation({
    mutationFn: startBotWorker,
    onSuccess: () => {
      toast({ title: "Bot iniciado!", description: "O worker está processando tarefas." });
    },
  });

  const stopBotMutation = useMutation({
    mutationFn: stopBotWorker,
    onSuccess: () => {
      toast({ title: "Bot parado" });
    },
  });

  // ============================================
  // Handlers
  // ============================================

  const handleQuickAction = (taskType: string) => {
    createTaskMutation.mutate({ task_type: taskType });
    setBrowserViewerData({ isActive: true, status: "Iniciando..." });
  };

  const runningTask = botTasks.find((t) => t.state === "running");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Crown className="h-6 w-6 text-yellow-500" />
            Seller Bot
          </h1>
          <p className="text-muted-foreground">
            Automação Premium para Central do Vendedor TikTok Shop
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* WebSocket Status Indicator */}
          <Badge 
            variant="outline" 
            className={wsConnected 
              ? "bg-green-500/10 text-green-600 border-green-500/50" 
              : "bg-gray-500/10 text-gray-500 border-gray-500/50"
            }
            title={wsConnected ? "Tempo real ativo" : "Polling mode (reconectando...)"}
          >
            {wsConnected ? <Wifi className="h-3 w-3 mr-1" /> : <WifiOff className="h-3 w-3 mr-1" />}
            {wsConnected ? "Live" : "Offline"}
          </Badge>
          
          <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/50">
            Premium R$149,90/mês
          </Badge>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => startBotMutation.mutate()}
            disabled={startBotMutation.isPending}
          >
            <Play className="h-4 w-4 mr-1" />
            Iniciar
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => stopBotMutation.mutate()}
            disabled={stopBotMutation.isPending}
          >
            <StopCircle className="h-4 w-4 mr-1" />
            Parar
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Na Fila</CardDescription>
            <CardTitle className="text-2xl">{botStats?.total_queued || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Executando</CardDescription>
            <CardTitle className="text-2xl text-blue-500">{botStats?.total_running || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Concluídas</CardDescription>
            <CardTitle className="text-2xl text-green-500">{botStats?.total_completed || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Falhas</CardDescription>
            <CardTitle className="text-2xl text-destructive">{botStats?.total_failed || 0}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="actions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="actions">Ações Rápidas</TabsTrigger>
          <TabsTrigger value="tasks">Tarefas ({botTasks.length})</TabsTrigger>
          <TabsTrigger value="profiles">Perfis ({botProfiles.length})</TabsTrigger>
        </TabsList>

        {/* Quick Actions Tab */}
        <TabsContent value="actions" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <QuickActionCard
              title="Publicar Produtos"
              description="Postar produtos automaticamente no TikTok Shop"
              icon={<Package className="h-5 w-5" />}
              onClick={() => handleQuickAction("post_product")}
              disabled={createTaskMutation.isPending}
            />
            <QuickActionCard
              title="Gerenciar Pedidos"
              description="Imprimir etiquetas e processar envios"
              icon={<Truck className="h-5 w-5" />}
              onClick={() => handleQuickAction("manage_orders")}
              disabled={createTaskMutation.isPending}
            />
            <QuickActionCard
              title="Responder Mensagens"
              description="Responder automaticamente aos compradores"
              icon={<MessageSquare className="h-5 w-5" />}
              onClick={() => handleQuickAction("reply_messages")}
              disabled={createTaskMutation.isPending}
            />
            <QuickActionCard
              title="Extrair Analytics"
              description="Obter métricas de vendas e tráfego"
              icon={<BarChart3 className="h-5 w-5" />}
              onClick={() => handleQuickAction("analytics")}
              disabled={createTaskMutation.isPending}
            />
            <QuickActionCard
              title="Postar no Instagram"
              description="Publicar foto/vídeo no feed"
              icon={<Instagram className="h-5 w-5" />}
              onClick={() => handleQuickAction("instagram_post")}
              disabled={createTaskMutation.isPending}
            />
            <QuickActionCard
              title="Enviar WhatsApp"
              description="Disparo de mensagens em massa"
              icon={<Smartphone className="h-5 w-5" />}
              onClick={() => handleQuickAction("whatsapp_message")}
              disabled={createTaskMutation.isPending}
            />
            <QuickActionCard
              title="Upload TikTok"
              description="Publicar vídeo no TikTok"
              icon={<Video className="h-5 w-5" />}
              onClick={() => handleQuickAction("tiktok_upload")}
              disabled={createTaskMutation.isPending}
            />
            <QuickActionCard
              title="Upload YouTube"
              description="Publicar vídeo no YouTube"
              icon={<Youtube className="h-5 w-5" />}
              onClick={() => handleQuickAction("youtube_upload")}
              disabled={createTaskMutation.isPending}
            />
          </div>

          {/* Browser Viewer */}
          {(runningTask || browserViewerData.isActive) && (
            <Card className="mt-6">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Monitor className="h-5 w-5 text-primary" />
                  <CardTitle>Visualizador do Navegador</CardTitle>
                  {runningTask && (
                    <Badge variant="outline" className="animate-pulse">
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                      Executando
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <BrowserViewer
                  isActive={!!runningTask || browserViewerData.isActive}
                  currentUrl={browserViewerData.currentUrl}
                  screenshot={browserViewerData.screenshot}
                  status={browserViewerData.status || runningTask?.logs.slice(-1)[0]}
                  productsFound={0}
                  progress={0}
                  logs={runningTask?.logs || []}
                />
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Tasks Tab */}
        <TabsContent value="tasks">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Histórico de Tarefas</CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => queryClient.invalidateQueries({ queryKey: ["bot-tasks"] })}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Atualizar
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {botTasksLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : botTasks.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Nenhuma tarefa executada ainda</p>
                  <p className="text-sm">Use as Ações Rápidas para começar</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  {botTasks.map((task) => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      onCancel={() => cancelTaskMutation.mutate(task.id)}
                    />
                  ))}
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Profiles Tab */}
        <TabsContent value="profiles">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Perfis de Navegador</CardTitle>
                  <CardDescription>
                    Gerencie perfis Chrome com sessões salvas
                  </CardDescription>
                </div>
                <Dialog open={isNewProfileOpen} onOpenChange={setIsNewProfileOpen}>
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="h-4 w-4 mr-2" />
                      Novo Perfil
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Criar Novo Perfil</DialogTitle>
                      <DialogDescription>
                        Crie um perfil de navegador para manter suas sessões
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div className="space-y-2">
                        <Label htmlFor="profile-name">Nome do Perfil</Label>
                        <Input
                          id="profile-name"
                          placeholder="Ex: Minha Loja TikTok"
                          value={newProfileName}
                          onChange={(e) => setNewProfileName(e.target.value)}
                        />
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="clone-system"
                          checked={cloneFromSystem}
                          onCheckedChange={(checked) => setCloneFromSystem(checked as boolean)}
                        />
                        <Label htmlFor="clone-system" className="text-sm">
                          Clonar cookies do Chrome (manter login)
                        </Label>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button
                        onClick={() => createProfileMutation.mutate({
                          name: newProfileName,
                          clone_from_system: cloneFromSystem,
                        })}
                        disabled={!newProfileName || createProfileMutation.isPending}
                      >
                        {createProfileMutation.isPending ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <Chrome className="h-4 w-4 mr-2" />
                        )}
                        Criar Perfil
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {profilesLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : botProfiles.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Chrome className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Nenhum perfil criado</p>
                  <p className="text-sm">Crie um perfil para começar a usar o bot</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {botProfiles.map((profile) => (
                    <Card key={profile.id}>
                      <CardHeader className="py-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <Chrome className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <CardTitle className="text-sm">{profile.name}</CardTitle>
                              <CardDescription className="text-xs">
                                Criado em {new Date(profile.created_at).toLocaleDateString("pt-BR")}
                                {profile.last_used_at && (
                                  <> · Último uso: {new Date(profile.last_used_at).toLocaleDateString("pt-BR")}</>
                                )}
                              </CardDescription>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant={profile.is_logged_in ? "default" : "secondary"}>
                              {profile.is_logged_in ? "Logado" : "Não Logado"}
                            </Badge>
                            
                            {/* View Profile */}
                            <Dialog open={profileToView?.id === profile.id} onOpenChange={(open) => !open && setProfileToView(null)}>
                              <DialogTrigger asChild>
                                <Button 
                                  variant="ghost" 
                                  size="icon"
                                  onClick={() => setProfileToView(profile)}
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                              </DialogTrigger>
                              <DialogContent>
                                <DialogHeader>
                                  <DialogTitle>Detalhes do Perfil</DialogTitle>
                                </DialogHeader>
                                <div className="space-y-4 py-4">
                                  <div className="grid grid-cols-2 gap-4 text-sm">
                                    <div>
                                      <Label className="text-muted-foreground">ID</Label>
                                      <p className="font-mono">{profile.id}</p>
                                    </div>
                                    <div>
                                      <Label className="text-muted-foreground">Nome</Label>
                                      <p>{profile.name}</p>
                                    </div>
                                    <div>
                                      <Label className="text-muted-foreground">Status</Label>
                                      <p>{profile.is_logged_in ? "✅ Logado" : "❌ Não logado"}</p>
                                    </div>
                                    <div>
                                      <Label className="text-muted-foreground">Criado em</Label>
                                      <p>{new Date(profile.created_at).toLocaleString("pt-BR")}</p>
                                    </div>
                                  </div>
                                </div>
                                <DialogFooter>
                                  <Button
                                    variant="outline"
                                    onClick={() => verifyProfileMutation.mutate(profile.id)}
                                    disabled={verifyProfileMutation.isPending}
                                  >
                                    {verifyProfileMutation.isPending ? (
                                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    ) : (
                                      <RefreshCw className="h-4 w-4 mr-2" />
                                    )}
                                    Verificar Login
                                  </Button>
                                </DialogFooter>
                              </DialogContent>
                            </Dialog>
                            
                            {/* Delete Profile */}
                            <AlertDialog open={profileToDelete === profile.id} onOpenChange={(open) => !open && setProfileToDelete(null)}>
                              <AlertDialogTrigger asChild>
                                <Button 
                                  variant="ghost" 
                                  size="icon"
                                  onClick={() => setProfileToDelete(profile.id)}
                                >
                                  <Trash2 className="h-4 w-4 text-destructive" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Deletar perfil?</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    Isso irá remover permanentemente o perfil &quot;{profile.name}&quot; e todos os dados de sessão salvos.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancelar</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => deleteProfileMutation.mutate(profile.id)}
                                    className="bg-destructive text-destructive-foreground"
                                  >
                                    {deleteProfileMutation.isPending ? (
                                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    ) : null}
                                    Deletar
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </div>
                        </div>
                      </CardHeader>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SellerBot;
