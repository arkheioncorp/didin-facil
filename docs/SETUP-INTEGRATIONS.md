# 🔧 Guia de Configuração de Integrações

Este guia mostra como obter as credenciais para cada integração.

## ✅ Já Configuradas (Funcionando)

| Integração | Status |
|------------|--------|
| PostgreSQL | ✅ Conectado |
| Redis | ✅ v7.4.7 |
| OpenAI | ✅ 102 modelos |
| Evolution API | ✅ WhatsApp |
| Mercado Livre | ✅ API pública |

---

## ⏳ Pendentes de Configuração

### 1. 💳 Mercado Pago (Pagamentos)

**Onde obter:**
1. Acesse: https://www.mercadopago.com.br/developers/panel
2. Crie uma aplicação ou selecione existente
3. Vá em **Credenciais de produção**
4. Copie `Access Token` e `Public Key`

**Variáveis no `.env`:**
```env
MERCADOPAGO_ACCESS_TOKEN=APP_USR-xxx
MERCADOPAGO_PUBLIC_KEY=APP_USR-xxx
```

---

### 2. 🎬 Google OAuth (YouTube)

**Onde obter:**
1. Acesse: https://console.cloud.google.com/apis/credentials
2. Crie ou selecione um projeto
3. Vá em **Criar credenciais** > **ID do cliente OAuth**
4. Tipo: **Aplicativo da Web**
5. Adicione URIs de redirecionamento:
   - `http://localhost:5173/callback/google`
   - `https://app.tiktrend.com.br/callback/google`
6. Copie **ID do cliente** e **Secret**

**Ativar APIs necessárias:**
- YouTube Data API v3
- Google+ API (para login)

**Variáveis no `.env`:**
```env
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
```

---

### 3. 🎵 TikTok OAuth

**Onde obter:**
1. Acesse: https://developers.tiktok.com/
2. Crie uma conta de desenvolvedor
3. Vá em **Manage apps** > **Create app**
4. Categoria: **Business** ou **Utility**
5. Em **App Info**, copie **Client Key** e **Client Secret**
6. Configure Redirect URI:
   - `http://localhost:5173/callback/tiktok`
   - `https://app.tiktrend.com.br/callback/tiktok`

**Variáveis no `.env`:**
```env
TIKTOK_CLIENT_KEY=xxx
TIKTOK_CLIENT_SECRET=xxx
```

---

### 4. 📸 Instagram/Facebook OAuth

**Onde obter:**
1. Acesse: https://developers.facebook.com/
2. Crie um app do tipo **Business**
3. Adicione o produto **Instagram Basic Display**
4. Em **Configurações** > **Básico**, copie **App ID** e **Secret**
5. Configure OAuth Redirect URIs:
   - `http://localhost:5173/callback/instagram`
   - `https://app.tiktrend.com.br/callback/instagram`

**Variáveis no `.env`:**
```env
INSTAGRAM_CLIENT_ID=xxx
INSTAGRAM_CLIENT_SECRET=xxx
```

---

### 5. 💬 Chatwoot (Suporte ao Cliente)

**Opção A: Usar Chatwoot Cloud (gratuito)**
1. Crie conta em: https://app.chatwoot.com/
2. Vá em **Settings** > **Profile** > **Access Token**
3. Copie o token
4. O Account ID está na URL: `/app/accounts/[ID]/...`

**Opção B: Self-hosted**
1. Deploy via Docker: https://www.chatwoot.com/docs/self-hosted

**Variáveis no `.env`:**
```env
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_ACCESS_TOKEN=xxx
CHATWOOT_ACCOUNT_ID=1
```

---

### 6. 🔄 n8n (Automação de Workflows)

**Onde obter:**
1. Instale n8n: https://n8n.io/
2. Via Docker: `docker run -it --rm -p 5678:5678 n8nio/n8n`
3. Ou use n8n Cloud: https://n8n.cloud/
4. Vá em **Settings** > **API** > **Create API Key**

**Variáveis no `.env`:**
```env
N8N_API_URL=http://localhost:5678
N8N_API_KEY=xxx
```

---

## 🏪 APIs de Marketplace (Opcional)

### Amazon PAAPI (Afiliados)

**Requisitos:**
- Conta Amazon Associates aprovada
- Ter feito pelo menos 3 vendas qualificadas

**Onde obter:**
1. Crie conta: https://affiliate-program.amazon.com.br/
2. Após aprovação, acesse: https://affiliate-program.amazon.com.br/assoc_credentials/home
3. Gere credenciais de API

**Variáveis no `.env`:**
```env
AMAZON_ACCESS_KEY=xxx
AMAZON_SECRET_KEY=xxx
AMAZON_PARTNER_TAG=seunome-20
```

### Mercado Livre (Opcional)

Para maior rate limit na API.

1. Acesse: https://developers.mercadolibre.com/
2. Crie aplicação
3. Copie App ID e Secret

**Variáveis no `.env`:**
```env
ML_CLIENT_ID=xxx
ML_CLIENT_SECRET=xxx
```

---

## ☁️ Storage (Cloudflare R2)

**Onde obter:**
1. Acesse: https://dash.cloudflare.com/
2. Vá em **R2 Object Storage**
3. Crie um bucket (ex: `tiktrend-images`)
4. Vá em **Manage R2 API Tokens**
5. Crie token com permissão **Admin Read & Write**

**Variáveis no `.env`:**
```env
CDN_URL=https://cdn.tiktrend.app
R2_BUCKET_NAME=tiktrend-images
R2_ENDPOINT=https://ACCOUNT_ID.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
```

---

## 📊 Monitoramento

### Sentry (Erros)

1. Crie conta: https://sentry.io/
2. Crie projeto Python/FastAPI
3. Copie o DSN

```env
SENTRY_DSN=https://xxx@sentry.io/xxx
```

### PostHog (Analytics)

1. Crie conta: https://posthog.com/
2. Crie projeto
3. Copie API Key

```env
POSTHOG_API_KEY=phc_xxx
```

---

## 🧪 Testar Integrações

Após configurar, execute:

```bash
cd backend
source venv/bin/activate
python -m scripts.test_integrations
```

Para testar uma integração específica:

```bash
python -m scripts.test_integrations --only google
python -m scripts.test_integrations --only mercadopago
```
