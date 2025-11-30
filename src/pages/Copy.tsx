import * as React from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { SettingLabel } from "@/components/ui/info-tooltip";
import { 
  SparkleIcon, 
  CopyIcon, 
  StarIcon,
  SearchIcon,
  ChartIcon
} from "@/components/icons";
import { 
  Zap, 
  MessageSquare, 
  Image, 
  Clock, 
  TrendingUp, 
  Send, 
  RefreshCw,
  Wand2,
  Target,
  ShoppingCart,
  Bell,
  Calendar,
  FileText,
  Users,
  BarChart3,
  Palette,
  Layers,
  ChevronRight,
  Play,
  CheckCircle2,
  Lightbulb,
  Flame,
  Instagram,
  Youtube,
  Phone,
  ExternalLink,
  Download,
  History,
  Award
} from "lucide-react";
import { COPY_TYPES, COPY_TONES } from "@/lib/constants";
import { formatCurrency } from "@/lib/utils";
import { generateCopy, getCopyHistory, getFavorites } from "@/lib/tauri";
import { api } from "@/lib/api";
import type { FavoriteWithProduct, CopyHistory } from "@/types";
import type { CopyType, CopyTone } from "@/types";
import { analytics } from "@/lib/analytics";
import { useToast } from "@/hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

// =============================================================================
// TYPES
// =============================================================================

interface CopyFormState {
  selectedProductId: string | null;
  copyType: CopyType;
  tone: CopyTone;
  generatedCopy: string | null;
  isGenerating: boolean;
  selectedPlatform: string | null;
  selectedType: CopyType | null;
}

interface ContentTemplate {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  platform: string;
  category: string;
  captionTemplate: string;
  variables: { name: string; description: string }[];
  hashtags: string[];
  bestTimes: string[];
  engagement: string;
}

interface AutomationWorkflow {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  category: string;
  trigger: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  estimatedTime: string;
  integrations: string[];
  steps?: Array<{
    name: string;
    type: string;
    config?: Record<string, unknown>;
  }>;
}

// =============================================================================
// CONTENT TEMPLATES DATA
// =============================================================================

const CONTENT_TEMPLATES: ContentTemplate[] = [
  {
    id: "flash_sale",
    name: "Promoção Relâmpago",
    description: "Post de promoção com urgência e FOMO",
    icon: <Flame className="h-5 w-5 text-orange-500" />,
    platform: "all",
    category: "promo",
    captionTemplate: `🔥 PROMOÇÃO RELÂMPAGO! 🔥

⚡ {{product_name}} com {{discount_percent}}% OFF!

De R$ {{original_price}} por apenas R$ {{sale_price}}

⏰ SÓ {{hours_remaining}} HORAS para aproveitar!

Link na bio 👆 ou arraste pra cima!`,
    variables: [
      { name: "product_name", description: "Nome do produto" },
      { name: "discount_percent", description: "Percentual de desconto" },
      { name: "original_price", description: "Preço original" },
      { name: "sale_price", description: "Preço promocional" },
      { name: "hours_remaining", description: "Horas restantes" },
    ],
    hashtags: ["#promoção", "#desconto", "#oferta", "#economia"],
    bestTimes: ["12:00", "18:00", "21:00"],
    engagement: "Alto - posts de urgência têm 2-3x mais engajamento",
  },
  {
    id: "price_drop_alert",
    name: "Alerta de Queda de Preço",
    description: "Aviso de produto que baixou de preço (Reels)",
    icon: <TrendingUp className="h-5 w-5 text-green-500" />,
    platform: "instagram",
    category: "promo",
    captionTemplate: `🚨 CAIU O PREÇO! 🚨

{{product_name}} que você ama estava R$ {{old_price}}...

AGORA: R$ {{new_price}}! 🤯

💰 Economia de R$ {{savings}}!

Quer receber alertas assim? Link na bio!`,
    variables: [
      { name: "product_name", description: "Nome do produto" },
      { name: "old_price", description: "Preço anterior" },
      { name: "new_price", description: "Preço atual" },
      { name: "savings", description: "Valor economizado" },
    ],
    hashtags: ["#quedadepreço", "#economia", "#alerta", "#oferta"],
    bestTimes: ["11:00", "14:00", "20:00"],
    engagement: "Muito Alto - formato reels + preço = viral potential",
  },
  {
    id: "daily_deals",
    name: "Ofertas do Dia",
    description: "Compilado das melhores ofertas diárias (Carousel)",
    icon: <Calendar className="h-5 w-5 text-blue-500" />,
    platform: "instagram",
    category: "promo",
    captionTemplate: `📱 OFERTAS DO DIA {{date}} 📱

Slide 1: {{deal_1_name}} - R$ {{deal_1_price}} ⬇️
Slide 2: {{deal_2_name}} - R$ {{deal_2_price}} ⬇️
Slide 3: {{deal_3_name}} - R$ {{deal_3_price}} ⬇️

💡 Todas verificadas e no menor preço!

Qual você vai garantir? 👇`,
    variables: [
      { name: "date", description: "Data (ex: 26/11)" },
      { name: "deal_1_name", description: "Nome oferta 1" },
      { name: "deal_1_price", description: "Preço oferta 1" },
      { name: "deal_2_name", description: "Nome oferta 2" },
      { name: "deal_2_price", description: "Preço oferta 2" },
      { name: "deal_3_name", description: "Nome oferta 3" },
      { name: "deal_3_price", description: "Preço oferta 3" },
    ],
    hashtags: ["#ofertasdodia", "#deals", "#promocao", "#economia"],
    bestTimes: ["07:00", "12:00", "19:00"],
    engagement: "Médio-Alto - carrosséis têm 1.4x mais alcance",
  },
  {
    id: "product_review",
    name: "Review de Produto",
    description: "Análise detalhada de produto (YouTube)",
    icon: <Youtube className="h-5 w-5 text-red-500" />,
    platform: "youtube",
    category: "educacional",
    captionTemplate: `📦 REVIEW: {{product_name}} - Vale a Pena?

Neste vídeo eu analiso o {{product_name}} que está em alta no TikTok Shop!

⏱️ TIMESTAMPS:
0:00 - Introdução
1:30 - Unboxing
3:00 - Primeiras impressões
5:00 - Teste na prática
8:00 - Pontos positivos
9:30 - Pontos negativos
11:00 - Veredicto final

🔗 Links na descrição!`,
    variables: [
      { name: "product_name", description: "Nome do produto" },
    ],
    hashtags: ["#review", "#unboxing", "#tiktokshop", "#analise"],
    bestTimes: ["10:00", "15:00", "20:00"],
    engagement: "Alto - reviews têm alta retenção",
  },
  {
    id: "poll_post",
    name: "Enquete Engajamento",
    description: "Post interativo com enquete",
    icon: <Users className="h-5 w-5 text-purple-500" />,
    platform: "all",
    category: "engajamento",
    captionTemplate: `🤔 ME AJUDA A DECIDIR!

Estou de olho nesses dois produtos:

1️⃣ {{option_a}}
2️⃣ {{option_b}}

Qual você compraria? Comenta aqui! 👇

{{hashtags}}`,
    variables: [
      { name: "option_a", description: "Opção A" },
      { name: "option_b", description: "Opção B" },
      { name: "hashtags", description: "Hashtags" },
    ],
    hashtags: ["#enquete", "#ajuda", "#opiniao"],
    bestTimes: ["12:00", "19:00"],
    engagement: "Muito Alto - interatividade aumenta alcance",
  },
  {
    id: "tiktok_hook",
    name: "TikTok Hook Viral",
    description: "Gancho para início de vídeo TikTok",
    icon: <Play className="h-5 w-5 text-pink-500" />,
    platform: "tiktok",
    category: "promo",
    captionTemplate: `{{hook_line}}

{{product_description}}

🔗 Link na bio pra garantir o seu!

{{hashtags}}`,
    variables: [
      { name: "hook_line", description: "Linha de abertura impactante" },
      { name: "product_description", description: "Descrição curta do produto" },
      { name: "hashtags", description: "Hashtags TikTok" },
    ],
    hashtags: ["#tiktokshop", "#viral", "#achados", "#compras"],
    bestTimes: ["11:00", "17:00", "22:00"],
    engagement: "Viral potential - hooks fortes = mais FYP",
  },
];

