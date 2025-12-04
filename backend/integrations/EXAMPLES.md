# 💡 Exemplos Práticos - Hubs de Integração

Este arquivo contém exemplos práticos de uso dos hubs centralizados.

---

## 📱 WhatsApp Hub

### Exemplo 1: Enviar Mensagem Simples

```python
from integrations import get_whatsapp_hub

async def send_welcome_message(phone_number: str):
    hub = get_whatsapp_hub()
    
    await hub.send_message(
        instance_name="tiktrend-whatsapp",
        to=phone_number,
        message="Bem-vindo ao TikTrend Finder! 🎉"
    )
```

### Exemplo 2: Criar Nova Instância e Obter QR Code

```python
from integrations import get_whatsapp_hub

async def setup_new_whatsapp_instance(instance_name: str):
    hub = get_whatsapp_hub()
    
    # Criar instância
    instance = await hub.create_instance(instance_name)
    print(f"✅ Instância criada: {instance.name}")
    
    # Obter QR Code
    qr_code = await hub.get_qr_code(instance_name)
    print(f"📱 QR Code: {qr_code}")
    
    return qr_code
```

### Exemplo 3: Processar Webhook do WhatsApp

```python
from fastapi import APIRouter, Request
from integrations import get_whatsapp_hub

router = APIRouter()

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    payload = await request.json()
    hub = get_whatsapp_hub()
    
    # Normalizar mensagem
    message = hub._normalize_webhook_message(payload)
    
    if message and not message.from_me:
        # Processar mensagem recebida
        print(f"📨 Nova mensagem de {message.from_number}: {message.content}")
        
        # Responder
        await hub.send_message(
            instance_name=message.instance,
            to=message.from_number,
            message=f"Recebi sua mensagem: {message.content}"
        )
    
    return {"status": "ok"}
```

### Exemplo 4: Usar com Seller Bot

```python
from integrations import get_whatsapp_hub
from modules.chatbot import WhatsAppHubAdapter, create_seller_bot

async def handle_whatsapp_conversation(webhook_payload: dict):
    # Setup
    hub = get_whatsapp_hub()
    adapter = WhatsAppHubAdapter(hub, "tiktrend-whatsapp")
    bot = await create_seller_bot()
    
    # Parse incoming
    incoming_msg = await adapter.parse_incoming(webhook_payload)
    
    if incoming_msg:
        # Process with bot
        response = await bot.process_message(incoming_msg, adapter)
        
        # Send response (adapter faz isso automaticamente)
        print(f"🤖 Bot respondeu: {response.content}")
```

---

## 📸 Instagram Hub

### Exemplo 1: Configurar e Enviar Mensagem

```python
from integrations import get_instagram_hub
import os

async def send_instagram_dm(recipient_id: str, message: str):
    hub = get_instagram_hub()
    
    # Configurar (apenas uma vez no startup)
    hub.configure(
        access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN"),
        page_id=os.getenv("INSTAGRAM_PAGE_ID"),
        app_secret=os.getenv("INSTAGRAM_APP_SECRET")
    )
    
    # Enviar mensagem
    result = await hub.send_message(recipient_id, message)
    return result
```

### Exemplo 2: Quick Replies

```python
from integrations import get_instagram_hub

async def send_product_options(recipient_id: str):
    hub = get_instagram_hub()
    
    await hub.send_quick_replies(
        recipient_id=recipient_id,
        text="Qual categoria você procura?",
        options=[
            "Eletrônicos 📱",
            "Moda 👗",
            "Casa 🏠",
            "Esportes ⚽",
            "Falar com atendente 💬"
        ]
    )
```

### Exemplo 3: Enviar Imagem com Caption

```python
from integrations import get_instagram_hub

async def send_product_image(recipient_id: str, product_url: str):
    hub = get_instagram_hub()
    
    await hub.send_media(
        recipient_id=recipient_id,
        media_url=product_url,
        media_type="image"
    )
```

### Exemplo 4: Processar Webhook do Instagram

```python
from fastapi import APIRouter, Request
from integrations import get_instagram_hub

router = APIRouter()

@router.post("/webhook/instagram")
async def instagram_webhook(request: Request):
    payload = await request.json()
    hub = get_instagram_hub()
    
    # Normalizar mensagem
    message = hub.normalize_webhook_event(payload)
    
    if message and not message.is_echo:
        print(f"📨 Nova mensagem Instagram de {message.sender_id}")
        
        # Enviar typing indicator
        await hub.send_typing(message.sender_id, duration_ms=2000)
        
        # Responder
        await hub.send_message(
            message.sender_id,
            "Obrigado pela mensagem! Em breve responderemos."
        )
    
    return {"status": "ok"}
```

