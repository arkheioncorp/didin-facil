"""
Automation Templates
====================
Templates de automação prontos para n8n.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class AutomationCategory(str, Enum):
    """Categorias de automação."""
    MARKETING = "marketing"
    VENDAS = "vendas"
    ATENDIMENTO = "atendimento"
    CONTEUDO = "conteudo"
    INTEGRACAO = "integracao"
    MONITORAMENTO = "monitoramento"


class AutomationTrigger(str, Enum):
    """Tipos de gatilho."""
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    EVENT = "event"


@dataclass
class AutomationTemplate:
    """Template de automação."""
    id: str
    name: str
    description: str
    category: AutomationCategory
    trigger: AutomationTrigger
    difficulty: str  # beginner, intermediate, advanced
    estimated_time: str  # "5 min", "15 min", etc
    tags: List[str] = field(default_factory=list)
    required_integrations: List[str] = field(default_factory=list)
    workflow_json: Dict[str, Any] = field(default_factory=dict)
    variables: List[Dict[str, str]] = field(default_factory=list)
    preview_image: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "trigger": self.trigger.value,
            "difficulty": self.difficulty,
            "estimated_time": self.estimated_time,
            "tags": self.tags,
            "required_integrations": self.required_integrations,
            "variables": self.variables,
            "preview_image": self.preview_image,
        }


# ============================================
# TEMPLATES DE AUTOMAÇÃO
# ============================================

AUTOMATION_TEMPLATES: Dict[str, AutomationTemplate] = {
    # ===== MARKETING =====
    "welcome_sequence": AutomationTemplate(
        id="welcome_sequence",
        name="Sequência de Boas-Vindas",
        description="Envia mensagens automáticas para novos leads via WhatsApp",
        category=AutomationCategory.MARKETING,
        trigger=AutomationTrigger.WEBHOOK,
        difficulty="beginner",
        estimated_time="10 min",
        tags=["whatsapp", "leads", "onboarding"],
        required_integrations=["evolution-api"],
        variables=[
            {"name": "WELCOME_MESSAGE", "description": "Mensagem de boas-vindas", "default": "Olá! Bem-vindo ao TikTrend Finder!"},
            {"name": "DELAY_MINUTES", "description": "Delay entre mensagens (minutos)", "default": "5"},
        ],
        workflow_json={
            "name": "Sequência de Boas-Vindas",
            "nodes": [
                {
                    "id": "webhook_trigger",
                    "type": "n8n-nodes-base.webhook",
                    "position": [250, 300],
                    "parameters": {
                        "path": "new-lead",
                        "httpMethod": "POST"
                    }
                },
                {
                    "id": "set_variables",
                    "type": "n8n-nodes-base.set",
                    "position": [450, 300],
                    "parameters": {
                        "values": {
                            "string": [
                                {"name": "phone", "value": "={{$json.phone}}"},
                                {"name": "name", "value": "={{$json.name}}"}
                            ]
                        }
                    }
                },
                {
                    "id": "send_welcome",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [650, 300],
                    "parameters": {
                        "url": "={{$env.EVOLUTION_API_URL}}/message/sendText/{{$env.WHATSAPP_INSTANCE}}",
                        "method": "POST",
                        "headers": {
                            "apikey": "={{$env.EVOLUTION_API_KEY}}"
                        },
                        "body": {
                            "number": "={{$node.set_variables.json.phone}}",
                            "text": "={{$env.WELCOME_MESSAGE}}"
                        }
                    }
                },
                {
                    "id": "wait",
                    "type": "n8n-nodes-base.wait",
                    "position": [850, 300],
                    "parameters": {
                        "amount": "={{$env.DELAY_MINUTES}}",
                        "unit": "minutes"
                    }
                },
                {
                    "id": "send_followup",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [1050, 300],
                    "parameters": {
                        "url": "={{$env.EVOLUTION_API_URL}}/message/sendText/{{$env.WHATSAPP_INSTANCE}}",
                        "method": "POST",
                        "headers": {
                            "apikey": "={{$env.EVOLUTION_API_KEY}}"
                        },
                        "body": {
                            "number": "={{$node.set_variables.json.phone}}",
                            "text": "Você já conhece nossas ofertas? 🔥\n\nAcesse: https://tiktrendfinder.app/ofertas"
                        }
                    }
                }
            ],
            "connections": {
                "webhook_trigger": {"main": [[{"node": "set_variables", "type": "main", "index": 0}]]},
                "set_variables": {"main": [[{"node": "send_welcome", "type": "main", "index": 0}]]},
                "send_welcome": {"main": [[{"node": "wait", "type": "main", "index": 0}]]},
                "wait": {"main": [[{"node": "send_followup", "type": "main", "index": 0}]]}
            }
        }
    ),
    
    "price_drop_alert": AutomationTemplate(
        id="price_drop_alert",
        name="Alerta de Queda de Preço",
        description="Notifica usuários quando um produto monitorado baixa de preço",
        category=AutomationCategory.MARKETING,
        trigger=AutomationTrigger.WEBHOOK,
        difficulty="intermediate",
        estimated_time="15 min",
        tags=["preços", "alertas", "whatsapp", "email"],
        required_integrations=["evolution-api", "smtp"],
        variables=[
            {"name": "MIN_DISCOUNT", "description": "Desconto mínimo para notificar (%)", "default": "10"},
        ],
        workflow_json={
            "name": "Alerta de Queda de Preço",
            "nodes": [
                {
                    "id": "webhook",
                    "type": "n8n-nodes-base.webhook",
                    "position": [250, 300],
                    "parameters": {
                        "path": "price-drop",
                        "httpMethod": "POST"
                    }
                },
                {
                    "id": "check_discount",
                    "type": "n8n-nodes-base.if",
                    "position": [450, 300],
                    "parameters": {
                        "conditions": {
                            "number": [{
                                "value1": "={{$json.discount_percent}}",
                                "operation": "largerEqual",
                                "value2": "={{$env.MIN_DISCOUNT}}"
                            }]
                        }
                    }
                },
                {
                    "id": "get_watchers",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [650, 200],
                    "parameters": {
                        "url": "={{$env.API_URL}}/api/v1/products/{{$json.product_id}}/watchers",
                        "method": "GET",
                        "headers": {
                            "Authorization": "Bearer {{$env.API_KEY}}"
                        }
                    }
                },
                {
                    "id": "split_watchers",
                    "type": "n8n-nodes-base.splitInBatches",
                    "position": [850, 200],
                    "parameters": {
                        "batchSize": 1
                    }
                },
                {
                    "id": "send_whatsapp",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [1050, 200],
                    "parameters": {
                        "url": "={{$env.EVOLUTION_API_URL}}/message/sendText/{{$env.WHATSAPP_INSTANCE}}",
                        "method": "POST",
                        "body": {
                            "number": "={{$json.phone}}",
                            "text": "🔔 *Alerta de Preço!*\n\n{{$json.product_name}} baixou de R$ {{$json.old_price}} para *R$ {{$json.new_price}}*!\n\n💸 Economia de {{$json.discount_percent}}%\n\n🛒 Compre agora: {{$json.url}}"
                        }
                    }
                }
            ]
        }
    ),
    
    "abandoned_cart": AutomationTemplate(
        id="abandoned_cart",
        name="Recuperação de Carrinho Abandonado",
        description="Envia lembretes para clientes que abandonaram o carrinho",
        category=AutomationCategory.VENDAS,
        trigger=AutomationTrigger.SCHEDULE,
        difficulty="intermediate",
        estimated_time="20 min",
        tags=["carrinho", "vendas", "recuperação"],
        required_integrations=["evolution-api", "database"],
        variables=[
            {"name": "HOURS_THRESHOLD", "description": "Horas desde abandono para notificar", "default": "2"},
            {"name": "MAX_REMINDERS", "description": "Máximo de lembretes por carrinho", "default": "3"},
        ],
        workflow_json={
            "name": "Recuperação de Carrinho",
            "nodes": [
                {
                    "id": "schedule",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "position": [250, 300],
                    "parameters": {
                        "rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}
                    }
                },
                {
                    "id": "get_abandoned",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 300],
                    "parameters": {
                        "url": "={{$env.API_URL}}/api/v1/carts/abandoned?hours={{$env.HOURS_THRESHOLD}}",
                        "method": "GET"
                    }
                },
                {
                    "id": "filter_notified",
                    "type": "n8n-nodes-base.filter",
                    "position": [650, 300],
                    "parameters": {
                        "conditions": {
                            "number": [{
                                "value1": "={{$json.reminder_count}}",
                                "operation": "smaller",
                                "value2": "={{$env.MAX_REMINDERS}}"
                            }]
                        }
                    }
                },
                {
                    "id": "send_reminder",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [850, 300],
                    "parameters": {
                        "url": "={{$env.EVOLUTION_API_URL}}/message/sendText/{{$env.WHATSAPP_INSTANCE}}",
                        "method": "POST",
                        "body": {
                            "number": "={{$json.customer_phone}}",
                            "text": "Oi {{$json.customer_name}}! 👋\n\nVocê deixou alguns itens no carrinho:\n\n{{$json.items_summary}}\n\n🛒 Finalize sua compra: {{$json.checkout_url}}\n\n⏰ Seus itens estão reservados por mais 24h!"
                        }
                    }
                }
            ]
        }
    ),
    
    # ===== CONTEÚDO =====
    "auto_post_scheduler": AutomationTemplate(
        id="auto_post_scheduler",
        name="Publicador Automático de Posts",
        description="Publica posts agendados automaticamente nas redes sociais",
        category=AutomationCategory.CONTEUDO,
        trigger=AutomationTrigger.SCHEDULE,
        difficulty="intermediate",
        estimated_time="15 min",
        tags=["social media", "instagram", "tiktok", "youtube"],
        required_integrations=["instagram", "tiktok"],
        variables=[
            {"name": "CHECK_INTERVAL", "description": "Intervalo de verificação (minutos)", "default": "5"},
        ],
        workflow_json={
            "name": "Publicador Automático",
            "nodes": [
                {
                    "id": "schedule",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "position": [250, 300],
                    "parameters": {
                        "rule": {"interval": [{"field": "minutes", "minutesInterval": 5}]}
                    }
                },
                {
                    "id": "get_scheduled",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 300],
                    "parameters": {
                        "url": "={{$env.API_URL}}/api/v1/posts/scheduled/ready",
                        "method": "GET"
                    }
                },
                {
                    "id": "switch_platform",
                    "type": "n8n-nodes-base.switch",
                    "position": [650, 300],
                    "parameters": {
                        "dataPropertyName": "platform",
                        "rules": {
                            "rules": [
                                {"value": "instagram"},
                                {"value": "tiktok"},
                                {"value": "youtube"}
                            ]
                        }
                    }
                },
                {
                    "id": "post_instagram",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [850, 200],
                    "parameters": {
                        "url": "={{$env.API_URL}}/api/v1/instagram/post",
                        "method": "POST",
                        "body": "={{$json}}"
                    }
                },
                {
                    "id": "post_tiktok",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [850, 300],
                    "parameters": {
                        "url": "={{$env.API_URL}}/api/v1/tiktok/post",
                        "method": "POST",
                        "body": "={{$json}}"
                    }
                },
                {
                    "id": "post_youtube",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [850, 400],
                    "parameters": {
                        "url": "={{$env.API_URL}}/api/v1/youtube/post",
                        "method": "POST",
                        "body": "={{$json}}"
                    }
                },
                {
                    "id": "update_status",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [1050, 300],
                    "parameters": {
                        "url": "={{$env.API_URL}}/api/v1/posts/{{$json.id}}/status",
                        "method": "PATCH",
                        "body": {"status": "published", "published_at": "={{$now}}"}
                    }
                }
            ]
        }
    ),
    
    "content_generator": AutomationTemplate(
        id="content_generator",
        name="Gerador de Conteúdo com IA",
        description="Gera conteúdo automaticamente para produtos usando IA",
        category=AutomationCategory.CONTEUDO,
        trigger=AutomationTrigger.WEBHOOK,
        difficulty="advanced",
        estimated_time="25 min",
        tags=["ia", "openai", "conteúdo", "automático"],
        required_integrations=["openai"],
        variables=[
            {"name": "OPENAI_MODEL", "description": "Modelo OpenAI", "default": "gpt-4o-mini"},
            {"name": "CONTENT_STYLE", "description": "Estilo do conteúdo", "default": "promotional"},
        ],
        workflow_json={
            "name": "Gerador de Conteúdo IA",
            "nodes": [
                {
                    "id": "webhook",
                    "type": "n8n-nodes-base.webhook",
                    "position": [250, 300],
                    "parameters": {"path": "generate-content", "httpMethod": "POST"}
                },
                {
                    "id": "openai",
                    "type": "n8n-nodes-base.openAi",
                    "position": [450, 300],
                    "parameters": {
                        "model": "={{$env.OPENAI_MODEL}}",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Você é um especialista em marketing digital e criação de conteúdo para redes sociais."
                            },
                            {
                                "role": "user",
                                "content": "Crie uma legenda {{$env.CONTENT_STYLE}} para o produto: {{$json.product_name}} (R$ {{$json.price}}). Inclua emojis e 5 hashtags."
                            }
                        ]
                    }
                },
                {
                    "id": "save_content",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [650, 300],
                    "parameters": {
                        "url": "={{$env.API_URL}}/api/v1/content",
                        "method": "POST",
                        "body": {
                            "product_id": "={{$json.product_id}}",
                            "caption": "={{$node.openai.json.message.content}}",
                            "generated_at": "={{$now}}"
                        }
                    }
                }
            ]
        }
    ),
    
    # ===== ATENDIMENTO =====
    "auto_reply": AutomationTemplate(
        id="auto_reply",
        name="Resposta Automática Inteligente",
        description="Responde automaticamente mensagens de clientes com IA",
        category=AutomationCategory.ATENDIMENTO,
        trigger=AutomationTrigger.WEBHOOK,
        difficulty="advanced",
        estimated_time="30 min",
        tags=["atendimento", "ia", "whatsapp", "chatbot"],
        required_integrations=["evolution-api", "openai"],
        variables=[
            {"name": "BUSINESS_CONTEXT", "description": "Contexto do negócio para IA", "default": "Loja de comparação de preços"},
            {"name": "FALLBACK_MESSAGE", "description": "Mensagem quando IA falha", "default": "Um momento, vou transferir para um atendente."},
        ],
        workflow_json={
            "name": "Resposta Automática IA",
            "nodes": [
                {
                    "id": "webhook",
                    "type": "n8n-nodes-base.webhook",
                    "position": [250, 300],
                    "parameters": {"path": "whatsapp-message", "httpMethod": "POST"}
                },
                {
                    "id": "check_intent",
                    "type": "n8n-nodes-base.openAi",
                    "position": [450, 300],
                    "parameters": {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Analise a intenção da mensagem e classifique como: DUVIDA, RECLAMACAO, COMPRA, SUPORTE, OUTRO"
                            },
                            {"role": "user", "content": "={{$json.message}}"}
                        ]
                    }
                },
                {
                    "id": "generate_response",
                    "type": "n8n-nodes-base.openAi",
                    "position": [650, 300],
                    "parameters": {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Você é um atendente da {{$env.BUSINESS_CONTEXT}}. Responda de forma amigável e profissional."
                            },
                            {"role": "user", "content": "={{$json.message}}"}
                        ]
                    }
                },
                {
                    "id": "send_reply",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [850, 300],
                    "parameters": {
                        "url": "={{$env.EVOLUTION_API_URL}}/message/sendText/{{$env.WHATSAPP_INSTANCE}}",
                        "method": "POST",
                        "body": {
                            "number": "={{$json.from}}",
                            "text": "={{$node.generate_response.json.message.content}}"
                        }
                    }
                }
            ]
        }
    ),
    
    "ticket_creation": AutomationTemplate(
        id="ticket_creation",
        name="Criação Automática de Tickets",
        description="Cria tickets de suporte automaticamente a partir de mensagens",
        category=AutomationCategory.ATENDIMENTO,
        trigger=AutomationTrigger.WEBHOOK,
        difficulty="beginner",
        estimated_time="10 min",
        tags=["suporte", "tickets", "atendimento"],
        required_integrations=["database"],
        variables=[
            {"name": "DEFAULT_PRIORITY", "description": "Prioridade padrão", "default": "medium"},
        ],
        workflow_json={
            "name": "Criador de Tickets",
            "nodes": [
                {
                    "id": "webhook",
                    "type": "n8n-nodes-base.webhook",
                    "position": [250, 300],
                    "parameters": {"path": "new-ticket", "httpMethod": "POST"}
                },
                {
                    "id": "create_ticket",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 300],
                    "parameters": {
                        "url": "={{$env.API_URL}}/api/v1/tickets",
                        "method": "POST",
                        "body": {
                            "customer_id": "={{$json.customer_id}}",
                            "subject": "={{$json.subject}}",
                            "message": "={{$json.message}}",
                            "priority": "={{$env.DEFAULT_PRIORITY}}",
                            "source": "={{$json.source}}"
                        }
                    }
                },
                {
                    "id": "notify_team",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [650, 300],
                    "parameters": {
                        "url": "={{$env.SLACK_WEBHOOK_URL}}",
                        "method": "POST",
                        "body": {
                            "text": "🎫 Novo ticket criado!\n\n*Assunto:* {{$json.subject}}\n*Cliente:* {{$json.customer_name}}\n*Prioridade:* {{$env.DEFAULT_PRIORITY}}"
                        }
                    }
                }
            ]
        }
    ),
    
    # ===== MONITORAMENTO =====
    "competitor_price_monitor": AutomationTemplate(
        id="competitor_price_monitor",
        name="Monitor de Preços da Concorrência",
        description="Monitora preços de concorrentes e alerta sobre mudanças",
        category=AutomationCategory.MONITORAMENTO,
        trigger=AutomationTrigger.SCHEDULE,
        difficulty="advanced",
        estimated_time="30 min",
        tags=["preços", "concorrência", "monitoramento"],
        required_integrations=["scraper"],
        variables=[
            {"name": "PRICE_CHANGE_THRESHOLD", "description": "Mudança mínima para alertar (%)", "default": "5"},
            {"name": "CHECK_INTERVAL_HOURS", "description": "Intervalo de verificação (horas)", "default": "6"},
        ],
        workflow_json={
            "name": "Monitor de Concorrência",
            "nodes": [
                {
                    "id": "schedule",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "position": [250, 300],
                    "parameters": {
                        "rule": {"interval": [{"field": "hours", "hoursInterval": "={{$env.CHECK_INTERVAL_HOURS}}"}]}
                    }
                },
                {
                    "id": "get_products",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 300],
                    "parameters": {
                        "url": "={{$env.API_URL}}/api/v1/products/monitored",
                        "method": "GET"
                    }
                },
                {
                    "id": "scrape_prices",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [650, 300],
                    "parameters": {
                        "url": "={{$env.API_URL}}/api/v1/scraper/batch",
                        "method": "POST",
                        "body": {"products": "={{$json}}"}
                    }
                },
                {
                    "id": "compare_prices",
                    "type": "n8n-nodes-base.code",
                    "position": [850, 300],
                    "parameters": {
                        "jsCode": """
                            const threshold = parseFloat($env.PRICE_CHANGE_THRESHOLD);
                            const results = [];
                            
                            for (const item of $input.all()) {
                                const oldPrice = item.json.old_price;
                                const newPrice = item.json.new_price;
                                const change = ((newPrice - oldPrice) / oldPrice) * 100;
                                
                                if (Math.abs(change) >= threshold) {
                                    results.push({
                                        ...item.json,
                                        price_change: change.toFixed(2)
                                    });
                                }
                            }
                            
                            return results.map(r => ({json: r}));
                        """
                    }
                },
                {
                    "id": "alert",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [1050, 300],
                    "parameters": {
                        "url": "={{$env.EVOLUTION_API_URL}}/message/sendText/{{$env.WHATSAPP_INSTANCE}}",
                        "method": "POST",
                        "body": {
                            "number": "={{$env.ADMIN_PHONE}}",
                            "text": "📊 *Alerta de Preço Concorrência*\n\n{{$json.product_name}}\nMudança: {{$json.price_change}}%\nNovo preço: R$ {{$json.new_price}}"
                        }
                    }
                }
            ]
        }
    ),
    
    "daily_report": AutomationTemplate(
        id="daily_report",
        name="Relatório Diário Automático",
        description="Envia relatório diário de métricas por WhatsApp/Email",
        category=AutomationCategory.MONITORAMENTO,
        trigger=AutomationTrigger.SCHEDULE,
        difficulty="intermediate",
        estimated_time="20 min",
        tags=["relatórios", "métricas", "analytics"],
        required_integrations=["evolution-api", "smtp"],
        variables=[
            {"name": "REPORT_TIME", "description": "Horário do relatório (HH:MM)", "default": "08:00"},
            {"name": "REPORT_RECIPIENTS", "description": "Destinatários (separados por vírgula)", "default": ""},
        ],
        workflow_json={
            "name": "Relatório Diário",
            "nodes": [
                {
                    "id": "schedule",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "position": [250, 300],
                    "parameters": {
                        "rule": {"interval": [{"field": "cronExpression", "expression": "0 8 * * *"}]}
                    }
                },
                {
                    "id": "get_metrics",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 300],
                    "parameters": {
                        "url": "={{$env.API_URL}}/api/v1/analytics/daily-summary",
                        "method": "GET"
                    }
                },
                {
                    "id": "format_report",
                    "type": "n8n-nodes-base.code",
                    "position": [650, 300],
                    "parameters": {
                        "jsCode": """
                            const metrics = $input.first().json;
                            const today = new Date().toLocaleDateString('pt-BR');
                            
                            const report = '📊 *Relatório Diário - ' + today + '*\\n\\n' +
                                '👥 Novos Leads: ' + metrics.new_leads + '\\n' +
                                '💰 Vendas: R$ ' + metrics.total_sales.toFixed(2) + '\\n' +
                                '📱 Posts Publicados: ' + metrics.posts_published + '\\n' +
                                '👁️ Visualizações: ' + metrics.total_views + '\\n' +
                                '💬 Mensagens: ' + metrics.messages_received + '\\n\\n' +
                                '🏆 Top Produto: ' + metrics.top_product + '\\n' +
                                '📈 Crescimento: ' + metrics.growth_percent + '%';
                            
                            return [{ json: { report: report } }];
                        """
                    }
                },
                {
                    "id": "send_whatsapp",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [850, 300],
                    "parameters": {
                        "url": "={{$env.EVOLUTION_API_URL}}/message/sendText/{{$env.WHATSAPP_INSTANCE}}",
                        "method": "POST",
                        "body": {
                            "number": "={{$env.ADMIN_PHONE}}",
                            "text": "={{$json.report}}"
                        }
                    }
                }
            ]
        }
    ),
    
    # ===== INTEGRAÇÃO =====
    "crm_sync": AutomationTemplate(
        id="crm_sync",
        name="Sincronização com CRM",
        description="Sincroniza leads e contatos com CRM externo",
        category=AutomationCategory.INTEGRACAO,
        trigger=AutomationTrigger.WEBHOOK,
        difficulty="intermediate",
        estimated_time="15 min",
        tags=["crm", "integração", "leads"],
        required_integrations=["database"],
        variables=[
            {"name": "CRM_API_URL", "description": "URL da API do CRM", "default": ""},
            {"name": "CRM_API_KEY", "description": "Chave da API do CRM", "default": ""},
        ],
        workflow_json={
            "name": "Sync CRM",
            "nodes": [
                {
                    "id": "webhook",
                    "type": "n8n-nodes-base.webhook",
                    "position": [250, 300],
                    "parameters": {"path": "sync-crm", "httpMethod": "POST"}
                },
                {
                    "id": "sync_lead",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 300],
                    "parameters": {
                        "url": "={{$env.CRM_API_URL}}/contacts",
                        "method": "POST",
                        "headers": {"Authorization": "Bearer {{$env.CRM_API_KEY}}"},
                        "body": {
                            "name": "={{$json.name}}",
                            "email": "={{$json.email}}",
                            "phone": "={{$json.phone}}",
                            "source": "tiktrend_facil"
                        }
                    }
                }
            ]
        }
    ),
}


def get_automation_templates(
    category: Optional[AutomationCategory] = None,
    difficulty: Optional[str] = None
) -> List[AutomationTemplate]:
    """
    Retorna templates de automação filtrados.
    
    Args:
        category: Filtrar por categoria
        difficulty: Filtrar por dificuldade
    
    Returns:
        Lista de templates
    """
    templates = list(AUTOMATION_TEMPLATES.values())
    
    if category:
        templates = [t for t in templates if t.category == category]
    
    if difficulty:
        templates = [t for t in templates if t.difficulty == difficulty]
    
    return templates


def get_template_by_id(template_id: str) -> Optional[AutomationTemplate]:
    """Retorna template por ID."""
    return AUTOMATION_TEMPLATES.get(template_id)


def export_n8n_workflow(template_id: str, variables: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Exporta workflow n8n pronto para importar.
    
    Args:
        template_id: ID do template
        variables: Variáveis customizadas
    
    Returns:
        JSON do workflow n8n
    """
    template = get_template_by_id(template_id)
    if not template:
        raise ValueError(f"Template não encontrado: {template_id}")
    
    workflow = template.workflow_json.copy()
    
    # Aplicar variáveis customizadas
    if variables:
        workflow_str = json.dumps(workflow)
        for key, value in variables.items():
            workflow_str = workflow_str.replace(f"{{{{$env.{key}}}}}", value)
        workflow = json.loads(workflow_str)
    
    # Adicionar metadados
    workflow["meta"] = {
        "instanceId": "",
        "templateCreatedBy": "tiktrend-facil",
        "templateId": template_id
    }
    
    return workflow
