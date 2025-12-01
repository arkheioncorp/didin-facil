import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  MessageSquare,
  Users,
  TrendingUp,
  Bot,
  Phone,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  Activity,
  Zap,
  Target,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  PieChart,
} from 'lucide-react';
import { whatsappService } from '@/lib/whatsapp';
// toast removed - not currently used

// Types
interface WhatsAppStats {
  total_messages: number;
  messages_sent: number;
  messages_received: number;
  active_conversations: number;
  unique_contacts: number;
  avg_response_time: number;
  bot_interactions: number;
  human_transfers: number;
}

interface ChatbotMetrics {
  total_sessions: number;
  product_searches: number;
  price_comparisons: number;
  alerts_created: number;
  conversion_rate: number;
  satisfaction_rate: number;
}

interface ConversationItem {
  id: string;
  contact_name: string;
  contact_phone: string;
  last_message: string;
  timestamp: string;
  status: 'active' | 'resolved' | 'pending';
  bot_active: boolean;
}

interface HourlyActivity {
  hour: number;
  messages: number;
}

// Mock data generator
const generateMockStats = (): WhatsAppStats => ({
  total_messages: Math.floor(Math.random() * 5000) + 1000,
  messages_sent: Math.floor(Math.random() * 2500) + 500,
  messages_received: Math.floor(Math.random() * 2500) + 500,
  active_conversations: Math.floor(Math.random() * 50) + 10,
  unique_contacts: Math.floor(Math.random() * 500) + 100,
  avg_response_time: Math.floor(Math.random() * 120) + 30,
  bot_interactions: Math.floor(Math.random() * 3000) + 500,
  human_transfers: Math.floor(Math.random() * 100) + 20,
});

const generateMockChatbotMetrics = (): ChatbotMetrics => ({
  total_sessions: Math.floor(Math.random() * 2000) + 500,
  product_searches: Math.floor(Math.random() * 1500) + 300,
  price_comparisons: Math.floor(Math.random() * 800) + 150,
  alerts_created: Math.floor(Math.random() * 200) + 50,
  conversion_rate: Math.random() * 30 + 10,
  satisfaction_rate: Math.random() * 20 + 75,
});

const generateMockConversations = (): ConversationItem[] => [
  {
    id: '1',
    contact_name: 'Maria Silva',
    contact_phone: '5511999999999',
    last_message: 'Encontrei o produto que você procurava!',
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
    status: 'active',
    bot_active: true,
  },
  {
    id: '2',
    contact_name: 'João Santos',
    contact_phone: '5511888888888',
    last_message: 'Obrigado pela ajuda!',
    timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
    status: 'resolved',
    bot_active: false,
  },
  {
    id: '3',
    contact_name: 'Ana Oliveira',
    contact_phone: '5511777777777',
    last_message: 'Quero falar com atendente',
    timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
    status: 'pending',
    bot_active: false,
  },
  {
    id: '4',
    contact_name: 'Pedro Costa',
    contact_phone: '5511666666666',
    last_message: 'Buscar smartwatch',
    timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
    status: 'active',
    bot_active: true,
  },
  {
    id: '5',
    contact_name: 'Carla Lima',
    contact_phone: '5511555555555',
    last_message: 'Qual o preço mais baixo?',
    timestamp: new Date(Date.now() - 60 * 60000).toISOString(),
    status: 'active',
    bot_active: true,
  },
];

const generateHourlyActivity = (): HourlyActivity[] => {
  return Array.from({ length: 24 }, (_, i) => ({
    hour: i,
    messages: Math.floor(Math.random() * 100) + (i >= 9 && i <= 18 ? 50 : 10),
  }));
};

