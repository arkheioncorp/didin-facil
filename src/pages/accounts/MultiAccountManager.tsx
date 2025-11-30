import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import {
  Plus,
  Trash2,
  Star,
  Settings,
  RefreshCw,
  Users,
  Instagram,
  Youtube,
  Video,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ExternalLink,
  MoreVertical,
  ArrowRight,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { api } from '@/lib/api';

interface Account {
  id: string;
  platform: string;
  username: string;
  display_name?: string;
  profile_url?: string;
  profile_image?: string;
  status: string;
  is_primary: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
  last_used_at?: string;
  metrics: {
    followers?: number;
    following?: number;
    posts?: number;
    engagement_rate?: number;
  };
  metadata: Record<string, unknown>;
}

interface AccountSummary {
  total_accounts: number;
  total_followers: number;
  by_platform: Record<string, { count: number; active: number; needs_reauth: number }>;
  platforms: string[];
}

const platformIcons: Record<string, React.ReactNode> = {
  instagram: <Instagram className="h-5 w-5" />,
  youtube: <Youtube className="h-5 w-5" />,
  tiktok: <Video className="h-5 w-5" />,
};

const platformBgColors: Record<string, string> = {
  instagram: 'bg-gradient-to-r from-purple-500 to-pink-500',
  youtube: 'bg-red-500',
  tiktok: 'bg-black',
};

const statusConfig: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  active: { label: 'Ativo', icon: <CheckCircle className="h-4 w-4" />, color: 'text-green-500' },
  inactive: { label: 'Inativo', icon: <XCircle className="h-4 w-4" />, color: 'text-muted-foreground' },
  suspended: { label: 'Suspenso', icon: <XCircle className="h-4 w-4" />, color: 'text-red-500' },
  needs_reauth: { label: 'Reautenticar', icon: <AlertTriangle className="h-4 w-4" />, color: 'text-yellow-500' },
};

