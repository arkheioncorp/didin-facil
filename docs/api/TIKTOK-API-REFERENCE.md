# TikTok API Scraper - Documentação Técnica

> **Versão:** 2.0.0  
> **Última Atualização:** 07 de Julho de 2025  
> **Autores:** TikTrend Finder Team

## 📋 Visão Geral

O TikTok API Scraper é um sistema de coleta de dados de produtos do TikTok Shop que utiliza chamadas de API diretas em vez de automação de browser. Isso proporciona:

- **Velocidade:** 10x mais rápido que scraping via Playwright
- **Confiabilidade:** Bypass completo de CAPTCHA via cookies autenticados
- **Escalabilidade:** Menor uso de recursos (sem browser headless)
- **Resiliência:** Sistema de fallback em 3 camadas

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                     API Routes Layer                         │
│  /api/v1/tiktok/api/search                                  │
│  /api/v1/tiktok/api/trending                                │
│  /api/v1/tiktok/api/health                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 ProductCacheManager                          │
│  - Redis-based caching                                       │
│  - TTL: 30min (search), 6h (products)                       │
│  - Hit/miss metrics                                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Scraper Fallback System                      │
│  Tier 1: TikTokAPIScraper (httpx + cookies)                 │
│  Tier 2: TikTokScraper (Playwright browser)                 │
│  Tier 3: TikTokDataProvider (curated data)                  │
└─────────────────────────────────────────────────────────────┘
```

## 🔌 Endpoints

### GET `/api/v1/tiktok/api/health`

Verifica a saúde do scraper de API TikTok.

**Autenticação:** Bearer Token (obrigatório)

**Response:**

```json
{
  "status": "healthy",
  "api_accessible": true,
  "cookies_valid": true,
  "cookie_expires": "2026-05-06T03:12:06Z",
  "endpoints_tested": ["search_general", "trending"],
  "response_time_ms": 245.67
}
```

**Status Codes:**
- `200`: Healthy
- `503`: Degraded/Error

---

### GET `/api/v1/tiktok/api/search`

Busca produtos no TikTok Shop usando API direta.

**Autenticação:** Bearer Token (obrigatório)

**Query Parameters:**

| Parâmetro | Tipo | Obrigatório | Default | Descrição |
|-----------|------|-------------|---------|-----------|
| `q` | string | ✅ | - | Query de busca (2-200 chars) |
| `max_results` | int | ❌ | 20 | Máximo de resultados (1-100) |
| `use_cache` | bool | ❌ | true | Usar cache Redis |

**Request:**
```bash
curl -X GET "https://api.tiktrendfinder.com/api/v1/tiktok/api/search?q=iphone+case&max_results=10" \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "products": [
    {
      "id": "7382941023847",
      "title": "Capa iPhone 15 Pro Max Silicone",
      "price": 29.90,
      "original_price": 59.90,
      "discount": "50% OFF",
      "image_url": "https://p16-...",
      "product_url": "https://www.tiktok.com/...",
      "shop_name": "TechStore BR",
      "sales_count": 15420,
      "rating": 4.8,
      "source": "tiktok_api"
    }
  ],
  "total": 10,
  "cached": false,
  "cache_ttl": null,
  "scraper_type": "api"
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid query
- `401`: Unauthorized
- `500`: Scraper error

---

### GET `/api/v1/tiktok/api/trending`

Retorna produtos em alta no TikTok Shop.

**Autenticação:** Bearer Token (obrigatório)

**Query Parameters:**

| Parâmetro | Tipo | Obrigatório | Default | Descrição |
|-----------|------|-------------|---------|-----------|
| `category` | string | ❌ | null | Filtrar por categoria |
| `max_results` | int | ❌ | 20 | Máximo de resultados (1-50) |
| `use_cache` | bool | ❌ | true | Usar cache Redis |

**Request:**
```bash
curl -X GET "https://api.tiktrendfinder.com/api/v1/tiktok/api/trending?max_results=20" \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "products": [
    {
      "id": "7382941023848",
      "title": "Fone Bluetooth TWS",
      "price": 49.90,
      "original_price": 99.90,
      "discount": "50% OFF",
      "image_url": "https://p16-...",
      "product_url": "https://www.tiktok.com/...",
      "shop_name": "AudioPro",
      "sales_count": 28450,
      "rating": 4.9,
      "source": "tiktok_api"
    }
  ],
  "total": 20,
  "cached": true,
  "cache_ttl": 1542,
  "scraper_type": "api"
}
```

---

### GET `/api/v1/tiktok/api/cache/stats`

Retorna estatísticas do cache de produtos.

**Autenticação:** Bearer Token (obrigatório)

**Response:**
```json
{
  "total_keys": 1542,
  "hits": 28450,
  "misses": 3240,
  "hit_rate": 89.8,
  "trending_cached": true,
  "search_queries_cached": 42,
  "memory_used_mb": 45.6
}
```

---

### POST `/api/v1/tiktok/api/cache/clear`

Limpa o cache de produtos.

