import * as React from "react";
import { cn } from "@/lib/utils";
import { 
  CheckSquare, 
  Square, 
  X, 
  Play, 
  Pause,
  CheckCircle2,
  XCircle,
  Loader2,
  Sparkles,
  MessageCircle,
  Instagram,
  Youtube,
  Copy,
  Download,
  MoreHorizontal,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useProductSelection, useBulkJob } from "@/stores/bulkActionsStore";
import type { Product } from "@/types";
import type { ActionId } from "@/components/product/actions/types";

// TikTok Icon
const TikTokIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" className={cn("fill-current", className)}>
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
  </svg>
);

// ============================================
// BULK ACTIONS AVAILABLE
// ============================================

interface BulkAction {
  id: ActionId;
  label: string;
  description: string;
  icon: React.ReactNode;
  color?: string;
}

const BULK_ACTIONS: BulkAction[] = [
  {
    id: "generate-copy",
    label: "Gerar Copies",
    description: "Gerar copy com IA para todos os produtos",
    icon: <Sparkles className="h-4 w-4" />,
    color: "text-purple-500",
  },
  {
    id: "whatsapp",
    label: "WhatsApp",
    description: "Enviar para WhatsApp",
    icon: <MessageCircle className="h-4 w-4" />,
    color: "text-green-500",
  },
  {
    id: "instagram",
    label: "Instagram",
    description: "Preparar para Instagram",
    icon: <Instagram className="h-4 w-4" />,
    color: "text-pink-500",
  },
  {
    id: "tiktok",
    label: "TikTok",
    description: "Preparar para TikTok",
    icon: <TikTokIcon className="h-4 w-4" />,
  },
  {
    id: "youtube",
    label: "YouTube",
    description: "Preparar para YouTube",
    icon: <Youtube className="h-4 w-4" />,
    color: "text-red-500",
  },
  {
    id: "copy-info",
    label: "Copiar Info",
    description: "Copiar informações dos produtos",
    icon: <Copy className="h-4 w-4" />,
  },
  {
    id: "export",
    label: "Exportar",
    description: "Exportar dados dos produtos",
    icon: <Download className="h-4 w-4" />,
  },
];

// ============================================
// SELECTION BAR COMPONENT
// ============================================

interface BulkSelectionBarProps {
  totalProducts: number;
  onBulkAction: (actionId: ActionId) => void;
  className?: string;
}

export const BulkSelectionBar: React.FC<BulkSelectionBarProps> = ({
  totalProducts,
  onBulkAction,
  className,
}) => {
  const { selectedProducts, selectAll, deselectAll } = useProductSelection();
  const selectedCount = selectedProducts.length;

  if (selectedCount === 0) return null;

  return (
    <div className={cn(
      "fixed bottom-4 left-1/2 -translate-x-1/2 z-50",
      "flex items-center gap-3 p-3 pr-4",
      "bg-background/95 backdrop-blur-sm border rounded-full shadow-lg",
      className
    )}>
      {/* Selection count */}
      <div className="flex items-center gap-2 px-3 py-1 bg-tiktrend-primary/10 rounded-full">
        <CheckSquare className="h-4 w-4 text-tiktrend-primary" />
        <span className="text-sm font-medium">
          {selectedCount} selecionado{selectedCount > 1 ? "s" : ""}
        </span>
      </div>

      {/* Quick actions */}
      <div className="flex items-center gap-1">
        {BULK_ACTIONS.slice(0, 4).map((action) => (
          <Button
            key={action.id}
            variant="ghost"
            size="sm"
            onClick={() => onBulkAction(action.id)}
            className={cn("h-8", action.color)}
          >
            {action.icon}
            <span className="ml-1 hidden sm:inline">{action.label}</span>
          </Button>
        ))}

        {/* More actions dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {BULK_ACTIONS.slice(4).map((action) => (
              <DropdownMenuItem
                key={action.id}
                onClick={() => onBulkAction(action.id)}
              >
                <span className={cn("mr-2", action.color)}>{action.icon}</span>
                {action.label}
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => selectAll([])}>
              <CheckSquare className="h-4 w-4 mr-2" />
              Selecionar Todos ({totalProducts})
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Clear selection */}
      <Button
        variant="ghost"
        size="icon"
        onClick={deselectAll}
        className="h-8 w-8 rounded-full hover:bg-destructive/10 hover:text-destructive"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
};

// ============================================
// PRODUCT CHECKBOX COMPONENT
// ============================================

interface ProductCheckboxProps {
  product: Product;
  className?: string;
}

export const ProductCheckbox: React.FC<ProductCheckboxProps> = ({
  product,
  className,
}) => {
  const { toggleProduct, isSelected } = useProductSelection();
  const selected = isSelected(product.id);

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        toggleProduct(product);
      }}
      className={cn(
        "p-1 rounded transition-colors",
        selected 
          ? "text-tiktrend-primary" 
          : "text-muted-foreground hover:text-foreground",
        className
      )}
    >
      {selected ? (
        <CheckSquare className="h-5 w-5" />
      ) : (
        <Square className="h-5 w-5" />
      )}
    </button>
  );
};

