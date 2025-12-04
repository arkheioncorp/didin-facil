"""
Comprehensive tests for template_library.py routes.
Target: Increase coverage from 42% to 90%+
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_automation_template():
    """Mock automation template."""
    mock = MagicMock()
    mock.to_dict.return_value = {
        "id": "auto-123",
        "name": "Price Alert Workflow",
        "category": "alerts",
        "difficulty": "beginner"
    }
    mock.category = MagicMock(value="alerts")
    return mock


@pytest.fixture
def mock_chatbot_template():
    """Mock chatbot template."""
    mock = MagicMock()
    mock.to_dict.return_value = {
        "id": "chat-123",
        "name": "Sales Funnel Bot",
        "category": "vendas",
        "difficulty": "intermediate"
    }
    mock.category = MagicMock(value="vendas")
    return mock


@pytest.fixture
def mock_content_template():
    """Mock content template."""
    mock = MagicMock()
    mock.to_dict.return_value = {
        "id": "content-123",
        "name": "Instagram Promo Post",
        "platform": "instagram",
        "content_type": "post"
    }
    mock.platform = MagicMock(value="instagram")
    mock.content_type = MagicMock(value="post")
    mock.hashtags = ["#promo", "#sale"]
    mock.best_posting_times = ["9:00", "18:00"]
    mock.visual_tips = ["Use bright colors"]
    mock.estimated_engagement = 4.5
    return mock


@pytest.fixture
def mock_business_preset():
    """Mock business preset."""
    mock = MagicMock()
    mock.to_dict.return_value = {
        "id": "preset-123",
        "name": "E-commerce Starter",
        "business_type": "ecommerce",
        "business_size": "micro"
    }
    mock.business_type = MagicMock(value="ecommerce")
    return mock


# ============================================
# AUTOMATION TEMPLATE TESTS
# ============================================

class TestListAutomationTemplates:
    """Tests for GET /library/automation endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_all_templates(self, mock_automation_template):
        """Test listing all automation templates."""
        with patch("api.routes.template_library.get_automation_templates") as mock_get, \
             patch("api.routes.template_library.AutomationCategory") as MockCat:
            
            mock_get.return_value = [mock_automation_template]
            MockCat.__iter__ = lambda self: iter([MagicMock(value="alerts")])
            
            from api.routes.template_library import list_automation_templates
            
            result = await list_automation_templates(category=None, difficulty=None)
            
            assert result["total"] == 1
            assert len(result["templates"]) == 1
    
    @pytest.mark.asyncio
    async def test_list_with_category_filter(self, mock_automation_template):
        """Test listing templates with category filter."""
        with patch("api.routes.template_library.get_automation_templates") as mock_get, \
             patch("api.routes.template_library.AutomationCategory") as MockCat:
            
            mock_get.return_value = [mock_automation_template]
            MockCat.__call__ = lambda self, x: MagicMock(value=x)
            MockCat.__iter__ = lambda self: iter([MagicMock(value="alerts")])
            
            from api.routes.template_library import list_automation_templates
            
            result = await list_automation_templates(category="alerts", difficulty=None)
            
            mock_get.assert_called_once()


