// Application constants
export const APP_NAME = "TikTrend Finder";
export const APP_VERSION = "1.0.0";

// API endpoints
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const LICENSE_SERVER_URL = import.meta.env.VITE_LICENSE_URL || "http://localhost:8000";

// WhatsApp / Evolution API
export const EVOLUTION_API_URL = import.meta.env.VITE_EVOLUTION_API_URL || "http://localhost:8082";
export const EVOLUTION_API_KEY = import.meta.env.VITE_EVOLUTION_API_KEY || "429683C4C977415CAAFCCE10F7D57E11";
export const EVOLUTION_INSTANCE = import.meta.env.VITE_EVOLUTION_INSTANCE || "tiktrend-whatsapp";

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

// Limits
export const MAX_FAVORITE_LISTS = 20;
export const MAX_FILTER_PRESETS = 10;
export const MAX_SEARCH_HISTORY = 100;
export const MAX_COPY_HISTORY = 100;

// License and Credits
// Note: License is now included with any credit purchase
export const LICENSE_PRICE = 0; 

export const CREDIT_PACKS = {
  starter: {
    name: "Starter",
    credits: 50,
    price: 19.90,
    pricePerCredit: 0.40,
    description: "Ideal para começar. Inclui licença vitalícia.",
    badge: null,
  },
  pro: {
    name: "Pro",
    credits: 200,
    price: 49.90,
    pricePerCredit: 0.25,
    description: "Para criadores ativos. Melhor custo-benefício.",
    badge: "Mais Popular",
  },
  ultra: {
    name: "Ultra",
    credits: 500,
    price: 99.90,
    pricePerCredit: 0.20,
    description: "Para agências e power users.",
    badge: "Melhor Valor",
  },
} as const;

// Legacy combos removed - all packs now include license
export const COMBO_PACKS = {} as const;

// Credit costs per action
export const CREDIT_COSTS = {
  copy: 1,           // 1 crédito por copy gerada
  trendAnalysis: 2,  // 2 créditos por análise de tendência
  nicheReport: 5,    // 5 créditos por relatório de nicho
} as const;

// Features included in lifetime license (no limits)
export const LIFETIME_FEATURES = {
  unlimitedSearches: true,
  multiSource: true,       // TikTok Shop, AliExpress
  advancedFilters: true,
  unlimitedFavorites: true,
  exportAll: true,         // CSV, Excel, JSON
  freeUpdates: true,
  maxDevices: 2,
} as const;

// Legacy PLANS constant for backward compatibility
export const PLANS = {
  lifetime: {
    name: "Licença Vitalícia",
    price: LICENSE_PRICE,
    duration: -1, // lifetime (never expires)
    features: {
      searchesPerMonth: -1, // unlimited
      copiesPerMonth: 0,    // uses credits
      favoriteLists: -1,    // unlimited
      exportEnabled: true,
      schedulerEnabled: true,
    },
  },
  // Deprecated plans - kept for migration
  trial: {
    name: "Trial",
    price: 0,
    duration: 7,
    features: {
      searchesPerMonth: 10,
      copiesPerMonth: 5,
      favoriteLists: 2,
      exportEnabled: false,
      schedulerEnabled: false,
    },
  },
  basic: {
    name: "Básico",
    price: 10,
    duration: 30,
    features: {
      searchesPerMonth: 100,
      copiesPerMonth: 50,
      favoriteLists: 5,
      exportEnabled: true,
      schedulerEnabled: false,
    },
  },
  pro: {
    name: "Pro",
    price: 29,
    duration: 30,
    features: {
      searchesPerMonth: -1,
      copiesPerMonth: -1,
      favoriteLists: -1,
      exportEnabled: true,
      schedulerEnabled: true,
    },
  },
} as const;

// Categories
export const CATEGORIES = [
  { id: "beauty", name: "Beleza", icon: "✨", slug: "beauty" },
  { id: "fashion", name: "Moda", icon: "👗", slug: "fashion" },
  { id: "home", name: "Casa", icon: "🏠", slug: "home" },
  { id: "electronics", name: "Eletrônicos", icon: "📱", slug: "electronics" },
  { id: "health", name: "Saúde", icon: "💪", slug: "health" },
  { id: "sports", name: "Esportes", icon: "⚽", slug: "sports" },
  { id: "toys", name: "Brinquedos", icon: "🎮", slug: "toys" },
  { id: "pet", name: "Pet Shop", icon: "🐾", slug: "pet" },
  { id: "baby", name: "Bebê", icon: "👶", slug: "baby" },
  { id: "auto", name: "Automotivo", icon: "🚗", slug: "auto" },
] as const;

