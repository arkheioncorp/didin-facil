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
import { Youtube, ExternalLink, Loader2, Eye, Edit, Monitor, Smartphone } from "lucide-react";
import { YouTubePreview } from "../previews/SocialPreviews";
import { QuickTemplates, SaveTemplateButton } from "@/components/product/templates";
import type { ActionTemplate } from "@/stores/templatesStore";
import type { Product } from "@/types";

interface YouTubeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  product: Product;
  isLoading: boolean;
  title: string;
  setTitle: (title: string) => void;
  description: string;
  setDescription: (description: string) => void;
  onUpload: () => Promise<void>;
  onNavigate: (path: string) => void;
}

export const YouTubeModal: React.FC<YouTubeModalProps> = ({
  open,
  onOpenChange,
  product,
  isLoading,
  title,
  setTitle,
  description,
  setDescription,
  onUpload,
  onNavigate,
}) => {
  const [activeTab, setActiveTab] = React.useState<"edit" | "preview">("edit");
  const [previewVariant, setPreviewVariant] = React.useState<"card" | "watch">("watch");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl" data-testid="youtube-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Youtube className="h-5 w-5 text-red-500" />
            Enviar para YouTube
          </DialogTitle>
          <DialogDescription>
            Faça upload de vídeo do "{product.title}"
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
              type="youtube" 
              onSelect={(template: ActionTemplate) => {
                const data = template.data as { title?: string; description?: string };
                if (data.title) setTitle(data.title);
                if (data.description) setDescription(data.description);
              }} 
            />

            {/* Thumbnail Preview */}
            <div className="relative aspect-video max-w-[250px] mx-auto rounded-lg overflow-hidden border">
              <img 
                src={product.imageUrl || undefined} 
                alt={product.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-2 right-2 bg-black/80 text-white text-[10px] px-1 rounded">
                0:00
              </div>
            </div>

            <div className="space-y-2">
              <Label>Título do Vídeo</Label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Título do vídeo..."
                data-testid="youtube-title-input"
              />
              <p className="text-xs text-muted-foreground">
                {title.length}/100 caracteres
              </p>
            </div>
            
            <div className="space-y-2">
              <Label>Descrição</Label>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="min-h-[120px]"
                placeholder="Descrição do vídeo com links e hashtags..."
                data-testid="youtube-description-input"
              />
              <p className="text-xs text-muted-foreground">
                {description.length}/5000 caracteres
              </p>
            </div>

            {/* SEO Tips */}
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
              <p className="text-xs font-medium mb-1 text-red-600">📹 Dicas de SEO:</p>
              <ul className="text-xs text-muted-foreground space-y-1">
                <li>• Inclua palavras-chave no título</li>
                <li>• Adicione timestamps na descrição</li>
                <li>• Use tags relevantes</li>
              </ul>
            </div>

            {/* Save as Template */}
            <div className="pt-2 border-t">
              <SaveTemplateButton
                type="youtube"
                data={{ title, description }}
              />
            </div>
          </TabsContent>

          <TabsContent value="preview" className="py-4 mt-0">
            {/* Preview variant toggle */}
            <div className="flex justify-center gap-2 mb-4">
              <Button
                variant={previewVariant === "watch" ? "default" : "outline"}
                size="sm"
                onClick={() => setPreviewVariant("watch")}
              >
                <Monitor className="h-4 w-4 mr-2" />
                Página do Vídeo
              </Button>
              <Button
                variant={previewVariant === "card" ? "default" : "outline"}
                size="sm"
                onClick={() => setPreviewVariant("card")}
              >
                <Smartphone className="h-4 w-4 mr-2" />
                Card
              </Button>
            </div>
            
            <div className="flex justify-center">
              <YouTubePreview
                imageUrl={product.imageUrl || "https://placehold.co/640x360"}
                title={title || product.title}
                description={description}
                channelName="Seu Canal"
                variant={previewVariant}
              />
            </div>
            <p className="text-xs text-center text-muted-foreground mt-4">
              Visualização aproximada de como o vídeo aparecerá no YouTube
            </p>
          </TabsContent>
        </Tabs>
        
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button 
            variant="outline" 
            onClick={() => onNavigate(`/social/youtube?action=post&productId=${product.id}`)}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Abrir Página
          </Button>
          <Button 
            onClick={onUpload}
            disabled={isLoading || !title}
            className="bg-red-600 hover:bg-red-700"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Enviando...
              </>
            ) : (
              <>
                <Youtube className="h-4 w-4 mr-2" />
                Enviar Vídeo
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
