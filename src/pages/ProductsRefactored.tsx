/**
 * Products Page - Refactored Version
 * 
 * Versão otimizada que usa componentes modularizados e hook customizado.
 * 
 * @performance
 * - Usa useProductsPage hook para lógica centralizada
 * - Componentes memoizados (ProductFilters, ProductToolbar, ExportModal)
 * - VirtualizedGrid para renderização eficiente
 * - Lazy loading para modais e charts
 */

import * as React from "react";
import { useTranslation } from "react-i18next";
import { Card } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ProductsIcon, ExportIcon, StarIcon, TrendingIcon } from "@/components/icons";
import { 
  VirtualizedGrid, 
  ProductFilters,
  ProductToolbar,
  ExportModal,
  ProductActionsPanel,
} from "@/components/product";
import { ProductHistoryChart } from "@/components/product/ProductHistoryChart";
import { BulkSelectionBar } from "@/components/product/bulk";
import { useProductsPage, SORT_OPTIONS } from "@/hooks/useProductsPage";
import { analytics } from "@/lib/analytics";
import { cn, formatCurrency, formatNumber } from "@/lib/utils";
import { X, Heart, RefreshCw, Info, ExternalLink, BarChart3 } from "lucide-react";
import { getProductHistory } from "@/services/products";
import type { Product, ProductHistory } from "@/types";

// ============================================
// PRODUCT DETAIL MODAL (Lazy Loaded)
// ============================================

interface ProductDetailModalProps {
  product: Product;
  isOpen: boolean;
  onClose: () => void;
  isFavorite?: boolean;
  onFavorite?: (product: Product) => void;
}

const ProductDetailModal: React.FC<ProductDetailModalProps> = React.memo(({
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
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
        onClick={onClose}
        data-testid="modal-backdrop"
      />
      
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
                    <div data-testid="product-description">
                      <h3 className="font-semibold mb-2 flex items-center gap-2">
                        <Info size={16} />
                        Descrição
                      </h3>
                      <p className="text-muted-foreground leading-relaxed">
                        {product.description || "Sem descrição disponível para este produto."}
                      </p>
                    </div>

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
});

ProductDetailModal.displayName = "ProductDetailModal";

// ============================================
// PRODUCTS PAGE COMPONENT
// ============================================

export const ProductsRefactored: React.FC = () => {
  const { t } = useTranslation();
  
  // Use the centralized hook for all page logic
  const {
    // Data
    products,
    categories,
    total,
    totalPages,
    
    // Loading states
    isLoading,
    isRefreshing,
    isExporting,
    error,
    
    // Filter/Sort values
    page,
    sortFromUrl,
    category,
    minPrice,
    maxPrice,
    minSales,
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
  } = useProductsPage();

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

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">{t("common.total")}</div>
          <div className="text-2xl font-bold">{stats.total}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">{t("products.trending")}</div>
          <div className="text-2xl font-bold text-tiktrend-primary">{stats.trending}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">{t("products.on_sale")}</div>
          <div className="text-2xl font-bold text-green-500">{stats.onSale}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">{t("products.free_shipping")}</div>
          <div className="text-2xl font-bold">{stats.freeShipping}</div>
        </Card>
      </div>

      {/* Bulk Selection Bar */}
      <BulkSelectionBar 
        totalProducts={products.length}
        onBulkAction={(actionId) => {
          analytics.track('export_performed', { 
            format: actionId, 
            count: bulkSelectedProducts.length 
          });
        }} 
      />

      {/* Results Count & Bulk Actions */}
      <div className="flex items-center justify-between">
        <div data-testid="results-count" className="text-sm text-muted-foreground">
          {hasActiveFilters ? (
            <span>{t("products.showing_filtered", { count: products.length, total })}</span>
          ) : (
            <span>{t("products.showing", { count: products.length, total })}</span>
          )}
        </div>

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
          </div>
        )}
      </div>

      {/* Filters and Content */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Filter Sidebar */}
        <ProductFilters
          category={category}
          minPrice={minPrice}
          maxPrice={maxPrice}
          minSales={minSales}
          showTrending={showTrending}
          showOnSale={showOnSale}
          showFreeShipping={showFreeShipping}
          categories={categories}
          onCategoryChange={handleCategoryChange}
          onApplyFilters={handleApplyFilters}
          onClearFilters={handleClearFilters}
          hasActiveFilters={hasActiveFilters}
        />

        {/* Main Content */}
        <div className="flex-1 space-y-4">
          {/* Toolbar */}
          <ProductToolbar
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            gridScale={gridScale}
            onGridScaleChange={setGridScale}
            sortValue={sortFromUrl}
            sortOptions={SORT_OPTIONS}
            onSortChange={handleSortChange}
            isAllSelected={selectedProducts.size === products.length && products.length > 0}
            hasProducts={products.length > 0}
            onSelectAll={handleSelectAll}
          />

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
                gridScale={gridScale}
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
        <div className="fixed bottom-6 right-6 flex flex-col gap-3 z-40">
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
        <ProductDetailModal
          product={selectedProduct}
          isOpen={showDetailModal}
          onClose={handleCloseModal}
          isFavorite={isFavorite(selectedProduct.id)}
          onFavorite={handleFavorite}
        />
      )}

      {/* Export Modal */}
      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        onExport={handleExport}
        selectedCount={selectedProducts.size}
        totalCount={products.length}
        isExporting={isExporting}
      />
    </div>
  );
};

export default ProductsRefactored;
