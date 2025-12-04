"""
Comprehensive tests for Instagram Session Manager.
Tests session persistence, backup, and challenge detection.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from api.services.instagram_session import (ChallengeInfo, ChallengeStatus,
                                            ChallengeType, InstagramChallenge,
                                            InstagramSession,
                                            InstagramSessionManager,
                                            detect_challenge_type)

# ============================================================================
# detect_challenge_type Function Tests
# ============================================================================

class TestDetectChallengeType:
    """Tests for detect_challenge_type function."""
    
    def test_detect_2fa(self):
        """Should detect two-factor authentication."""
        result = detect_challenge_type("Please enter your 2FA code")
        
        assert result.type == ChallengeType.TWO_FACTOR
        assert "Two-Factor" in result.message
        assert "authenticator_app" in result.methods_available
    
    def test_detect_two_factor(self):
        """Should detect two factor authentication."""
        result = detect_challenge_type("Two factor authentication required")
        
        assert result.type == ChallengeType.TWO_FACTOR
    
    def test_detect_sms(self):
        """Should detect SMS verification."""
        result = detect_challenge_type("Enter SMS code sent to +55 11 9****-5678")
        
        assert result.type == ChallengeType.SMS
        assert "sms" in result.methods_available
        assert result.contact_hint is not None
    
    def test_detect_sms_with_phone_hint(self):
        """Should extract phone hint from message."""
        result = detect_challenge_type("SMS sent to +1 555 123 4567")
        
        assert result.type == ChallengeType.SMS
        assert result.contact_hint is not None
    
    def test_detect_email(self):
        """Should detect email verification."""
        result = detect_challenge_type("Email verification sent to t***@gmail.com")
        
        assert result.type == ChallengeType.EMAIL
        assert "email" in result.methods_available
    
    def test_detect_email_with_hint(self):
        """Should extract email hint from message."""
        result = detect_challenge_type("Check your email at test***@example.com")
        
        assert result.type == ChallengeType.EMAIL
    
    def test_detect_phone_call(self):
        """Should detect phone call verification."""
        result = detect_challenge_type("We will call you with a code")
        
        assert result.type == ChallengeType.PHONE_CALL
        assert "phone_call" in result.methods_available
    
    def test_detect_captcha(self):
        """Should detect CAPTCHA challenge."""
        result = detect_challenge_type("Complete the captcha to continue")
        
        assert result.type == ChallengeType.CAPTCHA
        assert "manual_browser" in result.methods_available
    
    def test_detect_captcha_robot(self):
        """Should detect robot check."""
        result = detect_challenge_type("Please prove you're not a robot")
        
        assert result.type == ChallengeType.CAPTCHA
    
    def test_detect_suspicious_login(self):
        """Should detect suspicious login."""
        result = detect_challenge_type("Suspicious activity detected on your account")
        
        assert result.type == ChallengeType.SUSPICIOUS_LOGIN
    
    def test_detect_rate_limit(self):
        """Should detect rate limit."""
        result = detect_challenge_type("Too many requests, try again later")
        
        assert result.type == ChallengeType.RATE_LIMIT
        assert "wait" in result.methods_available
        assert result.retry_after is not None
    
    def test_detect_rate_limit_with_time(self):
        """Should extract wait time from message."""
        result = detect_challenge_type("Rate limit exceeded, wait 5 minutes")
        
        assert result.type == ChallengeType.RATE_LIMIT
        assert result.retry_after == 300  # 5 * 60
    
    def test_detect_rate_limit_hours(self):
        """Should handle hours in rate limit."""
        result = detect_challenge_type("Wait 2 hours before trying again")
        
        assert result.type == ChallengeType.RATE_LIMIT
        assert result.retry_after == 7200  # 2 * 3600
    
    def test_detect_action_blocked(self):
        """Should detect action blocked."""
        result = detect_challenge_type("Action blocked temporarily")
        
        assert result.type == ChallengeType.ACTION_BLOCKED
        assert result.retry_after is not None
    
    def test_detect_checkpoint(self):
        """Should detect checkpoint challenge."""
        result = detect_challenge_type("Checkpoint required, verify your account")
        
        assert result.type == ChallengeType.CHECKPOINT
    
    def test_detect_unknown(self):
        """Should return unknown for unrecognized challenges."""
        result = detect_challenge_type("Some random error message")
        
        assert result.type == ChallengeType.UNKNOWN
        assert "manual_app" in result.methods_available


# ============================================================================
# ChallengeType Enum Tests
# ============================================================================

class TestChallengeTypeEnum:
    """Tests for ChallengeType enum."""
    
    def test_challenge_type_values(self):
        """Should have correct values."""
        assert ChallengeType.TWO_FACTOR.value == "2fa"
        assert ChallengeType.SMS.value == "sms"
        assert ChallengeType.EMAIL.value == "email"
        assert ChallengeType.PHONE_CALL.value == "phone_call"
        assert ChallengeType.CAPTCHA.value == "captcha"
        assert ChallengeType.RATE_LIMIT.value == "rate_limit"


class TestChallengeStatusEnum:
    """Tests for ChallengeStatus enum."""
    
    def test_challenge_status_values(self):
        """Should have correct values."""
        assert ChallengeStatus.PENDING.value == "pending"
        assert ChallengeStatus.IN_PROGRESS.value == "in_progress"
        assert ChallengeStatus.RESOLVED.value == "resolved"
        assert ChallengeStatus.FAILED.value == "failed"
        assert ChallengeStatus.EXPIRED.value == "expired"


# ============================================================================
# InstagramChallenge Model Tests
# ============================================================================

class TestInstagramChallengeModel:
    """Tests for InstagramChallenge Pydantic model."""
    
    def test_create_challenge_default(self):
        """Should create challenge with defaults."""
        challenge = InstagramChallenge(
            username="test_user",
            challenge_type=ChallengeType.SMS
        )
        
        assert challenge.username == "test_user"
        assert challenge.challenge_type == ChallengeType.SMS
        assert challenge.status == ChallengeStatus.PENDING
        assert challenge.attempts == 0
        assert challenge.max_attempts == 5
        assert challenge.id is not None
    
    def test_challenge_serialization(self):
        """Should serialize/deserialize correctly."""
        challenge = InstagramChallenge(
            username="test_user",
            challenge_type=ChallengeType.EMAIL,
            message="Check email"
        )
        
        json_str = challenge.model_dump_json()
        restored = InstagramChallenge.model_validate_json(json_str)
        
        assert restored.username == challenge.username
        assert restored.challenge_type == challenge.challenge_type
        assert restored.message == challenge.message


# ============================================================================
# InstagramSession Model Tests
# ============================================================================

class TestInstagramSessionModel:
    """Tests for InstagramSession Pydantic model."""
    
    def test_create_session_default(self):
        """Should create session with defaults."""
        session = InstagramSession(username="test_user")
        
        assert session.username == "test_user"
        assert session.status == "active"
        assert session.is_valid is True
        assert session.metadata == {}
    
    def test_create_session_with_metadata(self):
        """Should create session with metadata."""
        session = InstagramSession(
            username="test_user",
            metadata={"device": "iPhone"}
        )
        
        assert session.metadata["device"] == "iPhone"


# ============================================================================
# InstagramSessionManager Tests
# ============================================================================

class TestInstagramSessionManagerInit:
    """Tests for InstagramSessionManager initialization."""
    
    def test_manager_prefixes(self):
        """Should have correct prefixes."""
        manager = InstagramSessionManager()
        
        assert manager.SESSION_PREFIX == "instagram:session:"
        assert manager.BACKUP_PREFIX == "instagram:session:backup:"
        assert manager.CHALLENGE_PREFIX == "instagram:challenge:"
    
    def test_manager_expiry_times(self):
        """Should have correct expiry times."""
        manager = InstagramSessionManager()
        
        assert manager.SESSION_EXPIRY == 60 * 60 * 24 * 30  # 30 days
        assert manager.BACKUP_EXPIRY == 60 * 60 * 24 * 90  # 90 days
        assert manager.CHALLENGE_EXPIRY == 600  # 10 minutes


class TestBackupSession:
    """Tests for backup_session method."""
    
    @pytest.fixture
    def manager(self):
        return InstagramSessionManager()
    
    @pytest.mark.asyncio
    async def test_backup_session_success(self, manager):
        """Should backup session to Redis."""
        settings = {"device_id": "abc123", "uuid": "xyz789"}
        
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(return_value=True)
            
            result = await manager.backup_session("test_user", settings)
            
            assert result is True
            mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backup_session_error(self, manager):
        """Should return False on error."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(side_effect=Exception("Redis error"))
            
            result = await manager.backup_session("test_user", {})
            
            assert result is False


