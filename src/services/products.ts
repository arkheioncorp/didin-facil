import { invoke } from "@tauri-apps/api/core";
import type { PaginatedResponse, Product, ProductHistory, SearchFilters } from "@/types";
import { z } from "zod";

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
  try {
    const response = await invoke<PaginatedResponse<Product>>("get_products", { page, pageSize });
    return PaginatedResponseSchema.parse(response) as unknown as PaginatedResponse<Product>;
  } catch (error) {
    console.error("Error getting products:", error);
    throw error;
  }
}

export async function getProductById(id: string): Promise<Product | null> {
  try {
    return await invoke<Product | null>("get_product_by_id", { id });
  } catch (error) {
    console.error("Error getting product:", error);
    throw error;
  }
}

export async function getProductHistory(id: string): Promise<ProductHistory[]> {
  try {
    return await invoke<ProductHistory[]>("get_product_history", { id });
  } catch (error) {
    console.error("Error getting product history:", error);
    throw error;
  }
}
