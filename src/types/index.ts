// Product types
export interface Product {
  id: string;
  tiktokId: string;
  title: string;
  description: string | null;
  price: number;
  originalPrice: number | null;
  currency: string;
  category: string | null;
  subcategory: string | null;
  sellerName: string | null;
  sellerRating: number | null;
  productRating: number | null;
  reviewsCount: number;
  salesCount: number;
  sales7d: number;
  sales30d: number;
  commissionRate: number | null;
  imageUrl: string | null;
  images: string[];
  videoUrl: string | null;
  productUrl: string;
  affiliateUrl: string | null;
  hasFreeShipping: boolean;
  isTrending: boolean;
  isOnSale: boolean;
  inStock: boolean;
  stockLevel?: number | null;
  collectedAt: string;
  updatedAt: string;
}

export interface ProductHistory {
  id: string;
  productId: string;
  price: number;
  salesCount: number;
  stockLevel: number | null;
  collectedAt: string;
}

// Filter types
export interface ProductFilters {
  query: string;
  categories: string[];
  priceRange: {
    min: number | null;
    max: number | null;
  };
  salesRange: {
    min: number | null;
    max: number | null;
  };
  minRating: number | null;
  flags: {
    freeShipping: boolean | null;
    trending: boolean | null;
    onSale: boolean | null;
    inStock: boolean | null;
  };
  sort: SortOption;
}

export type SortOption =
  | "trending"
  | "sales"
  | "price_asc"
  | "price_desc"
  | "rating"
  | "recent";

// Favorite types
export interface FavoriteList {
  id: string;
  name: string;
  description: string | null;
  color: string;
  icon: string;
  productCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface FavoriteItem {
  id: string;
  listId: string;
  productId: string;
  notes: string | null;
  addedAt: string;
  product?: Product;
}

// Copy types
export interface CopyHistory {
  id: string;
  productId: string | null;
  productTitle?: string;
  copyType: CopyType;
  tone: CopyTone;
  copyText: string;
  createdAt: string;
  product?: Product;
}

export type CopyType =
  | "facebook_ad"
  | "tiktok_hook"
  | "product_description"
  | "story_reels"
  | "email"
  | "whatsapp"
  | "email_sequence"
  | "landing_page";

export type CopyTone =
  | "urgent"
  | "educational"
  | "casual"
  | "professional"
  | "emotional"
  | "authority"
  | "persuasive"
  | "friendly"
  | "humorous";

export interface CopyRequest {
  productId: string;
  productTitle: string;
  productDescription?: string;
  productPrice: number;
  productBenefits?: string[];
  copyType: CopyType;
  tone: CopyTone;
  platform: string;
  language: string;
  maxLength?: number;
  includeEmoji?: boolean;
  includeHashtags?: boolean;
  customInstructions?: string;
}

export interface CopyResponse {
  id: string;
  copyText: string;
  copyType: string;
  tone: string;
  platform: string;
  wordCount: number;
  characterCount: number;
  createdAt: string;
  cached: boolean;
  creditsUsed: number;
  creditsRemaining: number;
}

// User types
export interface User {
  id: string;
  email: string;
  name: string | null;
  avatarUrl: string | null;
  phone: string | null;
  // License status
  hasLifetimeLicense: boolean;
  licenseActivatedAt: string | null;
  // Account status
  isActive: boolean;
  isEmailVerified: boolean;
  // Preferences
  language: string;
  timezone: string;
  // Metadata
  createdAt: string;
  updatedAt: string | null;
  lastLoginAt: string | null;
}

export interface License {
  id: string | null;
  isValid: boolean;
  isLifetime: boolean;
  plan: LicensePlan;
  activatedAt: string | null;
  expiresAt: string | null;
  maxDevices: number;
  activeDevices: number;
  // Device binding
  currentDeviceId: string | null;
  isCurrentDeviceAuthorized: boolean;
}

export type LicensePlan = 'free' | 'lifetime' | 'trial';

// ============================================
// SUBSCRIPTION TYPES (SaaS Híbrido)
// ============================================

export type PlanTier = 'free' | 'starter' | 'business' | 'enterprise';
export type BillingCycle = 'monthly' | 'yearly';
export type ExecutionMode = 'web_only' | 'hybrid' | 'local_first';
export type SubscriptionStatus = 'active' | 'trialing' | 'past_due' | 'canceled' | 'expired';
export type MarketplaceAccess = 'tiktok' | 'shopee' | 'amazon' | 'mercado_livre' | 'hotmart' | 'aliexpress';

export interface Subscription {
  id: string;
  plan: PlanTier;
  status: SubscriptionStatus;
  billingCycle: BillingCycle;
  executionMode: ExecutionMode;
  currentPeriodStart: string;
  currentPeriodEnd: string;
  marketplaces: MarketplaceAccess[];
  limits: Record<string, number>;
  features: Record<string, boolean>;
}

export interface PlanInfo {
  tier: PlanTier;
  name: string;
  description: string;
  priceMonthly: number;
  priceYearly: number;
  executionModes: ExecutionMode[];
  marketplaces: MarketplaceAccess[];
  scraperPriority: string;
  limits: Record<string, number>;
  features: Record<string, boolean>;
  highlights: string[];
  offlineDays: number;
}

export interface UsageStats {
  feature: string;
  current: number;
  limit: number;
  percentage: number;
  isUnlimited: boolean;
  resetsAt: string;
}

export interface SubscriptionWithPlan {
  subscription: Subscription;
  plan: PlanInfo;
  usage: UsageStats[];
}

// ============================================

export interface Credits {
  balance: number;
  totalPurchased: number;
  totalUsed: number;
  lastPurchaseAt: string | null;
  // Bonus credits
  bonusBalance: number;
  bonusExpiresAt: string | null;
}

export interface UserState {
  user: User | null;
  license: License | null;
  credits: Credits | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Legacy types for backward compatibility
export interface LegacyLicense {
  isValid: boolean;
  plan: "trial" | "basic" | "pro" | "lifetime";
  features: PlanFeatures;
  expiresAt: string;
  usageThisMonth: {
    searches: number;
    copies: number;
  };
}


export interface PlanFeatures {
  searchesPerMonth: number;
  copiesPerMonth: number;
  favoriteLists: number;
  exportEnabled: boolean;
  schedulerEnabled: boolean;
}

// Search history
export interface SearchHistory {
  id: string;
  query: string;
  filters: ProductFilters;
  resultsCount: number;
  searchedAt: string;
}

// Filter preset
export interface FilterPreset {
  id: string;
  name: string;
  filters: ProductFilters;
  usageCount: number;
  createdAt: string;
}

// Settings
export interface CredentialsConfig {
  openaiKey: string;
  proxies: string[];
}

export interface ScraperConfig {
  maxProducts: number;
  intervalMinutes: number;
  categories: string[];
  useProxy: boolean;
  headless: boolean;
  timeout: number;
}

export interface LicenseConfig {
  key: string | null;
  plan: LicensePlan;
  expiresAt: string | null; // null = lifetime (never expires)
  trialStarted: string | null;
  isActive: boolean;
  credits: number; // Créditos IA disponíveis
}

export interface SystemConfig {
  autoUpdate: boolean;
  checkInterval: number;
  logsEnabled: boolean;
  maxLogSize: number;
  analyticsEnabled: boolean;
  // API Configurations
  evolutionApiUrl?: string;
  evolutionApiKey?: string;
  youtubeCredentialsPath?: string;
  tiktokDataDir?: string;
}

export interface AppSettings {
  theme: "light" | "dark" | "system";
  language: string;
  notificationsEnabled: boolean;
  autoUpdate: boolean;
  maxProductsPerSearch: number;
  cacheImages: boolean;
  proxyEnabled: boolean;
  proxyList: string[];
  openaiModel: string;
  defaultCopyType: CopyType;
  defaultCopyTone: CopyTone;
  
