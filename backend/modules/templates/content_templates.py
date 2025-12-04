"""
Content Templates
=================
Templates de conteúdo para redes sociais (Instagram, TikTok, YouTube).
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid


class ContentPlatform(str, Enum):
    """Plataformas suportadas."""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    WHATSAPP = "whatsapp"
    ALL = "all"


class ContentType(str, Enum):
    """Tipos de conteúdo."""
    POST = "post"
    REELS = "reels"
    STORY = "story"
    CAROUSEL = "carousel"
    VIDEO = "video"
    SHORTS = "shorts"


class ContentCategory(str, Enum):
    """Categorias de conteúdo."""
    PROMO = "promo"
    EDUCACIONAL = "educacional"
    ENGAJAMENTO = "engajamento"
    LANCAMENTO = "lancamento"
    SOCIAL_PROOF = "social_proof"
    BASTIDORES = "bastidores"


@dataclass
class ContentTemplate:
    """Template de conteúdo para redes sociais."""
    id: str
    name: str
    description: str
    platform: ContentPlatform
    content_type: ContentType
    category: ContentCategory
    
    # Conteúdo
    caption_template: str
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    
    # Visual
    recommended_dimensions: Dict[str, int] = field(default_factory=dict)
    visual_tips: List[str] = field(default_factory=list)
    color_scheme: Dict[str, str] = field(default_factory=dict)
    
    # Mídia
    media_type: str = "image"  # image, video, carousel
    duration_seconds: Optional[int] = None
    
    # Variáveis
    variables: List[Dict[str, str]] = field(default_factory=list)
    
    # Metadados
    estimated_engagement: str = ""
    best_posting_times: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "platform": self.platform.value,
            "content_type": self.content_type.value,
            "category": self.category.value,
            "caption_template": self.caption_template,
            "hashtags": self.hashtags,
            "mentions": self.mentions,
            "recommended_dimensions": self.recommended_dimensions,
            "visual_tips": self.visual_tips,
            "media_type": self.media_type,
            "variables": self.variables,
            "estimated_engagement": self.estimated_engagement,
            "best_posting_times": self.best_posting_times,
        }


# ============================================
# TEMPLATES DE CONTEÚDO
# ============================================

CONTENT_TEMPLATES: Dict[str, ContentTemplate] = {
    
    # ===== PROMOÇÕES =====
    "flash_sale": ContentTemplate(
        id="flash_sale",
        name="Promoção Relâmpago",
        description="Post de promoção com urgência e FOMO",
        platform=ContentPlatform.ALL,
        content_type=ContentType.POST,
        category=ContentCategory.PROMO,
        caption_template="""🔥 PROMOÇÃO RELÂMPAGO! 🔥

⚡ {{product_name}} com {{discount_percent}}% OFF!

De R$ {{original_price}} por apenas R$ {{sale_price}}

⏰ SÓ {{hours_remaining}} HORAS para aproveitar!

Link na bio 👆 ou arraste pra cima!

