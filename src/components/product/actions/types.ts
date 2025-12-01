import type { Product } from "@/types";
import type { ReactNode } from "react";

// ============================================
// CORE TYPES
// ============================================

export type ActionId = 
  | "generate-copy"
  | "schedule"
  | "whatsapp"
  | "instagram"
  | "tiktok"
  | "youtube"
  | "seller-bot"
  | "crm"
  | "email"
  | "copy-info"
  | "copy-link"
  | "export";

export interface ProductActionsPanelProps {
  product: Product;
  isFavorite?: boolean;
  onFavorite?: (product: Product) => void;
  onClose?: () => void;
  variant?: "full" | "compact";
}

export interface ActionItem {
  id: string;
  label: string;
  description: string;
  icon: ReactNode;
  onClick: () => void;
  variant?: "default" | "primary" | "secondary";
  badge?: string;
  disabled?: boolean;
}

export interface ActionGroup {
  title: string;
  actions: ActionItem[];
}

// ============================================
// MODAL PROPS BASE
// ============================================

export interface BaseModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product;
  isLoading: boolean;
  onNavigate: (path: string) => void;
  onClose?: () => void;
}

// ============================================
// COPY AI TYPES
// ============================================

export type CopyType = "ad" | "description" | "headline" | "cta" | "story" | "whatsapp";
export type CopyTone = "professional" | "casual" | "urgent" | "friendly" | "luxury" | "emotional";

export interface CopyModalProps extends BaseModalProps {
  copyType: CopyType;
  setCopyType: (type: CopyType) => void;
  copyTone: CopyTone;
  setCopyTone: (tone: CopyTone) => void;
  generatedCopy: string | null;
  onGenerate: () => Promise<void>;
  onCopyText: () => Promise<void>;
}

// ============================================
// WHATSAPP TYPES
// ============================================

export interface WhatsAppModalProps extends BaseModalProps {
  phoneNumber: string;
  setPhoneNumber: (number: string) => void;
  message: string;
  setMessage: (message: string) => void;
  onSend: () => Promise<void>;
}

// ============================================
// SCHEDULE TYPES
// ============================================

export type SchedulePlatform = "instagram" | "tiktok" | "youtube" | "whatsapp";

export interface ScheduleModalProps extends BaseModalProps {
  platform: SchedulePlatform;
  setPlatform: (platform: SchedulePlatform) => void;
  scheduleDate: string;
  setScheduleDate: (date: string) => void;
  onSchedule: () => Promise<void>;
}

// ============================================
// INSTAGRAM TYPES
// ============================================

export interface InstagramModalProps extends BaseModalProps {
  caption: string;
  setCaption: (caption: string) => void;
  hashtags: string;
  setHashtags: (hashtags: string) => void;
  onPost: () => Promise<void>;
}

// ============================================
// TIKTOK TYPES
// ============================================

export interface TikTokModalProps extends BaseModalProps {
  caption: string;
  setCaption: (caption: string) => void;
  sounds: string;
  setSounds: (sounds: string) => void;
  onPost: () => Promise<void>;
}

// ============================================
// YOUTUBE TYPES
// ============================================

export interface YouTubeModalProps extends BaseModalProps {
  title: string;
  setTitle: (title: string) => void;
  description: string;
  setDescription: (description: string) => void;
  onUpload: () => Promise<void>;
}

// ============================================
// SELLER BOT TYPES
// ============================================

export type BotTargetAudience = "all" | "leads" | "customers" | "inactive" | "engaged";

export interface SellerBotModalProps extends BaseModalProps {
  campaignName: string;
  setCampaignName: (name: string) => void;
  message: string;
  setMessage: (message: string) => void;
  targetAudience: BotTargetAudience;
  setTargetAudience: (audience: BotTargetAudience) => void;
  scheduleEnabled: boolean;
  setScheduleEnabled: (enabled: boolean) => void;
  onCreateCampaign: () => Promise<void>;
}

// ============================================
// CRM TYPES
// ============================================

export type CRMStage = "lead" | "qualified" | "proposal" | "negotiation" | "won";

export interface CRMModalProps extends BaseModalProps {
  opportunityTitle: string;
  setOpportunityTitle: (title: string) => void;
  value: number;
  setValue: (value: number) => void;
  stage: CRMStage;
  setStage: (stage: CRMStage) => void;
  notes: string;
  setNotes: (notes: string) => void;
  onCreateOpportunity: () => Promise<void>;
}

// ============================================
// EMAIL TYPES
// ============================================

export type EmailTemplate = "product_launch" | "promotion" | "newsletter" | "follow_up" | "custom";
export type EmailAudience = "all" | "subscribers" | "customers" | "leads" | "vip";

