# 🤖 Professional Seller Bot - TikTrend Finder

Sistema de chatbot profissional com IA avançada, multi-canal e integração completa com CRM e Analytics.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Features](#features)
4. [Instalação](#instalação)
5. [Configuração](#configuração)
6. [API Reference](#api-reference)
7. [Integrações](#integrações)
8. [Workflows n8n](#workflows-n8n)
9. [Customização](#customização)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O Professional Seller Bot é um assistente de vendas conversacional projetado para:

- **Atender clientes 24/7** via WhatsApp, Instagram, TikTok e webchat
- **Qualificar leads automaticamente** com scoring baseado em comportamento
- **Buscar e comparar produtos** integrado ao sistema de preços
- **Escalar para humanos** quando necessário, com contexto completo
- **Integrar com CRM** para tracking completo do funil de vendas

### Fluxo de Conversa

```
┌─────────────────┐
│  Cliente envia  │
│    mensagem     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Intent Detector │──► 20+ intenções detectáveis
│  (Rule-based)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Handler por    │
│    Intenção     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────────┐
│ Bot   │ │ Handoff   │
│Response│ │ (Humano) │
└───┬───┘ └─────┬─────┘
    │           │
    ▼           ▼
┌─────────────────┐
│  Enviar via     │
│  Canal Original │
└─────────────────┘
```

---

## 🏗️ Arquitetura

### Componentes Principais

```
backend/modules/chatbot/
├── __init__.py                    # Exports do módulo
├── professional_seller_bot.py     # Core do bot
└── channel_integrations.py        # Adaptadores de canal

backend/api/routes/
└── seller_bot.py                  # API REST
```

### Classes Principais

| Classe | Responsabilidade |
|--------|-----------------|
| `ProfessionalSellerBot` | Orquestrador principal |
| `IntentDetector` | Detecção de intenções (rule-based) |
| `ConversationContext` | Estado da conversa |
| `ChannelRouter` | Roteamento multi-canal |
| `ChatwootAdapter` | Integração Chatwoot |
| `EvolutionAdapter` | Integração WhatsApp |

---

## ✨ Features

### 1. Detecção de Intenção

**20+ intenções suportadas:**

| Categoria | Intenções |
|-----------|-----------|
| Saudações | `greeting`, `farewell`, `help`, `menu` |
| Produtos | `product_search`, `product_info`, `price_check`, `compare_prices` |
| Compra | `how_to_buy`, `payment_info`, `shipping_info` |
| Suporte | `order_status`, `complaint`, `refund` |
| Ações | `talk_to_human`, `schedule`, `subscribe` |

### 2. Qualificação de Leads

```python
# Lead scoring automático
COLD → WARM → HOT → QUALIFIED

# Pontuação por ação:
- Buscar produto: +5
- Ver info: +10
- Verificar preço: +15
- Comparar: +20
- Como comprar: +50
```

### 3. Estágios do Funil

```python
NEW → GREETING → DISCOVERY → QUALIFICATION → 
PRODUCT_SEARCH → PRODUCT_DETAIL → COMPARISON → 
CLOSING → SUPPORT | HUMAN_HANDOFF
```

### 4. Multi-Canal

- ✅ WhatsApp (Evolution API)
- ✅ Chatwoot (Unified Inbox)
- ✅ Instagram (Graph API)
- 🔄 TikTok (em desenvolvimento)
- 🔄 Telegram (em desenvolvimento)

### 5. Templates de Resposta

```python
# Saudações dinâmicas por período
- Bom dia (5h-12h)
- Boa tarde (12h-18h)
- Boa noite (18h-5h)
- Usuário retornando (personalizado)

# Templates por contexto
- Menu principal
- Busca de produtos
- Detalhes do produto
- Comparação de preços
- Suporte e reclamações
```

---

## 🚀 Instalação

### 1. Dependências Python

```bash
cd backend
pip install -r requirements.txt
```

### 2. Variáveis de Ambiente

```bash
# .env
# Seller Bot
SELLER_BOT_ENABLED=true
SELLER_BOT_AI_ENABLED=true

# Chatwoot
CHATWOOT_API_URL=http://localhost:3000
CHATWOOT_API_TOKEN=your_token
CHATWOOT_ACCOUNT_ID=1

# Evolution API (WhatsApp)
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=your_key
EVOLUTION_INSTANCE=tiktrend-bot

# n8n
N8N_API_URL=http://localhost:5678
N8N_API_KEY=your_key
```

### 3. Importar Workflow n8n

```bash
python import_seller_bot_workflow.py
```

---

## ⚙️ Configuração

### Configurar Webhook Chatwoot

1. Acesse Chatwoot → Settings → Webhooks
2. Adicione novo webhook:
   - URL: `https://api.tiktrendfinder.com/seller-bot/webhook/chatwoot`
   - Eventos: `message_created`

### Configurar Webhook Evolution API

1. Acesse painel Evolution API
2. Configure webhook:
   - URL: `https://api.tiktrendfinder.com/seller-bot/webhook/evolution`
   - Eventos: `messages.upsert`

---

## 📡 API Reference

### Endpoints Principais

#### POST /seller-bot/message
Envia mensagem direta ao bot (útil para testes).

```json
{
  "channel": "webchat",
  "sender_id": "user123",
  "sender_name": "João",
  "content": "Quero um iPhone barato"
}
```

**Resposta:**
```json
{
  "status": "success",
  "responses": [
    {
      "content": "🔎 Buscando as melhores ofertas...",
      "quick_replies": ["1", "2", "3"],
      "intent": "product_search"
    }
  ]
}
```

#### GET /seller-bot/conversations
Lista conversas ativas.

```bash
curl -X GET "http://localhost:8000/seller-bot/conversations?active_only=true"
```

#### GET /seller-bot/stats
Estatísticas do bot.

```json
{
  "total_conversations": 150,
  "active_conversations": 23,
  "messages_today": 456,
  "handoffs_today": 12,
  "lead_distribution": {
    "cold": 80,
    "warm": 45,
    "hot": 20,
    "qualified": 5
  }
}
```

#### POST /seller-bot/conversations/{id}/handoff
Escala conversa para humano.

---

## 🔗 Integrações

### CRM Integration

O bot sincroniza automaticamente com o módulo CRM:

```python
# Ao detectar lead warm/hot
if context.lead_temperature in [WARM, HOT]:
    await crm_service.contacts.create(...)
    
# Ao detectar intenção de compra
if context.lead_temperature == HOT:
    await crm_service.deals.create(...)
```

### Analytics Integration

Eventos rastreados:
- `chatbot_message` - Cada mensagem processada
- `chatbot_intent` - Intenção detectada
- `chatbot_handoff` - Escalonamento para humano
- `chatbot_lead_qualified` - Lead qualificado

### n8n Integration

Webhooks disponíveis:
- `/webhook/seller-bot` - Mensagens do bot
- `/webhook/seller-bot/product-alert` - Alertas de preço
- `/webhook/seller-bot/daily-report` - Relatório diário

---

## 🔄 Workflows n8n

### Workflow Principal

```
Webhook → Filtrar → Processar Bot → Verificar Handoff
                                    ↓
                              ┌─────┴─────┐
                              │           │
                              ▼           ▼
                        Resposta      Handoff
                        Normal        Humano
                              │           │
                              ▼           ▼
                        Chatwoot/     Slack +
                        Evolution     Labels
                              │           │
                              └─────┬─────┘
                                    ▼
                              CRM + Analytics
```

### Alertas de Produto

Dispara notificação quando preço cai:

```json
POST /webhook/seller-bot/product-alert
{
  "phone": "5511999999999",
  "product_name": "iPhone 15",
  "old_price": 5999,
  "new_price": 4999,
  "discount_percent": 17,
  "store": "Amazon",
  "url": "https://..."
}
```

### Relatório Diário

Agendado para 18h, envia para Slack:

```
📊 Relatório Diário - Seller Bot

👥 Total conversas: 150
✅ Ativas: 23
💬 Mensagens hoje: 456
🔄 Handoffs: 12

📈 Top Intenções:
1. product_search: 120
2. greeting: 89
3. price_check: 67

🎯 Leads:
🔥 Hot: 20
🌡️ Warm: 45
❄️ Cold: 80
```

---

## 🎨 Customização

### Adicionar Nova Intenção

```python
# 1. Adicionar na enum Intent
class Intent(str, Enum):
    MY_NEW_INTENT = "my_new_intent"

# 2. Adicionar padrões
INTENT_PATTERNS = {
    Intent.MY_NEW_INTENT: [
        r"\b(padrão|regex|aqui)\b",
    ],
}

# 3. Criar handler
async def _handle_my_new_intent(self, message, context, analysis):
    return [BotResponse(content="Resposta personalizada")]

# 4. Registrar handler
self._intent_handlers[Intent.MY_NEW_INTENT] = self._handle_my_new_intent
```

### Personalizar Templates

```python
# Em ResponseTemplates
CUSTOM_TEMPLATES = {
    "minha_resposta": "Template personalizado com {variavel}",
}
```

### Integrar Novo Canal

```python
class MeuCanalAdapter(ChannelAdapter):
    async def parse_incoming(self, payload):
        # Converter para IncomingMessage
        pass
    
    async def send_response(self, response, recipient):
        # Enviar resposta
        pass

# Registrar
router.register_adapter(MessageChannel.MEU_CANAL, MeuCanalAdapter())
```

---

## 🔧 Troubleshooting

### Bot não responde

1. Verificar se webhook está configurado corretamente
2. Checar logs: `docker logs tiktrend-api`
3. Testar endpoint diretamente: `POST /seller-bot/message`

### Intenção não detectada

1. Verificar padrões regex em `INTENT_PATTERNS`
2. Adicionar palavras-chave faltantes
3. Considerar usar IA para casos complexos

### Handoff não funciona

1. Verificar configuração do Chatwoot
2. Checar se labels existem
3. Verificar integração Slack (se configurado)

### Contexto perdido

1. Por padrão, contexto expira em 30 minutos
2. Aumentar timeout em `_get_or_create_context`
3. Em produção, usar Redis para persistência

---

## 📈 Métricas Recomendadas

| Métrica | Descrição | Meta |
|---------|-----------|------|
| Taxa de Resolução | % conversas resolvidas sem handoff | > 80% |
| Tempo Médio de Resposta | Latência do bot | < 500ms |
| Taxa de Qualificação | % leads que chegam a HOT | > 10% |
| Satisfação | CSAT pós-atendimento | > 4.0/5 |
| Conversão | % leads → vendas | > 5% |

---

## 🆘 Suporte

- 📧 Email: suporte@tiktrendfinder.com
- 💬 Discord: discord.gg/tiktrendfinder
- 📖 Docs: docs.tiktrendfinder.com

---

**Versão:** 1.0.0  
**Última atualização:** 30 de janeiro de 2025  
**Mantido por:** Equipe TikTrend Finder
