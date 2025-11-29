import { invoke } from "@tauri-apps/api/core";
import type { PaginatedResponse, Product, ProductHistory, SearchFilters } from "@/types";
import { z } from "zod";

// Check if running in Tauri environment
const isTauri = (): boolean => {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
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
  // Add other fields as needed, keeping it loose for now to avoid breaking changes
  // strict validation can be added incrementally
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
  // In non-Tauri environment (E2E tests), return mock data
  if (!isTauri()) {
    return {
      data: mockProducts,
      total: mockProducts.length,
      page: 1,
      pageSize: 20,
      hasMore: false,
    };
  }
  
  try {
    const response = await invoke<PaginatedResponse<Product>>("search_products", { filters });
    return PaginatedResponseSchema.parse(response) as unknown as PaginatedResponse<Product>;
  } catch (error) {
    console.error("Error searching products:", error);
    throw error;
  }
}

export async function getProducts(
  page?: number,
  pageSize?: number
): Promise<PaginatedResponse<Product>> {
  // In non-Tauri environment (E2E tests), return mock data with pagination
  if (!isTauri()) {
    const currentPage = page || 1;
    const currentPageSize = pageSize || 20;
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
  
  try {
    const response = await invoke<PaginatedResponse<Product>>("get_products", { page, pageSize });
    return PaginatedResponseSchema.parse(response) as unknown as PaginatedResponse<Product>;
  } catch (error) {
    console.error("Error getting products:", error);
    throw error;
  }
}

export async function getProductById(id: string): Promise<Product | null> {
  // In non-Tauri environment (E2E tests), return mock data
  if (!isTauri()) {
    return mockProducts.find(p => p.id === id) || null;
  }
  
  try {
    return await invoke<Product | null>("get_product_by_id", { id });
  } catch (error) {
    console.error("Error getting product:", error);
    throw error;
  }
}

export async function getProductHistory(id: string): Promise<ProductHistory[]> {
  // In non-Tauri environment (E2E tests), return mock data
  if (!isTauri()) {
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
  
  try {
    return await invoke<ProductHistory[]>("get_product_history", { id });
  } catch (error) {
    console.error("Error getting product history:", error);
    throw error;
  }
}
