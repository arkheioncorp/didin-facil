# Guia de Hubs Centralizados - TikTrend Finder

## 📋 Visão Geral

Este guia documenta a arquitetura centralizada de integração com redes sociais e plataformas de mensagens do TikTrend Finder.

## 🏗️ Arquitetura

### Princípio de Design

Cada plataforma possui **um único Hub** que centraliza todas as operações:

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│  (Routes, Bot, Workers)                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Channel Adapters (Optional)        │
│  WhatsAppHubAdapter                     │
│  InstagramHubAdapter                    │
│  TikTokHubAdapter                       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Centralized Hubs                │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ WhatsApp │ │Instagram │ │ TikTok  │ │
│  │   Hub    │ │   Hub    │ │   Hub   │ │
│  └──────────┘ └──────────┘ └─────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         External APIs                   │
│  Evolution API / Graph API / TikTok API │
└─────────────────────────────────────────┘
```

## 🔌 Hubs Disponíveis

### 1. WhatsApp Hub

**Localização:** `backend/integrations/whatsapp_hub.py`

**Responsabilidades:**
- Gerenciamento de instâncias Evolution API
- Envio/recebimento de mensagens
- Webhooks
- Integração com Chatwoot
- QR Code para conexão

**Uso Básico:**

```python
from integrations.whatsapp_hub import get_whatsapp_hub

hub = get_whatsapp_hub()

# Enviar mensagem
await hub.send_message(
    instance_name="tiktrend-whatsapp",
    to="5511999999999",
    message="Olá!"
)

# Criar instância
instance = await hub.create_instance("nova-instancia")

# Obter QR Code
qr_code = await hub.get_qr_code("tiktrend-whatsapp")
```

**Configuração:**

```python
from integrations.whatsapp_hub import WhatsAppHubConfig

config = WhatsAppHubConfig(
    evolution_api_url="http://localhost:8082",
    evolution_api_key="seu-api-key",
    default_instance="tiktrend-whatsapp"
)
```

---

### 2. Instagram Hub

**Localização:** `backend/integrations/instagram_hub.py`

**Responsabilidades:**
- Envio de mensagens diretas (DM)
- Quick Replies
- Mídia (imagens, vídeos)
- Webhooks do Messenger API
- Typing indicators

**Uso Básico:**

```python
from integrations.instagram_hub import get_instagram_hub

hub = get_instagram_hub()

# Configurar credenciais
hub.configure(
    access_token="seu-access-token",
    page_id="seu-page-id",
    app_secret="seu-app-secret"
)

# Enviar mensagem
await hub.send_message(recipient_id="123456", text="Oi!")

# Quick Replies
await hub.send_quick_replies(
    recipient_id="123456",
    text="Escolha uma opção:",
    options=["Produto A", "Produto B", "Falar com atendente"]
)

# Enviar mídia
await hub.send_media(
    recipient_id="123456",
    media_url="https://exemplo.com/imagem.jpg",
    media_type="image"
)
```

**Configuração:**

```python
from integrations.instagram_hub import InstagramHubConfig

config = InstagramHubConfig(
    access_token="token",
    page_id="page-id",
    app_secret="secret",
    graph_version="v18.0"
)
```

---

### 3. TikTok Hub

**Localização:** `backend/integrations/tiktok_hub.py`

**Responsabilidades:**
- Gerenciamento de sessões (cookies)
- Upload de vídeos
- Analytics (futuro)
- **Nota:** Mensagens diretas ainda não suportadas oficialmente

**Uso Básico:**

```python
from integrations.tiktok_hub import get_tiktok_hub

hub = get_tiktok_hub()

# Salvar sessão (cookies)
await hub.save_session(
    user_id="user123",
    account_name="minha_conta_tiktok",
    cookies=[...]
)

# Upload de vídeo (futuro - requer implementação completa)
result = await hub.upload_video(
    user_id="user123",
    account_name="minha_conta_tiktok",
    video_path="/path/to/video.mp4",
    caption="Meu vídeo incrível! #tiktok",
    privacy="public"
)
```

**Configuração:**

```python
from integrations.tiktok_hub import TikTokHubConfig

config = TikTokHubConfig(
    headless=True,
    upload_timeout=300
)
```

---

## 🎯 Adaptadores para Seller Bot

Se você está integrando com o **Seller Bot**, use os adaptadores específicos:

### WhatsApp

```python
from modules.chatbot import WhatsAppHubAdapter
from integrations.whatsapp_hub import get_whatsapp_hub

hub = get_whatsapp_hub()
adapter = WhatsAppHubAdapter(hub, instance_name="tiktrend-whatsapp")

# O adapter implementa a interface ChannelAdapter
incoming_msg = await adapter.parse_incoming(webhook_payload)
await adapter.send_response(bot_response, recipient_id)
```

### Instagram

```python
from modules.chatbot import InstagramHubAdapter
from integrations.instagram_hub import get_instagram_hub

