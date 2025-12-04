"""
Copy Generation Use Cases
=========================

Business logic for AI-powered copy generation.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Literal, Optional, Protocol
from uuid import UUID

from domain.usecases.base import UseCase, UseCaseResult

# ==================== Types ====================

CopyType = Literal[
    "tiktok_caption",
    "instagram_caption",
    "product_description",
    "ad_copy",
    "email_marketing",
    "blog_post",
]

CopyTone = Literal[
    "professional",
    "casual",
    "funny",
    "urgent",
    "inspirational",
    "educational",
]


# ==================== Repository Interfaces ====================

class CopyHistoryRepository(Protocol):
    """Interface for copy history repository."""
    
    async def save(
        self,
        user_id: UUID,
        product_id: Optional[UUID],
        copy_type: str,
        tone: str,
        prompt: str,
        result: str,
        tokens_used: int,
    ) -> dict:
        """Save generated copy to history."""
        ...
    
    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        copy_type: Optional[str] = None,
    ) -> List[dict]:
        """List copy history for a user."""
        ...
    
    async def count_by_user(
        self,
        user_id: UUID,
        copy_type: Optional[str] = None,
    ) -> int:
        """Count copy history items for a user."""
        ...


class AIService(Protocol):
    """Interface for AI service (OpenAI, etc.)."""
    
    async def generate_copy(
        self,
        prompt: str,
        copy_type: str,
        tone: str,
        max_tokens: int = 500,
    ) -> tuple[str, int]:
        """
        Generate copy using AI.
        
        Returns:
            Tuple of (generated_text, tokens_used)
        """
        ...


class CreditService(Protocol):
    """Interface for credit management service."""
    
    async def has_credits(self, user_id: UUID, amount: int = 1) -> bool:
        """Check if user has enough credits."""
        ...
    
    async def deduct_credits(
        self,
        user_id: UUID,
        amount: int,
        reason: str,
    ) -> bool:
        """Deduct credits from user balance."""
        ...


class ProductRepository(Protocol):
    """Interface for product repository."""
    
    async def get_by_id(self, product_id: UUID) -> Optional[dict]:
        """Get product by ID."""
        ...


# ==================== Input/Output DTOs ====================

@dataclass(frozen=True)
class GenerateCopyInput:
    """Input for generating copy."""
    user_id: UUID
    product_id: Optional[UUID]
    copy_type: CopyType
    tone: CopyTone
    custom_instructions: Optional[str] = None
    language: str = "pt-BR"


@dataclass(frozen=True)
class GetCopyHistoryInput:
    """Input for getting copy history."""
    user_id: UUID
    limit: int = 50
    offset: int = 0
    copy_type: Optional[CopyType] = None


@dataclass
class GeneratedCopyOutput:
    """Output for generated copy."""
    id: UUID
    copy_type: str
    tone: str
    content: str
    tokens_used: int
    credits_charged: int
    created_at: datetime


@dataclass
class CopyHistoryItem:
    """Single copy history item."""
    id: UUID
    product_id: Optional[UUID]
    copy_type: str
    tone: str
    content: str
    tokens_used: int
    created_at: datetime


@dataclass
class CopyHistoryOutput:
    """Output for copy history."""
    items: List[CopyHistoryItem]
    total: int
    has_more: bool


# ==================== Use Cases ====================

# Cost per copy type (in credits)
COPY_COSTS = {
    "tiktok_caption": 1,
    "instagram_caption": 1,
    "product_description": 2,
    "ad_copy": 3,
    "email_marketing": 3,
    "blog_post": 5,
}


class GenerateCopyUseCase(UseCase[GenerateCopyInput, GeneratedCopyOutput]):
    """
    Generate AI-powered marketing copy.
    
    Business Rules:
    - User must have sufficient credits
    - If product_id provided, include product details in prompt
    - Deduct credits after successful generation
    - Save to history for future reference
    """
    
    def __init__(
        self,
        copy_history_repo: CopyHistoryRepository,
        ai_service: AIService,
        credit_service: CreditService,
        product_repo: ProductRepository,
    ):
        self.copy_history_repo = copy_history_repo
        self.ai_service = ai_service
        self.credit_service = credit_service
        self.product_repo = product_repo
    
    async def execute(
        self, input: GenerateCopyInput
    ) -> UseCaseResult[GeneratedCopyOutput]:
        # Calculate credit cost
        credit_cost = COPY_COSTS.get(input.copy_type, 1)
        
        # Check credits
        has_credits = await self.credit_service.has_credits(
            input.user_id, credit_cost
        )
        if not has_credits:
            return UseCaseResult.fail(
                f"Insufficient credits. Need {credit_cost} credits.",
                error_code="INSUFFICIENT_CREDITS"
            )
        
        # Build prompt
        prompt = await self._build_prompt(input)
        
        # Generate copy
        try:
            content, tokens = await self.ai_service.generate_copy(
                prompt=prompt,
                copy_type=input.copy_type,
                tone=input.tone,
            )
        except Exception as e:
            return UseCaseResult.fail(
                f"AI generation failed: {str(e)}",
                error_code="AI_ERROR"
            )
        
        # Deduct credits
        await self.credit_service.deduct_credits(
            user_id=input.user_id,
            amount=credit_cost,
            reason=f"copy_generation:{input.copy_type}",
        )
        
        # Save to history
        record = await self.copy_history_repo.save(
            user_id=input.user_id,
            product_id=input.product_id,
            copy_type=input.copy_type,
            tone=input.tone,
            prompt=prompt,
            result=content,
            tokens_used=tokens,
        )
        
        output = GeneratedCopyOutput(
            id=record["id"],
            copy_type=input.copy_type,
            tone=input.tone,
            content=content,
            tokens_used=tokens,
            credits_charged=credit_cost,
            created_at=record["created_at"],
        )
        
        return UseCaseResult.ok(output)
    
    async def _build_prompt(self, input: GenerateCopyInput) -> str:
        """Build the AI prompt based on input."""
        parts = []
        
        # Add product context if available
        if input.product_id:
            product = await self.product_repo.get_by_id(input.product_id)
            if product:
                parts.append(f"Product: {product.get('title', 'Unknown')}")
                if product.get("description"):
                    parts.append(f"Description: {product['description'][:500]}")
                if product.get("price"):
                    parts.append(f"Price: R$ {product['price']:.2f}")
        
        # Add instructions
        parts.append(f"Generate a {input.copy_type} in {input.language}")
        parts.append(f"Tone: {input.tone}")
        
        if input.custom_instructions:
            parts.append(f"Additional instructions: {input.custom_instructions}")
        
        return "\n".join(parts)


class GetCopyHistoryUseCase(UseCase[GetCopyHistoryInput, CopyHistoryOutput]):
    """
    Get user's copy generation history.
    
    Business Rules:
    - Returns paginated results
    - Can filter by copy type
    - Orders by most recent first
    """
    
    def __init__(self, copy_history_repo: CopyHistoryRepository):
        self.copy_history_repo = copy_history_repo
    
    async def execute(
        self, input: GetCopyHistoryInput
    ) -> UseCaseResult[CopyHistoryOutput]:
        # Get history items
        items = await self.copy_history_repo.list_by_user(
            user_id=input.user_id,
            limit=input.limit,
            offset=input.offset,
            copy_type=input.copy_type,
        )
        
        # Get total count
        total = await self.copy_history_repo.count_by_user(
            user_id=input.user_id,
            copy_type=input.copy_type,
        )
        
        # Map to output
        history_items = [
            CopyHistoryItem(
                id=item["id"],
                product_id=item.get("product_id"),
                copy_type=item["copy_type"],
                tone=item["tone"],
                content=item["result"],
                tokens_used=item["tokens_used"],
                created_at=item["created_at"],
            )
            for item in items
        ]
        
        output = CopyHistoryOutput(
            items=history_items,
            total=total,
            has_more=input.offset + len(history_items) < total,
        )
        
        return UseCaseResult.ok(output)
