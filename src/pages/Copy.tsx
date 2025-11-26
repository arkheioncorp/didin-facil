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
import { useToast } from "@/hooks/use-toast";

interface CopyFormState {
  selectedProductId: string | null;
  copyType: CopyType;
  tone: CopyTone;
  generatedCopy: string | null;
  isGenerating: boolean;
}

export const Copy: React.FC = () => {
  const { toast } = useToast();
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

      if (String(error).includes("QUOTA_EXCEEDED")) {
        toast({
          title: "Limite de cota atingido",
          description: "Você atingiu o limite de gerações do seu plano. Atualize para continuar.",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Erro ao gerar copy",
          description: "Ocorreu um erro ao gerar a copy. Tente novamente.",
          variant: "destructive",
        });
      }
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

            {/* Tone - Melhoria #14 */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Tom de Voz</label>
              <div className="flex flex-wrap gap-2">
                {COPY_TONES.map((tone) => (
                  <Badge
                    key={tone.id}
                    variant={state.tone === tone.id ? "tiktrend" : "outline"}
                    className="cursor-pointer py-2 px-4 transition-all hover:scale-105"
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
              className="w-full gap-2 shadow-lg shadow-tiktrend-primary/25"
              onClick={handleGenerate}
              disabled={!state.selectedProductId || state.isGenerating}
            >
              <SparkleIcon size={18} className={state.isGenerating ? "animate-spin" : ""} />
              {state.isGenerating ? "Gerando..." : "Gerar Copy com IA"}
            </Button>
          </CardContent>
        </Card>

        {/* Result - Melhoria #19: Preview estilo post */}
        <Card className="overflow-hidden">
          <CardHeader className="border-b bg-muted/30">
            <CardTitle className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-tiktrend-primary to-tiktrend-secondary flex items-center justify-center text-white text-sm">
                ✨
              </span>
              Copy Gerada
            </CardTitle>
            <CardDescription>
              Copie e use nas suas campanhas de marketing
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {state.isGenerating ? (
              <div className="space-y-4 animate-pulse">
                <div className="flex items-center gap-3 mb-4">
                  <Skeleton className="w-10 h-10 rounded-full" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-3 w-16" />
                  </div>
                </div>
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-32 w-full rounded-xl" />
              </div>
            ) : state.generatedCopy ? (
              <div className="space-y-4">
                {/* Post preview - TikTok style */}
                <div className="copy-preview rounded-xl p-5 bg-gradient-to-br from-gray-900 to-gray-800 text-white relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-r from-tiktrend-primary/10 to-tiktrend-secondary/10" />
                  <div className="relative">
                    {/* Fake profile header */}
                    <div className="flex items-center gap-3 mb-4 pb-4 border-b border-white/10">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary flex items-center justify-center text-sm font-bold">
                        TT
                      </div>
                      <div>
                        <p className="font-semibold text-sm">@sua_loja</p>
                        <p className="text-xs text-gray-400">Agora</p>
                      </div>
                    </div>
                    {/* Copy content */}
                    <div className="whitespace-pre-wrap text-sm leading-relaxed max-h-[250px] overflow-y-auto scrollbar-thin">
                      {state.generatedCopy}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="tiktrend"
                    className="gap-2 flex-1 shadow-lg"
                    onClick={copyToClipboard}
                  >
                    <CopyIcon size={16} />
                    Copiar Texto
                  </Button>
                  <Button variant="outline" className="gap-2" onClick={regenerate}>
                    <SparkleIcon size={16} />
                    Regenerar
                  </Button>
                </div>
              </div>
            ) : (
              <div className="min-h-[300px] flex items-center justify-center text-center">
                <div className="empty-state">
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-tiktrend-primary/10 to-tiktrend-secondary/10 flex items-center justify-center mb-6 mx-auto animate-float">
                    <SparkleIcon size={32} className="text-tiktrend-primary/50" />
                  </div>
                  <h3 className="font-semibold mb-2">Pronto para criar</h3>
                  <p className="text-muted-foreground text-sm">
                    Selecione um produto e clique em "Gerar Copy"
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* History - Melhoria visual */}
      <Card>
        <CardHeader className="border-b">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Histórico de Copies</CardTitle>
              <CardDescription>
                Suas copies geradas recentemente
              </CardDescription>
            </div>
            {copyHistory.length > 0 && (
              <Badge variant="secondary" className="font-mono">{copyHistory.length}</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {isLoadingHistory ? (
            <div className="space-y-4">
              <Skeleton className="h-24 w-full rounded-xl" />
              <Skeleton className="h-24 w-full rounded-xl" />
            </div>
          ) : copyHistory.length > 0 ? (
            <div className="space-y-3">
              {copyHistory.map((copy, index) => (
                <div
                  key={copy.id}
                  className="p-4 border rounded-xl hover:bg-accent/50 hover:border-tiktrend-primary/30 transition-all cursor-pointer group animate-slide-up"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" size="sm">{copy.copyType}</Badge>
                      <Badge variant="secondary" size="sm">{copy.tone}</Badge>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {new Date(copy.createdAt).toLocaleDateString("pt-BR", { day: '2-digit', month: 'short' })}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                    {copy.content}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => navigator.clipboard.writeText(copy.content)}
                    >
                      <CopyIcon size={12} className="mr-1" />
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
            <div className="empty-state py-12">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4 mx-auto">
                <CopyIcon size={24} className="text-muted-foreground" />
              </div>
              <p className="text-muted-foreground">Nenhuma copy gerada ainda</p>
              <p className="text-sm text-muted-foreground/60 mt-1">Suas copies aparecerão aqui</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
