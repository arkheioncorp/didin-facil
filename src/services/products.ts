import { invoke } from "@tauri-apps/api/core";
import type { PaginatedResponse, Product, SearchFilters } from "@/types";

export async function searchProducts(
  filters: Partial<SearchFilters>
): Promise<PaginatedResponse<Product>> {
  try {
    return await invoke<PaginatedResponse<Product>>("search_products", { filters });
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
    return await invoke<PaginatedResponse<Product>>("get_products", { page, pageSize });
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