class TestGetAutomationTemplate:
    """Tests for GET /library/automation/{template_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_template_found(self, mock_automation_template):
        """Test getting existing template."""
        with patch("api.routes.template_library.get_automation_by_id") as mock_get:
            mock_get.return_value = mock_automation_template
            
            from api.routes.template_library import get_automation_template
            
            result = await get_automation_template(template_id="auto-123")
            
            assert result["id"] == "auto-123"
    
    @pytest.mark.asyncio
    async def test_get_template_not_found(self):
        """Test getting non-existent template."""
        with patch("api.routes.template_library.get_automation_by_id") as mock_get:
            mock_get.return_value = None
            
            from api.routes.template_library import get_automation_template
            
            with pytest.raises(HTTPException) as exc:
                await get_automation_template(template_id="nonexistent")
            
            assert exc.value.status_code == 404


class TestExportAutomationWorkflow:
    """Tests for POST /library/automation/export endpoint."""
    
    @pytest.mark.asyncio
    async def test_export_success(self):
        """Test exporting workflow successfully."""
        with patch("api.routes.template_library.export_n8n_workflow") as mock_export:
            mock_export.return_value = {"nodes": [], "connections": {}}
            
            from api.routes.template_library import (
                ExportWorkflowRequest, export_automation_workflow)
            
            request = ExportWorkflowRequest(
                template_id="auto-123",
                variables={"api_key": "test"},
                webhook_url="https://webhook.example.com"
            )
            
            result = await export_automation_workflow(request=request)
            
            assert result["success"] is True
            assert "workflow" in result
            assert "import_instructions" in result
    
    @pytest.mark.asyncio
    async def test_export_not_found(self):
        """Test exporting non-existent template."""
        with patch("api.routes.template_library.export_n8n_workflow") as mock_export:
            mock_export.side_effect = ValueError("Template not found")
            
            from api.routes.template_library import (
                ExportWorkflowRequest, export_automation_workflow)
            
            request = ExportWorkflowRequest(template_id="nonexistent")
            
            with pytest.raises(HTTPException) as exc:
                await export_automation_workflow(request=request)
            
            assert exc.value.status_code == 404


# ============================================
# CHATBOT TEMPLATE TESTS
# ============================================

class TestListChatbotTemplates:
    """Tests for GET /library/chatbot endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_all_chatbot_templates(self, mock_chatbot_template):
        """Test listing all chatbot templates."""
        with patch("api.routes.template_library.get_chatbot_templates") as mock_get, \
             patch("api.routes.template_library.ChatbotCategory") as MockCat:
            
            mock_get.return_value = [mock_chatbot_template]
            MockCat.__iter__ = lambda self: iter([MagicMock(value="vendas")])
            
            from api.routes.template_library import list_chatbot_templates
            
            result = await list_chatbot_templates(category=None, difficulty=None)
            
            assert result["total"] == 1


class TestGetChatbotTemplate:
    """Tests for GET /library/chatbot/{template_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_chatbot_found(self, mock_chatbot_template):
        """Test getting existing chatbot template."""
        with patch("api.routes.template_library.get_chatbot_by_id") as mock_get:
            mock_get.return_value = mock_chatbot_template
            
            from api.routes.template_library import get_chatbot_template
            
            result = await get_chatbot_template(template_id="chat-123")
            
            assert result["id"] == "chat-123"
    
    @pytest.mark.asyncio
    async def test_get_chatbot_not_found(self):
        """Test getting non-existent chatbot template."""
        with patch("api.routes.template_library.get_chatbot_by_id") as mock_get:
            mock_get.return_value = None
            
            from api.routes.template_library import get_chatbot_template
            
            with pytest.raises(HTTPException) as exc:
                await get_chatbot_template(template_id="nonexistent")
            
            assert exc.value.status_code == 404


class TestExportChatbotFlow:
    """Tests for POST /library/chatbot/export endpoint."""
    
    @pytest.mark.asyncio
    async def test_export_chatbot_success(self):
        """Test exporting chatbot flow successfully."""
        with patch("api.routes.template_library.export_typebot_flow") as mock_export:
            mock_export.return_value = {"groups": [], "edges": []}
            
            from api.routes.template_library import (ExportChatbotRequest,
                                                     export_chatbot_flow)
            
            request = ExportChatbotRequest(
                template_id="chat-123",
                variables={"company_name": "Test Corp"}
            )
            
            result = await export_chatbot_flow(request=request)
            
            assert result["success"] is True
            assert "flow" in result
    
    @pytest.mark.asyncio
    async def test_export_chatbot_not_found(self):
        """Test exporting non-existent chatbot template."""
        with patch("api.routes.template_library.export_typebot_flow") as mock_export:
            mock_export.side_effect = ValueError("Template not found")
            
            from api.routes.template_library import (ExportChatbotRequest,
                                                     export_chatbot_flow)
            
            request = ExportChatbotRequest(template_id="nonexistent")
            
            with pytest.raises(HTTPException) as exc:
                await export_chatbot_flow(request=request)
            
            assert exc.value.status_code == 404


# ============================================
# CONTENT TEMPLATE TESTS
# ============================================

class TestListContentTemplates:
    """Tests for GET /library/content endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_all_content_templates(self, mock_content_template):
        """Test listing all content templates."""
        with patch("api.routes.template_library.get_content_templates") as mock_get, \
             patch("api.routes.template_library.ContentPlatform") as MockPlat, \
             patch("api.routes.template_library.ContentType") as MockType, \
             patch("api.routes.template_library.ContentCategory") as MockCat:
            
            mock_get.return_value = [mock_content_template]
            MockPlat.__iter__ = lambda self: iter([MagicMock(value="instagram")])
            MockType.__iter__ = lambda self: iter([MagicMock(value="post")])
            MockCat.__iter__ = lambda self: iter([MagicMock(value="promo")])
            
            from api.routes.template_library import list_content_templates
            
            result = await list_content_templates(platform=None, content_type=None, category=None)
            
            assert result["total"] == 1
    
    @pytest.mark.asyncio
    async def test_list_content_with_filters(self, mock_content_template):
        """Test listing content templates with filters."""
        with patch("api.routes.template_library.get_content_templates") as mock_get, \
             patch("api.routes.template_library.ContentPlatform") as MockPlat, \
             patch("api.routes.template_library.ContentType") as MockType, \
             patch("api.routes.template_library.ContentCategory") as MockCat:
            
            mock_get.return_value = [mock_content_template]
            MockPlat.__call__ = lambda self, x: MagicMock(value=x)
            MockPlat.__iter__ = lambda self: iter([MagicMock(value="instagram")])
            MockType.__call__ = lambda self, x: MagicMock(value=x)
            MockType.__iter__ = lambda self: iter([MagicMock(value="post")])
            MockCat.__call__ = lambda self, x: MagicMock(value=x)
            MockCat.__iter__ = lambda self: iter([MagicMock(value="promo")])
            
            from api.routes.template_library import list_content_templates
            
            result = await list_content_templates(
                platform="instagram",
                content_type="post",
                category="promo"
            )
            
            mock_get.assert_called_once()


