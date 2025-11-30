"""
OpenAI Service
AI copy generation with credits system and cost tracking
"""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from openai import AsyncOpenAI

from api.database.connection import database, get_db
from api.services.cache import CacheService
from api.services.accounting import AccountingService


# OpenAI settings from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")


class OpenAIService:
    """OpenAI API proxy with credits management and cost tracking"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.cache_service = CacheService()
        self.model = OPENAI_MODEL
        self.db = database
        self.accounting = AccountingService()
    
    async def generate_copy(
        self,
        product_title: str,
        product_description: Optional[str],
        product_price: float,
        product_benefits: Optional[List[str]],
        copy_type: str,
        tone: str,
        platform: str,
        language: str = "pt-BR",
        max_length: Optional[int] = None,
        include_emoji: bool = True,
        include_hashtags: bool = True,
        custom_instructions: Optional[str] = None,
    ) -> dict:
        """Generate marketing copy using OpenAI"""
        
        # Build prompt
        prompt = self._build_prompt(
            product_title=product_title,
            product_description=product_description,
            product_price=product_price,
            product_benefits=product_benefits,
            copy_type=copy_type,
            tone=tone,
            platform=platform,
            language=language,
            max_length=max_length,
            include_emoji=include_emoji,
            include_hashtags=include_hashtags,
            custom_instructions=custom_instructions
        )
        
        # Call OpenAI API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt(platform, language)
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=max_length or 500,
            temperature=0.7
        )
        
        copy_text = response.choices[0].message.content.strip()
        
        # Track token usage for accounting
        usage = response.usage
        if usage:
            await self.accounting.track_openai_usage(
                operation_type="copy_generation",
                model=self.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                user_id=None  # Will be set by route
            )
        
        return {
            "id": str(uuid.uuid4()),
            "copy_text": copy_text,
            "copy_type": copy_type,
            "tone": tone,
            "platform": platform,
            "word_count": len(copy_text.split()),
            "character_count": len(copy_text),
            "tokens_used": usage.total_tokens if usage else 0,
            "created_at": datetime.now(timezone.utc)
        }
    
    def _get_system_prompt(self, platform: str, language: str) -> str:
        """Get system prompt based on platform"""
        
        platform_guidelines = {
            "instagram": """Você é um especialista em copywriting para Instagram.
                - Use parágrafos curtos e espaçados
                - Emojis são essenciais para engajamento
                - Inclua hashtags relevantes no final
                - CTAs devem ser diretos (Link na bio, Arrasta pra cima)
                - Limite: 2200 caracteres""",
            
            "facebook": """Você é um especialista em copywriting para Facebook.
                - Posts podem ser mais longos e detalhados
                - Storytelling funciona bem
                - Use perguntas para gerar engajamento
                - CTAs podem ser mais explicativos""",
            
            "tiktok": """Você é um especialista em copywriting para TikTok.
                - Seja extremamente conciso e direto
                - Use linguagem jovem e casual
                - Trending phrases funcionam bem
                - Máximo 150 caracteres para caption""",
            
            "whatsapp": """Você é um especialista em copywriting para WhatsApp.
                - Formato de mensagem direta
                - Use bullet points para benefícios
                - Seja pessoal e conversacional
                - Inclua urgência quando apropriado""",
            
            "general": """Você é um especialista em copywriting para vendas.
                - Adapte o tom conforme solicitado
                - Foque nos benefícios do produto
                - Use gatilhos mentais apropriados
                - Seja persuasivo mas não agressivo"""
        }
        
        base_prompt = f"""Você é um copywriter brasileiro especializado em dropshipping e e-commerce.
        
{platform_guidelines.get(platform, platform_guidelines['general'])}

