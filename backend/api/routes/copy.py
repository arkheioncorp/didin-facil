"""
AI Copy Generation Routes
OpenAI proxy with quota management
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.middleware.auth import get_current_user
from api.middleware.quota import check_copy_quota, QuotaExceededError
from api.services.openai import OpenAIService
from api.services.cache import CacheService


router = APIRouter()


class CopyRequest(BaseModel):
    """Copy generation request"""
    product_id: str
    product_title: str
    product_description: Optional[str] = None
    product_price: float
    product_benefits: Optional[List[str]] = None
    copy_type: str = Field(..., pattern="^(ad|description|headline|cta|story)$")
    tone: str = Field(..., pattern="^(professional|casual|urgent|friendly|luxury)$")
    platform: str = Field(default="instagram", pattern="^(instagram|facebook|tiktok|whatsapp|general)$")
    language: str = Field(default="pt-BR")
    max_length: Optional[int] = Field(None, ge=50, le=2000)
    include_emoji: bool = True
    include_hashtags: bool = True
    custom_instructions: Optional[str] = Field(None, max_length=500)


class CopyResponse(BaseModel):
    """Copy generation response"""
    id: str
    copy_text: str
    copy_type: str
    tone: str
    platform: str
    word_count: int
    character_count: int
    created_at: datetime
    cached: bool = False
    quota_remaining: int


class CopyHistoryItem(BaseModel):
    """Copy history item"""
    id: str
    product_id: str
    product_title: str
    copy_type: str
    tone: str
    copy_text: str
    created_at: datetime


class QuotaStatus(BaseModel):
    """User quota status"""
    copies_used: int
    copies_limit: int
    copies_remaining: int
    reset_date: datetime
    plan: str


@router.post("/generate", response_model=CopyResponse)
async def generate_copy(
    request: CopyRequest,
    user: dict = Depends(get_current_user),
):
    """
    Generate AI copy for a product.
    Uses OpenAI GPT-4 with quota enforcement.
    Similar copies are cached to reduce API costs.
    """
    cache = CacheService()
    openai_service = OpenAIService()
    
    # Check quota
    try:
        quota_info = await check_copy_quota(user["id"])
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": str(e),
                "upgrade_url": "/pricing",
                "reset_date": e.reset_date.isoformat() if hasattr(e, 'reset_date') else None
            }
        )
    
    # Check cache for similar copy
    cache_key = cache.build_copy_cache_key(
        product_id=request.product_id,
        copy_type=request.copy_type,
        tone=request.tone,
        platform=request.platform
    )
    
    cached_copy = await cache.get(cache_key)
    if cached_copy:
        return CopyResponse(
            **cached_copy,
            cached=True,
            quota_remaining=quota_info["remaining"]
        )
    
    # Generate copy with OpenAI
    copy_result = await openai_service.generate_copy(
        product_title=request.product_title,
        product_description=request.product_description,
        product_price=request.product_price,
        product_benefits=request.product_benefits,
        copy_type=request.copy_type,
        tone=request.tone,
        platform=request.platform,
        language=request.language,
        max_length=request.max_length,
        include_emoji=request.include_emoji,
        include_hashtags=request.include_hashtags,
        custom_instructions=request.custom_instructions
    )
    
    # Increment quota usage
    await openai_service.increment_quota(user["id"])
    
    # Cache the result
    await cache.set(cache_key, copy_result, ttl=86400)  # 24 hours
    
    # Save to history
    await openai_service.save_to_history(
        user_id=user["id"],
        product_id=request.product_id,
        product_title=request.product_title,
        copy_result=copy_result
    )
    
    return CopyResponse(
        **copy_result,
        cached=False,
        quota_remaining=quota_info["remaining"] - 1
    )


@router.get("/quota", response_model=QuotaStatus)
async def get_quota_status(user: dict = Depends(get_current_user)):
    """Get current user's copy generation quota status"""
    openai_service = OpenAIService()
    quota = await openai_service.get_quota_status(user["id"])
    
    return QuotaStatus(
        copies_used=quota["used"],
        copies_limit=quota["limit"],
        copies_remaining=quota["remaining"],
        reset_date=quota["reset_date"],
        plan=user["plan"]
    )


