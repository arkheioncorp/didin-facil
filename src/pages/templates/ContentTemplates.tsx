import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import {
  Plus,
  Copy,
  Trash2,
  Edit,
  Eye,
  FileText,
  Instagram,
  Youtube,
  Video,
  Globe,
  Search,
  Tag,
  Hash,
  Sparkles,
  LayoutTemplate,
  ChevronRight,
} from 'lucide-react';
import { api } from '@/lib/api';

interface TemplateVariable {
  name: string;
  description: string;
  default_value?: string;
  required: boolean;
}

interface Template {
  id: string;
  name: string;
  description?: string;
  platform: string;
  category: string;
  caption_template: string;
  hashtags: string[];
  variables: TemplateVariable[];
  thumbnail_url?: string;
  is_public: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
  usage_count: number;
}

interface DefaultTemplate {
  name: string;
  description: string;
  platform: string;
  category: string;
  caption_template: string;
  hashtags: string[];
  variables: TemplateVariable[];
}

const platformIcons: Record<string, React.ReactNode> = {
  instagram: <Instagram className="h-4 w-4" />,
  youtube: <Youtube className="h-4 w-4" />,
  tiktok: <Video className="h-4 w-4" />,
  all: <Globe className="h-4 w-4" />,
};

const platformColors: Record<string, string> = {
  instagram: 'bg-gradient-to-r from-purple-500 to-pink-500',
  youtube: 'bg-red-500',
  tiktok: 'bg-black',
  all: 'bg-blue-500',
};

const categoryLabels: Record<string, string> = {
  product: 'Produto',
  promo: 'Promoção',
  educational: 'Educacional',
  entertainment: 'Entretenimento',
  testimonial: 'Depoimento',
  behind_scenes: 'Bastidores',
  announcement: 'Anúncio',
  custom: 'Personalizado',
};

function TemplateCard({
  template,
  onEdit,
  onDelete,
  onPreview,
  onClone,
}: {
  template: Template;
  onEdit: (template: Template) => void;
  onDelete: (id: string) => void;
  onPreview: (template: Template) => void;
  onClone: (template: Template) => void;
}) {
  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div className={`p-2 rounded-lg text-white ${platformColors[template.platform] || 'bg-muted-foreground'}`}>
              {platformIcons[template.platform] || <FileText className="h-4 w-4" />}
            </div>
            <div>
              <CardTitle className="text-base">{template.name}</CardTitle>
              <CardDescription className="text-xs">
                {categoryLabels[template.category] || template.category}
              </CardDescription>
            </div>
          </div>
          <Badge variant={template.is_public ? 'default' : 'secondary'} className="text-xs">
            {template.is_public ? 'Público' : 'Privado'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        <p className="text-sm text-muted-foreground line-clamp-2">
          {template.description || template.caption_template.slice(0, 100) + '...'}
        </p>
        <div className="flex items-center gap-2 mt-3 flex-wrap">
          {template.hashtags.slice(0, 3).map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              #{tag}
            </Badge>
          ))}
          {template.hashtags.length > 3 && (
            <Badge variant="outline" className="text-xs">
              +{template.hashtags.length - 3}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
          <span>{template.variables.length} variáveis</span>
          <span>•</span>
          <span>{template.usage_count} usos</span>
        </div>
      </CardContent>
      <CardFooter className="gap-2 pt-0">
        <Button variant="ghost" size="sm" onClick={() => onPreview(template)}>
          <Eye className="h-4 w-4 mr-1" />
          Preview
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onClone(template)}>
          <Copy className="h-4 w-4 mr-1" />
          Clonar
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onEdit(template)}>
          <Edit className="h-4 w-4 mr-1" />
          Editar
        </Button>
        <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive" onClick={() => onDelete(template.id)}>
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}