  // Setup & Onboarding
  setupComplete: boolean;
  termsAccepted: boolean;
  termsAcceptedAt: string | null;
  
  credentials: CredentialsConfig;
  scraper: ScraperConfig;
  license: LicenseConfig;
  system: SystemConfig;
}

// API response types
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// Scraper types
export interface ScraperStatus {
  isRunning: boolean;
  progress: number;
  currentProduct: string | null;
  productsFound: number;
  errors: string[];
  logs: string[];
  startedAt: string | null;
  statusMessage: string | null;
}

export interface CollectionLog {
  id: string;
  status: "running" | "completed" | "failed" | "cancelled";
  productsFound: number;
  productsSaved: number;
  errorsCount: number;
  durationMs: number;
  startedAt: string;
  completedAt: string | null;
}

// Search configuration
export interface SearchFilters {
  query?: string;
  categories: string[];
  priceMin?: number;
  priceMax?: number;
  salesMin?: number;
  ratingMin?: number;
  hasFreeShipping?: boolean;
  isTrending?: boolean;
  isOnSale?: boolean;
  sortBy: SortOption;
  sortOrder: "asc" | "desc";
  page?: number;
  pageSize?: number;
}

export interface SearchConfig {
  maxResults: number;
  includeImages: boolean;
  includeDescription: boolean;
  includeMetrics: boolean;
  autoSave: boolean;
  refreshInterval: number;
}

// Dashboard stats
export interface DashboardStats {
  totalProducts: number;
  trendingProducts: number;
  favoriteCount: number;
  searchesToday: number;
  copiesGenerated: number;
  topCategories: { name: string; count: number }[];
}

// Notification types
export interface AppNotification {
  id: string;
  type: "success" | "error" | "warning" | "info";
  title: string;
  message: string;
  duration?: number;
  createdAt: string;
}

// Search History types
export interface SearchHistoryItem {
  id: string;
  userId: string;
  query: string;
  filters: string; // JSON string
  resultsCount: number;
  searchedAt: string;
}

// Settings types
export interface Setting {
  key: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  value: any;
  category: string;
  updatedAt: string;
}

// Extended types
export interface FavoriteWithProduct {
  favorite: FavoriteItem;
  product: Product;
}

// Subscription Types (SaaS Hybrid)
export type PlanTier = 'free' | 'starter' | 'business' | 'enterprise';
export type BillingCycle = 'monthly' | 'yearly';
export type SubscriptionStatus = 'active' | 'past_due' | 'canceled' | 'incomplete' | 'incomplete_expired' | 'trialing' | 'unpaid';
export type ExecutionMode = 'web_only' | 'local_only' | 'hybrid';

export interface Subscription {
  id: string;
  plan: PlanTier;
  status: SubscriptionStatus;
  billingCycle: BillingCycle;
  executionMode: ExecutionMode;
  currentPeriodStart: string;
  currentPeriodEnd: string;
  canceledAt?: string | null;
  marketplaces: string[];
  limits: Record<string, number>;
  features: Record<string, boolean>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  metadata?: Record<string, any>;
}

export interface PlanInfo {
  tier: PlanTier;
  name: string;
  description: string;
  priceMonthly: number;
  priceYearly: number;
  features: Record<string, boolean>;
  limits: Record<string, number>;
  executionModes: ExecutionMode[];
  marketplaces: string[];
}

export interface UsageStats {
  feature: string;
  current: number;
  limit: number;
  percentage: number;
  isUnlimited: boolean;
  resetsAt?: string;
}
