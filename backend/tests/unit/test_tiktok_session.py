"""
Tests for TikTok Session Manager
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
import json

from api.services.tiktok_session import (
    TikTokSessionManager,
    TikTokSession,
    TikTokSessionStatus,
)


@pytest.fixture
def session_manager():
    """Create session manager instance"""
    return TikTokSessionManager()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('api.services.tiktok_session.redis_client') as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=True)
        mock.keys = AsyncMock(return_value=[])
        yield mock


@pytest.fixture
def sample_cookies():
    """Sample TikTok cookies"""
    return [
        {
            "name": "sessionid",
            "value": "abc123",
            "domain": ".tiktok.com",
            "path": "/"
        },
        {
            "name": "tt_csrf_token",
            "value": "xyz789",
            "domain": ".tiktok.com",
            "path": "/"
        }
    ]


class TestTikTokSessionManager:
    """Tests for TikTokSessionManager"""

    @pytest.mark.asyncio
    async def test_save_session(self, session_manager, mock_redis, sample_cookies):
        """Should save session to Redis"""
        session = await session_manager.save_session(
            user_id="user123",
            account_name="myaccount",
            cookies=sample_cookies
        )
        
        assert session.user_id == "user123"
        assert session.account_name == "myaccount"
        assert session.status == TikTokSessionStatus.ACTIVE
        assert len(session.cookies) == 2
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session(self, session_manager, mock_redis, sample_cookies):
        """Should get session from Redis"""
        session = TikTokSession(
            user_id="user123",
            account_name="myaccount",
            cookies=sample_cookies
        )
        mock_redis.get.return_value = session.model_dump_json()
        
        result = await session_manager.get_session("user123", "myaccount")
        
        assert result is not None
        assert result.account_name == "myaccount"
        assert len(result.cookies) == 2

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_manager, mock_redis):
        """Should return None for non-existent session"""
        mock_redis.get.return_value = None
        
        result = await session_manager.get_session("user123", "nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_cookies(self, session_manager, mock_redis, sample_cookies):
        """Should get cookies and mark session as used"""
        session = TikTokSession(
            user_id="user123",
            account_name="myaccount",
            cookies=sample_cookies
        )
        mock_redis.get.return_value = session.model_dump_json()
        
        result = await session_manager.get_cookies("user123", "myaccount")
        
        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "sessionid"

    @pytest.mark.asyncio
    async def test_mark_session_used(self, session_manager, mock_redis, sample_cookies):
        """Should update last_used and upload_count"""
        session = TikTokSession(
            user_id="user123",
            account_name="myaccount",
            cookies=sample_cookies,
            upload_count=5
        )
        mock_redis.get.return_value = session.model_dump_json()
        
        result = await session_manager.mark_session_used("user123", "myaccount")
        
        assert result is True
        # Verify set was called with updated data
        call_args = mock_redis.set.call_args
        saved_data = json.loads(call_args[0][1])
        assert saved_data["upload_count"] == 6

    @pytest.mark.asyncio
    async def test_update_session_status(self, session_manager, mock_redis, sample_cookies):
        """Should update session status"""
        session = TikTokSession(
            user_id="user123",
            account_name="myaccount",
            cookies=sample_cookies
        )
        mock_redis.get.return_value = session.model_dump_json()
        
        result = await session_manager.update_session_status(
            "user123", "myaccount",
            TikTokSessionStatus.NEEDS_REAUTH,
            "Session expired"
        )
        
        assert result is True
        call_args = mock_redis.set.call_args
        saved_data = json.loads(call_args[0][1])
        assert saved_data["status"] == "needs_reauth"
        assert saved_data["last_error"] == "Session expired"

    @pytest.mark.asyncio
    async def test_backup_session(self, session_manager, mock_redis, sample_cookies):
        """Should create session backup"""
        session = TikTokSession(
            user_id="user123",
            account_name="myaccount",
            cookies=sample_cookies
        )
        mock_redis.get.return_value = session.model_dump_json()
        
        result = await session_manager.backup_session("user123", "myaccount")
        
        assert result is True
        mock_redis.set.assert_called_once()
        call_key = mock_redis.set.call_args[0][0]
        assert "backup" in call_key

    @pytest.mark.asyncio
    async def test_backup_session_not_found(self, session_manager, mock_redis):
        """Should return False when session not found"""
        mock_redis.get.return_value = None
        
        result = await session_manager.backup_session("user123", "nonexistent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_restore_session(self, session_manager, mock_redis, sample_cookies):
        """Should restore session from backup"""
        session = TikTokSession(
            user_id="user123",
            account_name="myaccount",
            cookies=sample_cookies
        )
        mock_redis.keys.return_value = [
            "tiktok:session:backup:user123:myaccount:20240101120000"
        ]
        mock_redis.get.return_value = session.model_dump_json()
        
        result = await session_manager.restore_session("user123", "myaccount")
        
        assert result is not None
        assert result.account_name == "myaccount"
        # Verify session was saved
        assert mock_redis.set.call_count == 1

    @pytest.mark.asyncio
    async def test_restore_session_no_backup(self, session_manager, mock_redis):
        """Should return None when no backup exists"""
        mock_redis.keys.return_value = []
        
        result = await session_manager.restore_session("user123", "myaccount")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_session(self, session_manager, mock_redis):
        """Should delete session"""
        result = await session_manager.delete_session("user123", "myaccount")
        
        assert result is True
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_with_backups(self, session_manager, mock_redis):
        """Should delete session and backups when keep_backups=False"""
        mock_redis.keys.return_value = [
            "tiktok:session:backup:user123:myaccount:20240101"
        ]
        
        result = await session_manager.delete_session(
            "user123", "myaccount",
            keep_backups=False
        )
        
        assert result is True
        # delete called twice: once for session, once for backups
        assert mock_redis.delete.call_count == 2

    @pytest.mark.asyncio
    async def test_list_sessions(self, session_manager, mock_redis, sample_cookies):
        """Should list all sessions for a user"""
        mock_redis.keys.return_value = [
            "tiktok:session:user123:account1",
            "tiktok:session:user123:account2"
        ]
        
        session = TikTokSession(
            user_id="user123",
            account_name="account1",
            cookies=sample_cookies
        )
        mock_redis.get.return_value = session.model_dump_json()
        
        result = await session_manager.list_sessions("user123")
        
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_session_health_valid(self, session_manager, mock_redis, sample_cookies):
        """Should return health info for valid session"""
        session = TikTokSession(
            user_id="user123",
            account_name="myaccount",
            cookies=sample_cookies,
            expires_at=datetime.utcnow() + timedelta(days=15),
            upload_count=10
        )
        mock_redis.get.return_value = session.model_dump_json()
        mock_redis.keys.return_value = []
        
        result = await session_manager.get_session_health("user123", "myaccount")
        
        assert result["exists"] is True
        assert result["is_valid"] is True
        assert result["days_until_expiry"] == 14 or result["days_until_expiry"] == 15
        assert result["upload_count"] == 10

    @pytest.mark.asyncio
    async def test_get_session_health_expired(self, session_manager, mock_redis, sample_cookies):
        """Should return health info for expired session"""
        session = TikTokSession(
            user_id="user123",
            account_name="myaccount",
            cookies=sample_cookies,
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        mock_redis.get.return_value = session.model_dump_json()
        mock_redis.keys.return_value = []
        
        result = await session_manager.get_session_health("user123", "myaccount")
        
        assert result["is_expired"] is True
        assert result["is_valid"] is False

    @pytest.mark.asyncio
    async def test_get_session_health_not_found(self, session_manager, mock_redis):
        """Should return not found for missing session"""
        mock_redis.get.return_value = None
        
        result = await session_manager.get_session_health("user123", "nonexistent")
        
        assert result["exists"] is False
        assert result["is_valid"] is False

    @pytest.mark.asyncio
    async def test_update_cookies(self, session_manager, mock_redis, sample_cookies):
        """Should update cookies with backup"""
        session = TikTokSession(
            user_id="user123",
            account_name="myaccount",
            cookies=[{"name": "old", "value": "cookie"}]
        )
        mock_redis.get.return_value = session.model_dump_json()
        
        result = await session_manager.update_cookies(
            "user123", "myaccount",
            sample_cookies
        )
        
        assert result is True
        # Should have called set twice: backup + update
        assert mock_redis.set.call_count == 2

    @pytest.mark.asyncio
    async def test_get_stats(self, session_manager, mock_redis, sample_cookies):
        """Should return session statistics"""
        session = TikTokSession(
            user_id="user123",
            account_name="myaccount",
            cookies=sample_cookies,
            status=TikTokSessionStatus.ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=10)
        )
        mock_redis.keys.return_value = [
            "tiktok:session:user123:account1"
        ]
        mock_redis.get.return_value = session.model_dump_json()
        
        result = await session_manager.get_stats()
        
        assert result["total_sessions"] == 1
        assert result["active"] == 1
        assert result["expired"] == 0


class TestTikTokSession:
    """Tests for TikTokSession model"""

    def test_create_session_defaults(self):
        """Should create session with defaults"""
        session = TikTokSession(
            user_id="user123",
            account_name="myaccount",
            cookies=[]
        )
        
        assert session.status == TikTokSessionStatus.ACTIVE
        assert session.upload_count == 0
        assert session.id is not None

    def test_session_serialization(self):
        """Should serialize to JSON"""
        session = TikTokSession(
            user_id="user123",
            account_name="myaccount",
            cookies=[{"name": "test", "value": "value"}]
        )
        
        json_str = session.model_dump_json()
        parsed = json.loads(json_str)
        
        assert parsed["user_id"] == "user123"
        assert parsed["account_name"] == "myaccount"
        assert len(parsed["cookies"]) == 1

    def test_session_deserialization(self):
        """Should deserialize from JSON"""
        data = {
            "id": "test-id",
            "user_id": "user123",
            "account_name": "myaccount",
            "status": "active",
            "cookies": [],
            "upload_count": 5
        }
        
        session = TikTokSession.model_validate(data)
        
        assert session.id == "test-id"
        assert session.upload_count == 5
        assert session.status == TikTokSessionStatus.ACTIVE
