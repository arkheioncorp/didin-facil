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
  Bot,
  Plus,
  Play,
  Pause,
  Settings,
  Trash2,
  Copy,
  MessageSquare,
  Users,
  BarChart3,
  Zap,
  Globe,
  Smartphone,
  Instagram,
  Phone,
} from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

interface Chatbot {
  id: string;
  name: string;
  description: string;
  typebot_id: string;
  status: 'active' | 'paused' | 'draft';
  channels: string[];
  total_sessions: number;
  total_messages: number;
  completion_rate: number;
  created_at: string;
  updated_at: string;
}

interface ChatbotStats {
  total_chatbots: number;
  active_chatbots: number;
  total_sessions_today: number;
  total_messages_today: number;
  avg_completion_rate: number;
  popular_flows: Array<{
    name: string;
    sessions: number;
    completion_rate: number;
  }>;
}

interface ChatbotTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  preview_url: string;
  tags: string[];
}

const channelIcons: Record<string, React.ReactNode> = {
  whatsapp: <Phone className="h-4 w-4" />,
  instagram: <Instagram className="h-4 w-4" />,
  web: <Globe className="h-4 w-4" />,
  app: <Smartphone className="h-4 w-4" />,
};

const statusColors: Record<string, string> = {
  active: 'bg-green-500/20 text-green-400',
  paused: 'bg-yellow-500/20 text-yellow-400',
  draft: 'bg-muted text-muted-foreground',
};

