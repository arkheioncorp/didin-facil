import { invoke } from "@tauri-apps/api/core";
import type { SearchFilters, SearchHistoryItem } from "@/types";

export async function saveSearchHistory(
  query: string,
  filters: SearchFilters,
  resultsCount: number
): Promise<boolean> {
  try {
    return await invoke<boolean>("save_search_history", {
      query,
      filters: JSON.stringify(filters),
      resultsCount,
    });
  } catch (error) {
    console.error("Error saving search history:", error);
    throw error;
  }
}

export async function getSearchHistory(limit = 20): Promise<SearchHistoryItem[]> {
  try {
    return await invoke<SearchHistoryItem[]>("get_search_history", { limit });
  } catch (error) {
    console.error("Error getting search history:", error);
    throw error;
  }
}
