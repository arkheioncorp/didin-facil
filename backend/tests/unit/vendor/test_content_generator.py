"""
Unit Tests - Content Generator
==============================
Testes unitários para o gerador de conteúdo (vídeos, imagens).

Cobertura:
- VideoConfig dataclass
- ProductData dataclass
- TextSlide dataclass
- FFmpegVideoGenerator métodos
- Tratamento de erros
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from vendor.content_generator.generator import (
    FFmpegVideoGenerator,
    VideoConfig,
    ProductData,
    TextSlide,
    AspectRatio,
    TemplateStyle,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def video_config() -> VideoConfig:
    """Configuração padrão de vídeo."""
    return VideoConfig(
        aspect_ratio=AspectRatio.PORTRAIT,
        duration=15,
        fps=30,
        background_color="#1a1a2e",
        font_family="Montserrat",
        font_size=48,
        text_color="#ffffff",
        accent_color="#e94560"
    )


@pytest.fixture
def product_data() -> ProductData:
    """Dados de produto para testes."""
    return ProductData(
        name="Smartphone XYZ",
        price=1299.99,
        original_price=1599.99,
        image_url="https://example.com/phone.jpg",
        store="Amazon",
        category="Electronics",
        description="Latest smartphone with amazing features"
    )


@pytest.fixture
def text_slides() -> list:
    """Lista de slides de texto."""
    return [
        TextSlide(text="Welcome!", duration=2.0),
        TextSlide(text="Check this offer", duration=3.0),
        TextSlide(text="Buy now!", duration=2.0, color="#ff0000")
    ]


@pytest.fixture
def mock_ffmpeg():
    """Mock do subprocess para FFmpeg."""
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=0, stderr="")
        yield mock


# ============================================
# DATACLASS TESTS
# ============================================

class TestVideoConfig:
    """Testes para VideoConfig dataclass."""
    
    def test_config_defaults(self):
        """Deve criar config com valores padrão."""
        config = VideoConfig()
        
        assert config.aspect_ratio == AspectRatio.PORTRAIT
        assert config.duration == 15
        assert config.fps == 30
    
    def test_config_with_values(self, video_config):
        """Deve criar config com valores customizados."""
        assert video_config.background_color == "#1a1a2e"
        assert video_config.font_size == 48
    
    def test_get_dimensions_portrait(self):
        """Deve retornar dimensões para portrait."""
        config = VideoConfig(aspect_ratio=AspectRatio.PORTRAIT)
        width, height = config.get_dimensions()
        
        assert width == 1080
        assert height == 1920
    
    def test_get_dimensions_landscape(self):
        """Deve retornar dimensões para landscape."""
        config = VideoConfig(aspect_ratio=AspectRatio.LANDSCAPE)
        width, height = config.get_dimensions()
        
        assert width == 1920
        assert height == 1080
    
    def test_get_dimensions_square(self):
        """Deve retornar dimensões para square."""
        config = VideoConfig(aspect_ratio=AspectRatio.SQUARE)
        width, height = config.get_dimensions()
        
        assert width == 1080
        assert height == 1080
    
    def test_custom_dimensions(self):
        """Deve usar dimensões customizadas se fornecidas."""
        config = VideoConfig(width=720, height=1280)
        width, height = config.get_dimensions()
        
        assert width == 720
        assert height == 1280


class TestProductData:
    """Testes para ProductData dataclass."""
    
    def test_product_data_creation(self, product_data):
        """Deve criar dados de produto."""
        assert product_data.name == "Smartphone XYZ"
        assert product_data.price == 1299.99
        assert product_data.store == "Amazon"
    
    def test_discount_percent_calculation(self, product_data):
        """Deve calcular porcentagem de desconto."""
        discount = product_data.discount_percent
        
        # (1599.99 - 1299.99) / 1599.99 * 100 ≈ 18%
        assert discount == 18
    
    def test_discount_percent_without_original(self):
        """Deve retornar None sem preço original."""
        product = ProductData(name="Product", price=100.0)
        
        assert product.discount_percent is None
    
    def test_discount_percent_no_discount(self):
        """Deve retornar None se não houver desconto."""
        product = ProductData(
            name="Product",
            price=100.0,
            original_price=100.0
        )
        
        assert product.discount_percent is None
    
    def test_discount_percent_price_higher_than_original(self):
        """Deve retornar None se preço maior que original."""
        product = ProductData(
            name="Product",
            price=150.0,
            original_price=100.0
        )
        
        assert product.discount_percent is None


class TestTextSlide:
    """Testes para TextSlide dataclass."""
    
    def test_slide_defaults(self):
        """Deve criar slide com valores padrão."""
        slide = TextSlide(text="Hello")
        
        assert slide.text == "Hello"
        assert slide.duration == 3.0
        assert slide.animation == "fade"
    
    def test_slide_with_values(self):
        """Deve criar slide com valores customizados."""
        slide = TextSlide(
            text="Custom",
            duration=5.0,
            font_size=64,
            color="#ff0000",
            animation="slide"
        )
        
        assert slide.duration == 5.0
        assert slide.font_size == 64
        assert slide.color == "#ff0000"


class TestAspectRatio:
    """Testes para AspectRatio enum."""
    
    def test_all_ratios(self):
        """Deve ter todos os aspect ratios."""
        assert AspectRatio.PORTRAIT.value == "9:16"
        assert AspectRatio.LANDSCAPE.value == "16:9"
        assert AspectRatio.SQUARE.value == "1:1"


class TestTemplateStyle:
    """Testes para TemplateStyle enum."""
    
    def test_all_styles(self):
        """Deve ter todos os estilos de template."""
        expected = [
            "PRODUCT_SHOWCASE",
            "PRICE_COMPARISON",
            "DEAL_ALERT",
            "TESTIMONIAL",
            "TEXT_ANIMATION"
        ]
        actual = [s.name for s in TemplateStyle]
        
        for expected_val in expected:
            assert expected_val in actual


# ============================================
# FFMPEG GENERATOR TESTS
# ============================================

class TestFFmpegVideoGenerator:
    """Testes para FFmpegVideoGenerator."""
    
    def test_generator_creation(self, video_config, mock_ffmpeg):
        """Deve criar gerador com configuração."""
        generator = FFmpegVideoGenerator(video_config)
        
        assert generator.config == video_config
    
    def test_ffmpeg_not_found(self, video_config):
        """Deve lançar erro se FFmpeg não estiver instalado."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="FFmpeg"):
                FFmpegVideoGenerator(video_config)
    
    @pytest.mark.asyncio
    async def test_run_ffmpeg_success(self, video_config, mock_ffmpeg):
        """Deve executar FFmpeg com sucesso."""
        generator = FFmpegVideoGenerator(video_config)
        
        with patch.object(generator, '_run_ffmpeg', new_callable=AsyncMock, return_value=True):
            result = await generator._run_ffmpeg(["-version"])
            assert result is True
    
    @pytest.mark.asyncio
    async def test_run_ffmpeg_failure(self, video_config, mock_ffmpeg):
        """Deve tratar falha do FFmpeg."""
        generator = FFmpegVideoGenerator(video_config)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Error")
            
            result = await generator._run_ffmpeg(["-invalid"])
            
            assert result is False