// Components
function MetricCard({
  title,
  value,
  change,
  icon,
  trend,
}: {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="p-2 rounded-lg bg-primary/10">{icon}</div>
          {change !== undefined && (
            <Badge variant={trend === 'up' ? 'default' : trend === 'down' ? 'destructive' : 'secondary'}>
              {trend === 'up' ? <ArrowUpRight className="h-3 w-3 mr-1" /> : <ArrowDownRight className="h-3 w-3 mr-1" />}
              {Math.abs(change)}%
            </Badge>
          )}
        </div>
        <div className="mt-4">
          <p className="text-2xl font-bold">{typeof value === 'number' ? value.toLocaleString('pt-BR') : value}</p>
          <p className="text-sm text-muted-foreground">{title}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function ActivityChart({ data }: { data: HourlyActivity[] }) {
  const maxMessages = Math.max(...data.map(d => d.messages));
  
  return (
    <div className="flex items-end gap-1 h-32">
      {data.map((item) => (
        <div
          key={item.hour}
          className="flex-1 bg-primary/20 hover:bg-primary/40 transition-colors rounded-t cursor-pointer relative group"
          style={{ height: `${(item.messages / maxMessages) * 100}%` }}
        >
          <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-popover px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
            {item.hour}h: {item.messages} msgs
          </div>
        </div>
      ))}
    </div>
  );
}

function ConversationList({ conversations }: { conversations: ConversationItem[] }) {
  const getStatusColor = (status: ConversationItem['status']) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'resolved': return 'bg-gray-400';
      case 'pending': return 'bg-yellow-500';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 60000);
    
    if (diff < 1) return 'Agora';
    if (diff < 60) return `${diff}min`;
    if (diff < 1440) return `${Math.floor(diff / 60)}h`;
    return date.toLocaleDateString('pt-BR');
  };

  return (
    <ScrollArea className="h-64">
      <div className="space-y-2">
        {conversations.map((conv) => (
          <div key={conv.id} className="flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors">
            <div className="relative">
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                <span className="text-sm font-medium">
                  {conv.contact_name.split(' ').map(n => n[0]).join('')}
                </span>
              </div>
              <span className={`absolute bottom-0 right-0 w-3 h-3 rounded-full ${getStatusColor(conv.status)}`} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="font-medium truncate">{conv.contact_name}</span>
                <span className="text-xs text-muted-foreground">{formatTime(conv.timestamp)}</span>
              </div>
              <div className="flex items-center gap-2">
                <p className="text-sm text-muted-foreground truncate">{conv.last_message}</p>
                {conv.bot_active && <Bot className="h-3 w-3 text-blue-500" />}
              </div>
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}

function ChatbotFunnel({ metrics }: { metrics: ChatbotMetrics }) {
  const funnelData = [
    { label: 'Sessões Iniciadas', value: metrics.total_sessions, color: 'bg-blue-500' },
    { label: 'Buscas de Produtos', value: metrics.product_searches, color: 'bg-green-500' },
    { label: 'Comparações de Preço', value: metrics.price_comparisons, color: 'bg-yellow-500' },
    { label: 'Alertas Criados', value: metrics.alerts_created, color: 'bg-purple-500' },
  ];

  const maxValue = Math.max(...funnelData.map(d => d.value));

  return (
    <div className="space-y-4">
      {funnelData.map((item, index) => (
        <div key={index} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span>{item.label}</span>
            <span className="font-medium">{item.value.toLocaleString('pt-BR')}</span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className={`h-full ${item.color} transition-all duration-500`}
              style={{ width: `${(item.value / maxValue) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function WhatsAppAnalytics() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<WhatsAppStats | null>(null);
  const [chatbotMetrics, setChatbotMetrics] = useState<ChatbotMetrics | null>(null);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [hourlyActivity, setHourlyActivity] = useState<HourlyActivity[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  const fetchData = async () => {
    setLoading(true);
    
    try {
      // Check WhatsApp connection
      const state = await whatsappService.getConnectionState();
      setConnectionStatus(state.instance.state === 'open' ? 'connected' : 'disconnected');
      
      // For now, use mock data (in production, fetch from backend)
      setStats(generateMockStats());
      setChatbotMetrics(generateMockChatbotMetrics());
      setConversations(generateMockConversations());
      setHourlyActivity(generateHourlyActivity());
      
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setConnectionStatus('disconnected');
      
      // Still show mock data for demo
      setStats(generateMockStats());
      setChatbotMetrics(generateMockChatbotMetrics());
      setConversations(generateMockConversations());
      setHourlyActivity(generateHourlyActivity());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">📊 Analytics WhatsApp</h1>
          <p className="text-muted-foreground">Métricas de mensagens, chatbot e conversões</p>
        </div>
        <div className="flex items-center gap-4">
          <Badge 
            variant={connectionStatus === 'connected' ? 'default' : 'destructive'}
            className="flex items-center gap-2"
          >
            {connectionStatus === 'connected' ? (
              <><CheckCircle className="h-3 w-3" /> WhatsApp Conectado</>
            ) : connectionStatus === 'checking' ? (
              <><RefreshCw className="h-3 w-3 animate-spin" /> Verificando...</>
            ) : (
              <><XCircle className="h-3 w-3" /> WhatsApp Desconectado</>
            )}
          </Badge>
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>
      </div>

      {/* Main Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total de Mensagens"
          value={stats?.total_messages || 0}
          change={12}
          trend="up"
          icon={<MessageSquare className="h-5 w-5 text-primary" />}
        />
        <MetricCard
          title="Conversas Ativas"
          value={stats?.active_conversations || 0}
          change={5}
          trend="up"
          icon={<Activity className="h-5 w-5 text-green-500" />}
        />
        <MetricCard
          title="Contatos Únicos"
          value={stats?.unique_contacts || 0}
          change={8}
          trend="up"
          icon={<Users className="h-5 w-5 text-blue-500" />}
        />
        <MetricCard
          title="Tempo Médio de Resposta"
          value={`${stats?.avg_response_time || 0}s`}
          change={-15}
          trend="up"
          icon={<Clock className="h-5 w-5 text-yellow-500" />}
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Interações do Bot"
          value={stats?.bot_interactions || 0}
          icon={<Bot className="h-5 w-5 text-purple-500" />}
        />
        <MetricCard
          title="Transferências para Humano"
          value={stats?.human_transfers || 0}
          icon={<Phone className="h-5 w-5 text-orange-500" />}
        />
        <MetricCard
          title="Taxa de Conversão"
          value={`${chatbotMetrics?.conversion_rate.toFixed(1) || 0}%`}
          change={3}
          trend="up"
          icon={<Target className="h-5 w-5 text-red-500" />}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Atividade por Hora
            </CardTitle>
            <CardDescription>Mensagens recebidas nas últimas 24h</CardDescription>
          </CardHeader>
          <CardContent>
            <ActivityChart data={hourlyActivity} />
            <div className="flex justify-between mt-2 text-xs text-muted-foreground">
              <span>0h</span>
              <span>6h</span>
              <span>12h</span>
              <span>18h</span>
              <span>23h</span>
            </div>
          </CardContent>
        </Card>

        {/* Chatbot Funnel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Funil do Chatbot
            </CardTitle>
            <CardDescription>Jornada do usuário no bot</CardDescription>
          </CardHeader>
          <CardContent>
            {chatbotMetrics && <ChatbotFunnel metrics={chatbotMetrics} />}
          </CardContent>
        </Card>
      </div>

      {/* Conversations & Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Conversations */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Conversas Recentes
            </CardTitle>
            <CardDescription>Últimas interações do chatbot</CardDescription>
          </CardHeader>
          <CardContent>
            <ConversationList conversations={conversations} />
          </CardContent>
        </Card>

        {/* Performance Indicators */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Indicadores de Performance
            </CardTitle>
            <CardDescription>Métricas de qualidade do atendimento</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Taxa de Satisfação</span>
                <span className="font-medium">{chatbotMetrics?.satisfaction_rate.toFixed(1) || 0}%</span>
              </div>
              <Progress value={chatbotMetrics?.satisfaction_rate || 0} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Resoluções pelo Bot</span>
                <span className="font-medium">
                  {stats ? Math.round((stats.bot_interactions / stats.total_messages) * 100) : 0}%
                </span>
              </div>
              <Progress 
                value={stats ? (stats.bot_interactions / stats.total_messages) * 100 : 0} 
                className="h-2" 
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Taxa de Resposta</span>
                <span className="font-medium">98.5%</span>
              </div>
              <Progress value={98.5} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>NPS Score</span>
                <span className="font-medium">+72</span>
              </div>
              <Progress value={72} className="h-2" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-green-500/10 to-green-500/5 border-green-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/20">
                <TrendingUp className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.messages_sent || 0}</p>
                <p className="text-sm text-muted-foreground">Mensagens Enviadas</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <MessageSquare className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.messages_received || 0}</p>
                <p className="text-sm text-muted-foreground">Mensagens Recebidas</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-500/10 to-purple-500/5 border-purple-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/20">
                <Bot className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{chatbotMetrics?.product_searches || 0}</p>
                <p className="text-sm text-muted-foreground">Buscas de Produtos</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-orange-500/10 to-orange-500/5 border-orange-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-500/20">
                <Target className="h-5 w-5 text-orange-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{chatbotMetrics?.alerts_created || 0}</p>
                <p className="text-sm text-muted-foreground">Alertas Criados</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default WhatsAppAnalytics;