hub = get_instagram_hub()
hub.configure(access_token="...", page_id="...")

adapter = InstagramHubAdapter(hub)
incoming_msg = await adapter.parse_incoming(webhook_payload)
await adapter.send_response(bot_response, recipient_id)
```

### TikTok

```python
from modules.chatbot import TikTokHubAdapter
from integrations.tiktok_hub import get_tiktok_hub

hub = get_tiktok_hub()
adapter = TikTokHubAdapter(hub)

# Nota: TikTok não possui API oficial de mensagens
# Métodos retornarão NotImplementedError
```

---

## 🔄 Migração de Código Legado

### Antes (Código Antigo)

```python
# ❌ Múltiplos pontos de integração espalhados
from modules.chatbot import EvolutionAdapter, InstagramAdapter

evolution = EvolutionAdapter(config)
instagram = InstagramAdapter(config)
```

### Depois (Código Novo)

```python
# ✅ Hub centralizado + Adapter
from integrations import get_whatsapp_hub, get_instagram_hub
from modules.chatbot import WhatsAppHubAdapter, InstagramHubAdapter

whatsapp_hub = get_whatsapp_hub()
whatsapp_adapter = WhatsAppHubAdapter(whatsapp_hub, "tiktrend-whatsapp")

instagram_hub = get_instagram_hub()
instagram_hub.configure(access_token="...", page_id="...")
instagram_adapter = InstagramHubAdapter(instagram_hub)
```

**Nota:** As classes antigas (`EvolutionAdapter`, `InstagramAdapter`, `TikTokAdapter`) ainda funcionam, mas agora são **wrappers** dos novos hubs. Prefira usar os `HubAdapters` diretamente.

---

## 📦 Estrutura de Arquivos

```
backend/
├── integrations/           # HUBS CENTRALIZADOS
│   ├── __init__.py        # Exporta todos os hubs
│   ├── whatsapp_hub.py    # Hub WhatsApp
│   ├── instagram_hub.py   # Hub Instagram
│   └── tiktok_hub.py      # Hub TikTok
│
└── modules/
    └── chatbot/           # ADAPTADORES PARA SELLER BOT
        ├── __init__.py
        ├── whatsapp_adapter.py    # Adapter WhatsApp
        ├── instagram_adapter.py   # Adapter Instagram
        ├── tiktok_adapter.py      # Adapter TikTok
        └── channel_integrations.py # Classes legadas (wrappers)
```

---

## 🚀 Boas Práticas

### 1. Use Singletons

Os hubs são singletons. Sempre use as funções `get_*_hub()`:

```python
# ✅ Correto
hub = get_whatsapp_hub()

# ❌ Evite
hub = WhatsAppHub()  # Cria nova instância em vez de reutilizar
```

### 2. Configure Uma Vez

Configure o hub na inicialização da aplicação ou no primeiro uso:

```python
# No startup da API
@app.on_event("startup")
async def configure_hubs():
    instagram = get_instagram_hub()
    instagram.configure(
        access_token=settings.INSTAGRAM_TOKEN,
        page_id=settings.INSTAGRAM_PAGE_ID
    )
```

### 3. Use Variáveis de Ambiente

```python
# .env
EVOLUTION_API_URL=http://evolution-api:8082
EVOLUTION_API_KEY=sua-chave
INSTAGRAM_ACCESS_TOKEN=seu-token
INSTAGRAM_PAGE_ID=seu-page-id
TIKTOK_HEADLESS=true
```

### 4. Tratamento de Erros

```python
try:
    await hub.send_message(instance_name="...", to="...", message="...")
except ValueError as e:
    # Configuração inválida
    logger.error(f"Hub mal configurado: {e}")
except httpx.HTTPStatusError as e:
    # Erro na API externa
    logger.error(f"Erro HTTP: {e.response.status_code}")
except Exception as e:
    # Erro genérico
    logger.error(f"Erro inesperado: {e}")
```

---

## 🧪 Testes

Exemplo de teste unitário com mocks:

```python
from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
async def test_whatsapp_hub_send_message():
    with patch("integrations.whatsapp_hub.httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.post = AsyncMock(return_value=MagicMock(
            status_code=200,
            json=lambda: {"message_id": "123"}
        ))
        
        hub = get_whatsapp_hub()
        result = await hub.send_message("test", "5511999999999", "Oi")
        
        assert result["message_id"] == "123"
        mock_client.post.assert_called_once()
```

---

## 📞 Suporte e Contribuição

- **Documentação Completa:** `/docs/ARCHITECTURE.md`
- **Issues:** GitHub Issues
- **Slack:** Canal #backend-integrations

---

**Última atualização:** 30 de novembro de 2025  
**Versão:** 2.0.0
