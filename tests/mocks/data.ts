/**
 * Mock Data for Tests
 * Contains all mock data used across tests
 */

// ============================================
// USER DATA
// ============================================

export const mockUser = {
  id: "user-123",
  email: "test@example.com",
  name: "Test User",
  avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=test",
  plan: "pro" as const,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-11-25T00:00:00Z",
  preferences: {
    theme: "dark" as const,
    language: "pt-BR",
    notifications: true,
    autoSave: true,
  },
};

export const mockLicense = {
  id: "license-123",
  key: "VALID-LICENSE-KEY-123",
  user_id: "user-123",
  plan: "pro" as const,
  status: "active" as const,
  hwid: "test-hwid-12345",
  activated_at: "2024-01-01T00:00:00Z",
  expires_at: "2025-01-01T00:00:00Z",
  features: {
    max_searches_per_day: 100,
    max_copies_per_day: 50,
    max_favorites: 500,
    export_enabled: true,
    priority_support: true,
  },
};

// ============================================
// PRODUCTS DATA
// ============================================

export const mockProducts = [
  {
    id: "prod-1",
    title: "Fone de Ouvido Bluetooth Premium",
    description: "Fone sem fio com cancelamento de ruído ativo e 40h de bateria",
    price: 199.90,
    original_price: 299.90,
    discount_percentage: 33,
    image_url: "https://picsum.photos/seed/prod1/400/400",
    category: "electronics",
    views: 15000,
    sales: 2500,
    rating: 4.8,
    tiktok_url: "https://tiktok.com/@seller/video/123",
    created_at: "2024-11-20T10:00:00Z",
    trend_score: 95,
    tags: ["tecnologia", "audio", "bluetooth"],
  },
  {
    id: "prod-2",
    title: "Kit Skincare Coreano 10 Passos",
    description: "Kit completo de cuidados com a pele importado da Coreia",
    price: 149.90,
    original_price: 249.90,
    discount_percentage: 40,
    image_url: "https://picsum.photos/seed/prod2/400/400",
    category: "beauty",
    views: 25000,
    sales: 4500,
    rating: 4.9,
    tiktok_url: "https://tiktok.com/@seller/video/456",
    created_at: "2024-11-19T14:00:00Z",
    trend_score: 98,
    tags: ["beleza", "skincare", "coreano"],
  },
  {
    id: "prod-3",
    title: "Luminária LED RGB Gamer",
    description: "Luminária com 16 cores e controle por app",
    price: 89.90,
    original_price: 129.90,
    discount_percentage: 31,
    image_url: "https://picsum.photos/seed/prod3/400/400",
    category: "home",
    views: 8000,
    sales: 1200,
    rating: 4.6,
    tiktok_url: "https://tiktok.com/@seller/video/789",
    created_at: "2024-11-18T08:00:00Z",
    trend_score: 82,
    tags: ["decoracao", "gamer", "led"],
  },
  {
    id: "prod-4",
    title: "Tênis Esportivo Ultra Leve",
    description: "Tênis para corrida com tecnologia de amortecimento",
    price: 179.90,
    original_price: 299.90,
    discount_percentage: 40,
    image_url: "https://picsum.photos/seed/prod4/400/400",
    category: "fashion",
    views: 12000,
    sales: 1800,
    rating: 4.7,
    tiktok_url: "https://tiktok.com/@seller/video/101",
    created_at: "2024-11-17T16:00:00Z",
    trend_score: 88,
    tags: ["moda", "esporte", "tenis"],
  },
  {
    id: "prod-5",
    title: "Smartwatch Fitness Pro",
    description: "Relógio inteligente com monitor cardíaco e GPS integrado",
    price: 249.90,
    original_price: 399.90,
    discount_percentage: 38,
    image_url: "https://picsum.photos/seed/prod5/400/400",
    category: "electronics",
    views: 18000,
    sales: 3200,
    rating: 4.8,
    tiktok_url: "https://tiktok.com/@seller/video/202",
    created_at: "2024-11-16T12:00:00Z",
    trend_score: 92,
    tags: ["tecnologia", "fitness", "smartwatch"],
  },
  {
    id: "prod-6",
    title: "Bolsa Térmica Multiuso",
    description: "Bolsa térmica para alimentos com capacidade de 15L",
    price: 59.90,
    original_price: 89.90,
    discount_percentage: 33,
    image_url: "https://picsum.photos/seed/prod6/400/400",
    category: "home",
    views: 5000,
    sales: 800,
    rating: 4.5,
    tiktok_url: "https://tiktok.com/@seller/video/303",
    created_at: "2024-11-15T09:00:00Z",
    trend_score: 75,
    tags: ["casa", "cozinha", "termica"],
  },
  {
    id: "prod-7",
    title: "Ring Light Profissional 18\"",
    description: "Iluminação circular para fotos e vídeos com tripé ajustável",
    price: 129.90,
    original_price: 199.90,
    discount_percentage: 35,
    image_url: "https://picsum.photos/seed/prod7/400/400",
    category: "electronics",
    views: 22000,
    sales: 5500,
    rating: 4.9,
    tiktok_url: "https://tiktok.com/@seller/video/404",
    created_at: "2024-11-14T11:00:00Z",
    trend_score: 96,
    tags: ["foto", "video", "iluminacao"],
  },
  {
    id: "prod-8",
    title: "Kit Organizador de Maquiagem",
    description: "Organizador acrílico com 6 compartimentos e gavetas",
    price: 69.90,
    original_price: 99.90,
    discount_percentage: 30,
    image_url: "https://picsum.photos/seed/prod8/400/400",
    category: "beauty",
    views: 9500,
    sales: 1600,
    rating: 4.6,
    tiktok_url: "https://tiktok.com/@seller/video/505",
    created_at: "2024-11-13T13:00:00Z",
    trend_score: 80,
    tags: ["beleza", "organizacao", "maquiagem"],
  },
];

