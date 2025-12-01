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
import { Bot, ExternalLink, Loader2 } from "lucide-react";
import type { Product } from "@/types";
import type { BotTargetAudience } from "../types";

interface SellerBotModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product;
  isLoading: boolean;
  campaignName: string;
  setCampaignName: (name: string) => void;
  message: string;
  setMessage: (message: string) => void;
  targetAudience: BotTargetAudience;
  setTargetAudience: (audience: BotTargetAudience) => void;
  scheduleEnabled: boolean;
  setScheduleEnabled: (enabled: boolean) => void;
  onCreateCampaign: () => Promise<void>;
  onNavigate: (path: string) => void;
}

export const SellerBotModal: React.FC<SellerBotModalProps> = ({
  open,
  onOpenChange,
  product,
  isLoading,
  campaignName,
  setCampaignName,
  message,
  setMessage,
  targetAudience,
  setTargetAudience,
  scheduleEnabled,
  setScheduleEnabled,
  onCreateCampaign,
  onNavigate,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" data-testid="seller-bot-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-purple-500" />
            Seller Bot - Campanha
          </DialogTitle>
          <DialogDescription>
            Configure uma campanha automática para "{product.title}"
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Nome da Campanha</Label>
            <input
              type="text"
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Nome da campanha..."
              data-testid="bot-campaign-name-input"
            />
          </div>
          
          <div className="space-y-2">
            <Label>Mensagem</Label>
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="min-h-[120px]"
              placeholder="Mensagem que será enviada..."
              data-testid="bot-message-input"
            />
          </div>

          <div className="space-y-2">
            <Label>Público-alvo</Label>
            <Select value={targetAudience} onValueChange={(v) => setTargetAudience(v as BotTargetAudience)}>
              <SelectTrigger data-testid="bot-audience-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os Contatos</SelectItem>
                <SelectItem value="leads">Leads Novos</SelectItem>
                <SelectItem value="customers">Clientes</SelectItem>
                <SelectItem value="inactive">Inativos (30+ dias)</SelectItem>
                <SelectItem value="engaged">Engajados</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border">
            <div>
              <p className="text-sm font-medium">Agendamento Automático</p>
              <p className="text-xs text-muted-foreground">Enviar em horários otimizados</p>
            </div>
            <Button
              variant={scheduleEnabled ? "default" : "outline"}
              size="sm"
              onClick={() => setScheduleEnabled(!scheduleEnabled)}
            >
              {scheduleEnabled ? "Ativado" : "Desativado"}
            </Button>
          </div>

          {/* Stats Preview */}
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20">
              <p className="text-lg font-bold text-purple-500">~500</p>
              <p className="text-[10px] text-muted-foreground">Alcance</p>
            </div>
            <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <p className="text-lg font-bold text-blue-500">~15%</p>
              <p className="text-[10px] text-muted-foreground">Taxa Abertura</p>
            </div>
            <div className="p-2 rounded-lg bg-green-500/10 border border-green-500/20">
              <p className="text-lg font-bold text-green-500">~3%</p>
              <p className="text-[10px] text-muted-foreground">Conversão</p>
            </div>
          </div>
        </div>
        
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button 
            variant="outline" 
            onClick={() => onNavigate(`/seller-bot?productId=${product.id}`)}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Configurar Avançado
          </Button>
          <Button 
            onClick={onCreateCampaign}
            disabled={isLoading || !campaignName}
            className="bg-purple-600 hover:bg-purple-700"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Criando...
              </>
            ) : (
              <>
                <Bot className="h-4 w-4 mr-2" />
                Criar Campanha
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
