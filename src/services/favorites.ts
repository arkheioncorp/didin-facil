import { invoke } from "@tauri-apps/api/core";
import type { FavoriteItem, FavoriteList, FavoriteWithProduct } from "@/types";

export async function addFavorite(
  productId: string,
  listId?: string,
  notes?: string
): Promise<FavoriteItem> {
  try {
    return await invoke<FavoriteItem>("add_favorite", { productId, listId, notes });
  } catch (error) {
    console.error("Error adding favorite:", error);
    throw error;
  }
}

export async function removeFavorite(productId: string): Promise<boolean> {
  try {
    return await invoke<boolean>("remove_favorite", { productId });
  } catch (error) {
    console.error("Error removing favorite:", error);
    throw error;
  }
}

export async function getFavorites(listId?: string): Promise<FavoriteWithProduct[]> {
  try {
    return await invoke<FavoriteWithProduct[]>("get_favorites", { listId });
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
    return await invoke<FavoriteList>("create_favorite_list", { name, description, color, icon });
  } catch (error) {
    console.error("Error creating favorite list:", error);
    throw error;
  }
}

export async function getFavoriteLists(): Promise<FavoriteList[]> {
  try {
    return await invoke<FavoriteList[]>("get_favorite_lists");
  } catch (error) {
    console.error("Error getting favorite lists:", error);
    throw error;
  }
}

export async function deleteFavoriteList(listId: string): Promise<boolean> {
  try {
    return await invoke<boolean>("delete_favorite_list", { listId });
  } catch (error) {
    console.error("Error deleting favorite list:", error);
    throw error;
  }
}
