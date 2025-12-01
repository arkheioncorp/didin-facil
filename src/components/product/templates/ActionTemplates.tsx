import * as React from "react";
import { cn } from "@/lib/utils";
import {
  FileText,
  Star,
  StarOff,
  Trash2,
  Copy,
  Edit2,
  Search,
  Filter,
  Clock,
  BarChart2,
  Sparkles,
  MessageCircle,
  Instagram,
  Youtube,
  Calendar,
  Mail,
  MoreHorizontal,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useTemplatesStore, type TemplateType, type ActionTemplate } from "@/stores/templatesStore";

// TikTok Icon
const TikTokIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" className={cn("fill-current", className)}>
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
  </svg>
);

// ============================================
// TEMPLATE TYPE CONFIG
// ============================================

const TEMPLATE_TYPES: Record<TemplateType, { label: string; icon: React.ReactNode; color: string }> = {
  copy: {
    label: "Copy IA",
    icon: <Sparkles className="h-4 w-4" />,
    color: "text-purple-500 bg-purple-500/10 border-purple-500/20",
  },
  whatsapp: {
    label: "WhatsApp",
    icon: <MessageCircle className="h-4 w-4" />,
    color: "text-green-500 bg-green-500/10 border-green-500/20",
  },
  instagram: {
    label: "Instagram",
    icon: <Instagram className="h-4 w-4" />,
    color: "text-pink-500 bg-pink-500/10 border-pink-500/20",
  },
  tiktok: {
    label: "TikTok",
    icon: <TikTokIcon className="h-4 w-4" />,
    color: "bg-foreground/10 border-foreground/20",
  },
  youtube: {
    label: "YouTube",
    icon: <Youtube className="h-4 w-4" />,
    color: "text-red-500 bg-red-500/10 border-red-500/20",
  },
  email: {
    label: "Email",
    icon: <Mail className="h-4 w-4" />,
    color: "text-blue-500 bg-blue-500/10 border-blue-500/20",
  },
  schedule: {
    label: "Agendamento",
    icon: <Calendar className="h-4 w-4" />,
    color: "text-orange-500 bg-orange-500/10 border-orange-500/20",
  },
};

// ============================================
// TEMPLATE CARD
// ============================================

interface TemplateCardProps {
  template: ActionTemplate;
  onSelect: (template: ActionTemplate) => void;
  onEdit: (template: ActionTemplate) => void;
  compact?: boolean;
}

const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  onSelect,
  onEdit,
  compact = false,
}) => {
  const { toggleFavorite, deleteTemplate, duplicateTemplate, incrementUsage } = useTemplatesStore();
  const typeConfig = TEMPLATE_TYPES[template.type];

  const handleSelect = () => {
    incrementUsage(template.id);
    onSelect(template);
  };

  if (compact) {
    return (
      <button
        onClick={handleSelect}
        className={cn(
          "flex items-center gap-2 p-2 rounded-lg w-full text-left transition-colors",
          "hover:bg-muted border",
          typeConfig.color
        )}
      >
        {typeConfig.icon}
        <span className="text-sm font-medium truncate flex-1">{template.name}</span>
        {template.isFavorite && <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />}
      </button>
    );
  }

  return (
    <div className={cn(
      "group p-4 rounded-lg border transition-all hover:shadow-md",
      typeConfig.color
    )}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {typeConfig.icon}
          <Badge variant="secondary" className="text-xs">
            {typeConfig.label}
          </Badge>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => toggleFavorite(template.id)}>
              {template.isFavorite ? (
                <>
                  <StarOff className="h-4 w-4 mr-2" />
                  Remover dos Favoritos
                </>
              ) : (
                <>
                  <Star className="h-4 w-4 mr-2" />
                  Adicionar aos Favoritos
                </>
              )}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onEdit(template)}>
              <Edit2 className="h-4 w-4 mr-2" />
              Editar
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => duplicateTemplate(template.id)}>
              <Copy className="h-4 w-4 mr-2" />
              Duplicar
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => deleteTemplate(template.id)}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Excluir
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <button
        onClick={handleSelect}
        className="w-full text-left"
      >
        <h3 className="font-semibold text-sm mb-1 truncate flex items-center gap-2">
          {template.name}
          {template.isFavorite && <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />}
        </h3>
        {template.description && (
          <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
            {template.description}
          </p>
        )}
      </button>

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-dashed">
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <BarChart2 className="h-3 w-3" />
            {template.usageCount}x usado
          </span>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {new Date(template.updatedAt).toLocaleDateString("pt-BR")}
          </span>
        </div>
        <Button size="sm" variant="secondary" onClick={handleSelect}>
          Usar
        </Button>
      </div>
    </div>
  );
};

