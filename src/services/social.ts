/**
 * Social Media Service
 * Serviço para gerenciamento de redes sociais
 */

// ==================== Types ====================

export interface ConnectedAccount {
  platform: "instagram" | "tiktok" | "youtube";
  accountName: string;
  username?: string;
  connectedAt: string;
  expiresAt?: string;
  status: "active" | "expired" | "revoked";
}

export interface ScheduledPost {
  id: string;
  platform: string;
  scheduledTime: string;
  status: "scheduled" | "processing" | "published" | "failed" | "cancelled";
  contentType: string;
  caption: string;
  createdAt: string;
  publishedAt?: string;
}

export interface SchedulePostRequest {
  platform: string;
  scheduledTime: string;
  contentType: string;
  caption: string;
  hashtags?: string[];
  accountName?: string;
  platformConfig?: Record<string, unknown>;
}

export interface SchedulerStats {
  total: number;
  scheduled: number;
  published: number;
  failed: number;
  cancelled: number;
  retrying: number;
  byPlatform: Record<string, number>;
}

export interface PlatformInfo {
  name: string;
  configured: boolean;
  scopes: string[];
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

// ==================== OAuth Service ====================

export const oAuthService = {
  /**
   * Lista plataformas suportadas e status de configuração
   */
  async getPlatforms(): Promise<{ platforms: PlatformInfo[] }> {
    return fetchWithAuth("/social-auth/platforms");
  },

  /**
   * Inicia fluxo OAuth para uma plataforma
   */
  async initOAuth(
    platform: string,
    accountName: string
  ): Promise<{ authUrl: string; state: string; expiresIn: number }> {
    return fetchWithAuth("/social-auth/init", {
      method: "POST",
      body: JSON.stringify({
        platform,
        account_name: accountName,
      }),
    });
  },

  /**
   * Lista contas conectadas
   */
  async getConnectedAccounts(): Promise<{ accounts: ConnectedAccount[] }> {
    return fetchWithAuth("/social-auth/accounts");
  },

  /**
   * Desconecta uma conta
   */
  async disconnectAccount(
    platform: string,
    accountName: string
  ): Promise<void> {
    await fetchWithAuth(`/social-auth/accounts/${platform}/${accountName}`, {
      method: "DELETE",
    });
  },

  /**
   * Atualiza token de uma conta
   */
  async refreshToken(
    platform: string,
    accountName: string
  ): Promise<{ status: string; expiresAt?: string }> {
    return fetchWithAuth("/social-auth/refresh", {
      method: "POST",
      body: JSON.stringify({
        platform,
        account_name: accountName,
      }),
    });
  },
};

// ==================== Scheduler Service ====================

export const schedulerService = {
  /**
   * Agenda um novo post
   */
  async schedulePost(
    data: SchedulePostRequest
  ): Promise<ScheduledPost> {
    return fetchWithAuth("/scheduler/posts", {
      method: "POST",
      body: JSON.stringify({
        platform: data.platform,
        scheduled_time: data.scheduledTime,
        content_type: data.contentType,
        caption: data.caption,
        hashtags: data.hashtags || [],
        account_name: data.accountName,
        platform_config: data.platformConfig || {},
      }),
    });
  },

  /**
   * Agenda post com arquivo
   */
  async schedulePostWithFile(
    file: File,
    data: Omit<SchedulePostRequest, "file">
  ): Promise<ScheduledPost> {
    const token = localStorage.getItem("auth_token");
    const formData = new FormData();
    
    formData.append("file", file);
    formData.append("platform", data.platform);
    formData.append("scheduled_time", data.scheduledTime);
    formData.append("content_type", data.contentType);
    formData.append("caption", data.caption);
    formData.append("hashtags", (data.hashtags || []).join(","));
    if (data.accountName) {
      formData.append("account_name", data.accountName);
    }

    const response = await fetch(`${API_BASE}/scheduler/posts/with-file`, {
      method: "POST",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  },

  /**
   * Lista posts agendados
   */
  async listPosts(
    status?: string,
    limit = 50
  ): Promise<{ posts: ScheduledPost[]; total: number }> {
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    params.append("limit", limit.toString());

    return fetchWithAuth(`/scheduler/posts?${params}`);
  },

  /**
   * Cancela um post agendado
   */
  async cancelPost(postId: string): Promise<{ status: string }> {
    return fetchWithAuth(`/scheduler/posts/${postId}`, {
      method: "DELETE",
    });
  },

  /**
   * Obtém estatísticas do agendador
   */
  async getStats(): Promise<SchedulerStats> {
    return fetchWithAuth("/scheduler/stats");
  },

  /**
   * Lista posts na Dead Letter Queue
   */
  async getDLQPosts(
    limit = 50
  ): Promise<Array<{
    id: string;
    platform: string;
    scheduledTime: string;
    failedAt: string;
    attempts: number;
    lastError: string;
    errorType: string;
  }>> {
    return fetchWithAuth(`/scheduler/dlq?limit=${limit}`);
  },

  /**
   * Retenta um post da DLQ
   */
  async retryDLQPost(postId: string): Promise<{ status: string }> {
    return fetchWithAuth(`/scheduler/dlq/${postId}/retry`, {
      method: "POST",
    });
  },
};

// ==================== Platform-Specific Services ====================

export const instagramService = {
  async login(
    username: string,
    password: string,
    verificationCode?: string
  ): Promise<{
    status: string;
    message: string;
    challengeType?: string;
  }> {
    return fetchWithAuth("/instagram/login", {
      method: "POST",
      body: JSON.stringify({
        username,
        password,
        verification_code: verificationCode,
      }),
    });
  },

  async resolveChallenge(
    username: string,
    code: string
  ): Promise<{ status: string; message: string }> {
    return fetchWithAuth("/instagram/challenge/resolve", {
      method: "POST",
      body: JSON.stringify({ username, code }),
    });
  },

  async listAccounts(): Promise<{
    accounts: Array<{ username: string; isActive: boolean }>;
  }> {
    return fetchWithAuth("/instagram/accounts");
  },
};

export const tiktokService = {
  async createSession(
    accountName: string,
    cookies: Array<Record<string, string>>
  ): Promise<{ status: string; message: string }> {
    return fetchWithAuth("/tiktok/sessions", {
      method: "POST",
      body: JSON.stringify({
        account_name: accountName,
        cookies,
      }),
    });
  },

  async listSessions(): Promise<{
    sessions: Array<{ accountName: string; file: string }>;
  }> {
    return fetchWithAuth("/tiktok/sessions");
  },
};

export const youtubeService = {
  async initAuth(
    accountName: string
  ): Promise<{ status: string; message: string }> {
    return fetchWithAuth("/youtube/auth/init", {
      method: "POST",
      body: JSON.stringify({ account_name: accountName }),
    });
  },

  async listAccounts(): Promise<{
    accounts: Array<{ accountName: string; tokenFile: string }>;
  }> {
    return fetchWithAuth("/youtube/accounts");
  },
};

// ==================== Content Generation Service ====================

export const contentService = {
  async generateCaption(
    topic: string,
    platform: string,
    tone?: string
  ): Promise<{ caption: string; hashtags: string[] }> {
    return fetchWithAuth("/content/caption", {
      method: "POST",
      body: JSON.stringify({ topic, platform, tone }),
    });
  },

  async generateHashtags(
    topic: string,
    count = 10
  ): Promise<{ hashtags: string[] }> {
    return fetchWithAuth("/content/hashtags", {
      method: "POST",
      body: JSON.stringify({ topic, count }),
    });
  },

  async generateVideoScript(
    topic: string,
    duration: number,
    style?: string
  ): Promise<{ script: string; scenes: string[] }> {
    return fetchWithAuth("/content/video-script", {
      method: "POST",
      body: JSON.stringify({ topic, duration, style }),
    });
  },
};

// ==================== Exports ====================

export default {
  oauth: oAuthService,
  scheduler: schedulerService,
  instagram: instagramService,
  tiktok: tiktokService,
  youtube: youtubeService,
  content: contentService,
};