### Exemplo 5: Usar com Seller Bot

```python
from integrations import get_instagram_hub
from modules.chatbot import InstagramHubAdapter, create_seller_bot

async def handle_instagram_conversation(webhook_payload: dict):
    # Setup
    hub = get_instagram_hub()
    hub.configure(
        access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN"),
        page_id=os.getenv("INSTAGRAM_PAGE_ID")
    )
    
    adapter = InstagramHubAdapter(hub)
    bot = await create_seller_bot()
    
    # Parse incoming
    incoming_msg = await adapter.parse_incoming(webhook_payload)
    
    if incoming_msg:
        # Process with bot
        response = await bot.process_message(incoming_msg, adapter)
        print(f"🤖 Bot Instagram respondeu: {response.content}")
```

---

## 🎵 TikTok Hub

### Exemplo 1: Salvar Sessão (Cookies)

```python
from integrations import get_tiktok_hub

async def save_tiktok_session(user_id: str, account_name: str, cookies: list):
    hub = get_tiktok_hub()
    
    session = await hub.save_session(
        user_id=user_id,
        account_name=account_name,
        cookies=cookies
    )
    
    print(f"✅ Sessão TikTok salva: {session.account_name}")
    return session
```

### Exemplo 2: Listar Sessões de um Usuário

```python
from integrations import get_tiktok_hub

async def list_user_tiktok_accounts(user_id: str):
    hub = get_tiktok_hub()
    
    sessions = await hub.list_sessions(user_id)
    
    for session in sessions:
        print(f"📱 Conta: {session.account_name}")
        print(f"   Ativa: {session.is_active}")
        print(f"   Expira: {session.expires_at}")
    
    return sessions
```

### Exemplo 3: Upload de Vídeo (Planejado)

```python
from integrations import get_tiktok_hub
from datetime import datetime, timedelta

async def schedule_tiktok_video(
    user_id: str,
    account: str,
    video_path: str,
    caption: str
):
    hub = get_tiktok_hub()
    
    # Agendar para 1 hora no futuro
    schedule_time = datetime.now() + timedelta(hours=1)
    
    result = await hub.upload_video(
        user_id=user_id,
        account_name=account,
        video_path=video_path,
        caption=caption,
        privacy="public",
        schedule_time=schedule_time
    )
    
    print(f"✅ Vídeo agendado: {result}")
    return result
```

---

## 🔄 Multi-Canal (Uso Combinado)

### Exemplo 1: Enviar Promoção em Todos os Canais

```python
from integrations import get_whatsapp_hub, get_instagram_hub

async def send_promotion_multi_channel(
    whatsapp_numbers: list,
    instagram_ids: list,
    promotion_text: str
):
    # WhatsApp
    whatsapp = get_whatsapp_hub()
    for phone in whatsapp_numbers:
        await whatsapp.send_message(
            instance_name="tiktrend-whatsapp",
            to=phone,
            message=f"🎉 PROMOÇÃO 🎉\n\n{promotion_text}"
        )
    
    # Instagram
    instagram = get_instagram_hub()
    for ig_id in instagram_ids:
        await instagram.send_message(
            recipient_id=ig_id,
            text=f"🎉 PROMOÇÃO 🎉\n\n{promotion_text}"
        )
    
    print(f"✅ Promoção enviada para {len(whatsapp_numbers)} WhatsApp + {len(instagram_ids)} Instagram")
```

### Exemplo 2: Seller Bot Multi-Canal

