# 📋 IMPLEMENTAÇÃO ATUAL - TikTrend Finder Marketing Suite

> **Status:** Estrutura completa implementada ✅
> **Última atualização:** 2025-01-XX

---

## 🏗️ Estrutura Implementada

```
backend/vendor/
├── __init__.py
├── requirements.txt                 # Dependências dos módulos vendor
├── social_media_manager.py          # 🔥 Manager unificado de redes sociais
│
├── whatsapp/
│   ├── __init__.py
│   └── client.py                    # 📱 Cliente Evolution API
│       ├── EvolutionAPIClient       # Classe principal
│       └── WhatsAppConfig           # Configuração
│
├── instagram/
│   ├── __init__.py
│   └── client.py                    # 📸 Cliente instagrapi wrapper
│       ├── InstagramClient          # Cliente assíncrono
│       └── InstagramConfig          # Configuração
│
├── tiktok/
│   ├── __init__.py
│   └── client.py                    # 🎵 Cliente Selenium-based
│       ├── TikTokClient             # Uploader
│       └── TikTokConfig             # Configuração
│
├── youtube/
│   ├── __init__.py
│   └── client.py                    # 🎬 Cliente YouTube API OAuth2
│       ├── YouTubeClient            # Upload + analytics
│       └── YouTubeConfig            # Configuração
│
├── content_generator/
│   ├── __init__.py
│   └── generator.py                 # 🎨 Gerador de conteúdo
│       ├── ContentGenerator         # Gera vídeos promocionais
│       └── Templates                # DEAL_ALERT, PRICE_COMPARISON, etc.
│
├── integrations/
│   ├── __init__.py
│   ├── typebot.py                   # 🤖 Cliente Typebot
│   │   ├── TypebotClient            # Chatbot integration
│   │   └── TypebotConfig            # Configuração
│   ├── n8n.py                       # ⚙️ Cliente n8n
│   │   ├── N8nClient                # Workflow automation
│   │   └── N8nConfig                # Configuração
│   └── chatwoot.py                  # 💬 Cliente Chatwoot
│       ├── ChatwootClient           # Suporte ao cliente
│       ├── ChatwootWebhookHandler   # Handler de webhooks
│       └── create_support_ticket()  # Helper
│
├── crm/
│   ├── __init__.py
│   └── leads.py                     # 📊 Gerenciamento de leads
│       ├── LeadManager              # Pipeline CRM
│       ├── Lead                     # Dataclass de lead
│       └── LeadSource/LeadStatus    # Enums
│
└── email/
    └── __init__.py                  # 📧 Email Marketing
        ├── EmailMarketingService    # Serviço unificado
        ├── EmailTemplateEngine      # Motor de templates
        ├── ResendClient             # Provider Resend
        └── SendGridClient           # Provider SendGrid

backend/api/routers/
├── social_media.py                  # 🌐 Endpoints Social Media
│   ├── POST /api/v1/social/post
│   ├── POST /api/v1/social/schedule
│   ├── GET  /api/v1/social/status/{platform}
│   └── POST /api/v1/social/connect/{platform}
│
├── crm.py                           # 📊 Endpoints CRM
│   ├── POST /api/v1/crm/leads
│   ├── GET  /api/v1/crm/leads
│   ├── GET  /api/v1/crm/leads/{id}
│   ├── PUT  /api/v1/crm/leads/{id}
│   ├── POST /api/v1/crm/leads/{id}/advance
│   ├── GET  /api/v1/crm/leads/stats
│   └── GET  /api/v1/crm/leads/export
│
├── integrations.py                  # ⚙️ Endpoints Integrações
│   ├── POST /api/v1/integrations/typebot/start
│   ├── POST /api/v1/integrations/typebot/message
│   ├── POST /api/v1/integrations/n8n/webhook
│   ├── POST /api/v1/integrations/n8n/execute
│   ├── GET  /api/v1/integrations/n8n/workflows
│   └── GET  /api/v1/integrations/status
│
├── support.py                       # 💬 Endpoints Suporte
│   ├── POST /api/v1/support/tickets
│   ├── GET  /api/v1/support/tickets
│   ├── GET  /api/v1/support/tickets/{id}
│   ├── PUT  /api/v1/support/tickets/{id}
│   ├── POST /api/v1/support/tickets/{id}/resolve
│   ├── POST /api/v1/support/tickets/{id}/messages
│   ├── GET  /api/v1/support/agents
│   ├── GET  /api/v1/support/reports/summary
│   └── POST /api/v1/support/webhook/chatwoot
│
└── email.py                         # 📧 Endpoints Email
    ├── POST /api/v1/email/send
    ├── POST /api/v1/email/campaign
    ├── POST /api/v1/email/price-alert
    ├── POST /api/v1/email/welcome
    ├── POST /api/v1/email/weekly-deals
    ├── GET  /api/v1/email/templates
    └── POST /api/v1/email/templates/preview
```

