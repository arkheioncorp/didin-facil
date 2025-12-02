"""
OpenAI Service
AI copy generation with credits system and cost tracking
"""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from api.database.connection import database, get_db
from api.services.accounting import AccountingService
from api.services.cache import CacheService
from openai import AsyncOpenAI

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
                "SELECT credits_balance, has_lifetime_license FROM users WHERE id = :user_id",
                {"user_id": user_id}
            )

        credits = user["credits_balance"] if user else 0
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
                SET credits_balance = credits_balance - :amount,
                    credits_used = credits_used + :amount
                WHERE id = :user_id AND credits_balance >= :amount
                RETURNING credits_balance
                """,
                {"user_id": user_id, "amount": amount}
            )
            return result if result else 0
    
    async def save_to_history(
        self,
        user_id: str,
        product_id: str,
        product_title: str,
        copy_result: dict,
        cached: bool = False,
        credits_used: int = 1
    ):
        """Save generated copy to user history"""
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO copy_history
                    (id, user_id, product_id, product_title, copy_type,
                     platform, tone, copy_text, word_count, character_count,
                     cached, credits_used, created_at)
                VALUES
                    (:id, :user_id, :product_id, :product_title, :copy_type,
                     :platform, :tone, :copy_text, :word_count, :character_count,
                     :cached, :credits_used, :created_at)
                """,
                {
                    "id": copy_result["id"],
                    "user_id": user_id,
                    "product_id": product_id,
                    "product_title": product_title,
                    "copy_type": copy_result["copy_type"],
                    "platform": copy_result.get("platform", "instagram"),
                    "tone": copy_result["tone"],
                    "copy_text": copy_result["copy_text"],
                    "word_count": copy_result.get("word_count", 0),
                    "character_count": copy_result.get("character_count", 0),
                    "cached": cached,
                    "credits_used": credits_used,
                    "created_at": copy_result["created_at"]
                }
            )

            # Atualizar preferências do usuário com analytics
            await self._update_user_copy_analytics(db, user_id, copy_result)

    async def _update_user_copy_analytics(
        self, db, user_id: str, copy_result: dict
    ):
        """Atualiza analytics de uso do usuário"""
        await db.execute(
            """
            INSERT INTO user_copy_preferences
                (user_id, total_copies_generated, last_copy_generated_at,
                 most_used_copy_type, most_used_tone)
            VALUES (:user_id, 1, NOW(), :copy_type, :tone)
            ON CONFLICT (user_id) DO UPDATE SET
                total_copies_generated =
                    user_copy_preferences.total_copies_generated + 1,
                last_copy_generated_at = NOW(),
                most_used_copy_type = :copy_type,
                most_used_tone = :tone,
                updated_at = NOW()
            """,
            {
                "user_id": user_id,
                "copy_type": copy_result["copy_type"],
                "tone": copy_result["tone"]
            }
        )
    
    async def get_user_preferences(self, user_id: str) -> dict:
        """Obtém preferências de Copy AI do usuário"""
        async with get_db() as db:
            result = await db.fetch_one(
                """
                SELECT * FROM user_copy_preferences WHERE user_id = :user_id
                """,
                {"user_id": user_id}
            )
            
            if result:
                return dict(result)
            
            # Retorna defaults se não existir
            return {
                "default_copy_type": "tiktok_hook",
                "default_tone": "urgent",
                "default_platform": "instagram",
                "default_language": "pt-BR",
                "include_emoji": True,
                "include_hashtags": True,
                "total_copies_generated": 0
            }
    
    async def update_user_preferences(self, user_id: str, preferences: dict) -> dict:
        """Atualiza preferências de Copy AI do usuário"""
        async with get_db() as db:
            # Upsert
            await db.execute(
                """
                INSERT INTO user_copy_preferences (user_id, default_copy_type, default_tone, default_platform, 
                                                   default_language, include_emoji, include_hashtags)
                VALUES (:user_id, :copy_type, :tone, :platform, :language, :emoji, :hashtags)
                ON CONFLICT (user_id) DO UPDATE SET
                    default_copy_type = COALESCE(:copy_type, user_copy_preferences.default_copy_type),
                    default_tone = COALESCE(:tone, user_copy_preferences.default_tone),
                    default_platform = COALESCE(:platform, user_copy_preferences.default_platform),
                    default_language = COALESCE(:language, user_copy_preferences.default_language),
                    include_emoji = COALESCE(:emoji, user_copy_preferences.include_emoji),
                    include_hashtags = COALESCE(:hashtags, user_copy_preferences.include_hashtags),
                    updated_at = NOW()
                """,
                {
                    "user_id": user_id,
                    "copy_type": preferences.get("default_copy_type"),
                    "tone": preferences.get("default_tone"),
                    "platform": preferences.get("default_platform"),
                    "language": preferences.get("default_language"),
                    "emoji": preferences.get("include_emoji"),
                    "hashtags": preferences.get("include_hashtags")
                }
            )
            
            return await self.get_user_preferences(user_id)
    
    async def get_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        copy_type: Optional[str] = None,
        platform: Optional[str] = None
    ) -> List[dict]:
        """Get user's copy generation history with optional filters"""
        async with get_db() as db:
            query = """
                SELECT id, product_id, product_title, copy_type, platform, tone, 
                       copy_text, word_count, character_count, cached, credits_used, created_at
                FROM copy_history
                WHERE user_id = :user_id
            """
            params = {"user_id": user_id, "limit": limit, "offset": offset}
            
            if copy_type:
                query += " AND copy_type = :copy_type"
                params["copy_type"] = copy_type
            
            if platform:
                query += " AND platform = :platform"
                params["platform"] = platform
            
            query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            
            results = await db.fetch_all(query, params)
        
        return [dict(r) for r in results]
    
    async def get_history_stats(self, user_id: str) -> dict:
        """Obtém estatísticas de uso do histórico"""
        async with get_db() as db:
            stats = await db.fetch_one(
                """
                SELECT 
                    COUNT(*) as total_copies,
                    SUM(credits_used) as total_credits_used,
                    SUM(CASE WHEN cached THEN 1 ELSE 0 END) as cached_copies,
                    COUNT(DISTINCT copy_type) as copy_types_used,
                    COUNT(DISTINCT platform) as platforms_used,
                    MAX(created_at) as last_generated
                FROM copy_history
                WHERE user_id = :user_id
                """,
                {"user_id": user_id}
            )
            
            return dict(stats) if stats else {
                "total_copies": 0,
                "total_credits_used": 0,
                "cached_copies": 0,
                "copy_types_used": 0,
                "platforms_used": 0,
                "last_generated": None
            }
