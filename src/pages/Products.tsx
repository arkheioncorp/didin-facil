import * as React from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Card } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { ProductsIcon, ExportIcon, StarIcon, TrendingIcon } from "@/components/icons";
import { useFavoritesStore } from "@/stores";
import { VirtualizedGrid } from "@/components/product/VirtualizedGrid";
import { ProductActionsPanel } from "@/components/product/ProductActionsPanel";
import { ProductHistoryChart } from "@/components/product/ProductHistoryChart";
import { analytics } from "@/lib/analytics";
import { cn, formatCurrency, formatNumber } from "@/lib/utils";
import { Grid3X3, List, X, Heart, Download, RefreshCw, Info, ExternalLink, BarChart3 } from "lucide-react";
import { getProductHistory } from "@/services/products";

import { getProducts } from "@/services/products";
import { 
  addProductToFavorites, 
  removeProductFromFavorites,
  exportProductsToFile,
  fetchCategories,
  type CategoryInfo 
} from "@/services/api/products";
import type { Product, ProductHistory } from "@/types";

// Sort options
const SORT_OPTIONS = [
  { value: "sales_30d", label: "Mais Vendidos" },
  { value: "newest", label: "Mais Recentes" },
  { value: "price_asc", label: "Menor Preço" },
  { value: "price_desc", label: "Maior Preço" },
  { value: "rating", label: "Melhor Avaliação" },
];

// View modes
type ViewMode = "grid" | "list";

// Default categories (fallback)
const DEFAULT_CATEGORIES: CategoryInfo[] = [
  { name: "Todas", slug: "all", count: 0 },
  { name: "Eletrônicos", slug: "electronics", count: 0 },
  { name: "Moda", slug: "fashion", count: 0 },
  { name: "Casa", slug: "home", count: 0 },
  { name: "Beleza", slug: "beauty", count: 0 },
  { name: "Esportes", slug: "sports", count: 0 },
];

// ============================================
// ENHANCED PRODUCT DETAIL MODAL COMPONENT
// ============================================

interface ProductDetailModalEnhancedProps {
  product: Product;
  isOpen: boolean;
  onClose: () => void;
  isFavorite?: boolean;
  onFavorite?: (product: Product) => void;
}