// =============================================================================
// AUTOMATION WORKFLOWS DATA
// =============================================================================

const AUTOMATION_WORKFLOWS: AutomationWorkflow[] = [
  {
    id: "welcome_sequence",
    name: "Sequência de Boas-Vindas",
    description: "Envia mensagens automáticas para novos leads",
    icon: <Users className="h-5 w-5 text-green-500" />,
    category: "marketing",
    trigger: "Webhook (novo lead)",
    difficulty: "beginner",
    estimatedTime: "10 min",
    integrations: ["WhatsApp", "Evolution API"],
  },
  {
    id: "price_alert",
    name: "Alertas de Queda de Preço",
    description: "Notifica clientes quando produtos baixam de preço",
    icon: <Bell className="h-5 w-5 text-yellow-500" />,
    category: "alerts",
    trigger: "Evento (preço alterado)",
    difficulty: "intermediate",
    estimatedTime: "15 min",
    integrations: ["WhatsApp", "Email"],
  },
  {
    id: "cart_recovery",
    name: "Recuperação de Carrinho",
    description: "Recupera carrinhos abandonados automaticamente",
    icon: <ShoppingCart className="h-5 w-5 text-orange-500" />,
    category: "vendas",
    trigger: "Evento (carrinho abandonado)",
    difficulty: "intermediate",
    estimatedTime: "20 min",
    integrations: ["WhatsApp", "CRM"],
  },
  {
    id: "lead_qualification",
    name: "Qualificação de Leads",
    description: "Qualifica leads automaticamente com BANT",
    icon: <Target className="h-5 w-5 text-blue-500" />,
    category: "vendas",
    trigger: "Webhook (novo lead)",
    difficulty: "advanced",
    estimatedTime: "30 min",
    integrations: ["Typebot", "CRM", "WhatsApp"],
  },
  {
    id: "daily_deals_auto",
    name: "Compilação Diária de Ofertas",
    description: "Gera e envia ofertas do dia automaticamente",
    icon: <Calendar className="h-5 w-5 text-purple-500" />,
    category: "conteudo",
    trigger: "Agendado (diário)",
    difficulty: "intermediate",
    estimatedTime: "25 min",
    integrations: ["WhatsApp", "Instagram"],
  },
  {
    id: "competitor_monitor",
    name: "Monitor de Concorrência",
    description: "Monitora preços da concorrência",
    icon: <BarChart3 className="h-5 w-5 text-red-500" />,
    category: "monitoramento",
    trigger: "Agendado (a cada 6h)",
    difficulty: "advanced",
    estimatedTime: "45 min",
    integrations: ["Scraper", "Slack/Discord"],
  },
  {
    id: "content_reminder",
    name: "Lembretes de Conteúdo",
    description: "Lembretes para calendário de conteúdo",
    icon: <FileText className="h-5 w-5 text-cyan-500" />,
    category: "conteudo",
    trigger: "Agendado",
    difficulty: "beginner",
    estimatedTime: "10 min",
    integrations: ["WhatsApp", "Calendar"],
  },
  {
    id: "review_request",
    name: "Solicitação de Reviews",
    description: "Pede reviews após compra concluída",
    icon: <Award className="h-5 w-5 text-amber-500" />,
    category: "customer_success",
    trigger: "Evento (pedido entregue)",
    difficulty: "beginner",
    estimatedTime: "15 min",
    integrations: ["WhatsApp", "Email"],
  },
  {
    id: "daily_report",
    name: "Relatório Diário",
    description: "Gera e envia relatório de métricas",
    icon: <ChartIcon size={20} className="text-indigo-500" />,
    category: "analytics",
    trigger: "Agendado (diário 8h)",
    difficulty: "intermediate",
    estimatedTime: "20 min",
    integrations: ["Database", "Email/Slack"],
  },
];

