import * as React from "react";
import { useActionHistoryStore, formatActionTimestamp, getActionIcon } from "@/stores";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { Check, X, Trash2, History, TrendingUp } from "lucide-react";
import type { ActionHistoryEntry } from "./types";

// ============================================
// COMPONENT PROPS
// ============================================

interface ActionHistoryProps {
  productId?: string;
  maxHeight?: string;
  showStats?: boolean;
  showClearButton?: boolean;
  compact?: boolean;
}

// ============================================
// MAIN COMPONENT
// ============================================

export const ActionHistory: React.FC<ActionHistoryProps> = ({
  productId,
  maxHeight = "300px",
  showStats = true,
  showClearButton = false,
  compact = false,
}) => {
  const { 
    entries, 
    getHistoryByProduct, 
    getRecentHistory, 
    clearHistory, 
    clearProductHistory,
    getSuccessRate,
    getMostUsedActions,
  } = useActionHistoryStore();
  
  // Get filtered entries - entries in dep array forces recalculation when store updates
  const filteredEntries = React.useMemo(() => {
    return productId 
      ? getHistoryByProduct(productId) 
      : getRecentHistory(50);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId, entries.length, getHistoryByProduct, getRecentHistory]);
  
  // Get stats
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const successRate = React.useMemo(() => getSuccessRate(productId), [productId, entries.length, getSuccessRate]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const mostUsedActions = React.useMemo(() => getMostUsedActions(3), [entries.length, getMostUsedActions]);
  
  // Clear handler
  const handleClear = () => {
    if (productId) {
      clearProductHistory(productId);
    } else {
      clearHistory();
    }
  };
  
  if (filteredEntries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
        <History className="h-8 w-8 mb-2 opacity-50" />
        <p className="text-sm">Nenhuma ação registrada</p>
        {productId && (
          <p className="text-xs mt-1">Ações realizadas neste produto aparecerão aqui</p>
        )}
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {/* Stats Section */}
      {showStats && !compact && (
        <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border">
          <div className="flex items-center gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold">{filteredEntries.length}</p>
              <p className="text-xs text-muted-foreground">Ações</p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="text-center">
              <p className={cn(
                "text-2xl font-bold",
                successRate >= 80 ? "text-green-500" : 
                successRate >= 50 ? "text-yellow-500" : "text-red-500"
              )}>
                {successRate}%
              </p>
              <p className="text-xs text-muted-foreground">Sucesso</p>
            </div>
          </div>
          
          {mostUsedActions.length > 0 && (
            <div className="hidden md:flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <div className="flex gap-1">
                {mostUsedActions.map((action) => (
                  <Badge key={action.type} variant="outline" className="text-xs">
                    {getActionIcon(action.type)} {action.count}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Clear Button */}
      {showClearButton && filteredEntries.length > 0 && (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Limpar histórico
          </Button>
        </div>
      )}
      
      {/* History List */}
      <ScrollArea style={{ maxHeight }}>
        <div className="space-y-2 pr-4">
          {filteredEntries.map((entry) => (
            <ActionHistoryItem 
              key={entry.id} 
              entry={entry} 
              compact={compact}
              showProduct={!productId}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};

// ============================================
// HISTORY ITEM COMPONENT
// ============================================

interface ActionHistoryItemProps {
  entry: ActionHistoryEntry;
  compact?: boolean;
  showProduct?: boolean;
}

const ActionHistoryItem: React.FC<ActionHistoryItemProps> = ({
  entry,
  compact = false,
  showProduct = false,
}) => {
  if (compact) {
    return (
      <div className="flex items-center justify-between py-1 text-sm">
        <div className="flex items-center gap-2">
          <span>{getActionIcon(entry.actionType)}</span>
          <span className="truncate max-w-[150px]">{entry.actionLabel}</span>
        </div>
        <span className="text-xs text-muted-foreground">
          {formatActionTimestamp(entry.timestamp)}
        </span>
      </div>
    );
  }
  
  return (
    <TooltipProvider>
      <div className={cn(
        "flex items-start gap-3 p-3 rounded-lg border transition-colors",
        entry.success 
          ? "bg-background hover:bg-muted/50" 
          : "bg-destructive/5 border-destructive/20 hover:bg-destructive/10"
      )}>
        {/* Icon */}
        <div className={cn(
          "flex items-center justify-center h-8 w-8 rounded-full text-lg",
          entry.success ? "bg-primary/10" : "bg-destructive/10"
        )}>
          {getActionIcon(entry.actionType)}
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="font-medium text-sm">{entry.actionLabel}</p>
            {entry.success ? (
              <Check className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <Tooltip>
                <TooltipTrigger>
                  <X className="h-3.5 w-3.5 text-destructive" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">{entry.errorMessage || "Erro desconhecido"}</p>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
          
          {showProduct && (
            <p className="text-xs text-muted-foreground truncate mt-0.5">
              {entry.productTitle}
            </p>
          )}
          
          <p className="text-xs text-muted-foreground mt-1">
            {formatActionTimestamp(entry.timestamp)}
          </p>
        </div>
        
        {/* Metadata badge */}
        {entry.metadata && Object.keys(entry.metadata).length > 0 && (
          <Tooltip>
            <TooltipTrigger>
              <Badge variant="outline" className="text-xs">
                +{Object.keys(entry.metadata).length}
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <div className="text-xs space-y-1">
                {Object.entries(entry.metadata).slice(0, 5).map(([key, value]) => (
                  <p key={key}>
                    <span className="font-medium">{key}:</span>{" "}
                    {String(value).substring(0, 50)}
                  </p>
                ))}
              </div>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </TooltipProvider>
  );
};

export default ActionHistory;
