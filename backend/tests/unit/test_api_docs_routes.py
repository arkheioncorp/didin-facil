"""
Unit tests for API Documentation Routes
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestAPIDocsRoutes:
    """Tests for API documentation endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_api_categories(self):
        from api.routes.api_docs import get_api_categories, API_CATEGORIES
        
        result = await get_api_categories()
        
        assert "categories" in result
        assert len(result["categories"]) == len(API_CATEGORIES)
        
        for cat in result["categories"]:
            assert "name" in cat
            assert "description" in cat
            assert "icon" in cat
            assert "base_path" in cat
            assert "endpoints_count" in cat
    
    @pytest.mark.asyncio
    async def test_get_category_endpoints_valid(self):
        from api.routes.api_docs import get_category_endpoints
        
        result = await get_category_endpoints("Autenticação")
        
        assert "name" in result
        assert "description" in result
        assert "endpoints" in result
        assert len(result["endpoints"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_category_endpoints_by_path(self):
        from api.routes.api_docs import get_category_endpoints
        
        result = await get_category_endpoints("auth")
        
        assert "name" in result
        assert result["base_path"] == "/auth"
    
    @pytest.mark.asyncio
    async def test_get_category_endpoints_not_found(self):
        from api.routes.api_docs import get_category_endpoints
        
        result = await get_category_endpoints("nonexistent")
        
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_search_endpoints(self):
        from api.routes.api_docs import search_endpoints
        
        result = await search_endpoints("login")
        
        assert "results" in result
        assert "count" in result
        assert result["count"] > 0
        
        for res in result["results"]:
            assert "category" in res
            assert "path" in res
            assert "method" in res
            assert "summary" in res
    
    @pytest.mark.asyncio
    async def test_search_endpoints_no_results(self):
        from api.routes.api_docs import search_endpoints
        
        result = await search_endpoints("xyznonexistent123")
        
        assert "results" in result
        assert result["count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_api_overview(self):
        from api.routes.api_docs import get_api_overview
        
        result = await get_api_overview()
        
        assert "api_name" in result
        assert "version" in result
        assert "description" in result
        assert "base_url" in result
        assert "total_categories" in result
        assert "total_endpoints" in result
        assert "authentication" in result
        assert "rate_limiting" in result
        assert "documentation_urls" in result
        assert "categories" in result
        
        # Check authentication details
        assert "type" in result["authentication"]
        assert "header" in result["authentication"]
        
        # Check rate limiting details
        assert "default" in result["rate_limiting"]
        assert "authenticated" in result["rate_limiting"]
        
        # Check documentation URLs
        assert "openapi" in result["documentation_urls"]
        assert "swagger_ui" in result["documentation_urls"]
        assert "redoc" in result["documentation_urls"]
    
    @pytest.mark.asyncio
    async def test_get_interactive_docs(self):
        from api.routes.api_docs import get_interactive_docs
        
        result = await get_interactive_docs()
        
        # Should return HTML
        assert "<!DOCTYPE html>" in result
        assert "Didin Fácil API" in result
        assert "Documentação" in result.lower() or "API" in result


class TestAPIDocumentation:
    """Tests for API documentation content"""
    
    def test_all_categories_have_required_fields(self):
        from api.routes.api_docs import API_CATEGORIES
        
        for cat in API_CATEGORIES:
            assert "name" in cat
            assert "description" in cat
            assert "icon" in cat
            assert "base_path" in cat
            
            if "endpoints" in cat:
                for endpoint in cat["endpoints"]:
                    assert "path" in endpoint
                    assert "method" in endpoint
                    assert "summary" in endpoint
    
    def test_endpoints_have_valid_methods(self):
        from api.routes.api_docs import API_CATEGORIES
        
        valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}
        
        for cat in API_CATEGORIES:
            for endpoint in cat.get("endpoints", []):
                assert endpoint["method"] in valid_methods
    
    def test_examples_have_required_fields(self):
        from api.routes.api_docs import API_CATEGORIES
        
        for cat in API_CATEGORIES:
            for endpoint in cat.get("endpoints", []):
                for example in endpoint.get("examples", []):
                    assert "description" in example
                    assert "response" in example
    
    def test_total_endpoints_count(self):
        from api.routes.api_docs import API_CATEGORIES
        
        total = sum(len(cat.get("endpoints", [])) for cat in API_CATEGORIES)
        
        # Should have a reasonable number of documented endpoints
        assert total >= 10
    
    def test_authentication_category_exists(self):
        from api.routes.api_docs import API_CATEGORIES
        
        auth_cats = [c for c in API_CATEGORIES if "auth" in c["name"].lower() or "autenticação" in c["name"].lower()]
        assert len(auth_cats) > 0
    
    def test_social_media_categories_exist(self):
        from api.routes.api_docs import API_CATEGORIES
        
        social_platforms = ["instagram", "tiktok", "youtube"]
        
        for platform in social_platforms:
            matching = [c for c in API_CATEGORIES if platform.lower() in c["name"].lower()]
            assert len(matching) > 0, f"Missing category for {platform}"


class TestEndpointModels:
    """Tests for endpoint documentation models"""
    
    def test_endpoint_example_model(self):
        from api.routes.api_docs import EndpointExample
        
        example = EndpointExample(
            description="Test example",
            request={"key": "value"},
            response={"status": "success"}
        )
        
        assert example.description == "Test example"
        assert example.request == {"key": "value"}
        assert example.response == {"status": "success"}
    
    def test_endpoint_example_optional_fields(self):
        from api.routes.api_docs import EndpointExample
        
        example = EndpointExample(
            description="Test",
            response={"data": "test"}
        )
        
        assert example.request is None
        assert example.curl_example is None
    
    def test_endpoint_doc_model(self):
        from api.routes.api_docs import EndpointDoc
        
        doc = EndpointDoc(
            path="/test",
            method="GET",
            summary="Test endpoint",
            description="A test endpoint",
            tags=["test"]
        )
        
        assert doc.path == "/test"
        assert doc.method == "GET"
        assert doc.auth_required is True  # Default
    
    def test_api_category_model(self):
        from api.routes.api_docs import APICategory
        
        cat = APICategory(
            name="Test",
            description="Test category",
            icon="🧪",
            endpoints_count=5,
            base_path="/test"
        )
        
        assert cat.name == "Test"
        assert cat.endpoints_count == 5