export interface EmailModalProps extends BaseModalProps {
  subject: string;
  setSubject: (subject: string) => void;
  template: EmailTemplate;
  setTemplate: (template: EmailTemplate) => void;
  content: string;
  setContent: (content: string) => void;
  audience: EmailAudience;
  setAudience: (audience: EmailAudience) => void;
  onCreateCampaign: () => Promise<void>;
}

// ============================================
// HOOK RETURN TYPES
// ============================================

export interface UseProductActionsReturn {
  // Loading states
  isLoading: string | null;
  successAction: string | null;
  
  // Modal visibility
  modals: {
    copy: boolean;
    whatsApp: boolean;
    schedule: boolean;
    instagram: boolean;
    tiktok: boolean;
    youtube: boolean;
    sellerBot: boolean;
    crm: boolean;
    email: boolean;
  };
  
  // Modal controls
  openModal: (modal: keyof UseProductActionsReturn['modals']) => void;
  closeModal: (modal: keyof UseProductActionsReturn['modals']) => void;
  
  // Form states (grouped by modal)
  copyForm: {
    type: CopyType;
    setType: (type: CopyType) => void;
    tone: CopyTone;
    setTone: (tone: CopyTone) => void;
    generatedCopy: string | null;
  };
  
  whatsAppForm: {
    phoneNumber: string;
    setPhoneNumber: (number: string) => void;
    message: string;
    setMessage: (message: string) => void;
  };
  
  scheduleForm: {
    platform: SchedulePlatform;
    setPlatform: (platform: SchedulePlatform) => void;
    date: string;
    setDate: (date: string) => void;
  };
  
  instagramForm: {
    caption: string;
    setCaption: (caption: string) => void;
    hashtags: string;
    setHashtags: (hashtags: string) => void;
  };
  
  tiktokForm: {
    caption: string;
    setCaption: (caption: string) => void;
    sounds: string;
    setSounds: (sounds: string) => void;
  };
  
  youtubeForm: {
    title: string;
    setTitle: (title: string) => void;
    description: string;
    setDescription: (description: string) => void;
  };
  
  sellerBotForm: {
    campaignName: string;
    setCampaignName: (name: string) => void;
    message: string;
    setMessage: (message: string) => void;
    targetAudience: BotTargetAudience;
    setTargetAudience: (audience: BotTargetAudience) => void;
    scheduleEnabled: boolean;
    setScheduleEnabled: (enabled: boolean) => void;
  };
  
  crmForm: {
    opportunityTitle: string;
    setOpportunityTitle: (title: string) => void;
    value: number;
    setValue: (value: number) => void;
    stage: CRMStage;
    setStage: (stage: CRMStage) => void;
    notes: string;
    setNotes: (notes: string) => void;
  };
  
  emailForm: {
    subject: string;
    setSubject: (subject: string) => void;
    template: EmailTemplate;
    setTemplate: (template: EmailTemplate) => void;
    content: string;
    setContent: (content: string) => void;
    audience: EmailAudience;
    setAudience: (audience: EmailAudience) => void;
  };
  
  // Actions
  actions: {
    copyInfo: () => Promise<void>;
    copyLink: () => Promise<void>;
    generateCopy: () => Promise<void>;
    copyGeneratedText: () => Promise<void>;
    sendWhatsApp: () => Promise<void>;
    submitSchedule: () => Promise<void>;
    postInstagram: () => Promise<void>;
    postTikTok: () => Promise<void>;
    uploadYouTube: () => Promise<void>;
    createBotCampaign: () => Promise<void>;
    createCRMOpportunity: () => Promise<void>;
    createEmailCampaign: () => Promise<void>;
    exportProduct: (format: "csv" | "json") => Promise<void>;
  };
  
  // Pre-fill helpers
  prefill: {
    instagram: () => void;
    tiktok: () => void;
    youtube: () => void;
    sellerBot: () => void;
    crm: () => void;
    email: () => void;
    whatsApp: () => void;
  };
}

// ============================================
// ACTION HISTORY TYPES
// ============================================

export type ActionHistoryType = 
  | "copy_info" 
  | "copy_link" 
  | "generate_copy" 
  | "whatsapp" 
  | "schedule" 
  | "instagram" 
  | "tiktok" 
  | "youtube" 
  | "seller_bot" 
  | "crm" 
  | "email"
  | "export";

export interface ActionHistoryEntry {
  id: string;
  productId: string;
  productTitle: string;
  actionType: ActionHistoryType;
  actionLabel: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
  success: boolean;
  errorMessage?: string;
}

export interface ActionHistoryState {
  entries: ActionHistoryEntry[];
  addEntry: (entry: Omit<ActionHistoryEntry, "id" | "timestamp">) => void;
  clearHistory: () => void;
  getHistoryByProduct: (productId: string) => ActionHistoryEntry[];
  getRecentHistory: (limit?: number) => ActionHistoryEntry[];
}
