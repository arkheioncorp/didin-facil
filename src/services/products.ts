import type { PaginatedResponse, Product, ProductHistory, SearchFilters } from "@/types";
import { z } from "zod";
import { fetchProducts as fetchProductsFromApi, fetchProductById as fetchProductByIdFromApi, type ProductFilters } from "./api/products";

// Check if running in Tauri environment
const isTauri = (): boolean => {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
};

// Safe invoke wrapper
const safeInvoke = async <T>(cmd: string, args?: Record<string, unknown>): Promise<T> => {
  if (!isTauri()) {
    throw new Error(`Tauri command "${cmd}" not available in browser mode`);
  }
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke<T>(cmd, args);
};

// Generate mock products for E2E testing
const generateMockProducts = (count: number): Product[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: `prod-${i + 1}`,
    tiktokId: `tk-${i + 1}`,
    title: `Test Product ${i + 1}`,
    description: `Test product description ${i + 1}`,
    price: 49.90 + (i * 10),
    originalPrice: i % 2 === 0 ? 69.90 + (i * 10) : null,
    currency: "BRL",
    category: ["Electronics", "Fashion", "Home", "Beauty"][i % 4],
    subcategory: null,
    sellerName: `Test Seller ${i + 1}`,
    sellerRating: 4.0 + (i % 10) * 0.1,
    productRating: 4.0 + (i % 10) * 0.1,
    reviewsCount: 50 + i * 10,
    salesCount: 100 + i * 50,
    sales7d: 20 + i * 5,
    sales30d: 50 + i * 10,
    commissionRate: 5 + (i % 10),
    imageUrl: `https://picsum.photos/400/400?random=${i + 1}`,
    images: [`https://picsum.photos/400/400?random=${i + 1}`],
    videoUrl: null,
    productUrl: `https://example.com/product/${i + 1}`,
    affiliateUrl: null,
    hasFreeShipping: i % 2 === 0,
    isTrending: i % 3 === 0,
    isOnSale: i % 2 === 1,
    inStock: true,
    stockLevel: 50 + i * 5,
    collectedAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }));
};

// 50 mock products to enable pagination (with pageSize 20)
const mockProducts: Product[] = generateMockProducts(50);

const ProductSchema = z.object({
  id: z.string(),
  title: z.string(),
  price: z.number(),
}).passthrough();

const PaginatedResponseSchema = z.object({
  data: z.array(ProductSchema),
  total: z.number(),
  page: z.number(),
  pageSize: z.number(),
  hasMore: z.boolean(),
});

export async function searchProducts(
  filters: Partial<SearchFilters>
): Promise<PaginatedResponse<Product>> {
  // Try backend API first
  try {
    const apiFilters: ProductFilters = {
      page: filters.page || 1,
      per_page: filters.pageSize || 20,
      category: filters.categories?.[0],
      min_price: filters.priceMin,
      max_price: filters.priceMax,
      min_sales: filters.salesMin,
      search: filters.query,
      sort_by: filters.sortBy as ProductFilters['sort_by'] || 'sales_30d',
      sort_order: filters.sortOrder as ProductFilters['sort_order'] || 'desc',
    };
    return await fetchProductsFromApi(apiFilters);
  } catch (apiError) {
    console.warn('API unavailable, trying Tauri or mock:', apiError);
  }

  // In Tauri environment, use invoke
  if (isTauri()) {
    try {
      const response = await safeInvoke<PaginatedResponse<Product>>("search_products", { filters });
      return PaginatedResponseSchema.parse(response) as unknown as PaginatedResponse<Product>;
    } catch (error) {
      console.error("Error searching products:", error);
    }
  }
  
  // Fallback to mock data
  return {
    data: mockProducts,
    total: mockProducts.length,
    page: 1,
    pageSize: 20,
    hasMore: false,
  };
}

export async function getProducts(
  page?: number,
  pageSize?: number,
  filters?: {
    category?: string;
    minPrice?: number;
    maxPrice?: number;
    minSales?: number;
    sortBy?: string;
    sortOrder?: string;
    source?: string;
  }
): Promise<PaginatedResponse<Product>> {
  const currentPage = page || 1;
  const currentPageSize = pageSize || 20;

  // Try backend API first
  try {
    const apiFilters: ProductFilters = {
      page: currentPage,
      per_page: currentPageSize,
      category: filters?.category,
      min_price: filters?.minPrice,
      max_price: filters?.maxPrice,
      min_sales: filters?.minSales,
      sort_by: (filters?.sortBy as ProductFilters['sort_by']) || 'sales_30d',
      sort_order: (filters?.sortOrder as ProductFilters['sort_order']) || 'desc',
    };
    return await fetchProductsFromApi(apiFilters);
  } catch (apiError) {
    console.warn('API unavailable, trying Tauri or mock:', apiError);
  }

  // In Tauri environment, use invoke
  if (isTauri()) {
    try {
      const response = await safeInvoke<PaginatedResponse<Product>>("get_products", { page, pageSize });
      return PaginatedResponseSchema.parse(response) as unknown as PaginatedResponse<Product>;
    } catch (error) {
      console.error("Error getting products:", error);
    }
  }
  
  // Fallback to mock data with pagination
  const startIndex = (currentPage - 1) * currentPageSize;
  const endIndex = startIndex + currentPageSize;
  const paginatedProducts = mockProducts.slice(startIndex, endIndex);
  
  return {
    data: paginatedProducts,
    total: mockProducts.length,
    page: currentPage,
    pageSize: currentPageSize,
    hasMore: endIndex < mockProducts.length,
  };
}

export async function getProductById(id: string): Promise<Product | null> {
  // Try backend API first
  try {
    return await fetchProductByIdFromApi(id);
  } catch (apiError) {
    console.warn('API unavailable:', apiError);
  }

  // In Tauri environment, use invoke
  if (isTauri()) {
    try {
      return await safeInvoke<Product | null>("get_product_by_id", { id });
    } catch (error) {
      console.error("Error getting product:", error);
    }
  }
  
  // Fallback to mock data
  return mockProducts.find(p => p.id === id) || null;
}

export async function getProductHistory(id: string): Promise<ProductHistory[]> {
  // In Tauri environment, use invoke
  if (isTauri()) {
    try {
      return await safeInvoke<ProductHistory[]>("get_product_history", { id });
    } catch (error) {
      console.error("Error getting product history:", error);
    }
  }
  
  // Fallback to mock data
  return [
    {
      id: "hist-1",
      productId: id,
      price: 99.90,
      salesCount: 150,
      stockLevel: 100,
      collectedAt: new Date().toISOString(),
    }
  ];
}

