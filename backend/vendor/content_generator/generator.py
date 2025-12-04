"""
Content Generator Module
========================
Gerador automático de conteúdo para redes sociais.

Funcionalidades:
- Geração de vídeos shorts/reels a partir de templates
- Criação de imagens com texto overlay
- Geração de legendas com IA
- Templates pré-definidos
"""

from typing import Optional, List, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import asyncio
import subprocess
import logging
import tempfile

logger = logging.getLogger(__name__)


class AspectRatio(Enum):
    PORTRAIT = "9:16"    # Stories, Reels, TikTok
    LANDSCAPE = "16:9"   # YouTube
    SQUARE = "1:1"       # Instagram Feed


class TemplateStyle(Enum):
    PRODUCT_SHOWCASE = "product_showcase"
    PRICE_COMPARISON = "price_comparison"
    DEAL_ALERT = "deal_alert"
    TESTIMONIAL = "testimonial"
    TEXT_ANIMATION = "text_animation"


@dataclass
class VideoConfig:
    """Configuração para geração de vídeo."""
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT
    duration: int = 15  # segundos
    fps: int = 30
    width: Optional[int] = None
    height: Optional[int] = None
    background_color: str = "#1a1a2e"
    font_family: str = "Montserrat"
    font_size: int = 48
    text_color: str = "#ffffff"
    accent_color: str = "#e94560"
    
    def get_dimensions(self) -> Tuple[int, int]:
        """Retorna dimensões baseadas no aspect ratio."""
        if self.width and self.height:
            return (self.width, self.height)
        
        if self.aspect_ratio == AspectRatio.PORTRAIT:
            return (1080, 1920)
        elif self.aspect_ratio == AspectRatio.LANDSCAPE:
            return (1920, 1080)
        else:  # SQUARE
            return (1080, 1080)


@dataclass
class ProductData:
    """Dados de produto para geração de conteúdo."""
    name: str
    price: float
    original_price: Optional[float] = None
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    store: str = ""
    category: str = ""
    description: str = ""
    
    @property
    def discount_percent(self) -> Optional[int]:
        """Calcula porcentagem de desconto."""
        if self.original_price and self.original_price > self.price:
            return int((1 - self.price / self.original_price) * 100)
        return None


@dataclass
class TextSlide:
    """Slide de texto para vídeo."""
    text: str
    duration: float = 3.0  # segundos
    font_size: Optional[int] = None
    color: Optional[str] = None
    background: Optional[str] = None
    animation: str = "fade"  # fade, slide, zoom


