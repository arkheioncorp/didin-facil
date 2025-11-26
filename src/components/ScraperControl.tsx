import React from "react";
import { Play, Square, Loader2, TrendingUp, Package, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useStartScraper } from "@/hooks";
import { useQuery } from "@tanstack/react-query";
import { invoke } from "@tauri-apps/api/core";
import { toast } from "@/hooks/use-toast";

interface ScraperStatus {
    is_running: boolean;
    current_category?: string;
    products_found: number;
    progress_percentage: number;
    status_message: string;
}

export function ScraperControl() {
    const [selectedCategories, setSelectedCategories] = React.useState<string[]>(["trending"]);
    const [maxProducts, setMaxProducts] = React.useState(50);
    const startScraper = useStartScraper();

    // Poll scraper status every 2 seconds
    const { data: status } = useQuery<ScraperStatus>({
        queryKey: ["scraperStatus"],
        queryFn: async () => {
            try {
                return await invoke<ScraperStatus>("get_scraper_status");
            } catch {
                return {
                    is_running: false,
                    products_found: 0,
                    progress_percentage: 0,
                    status_message: "Pronto para iniciar",
                };
            }
        },
        refetchInterval: 2000,
        refetchIntervalInBackground: true,
    });

    const handleStartScraping = async () => {
        if (selectedCategories.length === 0) {
            toast({
                title: "Selecione categorias",
                description: "Escolha pelo menos uma categoria para coletar",
                variant: "destructive",
            });
            return;
        }

        try {
            await startScraper.mutateAsync({
                maxProducts,
                categories: selectedCategories,
                useProxy: false,
            });

            toast({
                title: "✅ Scraping iniciado!",
                description: `Coletando até ${maxProducts} produtos...`,
            });
        } catch (error) {
            toast({
                title: "❌ Erro ao iniciar",
                description: String(error),
                variant: "destructive",
            });
        }
    };

    const handleStopScraping = async () => {
        try {
            await invoke("stop_scraper");
            toast({
                title: "⏹️ Scraping parado",
                description: "Coleta foi interrompida",
            });
        } catch (error) {
            toast({
                title: "Erro",
                description: String(error),
                variant: "destructive",
            });
        }
    };

    const categories = [
        { id: "trending", label: "🔥 Em Alta", icon: TrendingUp },
        { id: "beauty", label: "💄 Beleza", icon: Package },
        { id: "electronics", label: "📱 Eletrônicos", icon: Package },
        { id: "fashion", label: "👗 Moda", icon: Package },
        { id: "home", label: "🏠 Casa", icon: Package },
    ];

    const isRunning = status?.is_running || false;
    const progress = status?.progress_percentage || 0;
    const productsFound = status?.products_found || 0;

    return (
        <Card className="col-span-2">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="text-2xl">🕷️ Coletor de Produtos</CardTitle>
                        <CardDescription>
                            Busque produtos em alta do TikTok Shop
                        </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                        {isRunning ? (
                            <Badge variant="default" className="bg-green-500 text-white">
                                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                                Coletando...
                            </Badge>
                        ) : (
                            <Badge variant="secondary">
                                ⏸️ Pausado
                            </Badge>
                        )}
                    </div>
                </div>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* Categories Selection */}
                <div className="space-y-3">
                    <label className="text-sm font-medium">📂 Categorias</label>
                    <div className="flex flex-wrap gap-2">
                        {categories.map((cat) => {
                            const isSelected = selectedCategories.includes(cat.id);
                            return (
                                <Button
                                    key={cat.id}
                                    variant={isSelected ? "default" : "outline"}
                                    size="sm"
                                    onClick={() => {
                                        setSelectedCategories((prev) =>
                                            isSelected
                                                ? prev.filter((c) => c !== cat.id)
                                                : [...prev, cat.id]
                                        );
                                    }}
                                    disabled={isRunning}
                                >
                                    {cat.label}
                                </Button>
                            );
                        })}
                    </div>
                    <p className="text-xs text-muted-foreground">
                        {selectedCategories.length} categoria(s) selecionada(s)
                    </p>
                </div>

                {/* Max Products */}
                <div className="space-y-2">
                    <label className="text-sm font-medium">🎯 Produtos por Categoria</label>
                    <div className="flex gap-2">
                        {[20, 50, 100, 200].map((num) => (
                            <Button
                                key={num}
                                variant={maxProducts === num ? "default" : "outline"}
                                size="sm"
                                onClick={() => setMaxProducts(num)}
                                disabled={isRunning}
                            >
                                {num}
                            </Button>
                        ))}
                    </div>
                </div>

                {isRunning && (
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                            <span className="font-medium">Progresso</span>
                            <span className="text-muted-foreground">
                                {productsFound} produtos encontrados
                            </span>
                        </div>
                        <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                            <div
                                className="h-full bg-primary transition-all duration-300"
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                        <p className="text-xs text-muted-foreground">
                            {status?.status_message || "Processando..."}
                        </p>
                    </div>
                )}

                {/* Actions */}
                <div className="flex gap-3">
                    {!isRunning ? (
                        <Button
                            onClick={handleStartScraping}
                            disabled={startScraper.isPending}
                            className="flex-1"
                            size="lg"
                        >
                            {startScraper.isPending ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Iniciando...
                                </>
                            ) : (
                                <>
                                    <Play className="w-4 h-4 mr-2" />
                                    Iniciar Coleta
                                </>
                            )}
                        </Button>
                    ) : (
                        <Button
                            onClick={handleStopScraping}
                            variant="destructive"
                            className="flex-1"
                            size="lg"
                        >
                            <Square className="w-4 h-4 mr-2" />
                            Parar Coleta
                        </Button>
                    )}
                </div>

                {/* Info Alert */}
                <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
                    <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                    <div className="text-sm text-blue-900 dark:text-blue-100">
                        <p className="font-medium mb-1">💡 Dica:</p>
                        <p className="text-blue-700 dark:text-blue-300">
                            O coletor busca produtos reais do TikTok Shop. Para testar, use as categorias acima.
                            Os produtos serão salvos automaticamente no banco de dados local.
                        </p>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
