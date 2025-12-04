"""
TikTok Routes Extended Tests
============================
Testes para cobrir endpoints adicionais do TikTok.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.services.tiktok_session import TikTokSessionStatus
from fastapi import HTTPException

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def mock_session():
    """Mock TikTok session."""
    session = MagicMock()
    session.id = "session-123"
    session.account_name = "test_account"
    session.status = TikTokSessionStatus.ACTIVE
    session.created_at = datetime.now(timezone.utc)
    session.last_used = datetime.now(timezone.utc)
    session.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session.upload_count = 5
    return session


@pytest.fixture
def mock_session_manager():
    """Mock session manager."""
    manager = MagicMock()
    manager.save_session = AsyncMock()
    manager.list_sessions = AsyncMock()
    manager.get_session_health = AsyncMock()
    manager.backup_session = AsyncMock()
    manager.restore_session = AsyncMock()
    manager.update_cookies = AsyncMock()
    manager.delete_session = AsyncMock()
    manager.validate_session = AsyncMock()
    return manager


# ============================================
# CREATE SESSION TESTS
# ============================================


class TestCreateSession:
    """Tests for session creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, mock_user, mock_session, mock_session_manager):
        """Test successful session creation."""
        from api.routes.tiktok import TikTokSessionSetup, create_session
        
        mock_session_manager.save_session.return_value = mock_session
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            data = TikTokSessionSetup(
                account_name="test_account",
                cookies=[{"name": "sessionid", "value": "abc123"}]
            )
            
            result = await create_session(data, mock_user)
        
        assert result["status"] == "success"
        assert result["account_name"] == "test_account"
        assert result["session_id"] == "session-123"

    @pytest.mark.asyncio
    async def test_create_session_error(self, mock_user, mock_session_manager):
        """Test session creation failure."""
        from api.routes.tiktok import TikTokSessionSetup, create_session
        
        mock_session_manager.save_session.side_effect = Exception("Redis error")
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            data = TikTokSessionSetup(
                account_name="test_account",
                cookies=[{"name": "sessionid", "value": "abc123"}]
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await create_session(data, mock_user)
            
            assert exc_info.value.status_code == 500


# ============================================
# LIST SESSIONS TESTS
# ============================================


class TestListSessions:
    """Tests for session listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_sessions_success(self, mock_user, mock_session, mock_session_manager):
        """Test successful session listing."""
        from api.routes.tiktok import list_sessions
        
        mock_session_manager.list_sessions.return_value = [mock_session]
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            result = await list_sessions(mock_user)
        
        assert len(result["sessions"]) == 1
        assert result["sessions"][0]["account_name"] == "test_account"
        assert result["sessions"][0]["upload_count"] == 5
        assert result["sessions"][0]["is_valid"] is True

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, mock_user, mock_session_manager):
        """Test empty session list."""
        from api.routes.tiktok import list_sessions
        
        mock_session_manager.list_sessions.return_value = []
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            result = await list_sessions(mock_user)
        
        assert result["sessions"] == []

    @pytest.mark.asyncio
    async def test_list_sessions_no_user(self, mock_session_manager):
        """Test session list without authenticated user."""
        from api.routes.tiktok import list_sessions
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            result = await list_sessions(None)
        
        assert result["sessions"] == []


# ============================================
# GET SESSION TESTS
# ============================================


class TestGetSession:
    """Tests for get session details endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_success(self, mock_user, mock_session_manager):
        """Test successful session retrieval."""
        from api.routes.tiktok import get_session
        
        mock_session_manager.get_session_health.return_value = {
            "exists": True,
            "account_name": "test_account",
            "status": "active",
            "cookies_valid": True
        }
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            result = await get_session("test_account", mock_user)
        
        assert result["exists"] is True
        assert result["account_name"] == "test_account"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_user, mock_session_manager):
        """Test session not found."""
        from api.routes.tiktok import get_session
        
        mock_session_manager.get_session_health.return_value = {"exists": False}
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            with pytest.raises(HTTPException) as exc_info:
                await get_session("nonexistent", mock_user)
            
            assert exc_info.value.status_code == 404


# ============================================
# BACKUP SESSION TESTS
# ============================================


class TestBackupSession:
    """Tests for backup session endpoint."""

    @pytest.mark.asyncio
    async def test_backup_session_success(self, mock_user, mock_session_manager):
        """Test successful session backup."""
        from api.routes.tiktok import backup_session
        
        mock_session_manager.backup_session.return_value = True
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            result = await backup_session("test_account", mock_user)
        
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_backup_session_failure(self, mock_user, mock_session_manager):
        """Test backup session failure."""
        from api.routes.tiktok import backup_session
        
        mock_session_manager.backup_session.return_value = False
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            with pytest.raises(HTTPException) as exc_info:
                await backup_session("test_account", mock_user)
            
            assert exc_info.value.status_code == 400


# ============================================
# RESTORE SESSION TESTS
# ============================================


class TestRestoreSession:
    """Tests for restore session endpoint."""

    @pytest.mark.asyncio
    async def test_restore_session_success(self, mock_user, mock_session, mock_session_manager):
        """Test successful session restore."""
        from api.routes.tiktok import restore_session
        
        mock_session_manager.restore_session.return_value = mock_session
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            result = await restore_session("test_account", mock_user)
        
        assert result["status"] == "success"
        assert result["account_name"] == "test_account"

    @pytest.mark.asyncio
    async def test_restore_session_no_backup(self, mock_user, mock_session_manager):
        """Test restore when no backup exists."""
        from api.routes.tiktok import restore_session
        
        mock_session_manager.restore_session.return_value = None
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            with pytest.raises(HTTPException) as exc_info:
                await restore_session("test_account", mock_user)
            
            assert exc_info.value.status_code == 404


