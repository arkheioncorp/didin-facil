import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { ActionHistoryEntry, ActionHistoryType } from "@/components/product/actions/types";

// ============================================
// ACTION LABELS MAP
// ============================================

const ACTION_LABELS: Record<ActionHistoryType, string> = {
  copy_info: "Copiou informações",
  copy_link: "Copiou link",
  generate_copy: "Gerou copy com IA",
  whatsapp: "Enviou via WhatsApp",
  schedule: "Agendou publicação",
  instagram: "Publicou no Instagram",
  tiktok: "Publicou no TikTok",
  youtube: "Enviou para YouTube",
  seller_bot: "Criou campanha Seller Bot",
  crm: "Adicionou ao CRM",
  email: "Criou campanha de email",
  export: "Exportou produto",
};

// ============================================
// STORE INTERFACE
// ============================================

interface ActionHistoryState {
  entries: ActionHistoryEntry[];
  maxEntries: number;
  
  // Actions
  addEntry: (entry: Omit<ActionHistoryEntry, "id" | "timestamp" | "actionLabel">) => void;
  clearHistory: () => void;
  clearProductHistory: (productId: string) => void;
  
  // Getters
  getHistoryByProduct: (productId: string) => ActionHistoryEntry[];
  getRecentHistory: (limit?: number) => ActionHistoryEntry[];
  getHistoryByType: (actionType: ActionHistoryType) => ActionHistoryEntry[];
  getSuccessRate: (productId?: string) => number;
  getMostUsedActions: (limit?: number) => Array<{ type: ActionHistoryType; count: number; label: string }>;
}

// ============================================
// STORE IMPLEMENTATION
// ============================================

export const useActionHistoryStore = create<ActionHistoryState>()(
  persist(
    (set, get) => ({
      entries: [],
      maxEntries: 500, // Limitar para não sobrecarregar localStorage
      
      addEntry: (entry) =>
        set((state) => {
          const newEntry: ActionHistoryEntry = {
            ...entry,
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            timestamp: new Date(),
            actionLabel: ACTION_LABELS[entry.actionType],
          };
          
          // Manter apenas as últimas N entradas
          const updatedEntries = [newEntry, ...state.entries].slice(0, state.maxEntries);
          
          return { entries: updatedEntries };
        }),
      
      clearHistory: () => set({ entries: [] }),
      
      clearProductHistory: (productId) =>
        set((state) => ({
          entries: state.entries.filter((e) => e.productId !== productId),
        })),
      
      getHistoryByProduct: (productId) => {
        return get().entries.filter((e) => e.productId === productId);
      },
      
      getRecentHistory: (limit = 20) => {
        return get().entries.slice(0, limit);
      },
      
      getHistoryByType: (actionType) => {
        return get().entries.filter((e) => e.actionType === actionType);
      },
      
      getSuccessRate: (productId) => {
        const entries = productId
          ? get().entries.filter((e) => e.productId === productId)
          : get().entries;
        
        if (entries.length === 0) return 100;
        
        const successful = entries.filter((e) => e.success).length;
        return Math.round((successful / entries.length) * 100);
      },
      
      getMostUsedActions: (limit = 5) => {
        const entries = get().entries;
        const counts: Record<ActionHistoryType, number> = {} as Record<ActionHistoryType, number>;
        
        entries.forEach((e) => {
          counts[e.actionType] = (counts[e.actionType] || 0) + 1;
        });
        
        return Object.entries(counts)
          .map(([type, count]) => ({
            type: type as ActionHistoryType,
            count,
            label: ACTION_LABELS[type as ActionHistoryType],
          }))
          .sort((a, b) => b.count - a.count)
          .slice(0, limit);
      },
    }),
    {
      name: "action-history-storage",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        entries: state.entries.map((e) => ({
          ...e,
          timestamp: e.timestamp.toISOString(),
        })),
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          // Convert timestamp strings back to Date objects
          state.entries = state.entries.map((e: ActionHistoryEntry & { timestamp: string | Date }) => ({
            ...e,
            timestamp: typeof e.timestamp === "string" ? new Date(e.timestamp) : e.timestamp,
          }));
        }
      },
    }
  )
);

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Formatar timestamp para exibição
 */
export function formatActionTimestamp(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMinutes < 1) return "Agora";
  if (diffMinutes < 60) return `${diffMinutes}m atrás`;
  if (diffHours < 24) return `${diffHours}h atrás`;
  if (diffDays < 7) return `${diffDays}d atrás`;
  
  return date.toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
  });
}

/**
 * Obter ícone para tipo de ação
 */
export function getActionIcon(type: ActionHistoryType): string {
  const icons: Record<ActionHistoryType, string> = {
    copy_info: "📋",
    copy_link: "🔗",
    generate_copy: "✨",
    whatsapp: "💬",
    schedule: "📅",
    instagram: "📸",
    tiktok: "🎵",
    youtube: "▶️",
    seller_bot: "🤖",
    crm: "💼",
    email: "📧",
    export: "📥",
  };
  return icons[type] || "📌";
}
