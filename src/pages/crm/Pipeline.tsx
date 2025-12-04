/**
 * Pipeline de Vendas - Kanban Board
 * 
 * CRM sales pipeline with drag-and-drop Kanban interface.
 * Features:
 * - Multiple pipelines support
 * - Stage-based deal organization
 * - Real-time metrics
 * - Drag & drop with optimistic updates
 */

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import {
  Plus, GripVertical, MoreHorizontal, Edit, Eye,
  Calendar, DollarSign, Clock,
  CheckCircle2, XCircle,
  Filter, Search, RefreshCw, Settings, BarChart3
} from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

// Import new API hooks and types  
import { usePipelines, usePipeline, usePipelineMetrics } from "./hooks/usePipeline";
import { useDeals, useMoveDeal, useCreateDeal, useUpdateDeal, useDeleteDeal, useWinDeal, useLoseDeal } from "./hooks/useDeals";
import type { Pipeline, Deal, PipelineStage } from "@/lib/api/crm";
import { formatCurrency, getTagColor, calculateDaysInStage } from "@/lib/api/crm";

// ==================== UTILITY FUNCTIONS ====================

/**
 * Filter deals belonging to a specific stage
 */
const getDealsByStage = (deals: Deal[], stageId: string): Deal[] => {
  return deals.filter(deal => deal.stage_id === stageId);
};

// ==================== SUB-COMPONENTS ====================

/**
 * DealCard Component
 */
