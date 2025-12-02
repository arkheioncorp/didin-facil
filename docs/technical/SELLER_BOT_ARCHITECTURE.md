# 🤖 Seller Bot - Arquitetura Técnica

> **Versão:** 2.0.0  
> **Data:** Novembro 2025  
> **Status:** Production Ready  

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura de Sistema](#arquitetura-de-sistema)
3. [APIs e Rotas](#apis-e-rotas)
4. [WebSocket](#websocket)
5. [Armazenamento Redis](#armazenamento-redis)
6. [Métricas Prometheus](#métricas-prometheus)
7. [Integrações](#integrações)
8. [Frontend](#frontend)
9. [Segurança](#segurança)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O Seller Bot é composto por **dois módulos distintos**:

| Módulo | API Base | Função | Tecnologia |
|--------|----------|--------|------------|
| **Bot (Automação)** | `/bot/*` | Automação de browser para TikTok Seller Center | Playwright + Python |
| **Seller Bot (IA)** | `/seller-bot/*` | Chatbot IA para atendimento multicanal | OpenAI + FastAPI |

### Diagrama de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Frontend (React)                               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  SellerBot.tsx - Unified Dashboard                                │   │
│  │  ├── BotDashboard (Automação TikTok)                              │   │
│  │  └── ChatbotDashboard (IA Multicanal)                             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────┬───────────────────────┬───────────────────────┘
                         │                       │
              WebSocket  │                       │  REST API
                         ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Backend (FastAPI)                              │
│  ┌─────────────────────────┐   ┌──────────────────────────────────────┐ │
│  │  /bot/* (bot.py)        │   │  /seller-bot/* (seller_bot.py)       │ │
│  │  ├── Tasks CRUD         │   │  ├── Webhooks (3 canais)             │ │
│  │  ├── Profiles CRUD      │   │  ├── Conversations                   │ │
│  │  ├── Start/Stop Bot     │   │  ├── Stats & Analytics               │ │
│  │  └── Stats              │   │  └── Config                          │ │
│  └──────────┬──────────────┘   └──────────────┬───────────────────────┘ │
│             │                                 │                          │
│             ▼                                 ▼                          │
│  ┌──────────────────────┐        ┌──────────────────────────────────┐   │
│  │  Playwright Worker    │        │  ProfessionalSellerBot           │   │
│  │  (Browser Automation) │        │  ├── Intent Detection            │   │
│  └──────────────────────┘        │  ├── Response Generation          │   │
│                                   │  └── CRM Integration              │   │
│                                   └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                         │                       │
                         ▼                       ▼
                   ┌───────────┐          ┌───────────────┐
                   │ PostgreSQL│          │     Redis     │
                   │  (Tasks,  │          │  (Contexts,   │
                   │ Profiles) │          │   Sessions)   │
                   └───────────┘          └───────────────┘
```

---

## 🏗️ Arquitetura de Sistema

### Camadas

```
├── Presentation Layer (Frontend)
│   └── SellerBot.tsx
│       ├── Hooks: useQuery (TanStack)
│       ├── State: Local + Server State
│       └── Real-time: WebSocket
│
├── API Layer (FastAPI)
│   ├── bot.py (11 endpoints)
│   └── seller_bot.py (14 endpoints)
│
├── Business Logic Layer
│   ├── ProfessionalSellerBot (IA)
│   └── BotWorker (Automação)
│
├── Data Access Layer
│   ├── SQLAlchemy (PostgreSQL)
│   └── Redis (aioredis)
│
└── External Services
    ├── OpenAI API
    ├── Chatwoot API
    ├── Evolution API (WhatsApp)
    ├── Instagram Graph API
    └── TikTok Seller Center
```

### Princípios Arquiteturais

1. **Separação de Responsabilidades**: APIs `/bot/*` e `/seller-bot/*` completamente isoladas
2. **Stateless API**: Contextos persistidos em Redis, não em memória
3. **Event-Driven**: WebSocket para atualizações em tempo real
4. **Graceful Degradation**: Fallback para polling se WebSocket falhar
5. **Observable**: Métricas Prometheus em todos os endpoints

---

## 🛣️ APIs e Rotas

### `/bot/*` - Automação Browser (11 endpoints)

| Método | Rota | Descrição | Métricas |
|--------|------|-----------|----------|
| `POST` | `/bot/tasks` | Criar tarefa de automação | `bot_task_created_total` |
| `GET` | `/bot/tasks` | Listar todas as tarefas | - |
| `DELETE` | `/bot/tasks/{id}` | Remover tarefa | - |
| `GET` | `/bot/stats` | Estatísticas gerais | - |
| `POST` | `/bot/profiles` | Criar perfil TikTok | `bot_profile_created_total` |
| `GET` | `/bot/profiles` | Listar perfis | - |
| `DELETE` | `/bot/profiles/{id}` | Remover perfil | - |
| `POST` | `/bot/profiles/{id}/verify` | Verificar login | `bot_profile_verified_total` |
| `POST` | `/bot/start` | Iniciar worker | `bot_started_total` |
| `POST` | `/bot/stop` | Parar worker | `bot_stopped_total` |
| `GET` | `/bot/worker-status` | Status do worker | - |

#### Exemplo de Request

```bash
# Criar tarefa
curl -X POST http://localhost:8000/bot/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "reply_comments",
    "profile_id": "123",
    "config": {
      "max_replies": 50,
      "delay_seconds": 5
    }
  }'
```

### `/seller-bot/*` - Chatbot IA (14 endpoints)

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/seller-bot/webhook/chatwoot` | Webhook Chatwoot |
| `POST` | `/seller-bot/webhook/evolution` | Webhook Evolution (WhatsApp) |
| `GET/POST` | `/seller-bot/webhook/instagram` | Webhook Instagram |
| `POST` | `/seller-bot/message` | Enviar mensagem manual |
| `GET` | `/seller-bot/conversations` | Listar conversas ativas |
| `DELETE` | `/seller-bot/conversations` | Limpar todas conversas |
| `POST` | `/seller-bot/conversations/{id}/handoff` | Transferir para humano |
| `GET` | `/seller-bot/stats` | Estatísticas gerais |
| `GET` | `/seller-bot/stats/intents` | Estatísticas de intents |
| `GET` | `/seller-bot/stats/funnel` | Funil de vendas |
| `GET` | `/seller-bot/config` | Obter configuração |
| `PATCH` | `/seller-bot/config` | Atualizar configuração |
| `GET` | `/seller-bot/health` | Health check |

#### Exemplo de Request

```bash
# Processar mensagem
curl -X POST http://localhost:8000/seller-bot/message \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "whatsapp:5511999999999",
    "message": "Qual o preço do produto X?",
    "channel": "whatsapp"
  }'
```

---

## 🔌 WebSocket

### Conexão

```typescript
// Frontend connection
const ws = new WebSocket(`wss://api.didinfacil.com/ws/notifications?token=${accessToken}`);
```

### Tipos de Notificação Bot

| Tipo | Descrição | Payload |
|------|-----------|---------|
| `bot_task_started` | Tarefa iniciada | `{ task_id, task_type, profile_id }` |
| `bot_task_completed` | Tarefa concluída | `{ task_id, result, duration }` |
| `bot_task_failed` | Tarefa falhou | `{ task_id, error, retry_count }` |
| `bot_worker_started` | Worker iniciado | `{ worker_id, profiles }` |
| `bot_worker_stopped` | Worker parado | `{ worker_id, reason }` |

### Implementação Backend

```python
# backend/api/routes/websocket_notifications.py

class NotificationType(str, Enum):
    # ... outros tipos
    BOT_TASK_STARTED = "bot_task_started"
    BOT_TASK_COMPLETED = "bot_task_completed"
    BOT_TASK_FAILED = "bot_task_failed"
    BOT_WORKER_STARTED = "bot_worker_started"
    BOT_WORKER_STOPPED = "bot_worker_stopped"

# Enviar notificação
await ws_manager.broadcast_to_user(
    user_id=user.id,
    message={
        "type": NotificationType.BOT_TASK_COMPLETED,
        "payload": {"task_id": task.id, "result": result}
    }
)
```

### Implementação Frontend

```typescript
// src/services/websocket.ts
type BotNotificationType = 
  | 'bot_task_started'
  | 'bot_task_completed' 
  | 'bot_task_failed'
  | 'bot_worker_started'
  | 'bot_worker_stopped';

// Handler
useEffect(() => {
  websocketService.subscribe('bot_task_completed', (data) => {
    queryClient.invalidateQueries({ queryKey: ['botTasks'] });
    toast.success(`Tarefa ${data.task_id} concluída!`);
  });
}, []);
```

---

## 🔴 Armazenamento Redis

### Keys Utilizadas

| Pattern | Descrição | TTL |
|---------|-----------|-----|
| `chatbot:context:{contact_id}` | Contexto de conversa | 30 min |
| `chatbot:session:{session_id}` | Sessão do usuário | 1 hora |
| `bot:task:{task_id}:status` | Status da tarefa | 24 horas |
| `bot:worker:heartbeat` | Heartbeat do worker | 1 min |

### Context Store

```python
# backend/modules/chatbot/context_store.py

class ContextStore:
    KEY_PREFIX = "chatbot:context:"
    DEFAULT_TTL = 1800  # 30 minutos
    
    async def get_context(self, contact_id: str) -> dict | None:
        key = f"{self.KEY_PREFIX}{contact_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def set_context(self, contact_id: str, context: dict) -> None:
        key = f"{self.KEY_PREFIX}{contact_id}"
        await self.redis.set(key, json.dumps(context), ex=self.DEFAULT_TTL)
    
    async def delete_context(self, contact_id: str) -> None:
        key = f"{self.KEY_PREFIX}{contact_id}"
        await self.redis.delete(key)
    
    async def get_all_contexts(self) -> list[dict]:
        keys = await self.redis.keys(f"{self.KEY_PREFIX}*")
        contexts = []
        for key in keys:
            data = await self.redis.get(key)
            if data:
                context = json.loads(data)
                context["contact_id"] = key.replace(self.KEY_PREFIX, "")
                contexts.append(context)
        return contexts
```

### Fallback Strategy

```python
# Se Redis não disponível, usa memória local
try:
    context = await self.context_store.get_context(contact_id)
except Exception:
    context = self._memory_contexts.get(contact_id)
```

---

## 📊 Métricas Prometheus

### Métricas Expostas

```python
# /metrics endpoint

# Contadores
bot_task_created_total{task_type="reply_comments"} 150
bot_task_completed_total{task_type="reply_comments"} 145
bot_task_failed_total{task_type="reply_comments", error="timeout"} 5
bot_profile_created_total 12
bot_profile_verified_total{status="success"} 10
bot_profile_verified_total{status="failed"} 2
bot_started_total 8
bot_stopped_total 7

# Histogramas
bot_task_duration_seconds_bucket{le="1.0"} 50
bot_task_duration_seconds_bucket{le="5.0"} 120
bot_task_duration_seconds_bucket{le="10.0"} 140

# Gauges
bot_active_tasks 3
bot_active_profiles 5
bot_worker_status 1  # 0=stopped, 1=running
```

### Grafana Dashboard

Query de exemplo:
```promql
# Taxa de sucesso de tarefas
sum(rate(bot_task_completed_total[5m])) / 
sum(rate(bot_task_created_total[5m])) * 100

# Latência P95
histogram_quantile(0.95, rate(bot_task_duration_seconds_bucket[5m]))
```

---

## 🔗 Integrações

### Chatwoot

```python
# Webhook recebido
POST /seller-bot/webhook/chatwoot
{
    "event": "message_created",
    "message": {
        "content": "Olá, preciso de ajuda",
        "conversation_id": 123
    }
}

# Resposta enviada via API
POST https://chatwoot.didinfacil.com/api/v1/conversations/{id}/messages
```

### Evolution API (WhatsApp)

```python
# Webhook recebido
POST /seller-bot/webhook/evolution
{
    "instance": "default",
    "data": {
        "key": {"remoteJid": "5511999999999@s.whatsapp.net"},
        "message": {"conversation": "Oi!"}
    }
}

# Resposta enviada
POST https://evolution.didinfacil.com/message/sendText/{instance}
```

### Instagram Graph API

```python
# Verificação (GET)
GET /seller-bot/webhook/instagram?hub.mode=subscribe&hub.verify_token=XXX

# Webhook recebido (POST)
POST /seller-bot/webhook/instagram
{
    "object": "instagram",
    "entry": [{
        "messaging": [{
            "sender": {"id": "123"},
            "message": {"text": "Oi!"}
        }]
    }]
}

# Resposta enviada
POST https://graph.facebook.com/v18.0/me/messages?access_token=XXX
```

---

## 🖥️ Frontend

### Estrutura do Componente

```
src/pages/SellerBot.tsx (900+ linhas)
├── State Management
│   ├── TanStack Query (Server State)
│   ├── useState (Local State)
│   └── WebSocket (Real-time)
│
├── API Calls
│   ├── useBotTasks() → GET /bot/tasks
│   ├── useBotProfiles() → GET /bot/profiles
│   ├── useBotStats() → GET /bot/stats
│   ├── useSellerBotConversations() → GET /seller-bot/conversations
│   └── useSellerBotStats() → GET /seller-bot/stats
│
├── Components
│   ├── Tabs (Automação | Chatbot IA)
│   ├── TaskList
│   ├── ProfileList
│   ├── ConversationList
│   └── StatsCards
│
└── Real-time Updates
    ├── WebSocket primary
    └── 15s polling fallback
```

### Hooks Principais

```typescript
// Tarefas de automação
const { data: tasks } = useQuery({
  queryKey: ['botTasks'],
  queryFn: () => api.get('/bot/tasks'),
  refetchInterval: isWsConnected ? 30000 : 15000,
});

// Conversas do chatbot
const { data: conversations } = useQuery({
  queryKey: ['sellerBotConversations'],
  queryFn: () => api.get('/seller-bot/conversations'),
  refetchInterval: isWsConnected ? 30000 : 15000,
});
```

---

## 🔒 Segurança

### Autenticação

- JWT Bearer Token em todos os endpoints
- Token renovado automaticamente no frontend
- Validação de permissões por endpoint

### Rate Limiting

```python
# Webhooks: 100 req/min
# API geral: 30 req/min por IP
# Bot start/stop: 5 req/min por usuário
```

### Validação de Input

```python
# Pydantic models para todos os inputs
class TaskCreate(BaseModel):
    task_type: TaskType  # Enum validado
    profile_id: str = Field(..., min_length=1)
    config: dict = Field(default_factory=dict)
    
    @validator('config')
    def validate_config(cls, v):
        # Validação customizada
        return v
```

### Webhooks

```python
# Verificação de assinatura (quando disponível)
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)
```

---

## 🔧 Troubleshooting

### Logs Estruturados

```python
import structlog
logger = structlog.get_logger()

logger.info(
    "bot_task_created",
    task_id=task.id,
    task_type=task.task_type,
    user_id=user.id
)
```

### Erros Comuns

| Sintoma | Causa Provável | Solução |
|---------|---------------|---------|
| 500 em `/bot/start` | Worker já rodando | Verificar `/bot/worker-status` primeiro |
| Contexto perdido | TTL Redis expirado | Aumentar TTL ou re-engajar cliente |
| WebSocket desconecta | Token expirado | Renovar token antes de reconectar |
| Webhook 401 | Token inválido | Verificar configuração de integração |

### Debug Commands

```bash
# Ver logs do bot
docker-compose logs -f api | grep -E "(bot_|seller_bot)"

# Status do Redis
redis-cli KEYS "chatbot:*" | head -20

# Métricas atuais
curl http://localhost:8000/metrics | grep bot_

# Testar webhook manualmente
curl -X POST http://localhost:8000/seller-bot/webhook/evolution \
  -H "Content-Type: application/json" \
  -d '{"instance":"test","data":{"key":{"remoteJid":"test"},"message":{"conversation":"Olá"}}}'
```

---

## 📈 Melhorias Futuras

1. **[ ] Circuit Breaker** para APIs externas (OpenAI, Chatwoot)
2. **[ ] Retry com backoff exponencial** para falhas de webhook
3. **[ ] Cache de respostas frequentes** (FAQ)
4. **[ ] A/B Testing** de prompts do chatbot
5. **[ ] Dashboard de analytics** mais detalhado
6. **[ ] Suporte a Telegram** como canal adicional

---

## 📚 Referências

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TanStack Query](https://tanstack.com/query)
- [Prometheus Python Client](https://prometheus.github.io/client_python/)
- [Chatwoot API](https://www.chatwoot.com/developers/api/)
- [Evolution API](https://evolution-api.com/)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api/)

---

**Mantido por:** Equipe Didin Fácil  
**Última atualização:** Novembro 2025
