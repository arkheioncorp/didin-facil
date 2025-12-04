import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { useActionHistoryStore } from "@/stores";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import type { Product } from "@/types";
import type {
  CopyType,
  CopyTone,
  SchedulePlatform,
  BotTargetAudience,
  CRMStage,
  EmailTemplate,
  EmailAudience,
  UseProductActionsReturn,
  ActionHistoryType,
} from "./types";

export function useProductActions(
  product: Product
): UseProductActionsReturn {
  const navigate = useNavigate();
  const { toast } = useToast();
  const addHistoryEntry = useActionHistoryStore((state) => state.addEntry);
  
  // ============================================
  // HISTORY HELPER
  // ============================================
  
  const logAction = useCallback((
    actionType: ActionHistoryType,
    success: boolean,
    errorMessage?: string,
    metadata?: Record<string, unknown>
  ) => {
    addHistoryEntry({
      productId: product.id,
      productTitle: product.title,
      actionType,
      success,
      errorMessage,
      metadata,
    });
  }, [product.id, product.title, addHistoryEntry]);
  
  // ============================================
  // LOADING & SUCCESS STATES
  // ============================================
  
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [successAction, setSuccessAction] = useState<string | null>(null);
  
  const showSuccess = useCallback((actionId: string) => {
    setSuccessAction(actionId);
    setTimeout(() => setSuccessAction(null), 2000);
  }, []);
  
  // ============================================
  // MODAL VISIBILITY STATES
  // ============================================
  
  const [modals, setModals] = useState({
    copy: false,
    whatsApp: false,
    schedule: false,
    instagram: false,
    tiktok: false,
    youtube: false,
    sellerBot: false,
    crm: false,
    email: false,
  });
  
  const openModal = useCallback((modal: keyof typeof modals) => {
    setModals(prev => ({ ...prev, [modal]: true }));
  }, []);
  
  const closeModal = useCallback((modal: keyof typeof modals) => {
    setModals(prev => ({ ...prev, [modal]: false }));
  }, []);
  
  // ============================================
  // COPY AI FORM STATES
  // ============================================
  
  const [copyType, setCopyType] = useState<CopyType>("facebook_ad");
  const [copyTone, setCopyTone] = useState<CopyTone>("professional");
  const [generatedCopy, setGeneratedCopy] = useState<string | null>(null);
  
  // ============================================
  // WHATSAPP FORM STATES
  // ============================================
  
  const [whatsAppNumber, setWhatsAppNumber] = useState("");
  const [whatsAppMessage, setWhatsAppMessage] = useState("");
  
  // ============================================
  // SCHEDULE FORM STATES
  // ============================================
  
  const [schedulePlatform, setSchedulePlatform] = useState<SchedulePlatform>("instagram");
  const [scheduleDate, setScheduleDate] = useState("");
  
  // ============================================
  // INSTAGRAM FORM STATES
  // ============================================
  
  const [instagramCaption, setInstagramCaption] = useState("");
  const [instagramHashtags, setInstagramHashtags] = useState("");
  
  // ============================================
  // TIKTOK FORM STATES
  // ============================================
  
  const [tiktokCaption, setTiktokCaption] = useState("");
  const [tiktokSounds, setTiktokSounds] = useState("");
  
  // ============================================
  // YOUTUBE FORM STATES
  // ============================================
  
  const [youtubeTitle, setYoutubeTitle] = useState("");
  const [youtubeDescription, setYoutubeDescription] = useState("");
  
  // ============================================
  // SELLER BOT FORM STATES
  // ============================================
  
  const [botCampaignName, setBotCampaignName] = useState("");
  const [botMessage, setBotMessage] = useState("");
  const [botTargetAudience, setBotTargetAudience] = useState<BotTargetAudience>("all");
  const [botScheduleEnabled, setBotScheduleEnabled] = useState(false);
  
  // ============================================
  // CRM FORM STATES
  // ============================================
  
  const [crmOpportunityTitle, setCrmOpportunityTitle] = useState("");
  const [crmValue, setCrmValue] = useState(0);
  const [crmStage, setCrmStage] = useState<CRMStage>("lead");
  const [crmNotes, setCrmNotes] = useState("");
  
  // ============================================
  // EMAIL FORM STATES
  // ============================================
  
  const [emailSubject, setEmailSubject] = useState("");
  const [emailTemplate, setEmailTemplate] = useState<EmailTemplate>("product_launch");
  const [emailContent, setEmailContent] = useState("");
  const [emailAudience, setEmailAudience] = useState<EmailAudience>("all");
  
  // ============================================
  // PRE-FILL HELPERS
  // ============================================
  
  const prefillInstagram = useCallback(() => {
    setInstagramCaption(`🛍️ ${product.title}\n\n💰 ${formatCurrency(product.price)}\n📦 ${product.salesCount.toLocaleString()} vendas\n\n`);
    setInstagramHashtags("#tiktrend #dropshipping #loja #produto #oferta");
  }, [product]);
  
  const prefillTikTok = useCallback(() => {
    setTiktokCaption(`${product.title} 🔥 ${formatCurrency(product.price)}`);
    setTiktokSounds("");
  }, [product]);
  
  const prefillYouTube = useCallback(() => {
    setYoutubeTitle(`${product.title} - Review e Unboxing`);
    setYoutubeDescription(`🛍️ ${product.title}\n\n💰 Preço: ${formatCurrency(product.price)}\n📦 Vendas: ${product.salesCount.toLocaleString()}\n\n${product.productUrl ? `🔗 Link: ${product.productUrl}` : ""}\n\n#tiktrend #dropshipping #produto`);
  }, [product]);
  
  const prefillSellerBot = useCallback(() => {
    setBotCampaignName(`Campanha - ${product.title}`);
    setBotMessage(`🔥 Oferta Especial!\n\n${product.title}\n\n💰 Apenas ${formatCurrency(product.price)}\n\n📦 Já foram ${product.salesCount.toLocaleString()} vendas!\n\n${product.productUrl || ""}`);
    setBotTargetAudience("all");
    setBotScheduleEnabled(false);
  }, [product]);
  
  const prefillCRM = useCallback(() => {
    setCrmOpportunityTitle(`Lead - ${product.title}`);
    setCrmValue(product.price);
    setCrmStage("lead");
    setCrmNotes(`Produto: ${product.title}\nPreço: ${formatCurrency(product.price)}\nVendas: ${product.salesCount.toLocaleString()}`);
  }, [product]);
  
  const prefillEmail = useCallback(() => {
    setEmailSubject(`🛍️ ${product.title} - Oferta Especial!`);
    setEmailTemplate("product_launch");
    setEmailContent(`Olá!\n\nTemos uma oferta especial para você:\n\n${product.title}\n\n💰 Por apenas ${formatCurrency(product.price)}\n\n${product.description || ""}\n\n🛒 Aproveite agora!\n\n${product.productUrl || ""}`);
    setEmailAudience("all");
  }, [product]);
  
  const prefillWhatsApp = useCallback(() => {
    setWhatsAppMessage(`🛍️ *${product.title}*\n\n💰 Preço: ${formatCurrency(product.price)}\n📦 Vendas: ${product.salesCount.toLocaleString()}\n\n${product.productUrl || ""}`);
  }, [product]);
  
  // ============================================
  // ACTIONS
  // ============================================
  
  const copyInfo = useCallback(async () => {
    try {
      const info = `🛍️ ${product.title}
💰 Preço: ${formatCurrency(product.price)}
📦 Vendas: ${product.salesCount.toLocaleString()}
⭐ Avaliação: ${product.productRating?.toFixed(1) || "N/A"}
🏪 Loja: ${product.sellerName || "TikTok Shop"}
${product.productUrl ? `🔗 Link: ${product.productUrl}` : ""}`;

      await navigator.clipboard.writeText(info);
      toast({ title: "Copiado!", description: "Informações do produto copiadas." });
      showSuccess("copy-info");
      logAction("copy_info", true);
    } catch (error) {
      logAction("copy_info", false, error instanceof Error ? error.message : "Erro ao copiar");
    }
  }, [product, toast, showSuccess, logAction]);
  
  const copyLink = useCallback(async () => {
    try {
      if (product.productUrl) {
        await navigator.clipboard.writeText(product.productUrl);
        toast({ title: "Link copiado!" });
        showSuccess("copy-link");
        logAction("copy_link", true, undefined, { url: product.productUrl });
      } else {
        toast({ title: "Link não disponível", variant: "destructive" });
        logAction("copy_link", false, "Link não disponível");
      }
    } catch (error) {
      logAction("copy_link", false, error instanceof Error ? error.message : "Erro ao copiar");
    }
  }, [product, toast, showSuccess, logAction]);
  
  const generateCopy = useCallback(async () => {
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
      logAction("generate_copy", true, undefined, { copyType, copyTone, creditsRemaining: response.data.credits_remaining });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao gerar copy";
      toast({ title: "Erro", description: message, variant: "destructive" });
      logAction("generate_copy", false, message);
    } finally {
      setIsLoading(null);
    }
  }, [product, copyType, copyTone, toast, logAction]);
  
  const copyGeneratedText = useCallback(async () => {
    if (generatedCopy) {
      await navigator.clipboard.writeText(generatedCopy);
      toast({ title: "Copy copiada!" });
      showSuccess("generate-copy");
    }
  }, [generatedCopy, toast, showSuccess]);
  
  const sendWhatsApp = useCallback(async () => {
    if (!whatsAppNumber || !whatsAppMessage) {
      toast({ title: "Preencha todos os campos", variant: "destructive" });
      return;
    }

    setIsLoading("whatsapp");
    try {
      const instancesResponse = await api.get<{ data: Array<{ name: string }> }>("/whatsapp/instances");
      const instances = instancesResponse.data.data || [];
      
      if (instances.length === 0) {
        toast({ 
          title: "Nenhuma instância configurada",
          description: "Configure uma instância do WhatsApp primeiro",
          variant: "destructive"
        });
        navigate("/whatsapp");
        logAction("whatsapp", false, "Nenhuma instância configurada");
        return;
      }

      await api.post("/whatsapp/messages/text", {
        instance_name: instances[0].name,
        number: whatsAppNumber.replace(/\D/g, ""),
        text: whatsAppMessage,
      });
      
      toast({ title: "Mensagem enviada!", description: "WhatsApp enviado com sucesso" });
      showSuccess("whatsapp");
      closeModal("whatsApp");
      logAction("whatsapp", true, undefined, { phoneNumber: whatsAppNumber.replace(/\D/g, "") });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao enviar";
      toast({ title: "Erro", description: message, variant: "destructive" });
      logAction("whatsapp", false, message);
    } finally {
      setIsLoading(null);
    }
  }, [whatsAppNumber, whatsAppMessage, navigate, toast, showSuccess, closeModal, logAction]);
  
  const submitSchedule = useCallback(async () => {
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
      closeModal("schedule");
      logAction("schedule", true, undefined, { platform: schedulePlatform, scheduledTime: scheduleDate });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao agendar";
      toast({ title: "Erro", description: message, variant: "destructive" });
      logAction("schedule", false, message);
    } finally {
      setIsLoading(null);
    }
  }, [product, schedulePlatform, scheduleDate, toast, showSuccess, closeModal, logAction]);
  
  const postInstagram = useCallback(async () => {
    setIsLoading("instagram");
    try {
      await api.post("/instagram/upload", {
        product_id: product.id,
        caption: instagramCaption,
        hashtags: instagramHashtags.split(/[\s,]+/).filter(h => h.startsWith("#")),
        image_url: product.imageUrl,
        post_type: "feed",
      });
      
      toast({ title: "Publicado no Instagram!", description: "Post criado com sucesso" });
      showSuccess("instagram");
      closeModal("instagram");
      logAction("instagram", true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao publicar";
      toast({ title: "Erro", description: message, variant: "destructive" });
      logAction("instagram", false, message);
    } finally {
      setIsLoading(null);
    }
  }, [product, instagramCaption, instagramHashtags, toast, showSuccess, closeModal, logAction]);
  
  const postTikTok = useCallback(async () => {
    setIsLoading("tiktok");
    try {
      await api.post("/tiktok/upload", {
        product_id: product.id,
        caption: tiktokCaption,
        video_url: product.videoUrl || product.imageUrl,
        sounds: tiktokSounds ? tiktokSounds.split(",").map(s => s.trim()) : [],
      });
      
      toast({ title: "Publicado no TikTok!", description: "Vídeo criado com sucesso" });
      showSuccess("tiktok");
      closeModal("tiktok");
      logAction("tiktok", true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao publicar";
      toast({ title: "Erro", description: message, variant: "destructive" });
      logAction("tiktok", false, message);
    } finally {
      setIsLoading(null);
    }
  }, [product, tiktokCaption, tiktokSounds, toast, showSuccess, closeModal, logAction]);
  
  const uploadYouTube = useCallback(async () => {
    setIsLoading("youtube");
    try {
      await api.post("/youtube/upload", {
        product_id: product.id,
        title: youtubeTitle,
        description: youtubeDescription,
        video_url: product.videoUrl || product.imageUrl,
        privacy: "public",
        category: "22",
      });
      
      toast({ title: "Enviado para o YouTube!", description: "Vídeo em processamento" });
      showSuccess("youtube");
      closeModal("youtube");
      logAction("youtube", true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao enviar";
      toast({ title: "Erro", description: message, variant: "destructive" });
      logAction("youtube", false, message);
    } finally {
      setIsLoading(null);
    }
  }, [product, youtubeTitle, youtubeDescription, toast, showSuccess, closeModal, logAction]);
  
  const createBotCampaign = useCallback(async () => {
    setIsLoading("seller-bot");
    try {
      // Criar campanha usando o endpoint de campaigns com configuração para seller bot
      await api.post("/campaigns", {
        name: botCampaignName,
        subject: `Campanha Seller Bot: ${product.title}`,
        content: botMessage,
        type: "whatsapp",
        metadata: {
          target_audience: botTargetAudience,
          schedule_enabled: botScheduleEnabled,
          product_id: product.id,
          product_data: {
            title: product.title,
            price: product.price,
            image_url: product.imageUrl,
            product_url: product.productUrl,
          }
        }
      });
      
      toast({ title: "Campanha criada!", description: "Seller Bot configurado com sucesso" });
      showSuccess("seller-bot");
      closeModal("sellerBot");
      logAction("seller_bot", true, undefined, { campaignName: botCampaignName, targetAudience: botTargetAudience });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao criar campanha";
      toast({ title: "Erro", description: message, variant: "destructive" });
      logAction("seller_bot", false, message);
    } finally {
      setIsLoading(null);
    }
  }, [product, botCampaignName, botMessage, botTargetAudience, botScheduleEnabled, toast, showSuccess, closeModal, logAction]);
  
  const createCRMOpportunity = useCallback(async () => {
    setIsLoading("crm");
    try {
      await api.post("/crm/leads", {
        name: crmOpportunityTitle,
        expected_value: crmValue,
        status: crmStage === "negotiation" ? "qualified" : crmStage === "won" ? "converted" : "new",
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
      closeModal("crm");
      logAction("crm", true, undefined, { opportunityTitle: crmOpportunityTitle, stage: crmStage, value: crmValue });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao criar oportunidade";
      toast({ title: "Erro", description: message, variant: "destructive" });
      logAction("crm", false, message);
    } finally {
      setIsLoading(null);
    }
  }, [product, crmOpportunityTitle, crmValue, crmStage, crmNotes, toast, showSuccess, closeModal, logAction]);
  
  const createEmailCampaign = useCallback(async () => {
    setIsLoading("email");
    try {
      await api.post("/campaigns", {
        name: emailSubject,
        subject: emailSubject,
        type: "email",
        template: emailTemplate,
        content: emailContent,
        metadata: {
          audience: emailAudience,
          product_id: product.id,
          product_data: {
            title: product.title,
            price: product.price,
            image_url: product.imageUrl,
            product_url: product.productUrl,
          }
        }
      });
      
      toast({ title: "Campanha criada!", description: "Email marketing configurado" });
      showSuccess("email");
      closeModal("email");
      logAction("email", true, undefined, { subject: emailSubject, template: emailTemplate, audience: emailAudience });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao criar campanha";
      toast({ title: "Erro", description: message, variant: "destructive" });
      logAction("email", false, message);
    } finally {
      setIsLoading(null);
    }
  }, [product, emailSubject, emailTemplate, emailContent, emailAudience, toast, showSuccess, closeModal, logAction]);
  
  const exportProduct = useCallback(async (format: "csv" | "json") => {
    setIsLoading("export");
    try {
      const response = await api.post("/products/export", {
        product_ids: [product.id],
        format,
      });
      
      const blob = new Blob([JSON.stringify(response.data)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `produto-${product.id}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast({ title: `Exportado como ${format.toUpperCase()}!` });
      logAction("export", true, undefined, { format });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Erro ao exportar";
      toast({ title: "Erro ao exportar", variant: "destructive" });
      logAction("export", false, message);
    } finally {
      setIsLoading(null);
    }
  }, [product, toast, logAction]);
  
  // ============================================
  // RETURN
  // ============================================
  
  return {
    isLoading,
    successAction,
    modals,
    openModal,
    closeModal,
    
    copyForm: {
      type: copyType,
      setType: setCopyType,
      tone: copyTone,
      setTone: setCopyTone,
      generatedCopy,
    },
    
    whatsAppForm: {
      phoneNumber: whatsAppNumber,
      setPhoneNumber: setWhatsAppNumber,
      message: whatsAppMessage,
      setMessage: setWhatsAppMessage,
    },
    
    scheduleForm: {
      platform: schedulePlatform,
      setPlatform: setSchedulePlatform,
      date: scheduleDate,
      setDate: setScheduleDate,
    },
    
    instagramForm: {
      caption: instagramCaption,
      setCaption: setInstagramCaption,
      hashtags: instagramHashtags,
      setHashtags: setInstagramHashtags,
    },
    
    tiktokForm: {
      caption: tiktokCaption,
      setCaption: setTiktokCaption,
      sounds: tiktokSounds,
      setSounds: setTiktokSounds,
    },
    
    youtubeForm: {
      title: youtubeTitle,
      setTitle: setYoutubeTitle,
      description: youtubeDescription,
      setDescription: setYoutubeDescription,
    },
    
    sellerBotForm: {
      campaignName: botCampaignName,
      setCampaignName: setBotCampaignName,
      message: botMessage,
      setMessage: setBotMessage,
      targetAudience: botTargetAudience,
      setTargetAudience: setBotTargetAudience,
      scheduleEnabled: botScheduleEnabled,
      setScheduleEnabled: setBotScheduleEnabled,
    },
    
    crmForm: {
      opportunityTitle: crmOpportunityTitle,
      setOpportunityTitle: setCrmOpportunityTitle,
      value: crmValue,
      setValue: setCrmValue,
      stage: crmStage,
      setStage: setCrmStage,
      notes: crmNotes,
      setNotes: setCrmNotes,
    },
    
    emailForm: {
      subject: emailSubject,
      setSubject: setEmailSubject,
      template: emailTemplate,
      setTemplate: setEmailTemplate,
      content: emailContent,
      setContent: setEmailContent,
      audience: emailAudience,
      setAudience: setEmailAudience,
    },
    
    actions: {
      copyInfo,
      copyLink,
      generateCopy,
      copyGeneratedText,
      sendWhatsApp,
      submitSchedule,
      postInstagram,
      postTikTok,
      uploadYouTube,
      createBotCampaign,
      createCRMOpportunity,
      createEmailCampaign,
      exportProduct,
    },
    
    prefill: {
      instagram: prefillInstagram,
      tiktok: prefillTikTok,
      youtube: prefillYouTube,
      sellerBot: prefillSellerBot,
      crm: prefillCRM,
      email: prefillEmail,
      whatsApp: prefillWhatsApp,
    },
  };
}