#PromoçãoRelâmpago #Desconto #OfertaImperdível #{{category}}""",
        hashtags=[
            "#promoção", "#desconto", "#oferta", "#economia",
            "#compras", "#blackfriday", "#sale", "#outlet"
        ],
        recommended_dimensions={"width": 1080, "height": 1080},
        visual_tips=[
            "Use cores vibrantes (vermelho/amarelo) para urgência",
            "Destaque o percentual de desconto em tamanho grande",
            "Inclua timer ou contagem regressiva visual",
            "Mostre o produto com tag de preço riscado"
        ],
        color_scheme={"primary": "#FF0000", "secondary": "#FFD700", "text": "#FFFFFF"},
        variables=[
            {"name": "product_name", "description": "Nome do produto"},
            {"name": "discount_percent", "description": "Percentual de desconto"},
            {"name": "original_price", "description": "Preço original"},
            {"name": "sale_price", "description": "Preço promocional"},
            {"name": "hours_remaining", "description": "Horas restantes"},
            {"name": "category", "description": "Categoria do produto"}
        ],
        estimated_engagement="Alto - posts de urgência têm 2-3x mais engajamento",
        best_posting_times=["12:00", "18:00", "21:00"]
    ),
    
    "price_drop_alert": ContentTemplate(
        id="price_drop_alert",
        name="Alerta de Queda de Preço",
        description="Aviso de produto que baixou de preço",
        platform=ContentPlatform.INSTAGRAM,
        content_type=ContentType.REELS,
        category=ContentCategory.PROMO,
        caption_template="""🚨 CAIU O PREÇO! 🚨

{{product_name}} que você ama estava R$ {{old_price}}...

AGORA: R$ {{new_price}}! 🤯

💰 Economia de R$ {{savings}}!

Quer receber alertas assim? Link na bio!

#QuedaDePreço #Economia #ComparaçãoDePreços #Oferta""",
        hashtags=[
            "#quedadepreço", "#economia", "#alerta", "#oferta",
            "#comprasinteligentes", "#dica", "#promoção"
        ],
        recommended_dimensions={"width": 1080, "height": 1920},
        visual_tips=[
            "Use gráfico mostrando a queda de preço",
            "Animação de preço caindo",
            "Som de 'cha-ching' ou notificação",
            "Transição rápida entre preços"
        ],
        media_type="video",
        duration_seconds=15,
        variables=[
            {"name": "product_name", "description": "Nome do produto"},
            {"name": "old_price", "description": "Preço anterior"},
            {"name": "new_price", "description": "Preço atual"},
            {"name": "savings", "description": "Valor economizado"}
        ],
        estimated_engagement="Muito Alto - formato reels + preço = viral potential",
        best_posting_times=["11:00", "14:00", "20:00"]
    ),
    
    "daily_deals": ContentTemplate(
        id="daily_deals",
        name="Ofertas do Dia",
        description="Compilado das melhores ofertas diárias",
        platform=ContentPlatform.INSTAGRAM,
        content_type=ContentType.CAROUSEL,
        category=ContentCategory.PROMO,
        caption_template="""📱 OFERTAS DO DIA {{date}} 📱

Slide 1: {{deal_1_name}} - R$ {{deal_1_price}} ⬇️
Slide 2: {{deal_2_name}} - R$ {{deal_2_price}} ⬇️
Slide 3: {{deal_3_name}} - R$ {{deal_3_price}} ⬇️

💡 Todas verificadas e no menor preço!

Qual você vai garantir? 👇

#OfertasDoDia #Economia #MenorPreço #Comparação""",
        hashtags=[
            "#ofertasdodia", "#deals", "#promocao", "#economia",
            "#tiktrendfinder", "#comparacao", "#precos"
        ],
        recommended_dimensions={"width": 1080, "height": 1350},
        visual_tips=[
            "Use layout consistente em todos os slides",
            "Inclua foto do produto + preço destacado",
            "Último slide com CTA para link na bio",
            "Use numeração nos slides (1/5, 2/5...)"
        ],
        media_type="carousel",
        variables=[
            {"name": "date", "description": "Data (ex: 26/11)"},
            {"name": "deal_1_name", "description": "Nome oferta 1"},
            {"name": "deal_1_price", "description": "Preço oferta 1"},
            {"name": "deal_2_name", "description": "Nome oferta 2"},
            {"name": "deal_2_price", "description": "Preço oferta 2"},
            {"name": "deal_3_name", "description": "Nome oferta 3"},
            {"name": "deal_3_price", "description": "Preço oferta 3"}
        ],
        estimated_engagement="Médio-Alto - carrosséis têm 1.4x mais alcance",
        best_posting_times=["07:00", "12:00", "19:00"]
    ),
    
    # ===== EDUCACIONAL =====
    "price_comparison_tip": ContentTemplate(
        id="price_comparison_tip",
        name="Dica de Economia",
        description="Conteúdo educacional sobre comparação de preços",
        platform=ContentPlatform.ALL,
        content_type=ContentType.REELS,
        category=ContentCategory.EDUCACIONAL,
        caption_template="""💡 DICA DE OURO PARA ECONOMIZAR! 💡

{{tip_title}}

{{tip_content}}

🎯 Resultado: {{expected_savings}}% de economia!

Salva pra não esquecer! 📌

#DicaDeEconomia #EducaçãoFinanceira #Economia""",
        hashtags=[
            "#dicadeeconomia", "#finanças", "#educacaofinanceira",
            "#comprasinteligentes", "#economia", "#dicas"
        ],
        recommended_dimensions={"width": 1080, "height": 1920},
        visual_tips=[
            "Comece com hook nos primeiros 3 segundos",
            "Use texto grande e legível",
            "Inclua exemplos visuais",
            "Termine com CTA claro"
        ],
        media_type="video",
        duration_seconds=30,
        variables=[
            {"name": "tip_title", "description": "Título da dica"},
            {"name": "tip_content", "description": "Conteúdo da dica"},
            {"name": "expected_savings", "description": "% economia esperada"}
        ],
        estimated_engagement="Alto - conteúdo educacional gera saves",
        best_posting_times=["09:00", "17:00", "21:00"]
    ),
    
    "product_review": ContentTemplate(
        id="product_review",
        name="Review de Produto",
        description="Análise completa de produto comparando preços",
        platform=ContentPlatform.YOUTUBE,
        content_type=ContentType.VIDEO,
        category=ContentCategory.EDUCACIONAL,
        caption_template="""{{product_name}} - VALE A PENA? 🤔

Neste vídeo analiso:
✅ Especificações técnicas
✅ Prós e contras
✅ Comparação de preços em {{num_stores}} lojas
✅ Onde está mais barato HOJE

Menor preço encontrado: R$ {{lowest_price}} na {{store_name}}!

🔔 Ative o sininho para mais análises!

#Review #Análise #ComparaçãoDePreços #{{category}}

⏱️ Timestamps:
0:00 - Introdução
{{timestamps}}""",
        hashtags=[
            "#review", "#analise", "#unboxing", "#tecologia",
            "#comparacao", "#dica", "#compra"
        ],
        recommended_dimensions={"width": 1920, "height": 1080},
        visual_tips=[
            "Thumbnail com produto + preço + expressão facial",
            "Inclua tabela de preços visual",
            "Mostre o produto em uso",
            "B-roll de qualidade"
        ],
        media_type="video",
        duration_seconds=600,
        variables=[
            {"name": "product_name", "description": "Nome do produto"},
            {"name": "num_stores", "description": "Número de lojas comparadas"},
            {"name": "lowest_price", "description": "Menor preço"},
            {"name": "store_name", "description": "Loja com menor preço"},
            {"name": "category", "description": "Categoria"},
            {"name": "timestamps", "description": "Timestamps do vídeo"}
        ],
        estimated_engagement="Médio - vídeos longos têm watch time maior",
        best_posting_times=["10:00", "15:00", "20:00"]
    ),
    
    # ===== ENGAJAMENTO =====
    "poll_post": ContentTemplate(
        id="poll_post",
        name="Enquete de Produtos",
        description="Post interativo com enquete entre produtos",
        platform=ContentPlatform.INSTAGRAM,
        content_type=ContentType.STORY,
        category=ContentCategory.ENGAJAMENTO,
        caption_template="""QUAL VOCÊ PREFERE? 🤔

A: {{product_a_name}}
R$ {{product_a_price}}

ou

B: {{product_b_name}}
R$ {{product_b_price}}

Vota aí! 👆""",
        hashtags=[],
        recommended_dimensions={"width": 1080, "height": 1920},
        visual_tips=[
            "Divida a tela ao meio",
            "Use cores contrastantes para A e B",
            "Adicione sticker de enquete",
            "Mostre os produtos lado a lado"
        ],
        media_type="image",
        variables=[
            {"name": "product_a_name", "description": "Nome produto A"},
            {"name": "product_a_price", "description": "Preço produto A"},
            {"name": "product_b_name", "description": "Nome produto B"},
            {"name": "product_b_price", "description": "Preço produto B"}
        ],
        estimated_engagement="Muito Alto - enquetes têm 20-40% de participação",
        best_posting_times=["11:00", "15:00", "20:00"]
    ),
    
    "question_post": ContentTemplate(
        id="question_post",
        name="Caixa de Perguntas",
        description="Story para responder dúvidas da audiência",
        platform=ContentPlatform.INSTAGRAM,
        content_type=ContentType.STORY,
        category=ContentCategory.ENGAJAMENTO,
        caption_template="""❓ HORA DE TIRAR DÚVIDAS! ❓

{{topic}}

Manda sua pergunta que eu respondo! 👇

Use a caixinha de perguntas ⬆️""",
        hashtags=[],
        recommended_dimensions={"width": 1080, "height": 1920},
        visual_tips=[
            "Fundo simples e limpo",
            "Destaque a caixa de perguntas",
            "Use foto sua ou mascote",
            "Cor vibrante de destaque"
        ],
        media_type="image",
        variables=[
            {"name": "topic", "description": "Tema das perguntas (ex: 'Dúvidas sobre comparação de preços')"}
        ],
        estimated_engagement="Alto - interações diretas aumentam alcance",
        best_posting_times=["14:00", "21:00"]
    ),
    
    "user_testimonial": ContentTemplate(
        id="user_testimonial",
        name="Depoimento de Usuário",
        description="Post com prova social de economia real",
        platform=ContentPlatform.ALL,
        content_type=ContentType.POST,
        category=ContentCategory.SOCIAL_PROOF,
        caption_template="""📣 OLHA O QUE O {{user_name}} CONSEGUIU! 📣

"{{testimonial_text}}"

💰 Economizou R$ {{savings}} usando o TikTrend Finder!

Quer economizar também? Link na bio! 👆

#Economia #Depoimento #ClienteFeliz #TikTrendFinder""",
        hashtags=[
            "#economia", "#depoimento", "#clientefeliz", "#prova",
            "#resultado", "#economizei", "#recomendo"
        ],
        recommended_dimensions={"width": 1080, "height": 1350},
        visual_tips=[
            "Use foto real do usuário (com permissão)",
            "Destaque o valor economizado",
            "Design limpo e profissional",
            "Inclua aspas no depoimento"
        ],
        media_type="image",
        variables=[
            {"name": "user_name", "description": "Nome do usuário"},
            {"name": "testimonial_text", "description": "Texto do depoimento"},
            {"name": "savings", "description": "Valor economizado"}
        ],
        estimated_engagement="Alto - prova social gera confiança",
        best_posting_times=["10:00", "14:00", "19:00"]
    ),
    
    # ===== LANÇAMENTO =====
    "new_feature": ContentTemplate(
        id="new_feature",
        name="Lançamento de Feature",
        description="Anúncio de nova funcionalidade do app",
        platform=ContentPlatform.ALL,
        content_type=ContentType.REELS,
        category=ContentCategory.LANCAMENTO,
        caption_template="""🎉 NOVIDADE NO APP! 🎉

{{feature_name}} já está disponível!

{{feature_description}}

Como usar:
1️⃣ {{step_1}}
2️⃣ {{step_2}}
3️⃣ {{step_3}}

Atualiza o app e testa agora! 📱

#Novidade #Update #Feature #TikTrendFinder""",
        hashtags=[
            "#novidade", "#update", "#app", "#funcionalidade",
            "#lancamento", "#novo", "#tecnologia"
        ],
        recommended_dimensions={"width": 1080, "height": 1920},
        visual_tips=[
            "Screencast do app funcionando",
            "Animação de reveal",
            "Música de celebração",
            "Destaque visual da nova feature"
        ],
        media_type="video",
        duration_seconds=20,
        variables=[
            {"name": "feature_name", "description": "Nome da feature"},
            {"name": "feature_description", "description": "Descrição breve"},
            {"name": "step_1", "description": "Passo 1"},
            {"name": "step_2", "description": "Passo 2"},
            {"name": "step_3", "description": "Passo 3"}
        ],
        estimated_engagement="Médio - atualizações geram interesse dos usuários ativos",
        best_posting_times=["10:00", "18:00"]
    ),
    
    # ===== BASTIDORES =====
    "behind_scenes": ContentTemplate(
        id="behind_scenes",
        name="Bastidores",
        description="Conteúdo mostrando como o app funciona por trás",
        platform=ContentPlatform.INSTAGRAM,
        content_type=ContentType.STORY,
        category=ContentCategory.BASTIDORES,
        caption_template="""👀 BASTIDORES DO DIDIN! 👀

{{scene_description}}

{{fun_fact}}

#Bastidores #ComoFunciona #Tech #Startup""",
        hashtags=[
            "#bastidores", "#behindthescenes", "#tech", "#startup",
            "#developer", "#coding", "#equipe"
        ],
        recommended_dimensions={"width": 1080, "height": 1920},
        visual_tips=[
            "Conteúdo autêntico e casual",
            "Mostre pessoas reais da equipe",
            "Ambiente de trabalho",
            "Momentos divertidos"
        ],
        media_type="video",
        duration_seconds=15,
        variables=[
            {"name": "scene_description", "description": "O que está acontecendo"},
            {"name": "fun_fact", "description": "Fato curioso sobre a cena"}
        ],
        estimated_engagement="Médio - humaniza a marca",
        best_posting_times=["11:00", "16:00", "22:00"]
    ),
    
    # ===== TIKTOK ESPECÍFICO =====
    "tiktok_trend": ContentTemplate(
        id="tiktok_trend",
        name="Trend TikTok Adaptada",
        description="Template para adaptar trends virais ao nicho",
        platform=ContentPlatform.TIKTOK,
        content_type=ContentType.VIDEO,
        category=ContentCategory.ENGAJAMENTO,
        caption_template="""{{trend_hook}}

{{content_adaptation}}

#{{trend_hashtag}} #Economia #fyp #viral""",
        hashtags=[
            "#fyp", "#foryou", "#parati", "#viral",
            "#economia", "#dica", "#trend"
        ],
        recommended_dimensions={"width": 1080, "height": 1920},
        visual_tips=[
            "Siga a estrutura exata da trend",
            "Adapte para seu nicho",
            "Use o áudio original da trend",
            "Primeiros 3 segundos são cruciais"
        ],
        media_type="video",
        duration_seconds=15,
        variables=[
            {"name": "trend_hook", "description": "Hook baseado na trend"},
            {"name": "content_adaptation", "description": "Conteúdo adaptado"},
            {"name": "trend_hashtag", "description": "Hashtag da trend"}
        ],
        estimated_engagement="Muito Alto - trends têm potencial viral",
        best_posting_times=["12:00", "19:00", "22:00"]
    ),
}


