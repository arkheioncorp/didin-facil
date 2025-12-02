"""
AI Copy Generation Routes
OpenAI proxy with credits management
"""

import json
from datetime import datetime
from typing import List, Optional

from api.middleware.auth import get_current_user
from api.middleware.quota import (CREDIT_COSTS, InsufficientCreditsError,
                                  check_credits, deduct_credits)
from api.services.cache import CacheService
from api.services.openai import OpenAIService
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


class CopyRequest(BaseModel):
    """Copy generation request"""
    product_id: str
    product_title: str
    product_description: Optional[str] = None
    product_price: float
    product_benefits: Optional[List[str]] = None
    copy_type: str = Field(..., pattern="^(ad|description|headline|cta|story|facebook_ad|tiktok_hook|product_description|story_reels|email|whatsapp)$")
    tone: str = Field(..., pattern="^(professional|casual|urgent|friendly|luxury|educational|emotional|authority)$")
    platform: str = Field(default="instagram", pattern="^(instagram|facebook|tiktok|whatsapp|general|youtube|email)$")
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
    credits_used: int
    credits_remaining: int


class CopyHistoryItem(BaseModel):
    """Copy history item"""
    id: str
    product_id: str
    product_title: str
    copy_type: str
    tone: str
    copy_text: str
    created_at: datetime


class CreditsStatus(BaseModel):
    """User credits status"""
    balance: int
    total_purchased: int
    total_used: int
    cost_per_copy: int


