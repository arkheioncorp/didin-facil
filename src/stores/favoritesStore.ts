import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { Product } from "@/types";

interface FavoritesState {
  // Data
  favorites: Product[];
  collections: { id: string; name: string; productIds: string[] }[];
  
  // Actions
  addFavorite: (product: Product) => void;
  removeFavorite: (productId: string) => void;
  toggleFavorite: (product: Product) => void;
  isFavorite: (productId: string) => boolean;
  clearFavorites: () => void;
  
  // Collections
  createCollection: (name: string) => void;
  deleteCollection: (collectionId: string) => void;
  addToCollection: (collectionId: string, productId: string) => void;
  removeFromCollection: (collectionId: string, productId: string) => void;
}

export const useFavoritesStore = create<FavoritesState>()(
  persist(
    (set, get) => ({
      favorites: [],
      collections: [],
      
      addFavorite: (product: Product) =>
        set((state: FavoritesState) => {
          if (state.favorites.some((p: Product) => p.id === product.id)) {
            return state;
          }
          return { favorites: [...state.favorites, product] };
        }),
        
      removeFavorite: (productId: string) =>
        set((state: FavoritesState) => ({
          favorites: state.favorites.filter((p: Product) => p.id !== productId),
        })),
        
      toggleFavorite: (product: Product) => {
        const { favorites, addFavorite, removeFavorite } = get();
        if (favorites.some((p: Product) => p.id === product.id)) {
          removeFavorite(product.id);
        } else {
          addFavorite(product);
        }
      },
      
      isFavorite: (productId: string) => {
        const { favorites } = get();
        return favorites.some((p: Product) => p.id === productId);
      },
      
      clearFavorites: () =>
        set({ favorites: [] }),
        
      createCollection: (name: string) =>
        set((state: FavoritesState) => ({
          collections: [
            ...state.collections,
            { id: Date.now().toString(), name, productIds: [] },
          ],
        })),
        
      deleteCollection: (collectionId: string) =>
        set((state: FavoritesState) => ({
          collections: state.collections.filter(
            (c: { id: string }) => c.id !== collectionId
          ),
        })),
        
      addToCollection: (collectionId: string, productId: string) =>
        set((state: FavoritesState) => ({
          collections: state.collections.map((c: { id: string; name: string; productIds: string[] }) =>
            c.id === collectionId
              ? { ...c, productIds: [...new Set([...c.productIds, productId])] }
              : c
          ),
        })),
        
      removeFromCollection: (collectionId: string, productId: string) =>
        set((state: FavoritesState) => ({
          collections: state.collections.map((c: { id: string; name: string; productIds: string[] }) =>
            c.id === collectionId
              ? { ...c, productIds: c.productIds.filter((id: string) => id !== productId) }
              : c
          ),
        })),
    }),
    {
      name: "tiktrend-favorites",
      storage: createJSONStorage(() => localStorage),
    }
  )
);
