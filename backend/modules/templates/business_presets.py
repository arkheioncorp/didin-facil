"""
Business Presets
================
Configurações pré-definidas por tipo de negócio.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class BusinessType(str, Enum):
    """Tipos de negócio suportados."""
    ECOMMERCE = "ecommerce"
    INFOPRODUTOS = "infoprodutos"
    SERVICOS = "servicos"
    SAAS = "saas"
    VAREJO = "varejo"
    ALIMENTACAO = "alimentacao"
    SAUDE = "saude"
    EDUCACAO = "educacao"
    MODA = "moda"
    TECNOLOGIA = "tecnologia"


class BusinessSize(str, Enum):
    """Tamanho do negócio."""
    SOLO = "solo"        # 1 pessoa
    MICRO = "micro"      # 2-10 pessoas
    SMALL = "small"      # 11-50 pessoas
    MEDIUM = "medium"    # 51-200 pessoas
    LARGE = "large"      # 200+ pessoas


@dataclass
class BusinessPreset:
    """Preset de configuração por tipo de negócio."""
    id: str
    name: str
    description: str
    business_type: BusinessType
    business_size: BusinessSize
    
    # Automações recomendadas
    recommended_workflows: List[str] = field(default_factory=list)
    
    # Chatbots recomendados
    recommended_chatbots: List[str] = field(default_factory=list)
    
    # Templates de conteúdo recomendados
    recommended_content: List[str] = field(default_factory=list)
    
    # Configurações específicas
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Métricas alvo
    target_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Integrações recomendadas
    recommended_integrations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "business_type": self.business_type.value,
            "business_size": self.business_size.value,
            "recommended_workflows": self.recommended_workflows,
            "recommended_chatbots": self.recommended_chatbots,
            "recommended_content": self.recommended_content,
            "config": self.config,
            "target_metrics": self.target_metrics,
            "recommended_integrations": self.recommended_integrations,
        }


# ============================================
# PRESETS POR TIPO DE NEGÓCIO
# ============================================

BUSINESS_PRESETS: Dict[str, BusinessPreset] = {
    
    # ===== E-COMMERCE =====
    "ecommerce_starter": BusinessPreset(
        id="ecommerce_starter",
        name="E-commerce Iniciante",
        description="Para lojas online começando a automatizar vendas",
        business_type=BusinessType.ECOMMERCE,
        business_size=BusinessSize.SOLO,
        recommended_workflows=[
            "price_drop_alert",
            "welcome_sequence",
            "abandoned_cart",
            "review_request",
        ],
        recommended_chatbots=[
            "customer_service",
            "faq_bot",
        ],
        recommended_content=[
            "flash_sale",
            "daily_deals",
            "price_drop_alert",
        ],
        config={
            "price_check_frequency": "4h",
            "alert_channels": ["whatsapp", "email"],
            "auto_post_deals": True,
            "cart_abandon_delay": "30m",
            "review_request_delay": "3d",
            "welcome_sequence_steps": 3,
        },
        target_metrics={
            "cart_recovery_rate": 0.15,
            "review_rate": 0.10,
            "email_open_rate": 0.25,
            "whatsapp_response_rate": 0.80,
        },
        recommended_integrations=[
            "whatsapp",
            "email",
            "mercadopago",
        ]
    ),
    
    "ecommerce_growth": BusinessPreset(
        id="ecommerce_growth",
        name="E-commerce em Crescimento",
        description="Para lojas estabelecidas buscando escalar",
        business_type=BusinessType.ECOMMERCE,
        business_size=BusinessSize.SMALL,
        recommended_workflows=[
            "price_drop_alert",
            "welcome_sequence",
            "abandoned_cart",
            "lead_qualification",
            "competitor_monitor",
            "restock_alert",
            "daily_deals",
        ],
        recommended_chatbots=[
            "customer_service",
            "sales_funnel",
            "lead_qualification",
            "support_ticket",
        ],
        recommended_content=[
            "flash_sale",
            "daily_deals",
            "price_drop_alert",
            "user_testimonial",
            "product_review",
        ],
        config={
            "price_check_frequency": "1h",
            "alert_channels": ["whatsapp", "email", "push"],
            "auto_post_deals": True,
            "cart_abandon_delay": "15m",
            "review_request_delay": "2d",
            "welcome_sequence_steps": 5,
            "competitor_check_frequency": "6h",
            "lead_scoring_enabled": True,
        },
        target_metrics={
            "cart_recovery_rate": 0.25,
            "review_rate": 0.15,
            "email_open_rate": 0.30,
            "whatsapp_response_rate": 0.90,
            "lead_conversion_rate": 0.05,
        },
        recommended_integrations=[
            "whatsapp",
            "email",
            "mercadopago",
            "crm",
            "analytics",
        ]
    ),
    
    "ecommerce_enterprise": BusinessPreset(
        id="ecommerce_enterprise",
        name="E-commerce Enterprise",
        description="Para grandes operações com alto volume",
        business_type=BusinessType.ECOMMERCE,
        business_size=BusinessSize.LARGE,
        recommended_workflows=[
            "price_drop_alert",
            "welcome_sequence",
            "abandoned_cart",
            "lead_qualification",
            "competitor_monitor",
            "restock_alert",
            "daily_deals",
            "content_reminder",
            "social_post_scheduler",
        ],
        recommended_chatbots=[
            "customer_service",
            "sales_funnel",
            "lead_qualification",
            "support_ticket",
            "appointment_booking",
        ],
        recommended_content=[
            "flash_sale",
            "daily_deals",
            "price_drop_alert",
            "user_testimonial",
            "product_review",
            "behind_scenes",
            "new_feature",
        ],
        config={
            "price_check_frequency": "15m",
            "alert_channels": ["whatsapp", "email", "push", "sms"],
            "auto_post_deals": True,
            "cart_abandon_delay": "5m",
            "review_request_delay": "1d",
            "welcome_sequence_steps": 7,
            "competitor_check_frequency": "1h",
            "lead_scoring_enabled": True,
            "ab_testing_enabled": True,
            "advanced_analytics": True,
            "multi_channel_sync": True,
        },
        target_metrics={
            "cart_recovery_rate": 0.35,
            "review_rate": 0.20,
            "email_open_rate": 0.35,
            "whatsapp_response_rate": 0.95,
            "lead_conversion_rate": 0.08,
            "nps_score": 70,
        },
        recommended_integrations=[
            "whatsapp",
            "email",
            "mercadopago",
            "crm",
            "analytics",
            "erp",
            "helpdesk",
            "bi",
        ]
    ),
    
    # ===== INFOPRODUTOS =====
    "infoproduct_creator": BusinessPreset(
        id="infoproduct_creator",
        name="Criador de Infoprodutos",
        description="Para quem vende cursos, ebooks, mentorias",
        business_type=BusinessType.INFOPRODUTOS,
        business_size=BusinessSize.SOLO,
        recommended_workflows=[
            "welcome_sequence",
            "lead_qualification",
            "content_reminder",
            "social_post_scheduler",
        ],
        recommended_chatbots=[
            "sales_funnel",
            "lead_qualification",
            "faq_bot",
        ],
        recommended_content=[
            "price_comparison_tip",
            "user_testimonial",
            "question_post",
            "tiktok_trend",
        ],
        config={
            "lead_magnet_enabled": True,
            "email_sequence_steps": 7,
            "launch_mode": True,
            "scarcity_enabled": True,
            "testimonial_collection": True,
            "content_calendar_enabled": True,
        },
        target_metrics={
            "lead_magnet_conversion": 0.25,
            "email_open_rate": 0.35,
            "sales_page_conversion": 0.03,
            "course_completion_rate": 0.40,
        },
        recommended_integrations=[
            "whatsapp",
            "email",
            "hotmart",
            "instagram",
            "youtube",
        ]
    ),
    
    # ===== SERVIÇOS =====
    "service_freelancer": BusinessPreset(
        id="service_freelancer",
        name="Freelancer/Consultor",
        description="Para profissionais liberais e consultores",
        business_type=BusinessType.SERVICOS,
        business_size=BusinessSize.SOLO,
        recommended_workflows=[
            "welcome_sequence",
            "lead_qualification",
            "content_reminder",
        ],
        recommended_chatbots=[
            "lead_qualification",
            "appointment_booking",
            "faq_bot",
        ],
        recommended_content=[
            "price_comparison_tip",
            "user_testimonial",
            "behind_scenes",
            "question_post",
        ],
        config={
            "calendar_integration": True,
            "proposal_automation": True,
            "follow_up_enabled": True,
            "portfolio_showcase": True,
        },
        target_metrics={
            "lead_to_call_rate": 0.30,
            "call_to_client_rate": 0.40,
            "client_retention_rate": 0.70,
            "referral_rate": 0.20,
        },
        recommended_integrations=[
            "whatsapp",
            "email",
            "google-calendar",
            "stripe",
        ]
    ),
    
    "service_agency": BusinessPreset(
        id="service_agency",
        name="Agência de Serviços",
        description="Para agências de marketing, design, desenvolvimento",
        business_type=BusinessType.SERVICOS,
        business_size=BusinessSize.SMALL,
        recommended_workflows=[
            "welcome_sequence",
            "lead_qualification",
            "content_reminder",
            "social_post_scheduler",
        ],
        recommended_chatbots=[
            "sales_funnel",
            "lead_qualification",
            "appointment_booking",
            "support_ticket",
        ],
        recommended_content=[
            "user_testimonial",
            "behind_scenes",
            "new_feature",
            "price_comparison_tip",
        ],
        config={
            "multi_project_tracking": True,
            "client_portal": True,
            "proposal_templates": True,
            "time_tracking": True,
            "invoicing_automation": True,
        },
        target_metrics={
            "lead_to_client_rate": 0.15,
            "client_retention_rate": 0.80,
            "project_profitability": 0.40,
            "nps_score": 60,
        },
        recommended_integrations=[
            "whatsapp",
            "email",
            "crm",
            "project-management",
            "invoicing",
        ]
    ),
    
    # ===== SAAS =====
    "saas_startup": BusinessPreset(
        id="saas_startup",
        name="SaaS Startup",
        description="Para startups de software como serviço",
        business_type=BusinessType.SAAS,
        business_size=BusinessSize.MICRO,
        recommended_workflows=[
            "welcome_sequence",
            "lead_qualification",
            "daily_deals",  # Para trials
        ],
        recommended_chatbots=[
            "customer_service",
            "sales_funnel",
            "support_ticket",
            "faq_bot",
        ],
        recommended_content=[
            "new_feature",
            "user_testimonial",
            "price_comparison_tip",
            "behind_scenes",
        ],
        config={
            "trial_onboarding": True,
            "usage_tracking": True,
            "churn_prediction": True,
            "feature_announcement": True,
            "in_app_messaging": True,
        },
        target_metrics={
            "trial_to_paid_rate": 0.10,
            "monthly_churn_rate": 0.05,
            "nps_score": 50,
            "dau_mau_ratio": 0.20,
        },
        recommended_integrations=[
            "email",
            "intercom",
            "stripe",
            "analytics",
            "slack",
        ]
    ),
    
    # ===== VAREJO FÍSICO =====
    "retail_store": BusinessPreset(
        id="retail_store",
        name="Loja Física",
        description="Para lojas físicas com presença digital",
        business_type=BusinessType.VAREJO,
        business_size=BusinessSize.SMALL,
        recommended_workflows=[
            "price_drop_alert",
            "welcome_sequence",
            "restock_alert",
            "review_request",
        ],
        recommended_chatbots=[
            "customer_service",
            "faq_bot",
            "appointment_booking",
        ],
        recommended_content=[
            "flash_sale",
            "daily_deals",
            "user_testimonial",
            "behind_scenes",
        ],
        config={
            "store_locator": True,
            "appointment_booking": True,
            "in_store_pickup": True,
            "loyalty_program": True,
            "local_seo": True,
        },
        target_metrics={
            "foot_traffic": 1000,  # mensal
            "conversion_rate": 0.25,
            "average_ticket": 150,
            "loyalty_retention": 0.60,
        },
        recommended_integrations=[
            "whatsapp",
            "google-my-business",
            "pos",
            "loyalty",
        ]
    ),
    
    # ===== ALIMENTAÇÃO =====
    "food_delivery": BusinessPreset(
        id="food_delivery",
        name="Delivery de Alimentos",
        description="Para restaurantes e dark kitchens",
        business_type=BusinessType.ALIMENTACAO,
        business_size=BusinessSize.MICRO,
        recommended_workflows=[
            "welcome_sequence",
            "review_request",
            "restock_alert",
        ],
        recommended_chatbots=[
            "customer_service",
            "faq_bot",
        ],
        recommended_content=[
            "flash_sale",
            "daily_deals",
            "behind_scenes",
            "user_testimonial",
        ],
        config={
            "menu_sync": True,
            "order_tracking": True,
            "peak_hour_alerts": True,
            "ingredient_tracking": True,
            "review_response": True,
        },
        target_metrics={
            "order_frequency": 2.5,  # pedidos por cliente/mês
            "average_order_value": 45,
            "delivery_time": 35,  # minutos
            "review_rating": 4.5,
        },
        recommended_integrations=[
            "whatsapp",
            "ifood",
            "rappi",
            "pos",
        ]
    ),
    
    # ===== SAÚDE =====
    "health_clinic": BusinessPreset(
        id="health_clinic",
        name="Clínica de Saúde",
        description="Para clínicas médicas, odontológicas, estéticas",
        business_type=BusinessType.SAUDE,
        business_size=BusinessSize.SMALL,
        recommended_workflows=[
            "welcome_sequence",
            "content_reminder",
        ],
        recommended_chatbots=[
            "appointment_booking",
            "faq_bot",
            "customer_service",
        ],
        recommended_content=[
            "price_comparison_tip",  # Dicas de saúde
            "user_testimonial",
            "behind_scenes",
        ],
        config={
            "appointment_reminders": True,
            "hipaa_compliant": True,
            "patient_portal": True,
            "prescription_reminders": True,
            "follow_up_care": True,
        },
        target_metrics={
            "appointment_show_rate": 0.90,
            "patient_retention": 0.75,
            "nps_score": 70,
            "referral_rate": 0.30,
        },
        recommended_integrations=[
            "whatsapp",
            "google-calendar",
            "medical-records",
            "payment",
        ]
    ),
    
    # ===== EDUCAÇÃO =====
    "education_school": BusinessPreset(
        id="education_school",
        name="Escola/Curso Presencial",
        description="Para escolas, cursos livres, academias",
        business_type=BusinessType.EDUCACAO,
        business_size=BusinessSize.SMALL,
        recommended_workflows=[
            "welcome_sequence",
            "content_reminder",
            "lead_qualification",
        ],
        recommended_chatbots=[
            "sales_funnel",
            "faq_bot",
            "appointment_booking",
        ],
        recommended_content=[
            "user_testimonial",
            "behind_scenes",
            "price_comparison_tip",
        ],
        config={
            "class_scheduling": True,
            "attendance_tracking": True,
            "parent_communication": True,
            "enrollment_funnel": True,
            "certification_automation": True,
        },
        target_metrics={
            "enrollment_rate": 0.20,
            "student_retention": 0.85,
            "class_attendance": 0.90,
            "nps_score": 60,
        },
        recommended_integrations=[
            "whatsapp",
            "email",
            "lms",
            "payment",
        ]
    ),
    
    # ===== MODA =====
    "fashion_brand": BusinessPreset(
        id="fashion_brand",
        name="Marca de Moda",
        description="Para marcas de roupas, acessórios, calçados",
        business_type=BusinessType.MODA,
        business_size=BusinessSize.SMALL,
        recommended_workflows=[
            "price_drop_alert",
            "welcome_sequence",
            "abandoned_cart",
            "restock_alert",
            "social_post_scheduler",
        ],
        recommended_chatbots=[
            "sales_funnel",
            "customer_service",
            "faq_bot",
        ],
        recommended_content=[
            "flash_sale",
            "daily_deals",
            "user_testimonial",
            "behind_scenes",
            "tiktok_trend",
        ],
        config={
            "size_guide": True,
            "lookbook_generator": True,
            "influencer_tracking": True,
            "season_planning": True,
            "ugc_collection": True,
        },
        target_metrics={
            "instagram_engagement": 0.05,
            "cart_recovery_rate": 0.20,
            "return_rate": 0.10,
            "average_order_value": 200,
        },
        recommended_integrations=[
            "whatsapp",
            "instagram",
            "tiktok",
            "shopify",
        ]
    ),
    
    # ===== TECNOLOGIA =====
    "tech_company": BusinessPreset(
        id="tech_company",
        name="Empresa de Tecnologia",
        description="Para empresas de TI, desenvolvimento, consultoria tech",
        business_type=BusinessType.TECNOLOGIA,
        business_size=BusinessSize.SMALL,
        recommended_workflows=[
            "welcome_sequence",
            "lead_qualification",
            "content_reminder",
            "social_post_scheduler",
        ],
        recommended_chatbots=[
            "lead_qualification",
            "support_ticket",
            "appointment_booking",
            "faq_bot",
        ],
        recommended_content=[
            "price_comparison_tip",
            "new_feature",
            "user_testimonial",
            "behind_scenes",
            "product_review",
        ],
        config={
            "technical_documentation": True,
            "api_status_page": True,
            "developer_portal": True,
            "ticket_escalation": True,
            "knowledge_base": True,
        },
        target_metrics={
            "ticket_resolution_time": 4,  # horas
            "customer_satisfaction": 0.90,
            "developer_adoption": 0.30,
            "documentation_usage": 0.60,
        },
        recommended_integrations=[
            "slack",
            "jira",
            "github",
            "intercom",
            "stripe",
        ]
    ),
}


def get_business_presets(
    business_type: Optional[BusinessType] = None,
    business_size: Optional[BusinessSize] = None
) -> List[BusinessPreset]:
    """
    Retorna presets filtrados por tipo e tamanho.
    """
    presets = list(BUSINESS_PRESETS.values())
    
    if business_type:
        presets = [p for p in presets if p.business_type == business_type]
    
    if business_size:
        presets = [p for p in presets if p.business_size == business_size]
    
    return presets


def get_preset_by_id(preset_id: str) -> Optional[BusinessPreset]:
    """Retorna preset por ID."""
    return BUSINESS_PRESETS.get(preset_id)


def recommend_preset(
    business_type: BusinessType,
    monthly_revenue: float = 0,
    team_size: int = 1
) -> BusinessPreset:
    """
    Recomenda o melhor preset baseado em critérios.
    """
    # Determinar tamanho do negócio
    if team_size == 1:
        size = BusinessSize.SOLO
    elif team_size <= 10:
        size = BusinessSize.MICRO
    elif team_size <= 50:
        size = BusinessSize.SMALL
    elif team_size <= 200:
        size = BusinessSize.MEDIUM
    else:
        size = BusinessSize.LARGE
    
    # Buscar presets compatíveis
    candidates = get_business_presets(business_type=business_type)
    
    # Priorizar por tamanho mais próximo
    size_order = [BusinessSize.SOLO, BusinessSize.MICRO, BusinessSize.SMALL, BusinessSize.MEDIUM, BusinessSize.LARGE]
    size_index = size_order.index(size)
    
    # Encontrar preset mais adequado
    best_preset = None
    best_distance = float('inf')
    
    for preset in candidates:
        preset_index = size_order.index(preset.business_size)
        distance = abs(preset_index - size_index)
        
        # Preferir preset menor ou igual
        if preset_index <= size_index:
            distance -= 0.5
        
        if distance < best_distance:
            best_distance = distance
            best_preset = preset
    
    return best_preset or candidates[0] if candidates else None


def apply_preset(preset_id: str) -> Dict[str, Any]:
    """
    Retorna configuração completa para aplicar preset.
    """
    preset = get_preset_by_id(preset_id)
    if not preset:
        raise ValueError(f"Preset não encontrado: {preset_id}")
    
    return {
        "preset": preset.to_dict(),
        "setup_steps": [
            {
                "step": 1,
                "title": "Configurar Integrações",
                "integrations": preset.recommended_integrations,
                "description": f"Configure as {len(preset.recommended_integrations)} integrações recomendadas"
            },
            {
                "step": 2,
                "title": "Importar Automações",
                "workflows": preset.recommended_workflows,
                "description": f"Importe {len(preset.recommended_workflows)} workflows automatizados"
            },
            {
                "step": 3,
                "title": "Configurar Chatbots",
                "chatbots": preset.recommended_chatbots,
                "description": f"Configure {len(preset.recommended_chatbots)} chatbots"
            },
            {
                "step": 4,
                "title": "Preparar Conteúdo",
                "templates": preset.recommended_content,
                "description": f"Use {len(preset.recommended_content)} templates de conteúdo"
            },
            {
                "step": 5,
                "title": "Ajustar Configurações",
                "config": preset.config,
                "description": "Personalize as configurações para seu negócio"
            },
            {
                "step": 6,
                "title": "Definir Metas",
                "metrics": preset.target_metrics,
                "description": "Configure as métricas e metas recomendadas"
            },
        ],
        "estimated_setup_time": "30-60 minutos",
        "automation_value": calculate_preset_value(preset),
    }


def calculate_preset_value(preset: BusinessPreset) -> Dict[str, Any]:
    """
    Calcula o valor estimado da automação.
    """
    # Estimativas de economia de tempo por tipo
    time_savings = {
        "workflow": 2,      # horas/semana por workflow
        "chatbot": 5,       # horas/semana por chatbot
        "content": 1,       # horas/semana por template de conteúdo
    }
    
    weekly_hours = (
        len(preset.recommended_workflows) * time_savings["workflow"] +
        len(preset.recommended_chatbots) * time_savings["chatbot"] +
        len(preset.recommended_content) * time_savings["content"]
    )
    
    hourly_rate = 50  # R$/hora estimado
    
    return {
        "weekly_hours_saved": weekly_hours,
        "monthly_hours_saved": weekly_hours * 4,
        "estimated_monthly_value": weekly_hours * 4 * hourly_rate,
        "breakdown": {
            "workflows": len(preset.recommended_workflows) * time_savings["workflow"] * 4,
            "chatbots": len(preset.recommended_chatbots) * time_savings["chatbot"] * 4,
            "content": len(preset.recommended_content) * time_savings["content"] * 4,
        }
    }
