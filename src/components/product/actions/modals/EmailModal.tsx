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
import { Mail, ExternalLink, Loader2 } from "lucide-react";
import type { Product } from "@/types";
import type { EmailTemplate, EmailAudience } from "../types";

interface EmailModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product;
  isLoading: boolean;
  subject: string;
  setSubject: (subject: string) => void;
  template: EmailTemplate;
  setTemplate: (template: EmailTemplate) => void;
  content: string;
  setContent: (content: string) => void;
  audience: EmailAudience;
  setAudience: (audience: EmailAudience) => void;
  onCreateCampaign: () => Promise<void>;
  onNavigate: (path: string) => void;
}

export const EmailModal: React.FC<EmailModalProps> = ({
  open,
  onOpenChange,
  product,
  isLoading,
  subject,
  setSubject,
  template,
  setTemplate,
  content,
  setContent,
  audience,
  setAudience,
  onCreateCampaign,
  onNavigate,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" data-testid="email-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-sky-500" />
            Email Marketing
          </DialogTitle>
          <DialogDescription>
            Crie uma campanha de email para "{product.title}"
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Assunto do Email</Label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Assunto do email..."
              data-testid="email-subject-input"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Template</Label>
              <Select value={template} onValueChange={(v) => setTemplate(v as EmailTemplate)}>
                <SelectTrigger data-testid="email-template-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="product_launch">Lançamento</SelectItem>
                  <SelectItem value="promotion">Promoção</SelectItem>
                  <SelectItem value="newsletter">Newsletter</SelectItem>
                  <SelectItem value="follow_up">Follow-up</SelectItem>
                  <SelectItem value="custom">Personalizado</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Audiência</Label>
              <Select value={audience} onValueChange={(v) => setAudience(v as EmailAudience)}>
                <SelectTrigger data-testid="email-audience-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="subscribers">Inscritos</SelectItem>
                  <SelectItem value="customers">Clientes</SelectItem>
                  <SelectItem value="leads">Leads</SelectItem>
                  <SelectItem value="vip">VIP</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="space-y-2">
            <Label>Conteúdo</Label>
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="min-h-[120px]"
              placeholder="Conteúdo do email..."
              data-testid="email-content-input"
            />
          </div>

          {/* Email Preview */}
          <div className="p-3 rounded-lg bg-sky-500/10 border border-sky-500/20">
            <p className="text-xs font-medium mb-1 text-sky-600">📧 Preview:</p>
            <p className="text-xs font-medium">{subject}</p>
            <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">
              {content.substring(0, 100)}...
            </p>
          </div>
        </div>
        
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button 
            variant="outline" 
            onClick={() => onNavigate(`/automation/workflows?tab=email&productId=${product.id}`)}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Editor Avançado
          </Button>
          <Button 
            onClick={onCreateCampaign}
            disabled={isLoading || !subject}
            className="bg-sky-600 hover:bg-sky-700"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Criando...
              </>
            ) : (
              <>
                <Mail className="h-4 w-4 mr-2" />
                Criar Campanha
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
