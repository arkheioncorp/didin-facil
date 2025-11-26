import * as React from "react";
import { VirtuosoGrid } from "react-virtuoso";
import { ProductCard } from "@/components/product";
import type { Product } from "@/types";

interface VirtualizedGridProps {
    products: Product[];
    onFavorite: (product: Product) => void;
    isFavorite: (id: string) => boolean;
}

export const VirtualizedGrid: React.FC<VirtualizedGridProps> = ({ products, onFavorite, isFavorite }) => {
    return (
        <VirtuosoGrid
            style={{ height: "calc(100vh - 250px)" }}
            totalCount={products.length}
            overscan={200}
            components={{
                List: React.forwardRef((props, ref) => {
                    const { style, children, ...rest } = props as React.HTMLAttributes<HTMLDivElement>;
                    return (
                    <div
                        ref={ref}
                        {...rest}
                        style={style}
                        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-6"
                        data-testid="products-grid"
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
            itemContent={(index) => (
                <ProductCard
                    product={products[index]}
                    onFavorite={onFavorite}
                    isFavorite={isFavorite(products[index].id)}
                />
            )}
        />
    );
};
