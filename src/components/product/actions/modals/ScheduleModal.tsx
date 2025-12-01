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
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Calendar, ExternalLink, Loader2, Instagram, Youtube, MessageCircle } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { Product } from "@/types";
import type { SchedulePlatform } from "../types";

// TikTok icon
const TikTokIcon = () => (
  <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current">
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
  </svg>
);

interface ScheduleModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product;
  isLoading: boolean;
  platform: SchedulePlatform;
  setPlatform: (platform: SchedulePlatform) => void;
  scheduleDate: string;
  setScheduleDate: (date: string) => void;
  onSchedule: () => Promise<void>;
  onNavigate: (path: string) => void;
}

export const ScheduleModal: React.FC<ScheduleModalProps> = ({
  open,
  onOpenChange,
  product,
  isLoading,
  platform,
  setPlatform,
  scheduleDate,
  setScheduleDate,
  onSchedule,
  onNavigate,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" data-testid="schedule-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-blue-500" />
            Agendar Publicação
          </DialogTitle>
          <DialogDescription>
            Programe a publicação deste produto
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Plataforma</Label>
            <Select value={platform} onValueChange={(v) => setPlatform(v as SchedulePlatform)}>
              <SelectTrigger data-testid="platform-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="instagram">
                  <span className="flex items-center gap-2">
                    <Instagram className="h-4 w-4" /> Instagram
                  </span>
                </SelectItem>
                <SelectItem value="tiktok">
                  <span className="flex items-center gap-2">
                    <TikTokIcon /> TikTok
                  </span>
                </SelectItem>
                <SelectItem value="youtube">
                  <span className="flex items-center gap-2">
                    <Youtube className="h-4 w-4" /> YouTube
                  </span>
                </SelectItem>
                <SelectItem value="whatsapp">
                  <span className="flex items-center gap-2">
                    <MessageCircle className="h-4 w-4" /> WhatsApp Status
                  </span>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label>Data e Hora</Label>
            <input
              type="datetime-local"
              value={scheduleDate}
              onChange={(e) => setScheduleDate(e.target.value)}
              min={new Date().toISOString().slice(0, 16)}
              data-testid="schedule-datetime-input"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>

          {/* Preview */}
          <div className="p-3 rounded-lg bg-muted/50 border">
            <p className="text-sm font-medium mb-1">Preview do Post:</p>
            <p className="text-sm text-muted-foreground">
              🛍️ {product.title}<br/>
              💰 {formatCurrency(product.price)}
            </p>
          </div>
        </div>
        
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button 
            variant="outline" 
            onClick={() => onNavigate(`/automation/scheduler?productId=${product.id}&platform=${platform}`)}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Configurar Avançado
          </Button>
          <Button 
            onClick={onSchedule}
            disabled={isLoading || !scheduleDate}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Agendando...
              </>
            ) : (
              <>
                <Calendar className="h-4 w-4 mr-2" />
                Agendar
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
