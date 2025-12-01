import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// ============================================
// TYPES
// ============================================

export type TemplateType = 
  | "copy" 
  | "whatsapp" 
  | "instagram" 
  | "tiktok" 
  | "youtube" 
  | "email" 
  | "schedule";

export interface ActionTemplate {
  id: string;
  name: string;
  description?: string;
  type: TemplateType;
  data: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  usageCount: number;
  isFavorite: boolean;
}

export interface TemplatesState {
  templates: ActionTemplate[];
  
  // Actions
  addTemplate: (template: Omit<ActionTemplate, "id" | "createdAt" | "updatedAt" | "usageCount">) => string;
  updateTemplate: (id: string, updates: Partial<Omit<ActionTemplate, "id" | "createdAt">>) => void;
  deleteTemplate: (id: string) => void;
  duplicateTemplate: (id: string) => string | null;
  toggleFavorite: (id: string) => void;
  incrementUsage: (id: string) => void;
  
  // Getters
  getTemplatesByType: (type: TemplateType) => ActionTemplate[];
  getFavoriteTemplates: () => ActionTemplate[];
  getMostUsedTemplates: (limit?: number) => ActionTemplate[];
  getRecentTemplates: (limit?: number) => ActionTemplate[];
  searchTemplates: (query: string) => ActionTemplate[];
}

// ============================================
// STORE
// ============================================

export const useTemplatesStore = create<TemplatesState>()(
  persist(
    (set, get) => ({
      templates: [],

      addTemplate: (template) => {
        const id = `template_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
        const now = new Date().toISOString();
        
        const newTemplate: ActionTemplate = {
          ...template,
          id,
          createdAt: now,
          updatedAt: now,
          usageCount: 0,
          isFavorite: template.isFavorite ?? false,
        };

        set((state) => ({
          templates: [newTemplate, ...state.templates],
        }));

        return id;
      },

      updateTemplate: (id, updates) => {
        set((state) => ({
          templates: state.templates.map((template) =>
            template.id === id
              ? { 
                  ...template, 
                  ...updates, 
                  updatedAt: new Date().toISOString() 
                }
              : template
          ),
        }));
      },

      deleteTemplate: (id) => {
        set((state) => ({
          templates: state.templates.filter((template) => template.id !== id),
        }));
      },

      duplicateTemplate: (id) => {
        const template = get().templates.find((t) => t.id === id);
        if (!template) return null;

        return get().addTemplate({
          name: `${template.name} (cópia)`,
          description: template.description,
          type: template.type,
          data: { ...template.data },
          isFavorite: false,
        });
      },

      toggleFavorite: (id) => {
        set((state) => ({
          templates: state.templates.map((template) =>
            template.id === id
              ? { ...template, isFavorite: !template.isFavorite }
              : template
          ),
        }));
      },

      incrementUsage: (id) => {
        set((state) => ({
          templates: state.templates.map((template) =>
            template.id === id
              ? { ...template, usageCount: template.usageCount + 1 }
              : template
          ),
        }));
      },

      getTemplatesByType: (type) => {
        return get().templates.filter((template) => template.type === type);
      },

      getFavoriteTemplates: () => {
        return get().templates.filter((template) => template.isFavorite);
      },

      getMostUsedTemplates: (limit = 5) => {
        return [...get().templates]
          .sort((a, b) => b.usageCount - a.usageCount)
          .slice(0, limit);
      },

      getRecentTemplates: (limit = 5) => {
        return [...get().templates]
          .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
          .slice(0, limit);
      },

      searchTemplates: (query) => {
        const lowerQuery = query.toLowerCase();
        return get().templates.filter(
          (template) =>
            template.name.toLowerCase().includes(lowerQuery) ||
            template.description?.toLowerCase().includes(lowerQuery)
        );
      },
    }),
    {
      name: "action-templates-storage",
      storage: createJSONStorage(() => localStorage),
    }
  )
);

// ============================================
// HOOKS
// ============================================

export const useTemplate = (id: string) => {
  const template = useTemplatesStore((state) => 
    state.templates.find((t) => t.id === id)
  );
  const { updateTemplate, deleteTemplate, toggleFavorite, incrementUsage } = useTemplatesStore();
  
  return {
    template,
    update: (updates: Partial<Omit<ActionTemplate, "id" | "createdAt">>) => updateTemplate(id, updates),
    delete: () => deleteTemplate(id),
    toggleFavorite: () => toggleFavorite(id),
    incrementUsage: () => incrementUsage(id),
  };
};

export const useTemplatesByType = (type: TemplateType) => {
  return useTemplatesStore((state) => state.getTemplatesByType(type));
};