---

## 📖 Guia de Uso Rápido

### 1. WhatsApp (via Evolution API)

```python
from backend.vendor.whatsapp.client import EvolutionAPIClient

config = {
    "api_url": "http://localhost:8080",
    "api_key": "sua-api-key",
    "instance_name": "tiktrend-facil"
}

async with EvolutionAPIClient(**config) as client:
    # Conectar e obter QR Code
    qr = await client.get_qr_code()
    print(f"Escaneie: {qr['base64']}")
    
    # Enviar mensagens
    await client.send_text("5511999999999", "Olá!")
    await client.send_media("5511999999999", "https://...", "Confira!")
    
    # Lista interativa
    await client.send_interactive_list(
        to="5511999999999",
        title="Ofertas do Dia",
        sections=[{"title": "Eletrônicos", "rows": [...]}]
    )
```

### 2. Instagram (via instagrapi)

```python
from backend.vendor.instagram.client import InstagramClient

async with InstagramClient(username="user", password="pass") as client:
    # Upload de Reel
    await client.upload_reel(
        video_path="/path/to/video.mp4",
        caption="Confira as ofertas!",
        hashtags=["ofertas", "promoção"]
    )
    
    # Story com link
    await client.upload_story(
        media_path="/path/to/image.jpg",
        link="https://tiktrendfinder.com/ofertas"
    )
```

### 3. TikTok (via Selenium)

```python
from backend.vendor.tiktok.client import TikTokClient

# Primeiro: extrair cookies via login manual
await TikTokClient.extract_cookies_interactive("./cookies.json")

# Depois: usar para upload
async with TikTokClient(cookies_file="./cookies.json") as client:
    await client.upload_video(
        video_path="/path/to/video.mp4",
        caption="Oferta imperdível! #fyp"
    )
```

### 4. YouTube (via OAuth2)

```python
from backend.vendor.youtube.client import YouTubeClient

async with YouTubeClient(credentials_file="./credentials.json") as client:
    # Autenticar (abre navegador primeira vez)
    await client.authenticate()
    
    # Upload de vídeo
    result = await client.upload_video(
        video_path="/path/to/video.mp4",
        title="Ofertas da Semana",
        description="Confira as melhores ofertas!",
        tags=["ofertas", "economia"]
    )
    
    # Upload de Short
    await client.upload_short(
        video_path="/path/to/short.mp4",
        title="Oferta Relâmpago! #shorts"
    )
```

### 5. Chatwoot (Suporte ao Cliente)

```python
from backend.vendor.integrations.chatwoot import ChatwootClient, create_support_ticket

async with ChatwootClient() as client:
    # Criar ticket de suporte
    ticket = await create_support_ticket(
        client=client,
        inbox_id=1,
        customer_name="João Silva",
        customer_email="joao@email.com",
        subject="Problema com pedido",
        message="Meu pedido não chegou",
        priority="high",
        labels=["pedido", "urgente"]
    )
    
    # Responder
    await client.send_message(
        conversation_id=ticket.id,
        content="Olá! Vamos verificar seu pedido."
    )
    
    # Resolver
    await client.toggle_status(ticket.id, ConversationStatus.RESOLVED)
```

### 6. Email Marketing

```python
from backend.vendor.email import EmailMarketingService, EmailConfig

config = EmailConfig(
    provider="resend",  # ou "sendgrid"
    api_key="re_xxxxx",
    from_email="ofertas@tiktrendfinder.com"
)

async with EmailMarketingService(config) as service:
    # Email de boas-vindas
    await service.send_welcome(
        to="novo@email.com",
        name="João"
    )
    
    # Alerta de preço
    await service.send_price_alert(
        to="user@email.com",
        product_name="iPhone 15",
        old_price=9999.00,
        new_price=7999.00,
        product_url="https://...",
        product_image="https://...",
        store_name="Amazon"
    )
    
    # Campanha
    await service.send_campaign(
        recipients=[{"email": "a@x.com", "name": "A"}, ...],
        subject="Ofertas da Semana",
        template="weekly_deals",
        context={"deals": [...]}
    )
```