class FFmpegVideoGenerator:
    """
    Gerador de vídeos usando FFmpeg.
    
    Requisitos:
        - FFmpeg instalado no sistema
        - Fontes disponíveis
    """
    
    def __init__(self, config: VideoConfig):
        self.config = config
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Verifica se FFmpeg está instalado."""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "FFmpeg não encontrado. Instale com: "
                "apt install ffmpeg (Linux) ou brew install ffmpeg (Mac)"
            )
    
    async def _run_ffmpeg(self, args: List[str]) -> bool:
        """Executa comando FFmpeg assincronamente."""
        loop = asyncio.get_event_loop()
        
        def run():
            result = subprocess.run(
                ["ffmpeg", "-y"] + args,
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stderr
        
        success, stderr = await loop.run_in_executor(None, run)
        
        if not success:
            logger.error(f"FFmpeg error: {stderr}")
        
        return success
    
    async def create_text_video(
        self,
        slides: List[TextSlide],
        output_path: Union[str, Path],
        audio_path: Optional[Union[str, Path]] = None
    ) -> bool:
        """
        Cria vídeo com slides de texto.
        
        Args:
            slides: Lista de slides
            output_path: Caminho do vídeo de saída
            audio_path: Áudio de fundo opcional
        """
        width, height = self.config.get_dimensions()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Gerar cada slide como imagem
            slide_paths = []
            
            for i, slide in enumerate(slides):
                slide_path = Path(tmpdir) / f"slide_{i:03d}.png"
                await self._create_text_image(
                    slide.text,
                    slide_path,
                    width, height,
                    font_size=slide.font_size or self.config.font_size,
                    color=slide.color or self.config.text_color,
                    background=slide.background or self.config.background_color
                )
                slide_paths.append((slide_path, slide.duration))
            
            # Criar vídeo a partir dos slides
            # Gerar arquivo de concat
            concat_file = Path(tmpdir) / "concat.txt"
            with open(concat_file, 'w') as f:
                for path, duration in slide_paths:
                    # FFmpeg concat demuxer format
                    f.write(f"file '{path}'\n")
                    f.write(f"duration {duration}\n")
                # Repetir último para evitar bug do concat
                if slide_paths:
                    f.write(f"file '{slide_paths[-1][0]}'\n")
            
            # Gerar vídeo intermediário
            temp_video = Path(tmpdir) / "temp.mp4"
            
            args = [
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-vf", f"fps={self.config.fps},format=yuv420p",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                str(temp_video)
            ]
            
            if not await self._run_ffmpeg(args):
                return False
            
            # Adicionar áudio se fornecido
            if audio_path:
                args = [
                    "-i", str(temp_video),
                    "-i", str(audio_path),
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    str(output_path)
                ]
            else:
                args = [
                    "-i", str(temp_video),
                    "-c:v", "copy",
                    str(output_path)
                ]
            
            return await self._run_ffmpeg(args)
    
    async def _create_text_image(
        self,
        text: str,
        output_path: Path,
        width: int,
        height: int,
        font_size: int,
        color: str,
        background: str
    ) -> bool:
        """Cria imagem com texto usando FFmpeg."""
        # Escapar caracteres especiais para FFmpeg
        safe_text = text.replace("'", "\\'").replace(":", "\\:")
        
        # Criar imagem de fundo e adicionar texto
        args = [
            "-f", "lavfi",
            "-i", f"color=c={background}:s={width}x{height}:d=1",
            "-vf", f"drawtext=text='{safe_text}':"
                   f"fontsize={font_size}:"
                   f"fontcolor={color}:"
                   f"x=(w-tw)/2:y=(h-th)/2:"
                   f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "-frames:v", "1",
            str(output_path)
        ]
        
        return await self._run_ffmpeg(args)
    
    async def create_product_video(
        self,
        product: ProductData,
        output_path: Union[str, Path],
        template: TemplateStyle = TemplateStyle.PRODUCT_SHOWCASE
    ) -> bool:
        """
        Cria vídeo promocional de produto.
        
        Args:
            product: Dados do produto
            output_path: Caminho de saída
            template: Estilo do template
        """
        slides = []
        
        if template == TemplateStyle.DEAL_ALERT:
            slides = [
                TextSlide("🔥 OFERTA IMPERDÍVEL!", duration=2),
                TextSlide(product.name, duration=3),
            ]
            
            if product.discount_percent:
                slides.append(TextSlide(
                    f"-{product.discount_percent}% OFF!",
                    duration=2,
                    color="#ff6b6b"
                ))
            
            slides.append(TextSlide(
                f"R$ {product.price:.2f}",
                duration=3,
                font_size=72
            ))
            
            if product.store:
                slides.append(TextSlide(
                    f"Na {product.store}",
                    duration=2
                ))
            
            slides.append(TextSlide(
                "Link na bio! 👆",
                duration=2
            ))
        
        elif template == TemplateStyle.PRICE_COMPARISON:
            slides = [
                TextSlide("💰 COMPARAMOS PREÇOS!", duration=2),
                TextSlide(product.name, duration=3),
                TextSlide(
                    f"MELHOR PREÇO:\nR$ {product.price:.2f}",
                    duration=4,
                    color="#4ecdc4"
                ),
                TextSlide(
                    f"Encontrado na {product.store}",
                    duration=3
                ),
                TextSlide("TikTrend Finder\nComparador de Preços", duration=3)
            ]
        
        else:  # PRODUCT_SHOWCASE
            slides = [
                TextSlide(product.name, duration=3),
                TextSlide(f"R$ {product.price:.2f}", duration=3, font_size=72),
            ]
            
            if product.description:
                slides.append(TextSlide(product.description[:100], duration=3))
            
            slides.append(TextSlide("Saiba mais! 👇", duration=2))
        
        return await self.create_text_video(slides, output_path)
    
    async def add_music(
        self,
        video_path: Union[str, Path],
        audio_path: Union[str, Path],
        output_path: Union[str, Path],
        volume: float = 0.3
    ) -> bool:
        """Adiciona música de fundo ao vídeo."""
        args = [
            "-i", str(video_path),
            "-i", str(audio_path),
            "-filter_complex",
            f"[1:a]volume={volume}[bg];[0:a][bg]amix=inputs=2:duration=first",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path)
        ]
        
        return await self._run_ffmpeg(args)
    
    async def add_watermark(
        self,
        video_path: Union[str, Path],
        watermark_path: Union[str, Path],
        output_path: Union[str, Path],
        position: str = "bottom-right",
        opacity: float = 0.5
    ) -> bool:
        """Adiciona marca d'água ao vídeo."""
        # Posições
        positions = {
            "top-left": "10:10",
            "top-right": "W-w-10:10",
            "bottom-left": "10:H-h-10",
            "bottom-right": "W-w-10:H-h-10",
            "center": "(W-w)/2:(H-h)/2"
        }
        
        pos = positions.get(position, positions["bottom-right"])
        
        args = [
            "-i", str(video_path),
            "-i", str(watermark_path),
            "-filter_complex",
            f"[1:v]format=rgba,colorchannelmixer=aa={opacity}[watermark];"
            f"[0:v][watermark]overlay={pos}",
            "-c:a", "copy",
            str(output_path)
        ]
        
        return await self._run_ffmpeg(args)


