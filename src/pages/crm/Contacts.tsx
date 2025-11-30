/**
 * CRM Contacts - Lista de Contatos
 * 
 * Gerenciamento completo de contatos com:
 * - Listagem paginada com filtros
 * - Busca por nome, email, empresa
 * - Tags e segmentação
 * - Ações em lote
 * - Importação/Exportação
 */

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "@/components/ui/table";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, 
  DropdownMenuSeparator, DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import {
  Users, UserPlus, Search, MoreHorizontal, Edit, Trash2,
  Mail, Phone, MapPin, Calendar, Tag, Download, Upload,
  ChevronLeft, ChevronRight, ArrowUpDown, Eye, MessageSquare,
  Star, StarOff, CheckCircle2, RefreshCw
} from "lucide-react";

// Types
interface Contact {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  company: string | null;
  position: string | null;
  city: string | null;
  state: string | null;
  source: string;
  status: "active" | "inactive" | "unsubscribed";
  is_subscribed: boolean;
  is_favorite: boolean;
  tags: string[];
  notes: string | null;
  created_at: string;
  updated_at: string;
  last_activity: string | null;
  lead_count: number;
  deal_count: number;
}

interface ContactFilters {
  status: string;
  source: string;
  tag: string;
  subscribed: string;
}

// Mock data
const mockContacts: Contact[] = [
  {
    id: "c1", first_name: "Maria", last_name: "Santos", email: "maria@techshop.com",
    phone: "(11) 99999-1111", company: "TechShop Ltda", position: "CEO",
    city: "São Paulo", state: "SP", source: "Website", status: "active",
    is_subscribed: true, is_favorite: true, tags: ["VIP", "Enterprise"],
    notes: "Cliente desde 2023", created_at: "2024-01-15", updated_at: "2024-11-26",
    last_activity: "2024-11-25", lead_count: 3, deal_count: 2
  },
  {
    id: "c2", first_name: "João", last_name: "Silva", email: "joao@loja.com",
    phone: "(11) 98888-2222", company: "Loja Virtual ME", position: "Proprietário",
    city: "Rio de Janeiro", state: "RJ", source: "Indicação", status: "active",
    is_subscribed: true, is_favorite: false, tags: ["Starter"],
    notes: null, created_at: "2024-06-10", updated_at: "2024-11-20",
    last_activity: "2024-11-18", lead_count: 1, deal_count: 1
  },
  {
    id: "c3", first_name: "Ana", last_name: "Costa", email: "ana@supermarket.com",
    phone: "(21) 97777-3333", company: "Super Market SA", position: "Diretora Comercial",
    city: "Belo Horizonte", state: "MG", source: "Evento", status: "active",
    is_subscribed: true, is_favorite: true, tags: ["Enterprise", "Hot"],
    notes: "Conheceu no evento de e-commerce", created_at: "2024-03-20", updated_at: "2024-11-26",
    last_activity: "2024-11-26", lead_count: 2, deal_count: 3
  },
  {
    id: "c4", first_name: "Pedro", last_name: "Lima", email: "pedro@varejo.com",
    phone: "(31) 96666-4444", company: "Varejo Express", position: "Gerente",
    city: "Curitiba", state: "PR", source: "LinkedIn", status: "active",
    is_subscribed: false, is_favorite: false, tags: [],
    notes: null, created_at: "2024-08-15", updated_at: "2024-11-15",
    last_activity: "2024-11-10", lead_count: 1, deal_count: 0
  },
  {
    id: "c5", first_name: "Carla", last_name: "Ferreira", email: "carla@atacado.com",
    phone: "(41) 95555-5555", company: "Atacadão Digital", position: "COO",
    city: "Porto Alegre", state: "RS", source: "Google Ads", status: "active",
    is_subscribed: true, is_favorite: true, tags: ["VIP", "Urgente"],
    notes: "Interessada em automação", created_at: "2024-02-28", updated_at: "2024-11-26",
    last_activity: "2024-11-26", lead_count: 4, deal_count: 2
  },
  {
    id: "c6", first_name: "Roberto", last_name: "Mendes", email: "roberto@megastore.com",
    phone: "(51) 94444-6666", company: "MegaStore", position: "Fundador",
    city: "Florianópolis", state: "SC", source: "Parceiro", status: "inactive",
    is_subscribed: true, is_favorite: false, tags: ["Enterprise"],
    notes: "Pausou assinatura temporariamente", created_at: "2023-11-10", updated_at: "2024-10-01",
    last_activity: "2024-09-15", lead_count: 2, deal_count: 1
  },
  {
    id: "c7", first_name: "Fernanda", last_name: "Oliveira", email: "fernanda@ecommerce.com",
    phone: "(47) 93333-7777", company: "E-commerce Pro", position: "Marketing",
    city: "Campinas", state: "SP", source: "Instagram", status: "active",
    is_subscribed: true, is_favorite: false, tags: ["Marketing"],
    notes: null, created_at: "2024-09-05", updated_at: "2024-11-22",
    last_activity: "2024-11-20", lead_count: 1, deal_count: 0
  },
  {
    id: "c8", first_name: "Lucas", last_name: "Rodrigues", email: "lucas@dropship.com",
    phone: null, company: "DropShip Brasil", position: "Analista",
    city: "Recife", state: "PE", source: "Website", status: "unsubscribed",
    is_subscribed: false, is_favorite: false, tags: [],
    notes: "Cancelou inscrição em 10/2024", created_at: "2024-04-12", updated_at: "2024-10-15",
    last_activity: "2024-10-10", lead_count: 0, deal_count: 0
  },
];