```python
from integrations import get_whatsapp_hub, get_instagram_hub
from modules.chatbot import (
    WhatsAppHubAdapter,
    InstagramHubAdapter,
    create_seller_bot,
    ChannelRouter,
    MessageChannel
)

async def setup_multi_channel_bot():
    # Criar bot
    bot = await create_seller_bot()
    
    # Setup WhatsApp
    whatsapp_hub = get_whatsapp_hub()
    whatsapp_adapter = WhatsAppHubAdapter(whatsapp_hub, "tiktrend-whatsapp")
    
    # Setup Instagram
    instagram_hub = get_instagram_hub()
    instagram_hub.configure(
        access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN"),
        page_id=os.getenv("INSTAGRAM_PAGE_ID")
    )
    instagram_adapter = InstagramHubAdapter(instagram_hub)
    
    # Router
    router = ChannelRouter()
    router.register_adapter(MessageChannel.WHATSAPP, whatsapp_adapter)
    router.register_adapter(MessageChannel.INSTAGRAM, instagram_adapter)
    
    return bot, router

# Uso em webhook
@app.post("/webhook/{channel}")
async def universal_webhook(channel: str, request: Request):
    bot, router = await setup_multi_channel_bot()
    payload = await request.json()
    
    # Detectar canal
    if channel == "whatsapp":
        channel_enum = MessageChannel.WHATSAPP
    elif channel == "instagram":
        channel_enum = MessageChannel.INSTAGRAM
    else:
        return {"error": "Canal não suportado"}
    
    # Processar
    incoming = await router.parse_incoming(channel_enum, payload)
    if incoming:
        response = await bot.process_message(incoming, router.get_adapter(channel_enum))
        print(f"🤖 Bot respondeu no {channel}: {response.content}")
    
    return {"status": "ok"}
```

---

## 🧪 Exemplos de Testes

### Teste 1: Mock do WhatsApp Hub

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_whatsapp_hub_send_message():
    with patch("integrations.whatsapp_hub.httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.post = AsyncMock(return_value=MagicMock(
            status_code=200,
            json=lambda: {"message_id": "msg-123"}
        ))
        
        from integrations import get_whatsapp_hub
        
        hub = get_whatsapp_hub()
        result = await hub.send_message(
            instance_name="test",
            to="5511999999999",
            message="Test"
        )
        
        assert "message_id" in result
        mock_client.post.assert_called_once()
```

### Teste 2: Mock do Instagram Hub

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_instagram_hub_send_quick_replies():
    with patch("integrations.instagram_hub.httpx.AsyncClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.post = AsyncMock(return_value=MagicMock(
            status_code=200,
            json=lambda: {"message_id": "ig-123"}
        ))
        
        from integrations import get_instagram_hub
        
        hub = get_instagram_hub()
        hub.configure(access_token="test", page_id="123")
        
        result = await hub.send_quick_replies(
            recipient_id="user123",
            text="Escolha:",
            options=["A", "B", "C"]
        )
        
        assert "message_id" in result
        
        # Verificar payload
        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]
        assert len(payload["message"]["quick_replies"]) == 3
```

### Teste 3: Integração End-to-End (Simulado)

```python
import pytest
from integrations import get_whatsapp_hub, get_instagram_hub

@pytest.mark.asyncio
async def test_multi_channel_broadcast():
    """Simula envio broadcast multi-canal."""
    
    whatsapp = get_whatsapp_hub()
    instagram = get_instagram_hub()
    
    # Mock manual (ou usar pytest-mock)
    whatsapp.send_message = AsyncMock(return_value={"status": "sent"})
    instagram.send_message = AsyncMock(return_value={"message_id": "123"})
    
    # Test
    message = "Teste broadcast"
    
    result_wa = await whatsapp.send_message("test", "5511999999999", message)
    result_ig = await instagram.send_message("user123", message)
    
    assert result_wa["status"] == "sent"
    assert "message_id" in result_ig
```

---

## 📋 Checklist de Implementação

Ao implementar um novo recurso usando os hubs:

### Preparação
- [ ] Identificar qual hub usar (WhatsApp, Instagram, TikTok)
- [ ] Verificar se credenciais estão configuradas (`.env`)
- [ ] Importar hub: `from integrations import get_*_hub`

### Desenvolvimento
- [ ] Obter singleton do hub: `hub = get_*_hub()`
- [ ] Configurar hub se necessário: `hub.configure(...)`
- [ ] Implementar lógica de negócio usando métodos do hub
- [ ] Adicionar tratamento de erros (try/except)

### Testes
- [ ] Criar teste unitário com mock do hub
- [ ] Testar casos de erro (credenciais inválidas, timeout, etc.)
- [ ] Testar integração E2E (se possível)

### Documentação
- [ ] Adicionar docstring explicando uso
- [ ] Atualizar este arquivo com exemplo se for caso comum
- [ ] Documentar variáveis de ambiente necessárias

---

**Última atualização:** 30 de novembro de 2025  
**Versão:** 1.0.0
