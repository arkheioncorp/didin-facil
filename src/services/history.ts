import { api } from "@/lib/api";
import type { SearchFilters, SearchHistoryItem } from "@/types";

// Check if running in Tauri environment
const isTauri = (): boolean => {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
};

// Safe invoke wrapper for Tauri commands
async function safeInvoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  if (isTauri()) {
    const { invoke } = await import("@tauri-apps/api/core");
    return invoke<T>(cmd, args);
  }
  throw new Error(`Tauri command "${cmd}" not available in browser mode`);
}

export async function saveSearchHistory(
  query: string,
  filters: SearchFilters,
  resultsCount: number
): Promise<boolean> {
  try {
    // In Tauri environment, use native invoke
    if (isTauri()) {
      return await safeInvoke<boolean>("save_search_history", {
        query,
        filters: JSON.stringify(filters),
        resultsCount,
      });
    }
    
    // In browser, try HTTP API
    try {
      await api.post("/history/search", {
        query,
        filters: JSON.stringify(filters),
        results_count: resultsCount,
      });
      return true;
    } catch {
      // If API not available, silently fail for dev mode
      console.info("[History] Running in browser mode, skipping save");
      return true;
    }
  } catch (error) {
    console.error("Error saving search history:", error);
    return false;
  }
}

export async function getSearchHistory(limit = 20): Promise<SearchHistoryItem[]> {
  try {
    // In Tauri environment, use native invoke
    if (isTauri()) {
      return await safeInvoke<SearchHistoryItem[]>("get_search_history", { limit });
    }
    
    // In browser, try HTTP API or return empty
    try {
      const response = await api.get<SearchHistoryItem[]>(`/history/search?limit=${limit}`);
      return response.data;
    } catch {
      // If API not available, return empty for dev mode
      console.info("[History] Running in browser mode with empty history");
      return [];
    }
  } catch (error) {
    console.error("Error getting search history:", error);
    return [];
  }
}