**Autenticação:** Bearer Token (obrigatório)  
**Permissão:** Pro/Enterprise only

**Query Parameters:**

| Parâmetro | Tipo | Obrigatório | Default | Descrição |
|-----------|------|-------------|---------|-----------|
| `pattern` | string | ❌* | null | Padrão de chaves (ex: "search:*") |
| `all` | bool | ❌* | false | Limpar todo o cache |

*Um dos dois é obrigatório

**Request:**
```bash
curl -X POST "https://api.tiktrendfinder.com/api/v1/tiktok/api/cache/clear?all=true" \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "status": "success",
  "message": "Cache limpo: 1542 chaves removidas"
}
```

---

### POST `/api/v1/tiktok/api/refresh`

Força atualização dos dados de produtos.

**Autenticação:** Bearer Token (obrigatório)  
**Permissão:** Pro/Enterprise only  
**Rate Limit:** 5 requests/hora

**Query Parameters:**

| Parâmetro | Tipo | Obrigatório | Default | Descrição |
|-----------|------|-------------|---------|-----------|
| `category` | string | ❌ | null | Categoria para refresh |

**Request:**
```bash
curl -X POST "https://api.tiktrendfinder.com/api/v1/tiktok/api/refresh?category=electronics" \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "status": "queued",
  "message": "Refresh agendado em background",
  "category": "electronics"
}
```

---

## 🔐 Autenticação

Todos os endpoints requerem autenticação via Bearer Token no header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Planos e Limites

| Plano | Rate Limit | Cache Clear | Refresh |
|-------|------------|-------------|---------|
| Free | 100 req/dia | ❌ | ❌ |
| Pro | 1000 req/dia | ✅ | ✅ (5/h) |
| Enterprise | Ilimitado | ✅ | ✅ (20/h) |

---

## 🍪 Sistema de Cookies

O scraper utiliza cookies autenticados para fazer requisições diretas à API do TikTok.

### Cookies Críticos

| Cookie | Descrição | Validade |
|--------|-----------|----------|
| `sessionid` | Sessão principal | ~6 meses |
| `sid_tt` | ID de sessão secundário | ~6 meses |
| `msToken` | Token anti-bot | ~1 dia |
| `tt_csrf_token` | CSRF protection | ~1 semana |
| `ttwid` | Web ID tracking | ~1 ano |

### Renovação Automática

O worker de scraping (`TikTokScrapingWorker`) tenta renovar automaticamente cookies que estão próximos de expirar:

```python
async def _auto_refresh_cookies(self):
    """Tenta renovar cookies 7 dias antes da expiração."""
    health = await self.scraper.health_check()
    
    if health.get("days_until_expiry", 30) < 7:
        # Trigger cookie refresh via browser session
        await self._refresh_via_browser()
```

### Atualização Manual

Para atualizar cookies manualmente:

1. Acesse TikTok no browser e faça login
2. Use extensão "Cookie-Editor" para exportar cookies
3. Envie via endpoint `/api/v1/tiktok/sessions`:

```bash
curl -X POST "https://api.tiktrendfinder.com/api/v1/tiktok/sessions" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "account_name": "main",
    "cookies": [...]
  }'
```

---

## 📊 Cache Strategy

### TTL (Time-To-Live)

| Tipo | TTL | Motivo |
|------|-----|--------|
| Produtos individuais | 6 horas | Preços mudam pouco |
| Trending | 30 minutos | Alta rotatividade |
| Search results | 15 minutos | Relevância temporal |
| Categorias | 1 hora | Estabilidade média |

### Invalidação

```python
# Padrões de invalidação
await cache.invalidate_product("7382941023847")  # Produto específico
await cache.invalidate_seller("seller_123")       # Todos de um vendedor
await cache.invalidate_trending()                  # Trending completo
await cache.invalidate_search("iphone")           # Buscas com keyword
await cache.invalidate_all()                       # Cache total
```

### Métricas

O cache expõe métricas via `/api/v1/tiktok/api/cache/stats`:

- **Hit Rate**: Porcentagem de requests servidos do cache
- **Miss Rate**: Porcentagem que precisou buscar da API
- **Memory Usage**: Memória Redis consumida
- **Key Count**: Total de chaves cacheadas

---

## 🔄 Fallback System

O sistema implementa 3 níveis de fallback:

### Tier 1: TikTokAPIScraper (Default)

- **Método:** Requisições httpx diretas
- **Vantagens:** Rápido, sem CAPTCHA
- **Quando falha:** Cookies inválidos, rate limit

### Tier 2: TikTokScraper (Browser)

- **Método:** Playwright com anti-detection
- **Vantagens:** Mais robusto, simula usuário real
- **Quando falha:** CAPTCHA não resolvível

### Tier 3: TikTokDataProvider (Static)

- **Método:** Dados curados/mock
- **Vantagens:** Sempre disponível
- **Quando usar:** Fallback final, desenvolvimento