const DealCard = ({
  deal,
  onDragStart,
  onEdit,
  onView,
  onWin,
  onLose
}: {
  deal: Deal;
  onDragStart: (e: React.DragEvent, deal: Deal) => void;
  onEdit: (deal: Deal) => void;
  onView: (deal: Deal) => void;
  onWin: (id: string) => void;
  onLose: (id: string) => void;
}) => {
  const daysInStage = calculateDaysInStage(deal);

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, deal)}
      className="bg-card border border-border rounded-lg p-3 cursor-grab active:cursor-grabbing shadow-sm hover:shadow-md transition-all hover:border-primary/50 group"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <GripVertical className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          <span className="font-medium text-sm truncate">{deal.title}</span>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onView(deal)}>
              <Eye className="mr-2 h-4 w-4" /> Ver detalhes
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onEdit(deal)}>
              <Edit className="mr-2 h-4 w-4" /> Editar
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-green-500" onClick={() => onWin(deal.id)}>
              <CheckCircle2 className="mr-2 h-4 w-4" /> Marcar como ganho
            </DropdownMenuItem>
            <DropdownMenuItem className="text-red-500" onClick={() => onLose(deal.id)}>
              <XCircle className="mr-2 h-4 w-4" /> Marcar como perdido
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Value */}
      <div className="flex items-center gap-1 text-lg font-semibold text-foreground mb-2">
        <DollarSign className="w-4 h-4 text-green-500" />
        {formatCurrency(deal.value)}
      </div>

      {/* Contact */}
      <div className="flex items-center gap-2 mb-2">
        <Avatar className="h-6 w-6">
          <AvatarImage src={deal.contact.avatar} />
          <AvatarFallback className="text-xs bg-primary/10 text-primary">
            {deal.contact.name.split(" ").map(n => n[0]).join("")}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium truncate">{deal.contact.name}</p>
          {deal.contact.company && (
            <p className="text-xs text-muted-foreground truncate">{deal.contact.company}</p>
          )}
        </div>
      </div>

      {/* Tags */}
      {deal.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {deal.tags.slice(0, 2).map(tag => (
            <Badge key={tag} variant="outline" className={`text-xs px-1.5 py-0 ${getTagColor(tag)}`}>
              {tag}
            </Badge>
          ))}
          {deal.tags.length > 2 && (
            <Badge variant="outline" className="text-xs px-1.5 py-0">
              +{deal.tags.length - 2}
            </Badge>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                <span>{daysInStage}d</span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>{daysInStage} dias neste estágio</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
        {deal.expected_close_date && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  <span>{new Date(deal.expected_close_date).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Previsão de fechamento</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
    </div>
  );
};

/**
 * StageColumn Component
 */
const StageColumn = ({
  stage,
  deals,
  onDragOver,
  onDrop,
  onDragStart,
  onEditDeal,
  onViewDeal,
  onWinDeal,
  onLoseDeal,
  onAddDeal
}: {
  stage: PipelineStage;
  deals: Deal[];
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent, stageId: string) => void;
  onDragStart: (e: React.DragEvent, deal: Deal) => void;
  onEditDeal: (deal: Deal) => void;
  onViewDeal: (deal: Deal) => void;
  onWinDeal: (id: string) => void;
  onLoseDeal: (id: string) => void;
  onAddDeal: (stageId: string) => void;
}) => {
  const stageValue = deals.reduce((sum, deal) => sum + deal.value, 0);
  const weightedValue = deals.reduce((sum, deal) => sum + (deal.value * stage.probability / 100), 0);

  return (
    <div
      className="flex-shrink-0 w-72 bg-muted/30 rounded-lg border border-border/50"
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, stage.id)}
    >
      {/* Stage Header */}
      <div className="p-3 border-b border-border/50">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: stage.color }}
            />
            <h3 className="font-semibold text-sm">{stage.name}</h3>
            <Badge variant="secondary" className="text-xs">
              {deals.length}
            </Badge>
          </div>
          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onAddDeal(stage.id)}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{formatCurrency(stageValue)}</span>
          <span>{stage.probability}% prob.</span>
        </div>
        <div className="text-xs text-green-500 mt-1">
          Ponderado: {formatCurrency(weightedValue)}
        </div>
      </div>

      {/* Deals List */}
      <ScrollArea className="h-[calc(100vh-280px)]">
        <div className="p-2 space-y-2">
          {deals.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              <p>Nenhum deal neste estágio</p>
              <Button variant="ghost" size="sm" className="mt-2" onClick={() => onAddDeal(stage.id)}>
                <Plus className="h-4 w-4 mr-1" /> Adicionar
              </Button>
            </div>
          ) : (
            deals.map(deal => (
              <DealCard
                key={deal.id}
                deal={deal}
                onDragStart={onDragStart}
                onEdit={onEditDeal}
                onView={onViewDeal}
                onWin={onWinDeal}
                onLose={onLoseDeal}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

// ==================== MAIN COMPONENT ====================

const PipelinePage = () => {
  const [selectedPipelineId, setSelectedPipelineId] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState("");
  const [draggedDeal, setDraggedDeal] = useState<Deal | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);
  const [currentStageId, setCurrentStageId] = useState<string>("");
  const [dealForm, setDealForm] = useState({
    title: "",
    value: 0,
    contact_name: "",
    contact_email: "",
    expected_close_date: "",
    description: "",
  });

  // React Query hooks (replacing all mock data!)
  const { data: pipelines, isLoading: loadingPipelines } = usePipelines();
  const { data: pipeline, isLoading: loadingPipeline } = usePipeline(selectedPipelineId);
  const { data: deals = [], isLoading: _loadingDeals } = useDeals({ pipeline_id: selectedPipelineId });
  const { data: _metrics } = usePipelineMetrics(selectedPipelineId);

  // Mutations
  const moveDeal = useMoveDeal();
  const createDeal = useCreateDeal();
  const updateDeal = useUpdateDeal();
  const _deleteDeal = useDeleteDeal();
  const winDeal = useWinDeal();
  const loseDeal = useLoseDeal();

  // Auto-select first pipeline
  useEffect(() => {
    if (pipelines && pipelines.length > 0 && !selectedPipelineId) {
      const defaultPipeline = pipelines.find(p => p.is_default) || pipelines[0];
      setSelectedPipelineId(defaultPipeline.id);
    }
  }, [pipelines, selectedPipelineId]);

  // Drag handlers
  const handleDragStart = useCallback((e: React.DragEvent, deal: Deal) => {
    setDraggedDeal(deal);
    e.dataTransfer.effectAllowed = "move";
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, stageId: string) => {
    e.preventDefault();
    if (!draggedDeal) return;

    // Call API to move deal (with optimistic update!)
    moveDeal.mutate({ id: draggedDeal.id, stage_id: stageId });
    setDraggedDeal(null);
  }, [draggedDeal, moveDeal]);

  // Actions
  const handleViewDeal = (deal: Deal) => {
    setSelectedDeal(deal);
    setViewDialogOpen(true);
  };

  const handleEditDeal = (deal: Deal) => {
    setSelectedDeal(deal);
    setDealForm({
      title: deal.title,
      value: deal.value,
      contact_name: deal.contact.name,
      contact_email: deal.contact.email,
      expected_close_date: deal.expected_close_date || "",
      description: deal.description || "",
    });
    setEditDialogOpen(true);
  };

  const handleAddDeal = (stageId: string) => {
    setCurrentStageId(stageId);
    setDealForm({
      title: "",
      value: 0,
      contact_name: "",
      contact_email: "",
      expected_close_date: "",
      description: "",
    });
    setCreateDialogOpen(true);
  };

  const handleSaveDeal = async () => {
    if (editDialogOpen && selectedDeal) {
      // Update existing deal
      updateDeal.mutate({
        id: selectedDeal.id,
        data: {
          title: dealForm.title,
          value: dealForm.value,
          expected_close_date: dealForm.expected_close_date || undefined,
        }
      }, {
        onSuccess: () => {
          setEditDialogOpen(false);
          setSelectedDeal(null);
        }
      });
    } else if (createDialogOpen) {
      // Create new deal
      createDeal.mutate({
        title: dealForm.title,
        value: dealForm.value,
        contact_email: dealForm.contact_email,
        contact_name: dealForm.contact_name,
        pipeline_id: selectedPipelineId,
        stage_id: currentStageId,
        expected_close_date: dealForm.expected_close_date || undefined,
      }, {
        onSuccess: () => {
          setCreateDialogOpen(false);
        }
      });
    }
  };

  // Filter deals by search
  const filteredDeals = deals.filter(deal => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      deal.title.toLowerCase().includes(term) ||
      deal.contact.name.toLowerCase().includes(term) ||
      deal.contact.company?.toLowerCase().includes(term)
    );
  });

  // Loading state
  if (loadingPipelines || (selectedPipelineId && loadingPipeline)) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex justify-between items-center">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {[1, 2, 3, 4].map(i => (
            <Skeleton key={i} className="flex-shrink-0 w-72 h-96" />
          ))}
        </div>
      </div>
    );
  }

  if (!pipeline) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Nenhum pipeline disponível</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b bg-background">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Pipeline de Vendas</h1>
            <p className="text-muted-foreground text-sm">
              Gerencie seu funil de vendas com drag & drop
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <BarChart3 className="h-4 w-4 mr-2" /> Métricas
            </Button>
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" /> Configurar
            </Button>
            <Button size="sm" onClick={() => handleAddDeal(pipeline.stages[0]?.id || "")}>
              <Plus className="h-4 w-4 mr-2" /> Novo Deal
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <Select
            value={selectedPipelineId}
            onValueChange={setSelectedPipelineId}
          >
            <SelectTrigger className="w-60">
              <SelectValue placeholder="Selecione um pipeline" />
            </SelectTrigger>
            <SelectContent>
              {pipelines?.map(p => (
                <SelectItem key={p.id} value={p.id}>
                  <div className="flex items-center justify-between w-full">
                    <span>{p.name}</span>
                    {p.is_default && (
                      <Badge variant="secondary" className="ml-2 text-xs">Padrão</Badge>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar deals..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>

          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" /> Filtros
          </Button>

          <Button variant="ghost" size="icon">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {/* Pipeline Summary */}
        <div className="flex items-center gap-6 mt-4 text-sm">
          <div>
            <span className="text-muted-foreground">Total de deals:</span>{" "}
            <span className="font-semibold">{filteredDeals.length}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Valor total:</span>{" "}
            <span className="font-semibold">
              {formatCurrency(filteredDeals.reduce((sum, d) => sum + d.value, 0))}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Valor ponderado:</span>{" "}
            <span className="font-semibold text-green-500">
              {formatCurrency(
                filteredDeals.reduce((sum, d) => {
                  const stage = pipeline.stages.find(s => s.id === d.stage_id);
                  return sum + (d.value * (stage?.probability || 0) / 100);
                }, 0)
              )}
            </span>
          </div>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="flex-1 overflow-x-auto p-4">
        <div className="flex gap-4 h-full">
          {pipeline.stages.map(stage => (
            <StageColumn
              key={stage.id}
              stage={stage}
              deals={getDealsByStage(filteredDeals, stage.id)}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onDragStart={handleDragStart}
              onEditDeal={handleEditDeal}
              onViewDeal={handleViewDeal}
              onWinDeal={(id) => winDeal.mutate(id)}
              onLoseDeal={(id) => loseDeal.mutate({ id })}
              onAddDeal={handleAddDeal}
            />
          ))}

          {/* Won/Lost Summary */}
          <div className="flex-shrink-0 w-72 space-y-4">
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span className="font-semibold text-sm text-green-400">Ganhos</span>
                <Badge variant="secondary" className="bg-green-500/20 text-green-400">
                  {deals.filter(d => d.status === "won").length}
                </Badge>
              </div>
              <p className="text-sm text-green-400">
                {formatCurrency(deals.filter(d => d.status === "won").reduce((s, d) => s + d.value, 0))}
              </p>
            </div>
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <XCircle className="w-4 h-4 text-red-500" />
                <span className="font-semibold text-sm text-red-400">Perdidos</span>
                <Badge variant="secondary" className="bg-red-500/20 text-red-400">
                  {deals.filter(d => d.status === "lost").length}
                </Badge>
              </div>
              <p className="text-sm text-red-400">
                {formatCurrency(deals.filter(d => d.status === "lost").reduce((s, d) => s + d.value, 0))}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* View Deal Dialog (simplified) */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{selectedDeal?.title}</DialogTitle>
          </DialogHeader>
          {selectedDeal && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Valor</p>
                  <p className="text-lg font-semibold">{formatCurrency(selectedDeal.value)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Probabilidade</p>
                  <p className="text-lg font-semibold">{selectedDeal.probability}%</p>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Create/Edit Deal Dialog (simplified) */}
      <Dialog open={editDialogOpen || createDialogOpen} onOpenChange={(open) => {
        if (!open) {
          setEditDialogOpen(false);
          setCreateDialogOpen(false);
          setSelectedDeal(null);
        }
      }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editDialogOpen ? "Editar Deal" : "Novo Deal"}
            </DialogTitle>
            <DialogDescription>
              {editDialogOpen
                ? "Atualize as informações do deal abaixo."
                : "Preencha as informações para criar um novo deal."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">Título</Label>
              <Input
                id="title"
                value={dealForm.title}
                onChange={(e) => setDealForm({ ...dealForm, title: e.target.value })}
                placeholder="Nome do deal"
              />
            </div>
            <div>
              <Label htmlFor="value">Valor (R$)</Label>
              <Input
                id="value"
                type="number"
                value={dealForm.value}
                onChange={(e) => setDealForm({ ...dealForm, value: parseFloat(e.target.value) || 0 })}
                placeholder="0.00"
              />
            </div>
            {!editDialogOpen && (
              <>
                <div>
                  <Label htmlFor="contact_name">Nome do Contato</Label>
                  <Input
                    id="contact_name"
                    value={dealForm.contact_name}
                    onChange={(e) => setDealForm({ ...dealForm, contact_name: e.target.value })}
                    placeholder="João Silva"
                  />
                </div>
                <div>
                  <Label htmlFor="contact_email">Email do Contato</Label>
                  <Input
                    id="contact_email"
                    type="email"
                    value={dealForm.contact_email}
                    onChange={(e) => setDealForm({ ...dealForm, contact_email: e.target.value })}
                    placeholder="joao@empresa.com"
                  />
                </div>
              </>
            )}
            <div>
              <Label htmlFor="expected_close_date">Previsão de Fechamento</Label>
              <Input
                id="expected_close_date"
                type="date"
                value={dealForm.expected_close_date}
                onChange={(e) => setDealForm({ ...dealForm, expected_close_date: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setEditDialogOpen(false);
              setCreateDialogOpen(false);
            }}>
              Cancelar
            </Button>
            <Button onClick={handleSaveDeal}>
              {editDialogOpen ? "Salvar" : "Criar Deal"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Export as default for lazy loading
export default PipelinePage;
