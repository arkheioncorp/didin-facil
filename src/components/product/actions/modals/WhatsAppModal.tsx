import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { MessageCircle, ExternalLink, Loader2, Send } from "lucide-react";
import type { Product } from "@/types";

interface WhatsAppModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product;
  isLoading: boolean;
  phoneNumber: string;
  setPhoneNumber: (number: string) => void;
  message: string;
  setMessage: (message: string) => void;
  onSend: () => Promise<void>;
  onNavigate: (path: string) => void;
}

export const WhatsAppModal: React.FC<WhatsAppModalProps> = ({
  open,
  onOpenChange,
  product,
  isLoading,
  phoneNumber,
  setPhoneNumber,
  message,
  setMessage,
  onSend,
  onNavigate,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" data-testid="whatsapp-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5 text-green-500" />
            Enviar via WhatsApp
          </DialogTitle>
          <DialogDescription>
            Compartilhe este produto pelo WhatsApp
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Número do WhatsApp</Label>
            <input
              type="tel"
              placeholder="+55 11 99999-9999"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              data-testid="whatsapp-number-input"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>
          
          <div className="space-y-2">
            <Label>Mensagem</Label>
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="min-h-[120px]"
              placeholder="Digite a mensagem..."
              data-testid="whatsapp-message-input"
            />
          </div>
        </div>
        
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button 
            variant="outline" 
            onClick={() => onNavigate(`/whatsapp?action=send&productId=${product.id}`)}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Abrir Página
          </Button>
          <Button 
            onClick={onSend}
            disabled={isLoading}
            className="bg-green-600 hover:bg-green-700"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Enviando...
              </>
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                Enviar
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
