/**
 * Pipeline de Vendas - Kanban Board
 * 
 * Visualização Kanban interativa do funil de vendas com:
 * - Múltiplos pipelines selecionáveis
 * - Colunas representando estágios
 * - Cards de deals draggáveis
 * - Métricas por estágio
 */

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import {
  Plus, GripVertical, MoreHorizontal, Edit, Eye, Phone,
  Mail, Calendar, DollarSign, Clock,
  CheckCircle2, XCircle,
  Filter, Search, RefreshCw, Settings, BarChart3
} from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

// Types
interface PipelineStage {
  id: string;
  name: string;
  order: number;
  color: string;
  probability: number;
  deal_ids: string[];
}

interface Pipeline {
  id: string;
  name: string;
  description: string;
  stages: PipelineStage[];
  is_default: boolean;
  deal_count: number;
  total_value: number;
}

interface Deal {
  id: string;
  title: string;
  value: number;
  stage_id: string;
  pipeline_id: string;
  lead_id: string;
  probability: number;
  expected_close_date: string | null;
  status: "open" | "won" | "lost";
  contact: {
    id: string;
    name: string;
    email: string;
    company?: string;
    avatar?: string;
  };
  tags: string[];
  created_at: string;
  updated_at: string;
  days_in_stage: number;
}

// Mock data para demonstração
const mockPipelines: Pipeline[] = [
  {
    id: "pip_1",
    name: "Pipeline Principal",
    description: "Funil de vendas padrão",
    is_default: true,
    deal_count: 25,
    total_value: 150000,
    stages: [
      { id: "stg_1", name: "Qualificação", order: 0, color: "#6366f1", probability: 10, deal_ids: [] },
      { id: "stg_2", name: "Proposta", order: 1, color: "#8b5cf6", probability: 30, deal_ids: [] },
      { id: "stg_3", name: "Negociação", order: 2, color: "#a855f7", probability: 60, deal_ids: [] },
      { id: "stg_4", name: "Fechamento", order: 3, color: "#d946ef", probability: 90, deal_ids: [] },
    ]
  },
  {
    id: "pip_2", 
    name: "Pipeline Enterprise",
    description: "Para grandes contas",
    is_default: false,
    deal_count: 8,
    total_value: 500000,
    stages: [
      { id: "stg_e1", name: "Descoberta", order: 0, color: "#0ea5e9", probability: 5, deal_ids: [] },
      { id: "stg_e2", name: "Apresentação", order: 1, color: "#06b6d4", probability: 20, deal_ids: [] },
      { id: "stg_e3", name: "POC", order: 2, color: "#14b8a6", probability: 50, deal_ids: [] },
      { id: "stg_e4", name: "Contrato", order: 3, color: "#10b981", probability: 80, deal_ids: [] },
      { id: "stg_e5", name: "Legal", order: 4, color: "#22c55e", probability: 95, deal_ids: [] },
    ]
  }
];

