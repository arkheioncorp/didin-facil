"""
Instagram Session Manager
Handles session persistence, backup, and challenge detection
"""

import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from enum import Enum

from shared.redis import redis_client

logger = logging.getLogger(__name__)


class ChallengeType(str, Enum):
    """Types of Instagram security challenges"""
    TWO_FACTOR = "2fa"
    SMS = "sms"
    EMAIL = "email"
    PHONE_CALL = "phone_call"
    CAPTCHA = "captcha"
    SUSPICIOUS_LOGIN = "suspicious_login"
    RATE_LIMIT = "rate_limit"
    ACTION_BLOCKED = "action_blocked"
    CHECKPOINT = "checkpoint"
    UNKNOWN = "unknown"


class ChallengeStatus(str, Enum):
    """Status of a challenge"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FAILED = "failed"
    EXPIRED = "expired"


class InstagramChallenge(BaseModel):
    """Challenge information with tracking"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    challenge_type: ChallengeType
    status: ChallengeStatus = ChallengeStatus.PENDING
    message: str = ""
    instructions: str = ""
    methods_available: List[str] = []
    contact_hint: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 5
    metadata: Dict = {}


class InstagramSession(BaseModel):
    """Instagram session with status tracking"""
    username: str
    status: str = "active"
    is_valid: bool = True
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict = {}


class ChallengeInfo(BaseModel):
    """Information about a detected challenge"""
    type: ChallengeType
    message: str
    instructions: str
    methods_available: List[str] = []
    contact_hint: Optional[str] = None
    expires_at: Optional[datetime] = None
    retry_after: Optional[int] = None


# ============= Challenge Detection =============

def detect_challenge_type(error_message: str) -> ChallengeInfo:
    """
    Analyze error message and detect the type of challenge.
    Returns detailed information about the challenge.
    """
    error_lower = error_message.lower()
    
    # 2FA (Two-Factor Authentication)
    if any(x in error_lower for x in ["2fa", "two factor", "two-factor", "authentication app"]):
        return ChallengeInfo(
            type=ChallengeType.TWO_FACTOR,
            message="Two-Factor Authentication Required",
            instructions="Enter the 6-digit code from your authenticator app",
            methods_available=["authenticator_app"]
        )
    
    # SMS Verification
    if any(x in error_lower for x in ["sms", "text message", "phone verification"]):
        phone_hint = None
        match = re.search(r"(\+\d[\d\s\*\-]+)", error_message)
        if match:
            phone_hint = match.group(1)
        
        return ChallengeInfo(
            type=ChallengeType.SMS,
            message="SMS Verification Required",
            instructions="Enter the 6-digit code sent to your phone",
            methods_available=["sms"],
            contact_hint=phone_hint
        )
    
    # Email Verification
    if any(x in error_lower for x in ["email", "e-mail", "mail verification"]):
        email_hint = None
        match = re.search(r"([a-zA-Z\*]+@[a-zA-Z\.]+)", error_message)
        if match:
            email_hint = match.group(1)
        
        return ChallengeInfo(
            type=ChallengeType.EMAIL,
            message="Email Verification Required",
            instructions="Enter the code sent to your email",
            methods_available=["email"],
            contact_hint=email_hint
        )
    
    # Phone Call
    if any(x in error_lower for x in ["phone call", "call you"]):
        return ChallengeInfo(
            type=ChallengeType.PHONE_CALL,
            message="Phone Call Verification Required",
            instructions="Answer the call from Instagram and note the code",
            methods_available=["phone_call"]
        )
    
    # CAPTCHA
    if any(x in error_lower for x in ["captcha", "human verification", "robot"]):
        return ChallengeInfo(
            type=ChallengeType.CAPTCHA,
            message="CAPTCHA Verification Required",
            instructions="Complete CAPTCHA in browser or Instagram app",
            methods_available=["manual_browser"]
        )
    
    # Suspicious Login
    if any(x in error_lower for x in ["suspicious", "unusual activity", "secure your account"]):
        return ChallengeInfo(
            type=ChallengeType.SUSPICIOUS_LOGIN,
            message="Suspicious Login Detected",
            instructions="Verify your identity using available methods",
            methods_available=["email", "sms"]
        )
    
    # Rate Limit
    if any(x in error_lower for x in ["rate limit", "too many requests", "try again later", "wait"]):
        retry_after = None
        match = re.search(r"(\d+)\s*(minute|hour|second)", error_lower)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            if "hour" in unit:
                retry_after = value * 3600
            elif "minute" in unit:
                retry_after = value * 60
            else:
                retry_after = value
        
        return ChallengeInfo(
            type=ChallengeType.RATE_LIMIT,
            message="Rate Limit Exceeded",
            instructions="Wait before trying again",
            methods_available=["wait"],
            retry_after=retry_after or 300
        )
    
    # Action Blocked
    if any(x in error_lower for x in ["action blocked", "blocked", "temporarily"]):
        return ChallengeInfo(
            type=ChallengeType.ACTION_BLOCKED,
            message="Action Temporarily Blocked",
            instructions="Try again later or verify in Instagram app",
            methods_available=["wait", "manual_app"],
            retry_after=3600
        )
    
    # Checkpoint (generic challenge)
    if any(x in error_lower for x in ["checkpoint", "challenge_required", "verify"]):
        return ChallengeInfo(
            type=ChallengeType.CHECKPOINT,
            message="Account Verification Required",
            instructions="Verify via Instagram app or browser",
            methods_available=["email", "sms", "manual_app"]
        )
    
    # Unknown challenge
    return ChallengeInfo(
        type=ChallengeType.UNKNOWN,
        message="Unknown Challenge",
        instructions=f"Unexpected challenge: {error_message[:100]}",
        methods_available=["manual_app"]
    )