class TestRestoreSession:
    """Tests for restore_session method."""
    
    @pytest.fixture
    def manager(self):
        return InstagramSessionManager()
    
    @pytest.mark.asyncio
    async def test_restore_session_success(self, manager):
        """Should restore from most recent backup."""
        backup_data = {
            "settings": {"device_id": "restored123"},
            "backed_up_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[
                "instagram:session:backup:test_user:20240115120000",
                "instagram:session:backup:test_user:20240114120000"
            ])
            mock_redis.get = AsyncMock(return_value=json.dumps(backup_data))
            
            result = await manager.restore_session("test_user")
            
            assert result == {"device_id": "restored123"}
    
    @pytest.mark.asyncio
    async def test_restore_session_no_backups(self, manager):
        """Should return None when no backups exist."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await manager.restore_session("test_user")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_restore_session_error(self, manager):
        """Should return None on error."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(side_effect=Exception("Redis error"))
            
            result = await manager.restore_session("test_user")
            
            assert result is None


class TestGetSession:
    """Tests for get_session method."""
    
    @pytest.fixture
    def manager(self):
        return InstagramSessionManager()
    
    @pytest.mark.asyncio
    async def test_get_session_found(self, manager):
        """Should return session when found."""
        session_data = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"device": "Android"}
        }
        
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=json.dumps(session_data))
            
            result = await manager.get_session("test_user")
            
            assert result is not None
            assert result.username == "test_user"
            assert result.status == "active"
            assert result.is_valid is True
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, manager):
        """Should return None when session not found."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.get_session("nonexistent")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_session_error(self, manager):
        """Should return None on error."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
            
            result = await manager.get_session("test_user")
            
            assert result is None


