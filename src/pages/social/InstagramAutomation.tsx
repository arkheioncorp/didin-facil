import React, { useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
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
  Loader2
} from "lucide-react";

interface InstagramSession {
  username: string;
  isLoggedIn: boolean;
}

export const InstagramAutomation = () => {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Auth state
  const [session, setSession] = useState<InstagramSession | null>(null);
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const [loginLoading, setLoginLoading] = useState(false);
  
  // Upload state
  const [uploadForm, setUploadForm] = useState({
    caption: "",
    mediaType: "photo" as "photo" | "video" | "reel"
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  const handleLogin = async () => {
    if (!loginForm.username || !loginForm.password) {
      toast({ title: "Preencha usuário e senha", variant: "destructive" });
      return;
    }
    
    setLoginLoading(true);
    try {
      await api.post("/instagram/login", {
        username: loginForm.username,
        password: loginForm.password
      });
      
      setSession({ username: loginForm.username, isLoggedIn: true });
      setLoginForm({ username: "", password: "" });
      toast({ title: "Login realizado com sucesso!" });
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
        {session?.isLoggedIn && (
          <Badge variant="outline" className="text-green-600 border-green-600">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Conectado: @{session.username}
          </Badge>
        )}
      </div>

      <Tabs defaultValue="login" className="space-y-4">
        <TabsList>
          <TabsTrigger value="login" className="flex items-center gap-2">
            <LogIn className="h-4 w-4" />
            Conexão
          </TabsTrigger>
          <TabsTrigger value="upload" className="flex items-center gap-2" disabled={!session?.isLoggedIn}>
            <Upload className="h-4 w-4" />
            Publicar
          </TabsTrigger>
        </TabsList>

        <TabsContent value="login">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Conectar Conta</CardTitle>
                <CardDescription>
                  Faça login na sua conta do Instagram para começar a automatizar.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="username">Usuário</Label>
                  <Input
                    id="username"
                    placeholder="seu_usuario"
                    value={loginForm.username}
                    onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
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
                  />
                </div>
                <Button 
                  className="w-full" 
                  onClick={handleLogin} 
                  disabled={loginLoading}
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
                {session?.isLoggedIn ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                      <CheckCircle2 className="h-8 w-8 text-green-500" />
                      <div>
                        <p className="font-medium">Conta Conectada</p>
                        <p className="text-sm text-muted-foreground">@{session.username}</p>
                      </div>
                    </div>
                    <Button 
                      variant="outline" 
                      className="w-full"
                      onClick={() => setSession(null)}
                    >
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
