import { invoke } from "@tauri-apps/api/core";
import { api } from "@/lib/api";
import type { CopyHistory, CopyRequest, CopyResponse } from "@/types";

const isTauri = () => typeof window !== 'undefined' && '__TAURI__' in window;

export async function generateCopy(request: CopyRequest): Promise<CopyResponse> {
  try {
    if (isTauri()) {
      return await invoke<CopyResponse>("generate_copy", { request });
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
      return await invoke<CopyHistory[]>("get_copy_history", { limit });
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
