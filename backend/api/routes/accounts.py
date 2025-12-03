"""
Multi-Account Management Routes
Manage multiple social media accounts per platform
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid
import json

from api.middleware.auth import get_current_user
from shared.redis import redis_client

router = APIRouter()


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    NEEDS_REAUTH = "needs_reauth"


class AccountCreate(BaseModel):
    """Create new account"""
    platform: Platform
    username: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    profile_image: Optional[str] = None
    is_primary: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AccountUpdate(BaseModel):
    """Update account"""
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    profile_image: Optional[str] = None
    is_primary: Optional[bool] = None
    status: Optional[AccountStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class Account(BaseModel):
    """Account response"""
    id: str
    platform: str
    username: str
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    profile_image: Optional[str] = None
    status: str
    is_primary: bool
    user_id: str
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AccountSwitch(BaseModel):
    """Account switch request"""
    account_id: str


class AccountMetrics(BaseModel):
    """Account metrics"""
    followers: int = 0
    following: int = 0
    posts: int = 0
    engagement_rate: float = 0.0
    last_post_date: Optional[datetime] = None


class MultiAccountService:
    """Service for managing multiple accounts"""
    
    PREFIX = "accounts:"
    
    async def create(
        self,
        user_id: str,
        data: AccountCreate
    ) -> Account:
        """Create new account"""
        account_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        # Check if username already exists for this platform
        existing = await self.get_by_username(user_id, data.platform.value, data.username)
        if existing:
            raise ValueError(f"Account @{data.username} already exists for {data.platform.value}")
        
        # If is_primary, unset other primary accounts for this platform
        if data.is_primary:
            await self._unset_primary(user_id, data.platform.value)
        
        account = {
            "id": account_id,
            "platform": data.platform.value,
            "username": data.username,
            "display_name": data.display_name or data.username,
            "profile_url": data.profile_url or "",
            "profile_image": data.profile_image or "",
            "status": AccountStatus.ACTIVE.value,
            "is_primary": str(data.is_primary),
            "user_id": user_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "last_used_at": "",
            "metrics": json.dumps({}),
            "metadata": json.dumps(data.metadata)
        }
        
        key = f"{self.PREFIX}{user_id}:{account_id}"
        await redis_client.hset(key, mapping=account)
        
        # Add to user's account list
        list_key = f"{self.PREFIX}list:{user_id}"
        await redis_client.sadd(list_key, account_id)
        
        # Add to platform list
        platform_key = f"{self.PREFIX}platform:{user_id}:{data.platform.value}"
        await redis_client.sadd(platform_key, account_id)
        
        return self._to_account(account)
    
    async def get(self, user_id: str, account_id: str) -> Optional[Account]:
        """Get account by ID"""
        key = f"{self.PREFIX}{user_id}:{account_id}"
        data = await redis_client.hgetall(key)
        
        if not data:
            return None
        
        return self._to_account(data)
    
    async def get_by_username(
        self,
        user_id: str,
        platform: str,
        username: str
    ) -> Optional[Account]:
        """Get account by username and platform"""
        accounts = await self.list_by_platform(user_id, platform)
        for account in accounts:
            if account.username.lower() == username.lower():
                return account
        return None
    
    async def list(self, user_id: str) -> List[Account]:
        """List all accounts for user"""
        accounts = []
        list_key = f"{self.PREFIX}list:{user_id}"
        account_ids = await redis_client.smembers(list_key)
        
        for aid in account_ids:
            account = await self.get(user_id, aid)
            if account:
                accounts.append(account)
        
        # Sort: primary first, then by platform
        accounts.sort(key=lambda a: (not a.is_primary, a.platform, a.username))
        
        return accounts
    
    async def list_by_platform(
        self,
        user_id: str,
        platform: str
    ) -> List[Account]:
        """List accounts by platform"""
        accounts = []
        platform_key = f"{self.PREFIX}platform:{user_id}:{platform}"
        account_ids = await redis_client.smembers(platform_key)
        
        for aid in account_ids:
            account = await self.get(user_id, aid)
            if account:
                accounts.append(account)
        
        # Sort: primary first, then by username
        accounts.sort(key=lambda a: (not a.is_primary, a.username))
        
        return accounts
    
    async def update(
        self,
        user_id: str,
        account_id: str,
        data: AccountUpdate
    ) -> Optional[Account]:
        """Update account"""
        key = f"{self.PREFIX}{user_id}:{account_id}"
        existing = await redis_client.hgetall(key)
        
        if not existing:
            return None
        
        updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if data.display_name is not None:
            updates["display_name"] = data.display_name
        if data.profile_url is not None:
            updates["profile_url"] = data.profile_url
        if data.profile_image is not None:
            updates["profile_image"] = data.profile_image
        if data.status is not None:
            updates["status"] = data.status.value
        if data.metadata is not None:
            updates["metadata"] = json.dumps(data.metadata)
        if data.is_primary is not None:
            if data.is_primary:
                # Unset other primary accounts
                await self._unset_primary(user_id, existing["platform"])
            updates["is_primary"] = str(data.is_primary)
        
        await redis_client.hset(key, mapping=updates)
        
        updated = await redis_client.hgetall(key)
        return self._to_account(updated)
    
    async def delete(self, user_id: str, account_id: str) -> bool:
        """Delete account"""
        account = await self.get(user_id, account_id)
        if not account:
            return False
        
        key = f"{self.PREFIX}{user_id}:{account_id}"
        result = await redis_client.delete(key)
        
        if result:
            # Remove from lists
            list_key = f"{self.PREFIX}list:{user_id}"
            await redis_client.srem(list_key, account_id)
            
            platform_key = f"{self.PREFIX}platform:{user_id}:{account.platform}"
            await redis_client.srem(platform_key, account_id)
        
        return result > 0
    
    async def switch(
        self,
        user_id: str,
        account_id: str
    ) -> Account:
        """Switch to a different account (mark as active)"""
        account = await self.get(user_id, account_id)
        if not account:
            raise ValueError("Account not found")
        
        # Update last used timestamp
        key = f"{self.PREFIX}{user_id}:{account_id}"
        await redis_client.hset(key, mapping={
            "last_used_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Store active account per platform
        active_key = f"{self.PREFIX}active:{user_id}:{account.platform}"
        await redis_client.set(active_key, account_id)
        
        return await self.get(user_id, account_id)
    
    async def get_active(
        self,
        user_id: str,
        platform: str
    ) -> Optional[Account]:
        """Get currently active account for platform"""
        active_key = f"{self.PREFIX}active:{user_id}:{platform}"
        account_id = await redis_client.get(active_key)
        
        if account_id:
            account = await self.get(user_id, account_id)
            if account:
                return account
        
        # Fallback to primary account
        accounts = await self.list_by_platform(user_id, platform)
        primary = next((a for a in accounts if a.is_primary), None)
        
        if primary:
            return primary
        
        # Fallback to first account
        return accounts[0] if accounts else None
    
    async def update_metrics(
        self,
        user_id: str,
        account_id: str,
        metrics: AccountMetrics
    ) -> Optional[Account]:
        """Update account metrics"""
        key = f"{self.PREFIX}{user_id}:{account_id}"
        existing = await redis_client.hgetall(key)
        
        if not existing:
            return None
        
        await redis_client.hset(key, mapping={
            "metrics": json.dumps(metrics.model_dump(mode="json")),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        return await self.get(user_id, account_id)
    
    async def get_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of all accounts"""
        accounts = await self.list(user_id)
        
        by_platform = {}
        total_followers = 0
        
        for account in accounts:
            platform = account.platform
            if platform not in by_platform:
                by_platform[platform] = {
                    "count": 0,
                    "active": 0,
                    "needs_reauth": 0
                }
            
            by_platform[platform]["count"] += 1
            if account.status == AccountStatus.ACTIVE.value:
                by_platform[platform]["active"] += 1
            elif account.status == AccountStatus.NEEDS_REAUTH.value:
                by_platform[platform]["needs_reauth"] += 1
            
            total_followers += account.metrics.get("followers", 0)
        
        return {
            "total_accounts": len(accounts),
            "total_followers": total_followers,
            "by_platform": by_platform,
            "platforms": list(by_platform.keys())
        }
    
    async def _unset_primary(self, user_id: str, platform: str) -> None:
        """Unset all primary flags for a platform"""
        accounts = await self.list_by_platform(user_id, platform)
        for account in accounts:
            if account.is_primary:
                key = f"{self.PREFIX}{user_id}:{account.id}"
                await redis_client.hset(key, "is_primary", "False")
    
    def _to_account(self, data: Dict) -> Account:
        """Convert Redis data to Account"""
        return Account(
            id=data["id"],
            platform=data["platform"],
            username=data["username"],
            display_name=data.get("display_name"),
            profile_url=data.get("profile_url") or None,
            profile_image=data.get("profile_image") or None,
            status=data.get("status", AccountStatus.ACTIVE.value),
            is_primary=data.get("is_primary") == "True",
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            last_used_at=datetime.fromisoformat(data["last_used_at"]) if data.get("last_used_at") else None,
            metrics=json.loads(data.get("metrics", "{}")),
            metadata=json.loads(data.get("metadata", "{}"))
        )