class TestGetAllSessions:
    """Tests for get_all_sessions method."""
    
    @pytest.fixture
    def manager(self):
        return InstagramSessionManager()
    
    @pytest.mark.asyncio
    async def test_get_all_sessions_found(self, manager):
        """Should return all sessions."""
        session_data = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {}
        }
        
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[
                "instagram:session:user1",
                "instagram:session:user2"
            ])
            mock_redis.get = AsyncMock(return_value=json.dumps(session_data))
            
            result = await manager.get_all_sessions()
            
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_get_all_sessions_filters_backups(self, manager):
        """Should filter out backup keys."""
        session_data = {
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[
                "instagram:session:user1",
                "instagram:session:backup:user1:20240115",  # Should be filtered
                "instagram:session:challenge:user1"  # Should be filtered
            ])
            mock_redis.get = AsyncMock(return_value=json.dumps(session_data))
            
            result = await manager.get_all_sessions()
            
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_all_sessions_empty(self, manager):
        """Should return empty list when no sessions."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await manager.get_all_sessions()
            
            assert result == []


class TestRecordChallenge:
    """Tests for record_challenge method."""
    
    @pytest.fixture
    def manager(self):
        return InstagramSessionManager()
    
    @pytest.mark.asyncio
    async def test_record_challenge_success(self, manager):
        """Should record challenge and return ID."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(return_value=True)
            
            challenge_id = await manager.record_challenge(
                username="test_user",
                challenge_type=ChallengeType.SMS,
                message="Enter SMS code",
                instructions="Check your phone",
                methods=["sms"],
                contact_hint="+55 11 9****"
            )
            
            assert challenge_id != ""
            assert mock_redis.set.call_count == 2  # Main + ID key
    
    @pytest.mark.asyncio
    async def test_record_challenge_error(self, manager):
        """Should return empty string on error."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(side_effect=Exception("Redis error"))
            
            challenge_id = await manager.record_challenge(
                username="test_user",
                challenge_type=ChallengeType.SMS
            )
            
            assert challenge_id == ""


class TestGetChallenge:
    """Tests for get_challenge method."""
    
    @pytest.fixture
    def manager(self):
        return InstagramSessionManager()
    
    @pytest.mark.asyncio
    async def test_get_challenge_found(self, manager):
        """Should return challenge when found."""
        challenge = InstagramChallenge(
            username="test_user",
            challenge_type=ChallengeType.EMAIL
        )
        
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=challenge.model_dump_json())
            
            result = await manager.get_challenge(challenge.id)
            
            assert result is not None
            assert result.username == "test_user"
            assert result.challenge_type == ChallengeType.EMAIL
    
    @pytest.mark.asyncio
    async def test_get_challenge_not_found(self, manager):
        """Should return None when not found."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.get_challenge("nonexistent-id")
            
            assert result is None


