import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FavoritesIcon, TrendingIcon, StarIcon } from "@/components/icons";
import { formatCurrency, formatNumber } from "@/lib/utils";
import type { Product } from "@/types";

interface ProductCardProps {
  product: Product;
  onFavorite?: (product: Product) => void;
  isFavorite?: boolean;
  onSelect?: (product: Product) => void;
  action?: React.ReactNode;
  // Bulk selection props
  showCheckbox?: boolean;
  isSelected?: boolean;
  onCheckboxChange?: (product: Product, checked: boolean) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onFavorite,
  isFavorite = false,
  onSelect,
  action,
  showCheckbox = false,
  isSelected = false,
  onCheckboxChange,
}) => {
  const discount = product.originalPrice
    ? Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)
    : 0;

  return (
    <Card
      hover
      className="overflow-hidden group cursor-pointer"
      onClick={() => onSelect?.(product)}
      data-testid="product-card"
    >
      {/* Image Container - Melhoria #13: Hover reveal */}
      <div className="relative aspect-square bg-muted overflow-hidden">
        <img
          src={product.imageUrl || "https://placehold.co/300x300/1a1a2e/ffffff?text=Produto"}
          alt={product.title}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          loading="lazy"
        />

        {/* Gradient Overlay on Hover */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        {/* Checkbox for Bulk Selection */}
        {showCheckbox && (
          <div
            className="absolute top-3 left-3 z-20"
            onClick={(e) => e.stopPropagation()}
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => onCheckboxChange?.(product, e.target.checked)}
              data-testid="product-checkbox"
              className="h-5 w-5 rounded bg-white/90 dark:bg-black/50 backdrop-blur-sm border-2 cursor-pointer accent-tiktrend-primary"
            />
          </div>
        )}

        {/* Badges - Top Left (shifted when checkbox is shown) */}
        <div className={`absolute top-3 ${showCheckbox ? 'left-10' : 'left-3'} flex flex-col gap-1.5`}>
          {product.isTrending && (
            <Badge variant="tiktrend" className="gap-1 text-xs shadow-lg">
              <TrendingIcon size={10} />
              Em Alta
            </Badge>
          )}
          {discount > 0 && (
            <Badge variant="destructive" className="text-xs font-bold shadow-lg">
              -{discount}%
            </Badge>
          )}
          {product.hasFreeShipping && (
            <Badge variant="success" className="text-xs shadow-lg">
              Frete Grátis
            </Badge>
          )}
        </div>

        {/* Favorite Button or Custom Action - Top Right */}
        {action ? (
          <div
            className="absolute top-3 right-3 z-10"
            onClick={(e) => e.stopPropagation()}
          >
            {action}
          </div>
        ) : onFavorite ? (
          <Button
            variant="ghost"
            size="icon"
            className={`absolute top-3 right-3 bg-white/90 dark:bg-black/50 backdrop-blur-sm hover:bg-white dark:hover:bg-black/70 h-9 w-9 rounded-full shadow-lg transition-all duration-300 ${isFavorite ? 'scale-110' : 'opacity-0 group-hover:opacity-100'}`}
            onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
              e.stopPropagation();
              onFavorite(product);
            }}
            data-testid="favorite-button"
          >
            <FavoritesIcon
              size={18}
              className={`transition-colors ${isFavorite ? "fill-tiktrend-primary text-tiktrend-primary" : "text-muted-foreground"}`}
            />
          </Button>
        ) : null}

        {/* Quick Stats Overlay - Bottom */}
        <div className="absolute bottom-0 left-0 right-0 p-3 translate-y-full group-hover:translate-y-0 transition-transform duration-300">
          <div className="flex items-center justify-between text-white text-xs font-medium">
            <div className="flex items-center gap-1 bg-black/50 backdrop-blur-sm rounded-full px-2 py-1">
              <StarIcon size={12} filled className="text-yellow-400" />
              <span>{product.productRating?.toFixed(1) || "N/A"}</span>
            </div>
            <div className="bg-black/50 backdrop-blur-sm rounded-full px-2 py-1">
              {formatNumber(product.salesCount)} vendas
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <CardContent className="p-4">
        {/* Category */}
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="secondary" size="sm" className="text-xs">
            {product.category || "Sem categoria"}
          </Badge>
        </div>

        {/* Title */}
        <h3
          className="font-medium line-clamp-2 mb-3 min-h-[44px] text-sm leading-snug group-hover:text-tiktrend-primary transition-colors"
          data-testid="product-title"
        >
          {product.title}
        </h3>

        {/* Price */}
        <div className="flex items-baseline gap-2 mb-3">
          <span
            className="text-xl font-bold text-tiktrend-primary"
            data-testid="product-price"
          >
            {formatCurrency(product.price)}
          </span>
          {product.originalPrice && (
            <span className="text-xs text-muted-foreground line-through">
              {formatCurrency(product.originalPrice)}
            </span>
          )}
        </div>

        {/* Stats Row */}
        <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t">
          <div className="flex items-center gap-1.5">
            <StarIcon size={14} filled className="text-yellow-500" />
            <span className="font-medium">{product.productRating?.toFixed(1) || "N/A"}</span>
            <span className="text-muted-foreground/60">({formatNumber(product.reviewsCount)})</span>
          </div>
          <span className="font-medium" data-testid="product-sales">{formatNumber(product.salesCount)} vendas</span>
        </div>

        {/* Sales Trend - Melhoria #22: Visual de tendência */}
        {product.sales7d > 0 && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Vendas 7d</span>
              <div className="flex items-center gap-1.5">
                <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary rounded-full"
                    style={{ width: `${Math.min((product.sales7d / 1000) * 100, 100)}%` }}
                  />
                </div>
                <span className="text-xs font-semibold text-green-500">+{formatNumber(product.sales7d)}</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