function SummaryCard({ summary }: { summary: AccountSummary }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total de Contas</CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{summary.total_accounts}</div>
          <p className="text-xs text-muted-foreground">
            {summary.platforms.length} plataformas conectadas
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total de Seguidores</CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {summary.total_followers.toLocaleString('pt-BR')}
          </div>
          <p className="text-xs text-muted-foreground">
            Em todas as plataformas
          </p>
        </CardContent>
      </Card>

      {Object.entries(summary.by_platform).slice(0, 2).map(([platform, data]) => (
        <Card key={platform}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium capitalize">{platform}</CardTitle>
            <div className={`p-1.5 rounded text-white ${platformBgColors[platform] || 'bg-muted-foreground'}`}>
              {platformIcons[platform]}
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.count}</div>
            <p className="text-xs text-muted-foreground">
              {data.active} ativas
              {data.needs_reauth > 0 && `, ${data.needs_reauth} precisam reautenticar`}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function AccountCard({
  account,
  onSwitch,
  onSetPrimary,
  onEdit,
  onDelete,
}: {
  account: Account;
  onSwitch: (id: string) => void;
  onSetPrimary: (id: string) => void;
  onEdit: (account: Account) => void;
  onDelete: (id: string) => void;
}) {
  const status = statusConfig[account.status] || statusConfig.inactive;

  return (
    <Card className="group hover:shadow-md transition-all">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <Avatar className="h-12 w-12 ring-2 ring-offset-2 ring-muted">
            <AvatarImage src={account.profile_image} alt={account.username} />
            <AvatarFallback className={`${platformBgColors[account.platform]} text-white`}>
              {account.username.slice(0, 2).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <CardTitle className="text-base truncate">
                @{account.username}
              </CardTitle>
              {account.is_primary && (
                <Badge variant="secondary" className="shrink-0">
                  <Star className="h-3 w-3 mr-1 fill-yellow-500 text-yellow-500" />
                  Principal
                </Badge>
              )}
            </div>
            <CardDescription className="flex items-center gap-2">
              <span className={`flex items-center gap-1 ${status.color}`}>
                {status.icon}
                {status.label}
              </span>
              <span>•</span>
              <span className="capitalize">{account.platform}</span>
            </CardDescription>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onSwitch(account.id)}>
                <ArrowRight className="h-4 w-4 mr-2" />
                Alternar para esta conta
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onSetPrimary(account.id)}>
                <Star className="h-4 w-4 mr-2" />
                Definir como principal
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onEdit(account)}>
                <Settings className="h-4 w-4 mr-2" />
                Editar
              </DropdownMenuItem>
              {account.profile_url && (
                <DropdownMenuItem asChild>
                  <a href={account.profile_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Ver perfil
                  </a>
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={() => onDelete(account.id)}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Remover
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        {account.metrics && Object.keys(account.metrics).length > 0 ? (
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-lg font-bold">
                {(account.metrics.followers || 0).toLocaleString('pt-BR')}
              </p>
              <p className="text-xs text-muted-foreground">Seguidores</p>
            </div>
            <div>
              <p className="text-lg font-bold">
                {(account.metrics.posts || 0).toLocaleString('pt-BR')}
              </p>
              <p className="text-xs text-muted-foreground">Posts</p>
            </div>
            <div>
              <p className="text-lg font-bold">
                {(account.metrics.engagement_rate || 0).toFixed(1)}%
              </p>
              <p className="text-xs text-muted-foreground">Engajamento</p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-2">
            Métricas não disponíveis
          </p>
        )}
      </CardContent>
      {account.last_used_at && (
        <CardFooter className="pt-0 text-xs text-muted-foreground">
          Último uso: {new Date(account.last_used_at).toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </CardFooter>
      )}
    </Card>
  );
}

function AddAccountDialog({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    platform: 'instagram',
    username: '',
    display_name: '',
    profile_url: '',
    is_primary: false,
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      return api.post('/accounts', formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast.success('Conta adicionada com sucesso!');
      onClose();
      setFormData({
        platform: 'instagram',
        username: '',
        display_name: '',
        profile_url: '',
        is_primary: false,
      });
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Erro ao adicionar conta');
    },
  });

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Adicionar Conta</DialogTitle>
          <DialogDescription>
            Conecte uma nova conta de rede social
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
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
                <SelectItem value="instagram">
                  <div className="flex items-center gap-2">
                    <Instagram className="h-4 w-4" />
                    Instagram
                  </div>
                </SelectItem>
                <SelectItem value="tiktok">
                  <div className="flex items-center gap-2">
                    <Video className="h-4 w-4" />
                    TikTok
                  </div>
                </SelectItem>
                <SelectItem value="youtube">
                  <div className="flex items-center gap-2">
                    <Youtube className="h-4 w-4" />
                    YouTube
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="username">Nome de Usuário</Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                @
              </span>
              <Input
                id="username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                placeholder="username"
                className="pl-8"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="display_name">Nome de Exibição (opcional)</Label>
            <Input
              id="display_name"
              value={formData.display_name}
              onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
              placeholder="Nome da conta"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="profile_url">URL do Perfil (opcional)</Label>
            <Input
              id="profile_url"
              value={formData.profile_url}
              onChange={(e) => setFormData({ ...formData, profile_url: e.target.value })}
              placeholder="https://instagram.com/username"
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Conta Principal</Label>
              <p className="text-xs text-muted-foreground">
                Usar como padrão para esta plataforma
              </p>
            </div>
            <Switch
              checked={formData.is_primary}
              onCheckedChange={(checked) => setFormData({ ...formData, is_primary: checked })}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            onClick={() => createMutation.mutate()}
            disabled={!formData.username || createMutation.isPending}
          >
            {createMutation.isPending ? 'Adicionando...' : 'Adicionar'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function MultiAccountManager() {
  const queryClient = useQueryClient();
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [platformFilter, setPlatformFilter] = useState<string>('all');

  const { data: accounts, isLoading } = useQuery({
    queryKey: ['accounts', platformFilter],
    queryFn: async () => {
      const params = platformFilter !== 'all' ? `?platform=${platformFilter}` : '';
      const response = await api.get<{ accounts: Account[] }>(`/accounts${params}`);
      return response.data.accounts;
    },
  });

  const { data: summary } = useQuery({
    queryKey: ['accounts', 'summary'],
    queryFn: async () => {
      const response = await api.get<AccountSummary>('/accounts/summary');
      return response.data;
    },
  });

  const switchMutation = useMutation({
    mutationFn: (id: string) => api.post(`/accounts/${id}/switch`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast.success('Conta alterada!');
    },
    onError: () => {
      toast.error('Erro ao alternar conta');
    },
  });

  const setPrimaryMutation = useMutation({
    mutationFn: (id: string) => api.post(`/accounts/${id}/set-primary`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast.success('Conta definida como principal!');
    },
    onError: () => {
      toast.error('Erro ao definir conta principal');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/accounts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast.success('Conta removida!');
      setDeleteDialogOpen(false);
    },
    onError: () => {
      toast.error('Erro ao remover conta');
    },
  });

  const handleDelete = (id: string) => {
    setSelectedAccountId(id);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (selectedAccountId) {
      deleteMutation.mutate(selectedAccountId);
    }
  };

  const groupedAccounts = accounts?.reduce((acc, account) => {
    const platform = account.platform;
    if (!acc[platform]) {
      acc[platform] = [];
    }
    acc[platform].push(account);
    return acc;
  }, {} as Record<string, Account[]>);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Users className="h-8 w-8" />
            Multi-Account
          </h1>
          <p className="text-muted-foreground">
            Gerencie múltiplas contas de redes sociais
          </p>
        </div>
        <Button onClick={() => setAddDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Adicionar Conta
        </Button>
      </div>

      {/* Summary */}
      {summary && <SummaryCard summary={summary} />}

      {/* Filters */}
      <div className="flex items-center gap-4">
        <Select value={platformFilter} onValueChange={setPlatformFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filtrar por plataforma" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as plataformas</SelectItem>
            <SelectItem value="instagram">Instagram</SelectItem>
            <SelectItem value="tiktok">TikTok</SelectItem>
            <SelectItem value="youtube">YouTube</SelectItem>
          </SelectContent>
        </Select>
        <Button
          variant="outline"
          size="icon"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['accounts'] })}
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Accounts */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array(6).fill(0).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Skeleton className="h-12 w-12 rounded-full" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-3 w-16" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : platformFilter === 'all' && groupedAccounts ? (
        <Tabs defaultValue={Object.keys(groupedAccounts)[0] || 'instagram'}>
          <TabsList>
            {Object.keys(groupedAccounts).map((platform) => (
              <TabsTrigger key={platform} value={platform} className="capitalize">
                <span className="flex items-center gap-2">
                  {platformIcons[platform]}
                  {platform}
                  <Badge variant="secondary" className="ml-1">
                    {groupedAccounts[platform].length}
                  </Badge>
                </span>
              </TabsTrigger>
            ))}
          </TabsList>

          {Object.entries(groupedAccounts).map(([platform, platformAccounts]) => (
            <TabsContent key={platform} value={platform} className="mt-4">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {platformAccounts.map((account) => (
                  <AccountCard
                    key={account.id}
                    account={account}
                    onSwitch={(id) => switchMutation.mutate(id)}
                    onSetPrimary={(id) => setPrimaryMutation.mutate(id)}
                    onEdit={() => {}}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            </TabsContent>
          ))}
        </Tabs>
      ) : accounts && accounts.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {accounts.map((account) => (
            <AccountCard
              key={account.id}
              account={account}
              onSwitch={(id) => switchMutation.mutate(id)}
              onSetPrimary={(id) => setPrimaryMutation.mutate(id)}
              onEdit={() => {}}
              onDelete={handleDelete}
            />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Users className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium">Nenhuma conta conectada</h3>
            <p className="text-muted-foreground text-sm mb-4">
              Adicione suas contas de redes sociais para começar
            </p>
            <Button onClick={() => setAddDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Adicionar Conta
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Dialogs */}
      <AddAccountDialog
        isOpen={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
      />

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover conta?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. A conta será desconectada
              e você precisará adicionar novamente.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Remover
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
