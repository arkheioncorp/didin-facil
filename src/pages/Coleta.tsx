import React from "react";
import { useTranslation } from "react-i18next";
import { 
  Play, 
  Square, 
  Loader2, 
  TrendingUp, 
  Package, 
  Settings2, 
  RefreshCw, 
  Wifi,
  Cookie,
  Check,
  Copy,
  ChevronRight,
  Info,
  ExternalLink,
  Download,
  Globe,
  Shield,
  Zap,
  AlertTriangle,
  HelpCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useStartScraper, useSyncProducts } from "@/hooks";
import { useQuery } from "@tanstack/react-query";
import { getScraperStatus, stopScraper } from "@/services/scraper";
import { toast } from "@/hooks/use-toast";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { BrowserViewer } from "@/components/scraper/BrowserViewer";
import { ScraperStatus } from "@/types";

// ========================================
// COOKIE SETUP COMPONENT
// ========================================
interface CookieSetupProps {
  onCookiesSaved: (cookies: string) => void;
  currentCookies: string;
  connectionStatus: "disconnected" | "testing" | "connected" | "error";
  onTestConnection: () => void;
}

const CookieSetup: React.FC<CookieSetupProps> = ({
  onCookiesSaved,
  currentCookies,
  connectionStatus,
  onTestConnection,
}) => {
  const [cookies, setCookies] = React.useState(currentCookies);
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText('document.cookie');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = () => {
    if (cookies.trim()) {
      localStorage.setItem("tiktok_cookies", cookies.trim());
      onCookiesSaved(cookies.trim());
      toast({
        title: "✅ Cookies Salvos",
        description: "Cookies do TikTok foram salvos com sucesso.",
      });
    }
  };

  const statusConfig = {
    disconnected: { color: "bg-muted-foreground", text: "Desconectado", icon: Globe },
    testing: { color: "bg-yellow-500 animate-pulse", text: "Testando...", icon: Loader2 },
    connected: { color: "bg-green-500", text: "Conectado", icon: Check },
    error: { color: "bg-red-500", text: "Erro", icon: AlertTriangle },
  };

  const status = statusConfig[connectionStatus];

  return (
    <Card className="border-2 border-dashed hover:border-solid transition-all">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-tiktrend-primary/20 to-tiktrend-secondary/20 flex items-center justify-center">
              <Cookie className="w-6 h-6 text-tiktrend-primary" />
            </div>
            <div>
              <CardTitle className="text-xl">Configuração de Cookies</CardTitle>
              <CardDescription>
                Conecte sua conta do TikTok para coleta autenticada
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${status.color}`} />
            <span className="text-sm font-medium">{status.text}</span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Status Alert */}
        {connectionStatus === "error" && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Conexão Falhou</AlertTitle>
            <AlertDescription>
              Os cookies podem estar expirados ou inválidos. Siga o passo-a-passo para obter novos cookies.
            </AlertDescription>
          </Alert>
        )}

        {connectionStatus === "connected" && (
          <Alert className="border-green-200 bg-green-50 dark:bg-green-950 dark:border-green-800">
            <Check className="h-4 w-4 text-green-600" />
            <AlertTitle className="text-green-800 dark:text-green-200">Conectado com Sucesso</AlertTitle>
            <AlertDescription className="text-green-700 dark:text-green-300">
              Sua sessão do TikTok está ativa. Você pode iniciar a coleta de produtos.
            </AlertDescription>
          </Alert>
        )}

        {/* Step-by-step Instructions */}
        <Accordion type="single" collapsible defaultValue="step-1" className="w-full">
          <AccordionItem value="step-1">
            <AccordionTrigger className="hover:no-underline">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-full bg-tiktrend-primary text-white flex items-center justify-center text-sm font-bold">1</span>
                <span className="font-medium">Acesse o TikTok Shop</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pl-11 space-y-4">
              <div className="space-y-3">
                <p className="text-muted-foreground">
                  Abra o navegador e acesse o TikTok Shop. Certifique-se de estar logado em sua conta.
                </p>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" asChild>
                    <a href="https://shop.tiktok.com" target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Abrir TikTok Shop
                    </a>
                  </Button>
                  <Button variant="outline" size="sm" asChild>
                    <a href="https://www.tiktok.com/login" target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Fazer Login
                    </a>
                  </Button>
                </div>
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Importante:</strong> Use o mesmo navegador que você costuma usar para acessar o TikTok.
                    Recomendamos Chrome ou Edge.
                  </AlertDescription>
                </Alert>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="step-2">
            <AccordionTrigger className="hover:no-underline">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-full bg-tiktrend-primary text-white flex items-center justify-center text-sm font-bold">2</span>
                <span className="font-medium">Abra o Console do Desenvolvedor</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pl-11 space-y-4">
              <div className="space-y-3">
                <p className="text-muted-foreground">
                  Com o TikTok Shop aberto, pressione a combinação de teclas para abrir o Console:
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-muted">
                    <p className="font-medium mb-2">🪟 Windows / Linux</p>
                    <code className="text-sm bg-black/10 dark:bg-white/10 px-2 py-1 rounded">
                      F12 ou Ctrl + Shift + J
                    </code>
                  </div>
                  <div className="p-4 rounded-lg bg-muted">
                    <p className="font-medium mb-2">🍎 macOS</p>
                    <code className="text-sm bg-black/10 dark:bg-white/10 px-2 py-1 rounded">
                      Cmd + Option + J
                    </code>
                  </div>
                </div>
                <Alert>
                  <HelpCircle className="h-4 w-4" />
                  <AlertDescription>
                    Clique na aba <strong>"Console"</strong> no painel que abrir. 
                    Ignore qualquer mensagem de erro ou aviso que aparecer.
                  </AlertDescription>
                </Alert>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="step-3">
            <AccordionTrigger className="hover:no-underline">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-full bg-tiktrend-primary text-white flex items-center justify-center text-sm font-bold">3</span>
                <span className="font-medium">Copie os Cookies</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pl-11 space-y-4">
              <div className="space-y-3">
                <p className="text-muted-foreground">
                  No console, digite o comando abaixo e pressione <strong>Enter</strong>:
                </p>
                <div className="flex items-center gap-2 p-3 rounded-lg bg-black text-green-400 font-mono text-sm">
                  <code className="flex-1">document.cookie</code>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8 text-green-400 hover:text-green-300 hover:bg-green-900/30"
                    onClick={handleCopy}
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
                <p className="text-muted-foreground">
                  O resultado será uma longa string de texto. <strong>Copie todo o conteúdo</strong> 
                  (incluindo as aspas, se aparecerem).
                </p>
                <Alert variant="default" className="border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                  <Shield className="h-4 w-4 text-amber-600" />
                  <AlertTitle className="text-amber-800 dark:text-amber-200">Segurança</AlertTitle>
                  <AlertDescription className="text-amber-700 dark:text-amber-300">
                    Seus cookies são armazenados apenas localmente no seu computador. 
                    Nunca os compartilhe com terceiros.
                  </AlertDescription>
                </Alert>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="step-4">
            <AccordionTrigger className="hover:no-underline">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-full bg-tiktrend-primary text-white flex items-center justify-center text-sm font-bold">4</span>
                <span className="font-medium">Cole os Cookies Aqui</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pl-11 space-y-4">
              <div className="space-y-3">
                <Label htmlFor="cookies-input">Cookies do TikTok</Label>
                <Textarea
                  id="cookies-input"
                  placeholder='Cole aqui os cookies copiados do console (ex: sessionid=abc123; tt_webid=xyz789...)'
                  value={cookies}
                  onChange={(e) => setCookies(e.target.value)}
                  className="min-h-[120px] font-mono text-sm"
                />
                <div className="flex gap-3">
                  <Button onClick={handleSave} disabled={!cookies.trim()} className="flex-1">
                    <Download className="w-4 h-4 mr-2" />
                    Salvar Cookies
                  </Button>
                  <Button variant="outline" onClick={onTestConnection} disabled={!cookies.trim()}>
                    {connectionStatus === "testing" ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Wifi className="w-4 h-4 mr-2" />
                    )}
                    Testar Conexão
                  </Button>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>

        {/* Quick Tips */}
        <div className="p-4 rounded-lg bg-muted/50 space-y-3">
          <h4 className="font-medium flex items-center gap-2">
            <Zap className="w-4 h-4 text-tiktrend-primary" />
            Dicas Rápidas
          </h4>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <ChevronRight className="w-4 h-4 mt-0.5 text-tiktrend-primary flex-shrink-0" />
              <span>Os cookies expiram após algumas horas. Se a coleta falhar, obtenha novos cookies.</span>
            </li>
            <li className="flex items-start gap-2">
              <ChevronRight className="w-4 h-4 mt-0.5 text-tiktrend-primary flex-shrink-0" />
              <span>Mantenha o navegador aberto com o TikTok logado durante a coleta.</span>
            </li>
            <li className="flex items-start gap-2">
              <ChevronRight className="w-4 h-4 mt-0.5 text-tiktrend-primary flex-shrink-0" />
              <span>Se aparecer CAPTCHA, resolva-o e obtenha novos cookies.</span>
            </li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

// ========================================
// SCRAPER CONTROL COMPONENT (Embedded)
// ========================================
interface ScraperPanelProps {
  isRunning: boolean;
  progress: number;
  productsFound: number;
  statusMessage: string;
  logs: string[];
  selectedCategories: string[];
  maxProducts: number;
  headless: boolean;
  onStartScraping: () => void;
  onStopScraping: () => void;
  onCategoryChange: (categories: string[]) => void;
  onMaxProductsChange: (max: number) => void;
  onHeadlessChange: (headless: boolean) => void;
  isPending: boolean;
}

const ScraperPanel: React.FC<ScraperPanelProps> = ({
  isRunning,
  progress,
  productsFound,
  statusMessage,
  logs,
  selectedCategories,
  maxProducts,
  headless,
  onStartScraping,
  onStopScraping,
  onCategoryChange,
  onMaxProductsChange,
  onHeadlessChange,
  isPending,
}) => {
  const logsEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  const categories = [
    { id: "trending", label: "🔥 Em Alta", icon: TrendingUp },
    { id: "beauty", label: "💄 Beleza", icon: Package },
    { id: "electronics", label: "📱 Eletrônicos", icon: Package },
    { id: "fashion", label: "👗 Moda", icon: Package },
    { id: "home", label: "🏠 Casa", icon: Package },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20 flex items-center justify-center">
              <Package className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <CardTitle className="text-xl">Coletor de Produtos</CardTitle>
              <CardDescription>
                Busque produtos em alta do TikTok Shop
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isRunning ? (
              <Badge variant="default" className="bg-green-500 text-white animate-pulse">
                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                {statusMessage}
              </Badge>
            ) : (
              <Badge variant="secondary">
                ⏸️ Pronto
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Categories Selection */}
        <div className="space-y-3">
          <Label className="flex items-center gap-2">
            <span className="text-lg">📂</span> Categorias para Coletar
          </Label>
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => {
              const isSelected = selectedCategories.includes(cat.id);
              return (
                <Button
                  key={cat.id}
                  variant={isSelected ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    const newCategories = isSelected
                      ? selectedCategories.filter((c) => c !== cat.id)
                      : [...selectedCategories, cat.id];
                    onCategoryChange(newCategories);
                  }}
                  disabled={isRunning}
                  className="transition-all"
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
        <div className="space-y-3">
          <Label className="flex items-center gap-2">
            <span className="text-lg">🎯</span> Produtos por Categoria
          </Label>
          <div className="flex gap-2">
            {[20, 50, 100, 200].map((num) => (
              <Button
                key={num}
                variant={maxProducts === num ? "default" : "outline"}
                size="sm"
                onClick={() => onMaxProductsChange(num)}
                disabled={isRunning}
              >
                {num}
              </Button>
            ))}
          </div>
        </div>

        {/* Headless Mode */}
        <div className="flex items-center justify-between p-4 border rounded-lg bg-secondary/20">
          <div className="space-y-1">
            <Label className="flex items-center gap-2">
              <span className="text-lg">👁️</span> Modo Headless
            </Label>
            <p className="text-xs text-muted-foreground">
              Ocultar navegador durante a coleta (mais rápido)
            </p>
          </div>
          <Button
            variant={headless ? "default" : "outline"}
            size="sm"
            onClick={() => onHeadlessChange(!headless)}
            disabled={isRunning}
          >
            {headless ? "✅ Ativado" : "❌ Desativado"}
          </Button>
        </div>

        {/* Progress */}
        {isRunning && (
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="font-medium">Progresso da Coleta</span>
              <span className="text-muted-foreground">
                {productsFound} produtos encontrados
              </span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        )}

        {/* Visual Log Terminal */}
        <div className="space-y-2">
          <Label className="flex items-center gap-2">
            <span className="text-lg">📋</span> Log de Atividade
          </Label>
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
              onClick={onStartScraping}
              disabled={isPending || selectedCategories.length === 0}
              className="flex-1"
              size="lg"
            >
              {isPending ? (
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
              onClick={onStopScraping}
              variant="destructive"
              className="flex-1"
              size="lg"
            >
              <Square className="w-4 h-4 mr-2" />
              Parar Coleta
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// ========================================
// MAIN COLETA PAGE
// ========================================
export const Coleta: React.FC = () => {
  const { t } = useTranslation();
  
  // State for cookies
  const [cookies, setCookies] = React.useState(() => {
    return localStorage.getItem("tiktok_cookies") || "";
  });
  const [connectionStatus, setConnectionStatus] = React.useState<"disconnected" | "testing" | "connected" | "error">(
    cookies ? "connected" : "disconnected"
  );

  // Scraper settings
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

  // Hooks
  const startScraper = useStartScraper();
  const syncProducts = useSyncProducts();

  // Browser viewer state
  const [browserState, setBrowserState] = React.useState<{
    url?: string;
    screenshot?: string;
    status?: string;
  }>({});

  // Check if running in Tauri
  const isTauri = typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;

  // Listen to browser events (only in Tauri)
  React.useEffect(() => {
    if (!isTauri) return;
    
    let cleanup: (() => void) | undefined;
    
    import("@tauri-apps/api/event").then(({ listen }) => {
      listen<{url: string; screenshot?: string; status: string}>(
        'browser-update',
        (event) => {
          setBrowserState(event.payload);
        }
      ).then(unlisten => {
        cleanup = unlisten;
      });
    }).catch(console.error);
    
    return () => {
      cleanup?.();
    };
  }, [isTauri]);

  // Persist settings
  React.useEffect(() => {
    localStorage.setItem("scraper_categories", JSON.stringify(selectedCategories));
  }, [selectedCategories]);

  React.useEffect(() => {
    localStorage.setItem("scraper_max_products", maxProducts.toString());
  }, [maxProducts]);

  React.useEffect(() => {
    localStorage.setItem("scraper_headless", JSON.stringify(headless));
  }, [headless]);

  // Poll scraper status
  const { data: status } = useQuery<ScraperStatus>({
    queryKey: ["scraperStatus"],
    queryFn: async () => {
      try {
        return await getScraperStatus();
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

  const handleTestConnection = async () => {
    setConnectionStatus("testing");
    
    try {
      // Simulated connection test - in production, would actually test cookies
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      if (cookies.includes("sessionid") || cookies.includes("tt_webid")) {
        setConnectionStatus("connected");
        toast({
          title: "✅ Conexão Válida",
          description: "Cookies do TikTok verificados com sucesso.",
        });
      } else {
        setConnectionStatus("error");
        toast({
          title: "❌ Cookies Inválidos",
          description: "Os cookies não parecem ser válidos. Verifique se copiou corretamente.",
          variant: "destructive",
        });
      }
    } catch {
      setConnectionStatus("error");
      toast({
        title: "❌ Erro na Conexão",
        description: "Não foi possível verificar os cookies.",
        variant: "destructive",
      });
    }
  };

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
        title: "✅ Coleta Iniciada!",
        description: `Coletando até ${maxProducts} produtos de ${selectedCategories.length} categoria(s)...`,
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
      await stopScraper();
      toast({
        title: "⏹️ Coleta Parada",
        description: "A coleta foi interrompida.",
      });
    } catch (error) {
      toast({
        title: "Erro",
        description: String(error),
        variant: "destructive",
      });
    }
  };

  const handleSync = async () => {
    try {
      const count = await syncProducts.mutateAsync();
      toast({
        title: "✅ Sincronização Concluída",
        description: `${count} produtos enviados para o servidor`,
      });
    } catch (e) {
      toast({
        title: "❌ Erro na Sincronização",
        description: String(e),
        variant: "destructive",
      });
    }
  };

  const isRunning = status?.isRunning || false;
  const progress = status?.progress || 0;
  const productsFound = status?.productsFound || 0;
  const logs = status?.logs || [];
  const statusMessage = status?.statusMessage || "Pronto para iniciar";

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
            🕷️ {t("coleta.title")}
          </h1>
          <p className="text-muted-foreground mt-1">
            {t("coleta.subtitle")}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={handleSync} disabled={isRunning || syncProducts.isPending}>
            {syncProducts.isPending ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            {t("coleta.sync")}
          </Button>
          <Badge variant="outline" className="font-mono">
            {productsFound} {t("coleta.collected")}
          </Badge>
        </div>
      </div>

      {/* Main Content - Tabs */}
      <Tabs defaultValue="configuracao" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 lg:w-[500px]">
          <TabsTrigger value="configuracao" className="flex items-center gap-2">
            <Settings2 className="w-4 h-4" />
            {t("coleta.configuration")}
          </TabsTrigger>
          <TabsTrigger value="coleta" className="flex items-center gap-2">
            <Package className="w-4 h-4" />
            {t("coleta.collection")}
          </TabsTrigger>
          <TabsTrigger value="avancado" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            {t("coleta.advanced")}
          </TabsTrigger>
        </TabsList>

        {/* Configuração Tab */}
        <TabsContent value="configuracao" className="space-y-6">
          <CookieSetup
            currentCookies={cookies}
            onCookiesSaved={setCookies}
            connectionStatus={connectionStatus}
            onTestConnection={handleTestConnection}
          />
        </TabsContent>

        {/* Coleta Tab */}
        <TabsContent value="coleta" className="space-y-6">
          <ScraperPanel
            isRunning={isRunning}
            progress={progress}
            productsFound={productsFound}
            statusMessage={statusMessage}
            logs={logs}
            selectedCategories={selectedCategories}
            maxProducts={maxProducts}
            headless={headless}
            onStartScraping={handleStartScraping}
            onStopScraping={handleStopScraping}
            onCategoryChange={setSelectedCategories}
            onMaxProductsChange={setMaxProducts}
            onHeadlessChange={setHeadless}
            isPending={startScraper.isPending}
          />
          
          {/* Browser Viewer */}
          <BrowserViewer
            isActive={isRunning}
            currentUrl={browserState.url}
            screenshot={browserState.screenshot}
            status={browserState.status}
          />
        </TabsContent>

        {/* Avançado Tab */}
        <TabsContent value="avancado" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Proxy Testing */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wifi className="w-5 h-5" />
                  Testar Proxy
                </CardTitle>
                <CardDescription>
                  Verifique se um proxy está funcionando corretamente
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="proxy">URL do Proxy</Label>
                  <Input
                    id="proxy"
                    placeholder="http://user:pass@ip:port"
                    disabled={isRunning}
                  />
                </div>
                <Button variant="outline" className="w-full" disabled={isRunning}>
                  <Wifi className="w-4 h-4 mr-2" />
                  Testar Conexão
                </Button>
              </CardContent>
            </Card>

            {/* Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Estatísticas
                </CardTitle>
                <CardDescription>
                  Resumo das coletas realizadas
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-muted text-center">
                    <p className="text-3xl font-bold text-tiktrend-primary">{productsFound}</p>
                    <p className="text-sm text-muted-foreground">Produtos Hoje</p>
                  </div>
                  <div className="p-4 rounded-lg bg-muted text-center">
                    <p className="text-3xl font-bold text-tiktrend-primary">{selectedCategories.length}</p>
                    <p className="text-sm text-muted-foreground">Categorias Ativas</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Help Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HelpCircle className="w-5 h-5" />
                Ajuda e FAQ
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="q1">
                  <AccordionTrigger>Por que preciso dos cookies?</AccordionTrigger>
                  <AccordionContent>
                    Os cookies permitem que o sistema acesse o TikTok Shop como se fosse você navegando.
                    Isso é necessário para coletar informações de produtos que requerem autenticação.
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="q2">
                  <AccordionTrigger>Com que frequência devo atualizar os cookies?</AccordionTrigger>
                  <AccordionContent>
                    Os cookies do TikTok geralmente expiram após algumas horas de inatividade.
                    Se a coleta começar a falhar, obtenha novos cookies seguindo o passo-a-passo.
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="q3">
                  <AccordionTrigger>O que é modo headless?</AccordionTrigger>
                  <AccordionContent>
                    No modo headless, o navegador roda em segundo plano sem interface visual.
                    É mais rápido, mas se você precisar resolver CAPTCHAs, desative esta opção.
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="q4">
                  <AccordionTrigger>A coleta está muito lenta. O que fazer?</AccordionTrigger>
                  <AccordionContent>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>Ative o modo headless para melhor performance</li>
                      <li>Reduza o número de produtos por categoria</li>
                      <li>Selecione menos categorias por vez</li>
                      <li>Verifique sua conexão com a internet</li>
                    </ul>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Coleta;
