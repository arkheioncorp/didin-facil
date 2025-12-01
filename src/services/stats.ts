import { api } from "@/lib/api";
import type { DashboardStats } from "@/types";

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

// Default stats for browser/fallback
const DEFAULT_STATS: DashboardStats = {
  totalProducts: 0,
  trendingProducts: 0,
  favoriteCount: 0,
  searchesToday: 0,
  copiesGenerated: 0,
  topCategories: [],
};

export async function getUserStats(): Promise<DashboardStats> {
  try {
    // In Tauri environment, use native invoke
    if (isTauri()) {
      return await safeInvoke<DashboardStats>("get_user_stats");
    }
    
    // In browser, try HTTP API or return defaults
    try {
      const response = await api.get<DashboardStats>("/users/stats");
      return response.data;
    } catch {
      // If API not available, return defaults for dev/demo mode
      console.info("[Stats] Running in browser mode with default stats");
      return DEFAULT_STATS;
    }
  } catch (error) {
    console.error("Error getting user stats:", error);
    return DEFAULT_STATS;
  }
}