function ChatbotCard({ chatbot, onEdit, onDelete, onToggle }: {
  chatbot: Chatbot;
  onEdit: () => void;
  onDelete: () => void;
  onToggle: () => void;
}) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">{chatbot.name}</CardTitle>
          </div>
          <Badge className={statusColors[chatbot.status]}>
            {chatbot.status === 'active' ? 'Ativo' :
              chatbot.status === 'paused' ? 'Pausado' : 'Rascunho'}
          </Badge>
        </div>
        <CardDescription className="line-clamp-2">
          {chatbot.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Channels */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Canais:</span>
            <div className="flex gap-1">
              {chatbot.channels.map((channel) => (
                <Badge key={channel} variant="outline" className="gap-1">
                  {channelIcons[channel]}
                  <span className="capitalize">{channel}</span>
                </Badge>
              ))}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold">{chatbot.total_sessions.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">Sessões</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{chatbot.total_messages.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">Mensagens</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{chatbot.completion_rate}%</p>
              <p className="text-xs text-muted-foreground">Conclusão</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 pt-2 border-t">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={onEdit}
            >
              <Settings className="h-4 w-4 mr-1" />
              Editar
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onToggle}
            >
              {chatbot.status === 'active' ? (
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

function TemplateCard({ template, onUse }: {
  template: ChatbotTemplate;
  onUse: () => void;
}) {
  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={onUse}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{template.name}</CardTitle>
          <Badge variant="secondary">{template.category}</Badge>
        </div>
        <CardDescription className="line-clamp-2">
          {template.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-1 mb-4">
          {template.tags.map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>
        <Button className="w-full" size="sm">
          <Plus className="h-4 w-4 mr-1" />
          Usar Template
        </Button>
      </CardContent>
    </Card>
  );
}

function StatsOverview({ stats }: { stats: ChatbotStats }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Bot className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.total_chatbots}</p>
              <p className="text-sm text-muted-foreground">Total de Bots</p>
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
              <p className="text-2xl font-bold">{stats.active_chatbots}</p>
              <p className="text-sm text-muted-foreground">Bots Ativos</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.total_sessions_today}</p>
              <p className="text-sm text-muted-foreground">Sessões Hoje</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <MessageSquare className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.total_messages_today}</p>
              <p className="text-sm text-muted-foreground">Mensagens Hoje</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export const ChatbotBuilder = () => {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newBot, setNewBot] = useState({
    name: '',
    description: '',
    channels: [] as string[],
  });

  // Fetch chatbots
  const { data: chatbots, isLoading: isLoadingChatbots, error: chatbotsError, refetch: refetchChatbots } = useQuery<Chatbot[]>({
    queryKey: ['chatbots'],
    queryFn: async (): Promise<Chatbot[]> => {
      const response = await api.get('/chatbot/bots');
      return response.data as Chatbot[];
    },
  });

  // Fetch stats
const { data: stats, error: _statsError } = useQuery<ChatbotStats>({
    queryKey: ['chatbot-stats'],
    queryFn: async (): Promise<ChatbotStats> => {
      const response = await api.get('/chatbot/stats');
      return response.data as ChatbotStats;
    },
  });

  // Fetch templates
const { data: templates, error: _templatesError } = useQuery<ChatbotTemplate[]>({
    queryKey: ['chatbot-templates'],
    queryFn: async (): Promise<ChatbotTemplate[]> => {
      const response = await api.get('/chatbot/templates');
      // Backend now returns array directly
      const data = response.data;
      // Defensive: ensure we always return an array
      return Array.isArray(data) ? data : [];
    },
  });

  // Create chatbot mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newBot) =>
      api.post('/chatbot/bots', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] });
      queryClient.invalidateQueries({ queryKey: ['chatbot-stats'] });
      setIsCreateOpen(false);
      setNewBot({ name: '', description: '', channels: [] });
      toast.success('Chatbot criado com sucesso!');
    },
    onError: () => {
      toast.error('Erro ao criar chatbot');
    },
  });

  // Toggle status mutation
  const toggleMutation = useMutation({
    mutationFn: (id: string) =>
      api.post(`/chatbot/bots/${id}/toggle`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] });
      toast.success('Status atualizado!');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      api.delete(`/chatbot/bots/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] });
      queryClient.invalidateQueries({ queryKey: ['chatbot-stats'] });
      toast.success('Chatbot removido!');
    },
  });

  const handleChannelToggle = (channel: string) => {
    setNewBot(prev => ({
      ...prev,
      channels: prev.channels.includes(channel)
        ? prev.channels.filter(c => c !== channel)
        : [...prev.channels, channel],
    }));
  };

  const openTypebotEditor = (typebotId: string) => {
    const typebotUrl = import.meta.env.VITE_TYPEBOT_URL || 'https://app.typebot.io';
    window.open(`${typebotUrl}/typebots/${typebotId}/edit`, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Bot className="h-8 w-8" />
            Construtor de Chatbot
          </h1>
          <p className="text-muted-foreground mt-1">
            Crie fluxos de conversa automatizados com Typebot
          </p>
        </div>

        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Novo Chatbot
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Criar Novo Chatbot</DialogTitle>
              <DialogDescription>
                Configure seu novo chatbot e escolha os canais de atendimento.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nome do Chatbot</Label>
                <Input
                  id="name"
                  value={newBot.name}
                  onChange={(e) => setNewBot(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Ex: Atendimento WhatsApp"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Descrição</Label>
                <Input
                  id="description"
                  value={newBot.description}
                  onChange={(e) => setNewBot(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Descrição breve do chatbot"
                />
              </div>

              <div className="space-y-2">
                <Label>Canais</Label>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(channelIcons).map(([channel, icon]) => (
                    <Button
                      key={channel}
                      type="button"
                      variant={newBot.channels.includes(channel) ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => handleChannelToggle(channel)}
                      className="gap-1"
                    >
                      {icon}
                      <span className="capitalize">{channel}</span>
                    </Button>
                  ))}
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancelar
              </Button>
              <Button
                onClick={() => createMutation.mutate(newBot)}
                disabled={!newBot.name || newBot.channels.length === 0 || createMutation.isPending}
              >
                {createMutation.isPending ? 'Criando...' : 'Criar Chatbot'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      {stats && <StatsOverview stats={stats} />}

      {/* Tabs */}
      <Tabs defaultValue="chatbots" className="space-y-4">
        <TabsList>
          <TabsTrigger value="chatbots">
            <Bot className="h-4 w-4 mr-2" />
            Meus Chatbots
          </TabsTrigger>
          <TabsTrigger value="templates">
            <Copy className="h-4 w-4 mr-2" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="chatbots">
          {isLoadingChatbots ? (
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
          ) : chatbots?.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Bot className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-xl font-semibold mb-2">Nenhum chatbot criado</h3>
                <p className="text-muted-foreground mb-4">
                  Comece criando seu primeiro chatbot ou use um template.
                </p>
                <Button onClick={() => setIsCreateOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Criar Primeiro Chatbot
                </Button>
              </CardContent>
            </Card>
          ) : chatbotsError ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Bot className="h-16 w-16 text-destructive mb-4" />
                <h3 className="text-xl font-semibold mb-2">Erro ao carregar chatbots</h3>
                <p className="text-muted-foreground mb-4">
                  Não foi possível carregar os chatbots. Tente novamente.
                </p>
                <Button onClick={() => refetchChatbots()}>
                  Tentar Novamente
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {chatbots?.map((chatbot) => (
                <ChatbotCard
                  key={chatbot.id}
                  chatbot={chatbot}
                  onEdit={() => openTypebotEditor(chatbot.typebot_id)}
                  onDelete={() => deleteMutation.mutate(chatbot.id)}
                  onToggle={() => toggleMutation.mutate(chatbot.id)}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="templates">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates?.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onUse={() => {
                  setNewBot({
                    name: template.name,
                    description: template.description,
                    channels: ['whatsapp'],
                  });
                  setIsCreateOpen(true);
                }}
              />
            ))}
            {!templates?.length && (
              <Card className="col-span-full">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Copy className="h-16 w-16 text-muted-foreground mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Templates em breve</h3>
                  <p className="text-muted-foreground">
                    Estamos preparando templates prontos para uso.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="analytics">
          <Card>
            <CardHeader>
              <CardTitle>Fluxos Mais Populares</CardTitle>
              <CardDescription>
                Veja quais fluxos de conversa têm melhor desempenho
              </CardDescription>
            </CardHeader>
            <CardContent>
              {stats?.popular_flows?.length ? (
                <div className="space-y-4">
                  {stats.popular_flows.map((flow, index) => (
                    <div
                      key={flow.name}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div className="flex items-center gap-4">
                        <span className="text-2xl font-bold text-muted-foreground">
                          #{index + 1}
                        </span>
                        <div>
                          <p className="font-medium">{flow.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {flow.sessions.toLocaleString()} sessões
                          </p>
                        </div>
                      </div>
                      <Badge variant={flow.completion_rate > 70 ? 'default' : 'secondary'}>
                        {flow.completion_rate}% conclusão
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Nenhum dado disponível ainda
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ChatbotBuilder;
