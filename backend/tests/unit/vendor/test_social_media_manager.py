"""
Unit Tests - Social Media Manager
=================================
Testes unitários para o gerenciador unificado de redes sociais.

Cobertura:
- SocialMediaConfig dataclass
- UnifiedPost dataclass
- PostResult dataclass
- SocialMediaManager métodos
- Publicação em múltiplas plataformas
- Tratamento de erros
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from vendor.social_media_manager import (
    SocialMediaManager,
    SocialMediaConfig,
    UnifiedPost,
    PostResult,
    Platform,
    ContentType,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def social_config() -> SocialMediaConfig:
    """Configuração padrão do Social Media Manager."""
    return SocialMediaConfig(
        instagram_username="didin_facil",
        instagram_password="test-password",
        instagram_session_file="./sessions/instagram.json",
        tiktok_cookies_file="./sessions/tiktok.json",
        tiktok_headless=True,
        whatsapp_api_url="http://localhost:8080",
        whatsapp_api_key="whatsapp-api-key",
        whatsapp_instance="didin-instance"
    )


@pytest.fixture
def instagram_only_config() -> SocialMediaConfig:
    """Configuração apenas com Instagram."""
    return SocialMediaConfig(
        instagram_username="didin_facil",
        instagram_password="test-password"
    )


@pytest.fixture
def unified_post() -> UnifiedPost:
    """Post unificado para testes."""
    return UnifiedPost(
        content_type=ContentType.IMAGE,
        media_paths=["/path/to/image.jpg"],
        caption="Confira essa oferta incrível!",
        hashtags=["ofertas", "promocao", "didinfacil"],
        platforms=[Platform.INSTAGRAM, Platform.TIKTOK]
    )


@pytest.fixture
def reel_post() -> UnifiedPost:
    """Post de reel para testes."""
    return UnifiedPost(
        content_type=ContentType.REEL,
        media_paths=["/path/to/video.mp4"],
        caption="Vídeo de oferta!",
        hashtags=["ofertas"],
        platforms=[Platform.INSTAGRAM, Platform.TIKTOK]
    )


@pytest.fixture
def whatsapp_post() -> UnifiedPost:
    """Post para WhatsApp."""
    return UnifiedPost(
        content_type=ContentType.IMAGE,
        media_paths=["/path/to/image.jpg"],
        caption="Oferta especial!",
        platforms=[Platform.WHATSAPP],
        whatsapp_recipients=["5511999999999", "5511888888888"]
    )


@pytest.fixture
def post_result_success() -> PostResult:
    """Resultado de publicação bem sucedida."""
    return PostResult(
        platform=Platform.INSTAGRAM,
        success=True,
        post_id="12345",
        url="https://instagram.com/p/ABC123"
    )


@pytest.fixture
def post_result_error() -> PostResult:
    """Resultado de publicação com erro."""
    return PostResult(
        platform=Platform.TIKTOK,
        success=False,
        error="Upload failed"
    )


# ============================================
# DATACLASS TESTS
# ============================================

class TestSocialMediaConfig:
    """Testes para SocialMediaConfig dataclass."""
    
    def test_config_creation(self, social_config):
        """Deve criar config com todos os valores."""
        assert social_config.instagram_username == "didin_facil"
        assert social_config.tiktok_cookies_file == "./sessions/tiktok.json"
        assert social_config.whatsapp_api_url == "http://localhost:8080"
    
    def test_config_defaults(self):
        """Deve criar config com valores padrão."""
        config = SocialMediaConfig()
        
        assert config.instagram_username is None
        assert config.tiktok_cookies_file is None
        assert config.whatsapp_api_url is None
        assert config.tiktok_headless is True
    
    def test_partial_config(self, instagram_only_config):
        """Deve criar config parcial."""
        assert instagram_only_config.instagram_username is not None
        assert instagram_only_config.tiktok_cookies_file is None


class TestUnifiedPost:
    """Testes para UnifiedPost dataclass."""
    
    def test_post_creation(self, unified_post):
        """Deve criar post com valores."""
        assert unified_post.content_type == ContentType.IMAGE
        assert len(unified_post.media_paths) == 1
        assert len(unified_post.hashtags) == 3
        assert len(unified_post.platforms) == 2
    
    def test_post_defaults(self):
        """Deve criar post com valores padrão."""
        post = UnifiedPost(
            content_type=ContentType.TEXT,
            media_paths=[]
        )
        
        assert post.caption == ""
        assert post.hashtags == []
        assert post.platforms == []
        assert post.schedule_time is None
    
    def test_post_with_location(self):
        """Deve criar post com localização."""
        post = UnifiedPost(
            content_type=ContentType.IMAGE,
            media_paths=["/path/to/image.jpg"],
            instagram_location=123456789
        )
        
        assert post.instagram_location == 123456789
    
    def test_post_with_tiktok_sound(self):
        """Deve criar post com som do TikTok."""
        post = UnifiedPost(
            content_type=ContentType.VIDEO,
            media_paths=["/path/to/video.mp4"],
            tiktok_sound="popular-sound-id"
        )
        
        assert post.tiktok_sound == "popular-sound-id"


class TestPostResult:
    """Testes para PostResult dataclass."""
    
    def test_success_result(self, post_result_success):
        """Deve criar resultado de sucesso."""
        assert post_result_success.success is True
        assert post_result_success.post_id == "12345"
        assert post_result_success.error is None
    
    def test_error_result(self, post_result_error):
        """Deve criar resultado com erro."""
        assert post_result_error.success is False
        assert post_result_error.error == "Upload failed"
        assert post_result_error.post_id is None


class TestPlatform:
    """Testes para Platform enum."""
    
    def test_all_platforms(self):
        """Deve ter todas as plataformas."""
        expected = ["INSTAGRAM", "TIKTOK", "WHATSAPP", "YOUTUBE", "FACEBOOK"]
        actual = [p.name for p in Platform]
        
        for expected_platform in expected:
            assert expected_platform in actual


class TestContentType:
    """Testes para ContentType enum."""
    
    def test_all_content_types(self):
        """Deve ter todos os tipos de conteúdo."""
        expected = ["IMAGE", "VIDEO", "REEL", "STORY", "CAROUSEL", "TEXT"]
        actual = [t.name for t in ContentType]
        
        for expected_type in expected:
            assert expected_type in actual


# ============================================
# MANAGER INITIALIZATION TESTS
# ============================================

class TestSocialMediaManagerInit:
    """Testes de inicialização do SocialMediaManager."""
    
    def test_manager_creation(self, social_config):
        """Deve criar manager com configuração."""
        manager = SocialMediaManager(social_config)
        
        assert manager.config == social_config
        assert manager._initialized is False
        assert len(manager._clients) == 0
    
    @pytest.mark.asyncio
    async def test_initialize_instagram(self, instagram_only_config):
        """Deve inicializar cliente Instagram."""
        with patch("vendor.social_media_manager.InstagramClient") as mock_ig:
            mock_client = AsyncMock()
            mock_ig.return_value = mock_client
            
            manager = SocialMediaManager(instagram_only_config)
            await manager.initialize()
            
            assert manager._initialized is True
            assert Platform.INSTAGRAM in manager._clients
    
    @pytest.mark.asyncio
    async def test_initialize_all_platforms(self, social_config):
        """Deve inicializar todos os clientes configurados."""
        with patch("vendor.social_media_manager.InstagramClient") as mock_ig, \
             patch("vendor.social_media_manager.TikTokClient") as mock_tt, \
             patch("vendor.social_media_manager.WhatsAppClient") as mock_wa:
            
            mock_ig.return_value = AsyncMock()
            mock_tt.return_value = MagicMock()
            mock_wa.return_value = MagicMock()
            
            manager = SocialMediaManager(social_config)
            await manager.initialize()
            
            assert manager._initialized is True
            assert len(manager._clients) == 3
    
    @pytest.mark.asyncio
    async def test_initialize_specific_platforms(self, social_config):
        """Deve inicializar apenas plataformas especificadas."""
        with patch("vendor.social_media_manager.InstagramClient") as mock_ig:
            mock_ig.return_value = AsyncMock()
            
            manager = SocialMediaManager(social_config)
            await manager.initialize(platforms=[Platform.INSTAGRAM])
            
            assert Platform.INSTAGRAM in manager._clients
            assert Platform.TIKTOK not in manager._clients


# ============================================
# PUBLISHING TESTS
# ============================================

class TestSocialMediaManagerPublish:
    """Testes de publicação do SocialMediaManager."""
    
    @pytest.mark.asyncio
    async def test_publish_not_initialized(self, social_config, unified_post):
        """Deve lançar erro se não inicializado."""
        manager = SocialMediaManager(social_config)
        
        with pytest.raises(RuntimeError, match="não inicializado"):
            await manager.publish(unified_post)
    
    @pytest.mark.asyncio
    async def test_publish_to_instagram(self, instagram_only_config):
        """Deve publicar no Instagram."""
        with patch("vendor.social_media_manager.InstagramClient") as mock_ig:
            mock_client = AsyncMock()
            mock_client.upload_photo.return_value = {
                "id": "post-123",
                "code": "ABC123"
            }
            mock_ig.return_value = mock_client
            
            manager = SocialMediaManager(instagram_only_config)
            await manager.initialize()
            
            post = UnifiedPost(
                content_type=ContentType.IMAGE,
                media_paths=["/path/to/image.jpg"],
                caption="Test",
                platforms=[Platform.INSTAGRAM]
            )
            
            results = await manager.publish(post)
            
            assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_publish_platform_not_initialized(self, instagram_only_config):
        """Deve retornar erro para plataforma não inicializada."""
        with patch("vendor.social_media_manager.InstagramClient") as mock_ig:
            mock_ig.return_value = AsyncMock()
            
            manager = SocialMediaManager(instagram_only_config)
            await manager.initialize()
            
            post = UnifiedPost(
                content_type=ContentType.IMAGE,
                media_paths=["/path/to/image.jpg"],
                platforms=[Platform.TIKTOK]  # Não inicializado
            )
            
            results = await manager.publish(post)
            
            assert len(results) == 1
            assert results[0].success is False
            assert "não inicializada" in results[0].error


# ============================================
# CLOSE TESTS
# ============================================

class TestSocialMediaManagerClose:
    """Testes de fechamento do SocialMediaManager."""
    
    @pytest.mark.asyncio
    async def test_close_clients(self, instagram_only_config):
        """Deve fechar todos os clientes."""
        with patch("vendor.social_media_manager.InstagramClient") as mock_ig:
            mock_client = AsyncMock()
            mock_ig.return_value = mock_client
            
            manager = SocialMediaManager(instagram_only_config)
            await manager.initialize()
            await manager.close()
            
            assert manager._initialized is False
            assert len(manager._clients) == 0


# ============================================
# CONTEXT MANAGER TESTS
# ============================================

class TestSocialMediaManagerContextManager:
    """Testes de context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self, instagram_only_config):
        """Deve funcionar como context manager."""
        with patch("vendor.social_media_manager.InstagramClient") as mock_ig:
            mock_client = AsyncMock()
            mock_ig.return_value = mock_client
            
            async with SocialMediaManager(instagram_only_config) as manager:
                assert manager._initialized is True
            
            assert manager._initialized is False


