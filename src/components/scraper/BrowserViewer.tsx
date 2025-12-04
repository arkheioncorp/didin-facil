import React, { useEffect, useCallback } from "react";
import { Monitor, Maximize2, Minimize2, RefreshCw, Eye, EyeOff, Loader2, Package } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface BrowserViewerProps {
    isActive: boolean;
    currentUrl?: string;
    screenshot?: string;
    status?: string;
    productsFound?: number;
    progress?: number;
    logs?: string[];
}

export function BrowserViewer({ 
    isActive, 
    currentUrl, 
    screenshot, 
    status,
    productsFound = 0,
    progress = 0,
    logs = []
}: BrowserViewerProps) {
    const [isExpanded, setIsExpanded] = React.useState(false);
    const [isVisible, setIsVisible] = React.useState(true);
    const [animationFrame, setAnimationFrame] = React.useState(0);
    const logsEndRef = React.useRef<HTMLDivElement>(null);

    // Animar o frame quando ativo
    useEffect(() => {
        if (!isActive) return;
        
        const interval = setInterval(() => {
            setAnimationFrame(prev => (prev + 1) % 4);
        }, 500);
        
        return () => clearInterval(interval);
    }, [isActive]);

    // Auto-scroll nos logs
    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [logs]);

    const getStatusIcon = useCallback(() => {
        if (!isActive) return <Monitor className="h-5 w-5 text-muted-foreground" />;
        
        switch(animationFrame) {
            case 0: return <Loader2 className="h-5 w-5 text-green-500 animate-spin" />;
            case 1: return <Package className="h-5 w-5 text-blue-500" />;
            case 2: return <RefreshCw className="h-5 w-5 text-yellow-500" />;
            default: return <Loader2 className="h-5 w-5 text-green-500 animate-spin" />;
        }
    }, [isActive, animationFrame]);

    const getStatusColor = () => {
        if (!isActive) return "border-border";
        return "border-green-500 shadow-green-500/20";
    };

    if (!isVisible) {
        return (
            <Button
                variant="outline"
                size="sm"
                onClick={() => setIsVisible(true)}
                className="fixed bottom-4 right-4 z-50 shadow-lg bg-background"
            >
                <Eye className="h-4 w-4 mr-2" />
                Mostrar Navegador
            </Button>
        );
    }

    return (
        <Card
            className={cn(
                "fixed z-50 transition-all duration-300 shadow-2xl border-2 bg-background/95 backdrop-blur-sm",
                isExpanded
                    ? "inset-4 md:inset-8"
                    : "bottom-4 right-4 w-80 md:w-96",
                getStatusColor()
            )}
        >
            <CardHeader className="pb-2 px-3 pt-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        {getStatusIcon()}
                        <CardTitle className="text-sm font-medium">Navegador ao Vivo</CardTitle>
                        {isActive && (
                            <Badge variant="outline" className="bg-green-500/10 text-green-600 text-xs px-1.5 py-0.5">
                                <span className="h-1.5 w-1.5 bg-green-500 rounded-full mr-1 animate-pulse" />
                                Ativo
                            </Badge>
                        )}
                    </div>
                    <div className="flex items-center gap-1">
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7"
                            onClick={() => setIsExpanded(!isExpanded)}
                        >
                            {isExpanded ? (
                                <Minimize2 className="h-3.5 w-3.5" />
                            ) : (
                                <Maximize2 className="h-3.5 w-3.5" />
                            )}
                        </Button>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7"
                            onClick={() => setIsVisible(false)}
                        >
                            <EyeOff className="h-3.5 w-3.5" />
                        </Button>
                    </div>
                </div>

                {/* Status Info */}
                {isActive && (
                    <div className="mt-2 space-y-2">
                        {/* Progress Bar */}
                        <div className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-muted-foreground">Progresso</span>
                                <span className="font-medium">{Math.round(progress)}%</span>
                            </div>
                            <Progress value={progress} className="h-1.5" />
                        </div>

                        {/* Stats Row */}
                        <div className="flex items-center justify-between text-xs">
                            <div className="flex items-center gap-1 text-muted-foreground">
                                <Package className="h-3 w-3" />
                                <span>{productsFound} produtos</span>
                            </div>
                            {status && (
                                <span className="text-primary font-medium truncate max-w-[150px]">
                                    {status}
                                </span>
                            )}
                        </div>
                    </div>
                )}

                {currentUrl && (
                    <div className="text-xs text-muted-foreground truncate mt-1 font-mono">
                        {currentUrl}
                    </div>
                )}
            </CardHeader>

            <CardContent className={cn("p-0", isExpanded ? "h-[calc(100%-120px)]" : "h-40")}>
                <div className="relative w-full h-full bg-black/5 dark:bg-black/30 overflow-hidden">
                    {screenshot ? (
                        <img
                            src={screenshot}
                            alt="Browser screenshot"
                            className="w-full h-full object-contain"
                        />
                    ) : isActive ? (
                        // Animação de coleta ativa
                        <div className="flex flex-col items-center justify-center h-full p-4 space-y-3">
                            <div className="relative">
                                <div className="absolute inset-0 bg-gradient-to-r from-tiktrend-primary/20 to-tiktrend-secondary/20 rounded-full blur-xl animate-pulse" />
                                <div className="relative w-16 h-16 rounded-full bg-gradient-to-br from-tiktrend-primary to-tiktrend-secondary flex items-center justify-center">
                                    <Loader2 className="h-8 w-8 text-white animate-spin" />
                                </div>
                            </div>
                            <div className="text-center space-y-1">
                                <p className="text-sm font-medium text-foreground">Coletando dados...</p>
                                <p className="text-xs text-muted-foreground">
                                    Navegando pelo TikTok Shop
                                </p>
                            </div>
                            
                            {/* Mini Log Viewer */}
                            {logs.length > 0 && isExpanded && (
                                <div className="w-full mt-2 bg-black/80 rounded-md p-2 font-mono text-xs max-h-24 overflow-y-auto">
                                    {logs.slice(-5).map((log, i) => (
                                        <div key={i} className="text-green-400/90 truncate">
                                            {log}
                                        </div>
                                    ))}
                                    <div ref={logsEndRef} />
                                </div>
                            )}
                        </div>
                    ) : (
                        // Estado inicial - aguardando
                        <div className="flex flex-col items-center justify-center h-full text-center space-y-3 p-4">
                            <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                                <Monitor className="h-6 w-6 text-muted-foreground" />
                            </div>
                            <div className="space-y-1">
                                <p className="text-sm text-muted-foreground">
                                    Aguardando scraper iniciar...
                                </p>
                                <p className="text-xs text-muted-foreground/70">
                                    Configure e inicie a coleta
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Browser Chrome Overlay - só mostra quando ativo */}
                    {isActive && (
                        <div className="absolute bottom-0 left-0 right-0">
                            <div className="bg-black/80 backdrop-blur-sm px-3 py-2 text-white text-xs">
                                <div className="flex items-center gap-2">
                                    <div className="flex gap-1">
                                        <div className="h-2 w-2 bg-red-500 rounded-full" />
                                        <div className="h-2 w-2 bg-yellow-500 rounded-full" />
                                        <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                                    </div>
                                    <span className="text-white/70 truncate flex-1">
                                        {status || "TikTok Shop - Buscando produtos..."}
                                    </span>
                                    <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 border-green-500/50 text-green-400">
                                        {productsFound} 📦
                                    </Badge>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
