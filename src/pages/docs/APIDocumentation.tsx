import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import {
  Search,
  Book,
  Code2,
  Copy,
  ExternalLink,
  Key,
  Zap,
  Shield,
  FileJson,
  ChevronRight,
} from 'lucide-react';
import { api } from '@/lib/api';

interface APICategory {
  name: string;
  description: string;
  icon: string;
  base_path: string;
  endpoints_count: number;
}

interface EndpointExample {
  description: string;
  request?: Record<string, unknown>;
  response: Record<string, unknown>;
  curl_example?: string;
}

interface Endpoint {
  path: string;
  method: string;
  summary: string;
  description: string;
  parameters?: Array<{
    name: string;
    type: string;
    description: string;
    default?: unknown;
  }>;
  examples?: EndpointExample[];
}

interface CategoryDetail {
  name: string;
  description: string;
  icon: string;
  base_path: string;
  endpoints: Endpoint[];
}

interface APIOverview {
  api_name: string;
  version: string;
  description: string;
  base_url: string;
  total_categories: number;
  total_endpoints: number;
  authentication: {
    type: string;
    header: string;
    endpoints: Record<string, string>;
  };
  rate_limiting: {
    default: string;
    authenticated: string;
    header: string;
  };
  documentation_urls: {
    openapi: string;
    swagger_ui: string;
    redoc: string;
  };
  categories: Array<{ name: string; icon: string; base_path: string }>;
}

const methodColors: Record<string, string> = {
  GET: 'bg-green-500/10 text-green-500 border-green-500/20',
  POST: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  PUT: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
  PATCH: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  DELETE: 'bg-red-500/10 text-red-500 border-red-500/20',
};

function CodeBlock({ code }: { code: string }) {
  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    toast.success('Copiado!');
  };

  return (
    <div className="relative group">
      <pre className="bg-zinc-900 text-zinc-100 p-4 rounded-lg overflow-x-auto text-sm font-mono">
        <code>{code}</code>
      </pre>
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-2 right-2 h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={handleCopy}
      >
        <Copy className="h-4 w-4" />
      </Button>
    </div>
  );
}

