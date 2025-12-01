import React, { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { 
  Instagram, 
  LogIn, 
  Upload, 
  Image, 
  Video, 
  Film, 
  CheckCircle2, 
  XCircle,
  Loader2,
  AlertTriangle,
  Shield,
  RefreshCw,
  Trash2
} from "lucide-react";

interface InstagramSession {
  username: string;
  isLoggedIn: boolean;
  status?: string;
  lastUsed?: string;
  expiresAt?: string;
}

interface ChallengeInfo {
  id?: string;
  type: string;
  message: string;
  attemptsRemaining?: number;
}

interface LoginResponse {
  status: string;
  message?: string;
  challenge_type?: string;
}

export const InstagramAutomation = () => {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Auth state
  const [session, setSession] = useState<InstagramSession | null>(null);
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const [loginLoading, setLoginLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(true);
  
  // Challenge state (2FA/SMS/Email verification)
  const [challenge, setChallenge] = useState<ChallengeInfo | null>(null);
  const [verificationCode, setVerificationCode] = useState("");
  const [challengeLoading, setChallengeLoading] = useState(false);
  
  // Upload state
  const [uploadForm, setUploadForm] = useState({
    caption: "",
    mediaType: "photo" as "photo" | "video" | "reel"
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  // Check for existing session on mount
  useEffect(() => {
    checkExistingSession();
  }, []);

  const checkExistingSession = async () => {
    setSessionLoading(true);
    try {
      const response = await api.get<{ sessions: Array<{
        username: string;
        status: string;
        is_valid: boolean;
        last_used: string | null;
        expires_at: string | null;
        active_challenges: number;
        challenges: Array<{ id: string; type: string; status: string }>;
      }> }>("/instagram/sessions");
      
      const activeSessions = response.data.sessions.filter(s => s.is_valid);
      if (activeSessions.length > 0) {
        const activeSession = activeSessions[0];
        setSession({
          username: activeSession.username,
          isLoggedIn: true,
          status: activeSession.status,
          lastUsed: activeSession.last_used || undefined,
          expiresAt: activeSession.expires_at || undefined
        });
        
        // Check for pending challenges
        if (activeSession.active_challenges > 0) {
          const pendingChallenge = activeSession.challenges.find(c => c.status === "pending");
          if (pendingChallenge) {
            setChallenge({
              id: pendingChallenge.id,
              type: pendingChallenge.type,
              message: `Verificação ${pendingChallenge.type.toUpperCase()} pendente`
            });
          }
        }
      }
    } catch {
      // No active sessions or not authenticated
      console.log("No active Instagram sessions found");
    } finally {
      setSessionLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!loginForm.username || !loginForm.password) {
      toast({ title: "Preencha usuário e senha", variant: "destructive" });
      return;
    }
    
    setLoginLoading(true);
    try {
      const response = await api.post<LoginResponse>("/instagram/login", {
        username: loginForm.username,
        password: loginForm.password
      });
      
      if (response.data.status === "success") {
        setSession({ username: loginForm.username, isLoggedIn: true });
        setLoginForm({ username: "", password: "" });
        setChallenge(null);
        toast({ title: "Login realizado com sucesso!" });
      } else if (response.data.status === "challenge_required") {
        // 2FA or verification challenge
        setChallenge({
          type: response.data.challenge_type || "unknown",
          message: response.data.message || "Verificação necessária"
        });
        toast({ 
          title: "Verificação necessária", 
          description: response.data.message,
          variant: "default" 
        });
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({ 
        title: "Erro no login", 
        description: err.response?.data?.detail || "Verifique suas credenciais",
        variant: "destructive" 
      });
    } finally {
      setLoginLoading(false);
    }
  };

  const handleResolveChallenge = async () => {
    if (!verificationCode) {
      toast({ title: "Insira o código de verificação", variant: "destructive" });
      return;
    }

    setChallengeLoading(true);
    try {
      const response = await api.post<{ status: string; message?: string; attempts_remaining?: number }>("/instagram/challenge/resolve", {
        username: loginForm.username,
        code: verificationCode
      });

      if (response.data.status === "success") {
        setSession({ username: loginForm.username, isLoggedIn: true });
        setChallenge(null);
        setVerificationCode("");
        setLoginForm({ username: "", password: "" });
        toast({ title: "Verificação concluída!" });
      } else if (response.data.status === "invalid_code") {
        toast({ 
          title: "Código inválido", 
          description: response.data.attempts_remaining 
            ? `Tentativas restantes: ${response.data.attempts_remaining}`
            : "Tente novamente",
          variant: "destructive" 
        });
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({ 
        title: "Erro na verificação", 
        description: err.response?.data?.detail || "Código inválido",
        variant: "destructive" 
      });
    } finally {
      setChallengeLoading(false);
    }
  };

  const handleResendCode = async (method: "email" | "sms" = "email") => {
    try {
      await api.post<{ status: string; message: string }>(`/instagram/challenge/request?username=${loginForm.username}&method=${method}`);
      toast({ title: `Código reenviado via ${method.toUpperCase()}` });
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({ 
        title: "Erro ao reenviar código", 
        description: err.response?.data?.detail,
        variant: "destructive" 
      });
    }
  };

  const handleDisconnect = async () => {
    if (!session?.username) return;
    
    try {
      await api.delete(`/instagram/sessions/${session.username}`);
      setSession(null);
      setChallenge(null);
      toast({ title: "Conta desconectada" });
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({ 
        title: "Erro ao desconectar", 
        description: err.response?.data?.detail,
        variant: "destructive" 
      });
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!session?.isLoggedIn) {
      toast({ title: "Faça login primeiro", variant: "destructive" });
      return;
    }
    
    if (!selectedFile) {
      toast({ title: "Selecione um arquivo", variant: "destructive" });
      return;
    }

    setUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append("username", session.username);
      formData.append("caption", uploadForm.caption);
      formData.append("media_type", uploadForm.mediaType);
      formData.append("file", selectedFile);

      await api.post("/instagram/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      toast({ title: "Mídia publicada com sucesso!" });
      setSelectedFile(null);
      setUploadForm({ caption: "", mediaType: "photo" });
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({ 
        title: "Erro no upload", 
        description: err.response?.data?.detail || "Tente novamente",
        variant: "destructive" 
      });
    } finally {
      setUploadLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Instagram className="h-8 w-8 text-pink-500" />
          <h1 className="text-3xl font-bold tracking-tight">Automação Instagram</h1>
        </div>
        <div className="flex items-center gap-2">
          {challenge && (
            <Badge variant="outline" className="text-yellow-600 border-yellow-600">
              <AlertTriangle className="h-3 w-3 mr-1" />
              Verificação pendente
            </Badge>
          )}
          {session?.isLoggedIn && (
            <Badge variant="outline" className="text-green-600 border-green-600">
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Conectado: @{session.username}
            </Badge>
          )}
        </div>
      </div>

      {/* Challenge Alert */}
      {challenge && (
        <Alert className="border-yellow-500 bg-yellow-500/10">
          <Shield className="h-4 w-4 text-yellow-500" />
          <AlertDescription className="flex items-center justify-between">
            <span>
              <strong>Verificação {challenge.type.toUpperCase()}</strong>: {challenge.message}
            </span>
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue={challenge ? "login" : (session?.isLoggedIn ? "upload" : "login")} className="space-y-4">
        <TabsList>
          <TabsTrigger value="login" className="flex items-center gap-2">
            <LogIn className="h-4 w-4" />
            Conexão
          </TabsTrigger>
          <TabsTrigger value="upload" className="flex items-center gap-2" disabled={!session?.isLoggedIn || !!challenge}>
            <Upload className="h-4 w-4" />
            Publicar
          </TabsTrigger>
        </TabsList>

        <TabsContent value="login">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Login or Challenge Card */}
            <Card>
              <CardHeader>
                <CardTitle>
                  {challenge ? (
                    <span className="flex items-center gap-2">
                      <Shield className="h-5 w-5 text-yellow-500" />
                      Verificação de Segurança
                    </span>
                  ) : (
                    "Conectar Conta"
                  )}
                </CardTitle>
                <CardDescription>
                  {challenge 
                    ? `Insira o código de verificação enviado via ${challenge.type.toUpperCase()}`
                    : "Faça login na sua conta do Instagram para começar a automatizar."
                  }
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {challenge ? (
                  /* Challenge/2FA Form */
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="verification-code">Código de Verificação</Label>
                      <Input
                        id="verification-code"
                        placeholder="000000"
                        maxLength={6}
                        value={verificationCode}
                        onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ""))}
                        className="text-center text-2xl tracking-widest font-mono"
                      />
                    </div>
                    <Button 
                      className="w-full" 
                      onClick={handleResolveChallenge} 
                      disabled={challengeLoading || verificationCode.length < 6}
                    >
                      {challengeLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Verificando...
                        </>
                      ) : (
                        <>
                          <Shield className="mr-2 h-4 w-4" />
                          Verificar Código
                        </>
                      )}
                    </Button>
                    <div className="flex gap-2">
                      <Button 
                        variant="outline" 
                        size="sm"
                        className="flex-1"
                        onClick={() => handleResendCode("email")}
                      >
                        <RefreshCw className="mr-1 h-3 w-3" />
                        Reenviar por Email
                      </Button>
                      {challenge.type === "sms" && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          className="flex-1"
                          onClick={() => handleResendCode("sms")}
                        >
                          <RefreshCw className="mr-1 h-3 w-3" />
                          Reenviar por SMS
                        </Button>
                      )}
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      className="w-full text-muted-foreground"
                      onClick={() => {
                        setChallenge(null);
                        setVerificationCode("");
                      }}
                    >
                      Cancelar e tentar novamente
                    </Button>
                  </>
                ) : (
                  /* Login Form */
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="username">Usuário</Label>
                      <Input
                        id="username"
                        placeholder="seu_usuario"
                        value={loginForm.username}
                        onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                        disabled={session?.isLoggedIn}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="password">Senha</Label>
                      <Input
                        id="password"
                        type="password"
                        placeholder="••••••••"
                        value={loginForm.password}
                        onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                        disabled={session?.isLoggedIn}
                      />
                    </div>
                    <Button 
                      className="w-full" 
                      onClick={handleLogin} 
                      disabled={loginLoading || session?.isLoggedIn}
                    >
                      {loginLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Conectando...
                        </>
                      ) : (
                        <>
                          <LogIn className="mr-2 h-4 w-4" />
                          Conectar
                        </>
                      )}
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Status da Conexão</CardTitle>
                <CardDescription>
                  Informações sobre sua conta conectada.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {sessionLoading ? (
                  <div className="flex items-center gap-3 p-4 rounded-lg bg-muted">
                    <Loader2 className="h-8 w-8 text-muted-foreground animate-spin" />
                    <div>
                      <p className="font-medium">Verificando sessões...</p>
                      <p className="text-sm text-muted-foreground">Aguarde um momento</p>
                    </div>
                  </div>
                ) : session?.isLoggedIn ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                      <CheckCircle2 className="h-8 w-8 text-green-500" />
                      <div className="flex-1">
                        <p className="font-medium">Conta Conectada</p>
                        <p className="text-sm text-muted-foreground">@{session.username}</p>
                        {session.lastUsed && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Último uso: {new Date(session.lastUsed).toLocaleDateString("pt-BR")}
                          </p>
                        )}
                      </div>
                    </div>
                    {challenge && (
                      <div className="flex items-center gap-3 p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                        <AlertTriangle className="h-6 w-6 text-yellow-500" />
                        <div className="flex-1">
                          <p className="font-medium text-yellow-600">Verificação Pendente</p>
                          <p className="text-sm text-muted-foreground">{challenge.message}</p>
                        </div>
                      </div>
                    )}
                    <Button 
                      variant="outline" 
                      className="w-full text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={handleDisconnect}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Desconectar
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center gap-3 p-4 rounded-lg bg-muted">
                    <XCircle className="h-8 w-8 text-muted-foreground" />
                    <div>
                      <p className="font-medium">Nenhuma conta conectada</p>
                      <p className="text-sm text-muted-foreground">Faça login para começar</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="upload">
          <Card>
            <CardHeader>
              <CardTitle>Publicar Conteúdo</CardTitle>
              <CardDescription>
                Envie fotos, vídeos ou reels para o Instagram.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-3">
                <Button
                  variant={uploadForm.mediaType === "photo" ? "default" : "outline"}
                  className="h-24 flex-col gap-2"
                  onClick={() => setUploadForm({ ...uploadForm, mediaType: "photo" })}
                >
                  <Image className="h-8 w-8" />
                  Foto
                </Button>
                <Button
                  variant={uploadForm.mediaType === "video" ? "default" : "outline"}
                  className="h-24 flex-col gap-2"
                  onClick={() => setUploadForm({ ...uploadForm, mediaType: "video" })}
                >
                  <Video className="h-8 w-8" />
                  Vídeo
                </Button>
                <Button
                  variant={uploadForm.mediaType === "reel" ? "default" : "outline"}
                  className="h-24 flex-col gap-2"
                  onClick={() => setUploadForm({ ...uploadForm, mediaType: "reel" })}
                >
                  <Film className="h-8 w-8" />
                  Reel
                </Button>
              </div>

              <div className="space-y-2">
                <Label>Arquivo de Mídia</Label>
                <Input
                  ref={fileInputRef}
                  type="file"
                  accept={uploadForm.mediaType === "photo" ? "image/*" : "video/*"}
                  onChange={handleFileSelect}
                />
                {selectedFile && (
                  <p className="text-sm text-muted-foreground">
                    Selecionado: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label>Legenda</Label>
                <Textarea
                  placeholder="Escreva sua legenda aqui... #hashtags"
                  rows={4}
                  value={uploadForm.caption}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => 
                    setUploadForm({ ...uploadForm, caption: e.target.value })
                  }
                />
              </div>

              <Button 
                className="w-full" 
                size="lg"
                onClick={handleUpload}
                disabled={uploadLoading || !selectedFile}
              >
                {uploadLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Publicando...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Publicar no Instagram
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default InstagramAutomation;
