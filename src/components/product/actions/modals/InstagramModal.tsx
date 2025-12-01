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
import { Instagram, ExternalLink, Loader2, Eye, Edit } from "lucide-react";
import { InstagramPreview } from "../previews/SocialPreviews";
import { QuickTemplates, SaveTemplateButton } from "@/components/product/templates";
import type { ActionTemplate } from "@/stores/templatesStore";
import type { Product } from "@/types";

interface InstagramModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product;
  isLoading: boolean;
  caption: string;
  setCaption: (caption: string) => void;
  hashtags: string;
  setHashtags: (hashtags: string) => void;
  onPost: () => Promise<void>;
  onNavigate: (path: string) => void;
}

export const InstagramModal: React.FC<InstagramModalProps> = ({
  open,
  onOpenChange,
  product,
  isLoading,
  caption,
  setCaption,
  hashtags,
  setHashtags,
  onPost,
  onNavigate,
}) => {
  const [activeTab, setActiveTab] = React.useState<"edit" | "preview">("edit");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl" data-testid="instagram-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Instagram className="h-5 w-5 text-pink-500" />
            Publicar no Instagram
          </DialogTitle>
          <DialogDescription>
            Crie um post para "{product.title}"
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
            {/* Preview Image */}
            <div className="relative aspect-square max-w-[200px] mx-auto rounded-lg overflow-hidden border">
              <img 
                src={product.imageUrl || undefined} 
                alt={product.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
                <p className="text-white text-xs truncate">{product.title}</p>
              </div>
            </div>

            {/* Quick Templates */}
            <QuickTemplates 
              type="instagram" 
              onSelect={(template: ActionTemplate) => {
                const data = template.data as { caption?: string; hashtags?: string };
                if (data.caption) setCaption(data.caption);
                if (data.hashtags) setHashtags(data.hashtags);
              }} 
            />

            <div className="space-y-2">
              <Label>Legenda</Label>
              <Textarea
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                className="min-h-[100px]"
                placeholder="Escreva sua legenda..."
                data-testid="instagram-caption-input"
              />
              <p className="text-xs text-muted-foreground">
                {caption.length}/2200 caracteres
              </p>
            </div>
            
            <div className="space-y-2">
              <Label>Hashtags</Label>
              <Textarea
                value={hashtags}
                onChange={(e) => setHashtags(e.target.value)}
                className="min-h-[60px]"
                placeholder="#hashtag1 #hashtag2"
                data-testid="instagram-hashtags-input"
              />
              <p className="text-xs text-muted-foreground">
                {hashtags.split(/[\s,]+/).filter(h => h.startsWith("#")).length}/30 hashtags
              </p>
            </div>

            {/* Save as Template */}
            <div className="pt-2 border-t">
              <SaveTemplateButton
                type="instagram"
                data={{ caption, hashtags }}
              />
            </div>
          </TabsContent>

          <TabsContent value="preview" className="py-4 mt-0">
            <div className="flex justify-center">
              <InstagramPreview
                imageUrl={product.imageUrl || "https://placehold.co/400x400"}
                caption={caption}
                hashtags={hashtags}
                username="seu_perfil"
                likes={Math.floor(Math.random() * 500) + 100}
              />
            </div>
            <p className="text-xs text-center text-muted-foreground mt-4">
              Visualização aproximada de como o post aparecerá no Instagram
            </p>
          </TabsContent>
        </Tabs>
        
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button 
            variant="outline" 
            onClick={() => onNavigate(`/social/instagram?action=post&productId=${product.id}`)}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Abrir Página
          </Button>
          <Button 
            onClick={onPost}
            disabled={isLoading || !caption}
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Publicando...
              </>
            ) : (
              <>
                <Instagram className="h-4 w-4 mr-2" />
                Publicar
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
