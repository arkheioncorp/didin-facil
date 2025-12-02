/**
 * useProductsPage Hook
 * 
 * Custom hook that encapsulates all the business logic for the Products page.
 * Handles loading, filtering, sorting, pagination, favorites, and selection.
 * 
 * @performance
 * - Uses useMemo for expensive calculations
 * - Debounced search not implemented here (use useDebounce separately)
 * - Optimized re-render prevention with useCallback
 */

import * as React from "react";
import { useSearchParams } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { useFavoritesStore } from "@/stores";
import { useBulkActionsStore, useProductSelection } from "@/stores/bulkActionsStore";
import { analytics } from "@/lib/analytics";
import { getProducts } from "@/services/products";
import { 
  addProductToFavorites, 
  removeProductFromFavorites,
  exportProductsToFile,
  fetchCategories,
  type CategoryInfo 
} from "@/services/api/products";
import type { Product } from "@/types";
import type { ViewMode, GridScale, ExportFormat, FilterState } from "@/components/product";

// ============================================
// CONSTANTS
// ============================================

const PAGE_SIZE = 24;

const DEFAULT_CATEGORIES: CategoryInfo[] = [
  { name: "Todas", slug: "all", count: 0 },
  { name: "Eletrônicos", slug: "electronics", count: 0 },
  { name: "Moda", slug: "fashion", count: 0 },
  { name: "Casa", slug: "home", count: 0 },
  { name: "Beleza", slug: "beauty", count: 0 },
  { name: "Esportes", slug: "sports", count: 0 },
];

export const SORT_OPTIONS = [
  { value: "sales_30d", label: "Mais Vendidos" },
  { value: "newest", label: "Mais Recentes" },
  { value: "price_asc", label: "Menor Preço" },
  { value: "price_desc", label: "Maior Preço" },
  { value: "rating", label: "Melhor Avaliação" },
];

// ============================================
// TYPES
// ============================================

interface UseProductsPageReturn {
  // Data
  products: Product[];
  categories: CategoryInfo[];
  total: number;
  totalPages: number;
  
  // Loading states
  isLoading: boolean;
  isLoadingMore: boolean;
  isRefreshing: boolean;
  isExporting: boolean;
  error: string | null;
  
  // Filter/Sort values from URL
  page: number;
  sort: string;
  sortFromUrl: string | null;
  category: string;
  minPrice: string;
  maxPrice: string;
  minSales: string;
  searchQuery: string;
  showTrending: boolean;
  showOnSale: boolean;
  showFreeShipping: boolean;
  hasActiveFilters: boolean;
  
  // View settings
  viewMode: ViewMode;
  gridScale: GridScale;
  
  // Selection
  selectedProducts: Set<string>;
  bulkSelectedProducts: Product[];
  
  // Modal state
  selectedProduct: Product | null;
  showDetailModal: boolean;
  showExportModal: boolean;
  
  // Stats
  stats: {
    total: number;
    trending: number;
    onSale: number;
    freeShipping: number;
  };
  
  // Handlers
  handleSortChange: (value: string) => void;
  handleCategoryChange: (value: string) => void;
  handleApplyFilters: (filters: FilterState) => void;
  handleClearFilters: () => void;
  handlePageChange: (newPage: number) => void;
  handleRefresh: () => Promise<void>;
  handleFavorite: (product: Product) => Promise<void>;
  handleExport: (format: ExportFormat) => Promise<void>;
  handleSelectProduct: (productId: string, checked: boolean) => void;
  handleSelectAll: (checked: boolean) => void;
  handleBulkFavorite: () => Promise<void>;
  handleProductClick: (product: Product) => void;
  handleCloseModal: () => void;
  setViewMode: (mode: ViewMode) => void;
  setGridScale: (scale: GridScale) => void;
  setShowExportModal: (show: boolean) => void;
  loadMoreProducts: () => Promise<void>;
  isFavorite: (productId: string) => boolean;
}

// ============================================
// HOOK
// ============================================

