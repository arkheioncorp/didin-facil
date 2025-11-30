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
from .instagram_hub import (
    InstagramHub,
    InstagramHubConfig,
    InstagramMessage,
    InstagramMessageType,
    get_instagram_hub,
)
from .tiktok_hub import (
    TikTokHub,
    TikTokHubConfig,
    get_tiktok_hub,
)
from .resilience import (
    # Rate Limiting
    RateLimiterConfig,
    TokenBucketRateLimiter,
    SlidingWindowRateLimiter,
    RateLimitExceededError,
    # Circuit Breaker
    CircuitBreakerConfig,
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    CircuitBreakerStats,
    # Retry
    RetryConfig,
    retry_with_backoff,
    # Decorators
    with_rate_limit,
    with_circuit_breaker,
    with_retry,
    # Mixin
    HubResilienceMixin,
)
from .metrics import (
    HubMetricsRegistry,
    HubHealthChecker,
    HubHealth,
    MetricType,
    with_metrics,
    get_metrics_registry,
    get_health_checker,
    export_prometheus_metrics,
)
from .alerts import (
    AlertManager,
    AlertSeverity,
    AlertType,
    Alert,
    SlackChannel,
    DiscordChannel,
    WebhookChannel,
    get_alert_manager,
    configure_alert_manager,
    alert_on_circuit_breaker_change,
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
    # Instagram Hub
    "InstagramHub",
    "InstagramHubConfig",
    "InstagramMessage",
    "InstagramMessageType",
    "get_instagram_hub",
    # TikTok Hub
    "TikTokHub",
    "TikTokHubConfig",
    "get_tiktok_hub",
    # Resilience
    "RateLimiterConfig",
    "TokenBucketRateLimiter",
    "SlidingWindowRateLimiter",
    "RateLimitExceededError",
    "CircuitBreakerConfig",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    "CircuitBreakerStats",
    "RetryConfig",
    "retry_with_backoff",
    "with_rate_limit",
    "with_circuit_breaker",
    "with_retry",
    "HubResilienceMixin",
    # Metrics
    "HubMetricsRegistry",
    "HubHealthChecker",
    "HubHealth",
    "MetricType",
    "with_metrics",
    "get_metrics_registry",
    "get_health_checker",
    "export_prometheus_metrics",
    # Alerts
    "AlertManager",
    "AlertSeverity",
    "AlertType",
    "Alert",
    "SlackChannel",
    "DiscordChannel",
    "WebhookChannel",
    "get_alert_manager",
    "configure_alert_manager",
    "alert_on_circuit_breaker_change",
]
