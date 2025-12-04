# Guia de Integração Completa - TikTrend Finder

Este documento consolida todas as integrações disponíveis no sistema.

## 📋 Sumário

- [Quick Start](#quick-start)
- [Integrações Disponíveis](#integrações-disponíveis)
- [WhatsApp (Evolution API)](#whatsapp-evolution-api)
- [YouTube](#youtube)
- [Instagram](#instagram)
- [TikTok](#tiktok)
- [CRM & Analytics](#crm--analytics)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Iniciar Serviços

```bash
# Dar permissão de execução aos scripts
chmod +x scripts/setup-integrations.sh
chmod +x scripts/test-uploads.sh

# Executar setup completo
./scripts/setup-integrations.sh
```

### 2. Testar Integrações

```bash
# Testar todas as integrações
./scripts/test-uploads.sh
```

### 3. Configurar Variáveis

Edite `backend/.env` com suas credenciais.

---

## Integrações Disponíveis

| Plataforma | Status | Funcionalidades |
|------------|--------|-----------------|
| WhatsApp | ✅ Pronto | Mensagens, Instâncias, QR Code |
| YouTube | ✅ Pronto | Upload, Quota, OAuth |
| Instagram | ✅ Pronto | Posts, Reels, Stories |
| TikTok | ✅ Pronto | Upload, Sessões |
| CRM | ✅ Pronto | Leads, Pipeline, Atividades |
| Analytics | ✅ Pronto | Métricas, Dashboards |

---

## WhatsApp (Evolution API)

### Configuração

A Evolution API já está configurada no Docker Compose:

```yaml
# docker/docker-compose.yml
evolution-api:
  image: atendai/evolution-api:v1.8.7
  ports:
    - "8082:8080"
  environment:
    - AUTHENTICATION_API_KEY=429683C4C977415CAAFCCE10F7D57E11
```

### Variáveis de Ambiente

```env
EVOLUTION_API_URL=http://localhost:8082
EVOLUTION_API_KEY=429683C4C977415CAAFCCE10F7D57E11
```

### Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/whatsapp/instances` | GET | Lista instâncias |
| `/whatsapp/instances` | POST | Cria instância |
| `/whatsapp/instances/{id}/qr` | GET | QR Code para conectar |
| `/whatsapp/instances/{id}/status` | GET | Status da conexão |
| `/whatsapp/send` | POST | Envia mensagem |
| `/whatsapp/webhook` | POST | Recebe eventos |

### Uso no Frontend

```typescript
// Configurações > Integrações > WhatsApp
// 1. Clique em "Adicionar Instância"
// 2. Escaneie o QR Code com WhatsApp
// 3. Aguarde status "Conectado"
```

---

## YouTube

### Configuração OAuth

Siga o guia completo em: **`docs/YOUTUBE-SETUP.md`**

Resumo:
1. Criar projeto no Google Cloud Console
2. Ativar YouTube Data API v3
3. Configurar tela de consentimento OAuth
4. Criar credenciais OAuth (Desktop)
5. Baixar JSON de credenciais
6. Autenticar no app

### Variáveis de Ambiente

```env
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
```

### Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/youtube/auth` | GET | Inicia OAuth |
| `/youtube/callback` | GET | Callback OAuth |
| `/youtube/accounts` | GET | Lista contas |
| `/youtube/upload` | POST | Upload de vídeo |
| `/youtube/quota` | GET | Quota restante |

### Quota

- **Limite diário:** 10.000 unidades
- **Upload:** ~1.600 unidades
- **~6 uploads/dia** máximo

---

## Instagram

### Configuração

O Instagram usa a biblioteca `instagrapi` para automação.

### Variáveis de Ambiente

```env
INSTAGRAM_USERNAME=sua_conta
INSTAGRAM_PASSWORD=sua_senha
```

### Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/instagram/login` | POST | Faz login |
| `/instagram/sessions` | GET | Lista sessões |
| `/instagram/challenge/resolve` | POST | Resolve desafio 2FA |
| `/instagram/upload` | POST | Upload de mídia |

### Tipos de Mídia

- **Foto:** JPEG, PNG (até 10MB)
- **Reels:** MP4 (até 100MB, 60s)
- **Stories:** Imagem ou vídeo (15s)

---

## TikTok

### Configuração

O TikTok usa Selenium para automação via browser.

### Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/tiktok/sessions` | GET | Lista sessões |
| `/tiktok/sessions` | POST | Cria sessão |
| `/tiktok/upload` | POST | Upload de vídeo |
| `/tiktok/search` | GET | Busca hashtags |

### Requisitos

- Chrome/Chromium instalado
- ChromeDriver compatível
- Sessão de cookies do TikTok

---

## CRM & Analytics

### CRM - Gerenciamento de Leads

#### Funcionalidades
- ✅ CRUD de Leads
- ✅ Pipeline Kanban
- ✅ Scoring automático
- ✅ Histórico de atividades
- ✅ Tags e segmentação
- ✅ Atribuição a vendedores

#### Endpoints CRM

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/crm/leads` | GET | Lista leads |
| `/api/v1/crm/leads` | POST | Cria lead |
| `/api/v1/crm/leads/{id}` | PUT | Atualiza lead |
| `/api/v1/crm/leads/{id}` | DELETE | Remove lead |
| `/api/v1/crm/leads/{id}/activities` | POST | Registra atividade |
| `/api/v1/crm/pipeline/stages` | GET | Estágios do pipeline |

### Analytics - Métricas

#### Funcionalidades
- ✅ Overview do Dashboard
- ✅ Métricas por plataforma
- ✅ Gráficos temporais
- ✅ Top conteúdos
- ✅ Taxa de engajamento
- ✅ Crescimento de seguidores

#### Endpoints Analytics

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/analytics/overview` | GET | Overview geral |
| `/analytics/social/overview` | GET | Social analytics |
| `/analytics/platform/{platform}` | GET | Por plataforma |
| `/analytics/top-content` | GET | Melhores posts |

### Navegação

No app:
- **CRM:** Menu lateral > CRM & Vendas
- **Analytics:** Menu lateral > Administração > Analytics

---

## Troubleshooting

### Evolution API não conecta

```bash
# Verificar se está rodando
docker ps | grep evolution

# Ver logs
docker logs evolution-api -f

# Reiniciar
docker restart evolution-api
```

### YouTube "Access blocked"

1. Adicione seu email como usuário de teste no Google Cloud
2. Durante login, clique "Avançado" > "Acessar (não seguro)"

### Instagram challenge

Se aparecer desafio de verificação:
1. Verifique email/SMS associado à conta
2. Use endpoint `/instagram/challenge/resolve`
3. Envie código de verificação

### TikTok sessão expirada

1. Faça login novamente no browser
2. Exporte cookies para JSON
3. Atualize sessão no app

### API retorna 500

```bash
# Ver logs da API
cd docker && docker logs tiktrend-api -f

# Verificar banco
docker exec -it tiktrend-postgres psql -U tiktrend -d tiktrend
```

### Redis não conecta

```bash
# Verificar Redis
docker exec -it tiktrend-redis redis-cli ping
# Deve retornar: PONG
```

---

## Arquivos de Configuração

| Arquivo | Descrição |
|---------|-----------|
| `backend/.env` | Variáveis de ambiente |
| `docker/docker-compose.yml` | Configuração Docker |
| `docs/YOUTUBE-SETUP.md` | Setup YouTube OAuth |
| `scripts/setup-integrations.sh` | Script de setup |
| `scripts/test-uploads.sh` | Script de testes |

---

## Suporte

- **Documentação:** `/docs/`
- **API Docs:** `http://localhost:8000/docs`
- **Logs:** `docker logs <container> -f`

---

**Última atualização:** Novembro 2025
**Versão:** 1.0.0