export function useProductsPage(): UseProductsPageReturn {
  const [searchParams, setSearchParams] = useSearchParams();
  const { isFavorite, addFavorite: addToFavorites, removeFavorite: removeFromFavorites } = useFavoritesStore();
  const { toast } = useToast();
  
  // Bulk actions store
  const { selectProduct, deselectProduct, deselectAll } = useBulkActionsStore();
  const { selectedProducts: bulkSelectedProducts } = useProductSelection();
  
  // Core state
  const [products, setProducts] = React.useState<Product[]>([]);
  const [categories, setCategories] = React.useState<CategoryInfo[]>(DEFAULT_CATEGORIES);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isLoadingMore, setIsLoadingMore] = React.useState(false);
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [isExporting, setIsExporting] = React.useState(false);
  const [total, setTotal] = React.useState(0);
  const [totalPages, setTotalPages] = React.useState(1);
  const [hasMore, setHasMore] = React.useState(true);
  const [currentPage, setCurrentPage] = React.useState(1);

  // URL-synced state
  const page = parseInt(searchParams.get("page") || "1", 10);
  const sortFromUrl = searchParams.get("sort");
  const sort = sortFromUrl || "sales_30d";
  const category = searchParams.get("category") || "all";
  const minPrice = searchParams.get("min_price") || "";
  const maxPrice = searchParams.get("max_price") || "";
  const minSales = searchParams.get("min_sales") || "";
  const searchQuery = searchParams.get("q") || "";
  const showTrending = searchParams.get("trending") === "true";
  const showOnSale = searchParams.get("on_sale") === "true";
  const showFreeShipping = searchParams.get("free_shipping") === "true";

  // View settings with localStorage
  const [viewMode, setViewMode] = React.useState<ViewMode>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("products-view-mode") as ViewMode) || "grid";
    }
    return "grid";
  });

  const [gridScale, setGridScale] = React.useState<GridScale>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("products-grid-scale") as GridScale) || "medium";
    }
    return "medium";
  });

  // Selection state
  const [selectedProducts, setSelectedProducts] = React.useState<Set<string>>(new Set());
  
  // Modal state
  const [selectedProduct, setSelectedProduct] = React.useState<Product | null>(null);
  const [showDetailModal, setShowDetailModal] = React.useState(false);
  const [showExportModal, setShowExportModal] = React.useState(false);

  // Persist view settings
  React.useEffect(() => {
    localStorage.setItem("products-view-mode", viewMode);
  }, [viewMode]);

  React.useEffect(() => {
    localStorage.setItem("products-grid-scale", gridScale);
  }, [gridScale]);

  // Load categories on mount
  React.useEffect(() => {
    const loadCategories = async () => {
      try {
        const cats = await fetchCategories();
        if (cats.length > 0) {
          setCategories(cats);
        }
      } catch (err) {
        console.warn("Error loading categories, using defaults:", err);
      }
    };
    loadCategories();
  }, []);

  // Build API sort params
  const getSortParams = React.useCallback(() => {
    switch (sort) {
      case "price_asc":
        return { sortBy: "price", sortOrder: "asc" };
      case "price_desc":
        return { sortBy: "price", sortOrder: "desc" };
      case "rating":
        return { sortBy: "rating", sortOrder: "desc" };
      case "newest":
        return { sortBy: "newest", sortOrder: "desc" };
      case "sales_30d":
      default:
        return { sortBy: "sales_30d", sortOrder: "desc" };
    }
  }, [sort]);

  // Apply client-side filters
  const applyClientFilters = React.useCallback((data: Product[]): Product[] => {
    let filtered = [...data];
    
    if (showTrending) {
      filtered = filtered.filter(p => p.isTrending);
    }
    if (showOnSale) {
      filtered = filtered.filter(p => p.isOnSale);
    }
    if (showFreeShipping) {
      filtered = filtered.filter(p => p.hasFreeShipping);
    }
    
    return filtered;
  }, [showTrending, showOnSale, showFreeShipping]);

  // Load products
  React.useEffect(() => {
    const loadProducts = async () => {
      setIsLoading(true);
      setError(null);
      setCurrentPage(1);
      
      try {
        const { sortBy, sortOrder } = getSortParams();
        
        const response = await getProducts(1, PAGE_SIZE, {
          category: category !== "all" ? category : undefined,
          minPrice: minPrice ? parseFloat(minPrice) : undefined,
          maxPrice: maxPrice ? parseFloat(maxPrice) : undefined,
          minSales: minSales ? parseInt(minSales, 10) : undefined,
          sortBy,
          sortOrder,
        });
        
        const filteredProducts = applyClientFilters(response.data);
        setProducts(filteredProducts);
        setTotal(response.total);
        setTotalPages(Math.ceil(response.total / response.pageSize));
        setHasMore(response.hasMore);
      } catch (err) {
        console.error("Error loading products:", err);
        setError("Erro ao carregar produtos. Tente novamente.");
      } finally {
        setIsLoading(false);
      }
    };

    loadProducts();
  }, [sort, category, minPrice, maxPrice, minSales, showTrending, showOnSale, showFreeShipping, getSortParams, applyClientFilters]);

  // Load more products (infinite scroll)
  const loadMoreProducts = React.useCallback(async () => {
    if (isLoadingMore || !hasMore) return;

    setIsLoadingMore(true);
    try {
      const nextPage = currentPage + 1;
      const { sortBy, sortOrder } = getSortParams();
      
      const response = await getProducts(nextPage, PAGE_SIZE, {
        category: category !== "all" ? category : undefined,
        minPrice: minPrice ? parseFloat(minPrice) : undefined,
        maxPrice: maxPrice ? parseFloat(maxPrice) : undefined,
        minSales: minSales ? parseInt(minSales, 10) : undefined,
        sortBy,
        sortOrder,
      });
      
      const filteredNewProducts = applyClientFilters(response.data);
      
      setProducts(prev => [...prev, ...filteredNewProducts]);
      setCurrentPage(nextPage);
      setHasMore(response.hasMore);
    } catch (err) {
      console.error("Error loading more products:", err);
    } finally {
      setIsLoadingMore(false);
    }
  }, [currentPage, hasMore, isLoadingMore, category, minPrice, maxPrice, minSales, getSortParams, applyClientFilters]);

  // Refresh products
  const handleRefresh = React.useCallback(async () => {
    setIsRefreshing(true);
    try {
      const { sortBy, sortOrder } = getSortParams();
      
      const response = await getProducts(1, PAGE_SIZE, {
        category: category !== "all" ? category : undefined,
        minPrice: minPrice ? parseFloat(minPrice) : undefined,
        maxPrice: maxPrice ? parseFloat(maxPrice) : undefined,
        minSales: minSales ? parseInt(minSales, 10) : undefined,
        sortBy,
        sortOrder,
      });
      
      const filteredProducts = applyClientFilters(response.data);
      setProducts(filteredProducts);
      setTotal(response.total);
      setCurrentPage(1);
      setHasMore(response.hasMore);
      
      toast({
        title: "Atualizado!",
        description: `${response.total} produtos carregados.`,
      });
    } catch (err) {
      console.error("Error refreshing products:", err);
      toast({
        title: "Erro",
        description: "Não foi possível atualizar os produtos.",
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  }, [category, minPrice, maxPrice, minSales, getSortParams, applyClientFilters, toast]);

  // URL update helper
  const updateSearchParams = React.useCallback((updates: Record<string, string | undefined>) => {
    const newParams = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, value]) => {
      if (value) {
        newParams.set(key, value);
      } else {
        newParams.delete(key);
      }
    });
    setSearchParams(newParams);
  }, [searchParams, setSearchParams]);

  const handleSortChange = React.useCallback((value: string) => {
    updateSearchParams({ sort: value, page: "1" });
  }, [updateSearchParams]);

  const handleCategoryChange = React.useCallback((value: string) => {
    updateSearchParams({ 
      category: value !== "all" ? value : undefined, 
      page: "1" 
    });
  }, [updateSearchParams]);

  const handleApplyFilters = React.useCallback((filters: FilterState) => {
    updateSearchParams({
      min_price: filters.minPrice || undefined,
      max_price: filters.maxPrice || undefined,
      min_sales: filters.minSales || undefined,
      trending: filters.trending ? "true" : undefined,
      on_sale: filters.onSale ? "true" : undefined,
      free_shipping: filters.freeShipping ? "true" : undefined,
      page: "1",
    });
  }, [updateSearchParams]);

  const handleClearFilters = React.useCallback(() => {
    setSearchParams(new URLSearchParams());
  }, [setSearchParams]);

  const handlePageChange = React.useCallback((newPage: number) => {
    updateSearchParams({ page: String(newPage) });
  }, [updateSearchParams]);

  // Favorite handlers
  const handleFavorite = React.useCallback(async (product: Product) => {
    try {
      if (isFavorite(product.id)) {
        const success = await removeProductFromFavorites(product.id);
        if (success) {
          removeFromFavorites(product.id);
        }
      } else {
        const success = await addProductToFavorites(product.id);
        if (success) {
          addToFavorites(product);
        }
      }
    } catch (err) {
      console.error("Error toggling favorite:", err);
      toast({
        title: "Erro",
        description: "Não foi possível atualizar favoritos.",
        variant: "destructive",
      });
    }
  }, [isFavorite, removeFromFavorites, addToFavorites, toast]);

  // Export handler
  const handleExport = React.useCallback(async (format: ExportFormat) => {
    const productsToExport = selectedProducts.size > 0 
      ? products.filter(p => selectedProducts.has(p.id))
      : products;
    
    if (productsToExport.length === 0) return;

    setIsExporting(true);
    try {
      analytics.track('export_performed', {
        format,
        count: productsToExport.length
      });

      const productIds = productsToExport.map(p => p.id);
      await exportProductsToFile(productIds, format);
      toast({ title: "Exportado!", description: `${productsToExport.length} produtos exportados com sucesso!` });
      setShowExportModal(false);
      setSelectedProducts(new Set());
    } catch (err) {
      console.error("Error exporting:", err);
      toast({
        title: "Erro",
        description: "Não foi possível exportar os produtos.",
        variant: "destructive",
      });
    } finally {
      setIsExporting(false);
    }
  }, [products, selectedProducts, toast]);

  // Selection handlers
  const handleSelectProduct = React.useCallback((productId: string, checked: boolean) => {
    const product = products.find(p => p.id === productId);
    if (!product) return;
    
    if (checked) {
      selectProduct(product);
    } else {
      deselectProduct(productId);
    }
    
    setSelectedProducts(prev => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(productId);
      } else {
        newSet.delete(productId);
      }
      return newSet;
    });
  }, [products, selectProduct, deselectProduct]);

  const handleSelectAll = React.useCallback((checked: boolean) => {
    if (checked) {
      products.forEach(p => selectProduct(p));
      setSelectedProducts(new Set(products.map(p => p.id)));
    } else {
      deselectAll();
      setSelectedProducts(new Set());
    }
  }, [products, selectProduct, deselectAll]);

  const handleBulkFavorite = React.useCallback(async () => {
    try {
      for (const productId of selectedProducts) {
        const product = products.find(p => p.id === productId);
        if (product && !isFavorite(productId)) {
          const success = await addProductToFavorites(productId);
          if (success) {
            addToFavorites(product);
          }
        }
      }
      toast({ title: "Adicionado!", description: `${selectedProducts.size} produtos adicionados aos favoritos!` });
      setSelectedProducts(new Set());
    } catch (err) {
      console.error("Error bulk adding favorites:", err);
    }
  }, [products, selectedProducts, isFavorite, addToFavorites, toast]);

  // Modal handlers
  const handleProductClick = React.useCallback((product: Product) => {
    setSelectedProduct(product);
    setShowDetailModal(true);
  }, []);

  const handleCloseModal = React.useCallback(() => {
    setShowDetailModal(false);
    setSelectedProduct(null);
  }, []);

  // Handle escape key for modal
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && showDetailModal) {
        handleCloseModal();
      }
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [showDetailModal, handleCloseModal]);

  // Handle window scroll for infinite scroll
  React.useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;
      const threshold = 200;

      if (scrollPosition >= documentHeight - threshold && hasMore && !isLoadingMore) {
        loadMoreProducts();
      }
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [loadMoreProducts, hasMore, isLoadingMore]);

  // Stats calculations
  const stats = React.useMemo(() => ({
    total: total,
    trending: products.filter(p => p.isTrending).length,
    onSale: products.filter(p => p.isOnSale).length,
    freeShipping: products.filter(p => p.hasFreeShipping).length,
  }), [products, total]);

  // Check if any filter is active
  const hasActiveFilters = category !== "all" || !!minPrice || !!maxPrice || !!minSales || showTrending || showOnSale || showFreeShipping;

  return {
    // Data
    products,
    categories,
    total,
    totalPages,
    
    // Loading states
    isLoading,
    isLoadingMore,
    isRefreshing,
    isExporting,
    error,
    
    // Filter/Sort values
    page,
    sort,
    sortFromUrl,
    category,
    minPrice,
    maxPrice,
    minSales,
    searchQuery,
    showTrending,
    showOnSale,
    showFreeShipping,
    hasActiveFilters,
    
    // View settings
    viewMode,
    gridScale,
    
    // Selection
    selectedProducts,
    bulkSelectedProducts,
    
    // Modal state
    selectedProduct,
    showDetailModal,
    showExportModal,
    
    // Stats
    stats,
    
    // Handlers
    handleSortChange,
    handleCategoryChange,
    handleApplyFilters,
    handleClearFilters,
    handlePageChange,
    handleRefresh,
    handleFavorite,
    handleExport,
    handleSelectProduct,
    handleSelectAll,
    handleBulkFavorite,
    handleProductClick,
    handleCloseModal,
    setViewMode,
    setGridScale,
    setShowExportModal,
    loadMoreProducts,
    isFavorite,
  };
}
