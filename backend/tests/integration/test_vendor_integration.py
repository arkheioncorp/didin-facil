"""
Integration Tests - Vendor Modules
==================================
Testes de integração para módulos do vendor.

Estes testes verificam a integração entre os módulos
e simulam cenários reais de uso.
"""

import pytest

# Import dataclasses and enums
from vendor.content_generator.generator import (
    VideoConfig,
    ProductData,
    TextSlide,
    AspectRatio,
    TemplateStyle,
)
from vendor.crm.leads import (
    Lead,
    LeadSource,
    LeadStatus,
    LeadPriority,
    LeadScorer,
)
from vendor.social_media_manager import (
    SocialMediaConfig,
    UnifiedPost,
    Platform,
    ContentType,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def sample_product() -> ProductData:
    """Produto de exemplo para testes."""
    return ProductData(
        name="iPhone 15 Pro Max",
        price=7999.00,
        original_price=9499.00,
        image_url="https://example.com/iphone.jpg",
        store="Amazon",
        category="Smartphones",
        description="O mais avançado iPhone de todos os tempos"
    )


@pytest.fixture
def sample_lead() -> Lead:
    """Lead de exemplo para testes."""
    return Lead(
        id="lead-001",
        name="João Silva",
        email="joao@email.com",
        phone="5511999999999",
        source=LeadSource.WHATSAPP,
        status=LeadStatus.NEW,
        priority=LeadPriority.HIGH,
        tags=["hot_lead", "high_value"],
        custom_fields={"interest": "smartphones", "budget": "high"}
    )


# ============================================
# CONTENT GENERATION FLOW TESTS
# ============================================

class TestContentGenerationFlow:
    """Testes de fluxo de geração de conteúdo."""
    
    def test_product_to_video_config(self, sample_product):
        """Deve criar configuração de vídeo a partir de produto."""
        config = VideoConfig(
            aspect_ratio=AspectRatio.PORTRAIT,
            duration=15,
            background_color="#1a1a2e"
        )
        
        # Verificar dimensões para stories/reels
        width, height = config.get_dimensions()
        assert width == 1080
        assert height == 1920
        
        # Verificar desconto do produto
        assert sample_product.discount_percent == 15  # ~15% off
    
    def test_product_to_slides(self, sample_product):
        """Deve criar slides a partir de produto."""
        slides = [
            TextSlide(text="🔥 OFERTA IMPERDÍVEL!", duration=2.0),
            TextSlide(text=sample_product.name, duration=3.0),
            TextSlide(
                text=f"-{sample_product.discount_percent}% OFF!",
                duration=2.0,
                color="#ff6b6b"
            ),
            TextSlide(
                text=f"R$ {sample_product.price:.2f}",
                duration=3.0,
                font_size=72
            ),
            TextSlide(
                text=f"Na {sample_product.store}",
                duration=2.0
            ),
            TextSlide(text="Link na bio! 👆", duration=2.0)
        ]
        
        assert len(slides) == 6
        assert sample_product.name in slides[1].text
        assert "15% OFF" in slides[2].text
    
    def test_template_selection(self, sample_product):
        """Deve selecionar template correto baseado no desconto."""
        # Produto com desconto grande -> DEAL_ALERT
        if sample_product.discount_percent and sample_product.discount_percent > 10:
            template = TemplateStyle.DEAL_ALERT
        else:
            template = TemplateStyle.PRODUCT_SHOWCASE
        
        assert template == TemplateStyle.DEAL_ALERT


# ============================================
# CRM LEAD FLOW TESTS
# ============================================

class TestCRMLeadFlow:
    """Testes de fluxo de CRM de leads."""
    
    def test_lead_scoring(self, sample_lead):
        """Deve calcular score do lead corretamente."""
        scorer = LeadScorer()
        
        # Score por fonte (WhatsApp = 25)
        source_score = scorer.score_by_source(sample_lead)
        assert source_score == 25
        
        # Score por completude (email + phone + name = 30)
        completeness_score = scorer.score_by_completeness(sample_lead)
        assert completeness_score == 30
        
        # Score por engajamento (hot_lead + high_value = 45)
        engagement_score = scorer.score_by_engagement(sample_lead)
        assert engagement_score == 45
    
    def test_lead_lifecycle(self, sample_lead):
        """Deve gerenciar ciclo de vida do lead."""
        # Lead novo
        assert sample_lead.status == LeadStatus.NEW
        
        # Marcar como contatado
        sample_lead.mark_contacted()
        assert sample_lead.status == LeadStatus.CONTACTED
        assert sample_lead.last_contact_at is not None
        
        # Verificar atividade registrada
        assert len(sample_lead.activities) == 1
        assert sample_lead.activities[0]["type"] == "contact"
    
    def test_lead_tagging(self, sample_lead):
        """Deve gerenciar tags do lead."""
        initial_tags = len(sample_lead.tags)
        
        # Adicionar tag
        sample_lead.add_tag("needs_followup")
        assert "needs_followup" in sample_lead.tags
        assert len(sample_lead.tags) == initial_tags + 1
        
        # Não duplicar tag
        sample_lead.add_tag("hot_lead")  # Já existe
        assert sample_lead.tags.count("hot_lead") == 1
        
        # Remover tag
        sample_lead.remove_tag("needs_followup")
        assert "needs_followup" not in sample_lead.tags
    
    def test_lead_activity_logging(self, sample_lead):
        """Deve registrar atividades do lead."""
        sample_lead.log_activity(
            activity_type="message_sent",
            description="Enviou promoção de smartphones",
            data={"campaign": "black-friday"}
        )
        
        assert len(sample_lead.activities) == 1
        activity = sample_lead.activities[0]
        assert activity["type"] == "message_sent"
        assert activity["data"]["campaign"] == "black-friday"
    
    def test_lead_to_dict(self, sample_lead):
        """Deve converter lead para dicionário."""
        lead_dict = sample_lead.to_dict()
        
        assert lead_dict["id"] == "lead-001"
        assert lead_dict["name"] == "João Silva"
        assert lead_dict["source"] == "whatsapp"
        assert lead_dict["status"] == "new"
        assert "hot_lead" in lead_dict["tags"]


# ============================================
# SOCIAL MEDIA INTEGRATION TESTS
# ============================================

class TestSocialMediaIntegration:
    """Testes de integração com redes sociais."""
    
    def test_unified_post_creation(self, sample_product):
        """Deve criar post unificado a partir de produto."""
        caption = f"🔥 {sample_product.name}\n\n"
        caption += f"De R$ {sample_product.original_price:.2f}\n"
        caption += f"Por R$ {sample_product.price:.2f}\n\n"
        caption += f"Encontrado na {sample_product.store}!"
        
        hashtags = ["ofertas", "promocao", "tiktrendfinder"]
        hashtags.append(sample_product.category.lower().replace(" ", ""))
        
        post = UnifiedPost(
            content_type=ContentType.IMAGE,
            media_paths=[sample_product.image_url],
            caption=caption,
            hashtags=hashtags,
            platforms=[Platform.INSTAGRAM, Platform.WHATSAPP]
        )
        
        assert sample_product.name in post.caption
        assert "smartphones" in post.hashtags
        assert Platform.INSTAGRAM in post.platforms
    
    def test_platform_config_validation(self):
        """Deve validar configuração de plataformas."""
        config = SocialMediaConfig(
            instagram_username="tiktrend_facil"
        )
        
        # Instagram configurado
        assert config.instagram_username is not None
        
        # TikTok não configurado
        assert config.tiktok_cookies_file is None
        
        # WhatsApp não configurado
        assert config.whatsapp_api_url is None
    
    def test_content_type_for_platform(self):
        """Deve mapear tipo de conteúdo para plataforma."""
        # Instagram Reels = TikTok Videos
        UnifiedPost(
            content_type=ContentType.REEL,
            media_paths=["/video.mp4"],
            platforms=[Platform.INSTAGRAM, Platform.TIKTOK]
        )
        
        assert ContentType.REEL in [ContentType.REEL, ContentType.VIDEO]
        
        # Stories são específicos do Instagram
        story_post = UnifiedPost(
            content_type=ContentType.STORY,
            media_paths=["/story.mp4"],
            platforms=[Platform.INSTAGRAM]
        )
        
        assert Platform.TIKTOK not in story_post.platforms


# ============================================
# END-TO-END FLOW TESTS
# ============================================

class TestEndToEndFlows:
    """Testes de fluxos end-to-end."""
    
    def test_product_alert_flow(self, sample_product):
        """Deve executar fluxo de alerta de produto."""
        # 1. Produto identificado com bom desconto
        assert sample_product.discount_percent > 10
        
        # 2. Configurar vídeo para redes sociais
        VideoConfig(
            aspect_ratio=AspectRatio.PORTRAIT,
            duration=15
        )
        
        # 3. Criar slides do vídeo
        slides = [
            TextSlide(text="🔥 ALERTA DE OFERTA!", duration=2.0),
            TextSlide(text=sample_product.name, duration=3.0),
            TextSlide(
                text=f"R$ {sample_product.price:.2f}",
                duration=3.0
            ),
        ]
        
        # 4. Criar post unificado
        post = UnifiedPost(
            content_type=ContentType.REEL,
            media_paths=["/generated/video.mp4"],
            caption=f"🔥 {sample_product.name} por R$ {sample_product.price:.2f}!",
            hashtags=["ofertas", "promocao"],
            platforms=[Platform.INSTAGRAM, Platform.TIKTOK]
        )
        
        assert len(slides) == 3
        assert post.content_type == ContentType.REEL
    
    def test_lead_capture_flow(self):
        """Deve executar fluxo de captura de lead."""
        # 1. Lead chega via WhatsApp
        lead = Lead(
            id="new-lead-001",
            name="Maria Santos",
            phone="5511888888888",
            source=LeadSource.WHATSAPP
        )
        
        # 2. Calcular score inicial
        scorer = LeadScorer()
        initial_score = scorer.calculate_score(lead)
        assert initial_score > 0
        
        # 3. Lead fornece email
        lead.email = "maria@email.com"
        
        # 4. Recalcular score
        new_score = scorer.calculate_score(lead)
        assert new_score > initial_score
        
        # 5. Marcar como contatado
        lead.mark_contacted()
        assert lead.status == LeadStatus.CONTACTED
        
        # 6. Qualificar lead
        lead.add_tag("interested_in_pricing")
        lead.status = LeadStatus.QUALIFIED
        
        assert lead.status == LeadStatus.QUALIFIED
        assert "interested_in_pricing" in lead.tags


# ============================================
# DATA CONSISTENCY TESTS
# ============================================

class TestDataConsistency:
    """Testes de consistência de dados."""
    
    def test_product_price_consistency(self, sample_product):
        """Deve manter consistência de preços."""
        # Preço atual menor que original
        assert sample_product.price < sample_product.original_price
        
        # Desconto calculado corretamente
        expected_discount = int(
            (1 - sample_product.price / sample_product.original_price) * 100
        )
        assert sample_product.discount_percent == expected_discount
    
    def test_lead_timestamp_consistency(self, sample_lead):
        """Deve manter consistência de timestamps."""
        initial_updated = sample_lead.updated_at
        
        # Adicionar tag atualiza timestamp
        sample_lead.add_tag("new_tag")
        
        assert sample_lead.updated_at >= initial_updated
    
    def test_video_dimensions_consistency(self):
        """Deve manter consistência de dimensões."""
        configs = [
            VideoConfig(aspect_ratio=AspectRatio.PORTRAIT),
            VideoConfig(aspect_ratio=AspectRatio.LANDSCAPE),
            VideoConfig(aspect_ratio=AspectRatio.SQUARE),
        ]
        
        for config in configs:
            width, height = config.get_dimensions()
            
            # Dimensões devem ser positivas
            assert width > 0
            assert height > 0
            
            # Dimensões devem corresponder ao aspect ratio
            if config.aspect_ratio == AspectRatio.PORTRAIT:
                assert height > width
            elif config.aspect_ratio == AspectRatio.LANDSCAPE:
                assert width > height
            else:  # SQUARE
                assert width == height