const mockDeals: Deal[] = [
  {
    id: "deal_1", title: "E-commerce Premium", value: 25000, stage_id: "stg_1", pipeline_id: "pip_1",
    lead_id: "lead_1", probability: 10, expected_close_date: "2025-01-15", status: "open",
    contact: { id: "c1", name: "Maria Santos", email: "maria@empresa.com", company: "TechShop Ltda" },
    tags: ["Urgente", "Enterprise"], created_at: "2024-11-20", updated_at: "2024-11-26", days_in_stage: 3
  },
  {
    id: "deal_2", title: "Dropshipping Starter", value: 5000, stage_id: "stg_1", pipeline_id: "pip_1",
    lead_id: "lead_2", probability: 15, expected_close_date: "2025-01-10", status: "open",
    contact: { id: "c2", name: "João Silva", email: "joao@loja.com", company: "Loja Virtual ME" },
    tags: ["Novo"], created_at: "2024-11-25", updated_at: "2024-11-26", days_in_stage: 1
  },
  {
    id: "deal_3", title: "Marketplace Integration", value: 45000, stage_id: "stg_2", pipeline_id: "pip_1",
    lead_id: "lead_3", probability: 35, expected_close_date: "2025-02-01", status: "open",
    contact: { id: "c3", name: "Ana Costa", email: "ana@market.com", company: "Super Market SA" },
    tags: ["Hot Lead"], created_at: "2024-11-15", updated_at: "2024-11-26", days_in_stage: 5
  },
  {
    id: "deal_4", title: "Sistema de Preços", value: 15000, stage_id: "stg_2", pipeline_id: "pip_1",
    lead_id: "lead_4", probability: 40, expected_close_date: "2025-01-20", status: "open",
    contact: { id: "c4", name: "Pedro Lima", email: "pedro@varejo.com", company: "Varejo Express" },
    tags: [], created_at: "2024-11-18", updated_at: "2024-11-24", days_in_stage: 4
  },
  {
    id: "deal_5", title: "Automação WhatsApp", value: 35000, stage_id: "stg_3", pipeline_id: "pip_1",
    lead_id: "lead_5", probability: 65, expected_close_date: "2024-12-20", status: "open",
    contact: { id: "c5", name: "Carla Ferreira", email: "carla@atacado.com", company: "Atacadão Digital" },
    tags: ["Urgente", "Hot Lead"], created_at: "2024-11-10", updated_at: "2024-11-26", days_in_stage: 2
  },
  {
    id: "deal_6", title: "Contrato Anual Pro", value: 28000, stage_id: "stg_4", pipeline_id: "pip_1",
    lead_id: "lead_6", probability: 90, expected_close_date: "2024-11-30", status: "open",
    contact: { id: "c6", name: "Roberto Mendes", email: "roberto@megastore.com", company: "MegaStore" },
    tags: ["VIP"], created_at: "2024-11-01", updated_at: "2024-11-26", days_in_stage: 1
  },
];

// Utility functions
const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format(value);
};

const getTagColor = (tag: string): string => {
  const colors: Record<string, string> = {
    "Urgente": "bg-red-500/20 text-red-400 border-red-500/30",
    "Hot Lead": "bg-orange-500/20 text-orange-400 border-orange-500/30",
    "Enterprise": "bg-purple-500/20 text-purple-400 border-purple-500/30",
    "VIP": "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    "Novo": "bg-green-500/20 text-green-400 border-green-500/30",
  };
  return colors[tag] || "bg-muted text-muted-foreground border-border";
};