# ============================================
# CALENDÁRIO DE CONTEÚDO
# ============================================

CONTENT_CALENDAR_TEMPLATE = {
    "monday": [
        {"time": "09:00", "template": "price_comparison_tip", "platform": "instagram"},
        {"time": "12:00", "template": "flash_sale", "platform": "all"},
    ],
    "tuesday": [
        {"time": "10:00", "template": "poll_post", "platform": "instagram"},
        {"time": "15:00", "template": "tiktok_trend", "platform": "tiktok"},
    ],
    "wednesday": [
        {"time": "09:00", "template": "daily_deals", "platform": "instagram"},
        {"time": "18:00", "template": "behind_scenes", "platform": "instagram"},
    ],
    "thursday": [
        {"time": "12:00", "template": "user_testimonial", "platform": "all"},
        {"time": "20:00", "template": "question_post", "platform": "instagram"},
    ],
    "friday": [
        {"time": "10:00", "template": "price_drop_alert", "platform": "instagram"},
        {"time": "14:00", "template": "flash_sale", "platform": "all"},
    ],
    "saturday": [
        {"time": "11:00", "template": "product_review", "platform": "youtube"},
        {"time": "15:00", "template": "tiktok_trend", "platform": "tiktok"},
    ],
    "sunday": [
        {"time": "10:00", "template": "price_comparison_tip", "platform": "all"},
        {"time": "19:00", "template": "daily_deals", "platform": "instagram"},
    ],
}