const ProductDetailModalEnhanced: React.FC<ProductDetailModalEnhancedProps> = ({
  product,
  isOpen,
  onClose,
  isFavorite = false,
  onFavorite,
}) => {
  const [history, setHistory] = React.useState<ProductHistory[]>([]);
  const [activeTab, setActiveTab] = React.useState("info");
  const [selectedImage, setSelectedImage] = React.useState(0);

  React.useEffect(() => {
    if (product?.id) {
      getProductHistory(product.id)
        .then(setHistory)
        .catch((err) => console.error("Failed to load history:", err));
    } else {
      setHistory([]);
    }
  }, [product?.id]);

  // Handle escape key
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  if (!isOpen || !product) return null;

  const discount = product.originalPrice
    ? Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)
    : 0;

  const images = product.images?.length ? product.images : [product.imageUrl || ""];

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
        onClick={onClose}
        data-testid="modal-backdrop"
      />
      
      {/* Modal */}
      <div 
        className="fixed inset-2 md:inset-6 lg:inset-10 bg-background rounded-2xl shadow-2xl z-50 flex flex-col overflow-hidden"
        data-testid="product-detail-modal"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 md:p-6 border-b shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <Badge variant="secondary" className="shrink-0">
              {product.category || "Sem categoria"}
            </Badge>
            {product.isTrending && (
              <Badge variant="tiktrend" className="gap-1 shrink-0">
                <TrendingIcon size={12} />
                Em Alta
              </Badge>
            )}
            {discount > 0 && (
              <Badge variant="destructive" className="shrink-0">
                -{discount}%
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* Quick Actions Bar */}
            <ProductActionsPanel 
              product={product} 
              isFavorite={isFavorite}
              onFavorite={onFavorite}
              onClose={onClose}
              variant="compact" 
            />
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X size={20} />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full grid lg:grid-cols-[1fr,400px]">
            {/* Left: Product Info */}
            <ScrollArea className="h-full">
              <div className="p-4 md:p-6 space-y-6">
                {/* Image Gallery */}
                <div className="space-y-4">
                  <div className="relative aspect-video md:aspect-[4/3] bg-muted rounded-xl overflow-hidden">
                    <img
                      src={images[selectedImage] || "https://placehold.co/600x400/1a1a2e/ffffff?text=Produto"}
                      alt={product.title}
                      className="w-full h-full object-contain"
                    />
                    {/* Badges on image */}
                    {product.hasFreeShipping && (
                      <Badge variant="success" className="absolute top-4 left-4 shadow-lg">
                        Frete Grátis
                      </Badge>
                    )}
                  </div>
                  {images.length > 1 && (
                    <div className="flex gap-2 overflow-x-auto pb-2">
                      {images.map((img, i) => (
                        <button
                          key={i}
                          onClick={() => setSelectedImage(i)}
                          className={cn(
                            "w-16 h-16 md:w-20 md:h-20 rounded-lg overflow-hidden border-2 transition-all shrink-0",
                            selectedImage === i 
                              ? "border-tiktrend-primary ring-2 ring-tiktrend-primary/20" 
                              : "border-transparent hover:border-muted-foreground/30"
                          )}
                        >
                          <img src={img} alt="" className="w-full h-full object-cover" />
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Title & Price */}
                <div className="space-y-3">
                  <h1 className="text-xl md:text-2xl font-bold leading-tight">{product.title}</h1>
                  <div className="flex items-baseline gap-3 flex-wrap">
                    <span className="text-3xl md:text-4xl font-bold text-tiktrend-primary">
                      {formatCurrency(product.price)}
                    </span>
                    {product.originalPrice && (
                      <span className="text-lg text-muted-foreground line-through">
                        {formatCurrency(product.originalPrice)}
                      </span>
                    )}
                    {discount > 0 && (
                      <span className="text-sm font-medium text-green-500">
                        Economia de {formatCurrency(product.originalPrice! - product.price)}
                      </span>
                    )}
                  </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-4 rounded-xl bg-muted/50 text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <StarIcon size={16} filled className="text-yellow-500" />
                      <span className="text-lg font-bold">{product.productRating?.toFixed(1) || "N/A"}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Avaliação</p>
                  </div>
                  <div className="p-4 rounded-xl bg-muted/50 text-center">
                    <p className="text-lg font-bold text-green-500">{formatNumber(product.salesCount)}</p>
                    <p className="text-xs text-muted-foreground">Vendas Totais</p>
                  </div>
                  <div className="p-4 rounded-xl bg-muted/50 text-center">
                    <p className="text-lg font-bold">{formatNumber(product.reviewsCount)}</p>
                    <p className="text-xs text-muted-foreground">Reviews</p>
                  </div>
                  <div className="p-4 rounded-xl bg-muted/50 text-center">
                    <p className="text-lg font-bold text-tiktrend-primary">
                      +{formatNumber(product.sales7d || 0)}
                    </p>
                    <p className="text-xs text-muted-foreground">Vendas 7 dias</p>
                  </div>
                </div>

                {/* Tabs */}
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="w-full grid grid-cols-3">
                    <TabsTrigger value="info" className="gap-2">
                      <Info size={14} />
                      Detalhes
                    </TabsTrigger>
                    <TabsTrigger value="stats" className="gap-2">
                      <BarChart3 size={14} />
                      Estatísticas
                    </TabsTrigger>
                    <TabsTrigger value="supplier" className="gap-2">
                      <ExternalLink size={14} />
                      Fornecedor
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="info" className="space-y-4 mt-4">
                    {/* Description */}
                    <div data-testid="product-description">
                      <h3 className="font-semibold mb-2 flex items-center gap-2">
                        <Info size={16} />
                        Descrição
                      </h3>
                      <p className="text-muted-foreground leading-relaxed">
                        {product.description || "Sem descrição disponível para este produto."}
                      </p>
                    </div>

                    {/* Sales Trend */}
                    {product.sales7d > 0 && (
                      <div className="p-4 rounded-xl bg-gradient-to-r from-tiktrend-primary/10 to-tiktrend-secondary/10 border border-tiktrend-primary/20">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Tendência de Vendas</span>
                          <span className="text-sm font-bold text-green-500">
                            +{formatNumber(product.sales7d)} nos últimos 7 dias
                          </span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary rounded-full transition-all duration-500"
                            style={{ width: `${Math.min((product.sales7d / 1000) * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="stats" className="space-y-4 mt-4">
                    {/* History Chart */}
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <BarChart3 size={16} />
                        Histórico de Vendas
                      </h3>
                      <ProductHistoryChart history={history} />
                    </div>
                  </TabsContent>

                  <TabsContent value="supplier" className="space-y-4 mt-4">
                    <div data-testid="supplier-info">
                      <h3 className="font-semibold mb-3">Informações do Fornecedor</h3>
                      <Card className="p-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium text-lg">{product.sellerName || "TikTok Shop"}</p>
                            <p className="text-sm text-muted-foreground">
                              {product.productUrl ? "✓ Loja verificada no TikTok Shop" : "Loja TikTok Shop"}
                            </p>
                          </div>
                          {product.productUrl && (
                            <Button variant="outline" size="sm" asChild>
                              <a href={product.productUrl} target="_blank" rel="noopener noreferrer">
                                <ExternalLink size={14} className="mr-1" />
                                Visitar
                              </a>
                            </Button>
                          )}
                        </div>
                      </Card>
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            </ScrollArea>

            {/* Right: Actions Panel (Desktop) */}
            <div className="hidden lg:block border-l">
              <ScrollArea className="h-full">
                <div className="p-6">
                  <ProductActionsPanel 
                    product={product}
                    isFavorite={isFavorite}
                    onFavorite={onFavorite}
                    onClose={onClose}
                    variant="full"
                  />
                </div>
              </ScrollArea>
            </div>
          </div>
        </div>

        {/* Mobile: Actions Panel Bottom Sheet */}
        <div className="lg:hidden border-t p-4 bg-background shrink-0">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-2xl font-bold text-tiktrend-primary">{formatCurrency(product.price)}</p>
              <p className="text-xs text-muted-foreground">{formatNumber(product.salesCount)} vendas</p>
            </div>
            <ProductActionsPanel 
              product={product}
              isFavorite={isFavorite}
              onFavorite={onFavorite}
              onClose={onClose}
              variant="compact"
            />
          </div>
        </div>
      </div>
    </>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================

export const Products: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { isFavorite, addFavorite: addToFavorites, removeFavorite: removeFromFavorites } = useFavoritesStore();
  const { toast } = useToast();
  
  // State
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
  const pageSize = 24; // Better for 3-column grid

  // URL-synced state
  const page = parseInt(searchParams.get("page") || "1", 10);
  const sortFromUrl = searchParams.get("sort");
  const sort = sortFromUrl || "sales_30d"; // Default to best sellers
  const category = searchParams.get("category") || "all";
  const minPrice = searchParams.get("min_price") || "";
  const maxPrice = searchParams.get("max_price") || "";
  const minSales = searchParams.get("min_sales") || "";
  const searchQuery = searchParams.get("q") || "";
  
  // Quick filter toggles from URL
  const showTrending = searchParams.get("trending") === "true";
  const showOnSale = searchParams.get("on_sale") === "true";
  const showFreeShipping = searchParams.get("free_shipping") === "true";

  // Local filter state (for form before apply)
  const [filterMinPrice, setFilterMinPrice] = React.useState(minPrice);
  const [filterMaxPrice, setFilterMaxPrice] = React.useState(maxPrice);
  const [filterMinSales, setFilterMinSales] = React.useState(minSales);
  // Future use: advanced filter states
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_filterSearch, _setFilterSearch] = React.useState(searchQuery);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_filterTrending, _setFilterTrending] = React.useState(showTrending);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_filterOnSale, _setFilterOnSale] = React.useState(showOnSale);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_filterFreeShipping, _setFilterFreeShipping] = React.useState(showFreeShipping);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_priceRange, _setPriceRange] = React.useState<[number, number]>([0, 1000]);

  // Mobile filter sheet state (future use)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_showMobileFilters, _setShowMobileFilters] = React.useState(false);

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
    // Advanced filter sync (future use)
    // _setFilterSearch(searchQuery);
    // _setFilterTrending(showTrending);
    // _setFilterOnSale(showOnSale);
    // _setFilterFreeShipping(showFreeShipping);
  }, [minPrice, maxPrice, minSales, searchQuery, showTrending, showOnSale, showFreeShipping]);

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

  // Persist view mode
  React.useEffect(() => {
    localStorage.setItem("products-view-mode", viewMode);
  }, [viewMode]);

  // Build API sort params
  const getSortParams = () => {
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
  };

  // Apply client-side filters for additional filtering
  const applyClientFilters = (data: Product[]): Product[] => {
    let filtered = [...data];
    
    // Quick filters (client-side since API may not support)
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
  };

  // Load products on mount and when params change
  React.useEffect(() => {
    const loadProducts = async () => {
      setIsLoading(true);
      setError(null);
      setCurrentPage(1);
      
      try {
        const { sortBy, sortOrder } = getSortParams();
        
        const response = await getProducts(1, pageSize, {
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sort, category, minPrice, maxPrice, minSales, showTrending, showOnSale, showFreeShipping]);

  // Load more products (infinite scroll)
  const loadMoreProducts = React.useCallback(async () => {
    if (isLoadingMore || !hasMore) return;

    setIsLoadingMore(true);
    try {
      const nextPage = currentPage + 1;
      const { sortBy, sortOrder } = getSortParams();
      
      const response = await getProducts(nextPage, pageSize, {
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, hasMore, isLoadingMore, category, minPrice, maxPrice, minSales, sort, showTrending, showOnSale, showFreeShipping]);

  // Refresh products
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const { sortBy, sortOrder } = getSortParams();
      
      const response = await getProducts(1, pageSize, {
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
  };

  // Handle favorite toggle
  const handleFavorite = async (product: Product) => {
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
  };

  // Handle export
  const handleExport = async (format: "csv" | "xlsx") => {
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
            onClick={handleRefresh}
            disabled={isRefreshing || isLoading}
          >
            <RefreshCw size={16} className={isRefreshing ? "animate-spin" : ""} />
            {isRefreshing ? t("common.refreshing") : t("common.refresh")}
          </Button>
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
                  {categories.map((cat) => (
                    <SelectItem key={cat.slug} value={cat.slug}>
                      {cat.name}
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

      {/* Enhanced Product Detail Modal */}
      {showDetailModal && selectedProduct && (
        <ProductDetailModalEnhanced
          product={selectedProduct}
          isOpen={showDetailModal}
          onClose={handleCloseModal}
          isFavorite={isFavorite(selectedProduct.id)}
          onFavorite={handleFavorite}
        />
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
