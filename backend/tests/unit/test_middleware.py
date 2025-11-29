"""
Middleware Unit Tests
Tests for request_id, ratelimit, and security middleware
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request
from httpx import AsyncClient, ASGITransport

from api.middleware.request_id import RequestIDMiddleware
from api.middleware.ratelimit import RateLimitMiddleware
from api.middleware.security import SecurityHeadersMiddleware


# ============== RequestIDMiddleware Tests ==============

class TestRequestIDMiddleware:
    
    @pytest.fixture
    def app_with_request_id(self):
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"request_id": request.state.request_id}
        
        return app
    
    @pytest.mark.asyncio
    async def test_request_id_added_to_response(self, app_with_request_id):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_request_id),
            base_url="http://test"
        ) as client:
            response = await client.get("/test")
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 36  # UUID format
    
    @pytest.mark.asyncio
    async def test_request_id_is_uuid(self, app_with_request_id):
        import uuid
        async with AsyncClient(
            transport=ASGITransport(app=app_with_request_id),
            base_url="http://test"
        ) as client:
            response = await client.get("/test")
        
        request_id = response.headers["X-Request-ID"]
        # Validate UUID format
        try:
            uuid.UUID(request_id)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False
        
        assert is_valid_uuid
    
    @pytest.mark.asyncio
    async def test_request_id_available_in_request_state(
        self, app_with_request_id
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_request_id),
            base_url="http://test"
        ) as client:
            response = await client.get("/test")
        
        data = response.json()
        assert "request_id" in data
        assert data["request_id"] == response.headers["X-Request-ID"]
    
    @pytest.mark.asyncio
    async def test_unique_request_ids(self, app_with_request_id):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_request_id),
            base_url="http://test"
        ) as client:
            response1 = await client.get("/test")
            response2 = await client.get("/test")
        
        id1 = response1.headers["X-Request-ID"]
        id2 = response2.headers["X-Request-ID"]
        assert id1 != id2


# ============== RateLimitMiddleware Tests ==============

class TestRateLimitMiddleware:
    
    @pytest.fixture
    def app_with_ratelimit(self, monkeypatch):
        from fastapi.responses import JSONResponse
        from fastapi.exceptions import HTTPException as FastAPIHTTPException
        
        # Disable TESTING bypass for these specific tests
        monkeypatch.setenv("TESTING", "")
        
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, requests_per_minute=5)
        
        # Add exception handler for proper HTTPException handling
        @app.exception_handler(FastAPIHTTPException)
        async def http_exception_handler(request, exc):
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail if isinstance(exc.detail, dict) else {
                    "detail": exc.detail
                }
            )
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        return app
    
    @pytest.mark.asyncio
    async def test_request_within_limit(self, app_with_ratelimit):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_ratelimit),
            base_url="http://test"
        ) as client:
            response = await client.get("/test")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_health_endpoint_not_rate_limited(self, app_with_ratelimit):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_ratelimit),
            base_url="http://test"
        ) as client:
            # Make many requests to health
            for _ in range(20):
                response = await client.get("/health")
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self, app_with_ratelimit):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_ratelimit),
            base_url="http://test"
        ) as client:
            response = await client.get("/test")
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    @pytest.mark.asyncio
    async def test_rate_limit_remaining_decreases(self, app_with_ratelimit):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_ratelimit),
            base_url="http://test"
        ) as client:
            response1 = await client.get("/test")
            remaining1 = int(response1.headers["X-RateLimit-Remaining"])
            
            response2 = await client.get("/test")
            remaining2 = int(response2.headers["X-RateLimit-Remaining"])
        
        assert remaining2 < remaining1
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, app_with_ratelimit):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_ratelimit),
            base_url="http://test"
        ) as client:
            # Exhaust the rate limit (5 requests)
            for _ in range(5):
                await client.get("/test")
            
            # Next request should fail with 429
            response = await client.get("/test")
            assert response.status_code == 429


class TestRateLimitMiddlewareClientId:
    
    def test_get_client_id_with_bearer_token(self):
        app = FastAPI()
        middleware = RateLimitMiddleware(app, requests_per_minute=60)
        
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer abc123xyz789token"}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        
        client_id = middleware._get_client_id(mock_request)
        assert client_id.startswith("user:")
    
    def test_get_client_id_with_forwarded_header(self):
        app = FastAPI()
        middleware = RateLimitMiddleware(app, requests_per_minute=60)
        
        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        
        client_id = middleware._get_client_id(mock_request)
        assert client_id == "ip:192.168.1.1"
    
    def test_get_client_id_fallback_to_client_host(self):
        app = FastAPI()
        middleware = RateLimitMiddleware(app, requests_per_minute=60)
        
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.5"
        
        client_id = middleware._get_client_id(mock_request)
        assert client_id == "ip:10.0.0.5"
    
    def test_get_client_id_no_client(self):
        app = FastAPI()
        middleware = RateLimitMiddleware(app, requests_per_minute=60)
        
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client = None
        
        client_id = middleware._get_client_id(mock_request)
        assert client_id == "unknown"


# ============== SecurityHeadersMiddleware Tests ==============

class TestSecurityHeadersMiddleware:
    
    @pytest.fixture
    def app_with_security(self):
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        @app.get("/docs")
        async def docs():
            return {"docs": "swagger"}
        
        return app
    
    @pytest.mark.asyncio
    async def test_security_headers_added(self, app_with_security):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_security),
            base_url="http://test"
        ) as client:
            response = await client.get("/test")
        
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Strict-Transport-Security" in response.headers
    
    @pytest.mark.asyncio
    async def test_hsts_header_value(self, app_with_security):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_security),
            base_url="http://test"
        ) as client:
            response = await client.get("/test")
        
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts
    
    @pytest.mark.asyncio
    async def test_docs_endpoint_skipped(self, app_with_security):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_security),
            base_url="http://test"
        ) as client:
            response = await client.get("/docs")
        
        # Docs should still work (security check skipped)
        assert response.status_code == 200


# ============== Auth Middleware Tests ==============

class TestAuthMiddleware:
    """Tests for auth middleware functions"""

    @pytest.fixture
    def mock_database(self):
        """Mock the database module"""
        with patch("api.middleware.auth.database") as mock_db:
            mock_db.fetch_one = AsyncMock()
            yield mock_db

    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self, mock_database):
        """Test get_user_by_id returns user when found"""
        from api.middleware.auth import get_user_by_id
        
        mock_database.fetch_one.return_value = {
            "id": "user_123",
            "email": "test@example.com",
            "name": "Test User",
            "plan": "lifetime",
            "created_at": "2024-01-01T00:00:00"
        }
        
        result = await get_user_by_id("user_123")
        
        assert result is not None
        assert result["id"] == "user_123"
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, mock_database):
        """Test get_user_by_id returns None when not found"""
        from api.middleware.auth import get_user_by_id
        
        mock_database.fetch_one.return_value = None
        
        result = await get_user_by_id("nonexistent")
        
        assert result is None

    def test_create_access_token(self):
        """Test create_access_token generates valid JWT"""
        from api.middleware.auth import create_access_token
        from datetime import datetime, timedelta
        from jose import jwt
        
        expires_at = datetime.utcnow() + timedelta(hours=12)
        token = create_access_token(
            user_id="user_123",
            hwid="hwid_abc",
            expires_at=expires_at
        )
        
        assert token is not None
        assert len(token) > 0
        
        # Decode and verify
        from api.middleware.auth import JWT_SECRET_KEY, JWT_ALGORITHM
        payload = jwt.decode(
            token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        assert payload["sub"] == "user_123"
        assert payload["hwid"] == "hwid_abc"

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, mock_database):
        """Test get_current_user with valid token"""
        from api.middleware.auth import (
            get_current_user,
            create_access_token
        )
        from datetime import datetime, timedelta
        
        mock_database.fetch_one.return_value = {
            "id": "user_123",
            "email": "test@example.com",
            "name": "Test User",
            "plan": "lifetime",
            "created_at": "2024-01-01T00:00:00"
        }
        
        expires_at = datetime.utcnow() + timedelta(hours=12)
        token = create_access_token(
            user_id="user_123",
            hwid="hwid_abc",
            expires_at=expires_at
        )
        
        # Create mock credentials
        mock_creds = MagicMock()
        mock_creds.credentials = token
        
        user = await get_current_user(mock_creds)
        
        assert user["id"] == "user_123"
        assert user["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_database):
        """Test get_current_user rejects invalid token"""
        from api.middleware.auth import get_current_user
        from fastapi import HTTPException
        
        mock_creds = MagicMock()
        mock_creds.credentials = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_creds)
        
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, mock_database):
        """Test get_current_user rejects expired token"""
        from api.middleware.auth import (
            get_current_user,
            create_access_token
        )
        from datetime import datetime, timedelta
        from fastapi import HTTPException
        
        # Create expired token
        expires_at = datetime.utcnow() - timedelta(hours=1)
        token = create_access_token(
            user_id="user_123",
            hwid="hwid_abc",
            expires_at=expires_at
        )
        
        mock_creds = MagicMock()
        mock_creds.credentials = token
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_creds)
        
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, mock_database):
        """Test get_current_user when user not in database"""
        from api.middleware.auth import (
            get_current_user,
            create_access_token
        )
        from datetime import datetime, timedelta
        from fastapi import HTTPException
        
        mock_database.fetch_one.return_value = None
        
        expires_at = datetime.utcnow() + timedelta(hours=12)
        token = create_access_token(
            user_id="deleted_user",
            hwid="hwid_abc",
            expires_at=expires_at
        )
        
        mock_creds = MagicMock()
        mock_creds.credentials = token
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_creds)
        
        assert exc_info.value.status_code == 401
        assert "not found" in exc_info.value.detail.lower()


# ============== Quota/Credits Middleware Tests ==============

class TestQuotaMiddleware:
    """Tests for quota/credits middleware functions"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database connection"""
        mock = AsyncMock()
        mock.fetchrow = AsyncMock()
        mock.execute = AsyncMock()
        return mock

    def test_insufficient_credits_error(self):
        """Test InsufficientCreditsError exception"""
        from api.middleware.quota import InsufficientCreditsError
        
        error = InsufficientCreditsError(
            "Not enough credits",
            required=5,
            available=2
        )
        
        assert error.message == "Not enough credits"
        assert error.required == 5
        assert error.available == 2
        assert str(error) == "Not enough credits"

    def test_quota_exceeded_error_alias(self):
        """Test QuotaExceededError is alias"""
        from api.middleware.quota import (
            QuotaExceededError,
            InsufficientCreditsError
        )
        
        assert QuotaExceededError is InsufficientCreditsError

    def test_credit_costs_defined(self):
        """Test credit costs are properly defined"""
        from api.middleware.quota import CREDIT_COSTS
        
        assert "copy" in CREDIT_COSTS
        assert "trend_analysis" in CREDIT_COSTS
        assert "niche_report" in CREDIT_COSTS
        assert CREDIT_COSTS["copy"] == 1
        assert CREDIT_COSTS["trend_analysis"] == 2
        assert CREDIT_COSTS["niche_report"] == 5

    @pytest.mark.asyncio
    async def test_get_user_credits_success(self, mock_db):
        """Test getting user credits"""
        from api.middleware.quota import get_user_credits
        
        mock_db.fetchrow.return_value = {
            "balance": 100,
            "total_purchased": 150,
            "total_used": 50
        }
        
        result = await get_user_credits("user_123", mock_db)
        
        assert result["balance"] == 100
        assert result["total_purchased"] == 150
        assert result["total_used"] == 50

    @pytest.mark.asyncio
    async def test_get_user_credits_not_found(self, mock_db):
        """Test get_user_credits raises for missing user"""
        from api.middleware.quota import get_user_credits
        from fastapi import HTTPException
        
        mock_db.fetchrow.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_user_credits("missing", mock_db)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_check_credits_sufficient(self, mock_db):
        """Test check_credits with sufficient balance"""
        from api.middleware.quota import check_credits
        
        mock_db.fetchrow.return_value = {
            "balance": 100,
            "total_purchased": 100,
            "total_used": 0
        }
        
        result = await check_credits("user_123", "copy", mock_db)
        
        assert result["balance"] == 100
        assert result["required"] == 1
        assert result["remaining_after"] == 99

    @pytest.mark.asyncio
    async def test_check_credits_insufficient(self, mock_db):
        """Test check_credits raises for insufficient balance"""
        from api.middleware.quota import (
            check_credits,
            InsufficientCreditsError
        )
        
        mock_db.fetchrow.return_value = {
            "balance": 0,
            "total_purchased": 10,
            "total_used": 10
        }
        
        with pytest.raises(InsufficientCreditsError) as exc_info:
            await check_credits("user_123", "copy", mock_db)
        
        assert exc_info.value.required == 1
        assert exc_info.value.available == 0

    @pytest.mark.asyncio
    async def test_check_credits_trend_analysis(self, mock_db):
        """Test check_credits for trend_analysis (2 credits)"""
        from api.middleware.quota import check_credits
        
        mock_db.fetchrow.return_value = {
            "balance": 10,
            "total_purchased": 10,
            "total_used": 0
        }
        
        result = await check_credits("user_123", "trend_analysis", mock_db)
        
        assert result["required"] == 2
        assert result["remaining_after"] == 8

    @pytest.mark.asyncio
    async def test_deduct_credits_success(self, mock_db):
        """Test successful credit deduction"""
        from api.middleware.quota import deduct_credits
        
        mock_db.fetchrow.return_value = {"new_balance": 99}
        
        result = await deduct_credits("user_123", "copy", mock_db)
        
        assert result["new_balance"] == 99
        assert result["cost"] == 1

    @pytest.mark.asyncio
    async def test_deduct_credits_insufficient(self, mock_db):
        """Test deduct_credits raises when insufficient"""
        from api.middleware.quota import (
            deduct_credits,
            InsufficientCreditsError
        )
        
        mock_db.fetchrow.return_value = None  # UPDATE returns nothing
        
        with pytest.raises(InsufficientCreditsError):
            await deduct_credits("user_123", "copy", mock_db)

    @pytest.mark.asyncio
    async def test_add_credits_success(self, mock_db):
        """Test adding credits to user"""
        from api.middleware.quota import add_credits
        
        mock_db.fetchrow.return_value = {"new_balance": 200}
        
        result = await add_credits("user_123", 100, "pay_123", mock_db)
        
        assert result["new_balance"] == 200
        assert result["added"] == 100
        mock_db.execute.assert_called_once()  # Log purchase

    @pytest.mark.asyncio
    async def test_add_credits_without_payment_id(self, mock_db):
        """Test adding credits without payment logging"""
        from api.middleware.quota import add_credits
        
        mock_db.fetchrow.return_value = {"new_balance": 150}
        
        result = await add_credits("user_123", 50, None, mock_db)
        
        assert result["new_balance"] == 150
        mock_db.execute.assert_not_called()  # No log

    @pytest.mark.asyncio
    async def test_add_credits_user_not_found(self, mock_db):
        """Test add_credits raises for missing user"""
        from api.middleware.quota import add_credits
        from fastapi import HTTPException
        
        mock_db.fetchrow.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await add_credits("missing", 100, None, mock_db)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_legacy_check_copy_quota(self, mock_db):
        """Test legacy check_copy_quota function"""
        from api.middleware.quota import check_copy_quota
        
        mock_db.fetchrow.return_value = {
            "balance": 50,
            "total_purchased": 50,
            "total_used": 0
        }
        
        result = await check_copy_quota("user_123", mock_db)
        
        assert result["required"] == 1

    @pytest.mark.asyncio
    async def test_legacy_get_user_quota(self, mock_db):
        """Test legacy get_user_quota function"""
        from api.middleware.quota import get_user_quota
        
        mock_db.fetchrow.return_value = {
            "balance": 75,
            "total_purchased": 100,
            "total_used": 25
        }
        
        result = await get_user_quota("user_123", "copy", mock_db)
        
        assert result["used"] == 25
        assert result["remaining"] == 75
        assert result["limit"] == -1
        assert result["plan"] == "lifetime"

    @pytest.mark.asyncio
    async def test_legacy_increment_quota(self, mock_db):
        """Test legacy increment_quota function"""
        from api.middleware.quota import increment_quota
        
        mock_db.fetchrow.return_value = {"new_balance": 49}
        
        await increment_quota("user_123", "copy", 1, mock_db)
        
        mock_db.fetchrow.assert_called()

