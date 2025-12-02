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
import { Sparkles, ExternalLink, Loader2, Copy } from "lucide-react";
import type { Product } from "@/types";
import type { CopyType, CopyTone } from "../types";

interface CopyAIModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product;
  isLoading: boolean;
  copyType: CopyType;
  setCopyType: (type: CopyType) => void;
  copyTone: CopyTone;
  setCopyTone: (tone: CopyTone) => void;
  generatedCopy: string | null;
  onGenerate: () => Promise<void>;
  onCopyText: () => Promise<void>;
  onNavigate: (path: string) => void;
}

export const CopyAIModal: React.FC<CopyAIModalProps> = ({
  open,
  onOpenChange,
  product,
  isLoading,
  copyType,
  setCopyType,
  copyTone,
  setCopyTone,
  generatedCopy,
  onGenerate,
  onCopyText,
  onNavigate,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" data-testid="copy-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-tiktrend-primary" />
            Gerar Copy com IA
          </DialogTitle>
          <DialogDescription>
            Gere textos persuasivos para "{product.title}"
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Tipo de Copy</Label>
              <Select value={copyType} onValueChange={(v) => setCopyType(v as CopyType)}>
                <SelectTrigger data-testid="copy-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ad">Anúncio</SelectItem>
                  <SelectItem value="description">Descrição</SelectItem>
                  <SelectItem value="headline">Headline</SelectItem>
                  <SelectItem value="cta">Call to Action</SelectItem>
                  <SelectItem value="story">Story/Reels</SelectItem>
                  <SelectItem value="whatsapp">WhatsApp</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Tom</Label>
              <Select value={copyTone} onValueChange={(v) => setCopyTone(v as CopyTone)}>
                <SelectTrigger data-testid="copy-tone-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="professional">Profissional</SelectItem>
                  <SelectItem value="casual">Casual</SelectItem>
                  <SelectItem value="urgent">Urgente</SelectItem>
                  <SelectItem value="friendly">Amigável</SelectItem>
                  <SelectItem value="luxury">Luxo</SelectItem>
                  <SelectItem value="emotional">Emocional</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {generatedCopy && (
            <div className="space-y-2">
              <Label>Copy Gerada</Label>
              <div className="relative">
                <Textarea
                  value={generatedCopy}
                  readOnly
                  className="min-h-[150px] pr-10"
                />
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute top-2 right-2"
                  onClick={onCopyText}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
        
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button 
            variant="outline" 
            onClick={() => onNavigate(`/copy?productId=${product.id}&title=${encodeURIComponent(product.title)}&price=${product.price}`)}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Abrir Página
          </Button>
          <Button 
            onClick={onGenerate}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Gerando...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Gerar Copy
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
