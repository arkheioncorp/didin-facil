"""
Backend Integrations Package.

Contém integrações com serviços externos:
- marketplaces: Mercado Livre, Amazon, Shopee
- typebot: Chatbot builder integration
- n8n: Workflow automation
- whatsapp_hub: Central WhatsApp integration via Evolution API
"""

from .marketplaces import (
    MarketplaceManager,
    MarketplaceType,
    Product,
    SearchResult,
    get_marketplace_manager,
    search_all_marketplaces,
)
from .typebot import (
    TypebotClient,
    TypebotSession,
    TypebotWebhookHandler,
    get_typebot_client,
)
from .n8n import (
    N8nClient,
    WorkflowStatus,
    TriggerType,
    get_n8n_client,
)
from .whatsapp_hub import (
    WhatsAppHub,
    WhatsAppHubConfig,
    WhatsAppMessage,
    InstanceInfo,
    MessageType,
    ConnectionState,
    get_whatsapp_hub,
    send_whatsapp_message,
)

__all__ = [
    # Marketplaces
    "MarketplaceManager",
    "MarketplaceType",
    "Product",
    "SearchResult",
    "get_marketplace_manager",
    "search_all_marketplaces",
    # Typebot
    "TypebotClient",
    "TypebotSession",
    "TypebotWebhookHandler",
    "get_typebot_client",
    # n8n
    "N8nClient",
    "WorkflowStatus",
    "TriggerType",
    "get_n8n_client",
    # WhatsApp Hub
    "WhatsAppHub",
    "WhatsAppHubConfig",
    "WhatsAppMessage",
    "InstanceInfo",
    "MessageType",
    "ConnectionState",
    "get_whatsapp_hub",
    "send_whatsapp_message",
]
