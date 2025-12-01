"""
Content Templates Routes
Reusable templates for social media posts
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import json

from api.middleware.auth import get_current_user
from shared.redis import redis_client

router = APIRouter()


class TemplatePlatform(str, Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    ALL = "all"


class TemplateCategory(str, Enum):
    PRODUCT = "product"
    PROMO = "promo"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    TESTIMONIAL = "testimonial"
    BEHIND_SCENES = "behind_scenes"
    ANNOUNCEMENT = "announcement"
    CUSTOM = "custom"


class TemplateVariable(BaseModel):
    """Variable placeholder in template"""
    name: str = Field(..., description="Variable name, e.g., {{product_name}}")
    description: str = Field(..., description="What this variable represents")
    default_value: Optional[str] = None
    required: bool = True


class TemplateCreate(BaseModel):
    """Create new template"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    platform: TemplatePlatform = TemplatePlatform.ALL
    category: TemplateCategory = TemplateCategory.CUSTOM
    caption_template: str = Field(..., min_length=1, max_length=2200)
    hashtags: List[str] = Field(default_factory=list, max_items=30)
    variables: List[TemplateVariable] = Field(default_factory=list)
    thumbnail_url: Optional[str] = None
    is_public: bool = False


class TemplateUpdate(BaseModel):
    """Update template"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    platform: Optional[TemplatePlatform] = None
    category: Optional[TemplateCategory] = None
    caption_template: Optional[str] = Field(None, min_length=1, max_length=2200)
    hashtags: Optional[List[str]] = None
    variables: Optional[List[TemplateVariable]] = None
    is_public: Optional[bool] = None


class Template(BaseModel):
    """Template response"""
    id: str
    name: str
    description: Optional[str] = None
    platform: str
    category: str
    caption_template: str
    hashtags: List[str]
    variables: List[Dict[str, Any]]
    thumbnail_url: Optional[str] = None
    is_public: bool
    user_id: str
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0


class RenderRequest(BaseModel):
    """Request to render template"""
    variables: Dict[str, str] = Field(default_factory=dict)
    include_hashtags: bool = True


class TemplateService:
    """Service for managing templates"""
    
    PREFIX = "templates:"
    
    async def create(
        self,
        user_id: str,
        data: TemplateCreate
    ) -> Template:
        """Create new template"""
        template_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        template = {
            "id": template_id,
            "name": data.name,
            "description": data.description,
            "platform": data.platform.value,
            "category": data.category.value,
            "caption_template": data.caption_template,
            "hashtags": json.dumps(data.hashtags),
            "variables": json.dumps([v.model_dump() for v in data.variables]),
            "thumbnail_url": data.thumbnail_url,
            "is_public": str(data.is_public),
            "user_id": user_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "usage_count": "0"
        }
        
        key = f"{self.PREFIX}{user_id}:{template_id}"
        await redis_client.hset(key, mapping=template)
        
        # Add to user's template list
        list_key = f"{self.PREFIX}list:{user_id}"
        await redis_client.sadd(list_key, template_id)
        
        return self._to_template(template)
    
    async def get(self, user_id: str, template_id: str) -> Optional[Template]:
        """Get template by ID"""
        key = f"{self.PREFIX}{user_id}:{template_id}"
        data = await redis_client.hgetall(key)
        
        if not data:
            # Check public templates
            pattern = f"{self.PREFIX}*:{template_id}"
            keys = await redis_client.keys(pattern)
            for k in keys:
                data = await redis_client.hgetall(k)
                if data and data.get("is_public") == "True":
                    return self._to_template(data)
            return None
        
        return self._to_template(data)
    
    async def list(
        self,
        user_id: str,
        platform: Optional[TemplatePlatform] = None,
        category: Optional[TemplateCategory] = None,
        include_public: bool = True
    ) -> List[Template]:
        """List user's templates"""
        templates = []
        
        # User's templates
        list_key = f"{self.PREFIX}list:{user_id}"
        template_ids = await redis_client.smembers(list_key)
        
        for tid in template_ids:
            key = f"{self.PREFIX}{user_id}:{tid}"
            data = await redis_client.hgetall(key)
            if data:
                template = self._to_template(data)
                
                # Filter by platform
                if platform and platform != TemplatePlatform.ALL:
                    if template.platform != platform.value and template.platform != "all":
                        continue
                
                # Filter by category
                if category and template.category != category.value:
                    continue
                
                templates.append(template)
        
        # Include public templates
        if include_public:
            public_templates = await self._get_public_templates(platform, category)
            # Avoid duplicates
            user_ids = {t.id for t in templates}
            for pt in public_templates:
                if pt.id not in user_ids and pt.user_id != user_id:
                    templates.append(pt)
        
        # Sort by usage count (most used first)
        templates.sort(key=lambda t: t.usage_count, reverse=True)
        
        return templates
    
    async def _get_public_templates(
        self,
        platform: Optional[TemplatePlatform] = None,
        category: Optional[TemplateCategory] = None
    ) -> List[Template]:
        """Get public templates"""
        templates = []
        pattern = f"{self.PREFIX}*:*"
        keys = await redis_client.keys(pattern)
        
        for key in keys[:100]:  # Limit for performance
            if ":list:" in key:
                continue
            data = await redis_client.hgetall(key)
            if data and data.get("is_public") == "True":
                template = self._to_template(data)
                
                if platform and platform != TemplatePlatform.ALL:
                    if template.platform != platform.value and template.platform != "all":
                        continue
                
                if category and template.category != category.value:
                    continue
                
                templates.append(template)
        
        return templates
    
    async def update(
        self,
        user_id: str,
        template_id: str,
        data: TemplateUpdate
    ) -> Optional[Template]:
        """Update template"""
        key = f"{self.PREFIX}{user_id}:{template_id}"
        existing = await redis_client.hgetall(key)
        
        if not existing:
            return None
        
        updates = {"updated_at": datetime.utcnow().isoformat()}
        
        if data.name is not None:
            updates["name"] = data.name
        if data.description is not None:
            updates["description"] = data.description
        if data.platform is not None:
            updates["platform"] = data.platform.value
        if data.category is not None:
            updates["category"] = data.category.value
        if data.caption_template is not None:
            updates["caption_template"] = data.caption_template
        if data.hashtags is not None:
            updates["hashtags"] = json.dumps(data.hashtags)
        if data.variables is not None:
            updates["variables"] = json.dumps([v.model_dump() for v in data.variables])
        if data.is_public is not None:
            updates["is_public"] = str(data.is_public)
        
        await redis_client.hset(key, mapping=updates)
        
        updated = await redis_client.hgetall(key)
        return self._to_template(updated)
    
    async def delete(self, user_id: str, template_id: str) -> bool:
        """Delete template"""
        key = f"{self.PREFIX}{user_id}:{template_id}"
        result = await redis_client.delete(key)
        
        if result:
            list_key = f"{self.PREFIX}list:{user_id}"
            await redis_client.srem(list_key, template_id)
        
        return result > 0
    
    async def render(
        self,
        user_id: str,
        template_id: str,
        variables: Dict[str, str],
        include_hashtags: bool = True
    ) -> Dict[str, str]:
        """Render template with variables"""
        template = await self.get(user_id, template_id)
        if not template:
            raise ValueError("Template not found")
        
        # Replace variables
        caption = template.caption_template
        for var_name, var_value in variables.items():
            placeholder = "{{" + var_name + "}}"
            caption = caption.replace(placeholder, var_value)
        
        # Add hashtags
        if include_hashtags and template.hashtags:
            hashtag_str = " ".join(f"#{h}" for h in template.hashtags)
            caption = f"{caption}\n\n{hashtag_str}"
        
        # Increment usage count
        key = f"{self.PREFIX}{template.user_id}:{template_id}"
        await redis_client.hincrby(key, "usage_count", 1)
        
        return {
            "caption": caption,
            "hashtags": template.hashtags,
            "platform": template.platform
        }
    
    async def clone(
        self,
        user_id: str,
        template_id: str,
        new_name: str
    ) -> Template:
        """Clone a template (public or own)"""
        original = await self.get(user_id, template_id)
        if not original:
            raise ValueError("Template not found")
        
        # Create new template from original
        return await self.create(user_id, TemplateCreate(
            name=new_name,
            description=f"Cloned from: {original.name}",
            platform=TemplatePlatform(original.platform),
            category=TemplateCategory(original.category),
            caption_template=original.caption_template,
            hashtags=original.hashtags,
            variables=[TemplateVariable(**v) for v in original.variables],
            is_public=False
        ))
    
    def _to_template(self, data: Dict) -> Template:
        """Convert Redis data to Template"""
        return Template(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            platform=data["platform"],
            category=data["category"],
            caption_template=data["caption_template"],
            hashtags=json.loads(data.get("hashtags", "[]")),
            variables=json.loads(data.get("variables", "[]")),
            thumbnail_url=data.get("thumbnail_url"),
            is_public=data.get("is_public") == "True",
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            usage_count=int(data.get("usage_count", 0))
        )


