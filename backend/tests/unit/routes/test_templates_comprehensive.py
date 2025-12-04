"""
Comprehensive tests for templates.py routes.
Target: templates.py 42% -> 95%+
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    return {
        "id": "user-123",
        "email": "test@example.com"
    }


@pytest.fixture
def mock_template_data():
    """Mock template data from Redis"""
    return {
        "id": "template-123",
        "name": "Test Template",
        "description": "A test template",
        "platform": "instagram",
        "category": "product",
        "caption_template": "🔥 {{product_name}} - {{price}}",
        "hashtags": '["sale", "product"]',
        "variables": '[{"name": "product_name", "description": "Name", "required": true}]',
        "thumbnail_url": None,
        "is_public": "False",
        "user_id": "user-123",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "usage_count": "5"
    }


# ============================================
# SCHEMA TESTS
# ============================================

class TestTemplateSchemas:
    """Test Pydantic schemas for templates"""
    
    def test_template_platform_enum(self):
        """Test TemplatePlatform enum values"""
        from api.routes.templates import TemplatePlatform
        
        assert TemplatePlatform.INSTAGRAM.value == "instagram"
        assert TemplatePlatform.TIKTOK.value == "tiktok"
        assert TemplatePlatform.YOUTUBE.value == "youtube"
        assert TemplatePlatform.ALL.value == "all"
    
    def test_template_category_enum(self):
        """Test TemplateCategory enum values"""
        from api.routes.templates import TemplateCategory
        
        assert TemplateCategory.PRODUCT.value == "product"
        assert TemplateCategory.PROMO.value == "promo"
        assert TemplateCategory.EDUCATIONAL.value == "educational"
        assert TemplateCategory.ENTERTAINMENT.value == "entertainment"
        assert TemplateCategory.CUSTOM.value == "custom"
    
    def test_template_variable_schema(self):
        """Test TemplateVariable schema"""
        from api.routes.templates import TemplateVariable
        
        var = TemplateVariable(
            name="{{product_name}}",
            description="The product name",
            default_value="Test Product",
            required=True
        )
        
        assert var.name == "{{product_name}}"
        assert var.description == "The product name"
        assert var.default_value == "Test Product"
        assert var.required is True
    
    def test_template_variable_defaults(self):
        """Test TemplateVariable default values"""
        from api.routes.templates import TemplateVariable
        
        var = TemplateVariable(
            name="{{name}}",
            description="Description"
        )
        
        assert var.default_value is None
        assert var.required is True
    
    def test_template_create_schema(self):
        """Test TemplateCreate schema"""
        from api.routes.templates import (TemplateCategory, TemplateCreate,
                                          TemplatePlatform)
        
        template = TemplateCreate(
            name="My Template",
            description="Description",
            platform=TemplatePlatform.INSTAGRAM,
            category=TemplateCategory.PRODUCT,
            caption_template="Test caption {{var}}",
            hashtags=["tag1", "tag2"],
            is_public=True
        )
        
        assert template.name == "My Template"
        assert template.platform == TemplatePlatform.INSTAGRAM
        assert template.is_public is True
    
    def test_template_create_defaults(self):
        """Test TemplateCreate default values"""
        from api.routes.templates import (TemplateCategory, TemplateCreate,
                                          TemplatePlatform)
        
        template = TemplateCreate(
            name="My Template",
            caption_template="Test caption"
        )
        
        assert template.platform == TemplatePlatform.ALL
        assert template.category == TemplateCategory.CUSTOM
        assert template.hashtags == []
        assert template.variables == []
        assert template.is_public is False
    
    def test_template_update_schema(self):
        """Test TemplateUpdate schema"""
        from api.routes.templates import TemplatePlatform, TemplateUpdate
        
        update = TemplateUpdate(
            name="Updated Name",
            platform=TemplatePlatform.TIKTOK,
            is_public=True
        )
        
        assert update.name == "Updated Name"
        assert update.platform == TemplatePlatform.TIKTOK
        assert update.is_public is True
    
    def test_template_update_partial(self):
        """Test TemplateUpdate with partial data"""
        from api.routes.templates import TemplateUpdate
        
        update = TemplateUpdate(name="Only Name")
        
        assert update.name == "Only Name"
        assert update.platform is None
        assert update.category is None
        assert update.is_public is None
    
    def test_render_request_schema(self):
        """Test RenderRequest schema"""
        from api.routes.templates import RenderRequest
        
        request = RenderRequest(
            variables={"product_name": "iPhone", "price": "$999"},
            include_hashtags=True
        )
        
        assert request.variables["product_name"] == "iPhone"
        assert request.include_hashtags is True
    
    def test_render_request_defaults(self):
        """Test RenderRequest default values"""
        from api.routes.templates import RenderRequest
        
        request = RenderRequest()
        
        assert request.variables == {}
        assert request.include_hashtags is True


# ============================================
# TEMPLATE SERVICE TESTS
# ============================================

class TestTemplateService:
    """Test TemplateService class"""
    
    @pytest.mark.asyncio
    async def test_create_template(self):
        """Test creating a template"""
        from api.routes.templates import (TemplateCreate, TemplatePlatform,
                                          template_service)
        
        data = TemplateCreate(
            name="Test Template",
            description="Description",
            platform=TemplatePlatform.INSTAGRAM,
            caption_template="Test {{var}}"
        )
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.hset = AsyncMock()
            mock_redis.sadd = AsyncMock()
            
            result = await template_service.create("user-123", data)
            
            assert result.name == "Test Template"
            assert result.platform == "instagram"
            mock_redis.hset.assert_called_once()
            mock_redis.sadd.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_template_exists(self, mock_template_data):
        """Test getting an existing template"""
        from api.routes.templates import template_service
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value=mock_template_data)
            
            result = await template_service.get("user-123", "template-123")
            
            assert result is not None
            assert result.id == "template-123"
            assert result.name == "Test Template"
    
    @pytest.mark.asyncio
    async def test_get_template_not_found(self):
        """Test getting a non-existent template"""
        from api.routes.templates import template_service
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value={})
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await template_service.get("user-123", "nonexistent")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_public_template(self, mock_template_data):
        """Test getting a public template from another user"""
        from api.routes.templates import template_service
        
        public_template = {**mock_template_data, "is_public": "True"}
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(side_effect=[{}, public_template])
            mock_redis.keys = AsyncMock(return_value=["templates:other-user:template-123"])
            
            result = await template_service.get("user-123", "template-123")
            
            assert result is not None
            assert result.is_public is True
    
    @pytest.mark.asyncio
    async def test_list_templates(self, mock_template_data):
        """Test listing templates"""
        from api.routes.templates import template_service
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.smembers = AsyncMock(return_value={"template-123"})
            mock_redis.hgetall = AsyncMock(return_value=mock_template_data)
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await template_service.list("user-123")
            
            assert len(result) == 1
            assert result[0].id == "template-123"
    
    @pytest.mark.asyncio
    async def test_list_templates_with_platform_filter(self, mock_template_data):
        """Test listing templates with platform filter"""
        from api.routes.templates import TemplatePlatform, template_service
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.smembers = AsyncMock(return_value={"template-123"})
            mock_redis.hgetall = AsyncMock(return_value=mock_template_data)
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await template_service.list(
                "user-123",
                platform=TemplatePlatform.INSTAGRAM
            )
            
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_list_templates_with_category_filter(self, mock_template_data):
        """Test listing templates with category filter"""
        from api.routes.templates import TemplateCategory, template_service
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.smembers = AsyncMock(return_value={"template-123"})
            mock_redis.hgetall = AsyncMock(return_value=mock_template_data)
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await template_service.list(
                "user-123",
                category=TemplateCategory.PRODUCT
            )
            
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_update_template(self, mock_template_data):
        """Test updating a template"""
        from api.routes.templates import TemplateUpdate, template_service
        
        update_data = TemplateUpdate(name="Updated Name")
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value=mock_template_data)
            mock_redis.hset = AsyncMock()
            
            result = await template_service.update("user-123", "template-123", update_data)
            
            assert result is not None
            mock_redis.hset.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_template_not_found(self):
        """Test updating a non-existent template"""
        from api.routes.templates import TemplateUpdate, template_service
        
        update_data = TemplateUpdate(name="Updated Name")
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value={})
            
            result = await template_service.update("user-123", "nonexistent", update_data)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_template(self):
        """Test deleting a template"""
        from api.routes.templates import template_service
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.delete = AsyncMock(return_value=1)
            mock_redis.srem = AsyncMock()
            
            result = await template_service.delete("user-123", "template-123")
            
            assert result is True
            mock_redis.srem.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_template_not_found(self):
        """Test deleting a non-existent template"""
        from api.routes.templates import template_service
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.delete = AsyncMock(return_value=0)
            
            result = await template_service.delete("user-123", "nonexistent")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_render_template(self, mock_template_data):
        """Test rendering a template with variables"""
        from api.routes.templates import template_service
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value=mock_template_data)
            mock_redis.hincrby = AsyncMock()
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await template_service.render(
                "user-123",
                "template-123",
                {"product_name": "iPhone", "price": "$999"},
                include_hashtags=True
            )
            
            assert "iPhone" in result["caption"]
            assert "$999" in result["caption"]
            assert result["platform"] == "instagram"
    
    @pytest.mark.asyncio
    async def test_render_template_without_hashtags(self, mock_template_data):
        """Test rendering a template without hashtags"""
        from api.routes.templates import template_service
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value=mock_template_data)
            mock_redis.hincrby = AsyncMock()
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await template_service.render(
                "user-123",
                "template-123",
                {"product_name": "iPhone"},
                include_hashtags=False
            )
            
            assert "#sale" not in result["caption"]
    
    @pytest.mark.asyncio
    async def test_render_template_not_found(self):
        """Test rendering a non-existent template"""
        from api.routes.templates import template_service
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value={})
            mock_redis.keys = AsyncMock(return_value=[])
            
            with pytest.raises(ValueError) as exc:
                await template_service.render("user-123", "nonexistent", {})
            
            assert "not found" in str(exc.value).lower()
    
    @pytest.mark.asyncio
    async def test_clone_template(self, mock_template_data):
        """Test cloning a template"""
        from api.routes.templates import template_service
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value=mock_template_data)
            mock_redis.hset = AsyncMock()
            mock_redis.sadd = AsyncMock()
            mock_redis.keys = AsyncMock(return_value=[])
            
            result = await template_service.clone("user-123", "template-123", "Cloned Template")
            
            assert result.name == "Cloned Template"
            assert "Cloned from" in result.description
    
    @pytest.mark.asyncio
    async def test_clone_template_not_found(self):
        """Test cloning a non-existent template"""
        from api.routes.templates import template_service
        
        with patch("api.routes.templates.redis_client") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value={})
            mock_redis.keys = AsyncMock(return_value=[])
            
            with pytest.raises(ValueError) as exc:
                await template_service.clone("user-123", "nonexistent", "Cloned")
            
            assert "not found" in str(exc.value).lower()


# ============================================
# ROUTE TESTS - LIST TEMPLATES
# ============================================

class TestListTemplatesRoute:
    """Test list_templates route"""
    
    @pytest.mark.asyncio
    async def test_list_templates_success(self, mock_current_user, mock_template_data):
        """Test listing templates successfully"""
        from api.routes.templates import list_templates
        
        with patch("api.routes.templates.template_service") as mock_service:
            mock_template = MagicMock()
            mock_template.model_dump.return_value = mock_template_data
            mock_service.list = AsyncMock(return_value=[mock_template])
            
            result = await list_templates(None, None, True, mock_current_user)
            
            assert "templates" in result
            assert len(result["templates"]) == 1


# ============================================
# ROUTE TESTS - CREATE TEMPLATE
# ============================================

class TestCreateTemplateRoute:
    """Test create_template route"""
    
    @pytest.mark.asyncio
    async def test_create_template_success(self, mock_current_user):
        """Test creating a template successfully"""
        from api.routes.templates import TemplateCreate, create_template
        
        data = TemplateCreate(
            name="New Template",
            caption_template="Test caption"
        )
        
        with patch("api.routes.templates.template_service") as mock_service:
            mock_template = MagicMock()
            mock_template.model_dump.return_value = {"id": "new-123", "name": "New Template"}
            mock_service.create = AsyncMock(return_value=mock_template)
            
            result = await create_template(data, mock_current_user)
            
            assert result["name"] == "New Template"


# ============================================
# ROUTE TESTS - GET DEFAULT TEMPLATES
# ============================================

class TestGetDefaultTemplatesRoute:
    """Test get_default_templates route"""
    
    @pytest.mark.asyncio
    async def test_get_default_templates(self):
        """Test getting default templates"""
        from api.routes.templates import (DEFAULT_TEMPLATES,
                                          get_default_templates)
        
        result = await get_default_templates()
        
        assert "templates" in result
        assert len(result["templates"]) == len(DEFAULT_TEMPLATES)
        assert any(t["name"] == "Produto em Destaque" for t in result["templates"])


# ============================================
# ROUTE TESTS - GET CATEGORIES
# ============================================

class TestGetCategoriesRoute:
    """Test get_categories route"""
    
    @pytest.mark.asyncio
    async def test_get_categories(self):
        """Test getting categories"""
        from api.routes.templates import get_categories
        
        result = await get_categories()
        
        assert "categories" in result
        assert len(result["categories"]) > 0
        
        values = [c["value"] for c in result["categories"]]
        assert "product" in values
        assert "promo" in values
        assert "educational" in values


# ============================================
# ROUTE TESTS - GET TEMPLATE
# ============================================

class TestGetTemplateRoute:
    """Test get_template route"""
    
    @pytest.mark.asyncio
    async def test_get_template_success(self, mock_current_user, mock_template_data):
        """Test getting a template successfully"""
        from api.routes.templates import get_template
        
        with patch("api.routes.templates.template_service") as mock_service:
            mock_template = MagicMock()
            mock_template.model_dump.return_value = mock_template_data
            mock_service.get = AsyncMock(return_value=mock_template)
            
            result = await get_template("template-123", mock_current_user)
            
            assert result["id"] == "template-123"
    
    @pytest.mark.asyncio
    async def test_get_template_not_found(self, mock_current_user):
        """Test getting a non-existent template"""
        from api.routes.templates import get_template
        
        with patch("api.routes.templates.template_service") as mock_service:
            mock_service.get = AsyncMock(return_value=None)
            
            with pytest.raises(HTTPException) as exc:
                await get_template("nonexistent", mock_current_user)
            
            assert exc.value.status_code == 404


# ============================================
# ROUTE TESTS - UPDATE TEMPLATE
# ============================================

class TestUpdateTemplateRoute:
    """Test update_template route"""
    
    @pytest.mark.asyncio
    async def test_update_template_success(self, mock_current_user, mock_template_data):
        """Test updating a template successfully"""
        from api.routes.templates import TemplateUpdate, update_template
        
        update_data = TemplateUpdate(name="Updated Name")
        
        with patch("api.routes.templates.template_service") as mock_service:
            mock_template = MagicMock()
            mock_template.model_dump.return_value = {**mock_template_data, "name": "Updated Name"}
            mock_service.update = AsyncMock(return_value=mock_template)
            
            result = await update_template("template-123", update_data, mock_current_user)
            
            assert result["name"] == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_update_template_not_found(self, mock_current_user):
        """Test updating a non-existent template"""
        from api.routes.templates import TemplateUpdate, update_template
        
        update_data = TemplateUpdate(name="Updated Name")
        
        with patch("api.routes.templates.template_service") as mock_service:
            mock_service.update = AsyncMock(return_value=None)
            
            with pytest.raises(HTTPException) as exc:
                await update_template("nonexistent", update_data, mock_current_user)
            
            assert exc.value.status_code == 404


# ============================================
# ROUTE TESTS - DELETE TEMPLATE
# ============================================

class TestDeleteTemplateRoute:
    """Test delete_template route"""
    
    @pytest.mark.asyncio
    async def test_delete_template_success(self, mock_current_user):
        """Test deleting a template successfully"""
        from api.routes.templates import delete_template
        
        with patch("api.routes.templates.template_service") as mock_service:
            mock_service.delete = AsyncMock(return_value=True)
            
            result = await delete_template("template-123", mock_current_user)
            
            assert result["status"] == "deleted"
    
    @pytest.mark.asyncio
    async def test_delete_template_not_found(self, mock_current_user):
        """Test deleting a non-existent template"""
        from api.routes.templates import delete_template
        
        with patch("api.routes.templates.template_service") as mock_service:
            mock_service.delete = AsyncMock(return_value=False)
            
            with pytest.raises(HTTPException) as exc:
                await delete_template("nonexistent", mock_current_user)
            
            assert exc.value.status_code == 404


# ============================================
# ROUTE TESTS - RENDER TEMPLATE
# ============================================

class TestRenderTemplateRoute:
    """Test render_template route"""
    
    @pytest.mark.asyncio
    async def test_render_template_success(self, mock_current_user):
        """Test rendering a template successfully"""
        from api.routes.templates import RenderRequest, render_template
        
        request = RenderRequest(
            variables={"product_name": "iPhone"},
            include_hashtags=True
        )
        
        with patch("api.routes.templates.template_service") as mock_service:
            mock_service.render = AsyncMock(return_value={
                "caption": "iPhone caption #sale",
                "hashtags": ["sale"],
                "platform": "instagram"
            })
            
            result = await render_template("template-123", request, mock_current_user)
            
            assert "caption" in result
            assert "iPhone" in result["caption"]
    
    @pytest.mark.asyncio
    async def test_render_template_not_found(self, mock_current_user):
        """Test rendering a non-existent template"""
        from api.routes.templates import RenderRequest, render_template
        
        request = RenderRequest()
        
        with patch("api.routes.templates.template_service") as mock_service:
            mock_service.render = AsyncMock(side_effect=ValueError("Template not found"))
            
            with pytest.raises(HTTPException) as exc:
                await render_template("nonexistent", request, mock_current_user)
            
            assert exc.value.status_code == 404


# ============================================
# ROUTE TESTS - CLONE TEMPLATE
# ============================================

class TestCloneTemplateRoute:
    """Test clone_template route"""
    
    @pytest.mark.asyncio
    async def test_clone_template_success(self, mock_current_user, mock_template_data):
        """Test cloning a template successfully"""
        from api.routes.templates import clone_template
        
        with patch("api.routes.templates.template_service") as mock_service:
            mock_template = MagicMock()
            mock_template.model_dump.return_value = {**mock_template_data, "name": "Cloned Template"}
            mock_service.clone = AsyncMock(return_value=mock_template)
            
            result = await clone_template("template-123", "Cloned Template", mock_current_user)
            
            assert result["name"] == "Cloned Template"
    
    @pytest.mark.asyncio
    async def test_clone_template_not_found(self, mock_current_user):
        """Test cloning a non-existent template"""
        from api.routes.templates import clone_template
        
        with patch("api.routes.templates.template_service") as mock_service:
            mock_service.clone = AsyncMock(side_effect=ValueError("Template not found"))
            
            with pytest.raises(HTTPException) as exc:
                await clone_template("nonexistent", "Cloned", mock_current_user)
            
            assert exc.value.status_code == 404


# ============================================
# DEFAULT TEMPLATES TESTS
# ============================================

class TestDefaultTemplates:
    """Test default templates data"""
    
    def test_default_templates_exist(self):
        """Test that default templates are defined"""
        from api.routes.templates import DEFAULT_TEMPLATES
        
        assert len(DEFAULT_TEMPLATES) > 0
    
    def test_default_templates_structure(self):
        """Test that default templates have required fields"""
        from api.routes.templates import DEFAULT_TEMPLATES
        
        for template in DEFAULT_TEMPLATES:
            assert "name" in template
            assert "description" in template
            assert "platform" in template
            assert "category" in template
            assert "caption_template" in template
            assert "hashtags" in template
            assert "variables" in template
    
    def test_default_templates_variables(self):
        """Test that default template variables are properly defined"""
        from api.routes.templates import DEFAULT_TEMPLATES
        
        for template in DEFAULT_TEMPLATES:
            for var in template["variables"]:
                assert "name" in var
                assert "description" in var
                assert "required" in var


# ============================================
# ROUTER TESTS
# ============================================

class TestTemplatesRouter:
    """Test router configuration"""
    
    def test_router_exists(self):
        """Test that router is defined"""
        from api.routes.templates import router
        
        assert router is not None
    
    def test_router_has_routes(self):
        """Test that router has expected routes"""
        from api.routes.templates import router
        
        routes = [r.path for r in router.routes if hasattr(r, 'path')]
        
        assert "" in routes  # list/create
        assert "/defaults" in routes
        assert "/categories" in routes
        assert "/{template_id}" in routes
        assert "/{template_id}/render" in routes
        assert "/{template_id}/clone" in routes
