import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Workflow,
  Plus,
  Play,
  Pause,
  Trash2,
  ExternalLink,
  Zap,
  Clock,
  CheckCircle2,
  XCircle,
  History,
  RefreshCw,
  ChevronRight,
} from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface N8nWorkflow {
  id: string;
  name: string;
  description: string;
  n8n_workflow_id: string;
  status: 'active' | 'inactive' | 'error';
  trigger_type: 'webhook' | 'schedule' | 'manual';
  last_run: string | null;
  total_executions: number;
  success_rate: number;
  created_at: string;
}

interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: 'success' | 'error' | 'running';
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
  error_message: string | null;
}

interface WorkflowStats {
  total_workflows: number;
  active_workflows: number;
  total_executions_today: number;
  success_rate: number;
  avg_execution_time_ms: number;
}

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  triggers: string[];
  actions: string[];
}

const statusIcons: Record<string, React.ReactNode> = {
  success: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  error: <XCircle className="h-4 w-4 text-red-500" />,
  running: <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />,
};

const triggerBadges: Record<string, { label: string; variant: 'default' | 'secondary' | 'outline' }> = {
  webhook: { label: 'Webhook', variant: 'default' },
  schedule: { label: 'Agendado', variant: 'secondary' },
  manual: { label: 'Manual', variant: 'outline' },
};

