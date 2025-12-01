"""
Testes para Template Library Routes
====================================
Cobertura para api/routes/template_library.py
"""

import pytest
from unittest.mock import MagicMock, patch


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_automation_template():
    """Mock de template de automação"""
    template = MagicMock()
    template.id = "auto-001"
    template.name = "Welcome Email"
    template.category = "marketing"
    template.difficulty = "beginner"
    template.to_dict.return_value = {
        "id": "auto-001",
        "name": "Welcome Email",
        "category": "marketing",
        "difficulty": "beginner"
    }
    return template


@pytest.fixture
def mock_chatbot_template():
    """Mock de template de chatbot"""
    template = MagicMock()
    template.id = "chat-001"
    template.name = "FAQ Bot"
    template.category = "faq"
    template.to_dict.return_value = {
        "id": "chat-001",
        "name": "FAQ Bot",
        "category": "faq"
    }
    return template


@pytest.fixture
def mock_content_template():
    """Mock de template de conteúdo"""
    template = MagicMock()
    template.id = "content-001"
    template.name = "Product Launch"
    template.platform = "instagram"
    template.to_dict.return_value = {
        "id": "content-001",
        "name": "Product Launch",
        "platform": "instagram"
    }
    return template


@pytest.fixture
def mock_business_preset():
    """Mock de preset de negócio"""
    preset = MagicMock()
    preset.id = "preset-001"
    preset.name = "E-commerce Starter"
    preset.business_type = "ecommerce"
    preset.to_dict.return_value = {
        "id": "preset-001",
        "name": "E-commerce Starter",
        "business_type": "ecommerce"
    }
    return preset


# ============================================
# TESTS: Automation Templates
# ============================================

class TestAutomationTemplates:
    """Testes de templates de automação"""

    @pytest.mark.asyncio
    async def test_list_automation_templates(self, mock_automation_template):
        """Deve listar templates de automação"""
        with patch(
            "api.routes.template_library.get_automation_templates"
        ) as mock_get:
            mock_get.return_value = [mock_automation_template]

            from api.routes.template_library import list_automation_templates

            result = await list_automation_templates(
                category=None, difficulty=None
            )

            assert result["total"] == 1
            assert len(result["templates"]) == 1
            assert result["templates"][0]["id"] == "auto-001"

    @pytest.mark.asyncio
    async def test_list_automation_by_category(self, mock_automation_template):
        """Deve filtrar por categoria"""
        with patch(
            "api.routes.template_library.get_automation_templates"
        ) as mock_get, patch(
            "api.routes.template_library.AutomationCategory"
        ) as mock_cat:
            mock_get.return_value = [mock_automation_template]
            mock_cat.return_value = "marketing"

            from api.routes.template_library import list_automation_templates

            result = await list_automation_templates(
                category="marketing", difficulty=None
            )

            assert result["total"] == 1
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_automation_template_success(
        self, mock_automation_template
    ):
        """Deve retornar template por ID"""
        with patch(
            "api.routes.template_library.get_automation_by_id"
        ) as mock_get:
            mock_get.return_value = mock_automation_template

            from api.routes.template_library import get_automation_template

            result = await get_automation_template("auto-001")

            assert result["id"] == "auto-001"
            mock_get.assert_called_once_with("auto-001")

    @pytest.mark.asyncio
    async def test_get_automation_template_not_found(self):
        """Deve retornar 404 se template não encontrado"""
        from fastapi import HTTPException

        with patch(
            "api.routes.template_library.get_automation_by_id"
        ) as mock_get:
            mock_get.return_value = None

            from api.routes.template_library import get_automation_template

            with pytest.raises(HTTPException) as exc:
                await get_automation_template("invalid")

            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_export_automation_workflow(self):
        """Deve exportar workflow n8n"""
        workflow_json = {
            "nodes": [],
            "connections": {},
            "name": "Test Workflow"
        }

        with patch(
            "api.routes.template_library.export_n8n_workflow"
        ) as mock_export:
            mock_export.return_value = workflow_json

            from api.routes.template_library import (
                export_automation_workflow, ExportWorkflowRequest
            )

            request = ExportWorkflowRequest(
                template_id="auto-001",
                variables={"key": "value"}
            )
            result = await export_automation_workflow(request)

            assert result["success"] is True
            assert result["workflow"] == workflow_json
            assert "import_instructions" in result

    @pytest.mark.asyncio
    async def test_export_automation_workflow_not_found(self):
        """Deve retornar 404 se template não encontrado"""
        from fastapi import HTTPException

        with patch(
            "api.routes.template_library.export_n8n_workflow"
        ) as mock_export:
            mock_export.side_effect = ValueError("Template not found")

            from api.routes.template_library import (
                export_automation_workflow, ExportWorkflowRequest
            )

            request = ExportWorkflowRequest(template_id="invalid")

            with pytest.raises(HTTPException) as exc:
                await export_automation_workflow(request)

            assert exc.value.status_code == 404


