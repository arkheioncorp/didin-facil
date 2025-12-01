import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ShoppingCart, ExternalLink, Loader2 } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { Product } from "@/types";
import type { CRMStage } from "../types";

interface CRMModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product;
  isLoading: boolean;
  opportunityTitle: string;
  setOpportunityTitle: (title: string) => void;
  value: number;
  setValue: (value: number) => void;
  stage: CRMStage;
  setStage: (stage: CRMStage) => void;
  notes: string;
  setNotes: (notes: string) => void;
  onCreateOpportunity: () => Promise<void>;
  onNavigate: (path: string) => void;
}

export const CRMModal: React.FC<CRMModalProps> = ({
  open,
  onOpenChange,
  product,
  isLoading,
  opportunityTitle,
  setOpportunityTitle,
  value,
  setValue,
  stage,
  setStage,
  notes,
  setNotes,
  onCreateOpportunity,
  onNavigate,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" data-testid="crm-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShoppingCart className="h-5 w-5 text-orange-500" />
            Adicionar ao CRM
          </DialogTitle>
          <DialogDescription>
            Crie uma oportunidade para "{product.title}"
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Título da Oportunidade</Label>
            <input
              type="text"
              value={opportunityTitle}
              onChange={(e) => setOpportunityTitle(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Ex: Lead - Nome do Produto"
              data-testid="crm-title-input"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Valor</Label>
              <input
                type="number"
                value={value}
                onChange={(e) => setValue(Number(e.target.value))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="0.00"
                data-testid="crm-value-input"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Estágio</Label>
              <Select value={stage} onValueChange={(v) => setStage(v as CRMStage)}>
                <SelectTrigger data-testid="crm-stage-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="lead">Lead</SelectItem>
                  <SelectItem value="qualified">Qualificado</SelectItem>
                  <SelectItem value="proposal">Proposta</SelectItem>
                  <SelectItem value="negotiation">Negociação</SelectItem>
                  <SelectItem value="won">Ganho</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="space-y-2">
            <Label>Notas</Label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="min-h-[80px]"
              placeholder="Observações sobre esta oportunidade..."
              data-testid="crm-notes-input"
            />
          </div>

          {/* Product Info */}
          <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 border">
            <img 
              src={product.imageUrl || undefined} 
              alt={product.title}
              className="w-12 h-12 rounded object-cover"
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{product.title}</p>
              <p className="text-xs text-muted-foreground">{formatCurrency(product.price)}</p>
            </div>
          </div>
        </div>
        
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button 
            variant="outline" 
            onClick={() => onNavigate(`/crm/contacts?action=add&productId=${product.id}`)}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Abrir CRM
          </Button>
          <Button 
            onClick={onCreateOpportunity}
            disabled={isLoading || !opportunityTitle}
            className="bg-orange-600 hover:bg-orange-700"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Criando...
              </>
            ) : (
              <>
                <ShoppingCart className="h-4 w-4 mr-2" />
                Criar Oportunidade
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
