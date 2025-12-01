import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import type { Product } from "@/types";
import {
  Sparkles,
  Calendar,
  MessageCircle,
  Instagram,
  Youtube,
  Heart,
  Share2,
  ExternalLink,
  Copy,
  Download,
  Bot,
  ChevronRight,
  MoreHorizontal,
  ShoppingCart,
  Mail,
  Zap,
  Loader2,
  Check,
  Send,
} from "lucide-react";

// TikTok icon
const TikTokIcon = () => (
  <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current">
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
  </svg>
);

interface ProductActionsPanelProps {
  product: Product;
  isFavorite?: boolean;
  onFavorite?: (product: Product) => void;
  onClose?: () => void;
  variant?: "full" | "compact";
}

interface ActionItem {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  onClick: () => void;
  variant?: "default" | "primary" | "secondary";
  badge?: string;
  disabled?: boolean;
}

interface ActionGroup {
  title: string;
  actions: ActionItem[];
}

export const ProductActionsPanel: React.FC<ProductActionsPanelProps> = ({
  product,
  isFavorite = false,
  onFavorite,
  onClose,
  variant = "full",
}) => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = React.useState<string | null>(null);
  const [successAction, setSuccessAction] = React.useState<string | null>(null);
  
  // Modal states
  const [showCopyModal, setShowCopyModal] = React.useState(false);
  const [showWhatsAppModal, setShowWhatsAppModal] = React.useState(false);
  const [showScheduleModal, setShowScheduleModal] = React.useState(false);
  const [showInstagramModal, setShowInstagramModal] = React.useState(false);
  const [showTikTokModal, setShowTikTokModal] = React.useState(false);
  const [showYouTubeModal, setShowYouTubeModal] = React.useState(false);
  const [showSellerBotModal, setShowSellerBotModal] = React.useState(false);
  const [showCRMModal, setShowCRMModal] = React.useState(false);
  const [showEmailModal, setShowEmailModal] = React.useState(false);
  
  // Form states
  const [copyType, setCopyType] = React.useState("ad");
  const [copyTone, setCopyTone] = React.useState("professional");
  const [generatedCopy, setGeneratedCopy] = React.useState<string | null>(null);
  const [whatsAppMessage, setWhatsAppMessage] = React.useState("");
  const [whatsAppNumber, setWhatsAppNumber] = React.useState("");
  const [schedulePlatform, setSchedulePlatform] = React.useState("instagram");
  const [scheduleDate, setScheduleDate] = React.useState("");
  
  // Social media form states
  const [instagramCaption, setInstagramCaption] = React.useState("");
  const [instagramHashtags, setInstagramHashtags] = React.useState("");
  const [tiktokCaption, setTiktokCaption] = React.useState("");
  const [tiktokSounds, setTiktokSounds] = React.useState("");
  const [youtubeTitle, setYoutubeTitle] = React.useState("");
  const [youtubeDescription, setYoutubeDescription] = React.useState("");
  
  // Seller Bot form states
  const [botCampaignName, setBotCampaignName] = React.useState("");
  const [botMessage, setBotMessage] = React.useState("");
  const [botTargetAudience, setBotTargetAudience] = React.useState("all");
  const [botScheduleEnabled, setBotScheduleEnabled] = React.useState(false);
  
  // CRM form states
  const [crmOpportunityTitle, setCrmOpportunityTitle] = React.useState("");
  const [crmValue, setCrmValue] = React.useState(0);
  const [crmStage, setCrmStage] = React.useState("lead");
  const [crmNotes, setCrmNotes] = React.useState("");
  
  // Email form states
  const [emailSubject, setEmailSubject] = React.useState("");
  const [emailTemplate, setEmailTemplate] = React.useState("product_launch");
  const [emailContent, setEmailContent] = React.useState("");
  const [emailAudience, setEmailAudience] = React.useState("all");

  // Helper to show success animation
  const showSuccess = (actionId: string) => {
    setSuccessAction(actionId);
    setTimeout(() => setSuccessAction(null), 2000);
  };

  // ============================================
  // HANDLERS
  // ============================================

  const handleCopyInfo = async () => {
    const info = `🛍️ ${product.title}
💰 Preço: ${formatCurrency(product.price)}
📦 Vendas: ${product.salesCount.toLocaleString()}
⭐ Avaliação: ${product.productRating?.toFixed(1) || "N/A"}
🏪 Loja: ${product.sellerName || "TikTok Shop"}
${product.productUrl ? `🔗 Link: ${product.productUrl}` : ""}`;

    await navigator.clipboard.writeText(info);
    toast({ title: "Copiado!", description: "Informações do produto copiadas." });
    showSuccess("copy-info");
  };

  const handleCopyLink = async () => {
    if (product.productUrl) {
      await navigator.clipboard.writeText(product.productUrl);
      toast({ title: "Link copiado!" });
      showSuccess("copy-link");
    } else {
      toast({ title: "Link não disponível", variant: "destructive" });
    }
  };

  // Quick action: navigate to full copy page
  const handleGenerateCopyPage = () => {
    navigate(`/copy?productId=${product.id}&title=${encodeURIComponent(product.title)}&price=${product.price}`);
    onClose?.();
  };

  // Direct action: generate copy via API
  const handleGenerateCopyDirect = async () => {
    setIsLoading("generate-copy");
    setGeneratedCopy(null);
    try {
      const response = await api.post<{ copy_text: string; credits_remaining: number }>("/copy/generate", {
        product_id: product.id,
        product_title: product.title,
        product_price: product.price,
        product_description: product.description || "",
        copy_type: copyType,
        tone: copyTone,
        platform: "instagram",
        include_emoji: true,
        include_hashtags: true,
      });
      
      setGeneratedCopy(response.data.copy_text);
      toast({ 
        title: "Copy gerada com sucesso!",
        description: `Créditos restantes: ${response.data.credits_remaining}`
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao gerar copy";
      toast({ title: "Erro", description: message, variant: "destructive" });
    } finally {
      setIsLoading(null);
    }
  };

  const handleCopyGeneratedText = async () => {
    if (generatedCopy) {
      await navigator.clipboard.writeText(generatedCopy);
      toast({ title: "Copy copiada!" });
      showSuccess("generate-copy");
    }
  };

  // Quick schedule (opens modal)
  const handleQuickSchedule = () => {
    setShowScheduleModal(true);
  };

  // Submit schedule directly
  const handleSubmitSchedule = async () => {
    if (!scheduleDate) {
      toast({ title: "Selecione uma data", variant: "destructive" });
      return;
    }

    setIsLoading("schedule");
    try {
      await api.post("/scheduler/posts", {
        platform: schedulePlatform,
        scheduled_time: new Date(scheduleDate).toISOString(),
        content_type: "photo",
        caption: `🛍️ ${product.title}\n💰 ${formatCurrency(product.price)}`,
        hashtags: ["tiktrend", "dropshipping", "produto"],
        platform_config: {
          product_id: product.id,
          product_image: product.imageUrl,
        }
      });
      
      toast({ title: "Post agendado!", description: `Será publicado em ${schedulePlatform}` });
      showSuccess("schedule");
      setShowScheduleModal(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao agendar";
      toast({ title: "Erro", description: message, variant: "destructive" });
    } finally {
      setIsLoading(null);
    }
  };

  const handleSchedulePost = (platform: string) => {
    navigate(`/automation/scheduler?productId=${product.id}&platform=${platform}`);
    onClose?.();
  };

  // Navigate to WhatsApp page
  const handleWhatsAppPage = () => {
    navigate(`/whatsapp?action=send&productId=${product.id}`);
    onClose?.();
  };

  // Open quick WhatsApp modal
  const handleQuickWhatsApp = () => {
    // Pre-fill message with product info
    setWhatsAppMessage(`🛍️ *${product.title}*\n\n💰 Preço: ${formatCurrency(product.price)}\n📦 Vendas: ${product.salesCount.toLocaleString()}\n\n${product.productUrl || ""}`);
    setShowWhatsAppModal(true);
  };

  // Send via WhatsApp directly
  const handleSendWhatsApp = async () => {
    if (!whatsAppNumber || !whatsAppMessage) {
      toast({ title: "Preencha todos os campos", variant: "destructive" });
      return;
    }

    setIsLoading("whatsapp");
    try {
      // Get default instance
      const instancesResponse = await api.get<{ data: Array<{ name: string }> }>("/whatsapp/instances");
      const instances = instancesResponse.data.data || [];
      
      if (instances.length === 0) {
        toast({ 
          title: "Nenhuma instância configurada",
          description: "Configure uma instância do WhatsApp primeiro",
          variant: "destructive"
        });
        navigate("/whatsapp");
        return;
      }

      await api.post("/whatsapp/messages/send", {
        instance_name: instances[0].name,
        to: whatsAppNumber.replace(/\D/g, ""),
        content: whatsAppMessage,
      });
      
      toast({ title: "Mensagem enviada!", description: "WhatsApp enviado com sucesso" });
      showSuccess("whatsapp");
      setShowWhatsAppModal(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao enviar";
      toast({ title: "Erro", description: message, variant: "destructive" });
    } finally {
      setIsLoading(null);
    }
  };

  const handleInstagram = () => {
    // Pre-fill caption with product info
    setInstagramCaption(`🛍️ ${product.title}\n\n💰 ${formatCurrency(product.price)}\n📦 ${product.salesCount.toLocaleString()} vendas\n\n`);
    setInstagramHashtags("#tiktrend #dropshipping #loja #produto #oferta");
    setShowInstagramModal(true);
  };

  // Direct Instagram post
  const handlePostInstagram = async () => {
    setIsLoading("instagram");
    try {
      await api.post("/social/instagram/post", {
        product_id: product.id,
        caption: instagramCaption,
        hashtags: instagramHashtags.split(/[\s,]+/).filter(h => h.startsWith("#")),
        image_url: product.imageUrl,
        post_type: "feed",
      });
      
      toast({ title: "Publicado no Instagram!", description: "Post criado com sucesso" });
      showSuccess("instagram");
      setShowInstagramModal(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao publicar";
      toast({ title: "Erro", description: message, variant: "destructive" });
    } finally {
      setIsLoading(null);
    }
  };

  const handleTikTok = () => {
    // Pre-fill caption with product info
    setTiktokCaption(`${product.title} 🔥 ${formatCurrency(product.price)}`);
    setTiktokSounds("");
    setShowTikTokModal(true);
  };

  // Direct TikTok post
  const handlePostTikTok = async () => {
    setIsLoading("tiktok");
    try {
      await api.post("/social/tiktok/post", {
        product_id: product.id,
        caption: tiktokCaption,
        video_url: product.videoUrl || product.imageUrl,
        sounds: tiktokSounds ? tiktokSounds.split(",").map(s => s.trim()) : [],
      });
      
      toast({ title: "Publicado no TikTok!", description: "Vídeo criado com sucesso" });
      showSuccess("tiktok");
      setShowTikTokModal(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao publicar";
      toast({ title: "Erro", description: message, variant: "destructive" });
    } finally {
      setIsLoading(null);
    }
  };

  const handleYouTube = () => {
    // Pre-fill YouTube info
    setYoutubeTitle(`${product.title} - Review e Unboxing`);
    setYoutubeDescription(`🛍️ ${product.title}\n\n💰 Preço: ${formatCurrency(product.price)}\n📦 Vendas: ${product.salesCount.toLocaleString()}\n\n${product.productUrl ? `🔗 Link: ${product.productUrl}` : ""}\n\n#tiktrend #dropshipping #produto`);
    setShowYouTubeModal(true);
  };

  // Direct YouTube upload
  const handleUploadYouTube = async () => {
    setIsLoading("youtube");
    try {
      await api.post("/social/youtube/upload", {
        product_id: product.id,
        title: youtubeTitle,
        description: youtubeDescription,
        video_url: product.videoUrl || product.imageUrl,
        privacy: "public",
        category: "22", // People & Blogs
      });
      
      toast({ title: "Enviado para o YouTube!", description: "Vídeo em processamento" });
      showSuccess("youtube");
      setShowYouTubeModal(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao enviar";
      toast({ title: "Erro", description: message, variant: "destructive" });
    } finally {
      setIsLoading(null);
    }
  };

  const handleSellerBot = () => {
    // Pre-fill campaign with product info
    setBotCampaignName(`Campanha - ${product.title}`);
    setBotMessage(`🔥 Oferta Especial!\n\n${product.title}\n\n💰 Apenas ${formatCurrency(product.price)}\n\n📦 Já foram ${product.salesCount.toLocaleString()} vendas!\n\n${product.productUrl || ""}`);
    setBotTargetAudience("all");
    setBotScheduleEnabled(false);
    setShowSellerBotModal(true);
  };

  // Create Seller Bot campaign directly
  const handleCreateBotCampaign = async () => {
    setIsLoading("seller-bot");
    try {
      await api.post("/seller-bot/campaigns", {
        name: botCampaignName,
        message: botMessage,
        target_audience: botTargetAudience,
        schedule_enabled: botScheduleEnabled,
        product_id: product.id,
        product_data: {
          title: product.title,
          price: product.price,
          image_url: product.imageUrl,
          product_url: product.productUrl,
        }
      });
      
      toast({ title: "Campanha criada!", description: "Seller Bot configurado com sucesso" });
      showSuccess("seller-bot");
      setShowSellerBotModal(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao criar campanha";
      toast({ title: "Erro", description: message, variant: "destructive" });
    } finally {
      setIsLoading(null);
    }
  };

  const handleCRM = () => {
    // Pre-fill CRM form
    setCrmOpportunityTitle(`Lead - ${product.title}`);
    setCrmValue(product.price);
    setCrmStage("lead");
    setCrmNotes(`Produto: ${product.title}\nPreço: ${formatCurrency(product.price)}\nVendas: ${product.salesCount.toLocaleString()}`);
    setShowCRMModal(true);
  };

  // Create CRM opportunity directly
  const handleCreateCRMOpportunity = async () => {
    setIsLoading("crm");
    try {
      await api.post("/crm/opportunities", {
        title: crmOpportunityTitle,
        value: crmValue,
        stage: crmStage,
        notes: crmNotes,
        source: "product_action",
        metadata: {
          product_id: product.id,
          product_title: product.title,
          product_price: product.price,
          product_url: product.productUrl,
        }
      });
      
      toast({ title: "Adicionado ao CRM!", description: "Oportunidade criada com sucesso" });
      showSuccess("crm");
      setShowCRMModal(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao criar oportunidade";
      toast({ title: "Erro", description: message, variant: "destructive" });
    } finally {
      setIsLoading(null);
    }
  };

  const handleEmail = () => {
    // Pre-fill email form
    setEmailSubject(`🛍️ ${product.title} - Oferta Especial!`);
    setEmailTemplate("product_launch");
    setEmailContent(`Olá!\n\nTemos uma oferta especial para você:\n\n${product.title}\n\n💰 Por apenas ${formatCurrency(product.price)}\n\n${product.description || ""}\n\n🛒 Aproveite agora!\n\n${product.productUrl || ""}`);
    setEmailAudience("all");
    setShowEmailModal(true);
  };

  // Create email campaign directly
  const handleCreateEmailCampaign = async () => {
    setIsLoading("email");
    try {
      await api.post("/campaigns/email", {
        subject: emailSubject,
        template: emailTemplate,
        content: emailContent,
        audience: emailAudience,
        product_id: product.id,
        product_data: {
          title: product.title,
          price: product.price,
          image_url: product.imageUrl,
          product_url: product.productUrl,
        }
      });
      
      toast({ title: "Campanha criada!", description: "Email marketing configurado" });
      showSuccess("email");
      setShowEmailModal(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao criar campanha";
      toast({ title: "Erro", description: message, variant: "destructive" });
    } finally {
      setIsLoading(null);
    }
  };

  const handleExport = async (format: "csv" | "json") => {
    setIsLoading("export");
    try {
      const response = await api.post("/products/export", {
        product_ids: [product.id],
        format,
      });
      
      // Create download link
      const blob = new Blob([JSON.stringify(response.data)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `produto-${product.id}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast({ title: `Exportado como ${format.toUpperCase()}!` });
    } catch {
      toast({ title: "Erro ao exportar", variant: "destructive" });
    } finally {
      setIsLoading(null);
    }
  };

  const handleViewOriginal = () => {
    if (product.productUrl) {
      window.open(product.productUrl, "_blank");
    }
  };

  // ============================================
  // ACTION GROUPS
  // ============================================

  const actionGroups: ActionGroup[] = [
    {
      title: "Conteúdo & Marketing",
      actions: [
        {
          id: "generate-copy",
          label: "Gerar Copy com IA",
          description: "Crie textos persuasivos para anúncios",
          icon: isLoading === "generate-copy" ? <Loader2 className="h-4 w-4 animate-spin" /> : successAction === "generate-copy" ? <Check className="h-4 w-4 text-green-500" /> : <Sparkles className="h-4 w-4" />,
          onClick: () => setShowCopyModal(true),
          variant: "primary",
          badge: "IA",
          disabled: isLoading === "generate-copy",
        },
        {
          id: "schedule-post",
          label: "Agendar Publicação",
          description: "Programe posts nas redes sociais",
          icon: isLoading === "schedule" ? <Loader2 className="h-4 w-4 animate-spin" /> : successAction === "schedule" ? <Check className="h-4 w-4 text-green-500" /> : <Calendar className="h-4 w-4" />,
          onClick: handleQuickSchedule,
          disabled: isLoading === "schedule",
        },
        {
          id: "seller-bot",
          label: "Seller Bot",
          description: "Automatize vendas com chatbot",
          icon: <Bot className="h-4 w-4" />,
          onClick: handleSellerBot,
          badge: "Auto",
        },
      ],
    },
    {
      title: "Redes Sociais",
      actions: [
        {
          id: "instagram",
          label: "Publicar no Instagram",
          description: "Crie um post ou story",
          icon: <Instagram className="h-4 w-4" />,
          onClick: handleInstagram,
        },
        {
          id: "tiktok",
          label: "Publicar no TikTok",
          description: "Crie um vídeo promocional",
          icon: <TikTokIcon />,
          onClick: handleTikTok,
        },
        {
          id: "youtube",
          label: "Publicar no YouTube",
          description: "Crie um Short ou vídeo",
          icon: <Youtube className="h-4 w-4" />,
          onClick: handleYouTube,
        },
      ],
    },
    {
      title: "Comunicação",
      actions: [
        {
          id: "whatsapp",
          label: "Enviar via WhatsApp",
          description: "Compartilhe com clientes",
          icon: isLoading === "whatsapp" ? <Loader2 className="h-4 w-4 animate-spin" /> : successAction === "whatsapp" ? <Check className="h-4 w-4 text-green-500" /> : <MessageCircle className="h-4 w-4" />,
          onClick: handleQuickWhatsApp,
          disabled: isLoading === "whatsapp",
        },
        {
          id: "email",
          label: "Campanha de Email",
          description: "Crie uma campanha de email",
          icon: isLoading === "email" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mail className="h-4 w-4" />,
          onClick: handleEmail,
          disabled: isLoading === "email",
        },
        {
          id: "crm",
          label: "Adicionar ao CRM",
          description: "Vincule a um contato/lead",
          icon: isLoading === "crm" ? <Loader2 className="h-4 w-4 animate-spin" /> : successAction === "crm" ? <Check className="h-4 w-4 text-green-500" /> : <ShoppingCart className="h-4 w-4" />,
          onClick: handleCRM,
          disabled: isLoading === "crm",
        },
      ],
    },
    {
      title: "Compartilhar & Exportar",
      actions: [
        {
          id: "copy-info",
          label: "Copiar Informações",
          description: "Copie dados formatados",
          icon: successAction === "copy-info" ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />,
          onClick: handleCopyInfo,
        },
        {
          id: "copy-link",
          label: "Copiar Link Original",
          description: "Copie o link do produto",
          icon: <Share2 className="h-4 w-4" />,
          onClick: handleCopyLink,
          disabled: !product.productUrl,
        },
        {
          id: "export",
          label: "Exportar Dados",
          description: "Baixe em CSV ou JSON",
          icon: <Download className="h-4 w-4" />,
          onClick: () => handleExport("csv"),
          disabled: isLoading === "export",
        },
        {
          id: "view-original",
          label: "Ver no TikTok Shop",
          description: "Abra a página original",
          icon: <ExternalLink className="h-4 w-4" />,
          onClick: handleViewOriginal,
          disabled: !product.productUrl,
        },
      ],
    },
  ];

  // ============================================
  // MODALS RENDER FUNCTION
  // ============================================

  const renderModals = () => (
    <>
      {/* Copy Generation Modal */}
      <Dialog open={showCopyModal} onOpenChange={setShowCopyModal}>
        <DialogContent className="sm:max-w-lg" data-testid="copy-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-tiktrend-primary" />
              Gerar Copy com IA
            </DialogTitle>
            <DialogDescription>
              Gere textos persuasivos para "{product.title}"
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tipo de Copy</Label>
                <Select value={copyType} onValueChange={setCopyType}>
                  <SelectTrigger data-testid="copy-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ad">Anúncio</SelectItem>
                    <SelectItem value="description">Descrição</SelectItem>
                    <SelectItem value="headline">Headline</SelectItem>
                    <SelectItem value="cta">Call to Action</SelectItem>
                    <SelectItem value="story">Story/Reels</SelectItem>
                    <SelectItem value="whatsapp">WhatsApp</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Tom</Label>
                <Select value={copyTone} onValueChange={setCopyTone}>
                  <SelectTrigger data-testid="copy-tone-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="professional">Profissional</SelectItem>
                    <SelectItem value="casual">Casual</SelectItem>
                    <SelectItem value="urgent">Urgente</SelectItem>
                    <SelectItem value="friendly">Amigável</SelectItem>
                    <SelectItem value="luxury">Luxo</SelectItem>
                    <SelectItem value="emotional">Emocional</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {generatedCopy && (
              <div className="space-y-2">
                <Label>Copy Gerada</Label>
                <div className="relative">
                  <Textarea
                    value={generatedCopy}
                    readOnly
                    className="min-h-[150px] pr-10"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-2 right-2"
                    onClick={handleCopyGeneratedText}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowCopyModal(false)}>
              Cancelar
            </Button>
            <Button variant="outline" onClick={handleGenerateCopyPage}>
              <ExternalLink className="h-4 w-4 mr-2" />
              Abrir Página
            </Button>
            <Button 
              onClick={handleGenerateCopyDirect}
              disabled={isLoading === "generate-copy"}
            >
              {isLoading === "generate-copy" ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Gerando...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Gerar Copy
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* WhatsApp Modal */}
      <Dialog open={showWhatsAppModal} onOpenChange={setShowWhatsAppModal}>
        <DialogContent className="sm:max-w-lg" data-testid="whatsapp-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5 text-green-500" />
              Enviar via WhatsApp
            </DialogTitle>
            <DialogDescription>
              Compartilhe este produto pelo WhatsApp
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Número do WhatsApp</Label>
              <input
                type="tel"
                placeholder="+55 11 99999-9999"
                value={whatsAppNumber}
                onChange={(e) => setWhatsAppNumber(e.target.value)}
                data-testid="whatsapp-number-input"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Mensagem</Label>
              <Textarea
                value={whatsAppMessage}
                onChange={(e) => setWhatsAppMessage(e.target.value)}
                className="min-h-[120px]"
                placeholder="Digite a mensagem..."
                data-testid="whatsapp-message-input"
              />
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowWhatsAppModal(false)}>
              Cancelar
            </Button>
            <Button variant="outline" onClick={handleWhatsAppPage}>
              <ExternalLink className="h-4 w-4 mr-2" />
              Abrir Página
            </Button>
            <Button 
              onClick={handleSendWhatsApp}
              disabled={isLoading === "whatsapp"}
              className="bg-green-600 hover:bg-green-700"
            >
              {isLoading === "whatsapp" ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Enviando...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Enviar
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Schedule Modal */}
      <Dialog open={showScheduleModal} onOpenChange={setShowScheduleModal}>
        <DialogContent className="sm:max-w-lg" data-testid="schedule-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-500" />
              Agendar Publicação
            </DialogTitle>
            <DialogDescription>
              Programe a publicação deste produto
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Plataforma</Label>
              <Select value={schedulePlatform} onValueChange={setSchedulePlatform}>
                <SelectTrigger data-testid="platform-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="instagram">
                    <span className="flex items-center gap-2">
                      <Instagram className="h-4 w-4" /> Instagram
                    </span>
                  </SelectItem>
                  <SelectItem value="tiktok">
                    <span className="flex items-center gap-2">
                      <TikTokIcon /> TikTok
                    </span>
                  </SelectItem>
                  <SelectItem value="youtube">
                    <span className="flex items-center gap-2">
                      <Youtube className="h-4 w-4" /> YouTube
                    </span>
                  </SelectItem>
                  <SelectItem value="whatsapp">
                    <span className="flex items-center gap-2">
                      <MessageCircle className="h-4 w-4" /> WhatsApp Status
                    </span>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Data e Hora</Label>
              <input
                type="datetime-local"
                value={scheduleDate}
                onChange={(e) => setScheduleDate(e.target.value)}
                min={new Date().toISOString().slice(0, 16)}
                data-testid="schedule-datetime-input"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>

            {/* Preview */}
            <div className="p-3 rounded-lg bg-muted/50 border">
              <p className="text-sm font-medium mb-1">Preview do Post:</p>
              <p className="text-sm text-muted-foreground">
                🛍️ {product.title}<br/>
                💰 {formatCurrency(product.price)}
              </p>
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowScheduleModal(false)}>
              Cancelar
            </Button>
            <Button variant="outline" onClick={() => handleSchedulePost(schedulePlatform)}>
              <ExternalLink className="h-4 w-4 mr-2" />
              Configurar Avançado
            </Button>
            <Button 
              onClick={handleSubmitSchedule}
              disabled={isLoading === "schedule" || !scheduleDate}
            >
              {isLoading === "schedule" ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Agendando...
                </>
              ) : (
                <>
                  <Calendar className="h-4 w-4 mr-2" />
                  Agendar
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Instagram Modal */}
      <Dialog open={showInstagramModal} onOpenChange={setShowInstagramModal}>
        <DialogContent className="sm:max-w-lg" data-testid="instagram-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Instagram className="h-5 w-5 text-pink-500" />
              Publicar no Instagram
            </DialogTitle>
            <DialogDescription>
              Crie um post para "{product.title}"
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Preview Image */}
            <div className="relative aspect-square max-w-[200px] mx-auto rounded-lg overflow-hidden border">
              <img 
                src={product.imageUrl} 
                alt={product.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
                <p className="text-white text-xs truncate">{product.title}</p>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Legenda</Label>
              <Textarea
                value={instagramCaption}
                onChange={(e) => setInstagramCaption(e.target.value)}
                className="min-h-[100px]"
                placeholder="Escreva sua legenda..."
                data-testid="instagram-caption-input"
              />
              <p className="text-xs text-muted-foreground">
                {instagramCaption.length}/2200 caracteres
              </p>
            </div>
            
            <div className="space-y-2">
              <Label>Hashtags</Label>
              <Textarea
                value={instagramHashtags}
                onChange={(e) => setInstagramHashtags(e.target.value)}
                className="min-h-[60px]"
                placeholder="#hashtag1 #hashtag2"
                data-testid="instagram-hashtags-input"
              />
              <p className="text-xs text-muted-foreground">
                {instagramHashtags.split(/[\s,]+/).filter(h => h.startsWith("#")).length}/30 hashtags
              </p>
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowInstagramModal(false)}>
              Cancelar
            </Button>
            <Button 
              variant="outline" 
              onClick={() => {
                navigate(`/social/instagram?action=post&productId=${product.id}`);
                onClose?.();
              }}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Abrir Página
            </Button>
            <Button 
              onClick={handlePostInstagram}
              disabled={isLoading === "instagram" || !instagramCaption}
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
            >
              {isLoading === "instagram" ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Publicando...
                </>
              ) : (
                <>
                  <Instagram className="h-4 w-4 mr-2" />
                  Publicar
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* TikTok Modal */}
      <Dialog open={showTikTokModal} onOpenChange={setShowTikTokModal}>
        <DialogContent className="sm:max-w-lg" data-testid="tiktok-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <TikTokIcon />
              <span className="ml-1">Publicar no TikTok</span>
            </DialogTitle>
            <DialogDescription>
              Crie um vídeo para "{product.title}"
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Video Preview */}
            <div className="relative aspect-[9/16] max-w-[150px] mx-auto rounded-lg overflow-hidden border bg-black">
              <img 
                src={product.imageUrl} 
                alt={product.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </div>
              </div>
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
                <p className="text-white text-[10px] truncate">{product.title}</p>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Legenda</Label>
              <Textarea
                value={tiktokCaption}
                onChange={(e) => setTiktokCaption(e.target.value)}
                className="min-h-[80px]"
                placeholder="Escreva sua legenda com hashtags..."
                data-testid="tiktok-caption-input"
              />
              <p className="text-xs text-muted-foreground">
                {tiktokCaption.length}/150 caracteres
              </p>
            </div>
            
            <div className="space-y-2">
              <Label>Sons (opcional)</Label>
              <input
                type="text"
                value={tiktokSounds}
                onChange={(e) => setTiktokSounds(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Buscar som trending..."
                data-testid="tiktok-sounds-input"
              />
            </div>

            {/* Tips */}
            <div className="p-3 rounded-lg bg-muted/50 border">
              <p className="text-xs font-medium mb-1">💡 Dicas para viralizar:</p>
              <ul className="text-xs text-muted-foreground space-y-1">
                <li>• Use sons em alta</li>
                <li>• Hashtags: #fyp #viral #produto</li>
                <li>• Vídeos curtos (15-30s) engajam mais</li>
              </ul>
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowTikTokModal(false)}>
              Cancelar
            </Button>
            <Button 
              variant="outline" 
              onClick={() => {
                navigate(`/social/tiktok?action=post&productId=${product.id}`);
                onClose?.();
              }}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Abrir Página
            </Button>
            <Button 
              onClick={handlePostTikTok}
              disabled={isLoading === "tiktok" || !tiktokCaption}
              className="bg-black hover:bg-zinc-800"
            >
              {isLoading === "tiktok" ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Publicando...
                </>
              ) : (
                <>
                  <TikTokIcon />
                  <span className="ml-2">Publicar</span>
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* YouTube Modal */}
      <Dialog open={showYouTubeModal} onOpenChange={setShowYouTubeModal}>
        <DialogContent className="sm:max-w-lg" data-testid="youtube-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Youtube className="h-5 w-5 text-red-500" />
              Enviar para YouTube
            </DialogTitle>
            <DialogDescription>
              Faça upload de vídeo do "{product.title}"
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Thumbnail Preview */}
            <div className="relative aspect-video max-w-[250px] mx-auto rounded-lg overflow-hidden border">
              <img 
                src={product.imageUrl} 
                alt={product.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-2 right-2 bg-black/80 text-white text-[10px] px-1 rounded">
                0:00
              </div>
            </div>

            <div className="space-y-2">
              <Label>Título do Vídeo</Label>
              <input
                type="text"
                value={youtubeTitle}
                onChange={(e) => setYoutubeTitle(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Título do vídeo..."
                data-testid="youtube-title-input"
              />
              <p className="text-xs text-muted-foreground">
                {youtubeTitle.length}/100 caracteres
              </p>
            </div>
            
            <div className="space-y-2">
              <Label>Descrição</Label>
              <Textarea
                value={youtubeDescription}
                onChange={(e) => setYoutubeDescription(e.target.value)}
                className="min-h-[120px]"
                placeholder="Descrição do vídeo com links e hashtags..."
                data-testid="youtube-description-input"
              />
              <p className="text-xs text-muted-foreground">
                {youtubeDescription.length}/5000 caracteres
              </p>
            </div>

            {/* SEO Tips */}
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
              <p className="text-xs font-medium mb-1 text-red-600">📹 Dicas de SEO:</p>
              <ul className="text-xs text-muted-foreground space-y-1">
                <li>• Inclua palavras-chave no título</li>
                <li>• Adicione timestamps na descrição</li>
                <li>• Use tags relevantes</li>
              </ul>
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowYouTubeModal(false)}>
              Cancelar
            </Button>
            <Button 
              variant="outline" 
              onClick={() => {
                navigate(`/social/youtube?action=post&productId=${product.id}`);
                onClose?.();
              }}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Abrir Página
            </Button>
            <Button 
              onClick={handleUploadYouTube}
              disabled={isLoading === "youtube" || !youtubeTitle}
              className="bg-red-600 hover:bg-red-700"
            >
              {isLoading === "youtube" ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Enviando...
                </>
              ) : (
                <>
                  <Youtube className="h-4 w-4 mr-2" />
                  Enviar Vídeo
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Seller Bot Modal */}
      <Dialog open={showSellerBotModal} onOpenChange={setShowSellerBotModal}>
        <DialogContent className="sm:max-w-lg" data-testid="seller-bot-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-purple-500" />
              Seller Bot - Campanha
            </DialogTitle>
            <DialogDescription>
              Configure uma campanha automática para "{product.title}"
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Nome da Campanha</Label>
              <input
                type="text"
                value={botCampaignName}
                onChange={(e) => setBotCampaignName(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Nome da campanha..."
                data-testid="bot-campaign-name-input"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Mensagem</Label>
              <Textarea
                value={botMessage}
                onChange={(e) => setBotMessage(e.target.value)}
                className="min-h-[120px]"
                placeholder="Mensagem que será enviada..."
                data-testid="bot-message-input"
              />
            </div>

            <div className="space-y-2">
              <Label>Público-alvo</Label>
              <Select value={botTargetAudience} onValueChange={setBotTargetAudience}>
                <SelectTrigger data-testid="bot-audience-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os Contatos</SelectItem>
                  <SelectItem value="leads">Leads Novos</SelectItem>
                  <SelectItem value="customers">Clientes</SelectItem>
                  <SelectItem value="inactive">Inativos (30+ dias)</SelectItem>
                  <SelectItem value="engaged">Engajados</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border">
              <div>
                <p className="text-sm font-medium">Agendamento Automático</p>
                <p className="text-xs text-muted-foreground">Enviar em horários otimizados</p>
              </div>
              <Button
                variant={botScheduleEnabled ? "default" : "outline"}
                size="sm"
                onClick={() => setBotScheduleEnabled(!botScheduleEnabled)}
              >
                {botScheduleEnabled ? "Ativado" : "Desativado"}
              </Button>
            </div>

            {/* Stats Preview */}
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20">
                <p className="text-lg font-bold text-purple-500">~500</p>
                <p className="text-[10px] text-muted-foreground">Alcance</p>
              </div>
              <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
                <p className="text-lg font-bold text-blue-500">~15%</p>
                <p className="text-[10px] text-muted-foreground">Taxa Abertura</p>
              </div>
              <div className="p-2 rounded-lg bg-green-500/10 border border-green-500/20">
                <p className="text-lg font-bold text-green-500">~3%</p>
                <p className="text-[10px] text-muted-foreground">Conversão</p>
              </div>
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowSellerBotModal(false)}>
              Cancelar
            </Button>
            <Button 
              variant="outline" 
              onClick={() => {
                navigate(`/seller-bot?productId=${product.id}`);
                onClose?.();
              }}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Configurar Avançado
            </Button>
            <Button 
              onClick={handleCreateBotCampaign}
              disabled={isLoading === "seller-bot" || !botCampaignName}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {isLoading === "seller-bot" ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Criando...
                </>
              ) : (
                <>
                  <Bot className="h-4 w-4 mr-2" />
                  Criar Campanha
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* CRM Modal */}
      <Dialog open={showCRMModal} onOpenChange={setShowCRMModal}>
        <DialogContent className="sm:max-w-lg" data-testid="crm-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5 text-orange-500" />
              Adicionar ao CRM
            </DialogTitle>
            <DialogDescription>
              Crie uma oportunidade para "{product.title}"
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Título da Oportunidade</Label>
              <input
                type="text"
                value={crmOpportunityTitle}
                onChange={(e) => setCrmOpportunityTitle(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Ex: Lead - Nome do Produto"
                data-testid="crm-title-input"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Valor</Label>
                <input
                  type="number"
                  value={crmValue}
                  onChange={(e) => setCrmValue(Number(e.target.value))}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  placeholder="0.00"
                  data-testid="crm-value-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Estágio</Label>
                <Select value={crmStage} onValueChange={setCrmStage}>
                  <SelectTrigger data-testid="crm-stage-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="lead">Lead</SelectItem>
                    <SelectItem value="qualified">Qualificado</SelectItem>
                    <SelectItem value="proposal">Proposta</SelectItem>
                    <SelectItem value="negotiation">Negociação</SelectItem>
                    <SelectItem value="won">Ganho</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>Notas</Label>
              <Textarea
                value={crmNotes}
                onChange={(e) => setCrmNotes(e.target.value)}
                className="min-h-[80px]"
                placeholder="Observações sobre esta oportunidade..."
                data-testid="crm-notes-input"
              />
            </div>

            {/* Product Info */}
            <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 border">
              <img 
                src={product.imageUrl} 
                alt={product.title}
                className="w-12 h-12 rounded object-cover"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{product.title}</p>
                <p className="text-xs text-muted-foreground">{formatCurrency(product.price)}</p>
              </div>
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowCRMModal(false)}>
              Cancelar
            </Button>
            <Button 
              variant="outline" 
              onClick={() => {
                navigate(`/crm/contacts?action=add&productId=${product.id}`);
                onClose?.();
              }}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Abrir CRM
            </Button>
            <Button 
              onClick={handleCreateCRMOpportunity}
              disabled={isLoading === "crm" || !crmOpportunityTitle}
              className="bg-orange-600 hover:bg-orange-700"
            >
              {isLoading === "crm" ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Criando...
                </>
              ) : (
                <>
                  <ShoppingCart className="h-4 w-4 mr-2" />
                  Criar Oportunidade
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Email Marketing Modal */}
      <Dialog open={showEmailModal} onOpenChange={setShowEmailModal}>
        <DialogContent className="sm:max-w-lg" data-testid="email-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5 text-sky-500" />
              Email Marketing
            </DialogTitle>
            <DialogDescription>
              Crie uma campanha de email para "{product.title}"
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Assunto do Email</Label>
              <input
                type="text"
                value={emailSubject}
                onChange={(e) => setEmailSubject(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Assunto do email..."
                data-testid="email-subject-input"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Template</Label>
                <Select value={emailTemplate} onValueChange={setEmailTemplate}>
                  <SelectTrigger data-testid="email-template-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="product_launch">Lançamento</SelectItem>
                    <SelectItem value="promotion">Promoção</SelectItem>
                    <SelectItem value="newsletter">Newsletter</SelectItem>
                    <SelectItem value="follow_up">Follow-up</SelectItem>
                    <SelectItem value="custom">Personalizado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Audiência</Label>
                <Select value={emailAudience} onValueChange={setEmailAudience}>
                  <SelectTrigger data-testid="email-audience-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    <SelectItem value="subscribers">Inscritos</SelectItem>
                    <SelectItem value="customers">Clientes</SelectItem>
                    <SelectItem value="leads">Leads</SelectItem>
                    <SelectItem value="vip">VIP</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>Conteúdo</Label>
              <Textarea
                value={emailContent}
                onChange={(e) => setEmailContent(e.target.value)}
                className="min-h-[120px]"
                placeholder="Conteúdo do email..."
                data-testid="email-content-input"
              />
            </div>

            {/* Email Preview */}
            <div className="p-3 rounded-lg bg-sky-500/10 border border-sky-500/20">
              <p className="text-xs font-medium mb-1 text-sky-600">📧 Preview:</p>
              <p className="text-xs font-medium">{emailSubject}</p>
              <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">
                {emailContent.substring(0, 100)}...
              </p>
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowEmailModal(false)}>
              Cancelar
            </Button>
            <Button 
              variant="outline" 
              onClick={() => {
                navigate(`/automation/workflows?tab=email&productId=${product.id}`);
                onClose?.();
              }}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Editor Avançado
            </Button>
            <Button 
              onClick={handleCreateEmailCampaign}
              disabled={isLoading === "email" || !emailSubject}
              className="bg-sky-600 hover:bg-sky-700"
            >
              {isLoading === "email" ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Criando...
                </>
              ) : (
                <>
                  <Mail className="h-4 w-4 mr-2" />
                  Criar Campanha
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );

  // ============================================
  // COMPACT VARIANT (Quick Actions Bar)
  // ============================================

  if (variant === "compact") {
    return (
      <div className="flex items-center gap-2" data-testid="quick-actions">
        <TooltipProvider>
          {/* Primary: Generate Copy */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="tiktrend"
                size="sm"
                className="gap-1.5"
                onClick={() => setShowCopyModal(true)}
                disabled={isLoading === "generate-copy"}
                data-testid="quick-copy"
              >
                {isLoading === "generate-copy" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                Gerar Copy
              </Button>
            </TooltipTrigger>
            <TooltipContent>Gerar copy com IA</TooltipContent>
          </Tooltip>

          {/* Schedule */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button 
                variant="outline" 
                size="icon" 
                onClick={handleQuickSchedule}
                disabled={isLoading === "schedule"}
                data-testid="quick-schedule"
              >
                {isLoading === "schedule" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Calendar className="h-4 w-4" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent>Agendar publicação</TooltipContent>
          </Tooltip>

          {/* WhatsApp */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button 
                variant="outline" 
                size="icon" 
                onClick={handleQuickWhatsApp}
                disabled={isLoading === "whatsapp"}
                data-testid="quick-whatsapp"
              >
                {isLoading === "whatsapp" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <MessageCircle className="h-4 w-4" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent>Enviar via WhatsApp</TooltipContent>
          </Tooltip>

          {/* Favorite */}
          {onFavorite && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={isFavorite ? "secondary" : "outline"}
                  size="icon"
                  onClick={() => onFavorite(product)}
                  data-testid="quick-favorite"
                >
                  <Heart
                    className={`h-4 w-4 ${isFavorite ? "fill-red-500 text-red-500" : ""}`}
                  />
                </Button>
              </TooltipTrigger>
              <TooltipContent>{isFavorite ? "Remover dos favoritos" : "Adicionar aos favoritos"}</TooltipContent>
            </Tooltip>
          )}

          {/* More Actions Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon" data-testid="more-actions">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>Mais Ações</DropdownMenuLabel>
              <DropdownMenuSeparator />
              
              <DropdownMenuItem onClick={handleInstagram}>
                <Instagram className="h-4 w-4 mr-2" />
                Instagram
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleTikTok}>
                <span className="mr-2"><TikTokIcon /></span>
                TikTok
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleYouTube}>
                <Youtube className="h-4 w-4 mr-2" />
                YouTube
              </DropdownMenuItem>
              
              <DropdownMenuSeparator />
              
              <DropdownMenuItem onClick={handleSellerBot}>
                <Bot className="h-4 w-4 mr-2" />
                Seller Bot
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleCRM}>
                <ShoppingCart className="h-4 w-4 mr-2" />
                Adicionar ao CRM
              </DropdownMenuItem>
              
              <DropdownMenuSeparator />
              
              <DropdownMenuItem onClick={handleCopyInfo}>
                <Copy className="h-4 w-4 mr-2" />
                Copiar Informações
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport("csv")}>
                <Download className="h-4 w-4 mr-2" />
                Exportar CSV
              </DropdownMenuItem>
              {product.productUrl && (
                <DropdownMenuItem onClick={handleViewOriginal}>
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Ver Original
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </TooltipProvider>

        {/* Modals for Compact Variant */}
        {renderModals()}
      </div>
    );
  }

  // ============================================
  // FULL VARIANT (Panel with all actions)
  // ============================================

  return (
    <div className="space-y-6" data-testid="product-actions-panel">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-tiktrend-primary" />
          <h3 className="font-semibold text-lg">Ações Rápidas</h3>
        </div>
        <Badge variant="outline" className="text-xs">
          {actionGroups.reduce((acc, g) => acc + g.actions.length, 0)} disponíveis
        </Badge>
      </div>

      {/* Action Groups */}
      <div className="space-y-6">
        {actionGroups.map((group) => (
          <div key={group.title} className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              {group.title}
            </h4>
            <div className="grid gap-2">
              {group.actions.map((action) => (
                <button
                  key={action.id}
                  data-testid={`action-${action.id}`}
                  onClick={action.onClick}
                  disabled={action.disabled}
                  className={`
                    group flex items-center gap-3 p-3 rounded-lg text-left transition-all
                    ${action.variant === "primary" 
                      ? "bg-tiktrend-primary/10 hover:bg-tiktrend-primary/20 border border-tiktrend-primary/20" 
                      : "bg-muted/50 hover:bg-muted border border-transparent"
                    }
                    ${action.disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
                  `}
                >
                  <div className={`
                    p-2 rounded-lg transition-colors
                    ${action.variant === "primary" 
                      ? "bg-tiktrend-primary/20 text-tiktrend-primary" 
                      : "bg-background text-muted-foreground group-hover:text-foreground"
                    }
                  `}>
                    {action.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{action.label}</span>
                      {action.badge && (
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                          {action.badge}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground truncate">
                      {action.description}
                    </p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Quick Stats */}
      <div className="pt-4 border-t">
        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
            <p className="text-lg font-bold text-green-500">{product.salesCount.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground">Vendas Totais</p>
          </div>
          <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
            <p className="text-lg font-bold text-yellow-500">{product.productRating?.toFixed(1) || "N/A"}</p>
            <p className="text-xs text-muted-foreground">Avaliação</p>
          </div>
        </div>
      </div>

      {/* Modals for Full Variant */}
      {renderModals()}
    </div>
  );
};

export default ProductActionsPanel;