// Product categories (for search filters) - labels MUST match database values
export const PRODUCT_CATEGORIES = [
  { id: "beauty", label: "Beleza & Skincare", icon: "✨" },
  { id: "fashion", label: "Moda & Acessórios", icon: "👗" },
  { id: "electronics", label: "Eletrônicos", icon: "📱" },
  { id: "home", label: "Casa & Decorações", icon: "🏠" },
  { id: "health", label: "Saúde & Fitness", icon: "💪" },
  { id: "sports", label: "Esportes", icon: "⚽" },
  { id: "toys", label: "Brinquedos & Games", icon: "🎮" },
  { id: "pet", label: "Pet Shop", icon: "🐾" },
  { id: "baby", label: "Bebê & Kids", icon: "👶" },
  { id: "auto", label: "Automotivo", icon: "🚗" },
  { id: "jewelry", label: "Joias & Bijuterias", icon: "💎" },
  { id: "office", label: "Escritório", icon: "💼" },
  { id: "gadgets", label: "Gadgets", icon: "🔌" },
  { id: "outdoor", label: "Outdoor & Camping", icon: "⛺" },
  { id: "kitchen", label: "Cozinha", icon: "🍳" },
  { id: "tools", label: "Ferramentas", icon: "🔧" },
  { id: "garden", label: "Jardim", icon: "🌱" },
  { id: "other", label: "Outros", icon: "📦" },
] as const;

// Map category ID to database value
export const CATEGORY_ID_TO_DB: Record<string, string> = {
  beauty: "Beleza & Skincare",
  fashion: "Moda & Acessórios",
  electronics: "Eletrônicos",
  home: "Casa & Decorações",
  health: "Saúde & Fitness",
  sports: "Esportes",
  toys: "Brinquedos & Games",
  pet: "Pet Shop",
  baby: "Bebê & Kids",
  auto: "Automotivo",
  jewelry: "Joias & Bijuterias",
  office: "Escritório",
  gadgets: "Gadgets",
  outdoor: "Outdoor & Camping",
  kitchen: "Cozinha",
  tools: "Ferramentas",
  garden: "Jardim",
  other: "Outros",
};

// Copy types
export const COPY_TYPES = [
  { id: "facebook_ad", name: "Anúncio Facebook/Instagram", icon: "📢" },
  { id: "tiktok_hook", name: "Hook TikTok", icon: "🎵" },
  { id: "product_description", name: "Descrição de Produto", icon: "📝" },
  { id: "story_reels", name: "Story/Reels", icon: "📸" },
  { id: "email", name: "Email Marketing", icon: "📧" },
  { id: "whatsapp", name: "WhatsApp", icon: "💬" },
] as const;

// Copy tones
export const COPY_TONES = [
  { id: "urgent", name: "Urgente/Escassez", icon: "🔥" },
  { id: "educational", name: "Educativo", icon: "💡" },
  { id: "casual", name: "Descontraído", icon: "😄" },
  { id: "professional", name: "Profissional", icon: "👔" },
  { id: "emotional", name: "Emocional", icon: "💖" },
  { id: "authority", name: "Autoridade", icon: "🏆" },
] as const;

// Sort options
export const SORT_OPTIONS = [
  { id: "trending", name: "Em Alta", field: "is_trending" },
  { id: "sales", name: "Mais Vendidos", field: "sales_count" },
  { id: "price_asc", name: "Menor Preço", field: "price" },
  { id: "price_desc", name: "Maior Preço", field: "price" },
  { id: "rating", name: "Melhor Avaliação", field: "product_rating" },
  { id: "recent", name: "Mais Recentes", field: "collected_at" },
] as const;

// Map sort ID to database field
export const SORT_ID_TO_FIELD: Record<string, { field: string; order: string }> = {
  trending: { field: "is_trending", order: "DESC" },
  sales: { field: "sales_count", order: "DESC" },
  price_asc: { field: "price", order: "ASC" },
  price_desc: { field: "price", order: "DESC" },
  rating: { field: "product_rating", order: "DESC" },
  recent: { field: "collected_at", order: "DESC" },
};

// Price ranges
export const PRICE_RANGES = [
  { min: 0, max: 50, label: "Até R$50" },
  { min: 50, max: 100, label: "R$50 - R$100" },
  { min: 100, max: 200, label: "R$100 - R$200" },
  { min: 200, max: 500, label: "R$200 - R$500" },
  { min: 500, max: Infinity, label: "Acima de R$500" },
] as const;

// Sales ranges
export const SALES_RANGES = [
  { min: 0, max: 100, label: "Até 100 vendas" },
  { min: 100, max: 500, label: "100 - 500 vendas" },
  { min: 500, max: 1000, label: "500 - 1k vendas" },
  { min: 1000, max: 5000, label: "1k - 5k vendas" },
  { min: 5000, max: Infinity, label: "Mais de 5k vendas" },
] as const;

// Keyboard shortcuts
export const SHORTCUTS = {
  search: "Ctrl+K",
  newSearch: "Ctrl+N",
  favorites: "Ctrl+F",
  settings: "Ctrl+,",
  export: "Ctrl+E",
} as const;
