# 🔌 Integrations - Didin Fácil

## 📋 Índice de Documentação

Este diretório contém todos os **hubs centralizados de integração** com plataformas externas (WhatsApp, Instagram, TikTok, etc.).

### 📚 Documentos Disponíveis

| Documento | Descrição | Público-Alvo |
|-----------|-----------|--------------|
| **[HUBS_GUIDE.md](./HUBS_GUIDE.md)** | Guia completo de uso dos hubs | Desenvolvedores |
| **[ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md)** | Diagramas e fluxos da arquitetura | Arquitetos / Tech Leads |
| **[EXAMPLES.md](./EXAMPLES.md)** | Exemplos práticos de código | Desenvolvedores |
| **[CONSOLIDATION_SUMMARY.md](./CONSOLIDATION_SUMMARY.md)** | Resumo da consolidação | Gestores / Product Owners |

---

## 🏗️ Arquitetura de Hubs

### Princípio de Design
**1 Hub = 1 Plataforma = 1 Ponto de Integração**

```
Application Layer (Routes, Bot, Workers)
            ↓
     Adapter Layer (Opcional)
            ↓
   ★ HUBS CENTRALIZADOS ★
    ┌─────────────────┐
    │  WhatsApp Hub   │
    │  Instagram Hub  │
    │  TikTok Hub     │
    └─────────────────┘
            ↓
    External APIs
```

---

## 🚀 Quick Start

### WhatsApp

```python
from integrations import get_whatsapp_hub

hub = get_whatsapp_hub()
await hub.send_message(
    instance_name="didin-whatsapp",
    to="5511999999999",
    message="Olá!"
)
```

