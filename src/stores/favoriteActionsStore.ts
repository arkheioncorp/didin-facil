import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// ============================================
// TYPES
// ============================================

export type FavoriteActionId = 
  | "copy-info" 
  | "copy-link" 
  | "generate-copy" 
  | "whatsapp" 
  | "schedule" 
  | "instagram" 
  | "tiktok" 
  | "youtube" 
  | "seller-bot" 
  | "crm" 
  | "email"
  | "export";

interface FavoriteAction {
  id: FavoriteActionId;
  label: string;
  addedAt: Date;
  usageCount: number;
}

interface FavoriteActionsState {
  favorites: FavoriteAction[];
  maxFavorites: number;
  
  // Actions
  addFavorite: (id: FavoriteActionId, label: string) => void;
  removeFavorite: (id: FavoriteActionId) => void;
  toggleFavorite: (id: FavoriteActionId, label: string) => void;
  isFavorite: (id: FavoriteActionId) => boolean;
  incrementUsage: (id: FavoriteActionId) => void;
  clearFavorites: () => void;
  
  // Getters
  getFavorites: () => FavoriteAction[];
  getMostUsed: (limit?: number) => FavoriteAction[];
  getRecentlyAdded: (limit?: number) => FavoriteAction[];
}

// ============================================
// DEFAULT ACTION LABELS
// ============================================

const ACTION_LABELS: Record<FavoriteActionId, string> = {
  "copy-info": "Copiar Informações",
  "copy-link": "Copiar Link",
  "generate-copy": "Gerar Copy com IA",
  "whatsapp": "Enviar via WhatsApp",
  "schedule": "Agendar Publicação",
  "instagram": "Publicar no Instagram",
  "tiktok": "Publicar no TikTok",
  "youtube": "Enviar para YouTube",
  "seller-bot": "Criar Campanha Bot",
  "crm": "Adicionar ao CRM",
  "email": "Criar Campanha Email",
  "export": "Exportar Produto",
};

// ============================================
// STORE
// ============================================

export const useFavoriteActionsStore = create<FavoriteActionsState>()(
  persist(
    (set, get) => ({
      favorites: [],
      maxFavorites: 8, // Limit favorite actions
      
      addFavorite: (id, label) =>
        set((state) => {
          // Check if already favorite
          if (state.favorites.some((f) => f.id === id)) {
            return state;
          }
          
          // Check max limit
          if (state.favorites.length >= state.maxFavorites) {
            return state;
          }
          
          const newFavorite: FavoriteAction = {
            id,
            label: label || ACTION_LABELS[id],
            addedAt: new Date(),
            usageCount: 0,
          };
          
          return { favorites: [...state.favorites, newFavorite] };
        }),
      
      removeFavorite: (id) =>
        set((state) => ({
          favorites: state.favorites.filter((f) => f.id !== id),
        })),
      
      toggleFavorite: (id, label) => {
        const { favorites, addFavorite, removeFavorite } = get();
        if (favorites.some((f) => f.id === id)) {
          removeFavorite(id);
        } else {
          addFavorite(id, label);
        }
      },
      
      isFavorite: (id) => {
        return get().favorites.some((f) => f.id === id);
      },
      
      incrementUsage: (id) =>
        set((state) => ({
          favorites: state.favorites.map((f) =>
            f.id === id ? { ...f, usageCount: f.usageCount + 1 } : f
          ),
        })),
      
      clearFavorites: () => set({ favorites: [] }),
      
      getFavorites: () => get().favorites,
      
      getMostUsed: (limit = 5) => {
        return [...get().favorites]
          .sort((a, b) => b.usageCount - a.usageCount)
          .slice(0, limit);
      },
      
      getRecentlyAdded: (limit = 5) => {
        return [...get().favorites]
          .sort((a, b) => 
            new Date(b.addedAt).getTime() - new Date(a.addedAt).getTime()
          )
          .slice(0, limit);
      },
    }),
    {
      name: "favorite-actions-storage",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        favorites: state.favorites.map((f) => ({
          ...f,
          addedAt: f.addedAt instanceof Date ? f.addedAt.toISOString() : f.addedAt,
        })),
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.favorites = state.favorites.map((f: FavoriteAction & { addedAt: string | Date }) => ({
            ...f,
            addedAt: typeof f.addedAt === "string" ? new Date(f.addedAt) : f.addedAt,
          }));
        }
      },
    }
  )
);

// ============================================
// HELPER HOOK
// ============================================

/**
 * Hook to get favorite action utilities
 */
export function useFavoriteAction(actionId: FavoriteActionId) {
  const { isFavorite, toggleFavorite, incrementUsage } = useFavoriteActionsStore();
  
  const favorite = isFavorite(actionId);
  const label = ACTION_LABELS[actionId];
  
  const toggle = () => toggleFavorite(actionId, label);
  const track = () => incrementUsage(actionId);
  
  return {
    isFavorite: favorite,
    toggle,
    trackUsage: track,
    label,
  };
}