```python
async def scrape_trending(self):
    # Tier 1: API
    try:
        api_scraper = TikTokAPIScraper()
        products = await api_scraper.get_trending_products()
        if products:
            return products
    except Exception:
        pass
    
    # Tier 2: Browser
    try:
        products = await self._browser_scrape()
        if products:
            return products
    except Exception:
        pass
    
    # Tier 3: Static data
    return TikTokDataProvider.get_trending()
```

---

## 🚀 Worker de Scraping

O `TikTokScrapingWorker` executa scraping automatizado em background.

### Configuração

```python
worker = TikTokScrapingWorker(
    scrape_interval=3600,      # 1 hora entre jobs
    trending_interval=1800,    # 30 min para trending
    categories_to_scrape=[
        "electronics",
        "fashion",
        "beauty",
        "home"
    ]
)
```

### Operações

```python
# Iniciar worker
await worker.start()

# Parar gracefully
await worker.stop()

# Status
status = await worker.get_status()
# {
#     "running": true,
#     "last_scrape": "2025-07-07T10:30:00Z",
#     "products_scraped": 1542,
#     "errors": 3
# }
```

### Systemd Service

```ini
[Unit]
Description=TikTok Scraping Worker
After=network.target redis.service

[Service]
Type=simple
User=tiktrend
WorkingDirectory=/app/backend
ExecStart=/app/.venv/bin/python -m workers.scraping_worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 🧪 Testando a API

### Health Check

```bash
# Verificar se API está saudável
curl -s "https://api.tiktrendfinder.com/api/v1/tiktok/api/health" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Resposta esperada
{
  "status": "healthy",
  "api_accessible": true,
  "cookies_valid": true
}
```

### Busca de Produtos

```bash
# Buscar produtos
curl -s "https://api.tiktrendfinder.com/api/v1/tiktok/api/search?q=fone+bluetooth&max_results=5" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Verificar cache
curl -s "https://api.tiktrendfinder.com/api/v1/tiktok/api/cache/stats" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Script de Teste Completo

```python
import httpx
import asyncio

async def test_tiktok_api():
    base_url = "https://api.tiktrendfinder.com/api/v1/tiktok/api"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        # Health
        health = await client.get(f"{base_url}/health", headers=headers)
        print(f"Health: {health.json()['status']}")
        
        # Search
        search = await client.get(
            f"{base_url}/search",
            params={"q": "iphone case", "max_results": 5},
            headers=headers
        )
        products = search.json()["products"]
        print(f"Found {len(products)} products")
        
        # Trending
        trending = await client.get(
            f"{base_url}/trending",
            params={"max_results": 10},
            headers=headers
        )
        print(f"Trending: {len(trending.json()['products'])} products")
        
        # Cache stats
        stats = await client.get(f"{base_url}/cache/stats", headers=headers)
        print(f"Cache hit rate: {stats.json()['hit_rate']}%")

asyncio.run(test_tiktok_api())
```

---

## ⚠️ Tratamento de Erros

### Códigos de Erro

| Status | Código | Descrição |
|--------|--------|-----------|
| 400 | `INVALID_QUERY` | Query de busca inválida |
| 401 | `UNAUTHORIZED` | Token inválido/ausente |
| 403 | `FORBIDDEN` | Sem permissão (plano) |
| 429 | `RATE_LIMITED` | Limite excedido |
| 500 | `SCRAPER_ERROR` | Erro interno do scraper |
| 503 | `API_UNAVAILABLE` | TikTok API indisponível |

### Response de Erro

```json
{
  "detail": "Erro ao buscar produtos: Connection timeout",
  "error_code": "SCRAPER_ERROR",
  "timestamp": "2025-07-07T10:30:00Z"
}
```

### Retry Logic

O scraper implementa retry com exponential backoff:

```python
async def _make_request(self, url, retries=3):
    for attempt in range(retries):
        try:
            response = await self.client.get(url)
            return response.json()
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise
```

---

## 📈 Monitoramento

### Métricas Prometheus

```python
# Métricas expostas
tiktok_api_requests_total{endpoint, status}
tiktok_api_response_time_seconds{endpoint}
tiktok_cache_hit_ratio
tiktok_products_scraped_total
tiktok_cookies_expiry_days
```

### Alertas Recomendados

```yaml
# prometheus/alerts.yml
groups:
  - name: tiktok_scraper
    rules:
      - alert: TikTokCookiesExpiring
        expr: tiktok_cookies_expiry_days < 7
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "TikTok cookies expiring soon"
          
      - alert: TikTokAPIDown
        expr: up{job="tiktok_scraper"} == 0
        for: 5m
        labels:
          severity: critical
```

---

## 📚 Recursos Adicionais

- [Arquitetura Geral](/docs/ARCHITECTURE.md)
- [Guia de Deployment](/docs/DEPLOYMENT.md)
- [Schema do Banco](/docs/DATABASE-SCHEMA.md)
- [Security Guidelines](/docs/SECURITY.md)

---

> **Suporte:** Para dúvidas ou problemas, abra uma issue no GitHub ou contate o time de desenvolvimento.