function DefaultTemplateCard({
  template,
  onUse,
}: {
  template: DefaultTemplate;
  onUse: (template: DefaultTemplate) => void;
}) {
  return (
    <Card className="group hover:shadow-md transition-shadow cursor-pointer" onClick={() => onUse(template)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div className={`p-2 rounded-lg text-white ${platformColors[template.platform] || 'bg-muted-foreground'}`}>
              {platformIcons[template.platform] || <FileText className="h-4 w-4" />}
            </div>
            <div>
              <CardTitle className="text-base">{template.name}</CardTitle>
              <CardDescription className="text-xs">
                {categoryLabels[template.category] || template.category}
              </CardDescription>
            </div>
          </div>
          <Badge variant="secondary" className="text-xs">
            <Sparkles className="h-3 w-3 mr-1" />
            Padrão
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        <p className="text-sm text-muted-foreground line-clamp-2">
          {template.description}
        </p>
      </CardContent>
      <CardFooter className="pt-0">
        <Button variant="outline" size="sm" className="w-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
          Usar Template
          <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </CardFooter>
    </Card>
  );
}

function TemplatePreview({
  template,
  isOpen,
  onClose,
}: {
  template: Template | null;
  isOpen: boolean;
  onClose: () => void;
}) {
  const [variables, setVariables] = useState<Record<string, string>>({});
  const [renderedCaption, setRenderedCaption] = useState('');

  interface RenderResponse {
    caption: string;
  }

  const renderMutation = useMutation({
    mutationFn: async () => {
      if (!template) return null;
      const response = await api.post<RenderResponse>(`/templates/${template.id}/render`, {
        variables,
        include_hashtags: true,
      });
      return response.data;
    },
    onSuccess: (data) => {
      if (data?.caption) {
        setRenderedCaption(data.caption);
      }
    },
  });

  const handleRender = () => {
    renderMutation.mutate();
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(renderedCaption || template?.caption_template || '');
    toast.success('Copiado para a área de transferência!');
  };

  if (!template) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Preview: {template.name}
          </DialogTitle>
          <DialogDescription>
            Preencha as variáveis para ver o resultado final
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-6">
            {/* Variables */}
            {template.variables.length > 0 && (
              <div className="space-y-4">
                <h4 className="font-medium flex items-center gap-2">
                  <Tag className="h-4 w-4" />
                  Variáveis
                </h4>
                <div className="grid gap-4">
                  {template.variables.map((v) => (
                    <div key={v.name} className="space-y-2">
                      <Label htmlFor={v.name}>
                        {v.name.replace(/_/g, ' ')}
                        {v.required && <span className="text-destructive">*</span>}
                      </Label>
                      <Input
                        id={v.name}
                        placeholder={v.description}
                        value={variables[v.name] || v.default_value || ''}
                        onChange={(e) =>
                          setVariables((prev) => ({ ...prev, [v.name]: e.target.value }))
                        }
                      />
                    </div>
                  ))}
                </div>
                <Button onClick={handleRender} disabled={renderMutation.isPending}>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Gerar Texto
                </Button>
              </div>
            )}

            {/* Preview */}
            <div className="space-y-4">
              <h4 className="font-medium flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Resultado
              </h4>
              <div className="p-4 rounded-lg bg-muted whitespace-pre-wrap text-sm">
                {renderedCaption || template.caption_template}
              </div>
              {template.hashtags.length > 0 && !renderedCaption && (
                <div className="flex flex-wrap gap-2">
                  {template.hashtags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      #{tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Fechar
          </Button>
          <Button onClick={handleCopy}>
            <Copy className="h-4 w-4 mr-2" />
            Copiar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function CreateTemplateDialog({
  isOpen,
  onClose,
  initialData,
}: {
  isOpen: boolean;
  onClose: () => void;
  initialData?: Partial<Template> | DefaultTemplate | null;
}) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    platform: 'all',
    category: 'custom',
    caption_template: '',
    hashtags: '',
    is_public: false,
  });

  useState(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        description: initialData.description || '',
        platform: initialData.platform || 'all',
        category: initialData.category || 'custom',
        caption_template: initialData.caption_template || '',
        hashtags: Array.isArray(initialData.hashtags) ? initialData.hashtags.join(', ') : '',
        is_public: 'is_public' in initialData ? (initialData.is_public || false) : false,
      });
    }
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      // Extrair variáveis do template (padrões: {{variavel}}, {variavel}, [variavel])
      const extractVariables = (template: string): string[] => {
        const patterns = [
          /\{\{([^}]+)\}\}/g,  // {{variavel}}
          /\{([^}]+)\}/g,      // {variavel}
          /\[([^\]]+)\]/g,     // [variavel]
        ];
        
        const variables = new Set<string>();
        patterns.forEach(pattern => {
          const matches = template.matchAll(pattern);
          for (const match of matches) {
            const varName = match[1].trim();
            // Filtrar variáveis que parecem ser placeholders reais (não URLs ou hashtags)
            if (varName && !varName.includes('http') && !varName.startsWith('#') && varName.length < 50) {
              variables.add(varName);
            }
          }
        });
        
        return Array.from(variables);
      };
      
      const payload = {
        ...formData,
        hashtags: formData.hashtags.split(',').map((h) => h.trim()).filter(Boolean),
        variables: extractVariables(formData.caption_template),
      };
      
      if (initialData && 'id' in initialData && initialData.id) {
        return api.patch(`/templates/${initialData.id}`, payload);
      }
      return api.post('/templates', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      toast.success(initialData && 'id' in initialData ? 'Template atualizado!' : 'Template criado!');
      onClose();
      setFormData({
        name: '',
        description: '',
        platform: 'all',
        category: 'custom',
        caption_template: '',
        hashtags: '',
        is_public: false,
      });
    },
    onError: () => {
      toast.error('Erro ao salvar template');
    },
  });

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>
            {initialData && 'id' in initialData ? 'Editar Template' : 'Criar Template'}
          </DialogTitle>
          <DialogDescription>
            Crie um template reutilizável para suas postagens
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nome</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ex: Promoção de Produto"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="platform">Plataforma</Label>
                <Select
                  value={formData.platform}
                  onValueChange={(v) => setFormData({ ...formData, platform: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas</SelectItem>
                    <SelectItem value="instagram">Instagram</SelectItem>
                    <SelectItem value="tiktok">TikTok</SelectItem>
                    <SelectItem value="youtube">YouTube</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Categoria</Label>
              <Select
                value={formData.category}
                onValueChange={(v) => setFormData({ ...formData, category: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(categoryLabels).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Descrição</Label>
              <Input
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Breve descrição do template"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="caption">
                Template de Legenda
                <span className="text-xs text-muted-foreground ml-2">
                  Use {"{{variavel}}"} para variáveis dinâmicas
                </span>
              </Label>
              <Textarea
                id="caption"
                value={formData.caption_template}
                onChange={(e) => setFormData({ ...formData, caption_template: e.target.value })}
                placeholder="🔥 {{produto}}&#10;&#10;Aproveite {{desconto}}% de desconto!&#10;&#10;🛒 Link na bio"
                rows={6}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="hashtags">
                <Hash className="h-4 w-4 inline mr-1" />
                Hashtags
                <span className="text-xs text-muted-foreground ml-2">
                  Separadas por vírgula
                </span>
              </Label>
              <Input
                id="hashtags"
                value={formData.hashtags}
                onChange={(e) => setFormData({ ...formData, hashtags: e.target.value })}
                placeholder="oferta, promocao, desconto"
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Template Público</Label>
                <p className="text-xs text-muted-foreground">
                  Permitir que outros usuários usem este template
                </p>
              </div>
              <Switch
                checked={formData.is_public}
                onCheckedChange={(checked) => setFormData({ ...formData, is_public: checked })}
              />
            </div>
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
            {createMutation.isPending ? 'Salvando...' : 'Salvar'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function ContentTemplates() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [platform, setPlatform] = useState<string>('all');
  const [category, setCategory] = useState<string>('all');
  const [createOpen, setCreateOpen] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [initialData, setInitialData] = useState<Partial<Template> | DefaultTemplate | null>(null);

  const { data: templates, isLoading } = useQuery({
    queryKey: ['templates', platform, category],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (platform !== 'all') params.set('platform', platform);
      if (category !== 'all') params.set('category', category);
      
      const response = await api.get<{ templates: Template[] }>(`/templates?${params}`);
      return response.data.templates;
    },
  });

  const { data: defaults } = useQuery({
    queryKey: ['templates', 'defaults'],
    queryFn: async () => {
      const response = await api.get<{ templates: DefaultTemplate[] }>('/templates/defaults');
      return response.data.templates;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/templates/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      toast.success('Template excluído!');
    },
    onError: () => {
      toast.error('Erro ao excluir template');
    },
  });

  const cloneMutation = useMutation({
    mutationFn: async (template: Template) => {
      return api.post(`/templates/${template.id}/clone?new_name=${template.name} (Cópia)`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      toast.success('Template clonado!');
    },
    onError: () => {
      toast.error('Erro ao clonar template');
    },
  });

  const handleEdit = (template: Template) => {
    setInitialData(template);
    setCreateOpen(true);
  };

  const handlePreview = (template: Template) => {
    setSelectedTemplate(template);
    setPreviewOpen(true);
  };

  const handleUseDefault = (template: DefaultTemplate) => {
    setInitialData(template);
    setCreateOpen(true);
  };

  const handleCreate = () => {
    setInitialData(null);
    setCreateOpen(true);
  };

  const filteredTemplates = templates?.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.description?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <LayoutTemplate className="h-8 w-8" />
            Templates de Conteúdo
          </h1>
          <p className="text-muted-foreground">
            Crie e gerencie templates reutilizáveis para suas postagens
          </p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Novo Template
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar templates..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={platform} onValueChange={setPlatform}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Plataforma" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            <SelectItem value="instagram">Instagram</SelectItem>
            <SelectItem value="tiktok">TikTok</SelectItem>
            <SelectItem value="youtube">YouTube</SelectItem>
          </SelectContent>
        </Select>
        <Select value={category} onValueChange={setCategory}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Categoria" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            {Object.entries(categoryLabels).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Content */}
      <Tabs defaultValue="my-templates" className="space-y-4">
        <TabsList>
          <TabsTrigger value="my-templates">Meus Templates</TabsTrigger>
          <TabsTrigger value="defaults">Templates Padrão</TabsTrigger>
        </TabsList>

        <TabsContent value="my-templates" className="space-y-4">
          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {Array(6).fill(0).map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-6 w-32" />
                    <Skeleton className="h-4 w-24" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-12 w-full" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredTemplates && filteredTemplates.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredTemplates.map((template) => (
                <TemplateCard
                  key={template.id}
                  template={template}
                  onEdit={handleEdit}
                  onDelete={(id) => deleteMutation.mutate(id)}
                  onPreview={handlePreview}
                  onClone={(t) => cloneMutation.mutate(t)}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <LayoutTemplate className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium">Nenhum template encontrado</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  Crie seu primeiro template ou use um template padrão
                </p>
                <Button onClick={handleCreate}>
                  <Plus className="h-4 w-4 mr-2" />
                  Criar Template
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="defaults" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {defaults?.map((template, index) => (
              <DefaultTemplateCard
                key={index}
                template={template}
                onUse={handleUseDefault}
              />
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <CreateTemplateDialog
        isOpen={createOpen}
        onClose={() => {
          setCreateOpen(false);
          setInitialData(null);
        }}
        initialData={initialData}
      />

      <TemplatePreview
        template={selectedTemplate}
        isOpen={previewOpen}
        onClose={() => {
          setPreviewOpen(false);
          setSelectedTemplate(null);
        }}
      />
    </div>
  );
}
