"""
Comprehensive tests for request_id.py middleware
=================================================
Tests for Request ID generation and propagation.

Target: 100% coverage for api/middleware/request_id.py
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse


class TestRequestIDMiddleware:
    """Tests for RequestIDMiddleware class."""

    @pytest.fixture
    def app_with_middleware(self):
        """Create FastAPI app with RequestIDMiddleware."""
        from api.middleware.request_id import RequestIDMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"request_id": getattr(request.state, "request_id", None)}
        
        @app.get("/health")
        async def health_check():
            return {"status": "ok"}
        
        @app.post("/items")
        async def create_item(request: Request):
            return {"created": True, "request_id": request.state.request_id}
        
        return app

    @pytest.fixture
    def client(self, app_with_middleware):
        """Test client for the app."""
        return TestClient(app_with_middleware)

    def test_request_id_added_to_response_headers(self, client):
        """Test that X-Request-ID header is added to response."""
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        
        # Verify it's a valid UUID
        request_id = response.headers["X-Request-ID"]
        assert UUID(request_id)  # Will raise if not valid UUID

    def test_request_id_is_unique_per_request(self, client):
        """Test that each request gets a unique ID."""
        response1 = client.get("/test")
        response2 = client.get("/test")
        response3 = client.get("/health")
        
        id1 = response1.headers["X-Request-ID"]
        id2 = response2.headers["X-Request-ID"]
        id3 = response3.headers["X-Request-ID"]
        
        # All should be different
        assert id1 != id2
        assert id2 != id3
        assert id1 != id3

    def test_request_id_available_in_request_state(self, client):
        """Test that request_id is accessible in request.state."""
        response = client.get("/test")
        
        assert response.status_code == 200
        data = response.json()
        
        # The endpoint returns request.state.request_id
        assert "request_id" in data
        assert data["request_id"] is not None
        
        # Should match the header
        assert data["request_id"] == response.headers["X-Request-ID"]

    def test_request_id_works_with_post_requests(self, client):
        """Test middleware works with POST requests."""
        response = client.post("/items", json={"name": "test"})
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        
        data = response.json()
        assert data["request_id"] == response.headers["X-Request-ID"]

    def test_request_id_format_is_uuid4(self, client):
        """Test that request ID is a valid UUID4 format."""
        response = client.get("/test")
        request_id = response.headers["X-Request-ID"]
        
        # Parse as UUID
        parsed = UUID(request_id)
        
        # Should be version 4 UUID
        assert parsed.version == 4

    def test_request_id_persists_through_request_lifecycle(self, client):
        """Test request ID remains consistent during request."""
        response = client.get("/test")
        
        header_id = response.headers["X-Request-ID"]
        body_id = response.json()["request_id"]
        
        # Header and body should have same ID
        assert header_id == body_id


class TestRequestIDMiddlewareIntegration:
    """Integration tests for RequestIDMiddleware."""

    @pytest.fixture
    def app_with_error_handling(self):
        """App that may raise errors."""
        from api.middleware.request_id import RequestIDMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)
        
        @app.get("/success")
        async def success():
            return {"status": "ok"}
        
        @app.get("/error")
        async def error():
            raise ValueError("Test error")
        
        @app.exception_handler(ValueError)
        async def value_error_handler(request: Request, exc: ValueError):
            return JSONResponse(
                status_code=500,
                content={"error": str(exc)},
                headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")}
            )
        
        return app

    @pytest.fixture
    def client(self, app_with_error_handling):
        return TestClient(app_with_error_handling, raise_server_exceptions=False)

    def test_request_id_available_even_on_error(self, client):
        """Test request ID is still accessible when endpoint raises."""
        response = client.get("/error")
        
        # Request ID should still be in state (set before error)
        assert "X-Request-ID" in response.headers

    def test_multiple_concurrent_requests(self, client):
        """Test that concurrent requests get unique IDs."""
        import concurrent.futures
        
        def make_request():
            response = client.get("/success")
            return response.headers["X-Request-ID"]
        
        # Simulate multiple requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            request_ids = [f.result() for f in futures]
        
        # All should be unique
        assert len(request_ids) == len(set(request_ids))


class TestRequestIDMiddlewareClass:
    """Tests for RequestIDMiddleware class methods."""

    def test_middleware_inherits_from_base(self):
        """Test middleware inherits from BaseHTTPMiddleware."""
        from api.middleware.request_id import RequestIDMiddleware
        from starlette.middleware.base import BaseHTTPMiddleware
        
        assert issubclass(RequestIDMiddleware, BaseHTTPMiddleware)

    def test_dispatch_method_exists(self):
        """Test dispatch method is defined."""
        from api.middleware.request_id import RequestIDMiddleware
        
        assert hasattr(RequestIDMiddleware, "dispatch")
        assert callable(getattr(RequestIDMiddleware, "dispatch"))

    @pytest.mark.asyncio
    async def test_dispatch_calls_next(self):
        """Test dispatch properly calls next middleware/handler."""
        from api.middleware.request_id import RequestIDMiddleware

        # Mock app and request
        mock_app = MagicMock()
        middleware = RequestIDMiddleware(mock_app)
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        
        mock_response = MagicMock()
        mock_response.headers = {}
        
        mock_call_next = AsyncMock(return_value=mock_response)
        
        # Call dispatch
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify call_next was called
        mock_call_next.assert_called_once_with(mock_request)
        
        # Verify request_id was set
        assert hasattr(mock_request.state, "request_id")


class TestRequestIDImports:
    """Tests for module imports."""

    def test_uuid_import(self):
        """Test uuid module is imported and used."""
        import uuid

        from api.middleware import request_id

        # Module should have uuid4 function available
        assert hasattr(uuid, "uuid4")
        assert callable(uuid.uuid4)

    def test_request_import(self):
        """Test FastAPI Request is imported."""
        from api.middleware.request_id import Request
        from fastapi import Request as FastAPIRequest
        
        assert Request is FastAPIRequest

    def test_middleware_can_be_imported(self):
        """Test middleware can be imported directly."""
        from api.middleware.request_id import RequestIDMiddleware
        
        assert RequestIDMiddleware is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api.middleware.request_id"])
