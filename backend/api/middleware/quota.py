"""
Credits Management Middleware
User credits validation and management for AI features
"""

from typing import Optional

from fastapi import HTTPException


class InsufficientCreditsError(Exception):
    """Raised when user doesn't have enough credits"""
    def __init__(self, message: str, required: int = 0, available: int = 0):
        self.message = message
        self.required = required
        self.available = available
        super().__init__(self.message)


# Legacy: QuotaExceededError alias for backward compatibility
QuotaExceededError = InsufficientCreditsError


# Credit costs per action
CREDIT_COSTS = {
    "copy": 1,              # 1 credit per copy generated
    "trend_analysis": 2,    # 2 credits per trend analysis
    "niche_report": 5,      # 5 credits per niche report
}


async def get_user_credits(user_id: str, db) -> dict:
    """
    Get current credit balance for a user.
    
    Returns:
        dict: {balance: int, total_purchased: int, total_used: int}
    """
    # Get user's credit balance
    query = """
        SELECT 
            COALESCE(credits_balance, 0) as balance,
            COALESCE(credits_purchased, 0) as total_purchased,
            COALESCE(credits_used, 0) as total_used
        FROM users WHERE id = $1
    """
    result = await db.fetchrow(query, user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "balance": result["balance"],
        "total_purchased": result["total_purchased"],
        "total_used": result["total_used"]
    }


async def check_credits(user_id: str, action: str = "copy", db = None) -> dict:
    """
    Check if user has enough credits for an action.
    
    Raises:
        InsufficientCreditsError: If credits are insufficient
    """
    required = CREDIT_COSTS.get(action, 1)
    credits = await get_user_credits(user_id, db)
    
    if credits["balance"] < required:
        raise InsufficientCreditsError(
            f"Créditos insuficientes. Você precisa de {required} crédito(s) para esta ação.",
            required=required,
            available=credits["balance"]
        )
    
    return {
        "balance": credits["balance"],
        "required": required,
        "remaining_after": credits["balance"] - required
    }


async def deduct_credits(user_id: str, action: str = "copy", db = None) -> dict:
    """Deduct credits for an action"""
    cost = CREDIT_COSTS.get(action, 1)
    
    query = """
        UPDATE users 
        SET credits_balance = credits_balance - $2,
            credits_used = credits_used + $2,
            updated_at = NOW()
        WHERE id = $1 AND credits_balance >= $2
        RETURNING credits_balance as new_balance
    """
    result = await db.fetchrow(query, user_id, cost)
    
    if not result:
        raise InsufficientCreditsError(
            "Créditos insuficientes",
            required=cost,
            available=0
        )
    
    return {"new_balance": result["new_balance"], "cost": cost}


async def add_credits(user_id: str, amount: int, payment_id: Optional[str] = None, db = None) -> dict:
    """Add credits to user account after purchase"""
    query = """
        UPDATE users 
        SET credits_balance = credits_balance + $2,
            credits_purchased = credits_purchased + $2,
            updated_at = NOW()
        WHERE id = $1
        RETURNING credits_balance as new_balance
    """
    result = await db.fetchrow(query, user_id, amount)
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log the purchase
    if payment_id:
        log_query = """
            INSERT INTO credit_purchases (user_id, amount, payment_id, created_at)
            VALUES ($1, $2, $3, NOW())
        """
        await db.execute(log_query, user_id, amount, payment_id)
    
    return {"new_balance": result["new_balance"], "added": amount}


# Legacy function aliases for backward compatibility
async def check_copy_quota(user_id: str, db = None) -> dict:
    """Legacy: Check credits for copy generation"""
    return await check_credits(user_id, "copy", db)


async def get_user_quota(user_id: str, quota_type: str, db) -> dict:
    """Legacy: Get quota as credits"""
    credits = await get_user_credits(user_id, db)
    return {
        "used": credits["total_used"],
        "limit": -1,  # No limit, just balance
        "remaining": credits["balance"],
        "reset_date": None,
        "plan": "lifetime"
    }


async def increment_quota(user_id: str, quota_type: str, count: int = 1, db = None):
    """Legacy: Increment quota = deduct credits"""
    await deduct_credits(user_id, quota_type, db)
