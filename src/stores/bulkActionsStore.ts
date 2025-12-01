import { create } from "zustand";
import type { Product } from "@/types";
import type { ActionId } from "@/components/product/actions/types";

// ============================================
// TYPES
// ============================================

export interface BulkActionResult {
  productId: string;
  productTitle: string;
  success: boolean;
  error?: string;
  timestamp: string;
}

export interface BulkActionJob {
  id: string;
  actionId: ActionId;
  products: Product[];
  status: "pending" | "running" | "completed" | "cancelled";
  results: BulkActionResult[];
  progress: number;
  startedAt?: string;
  completedAt?: string;
  config?: Record<string, unknown>;
}

export interface BulkActionsState {
  // Selection
  selectedProducts: Product[];
  selectProduct: (product: Product) => void;
  deselectProduct: (productId: string) => void;
  toggleProduct: (product: Product) => void;
  selectAll: (products: Product[]) => void;
  deselectAll: () => void;
  isSelected: (productId: string) => boolean;
  
  // Jobs
  jobs: BulkActionJob[];
  currentJob: BulkActionJob | null;
  
  // Job actions
  createJob: (actionId: ActionId, config?: Record<string, unknown>) => string;
  startJob: (jobId: string, executor: (product: Product, config?: Record<string, unknown>) => Promise<void>) => Promise<void>;
  cancelJob: (jobId: string) => void;
  clearJob: (jobId: string) => void;
  clearCompletedJobs: () => void;
  
  // Getters
  getJob: (jobId: string) => BulkActionJob | undefined;
  getJobHistory: () => BulkActionJob[];
}

// ============================================
// STORE
// ============================================

export const useBulkActionsStore = create<BulkActionsState>((set, get) => ({
  selectedProducts: [],
  jobs: [],
  currentJob: null,

  selectProduct: (product) => {
    set((state) => {
      if (state.selectedProducts.find((p) => p.id === product.id)) {
        return state; // Already selected
      }
      return {
        selectedProducts: [...state.selectedProducts, product],
      };
    });
  },

  deselectProduct: (productId) => {
    set((state) => ({
      selectedProducts: state.selectedProducts.filter((p) => p.id !== productId),
    }));
  },

  toggleProduct: (product) => {
    const isSelected = get().selectedProducts.find((p) => p.id === product.id);
    if (isSelected) {
      get().deselectProduct(product.id);
    } else {
      get().selectProduct(product);
    }
  },

  selectAll: (products) => {
    set({ selectedProducts: products });
  },

  deselectAll: () => {
    set({ selectedProducts: [] });
  },

  isSelected: (productId) => {
    return !!get().selectedProducts.find((p) => p.id === productId);
  },

  createJob: (actionId, config) => {
    const id = `job_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    const job: BulkActionJob = {
      id,
      actionId,
      products: [...get().selectedProducts],
      status: "pending",
      results: [],
      progress: 0,
      config,
    };

    set((state) => ({
      jobs: [job, ...state.jobs],
    }));

    return id;
  },

  startJob: async (jobId, executor) => {
    const job = get().jobs.find((j) => j.id === jobId);
    if (!job || job.status !== "pending") return;

    set((state) => ({
      jobs: state.jobs.map((j) =>
        j.id === jobId
          ? { ...j, status: "running" as const, startedAt: new Date().toISOString() }
          : j
      ),
      currentJob: { ...job, status: "running", startedAt: new Date().toISOString() },
    }));

    const results: BulkActionResult[] = [];

    for (let i = 0; i < job.products.length; i++) {
      // Check if cancelled
      const currentState = get();
      const currentJob = currentState.jobs.find((j) => j.id === jobId);
      if (currentJob?.status === "cancelled") break;

      const product = job.products[i];
      const timestamp = new Date().toISOString();

      try {
        await executor(product, job.config);
        results.push({
          productId: product.id,
          productTitle: product.title,
          success: true,
          timestamp,
        });
      } catch (error) {
        results.push({
          productId: product.id,
          productTitle: product.title,
          success: false,
          error: error instanceof Error ? error.message : "Erro desconhecido",
          timestamp,
        });
      }

      // Update progress
      const progress = Math.round(((i + 1) / job.products.length) * 100);
      set((state) => ({
        jobs: state.jobs.map((j) =>
          j.id === jobId
            ? { ...j, results: [...results], progress }
            : j
        ),
        currentJob: state.currentJob?.id === jobId
          ? { ...state.currentJob, results: [...results], progress }
          : state.currentJob,
      }));

      // Small delay between actions to prevent rate limiting
      await new Promise((resolve) => setTimeout(resolve, 500));
    }

    // Mark as completed
    set((state) => ({
      jobs: state.jobs.map((j) =>
        j.id === jobId
          ? {
              ...j,
              status: j.status === "cancelled" ? "cancelled" : "completed",
              results,
              progress: 100,
              completedAt: new Date().toISOString(),
            }
          : j
      ),
      currentJob: null,
      selectedProducts: [], // Clear selection after job completes
    }));
  },

  cancelJob: (jobId) => {
    set((state) => ({
      jobs: state.jobs.map((j) =>
        j.id === jobId && j.status === "running"
          ? { ...j, status: "cancelled" as const }
          : j
      ),
    }));
  },

  clearJob: (jobId) => {
    set((state) => ({
      jobs: state.jobs.filter((j) => j.id !== jobId),
    }));
  },

  clearCompletedJobs: () => {
    set((state) => ({
      jobs: state.jobs.filter((j) => j.status === "running" || j.status === "pending"),
    }));
  },

  getJob: (jobId) => {
    return get().jobs.find((j) => j.id === jobId);
  },

  getJobHistory: () => {
    return get().jobs.filter((j) => j.status === "completed" || j.status === "cancelled");
  },
}));

// ============================================
// HOOKS
// ============================================

export const useProductSelection = () => {
  const { selectedProducts, selectProduct, deselectProduct, toggleProduct, selectAll, deselectAll, isSelected } = useBulkActionsStore();
  
  return {
    selectedProducts,
    selectedCount: selectedProducts.length,
    selectProduct,
    deselectProduct,
    toggleProduct,
    selectAll,
    deselectAll,
    isSelected,
    hasSelection: selectedProducts.length > 0,
  };
};

export const useBulkJob = (jobId: string) => {
  const job = useBulkActionsStore((state) => state.jobs.find((j) => j.id === jobId));
  const { cancelJob, clearJob } = useBulkActionsStore();
  
  return {
    job,
    cancel: () => cancelJob(jobId),
    clear: () => clearJob(jobId),
    successCount: job?.results.filter((r) => r.success).length ?? 0,
    failureCount: job?.results.filter((r) => !r.success).length ?? 0,
  };
};
