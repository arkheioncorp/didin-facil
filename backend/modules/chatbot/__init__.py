"""
Chatbot Module
==============
Módulo de chatbot profissional com IA e integrações multi-canal.

Features:
- Professional Seller Bot com análise de intenção
- Integração multi-canal (WhatsApp, Instagram, Chatwoot)
- CRM integration
- Analytics tracking
- AI-powered responses
"""

from .professional_seller_bot import (
    # Main Bot
    ProfessionalSellerBot,
    create_seller_bot,
    
    # Models
    IncomingMessage,
    BotResponse,
    ConversationContext,
    IntentAnalysis,
    
    # Enums
    MessageChannel,
    ConversationStage,
    Intent,
    SentimentType,
    LeadTemperature,
    
    # Components
    IntentDetector,
    ResponseTemplates,
)

from .channel_integrations import (
    # Adapters
    ChannelAdapter,
    EvolutionAdapter,
    ChatwootAdapter,
    InstagramAdapter,
    TikTokAdapter,
    
    # Router
    ChannelRouter,
    
    # Configs
    EvolutionConfig,
    ChatwootConfig,
    InstagramConfig,
    TikTokConfig,
    
    # Factory functions
    create_evolution_adapter,
    create_chatwoot_adapter,
    create_instagram_adapter,
)

# Hub Adapters (New Centralized Architecture)
from .whatsapp_adapter import WhatsAppHubAdapter
from .instagram_adapter import InstagramHubAdapter
from .tiktok_adapter import TikTokHubAdapter

__all__ = [
    # Main Bot
    "ProfessionalSellerBot",
    "create_seller_bot",
    
    # Models
    "IncomingMessage",
    "BotResponse",
    "ConversationContext",
    "IntentAnalysis",
    
    # Enums
    "MessageChannel",
    "ConversationStage",
    "Intent",
    "SentimentType",
    "LeadTemperature",
    
    # Components
    "IntentDetector",
    "ResponseTemplates",
    
    # Channel Adapters (Legacy - use Hub Adapters instead)
    "ChannelAdapter",
    "EvolutionAdapter",
    "ChatwootAdapter",
    "InstagramAdapter",
    "TikTokAdapter",
    "ChannelRouter",
    
    # Hub Adapters (New Architecture)
    "WhatsAppHubAdapter",
    "InstagramHubAdapter",
    "TikTokHubAdapter",
    
    # Configs
    "EvolutionConfig",
    "ChatwootConfig",
    "InstagramConfig",
    "TikTokConfig",
    
    # Factory functions
    "create_evolution_adapter",
    "create_chatwoot_adapter",
    "create_instagram_adapter",
]
