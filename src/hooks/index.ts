// Custom React hooks for TikTrend Finder
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "@/lib/tauri";
import type { SearchFilters, License, CopyTone, CopyType } from "@/types";


// Query keys
export const queryKeys = {
  products: ["products"] as const,
  product: (id: string) => ["product", id] as const,
  favorites: ["favorites"] as const,
  stats: ["stats"] as const,
  license: ["license"] as const,
};

// Products hooks
export function useProducts(page?: number, pageSize?: number) {
  return useQuery({
    queryKey: [...queryKeys.products, page, pageSize],
    queryFn: () => api.getProducts(page, pageSize),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useProduct(id: string) {
  return useQuery({
    queryKey: queryKeys.product(id),
    queryFn: () => api.getProductById(id),
    enabled: !!id,
  });
}

export function useSearchProducts() {
  return useMutation({
    mutationFn: (filters: Partial<SearchFilters>) => api.searchProducts(filters),
  });
}

// Favorites hooks
export function useFavorites(listId?: string) {
  return useQuery({
    queryKey: listId ? [...queryKeys.favorites, listId] : queryKeys.favorites,
    queryFn: () => api.getFavorites(listId),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}


export function useAddFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ productId, listId }: { productId: string; listId?: string }) =>
      api.addFavorite(productId, listId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.favorites });
    },
  });
}

export function useRemoveFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (productId: string) => api.removeFavorite(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.favorites });
    },
  });
}

// Copy generation hook
export function useGenerateCopy() {
  return useMutation({
    mutationFn: (request: {
      productId: string;
      productTitle: string;
      productDescription: string;
      copyType: CopyType;
      tone: string;
      language: string;
    }) =>
      api.generateCopy({
        productId: request.productId,
        productTitle: request.productTitle,
        productDescription: request.productDescription,
        copyType: request.copyType,
        tone: request.tone as CopyTone,
        language: request.language,
      }),
  });
}

// Stats hook
export function useUserStats() {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: api.getUserStats,
    staleTime: 1 * 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

// License hook
export function useValidateLicense() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (licenseKey: string) => api.validateLicense(licenseKey),
    onSuccess: (data: License) => {
      queryClient.setQueryData(queryKeys.license, data);
    },
  });
}

// Scraper hook
export function useStartScraper() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (config: {
      maxProducts: number;
      categories: string[];
      useProxy: boolean;
      headless?: boolean;
    }) =>
      api.startScraper({
        maxProducts: config.maxProducts,
        categories: config.categories,
        useProxy: config.useProxy,
        intervalMinutes: 60, // Default
        headless: config.headless ?? true, // Default to true if not provided
        timeout: 30000, // Default
      }),
    onSuccess: () => {
      // Invalidate products to refetch after scraping
      queryClient.invalidateQueries({ queryKey: queryKeys.products });
      queryClient.invalidateQueries({ queryKey: queryKeys.stats });
    },
  });
}

export function useStopScraper() {
  return useMutation({
    mutationFn: () => api.stopScraper(),
  });
}

export function useTestProxy() {
  return useMutation({
    mutationFn: (proxy: string) => api.testProxy(proxy),
  });
}

export function useSyncProducts() {
  return useMutation({
    mutationFn: () => api.syncProducts(),
  });
}

// Re-export useToast
export { useToast, toast } from "./use-toast";
