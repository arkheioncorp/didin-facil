import * as React from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { SearchIcon, FilterIcon, TrendingIcon } from "@/components/icons";
import { ProductCard } from "@/components/product";
import { useSearchStore } from "@/stores";
import { PRODUCT_CATEGORIES, CATEGORY_ID_TO_DB, SORT_ID_TO_FIELD } from "@/lib/constants";
import { searchProducts, saveSearchHistory } from "@/lib/tauri";
import { analytics } from "@/lib/analytics";
import type { Product, SearchFilters } from "@/types";

export const Search: React.FC = () => {
  const { t } = useTranslation();
  const [query, setQuery] = React.useState("");
  const [isSearching, setIsSearching] = React.useState(false);
  const [searchResults, setSearchResults] = React.useState<Product[]>([]);
  const [totalResults, setTotalResults] = React.useState(0);
  const [hasSearched, setHasSearched] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const { filters, searchHistory, addToHistory } = useSearchStore();
  const [selectedCategories, setSelectedCategories] = React.useState<string[]>(filters.categories || []);
  const [priceMin, setPriceMin] = React.useState<string>("");
  const [priceMax, setPriceMax] = React.useState<string>("");
  const [minSales, setMinSales] = React.useState<string>("");

  const handleSearch = async () => {
    try {
      setIsSearching(true);
      setError(null);
      setHasSearched(true);

      if (query.trim()) {
        addToHistory(query);
      }

      // Map category IDs to database values
      const mappedCategories = selectedCategories
        .map(id => CATEGORY_ID_TO_DB[id])
        .filter(Boolean);

      // Map sort ID to database field
      const mappedSortBy = SORT_ID_TO_FIELD[filters.sortBy] || filters.sortBy;

      const searchFilters: Partial<SearchFilters> = {
        query: query.trim() || undefined,
        categories: mappedCategories,
        priceMin: priceMin ? parseFloat(priceMin) : undefined,
        priceMax: priceMax ? parseFloat(priceMax) : undefined,
        salesMin: minSales ? parseInt(minSales) : undefined,
        sortBy: mappedSortBy as unknown as SearchFilters["sortBy"],
        sortOrder: filters.sortOrder,
        page: 1,
        pageSize: 20,
      };

      analytics.track('search_performed', {
        query: query.trim(),
        filters: searchFilters
      });

      const response = await searchProducts(searchFilters);
      setSearchResults(response.data);
      setTotalResults(response.total);

      // Save search history to database
      await saveSearchHistory(
        query.trim(),
        searchFilters as SearchFilters,
        response.total
      ).catch(console.error);

    } catch (err) {
      console.error("Search error:", err);
      setError(t("errors.generic"));
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const toggleCategory = (categoryId: string) => {
    setSelectedCategories((prev) =>
      prev.includes(categoryId)
        ? prev.filter((id) => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const clearFilters = () => {
    setSelectedCategories([]);
    setPriceMin("");
    setPriceMax("");
    setMinSales("");
    setQuery("");
  };

  const handleQuickSearch = (tag: string) => {
    setQuery(tag);
  };

  return (
    <div className="space-y-4">
      {/* Search Bar - Compacto e integrado */}
      <Card className="border-0 shadow-none bg-transparent">
        <CardContent className="p-0">
          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                placeholder={t("search.placeholder")}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                icon={<SearchIcon size={16} />}
                className="h-10"
                data-testid="search-input"
              />
            </div>
            <Button
              variant="tiktrend"
              onClick={handleSearch}
              loading={isSearching}
              className="px-6 h-10"
            >
              {t("common.search")}
            </Button>
          </div>

          {/* Quick Search Tags */}
          <div className="mt-3 flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-muted-foreground">{t("search.popular")}:</span>
            {["Dropshipping", "Gadgets", t("search.categories.beauty"), "Fitness", t("search.categories.home")].map((tag) => (
              <Badge
                key={tag}
                variant="secondary"
                className="cursor-pointer hover:bg-accent transition-colors text-xs px-2 py-0.5 font-normal"
                onClick={() => handleQuickSearch(tag)}
              >
                {tag}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Filters and Results */}
      <div className="grid gap-4 lg:grid-cols-5">
        {/* Sidebar Filters - Mais compacto */}
        <Card className="lg:col-span-1 h-fit sticky top-4" data-testid="filters-container">
          <CardHeader className="pb-2 pt-3 px-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-1.5">
                <FilterIcon size={14} />
                {t("search.filters.title")}
              </CardTitle>
              <Button variant="ghost" size="sm" className="h-6 text-xs px-2" onClick={clearFilters}>
                {t("common.clear")}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 px-3 pb-3">
            {/* Categories - Grid compacto */}
            <div>
              <h4 className="text-xs font-medium mb-2 text-muted-foreground">{t("search.filters.categories")}</h4>
              <div className="grid grid-cols-2 gap-1">
                {PRODUCT_CATEGORIES.slice(0, 8).map((category) => (
                  <div
                    key={category.id}
                    onClick={() => toggleCategory(category.id)}
                    className={`flex items-center gap-1.5 px-2 py-1.5 rounded-md cursor-pointer transition-all text-xs ${selectedCategories.includes(category.id)
                        ? "bg-tiktrend-primary/15 text-tiktrend-primary border border-tiktrend-primary/30"
                        : "hover:bg-accent border border-transparent"
                      }`}
                  >
                    <span className="text-sm">{category.icon}</span>
                    <span className="truncate">{category.label.split(' ')[0]}</span>
                  </div>
                ))}
              </div>
              {/* Mais categorias expansível */}
              <details className="mt-1.5">
                <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground py-1">
                  + {PRODUCT_CATEGORIES.length - 8} mais categorias
                </summary>
                <div className="grid grid-cols-2 gap-1 mt-1.5">
                  {PRODUCT_CATEGORIES.slice(8).map((category) => (
                    <div
                      key={category.id}
                      onClick={() => toggleCategory(category.id)}
                      className={`flex items-center gap-1.5 px-2 py-1.5 rounded-md cursor-pointer transition-all text-xs ${selectedCategories.includes(category.id)
                          ? "bg-tiktrend-primary/15 text-tiktrend-primary border border-tiktrend-primary/30"
                          : "hover:bg-accent border border-transparent"
                        }`}
                    >
                      <span className="text-sm">{category.icon}</span>
                      <span className="truncate">{category.label.split(' ')[0]}</span>
                    </div>
                  ))}
                </div>
              </details>
            </div>

            {/* Price Range - Compacto */}
            <div>
              <h4 className="text-xs font-medium mb-2 text-muted-foreground">{t("search.filters.priceRange")}</h4>
              <div className="flex gap-1.5 items-center">
                <Input
                  type="number"
                  placeholder="Min"
                  value={priceMin}
                  onChange={(e) => setPriceMin(e.target.value)}
                  className="h-8 text-xs text-center px-2"
                />
                <span className="text-muted-foreground text-xs">—</span>
                <Input
                  type="number"
                  placeholder="Max"
                  value={priceMax}
                  onChange={(e) => setPriceMax(e.target.value)}
                  className="h-8 text-xs text-center px-2"
                />
              </div>
            </div>

            {/* Minimum Sales - Compacto */}
            <div>
              <h4 className="text-xs font-medium mb-2 text-muted-foreground">{t("search.filters.minSales")}</h4>
              <Input
                type="number"
                placeholder="Ex: 100"
                value={minSales}
                onChange={(e) => setMinSales(e.target.value)}
                className="h-8 text-xs"
              />
            </div>

            <Button variant="tiktrend" className="w-full h-8 text-xs gap-1.5" onClick={handleSearch}>
              <SearchIcon size={12} />
              {t("search.filters.apply")}
            </Button>
          </CardContent>
        </Card>

        {/* Main Content Area */}
        <div className="lg:col-span-4 space-y-4">
          {/* Search History - Mais compacto */}
          {searchHistory.length > 0 && !hasSearched && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <span>🕐</span>
                {t("search.recentSearches")}:
              </span>
              {searchHistory.slice(0, 6).map((term, index) => (
                <Badge
                  key={index}
                  variant="outline"
                  className="cursor-pointer hover:bg-accent hover:border-tiktrend-primary/50 transition-all text-xs px-2 py-0.5"
                  onClick={() => handleQuickSearch(term)}
                >
                  {term}
                </Badge>
              ))}
            </div>
          )}

          {/* Error State */}
          {error && (
            <Card className="border-destructive/50 bg-destructive/5">
              <CardContent className="py-3 flex items-center gap-2">
                <span className="text-destructive">⚠️</span>
                <p className="text-destructive text-sm">{error}</p>
              </CardContent>
            </Card>
          )}

          {/* Loading State - Grid compacto */}
          {isSearching && (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                <Card key={i} className="overflow-hidden">
                  <Skeleton className="aspect-[4/3]" />
                  <CardContent className="p-3 space-y-2">
                    <Skeleton className="h-3 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                    <Skeleton className="h-4 w-1/3" />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Results - Grid mais denso */}
          {!isSearching && hasSearched && searchResults.length > 0 && (
            <>
              <div className="flex items-center justify-between bg-muted/30 rounded-lg px-3 py-2">
                <p className="text-xs">
                  <span className="text-tiktrend-primary font-semibold">{totalResults.toLocaleString("pt-BR")}</span>
                  {" "}{t("search.productsFound")}
                </p>
                <Badge variant="success" dot className="text-xs">{t("search.updatedNow")}</Badge>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" data-testid="product-grid">
                {searchResults.map((product, index) => (
                  <div
                    key={product.id}
                    className="animate-slide-up"
                    style={{ animationDelay: `${index * 30}ms` }}
                  >
                    <ProductCard product={product} />
                  </div>
                ))}
              </div>
            </>
          )}

          {/* No Results - Compacto */}
          {!isSearching && hasSearched && searchResults.length === 0 && (
            <Card className="py-12 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-tiktrend-primary/10 to-tiktrend-secondary/10 flex items-center justify-center mb-4 mx-auto">
                  <SearchIcon size={24} className="text-tiktrend-primary/50" />
                </div>
                <h3 className="text-lg font-semibold mb-1">{t("search.noResults")}</h3>
                <p className="text-muted-foreground text-sm max-w-sm mb-4">
                  {t("search.noResultsHint")}
                </p>
                <Button variant="outline" size="sm" onClick={clearFilters}>
                  {t("search.clearFilters")}
                </Button>
              </div>
            </Card>
          )}

          {/* Empty State - Before Search */}
          {!isSearching && !hasSearched && (
            <Card className="py-16 flex items-center justify-center relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-tiktrend-primary/5 via-transparent to-tiktrend-secondary/5" />
              <div className="text-center relative z-10">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-tiktrend-primary/20 to-tiktrend-secondary/20 flex items-center justify-center mb-4 mx-auto animate-float">
                  <TrendingIcon size={32} className="text-tiktrend-primary" />
                </div>
                <h3 className="text-xl font-bold mb-2">{t("search.startSearch")}</h3>
                <p className="text-muted-foreground text-sm max-w-md mb-4">
                  {t("search.startSearchHint")}
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {["Gadgets", t("search.categories.beauty"), t("search.categories.home")].map((tag) => (
                    <Badge
                      key={tag}
                      variant="outline"
                      className="cursor-pointer hover:bg-tiktrend-primary hover:text-white hover:border-tiktrend-primary transition-all px-3 py-1.5 text-xs"
                      onClick={() => handleQuickSearch(tag)}
                    >
                      {t("search.searchFor")} "{tag}"
                    </Badge>
                  ))}
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default Search;