[📖 Ver mais exemplos WhatsApp](./EXAMPLES.md#-whatsapp-hub)

---

### Instagram

```python
from integrations import get_instagram_hub

hub = get_instagram_hub()
hub.configure(access_token="...", page_id="...")
await hub.send_message(recipient_id="123", text="Oi!")
```

[📖 Ver mais exemplos Instagram](./EXAMPLES.md#-instagram-hub)

---

### TikTok

```python
from integrations import get_tiktok_hub

hub = get_tiktok_hub()
session = await hub.save_session(user_id="...", account_name="...", cookies=[...])
```

[📖 Ver mais exemplos TikTok](./EXAMPLES.md#-tiktok-hub)

---

## 📦 Estrutura de Arquivos

```
backend/integrations/
├── README.md                    # ← Você está aqui
├── HUBS_GUIDE.md               # Guia completo
├── ARCHITECTURE_DIAGRAM.md      # Diagramas
├── EXAMPLES.md                  # Exemplos práticos
├── CONSOLIDATION_SUMMARY.md     # Resumo da consolidação
│
├── __init__.py                  # Exports dos hubs
├── whatsapp_hub.py             # ★ WhatsApp Hub
├── instagram_hub.py            # ★ Instagram Hub
├── tiktok_hub.py               # ★ TikTok Hub
│
├── n8n.py                       # Integração n8n
├── typebot.py                   # Integração Typebot
└── marketplaces.py              # Mercado Livre, etc.
```

---

## 🎯 Hubs Disponíveis

### ✅ WhatsApp Hub
- **Status:** ✅ Produção
- **API Externa:** Evolution API
- **Funcionalidades:** Mensagens, QR Code, Webhooks, Chatwoot
- **Documentação:** [whatsapp_hub.py](./whatsapp_hub.py)

### ✅ Instagram Hub
- **Status:** ✅ Produção
- **API Externa:** Facebook Graph API
- **Funcionalidades:** DMs, Quick Replies, Mídia, Typing
- **Documentação:** [instagram_hub.py](./instagram_hub.py)

### ⚠️ TikTok Hub
- **Status:** ⚠️ Parcial (apenas sessões)
- **API Externa:** TikTok Private/Web
- **Funcionalidades:** Sessões, Upload (planejado)
- **Nota:** Mensagens não suportadas oficialmente
- **Documentação:** [tiktok_hub.py](./tiktok_hub.py)

---

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# .env

# WhatsApp (Evolution API)
EVOLUTION_API_URL=http://evolution-api:8082
EVOLUTION_API_KEY=sua-chave-secreta
EVOLUTION_DEFAULT_INSTANCE=didin-whatsapp

# Instagram (Graph API)
INSTAGRAM_ACCESS_TOKEN=seu-token-de-acesso
INSTAGRAM_PAGE_ID=seu-page-id
INSTAGRAM_APP_SECRET=seu-app-secret

# TikTok
TIKTOK_HEADLESS=true
TIKTOK_UPLOAD_TIMEOUT=300
```

### Setup no Startup

```python
from fastapi import FastAPI
from integrations import get_instagram_hub, get_whatsapp_hub
from shared.config import settings

app = FastAPI()

@app.on_event("startup")
async def configure_hubs():
    # Instagram
    instagram = get_instagram_hub()
    instagram.configure(
        access_token=settings.INSTAGRAM_ACCESS_TOKEN,
        page_id=settings.INSTAGRAM_PAGE_ID,
        app_secret=settings.INSTAGRAM_APP_SECRET
    )
    
    # WhatsApp já vem configurado via env vars
    # TikTok não precisa configuração inicial
    
    print("✅ Hubs configurados!")
```

---

## 🧪 Testes

### Teste Manual Rápido

```bash
cd backend
python3 -c "
from integrations import get_whatsapp_hub, get_instagram_hub, get_tiktok_hub

print('✅ WhatsApp Hub:', get_whatsapp_hub())
print('✅ Instagram Hub:', get_instagram_hub())
print('✅ TikTok Hub:', get_tiktok_hub())
print('🎉 Todos os hubs OK!')
"
```

### Testes Automatizados

```bash
# Testes unitários
pytest tests/integrations/test_whatsapp_hub.py
pytest tests/integrations/test_instagram_hub.py
pytest tests/integrations/test_tiktok_hub.py

# Coverage
pytest --cov=integrations tests/integrations/
```

---

## 📖 Documentação Completa

### Para Desenvolvedores
1. **Começar aqui:** [EXAMPLES.md](./EXAMPLES.md) - Exemplos práticos
2. **Referência completa:** [HUBS_GUIDE.md](./HUBS_GUIDE.md)
3. **Código fonte:** Veja os arquivos `*_hub.py`

### Para Arquitetos
1. **Visão arquitetural:** [ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md)
2. **Padrões de design:** Singleton, Adapter, Factory
3. **Fluxos de dados:** Diagramas de sequência

### Para Gestores
1. **Resumo executivo:** [CONSOLIDATION_SUMMARY.md](./CONSOLIDATION_SUMMARY.md)
2. **Benefícios:** Redução de duplicação, manutenibilidade
3. **ROI:** Menos tempo de manutenção, mais features

---

## 🚀 Roadmap

### ✅ Concluído (v2.0.0)
- ✅ WhatsApp Hub centralizado
- ✅ Instagram Hub centralizado
- ✅ TikTok Hub (sessões)
- ✅ Adapters para Seller Bot
- ✅ Documentação completa

### 🔄 Em Progresso
- 🔄 TikTok Hub (upload de vídeos)
- 🔄 Rate limiting centralizado
- 🔄 Circuit breaker pattern
- 🔄 Métricas Prometheus

### 📋 Planejado (v2.1.0)
- 📋 Facebook Hub
- 📋 Twitter/X Hub
- 📋 Telegram Hub
- 📋 WebSocket support
- 📋 Health checks dashboard

---

## 🆘 Suporte

### Dúvidas Técnicas
- **Slack:** #backend-integrations
- **Email:** backend@didinfacil.com
- **Issues:** [GitHub Issues](https://github.com/arkheioncorp/didin-facil/issues)

### Reportar Bugs
1. Verificar se já existe issue aberta
2. Criar nova issue com label `bug` e `integrations`
3. Incluir logs, stack trace e steps to reproduce

### Solicitar Features
1. Criar issue com label `enhancement` e `integrations`
2. Descrever caso de uso
3. Sugerir solução (opcional)

---

## 🤝 Contribuindo

### Adicionar Novo Hub

1. **Criar arquivo:** `backend/integrations/{plataforma}_hub.py`
2. **Implementar padrão:**
   ```python
   class {Plataforma}Hub:
       """Hub central para {Plataforma}."""
       def __init__(self, config: Optional[{Plataforma}HubConfig] = None):
           ...
   
   _hub: Optional[{Plataforma}Hub] = None
   
   def get_{plataforma}_hub() -> {Plataforma}Hub:
       """Retorna singleton."""
       global _hub
       if _hub is None:
           _hub = {Plataforma}Hub()
       return _hub
   ```

3. **Exportar:** Adicionar em `__init__.py`
4. **Documentar:** Atualizar este README e criar exemplos
5. **Testar:** Adicionar testes unitários
6. **PR:** Criar pull request com descrição detalhada

---

## 📜 Changelog

### v2.0.0 (30 de novembro de 2025)
- ✨ Consolidação completa dos hubs
- ✨ Adaptadores para Seller Bot
- ✨ Documentação abrangente
- 🔧 Refatoração de código legado
- 🧪 Testes de integração

### v1.0.0 (Anterior)
- ✅ Implementação inicial dos hubs
- ✅ Integração básica com plataformas

---

## 📄 Licença

Propriedade de **Didin Fácil** © 2025. Todos os direitos reservados.

---

**Última atualização:** 30 de novembro de 2025  
**Versão:** 2.0.0  
**Mantenedores:** Time de Backend
