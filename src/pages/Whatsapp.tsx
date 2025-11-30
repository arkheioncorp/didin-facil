import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { MessageSquare, Radio, LayoutTemplate, Settings, RefreshCw, Send } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";

interface Message {
  id: string;
  remote_jid: string;
  from_me: boolean;
  content: string;
  timestamp: string;
  status: string;
}

export const WhatsappPage: React.FC = () => {
  const { t } = useTranslation();
  const { toast } = useToast();
  const [instanceName, setInstanceName] = useState("");
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [testMessage, setTestMessage] = useState({ to: "", content: "" });
  const [messages, setMessages] = useState<Message[]>([]);
  const [broadcastList, setBroadcastList] = useState("");
  const [broadcastMessage, setBroadcastMessage] = useState("");

  const fetchMessages = async () => {
    if (!instanceName) return;
    try {
      const response = await api.get<Message[]>(`/whatsapp/messages/${instanceName}`);
      setMessages(response.data);
      toast({ title: "Mensagens atualizadas" });
    } catch (error) {
      console.error("Error fetching messages", error);
      toast({ title: "Erro ao buscar mensagens", variant: "destructive" });
    }
  };

  const handleCreateInstance = async () => {
    if (!instanceName) return;
    setLoading(true);
    try {
      await api.post("/whatsapp/instances", { instance_name: instanceName });
      toast({
        title: t("success", "Sucesso"),
        description: t("instance_created", "Instância criada com sucesso"),
      });
      fetchQrCode();
    } catch (error) {
      toast({
        title: t("error", "Erro"),
        description: t("instance_create_error", "Erro ao criar instância"),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchQrCode = async () => {
    if (!instanceName) return;
    try {
      const response = await api.get<{ base64?: string }>(`/whatsapp/instances/${instanceName}/qrcode`);
      // Evolution API returns base64 in 'base64' field or sometimes directly
      // Adjust based on actual response structure from client.py
      if (response.data && response.data.base64) {
        setQrCode(response.data.base64);
      }
    } catch (error) {
      console.error("Error fetching QR Code", error);
    }
  };

  const handleSendMessage = async () => {
    if (!instanceName || !testMessage.to || !testMessage.content) return;
    setLoading(true);
    try {
      await api.post("/whatsapp/messages/text", {
        instance_name: instanceName,
        to: testMessage.to,
        content: testMessage.content,
      });
      toast({
        title: t("success", "Sucesso"),
        description: t("message_sent", "Mensagem enviada"),
      });
    } catch (error) {
      toast({
        title: t("error", "Erro"),
        description: t("message_send_error", "Erro ao enviar mensagem"),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">WhatsApp Automation</h1>
      </div>

      <Tabs defaultValue="connection" className="space-y-4">
        <TabsList>
          <TabsTrigger value="connection" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            {t("connection", "Conexão")}
          </TabsTrigger>
          <TabsTrigger value="conversations" className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Conversas
          </TabsTrigger>
          <TabsTrigger value="broadcast" className="flex items-center gap-2">
            <Radio className="h-4 w-4" />
            Disparos em Massa
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-2">
            <LayoutTemplate className="h-4 w-4" />
            Templates
          </TabsTrigger>
        </TabsList>

        <TabsContent value="connection" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>{t("connection", "Conexão")}</CardTitle>
                <CardDescription>
                  {t("connect_whatsapp_desc", "Conecte seu WhatsApp para iniciar automações")}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="instanceName">{t("instance_name", "Nome da Instância")}</Label>
                  <Input
                    id="instanceName"
                    value={instanceName}
                    onChange={(e) => setInstanceName(e.target.value)}
                    placeholder="ex: marketing-01"
                  />
                </div>
                <Button onClick={handleCreateInstance} disabled={loading || !instanceName}>
                  {loading ? t("processing", "Processando...") : t("connect", "Conectar / Gerar QR Code")}
                </Button>

                {qrCode && (
                  <div className="mt-4 flex justify-center p-4 bg-white rounded-lg">
                    <img src={qrCode} alt="WhatsApp QR Code" className="max-w-[250px]" />
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t("test_message", "Teste de Envio")}</CardTitle>
                <CardDescription>
                  {t("test_message_desc", "Envie uma mensagem de teste para validar a conexão")}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="to">{t("recipient", "Destinatário (55119...)")}</Label>
                  <Input
                    id="to"
                    value={testMessage.to}
                    onChange={(e) => setTestMessage({ ...testMessage, to: e.target.value })}
                    placeholder="5511999999999"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="content">{t("message", "Mensagem")}</Label>
                  <Input
                    id="content"
                    value={testMessage.content}
                    onChange={(e) => setTestMessage({ ...testMessage, content: e.target.value })}
                    placeholder="Olá, teste do Didin Fácil!"
                  />
                </div>
                <Button onClick={handleSendMessage} disabled={loading || !instanceName}>
                  {t("send", "Enviar")}
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="conversations">
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Conversas</CardTitle>
                <CardDescription>Histórico de mensagens da instância: {instanceName || "Nenhuma selecionada"}</CardDescription>
              </div>
              <Button variant="outline" size="icon" onClick={fetchMessages} disabled={!instanceName}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden p-0">
              {!instanceName ? (
                <div className="flex h-full items-center justify-center text-muted-foreground">
                  Selecione ou conecte uma instância na aba "Conexão" primeiro.
                </div>
              ) : (
                <ScrollArea className="h-full p-4">
                  <div className="space-y-4">
                    {messages.length === 0 ? (
                      <div className="text-center text-muted-foreground py-10">
                        Nenhuma mensagem encontrada.
                      </div>
                    ) : (
                      messages.map((msg) => (
                        <div
                          key={msg.id}
                          className={`flex ${msg.from_me ? "justify-end" : "justify-start"}`}
                        >
                          <div
                            className={`max-w-[80%] rounded-lg p-3 ${
                              msg.from_me
                                ? "bg-primary text-primary-foreground"
                                : "bg-muted"
                            }`}
                          >
                            <div className="flex justify-between items-center gap-2 mb-1">
                              <span className="text-xs font-bold opacity-70">
                                {msg.remote_jid.replace("@s.whatsapp.net", "")}
                              </span>
                              <span className="text-[10px] opacity-50">
                                {new Date(msg.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                            <div className="mt-1 text-right">
                              <Badge variant="outline" className="text-[10px] h-4 px-1 border-white/20">
                                {msg.status}
                              </Badge>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="broadcast">
          <Card>
            <CardHeader>
              <CardTitle>Disparos em Massa</CardTitle>
              <CardDescription>Envie mensagens para múltiplos contatos de uma vez.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Lista de Números (um por linha)</Label>
                <Textarea 
                  placeholder="5511999999999&#10;5511988888888" 
                  rows={5}
                  value={broadcastList}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setBroadcastList(e.target.value)}

                />
                <p className="text-xs text-muted-foreground">
                  Formato: DDI + DDD + Número (ex: 5511999999999)
                </p>
              </div>
              <div className="space-y-2">
                <Label>Mensagem</Label>
                <Textarea 
                  placeholder="Digite sua mensagem aqui..." 
                  rows={4}
                  value={broadcastMessage}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setBroadcastMessage(e.target.value)}

                />
              </div>
              <Button 
                className="w-full" 
                disabled={loading || !instanceName || !broadcastList || !broadcastMessage}
                onClick={async () => {
                  setLoading(true);
                  const numbers = broadcastList.split("\n").filter(n => n.trim().length > 0);
                  let successCount = 0;
                  let failCount = 0;

                  for (const number of numbers) {
                    try {
                      await api.post("/whatsapp/messages/text", {
                        instance_name: instanceName,
                        to: number.trim(),
                        content: broadcastMessage,
                      });
                      successCount++;
                    } catch (e) {
                      failCount++;
                    }
                  }
                  
                  toast({
                    title: "Disparo concluído",
                    description: `Enviados: ${successCount} | Falhas: ${failCount}`,
                  });
                  setLoading(false);
                }}
              >
                <Send className="mr-2 h-4 w-4" />
                Iniciar Disparo ({broadcastList.split("\n").filter(n => n.trim().length > 0).length} contatos)
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="templates">
          <Card>
            <CardHeader>
              <CardTitle>Templates de Mensagem</CardTitle>
              <CardDescription>Gerencie modelos de mensagens para reutilização.</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Em breve: Editor de templates.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default WhatsappPage;