const sources = ["Website", "Indicação", "Evento", "LinkedIn", "Google Ads", "Instagram", "Parceiro", "Outro"];
const allTags = ["VIP", "Enterprise", "Starter", "Hot", "Urgente", "Marketing"];

// Utility functions
const getStatusBadge = (status: string) => {
  const styles: Record<string, string> = {
    active: "bg-green-500/20 text-green-400 border-green-500/30",
    inactive: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    unsubscribed: "bg-muted text-muted-foreground border-border"
  };
  const labels: Record<string, string> = {
    active: "Ativo",
    inactive: "Inativo",
    unsubscribed: "Descadastrado"
  };
  return <Badge variant="outline" className={styles[status]}>{labels[status]}</Badge>;
};

const getTagColor = (tag: string): string => {
  const colors: Record<string, string> = {
    "VIP": "bg-yellow-500/20 text-yellow-400",
    "Enterprise": "bg-purple-500/20 text-purple-400",
    "Starter": "bg-blue-500/20 text-blue-400",
    "Hot": "bg-red-500/20 text-red-400",
    "Urgente": "bg-orange-500/20 text-orange-400",
    "Marketing": "bg-green-500/20 text-green-400",
  };
  return colors[tag] || "bg-muted text-muted-foreground";
};

export const Contacts = () => {
  const [loading, setLoading] = useState(true);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState<ContactFilters>({
    status: "all",
    source: "all",
    tag: "all",
    subscribed: "all"
  });
  const [selectedContacts, setSelectedContacts] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<keyof Contact>("created_at");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [currentPage, setCurrentPage] = useState(1);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const itemsPerPage = 10;

  // Form state for new contact
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    company: "",
    position: "",
    city: "",
    state: "",
    source: "Website",
    notes: "",
    tags: [] as string[]
  });

  // Load data
  useEffect(() => {
    const loadData = async () => {
      await new Promise(resolve => setTimeout(resolve, 800));
      setContacts(mockContacts);
      setLoading(false);
    };
    loadData();
  }, []);

  // Filter and sort contacts
  const filteredContacts = useMemo(() => {
    let result = [...contacts];

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(c =>
        c.first_name.toLowerCase().includes(term) ||
        c.last_name.toLowerCase().includes(term) ||
        c.email.toLowerCase().includes(term) ||
        c.company?.toLowerCase().includes(term)
      );
    }

    // Status filter
    if (filters.status !== "all") {
      result = result.filter(c => c.status === filters.status);
    }

    // Source filter
    if (filters.source !== "all") {
      result = result.filter(c => c.source === filters.source);
    }

    // Tag filter
    if (filters.tag !== "all") {
      result = result.filter(c => c.tags.includes(filters.tag));
    }

    // Subscribed filter
    if (filters.subscribed !== "all") {
      result = result.filter(c => 
        filters.subscribed === "yes" ? c.is_subscribed : !c.is_subscribed
      );
    }

    // Sort
    result.sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;
      const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return sortDirection === "asc" ? comparison : -comparison;
    });

    return result;
  }, [contacts, searchTerm, filters, sortField, sortDirection]);

  // Pagination
  const totalPages = Math.ceil(filteredContacts.length / itemsPerPage);
  const paginatedContacts = filteredContacts.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Selection handlers
  const toggleSelectAll = () => {
    if (selectedContacts.size === paginatedContacts.length) {
      setSelectedContacts(new Set());
    } else {
      setSelectedContacts(new Set(paginatedContacts.map(c => c.id)));
    }
  };

  const toggleSelectContact = (id: string) => {
    const newSelection = new Set(selectedContacts);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedContacts(newSelection);
  };

  // Sort handler
  const handleSort = (field: keyof Contact) => {
    if (sortField === field) {
      setSortDirection(prev => prev === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  // Action handlers
  const handleView = (contact: Contact) => {
    setSelectedContact(contact);
    setViewDialogOpen(true);
  };

  const handleToggleFavorite = (id: string) => {
    setContacts(prev => prev.map(c =>
      c.id === id ? { ...c, is_favorite: !c.is_favorite } : c
    ));
  };

  const handleDelete = (id: string) => {
    if (confirm("Tem certeza que deseja excluir este contato?")) {
      setContacts(prev => prev.filter(c => c.id !== id));
      setSelectedContacts(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }
  };

  const handleBulkDelete = () => {
    if (confirm(`Tem certeza que deseja excluir ${selectedContacts.size} contatos?`)) {
      setContacts(prev => prev.filter(c => !selectedContacts.has(c.id)));
      setSelectedContacts(new Set());
    }
  };

  const handleCreateContact = () => {
    const newContact: Contact = {
      id: `c_${Date.now()}`,
      ...formData,
      status: "active",
      is_subscribed: true,
      is_favorite: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_activity: null,
      lead_count: 0,
      deal_count: 0
    };
    setContacts(prev => [newContact, ...prev]);
    setCreateDialogOpen(false);
    setFormData({
      first_name: "", last_name: "", email: "", phone: "",
      company: "", position: "", city: "", state: "",
      source: "Website", notes: "", tags: []
    });
  };

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex justify-between items-center">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <Card>
          <CardContent className="p-0">
            <div className="space-y-2 p-4">
              {[1, 2, 3, 4, 5].map(i => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Users className="h-6 w-6" /> Contatos
          </h1>
          <p className="text-muted-foreground">
            {filteredContacts.length} contatos encontrados
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Upload className="h-4 w-4 mr-2" /> Importar
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" /> Exportar
          </Button>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <UserPlus className="h-4 w-4 mr-2" /> Novo Contato
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Novo Contato</DialogTitle>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="first_name">Nome *</Label>
                    <Input
                      id="first_name"
                      value={formData.first_name}
                      onChange={e => setFormData(prev => ({ ...prev, first_name: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last_name">Sobrenome *</Label>
                    <Input
                      id="last_name"
                      value={formData.last_name}
                      onChange={e => setFormData(prev => ({ ...prev, last_name: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={e => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="phone">Telefone</Label>
                    <Input
                      id="phone"
                      value={formData.phone}
                      onChange={e => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="source">Origem</Label>
                    <Select 
                      value={formData.source} 
                      onValueChange={v => setFormData(prev => ({ ...prev, source: v }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {sources.map(s => (
                          <SelectItem key={s} value={s}>{s}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="company">Empresa</Label>
                    <Input
                      id="company"
                      value={formData.company}
                      onChange={e => setFormData(prev => ({ ...prev, company: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="position">Cargo</Label>
                    <Input
                      id="position"
                      value={formData.position}
                      onChange={e => setFormData(prev => ({ ...prev, position: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notes">Observações</Label>
                  <Textarea
                    id="notes"
                    value={formData.notes}
                    onChange={e => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button 
                  onClick={handleCreateContact}
                  disabled={!formData.first_name || !formData.last_name || !formData.email}
                >
                  Criar Contato
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por nome, email ou empresa..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={filters.status} onValueChange={v => setFilters(prev => ({ ...prev, status: v }))}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos status</SelectItem>
                <SelectItem value="active">Ativos</SelectItem>
                <SelectItem value="inactive">Inativos</SelectItem>
                <SelectItem value="unsubscribed">Descadastrados</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filters.source} onValueChange={v => setFilters(prev => ({ ...prev, source: v }))}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Origem" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas origens</SelectItem>
                {sources.map(s => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filters.tag} onValueChange={v => setFilters(prev => ({ ...prev, tag: v }))}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Tag" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas tags</SelectItem>
                {allTags.map(t => (
                  <SelectItem key={t} value={t}>{t}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="ghost" size="icon" onClick={() => {
              setFilters({ status: "all", source: "all", tag: "all", subscribed: "all" });
              setSearchTerm("");
            }}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Bulk Actions */}
      {selectedContacts.size > 0 && (
        <div className="bg-primary/5 border rounded-lg p-3 flex items-center justify-between">
          <span className="text-sm font-medium">
            {selectedContacts.size} contato(s) selecionado(s)
          </span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Tag className="h-4 w-4 mr-2" /> Adicionar Tag
            </Button>
            <Button variant="outline" size="sm">
              <Mail className="h-4 w-4 mr-2" /> Enviar Email
            </Button>
            <Button variant="destructive" size="sm" onClick={handleBulkDelete}>
              <Trash2 className="h-4 w-4 mr-2" /> Excluir
            </Button>
          </div>
        </div>
      )}

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <Checkbox
                    checked={selectedContacts.size === paginatedContacts.length && paginatedContacts.length > 0}
                    onCheckedChange={toggleSelectAll}
                  />
                </TableHead>
                <TableHead className="w-12"></TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort("first_name")}>
                  <div className="flex items-center gap-1">
                    Contato <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead>Empresa</TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort("source")}>
                  <div className="flex items-center gap-1">
                    Origem <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead>Tags</TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort("status")}>
                  <div className="flex items-center gap-1">
                    Status <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort("created_at")}>
                  <div className="flex items-center gap-1">
                    Criado em <ArrowUpDown className="h-4 w-4" />
                  </div>
                </TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedContacts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-12 text-muted-foreground">
                    Nenhum contato encontrado
                  </TableCell>
                </TableRow>
              ) : (
                paginatedContacts.map(contact => (
                  <TableRow key={contact.id} className="group">
                    <TableCell>
                      <Checkbox
                        checked={selectedContacts.has(contact.id)}
                        onCheckedChange={() => toggleSelectContact(contact.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => handleToggleFavorite(contact.id)}
                      >
                        {contact.is_favorite ? (
                          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                        ) : (
                          <StarOff className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100" />
                        )}
                      </Button>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-9 w-9">
                          <AvatarFallback className="bg-primary/10 text-primary text-sm">
                            {contact.first_name[0]}{contact.last_name[0]}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{contact.first_name} {contact.last_name}</p>
                          <p className="text-sm text-muted-foreground">{contact.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {contact.company ? (
                        <div>
                          <p className="font-medium">{contact.company}</p>
                          {contact.position && (
                            <p className="text-sm text-muted-foreground">{contact.position}</p>
                          )}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{contact.source}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {contact.tags.slice(0, 2).map(tag => (
                          <Badge key={tag} variant="secondary" className={`text-xs ${getTagColor(tag)}`}>
                            {tag}
                          </Badge>
                        ))}
                        {contact.tags.length > 2 && (
                          <Badge variant="secondary" className="text-xs">
                            +{contact.tags.length - 2}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(contact.status)}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(contact.created_at).toLocaleDateString("pt-BR")}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleView(contact)}>
                            <Eye className="mr-2 h-4 w-4" /> Ver detalhes
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Edit className="mr-2 h-4 w-4" /> Editar
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem>
                            <Mail className="mr-2 h-4 w-4" /> Enviar email
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <MessageSquare className="mr-2 h-4 w-4" /> Enviar WhatsApp
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem 
                            className="text-destructive"
                            onClick={() => handleDelete(contact.id)}
                          >
                            <Trash2 className="mr-2 h-4 w-4" /> Excluir
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Mostrando {Math.min((currentPage - 1) * itemsPerPage + 1, filteredContacts.length)} a{" "}
          {Math.min(currentPage * itemsPerPage, filteredContacts.length)} de {filteredContacts.length} resultados
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(prev => prev - 1)}
          >
            <ChevronLeft className="h-4 w-4" /> Anterior
          </Button>
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const page = currentPage <= 3 ? i + 1 : currentPage - 2 + i;
              if (page > totalPages) return null;
              return (
                <Button
                  key={page}
                  variant={page === currentPage ? "default" : "outline"}
                  size="sm"
                  className="w-8"
                  onClick={() => setCurrentPage(page)}
                >
                  {page}
                </Button>
              );
            })}
          </div>
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(prev => prev + 1)}
          >
            Próxima <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* View Contact Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Detalhes do Contato</DialogTitle>
          </DialogHeader>
          {selectedContact && (
            <div className="space-y-6">
              {/* Contact header */}
              <div className="flex items-center gap-4">
                <Avatar className="h-16 w-16">
                  <AvatarFallback className="bg-primary/10 text-primary text-xl">
                    {selectedContact.first_name[0]}{selectedContact.last_name[0]}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <h3 className="text-xl font-semibold">
                    {selectedContact.first_name} {selectedContact.last_name}
                  </h3>
                  {selectedContact.company && (
                    <p className="text-muted-foreground">
                      {selectedContact.position} @ {selectedContact.company}
                    </p>
                  )}
                  <div className="flex items-center gap-2 mt-1">
                    {getStatusBadge(selectedContact.status)}
                    {selectedContact.is_subscribed && (
                      <Badge variant="outline" className="bg-green-50 text-green-700">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> Inscrito
                      </Badge>
                    )}
                  </div>
                </div>
              </div>

              <Separator />

              {/* Contact info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <span>{selectedContact.email}</span>
                </div>
                {selectedContact.phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <span>{selectedContact.phone}</span>
                  </div>
                )}
                {(selectedContact.city || selectedContact.state) && (
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-muted-foreground" />
                    <span>
                      {[selectedContact.city, selectedContact.state].filter(Boolean).join(", ")}
                    </span>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span>Criado em {new Date(selectedContact.created_at).toLocaleDateString("pt-BR")}</span>
                </div>
              </div>

              {/* Tags */}
              {selectedContact.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {selectedContact.tags.map(tag => (
                    <Badge key={tag} className={getTagColor(tag)}>
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold">{selectedContact.lead_count}</p>
                    <p className="text-sm text-muted-foreground">Leads</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold">{selectedContact.deal_count}</p>
                    <p className="text-sm text-muted-foreground">Deals</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold">{selectedContact.source}</p>
                    <p className="text-sm text-muted-foreground">Origem</p>
                  </CardContent>
                </Card>
              </div>

              {/* Notes */}
              {selectedContact.notes && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">Observações</h4>
                  <p className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
                    {selectedContact.notes}
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1">
                  <Phone className="h-4 w-4 mr-2" /> Ligar
                </Button>
                <Button variant="outline" className="flex-1">
                  <Mail className="h-4 w-4 mr-2" /> Email
                </Button>
                <Button variant="outline" className="flex-1">
                  <MessageSquare className="h-4 w-4 mr-2" /> WhatsApp
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Contacts;
