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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ExternalLink, Loader2, Eye, Edit } from "lucide-react";
import { TikTokPreview } from "../previews/SocialPreviews";
import { QuickTemplates, SaveTemplateButton } from "@/components/product/templates";
import type { ActionTemplate } from "@/stores/templatesStore";
import type { Product } from "@/types";

// TikTok icon
const TikTokIcon = ({ className = "h-4 w-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" className={`${className} fill-current`}>
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
  </svg>
);

interface TikTokModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product;
  isLoading: boolean;
  caption: string;
  setCaption: (caption: string) => void;
  sounds: string;
  setSounds: (sounds: string) => void;
  onPost: () => Promise<void>;
  onNavigate: (path: string) => void;
}

export const TikTokModal: React.FC<TikTokModalProps> = ({
  open,
  onOpenChange,
  product,
  isLoading,
  caption,
  setCaption,
  sounds,
  setSounds,
  onPost,
  onNavigate,
}) => {
  const [activeTab, setActiveTab] = React.useState<"edit" | "preview">("edit");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl" data-testid="tiktok-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <TikTokIcon className="h-5 w-5" />
            <span className="ml-1">Publicar no TikTok</span>
          </DialogTitle>
          <DialogDescription>
            Crie um vídeo para "{product.title}"
          </DialogDescription>
        </DialogHeader>
        
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "edit" | "preview")}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="edit" className="gap-2">
              <Edit className="h-4 w-4" />
              Editar
            </TabsTrigger>
            <TabsTrigger value="preview" className="gap-2">
              <Eye className="h-4 w-4" />
              Preview
            </TabsTrigger>
          </TabsList>

          <TabsContent value="edit" className="space-y-4 py-4 mt-0">
            {/* Quick Templates */}
            <QuickTemplates 
              type="tiktok" 
              onSelect={(template: ActionTemplate) => {
                const data = template.data as { caption?: string; sounds?: string };
                if (data.caption) setCaption(data.caption);
                if (data.sounds) setSounds(data.sounds);
              }} 
            />

            {/* Video Preview */}
            <div className="relative aspect-[9/16] max-w-[150px] mx-auto rounded-lg overflow-hidden border bg-black">
              <img 
                src={product.imageUrl || undefined} 
                alt={product.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </div>
              </div>
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
                <p className="text-white text-[10px] truncate">{product.title}</p>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Legenda</Label>
              <Textarea
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                className="min-h-[80px]"
                placeholder="Escreva sua legenda com hashtags..."
                data-testid="tiktok-caption-input"
              />
              <p className="text-xs text-muted-foreground">
                {caption.length}/150 caracteres
              </p>
            </div>
            
            <div className="space-y-2">
              <Label>Sons (opcional)</Label>
              <input
                type="text"
                value={sounds}
                onChange={(e) => setSounds(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Buscar som trending..."
                data-testid="tiktok-sounds-input"
              />
            </div>

            {/* Tips */}
            <div className="p-3 rounded-lg bg-muted/50 border">
              <p className="text-xs font-medium mb-1">💡 Dicas para viralizar:</p>
              <ul className="text-xs text-muted-foreground space-y-1">
                <li>• Use sons em alta</li>
                <li>• Hashtags: #fyp #viral #produto</li>
                <li>• Vídeos curtos (15-30s) engajam mais</li>
              </ul>
            </div>

            {/* Save as Template */}
            <div className="pt-2 border-t">
              <SaveTemplateButton
                type="tiktok"
                data={{ caption, sounds }}
              />
            </div>
          </TabsContent>

          <TabsContent value="preview" className="py-4 mt-0">
            <div className="flex justify-center">
              <TikTokPreview
                imageUrl={product.imageUrl || "https://placehold.co/270x480"}
                caption={caption}
                username="@seu_perfil"
                soundName={sounds || "Som original"}
              />
            </div>
            <p className="text-xs text-center text-muted-foreground mt-4">
              Visualização aproximada de como o vídeo aparecerá no TikTok
            </p>
          </TabsContent>
        </Tabs>
        
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button 
            variant="outline" 
            onClick={() => onNavigate(`/social/tiktok?action=post&productId=${product.id}`)}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Abrir Página
          </Button>
          <Button 
            onClick={onPost}
            disabled={isLoading || !caption}
            className="bg-black hover:bg-zinc-800"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Publicando...
              </>
            ) : (
              <>
                <TikTokIcon />
                <span className="ml-2">Publicar</span>
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
