# Arquitetura de Hubs Centralizados

## Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION LAYER                              │
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │   API    │  │  Seller  │  │ Workers  │  │   n8n    │               │
│  │  Routes  │  │   Bot    │  │          │  │ Webhooks │               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
└───────┼─────────────┼─────────────┼─────────────┼───────────────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌──────────────────┐      ┌──────────────────┐
│  Direct Hub Use  │      │  Adapter Layer   │
│                  │      │  (for Seller Bot)│
└────────┬─────────┘      └────────┬─────────┘
         │                         │
         │                ┌────────┴────────┐
         │                │                 │
         │                ▼                 ▼
         │    ┌──────────────────┐ ┌──────────────────┐
         │    │ WhatsAppHub      │ │ InstagramHub     │
         │    │ Adapter          │ │ Adapter          │
         │    └────────┬─────────┘ └────────┬─────────┘
         │             │                    │
         └─────────────┴────────────────────┘
                       │
         ┌─────────────┴─────────────────────────────┐
         │                                           │
         ▼                                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        INTEGRATION HUBS LAYER                           │
│                         (Singleton Pattern)                             │
│                                                                         │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐  │
│  │   WhatsApp Hub    │  │  Instagram Hub    │  │   TikTok Hub      │  │
│  │                   │  │                   │  │                   │  │
│  │ • Instances Mgmt  │  │ • Direct Messages │  │ • Sessions Mgmt   │  │
│  │ • Send Messages   │  │ • Quick Replies   │  │ • Video Upload    │  │
│  │ • Webhooks        │  │ • Media Messages  │  │ • Analytics       │  │
│  │ • QR Code         │  │ • Typing Status   │  │ • (No DM Support) │  │
│  │ • Chatwoot Sync   │  │ • Webhook Parse   │  │                   │  │
│  └─────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘  │
└────────────┼──────────────────────┼──────────────────────┼─────────────┘
             │                      │                      │
             │                      │                      │
         ┌───┴──────────────────────┴──────────────────────┴───┐
         │                                                      │
         ▼                                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL APIS LAYER                             │
│                                                                         │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐  │
│  │  Evolution API    │  │  Facebook Graph   │  │   TikTok API      │  │
│  │  (WhatsApp)       │  │  API (Instagram)  │  │  (Private/Web)    │  │
│  │                   │  │                   │  │                   │  │
│  │ localhost:8082    │  │ graph.facebook... │  │ tiktok.com        │  │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Fluxo de Mensagens

### 1. Envio de Mensagem (Application → External API)

```
User Code
   │
   ├─→ get_whatsapp_hub()
   │      │
   │      └─→ WhatsAppHub.send_message()
   │             │
   │             └─→ HTTP POST → Evolution API
   │                    │
   │                    └─→ WhatsApp Servers
   │
   ├─→ get_instagram_hub()
   │      │
   │      └─→ InstagramHub.send_message()
   │             │
   │             └─→ HTTP POST → Graph API
   │                    │
   │                    └─→ Instagram Servers
   │
   └─→ get_tiktok_hub()
          │
          └─→ TikTokHub.upload_video()
                 │
                 └─→ Browser Automation → TikTok Web
```

### 2. Recebimento de Mensagem (External API → Application)

```
WhatsApp/Instagram Servers
   │
   └─→ Webhook HTTP POST
          │
          ├─→ /api/v2/whatsapp/webhook
          │      │
          │      └─→ WhatsAppHub.normalize_webhook()
          │             │
          │             └─→ WhatsAppHubAdapter.parse_incoming()
          │                    │
          │                    └─→ Seller Bot
          │
          └─→ /api/instagram/webhook
                 │
                 └─→ InstagramHub.normalize_webhook_event()
                        │
                        └─→ InstagramHubAdapter.parse_incoming()
                               │
                               └─→ Seller Bot
```

## Padrões de Configuração

### Singleton Pattern

```python
# backend/integrations/whatsapp_hub.py

_whatsapp_hub: Optional[WhatsAppHub] = None

def get_whatsapp_hub() -> WhatsAppHub:
    """Retorna instância singleton do WhatsApp Hub."""
    global _whatsapp_hub
    if _whatsapp_hub is None:
        _whatsapp_hub = WhatsAppHub()
    return _whatsapp_hub
```

### Adapter Pattern

