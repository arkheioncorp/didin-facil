# Sistema de Automações n8n - Didin Fácil

## Visão Geral

O sistema de automações do Didin Fácil integra com n8n para orquestrar workflows automatizados de marketing, vendas e suporte ao cliente.

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                     Professional Seller Bot                      │
│                   (Intent Detection & Handlers)                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ _trigger_automations()
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      N8n Orchestrator                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │ Rate Limiter   │  │ Channel Router │  │ Event Queue    │     │
│  └────────────────┘  └────────────────┘  └────────────────┘     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
│   Scheduler     │ │  Webhooks   │ │  Dashboard  │
│  (Async Jobs)   │ │  (n8n)      │ │  (API)      │
└─────────────────┘ └─────────────┘ └─────────────┘
```

## Componentes

### 1. N8n Orchestrator (`backend/modules/automation/n8n_orchestrator.py`)

Orquestra todas as automações, gerenciando:
- **23 tipos de automação** (AutomationType enum)
- **Rate limiting** por usuário/automação
- **Multi-channel** (WhatsApp, Email, SMS, Push)
- **Prioridades** (HIGH, NORMAL, LOW)

#### Tipos de Automação

| Tipo | Descrição | Delay Padrão |
|------|-----------|--------------|
| `new_user_welcome` | Boas-vindas para novos usuários | 1 min |
| `lead_nurturing` | Nutrição de leads | 1 hora |
| `cart_abandoned` | Recuperação de carrinho | 30 min |
| `price_drop_alert` | Alerta de queda de preço | Imediato |
| `post_purchase` | Agradecimento pós-compra | 5 min |
| `review_request` | Solicitação de avaliação | 24 horas |
| `complaint_alert` | Alerta de reclamação | Imediato |
| `human_handoff` | Escalonamento humano | Imediato |
| `lead_qualified` | Lead qualificado | Imediato |
| `deal_won` | Negócio fechado | 5 min |
| `reengagement` | Reengajamento | 3 dias |

### 2. Scheduler (`backend/modules/automation/scheduler.py`)

Processa eventos assíncronos:
- **Agendamento com delay** configurable
- **Batch processing** (50 eventos/ciclo)
- **Retry automático** (3 tentativas)
- **Priorização** de eventos urgentes
- **Eventos recorrentes** (nurturing sequences)

### 3. Dashboard API (`backend/api/routes/automation_dashboard.py`)

Endpoints para monitoramento:
- `GET /automation/dashboard/health` - Health check
- `GET /automation/dashboard/overview` - Visão geral
- `GET /automation/dashboard/metrics` - Métricas
- `GET /automation/dashboard/queue/depth` - Profundidade da fila
- `POST /automation/dashboard/schedule` - Agendar evento
- `DELETE /automation/dashboard/schedule/{id}` - Cancelar evento

## Workflows n8n

Localização: `docker/n8n-workflows/seller-bot/`

### Workflows Disponíveis

1. **00-webhook-registry.json** - Router/Registry central
2. **01-new-user-welcome.json** - Onboarding sequence
3. **02-lead-nurturing.json** - Lead nurturing
4. **03-cart-abandoned.json** - Cart recovery
5. **04-price-drop-alert.json** - Price alerts
6. **05-post-purchase.json** - Thank you flow
7. **06-review-request.json** - Review solicitation
8. **07-complaint-alert.json** - Support escalation
9. **08-human-handoff.json** - Human transfer
10. **09-lead-qualified.json** - Hot lead notification
11. **10-deal-won.json** - Deal celebration
12. **11-reengagement.json** - Reactivation campaign
13. **12-scheduler-processor.json** - Scheduled events

### Importação no n8n

```bash
# Via CLI
n8n import:workflow --input=docker/n8n-workflows/seller-bot/*.json

# Via API
curl -X POST "http://localhost:5678/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @docker/n8n-workflows/seller-bot/01-new-user-welcome.json
```

## Integração com Seller Bot

O Professional Seller Bot dispara automações em pontos-chave:

```python
# Em qualquer handler do seller bot:
await self._trigger_automations(
    context=context,
    event_type="lead_qualified",
    data={
        "user_id": context.user_id,
        "user_name": context.user_name,
        "channel": context.channel.value,
        "lead_score": context.lead_score,
    }
)
```

### Handlers com Automação

| Handler | Automação Disparada |
|---------|---------------------|
| `_handle_greeting` | `new_user_welcome` |
| `_handle_complaint` | `complaint_alert` |
| `_handle_human_handoff` | `human_handoff` |
| `_handle_alert_create` | `price_drop_alert` |
| `_handle_purchase_interest` | `lead_qualified` |
| `_handle_cart_abandoned_check` | `cart_abandoned` |

## Banco de Dados

Schema SQL: `docker/n8n-workflows/seller-bot/database-schema.sql`

### Tabelas

- `automation_events` - Histórico de eventos
- `automation_metrics` - Métricas agregadas
- `automation_schedules` - Agendamentos ativos
- `user_automation_preferences` - Preferências do usuário

## Configuração

### Variáveis de Ambiente

```env
# n8n
N8N_API_URL=http://localhost:5678
N8N_API_KEY=your_api_key
N8N_WEBHOOK_BASE_URL=http://localhost:5678/webhook

# Rate Limiting
AUTOMATION_MAX_PER_USER_PER_DAY=100
AUTOMATION_TIME_WINDOW_MINUTES=60

# Canais
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=your_key
```

### Python

```python
from modules.automation import (
    get_orchestrator,
    get_scheduler,
    start_scheduler,
    AutomationType,
)

# Inicializar
orchestrator = get_orchestrator()
scheduler = get_scheduler(orchestrator)

# Iniciar processamento
await start_scheduler(orchestrator)

# Disparar automação
await orchestrator.trigger_welcome(
    user_id="user_123",
    user_name="João",
    channel="whatsapp"
)

# Agendar evento
await scheduler.schedule(
    automation_type=AutomationType.LEAD_NURTURING,
    user_id="user_123",
    data={"message": "Follow-up"},
    delay_minutes=60
)
```

## Monitoramento

### Grafana Dashboard

Métricas disponíveis:
- Taxa de sucesso por automação
- Tempo médio de processamento
- Eventos na fila
- Distribuição por canal
- Erros e retries

### Alertas

Configurar no AlertManager:
- Taxa de falha > 10%
- Fila > 1000 eventos
- Latência > 5s

## Testes

```bash
# Rodar testes
cd backend
pytest tests/test_automation_integration.py -v

# Com coverage
pytest tests/test_automation_integration.py --cov=modules/automation
```

## Troubleshooting

### Evento não dispara

1. Verificar se automação está habilitada
2. Checar rate limiting
3. Verificar logs do orchestrator
4. Testar webhook n8n diretamente

### Scheduler não processa

1. Verificar se scheduler está rodando
2. Checar conexão com n8n
3. Verificar eventos na fila
4. Analisar logs de erro

### Performance lenta

1. Aumentar batch_size
2. Verificar conexão de rede
3. Analisar métricas de processamento
4. Considerar sharding da fila

## Roadmap

- [ ] Persistência em Redis
- [ ] Dead letter queue
- [ ] A/B testing de mensagens
- [ ] ML para otimização de timing
- [ ] Multi-tenant support