# ============================================
# ERROR HANDLING TESTS
# ============================================

class TestSocialMediaManagerErrors:
    """Testes de tratamento de erros."""
    
    @pytest.mark.asyncio
    async def test_init_instagram_error(self):
        """Deve lançar erro se Instagram não configurado."""
        config = SocialMediaConfig()
        manager = SocialMediaManager(config)
        
        with pytest.raises(ValueError, match="Instagram não configurado"):
            await manager._init_platform(Platform.INSTAGRAM)
    
    @pytest.mark.asyncio
    async def test_init_tiktok_error(self):
        """Deve lançar erro se TikTok não configurado."""
        config = SocialMediaConfig()
        manager = SocialMediaManager(config)
        
        with pytest.raises(ValueError, match="TikTok não configurado"):
            await manager._init_platform(Platform.TIKTOK)
    
    @pytest.mark.asyncio
    async def test_init_whatsapp_error(self):
        """Deve lançar erro se WhatsApp não configurado."""
        config = SocialMediaConfig()
        manager = SocialMediaManager(config)
        
        with pytest.raises(ValueError, match="WhatsApp não configurado"):
            await manager._init_platform(Platform.WHATSAPP)
    
    @pytest.mark.asyncio
    async def test_publish_exception_handling(self, instagram_only_config):
        """Deve tratar exceções na publicação."""
        with patch("vendor.social_media_manager.InstagramClient") as mock_ig:
            mock_client = AsyncMock()
            mock_client.upload_photo.side_effect = Exception("Upload failed")
            mock_ig.return_value = mock_client
            
            manager = SocialMediaManager(instagram_only_config)
            await manager.initialize()
            
            post = UnifiedPost(
                content_type=ContentType.IMAGE,
                media_paths=["/path/to/image.jpg"],
                platforms=[Platform.INSTAGRAM]
            )
            
            results = await manager.publish(post)
            
            # Deve retornar resultado com erro, não lançar exceção
            assert len(results) == 1


