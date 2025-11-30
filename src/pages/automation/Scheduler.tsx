import React, { useState, useRef, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { format, parseISO, isSameDay, addDays, startOfMonth, endOfMonth } from "date-fns";
import { ptBR } from "date-fns/locale";
import { 
  Calendar as CalendarIcon, 
  Clock, 
  Upload, 
  Plus,
  CheckCircle2, 
  XCircle,
  Loader2,
  Trash2,
  Instagram,
  Youtube,
  MessageCircle,
  AlertCircle,
  AlertTriangle,
  PlayCircle,
  Filter,
  BarChart3,
  Image,
  Video,
  FileText,
  Timer,
  ChevronLeft,
  ChevronRight
} from "lucide-react";

// TikTok icon component (não existe no lucide)
const TikTokIcon = () => (
  <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current">
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
  </svg>
);

interface ScheduledPost {
  id: string;
  platform: string;
  scheduled_time: string;
  status: string;
  content_type: string;
  caption: string;
  created_at: string;
  published_at: string | null;
}

interface SchedulerStats {
  total: number;
  scheduled: number;
  published: number;
  failed: number;
  cancelled: number;
  by_platform: Record<string, number>;
}

const PLATFORM_CONFIG = {
  instagram: {
    name: "Instagram",
    icon: Instagram,
    color: "bg-gradient-to-r from-purple-500 to-pink-500",
    contentTypes: [
      { value: "photo", label: "Foto" },
      { value: "video", label: "Vídeo" },
      { value: "reel", label: "Reels" },
      { value: "story", label: "Story" }
    ]
  },
  tiktok: {
    name: "TikTok",
    icon: TikTokIcon,
    color: "bg-black",
    contentTypes: [
      { value: "video", label: "Vídeo" }
    ]
  },
  youtube: {
    name: "YouTube",
    icon: Youtube,
    color: "bg-red-600",
    contentTypes: [
      { value: "video", label: "Vídeo" },
      { value: "short", label: "Short" }
    ]
  },
  whatsapp: {
    name: "WhatsApp",
    icon: MessageCircle,
    color: "bg-green-500",
    contentTypes: [
      { value: "text", label: "Texto" }
    ]
  }
};

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  scheduled: { label: "Agendado", color: "bg-blue-500", icon: Timer },
  processing: { label: "Processando", color: "bg-yellow-500", icon: Loader2 },
  published: { label: "Publicado", color: "bg-green-500", icon: CheckCircle2 },
  failed: { label: "Falhou", color: "bg-red-500", icon: XCircle },
  cancelled: { label: "Cancelado", color: "bg-muted-foreground", icon: AlertCircle }
};

