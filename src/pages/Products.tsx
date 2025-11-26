import * as React from "react";
import { Card } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ProductsIcon, ExportIcon } from "@/components/icons";
import { useFavoritesStore } from "@/stores";
import { VirtualizedGrid } from "@/components/product/VirtualizedGrid";
import { analytics } from "@/lib/analytics";
import { cn } from "@/lib/utils";

import { exportProducts, getProducts, addFavorite, removeFavorite } from "@/lib/tauri";
import type { Product } from "@/types";

export const Products: React.FC = () => {
  const { isFavorite } = useFavoritesStore();
  const [products, setProducts] = React.useState<Product[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [page, setPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const [total, setTotal] = React.useState(0);
  const [isExporting, setIsExporting] = React.useState(false);
  const pageSize = 20;

  // Load products on mount and when page changes
  React.useEffect(() => {
    const loadProducts = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await getProducts(page, pageSize);
        setProducts(response.data);
        setTotal(response.total);
        setTotalPages(Math.ceil(response.total / response.pageSize));
      } catch (err) {
        console.error("Error loading products:", err);
        setError("Erro ao carregar produtos. Tente novamente.");
      } finally {
        setIsLoading(false);
      }
    };

    loadProducts();
  }, [page]);

  // Handle favorite toggle
  const handleFavorite = async (product: Product) => {
    try {
      if (isFavorite(product.id)) {
        await removeFavorite(product.id);
      } else {
        await addFavorite(product.id);
      }
    } catch (err) {
      console.error("Error toggling favorite:", err);
    }
  };

  // Handle export
  const handleExport = async (format: "csv" | "json" | "xlsx") => {
    if (products.length === 0) return;

    setIsExporting(true);
    try {
      analytics.track('export_performed', {
        format,
        count: products.length
      });

      const productIds = products.map(p => p.id);
      const filePath = await exportProducts(productIds, format);
      console.log("Exported to:", filePath);
    } catch (err) {
      console.error("Error exporting:", err);
    } finally {
      setIsExporting(false);
    }
  };

  // Stats calculations
  const stats = React.useMemo(() => ({
    total: total,
    trending: products.filter(p => p.isTrending).length,
    onSale: products.filter(p => p.isOnSale).length,
    freeShipping: products.filter(p => p.hasFreeShipping).length,
  }), [products, total]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Produtos</h1>
          <p className="text-muted-foreground">
            Explore os produtos coletados do TikTok Shop
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            className="gap-2"
            onClick={() => handleExport("csv")}
            disabled={isExporting || products.length === 0}
          >
            <ExportIcon size={16} />
            {isExporting ? "Exportando..." : "Exportar CSV"}
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Total</div>
          <div className="text-2xl font-bold">{stats.total}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Em Alta</div>
          <div className="text-2xl font-bold text-tiktrend-primary">
            {stats.trending}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Em Promoção</div>
          <div className="text-2xl font-bold text-green-500">
            {stats.onSale}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Frete Grátis</div>
          <div className="text-2xl font-bold">
            {stats.freeShipping}
          </div>
        </Card>
      </div>

      {/* Error State */}
      {error && (
        <Card className="p-4 border-destructive bg-destructive/10">
          <p className="text-destructive">{error}</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={() => setPage(1)}
          >
            Tentar Novamente
          </Button>
        </Card>
      )}

      {/* Products Grid - Virtualized */}
      {/* Products Grid - Virtualized */}
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
      ) : (
        <VirtualizedGrid products={products} onFavorite={handleFavorite} isFavorite={isFavorite} />
      )}

      {/* Pagination - Melhoria #20: Design moderno */}
      {!isLoading && totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 py-6" data-testid="pagination">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(p => Math.max(1, p - 1))}
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
              if (pageNum > totalPages) return null;
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  data-page={pageNum}
                  data-testid={page === pageNum ? "current-page" : undefined}
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
                  onClick={() => setPage(totalPages)}
                  data-page={totalPages}
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
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            className="gap-2"
            data-testid="next-page"
          >
            Próxima
            <span>→</span>
          </Button>
        </div>
      )}

      {/* Floating Action Button - Melhoria #27 */}
      {products.length > 0 && (
        <div className="fixed bottom-6 right-6 flex flex-col gap-3 z-50">
          <Button
            variant="tiktrend"
            size="lg"
            className="rounded-full w-14 h-14 shadow-xl shadow-tiktrend-primary/30 hover:scale-110 transition-transform"
            onClick={() => handleExport("csv")}
            disabled={isExporting}
          >
            <ExportIcon size={20} />
          </Button>
        </div>
      )}

      {/* Empty State - Melhoria #15 */}
      {!isLoading && !error && products.length === 0 && (
        <Card className="min-h-[400px] flex items-center justify-center">
          <div className="empty-state">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-tiktrend-primary/10 to-tiktrend-secondary/10 flex items-center justify-center mb-6">
              <ProductsIcon size={40} className="text-tiktrend-primary/50" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Nenhum produto encontrado</h3>
            <p className="text-muted-foreground max-w-sm">
              Faça uma busca para coletar produtos do TikTok Shop
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};