class TestGetContentTemplate:
    """Tests for GET /library/content/{template_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_content_found(self, mock_content_template):
        """Test getting existing content template."""
        with patch("api.routes.template_library.get_content_by_id") as mock_get:
            mock_get.return_value = mock_content_template
            
            from api.routes.template_library import get_content_template
            
            result = await get_content_template(template_id="content-123")
            
            assert result["id"] == "content-123"
    
    @pytest.mark.asyncio
    async def test_get_content_not_found(self):
        """Test getting non-existent content template."""
        with patch("api.routes.template_library.get_content_by_id") as mock_get:
            mock_get.return_value = None
            
            from api.routes.template_library import get_content_template
            
            with pytest.raises(HTTPException) as exc:
                await get_content_template(template_id="nonexistent")
            
            assert exc.value.status_code == 404


class TestGenerateContentCaption:
    """Tests for POST /library/content/generate-caption endpoint."""
    
    @pytest.mark.asyncio
    async def test_generate_caption_success(self, mock_content_template):
        """Test generating caption successfully."""
        with patch("api.routes.template_library.generate_caption") as mock_gen, \
             patch("api.routes.template_library.get_content_by_id") as mock_get:
            
            mock_gen.return_value = "🔥 Amazing sale on Test Product! #promo"
            mock_get.return_value = mock_content_template
            
            from api.routes.template_library import (GenerateCaptionRequest,
                                                     generate_content_caption)
            
            request = GenerateCaptionRequest(
                template_id="content-123",
                variables={"product_name": "Test Product", "discount": "50%"}
            )
            
            result = await generate_content_caption(request=request)
            
            assert result["success"] is True
            assert "caption" in result
            assert "hashtags" in result
    
    @pytest.mark.asyncio
    async def test_generate_caption_not_found(self):
        """Test generating caption for non-existent template."""
        with patch("api.routes.template_library.generate_caption") as mock_gen:
            mock_gen.side_effect = ValueError("Template not found")
            
            from api.routes.template_library import (GenerateCaptionRequest,
                                                     generate_content_caption)
            
            request = GenerateCaptionRequest(
                template_id="nonexistent",
                variables={}
            )
            
            with pytest.raises(HTTPException) as exc:
                await generate_content_caption(request=request)
            
            assert exc.value.status_code == 404


class TestGetContentCalendar:
    """Tests for GET /library/content/calendar endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_calendar_success(self):
        """Test getting content calendar."""
        mock_calendar = {
            "monday": {"type": "educational"},
            "tuesday": {"type": "engagement"}
        }
        
        with patch("api.routes.template_library.get_weekly_calendar") as mock_get:
            mock_get.return_value = mock_calendar
            
            from api.routes.template_library import get_content_calendar
            
            result = await get_content_calendar()
            
            assert "calendar" in result
            assert "tips" in result