```python
# backend/modules/chatbot/whatsapp_adapter.py

class WhatsAppHubAdapter(ChannelAdapter):
    """Adapta WhatsAppHub para interface do Seller Bot."""
    
    def __init__(self, hub: WhatsAppHub, instance_name: str):
        self.hub = hub
        self.instance_name = instance_name
    
    async def parse_incoming(self, payload):
        # Converte formato Hub → formato Seller Bot
        ...
    
    async def send_response(self, response, recipient_id):
        # Converte formato Seller Bot → formato Hub
        ...
```

## Comparação: Antes vs Depois

### ❌ Antes (Código Espalhado)

```
api/routes/whatsapp.py
   └─→ httpx.post(evolution_url, ...)  # Chamada direta HTTP

api/routes/instagram.py
   └─→ httpx.post(graph_url, ...)     # Chamada direta HTTP

modules/chatbot/channel_integrations.py
   ├─→ EvolutionAdapter
   │      └─→ httpx.post(...)          # Duplicação de lógica
   └─→ InstagramAdapter
          └─→ httpx.post(...)          # Duplicação de lógica

workers/upload_tiktok.py
   └─→ TikTokClient(...)               # Lógica isolada
```

**Problemas:**
- ❌ Lógica duplicada em múltiplos arquivos
- ❌ Difícil manutenção (mudança em API = mudar N arquivos)
- ❌ Configuração espalhada
- ❌ Difícil testar (mocks em vários lugares)

### ✅ Depois (Hub Centralizado)

```
integrations/
   ├─→ whatsapp_hub.py    # ÚNICO ponto WhatsApp
   ├─→ instagram_hub.py   # ÚNICO ponto Instagram
   └─→ tiktok_hub.py      # ÚNICO ponto TikTok

api/routes/whatsapp_v2.py
   └─→ get_whatsapp_hub().send_message(...)

api/routes/instagram.py
   └─→ get_instagram_hub().send_message(...)

modules/chatbot/whatsapp_adapter.py
   └─→ WhatsAppHubAdapter(hub)
          └─→ hub.send_message(...)

workers/upload_tiktok.py
   └─→ get_tiktok_hub().upload_video(...)
```

**Benefícios:**
- ✅ Lógica centralizada (1 arquivo por plataforma)
- ✅ Fácil manutenção
- ✅ Configuração unificada
- ✅ Testes simplificados (mock do hub apenas)
- ✅ Reutilização de código
- ✅ Singleton = menos overhead de conexões HTTP

## Responsabilidades de Cada Camada

### Application Layer
- **Responsabilidade:** Lógica de negócio
- **Exemplos:** Rotas da API, Seller Bot, Workers
- **NÃO deve:** Conhecer detalhes de APIs externas

### Adapter Layer (Opcional)
- **Responsabilidade:** Traduzir entre interfaces
- **Exemplos:** WhatsAppHubAdapter traduz Hub ↔ Seller Bot
- **NÃO deve:** Implementar lógica de integração

### Integration Hubs Layer
- **Responsabilidade:** Integração com APIs externas
- **Exemplos:** WhatsAppHub, InstagramHub, TikTokHub
- **NÃO deve:** Conhecer lógica de negócio da aplicação

### External APIs Layer
- **Responsabilidade:** Serviços externos de terceiros
- **Exemplos:** Evolution API, Graph API, TikTok
- **NÃO controlamos:** Esta camada

## Checklist de Migração

Ao migrar código antigo para a nova arquitetura:

- [ ] Identifique todas as chamadas HTTP diretas a APIs externas
- [ ] Verifique se existe um Hub para aquela plataforma
- [ ] Substitua chamadas diretas por `get_*_hub().método()`
- [ ] Se for Seller Bot, use o `*HubAdapter` correspondente
- [ ] Remova código duplicado
- [ ] Atualize testes para mockar o Hub em vez de httpx
- [ ] Documente a mudança no CHANGELOG.md

## Próximos Passos

### Futuras Integrações

Ao adicionar novas plataformas (Facebook, Twitter, LinkedIn, etc.):

1. Criar `{plataforma}_hub.py` em `backend/integrations/`
2. Implementar padrão singleton: `get_{plataforma}_hub()`
3. Se Seller Bot, criar `{plataforma}_adapter.py` em `backend/modules/chatbot/`
4. Exportar em `backend/integrations/__init__.py`
5. Atualizar este diagrama e `HUBS_GUIDE.md`

### Melhorias Planejadas

- [ ] Rate limiting centralizado nos Hubs
- [ ] Circuit breaker pattern para resiliência
- [ ] Retry automático com exponential backoff
- [ ] Métricas unificadas (Prometheus)
- [ ] Health checks dos hubs
- [ ] WebSocket support para eventos em tempo real

---

**Última atualização:** 30 de novembro de 2025  
**Versão:** 2.0.0
