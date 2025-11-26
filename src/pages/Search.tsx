import * as React from "react";
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
      setError("Erro ao buscar produtos. Tente novamente.");
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Buscar Produtos</h1>
        <p className="text-muted-foreground">
          Encontre produtos em alta no TikTok Shop com filtros avançados
        </p>
      </div>

      {/* Search Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <div className="flex-1">
              <Input
                placeholder="Digite palavras-chave, nome do produto ou categoria..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                icon={<SearchIcon size={18} />}
                className="h-12 text-lg"
              />
            </div>
            <Button
              variant="tiktrend"
              size="lg"
              onClick={handleSearch}
              loading={isSearching}
              className="px-8"
            >
              Buscar
            </Button>
          </div>

          {/* Quick Search Tags */}
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="text-sm text-muted-foreground mr-2">Populares:</span>
            {["Dropshipping", "Gadgets", "Beleza", "Fitness", "Casa Inteligente"].map((tag) => (
              <Badge
                key={tag}
                variant="outline"
                className="cursor-pointer hover:bg-accent transition-colors"
                onClick={() => handleQuickSearch(tag)}
              >
                {tag}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Filters and Results */}
      <div className="grid gap-6 lg:grid-cols-4">
        {/* Sidebar Filters */}
        <Card className="lg:col-span-1 h-fit">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <FilterIcon size={18} />
                Filtros
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                Limpar
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Categories */}
            <div>
              <h4 className="text-sm font-medium mb-3">Categorias</h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {PRODUCT_CATEGORIES.map((category) => (
                  <div
                    key={category.id}
                    onClick={() => toggleCategory(category.id)}
                    className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${
                      selectedCategories.includes(category.id)
                        ? "bg-tiktrend-primary/10 text-tiktrend-primary"
                        : "hover:bg-accent"
                    }`}
                  >
                    <span className="text-lg">{category.icon}</span>
                    <span className="text-sm">{category.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Price Range */}
            <div>
              <h4 className="text-sm font-medium mb-3">Faixa de Preço (R$)</h4>
              <div className="flex gap-2">
                <Input
                  type="number"
                  placeholder="Mín"
                  value={priceMin}
                  onChange={(e) => setPriceMin(e.target.value)}
                  className="w-full"
                />
                <Input
                  type="number"
                  placeholder="Máx"
                  value={priceMax}
                  onChange={(e) => setPriceMax(e.target.value)}
                  className="w-full"
                />
              </div>
            </div>

            {/* Minimum Sales */}
            <div>
              <h4 className="text-sm font-medium mb-3">Vendas Mínimas</h4>
              <Input
                type="number"
                placeholder="Ex: 100"
                value={minSales}
                onChange={(e) => setMinSales(e.target.value)}
              />
            </div>

            <Button variant="tiktrend" className="w-full" onClick={handleSearch}>
              Aplicar Filtros
            </Button>
          </CardContent>
        </Card>

        {/* Main Content Area */}
        <div className="lg:col-span-3 space-y-6">
          {/* Search History */}
          {searchHistory.length > 0 && !hasSearched && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Buscas Recentes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {searchHistory.slice(0, 8).map((term, index) => (
                    <Badge
                      key={index}
                      variant="secondary"
                      className="cursor-pointer hover:bg-secondary/80"
                      onClick={() => handleQuickSearch(term)}
                    >
                      {term}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error State */}
          {error && (
            <Card className="border-destructive">
              <CardContent className="pt-4">
                <p className="text-destructive text-sm">{error}</p>
              </CardContent>
            </Card>
          )}

          {/* Loading State */}
          {isSearching && (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <Card key={i}>
                  <CardContent className="p-4">
                    <Skeleton className="h-40 w-full mb-4" />
                    <Skeleton className="h-4 w-3/4 mb-2" />
                    <Skeleton className="h-4 w-1/2" />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Results */}
          {!isSearching && hasSearched && searchResults.length > 0 && (
            <>
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {totalResults.toLocaleString("pt-BR")} produtos encontrados
                </p>
              </div>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {searchResults.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
            </>
          )}

          {/* No Results */}
          {!isSearching && hasSearched && searchResults.length === 0 && (
            <Card className="min-h-[300px] flex items-center justify-center">
              <div className="text-center p-8">
                <SearchIcon size={48} className="mx-auto mb-4 text-muted-foreground/50" />
                <h3 className="text-xl font-semibold mb-2">Nenhum produto encontrado</h3>
                <p className="text-muted-foreground max-w-md">
                  Tente outros termos de busca ou ajuste os filtros.
                </p>
              </div>
            </Card>
          )}

          {/* Empty State - Before Search */}
          {!isSearching && !hasSearched && (
            <Card className="min-h-[400px] flex items-center justify-center">
              <div className="text-center p-8">
                <div className="mx-auto w-16 h-16 rounded-full bg-tiktrend-primary/10 flex items-center justify-center mb-4">
                  <TrendingIcon size={32} className="text-tiktrend-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Comece sua busca</h3>
                <p className="text-muted-foreground max-w-md">
                  Digite palavras-chave para encontrar os produtos mais vendidos do TikTok Shop.
                  Use filtros de categoria para refinar seus resultados.
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
