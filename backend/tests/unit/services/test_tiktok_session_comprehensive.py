"""
Comprehensive tests for TikTok Session Manager.
Tests session persistence, backup, and restoration via Redis.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.services.tiktok_session import (TikTokSession, TikTokSessionManager,
                                         TikTokSessionStatus, ensure_aware)

# ============================================================================
# Helper Functions Tests
# ============================================================================

class TestEnsureAware:
    """Tests for ensure_aware helper function."""
    
    def test_ensure_aware_with_none(self):
        """Should return None for None input."""
        assert ensure_aware(None) is None
    
    def test_ensure_aware_with_naive_datetime(self):
        """Should add UTC timezone to naive datetime."""
        naive = datetime(2024, 1, 15, 12, 0, 0)
        result = ensure_aware(naive)
        
        assert result.tzinfo == timezone.utc
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_ensure_aware_with_aware_datetime(self):
        """Should return aware datetime unchanged."""
        aware = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = ensure_aware(aware)
        
        assert result is aware
        assert result.tzinfo == timezone.utc


# ============================================================================
# TikTokSession Model Tests
# ============================================================================

class TestTikTokSessionModel:
    """Tests for TikTokSession Pydantic model."""
    
    def test_create_session_default_values(self):
        """Should create session with default values."""
        session = TikTokSession(
            user_id="user123",
            account_name="test_account"
        )
        
        assert session.user_id == "user123"
        assert session.account_name == "test_account"
        assert session.status == TikTokSessionStatus.ACTIVE
        assert session.cookies == []
        assert session.upload_count == 0
        assert session.metadata == {}
        assert session.id is not None
        assert session.created_at is not None
    
    def test_create_session_with_cookies(self):
        """Should create session with cookies."""
        cookies = [{"name": "session", "value": "abc123"}]
        session = TikTokSession(
            user_id="user123",
            account_name="test_account",
            cookies=cookies
        )
        
        assert session.cookies == cookies
    
    def test_create_session_with_metadata(self):
        """Should create session with metadata."""
        metadata = {"browser": "chrome", "version": "120"}
        session = TikTokSession(
            user_id="user123",
            account_name="test_account",
            metadata=metadata
        )
        
        assert session.metadata == metadata
    
    def test_session_json_serialization(self):
        """Should serialize/deserialize session correctly."""
        session = TikTokSession(
            user_id="user123",
            account_name="test_account",
            cookies=[{"name": "test", "value": "cookie"}]
        )
        
        json_str = session.model_dump_json()
        restored = TikTokSession.model_validate_json(json_str)
        
        assert restored.user_id == session.user_id
        assert restored.account_name == session.account_name
        assert restored.cookies == session.cookies


# ============================================================================
# TikTokSessionStatus Enum Tests
# ============================================================================

class TestTikTokSessionStatus:
    """Tests for TikTokSessionStatus enum."""
    
    def test_status_values(self):
        """Should have correct status values."""
        assert TikTokSessionStatus.ACTIVE.value == "active"
        assert TikTokSessionStatus.EXPIRED.value == "expired"
        assert TikTokSessionStatus.INVALID.value == "invalid"
        assert TikTokSessionStatus.NEEDS_REAUTH.value == "needs_reauth"
    
    def test_status_is_string_enum(self):
        """Status should be usable as string."""
        assert str(TikTokSessionStatus.ACTIVE) == "TikTokSessionStatus.ACTIVE"
        assert TikTokSessionStatus.ACTIVE == "active"


# ============================================================================
# TikTokSessionManager Tests
# ============================================================================

class TestTikTokSessionManagerInit:
    """Tests for TikTokSessionManager initialization."""
    
    def test_manager_prefixes(self):
        """Should have correct prefixes."""
        manager = TikTokSessionManager()
        
        assert manager.SESSION_PREFIX == "tiktok:session:"
        assert manager.BACKUP_PREFIX == "tiktok:session:backup:"
        assert manager.STATS_PREFIX == "tiktok:stats:"
    
    def test_manager_expiry_times(self):
        """Should have correct expiry times."""
        manager = TikTokSessionManager()
        
        assert manager.SESSION_EXPIRY == 60 * 60 * 24 * 30  # 30 days
        assert manager.BACKUP_EXPIRY == 60 * 60 * 24 * 7  # 7 days


class TestSaveSession:
    """Tests for save_session method."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_save_session_success(self, manager):
        """Should save session to Redis."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(return_value=True)
            
            session = await manager.save_session(
                user_id="user123",
                account_name="test_account",
                cookies=[{"name": "test", "value": "cookie"}],
                metadata={"browser": "chrome"}
            )
            
            assert session.user_id == "user123"
            assert session.account_name == "test_account"
            assert len(session.cookies) == 1
            assert session.metadata["browser"] == "chrome"
            
            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args
            assert "tiktok:session:user123:test_account" in call_args[0]
    
    @pytest.mark.asyncio
    async def test_save_session_error(self, manager):
        """Should raise on Redis error."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(side_effect=Exception("Redis error"))
            
            with pytest.raises(Exception, match="Redis error"):
                await manager.save_session(
                    user_id="user123",
                    account_name="test_account",
                    cookies=[]
                )


