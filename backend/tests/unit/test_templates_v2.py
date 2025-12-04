"""
Testes para api/routes/templates.py
Content Templates Routes
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.templates import (DEFAULT_TEMPLATES, RenderRequest, Template,
                                  TemplateCategory, TemplateCreate,
                                  TemplatePlatform, TemplateService,
                                  TemplateUpdate, TemplateVariable)

# ==================== TEST ENUMS ====================

class TestTemplatePlatform:
    """Testes para TemplatePlatform enum."""

    def test_instagram_value(self):
        assert TemplatePlatform.INSTAGRAM.value == "instagram"

    def test_tiktok_value(self):
        assert TemplatePlatform.TIKTOK.value == "tiktok"

    def test_youtube_value(self):
        assert TemplatePlatform.YOUTUBE.value == "youtube"

    def test_all_value(self):
        assert TemplatePlatform.ALL.value == "all"


class TestTemplateCategory:
    """Testes para TemplateCategory enum."""

    def test_product_value(self):
        assert TemplateCategory.PRODUCT.value == "product"

    def test_promo_value(self):
        assert TemplateCategory.PROMO.value == "promo"

    def test_educational_value(self):
        assert TemplateCategory.EDUCATIONAL.value == "educational"

    def test_entertainment_value(self):
        assert TemplateCategory.ENTERTAINMENT.value == "entertainment"

    def test_custom_value(self):
        assert TemplateCategory.CUSTOM.value == "custom"


# ==================== TEST MODELS ====================

class TestTemplateVariable:
    """Testes para modelo TemplateVariable."""

    def test_minimal_variable(self):
        var = TemplateVariable(
            name="{{product_name}}",
            description="Product name"
        )
        
        assert var.name == "{{product_name}}"
        assert var.default_value is None
        assert var.required is True

    def test_full_variable(self):
        var = TemplateVariable(
            name="{{price}}",
            description="Product price",
            default_value="0.00",
            required=False
        )
        
        assert var.default_value == "0.00"
        assert var.required is False


class TestTemplateCreate:
    """Testes para modelo TemplateCreate."""

    def test_minimal_create(self):
        data = TemplateCreate(
            name="My Template",
            caption_template="Hello {{name}}!"
        )
        
        assert data.name == "My Template"
        assert data.platform == TemplatePlatform.ALL
        assert data.category == TemplateCategory.CUSTOM
        assert data.hashtags == []
        assert data.is_public is False

    def test_full_create(self):
        var = TemplateVariable(name="{{name}}", description="Name")
        data = TemplateCreate(
            name="Full Template",
            description="A complete template",
            platform=TemplatePlatform.INSTAGRAM,
            category=TemplateCategory.PRODUCT,
            caption_template="Hello {{name}}!",
            hashtags=["hello", "world"],
            variables=[var],
            thumbnail_url="https://example.com/thumb.jpg",
            is_public=True
        )
        
        assert data.platform == TemplatePlatform.INSTAGRAM
        assert data.is_public is True
        assert len(data.variables) == 1


class TestTemplateUpdate:
    """Testes para modelo TemplateUpdate."""

    def test_empty_update(self):
        data = TemplateUpdate()
        
        assert data.name is None
        assert data.platform is None

    def test_partial_update(self):
        data = TemplateUpdate(
            name="Updated Name",
            is_public=True
        )
        
        assert data.name == "Updated Name"
        assert data.description is None


class TestTemplateModel:
    """Testes para modelo Template."""

    def test_create_template(self):
        template = Template(
            id="uuid-123",
            name="Test Template",
            platform="instagram",
            category="product",
            caption_template="Hello {{name}}",
            hashtags=["test"],
            variables=[{"name": "{{name}}", "description": "Name"}],
            is_public=False,
            user_id="user_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert template.id == "uuid-123"
        assert template.usage_count == 0


class TestRenderRequest:
    """Testes para modelo RenderRequest."""

    def test_empty_request(self):
        req = RenderRequest()
        
        assert req.variables == {}
        assert req.include_hashtags is True

    def test_with_variables(self):
        req = RenderRequest(
            variables={"name": "John", "price": "99.99"},
            include_hashtags=False
        )
        
        assert req.variables["name"] == "John"
        assert req.include_hashtags is False


# ==================== TEST TEMPLATE SERVICE ====================

class TestTemplateService:
    """Testes para TemplateService."""

    @pytest.fixture
    def service(self):
        return TemplateService()

    @pytest.fixture
    def mock_redis(self):
        """Mock do redis_client."""
        redis = AsyncMock()
        redis.hset = AsyncMock()
        redis.sadd = AsyncMock()
        redis.hgetall = AsyncMock()
        redis.smembers = AsyncMock()
        redis.keys = AsyncMock()
        redis.delete = AsyncMock()
        redis.srem = AsyncMock()
        redis.hincrby = AsyncMock()
        return redis

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_create_template(self, mock_redis_client, service):
        """Deve criar template corretamente."""
        mock_redis_client.hset = AsyncMock()
        mock_redis_client.sadd = AsyncMock()
        
        data = TemplateCreate(
            name="New Template",
            caption_template="Hello {{name}}!",
            platform=TemplatePlatform.INSTAGRAM
        )
        
        result = await service.create("user_123", data)
        
        assert result.name == "New Template"
        assert result.platform == "instagram"
        assert result.user_id == "user_123"
        mock_redis_client.hset.assert_called_once()
        mock_redis_client.sadd.assert_called_once()

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_get_template_found(self, mock_redis_client, service):
        """Deve retornar template existente."""
        mock_redis_client.hgetall = AsyncMock(return_value={
            "id": "template_123",
            "name": "Test",
            "platform": "all",
            "category": "custom",
            "caption_template": "Test",
            "hashtags": "[]",
            "variables": "[]",
            "is_public": "False",
            "user_id": "user_123",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "usage_count": "5"
        })
        
        result = await service.get("user_123", "template_123")
        
        assert result is not None
        assert result.id == "template_123"
        assert result.usage_count == 5

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_get_template_not_found(self, mock_redis_client, service):
        """Deve retornar None quando template não existe."""
        mock_redis_client.hgetall = AsyncMock(return_value={})
        mock_redis_client.keys = AsyncMock(return_value=[])
        
        result = await service.get("user_123", "nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_get_public_template(self, mock_redis_client, service):
        """Deve encontrar template público de outro usuário."""
        # Primeiro hgetall retorna vazio (template não é do user)
        # Depois keys encontra o template público
        mock_redis_client.hgetall = AsyncMock(side_effect=[
            {},  # Não encontrado para o user
            {    # Template público encontrado
                "id": "template_123",
                "name": "Public Template",
                "platform": "all",
                "category": "custom",
                "caption_template": "Test",
                "hashtags": "[]",
                "variables": "[]",
                "is_public": "True",
                "user_id": "other_user",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ])
        mock_redis_client.keys = AsyncMock(
            return_value=["templates:other_user:template_123"]
        )
        
        result = await service.get("user_123", "template_123")
        
        assert result is not None
        assert result.is_public is True

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_list_templates(self, mock_redis_client, service):
        """Deve listar templates do usuário."""
        mock_redis_client.smembers = AsyncMock(
            return_value=["t1", "t2"]
        )
        
        template_data = {
            "id": "t1",
            "name": "Template 1",
            "platform": "all",
            "category": "custom",
            "caption_template": "Test",
            "hashtags": "[]",
            "variables": "[]",
            "is_public": "False",
            "user_id": "user_123",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "usage_count": "10"
        }
        mock_redis_client.hgetall = AsyncMock(return_value=template_data)
        mock_redis_client.keys = AsyncMock(return_value=[])
        
        result = await service.list("user_123")
        
        assert len(result) >= 1

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_list_with_platform_filter(self, mock_redis_client, service):
        """Deve filtrar por plataforma."""
        mock_redis_client.smembers = AsyncMock(return_value=["t1"])
        mock_redis_client.hgetall = AsyncMock(return_value={
            "id": "t1",
            "name": "Instagram Template",
            "platform": "instagram",
            "category": "product",
            "caption_template": "Test",
            "hashtags": "[]",
            "variables": "[]",
            "is_public": "False",
            "user_id": "user_123",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        mock_redis_client.keys = AsyncMock(return_value=[])
        
        result = await service.list(
            "user_123",
            platform=TemplatePlatform.INSTAGRAM
        )
        
        # Template com platform instagram deve passar
        assert any(t.platform == "instagram" for t in result)

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_update_template(self, mock_redis_client, service):
        """Deve atualizar template."""
        mock_redis_client.hgetall = AsyncMock(return_value={
            "id": "t1",
            "name": "Old Name",
            "platform": "all",
            "category": "custom",
            "caption_template": "Old",
            "hashtags": "[]",
            "variables": "[]",
            "is_public": "False",
            "user_id": "user_123",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        mock_redis_client.hset = AsyncMock()
        
        update_data = TemplateUpdate(name="New Name")
        
        result = await service.update("user_123", "t1", update_data)
        
        assert result is not None
        mock_redis_client.hset.assert_called_once()

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_update_template_not_found(self, mock_redis_client, service):
        """Update de template inexistente retorna None."""
        mock_redis_client.hgetall = AsyncMock(return_value={})
        
        result = await service.update(
            "user_123",
            "nonexistent",
            TemplateUpdate(name="New")
        )
        
        assert result is None

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_delete_template(self, mock_redis_client, service):
        """Deve deletar template."""
        mock_redis_client.delete = AsyncMock(return_value=1)
        mock_redis_client.srem = AsyncMock()
        
        result = await service.delete("user_123", "t1")
        
        assert result is True
        mock_redis_client.delete.assert_called_once()
        mock_redis_client.srem.assert_called_once()

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_delete_template_not_found(self, mock_redis_client, service):
        """Delete de template inexistente retorna False."""
        mock_redis_client.delete = AsyncMock(return_value=0)
        
        result = await service.delete("user_123", "nonexistent")
        
        assert result is False

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_render_template(self, mock_redis_client, service):
        """Deve renderizar template com variáveis."""
        mock_redis_client.hgetall = AsyncMock(return_value={
            "id": "t1",
            "name": "Test",
            "platform": "all",
            "category": "custom",
            "caption_template": "Hello {{name}}! Price: {{price}}",
            "hashtags": '["test", "promo"]',
            "variables": "[]",
            "is_public": "False",
            "user_id": "user_123",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        mock_redis_client.hincrby = AsyncMock()
        
        result = await service.render(
            "user_123",
            "t1",
            {"name": "World", "price": "99.99"},
            include_hashtags=True
        )
        
        assert "Hello World!" in result["caption"]
        assert "99.99" in result["caption"]
        assert "#test" in result["caption"]

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_render_without_hashtags(self, mock_redis_client, service):
        """Deve renderizar sem hashtags."""
        mock_redis_client.hgetall = AsyncMock(return_value={
            "id": "t1",
            "name": "Test",
            "platform": "all",
            "category": "custom",
            "caption_template": "Hello {{name}}!",
            "hashtags": '["test"]',
            "variables": "[]",
            "is_public": "False",
            "user_id": "user_123",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        mock_redis_client.hincrby = AsyncMock()
        
        result = await service.render(
            "user_123",
            "t1",
            {"name": "World"},
            include_hashtags=False
        )
        
        assert "#test" not in result["caption"]

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_render_template_not_found(self, mock_redis_client, service):
        """Render de template inexistente levanta ValueError."""
        mock_redis_client.hgetall = AsyncMock(return_value={})
        mock_redis_client.keys = AsyncMock(return_value=[])
        
        with pytest.raises(ValueError, match="Template not found"):
            await service.render("user_123", "nonexistent", {})

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_clone_template(self, mock_redis_client, service):
        """Deve clonar template."""
        mock_redis_client.hgetall = AsyncMock(return_value={
            "id": "original",
            "name": "Original Template",
            "platform": "instagram",
            "category": "product",
            "caption_template": "Test caption",
            "hashtags": '["hashtag1"]',
            "variables": '[{"name": "{{var}}", "description": "test", "required": true}]',
            "is_public": "True",
            "user_id": "other_user",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        mock_redis_client.hset = AsyncMock()
        mock_redis_client.sadd = AsyncMock()
        
        result = await service.clone("user_123", "original", "My Clone")
        
        assert result.name == "My Clone"
        assert "Cloned from" in result.description
        assert result.is_public is False
        assert result.user_id == "user_123"

    @pytest.mark.asyncio
    @patch('api.routes.templates.redis_client')
    async def test_clone_template_not_found(self, mock_redis_client, service):
        """Clone de template inexistente levanta ValueError."""
        mock_redis_client.hgetall = AsyncMock(return_value={})
        mock_redis_client.keys = AsyncMock(return_value=[])
        
        with pytest.raises(ValueError, match="Template not found"):
            await service.clone("user_123", "nonexistent", "Clone")

    def test_to_template_conversion(self, service):
        """_to_template deve converter dados corretamente."""
        data = {
            "id": "t1",
            "name": "Test",
            "description": "Desc",
            "platform": "instagram",
            "category": "product",
            "caption_template": "Caption",
            "hashtags": '["a", "b"]',
            "variables": '[{"name": "{{x}}", "description": "x"}]',
            "thumbnail_url": "https://example.com/img.jpg",
            "is_public": "True",
            "user_id": "user_123",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
            "usage_count": "15"
        }
        
        result = service._to_template(data)
        
        assert result.id == "t1"
        assert result.hashtags == ["a", "b"]
        assert len(result.variables) == 1
        assert result.is_public is True
        assert result.usage_count == 15


# ==================== TEST DEFAULT TEMPLATES ====================

class TestDefaultTemplates:
    """Testes para DEFAULT_TEMPLATES."""

    def test_default_templates_exist(self):
        """Deve haver templates padrão."""
        assert len(DEFAULT_TEMPLATES) > 0

    def test_default_templates_structure(self):
        """Templates padrão devem ter estrutura correta."""
        for template in DEFAULT_TEMPLATES:
            assert "name" in template
            assert "caption_template" in template
            assert "platform" in template
            assert "category" in template
            assert "hashtags" in template
            assert "variables" in template

    def test_produto_em_destaque_template(self):
        """Template Produto em Destaque deve existir."""
        template = next(
            (t for t in DEFAULT_TEMPLATES if t["name"] == "Produto em Destaque"),
            None
        )
        
        assert template is not None
        assert "{{product_name}}" in template["caption_template"]
        assert "{{sale_price}}" in template["caption_template"]


# ==================== TEST ROUTES ====================

class TestTemplateRoutes:
    """Testes para endpoints de templates."""

    @pytest.fixture
    def current_user(self):
        return {"id": "user_123", "email": "test@test.com"}

    @pytest.mark.asyncio
    @patch('api.routes.templates.template_service')
    async def test_list_templates_endpoint(self, mock_service, current_user):
        """GET /templates deve listar templates."""
        from api.routes.templates import list_templates
        
        mock_template = Template(
            id="t1",
            name="Test",
            platform="all",
            category="custom",
            caption_template="Test",
            hashtags=[],
            variables=[],
            is_public=False,
            user_id="user_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_service.list = AsyncMock(return_value=[mock_template])
        
        result = await list_templates(
            platform=None,
            category=None,
            include_public=True,
            current_user=current_user
        )
        
        assert "templates" in result
        assert len(result["templates"]) == 1

    @pytest.mark.asyncio
    @patch('api.routes.templates.template_service')
    async def test_create_template_endpoint(self, mock_service, current_user):
        """POST /templates deve criar template."""
        from api.routes.templates import create_template
        
        mock_template = Template(
            id="new_id",
            name="New Template",
            platform="instagram",
            category="product",
            caption_template="Test",
            hashtags=["tag"],
            variables=[],
            is_public=False,
            user_id="user_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_service.create = AsyncMock(return_value=mock_template)
        
        data = TemplateCreate(
            name="New Template",
            caption_template="Test",
            platform=TemplatePlatform.INSTAGRAM
        )
        
        result = await create_template(data, current_user)
        
        assert result["name"] == "New Template"

    @pytest.mark.asyncio
    async def test_get_default_templates_endpoint(self):
        """GET /templates/defaults deve retornar templates padrão."""
        from api.routes.templates import get_default_templates
        
        result = await get_default_templates()
        
        assert "templates" in result
        assert len(result["templates"]) == len(DEFAULT_TEMPLATES)

    @pytest.mark.asyncio
    async def test_get_categories_endpoint(self):
        """GET /templates/categories deve retornar categorias."""
        from api.routes.templates import get_categories
        
        result = await get_categories()
        
        assert "categories" in result
        assert len(result["categories"]) == len(TemplateCategory)

    @pytest.mark.asyncio
    @patch('api.routes.templates.template_service')
    async def test_get_template_endpoint(self, mock_service, current_user):
        """GET /templates/{id} deve retornar template."""
        from api.routes.templates import get_template
        
        mock_template = Template(
            id="t1",
            name="Test",
            platform="all",
            category="custom",
            caption_template="Test",
            hashtags=[],
            variables=[],
            is_public=False,
            user_id="user_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_service.get = AsyncMock(return_value=mock_template)
        
        result = await get_template("t1", current_user)
        
        assert result["id"] == "t1"

    @pytest.mark.asyncio
    @patch('api.routes.templates.template_service')
    async def test_get_template_not_found(self, mock_service, current_user):
        """GET /templates/{id} com ID inválido retorna 404."""
        from api.routes.templates import get_template
        from fastapi import HTTPException
        
        mock_service.get = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_template("nonexistent", current_user)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch('api.routes.templates.template_service')
    async def test_update_template_endpoint(self, mock_service, current_user):
        """PATCH /templates/{id} deve atualizar template."""
        from api.routes.templates import update_template
        
        mock_template = Template(
            id="t1",
            name="Updated",
            platform="all",
            category="custom",
            caption_template="Test",
            hashtags=[],
            variables=[],
            is_public=False,
            user_id="user_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_service.update = AsyncMock(return_value=mock_template)
        
        result = await update_template(
            "t1",
            TemplateUpdate(name="Updated"),
            current_user
        )
        
        assert result["name"] == "Updated"

    @pytest.mark.asyncio
    @patch('api.routes.templates.template_service')
    async def test_delete_template_endpoint(self, mock_service, current_user):
        """DELETE /templates/{id} deve deletar template."""
        from api.routes.templates import delete_template
        
        mock_service.delete = AsyncMock(return_value=True)
        
        result = await delete_template("t1", current_user)
        
        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    @patch('api.routes.templates.template_service')
    async def test_delete_template_not_found(self, mock_service, current_user):
        """DELETE /templates/{id} com ID inválido retorna 404."""
        from api.routes.templates import delete_template
        from fastapi import HTTPException
        
        mock_service.delete = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_template("nonexistent", current_user)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch('api.routes.templates.template_service')
    async def test_render_template_endpoint(self, mock_service, current_user):
        """POST /templates/{id}/render deve renderizar template."""
        from api.routes.templates import render_template
        
        mock_service.render = AsyncMock(return_value={
            "caption": "Hello World!",
            "hashtags": ["test"],
            "platform": "all"
        })
        
        request = RenderRequest(variables={"name": "World"})
        
        result = await render_template("t1", request, current_user)
        
        assert result["caption"] == "Hello World!"

    @pytest.mark.asyncio
    @patch('api.routes.templates.template_service')
    async def test_render_template_not_found(self, mock_service, current_user):
        """POST /templates/{id}/render com ID inválido retorna 404."""
        from api.routes.templates import render_template
        from fastapi import HTTPException
        
        mock_service.render = AsyncMock(
            side_effect=ValueError("Template not found")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await render_template(
                "nonexistent",
                RenderRequest(),
                current_user
            )
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch('api.routes.templates.template_service')
    async def test_clone_template_endpoint(self, mock_service, current_user):
        """POST /templates/{id}/clone deve clonar template."""
        from api.routes.templates import clone_template
        
        mock_template = Template(
            id="cloned_id",
            name="My Clone",
            platform="all",
            category="custom",
            caption_template="Test",
            hashtags=[],
            variables=[],
            is_public=False,
            user_id="user_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_service.clone = AsyncMock(return_value=mock_template)
        
        result = await clone_template("original_id", "My Clone", current_user)
        
        assert result["name"] == "My Clone"

    @pytest.mark.asyncio
    @patch('api.routes.templates.template_service')
    async def test_clone_template_not_found(self, mock_service, current_user):
        """POST /templates/{id}/clone com ID inválido retorna 404."""
        from api.routes.templates import clone_template
        from fastapi import HTTPException
        
        mock_service.clone = AsyncMock(
            side_effect=ValueError("Template not found")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await clone_template("nonexistent", "Clone", current_user)
        
        assert exc_info.value.status_code == 404