Idioma: {language}
Sempre responda APENAS com o texto da copy, sem explicações ou comentários adicionais."""
        
        return base_prompt
    
    def _build_prompt(
        self,
        product_title: str,
        product_description: Optional[str],
        product_price: float,
        product_benefits: Optional[List[str]],
        copy_type: str,
        tone: str,
        platform: str,
        language: str,
        max_length: Optional[int],
        include_emoji: bool,
        include_hashtags: bool,
        custom_instructions: Optional[str],
    ) -> str:
        """Build the user prompt for copy generation"""
        
        copy_type_instructions = {
            "ad": "Crie um anúncio persuasivo focado em conversão",
            "description": "Crie uma descrição de produto completa e atraente",
            "headline": "Crie 5 opções de títulos/headlines impactantes",
            "cta": "Crie 5 opções de call-to-action diferentes",
            "story": "Crie um texto de storytelling vendedor",
            "facebook_ad": "Crie um anúncio para Facebook/Instagram focado em conversão",
            "tiktok_hook": "Crie um roteiro de vídeo curto para TikTok com gancho viral",
            "product_description": "Crie uma descrição de produto detalhada e persuasiva",
            "story_reels": "Crie um roteiro para Stories ou Reels do Instagram",
            "email": "Crie um email marketing de vendas",
            "whatsapp": "Crie uma mensagem de vendas para WhatsApp"
        }
        
        tone_instructions = {
            "professional": "Tom profissional e confiável",
            "casual": "Tom casual e descontraído",
            "urgent": "Tom de urgência e escassez",
            "friendly": "Tom amigável e próximo",
            "luxury": "Tom premium e exclusivo",
            "educational": "Tom educativo e informativo",
            "emotional": "Tom emocional que conecta com o leitor",
            "authority": "Tom de autoridade e especialista"
        }
        
        prompt = f"""**Produto:** {product_title}
**Preço:** R$ {product_price:.2f}
"""
        
        if product_description:
            prompt += f"**Descrição:** {product_description}\n"
        
        if product_benefits:
            benefits_str = "\n".join(f"- {b}" for b in product_benefits)
            prompt += f"**Benefícios:**\n{benefits_str}\n"
        
        prompt += f"""
**Tipo de Copy:** {copy_type_instructions.get(copy_type, copy_type)}
**Tom:** {tone_instructions.get(tone, tone)}
**Plataforma:** {platform}
"""
        
        if include_emoji:
            prompt += "**Incluir:** Emojis relevantes\n"
        
        if include_hashtags and platform in ["instagram", "tiktok"]:
            prompt += "**Incluir:** 5-10 hashtags relevantes no final\n"
        
        if max_length:
            prompt += f"**Limite:** Máximo {max_length} caracteres\n"
        
        if custom_instructions:
            prompt += f"**Instruções adicionais:** {custom_instructions}\n"
        
        prompt += "\nGere a copy agora:"

        return prompt

    async def get_credits_status(self, user_id: str) -> dict:
        """Get user's credits balance"""
        async with get_db() as db:
            user = await db.fetch_one(
                "SELECT credits, has_lifetime_license FROM users WHERE id = :user_id",
                {"user_id": user_id}
            )

        credits = user["credits"] if user else 0
        has_license = user["has_lifetime_license"] if user else False

        return {
            "credits": credits,
            "has_lifetime_license": has_license
        }

    async def deduct_credits(self, user_id: str, amount: int = 1) -> int:
        """Deduct credits from user's balance"""
        async with get_db() as db:
            result = await db.execute(
                """
                UPDATE users 
                SET credits = credits - :amount 
                WHERE id = :user_id AND credits >= :amount
                RETURNING credits
                """,
                {"user_id": user_id, "amount": amount}
            )
            return result if result else 0
    
    async def save_to_history(
        self,
        user_id: str,
        product_id: str,
        product_title: str,
        copy_result: dict
    ):
        """Save generated copy to user history"""
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO copy_history 
                (id, user_id, product_id, product_title, copy_type, tone, copy_text, created_at)
                VALUES (:id, :user_id, :product_id, :product_title, :copy_type, :tone, :copy_text, :created_at)
                """,
                {
                    "id": copy_result["id"],
                    "user_id": user_id,
                    "product_id": product_id,
                    "product_title": product_title,
                    "copy_type": copy_result["copy_type"],
                    "tone": copy_result["tone"],
                    "copy_text": copy_result["copy_text"],
                    "created_at": copy_result["created_at"]
                }
            )
    
    async def get_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """Get user's copy generation history"""
        async with get_db() as db:
            results = await db.fetch_all(
                """
                SELECT id, product_id, product_title, copy_type, tone, copy_text, created_at
                FROM copy_history
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
                """,
                {"user_id": user_id, "limit": limit, "offset": offset}
            )
        
        return [dict(r) for r in results]
