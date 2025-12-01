/**
 * Social Templates Page
 * ======================
 * Biblioteca de templates reutilizáveis para posts sociais
 * - Templates de legendas
 * - Templates de hashtags
 * - Templates de copy
 * - Organização por categoria
 */

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import {
  FileText,
  Hash,
  Copy,
  Plus,
  Search,
  Star,
  StarOff,
  Trash2,
  Edit,
  MoreVertical,
  Instagram,
  Youtube,
  MessageCircle,
  Loader2,
  Sparkles,
  Folder,
  Filter,
  CheckCircle2,
} from "lucide-react";

// TikTok Icon
const TikTokIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" className={`fill-current ${className || "h-4 w-4"}`}>
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z" />
  </svg>
);

// Types
interface Template {
  id: string;
  name: string;
  type: "caption" | "hashtags" | "full";
  category: string;
  platforms: string[];
  content: string;
  variables: string[];
  is_favorite: boolean;
  use_count: number;
  created_at: string;
  updated_at: string;
}

interface Category {
  id: string;
  name: string;
  count: number;
}

// Platform Config
const PLATFORM_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  instagram: Instagram,
  tiktok: TikTokIcon,
  youtube: Youtube,
  whatsapp: MessageCircle,
};

const TEMPLATE_TYPES = [
  { value: "caption", label: "Legenda", icon: FileText },
  { value: "hashtags", label: "Hashtags", icon: Hash },
  { value: "full", label: "Completo", icon: Sparkles },
];

const DEFAULT_CATEGORIES = [
  "Vendas",
  "Engajamento",
  "Promoções",
  "Lançamento",
  "Educacional",
  "Entretenimento",
  "Bastidores",
  "Depoimentos",
  "Dicas",
  "Geral",
];

// Template Card Component
const TemplateCard: React.FC<{
  template: Template;
  onUse: (template: Template) => void;
  onEdit: (template: Template) => void;
  onDelete: (id: string) => void;
  onToggleFavorite: (id: string) => void;
}> = ({ template, onUse, onEdit, onDelete, onToggleFavorite }) => {
  const typeConfig = TEMPLATE_TYPES.find(t => t.value === template.type);
  const TypeIcon = typeConfig?.icon || FileText;

  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-muted">
              <TypeIcon className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base">{template.name}</CardTitle>
              <div className="flex items-center gap-1 mt-1">
                <Badge variant="secondary" className="text-xs">
                  {typeConfig?.label}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {template.category}
                </Badge>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => onToggleFavorite(template.id)}
            >
              {template.is_favorite ? (
                <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
              ) : (
                <StarOff className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onEdit(template)}>
                  <Edit className="h-4 w-4 mr-2" />
                  Editar
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => onDelete(template.id)}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Excluir
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pb-3">
        <p className="text-sm text-muted-foreground line-clamp-3">
          {template.content}
        </p>
        
        {template.variables.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {template.variables.map((v) => (
              <Badge key={v} variant="outline" className="text-xs bg-blue-500/10">
                {`{{${v}}}`}
              </Badge>
            ))}
          </div>
        )}
        
        <div className="flex items-center gap-2 mt-3">
          {template.platforms.map((platform) => {
            const Icon = PLATFORM_ICONS[platform] || MessageCircle;
            return (
              <Icon key={platform} className="h-4 w-4 text-muted-foreground" />
            );
          })}
        </div>
      </CardContent>
      
      <CardFooter className="pt-0 flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          Usado {template.use_count}x
        </span>
        <Button size="sm" onClick={() => onUse(template)}>
          <Copy className="h-3 w-3 mr-1" />
          Usar
        </Button>
      </CardFooter>
    </Card>
  );
};