account_service = MultiAccountService()


# ============= Routes =============

@router.get("")
async def list_accounts(
    platform: Optional[Platform] = None,
    current_user=Depends(get_current_user)
):
    """
    List all connected social media accounts.
    
    - **platform**: Filter by platform (optional)
    """
    if platform:
        accounts = await account_service.list_by_platform(
            str(current_user["id"]),
            platform.value
        )
    else:
        accounts = await account_service.list(str(current_user["id"]))
    
    return {"accounts": [a.model_dump() for a in accounts]}


@router.post("")
async def create_account(
    data: AccountCreate,
    current_user=Depends(get_current_user)
):
    """Add a new social media account."""
    try:
        account = await account_service.create(str(current_user["id"]), data)
        return account.model_dump()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/summary")
async def get_accounts_summary(
    current_user=Depends(get_current_user)
):
    """Get summary of all connected accounts."""
    return await account_service.get_summary(str(current_user["id"]))


@router.get("/active/{platform}")
async def get_active_account(
    platform: Platform,
    current_user=Depends(get_current_user)
):
    """Get currently active account for a platform."""
    account = await account_service.get_active(
        str(current_user["id"]),
        platform.value
    )
    if not account:
        raise HTTPException(404, f"No account found for {platform.value}")
    return account.model_dump()