class TestSuggestNextContent:
    """Tests for GET /library/content/suggest-next endpoint."""
    
    @pytest.mark.asyncio
    async def test_suggest_next_success(self, mock_content_template):
        """Test suggesting next content."""
        with patch("api.routes.template_library.suggest_next_post") as mock_suggest:
            mock_suggest.return_value = mock_content_template
            
            from api.routes.template_library import suggest_next_content
            
            result = await suggest_next_content(last_post_type="promo")
            
            assert "suggestion" in result
            assert "reason" in result


# ============================================
# BUSINESS PRESET TESTS
# ============================================

class TestListBusinessPresets:
    """Tests for GET /library/presets endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_all_presets(self, mock_business_preset):
        """Test listing all business presets."""
        with patch("api.routes.template_library.get_business_presets") as mock_get, \
             patch("api.routes.template_library.BusinessType") as MockType, \
             patch("api.routes.template_library.BusinessSize") as MockSize:
            
            mock_get.return_value = [mock_business_preset]
            MockType.__iter__ = lambda self: iter([MagicMock(value="ecommerce")])
            MockSize.__iter__ = lambda self: iter([MagicMock(value="micro")])
            
            from api.routes.template_library import list_business_presets
            
            result = await list_business_presets(business_type=None, business_size=None)
            
            assert result["total"] == 1


class TestGetBusinessPreset:
    """Tests for GET /library/presets/{preset_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_preset_found(self, mock_business_preset):
        """Test getting existing business preset."""
        with patch("api.routes.template_library.get_preset_by_id") as mock_get:
            mock_get.return_value = mock_business_preset
            
            from api.routes.template_library import get_business_preset
            
            result = await get_business_preset(preset_id="preset-123")
            
            assert result["id"] == "preset-123"
    
    @pytest.mark.asyncio
    async def test_get_preset_not_found(self):
        """Test getting non-existent preset."""
        with patch("api.routes.template_library.get_preset_by_id") as mock_get:
            mock_get.return_value = None
            
            from api.routes.template_library import get_business_preset
            
            with pytest.raises(HTTPException) as exc:
                await get_business_preset(preset_id="nonexistent")
            
            assert exc.value.status_code == 404


class TestRecommendBusinessPreset:
    """Tests for POST /library/presets/recommend endpoint."""
    
    @pytest.mark.asyncio
    async def test_recommend_preset_success(self, mock_business_preset):
        """Test recommending preset successfully."""
        with patch("api.routes.template_library.recommend_preset") as mock_rec, \
             patch("api.routes.template_library.BusinessType") as MockType:
            
            mock_rec.return_value = mock_business_preset
            MockType.__call__ = lambda self, x: MagicMock(value=x)
            
            from api.routes.template_library import (RecommendPresetRequest,
                                                     recommend_business_preset)
            
            request = RecommendPresetRequest(
                business_type="ecommerce",
                monthly_revenue=10000,
                team_size=3
            )
            
            result = await recommend_business_preset(request=request)
            
            assert "recommendation" in result
    
    @pytest.mark.asyncio
    async def test_recommend_preset_invalid_type(self):
        """Test recommending with invalid business type."""
        with patch("api.routes.template_library.BusinessType") as MockType:
            MockType.side_effect = ValueError("Invalid type")
            
            from api.routes.template_library import (RecommendPresetRequest,
                                                     recommend_business_preset)
            
            request = RecommendPresetRequest(
                business_type="invalid_type",
                monthly_revenue=0,
                team_size=1
            )
            
            with pytest.raises(HTTPException) as exc:
                await recommend_business_preset(request=request)
            
            assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_recommend_preset_not_found(self):
        """Test when no preset found for profile."""
        with patch("api.routes.template_library.recommend_preset") as mock_rec, \
             patch("api.routes.template_library.BusinessType") as MockType:
            
            mock_rec.return_value = None
            MockType.__call__ = lambda self, x: MagicMock(value=x)
            
            from api.routes.template_library import (RecommendPresetRequest,
                                                     recommend_business_preset)
            
            request = RecommendPresetRequest(
                business_type="ecommerce",
                monthly_revenue=0,
                team_size=1
            )
            
            with pytest.raises(HTTPException) as exc:
                await recommend_business_preset(request=request)
            
            assert exc.value.status_code == 404


class TestApplyBusinessPreset:
    """Tests for POST /library/presets/{preset_id}/apply endpoint."""
    
    @pytest.mark.asyncio
    async def test_apply_preset_success(self):
        """Test applying preset successfully."""
        mock_setup = {
            "automations": ["workflow1"],
            "chatbots": ["bot1"],
            "templates": ["template1"],
            "metrics": {"target": 100}
        }
        
        with patch("api.routes.template_library.apply_preset") as mock_apply:
            mock_apply.return_value = mock_setup
            
            from api.routes.template_library import apply_business_preset
            
            result = await apply_business_preset(preset_id="preset-123")
            
            assert result["success"] is True
            assert "automations" in result
    
    @pytest.mark.asyncio
    async def test_apply_preset_not_found(self):
        """Test applying non-existent preset."""
        with patch("api.routes.template_library.apply_preset") as mock_apply:
            mock_apply.side_effect = ValueError("Preset not found")
            
            from api.routes.template_library import apply_business_preset
            
            with pytest.raises(HTTPException) as exc:
                await apply_business_preset(preset_id="nonexistent")
            
            assert exc.value.status_code == 404


# ============================================
# STATS TESTS
# ============================================

class TestGetLibraryStats:
    """Tests for GET /library/stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_stats_success(self, mock_automation_template, mock_chatbot_template,
                                     mock_content_template, mock_business_preset):
        """Test getting library statistics."""
        with patch("api.routes.template_library.get_automation_templates") as mock_auto, \
             patch("api.routes.template_library.get_chatbot_templates") as mock_chat, \
             patch("api.routes.template_library.get_content_templates") as mock_content, \
             patch("api.routes.template_library.get_business_presets") as mock_preset, \
             patch("api.routes.template_library.AutomationCategory") as MockAutoCat, \
             patch("api.routes.template_library.ChatbotCategory") as MockChatCat, \
             patch("api.routes.template_library.ContentPlatform") as MockPlat, \
             patch("api.routes.template_library.ContentType") as MockType, \
             patch("api.routes.template_library.BusinessType") as MockBizType:
            
            mock_auto.return_value = [mock_automation_template]
            mock_chat.return_value = [mock_chatbot_template]
            mock_content.return_value = [mock_content_template]
            mock_preset.return_value = [mock_business_preset]
            
            MockAutoCat.__iter__ = lambda self: iter([MagicMock(value="alerts")])
            MockChatCat.__iter__ = lambda self: iter([MagicMock(value="vendas")])
            MockPlat.__iter__ = lambda self: iter([MagicMock(value="instagram")])
            MockType.__iter__ = lambda self: iter([MagicMock(value="post")])
            MockBizType.__iter__ = lambda self: iter([MagicMock(value="ecommerce")])
            
            from api.routes.template_library import get_library_stats
            
            result = await get_library_stats()
            
            assert "summary" in result
            assert result["summary"]["total_templates"] == 4
            assert "automation" in result
            assert "chatbot" in result
            assert "content" in result
            assert "presets" in result


# ============================================
# PYDANTIC MODEL TESTS
# ============================================

class TestPydanticModels:
    """Tests for Pydantic request models."""
    
    def test_export_workflow_request_defaults(self):
        """Test ExportWorkflowRequest with defaults."""
        from api.routes.template_library import ExportWorkflowRequest
        
        request = ExportWorkflowRequest(template_id="auto-123")
        
        assert request.variables == {}
        assert request.webhook_url is None
    
    def test_export_chatbot_request_defaults(self):
        """Test ExportChatbotRequest with defaults."""
        from api.routes.template_library import ExportChatbotRequest
        
        request = ExportChatbotRequest(template_id="chat-123")
        
        assert request.variables == {}
    
    def test_recommend_preset_request_defaults(self):
        """Test RecommendPresetRequest with defaults."""
        from api.routes.template_library import RecommendPresetRequest
        
        request = RecommendPresetRequest(business_type="ecommerce")
        
        assert request.monthly_revenue == 0
        assert request.team_size == 1
