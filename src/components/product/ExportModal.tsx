/**
 * ExportModal Component
 * 
 * Modal for exporting products to CSV or Excel.
 * 
 * @performance
 * - Memoized to prevent unnecessary re-renders
 * - Shows loading state during export
 */

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

// ============================================
// TYPES
// ============================================

export type ExportFormat = "csv" | "xlsx";

export interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExport: (format: ExportFormat) => Promise<void>;
  selectedCount: number;
  totalCount: number;
  isExporting: boolean;
}

// ============================================
// COMPONENT
// ============================================

export const ExportModal: React.FC<ExportModalProps> = React.memo(({
  isOpen,
  onClose,
  onExport,
  selectedCount,
  totalCount,
  isExporting,
}) => {
  if (!isOpen) return null;

  const handleExport = async (format: ExportFormat) => {
    await onExport(format);
  };

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/50 z-50"
        onClick={onClose}
      />
      <div 
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-2xl shadow-2xl z-50 p-6 w-full max-w-md"
        data-testid="export-modal"
      >
        <h2 className="text-xl font-bold mb-4">Exportar Produtos</h2>
        <p className="text-muted-foreground mb-6">
          {selectedCount > 0 
            ? `Exportar ${selectedCount} produto(s) selecionado(s)`
            : `Exportar todos os ${totalCount} produtos`
          }
        </p>
        <div className="space-y-3">
          <Button 
            variant="outline" 
            className="w-full justify-start gap-3"
            onClick={() => handleExport("csv")}
            disabled={isExporting}
          >
            <Download size={18} />
            {isExporting ? "Exportando..." : "Exportar como CSV"}
          </Button>
          <Button 
            variant="outline" 
            className="w-full justify-start gap-3"
            onClick={() => handleExport("xlsx")}
            disabled={isExporting}
          >
            <Download size={18} />
            {isExporting ? "Exportando..." : "Exportar como Excel"}
          </Button>
        </div>
        <Button 
          variant="ghost" 
          className="w-full mt-4"
          onClick={onClose}
          disabled={isExporting}
        >
          Cancelar
        </Button>
      </div>
    </>
  );
});

ExportModal.displayName = "ExportModal";
