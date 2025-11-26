import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  FavoritesIcon,
  TrendingIcon,
  StarIcon,
  ExportIcon,
  CopyIcon,
} from "@/components/icons";
import { formatCurrency, formatNumber } from "@/lib/utils";
import type { Product, ProductHistory } from "@/types";
import { ProductHistoryChart } from "./ProductHistoryChart";
import { getProductHistory } from "@/services/products";

interface ProductDetailModalProps {
  product: Product | null;
  isOpen: boolean;
  onClose: () => void;
  onFavorite?: (product: Product) => void;
  isFavorite?: boolean;
  onGenerateCopy?: (product: Product) => void;
}

export const ProductDetailModal: React.FC<ProductDetailModalProps> = ({
  product,
  isOpen,
  onClose,
  onFavorite,
  isFavorite = false,
  onGenerateCopy,
}) => {
  const [history, setHistory] = React.useState<ProductHistory[]>([]);

  React.useEffect(() => {
    if (product?.id) {
      getProductHistory(product.id)
        .then(setHistory)
        .catch((err) => console.error("Failed to load history:", err));
    } else {
      setHistory([]);
    }
  }, [product?.id]);

  if (!product) return null;

  const discount = product.originalPrice
    ? Math.round(
        ((product.originalPrice - product.price) / product.originalPrice) * 100
      )
    : 0;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className="max-w-2xl p-0 overflow-hidden"
        data-testid="product-detail-modal"
      >
        {/* Image Section */}
        <div className="relative aspect-video bg-muted overflow-hidden">
          <img
            src={
              product.imageUrl ||
              "https://placehold.co/600x400/1a1a2e/ffffff?text=Produto"
            }
            alt={product.title}
            className="w-full h-full object-cover"
          />

          {/* Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

          {/* Badges */}
          <div className="absolute top-4 left-4 flex flex-wrap gap-2">
            {product.isTrending && (
              <Badge variant="tiktrend" className="gap-1 shadow-lg">
                <TrendingIcon size={12} />
                Em Alta
              </Badge>
            )}
            {discount > 0 && (
              <Badge variant="destructive" className="font-bold shadow-lg">
                -{discount}%
              </Badge>
            )}
            {product.hasFreeShipping && (
              <Badge variant="success" className="shadow-lg">
                Frete Grátis
              </Badge>
            )}
          </div>

          {/* Price Overlay */}
          <div className="absolute bottom-4 left-4 right-4">
            <div className="flex items-end justify-between">
              <div>
                <p className="text-3xl font-bold text-white drop-shadow-lg">
                  {formatCurrency(product.price)}
                </p>
                {product.originalPrice && (
                  <p className="text-lg text-white/70 line-through">
                    {formatCurrency(product.originalPrice)}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                {onFavorite && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="bg-white/20 backdrop-blur-sm hover:bg-white/30 h-10 w-10 rounded-full"
                    onClick={() => onFavorite(product)}
                  >
                    <FavoritesIcon
                      size={20}
                      className={
                        isFavorite
                          ? "fill-tiktrend-primary text-tiktrend-primary"
                          : "text-white"
                      }
                    />
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Content Section */}
        <div className="p-6 space-y-6">
          <DialogHeader className="space-y-3">
            <div className="flex items-center gap-2">
              <Badge variant="secondary" size="sm">
                {product.category || "Sem categoria"}
              </Badge>
              {product.sellerName && (
                <span className="text-sm text-muted-foreground">
                  por {product.sellerName}
                </span>
              )}
            </div>
            <DialogTitle className="text-xl leading-tight">
              {product.title}
            </DialogTitle>
          </DialogHeader>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 rounded-xl bg-muted/50">
              <div className="flex items-center justify-center gap-1 mb-1">
                <StarIcon size={16} filled className="text-yellow-500" />
                <span className="text-lg font-bold">
                  {product.productRating?.toFixed(1) || "N/A"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">Avaliação</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-muted/50">
              <p className="text-lg font-bold">
                {formatNumber(product.salesCount)}
              </p>
              <p className="text-xs text-muted-foreground">Vendas</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-muted/50">
              <p className="text-lg font-bold">
                {formatNumber(product.reviewsCount)}
              </p>
              <p className="text-xs text-muted-foreground">Reviews</p>
            </div>
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
                  style={{
                    width: `${Math.min((product.sales7d / 1000) * 100, 100)}%`,
                  }}
                />
              </div>
            </div>
          )}

          {/* History Chart */}
          <ProductHistoryChart history={history} />

          {/* Description */}
          {product.description && (
            <div>
              <h4 className="text-sm font-medium mb-2">Descrição</h4>
              <p className="text-sm text-muted-foreground leading-relaxed line-clamp-4">
                {product.description}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            {onGenerateCopy && (
              <Button
                variant="tiktrend"
                className="flex-1 gap-2"
                onClick={() => onGenerateCopy(product)}
              >
                <CopyIcon size={16} />
                Gerar Copy
              </Button>
            )}
            {product.productUrl && (
              <Button
                variant="outline"
                className="flex-1 gap-2"
                onClick={() => window.open(product.productUrl, "_blank")}
              >
                <ExportIcon size={16} />
                Ver no TikTok
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