class TestGetSession:
    """Tests for get_session method."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_get_session_found(self, manager):
        """Should return session when found."""
        session_data = TikTokSession(
            user_id="user123",
            account_name="test_account",
            cookies=[{"name": "test", "value": "cookie"}]
        )
        
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=session_data.model_dump_json())
            
            result = await manager.get_session("user123", "test_account")
            
            assert result is not None
            assert result.user_id == "user123"
            assert result.account_name == "test_account"
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, manager):
        """Should return None when session not found."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.get_session("user123", "nonexistent")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_session_error(self, manager):
        """Should return None on Redis error."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
            
            result = await manager.get_session("user123", "test_account")
            
            assert result is None


class TestGetCookies:
    """Tests for get_cookies method."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_get_cookies_found(self, manager):
        """Should return cookies when session found."""
        cookies = [{"name": "session", "value": "abc123"}]
        session_data = TikTokSession(
            user_id="user123",
            account_name="test_account",
            cookies=cookies
        )
        
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=session_data.model_dump_json())
            mock_redis.set = AsyncMock(return_value=True)
            
            result = await manager.get_cookies("user123", "test_account")
            
            assert result == cookies
    
    @pytest.mark.asyncio
    async def test_get_cookies_not_found(self, manager):
        """Should return None when session not found."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.get_cookies("user123", "nonexistent")
            
            assert result is None


class TestMarkSessionUsed:
    """Tests for mark_session_used method."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_mark_session_used_success(self, manager):
        """Should update last_used and upload_count."""
        session_data = TikTokSession(
            user_id="user123",
            account_name="test_account",
            upload_count=5
        )
        
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=session_data.model_dump_json())
            mock_redis.set = AsyncMock(return_value=True)
            
            result = await manager.mark_session_used("user123", "test_account")
            
            assert result is True
            mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mark_session_used_not_found(self, manager):
        """Should return False when session not found."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.mark_session_used("user123", "nonexistent")
            
            assert result is False


class TestUpdateSessionStatus:
    """Tests for update_session_status method."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_update_status_success(self, manager):
        """Should update session status."""
        session_data = TikTokSession(
            user_id="user123",
            account_name="test_account",
            status=TikTokSessionStatus.ACTIVE
        )
        
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=session_data.model_dump_json())
            mock_redis.set = AsyncMock(return_value=True)
            
            result = await manager.update_session_status(
                "user123",
                "test_account",
                TikTokSessionStatus.EXPIRED,
                error="Session expired"
            )
            
            assert result is True
            mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_status_not_found(self, manager):
        """Should return False when session not found."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.update_session_status(
                "user123",
                "nonexistent",
                TikTokSessionStatus.EXPIRED
            )
            
            assert result is False


class TestBackupSession:
    """Tests for backup_session method."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_backup_session_success(self, manager):
        """Should create backup of session."""
        session_data = TikTokSession(
            user_id="user123",
            account_name="test_account"
        )
        
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=session_data.model_dump_json())
            mock_redis.set = AsyncMock(return_value=True)
            
            result = await manager.backup_session("user123", "test_account")
            
            assert result is True
            mock_redis.set.assert_called_once()
            # Check backup key format
            call_args = mock_redis.set.call_args[0][0]
            assert "tiktok:session:backup:" in call_args
    
    @pytest.mark.asyncio
    async def test_backup_session_not_found(self, manager):
        """Should return False when session not found."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.backup_session("user123", "nonexistent")
            
            assert result is False


class TestRestoreSession:
    """Tests for restore_session method."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_restore_session_success(self, manager):
        """Should restore session from backup."""
        session_data = TikTokSession(
            user_id="user123",
            account_name="test_account"
        )
        
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[
                "tiktok:session:backup:user123:test_account:20240115120000",
                "tiktok:session:backup:user123:test_account:20240114120000"
            ])
            mock_redis.get = AsyncMock(return_value=session_data.model_dump_json())
            mock_redis.set = AsyncMock(return_value=True)
            
            result = await manager.restore_session("user123", "test_account")
            
            assert result is not None
            assert result.user_id == "user123"
    
    @pytest.mark.asyncio
    async def test_restore_session_no_backups(self, manager):
        """Should return None when no backups exist."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await manager.restore_session("user123", "test_account")
            
            assert result is None


class TestDeleteSession:
    """Tests for delete_session method."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_delete_session_keep_backups(self, manager):
        """Should delete session but keep backups."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.delete = AsyncMock(return_value=True)
            
            result = await manager.delete_session(
                "user123",
                "test_account",
                keep_backups=True
            )
            
            assert result is True
            assert mock_redis.delete.call_count == 1
    
    @pytest.mark.asyncio
    async def test_delete_session_delete_backups(self, manager):
        """Should delete session and backups."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.delete = AsyncMock(return_value=True)
            mock_redis.keys = AsyncMock(return_value=[
                "tiktok:session:backup:user123:test_account:20240115"
            ])
            
            result = await manager.delete_session(
                "user123",
                "test_account",
                keep_backups=False
            )
            
            assert result is True
            assert mock_redis.delete.call_count == 2


