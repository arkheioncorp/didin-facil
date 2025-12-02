import { api } from "@/lib/api";
import type { CopyHistory, CopyRequest, CopyResponse } from "@/types";

const isTauri = () => typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;

// Safe invoke wrapper for Tauri commands
async function safeInvoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  if (isTauri()) {
    const { invoke } = await import("@tauri-apps/api/core");
    return invoke<T>(cmd, args);
  }
  throw new Error(`Tauri command "${cmd}" not available in browser mode`);
}

export async function generateCopy(request: CopyRequest): Promise<CopyResponse> {
  try {
    if (isTauri()) {
      return await safeInvoke<CopyResponse>("generate_copy", { request });
    }

    // Map to backend snake_case
    const payload = {
      product_id: request.productId,
      product_title: request.productTitle,
      product_description: request.productDescription,
      product_price: request.productPrice,
      product_benefits: request.productBenefits,
      copy_type: request.copyType,
      tone: request.tone,
      platform: request.platform,
      language: request.language,
      max_length: request.maxLength,
      include_emoji: request.includeEmoji ?? true,
      include_hashtags: request.includeHashtags ?? true,
      custom_instructions: request.customInstructions,
    };

    const response = await api.post<any>("/copy/generate", payload);
    const data = response.data;

    // Map to frontend camelCase
    return {
      id: data.id,
      copyText: data.copy_text,
      copyType: data.copy_type,
      tone: data.tone,
      platform: data.platform,
      wordCount: data.word_count,
      characterCount: data.character_count,
      createdAt: data.created_at,
      cached: data.cached,
      creditsUsed: data.credits_used,
      creditsRemaining: data.credits_remaining,
    };
  } catch (error) {
    console.error("Error generating copy:", error);
    throw error;
  }
}

export async function getCopyHistory(limit = 50): Promise<CopyHistory[]> {
  try {
    if (isTauri()) {
      return await safeInvoke<CopyHistory[]>("get_copy_history", { limit });
    }

    const response = await api.get<any[]>("/copy/history", { params: { limit: limit.toString() } });
    
    return response.data.map(item => ({
      id: item.id,
      productId: item.product_id,
      productTitle: item.product_title,
      copyType: item.copy_type,
      tone: item.tone,
      copyText: item.copy_text,
      createdAt: item.created_at,
    }));
  } catch (error) {
    console.error("Error getting copy history:", error);
    throw error;
  }
}

// =============================================================================
// USER PREFERENCES
// =============================================================================

export interface CopyPreferences {
  defaultCopyType: string;
  defaultTone: string;
  defaultPlatform: string;
  defaultLanguage: string;
  includeEmoji: boolean;
  includeHashtags: boolean;
  totalCopiesGenerated: number;
  mostUsedCopyType?: string;
  mostUsedTone?: string;
}

export async function getUserPreferences(): Promise<CopyPreferences> {
  const response = await api.get<any>("/copy/preferences");
  const data = response.data;
  
  return {
    defaultCopyType: data.default_copy_type,
    defaultTone: data.default_tone,
    defaultPlatform: data.default_platform,
    defaultLanguage: data.default_language,
    includeEmoji: data.include_emoji,
    includeHashtags: data.include_hashtags,
    totalCopiesGenerated: data.total_copies_generated,
    mostUsedCopyType: data.most_used_copy_type,
    mostUsedTone: data.most_used_tone,
  };
}

export async function updateUserPreferences(
  preferences: Partial<CopyPreferences>
): Promise<CopyPreferences> {
  const payload: Record<string, any> = {};
  
  if (preferences.defaultCopyType !== undefined) {
    payload.default_copy_type = preferences.defaultCopyType;
  }
  if (preferences.defaultTone !== undefined) {
    payload.default_tone = preferences.defaultTone;
  }
  if (preferences.defaultPlatform !== undefined) {
    payload.default_platform = preferences.defaultPlatform;
  }
  if (preferences.defaultLanguage !== undefined) {
    payload.default_language = preferences.defaultLanguage;
  }
  if (preferences.includeEmoji !== undefined) {
    payload.include_emoji = preferences.includeEmoji;
  }
  if (preferences.includeHashtags !== undefined) {
    payload.include_hashtags = preferences.includeHashtags;
  }

  const response = await api.put<any>("/copy/preferences", payload);
  const data = response.data;
  
  return {
    defaultCopyType: data.default_copy_type,
    defaultTone: data.default_tone,
    defaultPlatform: data.default_platform,
    defaultLanguage: data.default_language,
    includeEmoji: data.include_emoji,
    includeHashtags: data.include_hashtags,
    totalCopiesGenerated: data.total_copies_generated,
    mostUsedCopyType: data.most_used_copy_type,
    mostUsedTone: data.most_used_tone,
  };
}

// =============================================================================
// USER SAVED TEMPLATES
// =============================================================================

export interface SavedTemplate {
  id: string;  // UUID
  name: string;
  captionTemplate: string;
  hashtags?: string[];  // Array de hashtags
  variables?: Record<string, any>;
  copyType?: string;
  createdAt: string;
  timesUsed: number;
}

export interface CreateTemplateRequest {
  name: string;
  captionTemplate: string;
  hashtags?: string[];  // Array de hashtags
  variables?: Record<string, any>;
  copyType?: string;
}

export async function saveUserTemplate(
  template: CreateTemplateRequest
): Promise<SavedTemplate> {
  const response = await api.post<any>("/copy/templates/user", {
    name: template.name,
    caption_template: template.captionTemplate,
    hashtags: template.hashtags,
    variables: template.variables,
    copy_type: template.copyType,
  });
  
  const data = response.data;
  return {
    id: data.id,
    name: data.name,
    captionTemplate: data.caption_template,
    hashtags: data.hashtags,
    variables: data.variables,
    copyType: data.copy_type,
    createdAt: data.created_at,
    timesUsed: data.times_used,
  };
}

export async function getUserTemplates(): Promise<SavedTemplate[]> {
  const response = await api.get<any[]>("/copy/templates/user");
  
  return response.data.map((item) => ({
    id: item.id,
    name: item.name,
    captionTemplate: item.caption_template,
    hashtags: item.hashtags,
    variables: item.variables,
    copyType: item.copy_type,
    createdAt: item.created_at,
    timesUsed: item.times_used,
  }));
}

export async function deleteUserTemplate(templateId: string): Promise<void> {
  await api.delete(`/copy/templates/user/${templateId}`);
}

export async function incrementTemplateUse(templateId: string): Promise<void> {
  await api.put(`/copy/templates/user/${templateId}/use`);
}

// =============================================================================
// COPY STATS
// =============================================================================

export interface CopyStats {
  totalCopies: number;
  totalCreditsUsed: number;
  cachedCopies: number;
  copyTypesUsed: number;
  platformsUsed: number;
  lastGenerated?: string;
  cacheHitRate: number;
}

export async function getCopyStats(): Promise<CopyStats> {
  const response = await api.get<any>("/copy/stats");
  const data = response.data;
  
  return {
    totalCopies: data.total_copies,
    totalCreditsUsed: data.total_credits_used,
    cachedCopies: data.cached_copies,
    copyTypesUsed: data.copy_types_used,
    platformsUsed: data.platforms_used,
    lastGenerated: data.last_generated,
    cacheHitRate: data.cache_hit_rate,
  };
}

// =============================================================================
// CACHE INVALIDATION
// =============================================================================

export async function invalidateProductCache(productId: string): Promise<void> {
  await api.delete(`/copy/cache/${productId}`);
}

