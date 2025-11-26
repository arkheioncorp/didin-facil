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
            {/* Melhoria #14: Price Range visual */}
            <div>
              <h4 className="text-sm font-medium mb-3">Faixa de Preço (R$)</h4>
              <div className="flex gap-2">
                <Input
                  type="number"
                  placeholder="Mín"
                  value={priceMin}
                  onChange={(e) => setPriceMin(e.target.value)}
                  className="w-full text-center"
                />
                <span className="text-muted-foreground self-center">—</span>
                <Input
                  type="number"
                  placeholder="Máx"
                  value={priceMax}
                  onChange={(e) => setPriceMax(e.target.value)}
                  className="w-full text-center"
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

            <Button variant="tiktrend" className="w-full gap-2" onClick={handleSearch}>
              <SearchIcon size={16} />
              Aplicar Filtros
            </Button>
          </CardContent>
        </Card>

        {/* Main Content Area */}
        <div className="lg:col-span-3 space-y-6">
          {/* Search History - Melhoria visual */}
          {searchHistory.length > 0 && !hasSearched && (
            <Card className="border-dashed">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <span className="w-6 h-6 rounded-lg bg-muted flex items-center justify-center text-sm">🕐</span>
                  Buscas Recentes
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {searchHistory.slice(0, 8).map((term, index) => (
                    <Badge
                      key={index}
                      variant="outline"
                      className="cursor-pointer hover:bg-accent hover:border-tiktrend-primary transition-all px-3 py-1.5"
                      onClick={() => handleQuickSearch(term)}
                    >
                      {term}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error State - Melhoria #15 */}
          {error && (
            <Card className="border-destructive/50 bg-destructive/5">
              <CardContent className="pt-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-destructive/10 flex items-center justify-center shrink-0">
                  <span className="text-destructive text-lg">!</span>
                </div>
                <p className="text-destructive text-sm">{error}</p>
              </CardContent>
            </Card>
          )}

          {/* Loading State - Melhoria #24 */}
          {isSearching && (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <Card key={i} className="overflow-hidden">
                  <Skeleton className="aspect-square" />
                  <CardContent className="p-4 space-y-3">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-6 w-1/3" />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Results - Melhoria visual */}
          {!isSearching && hasSearched && searchResults.length > 0 && (
            <>
              <div className="flex items-center justify-between bg-muted/50 rounded-xl px-4 py-3">
                <p className="text-sm font-medium">
                  <span className="text-tiktrend-primary font-bold">{totalResults.toLocaleString("pt-BR")}</span>
                  {" "}produtos encontrados
                </p>
                <Badge variant="success" dot>Atualizado agora</Badge>
              </div>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {searchResults.map((product, index) => (
                  <div
                    key={product.id}
                    className="animate-slide-up"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <ProductCard product={product} />
                  </div>
                ))}
              </div>
            </>
          )}

          {/* No Results - Melhoria #15 */}
          {!isSearching && hasSearched && searchResults.length === 0 && (
            <Card className="min-h-[300px] flex items-center justify-center">
              <div className="empty-state">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-tiktrend-primary/10 to-tiktrend-secondary/10 flex items-center justify-center mb-6">
                  <SearchIcon size={32} className="text-tiktrend-primary/50" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Nenhum produto encontrado</h3>
                <p className="text-muted-foreground max-w-md">
                  Tente outros termos de busca ou ajuste os filtros.
                </p>
                <Button variant="outline" className="mt-4" onClick={clearFilters}>
                  Limpar Filtros
                </Button>
              </div>
            </Card>
          )}

          {/* Empty State - Before Search - Melhoria #15 */}
          {!isSearching && !hasSearched && (
            <Card className="min-h-[400px] flex items-center justify-center relative overflow-hidden">
              {/* Background decoration */}
              <div className="absolute inset-0 bg-gradient-to-br from-tiktrend-primary/5 via-transparent to-tiktrend-secondary/5" />
              <div className="empty-state relative z-10">
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-tiktrend-primary/20 to-tiktrend-secondary/20 flex items-center justify-center mb-6 mx-auto animate-float">
                  <TrendingIcon size={40} className="text-tiktrend-primary" />
                </div>
                <h3 className="text-2xl font-bold mb-3">Comece sua busca</h3>
                <p className="text-muted-foreground max-w-md mb-6">
                  Digite palavras-chave para encontrar os produtos mais vendidos do TikTok Shop.
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {["Gadgets", "Beleza", "Casa"].map((tag) => (
                    <Badge
                      key={tag}
                      variant="outline"
                      className="cursor-pointer hover:bg-tiktrend-primary hover:text-white hover:border-tiktrend-primary transition-all px-4 py-2"
                      onClick={() => handleQuickSearch(tag)}
                    >
                      Buscar "{tag}"
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
