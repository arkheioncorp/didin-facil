import * as React from "react";
import { Card, CardContent } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { FavoritesIcon, ExportIcon, CloseIcon, PlusIcon } from "@/components/icons";
import { useFavoritesStore } from "@/stores";

import { getFavorites, getFavoriteLists, removeFavorite as removeFavoriteApi, createFavoriteList, deleteFavoriteList, exportProducts } from "@/lib/tauri";
import type { FavoriteWithProduct, FavoriteList } from "@/types";
import { ProductCard } from "@/components/product";
import { useNavigate } from "react-router-dom";

export const Favorites: React.FC = () => {
  const navigate = useNavigate();
  const [favorites, setFavorites] = React.useState<FavoriteWithProduct[]>([]);
  const [lists, setLists] = React.useState<FavoriteList[]>([]);
  const [selectedListId, setSelectedListId] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [isCreatingList, setIsCreatingList] = React.useState(false);
  const [newListName, setNewListName] = React.useState("");

  const { removeFavorite: removeFromLocalStore } = useFavoritesStore();

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const [favoritesData, listsData] = await Promise.all([
        getFavorites(selectedListId || undefined),
        getFavoriteLists(),
      ]);
      
      setFavorites(favoritesData);
      setLists(listsData);
    } catch (err) {
      console.error("Error fetching favorites:", err);
      setError("Erro ao carregar favoritos");
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    fetchData();
  }, [selectedListId]);

  const handleRemoveFavorite = async (productId: string) => {
    try {
      await removeFavoriteApi(productId);
      removeFromLocalStore(productId);
      setFavorites((prev) => prev.filter((f) => f.product.id !== productId));
    } catch (err) {
      console.error("Error removing favorite:", err);
    }
  };

  const handleCreateList = async () => {
    if (!newListName.trim()) return;
    
    try {
      const newList = await createFavoriteList(newListName.trim());
      setLists((prev) => [...prev, newList]);
      setNewListName("");
      setIsCreatingList(false);
    } catch (err) {
      console.error("Error creating list:", err);
    }
  };

  const handleDeleteList = async (listId: string) => {
    try {
      await deleteFavoriteList(listId);
      setLists((prev) => prev.filter((l) => l.id !== listId));
      if (selectedListId === listId) {
        setSelectedListId(null);
      }
    } catch (err) {
      console.error("Error deleting list:", err);
    }
  };

  const handleExport = async () => {
    try {
      const productIds = favorites.map((f) => f.product.id);
      const filePath = await exportProducts(productIds, "csv");
      console.log("Exported to:", filePath);
    } catch (err) {
      console.error("Error exporting:", err);
    }
  };

  const trendingCount = favorites.filter((f) => f.product.isTrending).length;
  const onSaleCount = favorites.filter((f) => f.product.isOnSale).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Favoritos</h1>
          <p className="text-muted-foreground">
            Seus produtos salvos para análise e criação de copies
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2" disabled={favorites.length === 0} onClick={handleExport}>
            <ExportIcon size={16} />
            Exportar
          </Button>
          <Button
            variant="outline"
            className="gap-2"
            onClick={() => setIsCreatingList(true)}
          >
            <PlusIcon size={16} />
            Nova Lista
          </Button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-4">
            <p className="text-destructive text-sm">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Total Favoritos</div>
          <div className="text-2xl font-bold">{isLoading ? <Skeleton className="h-8 w-12" /> : favorites.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Listas</div>
          <div className="text-2xl font-bold">{isLoading ? <Skeleton className="h-8 w-12" /> : lists.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Em Alta</div>
          <div className="text-2xl font-bold text-tiktrend-primary">
            {isLoading ? <Skeleton className="h-8 w-12" /> : trendingCount}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Em Promoção</div>
          <div className="text-2xl font-bold text-green-500">
            {isLoading ? <Skeleton className="h-8 w-12" /> : onSaleCount}
          </div>
        </Card>
      </div>

      {/* Lists Filter */}
      {lists.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          <Button
            variant={selectedListId === null ? "tiktrend" : "outline"}
            size="sm"
            onClick={() => setSelectedListId(null)}
          >
            Todos
          </Button>
          {lists.map((list) => (
            <Button
              key={list.id}
              variant={selectedListId === list.id ? "tiktrend" : "outline"}
              size="sm"
              onClick={() => setSelectedListId(list.id)}
              className="gap-2"
            >
              {list.name}
              <Badge variant="secondary" className="ml-1">{list.productCount}</Badge>
            </Button>
          ))}
        </div>
      )}

      {/* Create List Modal */}
      {isCreatingList && (
        <Card className="p-4">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Nome da lista..."
              value={newListName}
              onChange={(e) => setNewListName(e.target.value)}
              className="flex-1 px-3 py-2 border rounded-md bg-background"
              autoFocus
            />
            <Button variant="tiktrend" onClick={handleCreateList}>Criar</Button>
            <Button variant="ghost" onClick={() => setIsCreatingList(false)}>Cancelar</Button>
          </div>
        </Card>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <Skeleton className="aspect-square" />
              <CardContent className="p-4">
                <Skeleton className="h-4 w-3/4 mb-2" />
                <Skeleton className="h-4 w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Favorites Grid */}
      {!isLoading && favorites.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {favorites.map(({ product, favorite }) => (
            <ProductCard
              key={favorite.id}
              product={product}
              action={
                <Button
                  variant="ghost"
                  size="icon"
                  className="bg-background/80 hover:bg-destructive hover:text-white h-8 w-8 transition-colors"
                  onClick={() => handleRemoveFavorite(product.id)}
                >
                  <CloseIcon size={16} />
                </Button>
              }
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && favorites.length === 0 && (
        <div className="text-center py-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-muted mb-4">
            <FavoritesIcon size={32} className="text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium mb-2">Nenhum favorito nesta lista</h3>
          <p className="text-muted-foreground mb-6">
            Adicione produtos aos favoritos para vê-los aqui.
          </p>
          <Button variant="tiktrend" onClick={() => navigate("/products")}>
            Explorar Produtos
          </Button>
        </div>
      )}

      {/* Lists Management (Bottom) */}
      <div className="mt-12 border-t pt-8">
        <h3 className="text-lg font-medium mb-4">Gerenciar Listas</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {lists.map((list) => (
            <Card key={list.id} className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full bg-${list.color}-500`} />
                <div>
                  <div className="font-medium">{list.name}</div>
                  <div className="text-xs text-muted-foreground">
                    <Badge variant="secondary">{list.productCount} itens</Badge>
                  </div>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-destructive"
                onClick={() => handleDeleteList(list.id)}
              >
                <CloseIcon size={14} />
              </Button>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};
