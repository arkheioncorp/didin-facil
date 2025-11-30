"""
TikTok Session Manager
Handles session persistence, backup, and restoration via Redis
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from enum import Enum
import uuid

from shared.redis import redis_client

logger = logging.getLogger(__name__)


class TikTokSessionStatus(str, Enum):
    """Status of a TikTok session"""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALID = "invalid"
    NEEDS_REAUTH = "needs_reauth"


class TikTokSession(BaseModel):
    """TikTok session with status tracking"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    account_name: str
    status: TikTokSessionStatus = TikTokSessionStatus.ACTIVE
    cookies: List[Dict] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_error: Optional[str] = None
    upload_count: int = 0
    metadata: Dict = {}


class TikTokSessionManager:
    """
    Manages TikTok session storage and restoration via Redis.
    
    Features:
    - Store session cookies in Redis (replaces file storage)
    - Auto-restore session on worker restart
    - Track session health and expiration
    - Backup before risky operations
    """
    
    SESSION_PREFIX = "tiktok:session:"
    BACKUP_PREFIX = "tiktok:session:backup:"
    STATS_PREFIX = "tiktok:stats:"
    SESSION_EXPIRY = 60 * 60 * 24 * 30  # 30 days
    BACKUP_EXPIRY = 60 * 60 * 24 * 7  # 7 days for backup
    
    async def save_session(
        self,
        user_id: str,
        account_name: str,
        cookies: List[Dict],
        metadata: Dict = None
    ) -> TikTokSession:
        """
        Save TikTok session to Redis.
        
        Args:
            user_id: Owner user ID
            account_name: TikTok account name
            cookies: List of cookie dictionaries
            metadata: Optional metadata (browser info, etc.)
        
        Returns:
            Created TikTokSession object
        """
        try:
            session = TikTokSession(
                user_id=user_id,
                account_name=account_name,
                cookies=cookies,
                expires_at=datetime.utcnow() + timedelta(days=30),
                metadata=metadata or {}
            )
            
            key = f"{self.SESSION_PREFIX}{user_id}:{account_name}"
            await redis_client.set(
                key,
                session.model_dump_json(),
                ex=self.SESSION_EXPIRY
            )
            
            logger.info(f"TikTok session saved for {account_name}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to save TikTok session: {e}")
            raise
    
    async def get_session(
        self,
        user_id: str,
        account_name: str
    ) -> Optional[TikTokSession]:
        """Get TikTok session by user and account name."""
        try:
            key = f"{self.SESSION_PREFIX}{user_id}:{account_name}"
            data = await redis_client.get(key)
            
            if not data:
                return None
            
            return TikTokSession.model_validate_json(data)
            
        except Exception as e:
            logger.error(f"Failed to get TikTok session: {e}")
            return None
    
    async def get_cookies(
        self,
        user_id: str,
        account_name: str
    ) -> Optional[List[Dict]]:
        """
        Get cookies for a session (for use with Selenium).
        
        Returns:
            List of cookie dictionaries or None if not found
        """
        session = await self.get_session(user_id, account_name)
        if not session:
            return None
        
        # Update last_used
        await self.mark_session_used(user_id, account_name)
        
        return session.cookies
    
    async def mark_session_used(
        self,
        user_id: str,
        account_name: str
    ) -> bool:
        """Mark session as recently used."""
        try:
            session = await self.get_session(user_id, account_name)
            if not session:
                return False
            
            session.last_used = datetime.utcnow()
            session.upload_count += 1
            
            key = f"{self.SESSION_PREFIX}{user_id}:{account_name}"
            await redis_client.set(
                key,
                session.model_dump_json(),
                ex=self.SESSION_EXPIRY
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark session used: {e}")
            return False
    
    async def update_session_status(
        self,
        user_id: str,
        account_name: str,
        status: TikTokSessionStatus,
        error: str = None
    ) -> bool:
        """Update session status (e.g., after login failure)."""
        try:
            session = await self.get_session(user_id, account_name)
            if not session:
                return False
            
            session.status = status
            if error:
                session.last_error = error
            
            key = f"{self.SESSION_PREFIX}{user_id}:{account_name}"
            await redis_client.set(
                key,
                session.model_dump_json(),
                ex=self.SESSION_EXPIRY
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session status: {e}")
            return False
    
    async def backup_session(
        self,
        user_id: str,
        account_name: str
    ) -> bool:
        """
        Create backup of current session.
        
        Useful before risky operations like password change.
        """
        try:
            session = await self.get_session(user_id, account_name)
            if not session:
                return False
            
            ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            backup_key = f"{self.BACKUP_PREFIX}{user_id}:{account_name}:{ts}"
            
            await redis_client.set(
                backup_key,
                session.model_dump_json(),
                ex=self.BACKUP_EXPIRY
            )
            
            logger.info(f"TikTok session backup created for {account_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup TikTok session: {e}")
            return False
    
    async def restore_session(
        self,
        user_id: str,
        account_name: str
    ) -> Optional[TikTokSession]:
        """
        Restore session from most recent backup.
        """
        try:
            pattern = f"{self.BACKUP_PREFIX}{user_id}:{account_name}:*"
            keys = await redis_client.keys(pattern)
            
            if not keys:
                return None
            
            # Sort by timestamp (newest first)
            keys.sort(reverse=True)
            latest_key = keys[0]
            
            data = await redis_client.get(latest_key)
            if not data:
                return None
            
            session = TikTokSession.model_validate_json(data)
            
            # Save as active session
            key = f"{self.SESSION_PREFIX}{user_id}:{account_name}"
            await redis_client.set(
                key,
                session.model_dump_json(),
                ex=self.SESSION_EXPIRY
            )
            
            logger.info(f"TikTok session restored for {account_name}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to restore TikTok session: {e}")
            return None
    
    async def delete_session(
        self,
        user_id: str,
        account_name: str,
        keep_backups: bool = True
    ) -> bool:
        """Delete session (optionally keeping backups)."""
        try:
            key = f"{self.SESSION_PREFIX}{user_id}:{account_name}"
            await redis_client.delete(key)
            
            if not keep_backups:
                pattern = f"{self.BACKUP_PREFIX}{user_id}:{account_name}:*"
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
            
            logger.info(f"TikTok session deleted for {account_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete TikTok session: {e}")
            return False
    
    async def list_sessions(
        self,
        user_id: str
    ) -> List[TikTokSession]:
        """List all sessions for a user."""
        try:
            pattern = f"{self.SESSION_PREFIX}{user_id}:*"
            keys = await redis_client.keys(pattern)
            
            sessions = []
            for key in keys:
                data = await redis_client.get(key)
                if data:
                    session = TikTokSession.model_validate_json(data)
                    sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list TikTok sessions: {e}")
            return []
    
    async def get_session_health(
        self,
        user_id: str,
        account_name: str
    ) -> Dict:
        """
        Get session health information.
        
        Returns:
            Dict with status, is_valid, days_until_expiry, etc.
        """
        session = await self.get_session(user_id, account_name)
        
        if not session:
            return {
                "exists": False,
                "is_valid": False,
                "status": "not_found"
            }
        
        now = datetime.utcnow()
        is_expired = session.expires_at and session.expires_at < now
        
        days_until_expiry = None
        if session.expires_at:
            delta = session.expires_at - now
            days_until_expiry = max(0, delta.days)
        
        return {
            "exists": True,
            "is_valid": not is_expired and session.status == TikTokSessionStatus.ACTIVE,
            "status": session.status.value,
            "is_expired": is_expired,
            "days_until_expiry": days_until_expiry,
            "last_used": session.last_used.isoformat() if session.last_used else None,
            "upload_count": session.upload_count,
            "last_error": session.last_error,
            "has_backup": await self._has_backup(user_id, account_name)
        }
    
    async def _has_backup(
        self,
        user_id: str,
        account_name: str
    ) -> bool:
        """Check if backup exists for session."""
        pattern = f"{self.BACKUP_PREFIX}{user_id}:{account_name}:*"
        keys = await redis_client.keys(pattern)
        return len(keys) > 0
    
    async def update_cookies(
        self,
        user_id: str,
        account_name: str,
        cookies: List[Dict]
    ) -> bool:
        """
        Update session cookies (e.g., after refresh from browser).
        
        Creates backup of old session first.
        """
        try:
            # Backup current session
            await self.backup_session(user_id, account_name)
            
            # Update with new cookies
            session = await self.get_session(user_id, account_name)
            if not session:
                return False
            
            session.cookies = cookies
            session.status = TikTokSessionStatus.ACTIVE
            session.last_error = None
            session.expires_at = datetime.utcnow() + timedelta(days=30)
            
            key = f"{self.SESSION_PREFIX}{user_id}:{account_name}"
            await redis_client.set(
                key,
                session.model_dump_json(),
                ex=self.SESSION_EXPIRY
            )
            
            logger.info(f"TikTok cookies updated for {account_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update TikTok cookies: {e}")
            return False
    
    async def get_stats(self) -> Dict:
        """Get overall TikTok session statistics."""
        try:
            session_keys = await redis_client.keys(f"{self.SESSION_PREFIX}*")
            
            total = 0
            active = 0
            expired = 0
            needs_reauth = 0
            
            for key in session_keys:
                if "backup" in key:
                    continue
                    
                data = await redis_client.get(key)
                if data:
                    total += 1
                    session = TikTokSession.model_validate_json(data)
                    
                    if session.status == TikTokSessionStatus.ACTIVE:
                        if session.expires_at and session.expires_at < datetime.utcnow():
                            expired += 1
                        else:
                            active += 1
                    elif session.status == TikTokSessionStatus.NEEDS_REAUTH:
                        needs_reauth += 1
                    else:
                        expired += 1
            
            return {
                "total_sessions": total,
                "active": active,
                "expired": expired,
                "needs_reauth": needs_reauth
            }
            
        except Exception as e:
            logger.error(f"Failed to get TikTok stats: {e}")
            return {
                "total_sessions": 0,
                "active": 0,
                "expired": 0,
                "needs_reauth": 0
            }


# Singleton for convenience
tiktok_session_manager = TikTokSessionManager()