function WorkflowCard({ workflow, onEdit, onDelete, onToggle, onRun }: {
  workflow: N8nWorkflow;
  onEdit: () => void;
  onDelete: () => void;
  onToggle: () => void;
  onRun: () => void;
}) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Workflow className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">{workflow.name}</CardTitle>
          </div>
          <Badge variant={workflow.status === 'active' ? 'default' : 
                         workflow.status === 'error' ? 'destructive' : 'secondary'}>
            {workflow.status === 'active' ? 'Ativo' : 
             workflow.status === 'error' ? 'Erro' : 'Inativo'}
          </Badge>
        </div>
        <CardDescription className="line-clamp-2">
          {workflow.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Trigger Type */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Gatilho:</span>
            <Badge variant={triggerBadges[workflow.trigger_type].variant}>
              {triggerBadges[workflow.trigger_type].label}
            </Badge>
          </div>

          {/* Last Run */}
          {workflow.last_run && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>
                Última execução: {formatDistanceToNow(new Date(workflow.last_run), {
                  addSuffix: true,
                  locale: ptBR,
                })}
              </span>
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold">{workflow.total_executions}</p>
              <p className="text-xs text-muted-foreground">Execuções</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{workflow.success_rate}%</p>
              <p className="text-xs text-muted-foreground">Sucesso</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 pt-2 border-t">
            {workflow.trigger_type === 'manual' && (
              <Button 
                variant="default" 
                size="sm"
                onClick={onRun}
                className="flex-1"
              >
                <Play className="h-4 w-4 mr-1" />
                Executar
              </Button>
            )}
            <Button 
              variant="outline" 
              size="sm" 
              className={workflow.trigger_type !== 'manual' ? 'flex-1' : ''}
              onClick={onEdit}
            >
              <ExternalLink className="h-4 w-4 mr-1" />
              Editar no n8n
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={onToggle}
            >
              {workflow.status === 'active' ? (
                <Pause className="h-4 w-4" />
              ) : (
                <Play className="h-4 w-4" />
              )}
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={onDelete}
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ExecutionRow({ execution }: { execution: WorkflowExecution }) {
  return (
    <div className="flex items-center justify-between p-3 border rounded-lg">
      <div className="flex items-center gap-3">
        {statusIcons[execution.status]}
        <div>
          <p className="text-sm font-medium">
            Execução #{execution.id.slice(0, 8)}
          </p>
          <p className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(execution.started_at), {
              addSuffix: true,
              locale: ptBR,
            })}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        {execution.duration_ms && (
          <span className="text-sm text-muted-foreground">
            {execution.duration_ms}ms
          </span>
        )}
        {execution.error_message && (
          <Badge variant="destructive" className="truncate max-w-[200px]">
            {execution.error_message}
          </Badge>
        )}
        <Button variant="ghost" size="sm">
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

function StatsOverview({ stats }: { stats: WorkflowStats }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Workflow className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.total_workflows}</p>
              <p className="text-sm text-muted-foreground">Workflows</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-green-100 rounded-lg">
              <Zap className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.active_workflows}</p>
              <p className="text-sm text-muted-foreground">Ativos</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Play className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.total_executions_today}</p>
              <p className="text-sm text-muted-foreground">Exec. Hoje</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.success_rate}%</p>
              <p className="text-sm text-muted-foreground">Sucesso</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Clock className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.avg_execution_time_ms}ms</p>
              <p className="text-sm text-muted-foreground">Tempo Médio</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export const Workflows = () => {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newWorkflow, setNewWorkflow] = useState({
    name: '',
    description: '',
    trigger_type: 'webhook' as 'webhook' | 'schedule' | 'manual',
  });

  // Fetch workflows
  const { data: workflows, isLoading: isLoadingWorkflows } = useQuery<N8nWorkflow[]>({
    queryKey: ['workflows'],
    queryFn: async (): Promise<N8nWorkflow[]> => {
      const response = await api.get('/automation/workflows');
      return response.data as N8nWorkflow[];
    },
  });

  // Fetch stats
  const { data: stats } = useQuery<WorkflowStats>({
    queryKey: ['workflow-stats'],
    queryFn: async (): Promise<WorkflowStats> => {
      const response = await api.get('/automation/stats');
      return response.data as WorkflowStats;
    },
  });

  // Fetch executions
  const { data: executions } = useQuery<WorkflowExecution[]>({
    queryKey: ['workflow-executions'],
    queryFn: async (): Promise<WorkflowExecution[]> => {
      const response = await api.get('/automation/executions');
      return response.data as WorkflowExecution[];
    },
  });

  // Fetch templates
  const { data: templates } = useQuery<WorkflowTemplate[]>({
    queryKey: ['workflow-templates'],
    queryFn: async (): Promise<WorkflowTemplate[]> => {
      const response = await api.get('/automation/templates');
      return response.data as WorkflowTemplate[];
    },
  });

  // Create workflow mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newWorkflow) => 
      api.post('/automation/workflows', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['workflow-stats'] });
      setIsCreateOpen(false);
      setNewWorkflow({ name: '', description: '', trigger_type: 'webhook' });
      toast.success('Workflow criado com sucesso!');
    },
    onError: () => {
      toast.error('Erro ao criar workflow');
    },
  });

  // Toggle status mutation
  const toggleMutation = useMutation({
    mutationFn: (id: string) => 
      api.post(`/automation/workflows/${id}/toggle`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      toast.success('Status atualizado!');
    },
  });

  // Run workflow mutation
  const runMutation = useMutation({
    mutationFn: (id: string) => 
      api.post(`/automation/workflows/${id}/run`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow-executions'] });
      toast.success('Workflow executado!');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => 
      api.delete(`/automation/workflows/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['workflow-stats'] });
      toast.success('Workflow removido!');
    },
  });

  const openN8nEditor = (n8nWorkflowId: string) => {
    const n8nUrl = import.meta.env.VITE_N8N_URL || 'https://n8n.tiktrendfinder.app';
    window.open(`${n8nUrl}/workflow/${n8nWorkflowId}`, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Workflow className="h-8 w-8" />
            Automações n8n
          </h1>
          <p className="text-muted-foreground mt-1">
            Gerencie workflows de automação com n8n
          </p>
        </div>
        
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Novo Workflow
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Criar Novo Workflow</DialogTitle>
              <DialogDescription>
                Configure seu novo workflow de automação.
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nome do Workflow</Label>
                <Input
                  id="name"
                  value={newWorkflow.name}
                  onChange={(e) => setNewWorkflow(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Ex: Notificar novo lead"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Descrição</Label>
                <Input
                  id="description"
                  value={newWorkflow.description}
                  onChange={(e) => setNewWorkflow(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="O que este workflow faz?"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Tipo de Gatilho</Label>
                <Select 
                  value={newWorkflow.trigger_type}
                  onValueChange={(value: 'webhook' | 'schedule' | 'manual') => 
                    setNewWorkflow(prev => ({ ...prev, trigger_type: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o gatilho" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="webhook">Webhook (Evento)</SelectItem>
                    <SelectItem value="schedule">Agendado (Cron)</SelectItem>
                    <SelectItem value="manual">Manual</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancelar
              </Button>
              <Button 
                onClick={() => createMutation.mutate(newWorkflow)}
                disabled={!newWorkflow.name || createMutation.isPending}
              >
                {createMutation.isPending ? 'Criando...' : 'Criar Workflow'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      {stats && <StatsOverview stats={stats} />}

      {/* Tabs */}
      <Tabs defaultValue="workflows" className="space-y-4">
        <TabsList>
          <TabsTrigger value="workflows">
            <Workflow className="h-4 w-4 mr-2" />
            Workflows
          </TabsTrigger>
          <TabsTrigger value="executions">
            <History className="h-4 w-4 mr-2" />
            Execuções
          </TabsTrigger>
          <TabsTrigger value="templates">
            <Zap className="h-4 w-4 mr-2" />
            Templates
          </TabsTrigger>
        </TabsList>

        <TabsContent value="workflows">
          {isLoadingWorkflows ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-6 w-40" />
                    <Skeleton className="h-4 w-full" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-20 w-full" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : workflows?.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Workflow className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-xl font-semibold mb-2">Nenhum workflow criado</h3>
                <p className="text-muted-foreground mb-4">
                  Comece criando seu primeiro workflow de automação.
                </p>
                <Button onClick={() => setIsCreateOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Criar Primeiro Workflow
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {workflows?.map((workflow) => (
                <WorkflowCard
                  key={workflow.id}
                  workflow={workflow}
                  onEdit={() => openN8nEditor(workflow.n8n_workflow_id)}
                  onDelete={() => deleteMutation.mutate(workflow.id)}
                  onToggle={() => toggleMutation.mutate(workflow.id)}
                  onRun={() => runMutation.mutate(workflow.id)}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="executions">
          <Card>
            <CardHeader>
              <CardTitle>Histórico de Execuções</CardTitle>
              <CardDescription>
                Últimas execuções de workflows
              </CardDescription>
            </CardHeader>
            <CardContent>
              {executions?.length ? (
                <div className="space-y-2">
                  {executions.map((execution) => (
                    <ExecutionRow key={execution.id} execution={execution} />
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Nenhuma execução registrada
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="templates">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates?.map((template) => (
              <Card key={template.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{template.name}</CardTitle>
                    <Badge variant="secondary">{template.category}</Badge>
                  </div>
                  <CardDescription className="line-clamp-2">
                    {template.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 mb-4">
                    <div className="flex flex-wrap gap-1">
                      <span className="text-xs font-medium">Gatilhos:</span>
                      {template.triggers.map((trigger) => (
                        <Badge key={trigger} variant="outline" className="text-xs">
                          {trigger}
                        </Badge>
                      ))}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      <span className="text-xs font-medium">Ações:</span>
                      {template.actions.map((action) => (
                        <Badge key={action} variant="outline" className="text-xs">
                          {action}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Button 
                    className="w-full" 
                    size="sm"
                    onClick={() => {
                      setNewWorkflow({
                        name: template.name,
                        description: template.description,
                        trigger_type: 'webhook',
                      });
                      setIsCreateOpen(true);
                    }}
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Usar Template
                  </Button>
                </CardContent>
              </Card>
            ))}
            {!templates?.length && (
              <Card className="col-span-full">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Zap className="h-16 w-16 text-muted-foreground mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Templates em breve</h3>
                  <p className="text-muted-foreground">
                    Estamos preparando templates de automação prontos.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Workflows;