export const Scheduler = () => {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Posts state
  const [posts, setPosts] = useState<ScheduledPost[]>([]);
  const [stats, setStats] = useState<SchedulerStats | null>(null);
  const [dlqCount, setDlqCount] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  
  // Calendar state
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());
  
  // New post form
  const [newPost, setNewPost] = useState({
    platform: "instagram",
    contentType: "photo",
    scheduledDate: new Date(),
    scheduledTime: "12:00",
    caption: "",
    hashtags: "",
    accountName: ""
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitLoading, setSubmitLoading] = useState(false);
  
  // Fetch data
  const fetchPosts = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (statusFilter && statusFilter !== "all") {
        params.status = statusFilter;
      }
      const response = await api.get<{ posts: ScheduledPost[]; total: number }>("/scheduler/posts", { params });
      setPosts(response.data.posts || []);
    } catch (error) {
      console.error("Error fetching posts:", error);
      toast({ title: "Erro ao carregar posts", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [statusFilter, toast]);

  const fetchStats = async () => {
    try {
      const response = await api.get<SchedulerStats>("/scheduler/stats");
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const fetchDlqCount = async () => {
    try {
      const response = await api.get<{ total: number }>("/scheduler/dlq/stats");
      setDlqCount(response.data.total || 0);
    } catch (error) {
      console.error("Error fetching DLQ stats:", error);
    }
  };

  useEffect(() => {
    fetchPosts();
    fetchStats();
    fetchDlqCount();
  }, [fetchPosts]);

  // Handlers
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSchedulePost = async () => {
    if (!selectedFile && newPost.platform !== "whatsapp") {
      toast({ title: "Selecione um arquivo", variant: "destructive" });
      return;
    }

    if (!newPost.caption.trim()) {
      toast({ title: "Adicione uma legenda", variant: "destructive" });
      return;
    }

    setSubmitLoading(true);
    try {
      const formData = new FormData();
      formData.append("platform", newPost.platform);
      formData.append("content_type", newPost.contentType);
      formData.append("caption", newPost.caption);
      formData.append("hashtags", newPost.hashtags);
      
      // Combine date and time
      const [hours, minutes] = newPost.scheduledTime.split(":");
      const scheduledDateTime = new Date(newPost.scheduledDate);
      scheduledDateTime.setHours(parseInt(hours), parseInt(minutes), 0, 0);
      formData.append("scheduled_time", scheduledDateTime.toISOString());
      
      if (newPost.accountName) {
        formData.append("account_name", newPost.accountName);
      }
      
      if (selectedFile) {
        formData.append("file", selectedFile);
      }

      await api.post("/scheduler/posts/with-file", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      
      toast({ title: "Post agendado com sucesso!" });
      
      // Reset form
      setNewPost({
        platform: "instagram",
        contentType: "photo",
        scheduledDate: new Date(),
        scheduledTime: "12:00",
        caption: "",
        hashtags: "",
        accountName: ""
      });
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      
      // Refresh data
      fetchPosts();
      fetchStats();
      
    } catch (error: unknown) {
      console.error("Error scheduling post:", error);
      const message = error instanceof Error ? error.message : "Erro ao agendar post";
      toast({ title: message, variant: "destructive" });
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleCancelPost = async (postId: string) => {
    try {
      await api.delete(`/scheduler/posts/${postId}`);
      toast({ title: "Post cancelado" });
      fetchPosts();
      fetchStats();
    } catch (error) {
      console.error("Error cancelling post:", error);
      toast({ title: "Erro ao cancelar post", variant: "destructive" });
    }
  };

  // Filter posts by selected date
  const postsForSelectedDate = posts.filter(post => 
    isSameDay(parseISO(post.scheduled_time), selectedDate)
  );

  // Get dates with posts for calendar highlighting
  const datesWithPosts = posts.reduce((acc, post) => {
    const date = parseISO(post.scheduled_time).toDateString();
    acc[date] = (acc[date] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Platform icon helper
  const getPlatformIcon = (platform: string) => {
    const config = PLATFORM_CONFIG[platform as keyof typeof PLATFORM_CONFIG];
    if (!config) return null;
    const Icon = config.icon;
    return <Icon />;
  };

  const getContentTypeIcon = (contentType: string) => {
    switch (contentType) {
      case "photo": return <Image className="h-4 w-4" />;
      case "video": case "reel": case "short": return <Video className="h-4 w-4" />;
      case "text": return <FileText className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header com Stats */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <CalendarIcon className="h-8 w-8" />
            Agendador de Posts
          </h1>
          <p className="text-muted-foreground mt-1">
            Gerencie publicações em todas as plataformas
          </p>
        </div>
        
        {stats && (
          <div className="flex gap-4">
            <Card className="px-4 py-2">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Total:</span>
                <span className="font-bold">{stats.total}</span>
              </div>
            </Card>
            <Card className="px-4 py-2">
              <div className="flex items-center gap-2">
                <Timer className="h-4 w-4 text-blue-500" />
                <span className="text-sm text-muted-foreground">Agendados:</span>
                <span className="font-bold text-blue-500">{stats.scheduled}</span>
              </div>
            </Card>
            <Card className="px-4 py-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span className="text-sm text-muted-foreground">Publicados:</span>
                <span className="font-bold text-green-500">{stats.published}</span>
              </div>
            </Card>
          </div>
        )}
      </div>

      {/* DLQ Alert Banner */}
      {dlqCount > 0 && (
        <Link to="/automation/dlq">
          <Card className="bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800 cursor-pointer hover:shadow-md transition-shadow">
            <CardContent className="py-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <div>
                  <p className="font-medium text-red-700 dark:text-red-300">
                    {dlqCount} post{dlqCount > 1 ? 's' : ''} com falha
                  </p>
                  <p className="text-sm text-red-600 dark:text-red-400">
                    Clique para revisar e tentar novamente
                  </p>
                </div>
              </div>
              <Button variant="destructive" size="sm">
                Ver Dead Letter Queue
              </Button>
            </CardContent>
          </Card>
        </Link>
      )}

      <Tabs defaultValue="calendar" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-3">
          <TabsTrigger value="calendar" className="flex items-center gap-2">
            <CalendarIcon className="h-4 w-4" />
            Calendário
          </TabsTrigger>
          <TabsTrigger value="new" className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Novo Post
          </TabsTrigger>
          <TabsTrigger value="list" className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Lista
          </TabsTrigger>
        </TabsList>

        {/* Tab: Calendário */}
        <TabsContent value="calendar" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Calendário */}
            <Card className="lg:col-span-2">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle>Calendário de Publicações</CardTitle>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setCurrentMonth(addDays(startOfMonth(currentMonth), -1))}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <span className="font-medium w-32 text-center">
                    {format(currentMonth, "MMMM yyyy", { locale: ptBR })}
                  </span>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setCurrentMonth(addDays(endOfMonth(currentMonth), 1))}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Calendar
                  mode="single"
                  selected={selectedDate}
                  onSelect={(date: Date | undefined) => date && setSelectedDate(date)}
                  month={currentMonth}
                  onMonthChange={setCurrentMonth}
                  locale={ptBR}
                  className="rounded-md border"
                  modifiers={{
                    hasPost: (date: Date) => datesWithPosts[date.toDateString()] > 0
                  }}
                  modifiersClassNames={{
                    hasPost: "bg-primary/20 font-bold"
                  }}
                />
              </CardContent>
            </Card>

            {/* Posts do dia selecionado */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>
                    {format(selectedDate, "dd 'de' MMMM", { locale: ptBR })}
                  </span>
                  <Badge variant="secondary">
                    {postsForSelectedDate.length} post{postsForSelectedDate.length !== 1 && "s"}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  {postsForSelectedDate.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                      <CalendarIcon className="h-8 w-8 mb-2 opacity-50" />
                      <p>Nenhum post agendado</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {postsForSelectedDate.map((post) => {
                        const statusConfig = STATUS_CONFIG[post.status];
                        const platformConfig = PLATFORM_CONFIG[post.platform as keyof typeof PLATFORM_CONFIG];
                        
                        return (
                          <Card key={post.id} className="p-3">
                            <div className="flex items-start justify-between">
                              <div className="flex items-center gap-2">
                                <div className={`p-1.5 rounded ${platformConfig?.color || "bg-muted-foreground"} text-white`}>
                                  {getPlatformIcon(post.platform)}
                                </div>
                                <div>
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium text-sm">
                                      {format(parseISO(post.scheduled_time), "HH:mm")}
                                    </span>
                                    <Badge 
                                      variant="secondary" 
                                      className={`${statusConfig?.color} text-white text-xs`}
                                    >
                                      {statusConfig?.label || post.status}
                                    </Badge>
                                  </div>
                                  <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                                    {post.caption}
                                  </p>
                                </div>
                              </div>
                              {post.status === "scheduled" && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleCancelPost(post.id)}
                                  className="text-red-500 hover:text-red-600"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              )}
                            </div>
                          </Card>
                        );
                      })}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab: Novo Post */}
        <TabsContent value="new" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                Agendar Novo Post
              </CardTitle>
              <CardDescription>
                Configure e agende uma publicação para qualquer plataforma
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Coluna Esquerda - Configurações */}
                <div className="space-y-4">
                  {/* Plataforma */}
                  <div className="space-y-2">
                    <Label>Plataforma</Label>
                    <div className="grid grid-cols-4 gap-2">
                      {Object.entries(PLATFORM_CONFIG).map(([key, config]) => {
                        const Icon = config.icon;
                        return (
                          <Button
                            key={key}
                            variant={newPost.platform === key ? "default" : "outline"}
                            className={`flex flex-col items-center gap-1 h-auto py-3 ${
                              newPost.platform === key ? config.color : ""
                            }`}
                            onClick={() => {
                              setNewPost({
                                ...newPost,
                                platform: key,
                                contentType: config.contentTypes[0].value
                              });
                            }}
                          >
                            <Icon />
                            <span className="text-xs">{config.name}</span>
                          </Button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Tipo de Conteúdo */}
                  <div className="space-y-2">
                    <Label>Tipo de Conteúdo</Label>
                    <Select
                      value={newPost.contentType}
                      onValueChange={(value) => setNewPost({ ...newPost, contentType: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PLATFORM_CONFIG[newPost.platform as keyof typeof PLATFORM_CONFIG]?.contentTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            <span className="flex items-center gap-2">
                              {getContentTypeIcon(type.value)}
                              {type.label}
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Data e Hora */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Data</Label>
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button variant="outline" className="w-full justify-start text-left">
                            <CalendarIcon className="mr-2 h-4 w-4" />
                            {format(newPost.scheduledDate, "dd/MM/yyyy")}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0">
                          <Calendar
                            mode="single"
                            selected={newPost.scheduledDate}
                            onSelect={(date: Date | undefined) => date && setNewPost({ ...newPost, scheduledDate: date })}
                            locale={ptBR}
                            disabled={(date: Date) => date < new Date()}
                          />
                        </PopoverContent>
                      </Popover>
                    </div>
                    <div className="space-y-2">
                      <Label>Hora</Label>
                      <div className="relative">
                        <Clock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          type="time"
                          value={newPost.scheduledTime}
                          onChange={(e) => setNewPost({ ...newPost, scheduledTime: e.target.value })}
                          className="pl-9"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Conta (opcional) */}
                  <div className="space-y-2">
                    <Label>Conta (opcional)</Label>
                    <Input
                      placeholder="Nome da conta configurada"
                      value={newPost.accountName}
                      onChange={(e) => setNewPost({ ...newPost, accountName: e.target.value })}
                    />
                  </div>

                  {/* Upload de Arquivo */}
                  {newPost.platform !== "whatsapp" && (
                    <div className="space-y-2">
                      <Label>Arquivo</Label>
                      <div 
                        className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-primary transition-colors"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        {selectedFile ? (
                          <div className="flex items-center justify-center gap-2">
                            {getContentTypeIcon(newPost.contentType)}
                            <span className="text-sm">{selectedFile.name}</span>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedFile(null);
                                if (fileInputRef.current) fileInputRef.current.value = "";
                              }}
                            >
                              <XCircle className="h-4 w-4" />
                            </Button>
                          </div>
                        ) : (
                          <div className="text-muted-foreground">
                            <Upload className="h-8 w-8 mx-auto mb-2" />
                            <p>Clique para selecionar arquivo</p>
                            <p className="text-xs">ou arraste e solte</p>
                          </div>
                        )}
                        <input
                          ref={fileInputRef}
                          type="file"
                          className="hidden"
                          accept={newPost.contentType === "photo" ? "image/*" : "video/*"}
                          onChange={handleFileSelect}
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Coluna Direita - Conteúdo */}
                <div className="space-y-4">
                  {/* Legenda */}
                  <div className="space-y-2">
                    <Label>Legenda</Label>
                    <Textarea
                      placeholder="Escreva sua legenda aqui..."
                      value={newPost.caption}
                      onChange={(e) => setNewPost({ ...newPost, caption: e.target.value })}
                      className="min-h-[200px]"
                    />
                    <p className="text-xs text-muted-foreground text-right">
                      {newPost.caption.length} caracteres
                    </p>
                  </div>

                  {/* Hashtags */}
                  <div className="space-y-2">
                    <Label>Hashtags</Label>
                    <Input
                      placeholder="#marketing, #vendas, #socialmedia"
                      value={newPost.hashtags}
                      onChange={(e) => setNewPost({ ...newPost, hashtags: e.target.value })}
                    />
                    <p className="text-xs text-muted-foreground">
                      Separe por vírgula ou espaço
                    </p>
                  </div>

                  {/* Preview */}
                  <Card className="bg-muted/50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Resumo do Agendamento</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Plataforma:</span>
                        <span className="font-medium flex items-center gap-1">
                          {getPlatformIcon(newPost.platform)}
                          {PLATFORM_CONFIG[newPost.platform as keyof typeof PLATFORM_CONFIG]?.name}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Data/Hora:</span>
                        <span className="font-medium">
                          {format(newPost.scheduledDate, "dd/MM/yyyy")} às {newPost.scheduledTime}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Tipo:</span>
                        <span className="font-medium flex items-center gap-1">
                          {getContentTypeIcon(newPost.contentType)}
                          {PLATFORM_CONFIG[newPost.platform as keyof typeof PLATFORM_CONFIG]
                            ?.contentTypes.find(t => t.value === newPost.contentType)?.label}
                        </span>
                      </div>
                      {selectedFile && (
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Arquivo:</span>
                          <span className="font-medium truncate max-w-[150px]">
                            {selectedFile.name}
                          </span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </div>

              <Separator />

              <div className="flex justify-end gap-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setNewPost({
                      platform: "instagram",
                      contentType: "photo",
                      scheduledDate: new Date(),
                      scheduledTime: "12:00",
                      caption: "",
                      hashtags: "",
                      accountName: ""
                    });
                    setSelectedFile(null);
                  }}
                >
                  Limpar
                </Button>
                <Button
                  onClick={handleSchedulePost}
                  disabled={submitLoading}
                  className="gap-2"
                >
                  {submitLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Agendando...
                    </>
                  ) : (
                    <>
                      <PlayCircle className="h-4 w-4" />
                      Agendar Post
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Lista */}
        <TabsContent value="list" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Todos os Posts</CardTitle>
              <div className="flex items-center gap-2">
                <Label className="text-sm font-normal">Filtrar:</Label>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[150px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    <SelectItem value="scheduled">Agendados</SelectItem>
                    <SelectItem value="published">Publicados</SelectItem>
                    <SelectItem value="failed">Falhos</SelectItem>
                    <SelectItem value="cancelled">Cancelados</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : posts.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                  <CalendarIcon className="h-8 w-8 mb-2 opacity-50" />
                  <p>Nenhum post encontrado</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {posts.map((post) => {
                    const statusConfig = STATUS_CONFIG[post.status];
                    const platformConfig = PLATFORM_CONFIG[post.platform as keyof typeof PLATFORM_CONFIG];
                    const StatusIcon = statusConfig?.icon || AlertCircle;
                    
                    return (
                      <Card key={post.id} className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className={`p-2 rounded-lg ${platformConfig?.color || "bg-muted-foreground"} text-white`}>
                              {getPlatformIcon(post.platform)}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-medium">
                                  {platformConfig?.name || post.platform}
                                </span>
                                <Badge variant="secondary" className="text-xs">
                                  {post.content_type}
                                </Badge>
                                <Badge 
                                  className={`${statusConfig?.color} text-white text-xs flex items-center gap-1`}
                                >
                                  <StatusIcon className="h-3 w-3" />
                                  {statusConfig?.label}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground line-clamp-1 max-w-md mt-1">
                                {post.caption}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right text-sm">
                              <p className="font-medium">
                                {format(parseISO(post.scheduled_time), "dd/MM/yyyy")}
                              </p>
                              <p className="text-muted-foreground">
                                {format(parseISO(post.scheduled_time), "HH:mm")}
                              </p>
                            </div>
                            {post.status === "scheduled" && (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleCancelPost(post.id)}
                                className="text-red-500 hover:text-red-600"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Scheduler;