// ============================================
// CREATE/EDIT TEMPLATE DIALOG
// ============================================

interface TemplateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  template?: ActionTemplate;
  defaultType?: TemplateType;
  currentData?: Record<string, unknown>;
  onSave?: (template: ActionTemplate) => void;
}

export const TemplateDialog: React.FC<TemplateDialogProps> = ({
  open,
  onOpenChange,
  template,
  defaultType = "copy",
  currentData = {},
  onSave,
}) => {
  const { addTemplate, updateTemplate } = useTemplatesStore();
  const [name, setName] = React.useState(template?.name || "");
  const [description, setDescription] = React.useState(template?.description || "");
  const [type, setType] = React.useState<TemplateType>(template?.type || defaultType);

  const isEditing = !!template;

  React.useEffect(() => {
    if (template) {
      setName(template.name);
      setDescription(template.description || "");
      setType(template.type);
    } else {
      setName("");
      setDescription("");
      setType(defaultType);
    }
  }, [template, defaultType]);

  const handleSave = () => {
    if (!name.trim()) return;

    if (isEditing) {
      updateTemplate(template.id, {
        name: name.trim(),
        description: description.trim(),
        type,
        data: { ...template.data, ...currentData },
      });
    } else {
      const id = addTemplate({
        name: name.trim(),
        description: description.trim(),
        type,
        data: currentData,
        isFavorite: false,
      });
      
      if (onSave) {
        const templates = useTemplatesStore.getState().templates;
        const newTemplate = templates.find((t) => t.id === id);
        if (newTemplate) onSave(newTemplate);
      }
    }

    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {isEditing ? "Editar Template" : "Salvar como Template"}
          </DialogTitle>
          <DialogDescription>
            {isEditing 
              ? "Atualize as informações do template" 
              : "Salve a configuração atual para reutilizar depois"
            }
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Nome do Template</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Copy para promoções"
            />
          </div>

          <div className="space-y-2">
            <Label>Descrição (opcional)</Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Descreva quando usar este template..."
              className="min-h-[80px]"
            />
          </div>

          <div className="space-y-2">
            <Label>Tipo</Label>
            <Select value={type} onValueChange={(v) => setType(v as TemplateType)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(TEMPLATE_TYPES).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    <div className="flex items-center gap-2">
                      {config.icon}
                      {config.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {Object.keys(currentData).length > 0 && (
            <div className="p-3 rounded-lg bg-muted/50 border">
              <p className="text-xs text-muted-foreground mb-2">Dados salvos:</p>
              <pre className="text-xs overflow-auto max-h-[100px]">
                {JSON.stringify(currentData, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSave} disabled={!name.trim()}>
            {isEditing ? "Salvar Alterações" : "Criar Template"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// ============================================
// TEMPLATES LIST COMPONENT
// ============================================

interface TemplatesListProps {
  type?: TemplateType;
  onSelectTemplate: (template: ActionTemplate) => void;
  maxHeight?: string;
  showSearch?: boolean;
  showFilters?: boolean;
}

export const TemplatesList: React.FC<TemplatesListProps> = ({
  type,
  onSelectTemplate,
  maxHeight = "400px",
  showSearch = true,
  showFilters = true,
}) => {
  const { templates, searchTemplates } = useTemplatesStore();
  const [search, setSearch] = React.useState("");
  const [filter, setFilter] = React.useState<"all" | "favorites" | "recent" | "most-used">("all");
  const [editingTemplate, setEditingTemplate] = React.useState<ActionTemplate | null>(null);

  const filteredTemplates = React.useMemo(() => {
    let result = type 
      ? templates.filter((t) => t.type === type)
      : templates;

    if (search) {
      const searchResults = searchTemplates(search);
      result = result.filter((t) => searchResults.find((s) => s.id === t.id));
    }

    switch (filter) {
      case "favorites":
        result = result.filter((t) => t.isFavorite);
        break;
      case "recent":
        result = [...result].sort((a, b) => 
          new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
        ).slice(0, 10);
        break;
      case "most-used":
        result = [...result].sort((a, b) => b.usageCount - a.usageCount).slice(0, 10);
        break;
    }

    return result;
  }, [templates, type, search, filter, searchTemplates]);

  return (
    <div className="space-y-4">
      {/* Search & Filters */}
      {(showSearch || showFilters) && (
        <div className="flex items-center gap-2">
          {showSearch && (
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar templates..."
                className="pl-9"
              />
            </div>
          )}
          {showFilters && (
            <Select value={filter} onValueChange={(v) => setFilter(v as typeof filter)}>
              <SelectTrigger className="w-[140px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="favorites">Favoritos</SelectItem>
                <SelectItem value="recent">Recentes</SelectItem>
                <SelectItem value="most-used">Mais Usados</SelectItem>
              </SelectContent>
            </Select>
          )}
        </div>
      )}

      {/* Templates Grid */}
      <ScrollArea style={{ maxHeight }}>
        {filteredTemplates.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">Nenhum template encontrado</p>
            <p className="text-xs">Crie um template para começar</p>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {filteredTemplates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onSelect={onSelectTemplate}
                onEdit={setEditingTemplate}
              />
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Edit Dialog */}
      <TemplateDialog
        open={!!editingTemplate}
        onOpenChange={(open) => !open && setEditingTemplate(null)}
        template={editingTemplate || undefined}
      />
    </div>
  );
};

// ============================================
// SAVE TEMPLATE BUTTON
// ============================================

interface SaveTemplateButtonProps {
  type: TemplateType;
  data: Record<string, unknown>;
  disabled?: boolean;
  className?: string;
}

export const SaveTemplateButton: React.FC<SaveTemplateButtonProps> = ({
  type,
  data,
  disabled = false,
  className,
}) => {
  const [open, setOpen] = React.useState(false);

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(true)}
        disabled={disabled}
        className={className}
      >
        <FileText className="h-4 w-4 mr-2" />
        Salvar Template
      </Button>

      <TemplateDialog
        open={open}
        onOpenChange={setOpen}
        defaultType={type}
        currentData={data}
      />
    </>
  );
};

// ============================================
// QUICK TEMPLATES (Compact List)
// ============================================

interface QuickTemplatesProps {
  type: TemplateType;
  onSelect: (template: ActionTemplate) => void;
  maxItems?: number;
}

export const QuickTemplates: React.FC<QuickTemplatesProps> = ({
  type,
  onSelect,
  maxItems = 3,
}) => {
  const templates = useTemplatesStore((state) => 
    state.templates
      .filter((t) => t.type === type)
      .sort((a, b) => b.usageCount - a.usageCount)
      .slice(0, maxItems)
  );

  if (templates.length === 0) return null;

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground font-medium">Templates Salvos</p>
      <div className="flex flex-wrap gap-2">
        {templates.map((template) => (
          <Button
            key={template.id}
            variant="outline"
            size="sm"
            onClick={() => onSelect(template)}
            className="text-xs"
          >
            {template.isFavorite && <Star className="h-3 w-3 mr-1 text-yellow-500 fill-yellow-500" />}
            {template.name}
          </Button>
        ))}
      </div>
    </div>
  );
};

export default {
  TemplateCard,
  TemplateDialog,
  TemplatesList,
  SaveTemplateButton,
  QuickTemplates,
};