// =============================================================================
// CHATBOT TEMPLATES DATA
// =============================================================================

const CHATBOT_TEMPLATES = [
  {
    id: "customer_service",
    name: "Atendimento Completo",
    description: "Menu interativo com todas as opções de atendimento",
    icon: <MessageSquare className="h-5 w-5 text-blue-500" />,
    category: "atendimento",
    features: ["Menu principal", "FAQ", "Suporte humano", "Histórico"],
  },
  {
    id: "sales_funnel",
    name: "Funil de Vendas",
    description: "Qualifica e converte leads em clientes",
    icon: <Target className="h-5 w-5 text-green-500" />,
    category: "vendas",
    features: ["Qualificação", "Apresentação", "Objeções", "Fechamento"],
  },
  {
    id: "lead_qualification_bot",
    name: "BANT Scoring",
    description: "Qualificação de leads com pontuação automática",
    icon: <BarChart3 className="h-5 w-5 text-purple-500" />,
    category: "qualificacao",
    features: ["Budget", "Authority", "Need", "Timeline"],
  },
  {
    id: "appointment_booking",
    name: "Agendamento de Consultas",
    description: "Agenda reuniões e consultas automaticamente",
    icon: <Calendar className="h-5 w-5 text-orange-500" />,
    category: "agendamento",
    features: ["Disponibilidade", "Confirmação", "Lembretes", "Reagendamento"],
  },
  {
    id: "faq_bot",
    name: "Perguntas Frequentes",
    description: "Responde dúvidas comuns instantaneamente",
    icon: <Lightbulb className="h-5 w-5 text-yellow-500" />,
    category: "faq",
    features: ["Busca inteligente", "Categorias", "Escalação"],
  },
  {
    id: "support_ticket",
    name: "Criação de Tickets",
    description: "Cria tickets de suporte estruturados",
    icon: <FileText className="h-5 w-5 text-red-500" />,
    category: "suporte",
    features: ["Coleta de dados", "Priorização", "Notificação", "Tracking"],
  },
];

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