@router.get("/history", response_model=List[CopyHistoryItem])
async def get_copy_history(
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user),
):
    """Get user's copy generation history"""
    openai_service = OpenAIService()
    history = await openai_service.get_history(
        user_id=user["id"],
        limit=limit,
        offset=offset
    )
    
    return [CopyHistoryItem(**item) for item in history]


@router.get("/templates")
async def get_copy_templates(user: dict = Depends(get_current_user)):
    """
    Get predefined copy templates.
    Used as fallback when OpenAI quota is exceeded.
    """
    return {
        "templates": [
            {
                "id": "urgency",
                "name": "Urgência",
                "template": "🔥 OFERTA IMPERDÍVEL! {product_title} por apenas R${price}! ⚡ Estoque limitado - não perca essa chance única! 👉 Compre agora antes que acabe!",
                "variables": ["product_title", "price"]
            },
            {
                "id": "benefits",
                "name": "Benefícios",
                "template": "✨ {product_title} - Transforme sua rotina!\n\n✅ {benefit_1}\n✅ {benefit_2}\n✅ {benefit_3}\n\n💰 Apenas R${price}\n\n🛒 Link na bio!",
                "variables": ["product_title", "benefit_1", "benefit_2", "benefit_3", "price"]
            },
            {
                "id": "story",
                "name": "Storytelling",
                "template": "Você já se perguntou como seria ter {desired_outcome}? 🤔\n\nEu descobri o {product_title} e minha vida mudou!\n\nAgora você também pode experimentar por apenas R${price} 💫\n\n👇 Arrasta pra cima!",
                "variables": ["desired_outcome", "product_title", "price"]
            },
            {
                "id": "social_proof",
                "name": "Prova Social",
                "template": "⭐⭐⭐⭐⭐ +{reviews_count} avaliações positivas!\n\n{product_title} é o favorito de milhares de clientes!\n\n📦 Frete grátis\n💰 R${price}\n🔒 Compra segura\n\n👉 Garanta o seu agora!",
                "variables": ["reviews_count", "product_title", "price"]
            }
        ]
    }


@router.post("/templates/{template_id}/apply")
async def apply_template(
    template_id: str,
    variables: dict,
    user: dict = Depends(get_current_user),
):
    """
    Apply a predefined template with custom variables.
    Does not count against quota.
    """
    templates = {
        "urgency": "🔥 OFERTA IMPERDÍVEL! {product_title} por apenas R${price}! ⚡ Estoque limitado - não perca essa chance única! 👉 Compre agora antes que acabe!",
        "benefits": "✨ {product_title} - Transforme sua rotina!\n\n✅ {benefit_1}\n✅ {benefit_2}\n✅ {benefit_3}\n\n💰 Apenas R${price}\n\n🛒 Link na bio!",
        "story": "Você já se perguntou como seria ter {desired_outcome}? 🤔\n\nEu descobri o {product_title} e minha vida mudou!\n\nAgora você também pode experimentar por apenas R${price} 💫\n\n👇 Arrasta pra cima!",
        "social_proof": "⭐⭐⭐⭐⭐ +{reviews_count} avaliações positivas!\n\n{product_title} é o favorito de milhares de clientes!\n\n📦 Frete grátis\n💰 R${price}\n🔒 Compra segura\n\n👉 Garanta o seu agora!"
    }
    
    template = templates.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        result = template.format(**variables)
        return {
            "copy_text": result,
            "template_id": template_id,
            "word_count": len(result.split()),
            "character_count": len(result)
        }
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Missing variable: {e}"
        )