// Create/Edit Template Dialog
const TemplateDialog: React.FC<{
  open: boolean;
  onOpenChange: (open: boolean) => void;
  template?: Template;
  onSave: (data: Partial<Template>) => void;
  loading?: boolean;
}> = ({ open, onOpenChange, template, onSave, loading }) => {
  const [formData, setFormData] = useState({
    name: "",
    type: "caption" as "caption" | "hashtags" | "full",
    category: "Geral",
    platforms: ["instagram"] as string[],
    content: "",
  });

  useEffect(() => {
    if (template) {
      setFormData({
        name: template.name,
        type: template.type,
        category: template.category,
        platforms: template.platforms,
        content: template.content,
      });
    } else {
      setFormData({
        name: "",
        type: "caption",
        category: "Geral",
        platforms: ["instagram"],
        content: "",
      });
    }
  }, [template, open]);

  const handleSubmit = () => {
    // Extract variables from content (format: {{variable_name}})
    const variableRegex = /\{\{(\w+)\}\}/g;
    const variables: string[] = [];
    let match;
    while ((match = variableRegex.exec(formData.content)) !== null) {
      if (!variables.includes(match[1])) {
        variables.push(match[1]);
      }
    }

    onSave({
      ...formData,
      variables,
    });
  };

  const togglePlatform = (platform: string) => {
    if (formData.platforms.includes(platform)) {
      setFormData({
        ...formData,
        platforms: formData.platforms.filter(p => p !== platform),
      });
    } else {
      setFormData({
        ...formData,
        platforms: [...formData.platforms, platform],
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {template ? "Editar Template" : "Novo Template"}
          </DialogTitle>
          <DialogDescription>
            {template 
              ? "Atualize as informações do template"
              : "Crie um novo template reutilizável para seus posts"
            }
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nome do Template</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ex: Promoção Flash"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Tipo</Label>
              <Select 
                value={formData.type} 
                onValueChange={(v) => setFormData({ ...formData, type: v as typeof formData.type })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TEMPLATE_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      <div className="flex items-center gap-2">
                        <type.icon className="h-4 w-4" />
                        {type.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Categoria</Label>
            <Select 
              value={formData.category} 
              onValueChange={(v) => setFormData({ ...formData, category: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DEFAULT_CATEGORIES.map((cat) => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Plataformas</Label>
            <div className="flex gap-2">
              {Object.entries(PLATFORM_ICONS).map(([platform, Icon]) => (
                <Button
                  key={platform}
                  type="button"
                  variant={formData.platforms.includes(platform) ? "default" : "outline"}
                  size="sm"
                  onClick={() => togglePlatform(platform)}
                >
                  <Icon className="h-4 w-4 mr-1" />
                  {platform.charAt(0).toUpperCase() + platform.slice(1)}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="content">Conteúdo</Label>
            <Textarea
              id="content"
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              placeholder="Use {{variavel}} para campos dinâmicos. Ex: Olá {{nome}}, confira nossa {{promocao}}!"
              rows={6}
            />
            <p className="text-xs text-muted-foreground">
              Use {"{{variavel}}"} para criar campos que serão preenchidos na hora de usar o template.
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={loading || !formData.name || !formData.content}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Salvando...
              </>
            ) : (
              <>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Salvar Template
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Use Template Dialog
const UseTemplateDialog: React.FC<{
  open: boolean;
  onOpenChange: (open: boolean) => void;
  template: Template | null;
  onCopy: (content: string) => void;
}> = ({ open, onOpenChange, template, onCopy }) => {
  const [variables, setVariables] = useState<Record<string, string>>({});
  const [previewContent, setPreviewContent] = useState("");

  useEffect(() => {
    if (template) {
      const initialVars: Record<string, string> = {};
      template.variables.forEach(v => {
        initialVars[v] = "";
      });
      setVariables(initialVars);
      setPreviewContent(template.content);
    }
  }, [template]);

  useEffect(() => {
    if (template) {
      let content = template.content;
      Object.entries(variables).forEach(([key, value]) => {
        content = content.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value || `{{${key}}}`);
      });
      setPreviewContent(content);
    }
  }, [variables, template]);

  const handleCopy = () => {
    onCopy(previewContent);
    onOpenChange(false);
  };

  if (!template) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Usar Template: {template.name}</DialogTitle>
          <DialogDescription>
            Preencha as variáveis e copie o conteúdo
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {template.variables.length > 0 && (
            <div className="space-y-3">
              <Label>Variáveis</Label>
              <div className="grid grid-cols-2 gap-3">
                {template.variables.map((v) => (
                  <div key={v} className="space-y-1">
                    <Label htmlFor={v} className="text-sm text-muted-foreground">
                      {v}
                    </Label>
                    <Input
                      id={v}
                      value={variables[v] || ""}
                      onChange={(e) => setVariables({ ...variables, [v]: e.target.value })}
                      placeholder={`Digite ${v}...`}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Label>Preview</Label>
            <div className="p-4 rounded-lg bg-muted min-h-[100px]">
              <p className="whitespace-pre-wrap">{previewContent}</p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={handleCopy}>
            <Copy className="h-4 w-4 mr-2" />
            Copiar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Main Component
export const Templates: React.FC = () => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<string>("all");
  const [filterCategory, setFilterCategory] = useState<string>("all");
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  
  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editTemplate, setEditTemplate] = useState<Template | null>(null);
  const [useTemplate, setUseTemplate] = useState<Template | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const response = await api.get<{ templates: Template[]; categories: Category[] }>("/templates");
      setTemplates(response.data.templates || []);
      setCategories(response.data.categories || []);
    } catch (error) {
      console.error("Error fetching templates:", error);
      // Use mock data
      setTemplates(getMockTemplates());
      setCategories(DEFAULT_CATEGORIES.map((c, i) => ({ id: String(i), name: c, count: 0 })));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const handleSaveTemplate = async (data: Partial<Template>) => {
    setSaving(true);
    try {
      if (editTemplate) {
        await api.put(`/templates/${editTemplate.id}`, data);
        toast({ title: "Template atualizado!" });
      } else {
        await api.post("/templates", data);
        toast({ title: "Template criado!" });
      }
      fetchTemplates();
      setCreateDialogOpen(false);
      setEditTemplate(null);
    } catch (error) {
      console.error("Error saving template:", error);
      toast({ title: "Erro ao salvar template", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteTemplate = async (id: string) => {
    try {
      await api.delete(`/templates/${id}`);
      toast({ title: "Template excluído" });
      setTemplates(templates.filter(t => t.id !== id));
    } catch (error) {
      console.error("Error deleting template:", error);
      toast({ title: "Erro ao excluir template", variant: "destructive" });
    }
  };

  const handleToggleFavorite = async (id: string) => {
    const template = templates.find(t => t.id === id);
    if (!template) return;

    try {
      await api.patch(`/templates/${id}/favorite`, { is_favorite: !template.is_favorite });
      setTemplates(templates.map(t => 
        t.id === id ? { ...t, is_favorite: !t.is_favorite } : t
      ));
    } catch (error) {
      console.error("Error toggling favorite:", error);
      // Still update locally
      setTemplates(templates.map(t => 
        t.id === id ? { ...t, is_favorite: !t.is_favorite } : t
      ));
    }
  };

  const handleUseTemplate = (template: Template) => {
    setUseTemplate(template);
    // Increment use count
    setTemplates(templates.map(t => 
      t.id === template.id ? { ...t, use_count: t.use_count + 1 } : t
    ));
  };

  const handleCopyContent = (content: string) => {
    navigator.clipboard.writeText(content);
    toast({ title: "Copiado!", description: "O conteúdo foi copiado para a área de transferência" });
  };

  // Filter templates
  const filteredTemplates = templates.filter(t => {
    if (searchQuery && !t.name.toLowerCase().includes(searchQuery.toLowerCase()) && 
        !t.content.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    if (filterType !== "all" && t.type !== filterType) return false;
    if (filterCategory !== "all" && t.category !== filterCategory) return false;
    if (showFavoritesOnly && !t.is_favorite) return false;
    return true;
  });

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <FileText className="h-8 w-8" />
            Templates
          </h1>
          <p className="text-muted-foreground mt-1">
            Biblioteca de templates reutilizáveis para suas publicações
          </p>
        </div>
        
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Novo Template
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 items-center">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <Select value={filterType} onValueChange={setFilterType}>
          <SelectTrigger className="w-[140px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Tipo" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            {TEMPLATE_TYPES.map((type) => (
              <SelectItem key={type.value} value={type.value}>
                {type.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-[140px]">
            <Folder className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Categoria" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            {(categories.length > 0 ? categories.map(c => c.name) : DEFAULT_CATEGORIES).map((cat) => (
              <SelectItem key={cat} value={cat}>{cat}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button 
          variant={showFavoritesOnly ? "default" : "outline"} 
          size="sm"
          onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
        >
          <Star className={`h-4 w-4 mr-1 ${showFavoritesOnly ? 'fill-current' : ''}`} />
          Favoritos
        </Button>
      </div>

      {/* Stats */}
      <div className="flex gap-4 text-sm text-muted-foreground">
        <span>{filteredTemplates.length} templates encontrados</span>
        <span>•</span>
        <span>{templates.filter(t => t.is_favorite).length} favoritos</span>
      </div>

      {/* Templates Grid */}
      {loading ? (
        <div className="flex items-center justify-center min-h-[300px]">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : filteredTemplates.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium">Nenhum template encontrado</h3>
            <p className="text-muted-foreground mt-1">
              {searchQuery || filterType !== "all" || filterCategory !== "all"
                ? "Tente ajustar os filtros"
                : "Crie seu primeiro template para começar"
              }
            </p>
            {!searchQuery && filterType === "all" && filterCategory === "all" && (
              <Button className="mt-4" onClick={() => setCreateDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Criar Template
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredTemplates.map((template) => (
            <TemplateCard
              key={template.id}
              template={template}
              onUse={handleUseTemplate}
              onEdit={(t) => {
                setEditTemplate(t);
                setCreateDialogOpen(true);
              }}
              onDelete={handleDeleteTemplate}
              onToggleFavorite={handleToggleFavorite}
            />
          ))}
        </div>
      )}

      {/* Dialogs */}
      <TemplateDialog
        open={createDialogOpen}
        onOpenChange={(open) => {
          setCreateDialogOpen(open);
          if (!open) setEditTemplate(null);
        }}
        template={editTemplate || undefined}
        onSave={handleSaveTemplate}
        loading={saving}
      />

      <UseTemplateDialog
        open={!!useTemplate}
        onOpenChange={(open) => !open && setUseTemplate(null)}
        template={useTemplate}
        onCopy={handleCopyContent}
      />
    </div>
  );
};

// Mock data
function getMockTemplates(): Template[] {
  return [
    {
      id: "1",
      name: "Promoção Flash",
      type: "full",
      category: "Promoções",
      platforms: ["instagram", "tiktok"],
      content: "🔥 PROMOÇÃO RELÂMPAGO!\n\n{{produto}} com {{desconto}}% OFF! 💰\n\nApenas {{quantidade}} unidades disponíveis!\n\n➡️ Link na bio\n\n#promocao #oferta #desconto",
      variables: ["produto", "desconto", "quantidade"],
      is_favorite: true,
      use_count: 45,
      created_at: "2024-01-15T10:00:00Z",
      updated_at: "2024-01-15T10:00:00Z",
    },
    {
      id: "2",
      name: "Dica Rápida",
      type: "caption",
      category: "Dicas",
      platforms: ["instagram", "youtube"],
      content: "💡 DICA DO DIA!\n\n{{dica}}\n\n📌 Salva esse post pra não esquecer!\n\nComente \"🔥\" se você já sabia!",
      variables: ["dica"],
      is_favorite: false,
      use_count: 32,
      created_at: "2024-01-10T14:30:00Z",
      updated_at: "2024-01-10T14:30:00Z",
    },
    {
      id: "3",
      name: "Hashtags Vendas",
      type: "hashtags",
      category: "Vendas",
      platforms: ["instagram", "tiktok"],
      content: "#empreendedorismo #vendas #marketing #negocios #dinheiro #sucesso #trabalho #motivacao #foco #meta #resultado #lucro #investimento #renda #financas",
      variables: [],
      is_favorite: true,
      use_count: 78,
      created_at: "2024-01-05T09:00:00Z",
      updated_at: "2024-01-05T09:00:00Z",
    },
    {
      id: "4",
      name: "Depoimento Cliente",
      type: "full",
      category: "Depoimentos",
      platforms: ["instagram", "whatsapp"],
      content: "⭐ O QUE NOSSOS CLIENTES DIZEM:\n\n\"{{depoimento}}\"\n\n- {{nome}}, {{cidade}}\n\n📲 Quer resultados assim também? Chama no Direct!",
      variables: ["depoimento", "nome", "cidade"],
      is_favorite: false,
      use_count: 23,
      created_at: "2024-01-08T16:00:00Z",
      updated_at: "2024-01-08T16:00:00Z",
    },
    {
      id: "5",
      name: "Lançamento Produto",
      type: "full",
      category: "Lançamento",
      platforms: ["instagram", "tiktok", "youtube"],
      content: "🚀 LANÇAMENTO!\n\nApresentamos: {{nome_produto}}\n\n✨ {{beneficio1}}\n✨ {{beneficio2}}\n✨ {{beneficio3}}\n\n💰 De R$ {{preco_original}} por apenas R$ {{preco_promocional}}\n\n🛒 Disponível agora no link da bio!\n\n#lancamento #novidade #produto",
      variables: ["nome_produto", "beneficio1", "beneficio2", "beneficio3", "preco_original", "preco_promocional"],
      is_favorite: true,
      use_count: 15,
      created_at: "2024-01-20T11:00:00Z",
      updated_at: "2024-01-20T11:00:00Z",
    },
  ];
}

export default Templates;
