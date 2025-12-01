import React, { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
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
  Youtube, 
  Upload, 
  Key, 
  CheckCircle2, 
  XCircle,
  Loader2,
  Trash2,
  Globe,
  EyeOff,
  Link2,
  Film,
  Image
} from "lucide-react";
import { YouTubeQuotaWidget } from "@/components/YouTubeQuotaWidget";

interface YouTubeAccount {
  account_name: string;
  token_file: string;
}

const CATEGORIES = [
  { value: "1", label: "Filme e animação" },
  { value: "2", label: "Automóveis" },
  { value: "10", label: "Música" },
  { value: "15", label: "Animais" },
  { value: "17", label: "Esportes" },
  { value: "19", label: "Viagem e eventos" },
  { value: "20", label: "Jogos" },
  { value: "22", label: "Pessoas e blogs" },
  { value: "23", label: "Comédia" },
  { value: "24", label: "Entretenimento" },
  { value: "25", label: "Notícias e política" },
  { value: "26", label: "Instruções e estilo" },
  { value: "27", label: "Educação" },
  { value: "28", label: "Ciência e tecnologia" },
];

export const YouTubeAutomation = () => {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const thumbInputRef = useRef<HTMLInputElement>(null);
  
  // Accounts state
  const [accounts, setAccounts] = useState<YouTubeAccount[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<string>("");
  const [accountsLoading, setAccountsLoading] = useState(false);
  
  // Auth state
  const [authForm, setAuthForm] = useState({ accountName: "" });
  const [authLoading, setAuthLoading] = useState(false);
  
  // Upload state
  const [uploadForm, setUploadForm] = useState({
    title: "",
    description: "",
    tags: "",
    privacy: "private",
    category: "26",
    isShort: false
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedThumb, setSelectedThumb] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  useEffect(() => {
    fetchAccounts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchAccounts = async () => {
    setAccountsLoading(true);
    try {
      const response = await api.get<{ accounts: YouTubeAccount[] }>("/youtube/accounts");
      setAccounts(response.data.accounts || []);
      if (response.data.accounts?.length > 0 && !selectedAccount) {
        setSelectedAccount(response.data.accounts[0].account_name);
      }
    } catch (error) {
      console.error("Error fetching accounts", error);
    } finally {
      setAccountsLoading(false);
    }
  };

  const handleDeleteAccount = async (accountName: string) => {
    try {
      await api.delete(`/youtube/accounts/${accountName}`);
      toast({ title: "Canal removido" });
      fetchAccounts();
      if (selectedAccount === accountName) {
        setSelectedAccount("");
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({ 
        title: "Erro ao remover canal", 
        description: err.response?.data?.detail,
        variant: "destructive" 
      });
    }
  };

  const handleAuth = async () => {
    if (!authForm.accountName) {
      toast({ title: "Digite um nome para a conta", variant: "destructive" });
      return;
    }

    setAuthLoading(true);
    try {
      await api.post("/youtube/auth/init", {
        account_name: authForm.accountName
      });
      
      toast({ title: "Conta autenticada com sucesso!" });
      setAuthForm({ accountName: "" });
      fetchAccounts();
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({ 
        title: "Erro na autenticação", 
        description: err.response?.data?.detail || "Verifique as credenciais do Google",
        variant: "destructive" 
      });
    } finally {
      setAuthLoading(false);
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

  const handleThumbSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith("image/")) {
        toast({ title: "Selecione uma imagem", variant: "destructive" });
        return;
      }
      setSelectedThumb(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedAccount) {
      toast({ title: "Selecione uma conta", variant: "destructive" });
      return;
    }
    
    if (!selectedFile) {
      toast({ title: "Selecione um vídeo", variant: "destructive" });
      return;
    }

    if (!uploadForm.title) {
      toast({ title: "Digite um título", variant: "destructive" });
      return;
    }

    setUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append("account_name", selectedAccount);
      formData.append("title", uploadForm.title);
      formData.append("description", uploadForm.description);
      formData.append("tags", uploadForm.tags);
      formData.append("privacy", uploadForm.privacy);
      formData.append("category", uploadForm.category);
      formData.append("is_short", String(uploadForm.isShort));
      formData.append("file", selectedFile);
      
      if (selectedThumb) {
        formData.append("thumbnail", selectedThumb);
      }

      const response = await api.post<{ url?: string }>("/youtube/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      toast({ 
        title: "Vídeo publicado com sucesso!",
        description: response.data.url
      });
      setSelectedFile(null);
      setSelectedThumb(null);
      setUploadForm({
        title: "",
        description: "",
        tags: "",
        privacy: "private",
        category: "26",
        isShort: false
      });
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (thumbInputRef.current) thumbInputRef.current.value = "";
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
          <Youtube className="h-8 w-8 text-red-600" />
          <h1 className="text-3xl font-bold tracking-tight">Automação YouTube</h1>
        </div>
        {accounts.length > 0 && (
          <Badge variant="outline" className="text-green-600 border-green-600">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            {accounts.length} canal(is) conectado(s)
          </Badge>
        )}
      </div>

      {/* YouTube Quota Widget - Versão Completa */}
      <YouTubeQuotaWidget />

      <Tabs defaultValue="accounts" className="space-y-4">
        <TabsList>
          <TabsTrigger value="accounts" className="flex items-center gap-2">
            <Key className="h-4 w-4" />
            Canais
          </TabsTrigger>
          <TabsTrigger value="upload" className="flex items-center gap-2" disabled={accounts.length === 0}>
            <Upload className="h-4 w-4" />
            Publicar
          </TabsTrigger>
        </TabsList>

        <TabsContent value="accounts">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Autenticar Canal</CardTitle>
                <CardDescription>
                  Conecte seu canal do YouTube via OAuth do Google.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400">
                  <p className="text-sm">
                    <strong>Requisito:</strong> É necessário ter o arquivo de credenciais do Google 
                    (<code>youtube_credentials.json</code>) configurado no servidor.
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="accountName">Nome do Canal</Label>
                  <Input
                    id="accountName"
                    placeholder="meu_canal"
                    value={authForm.accountName}
                    onChange={(e) => setAuthForm({ accountName: e.target.value })}
                  />
                </div>
                <Button 
                  className="w-full" 
                  onClick={handleAuth} 
                  disabled={authLoading}
                >
                  {authLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Autenticando...
                    </>
                  ) : (
                    <>
                      <Key className="mr-2 h-4 w-4" />
                      Conectar com Google
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Canais Conectados</CardTitle>
                <CardDescription>
                  Gerencie seus canais do YouTube.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {accountsLoading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : accounts.length === 0 ? (
                  <div className="flex items-center gap-3 p-4 rounded-lg bg-muted">
                    <XCircle className="h-8 w-8 text-muted-foreground" />
                    <div>
                      <p className="font-medium">Nenhum canal conectado</p>
                      <p className="text-sm text-muted-foreground">Autentique para começar</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {accounts.map((account) => (
                      <div 
                        key={account.account_name}
                        className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border"
                      >
                        <div className="flex items-center gap-3">
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                          <span className="font-medium">{account.account_name}</span>
                        </div>
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="text-destructive hover:text-destructive"
                          onClick={() => handleDeleteAccount(account.account_name)}
                        >
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
                Envie vídeos ou Shorts para o YouTube.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label>Canal</Label>
                  <Select value={selectedAccount} onValueChange={setSelectedAccount}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione um canal" />
                    </SelectTrigger>
                    <SelectContent>
                      {accounts.map((account) => (
                        <SelectItem key={account.account_name} value={account.account_name}>
                          {account.account_name}
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
                      <SelectItem value="unlisted">
                        <div className="flex items-center gap-2">
                          <Link2 className="h-4 w-4" /> Não listado
                        </div>
                      </SelectItem>
                      <SelectItem value="private">
                        <div className="flex items-center gap-2">
                          <EyeOff className="h-4 w-4" /> Privado
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Categoria</Label>
                  <Select value={uploadForm.category} onValueChange={(v) => setUploadForm({ ...uploadForm, category: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map((cat) => (
                        <SelectItem key={cat.value} value={cat.value}>
                          {cat.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="is-short"
                  checked={uploadForm.isShort}
                  onCheckedChange={(checked) => setUploadForm({ ...uploadForm, isShort: checked })}
                />
                <Label htmlFor="is-short" className="flex items-center gap-2">
                  <Film className="h-4 w-4" />
                  Este é um YouTube Short (vertical, até 60s)
                </Label>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
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
                      {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label>Thumbnail (opcional)</Label>
                  <Input
                    ref={thumbInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleThumbSelect}
                  />
                  {selectedThumb && (
                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                      <Image className="h-3 w-3" />
                      {selectedThumb.name}
                    </p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Título</Label>
                <Input
                  placeholder="Título do vídeo (máx. 100 caracteres)"
                  maxLength={100}
                  value={uploadForm.title}
                  onChange={(e) => setUploadForm({ ...uploadForm, title: e.target.value })}
                />
                <p className="text-xs text-muted-foreground text-right">
                  {uploadForm.title.length}/100
                </p>
              </div>

              <div className="space-y-2">
                <Label>Descrição</Label>
                <Textarea
                  placeholder="Descrição do vídeo..."
                  rows={4}
                  maxLength={5000}
                  value={uploadForm.description}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => 
                    setUploadForm({ ...uploadForm, description: e.target.value })
                  }
                />
                <p className="text-xs text-muted-foreground text-right">
                  {uploadForm.description.length}/5000
                </p>
              </div>

              <div className="space-y-2">
                <Label>Tags</Label>
                <Input
                  placeholder="gaming, tutorial, vlog"
                  value={uploadForm.tags}
                  onChange={(e) => setUploadForm({ ...uploadForm, tags: e.target.value })}
                />
                <p className="text-xs text-muted-foreground">
                  Separe as tags por vírgula.
                </p>
              </div>

              <Button 
                className="w-full" 
                size="lg"
                onClick={handleUpload}
                disabled={uploadLoading || !selectedFile || !selectedAccount || !uploadForm.title}
              >
                {uploadLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Publicando...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Publicar no YouTube
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

export default YouTubeAutomation;
