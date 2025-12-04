# 🚀 n8n Improvements - Deployment Guide

## 📋 Resumo das Melhorias

### ✅ Implementado

1. **Segurança**
   - ✅ Remoção de tokens hardcoded
   - ✅ Sistema de credenciais com variáveis de ambiente
   - ✅ Rate limiting com Redis
   - ✅ Logging estruturado

2. **Performance**
   - ✅ Cache Redis para contexto de conversas
   - ✅ Schema PostgreSQL otimizado com índices

3. **Funcionalidades**
   - ✅ 3 Workflows utilitários (Rate Limiter, Logger, Context Manager)
   - ✅ Workflow Master v2 completamente refatorado
   - ✅ Integração bidirecional com backend

4. **Infraestrutura**
   - ✅ Migration SQL completa
   - ✅ Template de variáveis de ambiente
   - ✅ Template de credenciais n8n

---

## 📦 Arquivos Criados

```
.
├── .env.n8n.example                    # Template de variáveis de ambiente
├── docker/
│   └── n8n-workflows/
│       ├── migrations/
│       │   └── n8n_improvements.sql    # Schema do banco
│       ├── n8n-credentials-template.json   # Template de credenciais
│       ├── 07-master-workflow-v2.json  # Workflow master refatorado
│       ├── 08-rate-limiter.json        # Workflow de rate limiting
│       ├── 09-logger.json              # Workflow de logging
│       └── 10-context-manager.json     # Workflow de contexto
└── backend/
    └── api/
        └── routes/
            └── n8n_webhooks.py         # Integração backend ↔ n8n
```

---

## 🔧 Instalação

### Passo 1: Configurar Variáveis de Ambiente

```bash
# Copiar template
cp .env.n8n.example .env.n8n

# Editar com seus valores
nano .env.n8n
```

**Valores obrigatórios:**
- `CHATWOOT_API_TOKEN` - Token da API do Chatwoot
- `OPENAI_API_KEY` - API Key da OpenAI (se usar IA)
- `N8N_DB_POSTGRESDB_PASSWORD` - Senha do PostgreSQL

### Passo 2: Aplicar Migration SQL

```bash
# Conectar ao PostgreSQL
docker exec -i tiktrend-postgres psql -U tiktrend -d tiktrend < docker/n8n-workflows/migrations/n8n_improvements.sql
```

**Verificar:**
```sql
-- Deve retornar 9 tabelas
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%workflow%' OR table_name LIKE '%conversation%';
```

### Passo 3: Configurar Credenciais no n8n

1. Acesse http://localhost:5678
2. Vá em **Settings → Credentials**
3. Crie as seguintes credenciais:

#### Chatwoot API
- Tipo: **HTTP Header Auth**
- Name: `Chatwoot API`
- Header Name: `api_access_token`
- Header Value: `{{$env.CHATWOOT_API_TOKEN}}`

#### PostgreSQL TikTrend
- Tipo: **Postgres**
- Name: `PostgreSQL TikTrend`
- Host: `tiktrend-postgres`
- Port: `5432`
- Database: `tiktrend`
- User: `tiktrend`
- Password: `{{$env.N8N_DB_POSTGRESDB_PASSWORD}}`

#### Redis TikTrend
- Tipo: **Redis**
- Name: `Redis TikTrend`
- Host: `{{$env.REDIS_HOST}}`
- Port: `6379`
- Password: `{{$env.REDIS_PASSWORD}}` (deixe vazio se não tiver)

#### OpenAI TikTrend
- Tipo: **OpenAI**
- Name: `OpenAI TikTrend`
- API Key: `{{$env.OPENAI_API_KEY}}`

### Passo 4: Importar Workflows

**Ordem de importação (importante!):**

```bash
# 1. Workflows utilitários (são dependências)
# Importe manualmente no n8n:
docker/n8n-workflows/08-rate-limiter.json
docker/n8n-workflows/09-logger.json
docker/n8n-workflows/10-context-manager.json

# 2. Workflow master
docker/n8n-workflows/07-master-workflow-v2.json
```

**No n8n:**
1. Workflows → Import from File
2. Selecione cada arquivo JSON
3. Após importar, **ative** cada workflow

### Passo 5: Atualizar Backend

```python
# Adicionar rota ao __init__.py
# backend/api/routes/__init__.py

from . import n8n_webhooks

__all__ = [
    # ... existing routes
    "n8n_webhooks",
]
```

```python
# Registrar no main.py
# backend/api/main.py

from api.routes import n8n_webhooks

app.include_router(n8n_webhooks.router, prefix="/api")
```

### Passo 6: Verificar Instalação

#### Testar Rate Limiter
```bash
curl -X POST http://localhost:5678/webhook/rate-limit-check \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "test-123"}'
  
# Resposta esperada:
# {"allowed": true, "current_count": 1, "limit": 10, "remaining": 9}
```

#### Testar Logger
```bash
curl -X POST http://localhost:5678/webhook/workflow-log \
  -H "Content-Type: application/json" \
  -d '{"workflow_name": "test", "success": true, "execution_time_ms": 100}'
  
# Verificar no banco:
psql -U tiktrend -d tiktrend -c "SELECT * FROM workflow_logs ORDER BY created_at DESC LIMIT 1;"
```