class TestListSessions:
    """Tests for list_sessions method."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_list_sessions_found(self, manager):
        """Should list all sessions for user."""
        session1 = TikTokSession(user_id="user123", account_name="account1")
        session2 = TikTokSession(user_id="user123", account_name="account2")
        
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[
                "tiktok:session:user123:account1",
                "tiktok:session:user123:account2"
            ])
            mock_redis.get = AsyncMock(side_effect=[
                session1.model_dump_json(),
                session2.model_dump_json()
            ])
            
            result = await manager.list_sessions("user123")
            
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, manager):
        """Should return empty list when no sessions."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await manager.list_sessions("user123")
            
            assert result == []


class TestGetSessionHealth:
    """Tests for get_session_health method."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_health_active_session(self, manager):
        """Should return healthy status for active session."""
        session_data = TikTokSession(
            user_id="user123",
            account_name="test_account",
            status=TikTokSessionStatus.ACTIVE,
            expires_at=datetime.now(timezone.utc) + timedelta(days=25),
            upload_count=10
        )
        
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=session_data.model_dump_json())
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await manager.get_session_health("user123", "test_account")
            
            assert result["exists"] is True
            assert result["is_valid"] is True
            assert result["status"] == "active"
            assert result["is_expired"] is False
            assert result["days_until_expiry"] >= 24
    
    @pytest.mark.asyncio
    async def test_health_expired_session(self, manager):
        """Should detect expired session."""
        session_data = TikTokSession(
            user_id="user123",
            account_name="test_account",
            status=TikTokSessionStatus.ACTIVE,
            expires_at=datetime.now(timezone.utc) - timedelta(days=5)
        )
        
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=session_data.model_dump_json())
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await manager.get_session_health("user123", "test_account")
            
            assert result["is_valid"] is False
            assert result["is_expired"] is True
    
    @pytest.mark.asyncio
    async def test_health_not_found(self, manager):
        """Should return not_found status when session missing."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.get_session_health("user123", "nonexistent")
            
            assert result["exists"] is False
            assert result["is_valid"] is False
            assert result["status"] == "not_found"