// ============================================
// BULK ACTION PROGRESS DIALOG
// ============================================

interface BulkActionProgressDialogProps {
  jobId: string;
  open: boolean;
  onClose: () => void;
}

export const BulkActionProgressDialog: React.FC<BulkActionProgressDialogProps> = ({
  jobId,
  open,
  onClose,
}) => {
  const { job, cancel, clear, successCount, failureCount } = useBulkJob(jobId);

  if (!job) return null;

  const actionInfo = BULK_ACTIONS.find((a) => a.id === job.actionId);
  const isRunning = job.status === "running";
  const isCompleted = job.status === "completed" || job.status === "cancelled";

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {actionInfo?.icon}
            {actionInfo?.label || "Ação em Lote"}
          </DialogTitle>
          <DialogDescription>
            {isRunning && "Executando ação em múltiplos produtos..."}
            {job.status === "completed" && "Ação concluída!"}
            {job.status === "cancelled" && "Ação cancelada"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Progress */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Progresso</span>
              <span className="font-medium">{job.progress}%</span>
            </div>
            <Progress value={job.progress} className="h-2" />
            <p className="text-xs text-muted-foreground text-center">
              {job.results.length} de {job.products.length} produtos
            </p>
          </div>

          {/* Status badges */}
          <div className="flex items-center justify-center gap-4">
            <div className="flex items-center gap-1 text-green-500">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-sm font-medium">{successCount} sucesso</span>
            </div>
            {failureCount > 0 && (
              <div className="flex items-center gap-1 text-red-500">
                <XCircle className="h-4 w-4" />
                <span className="text-sm font-medium">{failureCount} falha{failureCount > 1 ? "s" : ""}</span>
              </div>
            )}
          </div>

          {/* Results list */}
          {job.results.length > 0 && (
            <ScrollArea className="h-[200px] rounded-md border p-2">
              <div className="space-y-2">
                {job.results.map((result, index) => (
                  <div
                    key={`${result.productId}-${index}`}
                    className={cn(
                      "flex items-center gap-2 p-2 rounded text-sm",
                      result.success ? "bg-green-500/10" : "bg-red-500/10"
                    )}
                  >
                    {result.success ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
                    )}
                    <span className="truncate flex-1">{result.productTitle}</span>
                    {result.error && (
                      <span className="text-xs text-red-500 truncate max-w-[100px]">
                        {result.error}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}

          {/* Running indicator */}
          {isRunning && (
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Processando...</span>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          {isRunning && (
            <Button variant="destructive" onClick={cancel}>
              <Pause className="h-4 w-4 mr-2" />
              Cancelar
            </Button>
          )}
          {isCompleted && (
            <>
              <Button variant="outline" onClick={() => { clear(); onClose(); }}>
                Fechar
              </Button>
              {failureCount > 0 && (
                <Button variant="default">
                  <Play className="h-4 w-4 mr-2" />
                  Tentar Novamente ({failureCount})
                </Button>
              )}
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Re-export the hook from separate file for Fast Refresh compatibility  
// Note: useBulkActions is exported from ./useBulkActions.ts

export default {
  BulkSelectionBar,
  ProductCheckbox,
  BulkActionProgressDialog,
};
