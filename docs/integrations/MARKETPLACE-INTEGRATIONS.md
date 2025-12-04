# Marketplace Integrations

Sistema de integração com múltiplos e-commerces para comparação de preços.

## Overview

O TikTrend Finder integra com os principais marketplaces brasileiros através de APIs oficiais e SDKs de terceiros. Isso permite buscar produtos, comparar preços e encontrar as melhores ofertas automaticamente.

## Marketplaces Suportados

| Marketplace | Método | Auth Requerida | Status |
|------------|--------|----------------|--------|
| Mercado Livre | API REST | Não* | ✅ Completo |
| Amazon | PAAPI 5.0 | Sim | ✅ Completo |
| Shopee | API Pública | Não* | ✅ Completo |
| AliExpress | Scraper | Não | ✅ Existente |
| TikTok Shop | Scraper | Não | ✅ Existente |
| Magazine Luiza | Em desenvolvimento | - | 🚧 Planejado |

\* Auth opcional, mas recomendada para maior rate limit

## Instalação

```bash
# Dependências adicionais
pip install python-amazon-paapi pyshopee
```

## Uso Básico

### Python API

```python
from backend.integrations.marketplaces import (
    MarketplaceManager,
    search_all_marketplaces,
)

# Busca simples em todos os marketplaces
results = await search_all_marketplaces("iphone 15")

print(f"Total: {results.total_products} produtos")
print(f"Menor preço: R${results.best_price.price}")
print(f"Melhor avaliado: {results.best_rating.title}")

# Usando o Manager com configuração
manager = MarketplaceManager()

# Configurar credenciais (opcional)
manager.configure_mercado_livre(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
)

manager.configure_amazon(
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY",
    partner_tag="YOUR-TAG-20",
)

# Buscar em marketplace específico
ml_results = await manager.search(
    MarketplaceType.MERCADO_LIVRE,
    "samsung galaxy",
    page=1,
    per_page=20,
)

# Encontrar melhor oferta
best = await manager.find_best_deal(
    "fone bluetooth",
    min_rating=4.0,
    max_price=500.0,
)
```

### REST API

```bash
# Listar marketplaces
GET /marketplaces/

# Buscar em um marketplace
GET /marketplaces/search?q=iphone&marketplace=mercado_livre&per_page=20

# Comparar entre marketplaces
GET /marketplaces/compare?q=iphone+15&per_page=10

# Encontrar melhor oferta
GET /marketplaces/best-deal?q=fone+bluetooth&min_rating=4.0&max_price=500

# Detalhes de produto
GET /marketplaces/mercado_livre/product/MLB123456789

# Categorias
GET /marketplaces/mercado_livre/categories
```

## Estrutura de Dados

### Product (Modelo Unificado)

```python
class Product:
    id: str                          # ID no marketplace
    marketplace: MarketplaceType     # mercado_livre, amazon, shopee
    external_url: HttpUrl            # URL do produto
    title: str
    description: Optional[str]
    brand: Optional[str]
    category: Optional[str]
    condition: ProductCondition      # new, used, refurbished
    
    # Preços
    price: Decimal
    original_price: Optional[Decimal]
    currency: str = "BRL"
    discount_percentage: Optional[float]
    installments: Optional[int]
    installment_value: Optional[Decimal]
    
    # Imagens
    thumbnail: Optional[HttpUrl]
    images: list[HttpUrl]
    
    # Envio
    free_shipping: bool
    shipping_price: Optional[Decimal]
    estimated_delivery_days: Optional[int]
    
    # Vendedor
    seller_id: Optional[str]
    seller_name: Optional[str]
    seller_reputation: Optional[float]
    is_official_store: bool
    
    # Métricas
    rating: Optional[float]          # 0-5
    reviews_count: Optional[int]
    sales_count: Optional[int]
    available_quantity: Optional[int]
    
    # Metadados
    attributes: dict[str, Any]
    fetched_at: datetime
```

### SearchResult

```python
class SearchResult:
    query: str
    marketplace: MarketplaceType
    total_results: int
    page: int
    per_page: int
    products: list[Product]
    search_time_ms: float
    filters_applied: dict
```

### ComparisonResult

```python
class ComparisonResult:
    query: str
    total_products: int
    best_price: Optional[Product]      # Menor preço
    best_rating: Optional[Product]     # Melhor avaliação
    best_value: Optional[Product]      # Melhor custo-benefício
    by_marketplace: dict[str, list[Product]]
    search_time_ms: float
    errors: dict[str, str]
```