function EndpointCard({ endpoint, basePath }: { endpoint: Endpoint; basePath: string }) {
  return (
    <Card className="border-l-4" style={{ borderLeftColor: `var(--${endpoint.method.toLowerCase()}-color, #666)` }}>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-3">
          <Badge variant="outline" className={methodColors[endpoint.method]}>
            {endpoint.method}
          </Badge>
          <code className="text-sm font-mono">{basePath}{endpoint.path}</code>
        </div>
        <CardTitle className="text-base mt-2">{endpoint.summary}</CardTitle>
        {endpoint.description && (
          <CardDescription>{endpoint.description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Parameters */}
        {endpoint.parameters && endpoint.parameters.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-2">Parâmetros</h4>
            <div className="space-y-2">
              {endpoint.parameters.map((param) => (
                <div key={param.name} className="flex items-start gap-2 text-sm">
                  <code className="px-1.5 py-0.5 bg-muted rounded text-xs">
                    {param.name}
                  </code>
                  <span className="text-muted-foreground text-xs">{param.type}</span>
                  <span className="text-muted-foreground">{param.description}</span>
                  {param.default !== undefined && (
                    <span className="text-xs text-muted-foreground">
                      (default: {String(param.default)})
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Examples */}
        {endpoint.examples && endpoint.examples.length > 0 && (
          <Accordion type="single" collapsible>
            <AccordionItem value="examples" className="border-none">
              <AccordionTrigger className="text-sm font-medium py-2">
                Exemplos ({endpoint.examples.length})
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  {endpoint.examples.map((example, idx) => (
                    <div key={idx} className="space-y-2">
                      <p className="text-sm text-muted-foreground">{example.description}</p>
                      
                      {example.request && (
                        <div>
                          <p className="text-xs font-medium mb-1">Request:</p>
                          <CodeBlock code={JSON.stringify(example.request, null, 2)} />
                        </div>
                      )}
                      
                      <div>
                        <p className="text-xs font-medium mb-1">Response:</p>
                        <CodeBlock code={JSON.stringify(example.response, null, 2)} />
                      </div>

                      {example.curl_example && (
                        <div>
                          <p className="text-xs font-medium mb-1">cURL:</p>
                          <CodeBlock code={example.curl_example} />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        )}
      </CardContent>
    </Card>
  );
}

function CategorySection({ category }: { category: APICategory }) {
  const [isOpen, setIsOpen] = useState(false);

  const { data: detail, isLoading } = useQuery({
    queryKey: ['api-docs', 'category', category.name],
    queryFn: async () => {
      const response = await api.get(`/api-docs/categories/${encodeURIComponent(category.name)}`);
      return response.data as CategoryDetail;
    },
    enabled: isOpen,
  });

  return (
    <Card>
      <CardHeader
        className="cursor-pointer hover:bg-muted/50 transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{category.icon}</span>
            <div>
              <CardTitle className="text-lg">{category.name}</CardTitle>
              <CardDescription>{category.description}</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{category.endpoints_count} endpoints</Badge>
            <ChevronRight
              className={`h-5 w-5 text-muted-foreground transition-transform ${isOpen ? 'rotate-90' : ''}`}
            />
          </div>
        </div>
      </CardHeader>
      
      {isOpen && (
        <CardContent className="pt-0 space-y-4">
          {isLoading ? (
            <div className="space-y-4">
              {Array(3).fill(0).map((_, i) => (
                <Skeleton key={i} className="h-32 w-full" />
              ))}
            </div>
          ) : detail?.endpoints ? (
            detail.endpoints.map((endpoint, idx) => (
              <EndpointCard
                key={idx}
                endpoint={endpoint}
                basePath={category.base_path}
              />
            ))
          ) : null}
        </CardContent>
      )}
    </Card>
  );
}

export default function APIDocumentation() {
  const [search, setSearch] = useState('');

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['api-docs', 'overview'],
    queryFn: async () => {
      const response = await api.get<APIOverview>('/api-docs/overview');
      return response.data;
    },
  });

  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ['api-docs', 'categories'],
    queryFn: async () => {
      const response = await api.get<{ categories: APICategory[] }>('/api-docs/categories');
      return response.data.categories;
    },
  });

  const { data: searchResults } = useQuery({
    queryKey: ['api-docs', 'search', search],
    queryFn: async () => {
      const response = await api.get<{ results: Array<Endpoint & { category: string; icon: string }> }>(`/api-docs/search?q=${encodeURIComponent(search)}`);
      return response.data.results;
    },
    enabled: search.length >= 2,
  });

  const isLoading = overviewLoading || categoriesLoading;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Book className="h-8 w-8" />
            Documentação da API
          </h1>
          <p className="text-muted-foreground">
            Referência completa da API do TikTrend
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" asChild>
            <a href="/docs" target="_blank">
              <FileJson className="h-4 w-4 mr-2" />
              Swagger UI
            </a>
          </Button>
          <Button variant="outline" asChild>
            <a href="/redoc" target="_blank">
              <ExternalLink className="h-4 w-4 mr-2" />
              ReDoc
            </a>
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-4">
          {Array(4).fill(0).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : overview && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Code2 className="h-4 w-4" />
                Versão
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{overview.version}</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Zap className="h-4 w-4" />
                Endpoints
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{overview.total_endpoints}</p>
              <p className="text-xs text-muted-foreground">{overview.total_categories} categorias</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Key className="h-4 w-4" />
                Autenticação
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm font-medium">{overview.authentication.type}</p>
              <code className="text-xs text-muted-foreground">{overview.authentication.header}</code>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Rate Limit
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm font-medium">{overview.rate_limiting.authenticated}</p>
              <code className="text-xs text-muted-foreground">{overview.rate_limiting.header}</code>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar endpoints..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Search Results */}
      {search.length >= 2 && searchResults && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Resultados da busca ({searchResults.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {searchResults.length > 0 ? (
              <div className="space-y-3">
                {searchResults.map((result, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                    <span className="text-xl">{result.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={methodColors[result.method]}>
                          {result.method}
                        </Badge>
                        <code className="text-sm">{result.path}</code>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{result.summary}</p>
                    </div>
                    <Badge variant="secondary">{result.category}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground">Nenhum resultado encontrado</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Categories */}
      {!search && (
        <Tabs defaultValue="all" className="space-y-4">
          <TabsList>
            <TabsTrigger value="all">Todas as Categorias</TabsTrigger>
            <TabsTrigger value="auth">Autenticação</TabsTrigger>
            <TabsTrigger value="social">Redes Sociais</TabsTrigger>
            <TabsTrigger value="content">Conteúdo</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-4">
            {categoriesLoading ? (
              <div className="space-y-4">
                {Array(5).fill(0).map((_, i) => (
                  <Skeleton key={i} className="h-24" />
                ))}
              </div>
            ) : categories?.map((category) => (
              <CategorySection key={category.name} category={category} />
            ))}
          </TabsContent>

          <TabsContent value="auth" className="space-y-4">
            {categories?.filter(c => 
              c.name.includes('Autenticação') || c.base_path.includes('auth')
            ).map((category) => (
              <CategorySection key={category.name} category={category} />
            ))}
          </TabsContent>

          <TabsContent value="social" className="space-y-4">
            {categories?.filter(c => 
              ['Instagram', 'TikTok', 'YouTube', 'Multi-Account'].some(n => c.name.includes(n))
            ).map((category) => (
              <CategorySection key={category.name} category={category} />
            ))}
          </TabsContent>

          <TabsContent value="content" className="space-y-4">
            {categories?.filter(c => 
              ['Content', 'Templates', 'Scheduler'].some(n => c.name.includes(n) || c.base_path.includes(n.toLowerCase()))
            ).map((category) => (
              <CategorySection key={category.name} category={category} />
            ))}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
