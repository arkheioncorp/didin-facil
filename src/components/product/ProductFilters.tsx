/**
 * ProductFilters Component
 * 
 * Sidebar filter component for Products page.
 * Handles category, price range, sales, and quick filters.
 * 
 * @performance
 * - Uses controlled inputs to minimize re-renders
 * - Filters are applied on button click, not on every change
 */

import * as React from "react";
import { useTranslation } from "react-i18next";
import { Card } from "@/components/ui";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { X } from "lucide-react";

// ============================================
// TYPES
// ============================================

export interface CategoryInfo {
  name: string;
  slug: string;
  count: number;
}

export interface ProductFiltersProps {
  // Current filter values from URL
  category: string;
  minPrice: string;
  maxPrice: string;
  minSales: string;
  showTrending: boolean;
  showOnSale: boolean;
  showFreeShipping: boolean;
  
  // Available categories
  categories: CategoryInfo[];
  
  // Handlers
  onCategoryChange: (value: string) => void;
  onApplyFilters: (filters: FilterState) => void;
  onClearFilters: () => void;
  
  // State
  hasActiveFilters: boolean;
}

export interface FilterState {
  minPrice: string;
  maxPrice: string;
  minSales: string;
  trending?: boolean;
  onSale?: boolean;
  freeShipping?: boolean;
}

// ============================================
// COMPONENT
// ============================================

export const ProductFilters: React.FC<ProductFiltersProps> = React.memo(({
  category,
  minPrice,
  maxPrice,
  minSales,
  showTrending,
  showOnSale,
  showFreeShipping,
  categories,
  onCategoryChange,
  onApplyFilters,
  onClearFilters,
  hasActiveFilters,
}) => {
  const { t } = useTranslation();
  
  // Local filter state (for form before apply)
  const [filterMinPrice, setFilterMinPrice] = React.useState(minPrice);
  const [filterMaxPrice, setFilterMaxPrice] = React.useState(maxPrice);
  const [filterMinSales, setFilterMinSales] = React.useState(minSales);
  const [filterTrending, setFilterTrending] = React.useState(showTrending);
  const [filterOnSale, setFilterOnSale] = React.useState(showOnSale);
  const [filterFreeShipping, setFilterFreeShipping] = React.useState(showFreeShipping);

  // Sync local state when URL params change
  React.useEffect(() => {
    setFilterMinPrice(minPrice);
    setFilterMaxPrice(maxPrice);
    setFilterMinSales(minSales);
    setFilterTrending(showTrending);
    setFilterOnSale(showOnSale);
    setFilterFreeShipping(showFreeShipping);
  }, [minPrice, maxPrice, minSales, showTrending, showOnSale, showFreeShipping]);

  const handleApply = () => {
    onApplyFilters({
      minPrice: filterMinPrice,
      maxPrice: filterMaxPrice,
      minSales: filterMinSales,
      trending: filterTrending,
      onSale: filterOnSale,
      freeShipping: filterFreeShipping,
    });
  };

  const handleClear = () => {
    setFilterMinPrice("");
    setFilterMaxPrice("");
    setFilterMinSales("");
    setFilterTrending(false);
    setFilterOnSale(false);
    setFilterFreeShipping(false);
    onClearFilters();
  };

  return (
    <aside className="lg:w-64 shrink-0" data-testid="filter-sidebar">
      <Card className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{t("search.filters.title")}</h3>
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClear}
              data-testid="clear-filters"
              className="text-xs"
            >
              <X size={14} className="mr-1" />
              {t("common.clear")}
            </Button>
          )}
        </div>

        {/* Category Filter */}
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("search.filters.category")}</label>
          <Select value={category} onValueChange={onCategoryChange}>
            <SelectTrigger className="w-full" data-testid="category-filter">
              <SelectValue placeholder={t("products.all_categories")} />
            </SelectTrigger>
            <SelectContent>
              {categories.map((cat) => (
                <SelectItem key={cat.slug} value={cat.slug}>
                  {cat.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Price Range */}
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("search.filters.priceRange")}</label>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder={t("search.filters.min")}
              value={filterMinPrice}
              onChange={(e) => setFilterMinPrice(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border bg-background text-sm"
              data-testid="min-price"
            />
            <input
              type="number"
              placeholder={t("search.filters.max")}
              value={filterMaxPrice}
              onChange={(e) => setFilterMaxPrice(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border bg-background text-sm"
              data-testid="max-price"
            />
          </div>
        </div>

        {/* Min Sales */}
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("search.filters.minSales")}</label>
          <input
            type="number"
            placeholder={t("search.filters.minSalesPlaceholder")}
            value={filterMinSales}
            onChange={(e) => setFilterMinSales(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border bg-background text-sm"
            data-testid="min-sales"
          />
        </div>

        {/* Quick Filters */}
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("products.quick_filters")}</label>
          <div className="space-y-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input 
                type="checkbox" 
                className="rounded"
                checked={filterTrending}
                onChange={(e) => setFilterTrending(e.target.checked)}
              />
              <span className="text-sm">{t("products.trending")}</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input 
                type="checkbox" 
                className="rounded"
                checked={filterOnSale}
                onChange={(e) => setFilterOnSale(e.target.checked)}
              />
              <span className="text-sm">{t("products.on_sale")}</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input 
                type="checkbox" 
                className="rounded"
                checked={filterFreeShipping}
                onChange={(e) => setFilterFreeShipping(e.target.checked)}
              />
              <span className="text-sm">{t("products.free_shipping")}</span>
            </label>
          </div>
        </div>

        {/* Apply Button */}
        <Button 
          onClick={handleApply} 
          className="w-full"
          data-testid="apply-filters"
        >
          {t("search.filters.apply")}
        </Button>
      </Card>
    </aside>
  );
});

ProductFilters.displayName = "ProductFilters";
