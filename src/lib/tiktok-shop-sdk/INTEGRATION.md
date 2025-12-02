# TikTok Shop SDK - Guia de Integração

> SDK copiado de `~/Downloads/nodejs_sdk/` em 02/12/2025

## Status: ⏳ Aguardando Aprovação

A integração com TikTok Shop API está pendente:
- App em avaliação no Partner Center
- Restrição regional detectada (app não configurado para Brasil)

## Estrutura do SDK

```
src/lib/tiktok-shop-sdk/
├── api/           # 42 APIs versionadas
├── client/        # TikTokShopNodeApiClient
├── model/         # Tipos TypeScript
├── utils/         # Gerador de assinatura HMAC
└── index.ts       # Entry point
```

## Instalação de Dependências

```bash
npm install request @types/request
```

## Uso Básico (quando OAuth funcionar)

```typescript
import { 
  ClientConfiguration, 
  TikTokShopNodeApiClient,
  AccessTokenTool 
} from '@/lib/tiktok-shop-sdk';

// 1. Configurar credenciais
ClientConfiguration.globalConfig.app_key = import.meta.env.VITE_TIKTOK_SHOP_APP_KEY;
ClientConfiguration.globalConfig.app_secret = import.meta.env.VITE_TIKTOK_SHOP_APP_SECRET;

// 2. Criar cliente
const client = new TikTokShopNodeApiClient({
  config: { sandbox: false }
});

// 3. Obter token (após OAuth)
const tokenResponse = await AccessTokenTool.getAccessToken(
  authCode,
  appKey,
  appSecret
);

// 4. Buscar produtos
const products = await client.api.ProductV202502Api.ProductsSearchPost(
  20,                           // pageSize
  tokenResponse.access_token,   // token
  'application/json',           // Content-Type
);
```

## APIs Principais

| API | Uso |
|-----|-----|
| `ProductV202502Api.ProductsSearchPost` | Buscar produtos da loja |
| `SellerV202309Api.ShopsGet` | Listar lojas ativas |
| `OrderV202507Api` | Gestão de pedidos |
| `PromotionV202406Api` | Cupons e promoções |

## Próximos Passos

1. [ ] Resolver região no Partner Center
2. [ ] Completar fluxo OAuth
3. [ ] Implementar service layer no backend
4. [ ] Criar hooks React para integração

## Alternativa: Affiliate APIs

Para comparação de preços (sem OAuth de seller):

```typescript
// Buscar produtos com Open Collaboration
// Requer credenciais de Creator/Affiliate
POST /affiliate/202410/products/search
{
  "keyword": "smartphone",
  "commission_rate_min": 5,
  "category_id": "..."
}
```

## Documentação

- [SDK README](./README.md)
- [Análise Técnica](/docs/technical/tiktok-shop-api-analysis.md)
- [TikTok Shop Partner Center](https://partner.tiktokshop.com)