# ==================== Caption Generator ====================

class CaptionGenerator:
    """
    Gerador de legendas usando templates ou IA.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
    
    def generate_product_caption(
        self,
        product: ProductData,
        style: str = "promotional",
        include_hashtags: bool = True,
        include_cta: bool = True
    ) -> str:
        """
        Gera legenda para produto usando templates.
        
        Args:
            product: Dados do produto
            style: promotional, informative, urgent
            include_hashtags: Incluir hashtags
            include_cta: Incluir call-to-action
        """
        captions = {
            "promotional": [
                f"🔥 {product.name} por apenas R$ {product.price:.2f}!",
                f"💰 Oferta imperdível! {product.name} - R$ {product.price:.2f}",
                f"✨ Acabei de encontrar! {product.name} com preço incrível!"
            ],
            "informative": [
                f"📦 {product.name}\n💵 Preço: R$ {product.price:.2f}\n🏪 Loja: {product.store}",
                f"Comparamos preços e encontramos: {product.name} por R$ {product.price:.2f} na {product.store}"
            ],
            "urgent": [
                f"⚡ CORRE! {product.name} por R$ {product.price:.2f} - pode acabar!",
                f"🚨 ÚLTIMA CHANCE! {product.name} com {product.discount_percent}% OFF!"
            ]
        }
        
        import random
        caption = random.choice(captions.get(style, captions["promotional"]))
        
        # Adicionar desconto
        if product.discount_percent:
            caption += f"\n\n💸 Economia de {product.discount_percent}%!"
        
        # CTA
        if include_cta:
            ctas = [
                "\n\n👆 Link na bio!",
                "\n\n🛒 Acesse o link nos stories!",
                "\n\n💬 Comenta 'QUERO' que envio o link!",
                "\n\n📲 Arraste para cima e aproveite!"
            ]
            caption += random.choice(ctas)
        
        # Hashtags
        if include_hashtags:
            base_hashtags = ["ofertas", "promoção", "economia", "desconto"]
            category_tags = {
                "eletrônicos": ["tech", "gadgets", "tecnologia"],
                "moda": ["fashion", "estilo", "look"],
                "casa": ["decoração", "casa", "lar"],
                "beleza": ["beauty", "skincare", "makeup"]
            }
            
            tags = base_hashtags + category_tags.get(product.category.lower(), [])
            hashtags = " ".join(f"#{tag}" for tag in tags[:8])
            caption += f"\n\n{hashtags}"
        
        return caption
    
    async def generate_with_ai(
        self,
        product: ProductData,
        tone: str = "friendly",
        platform: str = "instagram"
    ) -> str:
        """
        Gera legenda usando OpenAI.
        
        Requer OPENAI_API_KEY configurada.
        """
        if not self.openai_api_key:
            logger.warning("OpenAI API key não configurada, usando template")
            return self.generate_product_caption(product)
        
        try:
            import httpx
            
            prompt = f"""
            Crie uma legenda para {platform} para o seguinte produto:
            
            Produto: {product.name}
            Preço: R$ {product.price:.2f}
            {"Preço original: R$ " + str(product.original_price) if product.original_price else ""}
            Loja: {product.store}
            Categoria: {product.category}
            
            Requisitos:
            - Tom: {tone}
            - Inclua emojis relevantes
            - Inclua call-to-action
            - Inclua 5-8 hashtags relevantes
            - Máximo 300 caracteres para o texto principal
            - Para {platform}
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openai_api_key}"},
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {"role": "system", "content": "Você é um expert em social media marketing."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"Erro ao gerar com IA: {e}")
            return self.generate_product_caption(product)


