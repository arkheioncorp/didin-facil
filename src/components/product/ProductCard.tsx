import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { FavoritesIcon, TrendingIcon, StarIcon } from "@/components/icons";
import { cn, formatCurrency, formatNumber } from "@/lib/utils";
import type { Product } from "@/types";
import { Sparkles, Calendar, MessageCircle, MoreHorizontal } from "lucide-react";

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
  // Quick actions
  showQuickActions?: boolean;
  // Compact mode for smaller grid scales
  compact?: boolean;
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
  showQuickActions = true,
  compact = false,
}) => {
  const navigate = useNavigate();
  const discount = product.originalPrice
    ? Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)
    : 0;

  // Quick action handlers
  const handleQuickCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/copy?productId=${product.id}&title=${encodeURIComponent(product.title)}&price=${product.price}`);
  };

  const handleQuickSchedule = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/automation/scheduler?productId=${product.id}`);
  };

  const handleQuickWhatsApp = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/whatsapp?action=send&productId=${product.id}`);
  };

  return (
    <Card
      hover
      className="overflow-hidden group cursor-pointer"
      onClick={() => onSelect?.(product)}
      data-testid="product-card"
    >
      {/* Image Container */}
      <div className={cn("relative bg-muted overflow-hidden", compact ? "aspect-[4/3]" : "aspect-square")}>
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
            className={cn("absolute z-20", compact ? "top-2 left-2" : "top-3 left-3")}
            onClick={(e) => e.stopPropagation()}
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => onCheckboxChange?.(product, e.target.checked)}
              data-testid="product-checkbox"
              className={cn(
                "rounded bg-white/90 dark:bg-black/50 backdrop-blur-sm border-2 cursor-pointer accent-tiktrend-primary",
                compact ? "h-4 w-4" : "h-5 w-5"
              )}
            />
          </div>
        )}

        {/* Badges - Top Left (shifted when checkbox is shown) */}
        <div className={cn(
          "absolute flex flex-col gap-1",
          compact ? "top-2" : "top-3",
          showCheckbox ? (compact ? 'left-8' : 'left-10') : (compact ? 'left-2' : 'left-3')
        )}>
          {product.isTrending && (
            <Badge variant="tiktrend" className={cn("gap-1 shadow-lg", compact ? "text-[10px] px-1.5 py-0.5" : "text-xs")}>
              <TrendingIcon size={compact ? 8 : 10} />
              {!compact && "Em Alta"}
            </Badge>
          )}
          {discount > 0 && (
            <Badge variant="destructive" className={cn("font-bold shadow-lg", compact ? "text-[10px] px-1.5 py-0.5" : "text-xs")}>
              -{discount}%
            </Badge>
          )}
          {product.hasFreeShipping && !compact && (
            <Badge variant="success" className="text-xs shadow-lg">
              Frete Grátis
            </Badge>
          )}
        </div>

        {/* Favorite Button or Custom Action - Top Right */}
        {action ? (
          <div
            className={cn("absolute z-10", compact ? "top-2 right-2" : "top-3 right-3")}
            onClick={(e) => e.stopPropagation()}
          >
            {action}
          </div>
        ) : onFavorite ? (
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "absolute bg-white/90 dark:bg-black/50 backdrop-blur-sm hover:bg-white dark:hover:bg-black/70 rounded-full shadow-lg transition-all duration-300",
              compact ? "top-2 right-2 h-7 w-7" : "top-3 right-3 h-9 w-9",
              isFavorite ? 'scale-110' : 'opacity-0 group-hover:opacity-100'
            )}
            onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
              e.stopPropagation();
              onFavorite(product);
            }}
            data-testid="favorite-button"
          >
            <FavoritesIcon
              size={compact ? 14 : 18}
              className={`transition-colors ${isFavorite ? "fill-tiktrend-primary text-tiktrend-primary" : "text-muted-foreground"}`}
            />
          </Button>
        ) : null}

        {/* Quick Actions Bar - Appears on Hover (hidden in compact) */}
        {showQuickActions && !compact && (
          <div className="absolute bottom-12 left-0 right-0 px-3 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-2 group-hover:translate-y-0">
            <TooltipProvider>
              <div className="flex items-center justify-center gap-1 bg-black/70 backdrop-blur-sm rounded-full p-1">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 rounded-full text-white hover:bg-white/20"
                      onClick={handleQuickCopy}
                    >
                      <Sparkles size={14} />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="text-xs">
                    Gerar Copy IA
                  </TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 rounded-full text-white hover:bg-white/20"
                      onClick={handleQuickSchedule}
                    >
                      <Calendar size={14} />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="text-xs">
                    Agendar Post
                  </TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 rounded-full text-white hover:bg-white/20"
                      onClick={handleQuickWhatsApp}
                    >
                      <MessageCircle size={14} />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="text-xs">
                    WhatsApp
                  </TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 rounded-full text-white hover:bg-white/20"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelect?.(product);
                      }}
                    >
                      <MoreHorizontal size={14} />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="text-xs">
                    Ver Todas Ações
                  </TooltipContent>
                </Tooltip>
              </div>
            </TooltipProvider>
          </div>
        )}

        {/* Quick Stats Overlay - Bottom (hidden in compact) */}
        {!compact && (
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
        )}
      </div>

      {/* Content */}
      <CardContent className={cn(compact ? "p-2.5" : "p-4")}>
        {/* Category - hidden in compact */}
        {!compact && (
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="secondary" size="sm" className="text-xs">
              {product.category || "Sem categoria"}
            </Badge>
          </div>
        )}

        {/* Title */}
        <h3
          className={cn(
            "font-medium line-clamp-2 group-hover:text-tiktrend-primary transition-colors",
            compact ? "text-xs leading-tight mb-1.5 min-h-[32px]" : "mb-3 min-h-[44px] text-sm leading-snug"
          )}
          data-testid="product-title"
        >
          {product.title}
        </h3>

        {/* Price */}
        <div className={cn("flex items-baseline gap-1.5", compact ? "mb-1.5" : "mb-3")}>
          <span
            className={cn("font-bold text-tiktrend-primary", compact ? "text-base" : "text-xl")}
            data-testid="product-price"
          >
            {formatCurrency(product.price)}
          </span>
          {product.originalPrice && (
            <span className={cn("text-muted-foreground line-through", compact ? "text-[10px]" : "text-xs")}>
              {formatCurrency(product.originalPrice)}
            </span>
          )}
        </div>

        {/* Stats Row - simplified in compact mode */}
        <div className={cn(
          "flex items-center justify-between text-muted-foreground border-t",
          compact ? "text-[10px] pt-1.5" : "text-xs pt-3"
        )}>
          <div className="flex items-center gap-1">
            <StarIcon size={compact ? 10 : 14} filled className="text-yellow-500" />
            <span className="font-medium">{product.productRating?.toFixed(1) || "N/A"}</span>
            {!compact && <span className="text-muted-foreground/60">({formatNumber(product.reviewsCount)})</span>}
          </div>
          <span className="font-medium" data-testid="product-sales">
            {formatNumber(product.salesCount)} {compact ? "" : "vendas"}
          </span>
        </div>

        {/* Sales Trend - hidden in compact mode */}
        {!compact && product.sales7d > 0 && (
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

// Memoized ProductCard to prevent unnecessary re-renders
// Only re-renders when product data, favorite status, or selection changes
export const MemoizedProductCard = React.memo(ProductCard, (prevProps, nextProps) => {
  return (
    prevProps.product.id === nextProps.product.id &&
    prevProps.product.price === nextProps.product.price &&
    prevProps.product.salesCount === nextProps.product.salesCount &&
    prevProps.isFavorite === nextProps.isFavorite &&
    prevProps.isSelected === nextProps.isSelected &&
    prevProps.compact === nextProps.compact
  );
});