#### Testar Context Manager
```bash
curl -X POST http://localhost:5678/webhook/context-get \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "test-123"}'
```

#### Testar Backend Integration
```bash
curl -X GET http://localhost:8000/api/n8n/workflows \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔄 Migração do Workflow Antigo

### Substituir Workflow Master

1. **Desative** o workflow `07 - Workflow Master (Hub Central)` antigo
2. **Ative** o novo `07 - Workflow Master v2 (Improved)`
3. **Teste** enviando mensagem pelo WhatsApp

### Atualizar Outros Workflows (01-06)

Para cada workflow existente, você precisa:

1. **Remover token hardcoded**
   - Substituir `"api_access_token": "2nQ98Rj5MtwnMurVVfaoYN4t"`
   - Por autenticação com credencial `Chatwoot API`

2. **Adicionar logging**
   - Adicionar nó HTTP Request ao final
   - URL: `{{$env.N8N_WEBHOOK_URL}}/workflow-log`
   - Body: Dados da execução

**Exemplo de nó de logging:**
```json
{
  "method": "POST",
  "url": "={{$env.N8N_WEBHOOK_URL}}/workflow-log",
  "sendBody": true,
  "specifyBody": "json",
  "jsonBody": {
    "workflow_name": "01-basic-auto-reply",
    "execution_id": "={{$execution.id}}",
    "conversation_id": "={{$json.conversation_id}}",
    "success": true,
    "execution_time_ms": "={{$execution.duration}}"
  }
}
```

---

## 📊 Monitoramento

### Queries Úteis

**Métricas em tempo real (últimas 24h):**
```sql
SELECT * FROM v_realtime_metrics;
```

**Top intents da semana:**
```sql
SELECT * FROM v_top_intents;
```

**Taxa de sucesso por workflow:**
```sql
SELECT 
  workflow_name,
  COUNT(*) as total,
  SUM(CASE WHEN success THEN 1 ELSE 0 END) as sucessos,
  ROUND(100.0 * SUM(CASE WHEN success THEN 1 ELSE 0 END) / COUNT(*), 2) as taxa_sucesso
FROM workflow_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY workflow_name
ORDER BY total DESC;
```

**Uso da IA:**
```sql
SELECT * FROM v_ai_usage_summary LIMIT 7;
```

**Conversas bloqueadas por rate limit:**
```sql
SELECT 
  conversation_id,
  COUNT(*) as vezes_bloqueado,
  MAX(created_at) as ultimo_bloqueio
FROM rate_limits
WHERE blocked = true
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY conversation_id
ORDER BY vezes_bloqueado DESC
LIMIT 10;
```

### Limpeza Automática

Configurar cron job para rodar diariamente:

```sql
-- Limpa logs com +90 dias
SELECT cleanup_old_logs();
```

---

## 🐛 Troubleshooting

### Erro: "Cannot import name 'EmailClient'"
**Solução:** Arquivo `vendor/email/__init__.py` já possui alias `EmailClient = EmailMarketingService`

### Erro: "Redis connection refused"
**Solução:** Verificar se Redis está rodando:
```bash
docker ps | grep redis
docker logs tiktrend-redis
```

### Erro: "Chatwoot API 401 Unauthorized"
**Solução:** Verificar token no `.env.n8n`:
```bash
grep CHATWOOT_API_TOKEN .env.n8n
```

### Workflows não aparecem no n8n
**Solução:** Verificar se n8n está rodando e importar manualmente:
```bash
docker logs tiktrend-n8n
```

### Rate limit muito agressivo
**Solução:** Ajustar variáveis em `.env.n8n`:
```bash
RATE_LIMIT_MESSAGES_PER_MINUTE=20  # aumentar de 10 para 20
```

---

## 📈 Próximos Passos

### Fase 2: Performance (próxima sprint)
- [ ] Benchmark de performance
- [ ] Otimizar consultas SQL
- [ ] Implementar fallback hierarchy para IA
- [ ] Load testing com k6

### Fase 3: Escalabilidade
- [ ] Implementar RabbitMQ
- [ ] Refatorar para event-driven
- [ ] Auto-scaling de workflows

### Fase 4: Funcionalidades
- [ ] A/B testing framework
- [ ] Dashboard Grafana
- [ ] Personalização por perfil

---

## 📚 Documentação Adicional

- [Análise Completa](./n8n_improvements.md)
- [Plano de Implementação](./n8n_implementation_plan.md)
- [Task List](./n8n_task.md)

---

## ✅ ChecklistPós-Deploy

- [ ] Migration SQL aplicada
- [ ] Variáveis de ambiente configuradas
- [ ] Credenciais criadas no n8n
- [ ] 3 Workflows utilitários importados e ativos
- [ ] Workflow Master v2 importado e ativo
- [ ] Backend atualizado com n8n_webhooks.py
- [ ] Testes de rate limiting OK
- [ ] Testes de logging OK
- [ ] Testes de context OK
- [ ] Workflow antigo desativado
- [ ] Teste end-to-end com mensagem WhatsApp OK

---

**Versão:** 2.0.0  
**Data:** 2025-11-30  
**Autor:** TikTrend Finder Team