@router.post("/generate", response_model=CopyResponse)
async def generate_copy(
    request: CopyRequest,
    user: dict = Depends(get_current_user),
):
    """
    Generate AI copy for a product.
    Uses OpenAI GPT-4 with credits system.
    Similar copies are cached to reduce API costs.
    """
    cache = CacheService()
    openai_service = OpenAIService()
    
    # Check credits
    try:
        credits_info = await check_credits(user["id"], "copy")
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": str(e),
                "required": e.required,
                "available": e.available,
                "buy_credits_url": "/subscription"
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
        # Salvar no histórico mesmo se cached (para analytics)
        await openai_service.save_to_history(
            user_id=user["id"],
            product_id=request.product_id,
            product_title=request.product_title,
            copy_result=cached_copy,
            cached=True,
            credits_used=0
        )
        return CopyResponse(
            **cached_copy,
            cached=True,
            credits_used=0,
            credits_remaining=credits_info["balance"]
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

    # Deduct credits
    deduct_result = await deduct_credits(user["id"], "copy")

    # Cache the result
    await cache.set(cache_key, copy_result, ttl=86400)  # 24 hours

    # Save to history
    await openai_service.save_to_history(
        user_id=user["id"],
        product_id=request.product_id,
        product_title=request.product_title,
        copy_result=copy_result,
        cached=False,
        credits_used=deduct_result["cost"]
    )

    return CopyResponse(
        **copy_result,
        cached=False,
        credits_used=deduct_result["cost"],
        credits_remaining=deduct_result["new_balance"]
    )


@router.get("/credits", response_model=CreditsStatus)
async def get_credits_status(user: dict = Depends(get_current_user)):
    """Get current user's credits balance"""
    openai_service = OpenAIService()
    credits = await openai_service.get_credits_status(user["id"])
    
    return CreditsStatus(
        balance=credits["balance"],
        total_purchased=credits["total_purchased"],
        total_used=credits["total_used"],
        cost_per_copy=CREDIT_COSTS["copy"]
    )


# Legacy endpoint for backward compatibility
@router.get("/quota")
async def get_quota_status(user: dict = Depends(get_current_user)):
    """Legacy: Get quota as credits info"""
    openai_service = OpenAIService()
    credits = await openai_service.get_credits_status(user["id"])
    
    return {
        "copies_used": credits["total_used"],
        "copies_limit": -1,  # Unlimited with credits
        "copies_remaining": credits["balance"],
        "reset_date": None,
        "plan": "lifetime"
    }


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


# =============================================================================
# PREFERENCES ENDPOINTS
# =============================================================================


class UserCopyPreferences(BaseModel):
    """User copy preferences"""
    default_copy_type: Optional[str] = None
    default_tone: Optional[str] = None
    default_platform: Optional[str] = None
    default_language: Optional[str] = None
    include_emoji: Optional[bool] = None
    include_hashtags: Optional[bool] = None


class PreferencesResponse(BaseModel):
    """Preferences response"""
    default_copy_type: str
    default_tone: str
    default_platform: str
    default_language: str
    include_emoji: bool
    include_hashtags: bool
    total_copies_generated: int
    most_used_copy_type: Optional[str] = None
    most_used_tone: Optional[str] = None


@router.get("/preferences", response_model=PreferencesResponse)
async def get_user_preferences(user: dict = Depends(get_current_user)):
    """Get user's copy generation preferences"""
    openai_service = OpenAIService()
    prefs = await openai_service.get_user_preferences(user["id"])
    return PreferencesResponse(**prefs)


@router.put("/preferences", response_model=PreferencesResponse)
async def update_user_preferences(
    preferences: UserCopyPreferences,
    user: dict = Depends(get_current_user),
):
    """Update user's copy generation preferences"""
    openai_service = OpenAIService()
    updated = await openai_service.update_user_preferences(
        user["id"],
        preferences.model_dump(exclude_none=True)
    )
    return PreferencesResponse(**updated)


# =============================================================================
# STATS ENDPOINTS
# =============================================================================


class CopyStats(BaseModel):
    """Copy generation statistics"""
    total_copies: int
    total_credits_used: int
    cached_copies: int
    copy_types_used: int
    platforms_used: int
    last_generated: Optional[str] = None
    cache_hit_rate: float = 0.0


@router.get("/stats", response_model=CopyStats)
async def get_copy_stats(user: dict = Depends(get_current_user)):
    """Get user's copy generation statistics"""
    openai_service = OpenAIService()
    stats = await openai_service.get_history_stats(user["id"])

    total = stats.get("total_copies", 0) or 0
    cached = stats.get("cached_copies", 0) or 0
    cache_rate = (cached / total * 100) if total > 0 else 0.0

    return CopyStats(
        total_copies=total,
        total_credits_used=stats.get("total_credits_used", 0) or 0,
        cached_copies=cached,
        copy_types_used=stats.get("copy_types_used", 0) or 0,
        platforms_used=stats.get("platforms_used", 0) or 0,
        last_generated=str(stats["last_generated"]) if stats.get("last_generated") else None,
        cache_hit_rate=round(cache_rate, 2)
    )


# =============================================================================
# INVALIDATE CACHE
# =============================================================================


@router.delete("/cache/{product_id}")
async def invalidate_product_cache(
    product_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Invalidate cache for a specific product.
    Use when product details change.
    """
    cache = CacheService()

    # Deletar todas as variações de cache para este produto
    deleted = await cache.delete_pattern(f"copy:*{product_id}*")

    return {
        "message": f"Cache invalidado para produto {product_id}",
        "keys_deleted": deleted
    }


# =============================================================================
# USER SAVED TEMPLATES
# =============================================================================


class SavedTemplateCreate(BaseModel):
    """Create saved template request"""
    name: str
    caption_template: str
    hashtags: Optional[list[str]] = None  # Array de hashtags
    variables: Optional[dict] = None
    copy_type: Optional[str] = None


class SavedTemplateResponse(BaseModel):
    """Saved template response"""
    id: str  # UUID como string
    name: str
    caption_template: str
    hashtags: Optional[list[str]] = None  # Array de strings
    variables: Optional[dict] = None
    copy_type: Optional[str] = None
    created_at: str
    times_used: int = 0


@router.post("/templates/user", response_model=SavedTemplateResponse, status_code=201)
async def save_user_template(
    template: SavedTemplateCreate,
    user: dict = Depends(get_current_user),
):
    """
    Save a custom template for the user.
    This is called when user clicks "Salvar como Template" in the frontend.
    """
    from api.database.connection import get_db_pool
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO user_saved_templates 
                (user_id, name, caption_template, hashtags, variables, copy_type)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, name, caption_template, hashtags, variables, copy_type,
                      created_at, usage_count
            """,
            user["id"],
            template.name,
            template.caption_template,
            template.hashtags,
            json.dumps(template.variables) if template.variables else None,
            template.copy_type
        )
        
        return SavedTemplateResponse(
            id=str(row["id"]),
            name=row["name"],
            caption_template=row["caption_template"],
            hashtags=list(row["hashtags"]) if row["hashtags"] else None,
            variables=json.loads(row["variables"]) if row["variables"] else None,
            copy_type=row["copy_type"],
            created_at=str(row["created_at"]),
            times_used=row["usage_count"]
        )


@router.get("/templates/user", response_model=list[SavedTemplateResponse])
async def list_user_templates(user: dict = Depends(get_current_user)):
    """List all saved templates for the user"""
    from api.database.connection import get_db_pool
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, name, caption_template, hashtags, variables, copy_type,
                   created_at, usage_count
            FROM user_saved_templates
            WHERE user_id = $1
            ORDER BY usage_count DESC, created_at DESC
            """,
            user["id"]
        )
        
        return [
            SavedTemplateResponse(
                id=str(row["id"]),
                name=row["name"],
                caption_template=row["caption_template"],
                hashtags=list(row["hashtags"]) if row["hashtags"] else None,
                variables=json.loads(row["variables"]) if row["variables"] else None,
                copy_type=row["copy_type"],
                created_at=str(row["created_at"]),
                times_used=row["usage_count"]
            )
            for row in rows
        ]


@router.delete("/templates/user/{template_id}")
async def delete_user_template(
    template_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete a saved template"""
    from api.database.connection import get_db_pool
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM user_saved_templates
            WHERE id = $1 AND user_id = $2
            """,
            template_id,
            user["id"]
        )
        
        if result == "DELETE 0":
            raise HTTPException(
                status_code=404,
                detail="Template não encontrado"
            )
        
        return {"message": "Template deletado com sucesso"}


@router.put("/templates/user/{template_id}/use")
async def increment_template_use(
    template_id: str,
    user: dict = Depends(get_current_user),
):
    """Increment the usage counter for a template"""
    from api.database.connection import get_db_pool
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE user_saved_templates
            SET usage_count = usage_count + 1
            WHERE id = $1 AND user_id = $2
            """,
            template_id,
            user["id"]
        )
        
        if result == "UPDATE 0":
            raise HTTPException(
                status_code=404,
                detail="Template não encontrado"
            )
        
        return {"message": "Uso do template registrado"}