# ============================================
# TESTS: Chatbot Templates
# ============================================

class TestChatbotTemplates:
    """Testes de templates de chatbot"""

    @pytest.mark.asyncio
    async def test_list_chatbot_templates(self, mock_chatbot_template):
        """Deve listar templates de chatbot"""
        with patch(
            "api.routes.template_library.get_chatbot_templates"
        ) as mock_get:
            mock_get.return_value = [mock_chatbot_template]

            from api.routes.template_library import list_chatbot_templates

            result = await list_chatbot_templates(
                category=None, difficulty=None
            )

            assert result["total"] == 1
            assert len(result["templates"]) == 1

    @pytest.mark.asyncio
    async def test_get_chatbot_template_success(self, mock_chatbot_template):
        """Deve retornar template por ID"""
        with patch(
            "api.routes.template_library.get_chatbot_by_id"
        ) as mock_get:
            mock_get.return_value = mock_chatbot_template

            from api.routes.template_library import get_chatbot_template

            result = await get_chatbot_template("chat-001")

            assert result["id"] == "chat-001"

    @pytest.mark.asyncio
    async def test_get_chatbot_template_not_found(self):
        """Deve retornar 404 se não encontrado"""
        from fastapi import HTTPException

        with patch(
            "api.routes.template_library.get_chatbot_by_id"
        ) as mock_get:
            mock_get.return_value = None

            from api.routes.template_library import get_chatbot_template

            with pytest.raises(HTTPException) as exc:
                await get_chatbot_template("invalid")

            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_export_chatbot_flow(self):
        """Deve exportar fluxo Typebot"""
        flow_json = {"blocks": [], "variables": []}

        with patch(
            "api.routes.template_library.export_typebot_flow"
        ) as mock_export:
            mock_export.return_value = flow_json

            from api.routes.template_library import (
                export_chatbot_flow, ExportChatbotRequest
            )

            request = ExportChatbotRequest(
                template_id="chat-001",
                variables={}
            )
            result = await export_chatbot_flow(request)

            assert result["success"] is True
            assert result["flow"] == flow_json


# ============================================
# TESTS: Content Templates
# ============================================

class TestContentTemplates:
    """Testes de templates de conteúdo"""

    @pytest.mark.asyncio
    async def test_list_content_templates(self, mock_content_template):
        """Deve listar templates de conteúdo"""
        with patch(
            "api.routes.template_library.get_content_templates"
        ) as mock_get:
            mock_get.return_value = [mock_content_template]

            from api.routes.template_library import list_content_templates

            result = await list_content_templates(
                platform=None, content_type=None, category=None
            )

            assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_get_content_template_success(self, mock_content_template):
        """Deve retornar template por ID"""
        with patch(
            "api.routes.template_library.get_content_by_id"
        ) as mock_get:
            mock_get.return_value = mock_content_template

            from api.routes.template_library import get_content_template

            result = await get_content_template("content-001")

            assert result["id"] == "content-001"

    @pytest.mark.asyncio
    async def test_get_content_template_not_found(self):
        """Deve retornar 404 se não encontrado"""
        from fastapi import HTTPException

        with patch(
            "api.routes.template_library.get_content_by_id"
        ) as mock_get:
            mock_get.return_value = None

            from api.routes.template_library import get_content_template

            with pytest.raises(HTTPException) as exc:
                await get_content_template("invalid")

            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_content_caption(self):
        """Deve gerar caption personalizada"""
        with patch(
            "api.routes.template_library.generate_caption"
        ) as mock_gen:
            mock_gen.return_value = "Generated caption with #hashtags"

            from api.routes.template_library import (
                generate_content_caption, GenerateCaptionRequest
            )

            request = GenerateCaptionRequest(
                template_id="content-001",
                variables={"product": "Produto X"}
            )
            result = await generate_content_caption(request)

            assert result["success"] is True
            assert "caption" in result

    @pytest.mark.asyncio
    async def test_get_content_calendar(self):
        """Deve retornar calendário semanal"""
        calendar = [
            {"day": "Monday", "posts": []},
            {"day": "Tuesday", "posts": []}
        ]

        with patch(
            "api.routes.template_library.get_weekly_calendar"
        ) as mock_cal:
            mock_cal.return_value = calendar

            from api.routes.template_library import get_content_calendar

            result = await get_content_calendar()

            assert "calendar" in result
            assert len(result["calendar"]) == 2

    @pytest.mark.asyncio
    async def test_suggest_next_content(self, mock_content_template):
        """Deve sugerir próximo post"""
        mock_content_template.estimated_engagement = 0.85

        with patch(
            "api.routes.template_library.suggest_next_post"
        ) as mock_suggest:
            mock_suggest.return_value = mock_content_template

            from api.routes.template_library import suggest_next_content

            result = await suggest_next_content(last_post_type=None)

            assert "suggestion" in result
            assert "reason" in result