// ============================================
// COPY HISTORY DATA
// ============================================

export const mockCopyHistory = [
  {
    id: "copy-1",
    product_id: "prod-1",
    type: "product_description",
    tone: "professional",
    content: "Experimente a liberdade sonora com nosso Fone de Ouvido Bluetooth Premium...",
    tokens_used: 150,
    created_at: "2024-11-24T10:00:00Z",
  },
  {
    id: "copy-2",
    product_id: "prod-2",
    type: "social_media",
    tone: "casual",
    content: "Sua pele vai agradecer! 🌟 Kit Skincare Coreano com 10 passos...",
    tokens_used: 120,
    created_at: "2024-11-23T15:00:00Z",
  },
  {
    id: "copy-3",
    product_id: "prod-5",
    type: "ad_copy",
    tone: "persuasive",
    content: "Transforme sua rotina de exercícios com o Smartwatch Fitness Pro...",
    tokens_used: 180,
    created_at: "2024-11-22T09:00:00Z",
  },
];

// ============================================
// FAVORITES DATA
// ============================================

export const mockFavorites = [
  {
    id: "fav-1",
    product_id: "prod-1",
    list_id: "list-1",
    created_at: "2024-11-24T08:00:00Z",
  },
  {
    id: "fav-2",
    product_id: "prod-2",
    list_id: "list-1",
    created_at: "2024-11-23T14:00:00Z",
  },
  {
    id: "fav-3",
    product_id: "prod-5",
    list_id: "list-2",
    created_at: "2024-11-22T16:00:00Z",
  },
];

export const mockFavoriteLists = [
  {
    id: "list-1",
    name: "Para Revender",
    description: "Produtos com boa margem de lucro",
    color: "#3B82F6",
    product_count: 2,
    created_at: "2024-11-20T10:00:00Z",
  },
  {
    id: "list-2",
    name: "Tendências",
    description: "Produtos em alta no momento",
    color: "#10B981",
    product_count: 1,
    created_at: "2024-11-18T12:00:00Z",
  },
];

// ============================================
// SEARCH FILTERS DATA
// ============================================

export const mockCategories = [
  { id: "electronics", name: "Eletrônicos", count: 150 },
  { id: "beauty", name: "Beleza", count: 120 },
  { id: "fashion", name: "Moda", count: 200 },
  { id: "home", name: "Casa", count: 80 },
  { id: "sports", name: "Esportes", count: 60 },
  { id: "toys", name: "Brinquedos", count: 45 },
];

export const mockPriceRanges = [
  { min: 0, max: 50, label: "Até R$ 50" },
  { min: 50, max: 100, label: "R$ 50 - R$ 100" },
  { min: 100, max: 200, label: "R$ 100 - R$ 200" },
  { min: 200, max: 500, label: "R$ 200 - R$ 500" },
  { min: 500, max: null, label: "Acima de R$ 500" },
];

// ============================================
// SUBSCRIPTION DATA
// ============================================

export const mockPlans = [
  {
    id: "free",
    name: "Gratuito",
    price: 0,
    features: [
      "10 buscas por dia",
      "5 copies por dia",
      "50 favoritos",
      "Suporte básico",
    ],
    popular: false,
  },
  {
    id: "basic",
    name: "Básico",
    price: 19.90,
    features: [
      "50 buscas por dia",
      "25 copies por dia",
      "200 favoritos",
      "Exportação CSV",
      "Suporte prioritário",
    ],
    popular: false,
  },
  {
    id: "premium",
    name: "Premium",
    price: 49.90,
    features: [
      "Buscas ilimitadas",
      "100 copies por dia",
      "Favoritos ilimitados",
      "Exportação completa",
      "API access",
      "Suporte VIP 24/7",
    ],
    popular: true,
  },
];

// ============================================
// ERROR RESPONSES
// ============================================

export const mockErrors = {
  unauthorized: {
    status: 401,
    detail: "Not authenticated",
  },
  forbidden: {
    status: 403,
    detail: "Not enough permissions",
  },
  notFound: {
    status: 404,
    detail: "Resource not found",
  },
  rateLimited: {
    status: 429,
    detail: "Too many requests",
    retry_after: 60,
  },
  serverError: {
    status: 500,
    detail: "Internal server error",
  },
  quotaExceeded: {
    status: 402,
    detail: "Quota exceeded",
    upgrade_url: "/subscription",
  },
};
