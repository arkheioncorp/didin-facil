import React from "react";
import { Monitor, Maximize2, Minimize2, RefreshCw, Eye, EyeOff } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface BrowserViewerProps {
    isActive: boolean;
    currentUrl?: string;
    screenshot?: string;
    status?: string;
}

export function BrowserViewer({ isActive, currentUrl, screenshot, status }: BrowserViewerProps) {
    const [isExpanded, setIsExpanded] = React.useState(false);
    const [isVisible, setIsVisible] = React.useState(true);

    if (!isVisible) {
        return (
            <Button
                variant="outline"
                size="sm"
                onClick={() => setIsVisible(true)}
                className="fixed bottom-4 right-4 z-50 shadow-lg"
            >
                <Eye className="h-4 w-4 mr-2" />
                Mostrar Navegador
            </Button>
        );
    }

    return (
        <Card
            className={cn(
                "fixed z-50 transition-all duration-300 shadow-2xl border-2",
                isExpanded
                    ? "inset-4"
                    : "bottom-4 right-4 w-96 h-64",
                isActive ? "border-green-500" : "border-border"
            )}
        >
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Monitor className="h-5 w-5 text-primary" />
                        <CardTitle className="text-base">Navegador ao Vivo</CardTitle>
                        {isActive && (
                            <Badge variant="outline" className="bg-green-500/10 text-green-600 animate-pulse">
                                <span className="h-2 w-2 bg-green-500 rounded-full mr-1.5 animate-ping" />
                                Ativo
                            </Badge>
                        )}
                    </div>
                    <div className="flex items-center gap-1">
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => setIsExpanded(!isExpanded)}
                        >
                            {isExpanded ? (
                                <Minimize2 className="h-4 w-4" />
                            ) : (
                                <Maximize2 className="h-4 w-4" />
                            )}
                        </Button>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => setIsVisible(false)}
                        >
                            <EyeOff className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
                {currentUrl && (
                    <div className="text-xs text-muted-foreground truncate mt-1">
                        {currentUrl}
                    </div>
                )}
                {status && (
                    <div className="text-xs text-primary font-medium mt-1">
                        {status}
                    </div>
                )}
            </CardHeader>
            <CardContent className="p-0">
                <div className="relative w-full h-full bg-black/5 dark:bg-black/20 rounded-b-lg overflow-hidden">
                    {screenshot ? (
                        <img
                            src={screenshot}
                            alt="Browser screenshot"
                            className="w-full h-full object-contain"
                        />
                    ) : (
                        <div className="flex items-center justify-center h-full text-muted-foreground">
                            {isActive ? (
                                <div className="text-center space-y-2">
                                    <RefreshCw className="h-8 w-8 mx-auto animate-spin text-primary" />
                                    <p className="text-sm">Carregando visualização...</p>
                                </div>
                            ) : (
                                <div className="text-center space-y-2">
                                    <Monitor className="h-12 w-12 mx-auto opacity-50" />
                                    <p className="text-sm">Aguardando scraper iniciar...</p>
                                </div>
                            )}
                        </div>
                    )}
                    {isActive && (
                        <div className="absolute bottom-2 left-2 right-2">
                            <div className="bg-black/80 backdrop-blur-sm rounded-md px-3 py-2 text-white text-xs">
                                <div className="flex items-center gap-2">
                                    <div className="flex gap-1.5">
                                        <div className="h-2 w-2 bg-red-500 rounded-full" />
                                        <div className="h-2 w-2 bg-yellow-500 rounded-full" />
                                        <div className="h-2 w-2 bg-green-500 rounded-full" />
                                    </div>
                                    <span className="text-gray-300 truncate flex-1">
                                        TikTok Shop - Buscando produtos...
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
