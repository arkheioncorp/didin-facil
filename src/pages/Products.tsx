import * as React from "react";
import { Card } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ProductsIcon, ExportIcon } from "@/components/icons";
import { useFavoritesStore } from "@/stores";
import { ProductCard } from "@/components/product";
import { analytics } from "@/lib/analytics";

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

      {/* Products Grid */}
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {products.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              onFavorite={handleFavorite}
              isFavorite={isFavorite(product.id)}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!isLoading && totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(p => Math.max(1, p - 1))}
          >
            Anterior
          </Button>
          <span className="text-sm text-muted-foreground">
            Página {page} de {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
          >
            Próxima
          </Button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && products.length === 0 && (
        <Card className="min-h-[400px] flex items-center justify-center">
          <div className="text-center p-8">
            <ProductsIcon size={48} className="mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-xl font-semibold mb-2">Nenhum produto encontrado</h3>
            <p className="text-muted-foreground">
              Faça uma busca para coletar produtos do TikTok Shop
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};