@router.get("/{account_id}")
async def get_account(
    account_id: str,
    current_user=Depends(get_current_user)
):
    """Get account by ID."""
    account = await account_service.get(str(current_user["id"]), account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    return account.model_dump()


@router.patch("/{account_id}")
async def update_account(
    account_id: str,
    data: AccountUpdate,
    current_user=Depends(get_current_user)
):
    """Update account details."""
    account = await account_service.update(
        str(current_user["id"]),
        account_id,
        data
    )
    if not account:
        raise HTTPException(404, "Account not found")
    return account.model_dump()


@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    current_user=Depends(get_current_user)
):
    """Remove a connected account."""
    success = await account_service.delete(str(current_user["id"]), account_id)
    if not success:
        raise HTTPException(404, "Account not found")
    return {"status": "deleted"}


@router.post("/{account_id}/switch")
async def switch_account(
    account_id: str,
    current_user=Depends(get_current_user)
):
    """
    Switch to a different account.
    Sets this account as the active one for its platform.
    """
    try:
        account = await account_service.switch(str(current_user["id"]), account_id)
        return account.model_dump()
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/{account_id}/set-primary")
async def set_primary_account(
    account_id: str,
    current_user=Depends(get_current_user)
):
    """Set account as primary for its platform."""
    account = await account_service.update(
        str(current_user["id"]),
        account_id,
        AccountUpdate(is_primary=True)
    )
    if not account:
        raise HTTPException(404, "Account not found")
    return account.model_dump()


@router.patch("/{account_id}/metrics")
async def update_account_metrics(
    account_id: str,
    metrics: AccountMetrics,
    current_user=Depends(get_current_user)
):
    """Update account metrics (followers, posts, etc.)."""
    account = await account_service.update_metrics(
        str(current_user["id"]),
        account_id,
        metrics
    )
    if not account:
        raise HTTPException(404, "Account not found")
    return account.model_dump()
