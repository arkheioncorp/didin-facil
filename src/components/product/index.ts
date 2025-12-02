export { ProductCard } from "./ProductCard";
export { ProductDetailModal } from "./ProductDetailModal";
// Componente refatorado com arquitetura modular
export { ProductActionsPanelRefactored as ProductActionsPanel } from "./ProductActionsPanelRefactored";
export { ProductHistoryChart } from "./ProductHistoryChart";
// Exports adicionais para uso modular
export * from "./actions";

// New modular components for Products page
export { ProductFilters, type CategoryInfo, type FilterState, type ProductFiltersProps } from "./ProductFilters";
export { ProductToolbar, GRID_SCALE_CONFIG, type ViewMode, type GridScale, type SortOption, type ProductToolbarProps } from "./ProductToolbar";
export { ExportModal, type ExportFormat, type ExportModalProps } from "./ExportModal";
export { VirtualizedGrid } from "./VirtualizedGrid";
