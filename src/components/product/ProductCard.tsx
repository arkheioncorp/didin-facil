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
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onFavorite,
  isFavorite = false,
  onSelect,
  action,
}) => {
  const discount = product.originalPrice
    ? Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)
    : 0;

  return (
    <Card 
      hover 
      className="overflow-hidden cursor-pointer" 
      onClick={() => onSelect?.(product)}
    >
      {/* Image */}
      <div className="relative aspect-square bg-muted">
        <img
          src={product.imageUrl || "https://placehold.co/300x300/1a1a2e/ffffff?text=Produto"}
          alt={product.title}
          className="w-full h-full object-cover transition-transform hover:scale-105"
          loading="lazy"
        />
        
        {/* Badges */}
        <div className="absolute top-2 left-2 flex flex-col gap-1">
          {product.isTrending && (
            <Badge variant="tiktrend" className="gap-1 text-xs">
              <TrendingIcon size={10} />
              Em Alta
            </Badge>
          )}
          {discount > 0 && (
            <Badge variant="destructive" className="text-xs">-{discount}%</Badge>
          )}
          {product.hasFreeShipping && (
            <Badge variant="success" className="text-xs">Frete Grátis</Badge>
          )}
        </div>

        {/* Favorite Button or Custom Action */}
        {action ? (
          <div 
            className="absolute top-2 right-2 z-10"
            onClick={(e) => e.stopPropagation()}
          >
            {action}
          </div>
        ) : onFavorite ? (
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-2 right-2 bg-background/80 hover:bg-background h-8 w-8"
            onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
              e.stopPropagation();
              onFavorite(product);
            }}
          >
            <FavoritesIcon
              size={16}
              className={isFavorite ? "fill-tiktrend-primary text-tiktrend-primary" : ""}
            />
          </Button>
        ) : null}
      </div>

      {/* Content */}
      <CardContent className="p-4">
        {/* Category */}
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="secondary" className="text-xs">
            {product.category || "Sem categoria"}
          </Badge>
        </div>

        {/* Title */}
        <h3 className="font-medium line-clamp-2 mb-2 min-h-[40px] text-sm">
          {product.title}
        </h3>

        {/* Price */}
        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-lg font-bold text-tiktrend-primary">
            {formatCurrency(product.price)}
          </span>
          {product.originalPrice && (
            <span className="text-xs text-muted-foreground line-through">
              {formatCurrency(product.originalPrice)}
            </span>
          )}
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <StarIcon size={12} filled className="text-yellow-400" />
            <span>{product.productRating?.toFixed(1) || "N/A"}</span>
            <span>({formatNumber(product.reviewsCount)})</span>
          </div>
          <span>{formatNumber(product.salesCount)} vendas</span>
        </div>

        {/* Sales Trend */}
        {product.sales7d > 0 && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Vendas 7d</span>
              <span className="font-medium text-green-500">+{formatNumber(product.sales7d)}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