### 7. CRM / Leads

```python
from backend.vendor.crm.leads import LeadManager, LeadSource

manager = LeadManager()

# Adicionar lead
lead = await manager.add_lead(
    name="João Silva",
    email="joao@email.com",
    phone="+5511999999999",
    source=LeadSource.WHATSAPP,
    interest="iPhone 15 Pro"
)

# Lead scoring automático
score = await manager.score_lead(lead.id)
print(f"Score: {score}")  # 0-100

# Avançar no pipeline
await manager.advance_pipeline(lead.id)  # interested → negotiating → ...

# Estatísticas
stats = await manager.get_stats()
print(f"Total: {stats['total']}, Por status: {stats['by_status']}")
```

### 8. Typebot (Chatbots)

```python
from backend.vendor.integrations.typebot import TypebotClient

async with TypebotClient(api_url="https://...") as client:
    # Iniciar conversa
    session = await client.start_chat(
        typebot_id="my-bot",
        prefilted_variables={"user_name": "João"}
    )
    
    # Enviar resposta
    response = await client.send_message(
        session.session_id,
        "Quero ver ofertas"
    )
    
    print(f"Bot: {response.messages}")
```

### 9. n8n (Automação)

```python
from backend.vendor.integrations.n8n import N8nClient

async with N8nClient(api_url="https://...", api_key="...") as client:
    # Disparar webhook
    await client.trigger_webhook(
        "product-alert",
        {"product_id": 123, "new_price": 199.99}
    )
    
    # Executar workflow
    execution = await client.execute_workflow(
        workflow_id="abc123",
        data={"customer_email": "..."}
    )
```

---

## 🔧 Configuração de Ambiente

### Variáveis de Ambiente

```bash
# .env

# ==================== WhatsApp ====================
WHATSAPP_API_URL=http://localhost:8080
WHATSAPP_API_KEY=your-evolution-api-key
WHATSAPP_INSTANCE=tiktrend-facil

# ==================== Instagram ====================
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password

# ==================== TikTok ====================
TIKTOK_COOKIES_FILE=./sessions/tiktok_cookies.json

# ==================== YouTube ====================
YOUTUBE_CREDENTIALS_FILE=./credentials/youtube.json
YOUTUBE_TOKEN_FILE=./credentials/youtube_token.json

# ==================== Chatwoot ====================
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_API_TOKEN=your-token
CHATWOOT_ACCOUNT_ID=1

# ==================== Email ====================
EMAIL_PROVIDER=resend  # ou sendgrid
EMAIL_API_KEY=re_xxxxxx
EMAIL_FROM=ofertas@tiktrendfinder.com
EMAIL_FROM_NAME=TikTrend Finder

# ==================== Typebot ====================
TYPEBOT_API_URL=https://typebot.io
TYPEBOT_API_TOKEN=your-token

# ==================== n8n ====================
N8N_API_URL=https://n8n.example.com
N8N_API_KEY=your-api-key

# ==================== OpenAI ====================
OPENAI_API_KEY=sk-...
```

### Dependências

```bash
# Instalar dependências vendor
pip install -r backend/vendor/requirements.txt

# FFmpeg (para geração de vídeos)
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # Mac

# Chrome (para TikTok)
sudo apt install chromium-browser
```

---

## 📊 Referências

| Módulo | Repositório/Serviço | Licença |
|--------|---------------------|---------|
| WhatsApp | [EvolutionAPI/evolution-api](https://github.com/EvolutionAPI/evolution-api) | Apache 2.0 |
| Instagram | [subzeroid/instagrapi](https://github.com/subzeroid/instagrapi) | MIT |
| TikTok | [wkaisertexas/tiktok-uploader](https://github.com/wkaisertexas/tiktok-uploader) | MIT |
| YouTube | Google API | - |
| Chatwoot | [chatwoot/chatwoot](https://github.com/chatwoot/chatwoot) | MIT |
| Typebot | [baptisteArno/typebot.io](https://github.com/baptisteArno/typebot.io) | AGPL-3.0 |
| n8n | [n8n-io/n8n](https://github.com/n8n-io/n8n) | Sustainable Use |
| Email | Resend / SendGrid API | - |