def get_content_templates(
    platform: Optional[ContentPlatform] = None,
    content_type: Optional[ContentType] = None,
    category: Optional[ContentCategory] = None
) -> List[ContentTemplate]:
    """
    Retorna templates de conteúdo filtrados.
    """
    templates = list(CONTENT_TEMPLATES.values())
    
    if platform and platform != ContentPlatform.ALL:
        templates = [t for t in templates if t.platform in [platform, ContentPlatform.ALL]]
    
    if content_type:
        templates = [t for t in templates if t.content_type == content_type]
    
    if category:
        templates = [t for t in templates if t.category == category]
    
    return templates


def get_content_by_id(template_id: str) -> Optional[ContentTemplate]:
    """Retorna template por ID."""
    return CONTENT_TEMPLATES.get(template_id)


def generate_caption(template_id: str, variables: Dict[str, str]) -> str:
    """
    Gera legenda com variáveis substituídas.
    """
    template = get_content_by_id(template_id)
    if not template:
        raise ValueError(f"Template não encontrado: {template_id}")
    
    caption = template.caption_template
    for key, value in variables.items():
        caption = caption.replace(f"{{{{{key}}}}}", str(value))
    
    return caption


def get_weekly_calendar() -> Dict[str, List[Dict[str, Any]]]:
    """
    Retorna calendário semanal de conteúdo.
    """
    return CONTENT_CALENDAR_TEMPLATE


def suggest_next_post(last_post_type: str = None) -> ContentTemplate:
    """
    Sugere próximo tipo de post baseado no último publicado.
    """
    import random
    
    # Evitar repetição
    templates = list(CONTENT_TEMPLATES.values())
    if last_post_type:
        templates = [t for t in templates if t.id != last_post_type]
    
    # Pesos por categoria (para balanceamento)
    weights = {
        ContentCategory.PROMO: 3,
        ContentCategory.EDUCACIONAL: 2,
        ContentCategory.ENGAJAMENTO: 2,
        ContentCategory.SOCIAL_PROOF: 2,
        ContentCategory.LANCAMENTO: 1,
        ContentCategory.BASTIDORES: 1,
    }
    
    weighted_templates = []
    for template in templates:
        weight = weights.get(template.category, 1)
        weighted_templates.extend([template] * weight)
    
    return random.choice(weighted_templates)
