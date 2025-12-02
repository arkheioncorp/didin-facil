/**
 * ProductToolbar Component
 * 
 * Toolbar component for Products page.
 * Handles view mode, grid scale, sorting, and select all.
 * 
 * @performance
 * - Memoized to prevent unnecessary re-renders
 * - Uses localStorage for view preferences persistence
 */

import * as React from "react";
import { useTranslation } from "react-i18next";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { Grid3X3, Grid2X2, LayoutGrid, List, Rows3, Rows4 } from "lucide-react";

// ============================================
// TYPES
// ============================================

export type ViewMode = "grid" | "list";
export type GridScale = "compact" | "small" | "medium" | "large";

export interface SortOption {
  value: string;
  label: string;
}

export interface ProductToolbarProps {
  // View mode
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  
  // Grid scale
  gridScale: GridScale;
  onGridScaleChange: (scale: GridScale) => void;
  
  // Sort
  sortValue: string | null;
  sortOptions: SortOption[];
  onSortChange: (value: string) => void;
  
  // Selection
  isAllSelected: boolean;
  hasProducts: boolean;
  onSelectAll: (checked: boolean) => void;
}

// Grid scale configuration
export const GRID_SCALE_CONFIG = {
  compact: { 
    label: "Compacto", 
    cols: "grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 2xl:grid-cols-8", 
    icon: Rows4 
  },
  small: { 
    label: "Pequeno", 
    cols: "grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6", 
    icon: Rows3 
  },
  medium: { 
    label: "Médio", 
    cols: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4", 
    icon: Grid2X2 
  },
  large: { 
    label: "Grande", 
    cols: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3", 
    icon: LayoutGrid 
  },
} as const;

// ============================================
// COMPONENT
// ============================================

export const ProductToolbar: React.FC<ProductToolbarProps> = React.memo(({
  viewMode,
  onViewModeChange,
  gridScale,
  onGridScaleChange,
  sortValue,
  sortOptions,
  onSortChange,
  isAllSelected,
  hasProducts,
  onSelectAll,
}) => {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-between">
      {/* Select All */}
      <label className="flex items-center gap-2 cursor-pointer">
        <input 
          type="checkbox" 
          className="rounded"
          checked={isAllSelected && hasProducts}
          onChange={(e) => onSelectAll(e.target.checked)}
          disabled={!hasProducts}
          data-testid="select-all"
        />
        <span className="text-sm">{t("products.select_all")}</span>
      </label>

      <div className="flex items-center gap-3">
        {/* Grid Scale Selector - Only visible in grid mode */}
        {viewMode === "grid" && (
          <div className="flex items-center gap-1 border rounded-lg p-1">
            {(Object.entries(GRID_SCALE_CONFIG) as [GridScale, typeof GRID_SCALE_CONFIG[GridScale]][]).map(([key, config]) => {
              const Icon = config.icon;
              return (
                <TooltipProvider key={key}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => onGridScaleChange(key)}
                        className={cn(
                          "p-1.5 rounded transition-colors",
                          gridScale === key ? "bg-accent" : "hover:bg-accent/50"
                        )}
                        data-testid={`grid-scale-${key}`}
                      >
                        <Icon size={14} />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">
                      {config.label}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              );
            })}
          </div>
        )}

        {/* View Mode Toggle */}
        <div className="flex items-center gap-1 border rounded-lg p-1">
          <button
            onClick={() => onViewModeChange("grid")}
            className={cn(
              "p-2 rounded transition-colors",
              viewMode === "grid" ? "bg-accent" : "hover:bg-accent/50"
            )}
            data-testid="grid-view"
          >
            <Grid3X3 size={16} />
          </button>
          <button
            onClick={() => onViewModeChange("list")}
            className={cn(
              "p-2 rounded transition-colors",
              viewMode === "list" ? "bg-accent" : "hover:bg-accent/50"
            )}
            data-testid="list-view"
          >
            <List size={16} />
          </button>
        </div>

        {/* Sort Select */}
        <Select value={sortValue || ""} onValueChange={onSortChange}>
          <SelectTrigger className="w-[180px]" data-testid="sort-select">
            <SelectValue placeholder="Mais Recentes" />
          </SelectTrigger>
          <SelectContent>
            {sortOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
});

ProductToolbar.displayName = "ProductToolbar";
