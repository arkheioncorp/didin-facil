/**
 * TikTok Shop Service V2
 * Serviço para integração com TikTok Shop API
 * @module services/tiktokShop
 */

// ==================== Types ====================

export interface TikTokShopCredentials {
  appKey: string;
  appSecret: string;
  serviceId?: string;
}

export interface TikTokShopConnection {
  id: number;
  userId: number;
  shopId: string;
  shopName: string | null;
  shopRegion: string | null;
  accessToken: string;
  refreshToken: string;
  accessTokenExpiresAt: string;
  refreshTokenExpiresAt: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface TikTokShopProduct {
  id: number;
  connectionId: number;
  productId: string;
  title: string;
  description: string | null;
  category: string | null;
  status: string;
  skuCount: number;
  mainImageUrl: string | null;
  price: number | null;
  currency: string | null;
  inventory: number | null;
  salesCount: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface TikTokShopStatus {
  connected: boolean;
  seller_name?: string;
  seller_region?: string;
  shops: Array<{
    shop_id: string;
    shop_name: string;
    region: string;
  }>;
  token_expires_at?: string;
  last_sync?: string;
  product_count: number;
}

export interface TikTokShopProductSearchResult {
  products: TikTokShopProduct[];
  total: number;
  pageSize: number;
  pageNumber: number;
  hasMore: boolean;
}

export interface TikTokShopSyncResult {
  success: boolean;
  synced: number;
  total: number;
  message: string;
}

// ==================== API Configuration ====================

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem("auth_token");

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ==================== TikTok Shop Service ====================

export const tiktokShopService = {
  /**
   * Obtém a URL de autorização OAuth
   */
  async getAuthUrl(
    credentials: TikTokShopCredentials
  ): Promise<{ auth_url: string; state: string }> {
    const params = new URLSearchParams({
      app_key: credentials.appKey,
      ...(credentials.serviceId && { service_id: credentials.serviceId }),
    });

    return fetchWithAuth(`/tiktok-shop-v2/auth/url?${params.toString()}`);
  },

  /**
   * Salva token obtido manualmente (para fluxo com callback externo)
   */
  async saveToken(
    credentials: TikTokShopCredentials,
    authCode: string
  ): Promise<{ success: boolean; message: string; connection?: TikTokShopConnection }> {
    return fetchWithAuth("/tiktok-shop-v2/auth/token", {
      method: "POST",
      body: JSON.stringify({
        app_key: credentials.appKey,
        app_secret: credentials.appSecret,
        code: authCode,
      }),
    });
  },

  /**
   * Verifica o status da conexão atual
   */
  async getStatus(): Promise<TikTokShopStatus> {
    return fetchWithAuth("/tiktok-shop-v2/status");
  },

  /**
   * Busca produtos da loja TikTok Shop
   * Nota: Usa o endpoint /products com parâmetros de filtro
   */
  async searchProducts(
    pageSize: number = 20,
    pageToken?: string
  ): Promise<TikTokShopProductSearchResult> {
    const params = new URLSearchParams({
      page_size: pageSize.toString(),
    });
    
    if (pageToken) {
      params.append("page_token", pageToken);
    }

    return fetchWithAuth(`/tiktok-shop-v2/products?${params.toString()}`);
  },

  /**
   * Sincroniza produtos do TikTok Shop para o banco de dados
   */
  async syncProducts(): Promise<TikTokShopSyncResult> {
    return fetchWithAuth("/tiktok-shop-v2/products/sync", {
      method: "POST",
    });
  },

  /**
   * Lista produtos sincronizados no banco de dados
   */
  async getProducts(
    page: number = 1,
    pageSize: number = 20
  ): Promise<{ products: TikTokShopProduct[]; total: number }> {
    const params = new URLSearchParams({
      skip: ((page - 1) * pageSize).toString(),
      limit: pageSize.toString(),
    });

    return fetchWithAuth(`/tiktok-shop-v2/products?${params.toString()}`);
  },

  /**
   * Desconecta a loja TikTok Shop
   */
  async disconnect(): Promise<{ success: boolean; message: string }> {
    return fetchWithAuth("/tiktok-shop-v2/disconnect", {
      method: "POST",
    });
  },

  /**
   * Lista lojas conectadas
   */
  async getShops(): Promise<{ shops: Array<{ shop_id: string; shop_name: string; region: string }> }> {
    return fetchWithAuth("/tiktok-shop-v2/shops");
  },

  /**
   * Verifica status da sincronização
   */
  async getSyncStatus(): Promise<{ status: string; progress?: number; message?: string }> {
    return fetchWithAuth("/tiktok-shop-v2/products/sync/status");
  },
};

export default tiktokShopService;