class TestHasBackup:
    """Tests for _has_backup method."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_has_backup_true(self, manager):
        """Should return True when backup exists."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=["backup_key"])
            
            result = await manager._has_backup("user123", "test_account")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_has_backup_false(self, manager):
        """Should return False when no backup."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await manager._has_backup("user123", "test_account")
            
            assert result is False


class TestUpdateCookies:
    """Tests for update_cookies method."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_update_cookies_success(self, manager):
        """Should update cookies and reset status."""
        old_session = TikTokSession(
            user_id="user123",
            account_name="test_account",
            cookies=[{"name": "old", "value": "cookie"}],
            status=TikTokSessionStatus.EXPIRED,
            last_error="Previous error"
        )
        
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=old_session.model_dump_json())
            mock_redis.set = AsyncMock(return_value=True)
            mock_redis.keys = AsyncMock(return_value=[])
            
            new_cookies = [{"name": "new", "value": "cookie"}]
            result = await manager.update_cookies(
                "user123",
                "test_account",
                new_cookies
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_update_cookies_not_found(self, manager):
        """Should return False when session not found."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.set = AsyncMock(return_value=True)
            
            result = await manager.update_cookies(
                "user123",
                "nonexistent",
                [{"name": "new", "value": "cookie"}]
            )
            
            assert result is False


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error scenarios."""
    
    @pytest.fixture
    def manager(self):
        return TikTokSessionManager()
    
    @pytest.mark.asyncio
    async def test_empty_user_id(self, manager):
        """Should handle empty user_id."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await manager.get_session("", "account")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_special_characters_in_account_name(self, manager):
        """Should handle special characters in account name."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(return_value=True)
            
            session = await manager.save_session(
                user_id="user123",
                account_name="test@account#special",
                cookies=[]
            )
            
            assert session.account_name == "test@account#special"
    
    @pytest.mark.asyncio
    async def test_large_cookie_list(self, manager):
        """Should handle large number of cookies."""
        cookies = [{"name": f"cookie_{i}", "value": f"value_{i}"} for i in range(100)]
        
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.set = AsyncMock(return_value=True)
            
            session = await manager.save_session(
                user_id="user123",
                account_name="test_account",
                cookies=cookies
            )
            
            assert len(session.cookies) == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, manager):
        """Should handle concurrent session operations."""
        session_data = TikTokSession(
            user_id="user123",
            account_name="test_account"
        )
        
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=session_data.model_dump_json())
            mock_redis.set = AsyncMock(return_value=True)
            
            # Simular operações concorrentes
            import asyncio
            results = await asyncio.gather(
                manager.mark_session_used("user123", "test_account"),
                manager.get_session("user123", "test_account"),
                manager.get_cookies("user123", "test_account")
            )
            
            assert all(r is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_json_parse_error(self, manager):
        """Should handle invalid JSON gracefully."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value="invalid json{{{")
            
            result = await manager.get_session("user123", "test_account")
            
            # Should return None due to parse error
            assert result is None
    
    @pytest.mark.asyncio
    async def test_list_sessions_with_error(self, manager):
        """Should return empty list on error."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(side_effect=Exception("Redis error"))
            
            result = await manager.list_sessions("user123")
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_restore_with_corrupted_backup(self, manager):
        """Should handle corrupted backup data."""
        with patch("api.services.tiktok_session.redis_client") as mock_redis:
            mock_redis.keys = AsyncMock(return_value=["backup_key"])
            mock_redis.get = AsyncMock(return_value="corrupted{{{data")
            
            result = await manager.restore_session("user123", "test_account")
            
            # Should return None due to parse error
            assert result is None