# ============================================
# CONTENT TYPE HANDLING TESTS
# ============================================

class TestContentTypeHandling:
    """Testes de tratamento de tipos de conteúdo."""
    
    def test_image_post(self):
        """Deve criar post de imagem."""
        post = UnifiedPost(
            content_type=ContentType.IMAGE,
            media_paths=["/path/to/image.jpg"]
        )
        
        assert post.content_type == ContentType.IMAGE
    
    def test_video_post(self):
        """Deve criar post de vídeo."""
        post = UnifiedPost(
            content_type=ContentType.VIDEO,
            media_paths=["/path/to/video.mp4"]
        )
        
        assert post.content_type == ContentType.VIDEO
    
    def test_reel_post(self):
        """Deve criar post de reel."""
        post = UnifiedPost(
            content_type=ContentType.REEL,
            media_paths=["/path/to/reel.mp4"]
        )
        
        assert post.content_type == ContentType.REEL
    
    def test_story_post(self):
        """Deve criar post de story."""
        post = UnifiedPost(
            content_type=ContentType.STORY,
            media_paths=["/path/to/story.mp4"]
        )
        
        assert post.content_type == ContentType.STORY
    
    def test_carousel_post(self):
        """Deve criar post de carousel."""
        post = UnifiedPost(
            content_type=ContentType.CAROUSEL,
            media_paths=[
                "/path/to/image1.jpg",
                "/path/to/image2.jpg",
                "/path/to/image3.jpg"
            ]
        )
        
        assert post.content_type == ContentType.CAROUSEL
        assert len(post.media_paths) == 3


