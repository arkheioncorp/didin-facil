import { useState, useEffect } from 'react'
import { 
  Zap, 
  MessageSquare, 
  Image, 
  Building2, 
  Search,
  Filter,
  Download,
  Copy,
  ExternalLink,
  Clock,
  Star,
  ChevronRight,
  Play,
  BookOpen,
  Settings2,
  Sparkles
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/hooks/use-toast'
import { api } from '@/lib/api'

interface Template {
  id: string
  name: string
  description: string
  category: string
  difficulty?: string
  estimated_time?: string
  tags?: string[]
  required_integrations?: string[]
  platform?: string
  content_type?: string
  recommended_workflows?: string[]
  recommended_chatbots?: string[]
}

interface LibraryStats {
  summary: {
    total_templates: number
    automation_workflows: number
    chatbot_flows: number
    content_templates: number
    business_presets: number
  }
}

interface TemplateResponse {
  templates: Template[]
}

interface ExportResponse {
  workflow?: unknown
  flow?: unknown
}

interface PresetApplyResponse {
  setup_steps: unknown[]
}

const difficultyColors: Record<string, string> = {
  beginner: 'bg-green-100 text-green-700',
  intermediate: 'bg-yellow-100 text-yellow-700',
  advanced: 'bg-red-100 text-red-700',
}

// Category icons (disponível para uso futuro)
const _categoryIcons: Record<string, React.ReactNode> = {
  alerts: <Zap className="h-4 w-4" />,
  marketing: <Sparkles className="h-4 w-4" />,
  customer_success: <Star className="h-4 w-4" />,
  operations: <Settings2 className="h-4 w-4" />,
  analytics: <BookOpen className="h-4 w-4" />,
}
void _categoryIcons // Previne warning de variável não usada

export default function TemplateLibrary() {
  const [activeTab, setActiveTab] = useState('automation')
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [stats, setStats] = useState<LibraryStats | null>(null)
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    loadStats()
  }, [])

  useEffect(() => {
    loadTemplates()
  }, [activeTab, categoryFilter])

  const loadStats = async () => {
    try {
      const response = await api.get<LibraryStats>('/api/v1/templates/library/stats')
      setStats(response.data)
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error)
    }
  }

  const loadTemplates = async () => {
    setLoading(true)
    try {
      const endpoint = `/api/v1/templates/library/${activeTab}`
      const params: Record<string, string> = categoryFilter ? { category: categoryFilter } : {}
      const response = await api.get<TemplateResponse>(endpoint, { params })
      setTemplates(response.data.templates || [])
    } catch (error) {
      console.error('Erro ao carregar templates:', error)
      setTemplates([])
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (templateId: string) => {
    try {
      const endpoint = activeTab === 'automation' 
        ? '/api/v1/templates/library/automation/export'
        : '/api/v1/templates/library/chatbot/export'
      
      const response = await api.post<ExportResponse>(endpoint, { template_id: templateId })
      
      // Copiar para clipboard
      const json = JSON.stringify(response.data.workflow || response.data.flow, null, 2)
      await navigator.clipboard.writeText(json)
      
      toast({
        title: 'Template exportado!',
        description: 'JSON copiado para a área de transferência.',
      })
    } catch (error) {
      console.error('Erro ao exportar:', error)
      toast({
        title: 'Erro ao exportar',
        description: 'Tente novamente mais tarde.',
        variant: 'destructive',
      })
    }
  }

  const handleApplyPreset = async (presetId: string) => {
    try {
      const response = await api.post<PresetApplyResponse>(`/api/v1/templates/library/presets/${presetId}/apply`)
      setSelectedTemplate(null)
      
      toast({
        title: 'Preset aplicado!',
        description: `${response.data.setup_steps.length} etapas de configuração disponíveis.`,
      })
    } catch (error) {
      console.error('Erro ao aplicar preset:', error)
      toast({
        title: 'Erro ao aplicar preset',
        description: 'Tente novamente mais tarde.',
        variant: 'destructive',
      })
    }
  }

  const filteredTemplates = templates.filter(t => 
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.description.toLowerCase().includes(search.toLowerCase())
  )

  const getCategoryOptions = () => {
    switch (activeTab) {
      case 'automation':
        return ['alerts', 'marketing', 'customer_success', 'operations', 'analytics']
      case 'chatbot':
        return ['atendimento', 'vendas', 'suporte', 'qualificacao', 'agendamento', 'faq']
      case 'content':
        return ['promo', 'educacional', 'engajamento', 'lancamento', 'social_proof', 'bastidores']
      case 'presets':
        return ['ecommerce', 'infoprodutos', 'servicos', 'saas', 'varejo', 'alimentacao']
      default:
        return []
    }
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Biblioteca de Templates</h1>
          <p className="text-muted-foreground">
            Templates prontos para automação, chatbots, conteúdo e configurações de negócio
          </p>
        </div>
        
        {stats && (
          <div className="flex gap-4">
            <Badge variant="secondary" className="text-sm py-1 px-3">
              {stats.summary.total_templates} templates disponíveis
            </Badge>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setActiveTab('automation')}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Automações</CardTitle>
              <Zap className="h-4 w-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.summary.automation_workflows}</div>
              <p className="text-xs text-muted-foreground">Workflows n8n prontos</p>
            </CardContent>
          </Card>
          
          <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setActiveTab('chatbot')}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Chatbots</CardTitle>
              <MessageSquare className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.summary.chatbot_flows}</div>
              <p className="text-xs text-muted-foreground">Fluxos Typebot</p>
            </CardContent>
          </Card>
          
          <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setActiveTab('content')}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Conteúdo</CardTitle>
              <Image className="h-4 w-4 text-pink-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.summary.content_templates}</div>
              <p className="text-xs text-muted-foreground">Templates de posts</p>
            </CardContent>
          </Card>
          
          <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setActiveTab('presets')}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Presets</CardTitle>
              <Building2 className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.summary.business_presets}</div>
              <p className="text-xs text-muted-foreground">Configurações prontas</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs & Filters */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <TabsList className="grid w-full md:w-auto grid-cols-4">
            <TabsTrigger value="automation" className="gap-2">
              <Zap className="h-4 w-4" />
              <span className="hidden sm:inline">Automação</span>
            </TabsTrigger>
            <TabsTrigger value="chatbot" className="gap-2">
              <MessageSquare className="h-4 w-4" />
              <span className="hidden sm:inline">Chatbot</span>
            </TabsTrigger>
            <TabsTrigger value="content" className="gap-2">
              <Image className="h-4 w-4" />
              <span className="hidden sm:inline">Conteúdo</span>
            </TabsTrigger>
            <TabsTrigger value="presets" className="gap-2">
              <Building2 className="h-4 w-4" />
              <span className="hidden sm:inline">Presets</span>
            </TabsTrigger>
          </TabsList>
          
          <div className="flex gap-2">
            <div className="relative flex-1 md:w-64">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar templates..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8"
              />
            </div>
            
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-[180px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Categoria" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Todas</SelectItem>
                {getCategoryOptions().map(cat => (
                  <SelectItem key={cat} value={cat}>
                    {cat.charAt(0).toUpperCase() + cat.slice(1).replace('_', ' ')}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Template Grid */}
        <TabsContent value={activeTab} className="mt-6">
          {loading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <Card key={i} className="animate-pulse">
                  <CardHeader>
                    <div className="h-4 bg-muted rounded w-3/4"></div>
                    <div className="h-3 bg-muted rounded w-full mt-2"></div>
                  </CardHeader>
                  <CardContent>
                    <div className="h-20 bg-muted/50 rounded"></div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredTemplates.length === 0 ? (
            <Card className="py-12">
              <CardContent className="text-center">
                <BookOpen className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium">Nenhum template encontrado</h3>
                <p className="text-muted-foreground">Tente ajustar os filtros de busca</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredTemplates.map(template => (
                <Card 
                  key={template.id} 
                  className="hover:shadow-md transition-shadow cursor-pointer group"
                  onClick={() => setSelectedTemplate(template)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <CardTitle className="text-lg group-hover:text-primary transition-colors">
                          {template.name}
                        </CardTitle>
                        <div className="flex gap-2">
                          <Badge variant="outline">{template.category}</Badge>
                          {template.difficulty && (
                            <Badge className={difficultyColors[template.difficulty]}>
                              {template.difficulty}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                    </div>
                    <CardDescription className="line-clamp-2">
                      {template.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1">
                      {template.tags?.slice(0, 3).map(tag => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                      {template.estimated_time && (
                        <Badge variant="secondary" className="text-xs gap-1">
                          <Clock className="h-3 w-3" />
                          {template.estimated_time}
                        </Badge>
                      )}
                    </div>
                    
                    {template.required_integrations && template.required_integrations.length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-xs text-muted-foreground mb-1">Integrações necessárias:</p>
                        <div className="flex flex-wrap gap-1">
                          {template.required_integrations.map(int => (
                            <Badge key={int} variant="outline" className="text-xs">
                              {int}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Template Detail Dialog */}
      <Dialog open={!!selectedTemplate} onOpenChange={() => setSelectedTemplate(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          {selectedTemplate && (
            <>
              <DialogHeader>
                <DialogTitle className="text-xl">{selectedTemplate.name}</DialogTitle>
                <DialogDescription>{selectedTemplate.description}</DialogDescription>
              </DialogHeader>
              
              <div className="space-y-6">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{selectedTemplate.category}</Badge>
                  {selectedTemplate.difficulty && (
                    <Badge className={difficultyColors[selectedTemplate.difficulty]}>
                      {selectedTemplate.difficulty}
                    </Badge>
                  )}
                  {selectedTemplate.estimated_time && (
                    <Badge variant="secondary" className="gap-1">
                      <Clock className="h-3 w-3" />
                      {selectedTemplate.estimated_time}
                    </Badge>
                  )}
                </div>

                {selectedTemplate.tags && selectedTemplate.tags.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Tags</h4>
                    <div className="flex flex-wrap gap-1">
                      {selectedTemplate.tags.map(tag => (
                        <Badge key={tag} variant="secondary">{tag}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {selectedTemplate.required_integrations && selectedTemplate.required_integrations.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Integrações Necessárias</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedTemplate.required_integrations.map(int => (
                        <Badge key={int} variant="outline" className="gap-1">
                          <ExternalLink className="h-3 w-3" />
                          {int}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Presets específicos */}
                {activeTab === 'presets' && (
                  <>
                    {selectedTemplate.recommended_workflows && selectedTemplate.recommended_workflows.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium mb-2">Automações Incluídas</h4>
                        <ul className="list-disc list-inside text-sm text-muted-foreground">
                          {selectedTemplate.recommended_workflows.map(wf => (
                            <li key={wf}>{wf.replace(/_/g, ' ')}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {selectedTemplate.recommended_chatbots && selectedTemplate.recommended_chatbots.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium mb-2">Chatbots Incluídos</h4>
                        <ul className="list-disc list-inside text-sm text-muted-foreground">
                          {selectedTemplate.recommended_chatbots.map(cb => (
                            <li key={cb}>{cb.replace(/_/g, ' ')}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </>
                )}

                <div className="flex gap-2 pt-4 border-t">
                  {activeTab === 'automation' && (
                    <Button onClick={() => handleExport(selectedTemplate.id)} className="gap-2">
                      <Download className="h-4 w-4" />
                      Exportar Workflow
                    </Button>
                  )}
                  
                  {activeTab === 'chatbot' && (
                    <Button onClick={() => handleExport(selectedTemplate.id)} className="gap-2">
                      <Download className="h-4 w-4" />
                      Exportar Fluxo
                    </Button>
                  )}
                  
                  {activeTab === 'content' && (
                    <Button className="gap-2">
                      <Copy className="h-4 w-4" />
                      Copiar Template
                    </Button>
                  )}
                  
                  {activeTab === 'presets' && (
                    <Button onClick={() => handleApplyPreset(selectedTemplate.id)} className="gap-2">
                      <Play className="h-4 w-4" />
                      Aplicar Preset
                    </Button>
                  )}
                  
                  <Button variant="outline" onClick={() => setSelectedTemplate(null)}>
                    Fechar
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
