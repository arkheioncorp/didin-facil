import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import type { Product } from "@/types";
import {
  Sparkles,
  Calendar,
  MessageCircle,
  Instagram,
  Youtube,
  Heart,
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
  History,
  Star,
} from "lucide-react";

// Import modular components
import { useProductActions } from "./actions/useProductActions";
import { ActionHistory } from "./actions/ActionHistory";
import { FavoriteActionsList, FavoriteActionButton } from "./actions/FavoriteActions";
import {
  CopyAIModal,
  WhatsAppModal,
  ScheduleModal,
  InstagramModal,
  TikTokModal,
  YouTubeModal,
  SellerBotModal,
  CRMModal,
  EmailModal,
} from "./actions/modals";
import type { ActionGroup, ActionId } from "./actions/types";

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

export const ProductActionsPanelRefactored: React.FC<ProductActionsPanelProps> = ({
  product,
  isFavorite = false,
  onFavorite,
  onClose,
  variant = "full",
}) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = React.useState("actions");
  
  // Use the modular hook for all actions
  const {
    isLoading,
    successAction,
    modals,
    openModal,
    closeModal,
    copyForm,
    whatsAppForm,
    scheduleForm,
    instagramForm,
    tiktokForm,
    youtubeForm,
    sellerBotForm,
    crmForm,
    emailForm,
    actions,
    prefill,
  } = useProductActions(product);

  // Navigation helper
  const handleNavigate = (path: string) => {
    navigate(path);
    onClose?.();
  };

  // Open modal with prefill
  const handleOpenInstagram = () => {
    prefill.instagram();
    openModal("instagram");
  };

  const handleOpenTikTok = () => {
    prefill.tiktok();
    openModal("tiktok");
  };

  const handleOpenYouTube = () => {
    prefill.youtube();
    openModal("youtube");
  };

  const handleOpenSellerBot = () => {
    prefill.sellerBot();
    openModal("sellerBot");
  };

  const handleOpenCRM = () => {
    prefill.crm();
    openModal("crm");
  };

  const handleOpenEmail = () => {
    prefill.email();
    openModal("email");
  };

  const handleOpenWhatsApp = () => {
    prefill.whatsApp();
    openModal("whatsApp");
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
          onClick: () => openModal("copy"),
          variant: "primary",
          badge: "IA",
        },
        {
          id: "schedule",
          label: "Agendar Publicação",
          description: "Programe posts para redes sociais",
          icon: <Calendar className="h-4 w-4" />,
          onClick: () => openModal("schedule"),
        },
      ],
    },
    {
      title: "Redes Sociais",
      actions: [
        {
          id: "whatsapp",
          label: "WhatsApp",
          description: "Enviar para contatos ou grupos",
          icon: <MessageCircle className="h-4 w-4" />,
          onClick: handleOpenWhatsApp,
        },
        {
          id: "instagram",
          label: "Instagram",
          description: "Publicar no feed ou stories",
          icon: <Instagram className="h-4 w-4" />,
          onClick: handleOpenInstagram,
        },
        {
          id: "tiktok",
          label: "TikTok",
          description: "Criar vídeo de produto",
          icon: <TikTokIcon />,
          onClick: handleOpenTikTok,
        },
        {
          id: "youtube",
          label: "YouTube",
          description: "Upload de vídeo review",
          icon: <Youtube className="h-4 w-4" />,
          onClick: handleOpenYouTube,
        },
      ],
    },
    {
      title: "Automação & Vendas",
      actions: [
        {
          id: "seller-bot",
          label: "Seller Bot",
          description: "Automatizar vendas com bot",
          icon: <Bot className="h-4 w-4" />,
          onClick: handleOpenSellerBot,
          badge: "Auto",
        },
        {
          id: "crm",
          label: "Adicionar ao CRM",
          description: "Criar oportunidade de venda",
          icon: <ShoppingCart className="h-4 w-4" />,
          onClick: handleOpenCRM,
        },
        {
          id: "email",
          label: "Email Marketing",
          description: "Criar campanha de email",
          icon: <Mail className="h-4 w-4" />,
          onClick: handleOpenEmail,
        },
      ],
    },
    {
      title: "Utilitários",
      actions: [
        {
          id: "copy-info",
          label: "Copiar Informações",
          description: "Copiar dados do produto",
          icon: <Copy className="h-4 w-4" />,
          onClick: actions.copyInfo,
        },
        {
          id: "copy-link",
          label: "Copiar Link",
          description: "Copiar URL do produto",
          icon: <ExternalLink className="h-4 w-4" />,
          onClick: actions.copyLink,
        },
        {
          id: "export",
          label: "Exportar",
          description: "Baixar dados em CSV/JSON",
          icon: <Download className="h-4 w-4" />,
          onClick: () => actions.exportProduct("json"),
        },
      ],
    },
  ];

  // ============================================
  // RENDER MODALS
  // ============================================

  const renderModals = () => (
    <>
      <CopyAIModal
        open={modals.copy}
        onOpenChange={(open) => open ? openModal("copy") : closeModal("copy")}
        product={product}
        isLoading={isLoading === "generate-copy"}
        copyType={copyForm.type}
        setCopyType={copyForm.setType}
        copyTone={copyForm.tone}
        setCopyTone={copyForm.setTone}
        generatedCopy={copyForm.generatedCopy}
        onGenerate={actions.generateCopy}
        onCopyText={actions.copyGeneratedText}
        onNavigate={handleNavigate}
      />

      <WhatsAppModal
        open={modals.whatsApp}
        onOpenChange={(open) => open ? openModal("whatsApp") : closeModal("whatsApp")}
        product={product}
        isLoading={isLoading === "whatsapp"}
        phoneNumber={whatsAppForm.phoneNumber}
        setPhoneNumber={whatsAppForm.setPhoneNumber}
        message={whatsAppForm.message}
        setMessage={whatsAppForm.setMessage}
        onSend={actions.sendWhatsApp}
        onNavigate={handleNavigate}
      />

      <ScheduleModal
        open={modals.schedule}
        onOpenChange={(open) => open ? openModal("schedule") : closeModal("schedule")}
        product={product}
        isLoading={isLoading === "schedule"}
        platform={scheduleForm.platform}
        setPlatform={scheduleForm.setPlatform}
        scheduleDate={scheduleForm.date}
        setScheduleDate={scheduleForm.setDate}
        onSchedule={actions.submitSchedule}
        onNavigate={handleNavigate}
      />

      <InstagramModal
        open={modals.instagram}
        onOpenChange={(open) => open ? openModal("instagram") : closeModal("instagram")}
        product={product}
        isLoading={isLoading === "instagram"}
        caption={instagramForm.caption}
        setCaption={instagramForm.setCaption}
        hashtags={instagramForm.hashtags}
        setHashtags={instagramForm.setHashtags}
        onPost={actions.postInstagram}
        onNavigate={handleNavigate}
      />

      <TikTokModal
        open={modals.tiktok}
        onOpenChange={(open) => open ? openModal("tiktok") : closeModal("tiktok")}
        product={product}
        isLoading={isLoading === "tiktok"}
        caption={tiktokForm.caption}
        setCaption={tiktokForm.setCaption}
        sounds={tiktokForm.sounds}
        setSounds={tiktokForm.setSounds}
        onPost={actions.postTikTok}
        onNavigate={handleNavigate}
      />

      <YouTubeModal
        open={modals.youtube}
        onOpenChange={(open) => open ? openModal("youtube") : closeModal("youtube")}
        product={product}
        isLoading={isLoading === "youtube"}
        title={youtubeForm.title}
        setTitle={youtubeForm.setTitle}
        description={youtubeForm.description}
        setDescription={youtubeForm.setDescription}
        onUpload={actions.uploadYouTube}
        onNavigate={handleNavigate}
      />

      <SellerBotModal
        open={modals.sellerBot}
        onOpenChange={(open) => open ? openModal("sellerBot") : closeModal("sellerBot")}
        product={product}
        isLoading={isLoading === "seller-bot"}
        campaignName={sellerBotForm.campaignName}
        setCampaignName={sellerBotForm.setCampaignName}
        message={sellerBotForm.message}
        setMessage={sellerBotForm.setMessage}
        targetAudience={sellerBotForm.targetAudience}
        setTargetAudience={sellerBotForm.setTargetAudience}
        scheduleEnabled={sellerBotForm.scheduleEnabled}
        setScheduleEnabled={sellerBotForm.setScheduleEnabled}
        onCreateCampaign={actions.createBotCampaign}
        onNavigate={handleNavigate}
      />

      <CRMModal
        open={modals.crm}
        onOpenChange={(open) => open ? openModal("crm") : closeModal("crm")}
        product={product}
        isLoading={isLoading === "crm"}
        opportunityTitle={crmForm.opportunityTitle}
        setOpportunityTitle={crmForm.setOpportunityTitle}
        value={crmForm.value}
        setValue={crmForm.setValue}
        stage={crmForm.stage}
        setStage={crmForm.setStage}
        notes={crmForm.notes}
        setNotes={crmForm.setNotes}
        onCreateOpportunity={actions.createCRMOpportunity}
        onNavigate={handleNavigate}
      />

      <EmailModal
        open={modals.email}
        onOpenChange={(open) => open ? openModal("email") : closeModal("email")}
        product={product}
        isLoading={isLoading === "email"}
        subject={emailForm.subject}
        setSubject={emailForm.setSubject}
        template={emailForm.template}
        setTemplate={emailForm.setTemplate}
        content={emailForm.content}
        setContent={emailForm.setContent}
        audience={emailForm.audience}
        setAudience={emailForm.setAudience}
        onCreateCampaign={actions.createEmailCampaign}
        onNavigate={handleNavigate}
      />
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
                onClick={() => openModal("copy")}
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
                className="h-8 w-8"
                onClick={() => openModal("schedule")}
                data-testid="quick-schedule"
              >
                {successAction === "schedule" ? (
                  <Check className="h-4 w-4 text-green-500" />
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
                className="h-8 w-8"
                onClick={handleOpenWhatsApp}
                data-testid="quick-whatsapp"
              >
                {successAction === "whatsapp" ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <MessageCircle className="h-4 w-4" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent>Enviar via WhatsApp</TooltipContent>
          </Tooltip>

          {/* Favorite */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => onFavorite?.(product)}
                data-testid="quick-favorite"
              >
                <Heart className={`h-4 w-4 ${isFavorite ? "fill-red-500 text-red-500" : ""}`} />
              </Button>
            </TooltipTrigger>
            <TooltipContent>{isFavorite ? "Remover dos favoritos" : "Adicionar aos favoritos"}</TooltipContent>
          </Tooltip>

          {/* More Actions Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon" className="h-8 w-8">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel>Mais Ações</DropdownMenuLabel>
              <DropdownMenuSeparator />
              
              <DropdownMenuItem onClick={handleOpenInstagram}>
                <Instagram className="h-4 w-4 mr-2" />
                Instagram
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleOpenTikTok}>
                <TikTokIcon />
                <span className="ml-2">TikTok</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleOpenYouTube}>
                <Youtube className="h-4 w-4 mr-2" />
                YouTube
              </DropdownMenuItem>
              
              <DropdownMenuSeparator />
              
              <DropdownMenuItem onClick={handleOpenSellerBot}>
                <Bot className="h-4 w-4 mr-2" />
                Seller Bot
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleOpenCRM}>
                <ShoppingCart className="h-4 w-4 mr-2" />
                Adicionar ao CRM
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleOpenEmail}>
                <Mail className="h-4 w-4 mr-2" />
                Email Marketing
              </DropdownMenuItem>
              
              <DropdownMenuSeparator />
              
              <DropdownMenuItem onClick={actions.copyInfo}>
                <Copy className="h-4 w-4 mr-2" />
                Copiar Informações
              </DropdownMenuItem>
              <DropdownMenuItem onClick={actions.copyLink}>
                <ExternalLink className="h-4 w-4 mr-2" />
                Copiar Link
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => actions.exportProduct("json")}>
                <Download className="h-4 w-4 mr-2" />
                Exportar
              </DropdownMenuItem>
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
    <div className="space-y-4" data-testid="product-actions-panel">
      {/* Header with Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-tiktrend-primary" />
            <h3 className="font-semibold text-lg">Ações Rápidas</h3>
          </div>
          <TabsList className="grid grid-cols-3 h-8">
            <TabsTrigger value="actions" className="text-xs gap-1">
              <Zap className="h-3 w-3" />
              Ações
            </TabsTrigger>
            <TabsTrigger value="favorites" className="text-xs gap-1">
              <Star className="h-3 w-3" />
              Favoritos
            </TabsTrigger>
            <TabsTrigger value="history" className="text-xs gap-1">
              <History className="h-3 w-3" />
              Histórico
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Actions Tab */}
        <TabsContent value="actions" className="space-y-6 mt-0">
          {/* Action Groups */}
          <div className="space-y-6">
            {actionGroups.map((group) => (
              <div key={group.title} className="space-y-3">
                <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                  {group.title}
                </h4>
                <div className="grid gap-2">
                  {group.actions.map((action) => (
                    <div key={action.id} className="relative group/action">
                      <button
                        data-testid={`action-${action.id}`}
                        onClick={action.onClick}
                        disabled={action.disabled}
                        className={`
                          w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all
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
                            : "bg-background text-muted-foreground group-hover/action:text-foreground"
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
                        <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover/action:opacity-100 transition-opacity" />
                      </button>
                      {/* Favorite button */}
                      <div className="absolute right-10 top-1/2 -translate-y-1/2 opacity-0 group-hover/action:opacity-100 transition-opacity">
                        <FavoriteActionButton 
                          actionId={action.id as ActionId}
                          size="sm"
                        />
                      </div>
                    </div>
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
        </TabsContent>

        {/* Favorites Tab */}
        <TabsContent value="favorites" className="mt-0">
          <FavoriteActionsList
            onActionClick={(actionId: ActionId) => {
              // Map actionId to actual function
              const actionMap: Record<ActionId, () => void> = {
                "generate-copy": () => openModal("copy"),
                "schedule": () => openModal("schedule"),
                "whatsapp": handleOpenWhatsApp,
                "instagram": handleOpenInstagram,
                "tiktok": handleOpenTikTok,
                "youtube": handleOpenYouTube,
                "seller-bot": handleOpenSellerBot,
                "crm": handleOpenCRM,
                "email": handleOpenEmail,
                "copy-info": actions.copyInfo,
                "copy-link": actions.copyLink,
                "export": () => actions.exportProduct("json"),
              };
              
              const action = actionMap[actionId];
              if (action) {
                action();
              }
            }}
            maxItems={12}
            showEmpty={true}
          />
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="mt-0">
          <ActionHistory 
            productId={product.id} 
            maxHeight="400px"
            showStats={true}
            showClearButton={true}
          />
        </TabsContent>
      </Tabs>

      {/* Modals for Full Variant */}
      {renderModals()}
    </div>
  );
};

export default ProductActionsPanelRefactored;
