"""
Comprehensive tests for TikTok routes.
Coverage target: 90%+
"""

from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# Mock dependencies before importing router
@pytest.fixture(autouse=True)
def mock_tiktok_dependencies():
    """Mock TikTok dependencies."""
    mock_hub = MagicMock()
    mock_session_manager = MagicMock()
    mock_hub.session_manager = mock_session_manager
    
    with patch("api.routes.tiktok.get_tiktok_hub", return_value=mock_hub), \
         patch("api.routes.tiktok.hub", mock_hub), \
         patch("api.routes.tiktok.session_manager", mock_session_manager):
        yield mock_session_manager


@pytest.fixture
def mock_user():
    """Standard test user."""
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture
def mock_session():
    """Mock TikTok session."""
    from api.services.tiktok_session import TikTokSessionStatus
    session = MagicMock()
    session.id = "session-001"
    session.account_name = "test_account"
    session.status = TikTokSessionStatus.ACTIVE
    session.created_at = datetime.now(timezone.utc)
    session.last_used = datetime.now(timezone.utc)
    session.expires_at = datetime.now(timezone.utc)
    session.upload_count = 10
    return session


class TestCreateSession:
    """Tests for POST /sessions endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_session_success(self, mock_tiktok_dependencies, mock_user, mock_session):
        """Test successful session creation."""
        from api.routes.tiktok import TikTokSessionSetup, create_session
        
        mock_tiktok_dependencies.save_session = AsyncMock(return_value=mock_session)
        
        data = TikTokSessionSetup(
            account_name="my_account",
            cookies=[{"name": "sessionid", "value": "abc123"}]
        )
        
        result = await create_session(data, mock_user)
        
        assert result["status"] == "success"
        assert result["account_name"] == "my_account"
        assert result["session_id"] == "session-001"
        mock_tiktok_dependencies.save_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_session_error(self, mock_tiktok_dependencies, mock_user):
        """Test session creation error handling."""
        from api.routes.tiktok import TikTokSessionSetup, create_session
        from fastapi import HTTPException
        
        mock_tiktok_dependencies.save_session = AsyncMock(
            side_effect=Exception("Redis connection failed")
        )
        
        data = TikTokSessionSetup(
            account_name="my_account",
            cookies=[{"name": "sessionid", "value": "abc123"}]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await create_session(data, mock_user)
        
        assert exc_info.value.status_code == 500
        assert "Erro ao salvar sessão" in exc_info.value.detail


class TestListSessions:
    """Tests for GET /sessions endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_sessions_authenticated(self, mock_tiktok_dependencies, mock_user, mock_session):
        """Test listing sessions for authenticated user."""
        from api.routes.tiktok import list_sessions
        
        mock_tiktok_dependencies.list_sessions = AsyncMock(return_value=[mock_session])
        
        result = await list_sessions(mock_user)
        
        assert "sessions" in result
        assert len(result["sessions"]) == 1
        assert result["sessions"][0]["account_name"] == "test_account"
        assert result["sessions"][0]["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_list_sessions_no_user(self, mock_tiktok_dependencies):
        """Test listing sessions without authentication (trial mode)."""
        from api.routes.tiktok import list_sessions
        
        result = await list_sessions(None)
        
        assert result["sessions"] == []
    
    @pytest.mark.asyncio
    async def test_list_sessions_multiple(self, mock_tiktok_dependencies, mock_user, mock_session):
        """Test listing multiple sessions."""
        from api.routes.tiktok import list_sessions
        from api.services.tiktok_session import TikTokSessionStatus
        
        session2 = MagicMock()
        session2.account_name = "second_account"
        session2.status = TikTokSessionStatus.EXPIRED
        session2.created_at = datetime.now(timezone.utc)
        session2.last_used = None
        session2.expires_at = None
        session2.upload_count = 5
        
        mock_tiktok_dependencies.list_sessions = AsyncMock(
            return_value=[mock_session, session2]
        )
        
        result = await list_sessions(mock_user)
        
        assert len(result["sessions"]) == 2
        assert result["sessions"][0]["is_valid"] is True
        assert result["sessions"][1]["is_valid"] is False


class TestGetSession:
    """Tests for GET /sessions/{account_name} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_session_success(self, mock_tiktok_dependencies, mock_user):
        """Test getting session details."""
        from api.routes.tiktok import get_session
        
        mock_health = {
            "exists": True,
            "status": "active",
            "cookie_count": 5,
            "last_used": datetime.now(timezone.utc).isoformat()
        }
        mock_tiktok_dependencies.get_session_health = AsyncMock(return_value=mock_health)
        
        result = await get_session("my_account", mock_user)
        
        assert result["exists"] is True
        assert result["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_tiktok_dependencies, mock_user):
        """Test getting non-existent session."""
        from api.routes.tiktok import get_session
        from fastapi import HTTPException
        
        mock_tiktok_dependencies.get_session_health = AsyncMock(return_value={"exists": False})
        
        with pytest.raises(HTTPException) as exc_info:
            await get_session("nonexistent", mock_user)
        
        assert exc_info.value.status_code == 404


class TestBackupSession:
    """Tests for POST /sessions/{account_name}/backup endpoint."""
    
    @pytest.mark.asyncio
    async def test_backup_session_success(self, mock_tiktok_dependencies, mock_user):
        """Test successful session backup."""
        from api.routes.tiktok import backup_session
        
        mock_tiktok_dependencies.backup_session = AsyncMock(return_value=True)
        
        result = await backup_session("my_account", mock_user)
        
        assert result["status"] == "success"
        assert "Backup criado" in result["message"]
    
    @pytest.mark.asyncio
    async def test_backup_session_failure(self, mock_tiktok_dependencies, mock_user):
        """Test backup failure."""
        from api.routes.tiktok import backup_session
        from fastapi import HTTPException
        
        mock_tiktok_dependencies.backup_session = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await backup_session("my_account", mock_user)
        
        assert exc_info.value.status_code == 400


class TestRestoreSession:
    """Tests for POST /sessions/{account_name}/restore endpoint."""
    
    @pytest.mark.asyncio
    async def test_restore_session_success(self, mock_tiktok_dependencies, mock_user, mock_session):
        """Test successful session restore."""
        from api.routes.tiktok import restore_session
        
        mock_tiktok_dependencies.restore_session = AsyncMock(return_value=mock_session)
        
        result = await restore_session("my_account", mock_user)
        
        assert result["status"] == "success"
        assert result["account_name"] == "test_account"
    
    @pytest.mark.asyncio
    async def test_restore_session_no_backup(self, mock_tiktok_dependencies, mock_user):
        """Test restore when no backup exists."""
        from api.routes.tiktok import restore_session
        from fastapi import HTTPException
        
        mock_tiktok_dependencies.restore_session = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await restore_session("my_account", mock_user)
        
        assert exc_info.value.status_code == 404


class TestUpdateCookies:
    """Tests for PUT /sessions/{account_name}/cookies endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_cookies_success(self, mock_tiktok_dependencies, mock_user):
        """Test successful cookies update."""
        from api.routes.tiktok import update_cookies
        
        mock_tiktok_dependencies.update_cookies = AsyncMock(return_value=True)
        
        cookies = [{"name": "new_session", "value": "new123"}]
        result = await update_cookies("my_account", cookies, mock_user)
        
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_update_cookies_failure(self, mock_tiktok_dependencies, mock_user):
        """Test cookies update failure."""
        from api.routes.tiktok import update_cookies
        from fastapi import HTTPException
        
        mock_tiktok_dependencies.update_cookies = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await update_cookies("my_account", [], mock_user)
        
        assert exc_info.value.status_code == 400


class TestDeleteSession:
    """Tests for DELETE /sessions/{account_name} endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_session_success(self, mock_tiktok_dependencies, mock_user):
        """Test successful session deletion."""
        from api.routes.tiktok import delete_session
        
        mock_tiktok_dependencies.delete_session = AsyncMock(return_value=True)
        
        result = await delete_session("my_account", True, mock_user)
        
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_delete_session_failure(self, mock_tiktok_dependencies, mock_user):
        """Test session deletion failure."""
        from api.routes.tiktok import delete_session
        from fastapi import HTTPException
        
        mock_tiktok_dependencies.delete_session = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_session("my_account", True, mock_user)
        
        assert exc_info.value.status_code == 400


class TestTikTokAPIHealth:
    """Tests for GET /api/health endpoint."""
    
    @pytest.mark.asyncio
    async def test_api_health_healthy(self, mock_user):
        """Test healthy API status."""
        from api.routes.tiktok import tiktok_api_health
        
        mock_health_response = {
            "healthy": True,
            "api_accessible": True,
            "cookies_valid": True,
            "expires": "2025-12-01T00:00:00Z",
            "endpoints_tested": ["/search", "/trending"]
        }
        
        with patch("api.routes.tiktok.TikTokAPIScraper") as MockScraper:
            mock_scraper = MockScraper.return_value
            mock_scraper.health_check = AsyncMock(return_value=mock_health_response)
            
            result = await tiktok_api_health(mock_user)
        
        assert result.status == "healthy"
        assert result.api_accessible is True
        assert result.cookies_valid is True
    
    @pytest.mark.asyncio
    async def test_api_health_degraded(self, mock_user):
        """Test degraded API status."""
        from api.routes.tiktok import tiktok_api_health
        
        mock_health_response = {
            "healthy": False,
            "api_accessible": True,
            "cookies_valid": False
        }
        
        with patch("api.routes.tiktok.TikTokAPIScraper") as MockScraper:
            mock_scraper = MockScraper.return_value
            mock_scraper.health_check = AsyncMock(return_value=mock_health_response)
            
            result = await tiktok_api_health(mock_user)
        
        assert result.status == "degraded"
    
    @pytest.mark.asyncio
    async def test_api_health_error(self, mock_user):
        """Test API health check error."""
        from api.routes.tiktok import tiktok_api_health
        
        with patch("api.routes.tiktok.TikTokAPIScraper") as MockScraper:
            mock_scraper = MockScraper.return_value
            mock_scraper.health_check = AsyncMock(side_effect=Exception("Connection failed"))
            
            result = await tiktok_api_health(mock_user)
        
        assert result.status == "error"
        assert result.api_accessible is False
        assert "Connection failed" in result.error


class TestTikTokSessionSetupModel:
    """Tests for TikTokSessionSetup model."""
    
    def test_valid_session_setup(self):
        """Test valid session setup model."""
        from api.routes.tiktok import TikTokSessionSetup
        
        data = TikTokSessionSetup(
            account_name="test",
            cookies=[{"name": "session", "value": "123"}]
        )
        
        assert data.account_name == "test"
        assert len(data.cookies) == 1


class TestTikTokUploadRequest:
    """Tests for TikTokUploadRequest model."""
    
    def test_valid_upload_request(self):
        """Test valid upload request model."""
        from api.routes.tiktok import TikTokUploadRequest
        
        data = TikTokUploadRequest(
            account_name="test",
            caption="Test video",
            hashtags=["fun", "viral"],
            privacy="public"
        )
        
        assert data.account_name == "test"
        assert data.privacy == "public"
    
    def test_upload_request_defaults(self):
        """Test upload request with default values."""
        from api.routes.tiktok import TikTokUploadRequest
        
        data = TikTokUploadRequest(
            account_name="test",
            caption="Test"
        )
        
        assert data.hashtags is None
        assert data.privacy == "public"
        assert data.schedule_time is None


class TestTikTokSearchRequest:
    """Tests for TikTokSearchRequest model."""
    
    def test_valid_search_request(self):
        """Test valid search request."""
        from api.routes.tiktok import TikTokSearchRequest
        
        data = TikTokSearchRequest(query="phone", max_results=50)
        
        assert data.query == "phone"
        assert data.max_results == 50
    
    def test_search_request_defaults(self):
        """Test search request defaults."""
        from api.routes.tiktok import TikTokSearchRequest
        
        data = TikTokSearchRequest(query="test")
        
        assert data.max_results == 20


class TestTikTokProductResponse:
    """Tests for TikTokProductResponse model."""
    
    def test_product_response_with_alias(self):
        """Test product response with field aliases."""
        from api.routes.tiktok import TikTokProductResponse
        
        data = TikTokProductResponse(
            tiktok_id="123",
            title="Test Product",
            price=29.99,
            seller_name="Shop ABC",
            sold_count=100
        )
        
        assert data.id == "123"
        assert data.shop_name == "Shop ABC"
        assert data.sales_count == 100


class TestTikTokSearchResponse:
    """Tests for TikTokSearchResponse model."""
    
    def test_search_response_model(self):
        """Test search response model."""
        from api.routes.tiktok import (TikTokProductResponse,
                                       TikTokSearchResponse)
        
        product = TikTokProductResponse(
            tiktok_id="1",
            title="Product"
        )
        
        response = TikTokSearchResponse(
            products=[product],
            total=1,
            cached=True,
            cache_ttl=1800
        )
        
        assert response.total == 1
        assert response.cached is True
        assert response.scraper_type == "api"


class TestTikTokHealthResponse:
    """Tests for TikTokHealthResponse model."""
    
    def test_health_response_model(self):
        """Test health response model."""
        from api.routes.tiktok import TikTokHealthResponse
        
        response = TikTokHealthResponse(
            status="healthy",
            api_accessible=True,
            cookies_valid=True,
            response_time_ms=150.5
        )
        
        assert response.status == "healthy"
        assert response.error is None


class TestCacheStatsResponse:
    """Tests for CacheStatsResponse model."""
    
    def test_cache_stats_model(self):
        """Test cache stats model."""
        from api.routes.tiktok import CacheStatsResponse
        
        stats = CacheStatsResponse(
            total_keys=100,
            hits=80,
            misses=20,
            hit_rate=0.8,
            trending_cached=True,
            search_queries_cached=10
        )
        
        assert stats.hit_rate == 0.8
        assert stats.trending_cached is True


class TestSessionStatusValues:
    """Tests for session status handling."""
    
    @pytest.mark.asyncio
    async def test_session_status_active(self, mock_tiktok_dependencies, mock_user):
        """Test active session status display."""
        from api.routes.tiktok import list_sessions
        from api.services.tiktok_session import TikTokSessionStatus
        
        session = MagicMock()
        session.account_name = "active_account"
        session.status = TikTokSessionStatus.ACTIVE
        session.created_at = datetime.now(timezone.utc)
        session.last_used = datetime.now(timezone.utc)
        session.expires_at = datetime.now(timezone.utc)
        session.upload_count = 0
        
        mock_tiktok_dependencies.list_sessions = AsyncMock(return_value=[session])
        
        result = await list_sessions(mock_user)
        
        assert result["sessions"][0]["status"] == "active"
        assert result["sessions"][0]["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_session_status_expired(self, mock_tiktok_dependencies, mock_user):
        """Test expired session status display."""
        from api.routes.tiktok import list_sessions
        from api.services.tiktok_session import TikTokSessionStatus
        
        session = MagicMock()
        session.account_name = "expired_account"
        session.status = TikTokSessionStatus.EXPIRED
        session.created_at = datetime.now(timezone.utc)
        session.last_used = None
        session.expires_at = None
        session.upload_count = 0
        
        mock_tiktok_dependencies.list_sessions = AsyncMock(return_value=[session])
        
        result = await list_sessions(mock_user)
        
        assert result["sessions"][0]["is_valid"] is False


class TestPrivacyMapping:
    """Tests for privacy setting mapping."""
    
    def test_privacy_values(self):
        """Test privacy enum values are correctly imported."""
        from vendor.tiktok.client import Privacy
        
        assert Privacy.PUBLIC.value == "public"
        assert Privacy.FRIENDS.value == "friends"
        assert Privacy.PRIVATE.value == "private"