// Components
const DealCard = ({ 
  deal, 
  onDragStart,
  onEdit,
  onView 
}: { 
  deal: Deal;
  onDragStart: (e: React.DragEvent, deal: Deal) => void;
  onEdit: (deal: Deal) => void;
  onView: (deal: Deal) => void;
}) => {
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
            <DropdownMenuItem className="text-green-500">
              <CheckCircle2 className="mr-2 h-4 w-4" /> Marcar como ganho
            </DropdownMenuItem>
            <DropdownMenuItem className="text-red-500">
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
                <span>{deal.days_in_stage}d</span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>{deal.days_in_stage} dias neste estágio</p>
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

const StageColumn = ({
  stage,
  deals,
  onDragOver,
  onDrop,
  onDragStart,
  onEditDeal,
  onViewDeal,
  onAddDeal
}: {
  stage: PipelineStage;
  deals: Deal[];
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent, stageId: string) => void;
  onDragStart: (e: React.DragEvent, deal: Deal) => void;
  onEditDeal: (deal: Deal) => void;
  onViewDeal: (deal: Deal) => void;
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
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

export const Pipeline = () => {
  const [loading, setLoading] = useState(true);
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [draggedDeal, setDraggedDeal] = useState<Deal | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);

  // Load data
  useEffect(() => {
    const loadData = async () => {
      // Simular chamada API
      await new Promise(resolve => setTimeout(resolve, 1000));
      setPipelines(mockPipelines);
      setSelectedPipeline(mockPipelines[0]);
      setDeals(mockDeals);
      setLoading(false);
    };
    loadData();
  }, []);

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

    setDeals(prev => prev.map(deal => 
      deal.id === draggedDeal.id 
        ? { ...deal, stage_id: stageId, days_in_stage: 0 }
        : deal
    ));
    setDraggedDeal(null);
  }, [draggedDeal]);

  // Actions
  const handleViewDeal = (deal: Deal) => {
    setSelectedDeal(deal);
    setViewDialogOpen(true);
  };

  const handleEditDeal = (deal: Deal) => {
    // TODO: Abrir modal de edição
    console.log("Edit deal:", deal);
  };

  const handleAddDeal = (stageId: string) => {
    // TODO: Abrir modal de criação
    console.log("Add deal to stage:", stageId);
  };

  // Filter deals by pipeline and search
  const filteredDeals = deals.filter(deal => {
    if (selectedPipeline && deal.pipeline_id !== selectedPipeline.id) return false;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      return (
        deal.title.toLowerCase().includes(term) ||
        deal.contact.name.toLowerCase().includes(term) ||
        deal.contact.company?.toLowerCase().includes(term)
      );
    }
    return true;
  });

  // Get deals per stage
  const getDealsByStage = (stageId: string) => 
    filteredDeals.filter(deal => deal.stage_id === stageId);

  // Loading state
  if (loading) {
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
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" /> Novo Deal
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <Select
            value={selectedPipeline?.id}
            onValueChange={(value) => {
              const pipeline = pipelines.find(p => p.id === value);
              setSelectedPipeline(pipeline || null);
            }}
          >
            <SelectTrigger className="w-60">
              <SelectValue placeholder="Selecione um pipeline" />
            </SelectTrigger>
            <SelectContent>
              {pipelines.map(pipeline => (
                <SelectItem key={pipeline.id} value={pipeline.id}>
                  <div className="flex items-center justify-between w-full">
                    <span>{pipeline.name}</span>
                    {pipeline.is_default && (
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
        {selectedPipeline && (
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
                    const stage = selectedPipeline.stages.find(s => s.id === d.stage_id);
                    return sum + (d.value * (stage?.probability || 0) / 100);
                  }, 0)
                )}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Kanban Board */}
      <div className="flex-1 overflow-x-auto p-4">
        <div className="flex gap-4 h-full">
          {selectedPipeline?.stages.map(stage => (
            <StageColumn
              key={stage.id}
              stage={stage}
              deals={getDealsByStage(stage.id)}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onDragStart={handleDragStart}
              onEditDeal={handleEditDeal}
              onViewDeal={handleViewDeal}
              onAddDeal={handleAddDeal}
            />
          ))}

          {/* Coluna de Won/Lost */}
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

      {/* View Deal Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{selectedDeal?.title}</DialogTitle>
          </DialogHeader>
          {selectedDeal && (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <Avatar className="h-12 w-12">
                  <AvatarImage src={selectedDeal.contact.avatar} />
                  <AvatarFallback className="bg-primary/10 text-primary">
                    {selectedDeal.contact.name.split(" ").map(n => n[0]).join("")}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-semibold">{selectedDeal.contact.name}</p>
                  <p className="text-sm text-muted-foreground">{selectedDeal.contact.company}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Valor</p>
                  <p className="text-lg font-semibold">{formatCurrency(selectedDeal.value)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Probabilidade</p>
                  <p className="text-lg font-semibold">{selectedDeal.probability}%</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Data prevista</p>
                  <p className="font-medium">
                    {selectedDeal.expected_close_date 
                      ? new Date(selectedDeal.expected_close_date).toLocaleDateString("pt-BR")
                      : "-"}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Dias no estágio</p>
                  <p className="font-medium">{selectedDeal.days_in_stage} dias</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {selectedDeal.tags.map(tag => (
                  <Badge key={tag} variant="outline" className={getTagColor(tag)}>
                    {tag}
                  </Badge>
                ))}
              </div>

              <div className="flex gap-2 pt-4">
                <Button variant="outline" className="flex-1">
                  <Phone className="h-4 w-4 mr-2" /> Ligar
                </Button>
                <Button variant="outline" className="flex-1">
                  <Mail className="h-4 w-4 mr-2" /> Email
                </Button>
                <Button className="flex-1">
                  <Edit className="h-4 w-4 mr-2" /> Editar
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Pipeline;