template_service = TemplateService()


# ============= Default Templates =============

DEFAULT_TEMPLATES = [
    {
        "name": "Produto em Destaque",
        "description": "Template para destacar um produto com preço",
        "platform": "all",
        "category": "product",
        "caption_template": "🔥 {{product_name}}\n\n✨ {{description}}\n\n💰 De R$ {{original_price}} por apenas R$ {{sale_price}}\n\n🛒 Link na bio!",
        "hashtags": ["oferta", "promocao", "compras", "desconto"],
        "variables": [
            {"name": "product_name", "description": "Nome do produto", "required": True},
            {"name": "description", "description": "Descrição curta", "required": True},
            {"name": "original_price", "description": "Preço original", "required": True},
            {"name": "sale_price", "description": "Preço promocional", "required": True}
        ]
    },
    {
        "name": "Comparação de Preços",
        "description": "Comparar preços entre lojas",
        "platform": "all",
        "category": "product",
        "caption_template": "📊 COMPARATIVO DE PREÇOS\n\n{{product_name}}\n\n🏪 {{store1}}: R$ {{price1}}\n🏪 {{store2}}: R$ {{price2}}\n🏪 {{store3}}: R$ {{price3}}\n\n💡 Economize até {{savings}}%!",
        "hashtags": ["comparativo", "economia", "dicasdecompras", "melhorpreco"],
        "variables": [
            {"name": "product_name", "description": "Nome do produto", "required": True},
            {"name": "store1", "description": "Loja 1", "required": True},
            {"name": "price1", "description": "Preço loja 1", "required": True},
            {"name": "store2", "description": "Loja 2", "required": True},
            {"name": "price2", "description": "Preço loja 2", "required": True},
            {"name": "store3", "description": "Loja 3", "required": True},
            {"name": "price3", "description": "Preço loja 3", "required": True},
            {"name": "savings", "description": "% de economia", "required": True}
        ]
    },
    {
        "name": "Cupom de Desconto",
        "description": "Divulgar cupom de desconto",
        "platform": "instagram",
        "category": "promo",
        "caption_template": "🎁 CUPOM EXCLUSIVO!\n\n{{discount}}% OFF em {{store_name}}\n\n🔑 Cupom: {{coupon_code}}\n⏰ Válido até: {{expiry_date}}\n\nCorra que é por tempo limitado! 🏃‍♀️💨",
        "hashtags": ["cupom", "desconto", "promocao", "ofertaexclusiva"],
        "variables": [
            {"name": "discount", "description": "Percentual de desconto", "required": True},
            {"name": "store_name", "description": "Nome da loja", "required": True},
            {"name": "coupon_code", "description": "Código do cupom", "required": True},
            {"name": "expiry_date", "description": "Data de validade", "required": True}
        ]
    },
    {
        "name": "Review de Produto",
        "description": "Template para review",
        "platform": "youtube",
        "category": "educational",
        "caption_template": "📦 REVIEW COMPLETO: {{product_name}}\n\n⭐ Nota: {{rating}}/5\n\n✅ Prós:\n{{pros}}\n\n❌ Contras:\n{{cons}}\n\n💭 {{verdict}}\n\nAssista o vídeo completo para mais detalhes!",
        "hashtags": ["review", "analise", "unboxing", "vale_a_pena"],
        "variables": [
            {"name": "product_name", "description": "Nome do produto", "required": True},
            {"name": "rating", "description": "Nota de 1 a 5", "required": True},
            {"name": "pros", "description": "Pontos positivos", "required": True},
            {"name": "cons", "description": "Pontos negativos", "required": True},
            {"name": "verdict", "description": "Veredicto final", "required": True}
        ]
    },
    {
        "name": "Dica Rápida TikTok",
        "description": "Dica curta para TikTok",
        "platform": "tiktok",
        "category": "educational",
        "caption_template": "💡 DICA: {{tip_title}}\n\n{{tip_content}}\n\nSalva pra não esquecer! 📌",
        "hashtags": ["dica", "dicadodia", "aprendanotiktok", "fyp", "viral"],
        "variables": [
            {"name": "tip_title", "description": "Título da dica", "required": True},
            {"name": "tip_content", "description": "Conteúdo da dica", "required": True}
        ]
    }
]