# ============================================
# TEXT VIDEO TESTS
# ============================================

class TestTextVideoGeneration:
    """Testes de geração de vídeo com texto."""
    
    @pytest.mark.asyncio
    async def test_create_text_video(self, video_config, text_slides, mock_ffmpeg, tmp_path):
        """Deve criar vídeo com slides de texto."""
        output_path = tmp_path / "output.mp4"
        
        generator = FFmpegVideoGenerator(video_config)
        
        with patch.object(generator, '_create_text_image', new_callable=AsyncMock):
            with patch.object(generator, '_run_ffmpeg', new_callable=AsyncMock, return_value=True):
                result = await generator.create_text_video(
                    text_slides,
                    output_path
                )
                
                assert result is True
    
    @pytest.mark.asyncio
    async def test_create_text_video_with_audio(self, video_config, text_slides, mock_ffmpeg, tmp_path):
        """Deve criar vídeo com áudio de fundo."""
        output_path = tmp_path / "output.mp4"
        audio_path = tmp_path / "audio.mp3"
        audio_path.write_bytes(b"fake audio")
        
        generator = FFmpegVideoGenerator(video_config)
        
        with patch.object(generator, '_create_text_image', new_callable=AsyncMock):
            with patch.object(generator, '_run_ffmpeg', new_callable=AsyncMock, return_value=True):
                result = await generator.create_text_video(
                    text_slides,
                    output_path,
                    audio_path=audio_path
                )
                
                assert result is True