## Configuração por Marketplace

### Mercado Livre

```python
# API pública (sem autenticação)
client = MercadoLivreClient()

# Com autenticação (maior rate limit)
client = MercadoLivreClient(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    site_id="MLB",  # Brasil
)
await client.authenticate()
```

**Sites disponíveis:**
- `MLB` - Brasil
- `MLA` - Argentina
- `MLM` - México
- `MLC` - Chile
- `MCO` - Colômbia

**Documentação:** https://developers.mercadolibre.com/

### Amazon (PAAPI 5.0)

```python
client = AmazonClient(
    access_key=os.getenv("AMAZON_ACCESS_KEY"),
    secret_key=os.getenv("AMAZON_SECRET_KEY"),
    partner_tag=os.getenv("AMAZON_PARTNER_TAG"),
    country="BR",
)
```

**Requisitos:**
1. Conta Amazon Associates ativa
2. Aprovar na análise (requer vendas)
3. Access Key e Secret Key da AWS

**Limitações:**
- 1 request/segundo (padrão)
- Máx 10 requests/segundo (com vendas)
- Max 10 items por página
- Max 10 páginas por busca

**Documentação:** https://webservices.amazon.com/paapi5/documentation/

### Shopee

```python
# API pública (busca)
client = ShopeeClient()

# Partner API (para lojistas)
client = ShopeeClient(
    partner_id=123456,
    partner_key="YOUR_KEY",
    shop_id=789,
    access_token="SHOP_TOKEN",
)
```

**Documentação:** https://open.shopee.com/documents

## Variáveis de Ambiente

```env
# Mercado Livre (opcional)
ML_CLIENT_ID=your_client_id
ML_CLIENT_SECRET=your_client_secret

# Amazon (obrigatório para busca)
AMAZON_ACCESS_KEY=your_access_key
AMAZON_SECRET_KEY=your_secret_key
AMAZON_PARTNER_TAG=your-tag-20

# Shopee (opcional, para Partner API)
SHOPEE_PARTNER_ID=123456
SHOPEE_PARTNER_KEY=your_key
SHOPEE_SHOP_ID=789
```

## Algoritmos

### Melhor Custo-Benefício

O `best_value` é calculado com a fórmula:

```
score = (rating * 20) + (discount * 0.5) - (price / 50) + free_shipping_bonus

onde:
- rating: 0-5 → normalizado para 0-100
- discount: porcentagem de desconto
- price: preço em reais
- free_shipping_bonus: +10 se frete grátis
```

### Ordenação de Comparação

```python
# Por padrão, produtos são ordenados por:
1. Preço (menor primeiro)
2. Rating (maior primeiro, em caso de empate)
3. Frete grátis (prioridade)
```

## Arquitetura

```
backend/integrations/marketplaces/
├── __init__.py         # Exports públicos
├── base.py             # Classes abstratas e tipos
├── mercadolivre.py     # Cliente Mercado Livre
├── amazon.py           # Cliente Amazon PAAPI
├── shopee.py           # Cliente Shopee
├── manager.py          # Gerenciador unificado
└── ...

backend/api/routes/
└── marketplaces.py     # Endpoints REST
```

## Testes

```bash
# Rodar testes
pytest backend/tests/integrations/test_marketplaces.py -v

# Com coverage
pytest backend/tests/integrations/test_marketplaces.py --cov=backend/integrations/marketplaces

# Testes de integração (requer APIs reais)
pytest backend/tests/integrations/test_marketplaces.py -v -m "not skip"
```

## Tratamento de Erros

```python
try:
    results = await manager.search_all("produto")
except Exception as e:
    logger.error(f"Erro geral: {e}")

# Erros por marketplace são capturados e reportados
if results.errors:
    for mp, error in results.errors.items():
        logger.warning(f"{mp}: {error}")
```

## Performance

| Operação | Tempo Médio |
|----------|-------------|
| Busca ML | ~200ms |
| Busca Shopee | ~300ms |
| Busca Amazon | ~500ms |
| Comparação (3 MPs) | ~600ms (paralelo) |

## Roadmap

- [x] Mercado Livre API
- [x] Amazon PAAPI
- [x] Shopee API
- [ ] Magazine Luiza API
- [ ] Americanas API
- [ ] Casas Bahia API
- [ ] Cache Redis para buscas frequentes
- [ ] Alertas de preço
- [ ] Histórico de preços