# ============================================
# TESTS: Business Presets
# ============================================

class TestBusinessPresets:
    """Testes de presets de negócio"""

    @pytest.mark.asyncio
    async def test_list_business_presets(self, mock_business_preset):
        """Deve listar presets de negócio"""
        with patch(
            "api.routes.template_library.get_business_presets"
        ) as mock_get:
            mock_get.return_value = [mock_business_preset]

            from api.routes.template_library import list_business_presets

            result = await list_business_presets(
                business_type=None, business_size=None
            )

            assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_get_business_preset_success(self, mock_business_preset):
        """Deve retornar preset por ID"""
        with patch(
            "api.routes.template_library.get_preset_by_id"
        ) as mock_get:
            mock_get.return_value = mock_business_preset

            from api.routes.template_library import get_business_preset

            result = await get_business_preset("preset-001")

            assert result["id"] == "preset-001"

    @pytest.mark.asyncio
    async def test_get_business_preset_not_found(self):
        """Deve retornar 404 se não encontrado"""
        from fastapi import HTTPException

        with patch(
            "api.routes.template_library.get_preset_by_id"
        ) as mock_get:
            mock_get.return_value = None

            from api.routes.template_library import get_business_preset

            with pytest.raises(HTTPException) as exc:
                await get_business_preset("invalid")

            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_recommend_business_preset(self, mock_business_preset):
        """Deve recomendar preset baseado no negócio"""
        with patch(
            "api.routes.template_library.recommend_preset"
        ) as mock_rec, patch(
            "api.routes.template_library.BusinessType"
        ) as mock_type:
            mock_rec.return_value = mock_business_preset
            mock_type.return_value = MagicMock(value="ecommerce")

            from api.routes.template_library import (
                recommend_business_preset, RecommendPresetRequest
            )

            request = RecommendPresetRequest(
                business_type="ecommerce",
                monthly_revenue=50000,
                team_size=5
            )
            result = await recommend_business_preset(request)

            assert result["recommendation"]["id"] == "preset-001"

    @pytest.mark.asyncio
    async def test_apply_business_preset(self, mock_business_preset):
        """Deve aplicar preset ao ambiente"""
        applied_config = {
            "automations": [],
            "chatbots": [],
            "templates": []
        }

        with patch(
            "api.routes.template_library.apply_preset"
        ) as mock_apply:
            mock_apply.return_value = applied_config

            from api.routes.template_library import apply_business_preset

            result = await apply_business_preset("preset-001")

            assert result["success"] is True
            assert "automations" in result


# ============================================
# TESTS: Models
# ============================================

class TestTemplateLibraryModels:
    """Testes dos modelos Pydantic"""

    def test_export_workflow_request(self):
        """Deve criar request de export corretamente"""
        from api.routes.template_library import ExportWorkflowRequest

        request = ExportWorkflowRequest(
            template_id="auto-001",
            variables={"key": "value"},
            webhook_url="https://webhook.example.com"
        )
        assert request.template_id == "auto-001"
        assert request.webhook_url == "https://webhook.example.com"

    def test_export_workflow_request_defaults(self):
        """Deve ter defaults corretos"""
        from api.routes.template_library import ExportWorkflowRequest

        request = ExportWorkflowRequest(template_id="auto-001")
        assert request.variables == {}
        assert request.webhook_url is None

    def test_generate_caption_request(self):
        """Deve criar request de caption"""
        from api.routes.template_library import GenerateCaptionRequest

        request = GenerateCaptionRequest(
            template_id="content-001",
            variables={"product": "iPhone"}
        )
        assert request.template_id == "content-001"

    def test_recommend_preset_request(self):
        """Deve criar request de recomendação"""
        from api.routes.template_library import RecommendPresetRequest

        request = RecommendPresetRequest(
            business_type="saas",
            monthly_revenue=100000,
            team_size=10
        )
        assert request.business_type == "saas"
        assert request.team_size == 10
