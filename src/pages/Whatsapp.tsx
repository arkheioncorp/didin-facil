import { useState, useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import { 
  MessageSquare, 
  Send, 
  Phone, 
  Users,
  Plus,
  Trash2,
  RefreshCw,
  QrCode,
  Check,
  X,
  Wifi,
  WifiOff,
  Search,
  MoreVertical,
  Paperclip,
  Smile,
  FileText,
  Bot,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Alert,
  AlertDescription,
} from "@/components/ui/alert";
import { 
  whatsappService, 
  ChatMessage,
  Contact,
} from '@/lib/whatsapp';

// Types
interface Instance {
  id: string;
  name: string;
  phone_number?: string;
  status: 'connected' | 'disconnected' | 'connecting' | 'qrcode';
  qrcode?: string;
  profile_picture?: string;
  created_at: string;
  last_seen?: string;
  owner?: string;
}

interface LocalContact {
  id: string;
  name: string;
  phone: string;
  avatar?: string;
  last_message?: string;
  last_message_time?: string;
  unread_count?: number;
  jid: string;
}

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'contact';
  timestamp: string;
  status?: 'sent' | 'delivered' | 'read' | 'failed';
  type?: 'text' | 'image' | 'audio' | 'document';
  media_url?: string;
}

interface Conversation {
  id: string;
  contact: LocalContact;
  messages: Message[];
  instance_id: string;
  is_bot_active: boolean;
}

