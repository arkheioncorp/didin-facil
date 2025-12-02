import * as React from "react";
import { VirtuosoGrid } from "react-virtuoso";
import { MemoizedProductCard } from "@/components/product/ProductCard";
import { cn } from "@/lib/utils";
import type { Product } from "@/types";

// Grid scales - número de colunas
type GridScale = "compact" | "small" | "medium" | "large";

const GRID_SCALE_CONFIG = {
    compact: "grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 2xl:grid-cols-8 gap-3",
    small: "grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4",
    medium: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5",
    large: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
} as const;

interface VirtualizedGridProps {
    products: Product[];
    onFavorite: (product: Product) => void;
    isFavorite: (id: string) => boolean;
    onProductClick?: (product: Product) => void;
    selectedProducts?: Set<string>;
    onSelectProduct?: (productId: string, checked: boolean) => void;
    onEndReached?: () => void;
    gridScale?: GridScale;
}

export const VirtualizedGrid: React.FC<VirtualizedGridProps> = ({
    products,
    onFavorite,
    isFavorite,
    onProductClick,
    selectedProducts,
    onSelectProduct,
    onEndReached,
    gridScale = "medium",
}) => {
    const gridClasses = GRID_SCALE_CONFIG[gridScale];

    return (
        <VirtuosoGrid
            style={{ minHeight: 400 }}
            useWindowScroll
            totalCount={products.length}
            overscan={200}  // Otimizado de 400 para 200 para melhor performance
            endReached={onEndReached}
            components={{
                List: React.forwardRef((props, ref) => {
                    const { style, children, ...rest } = props as React.HTMLAttributes<HTMLDivElement>;
                    return (
                    <div
                        ref={ref}
                        {...rest}
                        style={style}
                        className={cn("grid pb-6", gridClasses)}
                    >
                        {children}
                    </div>
                )}),
                Item: ({ children, ...props }) => (
                    <div {...props} className="h-full">
                        {children}
                    </div>
                )
            }}
            itemContent={(index) => {
                const product = products[index];
                return (
                    <MemoizedProductCard
                        product={product}
                        onFavorite={onFavorite}
                        isFavorite={isFavorite(product.id)}
                        onSelect={onProductClick ? (p) => onProductClick(p) : undefined}
                        isSelected={selectedProducts?.has(product.id)}
                        onCheckboxChange={onSelectProduct ? (p, checked) => onSelectProduct(p.id, checked) : undefined}
                        showCheckbox={true}
                        compact={gridScale === "compact" || gridScale === "small"}
                    />
                );
            }}
        />
    );
};