const DifficultyBadge: React.FC<{ difficulty: string }> = ({ difficulty }) => {
  const colors = {
    beginner: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    intermediate: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
    advanced: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  };
  const labels = {
    beginner: "Iniciante",
    intermediate: "Intermediário",
    advanced: "Avançado",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[difficulty as keyof typeof colors]}`}>
      {labels[difficulty as keyof typeof labels]}
    </span>
  );
};

const PlatformBadge: React.FC<{ platform: string }> = ({ platform }) => {
  const icons: Record<string, React.ReactNode> = {
    instagram: <Instagram className="h-3 w-3" />,
    tiktok: <Play className="h-3 w-3" />,
    youtube: <Youtube className="h-3 w-3" />,
    whatsapp: <Phone className="h-3 w-3" />,
    all: <Layers className="h-3 w-3" />,
  };
  return (
    <Badge variant="outline" className="gap-1 text-xs">
      {icons[platform] || <Layers className="h-3 w-3" />}
      {platform === "all" ? "Multi-plataforma" : platform.charAt(0).toUpperCase() + platform.slice(1)}
    </Badge>
  );
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export const Copy: React.FC = () => {
  const { t } = useTranslation();
  const { toast } = useToast();
  
  // State
  const [activeTab, setActiveTab] = React.useState("generate");
  const [favorites, setFavorites] = React.useState<FavoriteWithProduct[]>([]);
  const [copyHistory, setCopyHistory] = React.useState<CopyHistory[]>([]);
  const [isLoadingFavorites, setIsLoadingFavorites] = React.useState(true);
  const [isLoadingHistory, setIsLoadingHistory] = React.useState(true);
  const [selectedTemplate, setSelectedTemplate] = React.useState<ContentTemplate | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = React.useState<AutomationWorkflow | null>(null);
  const [templateSearch, setTemplateSearch] = React.useState("");
  const [workflowCategory, setWorkflowCategory] = React.useState<string>("all");
  
  const [state, setState] = React.useState<CopyFormState>({
    selectedProductId: null,
    copyType: "tiktok_hook",
    tone: "urgent",
    generatedCopy: null,
    isGenerating: false,
    selectedPlatform: null,
    selectedType: null,
  });

  // Load data on mount
  React.useEffect(() => {
    const loadFavorites = async () => {
      setIsLoadingFavorites(true);
      try {
        const data = await getFavorites();
        setFavorites(data);
      } catch (err) {
        console.error("Error loading favorites:", err);
      } finally {
        setIsLoadingFavorites(false);
      }
    };
    loadFavorites();
  }, []);

  React.useEffect(() => {
    const loadHistory = async () => {
      setIsLoadingHistory(true);
      try {
        const data = await getCopyHistory(20);
        setCopyHistory(data);
      } catch (err) {
        console.error("Error loading copy history:", err);
      } finally {
        setIsLoadingHistory(false);
      }
    };
    loadHistory();
  }, []);

  // Handlers
  const handleGenerate = async () => {
    if (!state.selectedProductId) {
      toast({
        title: "Selecione um produto",
        description: "Você precisa escolher um produto dos favoritos para gerar a copy.",
        variant: "destructive",
      });
      return;
    }

    const selectedFavorite = favorites.find(f => f.product.id === state.selectedProductId);
    if (!selectedFavorite) {
      toast({
        title: "Produto não encontrado",
        description: "O produto selecionado não está mais disponível nos favoritos.",
        variant: "destructive",
      });
      return;
    }

    setState((prev) => ({ ...prev, isGenerating: true }));
    
    try {
      analytics.track('copy_generated', {
        productId: state.selectedProductId,
        copyType: state.copyType,
        tone: state.tone
      });

      const response = await generateCopy({
        productId: state.selectedProductId,
        productTitle: selectedFavorite.product.title,
        productDescription: selectedFavorite.product.description || "",
        productPrice: selectedFavorite.product.price,
        copyType: state.copyType,
        tone: state.tone,
        platform: "instagram", // Default to instagram, or derive from copyType
        language: "pt-BR"
      });
      
      setState((prev) => ({ 
        ...prev, 
        generatedCopy: response.copyText,
        isGenerating: false 
      }));

      toast({
        title: "✨ Copy gerada!",
        description: "Sua copy está pronta. Copie e use nas suas campanhas!",
      });
      
      const history = await getCopyHistory();
      setCopyHistory(history);
    } catch (error) {
      console.error("Error generating copy:", error);
      setState((prev) => ({ ...prev, isGenerating: false }));

      const errorStr = String(error).toLowerCase();
      
      if (errorStr.includes("quota_exceeded") || errorStr.includes("quota")) {
        toast({
          title: "Limite de cota atingido",
          description: "Você atingiu o limite de gerações do seu plano. Aguarde o próximo ciclo ou faça upgrade.",
          variant: "destructive",
        });
      } else if (errorStr.includes("network") || errorStr.includes("fetch") || errorStr.includes("connection")) {
        toast({
          title: "Erro de conexão",
          description: "Verifique sua conexão com a internet e tente novamente.",
          variant: "destructive",
        });
      } else if (errorStr.includes("timeout")) {
        toast({
          title: "Tempo esgotado",
          description: "A geração demorou muito. Tente novamente em alguns segundos.",
          variant: "destructive",
        });
      } else if (errorStr.includes("unauthorized") || errorStr.includes("401")) {
        toast({
          title: "Não autorizado",
          description: "Sua sessão expirou. Por favor, faça login novamente.",
          variant: "destructive",
        });
      } else if (errorStr.includes("openai") || errorStr.includes("api_key")) {
        toast({
          title: "Erro de configuração",
          description: "A chave da OpenAI não está configurada. Vá em Configurações > Credenciais.",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Erro ao gerar copy",
          description: "Ocorreu um erro inesperado. Tente novamente ou contate o suporte.",
          variant: "destructive",
        });
      }
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copiado!",
      description: "Texto copiado para a área de transferência.",
    });
  };

  const handleUseTemplate = (template: ContentTemplate) => {
    setState(prev => ({
      ...prev,
      generatedCopy: template.captionTemplate,
    }));
    setSelectedTemplate(null);
    setActiveTab("generate");
    toast({
      title: "Template carregado!",
      description: "Edite as variáveis {{...}} com seus dados.",
    });
  };

  // Action handlers for next steps
  const navigate = useNavigate();
  
  const handleSchedulePost = () => {
    if (!state.generatedCopy) return;
    // Navegar para o agendador passando os dados da copy
    navigate('/scheduler', { 
      state: { 
        copy: state.generatedCopy,
        platform: state.selectedPlatform,
        copyType: state.selectedType,
      } 
    });
    toast({
      title: "📅 Redirecionando!",
      description: "Configure o agendamento da sua publicação.",
    });
  };

  const handleSendWhatsApp = () => {
    if (!state.generatedCopy) return;
    const encodedText = encodeURIComponent(state.generatedCopy);
    window.open(`https://wa.me/?text=${encodedText}`, '_blank');
    toast({
      title: "WhatsApp aberto!",
      description: "Cole o texto na conversa desejada.",
    });
  };

  const handleCreateAutomation = () => {
    setActiveTab("automation");
    toast({
      title: "⚡ Automações",
      description: "Escolha um workflow para automatizar.",
    });
  };

  const handleSaveAsTemplate = async () => {
    if (!state.generatedCopy) return;
    
    try {
      // Extrair variáveis do template (padrão {{variavel}})
      const variableMatches = state.generatedCopy.match(/\{\{([^}]+)\}\}/g) || [];
      const variables = variableMatches.map(v => v.replace(/[{}]/g, '').trim());
      
      await api.post('/templates', {
        name: `Copy ${state.selectedType} - ${new Date().toLocaleDateString('pt-BR')}`,
        description: `Template gerado automaticamente de ${state.selectedType}`,
        platform: state.selectedPlatform || 'all',
        category: state.selectedType || 'custom',
        caption_template: state.generatedCopy,
        hashtags: [],
        variables: variables,
        is_public: false,
      });
      
      toast({
        title: "💾 Template salvo!",
        description: "Disponível na aba Templates.",
      });
    } catch (error) {
      console.error("Error saving template:", error);
      toast({
        title: "Erro ao salvar",
        description: "Não foi possível salvar o template. Tente novamente.",
        variant: "destructive",
      });
    }
  };

  const handleExportN8n = async (workflow: AutomationWorkflow) => {
    toast({
      title: "📥 Exportando...",
      description: `Workflow "${workflow.name}" será baixado como JSON.`,
    });
    
    try {
      // Determinar tipo de trigger baseado na string
      const isSchedule = workflow.trigger.toLowerCase().includes("agendado");
      
      // Criar estrutura de workflow n8n compatível
      const n8nWorkflow = {
        name: workflow.name,
        nodes: [
          {
            id: "trigger",
            name: "Trigger",
            type: isSchedule ? "n8n-nodes-base.cron" : "n8n-nodes-base.webhook",
            position: [250, 300],
            parameters: isSchedule 
              ? { cronExpression: "0 9 * * *" }
              : { httpMethod: "POST", path: `/didin/${workflow.id}` },
          },
          ...(workflow.steps || []).map((step, index) => ({
            id: `step_${index}`,
            name: step.name,
            type: step.type === "api_call" 
              ? "n8n-nodes-base.httpRequest"
              : step.type === "openai"
              ? "n8n-nodes-base.openAi"
              : "n8n-nodes-base.set",
            position: [450 + (index * 200), 300],
            parameters: step.config || {},
          })),
        ],
        connections: (workflow.steps || []).reduce((acc: Record<string, unknown>, _, index: number) => {
          const fromNode = index === 0 ? "trigger" : `step_${index - 1}`;
          acc[fromNode] = { main: [[{ node: `step_${index}`, type: "main", index: 0 }]] };
          return acc;
        }, {} as Record<string, unknown>),
        settings: { executionOrder: "v1" },
      };
      
      // Criar e baixar arquivo
      const blob = new Blob([JSON.stringify(n8nWorkflow, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `workflow_${workflow.id}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast({
        title: "✅ Pronto!",
        description: "Importe o arquivo no seu n8n.",
      });
    } catch (error) {
      console.error("Error exporting workflow:", error);
      toast({
        title: "Erro na exportação",
        description: "Não foi possível exportar o workflow.",
        variant: "destructive",
      });
    }
  };

  const handleOpenDocs = (workflow: AutomationWorkflow) => {
    window.open(`/docs/automation/${workflow.id}`, '_blank');
    toast({
      title: "📚 Documentação",
      description: "Abrindo guia de configuração...",
    });
  };

  // Filtered data
  const filteredTemplates = CONTENT_TEMPLATES.filter(t =>
    t.name.toLowerCase().includes(templateSearch.toLowerCase()) ||
    t.description.toLowerCase().includes(templateSearch.toLowerCase())
  );

  const filteredWorkflows = workflowCategory === "all"
    ? AUTOMATION_WORKFLOWS
    : AUTOMATION_WORKFLOWS.filter(w => w.category === workflowCategory);

  // Onboarding state
  const [showOnboarding, setShowOnboarding] = React.useState(() => {
    return localStorage.getItem('copy_ai_onboarding_complete') !== 'true';
  });

  const completeOnboarding = () => {
    localStorage.setItem('copy_ai_onboarding_complete', 'true');
    setShowOnboarding(false);
  };

  // ==========================================================================
  // RENDER
  // ==========================================================================

  return (
    <div className="space-y-6">
      {/* Onboarding Banner */}
      {showOnboarding && (
        <Card className="border-tiktrend-primary/30 bg-gradient-to-r from-tiktrend-primary/5 to-tiktrend-secondary/5">
          <CardContent className="p-5">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-tiktrend-primary to-tiktrend-secondary flex items-center justify-center flex-shrink-0">
                <Lightbulb className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-lg mb-2">🚀 Bem-vindo ao Copy AI!</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Gere textos persuasivos para seus produtos em segundos. Siga estes passos:
                </p>
                <div className="grid gap-3 sm:grid-cols-3 mb-4">
                  <div className="flex items-start gap-2 p-3 bg-background/60 rounded-lg">
                    <div className="w-6 h-6 rounded-full bg-tiktrend-primary/20 flex items-center justify-center text-xs font-bold text-tiktrend-primary flex-shrink-0">
                      1
                    </div>
                    <div>
                      <p className="font-medium text-sm">Adicione Favoritos</p>
                      <p className="text-xs text-muted-foreground">
                        Vá em Produtos e salve itens nos favoritos
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2 p-3 bg-background/60 rounded-lg">
                    <div className="w-6 h-6 rounded-full bg-tiktrend-primary/20 flex items-center justify-center text-xs font-bold text-tiktrend-primary flex-shrink-0">
                      2
                    </div>
                    <div>
                      <p className="font-medium text-sm">Escolha o Formato</p>
                      <p className="text-xs text-muted-foreground">
                        TikTok, Instagram, WhatsApp...
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2 p-3 bg-background/60 rounded-lg">
                    <div className="w-6 h-6 rounded-full bg-tiktrend-primary/20 flex items-center justify-center text-xs font-bold text-tiktrend-primary flex-shrink-0">
                      3
                    </div>
                    <div>
                      <p className="font-medium text-sm">Gere e Copie!</p>
                      <p className="text-xs text-muted-foreground">
                        IA cria o texto pronto para usar
                      </p>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Button 
                    variant="tiktrend" 
                    size="sm"
                    onClick={completeOnboarding}
                  >
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Entendi, começar!
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={completeOnboarding}
                  >
                    Não mostrar novamente
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Header */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-tiktrend-primary to-tiktrend-secondary flex items-center justify-center">
              <Wand2 className="h-5 w-5 text-white" />
            </div>
            {t("copy_ai.title")}
          </h1>
          {!showOnboarding && (
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => setShowOnboarding(true)}
              className="text-xs text-muted-foreground"
            >
              <Lightbulb className="h-4 w-4 mr-1" />
              Ver tutorial
            </Button>
          )}
        </div>
        <p className="text-muted-foreground">
          {t("copy_ai.subtitle")}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-tiktrend-primary/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Templates</p>
                <p className="text-2xl font-bold">{CONTENT_TEMPLATES.length}</p>
              </div>
              <div className="p-2 bg-tiktrend-primary/10 rounded-lg">
                <Image className="h-5 w-5 text-tiktrend-primary" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-blue-500/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Automações</p>
                <p className="text-2xl font-bold">{AUTOMATION_WORKFLOWS.length}</p>
              </div>
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Zap className="h-5 w-5 text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-green-500/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Chatbots</p>
                <p className="text-2xl font-bold">{CHATBOT_TEMPLATES.length}</p>
              </div>
              <div className="p-2 bg-green-500/10 rounded-lg">
                <MessageSquare className="h-5 w-5 text-green-500" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-purple-500/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Copies Geradas</p>
                <p className="text-2xl font-bold">{copyHistory.length}</p>
              </div>
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <History className="h-5 w-5 text-purple-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid grid-cols-4 w-full max-w-2xl">
          <TabsTrigger value="generate" className="gap-2">
            <Wand2 className="h-4 w-4" />
            <span className="hidden sm:inline">Gerar Copy</span>
          </TabsTrigger>
          <TabsTrigger value="templates" className="gap-2">
            <Palette className="h-4 w-4" />
            <span className="hidden sm:inline">Templates</span>
          </TabsTrigger>
          <TabsTrigger value="automation" className="gap-2">
            <Zap className="h-4 w-4" />
            <span className="hidden sm:inline">Automação</span>
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <History className="h-4 w-4" />
            <span className="hidden sm:inline">Histórico</span>
          </TabsTrigger>
        </TabsList>

        {/* ================================================================== */}
        {/* TAB: GERAR COPY */}
        {/* ================================================================== */}
        <TabsContent value="generate" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Form */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <SparkleIcon size={20} className="text-tiktrend-primary" />
                  {t("copy_ai.create_new")}
                </CardTitle>
                <CardDescription>
                  {t("copy_ai.select_product_desc")}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Product Selection */}
                <div className="space-y-2">
                  <SettingLabel 
                    label={t("copy_ai.select_product")}
                    tooltip="Selecione um produto dos favoritos para gerar copy personalizada"
                  />
                  {isLoadingFavorites ? (
                    <div className="space-y-2">
                      <Skeleton className="h-12 w-full" />
                      <Skeleton className="h-12 w-full" />
                    </div>
                  ) : favorites.length > 0 ? (
                    <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto">
                      {favorites.map((fav) => (
                        <div
                          key={fav.product.id}
                          onClick={() => setState((prev) => ({ ...prev, selectedProductId: fav.product.id }))}
                          className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-all ${
                            state.selectedProductId === fav.product.id
                              ? "bg-tiktrend-primary/10 border-2 border-tiktrend-primary ring-2 ring-tiktrend-primary/20"
                              : "hover:bg-accent border-2 border-transparent"
                          }`}
                        >
                          <img
                            src={fav.product.imageUrl || "https://placehold.co/50x50"}
                            alt={fav.product.title}
                            className="w-10 h-10 rounded object-cover"
                          />
                          <div className="flex-1 min-w-0">
                            <span className="text-sm line-clamp-1">{fav.product.title}</span>
                            <span className="text-xs text-muted-foreground">{formatCurrency(fav.product.price)}</span>
                          </div>
                          {state.selectedProductId === fav.product.id && (
                            <CheckCircle2 className="h-5 w-5 text-tiktrend-primary" />
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground p-4 text-center border rounded-lg bg-muted/30">
                      <StarIcon size={24} className="mx-auto mb-2 text-muted-foreground/50" />
                      {t("copy_ai.add_favorites_hint")}
                    </div>
                  )}
                </div>

                {/* Copy Type */}
                <div className="space-y-2">
                  <SettingLabel 
                    label={t("copy_ai.copy_type")}
                    tooltip="Escolha o formato de texto mais adequado para seu canal de comunicação"
                  />
                  <div className="grid grid-cols-2 gap-2">
                    {COPY_TYPES.map((type) => (
                      <div
                        key={type.id}
                        onClick={() => setState((prev) => ({ ...prev, copyType: type.id as CopyType }))}
                        className={`flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-all ${
                          state.copyType === type.id
                            ? "bg-tiktrend-primary/10 border-2 border-tiktrend-primary"
                            : "hover:bg-accent border-2 border-muted"
                        }`}
                      >
                        <span className="text-lg">{type.icon}</span>
                        <span className="text-sm">{type.name}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Tone */}
                <div className="space-y-2">
                  <SettingLabel 
                    label={t("copy_ai.tone")}
                    tooltip="O tom de voz define a personalidade do texto gerado"
                  />
                  <div className="flex flex-wrap gap-2">
                    {COPY_TONES.map((tone) => (
                      <Badge
                        key={tone.id}
                        variant={state.tone === tone.id ? "tiktrend" : "outline"}
                        className="cursor-pointer py-2 px-4 transition-all hover:scale-105"
                        onClick={() => setState((prev) => ({ ...prev, tone: tone.id as CopyTone }))}
                      >
                        {tone.icon} {tone.name}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Generate Button */}
                <Button
                  variant="tiktrend"
                  size="lg"
                  className="w-full gap-2 shadow-lg shadow-tiktrend-primary/25"
                  onClick={handleGenerate}
                  disabled={!state.selectedProductId || state.isGenerating}
                >
                  <SparkleIcon size={18} className={state.isGenerating ? "animate-spin" : ""} />
                  {state.isGenerating ? t("copy_ai.generating") : t("copy_ai.generate")}
                </Button>

                {/* Quick Actions */}
                <div className="pt-4 border-t">
                  <p className="text-xs text-muted-foreground mb-2">⚡ Ações rápidas</p>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      onClick={() => setActiveTab("templates")}
                    >
                      <Palette className="h-4 w-4 mr-1" />
                      Usar Template
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      onClick={() => setActiveTab("automation")}
                    >
                      <Zap className="h-4 w-4 mr-1" />
                      Automatizar
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Result */}
            <Card className="overflow-hidden">
              <CardHeader className="border-b bg-gradient-to-r from-muted/50 to-muted/30">
                <CardTitle className="flex items-center gap-2">
                  <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-tiktrend-primary to-tiktrend-secondary flex items-center justify-center text-white text-sm">
                    ✨
                  </span>
                  {t("copy_ai.generated_copy")}
                </CardTitle>
                <CardDescription>
                  {t("copy_ai.copy_and_use")}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {state.isGenerating ? (
                  <div className="space-y-4 animate-pulse">
                    <div className="flex items-center gap-3 mb-4">
                      <Skeleton className="w-10 h-10 rounded-full" />
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-3 w-16" />
                      </div>
                    </div>
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-32 w-full rounded-xl" />
                  </div>
                ) : state.generatedCopy ? (
                  <div className="space-y-4">
                    {/* Post preview */}
                    <div className="copy-preview rounded-xl p-5 bg-gradient-to-br from-gray-900 to-gray-800 text-white relative overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-r from-tiktrend-primary/10 to-tiktrend-secondary/10" />
                      <div className="relative">
                        <div className="flex items-center gap-3 mb-4 pb-4 border-b border-white/10">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary flex items-center justify-center text-sm font-bold">
                            🏪
                          </div>
                          <div>
                            <p className="font-semibold text-sm">@sua_loja</p>
                            <p className="text-xs text-white/50">Agora</p>
                          </div>
                        </div>
                        <div className="whitespace-pre-wrap text-sm leading-relaxed max-h-[250px] overflow-y-auto scrollbar-thin">
                          {state.generatedCopy}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="tiktrend"
                        className="gap-2 flex-1 shadow-lg"
                        onClick={() => copyToClipboard(state.generatedCopy!)}
                      >
                        <CopyIcon size={16} />
                        Copiar Texto
                      </Button>
                      <Button variant="outline" className="gap-2" onClick={handleGenerate}>
                        <RefreshCw size={16} />
                        Regenerar
                      </Button>
                    </div>
                    
                    {/* Next Steps */}
                    <div className="pt-4 border-t">
                      <p className="text-xs font-medium mb-2">🚀 Próximos passos</p>
                      <div className="grid grid-cols-2 gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="justify-start text-xs h-auto py-2"
                          onClick={handleSchedulePost}
                        >
                          <Send className="h-3 w-3 mr-2" />
                          Agendar post
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="justify-start text-xs h-auto py-2"
                          onClick={handleCreateAutomation}
                        >
                          <Zap className="h-3 w-3 mr-2" />
                          Criar automação
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="justify-start text-xs h-auto py-2"
                          onClick={handleSendWhatsApp}
                        >
                          <MessageSquare className="h-3 w-3 mr-2" />
                          Enviar WhatsApp
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="justify-start text-xs h-auto py-2"
                          onClick={handleSaveAsTemplate}
                        >
                          <StarIcon size={12} className="mr-2" />
                          Salvar template
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="min-h-[300px] flex items-center justify-center text-center">
                    <div className="empty-state">
                      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-tiktrend-primary/10 to-tiktrend-secondary/10 flex items-center justify-center mb-6 mx-auto animate-float">
                        <SparkleIcon size={32} className="text-tiktrend-primary/50" />
                      </div>
                      <h3 className="font-semibold mb-2">Pronto para criar</h3>
                      <p className="text-muted-foreground text-sm mb-4">
                        Selecione um produto e clique em "Gerar Copy"
                      </p>
                      <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                        <Lightbulb className="h-3 w-3" />
                        Dica: Use templates para começar mais rápido
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ================================================================== */}
        {/* TAB: TEMPLATES */}
        {/* ================================================================== */}
        <TabsContent value="templates" className="space-y-6">
          {/* Search */}
          <div className="flex gap-4">
            <div className="relative flex-1">
              <SearchIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Buscar templates..."
                value={templateSearch}
                onChange={(e) => setTemplateSearch(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Template Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredTemplates.map((template) => (
              <Card 
                key={template.id} 
                className="group hover:border-tiktrend-primary/50 hover:shadow-lg transition-all cursor-pointer"
                onClick={() => setSelectedTemplate(template)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-muted">
                        {template.icon}
                      </div>
                      <div>
                        <CardTitle className="text-base">{template.name}</CardTitle>
                        <PlatformBadge platform={template.platform} />
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-3">{template.description}</p>
                  <div className="flex items-center justify-between">
                    <div className="flex gap-1">
                      {template.hashtags.slice(0, 2).map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-tiktrend-primary transition-colors" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Template Dialog */}
          <Dialog open={!!selectedTemplate} onOpenChange={() => setSelectedTemplate(null)}>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
              {selectedTemplate && (
                <>
                  <DialogHeader>
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-lg bg-muted">
                        {selectedTemplate.icon}
                      </div>
                      <div>
                        <DialogTitle>{selectedTemplate.name}</DialogTitle>
                        <DialogDescription>{selectedTemplate.description}</DialogDescription>
                      </div>
                    </div>
                  </DialogHeader>
                  
                  <div className="space-y-4 mt-4">
                    {/* Template Preview */}
                    <div>
                      <h4 className="font-medium mb-2">📝 Template</h4>
                      <div className="p-4 bg-muted/50 rounded-lg font-mono text-sm whitespace-pre-wrap">
                        {selectedTemplate.captionTemplate}
                      </div>
                    </div>

                    {/* Variables */}
                    <div>
                      <h4 className="font-medium mb-2">🔧 Variáveis</h4>
                      <div className="grid grid-cols-2 gap-2">
                        {selectedTemplate.variables.map((v) => (
                          <div key={v.name} className="p-2 bg-muted/30 rounded text-sm">
                            <code className="text-tiktrend-primary">{`{{${v.name}}}`}</code>
                            <p className="text-xs text-muted-foreground">{v.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Best Times & Engagement */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium mb-2">⏰ Melhores horários</h4>
                        <div className="flex gap-2">
                          {selectedTemplate.bestTimes.map((time) => (
                            <Badge key={time} variant="outline">{time}</Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-medium mb-2">📊 Engajamento esperado</h4>
                        <p className="text-sm text-muted-foreground">{selectedTemplate.engagement}</p>
                      </div>
                    </div>

                    {/* Hashtags */}
                    <div>
                      <h4 className="font-medium mb-2">🏷️ Hashtags recomendadas</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedTemplate.hashtags.map((tag) => (
                          <Badge key={tag} variant="secondary">{tag}</Badge>
                        ))}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-4 border-t">
                      <Button 
                        variant="tiktrend" 
                        className="flex-1"
                        onClick={() => handleUseTemplate(selectedTemplate)}
                      >
                        <Wand2 className="h-4 w-4 mr-2" />
                        Usar Template
                      </Button>
                      <Button 
                        variant="outline"
                        onClick={() => copyToClipboard(selectedTemplate.captionTemplate)}
                      >
                        <CopyIcon size={16} className="mr-2" />
                        Copiar
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </DialogContent>
          </Dialog>
        </TabsContent>

        {/* ================================================================== */}
        {/* TAB: AUTOMATION */}
        {/* ================================================================== */}
        <TabsContent value="automation" className="space-y-6">
          {/* Categories */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant={workflowCategory === "all" ? "tiktrend" : "outline"}
              size="sm"
              onClick={() => setWorkflowCategory("all")}
            >
              Todos
            </Button>
            {["marketing", "vendas", "alerts", "conteudo", "customer_success", "analytics"].map((cat) => (
              <Button
                key={cat}
                variant={workflowCategory === cat ? "tiktrend" : "outline"}
                size="sm"
                onClick={() => setWorkflowCategory(cat)}
              >
                {cat.charAt(0).toUpperCase() + cat.slice(1).replace("_", " ")}
              </Button>
            ))}
          </div>

          {/* Workflows Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredWorkflows.map((workflow) => (
              <Card 
                key={workflow.id}
                className="group hover:border-blue-500/50 hover:shadow-lg transition-all cursor-pointer"
                onClick={() => setSelectedWorkflow(workflow)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                        {workflow.icon}
                      </div>
                      <div>
                        <CardTitle className="text-base">{workflow.name}</CardTitle>
                        <DifficultyBadge difficulty={workflow.difficulty} />
                      </div>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {workflow.estimatedTime}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-3">{workflow.description}</p>
                  <div className="flex items-center justify-between">
                    <div className="flex gap-1">
                      {workflow.integrations.slice(0, 2).map((int) => (
                        <Badge key={int} variant="outline" className="text-xs">
                          {int}
                        </Badge>
                      ))}
                      {workflow.integrations.length > 2 && (
                        <Badge variant="outline" className="text-xs">
                          +{workflow.integrations.length - 2}
                        </Badge>
                      )}
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-blue-500 transition-colors" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Chatbot Templates */}
          <div className="pt-6 border-t">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-green-500" />
              Templates de Chatbot (Typebot)
            </h3>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {CHATBOT_TEMPLATES.map((bot) => (
                <Card key={bot.id} className="hover:border-green-500/50 transition-all">
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-green-50 dark:bg-green-900/20">
                        {bot.icon}
                      </div>
                      <div>
                        <CardTitle className="text-base">{bot.name}</CardTitle>
                        <Badge variant="outline" className="text-xs">{bot.category}</Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-3">{bot.description}</p>
                    <div className="flex flex-wrap gap-1">
                      {bot.features.map((f) => (
                        <Badge key={f} variant="secondary" className="text-xs">{f}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Workflow Dialog */}
          <Dialog open={!!selectedWorkflow} onOpenChange={() => setSelectedWorkflow(null)}>
            <DialogContent className="max-w-lg">
              {selectedWorkflow && (
                <>
                  <DialogHeader>
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                        {selectedWorkflow.icon}
                      </div>
                      <div>
                        <DialogTitle>{selectedWorkflow.name}</DialogTitle>
                        <DialogDescription>{selectedWorkflow.description}</DialogDescription>
                      </div>
                    </div>
                  </DialogHeader>
                  
                  <div className="space-y-4 mt-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-muted/30 rounded-lg">
                        <p className="text-xs text-muted-foreground">Dificuldade</p>
                        <DifficultyBadge difficulty={selectedWorkflow.difficulty} />
                      </div>
                      <div className="p-3 bg-muted/30 rounded-lg">
                        <p className="text-xs text-muted-foreground">Tempo estimado</p>
                        <p className="font-medium">{selectedWorkflow.estimatedTime}</p>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">🔌 Integrações necessárias</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedWorkflow.integrations.map((int) => (
                          <Badge key={int} variant="outline">{int}</Badge>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">⚡ Gatilho</h4>
                      <p className="text-sm text-muted-foreground">{selectedWorkflow.trigger}</p>
                    </div>

                    <div className="flex gap-2 pt-4 border-t">
                      <Button 
                        variant="tiktrend" 
                        className="flex-1"
                        onClick={() => handleExportN8n(selectedWorkflow)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Exportar para n8n
                      </Button>
                      <Button 
                        variant="outline"
                        onClick={() => handleOpenDocs(selectedWorkflow)}
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Documentação
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </DialogContent>
          </Dialog>
        </TabsContent>

        {/* ================================================================== */}
        {/* TAB: HISTORY */}
        {/* ================================================================== */}
        <TabsContent value="history" className="space-y-6">
          <Card>
            <CardHeader className="border-b">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Histórico de Copies</CardTitle>
                  <CardDescription>
                    Suas copies geradas recentemente
                  </CardDescription>
                </div>
                {copyHistory.length > 0 && (
                  <Badge variant="secondary" className="font-mono">{copyHistory.length}</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              {isLoadingHistory ? (
                <div className="space-y-4">
                  <Skeleton className="h-24 w-full rounded-xl" />
                  <Skeleton className="h-24 w-full rounded-xl" />
                </div>
              ) : copyHistory.length > 0 ? (
                <div className="space-y-3">
                  {copyHistory.map((copy, index) => (
                    <div
                      key={copy.id}
                      className="p-4 border rounded-xl hover:bg-accent/50 hover:border-tiktrend-primary/30 transition-all cursor-pointer group animate-slide-up"
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">{copy.copyType}</Badge>
                          <Badge variant="secondary" className="text-xs">{copy.tone}</Badge>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(copy.createdAt).toLocaleDateString("pt-BR", { day: '2-digit', month: 'short' })}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                        {copy.copyText}
                      </p>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => copyToClipboard(copy.copyText)}
                        >
                          <CopyIcon size={12} className="mr-1" />
                          Copiar
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state py-12">
                  <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4 mx-auto">
                    <CopyIcon size={24} className="text-muted-foreground" />
                  </div>
                  <p className="text-muted-foreground">Nenhuma copy gerada ainda</p>
                  <p className="text-sm text-muted-foreground/60 mt-1">Suas copies aparecerão aqui</p>
                  <Button 
                    variant="outline" 
                    className="mt-4"
                    onClick={() => setActiveTab("generate")}
                  >
                    <Wand2 className="h-4 w-4 mr-2" />
                    Gerar primeira copy
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Copy;
