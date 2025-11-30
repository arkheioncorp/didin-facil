"""
Unit tests for Content Templates Routes
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
import json


class MockUser:
    id = "user_123"
    email = "test@example.com"


@pytest.fixture
def mock_current_user():
    return MockUser()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.get.return_value = None
    redis.set.return_value = True
    redis.hgetall.return_value = {}
    redis.hset.return_value = True
    redis.delete.return_value = 1
    redis.keys.return_value = []
    redis.smembers.return_value = set()
    redis.sadd.return_value = 1
    redis.srem.return_value = 1
    redis.hincrby.return_value = 1
    return redis


class TestTemplateService:
    """Tests for TemplateService"""
    
    @pytest.mark.asyncio
    async def test_create_template(self, mock_current_user, mock_redis):
        from api.routes.templates import template_service, TemplateCreate, TemplatePlatform, TemplateCategory
        
        with patch("api.routes.templates.redis_client", mock_redis):
            data = TemplateCreate(
                name="Test Template",
                description="A test template",
                platform=TemplatePlatform.INSTAGRAM,
                category=TemplateCategory.PRODUCT,
                caption_template="🔥 {{product_name}} - R$ {{price}}",
                hashtags=["oferta", "promocao"],
                variables=[]
            )
            
            template = await template_service.create(str(mock_current_user.id), data)
            
            assert template.name == "Test Template"
            assert template.platform == "instagram"
            assert template.category == "product"
            assert "product_name" in template.caption_template
            mock_redis.hset.assert_called()
            mock_redis.sadd.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_template(self, mock_current_user, mock_redis):
        from api.routes.templates import template_service
        
        mock_redis.hgetall.return_value = {
            "id": "template-123",
            "name": "Test Template",
            "description": "Description",
            "platform": "instagram",
            "category": "product",
            "caption_template": "Test caption",
            "hashtags": json.dumps(["test"]),
            "variables": json.dumps([]),
            "is_public": "False",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "usage_count": "5"
        }
        
        with patch("api.routes.templates.redis_client", mock_redis):
            template = await template_service.get(str(mock_current_user.id), "template-123")
            
            assert template is not None
            assert template.id == "template-123"
            assert template.name == "Test Template"
            assert template.usage_count == 5
    
    @pytest.mark.asyncio
    async def test_get_template_not_found(self, mock_current_user, mock_redis):
        from api.routes.templates import template_service
        
        mock_redis.hgetall.return_value = {}
        mock_redis.keys.return_value = []
        
        with patch("api.routes.templates.redis_client", mock_redis):
            template = await template_service.get(str(mock_current_user.id), "nonexistent")
            assert template is None
    
    @pytest.mark.asyncio
    async def test_list_templates(self, mock_current_user, mock_redis):
        from api.routes.templates import template_service
        
        mock_redis.smembers.return_value = {"template-1", "template-2"}
        mock_redis.hgetall.side_effect = [
            {
                "id": "template-1",
                "name": "Template 1",
                "platform": "instagram",
                "category": "product",
                "caption_template": "Caption 1",
                "hashtags": json.dumps([]),
                "variables": json.dumps([]),
                "is_public": "False",
                "user_id": "user_123",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "usage_count": "10"
            },
            {
                "id": "template-2",
                "name": "Template 2",
                "platform": "tiktok",
                "category": "promo",
                "caption_template": "Caption 2",
                "hashtags": json.dumps([]),
                "variables": json.dumps([]),
                "is_public": "False",
                "user_id": "user_123",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "usage_count": "5"
            }
        ]
        mock_redis.keys.return_value = []
        
        with patch("api.routes.templates.redis_client", mock_redis):
            templates = await template_service.list(str(mock_current_user.id))
            
            assert len(templates) == 2
            # Should be sorted by usage_count (descending)
            assert templates[0].usage_count >= templates[1].usage_count
    
    @pytest.mark.asyncio
    async def test_update_template(self, mock_current_user, mock_redis):
        from api.routes.templates import template_service, TemplateUpdate
        
        mock_redis.hgetall.return_value = {
            "id": "template-123",
            "name": "Old Name",
            "platform": "instagram",
            "category": "product",
            "caption_template": "Old caption",
            "hashtags": json.dumps([]),
            "variables": json.dumps([]),
            "is_public": "False",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "usage_count": "0"
        }
        
        with patch("api.routes.templates.redis_client", mock_redis):
            update_data = TemplateUpdate(name="New Name", is_public=True)
            await template_service.update(
                str(mock_current_user.id),
                "template-123",
                update_data
            )
            
            mock_redis.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete_template(self, mock_current_user, mock_redis):
        from api.routes.templates import template_service
        
        mock_redis.delete.return_value = 1
        
        with patch("api.routes.templates.redis_client", mock_redis):
            result = await template_service.delete(str(mock_current_user.id), "template-123")
            
            assert result is True
            mock_redis.delete.assert_called()
            mock_redis.srem.assert_called()
    
    @pytest.mark.asyncio
    async def test_render_template(self, mock_current_user, mock_redis):
        from api.routes.templates import template_service
        
        mock_redis.hgetall.return_value = {
            "id": "template-123",
            "name": "Product Template",
            "platform": "instagram",
            "category": "product",
            "caption_template": "🔥 {{product_name}} por apenas R$ {{price}}!",
            "hashtags": json.dumps(["oferta", "promocao"]),
            "variables": json.dumps([]),
            "is_public": "False",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "usage_count": "0"
        }
        
        with patch("api.routes.templates.redis_client", mock_redis):
            result = await template_service.render(
                str(mock_current_user.id),
                "template-123",
                {"product_name": "Smartphone XYZ", "price": "999.90"},
                include_hashtags=True
            )
            
            assert "Smartphone XYZ" in result["caption"]
            assert "999.90" in result["caption"]
            assert "#oferta" in result["caption"]
            assert "#promocao" in result["caption"]
    
    @pytest.mark.asyncio
    async def test_render_without_hashtags(self, mock_current_user, mock_redis):
        from api.routes.templates import template_service
        
        mock_redis.hgetall.return_value = {
            "id": "template-123",
            "name": "Test",
            "platform": "all",
            "category": "custom",
            "caption_template": "Hello {{name}}!",
            "hashtags": json.dumps(["test"]),
            "variables": json.dumps([]),
            "is_public": "False",
            "user_id": "user_123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "usage_count": "0"
        }
        
        with patch("api.routes.templates.redis_client", mock_redis):
            result = await template_service.render(
                str(mock_current_user.id),
                "template-123",
                {"name": "World"},
                include_hashtags=False
            )
            
            assert "Hello World!" in result["caption"]
            assert "#test" not in result["caption"]
    
    @pytest.mark.asyncio
    async def test_clone_template(self, mock_current_user, mock_redis):
        from api.routes.templates import template_service
        
        mock_redis.hgetall.return_value = {
            "id": "original-123",
            "name": "Original Template",
            "platform": "instagram",
            "category": "product",
            "caption_template": "Test caption",
            "hashtags": json.dumps(["test"]),
            "variables": json.dumps([]),
            "is_public": "True",
            "user_id": "other_user",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "usage_count": "100"
        }
        
        with patch("api.routes.templates.redis_client", mock_redis):
            cloned = await template_service.clone(
                str(mock_current_user.id),
                "original-123",
                "My Clone"
            )
            
            assert cloned.name == "My Clone"
            assert cloned.user_id == str(mock_current_user.id)
            assert cloned.is_public is False  # Clones are private by default


class TestTemplateRoutes:
    """Tests for template HTTP endpoints"""
    
    @pytest.mark.asyncio
    async def test_list_templates_endpoint(self, mock_current_user, mock_redis):
        from api.routes.templates import list_templates
        
        mock_redis.smembers.return_value = set()
        mock_redis.keys.return_value = []
        
        with patch("api.routes.templates.redis_client", mock_redis):
            with patch("api.routes.templates.get_current_user", return_value=mock_current_user):
                result = await list_templates(
                    platform=None,
                    category=None,
                    include_public=True,
                    current_user=mock_current_user
                )
                
                assert "templates" in result
    
    @pytest.mark.asyncio
    async def test_get_default_templates(self):
        from api.routes.templates import get_default_templates, DEFAULT_TEMPLATES
        
        result = await get_default_templates()
        
        assert "templates" in result
        assert len(result["templates"]) == len(DEFAULT_TEMPLATES)
        
        # Check that defaults have required fields
        for template in result["templates"]:
            assert "name" in template
            assert "platform" in template
            assert "category" in template
            assert "caption_template" in template
    
    @pytest.mark.asyncio
    async def test_get_categories(self):
        from api.routes.templates import get_categories
        
        result = await get_categories()
        
        assert "categories" in result
        assert len(result["categories"]) > 0
        
        for cat in result["categories"]:
            assert "value" in cat
            assert "label" in cat


class TestTemplateValidation:
    """Tests for template validation"""
    
    def test_template_create_validation(self):
        from api.routes.templates import TemplateCreate, TemplatePlatform, TemplateCategory
        
        # Valid template
        template = TemplateCreate(
            name="Valid Template",
            platform=TemplatePlatform.ALL,
            category=TemplateCategory.CUSTOM,
            caption_template="Test caption"
        )
        assert template.name == "Valid Template"
    
    def test_template_name_too_long(self):
        from api.routes.templates import TemplateCreate, TemplatePlatform, TemplateCategory
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            TemplateCreate(
                name="A" * 101,  # Max is 100
                platform=TemplatePlatform.ALL,
                category=TemplateCategory.CUSTOM,
                caption_template="Test"
            )
    
    def test_template_caption_too_long(self):
        from api.routes.templates import TemplateCreate, TemplatePlatform, TemplateCategory
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            TemplateCreate(
                name="Test",
                platform=TemplatePlatform.ALL,
                category=TemplateCategory.CUSTOM,
                caption_template="A" * 2201  # Max is 2200
            )
    
    def test_template_too_many_hashtags(self):
        from api.routes.templates import TemplateCreate, TemplatePlatform, TemplateCategory
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            TemplateCreate(
                name="Test",
                platform=TemplatePlatform.ALL,
                category=TemplateCategory.CUSTOM,
                caption_template="Test",
                hashtags=["tag"] * 31  # Max is 30
            )
