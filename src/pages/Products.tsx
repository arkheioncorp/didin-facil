import * as React from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Card } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { ProductsIcon, ExportIcon } from "@/components/icons";
import { useFavoritesStore } from "@/stores";
import { VirtualizedGrid } from "@/components/product/VirtualizedGrid";
import { analytics } from "@/lib/analytics";
import { cn } from "@/lib/utils";
import { Grid3X3, List, X, Heart, Download, Check } from "lucide-react";

import { exportProducts, getProducts, addFavorite, removeFavorite } from "@/lib/tauri";
import type { Product } from "@/types";

// Categories for filtering
const CATEGORIES = [
  { value: "all", label: "Todas" },
  { value: "electronics", label: "Eletrônicos" },
  { value: "fashion", label: "Moda" },
  { value: "home", label: "Casa" },
  { value: "beauty", label: "Beleza" },
  { value: "sports", label: "Esportes" },
];

// Sort options
const SORT_OPTIONS = [
  { value: "newest", label: "Mais Recentes" },
  { value: "price_asc", label: "Menor Preço" },
  { value: "price_desc", label: "Maior Preço" },
  { value: "sales", label: "Mais Vendidos" },
];

// View modes
type ViewMode = "grid" | "list";

export const Products: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { isFavorite, addFavorite: addToFavorites, removeFavorite: removeFromFavorites } = useFavoritesStore();
  const { toast } = useToast();
  
  // State
  const [products, setProducts] = React.useState<Product[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isLoadingMore, setIsLoadingMore] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [isExporting, setIsExporting] = React.useState(false);
  const [total, setTotal] = React.useState(0);
  const [totalPages, setTotalPages] = React.useState(1);
  const [hasMore, setHasMore] = React.useState(true);
  const [currentPage, setCurrentPage] = React.useState(1);
  const pageSize = 20;

  // URL-synced state
  const page = parseInt(searchParams.get("page") || "1", 10);
  const sortFromUrl = searchParams.get("sort");
  const sort = sortFromUrl || "newest"; // Default to newest but keep URL clean
  const category = searchParams.get("category") || "all";
  const minPrice = searchParams.get("min_price") || "";
  const maxPrice = searchParams.get("max_price") || "";
  const minSales = searchParams.get("min_sales") || "";

  // Local filter state (for form before apply)
  const [filterMinPrice, setFilterMinPrice] = React.useState(minPrice);
  const [filterMaxPrice, setFilterMaxPrice] = React.useState(maxPrice);
  const [filterMinSales, setFilterMinSales] = React.useState(minSales);

  // View mode with localStorage persistence
  const [viewMode, setViewMode] = React.useState<ViewMode>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("products-view-mode") as ViewMode) || "grid";
    }
    return "grid";
  });

  // Bulk selection state
  const [selectedProducts, setSelectedProducts] = React.useState<Set<string>>(new Set());
  const [showExportModal, setShowExportModal] = React.useState(false);

  // Product detail modal state
  const [selectedProduct, setSelectedProduct] = React.useState<Product | null>(null);
  const [showDetailModal, setShowDetailModal] = React.useState(false);

  // Sync filter state when URL changes
  React.useEffect(() => {
    setFilterMinPrice(minPrice);
    setFilterMaxPrice(maxPrice);
    setFilterMinSales(minSales);
  }, [minPrice, maxPrice, minSales]);

  // Persist view mode
  React.useEffect(() => {
    localStorage.setItem("products-view-mode", viewMode);
  }, [viewMode]);

  // Apply client-side filters and sorting
  const applyFiltersAndSort = (data: Product[]): Product[] => {
    let filtered = [...data];
    
    // Category filter
    if (category && category !== "all") {
      filtered = filtered.filter(p => p.category === category);
    }
    
    // Price filters
    const minPriceValue = minPrice ? parseFloat(minPrice) : undefined;
    const maxPriceValue = maxPrice ? parseFloat(maxPrice) : undefined;
    if (minPriceValue !== undefined) {
      filtered = filtered.filter(p => p.price >= minPriceValue);
    }
    if (maxPriceValue !== undefined) {
      filtered = filtered.filter(p => p.price <= maxPriceValue);
    }
    
    // Min sales filter
    const minSalesValue = minSales ? parseInt(minSales, 10) : undefined;
    if (minSalesValue !== undefined) {
      filtered = filtered.filter(p => (p.salesCount || 0) >= minSalesValue);
    }
    
    // Apply sorting
    if (sort === "price_asc") {
      filtered.sort((a, b) => a.price - b.price);
    } else if (sort === "price_desc") {
      filtered.sort((a, b) => b.price - a.price);
    } else if (sort === "sales") {
      filtered.sort((a, b) => (b.salesCount || 0) - (a.salesCount || 0));
    } else if (sort === "newest") {
      filtered.sort((a, b) => new Date(b.collectedAt || 0).getTime() - new Date(a.collectedAt || 0).getTime());
    }
    
    return filtered;
  };

  // Load products on mount and when params change
  React.useEffect(() => {
    const loadProducts = async () => {
      setIsLoading(true);
      setError(null);
      setCurrentPage(1);
      try {
        const response = await getProducts(1, pageSize);
        const filteredProducts = applyFiltersAndSort(response.data);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sort, category, minPrice, maxPrice, minSales]);

  // Load more products (infinite scroll)
  const loadMoreProducts = React.useCallback(async () => {
    if (isLoadingMore || !hasMore) return;

    setIsLoadingMore(true);
    try {
      const nextPage = currentPage + 1;
      const response = await getProducts(nextPage, pageSize);
      const filteredNewProducts = applyFiltersAndSort(response.data);
      
      setProducts(prev => [...prev, ...filteredNewProducts]);
      setCurrentPage(nextPage);
      setHasMore(response.hasMore);
    } catch (err) {
      console.error("Error loading more products:", err);
    } finally {
      setIsLoadingMore(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, hasMore, isLoadingMore, category, minPrice, maxPrice, minSales, sort]);

  // Handle favorite toggle
  const handleFavorite = async (product: Product) => {
    try {
      if (isFavorite(product.id)) {
        await removeFavorite(product.id);
        removeFromFavorites(product.id);
      } else {
        await addFavorite(product.id);
        addToFavorites(product);
      }
    } catch (err) {
      console.error("Error toggling favorite:", err);
    }
  };

  // Handle export
  const handleExport = async (format: "csv" | "json" | "xlsx") => {
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
      const filePath = await exportProducts(productIds, format);
      console.log("Exported to:", filePath);
      toast({ title: "Exportado!", description: `${productsToExport.length} produtos exportados com sucesso!` });
      setShowExportModal(false);
      setSelectedProducts(new Set());
    } catch (err) {
      console.error("Error exporting:", err);
    } finally {
      setIsExporting(false);
    }
  };

  // URL update helpers
  const updateSearchParams = (updates: Record<string, string | undefined>) => {
    const newParams = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, value]) => {
      if (value) {
        newParams.set(key, value);
      } else {
        newParams.delete(key);
      }
    });
    setSearchParams(newParams);
  };

  const handleSortChange = (value: string) => {
    updateSearchParams({ sort: value, page: "1" });
  };

  const handleCategoryChange = (value: string) => {
    updateSearchParams({ 
      category: value !== "all" ? value : undefined, 
      page: "1" 
    });
  };

  const handleApplyFilters = () => {
    updateSearchParams({
      min_price: filterMinPrice || undefined,
      max_price: filterMaxPrice || undefined,
      min_sales: filterMinSales || undefined,
      page: "1",
    });
  };

  const handleClearFilters = () => {
    setFilterMinPrice("");
    setFilterMaxPrice("");
    setFilterMinSales("");
    setSearchParams(new URLSearchParams());
  };

  const handlePageChange = (newPage: number) => {
    updateSearchParams({ page: String(newPage) });
  };

  // Bulk selection handlers
  const handleSelectProduct = (productId: string, checked: boolean) => {
    setSelectedProducts(prev => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(productId);
      } else {
        newSet.delete(productId);
      }
      return newSet;
    });
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedProducts(new Set(products.map(p => p.id)));
    } else {
      setSelectedProducts(new Set());
    }
  };

  const handleBulkFavorite = async () => {
    try {
      for (const productId of selectedProducts) {
        const product = products.find(p => p.id === productId);
        if (product && !isFavorite(productId)) {
          await addFavorite(productId);
          addToFavorites(product);
        }
      }
      toast({ title: "Adicionado!", description: `${selectedProducts.size} produtos adicionados aos favoritos!` });
      setSelectedProducts(new Set());
    } catch (err) {
      console.error("Error bulk adding favorites:", err);
    }
  };

  // Product detail modal handlers
  const handleProductClick = (product: Product) => {
    setSelectedProduct(product);
    setShowDetailModal(true);
  };

  const handleCloseModal = () => {
    setShowDetailModal(false);
    setSelectedProduct(null);
  };

  const handleCopyProductInfo = async () => {
    if (!selectedProduct) return;
    const info = `${selectedProduct.title}\nPreço: R$ ${selectedProduct.price}\nVendas: ${selectedProduct.salesCount}`;
    try {
      await navigator.clipboard.writeText(info);
    } catch {
      // Fallback for environments without clipboard API
      console.log("Clipboard API not available");
    }
    toast({ title: "Copiado!", description: "Informações copiadas para a área de transferência." });
  };

  const handleGenerateCopy = () => {
    if (!selectedProduct) return;
    navigate(`/copy?product=${selectedProduct.id}`);
  };

  // Handle escape key for modal
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && showDetailModal) {
        handleCloseModal();
      }
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [showDetailModal]);

  // Handle window scroll for infinite scroll (fallback for VirtuosoGrid)
  React.useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;
      const threshold = 200; // pixels from bottom to trigger load

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
  const hasActiveFilters = category !== "all" || minPrice || maxPrice || minSales;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t("products.title")}</h1>
          <p className="text-muted-foreground">
            {t("products.explore_collected")}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            className="gap-2"
            onClick={() => setShowExportModal(true)}
            disabled={isExporting || products.length === 0}
          >
            <ExportIcon size={16} />
            {isExporting ? t("common.exporting") : t("common.export")}
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">{t("common.total")}</div>
          <div className="text-2xl font-bold">{stats.total}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">{t("products.trending")}</div>
          <div className="text-2xl font-bold text-tiktrend-primary">
            {stats.trending}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">{t("products.on_sale")}</div>
          <div className="text-2xl font-bold text-green-500">
            {stats.onSale}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">{t("products.free_shipping")}</div>
          <div className="text-2xl font-bold">
            {stats.freeShipping}
          </div>
        </Card>
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between">
        <div data-testid="results-count" className="text-sm text-muted-foreground">
          {hasActiveFilters ? (
            <span>{t("products.showing_filtered", { count: products.length, total })}</span>
          ) : (
            <span>{t("products.showing", { count: products.length, total })}</span>
          )}
        </div>

        {/* Bulk Selection Info */}
        {selectedProducts.size > 0 && (
          <div className="flex items-center gap-4" data-testid="bulk-actions">
            <span data-testid="selected-count" className="text-sm font-medium">
              {t("products.selected", { count: selectedProducts.size })}
            </span>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={handleBulkFavorite}
              data-testid="bulk-favorite"
            >
              <Heart size={14} />
              {t("products.add_to_favorites")}
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => setShowExportModal(true)}
              data-testid="bulk-export"
            >
              <Download size={14} />
              {t("common.export")}
            </Button>
          </div>
        )}
      </div>

      {/* Filters and Sort */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Filter Sidebar */}
        <aside className="lg:w-64 shrink-0" data-testid="filter-sidebar">
          <Card className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">{t("search.filters.title")}</h3>
              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearFilters}
                  data-testid="clear-filters"
                  className="text-xs"
                >
                  <X size={14} className="mr-1" />
                  {t("common.clear")}
                </Button>
              )}
            </div>

            {/* Category Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium">{t("search.filters.category")}</label>
              <Select value={category} onValueChange={handleCategoryChange}>
                <SelectTrigger className="w-full" data-testid="category-filter">
                  <SelectValue placeholder={t("products.all_categories")} />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Price Range */}
            <div className="space-y-2">
              <label className="text-sm font-medium">{t("search.filters.priceRange")}</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder={t("search.filters.min")}
                  value={filterMinPrice}
                  onChange={(e) => setFilterMinPrice(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border bg-background text-sm"
                  data-testid="min-price"
                />
                <input
                  type="number"
                  placeholder={t("search.filters.max")}
                  value={filterMaxPrice}
                  onChange={(e) => setFilterMaxPrice(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border bg-background text-sm"
                  data-testid="max-price"
                />
              </div>
            </div>

            {/* Min Sales */}
            <div className="space-y-2">
              <label className="text-sm font-medium">{t("search.filters.minSales")}</label>
              <input
                type="number"
                placeholder={t("search.filters.minSalesPlaceholder")}
                value={filterMinSales}
                onChange={(e) => setFilterMinSales(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm"
                data-testid="min-sales"
              />
            </div>

            {/* Quick Filters */}
            <div className="space-y-2">
              <label className="text-sm font-medium">{t("products.quick_filters")}</label>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm">{t("products.trending")}</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm">{t("products.on_sale")}</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm">{t("products.free_shipping")}</span>
                </label>
              </div>
            </div>

            {/* Apply Button */}
            <Button 
              onClick={handleApplyFilters} 
              className="w-full"
              data-testid="apply-filters"
            >
              {t("search.filters.apply")}
            </Button>
          </Card>
        </aside>

        {/* Main Content */}
        <div className="flex-1 space-y-4">
          {/* Toolbar */}
          <div className="flex items-center justify-between">
            {/* Select All */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input 
                type="checkbox" 
                className="rounded"
                checked={selectedProducts.size === products.length && products.length > 0}
                onChange={(e) => handleSelectAll(e.target.checked)}
                data-testid="select-all"
              />
              <span className="text-sm">{t("products.select_all")}</span>
            </label>

            <div className="flex items-center gap-4">
              {/* View Mode Toggle */}
              <div className="flex items-center gap-1 border rounded-lg p-1">
                <button
                  onClick={() => setViewMode("grid")}
                  className={cn(
                    "p-2 rounded transition-colors",
                    viewMode === "grid" ? "bg-accent" : "hover:bg-accent/50"
                  )}
                  data-testid="grid-view"
                >
                  <Grid3X3 size={16} />
                </button>
                <button
                  onClick={() => setViewMode("list")}
                  className={cn(
                    "p-2 rounded transition-colors",
                    viewMode === "list" ? "bg-accent" : "hover:bg-accent/50"
                  )}
                  data-testid="list-view"
                >
                  <List size={16} />
                </button>
              </div>

              {/* Sort Select */}
              <Select value={sortFromUrl || ""} onValueChange={handleSortChange}>
                <SelectTrigger className="w-[180px]" data-testid="sort-select">
                  <SelectValue placeholder="Mais Recentes" />
                </SelectTrigger>
                <SelectContent>
                  {SORT_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Error State */}
          {error && (
            <Card className="p-4 border-destructive bg-destructive/10">
              <p className="text-destructive">{error}</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={() => handlePageChange(1)}
              >
                Tentar Novamente
              </Button>
            </Card>
          )}

          {/* Products Grid/List */}
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {[...Array(8)].map((_, i) => (
                <Card key={i} className="overflow-hidden">
                  <Skeleton className="aspect-square" />
                  <div className="p-4 space-y-3">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-6 w-1/3" />
                  </div>
                </Card>
              ))}
            </div>
          ) : viewMode === "grid" ? (
            <div data-testid="products-grid">
              <VirtualizedGrid
                products={products}
                onFavorite={handleFavorite}
                isFavorite={isFavorite}
                onProductClick={handleProductClick}
                selectedProducts={selectedProducts}
                onSelectProduct={handleSelectProduct}
                onEndReached={loadMoreProducts}
              />
            </div>
          ) : (
            <div data-testid="products-list" className="space-y-3">
              {products.map((product) => (
                <Card 
                  key={product.id} 
                  className="flex items-center gap-4 p-4 hover:bg-accent/50 cursor-pointer transition-colors"
                  onClick={() => handleProductClick(product)}
                  data-testid="product-card"
                >
                  <input
                    type="checkbox"
                    className="rounded"
                    checked={selectedProducts.has(product.id)}
                    onChange={(e) => {
                      e.stopPropagation();
                      handleSelectProduct(product.id, e.target.checked);
                    }}
                    onClick={(e) => e.stopPropagation()}
                    data-testid="product-checkbox"
                  />
                  <img
                    src={product.imageUrl ?? undefined}
                    alt={product.title}
                    className="w-16 h-16 object-cover rounded"
                    data-testid="product-image"
                  />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate" data-testid="product-title">
                      {product.title}
                    </h3>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span data-testid="product-price">R$ {product.price.toFixed(2)}</span>
                      <span data-testid="product-sales">{product.salesCount} vendas</span>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleFavorite(product);
                    }}
                    data-testid="favorite-button"
                  >
                    <Heart 
                      size={18} 
                      className={isFavorite(product.id) ? "fill-red-500 text-red-500" : ""} 
                    />
                  </Button>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Pagination */}
      {!isLoading && totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 py-6" data-testid="pagination">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => handlePageChange(page - 1)}
            className="gap-2"
            data-testid="prev-page"
          >
            <span>←</span>
            Anterior
          </Button>

          {/* Page indicators */}
          <div className="flex items-center gap-2">
            {Array.from({ length: Math.min(totalPages, 5) }).map((_, i) => {
              const pageNum = page <= 3 ? i + 1 : page - 2 + i;
              if (pageNum > totalPages || pageNum < 1) return null;
              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  data-page={pageNum}
                  data-testid={page === pageNum ? "current-page" : `page-${pageNum}`}
                  className={cn(
                    "w-10 h-10 rounded-xl text-sm font-medium transition-all duration-200",
                    page === pageNum
                      ? "bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary text-white shadow-lg shadow-tiktrend-primary/25"
                      : "bg-muted hover:bg-accent text-muted-foreground hover:text-foreground"
                  )}
                >
                  {pageNum}
                </button>
              );
            })}
            {totalPages > 5 && page < totalPages - 2 && (
              <>
                <span className="text-muted-foreground">...</span>
                <button
                  onClick={() => handlePageChange(totalPages)}
                  data-page={totalPages}
                  data-testid={`page-${totalPages}`}
                  className="w-10 h-10 rounded-xl text-sm font-medium bg-muted hover:bg-accent text-muted-foreground hover:text-foreground transition-all"
                >
                  {totalPages}
                </button>
              </>
            )}
          </div>

          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => handlePageChange(page + 1)}
            className="gap-2"
            data-testid="next-page"
          >
            Próxima
            <span>→</span>
          </Button>
        </div>
      )}

      {/* Floating Action Button */}
      {products.length > 0 && (
        <div className="fixed bottom-6 right-6 flex flex-col gap-3 z-50">
          <Button
            variant="tiktrend"
            size="lg"
            className="rounded-full w-14 h-14 shadow-xl shadow-tiktrend-primary/30 hover:scale-110 transition-transform"
            onClick={() => setShowExportModal(true)}
            disabled={isExporting}
          >
            <ExportIcon size={20} />
          </Button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && products.length === 0 && (
        <Card className="min-h-[400px] flex items-center justify-center">
          <div className="empty-state text-center">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-tiktrend-primary/10 to-tiktrend-secondary/10 flex items-center justify-center mb-6 mx-auto">
              <ProductsIcon size={40} className="text-tiktrend-primary/50" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Nenhum produto encontrado</h3>
            <p className="text-muted-foreground max-w-sm">
              {hasActiveFilters 
                ? "Tente ajustar os filtros para ver mais produtos"
                : "Faça uma busca para coletar produtos do TikTok Shop"
              }
            </p>
            {hasActiveFilters && (
              <Button 
                variant="outline" 
                className="mt-4" 
                onClick={handleClearFilters}
              >
                Limpar Filtros
              </Button>
            )}
          </div>
        </Card>
      )}

      {/* Product Detail Modal */}
      {showDetailModal && selectedProduct && (
        <>
          <div 
            className="fixed inset-0 bg-black/50 z-50"
            data-testid="modal-backdrop"
            onClick={handleCloseModal}
          />
          <div 
            className="fixed inset-4 md:inset-10 lg:inset-20 bg-background rounded-2xl shadow-2xl z-50 overflow-auto"
            data-testid="product-detail-modal"
          >
            <div className="p-6">
              {/* Modal Header */}
              <div className="flex items-start justify-between mb-6">
                <h2 className="text-2xl font-bold">{selectedProduct.title}</h2>
                <Button variant="ghost" size="icon" onClick={handleCloseModal}>
                  <X size={20} />
                </Button>
              </div>

              <div className="grid md:grid-cols-2 gap-8">
                {/* Image Gallery */}
                <div data-testid="product-gallery">
                  <img
                    src={selectedProduct.imageUrl ?? undefined}
                    alt={selectedProduct.title}
                    className="w-full rounded-xl"
                  />
                  {selectedProduct.images && selectedProduct.images.length > 1 && (
                    <div className="flex gap-2 mt-4 overflow-x-auto">
                      {selectedProduct.images.map((img, i) => (
                        <img 
                          key={i}
                          src={img}
                          alt={`${selectedProduct.title} ${i + 1}`}
                          className="w-20 h-20 object-cover rounded-lg border-2 border-transparent hover:border-tiktrend-primary cursor-pointer"
                        />
                      ))}
                    </div>
                  )}
                </div>

                {/* Product Info */}
                <div className="space-y-6">
                  {/* Price & Sales */}
                  <div className="flex items-center gap-4">
                    <span className="text-3xl font-bold text-tiktrend-primary">
                      R$ {selectedProduct.price.toFixed(2)}
                    </span>
                    <span className="text-muted-foreground">
                      {selectedProduct.salesCount} vendas
                    </span>
                  </div>

                  {/* Description */}
                  <div data-testid="product-description">
                    <h3 className="font-semibold mb-2">Descrição</h3>
                    <p className="text-muted-foreground">
                      {selectedProduct.description || "Sem descrição disponível."}
                    </p>
                  </div>

                  {/* Supplier Info */}
                  <div data-testid="supplier-info">
                    <h3 className="font-semibold mb-2">Fornecedor</h3>
                    <div className="bg-accent/50 rounded-lg p-4">
                      <p className="font-medium">{selectedProduct.sellerName || "TikTok Shop"}</p>
                      <p className="text-sm text-muted-foreground">
                        {selectedProduct.productUrl ? "Loja verificada no TikTok Shop" : "Loja TikTok Shop"}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-3">
                    <Button 
                      variant="outline" 
                      className="flex-1 gap-2"
                      onClick={handleCopyProductInfo}
                      data-testid="copy-info"
                    >
                      <Check size={16} />
                      Copiar Info
                    </Button>
                    <Button 
                      variant="tiktrend" 
                      className="flex-1 gap-2"
                      onClick={handleGenerateCopy}
                      data-testid="generate-copy"
                    >
                      Gerar Copy
                    </Button>
                  </div>

                  <Button 
                    variant={isFavorite(selectedProduct.id) ? "secondary" : "outline"}
                    className="w-full gap-2"
                    onClick={() => handleFavorite(selectedProduct)}
                  >
                    <Heart 
                      size={16} 
                      className={isFavorite(selectedProduct.id) ? "fill-red-500 text-red-500" : ""} 
                    />
                    {isFavorite(selectedProduct.id) ? "Remover dos Favoritos" : "Adicionar aos Favoritos"}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Export Modal */}
      {showExportModal && (
        <>
          <div 
            className="fixed inset-0 bg-black/50 z-50"
            onClick={() => setShowExportModal(false)}
          />
          <div 
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-2xl shadow-2xl z-50 p-6 w-full max-w-md"
            data-testid="export-modal"
          >
            <h2 className="text-xl font-bold mb-4">Exportar Produtos</h2>
            <p className="text-muted-foreground mb-6">
              {selectedProducts.size > 0 
                ? `Exportar ${selectedProducts.size} produto(s) selecionado(s)`
                : `Exportar todos os ${products.length} produtos`
              }
            </p>
            <div className="space-y-3">
              <Button 
                variant="outline" 
                className="w-full justify-start gap-3"
                onClick={() => handleExport("csv")}
                disabled={isExporting}
              >
                <Download size={18} />
                Exportar como CSV
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-start gap-3"
                onClick={() => handleExport("xlsx")}
                disabled={isExporting}
              >
                <Download size={18} />
                Exportar como Excel
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-start gap-3"
                onClick={() => handleExport("json")}
                disabled={isExporting}
              >
                <Download size={18} />
                Exportar como JSON
              </Button>
            </div>
            <Button 
              variant="ghost" 
              className="w-full mt-4"
              onClick={() => setShowExportModal(false)}
            >
              Cancelar
            </Button>
          </div>
        </>
      )}
    </div>
  );
};

export default Products;
