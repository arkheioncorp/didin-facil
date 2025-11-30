import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Key,
  Mail,
  MessageSquare,
  Phone,
  RefreshCw,
  Shield,
  Smartphone,
  Trash2,
  Upload,
  XCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

interface Challenge {
  id: string;
  type: string;
  status: string;
  message?: string;
  expires_at?: string;
  attempts?: number;
  max_attempts?: number;
}

interface Session {
  username: string;
  status: string;
  is_valid: boolean;
  last_used?: string;
  created_at?: string;
  expires_at?: string;
  active_challenges: number;
  challenges: Challenge[];
}

interface SessionsResponse {
  sessions: Session[];
}

const api = {
  getSessions: async (): Promise<SessionsResponse> => {
    const res = await fetch('/api/instagram/sessions');
    if (!res.ok) throw new Error('Failed to fetch sessions');
    return res.json();
  },
  backupSession: async (username: string) => {
    const res = await fetch(`/api/instagram/sessions/${username}/backup`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to backup session');
    return res.json();
  },
  restoreSession: async (username: string) => {
    const res = await fetch(`/api/instagram/sessions/${username}/restore`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to restore session');
    return res.json();
  },
  deleteSession: async (username: string) => {
    const res = await fetch(`/api/instagram/sessions/${username}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete session');
    return res.json();
  },
  resolveChallenge: async (challengeId: string, code: string) => {
    const res = await fetch(
      `/api/instagram/challenges/${challengeId}/resolve?code=${code}`,
      { method: 'POST' }
    );
    if (!res.ok) throw new Error('Failed to resolve challenge');
    return res.json();
  },
  requestCode: async (challengeId: string, method: string) => {
    const res = await fetch(
      `/api/instagram/challenges/${challengeId}/request-code?method=${method}`,
      { method: 'POST' }
    );
    if (!res.ok) throw new Error('Failed to request code');
    return res.json();
  },
};

const ChallengeTypeIcon = ({ type }: { type: string }) => {
  switch (type) {
    case '2fa':
      return <Key className="h-4 w-4" />;
    case 'sms':
      return <Smartphone className="h-4 w-4" />;
    case 'email':
      return <Mail className="h-4 w-4" />;
    case 'phone_call':
      return <Phone className="h-4 w-4" />;
    case 'captcha':
      return <Shield className="h-4 w-4" />;
    default:
      return <AlertCircle className="h-4 w-4" />;
  }
};

const ChallengeStatusBadge = ({ status }: { status: string }) => {
  const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: JSX.Element }> = {
    pending: { variant: 'secondary', icon: <Clock className="h-3 w-3 mr-1" /> },
    in_progress: { variant: 'default', icon: <RefreshCw className="h-3 w-3 mr-1 animate-spin" /> },
    resolved: { variant: 'outline', icon: <CheckCircle2 className="h-3 w-3 mr-1" /> },
    failed: { variant: 'destructive', icon: <XCircle className="h-3 w-3 mr-1" /> },
    expired: { variant: 'destructive', icon: <Clock className="h-3 w-3 mr-1" /> },
  };

  const config = variants[status] || variants.pending;

  return (
    <Badge variant={config.variant} className="text-xs">
      {config.icon}
      {status}
    </Badge>
  );
};

const ChallengeResolver = ({
  challenge,
  onResolved,
}: {
  challenge: Challenge;
  onResolved: () => void;
}) => {
  const [code, setCode] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const queryClient = useQueryClient();

  const resolveMutation = useMutation({
    mutationFn: () => api.resolveChallenge(challenge.id, code),
    onSuccess: (data) => {
      if (data.status === 'success') {
        toast.success('Challenge resolvido com sucesso!');
        setIsOpen(false);
        onResolved();
        queryClient.invalidateQueries({ queryKey: ['instagram-sessions'] });
      } else if (data.status === 'invalid_code') {
        toast.error(`Código inválido. ${data.attempts_remaining} tentativas restantes.`);
      }
    },
    onError: () => {
      toast.error('Erro ao resolver challenge');
    },
  });

  const requestCodeMutation = useMutation({
    mutationFn: (method: string) => api.requestCode(challenge.id, method),
    onSuccess: () => {
      toast.success('Código reenviado!');
    },
    onError: () => {
      toast.error('Erro ao solicitar código');
    },
  });

  const getChallengeInstructions = (type: string) => {
    switch (type) {
      case '2fa':
        return 'Digite o código de 6 dígitos do seu app autenticador (Google Authenticator, Authy, etc.)';
      case 'sms':
        return 'Digite o código de verificação enviado para seu telefone';
      case 'email':
        return 'Digite o código de verificação enviado para seu email';
      case 'phone_call':
        return 'Digite o código informado na ligação do Instagram';
      case 'captcha':
        return 'Acesse o Instagram pelo navegador para completar a verificação CAPTCHA';
      default:
        return 'Complete a verificação de segurança';
    }
  };

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        disabled={challenge.status !== 'pending' && challenge.status !== 'in_progress'}
      >
        <Key className="h-4 w-4 mr-1" />
        Resolver
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ChallengeTypeIcon type={challenge.type} />
              Resolver Challenge: {challenge.type.toUpperCase()}
            </DialogTitle>
            <DialogDescription>
              {getChallengeInstructions(challenge.type)}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {challenge.type !== 'captcha' && (
              <>
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="Digite o código"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    maxLength={8}
                    className="text-center text-lg tracking-widest"
                  />
                </div>

                {challenge.attempts !== undefined && (
                  <p className="text-sm text-muted-foreground text-center">
                    Tentativas: {challenge.attempts}/{challenge.max_attempts || 5}
                  </p>
                )}

                {(challenge.type === 'sms' || challenge.type === 'email') && (
                  <div className="flex justify-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => requestCodeMutation.mutate(challenge.type)}
                      disabled={requestCodeMutation.isPending}
                    >
                      <RefreshCw
                        className={cn('h-4 w-4 mr-1', requestCodeMutation.isPending && 'animate-spin')}
                      />
                      Reenviar código
                    </Button>
                  </div>
                )}
              </>
            )}

            {challenge.type === 'captcha' && (
              <div className="text-center text-muted-foreground">
                <Shield className="h-12 w-12 mx-auto mb-2 text-yellow-500" />
                <p>
                  Este tipo de verificação requer acesso manual ao Instagram.
                  <br />
                  Abra o app ou navegador e complete a verificação.
                </p>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancelar
            </Button>
            {challenge.type !== 'captcha' && (
              <Button
                onClick={() => resolveMutation.mutate()}
                disabled={!code || resolveMutation.isPending}
              >
                {resolveMutation.isPending ? (
                  <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 mr-1" />
                )}
                Verificar
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

const SessionCard = ({
  session,
  onRefresh,
}: {
  session: Session;
  onRefresh: () => void;
}) => {
  const queryClient = useQueryClient();

  const backupMutation = useMutation({
    mutationFn: () => api.backupSession(session.username),
    onSuccess: () => {
      toast.success('Backup criado com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['instagram-sessions'] });
    },
    onError: () => {
      toast.error('Erro ao criar backup');
    },
  });

  const restoreMutation = useMutation({
    mutationFn: () => api.restoreSession(session.username),
    onSuccess: () => {
      toast.success('Sessão restaurada com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['instagram-sessions'] });
    },
    onError: () => {
      toast.error('Erro ao restaurar sessão');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteSession(session.username),
    onSuccess: () => {
      toast.success('Sessão removida');
      queryClient.invalidateQueries({ queryKey: ['instagram-sessions'] });
    },
    onError: () => {
      toast.error('Erro ao remover sessão');
    },
  });

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const isExpiringSoon = () => {
    if (!session.expires_at) return false;
    const expiresAt = new Date(session.expires_at);
    const now = new Date();
    const daysUntilExpiry = Math.ceil(
      (expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    );
    return daysUntilExpiry <= 7;
  };

  return (
    <Card
      className={cn(
        'transition-all',
        !session.is_valid && 'border-destructive bg-destructive/5',
        session.active_challenges > 0 && 'border-yellow-500 bg-yellow-500/5'
      )}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={cn(
                'w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500',
                'flex items-center justify-center text-white font-bold'
              )}
            >
              {session.username.charAt(0).toUpperCase()}
            </div>
            <div>
              <CardTitle className="text-lg">@{session.username}</CardTitle>
              <CardDescription className="text-xs">
                Último uso: {formatDate(session.last_used)}
              </CardDescription>
            </div>
          </div>
          <Badge
            variant={session.is_valid ? 'default' : 'destructive'}
            className={cn(isExpiringSoon() && session.is_valid && 'bg-yellow-500')}
          >
            {session.is_valid
              ? isExpiringSoon()
                ? 'Expirando'
                : 'Ativa'
              : 'Expirada'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Challenges */}
        {session.challenges.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium flex items-center gap-1">
              <AlertCircle className="h-4 w-4 text-yellow-500" />
              Challenges Pendentes ({session.active_challenges})
            </h4>
            <div className="space-y-2">
              {session.challenges.map((challenge) => (
                <div
                  key={challenge.id}
                  className="flex items-center justify-between p-2 bg-muted rounded-md"
                >
                  <div className="flex items-center gap-2">
                    <ChallengeTypeIcon type={challenge.type} />
                    <span className="text-sm font-medium">
                      {challenge.type.toUpperCase()}
                    </span>
                    <ChallengeStatusBadge status={challenge.status} />
                  </div>
                  <ChallengeResolver challenge={challenge} onResolved={onRefresh} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Session Info */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-muted-foreground">Criada em:</div>
          <div>{formatDate(session.created_at)}</div>
          <div className="text-muted-foreground">Expira em:</div>
          <div
            className={cn(
              isExpiringSoon() && 'text-yellow-500 font-medium'
            )}
          >
            {formatDate(session.expires_at)}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-2 pt-2 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => backupMutation.mutate()}
            disabled={backupMutation.isPending || !session.is_valid}
          >
            {backupMutation.isPending ? (
              <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Upload className="h-4 w-4 mr-1" />
            )}
            Backup
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => restoreMutation.mutate()}
            disabled={restoreMutation.isPending}
          >
            {restoreMutation.isPending ? (
              <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-1" />
            )}
            Restaurar
          </Button>

          <Button
            variant="destructive"
            size="sm"
            onClick={() => {
              if (confirm('Tem certeza? Esta ação é irreversível.')) {
                deleteMutation.mutate();
              }
            }}
            disabled={deleteMutation.isPending}
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Remover
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export function InstagramSessionManager() {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['instagram-sessions'],
    queryFn: api.getSessions,
    refetchInterval: 30000, // Refresh every 30s
  });

  const sessions = data?.sessions || [];
  const activeSessions = sessions.filter((s) => s.is_valid).length;
  const pendingChallenges = sessions.reduce(
    (acc, s) => acc + s.active_challenges,
    0
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="flex items-center gap-2 p-4 text-destructive">
          <AlertCircle className="h-5 w-5" />
          Erro ao carregar sessões
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Tentar novamente
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <div className="p-3 rounded-full bg-green-500/10">
              <CheckCircle2 className="h-6 w-6 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{activeSessions}</p>
              <p className="text-sm text-muted-foreground">Sessões Ativas</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <div className="p-3 rounded-full bg-yellow-500/10">
              <AlertCircle className="h-6 w-6 text-yellow-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{pendingChallenges}</p>
              <p className="text-sm text-muted-foreground">
                Challenges Pendentes
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <div className="p-3 rounded-full bg-blue-500/10">
              <MessageSquare className="h-6 w-6 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{sessions.length}</p>
              <p className="text-sm text-muted-foreground">Total de Contas</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sessions List */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Sessões Instagram</h2>
        <Button
          variant="outline"
          size="sm"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['instagram-sessions'] })}
        >
          <RefreshCw className="h-4 w-4 mr-1" />
          Atualizar
        </Button>
      </div>

      {sessions.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center p-8 text-center">
            <MessageSquare className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="font-medium">Nenhuma sessão encontrada</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Conecte uma conta Instagram para começar
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sessions.map((session) => (
            <SessionCard
              key={session.username}
              session={session}
              onRefresh={refetch}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default InstagramSessionManager;
