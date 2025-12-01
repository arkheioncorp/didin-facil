import { api } from "@/lib/api";
import type { FavoriteItem, FavoriteList, FavoriteWithProduct } from "@/types";

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

export async function addFavorite(
  productId: string,
  listId?: string,
  notes?: string
): Promise<FavoriteItem> {
  // In non-Tauri environment, use HTTP API
  if (!isTauri()) {
    const response = await api.post<FavoriteItem>("/favorites", {
      product_id: productId,
      list_id: listId,
      notes,
    });
    return {
      id: response.data.id,
      productId: response.data.productId || productId,
      listId: response.data.listId || listId || "default",
      notes: response.data.notes || notes || null,
      addedAt: response.data.addedAt || new Date().toISOString(),
    };
  }

  try {
    return await safeInvoke<FavoriteItem>("add_favorite", { productId, listId, notes });
  } catch (error) {
    console.error("Error adding favorite:", error);
    throw error;
  }
}

export async function removeFavorite(productId: string): Promise<boolean> {
  // In non-Tauri environment, use HTTP API
  if (!isTauri()) {
    await api.delete(`/favorites/${productId}`);
    return true;
  }

  try {
    return await safeInvoke<boolean>("remove_favorite", { productId });
  } catch (error) {
    console.error("Error removing favorite:", error);
    throw error;
  }
}

export async function getFavorites(listId?: string): Promise<FavoriteWithProduct[]> {
  // In non-Tauri environment, use HTTP API
  if (!isTauri()) {
    try {
      const params: Record<string, string> = {};
      if (listId) params.list_id = listId;
      
      const response = await api.get<any[]>("/favorites", { params });
      
      return response.data.map((item: any) => ({
        favorite: {
          id: item.id,
          productId: item.product_id,
          listId: item.list_id,
          notes: item.notes,
          addedAt: item.added_at || item.created_at,
        },
        product: {
          id: item.product?.id || item.product_id,
          tiktokId: item.product?.tiktok_id || "",
          title: item.product?.title || item.product_title || "Produto",
          description: item.product?.description || item.product_description,
          price: item.product?.price || item.product_price || 0,
          originalPrice: item.product?.original_price || item.product_original_price,
          currency: item.product?.currency || "BRL",
          category: item.product?.category || null,
          subcategory: item.product?.subcategory || null,
          sellerName: item.product?.seller_name || item.shop_name || null,
          sellerRating: item.product?.seller_rating || null,
          productRating: item.product?.product_rating || item.product_rating || null,
          reviewsCount: item.product?.reviews_count || 0,
          salesCount: item.product?.sales_count || item.product_sales_count || 0,
          sales7d: item.product?.sales_7d || 0,
          sales30d: item.product?.sales_30d || 0,
          commissionRate: item.product?.commission_rate || null,
          imageUrl: item.product?.image_url || item.product_image_url || null,
          images: item.product?.images || [],
          videoUrl: item.product?.video_url || null,
          productUrl: item.product?.product_url || item.product_url || "",
          affiliateUrl: item.product?.affiliate_url || null,
          hasFreeShipping: item.product?.has_free_shipping || false,
          isTrending: item.product?.is_trending || item.is_trending || false,
          isOnSale: item.product?.is_on_sale || false,
          inStock: item.product?.in_stock ?? true,
          collectedAt: item.product?.collected_at || new Date().toISOString(),
          updatedAt: item.product?.updated_at || new Date().toISOString(),
        },
      }));
    } catch (error) {
      console.error("Error getting favorites via API:", error);
      return [];
    }
  }
  
  try {
    return await safeInvoke<FavoriteWithProduct[]>("get_favorites", { listId });
  } catch (error) {
    console.error("Error getting favorites:", error);
    throw error;
  }
}

export async function createFavoriteList(
  name: string,
  description?: string,
  color?: string,
  icon?: string
): Promise<FavoriteList> {
  try {
    return await safeInvoke<FavoriteList>("create_favorite_list", { name, description, color, icon });
  } catch (error) {
    console.error("Error creating favorite list:", error);
    throw error;
  }
}

export async function getFavoriteLists(): Promise<FavoriteList[]> {
  try {
    return await safeInvoke<FavoriteList[]>("get_favorite_lists");
  } catch (error) {
    console.error("Error getting favorite lists:", error);
    throw error;
  }
}

export async function deleteFavoriteList(listId: string): Promise<boolean> {
  try {
    return await safeInvoke<boolean>("delete_favorite_list", { listId });
  } catch (error) {
    console.error("Error deleting favorite list:", error);
    throw error;
  }
}
