"""
Template Library Routes
=======================
Endpoints para biblioteca de templates prontos (automação, chatbot, presets).
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from modules.templates import (
    # Automação
    get_automation_templates,
    get_automation_by_id,
    export_n8n_workflow,
    AutomationCategory,
    
    # Chatbot
    get_chatbot_templates,
    get_chatbot_by_id,
    export_typebot_flow,
    ChatbotCategory,
    
    # Conteúdo
    get_content_templates,
    get_content_by_id,
    generate_caption,
    get_weekly_calendar,
    suggest_next_post,
    ContentPlatform,
    ContentType,
    ContentCategory,
    
    # Presets
    get_business_presets,
    get_preset_by_id,
    recommend_preset,
    apply_preset,
    BusinessType,
    BusinessSize,
)

router = APIRouter(prefix="/library", tags=["Template Library"])


# ============================================
# SCHEMAS
# ============================================

class ExportWorkflowRequest(BaseModel):
    template_id: str
    variables: dict = {}
    webhook_url: Optional[str] = None


class ExportChatbotRequest(BaseModel):
    template_id: str
    variables: dict = {}


class GenerateCaptionRequest(BaseModel):
    template_id: str
    variables: dict


class RecommendPresetRequest(BaseModel):
    business_type: str
    monthly_revenue: float = 0
    team_size: int = 1


# ============================================
# AUTOMAÇÃO (N8N WORKFLOWS)
# ============================================

@router.get("/automation")
async def list_automation_templates(
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    difficulty: Optional[str] = Query(None, description="Filtrar por dificuldade")
):
    """
    Lista todos os templates de automação n8n.
    
    Categorias disponíveis:
    - alerts: Alertas e notificações
    - marketing: Marketing e vendas
    - customer_success: Sucesso do cliente
    - operations: Operações
    - analytics: Analytics e relatórios
    """
    category_enum = AutomationCategory(category) if category else None
    templates = get_automation_templates(category=category_enum, difficulty=difficulty)
    
    return {
        "total": len(templates),
        "templates": [t.to_dict() for t in templates],
        "categories": [c.value for c in AutomationCategory],
    }


@router.get("/automation/{template_id}")
async def get_automation_template(template_id: str):
    """
    Retorna detalhes de um template de automação.
    """
    template = get_automation_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    return template.to_dict()


@router.post("/automation/export")
async def export_automation_workflow(request: ExportWorkflowRequest):
    """
    Exporta workflow n8n pronto para importar.
    
    Retorna JSON compatível com n8n para importação direta.
    """
    try:
        workflow = export_n8n_workflow(
            template_id=request.template_id,
            variables=request.variables,
            webhook_url=request.webhook_url
        )
        return {
            "success": True,
            "workflow": workflow,
            "import_instructions": [
                "1. Acesse seu n8n em http://localhost:5678",
                "2. Vá em Settings → Import Workflow",
                "3. Cole o JSON do workflow",
                "4. Configure as credenciais necessárias",
                "5. Ative o workflow"
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# CHATBOT (TYPEBOT FLOWS)
# ============================================

@router.get("/chatbot")
async def list_chatbot_templates(
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    difficulty: Optional[str] = Query(None, description="Filtrar por dificuldade")
):
    """
    Lista todos os templates de chatbot Typebot.
    
    Categorias disponíveis:
    - atendimento: Atendimento ao cliente
    - vendas: Funis de vendas
    - suporte: Suporte técnico
    - qualificacao: Qualificação de leads
    - agendamento: Agendamento de consultas
    - faq: Perguntas frequentes
    """
    category_enum = ChatbotCategory(category) if category else None
    templates = get_chatbot_templates(category=category_enum, difficulty=difficulty)
    
    return {
        "total": len(templates),
        "templates": [t.to_dict() for t in templates],
        "categories": [c.value for c in ChatbotCategory],
    }


@router.get("/chatbot/{template_id}")
async def get_chatbot_template(template_id: str):
    """
    Retorna detalhes de um template de chatbot.
    """
    template = get_chatbot_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    return template.to_dict()


@router.post("/chatbot/export")
async def export_chatbot_flow(request: ExportChatbotRequest):
    """
    Exporta fluxo Typebot pronto para importar.
    """
    try:
        flow = export_typebot_flow(
            template_id=request.template_id,
            variables=request.variables
        )
        return {
            "success": True,
            "flow": flow,
            "import_instructions": [
                "1. Acesse o Typebot",
                "2. Crie um novo bot ou abra existente",
                "3. Vá em Settings → Import",
                "4. Cole o JSON do fluxo",
                "5. Configure as integrações"
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# CONTEÚDO (SOCIAL MEDIA)
# ============================================

@router.get("/content")
async def list_content_templates(
    platform: Optional[str] = Query(None, description="Filtrar por plataforma"),
    content_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    category: Optional[str] = Query(None, description="Filtrar por categoria")
):
    """
    Lista todos os templates de conteúdo para redes sociais.
    
    Plataformas: instagram, tiktok, youtube, whatsapp, all
    Tipos: post, reels, story, carousel, video, shorts
    Categorias: promo, educacional, engajamento, lancamento, social_proof, bastidores
    """
    platform_enum = ContentPlatform(platform) if platform else None
    type_enum = ContentType(content_type) if content_type else None
    category_enum = ContentCategory(category) if category else None
    
    templates = get_content_templates(
        platform=platform_enum,
        content_type=type_enum,
        category=category_enum
    )
    
    return {
        "total": len(templates),
        "templates": [t.to_dict() for t in templates],
        "platforms": [p.value for p in ContentPlatform],
        "types": [t.value for t in ContentType],
        "categories": [c.value for c in ContentCategory],
    }


@router.get("/content/{template_id}")
async def get_content_template(template_id: str):
    """
    Retorna detalhes de um template de conteúdo.
    """
    template = get_content_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    return template.to_dict()


@router.post("/content/generate-caption")
async def generate_content_caption(request: GenerateCaptionRequest):
    """
    Gera legenda com variáveis preenchidas.
    """
    try:
        caption = generate_caption(
            template_id=request.template_id,
            variables=request.variables
        )
        
        template = get_content_by_id(request.template_id)
        
        return {
            "success": True,
            "caption": caption,
            "hashtags": template.hashtags if template else [],
            "best_posting_times": template.best_posting_times if template else [],
            "visual_tips": template.visual_tips if template else [],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/content/calendar")
async def get_content_calendar():
    """
    Retorna calendário semanal de conteúdo sugerido.
    """
    calendar = get_weekly_calendar()
    return {
        "calendar": calendar,
        "description": "Sugestão de posts para cada dia da semana",
        "tips": [
            "Segunda: Comece a semana com conteúdo educacional",
            "Terça/Quinta: Dias bons para engajamento",
            "Quarta/Sexta: Promoções funcionam bem",
            "Sábado: Reviews e conteúdo longo",
            "Domingo: Conteúdo leve e reflexivo"
        ]
    }


@router.get("/content/suggest-next")
async def suggest_next_content(
    last_post_type: Optional[str] = Query(None, description="ID do último post")
):
    """
    Sugere próximo tipo de conteúdo a postar.
    """
    template = suggest_next_post(last_post_type)
    return {
        "suggestion": template.to_dict(),
        "reason": f"Baseado em diversificação de conteúdo e engajamento estimado: {template.estimated_engagement}"
    }


# ============================================
# PRESETS DE NEGÓCIO
# ============================================

@router.get("/presets")
async def list_business_presets(
    business_type: Optional[str] = Query(None, description="Filtrar por tipo de negócio"),
    business_size: Optional[str] = Query(None, description="Filtrar por tamanho")
):
    """
    Lista todos os presets de configuração por tipo de negócio.
    
    Tipos: ecommerce, infoprodutos, servicos, saas, varejo, alimentacao, saude, educacao, moda, tecnologia
    Tamanhos: solo (1), micro (2-10), small (11-50), medium (51-200), large (200+)
    """
    type_enum = BusinessType(business_type) if business_type else None
    size_enum = BusinessSize(business_size) if business_size else None
    
    presets = get_business_presets(business_type=type_enum, business_size=size_enum)
    
    return {
        "total": len(presets),
        "presets": [p.to_dict() for p in presets],
        "business_types": [t.value for t in BusinessType],
        "business_sizes": [s.value for s in BusinessSize],
    }


@router.get("/presets/{preset_id}")
async def get_business_preset(preset_id: str):
    """
    Retorna detalhes de um preset de negócio.
    """
    preset = get_preset_by_id(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset não encontrado")
    
    return preset.to_dict()


@router.post("/presets/recommend")
async def recommend_business_preset(request: RecommendPresetRequest):
    """
    Recomenda o melhor preset baseado no perfil do negócio.
    """
    try:
        business_type = BusinessType(request.business_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de negócio inválido. Opções: {[t.value for t in BusinessType]}"
        )
    
    preset = recommend_preset(
        business_type=business_type,
        monthly_revenue=request.monthly_revenue,
        team_size=request.team_size
    )
    
    if not preset:
        raise HTTPException(status_code=404, detail="Nenhum preset encontrado para este perfil")
    
    return {
        "recommendation": preset.to_dict(),
        "reason": f"Melhor fit para {business_type.value} com equipe de {request.team_size} pessoa(s)"
    }


@router.post("/presets/{preset_id}/apply")
async def apply_business_preset(preset_id: str):
    """
    Retorna guia completo para aplicar um preset.
    
    Inclui:
    - Lista de automações a configurar
    - Chatbots recomendados
    - Templates de conteúdo
    - Configurações específicas
    - Métricas alvo
    - Tempo estimado de setup
    """
    try:
        setup = apply_preset(preset_id)
        return {
            "success": True,
            **setup
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# ESTATÍSTICAS
# ============================================

@router.get("/stats")
async def get_library_stats():
    """
    Retorna estatísticas gerais da biblioteca de templates.
    """
    automation_templates = get_automation_templates()
    chatbot_templates = get_chatbot_templates()
    content_templates = get_content_templates()
    business_presets = get_business_presets()
    
    return {
        "summary": {
            "total_templates": (
                len(automation_templates) + 
                len(chatbot_templates) + 
                len(content_templates) +
                len(business_presets)
            ),
            "automation_workflows": len(automation_templates),
            "chatbot_flows": len(chatbot_templates),
            "content_templates": len(content_templates),
            "business_presets": len(business_presets),
        },
        "automation": {
            "total": len(automation_templates),
            "by_category": {
                cat.value: len([t for t in automation_templates if t.category == cat])
                for cat in AutomationCategory
            }
        },
        "chatbot": {
            "total": len(chatbot_templates),
            "by_category": {
                cat.value: len([t for t in chatbot_templates if t.category == cat])
                for cat in ChatbotCategory
            }
        },
        "content": {
            "total": len(content_templates),
            "by_platform": {
                plat.value: len([t for t in content_templates if t.platform == plat])
                for plat in ContentPlatform
            },
            "by_type": {
                typ.value: len([t for t in content_templates if t.content_type == typ])
                for typ in ContentType
            }
        },
        "presets": {
            "total": len(business_presets),
            "by_type": {
                typ.value: len([p for p in business_presets if p.business_type == typ])
                for typ in BusinessType
            }
        }
    }
