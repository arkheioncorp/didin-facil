"""
Chatbot Templates
=================
Templates de chatbot prontos para Typebot.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid


class ChatbotCategory(str, Enum):
    """Categorias de chatbot."""
    ATENDIMENTO = "atendimento"
    VENDAS = "vendas"
    SUPORTE = "suporte"
    QUALIFICACAO = "qualificacao"
    AGENDAMENTO = "agendamento"
    FAQ = "faq"


@dataclass
class ChatbotTemplate:
    """Template de chatbot."""
    id: str
    name: str
    description: str
    category: ChatbotCategory
    difficulty: str
    estimated_time: str
    tags: List[str] = field(default_factory=list)
    required_integrations: List[str] = field(default_factory=list)
    flow_json: Dict[str, Any] = field(default_factory=dict)
    variables: List[Dict[str, str]] = field(default_factory=list)
    preview_image: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "difficulty": self.difficulty,
            "estimated_time": self.estimated_time,
            "tags": self.tags,
            "required_integrations": self.required_integrations,
            "variables": self.variables,
            "preview_image": self.preview_image,
        }


# ============================================
# BLOCOS REUTILIZÁVEIS
# ============================================

def create_text_block(text: str, block_id: str = None) -> Dict[str, Any]:
    """Cria bloco de texto."""
    return {
        "id": block_id or str(uuid.uuid4())[:8],
        "type": "text",
        "content": {"richText": [{"type": "p", "children": [{"text": text}]}]}
    }


def create_input_block(label: str, variable: str, input_type: str = "text", block_id: str = None) -> Dict[str, Any]:
    """Cria bloco de input."""
    return {
        "id": block_id or str(uuid.uuid4())[:8],
        "type": "text input",
        "options": {
            "labels": {"placeholder": label},
            "variableId": variable
        }
    }


def create_buttons_block(buttons: List[Dict[str, str]], block_id: str = None) -> Dict[str, Any]:
    """Cria bloco de botões."""
    return {
        "id": block_id or str(uuid.uuid4())[:8],
        "type": "choice input",
        "items": [{"id": str(uuid.uuid4())[:8], "content": btn["text"]} for btn in buttons]
    }


def create_condition_block(variable: str, value: str, block_id: str = None) -> Dict[str, Any]:
    """Cria bloco de condição."""
    return {
        "id": block_id or str(uuid.uuid4())[:8],
        "type": "condition",
        "items": [
            {
                "id": str(uuid.uuid4())[:8],
                "content": {
                    "comparisons": [
                        {
                            "id": str(uuid.uuid4())[:8],
                            "variableId": variable,
                            "comparisonOperator": "Equal",
                            "value": value
                        }
                    ]
                }
            }
        ]
    }


def create_webhook_block(url: str, method: str = "POST", body: Dict = None, block_id: str = None) -> Dict[str, Any]:
    """Cria bloco de webhook."""
    return {
        "id": block_id or str(uuid.uuid4())[:8],
        "type": "webhook",
        "options": {
            "url": url,
            "method": method,
            "body": body or {}
        }
    }


# ============================================
# TEMPLATES DE CHATBOT
# ============================================

CHATBOT_TEMPLATES: Dict[str, ChatbotTemplate] = {
    # ===== ATENDIMENTO =====
    "customer_service": ChatbotTemplate(
        id="customer_service",
        name="Atendimento ao Cliente",
        description="Bot completo de atendimento com menu, FAQ e encaminhamento para humano",
        category=ChatbotCategory.ATENDIMENTO,
        difficulty="beginner",
        estimated_time="15 min",
        tags=["atendimento", "suporte", "menu"],
        required_integrations=["whatsapp"],
        variables=[
            {"name": "COMPANY_NAME", "description": "Nome da empresa", "default": "TikTrend Finder"},
            {"name": "SUPPORT_PHONE", "description": "Telefone do suporte", "default": ""},
        ],
        flow_json={
            "version": "6",
            "id": "customer-service-flow",
            "name": "Atendimento ao Cliente",
            "groups": [
                {
                    "id": "welcome",
                    "title": "Boas-vindas",
                    "blocks": [
                        {
                            "id": "welcome_msg",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "Olá! 👋 Bem-vindo ao "},
                                        {"text": "{{COMPANY_NAME}}", "bold": True},
                                        {"text": "!"}
                                    ]},
                                    {"type": "p", "children": [
                                        {"text": "Como posso ajudar você hoje?"}
                                    ]}
                                ]
                            }
                        },
                        {
                            "id": "name_input",
                            "type": "text input",
                            "options": {
                                "labels": {"placeholder": "Digite seu nome"},
                                "variableId": "user_name"
                            }
                        },
                        {
                            "id": "menu",
                            "type": "choice input",
                            "items": [
                                {"id": "opt1", "content": "🛒 Ver ofertas"},
                                {"id": "opt2", "content": "📦 Rastrear pedido"},
                                {"id": "opt3", "content": "❓ Dúvidas frequentes"},
                                {"id": "opt4", "content": "💬 Falar com atendente"}
                            ]
                        }
                    ],
                    "graphCoordinates": {"x": 0, "y": 0}
                },
                {
                    "id": "offers",
                    "title": "Ofertas",
                    "blocks": [
                        {
                            "id": "offers_msg",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "🔥 Confira nossas melhores ofertas do dia!"}
                                    ]}
                                ]
                            }
                        },
                        {
                            "id": "offers_webhook",
                            "type": "webhook",
                            "options": {
                                "url": "{{API_URL}}/api/v1/offers/top",
                                "method": "GET"
                            }
                        },
                        {
                            "id": "show_offers",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "{{webhook.offers}}"}
                                    ]}
                                ]
                            }
                        }
                    ],
                    "graphCoordinates": {"x": 400, "y": 0}
                },
                {
                    "id": "tracking",
                    "title": "Rastreamento",
                    "blocks": [
                        {
                            "id": "tracking_msg",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "📦 Para rastrear seu pedido, informe o código:"}
                                    ]}
                                ]
                            }
                        },
                        {
                            "id": "order_code",
                            "type": "text input",
                            "options": {
                                "labels": {"placeholder": "Ex: DD123456"},
                                "variableId": "order_code"
                            }
                        },
                        {
                            "id": "tracking_webhook",
                            "type": "webhook",
                            "options": {
                                "url": "{{API_URL}}/api/v1/orders/{{order_code}}/tracking",
                                "method": "GET"
                            }
                        }
                    ],
                    "graphCoordinates": {"x": 400, "y": 200}
                },
                {
                    "id": "faq",
                    "title": "FAQ",
                    "blocks": [
                        {
                            "id": "faq_msg",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "❓ Selecione sua dúvida:"}
                                    ]}
                                ]
                            }
                        },
                        {
                            "id": "faq_options",
                            "type": "choice input",
                            "items": [
                                {"id": "faq1", "content": "Como funciona a comparação de preços?"},
                                {"id": "faq2", "content": "Quais lojas estão disponíveis?"},
                                {"id": "faq3", "content": "Como ativar alertas de preço?"},
                                {"id": "faq4", "content": "Política de privacidade"}
                            ]
                        }
                    ],
                    "graphCoordinates": {"x": 400, "y": 400}
                },
                {
                    "id": "human",
                    "title": "Atendente",
                    "blocks": [
                        {
                            "id": "human_msg",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "💬 Entendi! Vou transferir você para um atendente."}
                                    ]},
                                    {"type": "p", "children": [
                                        {"text": "Aguarde um momento..."}
                                    ]}
                                ]
                            }
                        },
                        {
                            "id": "transfer_webhook",
                            "type": "webhook",
                            "options": {
                                "url": "{{API_URL}}/api/v1/chat/transfer",
                                "method": "POST",
                                "body": {
                                    "session_id": "{{session_id}}",
                                    "user_name": "{{user_name}}",
                                    "reason": "user_request"
                                }
                            }
                        }
                    ],
                    "graphCoordinates": {"x": 400, "y": 600}
                }
            ],
            "edges": [
                {"id": "e1", "from": {"blockId": "menu", "itemId": "opt1"}, "to": {"groupId": "offers"}},
                {"id": "e2", "from": {"blockId": "menu", "itemId": "opt2"}, "to": {"groupId": "tracking"}},
                {"id": "e3", "from": {"blockId": "menu", "itemId": "opt3"}, "to": {"groupId": "faq"}},
                {"id": "e4", "from": {"blockId": "menu", "itemId": "opt4"}, "to": {"groupId": "human"}}
            ],
            "variables": [
                {"id": "user_name", "name": "user_name"},
                {"id": "order_code", "name": "order_code"},
                {"id": "session_id", "name": "session_id"}
            ]
        }
    ),
    
    # ===== VENDAS =====
    "sales_funnel": ChatbotTemplate(
        id="sales_funnel",
        name="Funil de Vendas",
        description="Qualifica leads e apresenta produtos de forma automatizada",
        category=ChatbotCategory.VENDAS,
        difficulty="intermediate",
        estimated_time="25 min",
        tags=["vendas", "funil", "qualificação"],
        required_integrations=["whatsapp", "crm"],
        variables=[
            {"name": "PRODUCT_CATALOG_URL", "description": "URL do catálogo", "default": ""},
        ],
        flow_json={
            "version": "6",
            "id": "sales-funnel-flow",
            "name": "Funil de Vendas",
            "groups": [
                {
                    "id": "start",
                    "title": "Início",
                    "blocks": [
                        {
                            "id": "greeting",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "Olá! 🎉 Que bom te ver por aqui!"}
                                    ]},
                                    {"type": "p", "children": [
                                        {"text": "Sou o assistente virtual e vou te ajudar a encontrar as melhores ofertas!"}
                                    ]}
                                ]
                            }
                        },
                        {
                            "id": "get_name",
                            "type": "text input",
                            "options": {
                                "labels": {"placeholder": "Como posso te chamar?"},
                                "variableId": "lead_name"
                            }
                        },
                        {
                            "id": "confirm_name",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "Prazer, {{lead_name}}! 😊"}
                                    ]}
                                ]
                            }
                        }
                    ]
                },
                {
                    "id": "qualify",
                    "title": "Qualificação",
                    "blocks": [
                        {
                            "id": "interest_q",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "O que você está buscando hoje?"}
                                    ]}
                                ]
                            }
                        },
                        {
                            "id": "category_select",
                            "type": "choice input",
                            "items": [
                                {"id": "cat1", "content": "📱 Eletrônicos"},
                                {"id": "cat2", "content": "👗 Moda"},
                                {"id": "cat3", "content": "🏠 Casa e Decoração"},
                                {"id": "cat4", "content": "💄 Beleza"},
                                {"id": "cat5", "content": "🎮 Games"}
                            ]
                        },
                        {
                            "id": "budget_q",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "Qual sua faixa de orçamento?"}
                                    ]}
                                ]
                            }
                        },
                        {
                            "id": "budget_select",
                            "type": "choice input",
                            "items": [
                                {"id": "b1", "content": "Até R$ 100"},
                                {"id": "b2", "content": "R$ 100 - R$ 500"},
                                {"id": "b3", "content": "R$ 500 - R$ 1.000"},
                                {"id": "b4", "content": "Acima de R$ 1.000"}
                            ]
                        }
                    ]
                },
                {
                    "id": "present",
                    "title": "Apresentação",
                    "blocks": [
                        {
                            "id": "search_products",
                            "type": "webhook",
                            "options": {
                                "url": "{{API_URL}}/api/v1/products/recommend",
                                "method": "POST",
                                "body": {
                                    "category": "{{category}}",
                                    "budget": "{{budget}}",
                                    "lead_name": "{{lead_name}}"
                                }
                            }
                        },
                        {
                            "id": "show_products",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "✨ Encontrei essas ofertas perfeitas para você:"}
                                    ]},
                                    {"type": "p", "children": [
                                        {"text": "{{webhook.products}}"}
                                    ]}
                                ]
                            }
                        },
                        {
                            "id": "cta",
                            "type": "choice input",
                            "items": [
                                {"id": "cta1", "content": "🛒 Quero comprar!"},
                                {"id": "cta2", "content": "🔔 Avisar quando baixar"},
                                {"id": "cta3", "content": "👀 Ver mais opções"}
                            ]
                        }
                    ]
                },
                {
                    "id": "capture",
                    "title": "Captura",
                    "blocks": [
                        {
                            "id": "get_contact",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "📧 Para te enviar as melhores ofertas, me passa seu e-mail:"}
                                    ]}
                                ]
                            }
                        },
                        {
                            "id": "email_input",
                            "type": "email input",
                            "options": {
                                "labels": {"placeholder": "seu@email.com"},
                                "variableId": "lead_email"
                            }
                        },
                        {
                            "id": "get_phone",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "📱 E seu WhatsApp para avisar sobre promoções exclusivas:"}
                                    ]}
                                ]
                            }
                        },
                        {
                            "id": "phone_input",
                            "type": "phone input",
                            "options": {
                                "labels": {"placeholder": "(11) 99999-9999"},
                                "variableId": "lead_phone"
                            }
                        },
                        {
                            "id": "save_lead",
                            "type": "webhook",
                            "options": {
                                "url": "{{API_URL}}/api/v1/leads",
                                "method": "POST",
                                "body": {
                                    "name": "{{lead_name}}",
                                    "email": "{{lead_email}}",
                                    "phone": "{{lead_phone}}",
                                    "category": "{{category}}",
                                    "budget": "{{budget}}",
                                    "source": "chatbot_sales_funnel"
                                }
                            }
                        },
                        {
                            "id": "thanks",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "🎉 Perfeito, {{lead_name}}!"}
                                    ]},
                                    {"type": "p", "children": [
                                        {"text": "Você receberá nossas melhores ofertas em primeira mão!"}
                                    ]},
                                    {"type": "p", "children": [
                                        {"text": "Enquanto isso, explore nosso catálogo: {{PRODUCT_CATALOG_URL}}"}
                                    ]}
                                ]
                            }
                        }
                    ]
                }
            ],
            "variables": [
                {"id": "lead_name", "name": "lead_name"},
                {"id": "lead_email", "name": "lead_email"},
                {"id": "lead_phone", "name": "lead_phone"},
                {"id": "category", "name": "category"},
                {"id": "budget", "name": "budget"}
            ]
        }
    ),
    
    # ===== QUALIFICAÇÃO =====
    "lead_qualification": ChatbotTemplate(
        id="lead_qualification",
        name="Qualificação de Leads",
        description="Qualifica leads com perguntas BANT (Budget, Authority, Need, Timeline)",
        category=ChatbotCategory.QUALIFICACAO,
        difficulty="intermediate",
        estimated_time="20 min",
        tags=["leads", "bant", "qualificação"],
        required_integrations=["crm"],
        variables=[
            {"name": "MIN_BUDGET", "description": "Orçamento mínimo para qualificar", "default": "500"},
        ],
        flow_json={
            "version": "6",
            "id": "lead-qual-flow",
            "name": "Qualificação BANT",
            "groups": [
                {
                    "id": "intro",
                    "title": "Introdução",
                    "blocks": [
                        {
                            "id": "intro_msg",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [
                                        {"text": "👋 Olá! Obrigado pelo interesse!"}
                                    ]},
                                    {"type": "p", "children": [
                                        {"text": "Vou fazer algumas perguntas rápidas para entender melhor suas necessidades."}
                                    ]}
                                ]
                            }
                        }
                    ]
                },
                {
                    "id": "budget",
                    "title": "Budget",
                    "blocks": [
                        {
                            "id": "budget_q",
                            "type": "text",
                            "content": {
                                "richText": [{"type": "p", "children": [{"text": "💰 Qual seu orçamento mensal para marketing/vendas?"}]}]
                            }
                        },
                        {
                            "id": "budget_options",
                            "type": "choice input",
                            "items": [
                                {"id": "b1", "content": "Menos de R$ 500"},
                                {"id": "b2", "content": "R$ 500 - R$ 2.000"},
                                {"id": "b3", "content": "R$ 2.000 - R$ 5.000"},
                                {"id": "b4", "content": "Mais de R$ 5.000"}
                            ]
                        }
                    ]
                },
                {
                    "id": "authority",
                    "title": "Authority",
                    "blocks": [
                        {
                            "id": "auth_q",
                            "type": "text",
                            "content": {
                                "richText": [{"type": "p", "children": [{"text": "👤 Você é responsável pelas decisões de compra na empresa?"}]}]
                            }
                        },
                        {
                            "id": "auth_options",
                            "type": "choice input",
                            "items": [
                                {"id": "a1", "content": "Sim, sou o decisor"},
                                {"id": "a2", "content": "Influencio, mas preciso de aprovação"},
                                {"id": "a3", "content": "Sou pesquisador/analista"}
                            ]
                        }
                    ]
                },
                {
                    "id": "need",
                    "title": "Need",
                    "blocks": [
                        {
                            "id": "need_q",
                            "type": "text",
                            "content": {
                                "richText": [{"type": "p", "children": [{"text": "🎯 Qual seu principal desafio hoje?"}]}]
                            }
                        },
                        {
                            "id": "need_options",
                            "type": "choice input",
                            "items": [
                                {"id": "n1", "content": "Aumentar vendas"},
                                {"id": "n2", "content": "Automatizar processos"},
                                {"id": "n3", "content": "Melhorar atendimento"},
                                {"id": "n4", "content": "Reduzir custos"}
                            ]
                        }
                    ]
                },
                {
                    "id": "timeline",
                    "title": "Timeline",
                    "blocks": [
                        {
                            "id": "time_q",
                            "type": "text",
                            "content": {
                                "richText": [{"type": "p", "children": [{"text": "⏰ Quando você pretende implementar uma solução?"}]}]
                            }
                        },
                        {
                            "id": "time_options",
                            "type": "choice input",
                            "items": [
                                {"id": "t1", "content": "Imediatamente"},
                                {"id": "t2", "content": "Este mês"},
                                {"id": "t3", "content": "Próximos 3 meses"},
                                {"id": "t4", "content": "Apenas pesquisando"}
                            ]
                        }
                    ]
                },
                {
                    "id": "score",
                    "title": "Score",
                    "blocks": [
                        {
                            "id": "calculate_score",
                            "type": "set variable",
                            "options": {
                                "variableId": "lead_score",
                                "expressionToEvaluate": "{{budget_score + authority_score + need_score + timeline_score}}"
                            }
                        },
                        {
                            "id": "save_qualified",
                            "type": "webhook",
                            "options": {
                                "url": "{{API_URL}}/api/v1/leads/qualified",
                                "method": "POST",
                                "body": {
                                    "budget": "{{budget}}",
                                    "authority": "{{authority}}",
                                    "need": "{{need}}",
                                    "timeline": "{{timeline}}",
                                    "score": "{{lead_score}}"
                                }
                            }
                        }
                    ]
                },
                {
                    "id": "qualified",
                    "title": "Qualificado",
                    "blocks": [
                        {
                            "id": "qual_msg",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "🎉 Excelente! Você se qualifica para nossa solução!"}]},
                                    {"type": "p", "children": [{"text": "Um especialista entrará em contato em até 24h."}]}
                                ]
                            }
                        }
                    ]
                },
                {
                    "id": "nurture",
                    "title": "Nutrir",
                    "blocks": [
                        {
                            "id": "nurture_msg",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "📚 Obrigado pelas informações!"}]},
                                    {"type": "p", "children": [{"text": "Enquanto isso, confira nosso conteúdo gratuito que pode te ajudar!"}]}
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    ),
    
    # ===== AGENDAMENTO =====
    "appointment_booking": ChatbotTemplate(
        id="appointment_booking",
        name="Agendamento de Consultas",
        description="Agenda consultas/reuniões automaticamente com integração de calendário",
        category=ChatbotCategory.AGENDAMENTO,
        difficulty="intermediate",
        estimated_time="20 min",
        tags=["agendamento", "calendário", "reunião"],
        required_integrations=["google-calendar", "whatsapp"],
        variables=[
            {"name": "CALENDAR_ID", "description": "ID do calendário Google", "default": ""},
            {"name": "MEETING_DURATION", "description": "Duração da reunião (minutos)", "default": "30"},
        ],
        flow_json={
            "version": "6",
            "id": "appointment-flow",
            "name": "Agendamento",
            "groups": [
                {
                    "id": "start",
                    "title": "Início",
                    "blocks": [
                        {
                            "id": "welcome",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "📅 Vamos agendar seu horário!"}]},
                                    {"type": "p", "children": [{"text": "Primeiro, me conta um pouco sobre você:"}]}
                                ]
                            }
                        },
                        {
                            "id": "get_name",
                            "type": "text input",
                            "options": {"labels": {"placeholder": "Seu nome"}, "variableId": "client_name"}
                        },
                        {
                            "id": "get_email",
                            "type": "email input",
                            "options": {"labels": {"placeholder": "Seu email"}, "variableId": "client_email"}
                        },
                        {
                            "id": "get_phone",
                            "type": "phone input",
                            "options": {"labels": {"placeholder": "Seu WhatsApp"}, "variableId": "client_phone"}
                        }
                    ]
                },
                {
                    "id": "service",
                    "title": "Serviço",
                    "blocks": [
                        {
                            "id": "service_q",
                            "type": "text",
                            "content": {"richText": [{"type": "p", "children": [{"text": "Qual serviço você deseja agendar?"}]}]}
                        },
                        {
                            "id": "service_options",
                            "type": "choice input",
                            "items": [
                                {"id": "s1", "content": "📞 Consultoria (30 min)"},
                                {"id": "s2", "content": "🎯 Demonstração (45 min)"},
                                {"id": "s3", "content": "📊 Análise Completa (60 min)"}
                            ]
                        }
                    ]
                },
                {
                    "id": "date",
                    "title": "Data/Hora",
                    "blocks": [
                        {
                            "id": "fetch_slots",
                            "type": "webhook",
                            "options": {
                                "url": "{{API_URL}}/api/v1/calendar/available-slots",
                                "method": "GET"
                            }
                        },
                        {
                            "id": "date_q",
                            "type": "text",
                            "content": {"richText": [{"type": "p", "children": [{"text": "📅 Escolha uma data disponível:"}]}]}
                        },
                        {
                            "id": "date_picker",
                            "type": "date input",
                            "options": {"variableId": "appointment_date"}
                        },
                        {
                            "id": "time_q",
                            "type": "text",
                            "content": {"richText": [{"type": "p", "children": [{"text": "⏰ Horários disponíveis:"}]}]}
                        },
                        {
                            "id": "time_options",
                            "type": "choice input",
                            "items": [
                                {"id": "t1", "content": "09:00"},
                                {"id": "t2", "content": "10:00"},
                                {"id": "t3", "content": "11:00"},
                                {"id": "t4", "content": "14:00"},
                                {"id": "t5", "content": "15:00"},
                                {"id": "t6", "content": "16:00"}
                            ]
                        }
                    ]
                },
                {
                    "id": "confirm",
                    "title": "Confirmação",
                    "blocks": [
                        {
                            "id": "summary",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "📋 Confirme seu agendamento:"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "👤 Nome: {{client_name}}"}]},
                                    {"type": "p", "children": [{"text": "📅 Data: {{appointment_date}}"}]},
                                    {"type": "p", "children": [{"text": "⏰ Horário: {{appointment_time}}"}]},
                                    {"type": "p", "children": [{"text": "📌 Serviço: {{service}}"}]}
                                ]
                            }
                        },
                        {
                            "id": "confirm_btn",
                            "type": "choice input",
                            "items": [
                                {"id": "c1", "content": "✅ Confirmar agendamento"},
                                {"id": "c2", "content": "🔄 Escolher outro horário"}
                            ]
                        }
                    ]
                },
                {
                    "id": "book",
                    "title": "Agendar",
                    "blocks": [
                        {
                            "id": "create_event",
                            "type": "webhook",
                            "options": {
                                "url": "{{API_URL}}/api/v1/calendar/book",
                                "method": "POST",
                                "body": {
                                    "name": "{{client_name}}",
                                    "email": "{{client_email}}",
                                    "phone": "{{client_phone}}",
                                    "date": "{{appointment_date}}",
                                    "time": "{{appointment_time}}",
                                    "service": "{{service}}"
                                }
                            }
                        },
                        {
                            "id": "success",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "✅ Agendamento confirmado!"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "Você receberá um email de confirmação e um lembrete no WhatsApp."}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "Até lá! 👋"}]}
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    ),
    
    # ===== FAQ =====
    "faq_bot": ChatbotTemplate(
        id="faq_bot",
        name="Bot de Perguntas Frequentes",
        description="Responde automaticamente às dúvidas mais comuns dos clientes",
        category=ChatbotCategory.FAQ,
        difficulty="beginner",
        estimated_time="10 min",
        tags=["faq", "dúvidas", "autoatendimento"],
        required_integrations=[],
        variables=[
            {"name": "COMPANY_NAME", "description": "Nome da empresa", "default": "TikTrend Finder"},
        ],
        flow_json={
            "version": "6",
            "id": "faq-flow",
            "name": "FAQ Bot",
            "groups": [
                {
                    "id": "menu",
                    "title": "Menu Principal",
                    "blocks": [
                        {
                            "id": "greeting",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "🤖 Olá! Sou o assistente do {{COMPANY_NAME}}."}]},
                                    {"type": "p", "children": [{"text": "Sobre o que você gostaria de saber?"}]}
                                ]
                            }
                        },
                        {
                            "id": "faq_menu",
                            "type": "choice input",
                            "items": [
                                {"id": "f1", "content": "🔍 Como funciona a comparação?"},
                                {"id": "f2", "content": "💰 Quanto custa?"},
                                {"id": "f3", "content": "🔔 Como ativar alertas?"},
                                {"id": "f4", "content": "🛒 Lojas disponíveis"},
                                {"id": "f5", "content": "🔐 Segurança dos dados"},
                                {"id": "f6", "content": "💬 Falar com humano"}
                            ]
                        }
                    ]
                },
                {
                    "id": "how_it_works",
                    "title": "Como Funciona",
                    "blocks": [
                        {
                            "id": "how_answer",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "🔍 ", "bold": True}, {"text": "Como funciona a comparação de preços?"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "1️⃣ Pesquise o produto que deseja"}]},
                                    {"type": "p", "children": [{"text": "2️⃣ Comparamos preços em 20+ lojas"}]},
                                    {"type": "p", "children": [{"text": "3️⃣ Mostramos o menor preço com histórico"}]},
                                    {"type": "p", "children": [{"text": "4️⃣ Você clica e compra direto na loja!"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "Simples assim! 🎉"}]}
                                ]
                            }
                        }
                    ]
                },
                {
                    "id": "pricing",
                    "title": "Preços",
                    "blocks": [
                        {
                            "id": "pricing_answer",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "💰 ", "bold": True}, {"text": "Quanto custa usar o TikTrend Finder?"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "🆓 ", "bold": True}, {"text": "Gratuito para sempre:"}]},
                                    {"type": "p", "children": [{"text": "• Comparação ilimitada de preços"}]},
                                    {"type": "p", "children": [{"text": "• Histórico de 30 dias"}]},
                                    {"type": "p", "children": [{"text": "• 3 alertas de preço"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "⭐ ", "bold": True}, {"text": "Plano PRO (R$ 9,90/mês):"}]},
                                    {"type": "p", "children": [{"text": "• Alertas ilimitados"}]},
                                    {"type": "p", "children": [{"text": "• Histórico de 1 ano"}]},
                                    {"type": "p", "children": [{"text": "• Alertas por WhatsApp"}]}
                                ]
                            }
                        }
                    ]
                },
                {
                    "id": "alerts",
                    "title": "Alertas",
                    "blocks": [
                        {
                            "id": "alerts_answer",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "🔔 ", "bold": True}, {"text": "Como ativar alertas de preço?"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "1. Pesquise o produto desejado"}]},
                                    {"type": "p", "children": [{"text": "2. Clique no ícone de sino 🔔"}]},
                                    {"type": "p", "children": [{"text": "3. Defina o preço desejado"}]},
                                    {"type": "p", "children": [{"text": "4. Pronto! Avisaremos quando baixar!"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "Você pode gerenciar seus alertas em 'Minha Conta' > 'Alertas'."}]}
                                ]
                            }
                        }
                    ]
                },
                {
                    "id": "stores",
                    "title": "Lojas",
                    "blocks": [
                        {
                            "id": "stores_answer",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "🛒 ", "bold": True}, {"text": "Lojas disponíveis:"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "Amazon | Mercado Livre | Magazine Luiza"}]},
                                    {"type": "p", "children": [{"text": "Americanas | Casas Bahia | Shopee"}]},
                                    {"type": "p", "children": [{"text": "AliExpress | Submarino | Kabum"}]},
                                    {"type": "p", "children": [{"text": "Ponto Frio | Extra | Fast Shop"}]},
                                    {"type": "p", "children": [{"text": "E mais de 15 outras lojas!"}]}
                                ]
                            }
                        }
                    ]
                },
                {
                    "id": "security",
                    "title": "Segurança",
                    "blocks": [
                        {
                            "id": "security_answer",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "🔐 ", "bold": True}, {"text": "Segurança dos seus dados:"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "✅ Seus dados são criptografados"}]},
                                    {"type": "p", "children": [{"text": "✅ Não vendemos informações pessoais"}]},
                                    {"type": "p", "children": [{"text": "✅ Conformidade com LGPD"}]},
                                    {"type": "p", "children": [{"text": "✅ Você pode excluir seus dados a qualquer momento"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "Para mais detalhes, acesse nossa Política de Privacidade."}]}
                                ]
                            }
                        }
                    ]
                },
                {
                    "id": "back_menu",
                    "title": "Voltar",
                    "blocks": [
                        {
                            "id": "more_help",
                            "type": "text",
                            "content": {"richText": [{"type": "p", "children": [{"text": "Posso ajudar com mais alguma coisa?"}]}]}
                        },
                        {
                            "id": "back_options",
                            "type": "choice input",
                            "items": [
                                {"id": "b1", "content": "✅ Sim, tenho outra dúvida"},
                                {"id": "b2", "content": "👍 Não, obrigado!"}
                            ]
                        }
                    ]
                },
                {
                    "id": "goodbye",
                    "title": "Despedida",
                    "blocks": [
                        {
                            "id": "bye_msg",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "😊 Fico feliz em ajudar!"}]},
                                    {"type": "p", "children": [{"text": "Se precisar de mais alguma coisa, é só me chamar!"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "Até mais! 👋"}]}
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    ),
    
    # ===== SUPORTE =====
    "support_ticket": ChatbotTemplate(
        id="support_ticket",
        name="Suporte Técnico",
        description="Coleta informações e cria tickets de suporte automaticamente",
        category=ChatbotCategory.SUPORTE,
        difficulty="beginner",
        estimated_time="12 min",
        tags=["suporte", "ticket", "problema"],
        required_integrations=["zendesk", "freshdesk"],
        variables=[
            {"name": "SUPPORT_EMAIL", "description": "Email do suporte", "default": "suporte@tiktrendfinder.app"},
        ],
        flow_json={
            "version": "6",
            "id": "support-ticket-flow",
            "name": "Suporte Técnico",
            "groups": [
                {
                    "id": "start",
                    "title": "Início",
                    "blocks": [
                        {
                            "id": "greeting",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "🛠️ Olá! Vamos resolver seu problema."}]},
                                    {"type": "p", "children": [{"text": "Primeiro, qual é o tipo de problema?"}]}
                                ]
                            }
                        },
                        {
                            "id": "problem_type",
                            "type": "choice input",
                            "items": [
                                {"id": "p1", "content": "🔐 Login / Acesso"},
                                {"id": "p2", "content": "💳 Pagamento"},
                                {"id": "p3", "content": "🔔 Alertas não funcionam"},
                                {"id": "p4", "content": "🐛 Bug / Erro"},
                                {"id": "p5", "content": "📦 Pedido / Entrega"},
                                {"id": "p6", "content": "❓ Outro"}
                            ]
                        }
                    ]
                },
                {
                    "id": "details",
                    "title": "Detalhes",
                    "blocks": [
                        {
                            "id": "describe",
                            "type": "text",
                            "content": {"richText": [{"type": "p", "children": [{"text": "📝 Descreva o problema com detalhes:"}]}]}
                        },
                        {
                            "id": "problem_desc",
                            "type": "text input",
                            "options": {
                                "labels": {"placeholder": "Descreva aqui o que está acontecendo..."},
                                "variableId": "problem_description",
                                "isLong": True
                            }
                        },
                        {
                            "id": "screenshot_q",
                            "type": "text",
                            "content": {"richText": [{"type": "p", "children": [{"text": "📸 Tem algum print do erro? (opcional)"}]}]}
                        },
                        {
                            "id": "screenshot",
                            "type": "file input",
                            "options": {"variableId": "screenshot_url"}
                        }
                    ]
                },
                {
                    "id": "contact",
                    "title": "Contato",
                    "blocks": [
                        {
                            "id": "contact_q",
                            "type": "text",
                            "content": {"richText": [{"type": "p", "children": [{"text": "📧 Seu email para retorno:"}]}]}
                        },
                        {
                            "id": "email",
                            "type": "email input",
                            "options": {"labels": {"placeholder": "seu@email.com"}, "variableId": "user_email"}
                        }
                    ]
                },
                {
                    "id": "create",
                    "title": "Criar Ticket",
                    "blocks": [
                        {
                            "id": "create_ticket",
                            "type": "webhook",
                            "options": {
                                "url": "{{API_URL}}/api/v1/support/tickets",
                                "method": "POST",
                                "body": {
                                    "type": "{{problem_type}}",
                                    "description": "{{problem_description}}",
                                    "screenshot": "{{screenshot_url}}",
                                    "email": "{{user_email}}",
                                    "source": "chatbot"
                                }
                            }
                        },
                        {
                            "id": "success",
                            "type": "text",
                            "content": {
                                "richText": [
                                    {"type": "p", "children": [{"text": "✅ Ticket criado com sucesso!"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "📋 Número: #{{webhook.ticket_id}}"}]},
                                    {"type": "p", "children": [{"text": ""}]},
                                    {"type": "p", "children": [{"text": "Nossa equipe analisará e responderá em até 24h."}]},
                                    {"type": "p", "children": [{"text": "Você receberá atualizações por email."}]}
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    ),
}


def get_chatbot_templates(
    category: Optional[ChatbotCategory] = None,
    difficulty: Optional[str] = None
) -> List[ChatbotTemplate]:
    """
    Retorna templates de chatbot filtrados.
    """
    templates = list(CHATBOT_TEMPLATES.values())
    
    if category:
        templates = [t for t in templates if t.category == category]
    
    if difficulty:
        templates = [t for t in templates if t.difficulty == difficulty]
    
    return templates


def get_chatbot_by_id(template_id: str) -> Optional[ChatbotTemplate]:
    """Retorna template por ID."""
    return CHATBOT_TEMPLATES.get(template_id)


def export_typebot_flow(template_id: str, variables: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Exporta fluxo Typebot pronto para importar.
    """
    template = get_chatbot_by_id(template_id)
    if not template:
        raise ValueError(f"Template não encontrado: {template_id}")
    
    flow = template.flow_json.copy()
    
    # Aplicar variáveis customizadas
    if variables:
        flow_str = json.dumps(flow)
        for key, value in variables.items():
            flow_str = flow_str.replace(f"{{{{{key}}}}}", value)
        flow = json.loads(flow_str)
    
    return flow
