"""
Tests for Instagram Session Manager
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta, timezone
import json

from api.services.instagram_session import (
    InstagramSessionManager,
    InstagramSession,
    InstagramChallenge,
    ChallengeType,
    ChallengeStatus,
    detect_challenge_type,
)


# ============= Challenge Detection Tests =============

class TestDetectChallengeType:
    """Tests for challenge type detection"""

    def test_detect_2fa_challenge(self):
        """Should detect 2FA challenge"""
        error = "CHALLENGE_2FA_REQUIRED: Please enter your authentication code"
        result = detect_challenge_type(error)
        
        assert result.type == ChallengeType.TWO_FACTOR
        assert "authenticator" in result.instructions.lower()

    def test_detect_sms_challenge(self):
        """Should detect SMS verification challenge"""
        error = "CHALLENGE_SMS_REQUIRED: Code sent to +1 *** ***-**12"
        result = detect_challenge_type(error)
        
        assert result.type == ChallengeType.SMS
        assert "sms" in result.methods_available

    def test_detect_email_challenge(self):
        """Should detect email verification challenge"""
        error = "Email verification required. Code sent to j***@gmail.com"
        result = detect_challenge_type(error)
        
        assert result.type == ChallengeType.EMAIL
        assert "email" in result.methods_available

    def test_detect_phone_call_challenge(self):
        """Should detect phone call verification"""
        error = "We will call you with a verification code"
        result = detect_challenge_type(error)
        
        assert result.type == ChallengeType.PHONE_CALL

    def test_detect_captcha_challenge(self):
        """Should detect CAPTCHA challenge"""
        error = "Please complete captcha verification to continue"
        result = detect_challenge_type(error)
        
        assert result.type == ChallengeType.CAPTCHA

    def test_detect_suspicious_login(self):
        """Should detect suspicious login challenge"""
        error = "Suspicious activity detected. Secure your account"
        result = detect_challenge_type(error)
        
        assert result.type == ChallengeType.SUSPICIOUS_LOGIN

    def test_detect_rate_limit(self):
        """Should detect rate limit with retry time"""
        error = "Rate limit exceeded. Try again in 5 minutes"
        result = detect_challenge_type(error)
        
        assert result.type == ChallengeType.RATE_LIMIT
        assert result.retry_after == 300  # 5 minutes in seconds

    def test_detect_rate_limit_hours(self):
        """Should parse hours for rate limit"""
        error = "Too many requests. Wait 2 hours"
        result = detect_challenge_type(error)
        
        assert result.type == ChallengeType.RATE_LIMIT
        assert result.retry_after == 7200  # 2 hours in seconds

    def test_detect_action_blocked(self):
        """Should detect action blocked"""
        error = "Action blocked temporarily"
        result = detect_challenge_type(error)
        
        assert result.type == ChallengeType.ACTION_BLOCKED

    def test_detect_checkpoint(self):
        """Should detect generic checkpoint"""
        error = "challenge_required: verify your account"
        result = detect_challenge_type(error)
        
        assert result.type == ChallengeType.CHECKPOINT

    def test_detect_unknown(self):
        """Should return unknown for unrecognized errors"""
        error = "Some random error"
        result = detect_challenge_type(error)
        
        assert result.type == ChallengeType.UNKNOWN

    def test_extract_email_hint(self):
        """Should extract masked email hint"""
        error = "Email sent to j***@gmail.com"
        result = detect_challenge_type(error)
        
        assert result.contact_hint is not None
        assert "@" in result.contact_hint


# ============= Session Manager Tests =============

@pytest.fixture
def session_manager():
    """Create session manager instance"""
    return InstagramSessionManager()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('api.services.instagram_session.redis_client') as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=True)
        mock.keys = AsyncMock(return_value=[])
        mock.exists = AsyncMock(return_value=False)
        yield mock


class TestInstagramSessionManager:
    """Tests for InstagramSessionManager"""

    @pytest.mark.asyncio
    async def test_backup_session_success(self, session_manager, mock_redis):
        """Should create session backup"""
        settings = {"device_id": "test123", "uuids": {"phone_id": "abc"}}
        
        result = await session_manager.backup_session("testuser", settings)
        
        assert result is True
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert "backup" in call_args[0][0]
        assert "testuser" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_backup_session_failure(self, session_manager, mock_redis):
        """Should handle backup failure"""
        mock_redis.set.side_effect = Exception("Redis error")
        
        result = await session_manager.backup_session("testuser", {})
        
        assert result is False

    @pytest.mark.asyncio
    async def test_restore_session_success(self, session_manager, mock_redis):
        """Should restore session from backup"""
        backup_data = {
            "settings": {"device_id": "test123"},
            "backed_up_at": datetime.now(timezone.utc).isoformat()
        }
        mock_redis.keys.return_value = [
            "instagram:session:backup:testuser:20240101120000"
        ]
        mock_redis.get.return_value = json.dumps(backup_data)
        
        result = await session_manager.restore_session("testuser")
        
        assert result is not None
        assert result["device_id"] == "test123"

    @pytest.mark.asyncio
    async def test_restore_session_no_backup(self, session_manager, mock_redis):
        """Should return None when no backup exists"""
        mock_redis.keys.return_value = []
        
        result = await session_manager.restore_session("testuser")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_session(self, session_manager, mock_redis):
        """Should get session by username"""
        session_data = {
            "settings": {"device_id": "test123"},
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        mock_redis.get.return_value = json.dumps(session_data)
        
        result = await session_manager.get_session("testuser")
        
        assert result is not None
        assert isinstance(result, InstagramSession)
        assert result.username == "testuser"
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_manager, mock_redis):
        """Should return None for non-existent session"""
        mock_redis.get.return_value = None
        
        result = await session_manager.get_session("nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_sessions(self, session_manager, mock_redis):
        """Should list all sessions"""
        mock_redis.keys.return_value = [
            "instagram:session:user1",
            "instagram:session:user2"
        ]
        
        session_data = {
            "settings": {},
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        mock_redis.get.return_value = json.dumps(session_data)
        
        result = await session_manager.get_all_sessions()
        
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_record_challenge(self, session_manager, mock_redis):
        """Should record new challenge"""
        challenge_id = await session_manager.record_challenge(
            username="testuser",
            challenge_type=ChallengeType.TWO_FACTOR,
            message="Enter 2FA code",
            instructions="Use your authenticator app"
        )
        
        assert challenge_id != ""
        assert mock_redis.set.call_count == 2  # By username and by ID

    @pytest.mark.asyncio
    async def test_get_challenge_by_id(self, session_manager, mock_redis):
        """Should get challenge by ID"""
        challenge = InstagramChallenge(
            id="test-challenge-id",
            username="testuser",
            challenge_type=ChallengeType.SMS,
            status=ChallengeStatus.PENDING
        )
        mock_redis.get.return_value = challenge.model_dump_json()
        
        result = await session_manager.get_challenge("test-challenge-id")
        
        assert result is not None
        assert result.id == "test-challenge-id"
        assert result.challenge_type == ChallengeType.SMS

    @pytest.mark.asyncio
    async def test_get_active_challenges(self, session_manager, mock_redis):
        """Should get active challenges"""
        challenge = InstagramChallenge(
            id="test-id",
            username="testuser",
            challenge_type=ChallengeType.EMAIL,
            status=ChallengeStatus.PENDING
        )
        mock_redis.keys.return_value = ["instagram:challenge:id:test-id"]
        mock_redis.get.return_value = challenge.model_dump_json()
        
        result = await session_manager.get_active_challenges()
        
        assert len(result) == 1
        assert result[0].status == ChallengeStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_active_challenges_by_username(self, session_manager, mock_redis):
        """Should filter challenges by username"""
        challenge = InstagramChallenge(
            id="test-id",
            username="testuser",
            challenge_type=ChallengeType.EMAIL,
            status=ChallengeStatus.IN_PROGRESS
        )
        mock_redis.get.return_value = challenge.model_dump_json()
        
        result = await session_manager.get_active_challenges("testuser")
        
        assert len(result) == 1
        assert result[0].username == "testuser"

    @pytest.mark.asyncio
    async def test_update_challenge_status(self, session_manager, mock_redis):
        """Should update challenge status"""
        challenge = InstagramChallenge(
            id="test-id",
            username="testuser",
            challenge_type=ChallengeType.SMS,
            status=ChallengeStatus.PENDING
        )
        mock_redis.get.return_value = challenge.model_dump_json()
        
        result = await session_manager.update_challenge_status(
            "test-id",
            ChallengeStatus.RESOLVED
        )
        
        assert result is True
        # Verify set was called with updated status
        call_args = mock_redis.set.call_args_list
        assert len(call_args) == 2  # Updated both keys

    @pytest.mark.asyncio
    async def test_update_challenge_not_found(self, session_manager, mock_redis):
        """Should return False for non-existent challenge"""
        mock_redis.get.return_value = None
        
        result = await session_manager.update_challenge_status(
            "nonexistent",
            ChallengeStatus.RESOLVED
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_increment_challenge_attempts(self, session_manager, mock_redis):
        """Should increment attempt counter"""
        challenge = InstagramChallenge(
            id="test-id",
            username="testuser",
            challenge_type=ChallengeType.TWO_FACTOR,
            status=ChallengeStatus.PENDING,
            attempts=0
        )
        mock_redis.get.return_value = challenge.model_dump_json()
        
        result = await session_manager.increment_challenge_attempts("test-id")
        
        assert result is True
        # Check that the updated challenge was saved
        call_args = mock_redis.set.call_args
        saved_data = json.loads(call_args[0][1])
        assert saved_data["attempts"] == 1
        assert saved_data["status"] == ChallengeStatus.IN_PROGRESS.value

    @pytest.mark.asyncio
    async def test_detect_challenge_type_method(self, session_manager):
        """Should detect challenge type from error message"""
        result = await session_manager.detect_challenge_type(
            "CHALLENGE_2FA_REQUIRED"
        )
        
        assert result == ChallengeType.TWO_FACTOR


# ============= Model Tests =============

class TestInstagramChallenge:
    """Tests for InstagramChallenge model"""

    def test_create_challenge_with_defaults(self):
        """Should create challenge with default values"""
        challenge = InstagramChallenge(
            username="testuser",
            challenge_type=ChallengeType.SMS
        )
        
        assert challenge.id is not None
        assert challenge.status == ChallengeStatus.PENDING
        assert challenge.attempts == 0
        assert challenge.max_attempts == 5

    def test_challenge_serialization(self):
        """Should serialize to JSON correctly"""
        challenge = InstagramChallenge(
            username="testuser",
            challenge_type=ChallengeType.EMAIL,
            message="Check your email"
        )
        
        json_str = challenge.model_dump_json()
        parsed = json.loads(json_str)
        
        assert parsed["username"] == "testuser"
        assert parsed["challenge_type"] == "email"

    def test_challenge_deserialization(self):
        """Should deserialize from JSON correctly"""
        data = {
            "id": "test-id",
            "username": "testuser",
            "challenge_type": "2fa",
            "status": "pending",
            "attempts": 2
        }
        
        challenge = InstagramChallenge.model_validate(data)
        
        assert challenge.id == "test-id"
        assert challenge.challenge_type == ChallengeType.TWO_FACTOR


class TestInstagramSession:
    """Tests for InstagramSession model"""

    def test_create_session(self):
        """Should create session with correct defaults"""
        session = InstagramSession(
            username="testuser",
            is_valid=True
        )
        
        assert session.username == "testuser"
        assert session.status == "active"
        assert session.is_valid is True

    def test_session_with_dates(self):
        """Should handle date fields correctly"""
        now = datetime.now(timezone.utc)
        session = InstagramSession(
            username="testuser",
            created_at=now,
            expires_at=now + timedelta(days=30)
        )
        
        assert session.created_at == now
        assert session.expires_at > now
