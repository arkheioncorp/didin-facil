import * as React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { SparkleIcon, CopyIcon, StarIcon } from "@/components/icons";
import { COPY_TYPES, COPY_TONES } from "@/lib/constants";
import { formatCurrency } from "@/lib/utils";
import { generateCopy, getCopyHistory, getFavorites } from "@/lib/tauri";
import type { FavoriteWithProduct, CopyHistory } from "@/types";
import type { CopyType, CopyTone } from "@/types";
import { analytics } from "@/lib/analytics";

interface CopyFormState {
  selectedProductId: string | null;
  copyType: CopyType;
  tone: CopyTone;
  generatedCopy: string | null;
  isGenerating: boolean;
}

export const Copy: React.FC = () => {
  const [favorites, setFavorites] = React.useState<FavoriteWithProduct[]>([]);
  const [copyHistory, setCopyHistory] = React.useState<CopyHistory[]>([]);
  const [isLoadingFavorites, setIsLoadingFavorites] = React.useState(true);
  const [isLoadingHistory, setIsLoadingHistory] = React.useState(true);
  const [state, setState] = React.useState<CopyFormState>({
    selectedProductId: null,
    copyType: "tiktok_hook",
    tone: "urgent",
    generatedCopy: null,
    isGenerating: false,
  });

  // Load favorites on mount
  React.useEffect(() => {
    const loadFavorites = async () => {
      setIsLoadingFavorites(true);
      try {
        const data = await getFavorites();
        setFavorites(data);
      } catch (err) {
        console.error("Error loading favorites:", err);
      } finally {
        setIsLoadingFavorites(false);
      }
    };

    loadFavorites();
  }, []);

  // Load copy history on mount
  React.useEffect(() => {
    const loadHistory = async () => {
      setIsLoadingHistory(true);
      try {
        const data = await getCopyHistory(20);
        setCopyHistory(data);
      } catch (err) {
        console.error("Error loading copy history:", err);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    loadHistory();
  }, []);

  const handleGenerate = async () => {
    if (!state.selectedProductId) return;

    const selectedFavorite = favorites.find(f => f.product.id === state.selectedProductId);
    if (!selectedFavorite) return;

    setState((prev) => ({ ...prev, isGenerating: true }));
    
    try {
      analytics.track('copy_generated', {
        productId: state.selectedProductId,
        copyType: state.copyType,
        tone: state.tone
      });

      const response = await generateCopy({
        productId: state.selectedProductId,
        productTitle: selectedFavorite.product.title,
        productDescription: selectedFavorite.product.description || "",
        copyType: state.copyType,
        tone: state.tone,
        language: "pt-BR"
      });
      
      setState((prev) => ({ 
        ...prev, 
        generatedCopy: response.content,
        isGenerating: false 
      }));
      
      // Refresh history
      const history = await getCopyHistory();
      setCopyHistory(history);
    } catch (error) {
      console.error("Error generating copy:", error);
      setState((prev) => ({ ...prev, isGenerating: false }));
    }
  };

  const copyToClipboard = () => {
    if (state.generatedCopy) {
      navigator.clipboard.writeText(state.generatedCopy);
    }
  };

  const regenerate = () => {
    handleGenerate();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <SparkleIcon size={32} className="text-tiktrend-primary" />
          Copy AI
        </h1>
        <p className="text-muted-foreground">
          Gere textos persuasivos para seus produtos com inteligência artificial
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Form */}
        <Card>
          <CardHeader>
            <CardTitle>Criar Nova Copy</CardTitle>
            <CardDescription>
              Selecione um produto e configure o estilo do texto
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Product Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Selecione um produto</label>
              {isLoadingFavorites ? (
                <div className="space-y-2">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : favorites.length > 0 ? (
                <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto">
                  {favorites.map((fav) => (
                    <div
                      key={fav.product.id}
                      onClick={() => setState((prev) => ({ ...prev, selectedProductId: fav.product.id }))}
                      className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${
                        state.selectedProductId === fav.product.id
                          ? "bg-tiktrend-primary/10 border border-tiktrend-primary"
                          : "hover:bg-accent border border-transparent"
                      }`}
                    >
                      <img
                        src={fav.product.imageUrl || "https://placehold.co/50x50"}
                        alt={fav.product.title}
                        className="w-10 h-10 rounded object-cover"
                      />
                      <div className="flex-1 min-w-0">
                        <span className="text-sm line-clamp-1">{fav.product.title}</span>
                        <span className="text-xs text-muted-foreground">{formatCurrency(fav.product.price)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground p-4 text-center border rounded-lg">
                  Adicione produtos aos favoritos para gerar copies
                </div>
              )}
            </div>

            {/* Copy Type */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Tipo de Copy</label>
              <div className="grid grid-cols-2 gap-2">
                {COPY_TYPES.map((type) => (
                  <div
                    key={type.id}
                    onClick={() => setState((prev) => ({ ...prev, copyType: type.id as CopyType }))}
                    className={`flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-colors ${
                      state.copyType === type.id
                        ? "bg-tiktrend-primary/10 border border-tiktrend-primary"
                        : "hover:bg-accent border border-transparent"
                    }`}
                  >
                    <span className="text-lg">{type.icon}</span>
                    <span className="text-sm">{type.name}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Tone */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Tom de Voz</label>
              <div className="flex flex-wrap gap-2">
                {COPY_TONES.map((tone) => (
                  <Badge
                    key={tone.id}
                    variant={state.tone === tone.id ? "tiktrend" : "outline"}
                    className="cursor-pointer py-1.5 px-3"
                    onClick={() => setState((prev) => ({ ...prev, tone: tone.id as CopyTone }))}
                  >
                    {tone.icon} {tone.name}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Generate Button */}
            <Button
              variant="tiktrend"
              size="lg"
              className="w-full gap-2"
              onClick={handleGenerate}
              disabled={!state.selectedProductId || state.isGenerating}
            >
              <SparkleIcon size={18} />
              {state.isGenerating ? "Gerando..." : "Gerar Copy"}
            </Button>
          </CardContent>
        </Card>

        {/* Result */}
        <Card>
          <CardHeader>
            <CardTitle>Copy Gerada</CardTitle>
            <CardDescription>
              Copie e use nas suas campanhas de marketing
            </CardDescription>
          </CardHeader>
          <CardContent>
            {state.isGenerating ? (
              <div className="space-y-4">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-32 w-full" />
              </div>
            ) : state.generatedCopy ? (
              <div className="space-y-4">
                <div className="bg-muted rounded-lg p-4 whitespace-pre-wrap font-mono text-sm max-h-[300px] overflow-y-auto">
                  {state.generatedCopy}
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" className="gap-2 flex-1" onClick={copyToClipboard}>
                    <CopyIcon size={16} />
                    Copiar
                  </Button>
                  <Button variant="outline" className="gap-2 flex-1" onClick={regenerate}>
                    <SparkleIcon size={16} />
                    Gerar Outra
                  </Button>
                </div>
              </div>
            ) : (
              <div className="min-h-[300px] flex items-center justify-center text-center text-muted-foreground">
                <div>
                  <SparkleIcon size={48} className="mx-auto mb-4 opacity-50" />
                  <p>Selecione um produto e clique em "Gerar Copy"</p>
                  <p className="text-sm mt-2">para criar textos persuasivos com IA</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* History */}
      <Card>
        <CardHeader>
          <CardTitle>Histórico de Copies</CardTitle>
          <CardDescription>
            Suas copies geradas recentemente
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingHistory ? (
            <div className="space-y-4">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          ) : copyHistory.length > 0 ? (
            <div className="space-y-4">
              {copyHistory.map((copy) => (
                <div
                  key={copy.id}
                  className="p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{copy.copyType}</Badge>
                      <Badge variant="secondary">{copy.tone}</Badge>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {new Date(copy.createdAt).toLocaleDateString("pt-BR")}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {copy.content}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigator.clipboard.writeText(copy.content)}
                    >
                      <CopyIcon size={14} className="mr-1" />
                      Copiar
                    </Button>
                    {copy.isFavorite && (
                      <StarIcon size={14} filled className="text-yellow-400" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <p>Nenhuma copy gerada ainda</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
