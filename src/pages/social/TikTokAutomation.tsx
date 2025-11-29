import React, { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { 
  Video, 
  Upload, 
  Cookie, 
  CheckCircle2, 
  XCircle,
  Loader2,
  Trash2,
  Globe,
  Users,
  Lock
} from "lucide-react";

interface TikTokSession {
  account_name: string;
  file: string;
}

export const TikTokAutomation = () => {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Sessions state
  const [sessions, setSessions] = useState<TikTokSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<string>("");
  const [sessionsLoading, setSessionsLoading] = useState(false);
  
  // Cookie import state
  const [cookieForm, setCookieForm] = useState({
    accountName: "",
    cookiesJson: ""
  });
  const [cookieLoading, setCookieLoading] = useState(false);
  
  // Upload state
  const [uploadForm, setUploadForm] = useState({
    caption: "",
    hashtags: "",
    privacy: "public"
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  useEffect(() => {
    fetchSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchSessions = async () => {
    setSessionsLoading(true);
    try {
      const response = await api.get<{ sessions: TikTokSession[] }>("/tiktok/sessions");
      setSessions(response.data.sessions || []);
      if (response.data.sessions?.length > 0 && !selectedSession) {
        setSelectedSession(response.data.sessions[0].account_name);
      }
    } catch (error) {
      console.error("Error fetching sessions", error);
    } finally {
      setSessionsLoading(false);
    }
  };

  const handleImportCookies = async () => {
    if (!cookieForm.accountName || !cookieForm.cookiesJson) {
      toast({ title: "Preencha todos os campos", variant: "destructive" });
      return;
    }

    let parsedCookies;
    try {
      parsedCookies = JSON.parse(cookieForm.cookiesJson);
    } catch (e) {
      toast({ title: "JSON de cookies inválido", variant: "destructive" });
      return;
    }

    setCookieLoading(true);
    try {
      await api.post("/tiktok/sessions", {
        account_name: cookieForm.accountName,
        cookies: parsedCookies
      });
      
      toast({ title: "Sessão importada com sucesso!" });
      setCookieForm({ accountName: "", cookiesJson: "" });
      fetchSessions();
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({ 
        title: "Erro ao importar", 
        description: err.response?.data?.detail || "Tente novamente",
        variant: "destructive" 
      });
    } finally {
      setCookieLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith("video/")) {
        toast({ title: "Selecione um arquivo de vídeo", variant: "destructive" });
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedSession) {
      toast({ title: "Selecione uma conta", variant: "destructive" });
      return;
    }
    
    if (!selectedFile) {
      toast({ title: "Selecione um vídeo", variant: "destructive" });
      return;
    }

    setUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append("account_name", selectedSession);
      formData.append("caption", uploadForm.caption);
      formData.append("hashtags", uploadForm.hashtags);
      formData.append("privacy", uploadForm.privacy);
      formData.append("file", selectedFile);

      const response = await api.post<{ url?: string }>("/tiktok/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      toast({ 
        title: "Vídeo publicado com sucesso!",
        description: response.data.url ? `URL: ${response.data.url}` : undefined
      });
      setSelectedFile(null);
      setUploadForm({ caption: "", hashtags: "", privacy: "public" });
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
          <Video className="h-8 w-8 text-black dark:text-white" />
          <h1 className="text-3xl font-bold tracking-tight">Automação TikTok</h1>
        </div>
        {sessions.length > 0 && (
          <Badge variant="outline" className="text-green-600 border-green-600">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            {sessions.length} conta(s) conectada(s)
          </Badge>
        )}
      </div>

      <Tabs defaultValue="sessions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="sessions" className="flex items-center gap-2">
            <Cookie className="h-4 w-4" />
            Contas
          </TabsTrigger>
          <TabsTrigger value="upload" className="flex items-center gap-2" disabled={sessions.length === 0}>
            <Upload className="h-4 w-4" />
            Publicar
          </TabsTrigger>
        </TabsList>

        <TabsContent value="sessions">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Importar Cookies</CardTitle>
                <CardDescription>
                  Exporte os cookies do TikTok usando uma extensão como "EditThisCookie" ou "Cookie-Editor".
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="accountName">Nome da Conta</Label>
                  <Input
                    id="accountName"
                    placeholder="minha_conta_tiktok"
                    value={cookieForm.accountName}
                    onChange={(e) => setCookieForm({ ...cookieForm, accountName: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cookies">Cookies (JSON)</Label>
                  <Textarea
                    id="cookies"
                    placeholder='[{"name": "sessionid", "value": "..."}]'
                    rows={6}
                    value={cookieForm.cookiesJson}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => 
                      setCookieForm({ ...cookieForm, cookiesJson: e.target.value })
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    Cole o JSON exportado da extensão de cookies.
                  </p>
                </div>
                <Button 
                  className="w-full" 
                  onClick={handleImportCookies} 
                  disabled={cookieLoading}
                >
                  {cookieLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Importando...
                    </>
                  ) : (
                    <>
                      <Cookie className="mr-2 h-4 w-4" />
                      Importar Sessão
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Contas Salvas</CardTitle>
                <CardDescription>
                  Gerencie suas contas do TikTok.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {sessionsLoading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : sessions.length === 0 ? (
                  <div className="flex items-center gap-3 p-4 rounded-lg bg-muted">
                    <XCircle className="h-8 w-8 text-muted-foreground" />
                    <div>
                      <p className="font-medium">Nenhuma conta conectada</p>
                      <p className="text-sm text-muted-foreground">Importe os cookies para começar</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {sessions.map((session) => (
                      <div 
                        key={session.account_name}
                        className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border"
                      >
                        <div className="flex items-center gap-3">
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                          <span className="font-medium">@{session.account_name}</span>
                        </div>
                        <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="upload">
          <Card>
            <CardHeader>
              <CardTitle>Publicar Vídeo</CardTitle>
              <CardDescription>
                Envie vídeos para o TikTok.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Conta</Label>
                  <Select value={selectedSession} onValueChange={setSelectedSession}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione uma conta" />
                    </SelectTrigger>
                    <SelectContent>
                      {sessions.map((session) => (
                        <SelectItem key={session.account_name} value={session.account_name}>
                          @{session.account_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Privacidade</Label>
                  <Select value={uploadForm.privacy} onValueChange={(v) => setUploadForm({ ...uploadForm, privacy: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="public">
                        <div className="flex items-center gap-2">
                          <Globe className="h-4 w-4" /> Público
                        </div>
                      </SelectItem>
                      <SelectItem value="friends">
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4" /> Amigos
                        </div>
                      </SelectItem>
                      <SelectItem value="private">
                        <div className="flex items-center gap-2">
                          <Lock className="h-4 w-4" /> Privado
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Arquivo de Vídeo</Label>
                <Input
                  ref={fileInputRef}
                  type="file"
                  accept="video/*"
                  onChange={handleFileSelect}
                />
                {selectedFile && (
                  <p className="text-sm text-muted-foreground">
                    Selecionado: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label>Descrição</Label>
                <Textarea
                  placeholder="Escreva a descrição do seu vídeo..."
                  rows={3}
                  value={uploadForm.caption}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => 
                    setUploadForm({ ...uploadForm, caption: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>Hashtags</Label>
                <Input
                  placeholder="#viral, #fyp, #tiktok"
                  value={uploadForm.hashtags}
                  onChange={(e) => setUploadForm({ ...uploadForm, hashtags: e.target.value })}
                />
                <p className="text-xs text-muted-foreground">
                  Separe as hashtags por vírgula.
                </p>
              </div>

              <Button 
                className="w-full" 
                size="lg"
                onClick={handleUpload}
                disabled={uploadLoading || !selectedFile || !selectedSession}
              >
                {uploadLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Publicando...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Publicar no TikTok
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
