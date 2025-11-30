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
    
    # Router
    ChannelRouter,
    
    # Configs
    EvolutionConfig,
    ChatwootConfig,
    InstagramConfig,
    
    # Factory functions
    create_evolution_adapter,
    create_chatwoot_adapter,
    create_instagram_adapter,
)

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
    
    # Channel Adapters
    "ChannelAdapter",
    "EvolutionAdapter",
    "ChatwootAdapter",
    "InstagramAdapter",
    "ChannelRouter",
    
    # Configs
    "EvolutionConfig",
    "ChatwootConfig",
    "InstagramConfig",
    
    # Factory functions
    "create_evolution_adapter",
    "create_chatwoot_adapter",
    "create_instagram_adapter",
]