# ============= Session Management =============

class InstagramSessionManager:
    """Instance-based session manager for dependency injection"""
    
    SESSION_PREFIX = "instagram:session:"
    BACKUP_PREFIX = "instagram:session:backup:"
    CHALLENGE_PREFIX = "instagram:challenge:"
    CHALLENGE_ID_PREFIX = "instagram:challenge:id:"
    SESSION_EXPIRY = 60 * 60 * 24 * 30  # 30 days
    BACKUP_EXPIRY = 60 * 60 * 24 * 90  # 90 days
    CHALLENGE_EXPIRY = 600  # 10 minutes
    
    async def backup_session(
        self,
        username: str,
        settings: Dict
    ) -> bool:
        """Backup session to Redis with timestamp"""
        try:
            ts = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
            backup_key = f"{self.BACKUP_PREFIX}{username}:{ts}"
            
            backup_data = {
                "settings": settings,
                "backed_up_at": datetime.now(timezone.utc).isoformat(),
                "username": username
            }
            
            await redis_client.set(
                backup_key,
                json.dumps(backup_data),
                ex=self.BACKUP_EXPIRY
            )
            
            logger.info(f"Session backup created for {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup session for {username}: {e}")
            return False
    
    async def restore_session(self, username: str) -> Optional[Dict]:
        """Restore session from most recent backup"""
        try:
            pattern = f"{self.BACKUP_PREFIX}{username}:*"
            keys = await redis_client.keys(pattern)
            
            if not keys:
                return None
            
            keys.sort(reverse=True)
            latest_key = keys[0]
            
            data = await redis_client.get(latest_key)
            if not data:
                return None
            
            backup = json.loads(data)
            return backup.get("settings")
            
        except Exception as e:
            logger.error(f"Failed to restore session for {username}: {e}")
            return None
    
    async def get_session(self, username: str) -> Optional[InstagramSession]:
        """Get session info for a username"""
        try:
            key = f"{self.SESSION_PREFIX}{username}"
            data = await redis_client.get(key)
            
            if not data:
                return None
            
            session_data = json.loads(data)
            saved_at = session_data.get("saved_at")
            
            created = None
            expires = None
            if saved_at:
                created = datetime.fromisoformat(saved_at)
                expires = created + timedelta(days=30)
            
            return InstagramSession(
                username=username,
                status="active",
                is_valid=True,
                created_at=created,
                last_used=created,
                expires_at=expires,
                metadata=session_data.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Failed to get session for {username}: {e}")
            return None
    
    async def get_all_sessions(self) -> List[InstagramSession]:
        """Get all active sessions"""
        try:
            keys = await redis_client.keys(f"{self.SESSION_PREFIX}*")
            sessions = []
            
            for key in keys:
                if "backup" in key or "challenge" in key:
                    continue
                
                username = key.replace(self.SESSION_PREFIX, "")
                session = await self.get_session(username)
                if session:
                    sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get all sessions: {e}")
            return []
    
    async def record_challenge(
        self,
        username: str,
        challenge_type: ChallengeType,
        message: str = "",
        instructions: str = "",
        methods: List[str] = None,
        contact_hint: str = None
    ) -> str:
        """Record a new challenge and return its ID"""
        try:
            challenge = InstagramChallenge(
                username=username,
                challenge_type=challenge_type,
                message=message,
                instructions=instructions,
                methods_available=methods or [],
                contact_hint=contact_hint,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.CHALLENGE_EXPIRY)
            )
            
            key = f"{self.CHALLENGE_PREFIX}{username}"
            await redis_client.set(
                key,
                challenge.model_dump_json(),
                ex=self.CHALLENGE_EXPIRY
            )
            
            id_key = f"{self.CHALLENGE_ID_PREFIX}{challenge.id}"
            await redis_client.set(
                id_key,
                challenge.model_dump_json(),
                ex=self.CHALLENGE_EXPIRY
            )
            
            logger.info(f"Challenge recorded for {username}: {challenge.id}")
            return challenge.id
            
        except Exception as e:
            logger.error(f"Failed to record challenge for {username}: {e}")
            return ""
    
    async def get_challenge(self, challenge_id: str) -> Optional[InstagramChallenge]:
        """Get challenge by ID"""
        try:
            key = f"{self.CHALLENGE_ID_PREFIX}{challenge_id}"
            data = await redis_client.get(key)
            
            if not data:
                return None
            
            return InstagramChallenge.model_validate_json(data)
            
        except Exception as e:
            logger.error(f"Failed to get challenge {challenge_id}: {e}")
            return None
    
    async def get_active_challenges(
        self,
        username: Optional[str] = None
    ) -> List[InstagramChallenge]:
        """Get all active challenges, optionally filtered by username"""
        try:
            if username:
                key = f"{self.CHALLENGE_PREFIX}{username}"
                data = await redis_client.get(key)
                if not data:
                    return []
                return [InstagramChallenge.model_validate_json(data)]
            
            keys = await redis_client.keys(f"{self.CHALLENGE_ID_PREFIX}*")
            challenges = []
            
            for key in keys:
                data = await redis_client.get(key)
                if data:
                    challenge = InstagramChallenge.model_validate_json(data)
                    if challenge.status in [
                        ChallengeStatus.PENDING,
                        ChallengeStatus.IN_PROGRESS
                    ]:
                        challenges.append(challenge)
            
            return challenges
            
        except Exception as e:
            logger.error(f"Failed to get active challenges: {e}")
            return []
    
    async def update_challenge_status(
        self,
        challenge_id: str,
        status: ChallengeStatus,
        message: str = None
    ) -> bool:
        """Update challenge status"""
        try:
            challenge = await self.get_challenge(challenge_id)
            if not challenge:
                return False
            
            challenge.status = status
            if message:
                challenge.message = message
            if status == ChallengeStatus.RESOLVED:
                challenge.resolved_at = datetime.now(timezone.utc)
            
            key = f"{self.CHALLENGE_PREFIX}{challenge.username}"
            id_key = f"{self.CHALLENGE_ID_PREFIX}{challenge_id}"
            
            data = challenge.model_dump_json()
            await redis_client.set(key, data, ex=self.CHALLENGE_EXPIRY)
            await redis_client.set(id_key, data, ex=self.CHALLENGE_EXPIRY)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update challenge {challenge_id}: {e}")
            return False
    
    async def increment_challenge_attempts(self, challenge_id: str) -> bool:
        """Increment attempt counter for a challenge"""
        try:
            challenge = await self.get_challenge(challenge_id)
            if not challenge:
                return False
            
            challenge.attempts += 1
            challenge.status = ChallengeStatus.IN_PROGRESS
            
            key = f"{self.CHALLENGE_PREFIX}{challenge.username}"
            id_key = f"{self.CHALLENGE_ID_PREFIX}{challenge_id}"
            
            data = challenge.model_dump_json()
            await redis_client.set(key, data, ex=self.CHALLENGE_EXPIRY)
            await redis_client.set(id_key, data, ex=self.CHALLENGE_EXPIRY)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to increment attempts for {challenge_id}: {e}")
            return False
    
    async def detect_challenge_type(
        self,
        error_message: str
    ) -> Optional[ChallengeType]:
        """Detect challenge type from error message"""
        info = detect_challenge_type(error_message)
        return info.type if info else None
