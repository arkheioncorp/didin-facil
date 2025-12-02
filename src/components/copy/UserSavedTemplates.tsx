import * as React from "react";
import { Trash2, Clock, FileText, MoreVertical, Copy } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";
import {
  getUserTemplates,
  deleteUserTemplate,
  incrementTemplateUse,
  type SavedTemplate,
} from "@/services/copy";

interface UserSavedTemplatesProps {
  onSelectTemplate?: (template: SavedTemplate) => void;
}

export function UserSavedTemplates({ onSelectTemplate }: UserSavedTemplatesProps) {
  const { toast } = useToast();
  const [templates, setTemplates] = React.useState<SavedTemplate[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [templateToDelete, setTemplateToDelete] = React.useState<SavedTemplate | null>(null);

  const loadTemplates = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await getUserTemplates();
      setTemplates(data);
    } catch (error) {
      console.error("Error loading templates:", error);
      toast({
        title: "Erro ao carregar templates",
        description: "Não foi possível carregar seus templates salvos.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  // Carregar templates na montagem
  React.useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  const handleUseTemplate = async (template: SavedTemplate) => {
    try {
      await incrementTemplateUse(template.id);
      // Atualizar contagem localmente
      setTemplates((prev) =>
        prev.map((t) =>
          t.id === template.id ? { ...t, timesUsed: t.timesUsed + 1 } : t
        )
      );
      onSelectTemplate?.(template);
      toast({
        title: "📋 Template aplicado!",
        description: `"${template.name}" foi copiado.`,
      });
    } catch (error) {
      console.error("Error using template:", error);
    }
  };

  const handleCopyToClipboard = async (template: SavedTemplate) => {
    try {
      await navigator.clipboard.writeText(template.captionTemplate);
      await incrementTemplateUse(template.id);
      setTemplates((prev) =>
        prev.map((t) =>
          t.id === template.id ? { ...t, timesUsed: t.timesUsed + 1 } : t
        )
      );
      toast({
        title: "📋 Copiado!",
        description: "Template copiado para a área de transferência.",
      });
    } catch (error) {
      console.error("Error copying template:", error);
      toast({
        title: "Erro ao copiar",
        description: "Não foi possível copiar o template.",
        variant: "destructive",
      });
    }
  };

  const confirmDelete = (template: SavedTemplate) => {
    setTemplateToDelete(template);
    setDeleteDialogOpen(true);
  };

  const handleDelete = async () => {
    if (!templateToDelete) return;
    
    try {
      await deleteUserTemplate(templateToDelete.id);
      setTemplates((prev) => prev.filter((t) => t.id !== templateToDelete.id));
      toast({
        title: "🗑️ Template excluído",
        description: `"${templateToDelete.name}" foi removido.`,
      });
    } catch (error) {
      console.error("Error deleting template:", error);
      toast({
        title: "Erro ao excluir",
        description: "Não foi possível excluir o template.",
        variant: "destructive",
      });
    } finally {
      setDeleteDialogOpen(false);
      setTemplateToDelete(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-20" />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (templates.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-10 text-center">
          <FileText className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="font-semibold text-lg mb-2">
            Nenhum template salvo
          </h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            Quando você gerar uma copy, clique em "Salvar como Template" para
            guardar para uso futuro.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg flex items-center gap-2">
          <FileText className="h-5 w-5 text-purple-500" />
          Seus Templates Salvos
        </h3>
        <Badge variant="secondary">{templates.length} templates</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {templates.map((template) => (
          <Card
            key={template.id}
            className="group hover:border-purple-500/50 transition-colors cursor-pointer"
            onClick={() => handleUseTemplate(template)}
          >
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-base font-medium line-clamp-1">
                    {template.name}
                  </CardTitle>
                  <CardDescription className="flex items-center gap-2 text-xs">
                    <Clock className="h-3 w-3" />
                    {formatDate(template.createdAt)}
                    {template.copyType && (
                      <Badge variant="outline" className="text-xs">
                        {template.copyType}
                      </Badge>
                    )}
                  </CardDescription>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopyToClipboard(template);
                      }}
                    >
                      <Copy className="h-4 w-4 mr-2" />
                      Copiar
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        confirmDelete(template);
                      }}
                      className="text-destructive"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Excluir
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground line-clamp-3 whitespace-pre-wrap">
                {template.captionTemplate}
              </p>
              <div className="flex items-center justify-between mt-3 pt-3 border-t">
                <span className="text-xs text-muted-foreground">
                  Usado {template.timesUsed} {template.timesUsed === 1 ? "vez" : "vezes"}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCopyToClipboard(template);
                  }}
                >
                  <Copy className="h-3 w-3 mr-1" />
                  Copiar
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir template?</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir "{templateToDelete?.name}"? Esta ação
              não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export default UserSavedTemplates;