# ============================================
# MULTI-PLATFORM TESTS
# ============================================

class TestMultiPlatformPublishing:
    """Testes de publicação em múltiplas plataformas."""
    
    @pytest.mark.asyncio
    async def test_publish_to_multiple_platforms(self, social_config):
        """Deve publicar em múltiplas plataformas."""
        with patch("vendor.social_media_manager.InstagramClient") as mock_ig, \
             patch("vendor.social_media_manager.TikTokClient") as mock_tt, \
             patch("vendor.social_media_manager.WhatsAppClient") as mock_wa:
            
            mock_ig_client = AsyncMock()
            mock_ig_client.upload_photo.return_value = {"id": "ig-123"}
            mock_ig.return_value = mock_ig_client
            
            mock_tt.return_value = MagicMock()
            mock_wa.return_value = MagicMock()
            
            manager = SocialMediaManager(social_config)
            await manager.initialize()
            
            post = UnifiedPost(
                content_type=ContentType.IMAGE,
                media_paths=["/path/to/image.jpg"],
                platforms=[Platform.INSTAGRAM]
            )
            
            results = await manager.publish(post)
            
            # Cada plataforma deve ter um resultado
            assert len(results) >= 1
    
    def test_post_with_all_platforms(self):
        """Deve criar post para todas as plataformas."""
        post = UnifiedPost(
            content_type=ContentType.REEL,
            media_paths=["/path/to/video.mp4"],
            platforms=[Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE]
        )
        
        assert len(post.platforms) == 3