export function WhatsappPage() {
  // State - Instances
  const [instances, setInstances] = useState<Instance[]>([]);
  const [selectedInstance, setSelectedInstance] = useState<string | null>(null);
  const [showCreateInstance, setShowCreateInstance] = useState(false);
  const [showQRCode, setShowQRCode] = useState(false);
  const [qrCodeData, setQrCodeData] = useState<string | null>(null);
  const [newInstanceName, setNewInstanceName] = useState('');
  
  // State - Conversations
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // State - Messages
  const [newMessage, setNewMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  
  // State - UI
  const [loading, setLoading] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{success: boolean; message: string} | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch instances on mount
  useEffect(() => {
    fetchInstances();
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // Fetch conversations when instance changes
  useEffect(() => {
    if (selectedInstance) {
      fetchConversations();
    }
  }, [selectedInstance]);

  // Fetch messages when conversation changes
  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.contact.jid);
    }
  }, [selectedConversation]);

  // API Functions
  const fetchInstances = async () => {
    try {
      setLoading(true);
      setConnectionError(null);
      
      const data = await whatsappService.fetchInstances();
      
      const mappedInstances: Instance[] = data.map((item) => ({
        id: item.instance.instanceId || item.instance.instanceName,
        name: item.instance.instanceName,
        phone_number: item.instance.owner?.replace('@s.whatsapp.net', ''),
        status: item.instance.status === 'open' ? 'connected' : 
                item.instance.status === 'connecting' ? 'connecting' : 'disconnected',
        profile_picture: item.instance.profilePictureUrl || undefined,
        created_at: new Date().toISOString(),
        owner: item.instance.owner || undefined,
      }));
      
      setInstances(mappedInstances);
      
      if (mappedInstances.length > 0 && !selectedInstance) {
        setSelectedInstance(mappedInstances[0].name);
        whatsappService.setInstance(mappedInstances[0].name);
      }
      
      toast.success(`${mappedInstances.length} instância(s) encontrada(s)`);
    } catch (error) {
      console.error('Error fetching instances:', error);
      setConnectionError('Não foi possível conectar à Evolution API. Verifique se o serviço está rodando.');
      toast.error('Erro ao buscar instâncias');
    } finally {
      setLoading(false);
    }
  };

  const fetchConversations = async () => {
    try {
      setLoading(true);
      
      const contacts = await whatsappService.fetchContacts();
      
      const mappedConversations: Conversation[] = contacts
        .filter((c: Contact) => c.id && !c.id.includes('@g.us'))
        .slice(0, 50)
        .map((contact: Contact) => ({
          id: contact.id,
          contact: {
            id: contact.id,
            name: contact.pushName || whatsappService.formatJidToPhone(contact.id),
            phone: whatsappService.formatJidToPhone(contact.id),
            avatar: contact.profilePictureUrl,
            jid: contact.id,
          },
          messages: [],
          instance_id: selectedInstance || '',
          is_bot_active: false,
        }));
      
      setConversations(mappedConversations);
    } catch (error) {
      console.error('Error fetching conversations:', error);
      setConversations([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async (jid: string) => {
    try {
      setLoading(true);
      
      const result = await whatsappService.fetchMessages(jid, 50);
      
      const mappedMessages: Message[] = (result.messages || []).map((msg: ChatMessage) => ({
        id: msg.key.id,
        content: whatsappService.getMessageText(msg.message),
        sender: (msg.key.fromMe ? 'user' : 'contact') as 'user' | 'contact',
        timestamp: msg.messageTimestamp 
          ? new Date(msg.messageTimestamp * 1000).toISOString()
          : new Date().toISOString(),
        status: 'read' as const,
      })).reverse();
      
      setMessages(mappedMessages);
    } catch (error) {
      console.error('Error fetching messages:', error);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };

  const createInstance = async () => {
    if (!newInstanceName.trim()) {
      toast.error('Nome da instância é obrigatório');
      return;
    }

    try {
      setLoading(true);
      const result = await whatsappService.createInstance(newInstanceName);
      
      toast.success('Instância criada com sucesso');
      setNewInstanceName('');
      setShowCreateInstance(false);
      
      if (result.qrcode?.base64) {
        setQrCodeData(result.qrcode.base64);
        setShowQRCode(true);
      }
      
      fetchInstances();
    } catch (error) {
      toast.error('Erro ao criar instância');
    } finally {
      setLoading(false);
    }
  };

  const deleteInstance = async (name: string) => {
    try {
      setLoading(true);
      whatsappService.setInstance(name);
      await whatsappService.deleteInstance();
      toast.success('Instância removida');
      fetchInstances();
    } catch (error) {
      toast.error('Erro ao remover instância');
    } finally {
      setLoading(false);
    }
  };

  const connectInstance = async (name: string) => {
    try {
      setLoading(true);
      whatsappService.setInstance(name);
      
      const qrResponse = await whatsappService.connectInstance();
      
      if (qrResponse.base64) {
        setQrCodeData(qrResponse.base64);
        setShowQRCode(true);
        startConnectionPolling(name);
      }
      
      toast.info('Escaneie o QR Code para conectar');
    } catch (error) {
      toast.error('Erro ao conectar');
    } finally {
      setLoading(false);
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const startConnectionPolling = (_instanceName: string) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
    
    pollIntervalRef.current = setInterval(async () => {
      try {
        const state = await whatsappService.getConnectionState();
        
        if (state.instance.state === 'open') {
          toast.success('WhatsApp conectado com sucesso!');
          setShowQRCode(false);
          setQrCodeData(null);
          fetchInstances();
          
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        }
      } catch (error) {
        console.error('Error polling connection status:', error);
      }
    }, 3000);
    
    setTimeout(() => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }, 120000);
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedConversation) return;

    try {
      setLoading(true);
      
      const result = await whatsappService.sendText(
        selectedConversation.contact.phone,
        newMessage
      );
      
      const newMsg: Message = {
        id: result.key.id,
        content: newMessage,
        sender: 'user',
        timestamp: new Date().toISOString(),
        status: 'sent',
      };
      
      setMessages(prev => [...prev, newMsg]);
      setNewMessage('');
      toast.success('Mensagem enviada');
    } catch (error) {
      toast.error('Erro ao enviar mensagem');
    } finally {
      setLoading(false);
    }
  };

  const testWhatsAppFlow = useCallback(async () => {
    setLoading(true);
    setTestResult(null);
    
    try {
      const state = await whatsappService.getConnectionState();
      
      if (state.instance.state !== 'open') {
        setTestResult({
          success: false,
          message: `WhatsApp não conectado. Estado atual: ${state.instance.state}`
        });
        return;
      }
      
      const instance = await whatsappService.getCurrentInstance();
      
      if (!instance?.owner) {
        setTestResult({
          success: false,
          message: 'Instância sem número vinculado'
        });
        return;
      }
      
      const phone = instance.owner.replace('@s.whatsapp.net', '');
      const testMessage = `🧪 TESTE AUTOMATIZADO - Didin Fácil

✅ Sistema: Operacional
📱 Instância: ${instance.instanceName}
⏰ Data: ${new Date().toLocaleString('pt-BR')}

Para testar o chatbot, envie:
1 - Buscar produtos
2 - Comparar preços
3 - Alertas
4 - Falar com atendente`;
      
      await whatsappService.sendText(phone, testMessage);
      
      setTestResult({
        success: true,
        message: `Mensagem de teste enviada para ${phone}. Verifique seu WhatsApp!`
      });
      
      toast.success('Teste concluído com sucesso!');
      
    } catch (error) {
      console.error('Test failed:', error);
      setTestResult({
        success: false,
        message: `Erro no teste: ${error instanceof Error ? error.message : 'Erro desconhecido'}`
      });
    } finally {
      setLoading(false);
    }
  }, []);

  const toggleBot = async () => {
    if (!selectedConversation) return;

    setSelectedConversation({
      ...selectedConversation,
      is_bot_active: !selectedConversation.is_bot_active,
    });
    
    toast.success(selectedConversation.is_bot_active ? 'Bot desativado' : 'Bot ativado');
  };

  const getStatusColor = (status: Instance['status']) => {
    switch (status) {
      case 'connected': return 'bg-green-500';
      case 'disconnected': return 'bg-red-500';
      case 'connecting': return 'bg-yellow-500';
      case 'qrcode': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: Instance['status']) => {
    switch (status) {
      case 'connected': return <Wifi className="h-4 w-4 text-green-500" />;
      case 'disconnected': return <WifiOff className="h-4 w-4 text-red-500" />;
      case 'connecting': return <RefreshCw className="h-4 w-4 text-yellow-500 animate-spin" />;
      case 'qrcode': return <QrCode className="h-4 w-4 text-blue-500" />;
      default: return <WifiOff className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 86400000) {
      return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    } else if (diff < 172800000) {
      return 'Ontem';
    } else {
      return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    }
  };

  const filteredConversations = conversations.filter(conv =>
    conv.contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.contact.phone.includes(searchQuery)
  );

  const currentInstance = instances.find(i => i.name === selectedInstance);

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-background">
      {/* Left Sidebar - Instance List */}
      <div className="w-16 border-r bg-muted/30 flex flex-col items-center py-4 gap-2">
        <button
          onClick={testWhatsAppFlow}
          disabled={loading}
          className="p-3 rounded-xl hover:bg-green-500/20 text-green-500 transition-all"
          title="Testar Fluxo Completo"
        >
          {loading ? (
            <RefreshCw className="h-5 w-5 animate-spin" />
          ) : (
            <CheckCircle className="h-5 w-5" />
          )}
        </button>
        
        <div className="h-px w-8 bg-border my-2" />
        
        {instances.map((instance) => (
          <button
            key={instance.id}
            onClick={() => {
              setSelectedInstance(instance.name);
              whatsappService.setInstance(instance.name);
            }}
            className={`relative p-3 rounded-xl transition-all ${
              selectedInstance === instance.name 
                ? 'bg-primary text-primary-foreground' 
                : 'hover:bg-muted'
            }`}
            title={`${instance.name}${instance.phone_number ? ` (${instance.phone_number})` : ''}`}
          >
            <Phone className="h-5 w-5" />
            <span className={`absolute bottom-1 right-1 h-2.5 w-2.5 rounded-full ${getStatusColor(instance.status)}`} />
          </button>
        ))}
        
        <Dialog open={showCreateInstance} onOpenChange={setShowCreateInstance}>
          <DialogTrigger asChild>
            <button className="p-3 rounded-xl hover:bg-muted text-muted-foreground">
              <Plus className="h-5 w-5" />
            </button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nova Instância WhatsApp</DialogTitle>
              <DialogDescription>
                Crie uma nova conexão WhatsApp para gerenciar conversas.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="instance-name">Nome da Instância</Label>
                <Input
                  id="instance-name"
                  placeholder="Ex: vendas-principal"
                  value={newInstanceName}
                  onChange={(e) => setNewInstanceName(e.target.value)}
                />
                <p className="text-sm text-muted-foreground">
                  Use apenas letras minúsculas, números e hífens
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateInstance(false)}>
                Cancelar
              </Button>
              <Button onClick={createInstance} disabled={loading}>
                {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : null}
                Criar Instância
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Conversations List */}
      <div className="w-80 border-r flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {currentInstance && getStatusIcon(currentInstance.status)}
              <h2 className="font-semibold">{currentInstance?.name || 'WhatsApp'}</h2>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>Ações</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => fetchInstances()}>
                  <RefreshCw className="h-4 w-4 mr-2" /> Atualizar
                </DropdownMenuItem>
                {currentInstance?.status === 'disconnected' && (
                  <DropdownMenuItem onClick={() => connectInstance(currentInstance.name)}>
                    <QrCode className="h-4 w-4 mr-2" /> Conectar
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem 
                  className="text-destructive"
                  onClick={() => currentInstance && deleteInstance(currentInstance.name)}
                >
                  <Trash2 className="h-4 w-4 mr-2" /> Remover
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          
          {connectionError && (
            <Alert variant="destructive" className="mb-3">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-xs">
                {connectionError}
              </AlertDescription>
            </Alert>
          )}
          
          {testResult && (
            <Alert variant={testResult.success ? "default" : "destructive"} className="mb-3">
              {testResult.success ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <AlertDescription className="text-xs">
                {testResult.message}
              </AlertDescription>
            </Alert>
          )}
          
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar conversas..."
              className="pl-9"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {currentInstance && (
          <div className="px-4 py-2 border-b bg-muted/30">
            <div className="flex items-center gap-2">
              <Avatar className="h-8 w-8">
                <AvatarImage src={currentInstance.profile_picture} />
                <AvatarFallback>
                  {currentInstance.name.substring(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {currentInstance.phone_number || currentInstance.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {currentInstance.status === 'connected' ? '🟢 Conectado' : '🔴 Desconectado'}
                </p>
              </div>
            </div>
          </div>
        )}

        <ScrollArea className="flex-1">
          {filteredConversations.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Nenhuma conversa encontrada</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-4"
                onClick={() => fetchConversations()}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Recarregar
              </Button>
            </div>
          ) : (
            filteredConversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => setSelectedConversation(conv)}
                className={`p-4 border-b cursor-pointer hover:bg-muted/50 transition-colors ${
                  selectedConversation?.id === conv.id ? 'bg-muted' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <Avatar>
                    <AvatarImage src={conv.contact.avatar} />
                    <AvatarFallback>
                      {conv.contact.name.substring(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="font-medium truncate">{conv.contact.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {conv.contact.last_message_time && formatTime(conv.contact.last_message_time)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <p className="text-sm text-muted-foreground truncate">
                        {conv.contact.phone}
                      </p>
                      <div className="flex items-center gap-1">
                        {conv.is_bot_active && (
                          <Bot className="h-3.5 w-3.5 text-blue-500" />
                        )}
                        {conv.contact.unread_count ? (
                          <Badge variant="default" className="h-5 min-w-5 rounded-full text-xs">
                            {conv.contact.unread_count}
                          </Badge>
                        ) : null}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </ScrollArea>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedConversation ? (
          <>
            <div className="p-4 border-b flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Avatar>
                  <AvatarImage src={selectedConversation.contact.avatar} />
                  <AvatarFallback>
                    {selectedConversation.contact.name.substring(0, 2).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <h3 className="font-semibold">{selectedConversation.contact.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {selectedConversation.contact.phone}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant={selectedConversation.is_bot_active ? "default" : "outline"}
                  size="sm"
                  onClick={toggleBot}
                >
                  <Bot className="h-4 w-4 mr-1" />
                  {selectedConversation.is_bot_active ? 'Bot Ativo' : 'Ativar Bot'}
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>
                      <Users className="h-4 w-4 mr-2" /> Ver Contato
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <FileText className="h-4 w-4 mr-2" /> Exportar Chat
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>

            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>Nenhuma mensagem ainda</p>
                  </div>
                ) : (
                  messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[70%] rounded-2xl px-4 py-2 ${
                          message.sender === 'user'
                            ? 'bg-primary text-primary-foreground rounded-br-md'
                            : 'bg-muted rounded-bl-md'
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        <div className={`flex items-center gap-1 mt-1 ${
                          message.sender === 'user' ? 'justify-end' : 'justify-start'
                        }`}>
                          <span className="text-[10px] opacity-70">
                            {formatTime(message.timestamp)}
                          </span>
                          {message.sender === 'user' && message.status && (
                            <span className="text-[10px]">
                              {message.status === 'read' ? (
                                <Check className="h-3 w-3 text-blue-400" />
                              ) : message.status === 'delivered' ? (
                                <Check className="h-3 w-3" />
                              ) : message.status === 'sent' ? (
                                <Check className="h-3 w-3 opacity-50" />
                              ) : (
                                <X className="h-3 w-3 text-red-400" />
                              )}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            <div className="p-4 border-t">
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="icon">
                  <Smile className="h-5 w-5 text-muted-foreground" />
                </Button>
                <Button variant="ghost" size="icon">
                  <Paperclip className="h-5 w-5 text-muted-foreground" />
                </Button>
                <Input
                  placeholder="Digite uma mensagem..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                  className="flex-1"
                />
                <Button onClick={sendMessage} disabled={!newMessage.trim() || loading}>
                  {loading ? (
                    <RefreshCw className="h-5 w-5 animate-spin" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageSquare className="h-16 w-16 mx-auto mb-4 text-muted-foreground/50" />
              <h3 className="text-xl font-semibold mb-2">Selecione uma conversa</h3>
              <p className="text-muted-foreground mb-4">
                Escolha uma conversa na lista para começar a enviar mensagens
              </p>
              <Button onClick={testWhatsAppFlow} disabled={loading}>
                {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                Testar Fluxo Completo
              </Button>
            </div>
          </div>
        )}
      </div>

      <Dialog open={showQRCode} onOpenChange={setShowQRCode}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Conectar WhatsApp</DialogTitle>
            <DialogDescription>
              Escaneie o QR Code abaixo com seu WhatsApp para conectar.
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-center justify-center p-8">
            {qrCodeData ? (
              <img 
                src={qrCodeData.startsWith('data:') ? qrCodeData : `data:image/png;base64,${qrCodeData}`}
                alt="QR Code" 
                className="w-64 h-64"
              />
            ) : (
              <div className="w-64 h-64 bg-muted rounded-lg flex items-center justify-center">
                <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowQRCode(false);
              if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
                pollIntervalRef.current = null;
              }
            }}>
              Fechar
            </Button>
            <Button onClick={() => currentInstance && connectInstance(currentInstance.name)}>
              <RefreshCw className="h-4 w-4 mr-2" /> Atualizar QR Code
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default WhatsappPage;
