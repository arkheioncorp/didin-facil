"""
Quota Management Middleware
User quota validation and enforcement
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status

from api.database.connection import database


class QuotaExceededError(Exception):
    """Raised when user exceeds their plan quota"""
    def __init__(self, message: str, reset_date: datetime = None):
        self.message = message
        self.reset_date = reset_date
        super().__init__(self.message)


# Plan quotas configuration
PLAN_QUOTAS = {
    "trial": {
        "searches_per_month": 10,
        "copies_per_month": 5,
        "exports_per_month": 0,
    },
    "basic": {
        "searches_per_month": 100,
        "copies_per_month": 50,
        "exports_per_month": 10,
    },
    "pro": {
        "searches_per_month": -1,  # Unlimited
        "copies_per_month": -1,    # Unlimited
        "exports_per_month": -1,   # Unlimited
    },
    "enterprise": {
        "searches_per_month": -1,
        "copies_per_month": -1,
        "exports_per_month": -1,
    }
}


async def get_user_quota(user_id: str, quota_type: str, db) -> dict:
    """
    Get current quota usage for a user.
    
    Returns:
        dict: {used: int, limit: int, remaining: int, reset_date: datetime}
    """
    # Get current period (month start)
    now = datetime.utcnow()
    period_start = datetime(now.year, now.month, 1)
    period_end = (period_start + timedelta(days=32)).replace(day=1)
    
    # Get user's plan
    user_query = "SELECT plan FROM users WHERE id = $1"
    user = await db.fetchrow(user_query, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    plan = user["plan"]
    quota_key = f"{quota_type}_per_month"
    limit = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["trial"]).get(quota_key, 0)
    
    # Get current usage
    usage_query = """
        SELECT COALESCE(SUM(count), 0) as used
        FROM quota_usage
        WHERE user_id = $1 
          AND quota_type = $2
          AND created_at >= $3
          AND created_at < $4
    """
    result = await db.fetchrow(usage_query, user_id, quota_type, period_start, period_end)
    used = result["used"] if result else 0
    
    # Calculate remaining (-1 means unlimited)
    remaining = -1 if limit == -1 else max(0, limit - used)
    
    return {
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "reset_date": period_end,
        "plan": plan
    }


async def increment_quota(user_id: str, quota_type: str, count: int = 1, db = None):
    """Increment quota usage for a user"""
    query = """
        INSERT INTO quota_usage (user_id, quota_type, count, created_at)
        VALUES ($1, $2, $3, NOW())
    """
    await db.execute(query, user_id, quota_type, count)


async def check_quota(user_id: str, quota_type: str = "searches", db = None) -> dict:
    """
    Check if user has remaining quota.
    
    Raises:
        QuotaExceededError: If quota is exceeded
    """
    quota = await get_user_quota(user_id, quota_type, db)
    
    if quota["limit"] != -1 and quota["remaining"] <= 0:
        raise QuotaExceededError(
            f"You have exceeded your monthly {quota_type} limit ({quota['limit']})",
            reset_date=quota["reset_date"]
        )
    
    return quota


async def check_copy_quota(user_id: str, db = None) -> dict:
    """Check specifically copy generation quota"""
    return await check_quota(user_id, "copies", db)
