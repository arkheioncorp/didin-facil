import React from "react";
import { Play, Square, Loader2, TrendingUp, Package, AlertCircle, Settings2, RefreshCw, Wifi } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useStartScraper, useTestProxy, useSyncProducts } from "@/hooks";
import { useQuery } from "@tanstack/react-query";
import { invoke } from "@tauri-apps/api/core";
import { toast } from "@/hooks/use-toast";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

import { ScraperStatus } from "@/types";

export function ScraperControl() {
    // Initialize from localStorage or default
    const [selectedCategories, setSelectedCategories] = React.useState<string[]>(() => {
        const saved = localStorage.getItem("scraper_categories");
        return saved ? JSON.parse(saved) : ["trending"];
    });

    const [maxProducts, setMaxProducts] = React.useState(() => {
        const saved = localStorage.getItem("scraper_max_products");
        return saved ? parseInt(saved) : 50;
    });

    const [headless, setHeadless] = React.useState(() => {
        const saved = localStorage.getItem("scraper_headless");
        return saved ? JSON.parse(saved) : true;
    });

    const startScraper = useStartScraper();
    const testProxy = useTestProxy();
    const syncProducts = useSyncProducts();
    const logsEndRef = React.useRef<HTMLDivElement>(null);
    const [proxyToTest, setProxyToTest] = React.useState("");

    // Persist changes
    React.useEffect(() => {
        localStorage.setItem("scraper_categories", JSON.stringify(selectedCategories));
    }, [selectedCategories]);

    React.useEffect(() => {
        localStorage.setItem("scraper_max_products", maxProducts.toString());
    }, [maxProducts]);

    React.useEffect(() => {
        localStorage.setItem("scraper_headless", JSON.stringify(headless));
    }, [headless]);

    // Poll scraper status every 1 second for smoother logs
    const { data: status } = useQuery<ScraperStatus>({
        queryKey: ["scraperStatus"],
        queryFn: async () => {
            try {
                return await invoke<ScraperStatus>("get_scraper_status");
            } catch {
                return {
                    isRunning: false,
                    productsFound: 0,
                    progress: 0,
                    currentProduct: null,
                    errors: [],
                    startedAt: null,
                    statusMessage: "Pronto para iniciar",
                    logs: []
                };
            }
        },
        refetchInterval: 1000,
        refetchIntervalInBackground: true,
    });

    // Auto-scroll logs
    React.useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [status?.logs]);

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
                headless,
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

    const handleTestProxy = async () => {
        if (!proxyToTest) return;
        const isValid = await testProxy.mutateAsync(proxyToTest);
        toast({
            title: isValid ? "✅ Proxy Válido" : "❌ Proxy Inválido",
            description: isValid ? "Conexão estabelecida com sucesso" : "Não foi possível conectar",
            variant: isValid ? "default" : "destructive",
        });
    };

    const handleSync = async () => {
        try {
            const count = await syncProducts.mutateAsync();
            toast({
                title: "Sincronização Concluída",
                description: `${count} produtos enviados para o servidor`,
            });
        } catch (e) {
            toast({
                title: "Erro na Sincronização",
                description: String(e),
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

    const isRunning = status?.isRunning || false;
    const progress = status?.progress || 0;
    const productsFound = status?.productsFound || 0;
    const logs = status?.logs || [];
    const statusMessage = status?.statusMessage || "Pronto para iniciar";

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
                            <Badge variant="default" className="bg-green-500 text-white animate-pulse">
                                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                                {statusMessage}
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

                {/* Headless Mode */}
                <div className="flex items-center justify-between p-3 border rounded-lg bg-secondary/20">
                    <div className="space-y-0.5">
                        <label className="text-sm font-medium">Modo Headless</label>
                        <p className="text-xs text-muted-foreground">
                            Ocultar navegador durante a coleta
                        </p>
                    </div>
                    <Button
                        variant={headless ? "default" : "outline"}
                        size="sm"
                        onClick={() => setHeadless(!headless)}
                        disabled={isRunning}
                    >
                        {headless ? "Ativado" : "Desativado"}
                    </Button>
                </div>

                {/* Progress & Logs */}
                <div className="space-y-4">
                    {isRunning && (
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="font-medium">Progresso Geral</span>
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
                        </div>
                    )}

                    {/* Visual Log Terminal */}
                    <div className="bg-black/90 rounded-lg p-4 font-mono text-xs h-48 overflow-y-auto border border-border shadow-inner">
                        <div className="space-y-1">
                            {logs.length === 0 ? (
                                <div className="text-muted-foreground opacity-50 italic">
                                    Aguardando início do processo...
                                </div>
                            ) : (
                                logs.map((log, i) => (
                                    <div key={i} className="text-green-400/90 break-words">
                                        <span className="opacity-50 mr-2">{log.split(']')[0]}]</span>
                                        <span>{log.split(']')[1]}</span>
                                    </div>
                                ))
                            )}
                            <div ref={logsEndRef} />
                        </div>
                    </div>
                </div>

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

                {/* Proxy Testing */}
                <div className="space-y-3">
                    <label className="text-sm font-medium">🧪 Testar Proxy</label>
                    <div className="flex gap-2">
                        <Input
                            placeholder="http://meu-proxy:porta"
                            value={proxyToTest}
                            onChange={(e) => setProxyToTest(e.target.value)}
                            disabled={isRunning}
                            className="flex-1"
                        />
                        <Button
                            onClick={handleTestProxy}
                            disabled={isRunning}
                            className="whitespace-nowrap"
                        >
                            Testar
                        </Button>
                    </div>
                </div>

                {/* Sync Products */}
                <div className="space-y-3">
                    <label className="text-sm font-medium">🔄 Sincronizar Produtos</label>
                    <Button
                        onClick={handleSync}
                        disabled={isRunning}
                        className="w-full"
                    >
                        Sincronizar Agora
                    </Button>
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

            {/* Advanced Tools Dialog */}
            <Dialog>
                <DialogTrigger asChild>
                    <Button variant="outline" size="icon" className="shrink-0">
                        <Settings2 className="w-4 h-4" />
                    </Button>
                </DialogTrigger>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Ferramentas Avançadas</DialogTitle>
                        <DialogDescription>
                            Utilitários para manutenção do scraper
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Testar Proxy</label>
                            <div className="flex gap-2">
                                <Input
                                    placeholder="http://user:pass@ip:port"
                                    value={proxyToTest}
                                    onChange={(e) => setProxyToTest(e.target.value)}
                                />
                                <Button
                                    onClick={handleTestProxy}
                                    disabled={testProxy.isPending}
                                >
                                    {testProxy.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wifi className="w-4 h-4" />}
                                </Button>
                            </div>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Sincronizar Dados</label>
                            <Button
                                variant="secondary"
                                className="w-full"
                                onClick={handleSync}
                                disabled={syncProducts.isPending}
                            >
                                {syncProducts.isPending ? (
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                ) : (
                                    <RefreshCw className="w-4 h-4 mr-2" />
                                )}
                                Enviar Produtos para Nuvem
                            </Button>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </Card>
    );
}
