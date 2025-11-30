"""
Templates Module
================
Módulo central de templates e pré-configurações para usuários.

Inclui:
- Templates de automação n8n (10 workflows prontos)
- Templates de chatbot Typebot (7 fluxos conversacionais)
- Templates de conteúdo para redes sociais (15+ formatos)
- Configurações pré-definidas por nicho (12 presets de negócio)
"""

# Automação (n8n workflows)
from .automation_templates import (
    AutomationTemplate,
    AutomationCategory,
    AutomationTrigger,
    AUTOMATION_TEMPLATES,
    get_automation_templates,
    get_template_by_id as get_automation_by_id,
    export_n8n_workflow,
)

# Chatbot (Typebot flows)
from .chatbot_templates import (
    ChatbotTemplate,
    ChatbotCategory,
    CHATBOT_TEMPLATES,
    get_chatbot_templates,
    get_chatbot_by_id,
    export_typebot_flow,
    create_text_block,
    create_input_block,
    create_buttons_block,
    create_condition_block,
    create_webhook_block,
)

# Conteúdo (Social media)
from .content_templates import (
    ContentTemplate,
    ContentPlatform,
    ContentType,
    ContentCategory,
    CONTENT_TEMPLATES,
    CONTENT_CALENDAR_TEMPLATE,
    get_content_templates,
    get_content_by_id,
    generate_caption,
    get_weekly_calendar,
    suggest_next_post,
)

# Presets de Negócio
from .business_presets import (
    BusinessPreset,
    BusinessType,
    BusinessSize,
    BUSINESS_PRESETS,
    get_business_presets,
    get_preset_by_id,
    recommend_preset,
    apply_preset,
    calculate_preset_value,
)

__all__ = [
    # Automação
    "AutomationTemplate",
    "AutomationCategory",
    "AutomationTrigger",
    "AUTOMATION_TEMPLATES",
    "get_automation_templates",
    "get_automation_by_id",
    "export_n8n_workflow",
    
    # Chatbot
    "ChatbotTemplate",
    "ChatbotCategory",
    "CHATBOT_TEMPLATES",
    "get_chatbot_templates",
    "get_chatbot_by_id",
    "export_typebot_flow",
    "create_text_block",
    "create_input_block",
    "create_buttons_block",
    "create_condition_block",
    "create_webhook_block",
    
    # Conteúdo
    "ContentTemplate",
    "ContentPlatform",
    "ContentType",
    "ContentCategory",
    "CONTENT_TEMPLATES",
    "CONTENT_CALENDAR_TEMPLATE",
    "get_content_templates",
    "get_content_by_id",
    "generate_caption",
    "get_weekly_calendar",
    "suggest_next_post",
    
    # Presets
    "BusinessPreset",
    "BusinessType",
    "BusinessSize",
    "BUSINESS_PRESETS",
    "get_business_presets",
    "get_preset_by_id",
    "recommend_preset",
    "apply_preset",
    "calculate_preset_value",
]
