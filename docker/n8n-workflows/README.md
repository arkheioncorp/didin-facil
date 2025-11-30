# 🤖 Didin Fácil - Automações WhatsApp com n8n

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Workflows Disponíveis](#workflows-disponíveis)
4. [Configuração](#configuração)
5. [Personalização](#personalização)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

Este sistema integra **WhatsApp** via **Evolution API** com **Chatwoot** para atendimento e **n8n** para automações inteligentes.

### Stack Tecnológica

| Componente | Função | URL |
|-----------|--------|-----|
| **Evolution API** | Conexão WhatsApp | http://localhost:8082 |
| **Chatwoot** | Inbox compartilhado | http://localhost:3000 |
| **n8n** | Automações | http://localhost:5678 |
| **PostgreSQL** | Banco de dados | localhost:5434 |
| **Redis** | Cache | localhost:6379 |

### Fluxo de Dados

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐
│  WhatsApp   │────▶│ Evolution API │────▶│ Chatwoot │
└─────────────┘     └──────────────┘     └────┬─────┘
                                              │
                                              ▼
                    ┌──────────────┐     ┌──────────┐
                    │  PostgreSQL  │◀────│   n8n    │
                    └──────────────┘     └──────────┘
```

---

## 📦 Workflows Disponíveis

### 🟢 Nível Básico

#### 01 - Resposta Automática Básica
**Arquivo:** `01-basic-auto-reply.json`

**Funcionalidades:**
- ✅ Saudação automática (oi, olá, bom dia, etc.)
- ✅ Menu interativo com opções numeradas
- ✅ Respostas para opções 1-4
- ✅ Informações de horário de funcionamento

**Gatilhos:**
- Saudações: `oi`, `olá`, `bom dia`, `boa tarde`, `boa noite`
- Menu: números `1`, `2`, `3`, `4`

---

### 🟡 Nível Intermediário

#### 02 - FAQ Automático com Banco de Dados
**Arquivo:** `02-faq-database.json`

**Funcionalidades:**
- ✅ Busca inteligente no banco de FAQs
- ✅ Busca por similaridade (fuzzy matching)
- ✅ Registro de perguntas não respondidas
- ✅ Feedback de satisfação

**Requisitos:**
- Tabela `faqs` no PostgreSQL
- Extensão `pg_trgm` para busca por similaridade

---

#### 04 - Agendamento de Atendimento
**Arquivo:** `04-scheduling.json`

**Funcionalidades:**
- ✅ Integração com Google Calendar
- ✅ Exibe horários disponíveis
- ✅ Cria eventos automaticamente
- ✅ Confirmação por WhatsApp

**Requisitos:**
- Credenciais Google Calendar OAuth
- Tabela `appointments` no PostgreSQL

---

#### 05 - Busca de Produtos e Preços
**Arquivo:** `05-product-search.json`

**Funcionalidades:**
- ✅ Busca produtos na API Didin
- ✅ Exibe preços formatados
- ✅ Mostra economia e descontos
- ✅ Links para compra

**Gatilhos:**
- Palavras: `buscar`, `procurar`, `preço`, `quanto custa`

---

#### 06 - Notificação de Alertas de Preço
**Arquivo:** `06-price-alerts.json`

**Funcionalidades:**
- ✅ Verifica alertas a cada 6 horas
- ✅ Envia notificação quando preço baixa
- ✅ Marca alerta como notificado
- ✅ Registra log de envios

**Execução:** Automática (Schedule Trigger)

---

### 🔴 Nível Avançado

#### 03 - Chatbot com IA (OpenAI)
**Arquivo:** `03-ai-chatbot.json`

**Funcionalidades:**
- ✅ Respostas inteligentes com GPT-4
- ✅ Contexto personalizado para Didin Fácil
- ✅ Histórico de conversa
- ✅ Log de uso de tokens

**Requisitos:**
- API Key OpenAI
- Tabela `ai_conversations` no PostgreSQL

---

#### 07 - Workflow Master (Hub Central)
**Arquivo:** `07-master-workflow.json`

**Funcionalidades:**
- ✅ Roteador inteligente de intenções
- ✅ Estado de conversa persistente
- ✅ Fallback para IA quando não entende
- ✅ Integra todos os outros workflows

**Intenções detectadas:**
- Saudação → Menu de boas-vindas
- Menu → Opções disponíveis
- Busca → Prompt de pesquisa
- Humano → Transferência para atendente
- Agendamento → Opções de horário
- Outros → Resposta via IA

---

## ⚙️ Configuração

### 1. Executar Schema do Banco

```bash
docker exec -i tiktrend-postgres psql -U tiktrend -d tiktrend < n8n-workflows/database-schema.sql
```

### 2. Importar Workflows no n8n

1. Acesse http://localhost:5678
2. Vá em **Workflows** → **Import from File**
3. Importe cada arquivo `.json` da pasta `n8n-workflows/`

### 3. Configurar Credenciais no n8n

#### PostgreSQL
- **Host:** tiktrend-postgres
- **Port:** 5432
- **Database:** tiktrend
- **User:** tiktrend
- **Password:** (sua senha)

#### OpenAI (para workflow de IA)
- **API Key:** sua-api-key-openai

#### Google Calendar (para agendamentos)
- Configure OAuth 2.0 no Google Cloud Console

### 4. Ativar Workflows

Após importar e configurar, ative cada workflow clicando no toggle.

---

## 🎨 Personalização

### Alterar Mensagens

Edite o JSON do workflow, localizando os nós de `HTTP Request` e modificando o campo `jsonBody.content`.

### Adicionar Novas FAQs

```sql
INSERT INTO faqs (question, answer, category, keywords) VALUES
('Sua pergunta aqui?', 'Sua resposta aqui', 'categoria', 'palavras chave');
```

### Criar Novos Fluxos

1. Duplique o workflow mais próximo do desejado
2. Modifique os nós conforme necessidade
3. Teste com dados reais
4. Ative em produção

---

## 🔧 Troubleshooting

### Mensagens não chegam no n8n

1. Verifique se o webhook está ativo no Chatwoot
2. Confirme que os containers estão na mesma rede Docker
3. Teste o webhook manualmente:

```bash
curl -X POST http://localhost:5678/webhook/chatwoot \
  -H "Content-Type: application/json" \
  -d '{"event": "message_created", "message_type": "incoming", "content": "oi"}'
```

### Erro de conexão com PostgreSQL

1. Verifique as credenciais no n8n
2. Confirme que o container PostgreSQL está rodando
3. Teste a conexão:

```bash
docker exec -it tiktrend-postgres psql -U tiktrend -d tiktrend -c "SELECT 1"
```

### OpenAI retornando erro

1. Verifique se a API Key está válida
2. Confirme o limite de uso/créditos
3. Teste a API:

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer SUA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "teste"}]}'
```

---

## 📊 Métricas e Monitoramento

### Consultar métricas do chatbot

```sql
SELECT * FROM chatbot_metrics ORDER BY date DESC LIMIT 7;
```

### Ver perguntas não respondidas

```sql
SELECT * FROM unanswered_questions WHERE resolved = false ORDER BY created_at DESC;
```

### Uso de tokens da IA

```sql
SELECT 
  DATE(created_at) as data,
  COUNT(*) as conversas,
  SUM(tokens_used) as tokens_total
FROM ai_conversations
GROUP BY DATE(created_at)
ORDER BY data DESC;
```

---

## 📚 Recursos Adicionais

- [Documentação n8n](https://docs.n8n.io/)
- [Evolution API Docs](https://doc.evolution-api.com/)
- [Chatwoot API](https://www.chatwoot.com/developers/api/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

---

## 🆘 Suporte

Em caso de dúvidas ou problemas:

- 📧 Email: suporte@didin.com.br
- 💬 Slack: #automacoes
- 📖 Wiki: /docs/automacoes

---

**Versão:** 1.0.0  
**Última atualização:** 30 de novembro de 2025  
**Autor:** Equipe Didin Fácil