class TestGetActiveChallenges:
    """Tests for get_active_challenges method."""
    
    @pytest.fixture
    def manager(self):
        return InstagramSessionManager()
    
    @pytest.mark.asyncio
    async def test_get_active_challenges_by_username(self, manager):
        """Should return challenges for specific user."""
        challenge = InstagramChallenge(
            username="test_user",
            challenge_type=ChallengeType.SMS
        )
        
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=challenge.model_dump_json())
            
            result = await manager.get_active_challenges("test_user")
            
            assert len(result) == 1
            assert result[0].username == "test_user"
    
    @pytest.mark.asyncio
    async def test_get_active_challenges_all(self, manager):
        """Should return all active challenges."""
        pending_challenge = InstagramChallenge(
            username="user1",
            challenge_type=ChallengeType.SMS,
            status=ChallengeStatus.PENDING
        )
        in_progress = InstagramChallenge(
            username="user2",
            challenge_type=ChallengeType.EMAIL,
            status=ChallengeStatus.IN_PROGRESS
        )
        
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[
                "instagram:challenge:id:abc",
                "instagram:challenge:id:xyz"
            ])
            mock_redis.get = AsyncMock(side_effect=[
                pending_challenge.model_dump_json(),
                in_progress.model_dump_json()
            ])
            
            result = await manager.get_active_challenges()
            
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_get_active_challenges_empty(self, manager):
        """Should return empty list when no active challenges."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.get_active_challenges("test_user")
            
            assert result == []


class TestUpdateChallengeStatus:
    """Tests for update_challenge_status method."""
    
    @pytest.fixture
    def manager(self):
        return InstagramSessionManager()
    
    @pytest.mark.asyncio
    async def test_update_status_success(self, manager):
        """Should update challenge status."""
        challenge = InstagramChallenge(
            username="test_user",
            challenge_type=ChallengeType.SMS,
            status=ChallengeStatus.PENDING
        )
        
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=challenge.model_dump_json())
            mock_redis.set = AsyncMock(return_value=True)
            
            result = await manager.update_challenge_status(
                challenge.id,
                ChallengeStatus.RESOLVED,
                "Challenge completed"
            )
            
            assert result is True
            assert mock_redis.set.call_count == 2
    
    @pytest.mark.asyncio
    async def test_update_status_not_found(self, manager):
        """Should return False when challenge not found."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.update_challenge_status(
                "nonexistent-id",
                ChallengeStatus.RESOLVED
            )
            
            assert result is False


class TestIncrementChallengeAttempts:
    """Tests for increment_challenge_attempts method."""
    
    @pytest.fixture
    def manager(self):
        return InstagramSessionManager()
    
    @pytest.mark.asyncio
    async def test_increment_attempts_success(self, manager):
        """Should increment attempt counter."""
        challenge = InstagramChallenge(
            username="test_user",
            challenge_type=ChallengeType.SMS,
            attempts=2
        )
        
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=challenge.model_dump_json())
            mock_redis.set = AsyncMock(return_value=True)
            
            result = await manager.increment_challenge_attempts(challenge.id)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_increment_attempts_not_found(self, manager):
        """Should return False when challenge not found."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.increment_challenge_attempts("nonexistent")
            
            assert result is False


class TestDetectChallengeTypeMethod:
    """Tests for detect_challenge_type method on manager."""
    
    @pytest.fixture
    def manager(self):
        return InstagramSessionManager()
    
    @pytest.mark.asyncio
    async def test_detect_type(self, manager):
        """Should detect challenge type from message."""
        result = await manager.detect_challenge_type("Enter SMS code")
        
        assert result == ChallengeType.SMS


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error scenarios."""
    
    @pytest.fixture
    def manager(self):
        return InstagramSessionManager()
    
    @pytest.mark.asyncio
    async def test_empty_username(self, manager):
        """Should handle empty username."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.get_session("")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_special_characters_in_username(self, manager):
        """Should handle special characters in username."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(return_value=True)
            
            result = await manager.backup_session(
                "user.name_123",
                {"device_id": "abc"}
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_corrupted_json_handling(self, manager):
        """Should handle corrupted JSON gracefully."""
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value="invalid{{{json")
            
            result = await manager.get_session("test_user")
            
            # Should return None due to parse error
            assert result is None
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, manager):
        """Should handle concurrent operations."""
        challenge = InstagramChallenge(
            username="test_user",
            challenge_type=ChallengeType.SMS
        )
        
        with patch("api.services.instagram_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=challenge.model_dump_json())
            mock_redis.set = AsyncMock(return_value=True)
            mock_redis.keys = AsyncMock(return_value=[])
            
            import asyncio
            results = await asyncio.gather(
                manager.get_challenge(challenge.id),
                manager.get_active_challenges("test_user"),
                manager.get_session("test_user")
            )
            
            # First should succeed, second returns list, third None
            assert results[0] is not None
            assert isinstance(results[1], list)
    
    def test_challenge_info_model(self):
        """Should create ChallengeInfo correctly."""
        info = ChallengeInfo(
            type=ChallengeType.SMS,
            message="Test",
            instructions="Do this",
            methods_available=["sms"],
            retry_after=300
        )
        
        assert info.type == ChallengeType.SMS
        assert info.retry_after == 300
    
    def test_detect_rate_limit_seconds(self):
        """Should handle seconds in rate limit message."""
        result = detect_challenge_type("Rate limit, try again in 30 seconds")
        
        assert result.type == ChallengeType.RATE_LIMIT
        assert result.retry_after == 30