# ============= Routes =============

@router.get("")
async def list_templates(
    platform: Optional[TemplatePlatform] = None,
    category: Optional[TemplateCategory] = None,
    include_public: bool = True,
    current_user=Depends(get_current_user)
):
    """
    List all available templates.
    
    - **platform**: Filter by platform
    - **category**: Filter by category
    - **include_public**: Include public templates from community
    """
    templates = await template_service.list(
        str(current_user["id"]),
        platform,
        category,
        include_public
    )
    return {"templates": [t.model_dump() for t in templates]}


@router.post("")
async def create_template(
    data: TemplateCreate,
    current_user=Depends(get_current_user)
):
    """Create a new template."""
    template = await template_service.create(str(current_user["id"]), data)
    return template.model_dump()


@router.get("/defaults")
async def get_default_templates():
    """Get built-in default templates."""
    return {"templates": DEFAULT_TEMPLATES}


@router.get("/categories")
async def get_categories():
    """Get available template categories."""
    return {
        "categories": [
            {"value": c.value, "label": c.value.replace("_", " ").title()}
            for c in TemplateCategory
        ]
    }


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    current_user=Depends(get_current_user)
):
    """Get template by ID."""
    template = await template_service.get(str(current_user["id"]), template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    return template.model_dump()


@router.patch("/{template_id}")
async def update_template(
    template_id: str,
    data: TemplateUpdate,
    current_user=Depends(get_current_user)
):
    """Update a template."""
    template = await template_service.update(
        str(current_user["id"]),
        template_id,
        data
    )
    if not template:
        raise HTTPException(404, "Template not found")
    return template.model_dump()


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user=Depends(get_current_user)
):
    """Delete a template."""
    success = await template_service.delete(str(current_user["id"]), template_id)
    if not success:
        raise HTTPException(404, "Template not found")
    return {"status": "deleted"}


@router.post("/{template_id}/render")
async def render_template(
    template_id: str,
    request: RenderRequest,
    current_user=Depends(get_current_user)
):
    """
    Render a template with variables.
    
    Replace {{variable_name}} placeholders with provided values.
    """
    try:
        result = await template_service.render(
            str(current_user["id"]),
            template_id,
            request.variables,
            request.include_hashtags
        )
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/{template_id}/clone")
async def clone_template(
    template_id: str,
    new_name: str = Query(..., min_length=1, max_length=100),
    current_user=Depends(get_current_user)
):
    """Clone a template (public or own) to your library."""
    try:
        template = await template_service.clone(
            str(current_user["id"]),
            template_id,
            new_name
        )
        return template.model_dump()
    except ValueError as e:
        raise HTTPException(404, str(e))
