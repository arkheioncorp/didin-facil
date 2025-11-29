import React from "react";
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
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { BrowserViewer } from "@/components/scraper/BrowserViewer";

// ============================================
// Types
// ============================================

interface Task {
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

interface QueueStats {
  total_queued: number;
  total_running: number;
  total_completed: number;
  total_failed: number;
  by_task_type: Record<string, number>;
}

interface Profile {
  id: string;
  name: string;
  is_logged_in: boolean;
  last_used_at?: string;
  created_at: string;
}

// ============================================
// API Functions (Mocked for now)
// ============================================

const API_BASE = "http://localhost:8000";

async function fetchTasks(): Promise<Task[]> {
  // TODO: Replace with actual API call
  return [];
}

async function fetchStats(): Promise<QueueStats> {
  return {
    total_queued: 0,
    total_running: 0,
    total_completed: 0,
    total_failed: 0,
    by_task_type: {},
  };
}

async function fetchProfiles(): Promise<Profile[]> {
  return [];
}

async function createTask(data: { task_type: string; task_data?: Record<string, unknown> }): Promise<Task> {
  const response = await fetch(`${API_BASE}/bot/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return response.json();
}

async function cancelTask(taskId: string): Promise<void> {
  await fetch(`${API_BASE}/bot/tasks/${taskId}`, { method: "DELETE" });
}

async function createProfile(data: { name: string; clone_from_system: boolean }): Promise<Profile> {
  const response = await fetch(`${API_BASE}/bot/profiles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return response.json();
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
    default:
      return <Settings className="h-4 w-4" />;
  }
};

const TaskStatusBadge: React.FC<{ state: Task["state"] }> = ({ state }) => {
  const variants: Record<Task["state"], { variant: "default" | "secondary" | "destructive" | "outline"; icon: React.ReactNode }> = {
    queued: { variant: "secondary", icon: <Clock className="h-3 w-3" /> },
    running: { variant: "default", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
    completed: { variant: "outline", icon: <CheckCircle2 className="h-3 w-3 text-green-500" /> },
    failed: { variant: "destructive", icon: <XCircle className="h-3 w-3" /> },
    cancelled: { variant: "secondary", icon: <Square className="h-3 w-3" /> },
  };

  const { variant, icon } = variants[state];

  return (
    <Badge variant={variant} className="gap-1">
      {icon}
      {state.charAt(0).toUpperCase() + state.slice(1)}
    </Badge>
  );
};

const TaskCard: React.FC<{ task: Task; onCancel: () => void }> = ({ task, onCancel }) => {
  const taskTypeLabels: Record<string, string> = {
    post_product: "Publicar Produto",
    manage_orders: "Gerenciar Pedidos",
    reply_messages: "Responder Mensagens",
    analytics: "Extrair Analytics",
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
              <Button variant="ghost" size="icon" onClick={onCancel}>
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
          {task.error_message && (
            <p className="text-destructive">Erro: {task.error_message}</p>
          )}
        </div>
        {task.logs.length > 0 && (
          <ScrollArea className="h-24 mt-2 rounded border p-2">
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
    className={`cursor-pointer transition-all hover:border-primary ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
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
  const [isNewProfileOpen, setIsNewProfileOpen] = React.useState(false);
  const [newProfileName, setNewProfileName] = React.useState("");
  const [cloneFromSystem, setCloneFromSystem] = React.useState(true);
  const [browserViewerData, setBrowserViewerData] = React.useState<{
    isActive: boolean;
    currentUrl?: string;
    screenshot?: string;
    status?: string;
  }>({ isActive: false });

  // Queries
  const { data: tasks = [], isLoading: tasksLoading } = useQuery({
    queryKey: ["bot-tasks"],
    queryFn: fetchTasks,
    refetchInterval: 3000,
  });

  const { data: stats } = useQuery({
    queryKey: ["bot-stats"],
    queryFn: fetchStats,
    refetchInterval: 5000,
  });

  const { data: profiles = [] } = useQuery({
    queryKey: ["bot-profiles"],
    queryFn: fetchProfiles,
  });

  // Mutations
  const createTaskMutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bot-tasks"] });
    },
  });

  const cancelTaskMutation = useMutation({
    mutationFn: cancelTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bot-tasks"] });
    },
  });

  const createProfileMutation = useMutation({
    mutationFn: createProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bot-profiles"] });
      setIsNewProfileOpen(false);
      setNewProfileName("");
    },
  });

  // Handlers
  const handleQuickAction = (taskType: string) => {
    createTaskMutation.mutate({ task_type: taskType });
    setBrowserViewerData({ isActive: true, status: "Iniciando..." });
  };

  const runningTask = tasks.find((t) => t.state === "running");

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
            Automação completa da Central do Vendedor TikTok Shop
          </p>
        </div>
        <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/50">
          Premium R$149,90/mês
        </Badge>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Na Fila</CardDescription>
            <CardTitle className="text-2xl">{stats?.total_queued || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Executando</CardDescription>
            <CardTitle className="text-2xl text-blue-500">{stats?.total_running || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Concluídas</CardDescription>
            <CardTitle className="text-2xl text-green-500">{stats?.total_completed || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Falhas</CardDescription>
            <CardTitle className="text-2xl text-destructive">{stats?.total_failed || 0}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="actions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="actions">Ações Rápidas</TabsTrigger>
          <TabsTrigger value="tasks">Tarefas ({tasks.length})</TabsTrigger>
          <TabsTrigger value="profiles">Perfis ({profiles.length})</TabsTrigger>
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
              {tasksLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : tasks.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Nenhuma tarefa executada ainda</p>
                  <p className="text-sm">Use as Ações Rápidas para começar</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  {tasks.map((task) => (
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
                    <Button
                      className="w-full"
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
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {profiles.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Chrome className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Nenhum perfil criado</p>
                  <p className="text-sm">Crie um perfil para começar a usar o bot</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {profiles.map((profile) => (
                    <Card key={profile.id}>
                      <CardHeader className="py-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <Chrome className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <CardTitle className="text-sm">{profile.name}</CardTitle>
                              <CardDescription className="text-xs">
                                Criado em {new Date(profile.created_at).toLocaleDateString("pt-BR")}
                              </CardDescription>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant={profile.is_logged_in ? "default" : "secondary"}>
                              {profile.is_logged_in ? "Logado" : "Não Logado"}
                            </Badge>
                            <Button variant="ghost" size="icon">
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon">
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
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
