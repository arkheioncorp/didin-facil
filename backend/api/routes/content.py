"""
Content Generator Routes
Geração automática de vídeos e imagens para redes sociais
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime

from api.middleware.auth import get_current_user
from vendor.content_generator.generator import (
    FFmpegVideoGenerator, VideoConfig, ProductData,
    TextSlide, AspectRatio
)
from shared.config import settings

router = APIRouter()


class ProductVideoRequest(BaseModel):
    """Request para gerar vídeo de produto."""
    product_name: str
    price: float
    original_price: Optional[float] = None
    store: str = ""
    image_url: Optional[str] = None
    aspect_ratio: str = "portrait"  # portrait, landscape, square
    duration: int = 15
    template: str = "product_showcase"


class TextVideoRequest(BaseModel):
    """Request para gerar vídeo de texto."""
    slides: List[dict]
    aspect_ratio: str = "portrait"
    background_color: str = "#1a1a2e"
    text_color: str = "#ffffff"


class DealAlertRequest(BaseModel):
    """Request para gerar alerta de oferta."""
    products: List[dict]
    title: str = "🔥 OFERTAS DO DIA"
    aspect_ratio: str = "portrait"


@router.post("/product-video")
async def generate_product_video(
    data: ProductVideoRequest,
    current_user=Depends(get_current_user)
):
    """
    Gera vídeo curto (Reels/TikTok/Shorts) para um produto.
    
    O vídeo inclui:
    - Imagem do produto
    - Nome e preço
    - Desconto (se houver)
    - Animações
    """
    output_dir = os.path.join(
        settings.DATA_DIR, "generated_videos", str(current_user.id)
    )
    os.makedirs(output_dir, exist_ok=True)
    
    # Mapear aspect ratio
    ratio_map = {
        "portrait": AspectRatio.PORTRAIT,
        "landscape": AspectRatio.LANDSCAPE,
        "square": AspectRatio.SQUARE
    }
    
    # Configurar vídeo
    video_config = VideoConfig(
        aspect_ratio=ratio_map.get(data.aspect_ratio, AspectRatio.PORTRAIT),
        duration=data.duration
    )
    
    # Dados do produto
    product = ProductData(
        name=data.product_name,
        price=data.price,
        original_price=data.original_price,
        store=data.store,
        image_url=data.image_url
    )
    
    try:
        generator = FFmpegVideoGenerator(video_config)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            output_dir, f"product_{timestamp}.mp4"
        )
        
        result = await generator.generate_product_showcase(
            product=product,
            output_path=output_path
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Erro ao gerar vídeo")
            )
        
        # Retornar URL relativa para download
        relative_path = f"generated_videos/{current_user.id}/product_{timestamp}.mp4"
        
        return {
            "status": "success",
            "file_path": output_path,
            "download_url": f"/content/download/{relative_path}",
            "duration": data.duration,
            "dimensions": video_config.get_dimensions()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text-video")
async def generate_text_video(
    data: TextVideoRequest,
    current_user=Depends(get_current_user)
):
    """
    Gera vídeo com slides de texto animados.
    
    Útil para:
    - Dicas
    - Citações
    - Anúncios simples
    """
    output_dir = os.path.join(
        settings.DATA_DIR, "generated_videos", str(current_user.id)
    )
    os.makedirs(output_dir, exist_ok=True)
    
    ratio_map = {
        "portrait": AspectRatio.PORTRAIT,
        "landscape": AspectRatio.LANDSCAPE,
        "square": AspectRatio.SQUARE
    }
    
    video_config = VideoConfig(
        aspect_ratio=ratio_map.get(data.aspect_ratio, AspectRatio.PORTRAIT),
        background_color=data.background_color,
        text_color=data.text_color
    )
    
    # Converter slides
    slides = [
        TextSlide(
            text=s.get("text", ""),
            duration=s.get("duration", 3.0),
            animation=s.get("animation", "fade")
        )
        for s in data.slides
    ]
    
    try:
        generator = FFmpegVideoGenerator(video_config)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            output_dir, f"text_{timestamp}.mp4"
        )
        
        result = await generator.generate_text_animation(
            slides=slides,
            output_path=output_path
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Erro ao gerar vídeo")
            )
        
        relative_path = f"generated_videos/{current_user.id}/text_{timestamp}.mp4"
        
        return {
            "status": "success",
            "file_path": output_path,
            "download_url": f"/content/download/{relative_path}",
            "slides_count": len(slides)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deal-alert")
async def generate_deal_alert(
    data: DealAlertRequest,
    current_user=Depends(get_current_user)
):
    """
    Gera vídeo de alerta de ofertas com múltiplos produtos.
    
    Formato:
    - Título animado
    - Produtos em sequência
    - CTA no final
    """
    output_dir = os.path.join(
        settings.DATA_DIR, "generated_videos", str(current_user.id)
    )
    os.makedirs(output_dir, exist_ok=True)
    
    ratio_map = {
        "portrait": AspectRatio.PORTRAIT,
        "landscape": AspectRatio.LANDSCAPE,
        "square": AspectRatio.SQUARE
    }
    
    video_config = VideoConfig(
        aspect_ratio=ratio_map.get(data.aspect_ratio, AspectRatio.PORTRAIT)
    )
    
    # Converter produtos
    products = [
        ProductData(
            name=p.get("name", ""),
            price=p.get("price", 0),
            original_price=p.get("original_price"),
            store=p.get("store", ""),
            image_url=p.get("image_url")
        )
        for p in data.products
    ]
    
    try:
        generator = FFmpegVideoGenerator(video_config)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            output_dir, f"deals_{timestamp}.mp4"
        )
        
        result = await generator.generate_deal_compilation(
            products=products,
            title=data.title,
            output_path=output_path
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Erro ao gerar vídeo")
            )
        
        relative_path = f"generated_videos/{current_user.id}/deals_{timestamp}.mp4"
        
        return {
            "status": "success",
            "file_path": output_path,
            "download_url": f"/content/download/{relative_path}",
            "products_count": len(products)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{path:path}")
async def download_file(
    path: str,
    current_user=Depends(get_current_user)
):
    """Download de arquivo gerado."""
    from fastapi.responses import FileResponse
    
    # Verificar se o path pertence ao usuário
    if not path.startswith(f"generated_videos/{current_user.id}/"):
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    full_path = os.path.join(settings.DATA_DIR, path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(
        full_path,
        media_type="video/mp4",
        filename=os.path.basename(full_path)
    )


@router.get("/templates")
async def list_templates():
    """Lista templates disponíveis para geração de conteúdo."""
    return {
        "templates": [
            {
                "id": "product_showcase",
                "name": "Vitrine de Produto",
                "description": "Mostra produto com preço e desconto",
                "best_for": ["TikTok", "Reels", "Shorts"]
            },
            {
                "id": "price_comparison",
                "name": "Comparação de Preços",
                "description": "Compara preços entre lojas",
                "best_for": ["TikTok", "Reels"]
            },
            {
                "id": "deal_alert",
                "name": "Alerta de Oferta",
                "description": "Compilação de ofertas",
                "best_for": ["Stories", "TikTok"]
            },
            {
                "id": "text_animation",
                "name": "Texto Animado",
                "description": "Slides de texto com animações",
                "best_for": ["TikTok", "Reels", "Stories"]
            }
        ]
    }
