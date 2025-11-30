"""
API Documentation Routes
Enhanced OpenAPI documentation with examples
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

router = APIRouter()


class EndpointExample(BaseModel):
    """Example request/response for endpoint"""
    description: str
    request: Optional[Dict[str, Any]] = None
    response: Dict[str, Any]
    curl_example: Optional[str] = None


class EndpointDoc(BaseModel):
    """Detailed endpoint documentation"""
    path: str
    method: str
    summary: str
    description: str
    tags: List[str]
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    examples: List[EndpointExample] = Field(default_factory=list)
    rate_limit: Optional[str] = None
    auth_required: bool = True


class APICategory(BaseModel):
    """Category of API endpoints"""
    name: str
    description: str
    icon: str
    endpoints_count: int
    base_path: str


# API Documentation Data
API_CATEGORIES = [
    {
        "name": "Autenticação",
        "description": "Endpoints para login, registro e gerenciamento de tokens JWT",
        "icon": "🔐",
        "base_path": "/auth",
        "endpoints": [
            {
                "path": "/auth/login",
                "method": "POST",
                "summary": "Login de usuário",
                "description": "Autentica um usuário e retorna tokens de acesso",
                "examples": [
                    {
                        "description": "Login com email e senha",
                        "request": {"email": "user@example.com", "password": "senha123"},
                        "response": {
                            "access_token": "eyJhbGc...",
                            "refresh_token": "eyJhbGc...",
                            "token_type": "bearer",
                            "expires_in": 3600
                        },
                        "curl_example": 'curl -X POST "/auth/login" -H "Content-Type: application/json" -d \'{"email":"user@example.com","password":"senha123"}\''
                    }
                ]
            },
            {
                "path": "/auth/register",
                "method": "POST",
                "summary": "Registro de novo usuário",
                "description": "Cria uma nova conta de usuário",
                "examples": [
                    {
                        "description": "Criar nova conta",
                        "request": {
                            "email": "novo@example.com",
                            "password": "senha123",
                            "name": "Novo Usuário"
                        },
                        "response": {"id": "uuid", "email": "novo@example.com", "name": "Novo Usuário"}
                    }
                ]
            }
        ]
    },
    {
        "name": "Produtos",
        "description": "CRUD de produtos e comparação de preços",
        "icon": "📦",
        "base_path": "/products",
        "endpoints": [
            {
                "path": "/products",
                "method": "GET",
                "summary": "Listar produtos",
                "description": "Retorna lista paginada de produtos com filtros",
                "parameters": [
                    {"name": "page", "type": "integer", "description": "Número da página", "default": 1},
                    {"name": "limit", "type": "integer", "description": "Itens por página", "default": 20},
                    {"name": "category", "type": "string", "description": "Filtrar por categoria"},
                    {"name": "min_price", "type": "number", "description": "Preço mínimo"},
                    {"name": "max_price", "type": "number", "description": "Preço máximo"}
                ],
                "examples": [
                    {
                        "description": "Listar todos os produtos",
                        "response": {
                            "items": [{"id": "1", "name": "Produto A", "price": 99.90}],
                            "total": 100,
                            "page": 1,
                            "pages": 5
                        }
                    }
                ]
            },
            {
                "path": "/products/{id}",
                "method": "GET",
                "summary": "Buscar produto",
                "description": "Retorna detalhes de um produto específico",
                "examples": [
                    {
                        "description": "Buscar por ID",
                        "response": {
                            "id": "uuid",
                            "name": "Smartphone XYZ",
                            "description": "Descrição do produto",
                            "price": 1299.90,
                            "compare_prices": [
                                {"store": "Loja A", "price": 1299.90},
                                {"store": "Loja B", "price": 1350.00}
                            ]
                        }
                    }
                ]
            }
        ]
    },
    {
        "name": "Instagram Automation",
        "description": "Automação de publicações e gerenciamento de sessões do Instagram",
        "icon": "📸",
        "base_path": "/instagram",
        "endpoints": [
            {
                "path": "/instagram/sessions",
                "method": "GET",
                "summary": "Listar sessões",
                "description": "Lista todas as sessões do Instagram do usuário",
                "examples": [
                    {
                        "description": "Listar sessões ativas",
                        "response": {
                            "sessions": [
                                {
                                    "username": "myaccount",
                                    "status": "active",
                                    "created_at": "2024-01-01T00:00:00Z"
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "path": "/instagram/post",
                "method": "POST",
                "summary": "Criar publicação",
                "description": "Cria uma nova publicação no Instagram",
                "examples": [
                    {
                        "description": "Publicar imagem com legenda",
                        "request": {
                            "account": "myaccount",
                            "image_url": "https://...",
                            "caption": "Minha publicação #hashtag",
                            "schedule_at": None
                        },
                        "response": {"status": "published", "post_id": "123456"}
                    }
                ]
            }
        ]
    },
    {
        "name": "TikTok Automation",
        "description": "Automação de vídeos e gerenciamento de contas TikTok",
        "icon": "🎵",
        "base_path": "/tiktok",
        "endpoints": [
            {
                "path": "/tiktok/sessions",
                "method": "GET",
                "summary": "Listar sessões TikTok",
                "description": "Lista sessões de TikTok do usuário",
                "examples": [
                    {
                        "description": "Sessões ativas",
                        "response": {
                            "sessions": [{"account": "tiktoker", "status": "active"}]
                        }
                    }
                ]
            }
        ]
    },
    {
        "name": "YouTube Automation",
        "description": "Gerenciamento de canal e uploads do YouTube",
        "icon": "📺",
        "base_path": "/youtube",
        "endpoints": [
            {
                "path": "/youtube/quota",
                "method": "GET",
                "summary": "Status da quota",
                "description": "Retorna uso atual da quota da API do YouTube",
                "examples": [
                    {
                        "description": "Verificar quota",
                        "response": {
                            "used": 5000,
                            "limit": 10000,
                            "reset_at": "2024-01-02T00:00:00Z"
                        }
                    }
                ]
            }
        ]
    },
    {
        "name": "Content Generator",
        "description": "Geração de conteúdo com IA (OpenAI)",
        "icon": "✨",
        "base_path": "/content",
        "endpoints": [
            {
                "path": "/content/generate",
                "method": "POST",
                "summary": "Gerar conteúdo",
                "description": "Gera legendas e descrições usando IA",
                "examples": [
                    {
                        "description": "Gerar legenda para produto",
                        "request": {
                            "product_name": "Smartphone XYZ",
                            "tone": "promotional",
                            "platform": "instagram"
                        },
                        "response": {
                            "caption": "🔥 Smartphone XYZ chegou! Aproveite...",
                            "hashtags": ["#smartphone", "#tecnologia"]
                        }
                    }
                ]
            }
        ]
    },
    {
        "name": "Scheduler",
        "description": "Agendamento de publicações em múltiplas plataformas",
        "icon": "📅",
        "base_path": "/scheduler",
        "endpoints": [
            {
                "path": "/scheduler/posts",
                "method": "GET",
                "summary": "Listar agendamentos",
                "description": "Lista todas as publicações agendadas",
                "examples": [
                    {
                        "description": "Publicações pendentes",
                        "response": {
                            "posts": [
                                {
                                    "id": "uuid",
                                    "platform": "instagram",
                                    "scheduled_at": "2024-01-01T10:00:00Z",
                                    "status": "pending"
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "path": "/scheduler/posts",
                "method": "POST",
                "summary": "Agendar publicação",
                "description": "Agenda uma nova publicação",
                "examples": [
                    {
                        "description": "Agendar post no Instagram",
                        "request": {
                            "platform": "instagram",
                            "account": "myaccount",
                            "content": {"caption": "Meu post", "media_url": "https://..."},
                            "scheduled_at": "2024-01-01T10:00:00Z"
                        },
                        "response": {"id": "uuid", "status": "scheduled"}
                    }
                ]
            }
        ]
    },
    {
        "name": "Templates",
        "description": "Templates reutilizáveis para conteúdo",
        "icon": "📝",
        "base_path": "/templates",
        "endpoints": [
            {
                "path": "/templates",
                "method": "GET",
                "summary": "Listar templates",
                "description": "Lista templates do usuário e públicos",
                "examples": [
                    {
                        "description": "Todos os templates",
                        "response": {
                            "templates": [
                                {
                                    "id": "uuid",
                                    "name": "Produto em Destaque",
                                    "platform": "all",
                                    "caption_template": "🔥 {{product_name}}..."
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "path": "/templates/{id}/render",
                "method": "POST",
                "summary": "Renderizar template",
                "description": "Substitui variáveis e retorna texto final",
                "examples": [
                    {
                        "description": "Renderizar com variáveis",
                        "request": {
                            "variables": {"product_name": "Smartphone XYZ", "price": "999.90"}
                        },
                        "response": {"caption": "🔥 Smartphone XYZ - R$ 999.90"}
                    }
                ]
            }
        ]
    },
    {
        "name": "Multi-Account",
        "description": "Gerenciamento de múltiplas contas por plataforma",
        "icon": "👥",
        "base_path": "/accounts",
        "endpoints": [
            {
                "path": "/accounts",
                "method": "GET",
                "summary": "Listar contas",
                "description": "Lista todas as contas conectadas",
                "examples": [
                    {
                        "description": "Todas as contas",
                        "response": {
                            "accounts": [
                                {"id": "uuid", "platform": "instagram", "username": "account1", "is_primary": True}
                            ]
                        }
                    }
                ]
            },
            {
                "path": "/accounts/{id}/switch",
                "method": "POST",
                "summary": "Alternar conta",
                "description": "Define uma conta como ativa para sua plataforma",
                "examples": [
                    {
                        "description": "Alternar para conta",
                        "response": {"id": "uuid", "status": "active", "is_primary": False}
                    }
                ]
            }
        ]
    },
    {
        "name": "Analytics",
        "description": "Métricas e análises de desempenho",
        "icon": "📊",
        "base_path": "/analytics",
        "endpoints": [
            {
                "path": "/analytics/overview",
                "method": "GET",
                "summary": "Visão geral",
                "description": "Dashboard com métricas de todas as plataformas",
                "parameters": [
                    {"name": "start_date", "type": "string", "description": "Data inicial (YYYY-MM-DD)"},
                    {"name": "end_date", "type": "string", "description": "Data final (YYYY-MM-DD)"}
                ],
                "examples": [
                    {
                        "description": "Métricas dos últimos 30 dias",
                        "response": {
                            "period": {"start": "2024-01-01", "end": "2024-01-31", "days": 30},
                            "platforms": [{"platform": "instagram", "followers": 10000}],
                            "engagement": {"total_likes": 5000, "avg_engagement_rate": 5.2}
                        }
                    }
                ]
            }
        ]
    },
    {
        "name": "Webhooks",
        "description": "Gerenciamento de webhooks para integrações",
        "icon": "🔗",
        "base_path": "/status",
        "endpoints": [
            {
                "path": "/status/webhooks",
                "method": "GET",
                "summary": "Listar webhooks",
                "description": "Lista todos os webhooks configurados",
                "examples": [
                    {
                        "description": "Webhooks ativos",
                        "response": {
                            "webhooks": [
                                {"id": "uuid", "url": "https://...", "events": ["post.published"]}
                            ]
                        }
                    }
                ]
            }
        ]
    }
]


@router.get("/categories")
async def get_api_categories():
    """Get all API categories with endpoint counts."""
    categories = []
    for cat in API_CATEGORIES:
        categories.append({
            "name": cat["name"],
            "description": cat["description"],
            "icon": cat["icon"],
            "base_path": cat["base_path"],
            "endpoints_count": len(cat.get("endpoints", []))
        })
    return {"categories": categories}


@router.get("/categories/{category_name}")
async def get_category_endpoints(category_name: str):
    """Get all endpoints for a category."""
    for cat in API_CATEGORIES:
        if cat["name"].lower() == category_name.lower() or cat["base_path"].strip("/") == category_name.lower():
            return {
                "name": cat["name"],
                "description": cat["description"],
                "icon": cat["icon"],
                "base_path": cat["base_path"],
                "endpoints": cat.get("endpoints", [])
            }
    return {"error": "Category not found"}


@router.get("/search")
async def search_endpoints(q: str):
    """Search across all endpoints."""
    results = []
    query = q.lower()
    
    for cat in API_CATEGORIES:
        for endpoint in cat.get("endpoints", []):
            if (query in endpoint["path"].lower() or
                query in endpoint["summary"].lower() or
                query in endpoint.get("description", "").lower()):
                results.append({
                    "category": cat["name"],
                    "icon": cat["icon"],
                    **endpoint
                })
    
    return {"results": results, "count": len(results)}


@router.get("/overview")
async def get_api_overview():
    """Get API overview statistics."""
    total_endpoints = sum(len(cat.get("endpoints", [])) for cat in API_CATEGORIES)
    
    return {
        "api_name": "Didin Fácil API",
        "version": "2.0.0",
        "description": "API completa para automação de redes sociais e comparação de preços",
        "base_url": "/api/v1",
        "total_categories": len(API_CATEGORIES),
        "total_endpoints": total_endpoints,
        "authentication": {
            "type": "Bearer Token (JWT)",
            "header": "Authorization: Bearer <token>",
            "endpoints": {
                "login": "POST /auth/login",
                "refresh": "POST /auth/refresh"
            }
        },
        "rate_limiting": {
            "default": "100 requests/minute",
            "authenticated": "300 requests/minute",
            "header": "X-RateLimit-Remaining"
        },
        "documentation_urls": {
            "openapi": "/openapi.json",
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "categories": [
            {"name": cat["name"], "icon": cat["icon"], "base_path": cat["base_path"]}
            for cat in API_CATEGORIES
        ]
    }


# Interactive docs page
DOCS_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Didin Fácil API - Documentação Interativa</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen">
    <div class="max-w-7xl mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                🚀 Didin Fácil API
            </h1>
            <p class="text-gray-400 mt-2">Documentação interativa da API</p>
            <div class="flex gap-4 mt-4">
                <a href="/docs" class="px-4 py-2 bg-green-600 rounded hover:bg-green-700 transition">
                    📖 Swagger UI
                </a>
                <a href="/redoc" class="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 transition">
                    📚 ReDoc
                </a>
                <a href="/openapi.json" class="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600 transition">
                    📄 OpenAPI JSON
                </a>
            </div>
        </header>
        
        <div class="grid md:grid-cols-3 gap-4 mb-8">
            <div class="bg-gray-800 rounded-lg p-4">
                <h3 class="text-lg font-semibold text-purple-400">Autenticação</h3>
                <p class="text-sm text-gray-400">Bearer Token (JWT)</p>
                <code class="text-xs text-green-400">Authorization: Bearer &lt;token&gt;</code>
            </div>
            <div class="bg-gray-800 rounded-lg p-4">
                <h3 class="text-lg font-semibold text-purple-400">Rate Limit</h3>
                <p class="text-sm text-gray-400">100-300 req/min</p>
                <code class="text-xs text-green-400">X-RateLimit-Remaining</code>
            </div>
            <div class="bg-gray-800 rounded-lg p-4">
                <h3 class="text-lg font-semibold text-purple-400">Base URL</h3>
                <p class="text-sm text-gray-400">Produção</p>
                <code class="text-xs text-green-400">https://api.didinfacil.com/v1</code>
            </div>
        </div>
        
        <div id="categories" class="space-y-6">
            <!-- Categories will be loaded here -->
        </div>
    </div>
    
    <script>
        async function loadCategories() {
            const res = await fetch('/api-docs/categories');
            const data = await res.json();
            const container = document.getElementById('categories');
            
            container.innerHTML = data.categories.map(cat => `
                <div class="bg-gray-800 rounded-lg overflow-hidden">
                    <button 
                        onclick="toggleCategory('${cat.name}')"
                        class="w-full p-4 flex items-center justify-between hover:bg-gray-700 transition"
                    >
                        <div class="flex items-center gap-3">
                            <span class="text-2xl">${cat.icon}</span>
                            <div class="text-left">
                                <h2 class="text-lg font-semibold">${cat.name}</h2>
                                <p class="text-sm text-gray-400">${cat.description}</p>
                            </div>
                        </div>
                        <span class="text-gray-400">${cat.endpoints_count} endpoints</span>
                    </button>
                    <div id="endpoints-${cat.name}" class="hidden border-t border-gray-700">
                    </div>
                </div>
            `).join('');
        }
        
        async function toggleCategory(name) {
            const container = document.getElementById(`endpoints-${name}`);
            if (container.classList.contains('hidden')) {
                const res = await fetch(`/api-docs/categories/${encodeURIComponent(name)}`);
                const data = await res.json();
                
                container.innerHTML = data.endpoints.map(ep => `
                    <div class="p-4 border-b border-gray-700 last:border-b-0">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="px-2 py-1 rounded text-xs font-mono ${getMethodColor(ep.method)}">
                                ${ep.method}
                            </span>
                            <code class="text-sm text-gray-300">${ep.path}</code>
                        </div>
                        <p class="text-sm text-gray-400 mb-2">${ep.summary}</p>
                        ${ep.examples?.length ? `
                            <details class="mt-2">
                                <summary class="text-sm text-purple-400 cursor-pointer">Ver exemplos</summary>
                                ${ep.examples.map(ex => `
                                    <div class="mt-2 bg-gray-900 rounded p-3">
                                        <p class="text-xs text-gray-500 mb-2">${ex.description}</p>
                                        ${ex.request ? `
                                            <p class="text-xs text-gray-400 mb-1">Request:</p>
                                            <pre class="text-xs overflow-x-auto"><code class="language-json">${JSON.stringify(ex.request, null, 2)}</code></pre>
                                        ` : ''}
                                        <p class="text-xs text-gray-400 mb-1 mt-2">Response:</p>
                                        <pre class="text-xs overflow-x-auto"><code class="language-json">${JSON.stringify(ex.response, null, 2)}</code></pre>
                                    </div>
                                `).join('')}
                            </details>
                        ` : ''}
                    </div>
                `).join('');
                
                Prism.highlightAll();
            }
            container.classList.toggle('hidden');
        }
        
        function getMethodColor(method) {
            const colors = {
                GET: 'bg-green-600',
                POST: 'bg-blue-600',
                PATCH: 'bg-yellow-600',
                PUT: 'bg-orange-600',
                DELETE: 'bg-red-600'
            };
            return colors[method] || 'bg-gray-600';
        }
        
        loadCategories();
    </script>
</body>
</html>
"""


@router.get("/interactive", response_class=HTMLResponse)
async def get_interactive_docs():
    """Get interactive API documentation page."""
    return DOCS_HTML