# ==================== Batch Content Generator ====================

@dataclass
class ContentBatch:
    """Batch de conteúdo gerado."""
    video_path: Optional[str] = None
    caption: str = ""
    hashtags: List[str] = field(default_factory=list)
    product: Optional[ProductData] = None


class BatchContentGenerator:
    """
    Gerador em lote de conteúdo para múltiplos produtos.
    
    Uso:
        generator = BatchContentGenerator(output_dir="./content")
        
        products = [
            ProductData(name="iPhone", price=4999.99, store="Amazon"),
            ProductData(name="Samsung", price=3999.99, store="Magazine Luiza"),
        ]
        
        batches = await generator.generate_batch(products, template=TemplateStyle.DEAL_ALERT)
    """
    
    def __init__(
        self,
        output_dir: Union[str, Path],
        video_config: Optional[VideoConfig] = None,
        openai_api_key: Optional[str] = None
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.video_config = video_config or VideoConfig()
        self.video_generator = FFmpegVideoGenerator(self.video_config)
        self.caption_generator = CaptionGenerator(openai_api_key)
    
    async def generate_batch(
        self,
        products: List[ProductData],
        template: TemplateStyle = TemplateStyle.PRODUCT_SHOWCASE,
        generate_videos: bool = True,
        generate_captions: bool = True
    ) -> List[ContentBatch]:
        """
        Gera conteúdo para múltiplos produtos.
        
        Args:
            products: Lista de produtos
            template: Template a usar
            generate_videos: Se deve gerar vídeos
            generate_captions: Se deve gerar legendas
            
        Returns:
            Lista de ContentBatch com caminhos e legendas
        """
        results = []
        
        for i, product in enumerate(products):
            batch = ContentBatch(product=product)
            
            # Gerar vídeo
            if generate_videos:
                video_path = self.output_dir / f"video_{i:03d}_{self._slugify(product.name)}.mp4"
                success = await self.video_generator.create_product_video(
                    product, video_path, template
                )
                if success:
                    batch.video_path = str(video_path)
            
            # Gerar legenda
            if generate_captions:
                batch.caption = self.caption_generator.generate_product_caption(product)
                
                # Extrair hashtags
                import re
                hashtags = re.findall(r'#(\w+)', batch.caption)
                batch.hashtags = hashtags
            
            results.append(batch)
            logger.info(f"Gerado conteúdo para: {product.name}")
        
        return results
    
    def _slugify(self, text: str) -> str:
        """Converte texto para slug."""
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '_', text)
        return text[:50]
