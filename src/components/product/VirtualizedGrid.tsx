import * as React from "react";
import { VirtuosoGrid } from "react-virtuoso";
import { ProductCard } from "@/components/product";
import type { Product } from "@/types";

interface VirtualizedGridProps {
    products: Product[];
    onFavorite: (product: Product) => void;
    isFavorite: (id: string) => boolean;
    onProductClick?: (product: Product) => void;
    selectedProducts?: Set<string>;
    onSelectProduct?: (productId: string, checked: boolean) => void;
    onEndReached?: () => void;
}

export const VirtualizedGrid: React.FC<VirtualizedGridProps> = ({
    products,
    onFavorite,
    isFavorite,
    onProductClick,
    selectedProducts,
    onSelectProduct,
    onEndReached,
}) => {
    return (
        <VirtuosoGrid
            style={{ minHeight: 400 }}
            useWindowScroll
            totalCount={products.length}
            overscan={400}
            endReached={onEndReached}
            components={{
                List: React.forwardRef((props, ref) => {
                    const { style, children, ...rest } = props as React.HTMLAttributes<HTMLDivElement>;
                    return (
                    <div
                        ref={ref}
                        {...rest}
                        style={style}
                        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-6"
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
                    <ProductCard
                        product={product}
                        onFavorite={onFavorite}
                        isFavorite={isFavorite(product.id)}
                        onSelect={onProductClick ? (p) => onProductClick(p) : undefined}
                        isSelected={selectedProducts?.has(product.id)}
                        onCheckboxChange={onSelectProduct ? (p, checked) => onSelectProduct(p.id, checked) : undefined}
                        showCheckbox={true}
                    />
                );
            }}
        />
    );
};