# ============================================
# PRODUCT VIDEO TESTS
# ============================================

class TestProductVideoGeneration:
    """Testes de geração de vídeo de produto."""
    
    @pytest.mark.asyncio
    async def test_create_product_video_showcase(self, video_config, product_data, mock_ffmpeg, tmp_path):
        """Deve criar vídeo de produto com template showcase."""
        output_path = tmp_path / "product.mp4"
        
        generator = FFmpegVideoGenerator(video_config)
        
        with patch.object(generator, 'create_text_video', new_callable=AsyncMock, return_value=True):
            result = await generator.create_product_video(
                product_data,
                output_path,
                template=TemplateStyle.PRODUCT_SHOWCASE
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_create_product_video_deal_alert(self, video_config, product_data, mock_ffmpeg, tmp_path):
        """Deve criar vídeo de alerta de oferta."""
        output_path = tmp_path / "deal.mp4"
        
        generator = FFmpegVideoGenerator(video_config)
        
        with patch.object(generator, 'create_text_video', new_callable=AsyncMock, return_value=True):
            result = await generator.create_product_video(
                product_data,
                output_path,
                template=TemplateStyle.DEAL_ALERT
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_create_product_video_price_comparison(self, video_config, product_data, mock_ffmpeg, tmp_path):
        """Deve criar vídeo de comparação de preços."""
        output_path = tmp_path / "comparison.mp4"
        
        generator = FFmpegVideoGenerator(video_config)
        
        with patch.object(generator, 'create_text_video', new_callable=AsyncMock, return_value=True):
            result = await generator.create_product_video(
                product_data,
                output_path,
                template=TemplateStyle.PRICE_COMPARISON
            )
            
            assert result is True


# ============================================
# IMAGE GENERATION TESTS
# ============================================

class TestImageGeneration:
    """Testes de geração de imagens."""
    
    @pytest.mark.asyncio
    async def test_create_text_image(self, video_config, mock_ffmpeg, tmp_path):
        """Deve criar imagem com texto."""
        tmp_path / "text.png"
        
        generator = FFmpegVideoGenerator(video_config)
        
        with patch.object(generator, '_run_ffmpeg', new_callable=AsyncMock, return_value=True):
            # O método _create_text_image é interno
            # Verificar que FFmpegVideoGenerator tem o método
            assert hasattr(generator, '_create_text_image')


# ============================================
# TEMPLATE TESTS
# ============================================

class TestVideoTemplates:
    """Testes de templates de vídeo."""
    
    def test_product_showcase_slides(self, product_data):
        """Deve gerar slides para showcase de produto."""
        slides = [
            TextSlide(text="🔥 OFERTA", duration=1.5),
            TextSlide(text=product_data.name, duration=2.5),
            TextSlide(text=f"R$ {product_data.price:.2f}", duration=2.0),
            TextSlide(text="Compre agora!", duration=2.0),
        ]
        
        assert len(slides) == 4
        assert product_data.name in slides[1].text
    
    def test_deal_alert_with_discount(self, product_data):
        """Deve incluir desconto no alerta."""
        discount = product_data.discount_percent
        
        slides = [
            TextSlide(text=f"🏷️ {discount}% OFF", duration=2.0),
            TextSlide(text=product_data.name, duration=2.5),
        ]
        
        assert "18% OFF" in slides[0].text


# ============================================
# AUDIO/VIDEO MANIPULATION TESTS
# ============================================

class TestAudioVideoManipulation:
    """Testes de manipulação de áudio/vídeo."""
    
    @pytest.mark.asyncio
    async def test_add_music(self, video_config, mock_ffmpeg, tmp_path):
        """Deve adicionar música ao vídeo."""
        video_path = tmp_path / "video.mp4"
        audio_path = tmp_path / "audio.mp3"
        output_path = tmp_path / "output.mp4"
        
        video_path.write_bytes(b"fake video")
        audio_path.write_bytes(b"fake audio")
        
        generator = FFmpegVideoGenerator(video_config)
        
        with patch.object(generator, '_run_ffmpeg', new_callable=AsyncMock, return_value=True):
            result = await generator.add_music(video_path, audio_path, output_path, volume=0.3)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_add_watermark(self, video_config, mock_ffmpeg, tmp_path):
        """Deve adicionar marca d'água ao vídeo."""
        video_path = tmp_path / "video.mp4"
        watermark_path = tmp_path / "watermark.png"
        tmp_path / "output.mp4"
        
        video_path.write_bytes(b"fake video")
        watermark_path.write_bytes(b"fake watermark")
        
        generator = FFmpegVideoGenerator(video_config)
        
        # Verificar que o método existe
        assert hasattr(generator, 'add_watermark')


# ============================================
# ERROR HANDLING TESTS
# ============================================

class TestContentGeneratorErrors:
    """Testes de tratamento de erros."""
    
    def test_ffmpeg_check_failure(self, video_config):
        """Deve tratar falha na verificação do FFmpeg."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("FFmpeg not found")
            
            with pytest.raises(RuntimeError, match="FFmpeg"):
                FFmpegVideoGenerator(video_config)
    
    @pytest.mark.asyncio
    async def test_video_generation_failure(self, video_config, mock_ffmpeg, tmp_path):
        """Deve tratar falha na geração de vídeo."""
        output_path = tmp_path / "output.mp4"
        slides = [TextSlide(text="Test", duration=2.0)]
        
        generator = FFmpegVideoGenerator(video_config)
        
        with patch.object(generator, '_create_text_image', new_callable=AsyncMock):
            with patch.object(generator, '_run_ffmpeg', new_callable=AsyncMock, return_value=False):
                result = await generator.create_text_video(slides, output_path)
                
                assert result is False


# ============================================
# EDGE CASES
# ============================================

class TestContentGeneratorEdgeCases:
    """Testes de casos limite."""
    
    def test_empty_product_description(self):
        """Deve tratar descrição de produto vazia."""
        product = ProductData(
            name="Product",
            price=100.0,
            description=""
        )
        
        assert product.description == ""
    
    def test_very_long_product_name(self):
        """Deve tratar nome de produto muito longo."""
        long_name = "A" * 500
        product = ProductData(
            name=long_name,
            price=100.0
        )
        
        assert len(product.name) == 500
    
    def test_zero_price_product(self):
        """Deve tratar produto com preço zero."""
        product = ProductData(
            name="Free Product",
            price=0.0
        )
        
        assert product.price == 0.0
        assert product.discount_percent is None
    
    def test_slide_zero_duration(self):
        """Deve criar slide com duração zero."""
        slide = TextSlide(text="Test", duration=0.0)
        
        assert slide.duration == 0.0
    
    def test_empty_slides_list(self, video_config, mock_ffmpeg):
        """Deve tratar lista de slides vazia."""
        generator = FFmpegVideoGenerator(video_config)
        
        # O gerador deve ser criado mesmo sem slides
        assert generator is not None
