import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { SearchFilters, SearchConfig } from "@/types";

interface SearchState {
  // Filters
  filters: SearchFilters;
  config: SearchConfig;
  searchHistory: string[];
  
  // Actions
  setFilters: (filters: Partial<SearchFilters>) => void;
  resetFilters: () => void;
  setConfig: (config: Partial<SearchConfig>) => void;
  addToHistory: (query: string) => void;
  clearHistory: () => void;
}

const defaultFilters: SearchFilters = {
  query: undefined,
  categories: [],
  priceMin: undefined,
  priceMax: undefined,
  salesMin: undefined,
  ratingMin: undefined,
  hasFreeShipping: undefined,
  isTrending: undefined,
  isOnSale: undefined,
  sortBy: "trending",
  sortOrder: "desc",
  page: 1,
  pageSize: 20,
};

const defaultConfig: SearchConfig = {
  maxResults: 50,
  includeImages: true,
  includeDescription: true,
  includeMetrics: true,
  autoSave: true,
  refreshInterval: 3600000, // 1 hour in ms
};

export const useSearchStore = create<SearchState>()(
  persist(
    (set) => ({
      filters: defaultFilters,
      config: defaultConfig,
      searchHistory: [],
      
      setFilters: (newFilters: Partial<SearchFilters>) =>
        set((state: SearchState) => ({
          filters: { ...state.filters, ...newFilters },
        })),
        
      resetFilters: () =>
        set({ filters: defaultFilters }),
        
      setConfig: (newConfig: Partial<SearchConfig>) =>
        set((state: SearchState) => ({
          config: { ...state.config, ...newConfig },
        })),
        
      addToHistory: (query: string) =>
        set((state: SearchState) => ({
          searchHistory: [
            query,
            ...state.searchHistory.filter((q: string) => q !== query),
          ].slice(0, 20),
        })),
        
      clearHistory: () =>
        set({ searchHistory: [] }),
    }),
    {
      name: "tiktrend-search",
      storage: createJSONStorage(() => localStorage),
      partialize: (state: SearchState) => ({
        filters: state.filters,
        config: state.config,
        searchHistory: state.searchHistory,
      }),
    }
  )
);
