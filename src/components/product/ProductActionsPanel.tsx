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
  };

  const handleCopyLink = async () => {
    if (product.productUrl) {
      await navigator.clipboard.writeText(product.productUrl);
      toast({ title: "Link copiado!" });
    } else {
      toast({ title: "Link não disponível", variant: "destructive" });
    }
  };

  const handleGenerateCopy = () => {
    navigate(`/copy?productId=${product.id}&title=${encodeURIComponent(product.title)}&price=${product.price}`);
    onClose?.();
  };

  const handleSchedulePost = (platform: string) => {
    navigate(`/automation/scheduler?productId=${product.id}&platform=${platform}`);
    onClose?.();
  };

  const handleWhatsApp = () => {
    navigate(`/whatsapp?action=send&productId=${product.id}`);
    onClose?.();
  };

  const handleInstagram = () => {
    navigate(`/social/instagram?action=post&productId=${product.id}`);
    onClose?.();
  };

  const handleTikTok = () => {
    navigate(`/social/tiktok?action=post&productId=${product.id}`);
    onClose?.();
  };

  const handleYouTube = () => {
    navigate(`/social/youtube?action=post&productId=${product.id}`);
    onClose?.();
  };

  const handleSellerBot = () => {
    navigate(`/seller-bot?productId=${product.id}`);
    onClose?.();
  };

  const handleCRM = () => {
    navigate(`/crm/contacts?action=add&productId=${product.id}`);
    onClose?.();
  };

  const handleEmail = async () => {
    setIsLoading("email");
    try {
      // Create email campaign with product
      await api.post("/campaigns/email/draft", {
        product_id: product.id,
        product_title: product.title,
        product_price: product.price,
        product_image: product.imageUrl,
      });
      navigate(`/automation/workflows?tab=email&productId=${product.id}`);
      onClose?.();
    } catch {
      toast({ title: "Erro ao criar campanha", variant: "destructive" });
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
          icon: <Sparkles className="h-4 w-4" />,
          onClick: handleGenerateCopy,
          variant: "primary",
          badge: "IA",
        },
        {
          id: "schedule-post",
          label: "Agendar Publicação",
          description: "Programe posts nas redes sociais",
          icon: <Calendar className="h-4 w-4" />,
          onClick: () => handleSchedulePost("instagram"),
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
          icon: <MessageCircle className="h-4 w-4" />,
          onClick: handleWhatsApp,
        },
        {
          id: "email",
          label: "Campanha de Email",
          description: "Crie uma campanha de email",
          icon: <Mail className="h-4 w-4" />,
          onClick: handleEmail,
          disabled: isLoading === "email",
        },
        {
          id: "crm",
          label: "Adicionar ao CRM",
          description: "Vincule a um contato/lead",
          icon: <ShoppingCart className="h-4 w-4" />,
          onClick: handleCRM,
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
          icon: <Copy className="h-4 w-4" />,
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
  // COMPACT VARIANT (Quick Actions Bar)
  // ============================================

  if (variant === "compact") {
    return (
      <div className="flex items-center gap-2">
        <TooltipProvider>
          {/* Primary: Generate Copy */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="tiktrend"
                size="sm"
                className="gap-1.5"
                onClick={handleGenerateCopy}
              >
                <Sparkles className="h-4 w-4" />
                Gerar Copy
              </Button>
            </TooltipTrigger>
            <TooltipContent>Gerar copy com IA</TooltipContent>
          </Tooltip>

          {/* Schedule */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="icon" onClick={() => handleSchedulePost("instagram")}>
                <Calendar className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Agendar publicação</TooltipContent>
          </Tooltip>

          {/* WhatsApp */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="icon" onClick={handleWhatsApp}>
                <MessageCircle className="h-4 w-4" />
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
              <Button variant="outline" size="icon">
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
      </div>
    );
  }

  // ============================================
  // FULL VARIANT (Panel with all actions)
  // ============================================

  return (
    <div className="space-y-6">
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
    </div>
  );
};

export default ProductActionsPanel;
