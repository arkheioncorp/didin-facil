import { create } from "zustand";
import type { Product } from "@/types";


interface ProductsState {
  // Data
  products: Product[];
  selectedProduct: Product | null;
  total: number;
  page: number;
  hasMore: boolean;

  // Loading states
  isLoading: boolean;
  isLoadingMore: boolean;
  error: string | null;

  // Actions
  setProducts: (products: Product[], total: number, hasMore: boolean) => void;
  appendProducts: (products: Product[]) => void;
  setSelectedProduct: (product: Product | null) => void;
  setPage: (page: number) => void;
  setLoading: (isLoading: boolean) => void;
  setLoadingMore: (isLoadingMore: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  products: [],
  selectedProduct: null,
  total: 0,
  page: 1,
  hasMore: true,
  isLoading: false,
  isLoadingMore: false,
  error: null,
};

export const useProductsStore = create<ProductsState>((set) => ({
  ...initialState,

  setProducts: (products, total, hasMore) =>
    set({ products, total, hasMore, page: 1 }),

  appendProducts: (newProducts) =>
    set((state) => ({
      products: [...state.products, ...newProducts],
      page: state.page + 1,
    })),

  setSelectedProduct: (product) =>
    set({ selectedProduct: product }),

  setPage: (page) =>
    set({ page }),

  setLoading: (isLoading) =>
    set({ isLoading }),

  setLoadingMore: (isLoadingMore) =>
    set({ isLoadingMore }),

  setError: (error) =>
    set({ error }),

  reset: () =>
    set(initialState),
}));