# ============================================
# UPDATE COOKIES TESTS
# ============================================


class TestUpdateCookies:
    """Tests for update cookies endpoint."""

    @pytest.mark.asyncio
    async def test_update_cookies_success(self, mock_user, mock_session_manager):
        """Test successful cookie update."""
        from api.routes.tiktok import update_cookies
        
        mock_session_manager.update_cookies.return_value = True
        
        new_cookies = [{"name": "sessionid", "value": "new_value"}]
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            result = await update_cookies("test_account", new_cookies, mock_user)
        
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_update_cookies_failure(self, mock_user, mock_session_manager):
        """Test cookie update failure."""
        from api.routes.tiktok import update_cookies
        
        mock_session_manager.update_cookies.return_value = False
        
        new_cookies = [{"name": "sessionid", "value": "new_value"}]
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            with pytest.raises(HTTPException) as exc_info:
                await update_cookies("test_account", new_cookies, mock_user)
            
            assert exc_info.value.status_code == 400


# ============================================
# DELETE SESSION TESTS
# ============================================


class TestDeleteSession:
    """Tests for delete session endpoint."""

    @pytest.mark.asyncio
    async def test_delete_session_success(self, mock_user, mock_session_manager):
        """Test successful session deletion."""
        from api.routes.tiktok import delete_session
        
        mock_session_manager.delete_session.return_value = True
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            result = await delete_session("test_account", True, mock_user)
        
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_delete_session_without_backups(self, mock_user, mock_session_manager):
        """Test deletion without keeping backups."""
        from api.routes.tiktok import delete_session
        
        mock_session_manager.delete_session.return_value = True
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            result = await delete_session("test_account", False, mock_user)
        
        assert result["status"] == "success"
        mock_session_manager.delete_session.assert_called_with(
            "user-123", "test_account", keep_backups=False
        )

    @pytest.mark.asyncio
    async def test_delete_session_failure(self, mock_user, mock_session_manager):
        """Test session deletion failure."""
        from api.routes.tiktok import delete_session
        
        mock_session_manager.delete_session.return_value = False
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            with pytest.raises(HTTPException) as exc_info:
                await delete_session("test_account", True, mock_user)
            
            assert exc_info.value.status_code == 400


# ============================================
# MODEL TESTS
# ============================================


class TestTikTokModels:
    """Tests for TikTok request models."""

    def test_session_setup_model(self):
        """Test TikTokSessionSetup model."""
        from api.routes.tiktok import TikTokSessionSetup
        
        data = TikTokSessionSetup(
            account_name="test_account",
            cookies=[{"name": "session", "value": "abc123"}]
        )
        
        assert data.account_name == "test_account"
        assert len(data.cookies) == 1

    def test_upload_request_model_defaults(self):
        """Test TikTokUploadRequest with defaults."""
        from api.routes.tiktok import TikTokUploadRequest
        
        data = TikTokUploadRequest(
            account_name="test",
            caption="Test video"
        )
        
        assert data.account_name == "test"
        assert data.caption == "Test video"
        assert data.privacy == "public"
        assert data.hashtags is None
        assert data.schedule_time is None

    def test_upload_request_model_full(self):
        """Test TikTokUploadRequest with all fields."""
        from api.routes.tiktok import TikTokUploadRequest
        
        schedule = datetime.now(timezone.utc) + timedelta(hours=1)
        
        data = TikTokUploadRequest(
            account_name="test",
            caption="Test video with all options",
            hashtags=["fyp", "viral", "test"],
            privacy="friends",
            schedule_time=schedule
        )
        
        assert data.privacy == "friends"
        assert len(data.hashtags) == 3
        assert data.schedule_time == schedule


# ============================================
# INACTIVE SESSION TESTS  
# ============================================


class TestInactiveSessionHandling:
    """Tests for handling inactive sessions."""

    @pytest.mark.asyncio
    async def test_list_inactive_sessions(self, mock_user, mock_session_manager):
        """Test listing with inactive sessions."""
        from api.routes.tiktok import list_sessions
        
        inactive_session = MagicMock()
        inactive_session.account_name = "inactive_account"
        inactive_session.status = TikTokSessionStatus.EXPIRED
        inactive_session.created_at = datetime.now(timezone.utc)
        inactive_session.last_used = None
        inactive_session.expires_at = None
        inactive_session.upload_count = 0
        
        mock_session_manager.list_sessions.return_value = [inactive_session]
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            result = await list_sessions(mock_user)
        
        assert len(result["sessions"]) == 1
        assert result["sessions"][0]["is_valid"] is False
        assert result["sessions"][0]["status"] == "expired"


# ============================================
# MULTIPLE SESSIONS TESTS
# ============================================


class TestMultipleSessions:
    """Tests for handling multiple sessions."""

    @pytest.mark.asyncio
    async def test_list_multiple_sessions(self, mock_user, mock_session_manager):
        """Test listing multiple sessions."""
        from api.routes.tiktok import list_sessions
        
        sessions = []
        for i in range(3):
            s = MagicMock()
            s.account_name = f"account_{i}"
            s.status = TikTokSessionStatus.ACTIVE
            s.created_at = datetime.now(timezone.utc)
            s.last_used = datetime.now(timezone.utc)
            s.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            s.upload_count = i * 10
            sessions.append(s)
        
        mock_session_manager.list_sessions.return_value = sessions
        
        with patch("api.routes.tiktok.session_manager", mock_session_manager):
            result = await list_sessions(mock_user)
        
        assert len(result["sessions"]) == 3
        for i, session in enumerate(result["sessions"]):
            assert session["account_name"] == f"account_{i}"
            assert session["upload_count"] == i * 10
